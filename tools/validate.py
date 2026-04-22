#!/usr/bin/env python3
from __future__ import annotations

import sys
import re
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {"tools", "schemas", "docs", "adrs", ".github", ".git"}
VALID_LIFECYCLE = {"pre-invest", "invest", "maintain", "disinvest", "exit"}
VALID_CATALOG_STATUS = {"stub", "draft", "approved"}
TYPE_PREFIX = {
    "abb": "abb.",
    "rbb": "rbb.",
    "aag": "aag.",
    "ard": "ard.",
    "saas_service": "saas.",
    "compliance_framework": "framework.",
    "aag_control_mapping": "aagmap.",
    "product_service": "ps.",
    "reference_architecture": "ra.",
    "software_distribution_manifest": "sdm.",
}
BASE_REQUIRED = ["schemaVersion", "id", "type", "name", "lifecycleStatus", "catalogStatus"]
VALID_ARD_CATEGORY = {"risk", "decision"}
VALID_ARD_STATUS = {"open", "accepted", "mitigated", "resolved"}
VALID_FRAMEWORK_KIND = {"common", "organizational"}
ARD_ID_PATTERN = re.compile(r"^ard\.[a-z0-9-]+\.[0-9]+$")
PS_ID_PATTERN = re.compile(r"^ps\.[a-z0-9-]+\.[a-z0-9-]+$")
APPLIANCE_ABB_ID_PATTERN = re.compile(r"^abb\.appliance\.[a-z0-9-]+$")
SAAS_ID_PATTERN = re.compile(r"^saas\.[a-z0-9-]+$")
FRAMEWORK_ID_PATTERN = re.compile(r"^framework\.[a-z0-9-]+$")
AAG_MAPPING_ID_PATTERN = re.compile(r"^aagmap\.[a-z0-9-]+(?:\.[a-z0-9-]+)+$")
VALID_APPLIANCE_CAPABILITIES = {
    "load-balancing",
    "file-storage",
    "data-persistence",
    "compute",
    "container-orchestration",
    "security",
    "other",
}
VALID_SAAS_CAPABILITIES = {
    "waf",
    "identity",
    "messaging",
    "analytics",
    "monitoring",
    "storage",
    "security",
    "integration",
    "other",
}
VALID_NETWORK_PLACEMENT = {"public-facing", "internal", "vpc-private"}
VALID_PATCHING_OWNER = {"aws-managed", "organization-scheduled", "vendor-managed"}
VALID_SCALING_UNIT_TYPES = {"replicable", "shared"}
VALID_DIAGRAM_TIERS = {"presentation", "application", "data", "utility"}
DECISION_ENUMS = {
    "autoscaling": {"required", "optional", "none"},
    "loadBalancer": {"required", "optional", "none"},
}


def discover_yaml_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*.yaml")):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        files.append(path)
    return files


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("top-level YAML document must be a mapping")
    return data


def is_non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0
    return True


def get_nested_value(node: Any, dotted_key: str) -> Any:
    current = node
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def resolve_aag_requirements(aag_id: str, aags: dict[str, dict[str, Any]], stack: set[str] | None = None) -> list[dict[str, Any]]:
    if aag_id not in aags:
        raise KeyError(f"unknown AAG '{aag_id}'")
    stack = stack or set()
    if aag_id in stack:
        raise ValueError(f"cyclic AAG inheritance detected at '{aag_id}'")
    stack.add(aag_id)
    aag = aags[aag_id]
    requirements: list[dict[str, Any]] = []
    parent_id = aag.get("inherits")
    if parent_id:
        requirements.extend(resolve_aag_requirements(parent_id, aags, stack))
    requirements.extend(aag.get("requirements", []))
    stack.remove(aag_id)
    return requirements


