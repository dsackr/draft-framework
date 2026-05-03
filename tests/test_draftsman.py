from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from draft_table.config import save_config
from draft_table.draftsman import (
    DraftsmanEngine,
    build_draftsman_prompt,
    invoke_provider,
    parse_provider_response,
    provider_timeout_seconds,
    public_proposal,
    safe_workspace_path,
)
from draft_table.paths import REPO_ROOT
from draft_table.sessions import DraftsmanSessionStore


class DraftsmanTests(unittest.TestCase):
    def test_answers_framework_question_without_provider(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.yaml"
            save_config({"framework_repo_path": str(REPO_ROOT)}, config_path)
            engine = DraftsmanEngine(config_path, DraftsmanSessionStore(Path(directory) / "sessions"))

            response = engine.chat("What is a Technology Component?")

        self.assertFalse(response.provider_used)
        self.assertIn("Technology Component", response.answer)
        self.assertFalse(response.proposals)

    def test_answers_catalog_usage_question_without_provider(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.yaml"
            save_config({"framework_repo_path": str(REPO_ROOT)}, config_path)
            engine = DraftsmanEngine(config_path, DraftsmanSessionStore(Path(directory) / "sessions"))

            response = engine.chat("Where is the Falcon agent used?")

        self.assertFalse(response.provider_used)
        self.assertIn("CrowdStrike Falcon Agent", response.answer)
        self.assertNotIn("```", response.answer)

    def test_public_proposal_hides_backend_content(self) -> None:
        public = public_proposal(
            {
                "id": "p1",
                "action": "create",
                "artifactType": "Host Standard",
                "name": "Standard Host",
                "summary": "Creates a standard host.",
                "path": "catalog/host-standards/host-standard.yaml",
                "content": "schemaVersion: '1.0'",
            }
        )

        self.assertNotIn("content", public)
        self.assertEqual(public["path"], "catalog/host-standards/host-standard.yaml")
        self.assertEqual(public["name"], "Standard Host")

    def test_parse_provider_response_extracts_json(self) -> None:
        raw = "Here is the result:\n" + json.dumps({"answer": "Done", "questions": [], "proposals": []})

        parsed = parse_provider_response(raw)

        self.assertEqual(parsed["answer"], "Done")

    def test_provider_timeout_returns_visible_answer(self) -> None:
        with mock.patch(
            "draft_table.draftsman.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["gemini"], timeout=10),
        ):
            answer = invoke_provider(
                {"type": "gemini-cli", "executable": "/usr/bin/gemini", "timeout_seconds": 10},
                "Draft something",
            )

        self.assertIn("Gemini CLI provider did not return within 10 seconds", answer)
        self.assertIn("I did not create or apply any artifacts", answer)
        self.assertNotIn("Draft something", answer)

    def test_provider_timeout_is_clamped(self) -> None:
        self.assertEqual(provider_timeout_seconds({"timeout_seconds": 1}), 5)
        self.assertEqual(provider_timeout_seconds({"timeout_seconds": 99999}), 1800)
        self.assertEqual(provider_timeout_seconds({"timeout_seconds": "invalid"}), 180)

    def test_prompt_guides_host_patch_management_as_mechanism_not_team_owner(self) -> None:
        prompt = build_draftsman_prompt(REPO_ROOT, None, "Build a Windows Server Host Standard.", {"uploads": []})

        self.assertIn("For Host Requirement Group patch management", prompt)
        self.assertIn("patch platform, installed component", prompt)
        self.assertIn("do not ask which", prompt)
        self.assertIn("team owns patching", prompt)

    def test_prompt_explains_appliance_component_service_like_capability_answers(self) -> None:
        prompt = build_draftsman_prompt(REPO_ROOT, None, "Build an Appliance Component.", {"uploads": []})

        self.assertIn("For Appliance Components", prompt)
        self.assertIn("vendor-product", prompt)
        self.assertIn("no Host Standard or Service Standard wrapper", prompt)

    def test_safe_workspace_path_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                safe_workspace_path(Path(directory), "../outside.yaml")

    def test_provider_response_creates_public_artifact_proposal_without_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "provider.py"
            script.write_text(
                "#!/usr/bin/env python3\n"
                "import json, sys\n"
                "print(json.dumps({'answer':'I proposed one artifact.', 'questions': [], "
                "'proposals':[{'id':'p1','action':'create','artifactType':'Host Standard','name':'Standard Host',"
                "'summary':'A reusable host pattern.','path':'catalog/host-standards/host-standard.yaml',"
                "'content':'schemaVersion: 1.0'}]}))\n",
                encoding="utf-8",
            )
            script.chmod(0o755)
            config_path = Path(directory) / "config.yaml"
            save_config(
                {
                    "framework_repo_path": str(REPO_ROOT),
                    "provider": {"type": "custom-command", "executable": str(script)},
                },
                config_path,
            )
            engine = DraftsmanEngine(config_path, DraftsmanSessionStore(Path(directory) / "sessions"))

            response = engine.chat("Draft a standard host pattern.")

        public = response.public_dict()
        self.assertTrue(response.provider_used)
        self.assertEqual(public["proposals"][0]["name"], "Standard Host")
        self.assertNotIn("content", public["proposals"][0])


if __name__ == "__main__":
    unittest.main()
