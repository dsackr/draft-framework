from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from draft_table.paths import REPO_ROOT
from draft_table.repo import ensure_workspace_layout
from draft_table.validation import build_validate_command, validate_workspace


class ValidationTests(unittest.TestCase):
    def test_build_validate_command_targets_framework_tool(self) -> None:
        command = build_validate_command(REPO_ROOT / "examples")

        self.assertIn("framework/tools/validate.py", command[1])
        self.assertEqual(command[-2], "--workspace")
        self.assertEqual(Path(command[-1]), REPO_ROOT / "examples")

    def test_validate_examples_workspace(self) -> None:
        result = validate_workspace(REPO_ROOT / "examples")

        self.assertTrue(result.ok, result.stdout + result.stderr)
        self.assertIn("Validated", result.stdout)

    def test_build_validate_command_prefers_vendored_framework(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            ensure_workspace_layout(workspace)

            command = build_validate_command(workspace)

        self.assertIn(".draft/framework/tools/validate.py", command[1])

    def test_validate_workspace_uses_vendored_framework(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            ensure_workspace_layout(workspace)

            result = validate_workspace(workspace)

        self.assertTrue(result.ok, result.stdout + result.stderr)

    def test_active_control_profile_must_exist(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            ensure_workspace_layout(workspace)
            (workspace / ".draft" / "workspace.yaml").write_text(
                textwrap.dedent(
                    """
                    schemaVersion: "1.0"
                    workspace:
                      name: bad-compliance-config
                    framework:
                      source: https://github.com/dsackr/draft-framework.git
                      vendoredPath: .draft/framework
                      updatePolicy: explicit
                    paths:
                      catalog: catalog
                      configurations: configurations
                    compliance:
                      activeControlEnforcementProfiles:
                        - control-enforcement.missing
                      requireActiveProfileDisposition: false
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            result = validate_workspace(workspace)

        self.assertFalse(result.ok, result.stdout + result.stderr)
        self.assertIn("activeControlEnforcementProfiles references unknown", result.stdout)

    def test_appliance_component_satisfies_service_like_checklist_capabilities_directly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            catalog = workspace / "catalog" / "appliance-components"
            catalog.mkdir(parents=True)
            (workspace / "configurations").mkdir()
            (catalog / "appliance-aws-alb.yaml").write_text(
                textwrap.dedent(
                    """
                    schemaVersion: "1.0"
                    id: appliance.aws-alb
                    type: appliance_component
                    name: AWS Application Load Balancer
                    vendor: Amazon Web Services
                    productName: Application Load Balancer
                    productVersion: managed
                    classification: software
                    catalogStatus: draft
                    lifecycleStatus: invest
                    capabilities:
                      - compute
                    configurations:
                      - id: enterprise-access
                        name: Enterprise Access
                        description: SAML-authenticated administrative access.
                        capabilities:
                          - authentication
                      - id: managed-health
                        name: Managed Health Visibility
                        description: Publishes target and appliance health.
                        capabilities:
                          - health-welfare-monitoring
                    externalInteractions:
                      - name: Centralized logging
                        capabilities:
                          - log-management
                    networkPlacement: public-facing
                    patchingOwner: aws-managed
                    complianceCerts: []
                    architecturalDecisions:
                      resilienceModel: Managed multi-AZ control plane.
                      configurableSurface: Listeners, rules, certificates, and target groups.
                      failureDomain: Shared ingress dependency for the protected application path.
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            result = validate_workspace(workspace)

        self.assertTrue(result.ok, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