def applicable_aag_ids(obj: dict[str, Any], aags: dict[str, dict[str, Any]]) -> list[str]:
    object_type = obj.get("type")
    applicable: list[str] = []
    for aag_id, aag in aags.items():
        applies_to = aag.get("appliesTo", {})
        if not isinstance(applies_to, dict):
            continue
        if applies_to.get("type") != object_type:
            continue
        if applies_to.get("subtype") and obj.get("subtype") != applies_to.get("subtype"):
            continue
        if object_type == "rbb":
            category = applies_to.get("category")
            service_category = applies_to.get("serviceCategory")
            if category and obj.get("category") != category:
                continue
            if service_category and obj.get("serviceCategory") != service_category:
                continue
        applicable.append(aag_id)
    return sorted(applicable)


def mechanism_description(mechanism: dict[str, Any]) -> str:
    mechanism_type = mechanism.get("mechanism")
    if mechanism_type == "externalInteraction":
        capability = mechanism.get("criteria", {}).get("capability", "unknown")
        return f"externalInteraction(capability={capability})"
    if mechanism_type == "internalComponent":
        role = mechanism.get("criteria", {}).get("role", "unknown")
        return f"internalComponent(role={role})"
    if mechanism_type == "architecturalDecision":
        return f"architecturalDecision({mechanism.get('key', 'unknown')})"
    return str(mechanism_type)


def mechanism_satisfied(obj: dict[str, Any], mechanism: dict[str, Any]) -> bool:
    mechanism_type = mechanism.get("mechanism")
    if mechanism_type == "externalInteraction":
        capability = mechanism.get("criteria", {}).get("capability")
        return any(
            isinstance(interaction, dict) and interaction.get("capability") == capability
            for interaction in obj.get("externalInteractions", [])
        )
    if mechanism_type == "internalComponent":
        role = mechanism.get("criteria", {}).get("role")
        return any(
            isinstance(component, dict) and component.get("role") == role
            for component in obj.get("internalComponents", [])
        )
    if mechanism_type == "architecturalDecision":
        key = mechanism.get("key", "")
        variants = obj.get("variants", {})
        if not isinstance(variants, dict):
            return False
        for variant in variants.values():
            decisions = variant.get("architecturalDecisions", {}) if isinstance(variant, dict) else {}
            value = get_nested_value(decisions, key)
            if is_non_empty(value):
                return True
        return False
    return False


def validate_aag_requirement(obj: dict[str, Any], requirement: dict[str, Any]) -> tuple[bool, str]:
    mechanisms = requirement.get("canBeSatisfiedBy", [])
    minimum = int(requirement.get("minimumSatisfactions", 1))
    satisfied = [mechanism for mechanism in mechanisms if mechanism_satisfied(obj, mechanism)]
    if len(satisfied) >= minimum:
        return True, ""

    requirement_id = requirement.get("id", "unknown")
    mechanism_text = " or ".join(mechanism_description(mechanism) for mechanism in mechanisms)
    if minimum > 1:
        mechanism_text = f"at least {minimum} of {mechanism_text}"
    return (
        False,
        f"[{obj.get('id', 'unknown')}] AAG requirement '{requirement_id}' not satisfied — needs {mechanism_text}",
    )


def validate_base_fields(obj: dict[str, Any], path: Path, failures: list[str]) -> None:
    for field in BASE_REQUIRED:
        if not is_non_empty(obj.get(field)):
            failures.append(f"{path}: missing required field '{field}'")

    object_type = obj.get("type")
    object_id = obj.get("id", "")
    if object_type in TYPE_PREFIX and not str(object_id).startswith(TYPE_PREFIX[object_type]):
        failures.append(
            f"{path}: id '{object_id}' does not match expected prefix '{TYPE_PREFIX[object_type]}' for type '{object_type}'"
        )

    if obj.get("lifecycleStatus") not in VALID_LIFECYCLE:
        failures.append(f"{path}: invalid lifecycleStatus '{obj.get('lifecycleStatus')}'")
    if obj.get("catalogStatus") not in VALID_CATALOG_STATUS:
        failures.append(f"{path}: invalid catalogStatus '{obj.get('catalogStatus')}'")


