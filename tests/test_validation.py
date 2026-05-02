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

    def test_active_requirement_group_must_exist(self) -> None:
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
                    requirements:
                      activeRequirementGroups:
                        - requirement-group.missing
                      requireActiveRequirementGroupDisposition: false
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            result = validate_workspace(workspace)

        self.assertFalse(result.ok, result.stdout + result.stderr)
        self.assertIn("was not found", result.stdout)

    def test_active_requirement_group_is_incremental_when_disposition_not_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            ensure_workspace_layout(workspace)
            self._write_workspace_requirement_fixture(workspace, require_disposition=False)

            result = validate_workspace(workspace)

        self.assertTrue(result.ok, result.stdout + result.stderr)

    def test_active_requirement_group_is_enforced_when_disposition_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            ensure_workspace_layout(workspace)
            self._write_workspace_requirement_fixture(workspace, require_disposition=True)

            result = validate_workspace(workspace)

        self.assertFalse(result.ok, result.stdout + result.stderr)
        self.assertIn("Satisfy requirement 'company-required-field'", result.stdout)

    def test_requirement_implementation_evidence_satisfies_declared_workspace_group(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            ensure_workspace_layout(workspace)
            self._write_workspace_requirement_fixture(workspace, require_disposition=False)
            (workspace / "configurations" / "requirement-groups" / "requirement-group-company-control.yaml").write_text(
                textwrap.dedent(
                    """
                    schemaVersion: "1.0"
                    id: requirement-group.company-control
                    type: requirement_group
                    name: Company Control
                    description: Workspace-mode control group used by validation tests.
                    catalogStatus: draft
                    owner:
                      team: test
                    activation: workspace
                    appliesTo:
                      - product_service
                    requirements:
                      - id: company-required-field
                        description: Product services must provide company evidence.
                        rationale: Test requirement for workspace-mode evidence.
                        requirementMode: mandatory
                        naAllowed: false
                        canBeSatisfiedBy:
                          - mechanism: architecturalDecision
                            key: missingDecision
                        minimumSatisfactions: 1
                        validAnswerTypes:
                          - architecturalDecision
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            (workspace / "catalog" / "product-services" / "product-service-test-app.yaml").write_text(
                textwrap.dedent(
                    """
                    schemaVersion: "1.0"
                    id: product-service.test.app
                    type: product_service
                    name: Test App
                    product: Test
                    runsOn: host.test
                    catalogStatus: approved
                    lifecycleStatus: maintain
                    requirementGroups:
                      - requirement-group.company-control
                    architecturalDecisions:
                      companyEvidence: Provided by explicit object-level evidence.
                    requirementImplementations:
                      - requirementGroup: requirement-group.company-control
                        requirementId: company-required-field
                        status: satisfied
                        mechanism: architecturalDecision
                        key: companyEvidence
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            result = validate_workspace(workspace)

        self.assertTrue(result.ok, result.stdout + result.stderr)

    def _write_workspace_requirement_fixture(self, workspace: Path, require_disposition: bool) -> None:
        (workspace / ".draft" / "workspace.yaml").write_text(
            textwrap.dedent(
                f"""
                schemaVersion: "1.0"
                workspace:
                  name: incremental-compliance-config
                framework:
                  source: https://github.com/dsackr/draft-framework.git
                  vendoredPath: .draft/framework
                  updatePolicy: explicit
                paths:
                  catalog: catalog
                  configurations: configurations
                requirements:
                  activeRequirementGroups:
                    - requirement-group.company-control
                  requireActiveRequirementGroupDisposition: {str(require_disposition).lower()}
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        group_dir = workspace / "configurations" / "requirement-groups"
        group_dir.mkdir(parents=True, exist_ok=True)
        (group_dir / "requirement-group-company-control.yaml").write_text(
            textwrap.dedent(
                """
                schemaVersion: "1.0"
                id: requirement-group.company-control
                type: requirement_group
                name: Company Control
                description: Workspace-mode control group used by validation tests.
                catalogStatus: draft
                owner:
                  team: test
                activation: workspace
                appliesTo:
                  - product_service
                requirements:
                  - id: company-required-field
                    description: Product services must provide the company required field when disposition is required.
                    rationale: Test requirement for workspace-mode enforcement.
                    requirementMode: mandatory
                    naAllowed: false
                    canBeSatisfiedBy:
                      - mechanism: field
                        key: companyRequiredField
                    minimumSatisfactions: 1
                    validAnswerTypes:
                      - field
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        host_dir = workspace / "catalog" / "host-standards"
        host_dir.mkdir(parents=True, exist_ok=True)
        (host_dir / "host-test.yaml").write_text(
            textwrap.dedent(
                """
                schemaVersion: "1.0"
                id: host.test
                type: host_standard
                name: Test Host
                catalogStatus: stub
                lifecycleStatus: maintain
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        product_dir = workspace / "catalog" / "product-services"
        product_dir.mkdir(parents=True, exist_ok=True)
        (product_dir / "product-service-test-app.yaml").write_text(
            textwrap.dedent(
                """
                schemaVersion: "1.0"
                id: product-service.test.app
                type: product_service
                name: Test App
                product: Test
                runsOn: host.test
                catalogStatus: approved
                lifecycleStatus: maintain
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )

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
                      - capability.compute
                    configurations:
                      - id: enterprise-access
                        name: Enterprise Access
                        description: SAML-authenticated administrative access.
                        capabilities:
                          - capability.authentication
                      - id: managed-health
                        name: Managed Health Visibility
                        description: Publishes target and appliance health.
                        capabilities:
                          - capability.health-welfare-monitoring
                    externalInteractions:
                      - name: Centralized logging
                        capabilities:
                          - capability.log-management
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

    def test_external_interaction_ref_must_resolve(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            host_dir = workspace / "catalog" / "host-standards"
            host_dir.mkdir(parents=True)
            (workspace / "configurations").mkdir()
            (host_dir / "host-test.yaml").write_text(
                textwrap.dedent(
                    """
                    schemaVersion: "1.0"
                    id: host.test
                    type: host_standard
                    name: Test Host
                    catalogStatus: stub
                    lifecycleStatus: maintain
                    externalInteractions:
                      - name: Missing Logging Standard
                        ref: service.missing.logging
                        capabilities:
                          - capability.log-management
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            result = validate_workspace(workspace)

        self.assertFalse(result.ok, result.stdout + result.stderr)
        self.assertIn("externalInteractions[0].ref references unknown object", result.stdout)

    def test_capability_implementation_requires_company_owner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            patch_dir = workspace / "configurations" / "object-patches"
            tech_dir = workspace / "catalog" / "technology-components"
            patch_dir.mkdir(parents=True)
            tech_dir.mkdir(parents=True)
            (tech_dir / "technology-agent-test.yaml").write_text(
                textwrap.dedent(
                    """
                    schemaVersion: "1.0"
                    id: technology.agent.test
                    type: technology_component
                    name: Test Agent
                    vendor: Test Vendor
                    productName: Test Agent
                    productVersion: "1"
                    classification: agent
                    catalogStatus: draft
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            (patch_dir / "patch-security-monitoring.yaml").write_text(
                textwrap.dedent(
                    """
                    schemaVersion: "1.0"
                    id: patch.test.security-monitoring
                    type: object_patch
                    name: Test Security Monitoring Implementation
                    target: capability.security-monitoring
                    catalogStatus: draft
                    lifecycleStatus: maintain
                    patch:
                      implementations:
                        - ref: technology.agent.test
                          lifecycleStatus: invest
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            result = validate_workspace(workspace)

        self.assertFalse(result.ok, result.stdout + result.stderr)
        self.assertIn("Add owner.team before assigning capability implementations", result.stdout)

    def test_capability_implementation_ref_must_be_technology_component(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            patch_dir = workspace / "configurations" / "object-patches"
            service_dir = workspace / "catalog" / "service-standards"
            patch_dir.mkdir(parents=True)
            service_dir.mkdir(parents=True)
            (service_dir / "service-test.yaml").write_text(
                textwrap.dedent(
                    """
                    schemaVersion: "1.0"
                    id: service.test
                    type: service_standard
                    name: Test Service
                    catalogStatus: stub
                    lifecycleStatus: maintain
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            (patch_dir / "patch-security-monitoring.yaml").write_text(
                textwrap.dedent(
                    """
                    schemaVersion: "1.0"
                    id: patch.test.security-monitoring
                    type: object_patch
                    name: Test Security Monitoring Implementation
                    target: capability.security-monitoring
                    catalogStatus: draft
                    lifecycleStatus: maintain
                    patch:
                      owner:
                        team: security-engineering
                      implementations:
                        - ref: service.test
                          lifecycleStatus: invest
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            result = validate_workspace(workspace)

        self.assertFalse(result.ok, result.stdout + result.stderr)
        self.assertIn("capability lifecycle applies only to discrete vendor product versions", result.stdout)


if __name__ == "__main__":
    unittest.main()
