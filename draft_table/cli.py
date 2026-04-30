from __future__ import annotations

import argparse
import socket
import subprocess
import sys
from pathlib import Path

from .config import load_config, redacted_yaml
from .draftsman import DraftsmanEngine
from .github import github_status
from .onboard import run_onboarding
from .providers import doctor as provider_doctor
from .providers import format_statuses
from .repo import git_commit, git_status, is_workspace
from .validation import validate_workspace


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="draft-table", description="Local-first DRAFT Table CLI.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    onboard = subcommands.add_parser("onboard", help="Configure a local content repo and AI provider.")
    onboard.set_defaults(func=cmd_onboard)

    serve = subcommands.add_parser("serve", help="Start the local DRAFT Table web UI.")
    serve.add_argument(
        "--host",
        default="0.0.0.0",
        help="Interface to bind. Defaults to 0.0.0.0 for LAN access; use 127.0.0.1 for local-only.",
    )
    serve.add_argument("--port", type=int, default=0)
    serve.set_defaults(func=cmd_serve)

    validate = subcommands.add_parser("validate", help="Validate the selected or provided content repo.")
    validate.add_argument("--workspace", default="")
    validate.set_defaults(func=cmd_validate)

    chat = subcommands.add_parser("chat", help="Start the terminal fallback Draftsman conversation.")
    chat.set_defaults(func=cmd_chat)

    doctor = subcommands.add_parser("doctor", help="Show local setup status.")
    doctor.set_defaults(func=cmd_doctor)

    ai = subcommands.add_parser("ai", help="AI provider commands.")
    ai_subcommands = ai.add_subparsers(dest="ai_command", required=True)
    ai_doctor = ai_subcommands.add_parser("doctor", help="Check configured provider CLIs.")
    ai_doctor.set_defaults(func=cmd_ai_doctor)

    repo = subcommands.add_parser("repo", help="Content repo commands.")
    repo_subcommands = repo.add_subparsers(dest="repo_command", required=True)
    repo_status = repo_subcommands.add_parser("status", help="Show content repo Git status.")
    repo_status.set_defaults(func=cmd_repo_status)

    commit = subcommands.add_parser("commit", help="Commit content repo changes.")
    commit.add_argument("-m", "--message", required=True)
    commit.set_defaults(func=cmd_commit)
    return parser


def selected_workspace(config: dict, override: str = "") -> Path:
    path = override or str(config.get("content_repo_path") or "")
    if not path:
        raise SystemExit("No content repo selected. Run draft-table onboard first.")
    return Path(path).expanduser()


def cmd_onboard(args: argparse.Namespace) -> int:
    return run_onboarding()


def cmd_serve(args: argparse.Namespace) -> int:
    port = args.port or find_available_port()
    try:
        import uvicorn
    except ModuleNotFoundError as exc:
        raise SystemExit("Missing runtime dependency. Install with: python3 -m pip install -e .") from exc
    from .web import create_app

    app = create_app()
    print(f"DRAFT Table listening on {args.host}:{port}")
    for label, url in server_urls(args.host, port):
        print(f"{label}: {url}")
    if is_lan_bind(args.host):
        print("LAN mode is the default. Use --host 127.0.0.1 for local-only access.")
    uvicorn.run(app, host=args.host, port=port, log_config=None)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    config = load_config()
    workspace = selected_workspace(config, args.workspace)
    result = validate_workspace(workspace)
    output = result.stdout or result.stderr
    if output:
        print(output, end="" if output.endswith("\n") else "\n")
    return result.returncode


def cmd_chat(args: argparse.Namespace) -> int:
    engine = DraftsmanEngine()
    session_id = None
    print("DRAFT Table Draftsman")
    print("Type /exit to leave. Use draft-table serve for the full web drafting table.")
    while True:
        try:
            message = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not message:
            continue
        if message in {"/exit", "/quit"}:
            return 0
        response = engine.chat(message, session_id)
        session_id = response.session_id
        print(f"\nDraftsman: {response.answer}")
        if response.questions:
            print("\nQuestions:")
            for question in response.questions:
                print(f"- {question}")
        if response.proposals:
            print("\nProposed artifacts:")
            for proposal in response.public_dict()["proposals"]:
                print(f"- {proposal['action']} {proposal['artifactType']}: {proposal['name']}")
            print("Open the web UI to review and apply proposed artifacts.")
    return 0


def cmd_ai_doctor(args: argparse.Namespace) -> int:
    config = load_config()
    print(format_statuses(provider_doctor(config.get("provider") or {})))
    return 0


def cmd_repo_status(args: argparse.Namespace) -> int:
    config = load_config()
    workspace = selected_workspace(config)
    result = git_status(workspace)
    output = result.stdout or result.stderr
    print(output, end="" if output.endswith("\n") else "\n")
    return result.returncode


def cmd_commit(args: argparse.Namespace) -> int:
    config = load_config()
    workspace = selected_workspace(config)
    result = git_commit(workspace, args.message)
    output = result.stdout or result.stderr
    print(output, end="" if output.endswith("\n") else "\n")
    return result.returncode


def cmd_doctor(args: argparse.Namespace) -> int:
    config = load_config()
    print("Config:")
    print(redacted_yaml(config))
    github = github_status()
    print(f"GitHub: {github.detail}")
    print("Providers:")
    print(format_statuses(provider_doctor(config.get("provider") or {})))
    content_path = str(config.get("content_repo_path") or "")
    if content_path:
        workspace = Path(content_path).expanduser()
        print(f"Content repo: {workspace}")
        print(f"DRAFT workspace layout: {'ok' if is_workspace(workspace) else 'missing catalog/configurations'}")
    return 0


def find_available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def is_lan_bind(host: str) -> bool:
    return host in {"0.0.0.0", "::"}


def local_lan_address() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            address = str(sock.getsockname()[0])
            if address and not address.startswith("127."):
                return address
    except OSError:
        pass
    try:
        address = socket.gethostbyname(socket.gethostname())
    except OSError:
        return ""
    return "" if address.startswith("127.") else address


def server_urls(host: str, port: int) -> list[tuple[str, str]]:
    if is_lan_bind(host):
        lan_address = local_lan_address() or "<this-device-lan-ip>"
        return [
            ("LAN URL", f"http://{lan_address}:{port}"),
            ("Local URL", f"http://127.0.0.1:{port}"),
        ]
    return [("URL", f"http://{host}:{port}")]


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=str(cwd), text=True, capture_output=True, check=False)


if __name__ == "__main__":
    raise SystemExit(main())