def validate_architectural_decisions(obj: dict[str, Any], path: Path, failures: list[str]) -> None:
    variants = obj.get("variants", {})
    if not isinstance(variants, dict):
        return

    for variant in variants.values():
        if not isinstance(variant, dict):
            continue
        decisions = variant.get("architecturalDecisions", {})
        if not isinstance(decisions, dict):
            continue

        for key, allowed_values in DECISION_ENUMS.items():
            if key in decisions and decisions[key] not in allowed_values:
                allowed_text = ", ".join(sorted(allowed_values))
                failures.append(
                    f'{path}: [{obj.get("id", "unknown")}] architecturalDecisions.{key} must be one of: '
                    f'{allowed_text} — got "{decisions[key]}"'
                )

        if "minNodes" in decisions and not isinstance(decisions["minNodes"], int):
            failures.append(
                f'{path}: [{obj.get("id", "unknown")}] architecturalDecisions.minNodes must be an integer — '
                f'got "{decisions["minNodes"]}"'
            )


def validate_rbb(obj: dict[str, Any], path: Path, aags: dict[str, dict[str, Any]], catalog_ids: set[str], failures: list[str]) -> None:
    satisfies = obj.get("satisfiesAAG", [])
    if not isinstance(satisfies, list):
        failures.append(f"{path}: satisfiesAAG must be a list")
        return

    variants = obj.get("variants", {})
    if not isinstance(variants, dict) or len(variants) == 0:
        failures.append(
            f"{path}: [{obj.get('id', 'unknown')}] at least one named variant must be present with architecturalDecisions documented"
        )

    for aag_id in satisfies:
        if aag_id not in aags:
            failures.append(f"{path}: referenced AAG '{aag_id}' does not exist")
            continue
        for requirement in resolve_aag_requirements(aag_id, aags):
            valid, message = validate_aag_requirement(obj, requirement)
            if not valid:
                failures.append(f"{path}: {message}")

    if obj.get("category") == "host":
        for field in ("osAbb", "hardwareAbb"):
            ref = obj.get(field)
            if ref and ref not in catalog_ids:
                failures.append(f"{path}: {field} references unknown object '{ref}'")
    if obj.get("category") == "service":
        for field in ("hostRbb", "functionAbb"):
            ref = obj.get(field)
            if ref and ref not in catalog_ids:
                failures.append(f"{path}: {field} references unknown object '{ref}'")

    validate_architectural_decisions(obj, path, failures)


def validate_ra(obj: dict[str, Any], path: Path, aags: dict[str, dict[str, Any]], failures: list[str]) -> None:
    applicable = applicable_aag_ids(obj, aags)
    if "aag.ra" not in applicable:
        return

    object_id = obj.get("id", "unknown")
    if not is_non_empty(obj.get("patternType")):
        failures.append(
            f"{path}: [{object_id}] AAG requirement 'pattern-type' not satisfied — needs architecturalDecision(patternType)"
        )

    required_rbbs = obj.get("requiredRBBs", [])
    if not isinstance(required_rbbs, list) or not required_rbbs:
        failures.append(
            f"{path}: [{object_id}] AAG requirement 'required-rbbs' not satisfied — needs internalComponent(role=web-tier | app-tier | data-tier | cache-tier | messaging-tier)"
        )
    else:
        missing_roles = [entry.get("ref", "unknown") for entry in required_rbbs if not is_non_empty(entry.get("role"))]
        if missing_roles:
            failures.append(
                f"{path}: [{object_id}] AAG requirement 'required-rbbs' not satisfied — every requiredRBB must declare a role (missing on: {', '.join(missing_roles)})"
            )

    if not is_non_empty(obj.get("architecturalDecisions")):
        failures.append(
            f"{path}: [{object_id}] AAG requirement 'variant-coverage' not satisfied — needs architecturalDecision(variants)"
        )
        failures.append(
            f"{path}: [{object_id}] AAG requirement 'pattern-decisions' not satisfied — needs architecturalDecision(architecturalDecisions)"
        )
    elif not isinstance(obj.get("architecturalDecisions"), dict) or not obj["architecturalDecisions"]:
        failures.append(
            f"{path}: [{object_id}] AAG requirement 'pattern-decisions' not satisfied — needs architecturalDecision(architecturalDecisions)"
        )


