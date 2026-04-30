from __future__ import annotations

import re
import subprocess
from pathlib import Path

import yaml

from .paths import DEFAULT_WORKSPACE_PARENT, REPO_ROOT


WORKSPACE_DIRS = (
    "catalog",
    "catalog/technology-components",
    "catalog/appliance-components",
    "catalog/host-standards",
    "catalog/service-standards",
    "catalog/database-standards",
    "catalog/product-services",
    "catalog/paas-services",
    "catalog/saas-services",
    "catalog/reference-architectures",
    "catalog/software-deployment-patterns",
    "catalog/decision-records",
    "catalog/sessions",
    "configurations",
    "configurations/definition-checklists",
    "configurations/compliance-controls",
    "configurations/control-enforcement-profiles",
    "configurations/object-patches",
    ".draft",
)


def repo_name_from_url(url: str) -> str:
    cleaned = url.strip().rstrip("/")
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]
    name = cleaned.rsplit("/", 1)[-1]
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-")
    return name or "draft-content"


def default_clone_path(url: str) -> Path:
    return DEFAULT_WORKSPACE_PARENT / repo_name_from_url(url)


def run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )


def clone_or_pull(url: str, destination: Path) -> subprocess.CompletedProcess[str]:
    destination = destination.expanduser()
    if destination.exists() and (destination / ".git").exists():
        return run_git(["pull", "--ff-only"], destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        ["git", "clone", url, str(destination)],
        text=True,
        capture_output=True,
        check=False,
    )


def ensure_git_repo(repo_path: Path) -> subprocess.CompletedProcess[str]:
    root = repo_path.expanduser()
    if root.exists() and not root.is_dir():
        return subprocess.CompletedProcess(
            ["git", "init"],
            2,
            "",
            f"Path exists and is not a directory: {root}",
        )
    root.mkdir(parents=True, exist_ok=True)
    if (root / ".git").exists():
        return run_git(["status", "--short", "--branch"], root)
    return run_git(["init"], root)


def git_status(repo_path: Path) -> subprocess.CompletedProcess[str]:
    return run_git(["status", "--short", "--branch"], repo_path.expanduser())


def git_commit(repo_path: Path, message: str) -> subprocess.CompletedProcess[str]:
    run_git(["add", "-A"], repo_path.expanduser())
    return run_git(["commit", "-m", message], repo_path.expanduser())


def current_framework_commit(framework_repo: Path = REPO_ROOT) -> str:
    result = run_git(["rev-parse", "HEAD"], framework_repo)
    return result.stdout.strip() if result.returncode == 0 else ""


def ensure_workspace_layout(workspace: Path, framework_repo: Path = REPO_ROOT) -> list[Path]:
    workspace = workspace.expanduser()
    created: list[Path] = []
    for relative in WORKSPACE_DIRS:
        path = workspace / relative
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(path)

    framework_commit = current_framework_commit(framework_repo)
    workspace_yaml = workspace / ".draft" / "workspace.yaml"
    if not workspace_yaml.exists():
        workspace_yaml.write_text(
            yaml.safe_dump(
                {
                    "schemaVersion": "1.0",
                    "workspace": {"name": workspace.name},
                    "framework": {
                        "source": "https://github.com/dsackr/draft-framework.git",
                        "pinnedRef": "main",
                        "pinnedCommit": framework_commit,
                    },
                    "paths": {
                        "catalog": "catalog",
                        "configurations": "configurations",
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        created.append(workspace_yaml)

    framework_lock = workspace / ".draft" / "framework.lock"
    if not framework_lock.exists():
        framework_lock.write_text(
            yaml.safe_dump(
                {
                    "schemaVersion": "1.0",
                    "framework": {
                        "source": "https://github.com/dsackr/draft-framework.git",
                        "pinnedRef": "main",
                        "pinnedCommit": framework_commit,
                    },
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        created.append(framework_lock)
    return created


def is_workspace(path: Path) -> bool:
    root = path.expanduser()
    return (root / "catalog").exists() and (root / "configurations").exists()
