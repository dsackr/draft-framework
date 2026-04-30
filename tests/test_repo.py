from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from draft_table.repo import ensure_workspace_layout, is_workspace, repo_name_from_url


class RepoTests(unittest.TestCase):
    def test_repo_name_from_url_handles_common_github_urls(self) -> None:
        self.assertEqual(repo_name_from_url("https://github.com/acme/draft-content.git"), "draft-content")
        self.assertEqual(repo_name_from_url("git@github.com:acme/platform catalog.git"), "platform-catalog")

    def test_ensure_workspace_layout_bootstraps_expected_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "company-draft"
            workspace.mkdir()
            created = ensure_workspace_layout(workspace)

            self.assertTrue((workspace / "catalog").exists())
            self.assertTrue((workspace / "configurations" / "object-patches").exists())
            self.assertTrue((workspace / ".draft" / "workspace.yaml").exists())
            self.assertTrue((workspace / ".draft" / "framework.lock").exists())
            self.assertTrue(created)
            self.assertTrue(is_workspace(workspace))


if __name__ == "__main__":
    unittest.main()