def validate_sdm(obj: dict[str, Any], path: Path, aags: dict[str, dict[str, Any]], failures: list[str]) -> None:
    applicable = applicable_aag_ids(obj, aags)
    if "aag.sdm" not in applicable:
        return

    object_id = obj.get("id", "unknown")
    if not is_non_empty(obj.get("appliesPattern")):
        failures.append(
            f"{path}: [{object_id}] AAG requirement 'ra-conformance' not satisfied — needs architecturalDecision(appliesPattern)"
        )

    service_groups = obj.get("serviceGroups", [])
    if not isinstance(service_groups, list):
        service_groups = []

    all_intents: list[str] = []
    for group in service_groups:
        if not isinstance(group, dict):
            continue
        for key in ("productServices", "rbbs"):
            entries = group.get(key, [])
            if isinstance(entries, list):
                all_intents.extend(
                    str(entry.get("intent", "")).strip()
                    for entry in entries
                    if isinstance(entry, dict) and is_non_empty(entry.get("intent"))
                )

    if not service_groups:
        failures.append(
            f"{path}: [{object_id}] AAG requirement 'variant-selection' not satisfied — needs internalComponent(variantDeclared=true)"
        )
    elif not obj.get("appliesPattern") and not all_intents:
        failures.append(
            f"{path}: [{object_id}] AAG requirement 'variant-selection' not satisfied — needs internalComponent(variantDeclared=true)"
        )

    architectural_decisions = obj.get("architecturalDecisions", {})
    if not isinstance(architectural_decisions, dict):
        architectural_decisions = {}

    if not is_non_empty(architectural_decisions.get("availabilityRequirement")):
        failures.append(
            f"{path}: [{object_id}] AAG requirement 'availability-requirement' not satisfied — needs architecturalDecision(availabilityRequirement)"
        )

    has_additional_interactions = any(
        isinstance(group, dict)
        and isinstance(group.get("externalInteractions"), list)
        and len(group.get("externalInteractions", [])) > 0
        for group in service_groups
    )
    if not has_additional_interactions and not is_non_empty(architectural_decisions.get("noAdditionalInteractions")):
        failures.append(
            f"{path}: [{object_id}] AAG requirement 'additional-interactions' not satisfied — needs externalInteraction(capability=any) or architecturalDecision(noAdditionalInteractions)"
        )

    if not is_non_empty(architectural_decisions.get("dataClassification")):
        failures.append(
            f"{path}: [{object_id}] AAG requirement 'data-classification' not satisfied — needs architecturalDecision(dataClassification)"
        )


def validate_ard(obj: dict[str, Any], path: Path, failures: list[str], warnings: list[str]) -> None:
    for field in ("id", "name", "category", "status", "description", "affectedComponent", "impact"):
        if not is_non_empty(obj.get(field)):
            failures.append(f"{path}: missing required ARD field '{field}'")

    object_id = obj.get("id", "")
    if object_id and not ARD_ID_PATTERN.match(str(object_id)):
        failures.append(f"{path}: invalid ARD id '{object_id}' (expected format ard.<domain>.<sequence>)")

    category = obj.get("category")
    if category not in VALID_ARD_CATEGORY:
        failures.append(f"{path}: invalid ARD category '{category}'")

    status = obj.get("status")
    if status not in VALID_ARD_STATUS:
        failures.append(f"{path}: invalid ARD status '{status}'")

    if category == "decision" and not is_non_empty(obj.get("decisionRationale")):
        warnings.append(f"{path}: decision ARDs should include decisionRationale")


