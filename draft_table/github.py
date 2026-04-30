from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class GitHubStatus:
    gh_available: bool
    authenticated: bool
    detail: str


def github_status() -> GitHubStatus:
    gh = shutil.which("gh")
    if not gh:
        return GitHubStatus(False, False, "GitHub CLI not found. Install gh or use Git credentials for clone/push.")
    result = subprocess.run(
        [gh, "auth", "status"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return GitHubStatus(True, True, "GitHub CLI is authenticated.")
    return GitHubStatus(True, False, "Run gh auth login to authenticate GitHub CLI.")
