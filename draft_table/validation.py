from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .paths import REPO_ROOT, resolve_framework_root, workspace_framework_root


@dataclass(frozen=True)
class ValidationResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def build_validate_command(workspace: Path, framework_repo: Path = REPO_ROOT) -> list[str]:
    framework_root = selected_framework_root(workspace, framework_repo)
    return [
        sys.executable,
        str(framework_root / "tools" / "validate.py"),
        "--workspace",
        str(workspace.expanduser()),
    ]


def validate_workspace(workspace: Path, framework_repo: Path = REPO_ROOT) -> ValidationResult:
    framework_root = selected_framework_root(workspace, framework_repo)
    process = subprocess.run(
        build_validate_command(workspace, framework_root),
        cwd=str(framework_root.parent),
        text=True,
        capture_output=True,
        check=False,
    )
    return ValidationResult(process.returncode, process.stdout, process.stderr)


def selected_framework_root(workspace: Path | None, framework_repo: Path = REPO_ROOT) -> Path:
    if workspace:
        vendored = workspace_framework_root(workspace)
        if (vendored / "tools" / "validate.py").exists():
            return vendored.resolve()
    return resolve_framework_root(framework_repo)