def validate_appliance_abb(obj: dict[str, Any], path: Path, warnings: list[str], failures: list[str]) -> None:
    for field in ("id", "name", "vendor", "capability", "catalogStatus", "lifecycleStatus"):
        if not is_non_empty(obj.get(field)):
            failures.append(f"{path}: missing required Appliance ABB field '{field}'")

    object_id = obj.get("id", "")
    if object_id and not APPLIANCE_ABB_ID_PATTERN.match(str(object_id)):
        failures.append(f"{path}: invalid Appliance ABB id '{object_id}' (expected format abb.appliance.<vendor>-<product>)")

    if obj.get("capability") and obj.get("capability") not in VALID_APPLIANCE_CAPABILITIES:
        failures.append(f"{path}: invalid Appliance ABB capability '{obj.get('capability')}'")

    network_placement = obj.get("networkPlacement")
    if network_placement and network_placement not in VALID_NETWORK_PLACEMENT:
        failures.append(f"{path}: invalid networkPlacement '{network_placement}'")

    patching_owner = obj.get("patchingOwner")
    if patching_owner and patching_owner not in VALID_PATCHING_OWNER:
        failures.append(f"{path}: invalid patchingOwner '{patching_owner}'")


def validate_saas_service(obj: dict[str, Any], path: Path, warnings: list[str], failures: list[str]) -> None:
    for field in ("id", "name", "vendor", "capability", "catalogStatus", "lifecycleStatus", "dataLeavesInfrastructure"):
        if field not in obj or not is_non_empty(obj.get(field)):
            failures.append(f"{path}: missing required SaaS Service field '{field}'")

    object_id = obj.get("id", "")
    if object_id and not SAAS_ID_PATTERN.match(str(object_id)):
        failures.append(f"{path}: invalid SaaS Service id '{object_id}' (expected format saas.<vendor>-<product>)")

    if obj.get("capability") and obj.get("capability") not in VALID_SAAS_CAPABILITIES:
        failures.append(f"{path}: invalid SaaS Service capability '{obj.get('capability')}'")

    if "dataLeavesInfrastructure" in obj and not isinstance(obj.get("dataLeavesInfrastructure"), bool):
        failures.append(f"{path}: dataLeavesInfrastructure must be true or false")

    if obj.get("dataLeavesInfrastructure") is True and not is_non_empty(obj.get("dpaNotes")):
        warnings.append(f"{path}: SaaS Services with dataLeavesInfrastructure=true should document dpaNotes")


def validate_product_service(obj: dict[str, Any], path: Path, catalog_by_id: dict[str, dict[str, Any]], failures: list[str]) -> None:
    for field in ("id", "name", "product", "runsOn", "catalogStatus", "lifecycleStatus"):
        if not is_non_empty(obj.get(field)):
            failures.append(f"{path}: missing required Product Service field '{field}'")

    object_id = obj.get("id", "")
    if object_id and not PS_ID_PATTERN.match(str(object_id)):
        failures.append(f"{path}: invalid Product Service id '{object_id}' (expected format ps.<product>.<service-name>)")

    runs_on = obj.get("runsOn")
    target = catalog_by_id.get(runs_on) if runs_on else None
    if runs_on and (not target or target.get("type") != "rbb"):
        failures.append(f"{path}: runsOn references unknown RBB '{runs_on}'")

    variants = obj.get("variants", {})
    if not isinstance(variants, dict) or not variants:
        failures.append(f"{path}: [{object_id or 'unknown'}] at least one named variant must be present")


def validate_compliance_framework(obj: dict[str, Any], path: Path, catalog_by_id: dict[str, dict[str, Any]], failures: list[str]) -> None:
    object_id = obj.get("id", "")
    if object_id and not FRAMEWORK_ID_PATTERN.match(str(object_id)):
        failures.append(f"{path}: invalid compliance framework id '{object_id}' (expected format framework.<slug>)")

    framework_kind = obj.get("frameworkKind")
    if framework_kind not in VALID_FRAMEWORK_KIND:
        failures.append(f"{path}: invalid frameworkKind '{framework_kind}'")

    extends = obj.get("extends", [])
    if extends and not isinstance(extends, list):
        failures.append(f"{path}: extends must be a list of framework ids")
    elif isinstance(extends, list):
        for framework_id in extends:
            target = catalog_by_id.get(framework_id)
            if not target or target.get("type") != "compliance_framework":
                failures.append(f"{path}: extends references unknown compliance framework '{framework_id}'")


