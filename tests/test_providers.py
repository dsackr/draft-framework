from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from draft_table.providers import build_provider_command, detect_provider


class ProviderTests(unittest.TestCase):
    def test_detect_provider_finds_executable_on_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "codex"
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            executable.chmod(0o755)
            with mock.patch.dict(os.environ, {"PATH": directory}):
                status = detect_provider("codex")

        self.assertTrue(status.available)
        self.assertTrue(status.executable.endswith("codex"))

    def test_detect_missing_provider_returns_install_hint(self) -> None:
        with mock.patch.dict(os.environ, {"PATH": ""}):
            status = detect_provider("claude-code")

        self.assertFalse(status.available)
        self.assertIn("Claude Code", status.detail)

    def test_build_codex_command_does_not_include_secrets(self) -> None:
        command = build_provider_command("codex", "/usr/bin/codex", "Review object", "gpt-5.5")

        self.assertEqual(command[:2], ["/usr/bin/codex", "exec"])
        self.assertIn("--model", command)
        self.assertNotIn("api_key", " ".join(command).lower())
        self.assertNotIn("token", " ".join(command).lower())

    def test_local_llm_command_is_explicitly_not_supported_in_phase_one(self) -> None:
        with self.assertRaises(ValueError):
            build_provider_command("local-llm", "", "prompt")


if __name__ == "__main__":
    unittest.main()
