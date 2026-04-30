from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from draft_table.config import load_config, redact, save_config
from draft_table.paths import FRAMEWORK_ROOT


class ConfigTests(unittest.TestCase):
    def test_redact_masks_secret_keys_recursively(self) -> None:
        config = {
            "provider": {
                "type": "codex",
                "api_key": "should-not-log",
                "nested": {"refreshToken": "hidden"},
            },
            "content_repo_path": "/tmp/catalog",
        }

        redacted = redact(config)

        self.assertEqual(redacted["provider"]["api_key"], "[REDACTED]")
        self.assertEqual(redacted["provider"]["nested"]["refreshToken"], "[REDACTED]")
        self.assertEqual(redacted["content_repo_path"], "/tmp/catalog")

    def test_save_config_strips_unknown_secret_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            save_config(
                {
                    "content_repo_path": "/tmp/catalog",
                    "provider": {"type": "custom-command", "access_token": "nope"},
                },
                path,
            )

            raw = yaml.safe_load(path.read_text(encoding="utf-8"))

        self.assertNotIn("access_token", raw["provider"])
        self.assertEqual(raw["provider"]["type"], "custom-command")

    def test_load_config_merges_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text("provider:\n  type: codex\n", encoding="utf-8")
            config = load_config(path)

        self.assertEqual(config["provider"]["type"], "codex")
        self.assertIn("preferences", config)

    def test_load_config_accepts_framework_root_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text(f"framework_repo_path: {FRAMEWORK_ROOT}\n", encoding="utf-8")
            config = load_config(path)

        self.assertEqual(Path(config["framework_repo_path"]), FRAMEWORK_ROOT)


if __name__ == "__main__":
    unittest.main()