def validate_aag_control_mapping(
    obj: dict[str, Any],
    path: Path,
    catalog_by_id: dict[str, dict[str, Any]],
    aags: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    object_id = obj.get("id", "")
    if object_id and not AAG_MAPPING_ID_PATTERN.match(str(object_id)):
        failures.append(
            f"{path}: invalid AAG control mapping id '{object_id}' (expected format aagmap.<framework-slug>.<mapping-name>)"
        )

    framework_id = obj.get("framework")
    framework = catalog_by_id.get(framework_id) if framework_id else None
    if not framework or framework.get("type") != "compliance_framework":
        failures.append(f"{path}: framework references unknown compliance framework '{framework_id}'")

    aag_id = obj.get("aagId")
    if not aag_id or aag_id not in aags:
        failures.append(f"{path}: aagId references unknown AAG '{aag_id}'")
        resolved_requirements: list[dict[str, Any]] = []
    else:
        resolved_requirements = resolve_aag_requirements(aag_id, aags)

    requirement_index = {
        requirement.get("id"): requirement
        for requirement in resolved_requirements
        if isinstance(requirement, dict) and is_non_empty(requirement.get("id"))
    }

    mappings = obj.get("requirementMappings", [])
    if not isinstance(mappings, list) or not mappings:
        failures.append(f"{path}: requirementMappings must be a non-empty list")
        return

    for mapping in mappings:
        if not isinstance(mapping, dict):
            failures.append(f"{path}: each requirementMappings entry must be a mapping")
            continue
        requirement_id = mapping.get("requirementId")
        if not is_non_empty(requirement_id):
            failures.append(f"{path}: requirementMappings entries must include requirementId")
            continue
        if requirement_id not in requirement_index:
            failures.append(f"{path}: requirementMappings references unknown requirement '{requirement_id}' for AAG '{aag_id}'")
        controls = mapping.get("controls", [])
        if not isinstance(controls, list) or not controls or not all(is_non_empty(control) for control in controls):
            failures.append(f"{path}: requirementMappings '{requirement_id}' must include a non-empty controls list")


def validate_service_group_structure(
    obj: dict[str, Any],
    path: Path,
    ard_ids: set[str],
    product_service_ids: set[str],
    appliance_abb_ids: set[str],
    saas_service_ids: set[str],
    catalog_by_id: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    scaling_units = obj.get("scalingUnits", [])
    service_groups = obj.get("serviceGroups", [])
    scaling_unit_names: set[str] = set()

    if scaling_units and not isinstance(scaling_units, list):
        failures.append(f"{path}: scalingUnits must be a list")
        scaling_units = []
    if service_groups and not isinstance(service_groups, list):
        failures.append(f"{path}: serviceGroups must be a list")
        service_groups = []

    for scaling_unit in scaling_units:
        if not isinstance(scaling_unit, dict):
            failures.append(f"{path}: each scalingUnits entry must be a mapping")
            continue
        name = scaling_unit.get("name")
        if not is_non_empty(name):
            failures.append(f"{path}: scalingUnits entries must include name")
            continue
        scaling_unit_names.add(str(name))
        unit_type = scaling_unit.get("type")
        if unit_type not in VALID_SCALING_UNIT_TYPES:
            failures.append(f"{path}: scalingUnit '{name}' has invalid type '{unit_type}'")
        if unit_type == "replicable" and not isinstance(scaling_unit.get("instanceCount"), int):
            failures.append(f"{path}: scalingUnit '{name}' type replicable requires integer instanceCount")

    service_group_names: set[str] = set()
    for group in service_groups:
        if not isinstance(group, dict):
            failures.append(f"{path}: each serviceGroups entry must be a mapping")
            continue
        name = group.get("name")
        deployment_target = group.get("deploymentTarget")
        if not is_non_empty(name):
            failures.append(f"{path}: serviceGroups entries must include name")
            continue
        service_group_names.add(str(name))
        if not is_non_empty(deployment_target):
            failures.append(f"{path}: serviceGroup '{name}' missing deploymentTarget")

    for group in service_groups:
        if not isinstance(group, dict) or not is_non_empty(group.get("name")):
            continue
        group_name = str(group["name"])
        scaling_unit_name = group.get("scalingUnit")
        if scaling_unit_name and scaling_unit_name not in scaling_unit_names:
            failures.append(f"{path}: serviceGroup '{group_name}' references unknown scalingUnit '{scaling_unit_name}'")

        for entry in group.get("productServices", []) or []:
            if not isinstance(entry, dict):
                continue
            ref = entry.get("ref")
            if ref and ref not in product_service_ids:
                failures.append(f"{path}: serviceGroup '{group_name}' references unknown Product Service '{ref}'")
            diagram_tier = entry.get("diagramTier")
            if diagram_tier not in VALID_DIAGRAM_TIERS:
                failures.append(
                    f"{path}: serviceGroup '{group_name}' Product Service '{ref}' must set diagramTier to one of {sorted(VALID_DIAGRAM_TIERS)}"
                )
            risk_ref = entry.get("riskRef")
            if risk_ref and risk_ref not in ard_ids:
                failures.append(f"{path}: serviceGroup '{group_name}' Product Service '{ref}' references unknown ARD '{risk_ref}'")
            intent = entry.get("intent")
            if intent and intent not in {"ha", "sa"}:
                failures.append(f"{path}: serviceGroup '{group_name}' Product Service '{ref}' has invalid intent '{intent}'")

        for entry in group.get("rbbs", []) or []:
            if not isinstance(entry, dict):
                continue
            ref = entry.get("ref")
            target = catalog_by_id.get(ref) if ref else None
            if ref and (not target or target.get("type") != "rbb"):
                failures.append(f"{path}: serviceGroup '{group_name}' references unknown RBB '{ref}'")
            diagram_tier = entry.get("diagramTier")
            if diagram_tier not in VALID_DIAGRAM_TIERS:
                failures.append(
                    f"{path}: serviceGroup '{group_name}' RBB '{ref}' must set diagramTier to one of {sorted(VALID_DIAGRAM_TIERS)}"
                )
            risk_ref = entry.get("riskRef")
            if risk_ref and risk_ref not in ard_ids:
                failures.append(f"{path}: serviceGroup '{group_name}' RBB '{ref}' references unknown ARD '{risk_ref}'")
            intent = entry.get("intent")
            if intent and intent not in {"ha", "sa"}:
                failures.append(f"{path}: serviceGroup '{group_name}' RBB '{ref}' has invalid intent '{intent}'")

        for entry in group.get("applianceAbbs", []) or []:
            if not isinstance(entry, dict):
                continue
            ref = entry.get("ref")
            if ref and ref not in appliance_abb_ids:
                failures.append(f"{path}: serviceGroup '{group_name}' references unknown Appliance ABB '{ref}'")

        for entry in group.get("saasServices", []) or []:
            if not isinstance(entry, dict):
                continue
            ref = entry.get("ref")
            if ref and ref not in saas_service_ids:
                failures.append(f"{path}: serviceGroup '{group_name}' references unknown SaaS Service '{ref}'")

        for interaction in group.get("externalInteractions", []) or []:
            if not isinstance(interaction, dict):
                continue
            if interaction.get("type", "external") == "internal":
                ref = interaction.get("ref")
                if not ref or ref not in service_group_names:
                    failures.append(
                        f"{path}: serviceGroup '{group_name}' internal interaction '{interaction.get('name', 'unnamed')}' must reference a valid service group name"
                    )


def validate_sdm_refs(
    obj: dict[str, Any],
    path: Path,
    ard_ids: set[str],
    product_service_ids: set[str],
    appliance_abb_ids: set[str],
    saas_service_ids: set[str],
    catalog_by_id: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    for risk in obj.get("architectureRisksAndDecisions", []):
        if not isinstance(risk, dict):
            continue
        ref = risk.get("ref")
        if ref and ref not in ard_ids:
            failures.append(f"{path}: architectureRisksAndDecisions references unknown ARD '{ref}'")

    validate_service_group_structure(
        obj,
        path,
        ard_ids,
        product_service_ids,
        appliance_abb_ids,
        saas_service_ids,
        catalog_by_id,
        failures,
    )


def main() -> int:
    files = discover_yaml_files(REPO_ROOT)
    objects: dict[Path, dict[str, Any]] = {}
    failures: list[str] = []
    warnings: list[str] = []

    for path in files:
        try:
            objects[path] = load_yaml(path)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{path}: failed to parse YAML ({exc})")

    catalog_by_id = {
        obj["id"]: obj
        for obj in objects.values()
        if isinstance(obj, dict) and is_non_empty(obj.get("id"))
    }
    aags = {object_id: obj for object_id, obj in catalog_by_id.items() if obj.get("type") == "aag"}
    ard_ids = {object_id for object_id, obj in catalog_by_id.items() if obj.get("type") == "ard"}
    product_service_ids = {object_id for object_id, obj in catalog_by_id.items() if obj.get("type") == "product_service"}
    appliance_abb_ids = {
        object_id for object_id, obj in catalog_by_id.items() if obj.get("type") == "abb" and obj.get("subtype") == "appliance"
    }
    saas_service_ids = {object_id for object_id, obj in catalog_by_id.items() if obj.get("type") == "saas_service"}
    catalog_ids = set(catalog_by_id.keys())

    for path, obj in objects.items():
        validate_base_fields(obj, path, failures)
        if obj.get("type") == "ard":
            validate_ard(obj, path, failures, warnings)
        if obj.get("type") == "abb" and obj.get("subtype") == "appliance":
            validate_appliance_abb(obj, path, warnings, failures)
        if obj.get("type") == "saas_service":
            validate_saas_service(obj, path, warnings, failures)
        if obj.get("type") == "product_service":
            validate_product_service(obj, path, catalog_by_id, failures)
        if obj.get("type") == "compliance_framework":
            validate_compliance_framework(obj, path, catalog_by_id, failures)
        if obj.get("type") == "aag_control_mapping":
            validate_aag_control_mapping(obj, path, catalog_by_id, aags, failures)
        if obj.get("type") == "rbb":
            validate_rbb(obj, path, aags, catalog_ids, failures)
        if obj.get("type") == "reference_architecture":
            validate_ra(obj, path, aags, failures)
        if obj.get("type") == "software_distribution_manifest":
            validate_sdm(obj, path, aags, failures)
            validate_sdm_refs(obj, path, ard_ids, product_service_ids, appliance_abb_ids, saas_service_ids, catalog_by_id, failures)

    failing_paths = {entry.split(":", 1)[0] for entry in failures}
    for path in files:
        if str(path) in failing_paths:
            print(f"FAIL {path.relative_to(REPO_ROOT)}")
        else:
            print(f"PASS {path.relative_to(REPO_ROOT)}")

    if failures:
        print("")
        print("Validation failures:")
        for failure in failures:
            print(f"- {failure}")
        if warnings:
            print("")
            print("Validation warnings:")
            for warning in warnings:
                print(f"- {warning}")
        return 1

    if warnings:
        print("")
        print("Validation warnings:")
        for warning in warnings:
            print(f"- {warning}")

    print("")
    print(f"Validated {len(files)} catalog files successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
