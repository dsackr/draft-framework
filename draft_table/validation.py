from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .paths import REPO_ROOT


@dataclass(frozen=True)
class ValidationResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def build_validate_command(workspace: Path, framework_repo: Path = REPO_ROOT) -> list[str]:
    return [
        sys.executable,
        str(framework_repo / "framework" / "tools" / "validate.py"),
        "--workspace",
        str(workspace.expanduser()),
    ]


def validate_workspace(workspace: Path, framework_repo: Path = REPO_ROOT) -> ValidationResult:
    process = subprocess.run(
        build_validate_command(workspace, framework_repo),
        cwd=str(framework_repo),
        text=True,
        capture_output=True,
        check=False,
    )
    return ValidationResult(process.returncode, process.stdout, process.stderr)
