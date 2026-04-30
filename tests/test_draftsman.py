from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from draft_table.config import save_config
from draft_table.draftsman import DraftsmanEngine, parse_provider_response, public_proposal, safe_workspace_path
from draft_table.paths import REPO_ROOT
from draft_table.sessions import DraftsmanSessionStore


class DraftsmanTests(unittest.TestCase):
    def test_answers_framework_question_without_provider(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.yaml"
            save_config({"framework_repo_path": str(REPO_ROOT)}, config_path)
            engine = DraftsmanEngine(config_path, DraftsmanSessionStore(Path(directory) / "sessions"))

            response = engine.chat("What is an ABB?")

        self.assertFalse(response.provider_used)
        self.assertIn("Architecture Building Block", response.answer)
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
                "artifactType": "RBB",
                "name": "Standard Host",
                "summary": "Creates a standard host.",
                "path": "catalog/rbbs/rbb-host-standard.yaml",
                "content": "schemaVersion: '1.0'",
            }
        )

        self.assertNotIn("content", public)
        self.assertNotIn("path", public)
        self.assertEqual(public["name"], "Standard Host")

    def test_parse_provider_response_extracts_json(self) -> None:
        raw = "Here is the result:\n" + json.dumps({"answer": "Done", "questions": [], "proposals": []})

        parsed = parse_provider_response(raw)

        self.assertEqual(parsed["answer"], "Done")

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
                "'proposals':[{'id':'p1','action':'create','artifactType':'RBB','name':'Standard Host',"
                "'summary':'A reusable host pattern.','path':'catalog/rbbs/rbb-host-standard.yaml',"
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
