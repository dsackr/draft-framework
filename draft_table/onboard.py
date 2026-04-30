from __future__ import annotations

from pathlib import Path

from .config import load_config, save_config
from .github import github_status
from .providers import SUPPORTED_PROVIDERS, detect_provider, install_hint
from .repo import clone_or_pull, default_clone_path, ensure_git_repo, ensure_workspace_layout


ONBOARDING_BANNER = r"""
+------------------------------------------------+
|                  DRAFT TABLE                   |
|         Local Architecture Drafting Table       |
+------------------------------------------------+
        __________________________________
       /________________________________/|
      /______/ D R A F T /____________/ |
     /________________________________/  |
    |   ______________        /\      |  |
    |  /_____________/|      /__\     | /
    |_______________________________|/
       ||                         ||
       ||                         ||
""".strip("\n")


def prompt(default: str, label: str) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def print_banner() -> None:
    print(ONBOARDING_BANNER)


def run_onboarding(config_path: Path | None = None) -> int:
    config = load_config(config_path)
    print_banner()
    print("DRAFT Table onboarding")
    print("This stores repo paths and provider preferences only. It does not store API keys.")
    print("Your company repo will include a private .draft/framework copy for normal Draftsman use.")

    github = github_status()
    print(github.detail)
    if github.gh_available and not github.authenticated:
        print("Run gh auth login in another terminal if clone/push needs GitHub authentication.")

    current_repo = str(config.get("content_repo_path") or "")
    repo_url = prompt("", "GitHub company DRAFT repo URL (leave blank to select local path)")
    if repo_url:
        destination = Path(prompt(str(default_clone_path(repo_url)), "Local clone path")).expanduser()
        result = clone_or_pull(repo_url, destination)
        if result.returncode != 0:
            print(result.stderr or result.stdout)
            return result.returncode
        content_path = destination
    else:
        content_path = Path(prompt(current_repo, "Local company DRAFT repo path")).expanduser()
        if not content_path.exists():
            print(f"Creating local company DRAFT repo at {content_path}")
        git_result = ensure_git_repo(content_path)
        if git_result.returncode != 0:
            print(git_result.stderr or git_result.stdout)
            return git_result.returncode
        if git_result.args[-1] == "init":
            print(f"Initialized Git repo at {content_path}")

    created = ensure_workspace_layout(content_path)
    if created:
        print("Bootstrapped DRAFT workspace paths:")
        for path in created:
            print(f"  {path}")

    print("AI providers:")
    for index, provider in enumerate(SUPPORTED_PROVIDERS, start=1):
        print(f"  {index}. {provider}")
    selected = prompt(config.get("provider", {}).get("type") or "codex", "Provider")
    if selected.isdigit():
        index = int(selected) - 1
        if index < 0 or index >= len(SUPPORTED_PROVIDERS):
            print(f"Unsupported provider selection: {selected}")
            return 2
        selected = SUPPORTED_PROVIDERS[index]
    if selected not in SUPPORTED_PROVIDERS:
        print(f"Unsupported provider: {selected}")
        return 2

    executable = ""
    endpoint = ""
    if selected == "custom-command":
        executable = prompt("", "Custom provider command")
    elif selected == "local-llm":
        endpoint = prompt("http://127.0.0.1:11434", "Ollama-compatible endpoint")

    status = detect_provider(selected, executable or endpoint or None)
    print(status.detail if status.available else install_hint(selected))
    model = prompt(config.get("provider", {}).get("model") or "", "Model name (optional)")

    config["content_repo_path"] = str(content_path)
    config["provider"] = {
        "type": selected,
        "executable": status.executable if selected != "local-llm" else "",
        "endpoint": endpoint if selected == "local-llm" else "",
        "model": model,
    }
    save_config(config, config_path)
    print("Onboarding complete.")
    return 0
