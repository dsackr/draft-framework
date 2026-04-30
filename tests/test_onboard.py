from __future__ import annotations

import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from draft_table.github import GitHubStatus
from draft_table.onboard import ONBOARDING_BANNER, print_banner
from draft_table.onboard import run_onboarding


class OnboardingTests(unittest.TestCase):
    def test_onboarding_banner_is_ascii(self) -> None:
        ONBOARDING_BANNER.encode("ascii")

    def test_print_banner_shows_draft_table(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            print_banner()

        text = output.getvalue()
        self.assertIn("DRAFT TABLE", text)
        self.assertIn("D R A F T", text)
        self.assertIn("Local Architecture Drafting Table", text)

    def test_onboarding_creates_new_local_content_repo(self) -> None:
        with TemporaryDirectory() as directory:
            workspace = Path(directory) / "draft-content"
            config_path = Path(directory) / "config.yaml"
            answers = ["", str(workspace), "local-llm", "", ""]

            with mock.patch("builtins.input", side_effect=answers):
                with mock.patch(
                    "draft_table.onboard.github_status",
                    return_value=GitHubStatus(False, False, "GitHub CLI not found."),
                ):
                    with redirect_stdout(StringIO()):
                        result = run_onboarding(config_path)

            self.assertEqual(result, 0)
            self.assertTrue((workspace / ".git").exists())
            self.assertTrue((workspace / "catalog").exists())
            self.assertTrue((workspace / ".draft" / "workspace.yaml").exists())


if __name__ == "__main__":
    unittest.main()
