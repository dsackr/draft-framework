from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from draft_table.repo import ensure_git_repo, ensure_workspace_layout, is_workspace, repo_name_from_url


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
            self.assertTrue((workspace / "catalog" / "technology-components").exists())
            self.assertTrue((workspace / "catalog" / "host-standards").exists())
            self.assertTrue((workspace / "catalog" / "software-deployment-patterns").exists())
            self.assertTrue((workspace / "configurations" / "object-patches").exists())
            self.assertTrue((workspace / "configurations" / "definition-checklists").exists())
            self.assertTrue((workspace / ".draft" / "workspace.yaml").exists())
            self.assertTrue((workspace / ".draft" / "framework.lock").exists())
            self.assertTrue(created)
            self.assertTrue(is_workspace(workspace))

    def test_ensure_git_repo_creates_missing_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "new-draft-content"

            result = ensure_git_repo(workspace)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((workspace / ".git").exists())

    def test_ensure_git_repo_rejects_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "not-a-directory"
            target.write_text("content", encoding="utf-8")

            result = ensure_git_repo(target)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not a directory", result.stderr)


if __name__ == "__main__":
    unittest.main()
