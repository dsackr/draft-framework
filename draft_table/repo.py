from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

from .paths import DEFAULT_WORKSPACE_PARENT, REPO_ROOT, resolve_framework_root, workspace_framework_root


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

FRAMEWORK_VENDOR_DIRS = (
    "configurations",
    "docs",
    "schemas",
    "tools",
)

FRAMEWORK_VENDOR_OPTIONAL_DIRS = (
    "templates",
    "examples",
)

FRAMEWORK_VENDOR_FILES = (
    "AGENTS.md",
    "AI_INDEX.md",
    "CLAUDE.md",
    "GEMINI.md",
    "llms.txt",
    "security.md",
)

DEFAULT_FRAMEWORK_SOURCE = "https://github.com/dsackr/draft-framework.git"
COPY_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".git", ".pytest_cache")


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
    framework_root = resolve_framework_root(framework_repo)
    git_root = framework_root.parent if (framework_root.parent / ".git").exists() else framework_root
    result = run_git(["rev-parse", "HEAD"], git_root)
    return result.stdout.strip() if result.returncode == 0 else ""


def framework_lock_data(framework_repo: Path = REPO_ROOT, source_label: str | None = None) -> dict[str, Any]:
    framework_commit = current_framework_commit(framework_repo)
    return {
        "schemaVersion": "1.0",
        "framework": {
            "source": source_label or DEFAULT_FRAMEWORK_SOURCE,
            "vendoredPath": ".draft/framework",
            "updatePolicy": "explicit",
            "syncedRef": "main",
            "syncedCommit": framework_commit,
        },
    }


def copy_optional_framework_dir(source_root: Path, source_repo: Path, relative: str, destination: Path) -> bool:
    for source in (source_root / relative, source_repo / relative):
        if source.exists():
            shutil.copytree(source, destination / relative, dirs_exist_ok=True, ignore=COPY_IGNORE)
            return True
    return False


def copy_optional_framework_file(source_root: Path, source_repo: Path, filename: str, destination: Path) -> bool:
    for source in (source_root / filename, source_repo / filename):
        if source.exists():
            target = destination / filename
            if filename in {"AGENTS.md", "AI_INDEX.md", "CLAUDE.md", "GEMINI.md", "llms.txt"}:
                target.write_text(vendored_framework_text(source.read_text(encoding="utf-8")), encoding="utf-8")
            else:
                shutil.copy2(source, target)
            return True
    return False


def vendored_framework_text(text: str) -> str:
    replacements = {
        "framework/docs/": "docs/",
        "framework/schemas/": "schemas/",
        "framework/configurations/": "configurations/",
        "framework/tools/": "tools/",
        "framework/docs": "docs",
        "framework/schemas": "schemas",
        "framework/configurations": "configurations",
        "framework/tools": "tools",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def vendor_framework(workspace: Path, framework_repo: Path = REPO_ROOT, overwrite: bool = False) -> list[Path]:
    workspace = workspace.expanduser()
    destination = workspace_framework_root(workspace)
    if destination.exists() and not overwrite:
        if (destination / "tools" / "validate.py").exists():
            return []
        shutil.rmtree(destination)

    source_root = resolve_framework_root(framework_repo)
    source_repo = source_root.parent
    if source_root.resolve() == destination.resolve():
        return []
    if overwrite and destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    for relative in FRAMEWORK_VENDOR_DIRS:
        source = source_root / relative
        if source.exists():
            shutil.copytree(source, destination / relative, dirs_exist_ok=True, ignore=COPY_IGNORE)
    for relative in FRAMEWORK_VENDOR_OPTIONAL_DIRS:
        copy_optional_framework_dir(source_root, source_repo, relative, destination)
    for filename in FRAMEWORK_VENDOR_FILES:
        copy_optional_framework_file(source_root, source_repo, filename, destination)
    return [destination]


def refresh_vendored_framework(
    workspace: Path,
    framework_repo: Path = REPO_ROOT,
    source_label: str | None = None,
) -> list[Path]:
    workspace = workspace.expanduser()
    copied = vendor_framework(workspace, framework_repo, overwrite=True)
    lock_path = workspace / ".draft" / "framework.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(
        yaml.safe_dump(framework_lock_data(framework_repo, source_label), sort_keys=False),
        encoding="utf-8",
    )
    return copied + [lock_path]


def framework_status(workspace: Path, framework_repo: Path = REPO_ROOT) -> dict[str, Any]:
    workspace = workspace.expanduser()
    vendor_root = workspace_framework_root(workspace)
    lock_path = workspace / ".draft" / "framework.lock"
    lock: dict[str, Any] = {}
    if lock_path.exists():
        try:
            loaded = yaml.safe_load(lock_path.read_text(encoding="utf-8")) or {}
            lock = loaded if isinstance(loaded, dict) else {}
        except yaml.YAMLError:
            lock = {}
    framework = lock.get("framework") if isinstance(lock.get("framework"), dict) else {}
    return {
        "vendored": (vendor_root / "tools" / "validate.py").exists(),
        "vendoredPath": str(vendor_root),
        "lockPath": str(lock_path),
        "syncedCommit": str(framework.get("syncedCommit") or framework.get("pinnedCommit") or ""),
        "installedCommit": current_framework_commit(framework_repo),
        "updatePolicy": str(framework.get("updatePolicy") or "explicit"),
    }


def ensure_workspace_layout(workspace: Path, framework_repo: Path = REPO_ROOT) -> list[Path]:
    workspace = workspace.expanduser()
    created: list[Path] = []
    for relative in WORKSPACE_DIRS:
        path = workspace / relative
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(path)

    copied = vendor_framework(workspace, framework_repo, overwrite=False)
    created.extend(copied)

    workspace_yaml = workspace / ".draft" / "workspace.yaml"
    if not workspace_yaml.exists():
        workspace_yaml.write_text(
            yaml.safe_dump(
                {
                    "schemaVersion": "1.0",
                    "workspace": {"name": workspace.name},
                    "framework": {
                        "source": DEFAULT_FRAMEWORK_SOURCE,
                        "vendoredPath": ".draft/framework",
                        "updatePolicy": "explicit",
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
        framework_lock.write_text(yaml.safe_dump(framework_lock_data(framework_repo), sort_keys=False), encoding="utf-8")
        created.append(framework_lock)
    return created


def is_workspace(path: Path) -> bool:
    root = path.expanduser()
    framework_root = workspace_framework_root(root)
    return (
        (root / "catalog").exists()
        and (root / "configurations").exists()
        and (framework_root / "tools" / "validate.py").exists()
    )
