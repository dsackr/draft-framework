#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import sys
import re
from pathlib import Path
from typing import Any

import yaml


FRAMEWORK_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = FRAMEWORK_ROOT.parent
SCHEMA_ROOT = FRAMEWORK_ROOT / "schemas"
BASE_CONFIGURATION_ROOT = FRAMEWORK_ROOT / "configurations"
DEFAULT_WORKSPACE_ROOT = REPO_ROOT / "examples"
SKIP_DIRS = {"tools", "schemas", "docs", "adrs", ".github", ".git", ".draft"}
VALID_DIAGRAM_TIERS = {"presentation", "application", "data", "utility"}
VALID_TECHNOLOGY_COMPONENT_CLASSIFICATIONS = {"operating-system", "compute-platform", "software", "agent"}

def load_valid_capabilities(search_roots: list[Path] | None = None) -> set[str]:
    # Fallback to current concerns to allow transition
    capabilities = {
        "authentication",
        "log-management",
        "health-welfare-monitoring",
        "security-monitoring",
        "patch-management",
        "secrets-management",
        "test-authoring",
        "test-execution",
        "quality-gates",
        "performance-testing"
    }
    roots = search_roots or [BASE_CONFIGURATION_ROOT]
    for root in roots:
        domain_dir = root / "domains"
        if not domain_dir.exists():
            continue
        for domain_file in domain_dir.glob("*.yaml"):
            with domain_file.open("r", encoding="utf-8") as f:
                try:
                    data = yaml.safe_load(f)
                    if data and "capabilities" in data:
                        for cap in data["capabilities"]:
                            if isinstance(cap, dict) and "id" in cap:
                                capabilities.add(cap["id"])
                except Exception:
                    continue
    return capabilities

VALID_CAPABILITIES = load_valid_capabilities()
VALID_DEPLOYMENT_QUALITIES = {"availability", "scalability", "recoverability"}
DECISION_ENUMS = {
    "autoscaling": {"required", "optional", "none"},
    "loadBalancer": {"required", "optional", "none"},
}

TYPE_CHECKERS = {
    "bool": bool,
    "list": list,
    "dict": dict,
    "str": str,
    "int": int,
}

VALID_CONTROL_SCOPES = {
    "host_standard",
    "service_standard",
    "database_standard",
    "product_service",
    "paas_service_standard",
    "saas_service_standard",
    "reference_architecture",
    "software_deployment_pattern",
    "appliance_component",
}

VALID_CONTROL_ANSWER_TYPES = {
    "technologyComponent",
    "technologyComponentConfiguration",
    "deploymentConfiguration",
    "externalInteraction",
    "architecturalDecision",
    "field",
}
VALID_CONTROL_REQUIREMENT_MODES = {"mandatory", "conditional"}
STANDARD_TYPES = {
    "host_standard",
    "service_standard",
    "database_standard",
    "product_service",
    "paas_service_standard",
    "saas_service_standard",
}


def discover_yaml_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*.yaml")):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        files.append(path)
    return files


def workspace_yaml_roots(workspace_root: Path) -> list[Path]:
    roots = [BASE_CONFIGURATION_ROOT]
    workspace_config = workspace_root / "configurations"
    workspace_catalog = workspace_root / "catalog"
    if workspace_config.exists():
        roots.append(workspace_config)
    if workspace_catalog.exists():
        roots.append(workspace_catalog)
    elif workspace_root.exists() and workspace_root.name == "catalog":
        roots.append(workspace_root)
    return roots


def discover_workspace_yaml_files(workspace_root: Path) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for root in workspace_yaml_roots(workspace_root):
        for path in discover_yaml_files(root):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(path)
    return sorted(files)


def display_path(path: Path) -> str:
    for root in (REPO_ROOT, Path.cwd()):
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            continue
    return path.as_posix()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate DRAFT framework and workspace YAML.")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=DEFAULT_WORKSPACE_ROOT,
        help="Workspace root containing catalog/ and configurations/. Defaults to examples/.",
    )
    return parser.parse_args(argv)


def deep_merge(base: Any, patch: Any) -> Any:
    if isinstance(base, dict) and isinstance(patch, dict):
        merged = copy.deepcopy(base)
        for key, value in patch.items():
            if key in {"id", "type"}:
                continue
            merged[key] = deep_merge(merged.get(key), value)
        return merged
    return copy.deepcopy(patch)


def apply_object_patches(objects: dict[Path, dict[str, Any]], failures: list[str]) -> dict[Path, dict[str, Any]]:
    objects_by_id = {
        str(obj["id"]): obj
        for obj in objects.values()
        if isinstance(obj, dict) and is_non_empty(obj.get("id"))
    }
    patched_by_id: dict[str, dict[str, Any]] = {}
    for path, obj in objects.items():
        if obj.get("type") != "object_patch":
            continue
        target_id = obj.get("target")
        patch = obj.get("patch")
        if not is_non_empty(target_id):
            failures.append(f"{path}: object_patch must declare target")
            continue
        if not isinstance(patch, dict):
            failures.append(f"{path}: object_patch patch must be a mapping")
            continue
        target = patched_by_id.get(str(target_id)) or objects_by_id.get(str(target_id))
        if not target:
            failures.append(f"{path}: object_patch target '{target_id}' does not exist")
            continue
        patched_by_id[str(target_id)] = deep_merge(target, patch)

    if not patched_by_id:
        return objects

    patched_objects = dict(objects)
    for path, obj in objects.items():
        object_id = obj.get("id")
        if object_id in patched_by_id:
            patched_objects[path] = patched_by_id[str(object_id)]
    return patched_objects


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("top-level YAML document must be a mapping")
    return data


def load_schemas(root: Path) -> list[dict[str, Any]]:
    schemas: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.yaml")):
        data = load_yaml(path)
        data["_schema_path"] = path
        schemas.append(data)
    return schemas


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


def schema_specificity(schema: dict[str, Any]) -> int:
    return sum(1 for key in ("subtype", "category", "serviceCategory") if is_non_empty(schema.get(key)))


def select_schema(obj: dict[str, Any], schemas: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates: list[dict[str, Any]] = []
    for schema in schemas:
        if schema.get("type") != obj.get("type"):
            continue
        if is_non_empty(schema.get("subtype")) and schema.get("subtype") != obj.get("subtype"):
            continue
        if is_non_empty(schema.get("category")) and schema.get("category") != obj.get("category"):
            continue
        if is_non_empty(schema.get("serviceCategory")) and schema.get("serviceCategory") != obj.get("serviceCategory"):
            continue
        candidates.append(schema)
    if not candidates:
        return None
    return sorted(candidates, key=schema_specificity, reverse=True)[0]


def matches_conditions(obj: dict[str, Any], conditions: dict[str, Any]) -> bool:
    for key, expected in conditions.items():
        if obj.get(key) != expected:
            return False
    return True


def validate_schema_section(
    node: dict[str, Any],
    schema: dict[str, Any],
    context: str,
    failures: list[str],
) -> None:
    for field in schema.get("requiredFields", []):
        if not is_non_empty(node.get(field)):
            failures.append(f"{context}: missing required field '{field}'")

    id_pattern = schema.get("idPattern")
    if id_pattern and is_non_empty(node.get("id")) and not re.match(str(id_pattern), str(node.get("id"))):
        failures.append(f"{context}: invalid id '{node.get('id')}'")

    for field, allowed_values in (schema.get("enumFields") or {}).items():
        value = node.get(field)
        if value is None or value == "":
            continue
        if value not in allowed_values:
            failures.append(f"{context}: invalid {field} '{value}'")

    for field, expected_type in (schema.get("fieldTypes") or {}).items():
        if field not in node or node.get(field) is None:
            continue
        checker = TYPE_CHECKERS.get(str(expected_type))
        if checker and not isinstance(node.get(field), checker):
            failures.append(f"{context}: field '{field}' must be of type {expected_type}")

    for field, allowed_values in (schema.get("enumListFields") or {}).items():
        value = node.get(field)
        if value is None:
            continue
        if not isinstance(value, list):
            failures.append(f"{context}: field '{field}' must be a list")
            continue
        invalid = [item for item in value if item not in allowed_values]
        if invalid:
            failures.append(f"{context}: invalid {field} values {invalid}")

    for conditional in schema.get("conditionalRequired", []) or []:
        when = conditional.get("when", {})
        required = conditional.get("require", [])
        if isinstance(when, dict) and matches_conditions(node, when):
            for field in required:
                if not is_non_empty(node.get(field)):
                    failures.append(f"{context}: missing required field '{field}'")

    for field, section_name in (schema.get("collectionSchemas") or {}).items():
        if field not in node or node.get(field) is None:
            continue
        value = node.get(field)
        if not isinstance(value, list):
            failures.append(f"{context}: field '{field}' must be a list")
            continue
        child_schema = schema.get(section_name)
        if not isinstance(child_schema, dict):
            continue
        for index, item in enumerate(value):
            if not isinstance(item, dict):
                failures.append(f"{context}: field '{field}[{index}]' must be a mapping")
                continue
            validate_schema_section(item, child_schema, f"{context}: {field}[{index}]", failures)


def resolve_checklist_requirements(odc_id: str, odcs: dict[str, dict[str, Any]], stack: set[str] | None = None) -> list[dict[str, Any]]:
    if odc_id not in odcs:
        raise KeyError(f"unknown Definition Checklist '{odc_id}'")
    stack = stack or set()
    if odc_id in stack:
        raise ValueError(f"cyclic Definition Checklist inheritance detected at '{odc_id}'")
    stack.add(odc_id)
    odc = odcs[odc_id]
    requirements: list[dict[str, Any]] = []
    parent_id = odc.get("inherits")
    if parent_id:
        requirements.extend(resolve_checklist_requirements(parent_id, odcs, stack))
    requirements.extend(odc.get("requirements", []))
    stack.remove(odc_id)
    return requirements


def scope_to_checklist_id(scope: str) -> str | None:
    return {
        "host_standard": "checklist.host-standard",
        "service_standard": "checklist.service-standard",
        "database_standard": "checklist.database-standard",
        "paas_service_standard": "checklist.paas-service-standard",
        "saas_service_standard": "checklist.saas-service-standard",
        "reference_architecture": "checklist.reference-architecture",
        "software_deployment_pattern": "checklist.software-deployment-pattern",
        "appliance_component": "checklist.appliance-component",
        "drafting_session": "checklist.drafting-session",
    }.get(scope)


def applicable_checklist_ids(obj: dict[str, Any], odcs: dict[str, dict[str, Any]]) -> list[str]:
    object_type = obj.get("type")
    applicable: list[str] = []
    for odc_id, odc in odcs.items():
        applies_to = odc.get("appliesTo", {})
        if not isinstance(applies_to, dict):
            continue
        if applies_to.get("type") != object_type:
            continue
        if applies_to.get("subtype") and obj.get("subtype") != applies_to.get("subtype"):
            continue
        if object_type == "host_standard" and odc_id == "checklist.host-standard":
            object_id = str(obj.get("id", ""))
            if object_id.startswith("host.serverless.") or object_id.startswith("host.container."):
                continue
        applicable.append(odc_id)
    return sorted(applicable)


def mechanism_description(mechanism: dict[str, Any]) -> str:
    mechanism_type = mechanism.get("mechanism")
    if mechanism_type == "field":
        field = mechanism.get("key", "unknown")
        equals = mechanism.get("equals")
        return f"field({field}={equals})" if equals is not None else f"field({field})"
    if mechanism_type == "externalInteraction":
        capability = mechanism.get("criteria", {}).get("capability", "unknown")
        return f"externalInteraction(capability={capability})"
    if mechanism_type == "internalComponent":
        criteria = mechanism.get("criteria", {})
        concern = criteria.get("concern")
        role = criteria.get("role")
        if concern:
            return f"internalComponent(concern={concern})"
        return f"internalComponent(role={role or 'unknown'})"
    if mechanism_type == "technologyComponentConfiguration":
        capability = mechanism.get("criteria", {}).get("capability") or mechanism.get("criteria", {}).get("concern", "unknown")
        return f"technologyComponentConfiguration(capability={capability})"
    if mechanism_type == "deploymentConfiguration":
        quality = mechanism.get("criteria", {}).get("quality", "unknown")
        return f"deploymentConfiguration(quality={quality})"
    if mechanism_type == "architecturalDecision":
        return f"architecturalDecision({mechanism.get('key', 'unknown')})"
    return str(mechanism_type)


def referenced_technology_components(obj: dict[str, Any], catalog_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    refs: list[str] = []
    for field in ("operatingSystemComponent", "computePlatformComponent", "primaryTechnologyComponent"):
        ref = obj.get(field)
        if is_non_empty(ref):
            refs.append(str(ref))
    for component in obj.get("internalComponents", []) or []:
        if isinstance(component, dict) and is_non_empty(component.get("ref")):
            refs.append(str(component["ref"]))

    resolved: list[dict[str, Any]] = []
    seen: set[str] = set()
    if obj.get("type") in {"technology_component", "appliance_component"} and is_non_empty(obj.get("id")):
        resolved.append(obj)
        seen.add(str(obj["id"]))
    for ref in refs:
        if ref in seen:
            continue
        seen.add(ref)
        target = catalog_by_id.get(ref)
        if target and target.get("type") in {"technology_component", "appliance_component"}:
            resolved.append(target)
    return resolved


def mechanism_satisfied(obj: dict[str, Any], mechanism: dict[str, Any], catalog_by_id: dict[str, dict[str, Any]]) -> bool:
    mechanism_type = mechanism.get("mechanism")
    if mechanism_type == "field":
        key = mechanism.get("key", "")
        if key not in obj:
            return False
        value = obj.get(key)
        if "equals" in mechanism:
            return value == mechanism.get("equals")
        if mechanism.get("allowEmpty") is True:
            return value is not None
        return is_non_empty(value)
    if mechanism_type == "externalInteraction":
        capability = mechanism.get("criteria", {}).get("capability")
        # Check if any interaction has the required capability in its capabilities list
        for interaction in obj.get("externalInteractions", []) or []:
            if not isinstance(interaction, dict):
                continue
            caps = interaction.get("capabilities", [])
            if isinstance(caps, list) and capability in caps:
                return True
        return False
    if mechanism_type == "internalComponent":
        criteria = mechanism.get("criteria", {})
        capability = criteria.get("capability") or criteria.get("concern")
        role = criteria.get("role")
        classification = criteria.get("classification")
        if capability:
            for abb in referenced_technology_components(obj, catalog_by_id):
                if classification and abb.get("classification") != classification:
                    continue
                caps = abb.get("capabilities", [])
                if isinstance(caps, list) and capability in caps:
                    return True
            return False
        return any(
            isinstance(component, dict) and component.get("role") == role
            for component in obj.get("internalComponents", [])
        )
    if mechanism_type == "technologyComponentConfiguration":
        capability = mechanism.get("criteria", {}).get("capability") or mechanism.get("criteria", {}).get("concern")
        classification = mechanism.get("criteria", {}).get("classification")
        for abb in referenced_technology_components(obj, catalog_by_id):
            if classification and abb.get("classification") != classification:
                continue
            configurations = abb.get("configurations", [])
            if not isinstance(configurations, list):
                continue
            for configuration in configurations:
                if not isinstance(configuration, dict):
                    continue
                caps = configuration.get("capabilities", [])
                if isinstance(caps, list) and capability in caps:
                    return True
        return False
    if mechanism_type == "architecturalDecision":
        key = mechanism.get("key", "")
        decisions = obj.get("architecturalDecisions", {})
        if isinstance(decisions, dict):
            value = get_nested_value(decisions, key)
            if is_non_empty(value):
                return True
        return False
    if mechanism_type == "deploymentConfiguration":
        quality = mechanism.get("criteria", {}).get("quality")
        configurations = obj.get("deploymentConfigurations", [])
        if not isinstance(configurations, list):
            return False
        for configuration in configurations:
            if not isinstance(configuration, dict):
                continue
            qualities = configuration.get("addressesQualities", [])
            if isinstance(qualities, list) and quality in qualities:
                return True
        return False
    return False


def validate_checklist_requirement(
    obj: dict[str, Any],
    requirement: dict[str, Any],
    catalog_by_id: dict[str, dict[str, Any]],
) -> tuple[bool, str]:
    mechanisms = requirement.get("canBeSatisfiedBy", [])
    minimum = int(requirement.get("minimumSatisfactions", 1))
    satisfied = [mechanism for mechanism in mechanisms if mechanism_satisfied(obj, mechanism, catalog_by_id)]
    if len(satisfied) >= minimum:
        return True, ""

    requirement_id = requirement.get("id", "unknown")
    mechanism_text = " or ".join(mechanism_description(mechanism) for mechanism in mechanisms)
    if minimum > 1:
        mechanism_text = f"at least {minimum} of {mechanism_text}"
    return (
        False,
        f"[{obj.get('id', 'unknown')}] Definition Checklist requirement '{requirement_id}' not satisfied — needs {mechanism_text}",
    )


def validate_against_schema(obj: dict[str, Any], path: Path, schemas: list[dict[str, Any]], failures: list[str]) -> None:
    schema = select_schema(obj, schemas)
    if schema is None:
        failures.append(f"{path}: no schema found for type '{obj.get('type')}'")
        return
    validate_schema_section(obj, schema, str(path), failures)


def validate_architectural_decisions(obj: dict[str, Any], path: Path, failures: list[str]) -> None:
    decision_sets: list[dict[str, Any]] = []
    direct_decisions = obj.get("architecturalDecisions", {})
    if isinstance(direct_decisions, dict) and direct_decisions:
        decision_sets.append(direct_decisions)

    for decisions in decision_sets:
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


def validate_component(
    obj: dict[str, Any],
    path: Path,
    odcs: dict[str, dict[str, Any]],
    catalog_by_id: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    classification = obj.get("classification")
    if classification not in VALID_TECHNOLOGY_COMPONENT_CLASSIFICATIONS:
        failures.append(
            f"{path}: Technology Component classification must be one of {sorted(VALID_TECHNOLOGY_COMPONENT_CLASSIFICATIONS)}"
        )
    capabilities = obj.get("capabilities", [])
    if capabilities is not None:
        if not isinstance(capabilities, list):
            failures.append(f"{path}: capabilities must be a list")
        else:
            invalid = [cap for cap in capabilities if cap not in VALID_CAPABILITIES]
            if invalid:
                failures.append(
                    f"{path}: capabilities contains invalid ids {invalid} — expected values from {sorted(VALID_CAPABILITIES)}"
                )
    configurations = obj.get("configurations", [])
    if configurations is not None:
        if not isinstance(configurations, list):
            failures.append(f"{path}: configurations must be a list")
        else:
            for index, configuration in enumerate(configurations):
                if not isinstance(configuration, dict):
                    failures.append(f"{path}: configurations[{index}] must be a mapping")
                    continue
                config_caps = configuration.get("capabilities", [])
                if not isinstance(config_caps, list):
                    failures.append(f"{path}: configurations[{index}].capabilities must be a list")
                    continue
                invalid = [cap for cap in config_caps if cap not in VALID_CAPABILITIES]
                if invalid:
                    failures.append(
                        f"{path}: configurations[{index}].capabilities contains invalid ids {invalid} — expected values from {sorted(VALID_CAPABILITIES)}"
                    )

    applicable = applicable_checklist_ids(obj, odcs)
    for odc_id in applicable:
        if odc_id not in odcs:
            failures.append(f"{path}: referenced Definition Checklist '{odc_id}' does not exist")
            continue
        for requirement in resolve_checklist_requirements(odc_id, odcs):
            valid, message = validate_checklist_requirement(obj, requirement, catalog_by_id)
            if not valid:
                failures.append(f"{path}: {message}")
    validate_control_implementations(obj, path, catalog_by_id, failures)


def agent_interaction_exception(obj: dict[str, Any], abb_id: str) -> bool:
    decisions = obj.get("architecturalDecisions", {})
    if not isinstance(decisions, dict):
        return False
    exceptions = decisions.get("agentInteractionExceptions")
    if isinstance(exceptions, list):
        return abb_id in exceptions
    if isinstance(exceptions, dict):
        value = exceptions.get(abb_id)
        return is_non_empty(value) or value is True
    return False


def has_enabled_external_interaction(obj: dict[str, Any], abb_id: str) -> bool:
    interactions = obj.get("externalInteractions", [])
    if not isinstance(interactions, list):
        return False
    return any(
        isinstance(interaction, dict) and interaction.get("enabledBy") == abb_id
        for interaction in interactions
    )


def validate_classified_component_refs(
    obj: dict[str, Any],
    path: Path,
    catalog_by_id: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    def validate_ref(field: str, expected_classification: str | None = None) -> None:
        ref = obj.get(field)
        if not ref:
            return
        target = catalog_by_id.get(ref)
        if not target or target.get("type") != "technology_component":
            return
        target_classification = target.get("classification")
        if expected_classification and target_classification != expected_classification:
            failures.append(
                f"{path}: {field} must reference a Technology Component classified as '{expected_classification}' — got '{target_classification or 'unknown'}'"
            )

    validate_ref("operatingSystemComponent", "operating-system")
    validate_ref("computePlatformComponent", "compute-platform")

    function_ref = obj.get("primaryTechnologyComponent")
    if function_ref:
        target = catalog_by_id.get(function_ref)
        if target and target.get("type") == "technology_component":
            classification = target.get("classification")
            if classification not in {"software", "agent"}:
                failures.append(
                    f"{path}: primaryTechnologyComponent must reference a Technology Component classified as 'software' or 'agent' — got '{classification or 'unknown'}'"
                )

    components = obj.get("internalComponents", [])
    if not isinstance(components, list):
        return
    for component in components:
        if not isinstance(component, dict):
            continue
        ref = component.get("ref")
        if not ref:
            continue
        target = catalog_by_id.get(ref)
        if not target or target.get("type") != "technology_component":
            continue
        if target.get("classification") == "agent":
            if not has_enabled_external_interaction(obj, ref) and not agent_interaction_exception(obj, ref):
                failures.append(
                    f"{path}: agent Technology Component '{ref}' requires an externalInteraction enabledBy that Technology Component or architecturalDecisions.agentInteractionExceptions"
                )


def validate_standard(
    obj: dict[str, Any],
    path: Path,
    odcs: dict[str, dict[str, Any]],
    catalog_by_id: dict[str, dict[str, Any]],
    catalog_ids: set[str],
    failures: list[str],
    warnings: list[str],
) -> None:
    satisfies = obj.get("satisfiesDefinitionChecklist", [])
    if not isinstance(satisfies, list):
        failures.append(f"{path}: satisfiesDefinitionChecklist must be a list")
        return

    applicable = sorted(set(satisfies) | set(applicable_checklist_ids(obj, odcs)))
    for odc_id in applicable:
        if odc_id not in odcs:
            failures.append(f"{path}: referenced Definition Checklist '{odc_id}' does not exist")
            continue
        for requirement in resolve_checklist_requirements(odc_id, odcs):
            valid, message = validate_checklist_requirement(obj, requirement, catalog_by_id)
            if not valid:
                failures.append(f"{path}: {message}")

    object_type = obj.get("type")
    if object_type == "host_standard":
        host_id = str(obj.get("id", ""))
        required_host_fields = () if host_id.startswith(("host.serverless.", "host.container.")) else ("operatingSystemComponent", "computePlatformComponent")
        for field in required_host_fields:
            ref = obj.get(field)
            if ref and ref not in catalog_ids:
                failures.append(f"{path}: {field} references unknown object '{ref}'")
    if object_type in {"service_standard", "database_standard"}:
        for field in ("hostStandard", "primaryTechnologyComponent"):
            ref = obj.get(field)
            if ref and ref not in catalog_ids:
                failures.append(f"{path}: {field} references unknown object '{ref}'")
    if object_type == "product_service":
        runs_on = obj.get("runsOn")
        target = catalog_by_id.get(runs_on) if runs_on else None
        if runs_on and (not target or target.get("type") not in {"host_standard", "service_standard", "database_standard", "paas_service_standard", "saas_service_standard"}):
            failures.append(f"{path}: runsOn references unknown standard '{runs_on}'")
    if object_type == "saas_service_standard":
        if "dataLeavesInfrastructure" in obj and not isinstance(obj.get("dataLeavesInfrastructure"), bool):
            failures.append(f"{path}: dataLeavesInfrastructure must be true or false")
        if obj.get("dataLeavesInfrastructure") is True and not is_non_empty(obj.get("dpaNotes")):
            warnings.append(f"{path}: SaaS Services with dataLeavesInfrastructure=true should document dpaNotes")

    validate_classified_component_refs(obj, path, catalog_by_id, failures)
    deployment_configurations = obj.get("deploymentConfigurations", [])
    if deployment_configurations is not None:
        if not isinstance(deployment_configurations, list):
            failures.append(f"{path}: deploymentConfigurations must be a list")
        else:
            for index, configuration in enumerate(deployment_configurations):
                if not isinstance(configuration, dict):
                    failures.append(f"{path}: deploymentConfigurations[{index}] must be a mapping")
                    continue
                qualities = configuration.get("addressesQualities", [])
                if qualities is not None:
                    if not isinstance(qualities, list):
                        failures.append(f"{path}: deploymentConfigurations[{index}].addressesQualities must be a list")
                    else:
                        invalid = [quality for quality in qualities if quality not in VALID_DEPLOYMENT_QUALITIES]
                        if invalid:
                            failures.append(
                                f"{path}: deploymentConfigurations[{index}].addressesQualities contains invalid values {invalid}"
                            )
    validate_architectural_decisions(obj, path, failures)
    validate_control_implementations(obj, path, catalog_by_id, failures)


def validate_ra(
    obj: dict[str, Any],
    path: Path,
    odcs: dict[str, dict[str, Any]],
    catalog_by_id: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    applicable = applicable_checklist_ids(obj, odcs)
    if "checklist.reference-architecture" not in applicable:
        return

    object_id = obj.get("id", "unknown")
    if not is_non_empty(obj.get("patternType")):
        failures.append(
            f"{path}: [{object_id}] Definition Checklist requirement 'pattern-type' not satisfied — needs architecturalDecision(patternType)"
        )

    service_groups = obj.get("serviceGroups", [])
    if not isinstance(service_groups, list) or not service_groups:
        failures.append(
            f"{path}: [{object_id}] Definition Checklist requirement 'service-groups' not satisfied — needs serviceGroups with tiered Standard entries"
        )
    else:
        groups_without_rbbs = [
            group.get("name", "unknown")
            for group in service_groups
            if isinstance(group, dict) and not isinstance(group.get("standards"), list)
        ]
        if groups_without_rbbs:
            failures.append(
                f"{path}: [{object_id}] Definition Checklist requirement 'service-groups' not satisfied — every service group must declare standards (missing on: {', '.join(groups_without_rbbs)})"
            )

    if not is_non_empty(obj.get("architecturalDecisions")):
        failures.append(
            f"{path}: [{object_id}] Definition Checklist requirement 'deployment-qualities' not satisfied — needs architecturalDecision(architecturalDecisions)"
        )
    validate_control_implementations(obj, path, catalog_by_id, failures)


def validate_software_deployment_pattern(
    obj: dict[str, Any],
    path: Path,
    odcs: dict[str, dict[str, Any]],
    catalog_by_id: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    applicable = applicable_checklist_ids(obj, odcs)
    if "checklist.software-deployment-pattern" not in applicable:
        return

    object_id = obj.get("id", "unknown")
    if not is_non_empty(obj.get("followsReferenceArchitecture")) and not is_non_empty(obj.get("architecturalDecisions", {}).get("noApplicablePattern") if isinstance(obj.get("architecturalDecisions"), dict) else None):
        failures.append(
            f"{path}: [{object_id}] Definition Checklist requirement 'reference-architecture-conformance' not satisfied — needs field(followsReferenceArchitecture) or architecturalDecision(noApplicablePattern)"
        )

    service_groups = obj.get("serviceGroups", [])
    if not isinstance(service_groups, list):
        service_groups = []

    if not service_groups:
        failures.append(
            f"{path}: [{object_id}] Definition Checklist requirement 'service-groups' not satisfied — serviceGroups cannot be empty"
        )

    architectural_decisions = obj.get("architecturalDecisions", {})
    if not isinstance(architectural_decisions, dict):
        architectural_decisions = {}

    if not is_non_empty(architectural_decisions.get("deploymentTargets")):
        failures.append(
            f"{path}: [{object_id}] Definition Checklist requirement 'deployment-targets' not satisfied — needs architecturalDecision(deploymentTargets)"
        )

    if not is_non_empty(architectural_decisions.get("availabilityRequirement")):
        failures.append(
            f"{path}: [{object_id}] Definition Checklist requirement 'availability-requirement' not satisfied — needs architecturalDecision(availabilityRequirement)"
        )

    has_additional_interactions = any(
        isinstance(group, dict)
        and isinstance(group.get("externalInteractions"), list)
        and len(group.get("externalInteractions", [])) > 0
        for group in service_groups
    ) or (isinstance(obj.get("externalInteractions"), list) and len(obj.get("externalInteractions", [])) > 0)
    if not has_additional_interactions and not is_non_empty(architectural_decisions.get("noAdditionalInteractions")):
        failures.append(
            f"{path}: [{object_id}] Definition Checklist requirement 'additional-interactions' not satisfied — needs externalInteraction(capability=any) or architecturalDecision(noAdditionalInteractions)"
        )

    if not is_non_empty(architectural_decisions.get("dataClassification")):
        failures.append(
            f"{path}: [{object_id}] Definition Checklist requirement 'data-classification' not satisfied — needs architecturalDecision(dataClassification)"
        )

    if not is_non_empty(architectural_decisions.get("failureDomain")):
        failures.append(
            f"{path}: [{object_id}] Definition Checklist requirement 'failure-domain' not satisfied — needs architecturalDecision(failureDomain)"
        )

    if not is_non_empty(architectural_decisions.get("patternDeviations")) and not is_non_empty(architectural_decisions.get("noPatternDeviations")):
        failures.append(
            f"{path}: [{object_id}] Definition Checklist requirement 'pattern-deviations' not satisfied — needs architecturalDecision(patternDeviations) or architecturalDecision(noPatternDeviations)"
        )
    validate_control_implementations(obj, path, catalog_by_id, failures)


def validate_decision_record(obj: dict[str, Any], path: Path, failures: list[str], warnings: list[str]) -> None:
    if obj.get("category") == "decision" and not is_non_empty(obj.get("decisionRationale")):
        warnings.append(f"{path}: decision Decision Records should include decisionRationale")


def validate_drafting_session(
    obj: dict[str, Any],
    path: Path,
    odcs: dict[str, dict[str, Any]],
    catalog_by_id: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    applicable = applicable_checklist_ids(obj, odcs)
    for odc_id in applicable:
        if odc_id not in odcs:
            failures.append(f"{path}: referenced Definition Checklist '{odc_id}' does not exist")
            continue
        for requirement in resolve_checklist_requirements(odc_id, odcs):
            valid, message = validate_checklist_requirement(obj, requirement, catalog_by_id)
            if not valid:
                failures.append(f"{path}: {message}")

    primary_object_id = obj.get("primaryObjectId")
    if primary_object_id and primary_object_id not in catalog_by_id:
        failures.append(f"{path}: primaryObjectId references unknown object '{primary_object_id}'")

    generated_objects = obj.get("generatedObjects", [])
    if isinstance(generated_objects, list):
        for index, entry in enumerate(generated_objects):
            if not isinstance(entry, dict):
                continue
            ref = entry.get("ref")
            proposed_id = entry.get("proposedId")
            if not is_non_empty(ref) and not is_non_empty(proposed_id):
                failures.append(f"{path}: generatedObjects[{index}] must declare either ref or proposedId")
            if ref and ref not in catalog_by_id:
                failures.append(f"{path}: generatedObjects[{index}] references unknown object '{ref}'")

    for field_name in ("unresolvedQuestions", "assumptions", "nextSteps"):
        entries = obj.get(field_name, [])
        if not isinstance(entries, list):
            continue
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            related_objects = entry.get("relatedObjects", [])
            if not isinstance(related_objects, list):
                continue
            for ref_index, ref_entry in enumerate(related_objects):
                if not isinstance(ref_entry, dict):
                    continue
                ref = ref_entry.get("ref")
                if ref and ref not in catalog_by_id:
                    failures.append(
                        f"{path}: {field_name}[{index}].relatedObjects[{ref_index}] references unknown object '{ref}'"
                    )


def object_scope(obj: dict[str, Any]) -> str | None:
    object_type = obj.get("type")
    if object_type in VALID_CONTROL_SCOPES:
        return str(object_type)
    return None


def find_external_interaction(obj: dict[str, Any], implementation: dict[str, Any]) -> bool:
    interactions = obj.get("externalInteractions", [])
    if not isinstance(interactions, list):
        return False
    ref = implementation.get("ref")
    criteria = implementation.get("criteria", {}) if isinstance(implementation.get("criteria"), dict) else {}
    capabilities = criteria.get("capabilities") or ([criteria.get("capability")] if criteria.get("capability") else [])
    for interaction in interactions:
        if not isinstance(interaction, dict):
            continue
        interaction_caps = interaction.get("capabilities", [])
        if ref and ref in {interaction.get("ref"), interaction.get("name")} | set(interaction_caps):
            return True
        if capabilities and any(cap in interaction_caps for cap in capabilities):
            return True
    return False


def find_deployment_configuration(obj: dict[str, Any], implementation: dict[str, Any]) -> bool:
    configurations = obj.get("deploymentConfigurations", [])
    if not isinstance(configurations, list):
        return False
    key = implementation.get("key")
    ref = implementation.get("ref")
    criteria = implementation.get("criteria", {}) if isinstance(implementation.get("criteria"), dict) else {}
    quality = criteria.get("quality")
    for configuration in configurations:
        if not isinstance(configuration, dict):
            continue
        if key and key in {configuration.get("id"), configuration.get("name")}:
            return True
        if ref and ref in {configuration.get("id"), configuration.get("name")}:
            return True
        qualities = configuration.get("addressesQualities", [])
        if quality and isinstance(qualities, list) and quality in qualities:
            return True
    return False


def find_technology_component_reference(obj: dict[str, Any], implementation: dict[str, Any], catalog_by_id: dict[str, dict[str, Any]]) -> bool:
    ref = implementation.get("ref")
    if not is_non_empty(ref):
        return False
    if obj.get("operatingSystemComponent") == ref or obj.get("computePlatformComponent") == ref or obj.get("primaryTechnologyComponent") == ref:
        return True
    for component in obj.get("internalComponents", []) or []:
        if isinstance(component, dict) and component.get("ref") == ref:
            return True
    target = catalog_by_id.get(str(ref))
    return bool(target and target.get("type") in {"technology_component", "appliance_component"})


def find_technology_component_configuration(obj: dict[str, Any], implementation: dict[str, Any], catalog_by_id: dict[str, dict[str, Any]]) -> bool:
    ref = implementation.get("ref")
    key = implementation.get("key")
    criteria = implementation.get("criteria", {}) if isinstance(implementation.get("criteria"), dict) else {}
    capability = criteria.get("capability") or criteria.get("concern")
    for abb in referenced_technology_components(obj, catalog_by_id):
        if ref and abb.get("id") != ref:
            continue
        configurations = abb.get("configurations", [])
        if not isinstance(configurations, list):
            continue
        for configuration in configurations:
            if not isinstance(configuration, dict):
                continue
            if key and key in {configuration.get("id"), configuration.get("name")}:
                return True
            caps = configuration.get("capabilities", [])
            if capability and isinstance(caps, list) and capability in caps:
                return True
    return False


def implementation_resolves(
    obj: dict[str, Any],
    implementation: dict[str, Any],
    catalog_by_id: dict[str, dict[str, Any]],
) -> bool:
    mechanism = implementation.get("mechanism")
    if mechanism == "field":
        key = implementation.get("key")
        return is_non_empty(key) and is_non_empty(get_nested_value(obj, str(key)))
    if mechanism == "architecturalDecision":
        key = implementation.get("key")
        decisions = obj.get("architecturalDecisions", {})
        return is_non_empty(key) and isinstance(decisions, dict) and is_non_empty(get_nested_value(decisions, str(key)))
    if mechanism == "externalInteraction":
        return find_external_interaction(obj, implementation)
    if mechanism == "deploymentConfiguration":
        return find_deployment_configuration(obj, implementation)
    if mechanism == "technologyComponent":
        return find_technology_component_reference(obj, implementation, catalog_by_id)
    if mechanism == "technologyComponentConfiguration":
        return find_technology_component_configuration(obj, implementation, catalog_by_id)
    return False


def validate_control_enforcement_profile(
    obj: dict[str, Any],
    path: Path,
    catalog_by_id: dict[str, dict[str, Any]],
    odcs: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    applicable = applicable_checklist_ids(obj, odcs)
    if "checklist.control-enforcement-profile" not in applicable:
        failures.append(
            f"{path}: control enforcement profile is missing applicable Definition Checklist "
            "'checklist.control-enforcement-profile'"
        )

    controls_id = obj.get("controls")
    controls = catalog_by_id.get(str(controls_id)) if is_non_empty(controls_id) else None
    if not controls or controls.get("type") != "compliance_controls":
        failures.append(f"{path}: controls must reference an existing compliance controls object")
        framework_controls = set()
    else:
        framework_controls = {
            control.get("controlId")
            for control in controls.get("controls", [])
            if isinstance(control, dict) and is_non_empty(control.get("controlId"))
        }

    semantics = obj.get("controlSemantics")
    if semantics is None:
        return
    if not isinstance(semantics, list):
        failures.append(f"{path}: controlSemantics must be a list of semantic entries")
        return
    for index, semantic in enumerate(semantics):
        context = f"{path}: controlSemantics[{index}]"
        if not isinstance(semantic, dict):
            failures.append(f"{context}: control semantic entry must be a mapping")
            continue
        control_id = semantic.get("controlId")
        if not is_non_empty(control_id) or control_id not in framework_controls:
            failures.append(
                f"{context}: Definition Checklist requirement 'semantic-control-reference' not satisfied — controlId must exist in the referenced control catalog"
            )

        applies_to = semantic.get("appliesTo")
        if not isinstance(applies_to, list) or not applies_to:
            failures.append(
                f"{context}: Definition Checklist requirement 'draft-applicability' not satisfied — appliesTo must be a non-empty list"
            )
            continue
        invalid_scopes = [scope for scope in applies_to if scope not in VALID_CONTROL_SCOPES]
        if invalid_scopes:
            failures.append(
                f"{context}: Definition Checklist requirement 'draft-applicability' not satisfied — invalid appliesTo values {invalid_scopes}"
            )

        valid_answer_types = semantic.get("validAnswerTypes")
        if not isinstance(valid_answer_types, list) or not valid_answer_types:
            failures.append(
                f"{context}: Definition Checklist requirement 'valid-answer-types' not satisfied — validAnswerTypes must be a non-empty list"
            )
        else:
            invalid_answer_types = [value for value in valid_answer_types if value not in VALID_CONTROL_ANSWER_TYPES]
            if invalid_answer_types:
                failures.append(
                    f"{context}: Definition Checklist requirement 'valid-answer-types' not satisfied — invalid validAnswerTypes values {invalid_answer_types}"
                )

        requirement_mode = semantic.get("requirementMode")
        if requirement_mode not in VALID_CONTROL_REQUIREMENT_MODES:
            failures.append(
                f"{context}: Definition Checklist requirement 'requirement-mode' not satisfied — requirementMode must be one of {sorted(VALID_CONTROL_REQUIREMENT_MODES)}"
            )

        na_allowed = semantic.get("naAllowed")
        if na_allowed is not None and not isinstance(na_allowed, bool):
            failures.append(
                f"{context}: Definition Checklist requirement 'conditional-applicability' not satisfied — naAllowed must be true or false"
            )
        if requirement_mode == "mandatory" and na_allowed is True:
            failures.append(
                f"{context}: Definition Checklist requirement 'conditional-applicability' not satisfied — mandatory controls cannot allow N/A responses"
            )

        applicability = semantic.get("applicability")
        if applicability is not None:
            if not isinstance(applicability, dict):
                failures.append(
                    f"{context}: Definition Checklist requirement 'conditional-applicability' not satisfied — applicability must be a mapping"
                )
            else:
                groups = [key for key in ("anyOf", "allOf") if key in applicability]
                if not groups:
                    failures.append(
                        f"{context}: Definition Checklist requirement 'conditional-applicability' not satisfied — applicability must declare anyOf or allOf"
                    )
                for group in groups:
                    clauses = applicability.get(group)
                    if not isinstance(clauses, list) or not clauses:
                        failures.append(
                            f"{context}: Definition Checklist requirement 'conditional-applicability' not satisfied — applicability.{group} must be a non-empty list"
                        )
                        continue
                    for clause_index, clause in enumerate(clauses):
                        if not isinstance(clause, dict):
                            failures.append(
                                f"{context}: Definition Checklist requirement 'conditional-applicability' not satisfied — applicability.{group}[{clause_index}] must be a mapping"
                            )
                            continue
                        if not is_non_empty(clause.get("field")):
                            failures.append(
                                f"{context}: Definition Checklist requirement 'conditional-applicability' not satisfied — applicability.{group}[{clause_index}] must declare field"
                            )
                        predicates = [key for key in ("equals", "in", "contains", "truthy") if key in clause]
                        if not predicates:
                            failures.append(
                                f"{context}: Definition Checklist requirement 'conditional-applicability' not satisfied — applicability.{group}[{clause_index}] must declare equals, in, contains, or truthy"
                            )
                        if "truthy" in clause and not isinstance(clause.get("truthy"), bool):
                            failures.append(
                                f"{context}: Definition Checklist requirement 'conditional-applicability' not satisfied — applicability.{group}[{clause_index}].truthy must be true or false"
                            )
                        if "in" in clause and not isinstance(clause.get("in"), list):
                            failures.append(
                                f"{context}: Definition Checklist requirement 'conditional-applicability' not satisfied — applicability.{group}[{clause_index}].in must be a list"
                            )
        elif requirement_mode == "conditional":
            failures.append(
                f"{context}: Definition Checklist requirement 'conditional-applicability' not satisfied — conditional controls must declare applicability"
            )
        if requirement_mode == "conditional" and na_allowed is not True:
            failures.append(
                f"{context}: Definition Checklist requirement 'conditional-applicability' not satisfied — conditional controls must set naAllowed: true"
            )

        related_capability = semantic.get("relatedCapability")
        if is_non_empty(related_capability):
            for scope in applies_to:
                odc_id = scope_to_checklist_id(str(scope))
                if not odc_id or odc_id not in odcs:
                    continue
                resolved = resolve_checklist_requirements(odc_id, odcs)
                valid_requirement_ids = {
                    requirement.get("id")
                    for requirement in resolved
                    if isinstance(requirement, dict) and is_non_empty(requirement.get("id"))
                }
                if related_capability not in valid_requirement_ids:
                    failures.append(
                        f"{context}: relatedCapability '{related_capability}' is not defined on Definition Checklist '{odc_id}'"
                    )


def validate_control_implementations(
    obj: dict[str, Any],
    path: Path,
    catalog_by_id: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    scope = object_scope(obj)
    if not scope:
        return

    profiles = obj.get("controlEnforcementProfiles", [])
    if profiles is None:
        profiles = []
    if not isinstance(profiles, list):
        failures.append(f"{path}: controlEnforcementProfiles must be a list")
        return
    declared_profile_ids = {str(profile_id) for profile_id in profiles}

    implementations = obj.get("controlImplementations", [])
    if implementations is None:
        implementations = []
    if not isinstance(implementations, list):
        failures.append(f"{path}: controlImplementations must be a list")
        return

    implementations_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for index, implementation in enumerate(implementations):
        context = f"{path}: controlImplementations[{index}]"
        if not isinstance(implementation, dict):
            failures.append(f"{context}: control implementation must be a mapping")
            continue
        profile_id = implementation.get("profile")
        control_id = implementation.get("controlId")
        if not is_non_empty(profile_id) or not is_non_empty(control_id):
            continue
        if str(profile_id) not in declared_profile_ids:
            failures.append(
                f"{context}: profile '{profile_id}' is not declared in controlEnforcementProfiles; "
                "control implementations are evidence for an explicit compliance claim"
            )
            continue
        profile = catalog_by_id.get(str(profile_id))
        if not profile or profile.get("type") != "control_enforcement_profile":
            failures.append(f"{context}: profile must reference an existing control_enforcement_profile")
            continue
        semantics = next(
            (
                semantic for semantic in profile.get("controlSemantics", [])
                if isinstance(semantic, dict) and semantic.get("controlId") == control_id and scope in (semantic.get("appliesTo") or [])
            ),
            None,
        )
        if semantics is None:
            failures.append(f"{context}: controlId '{control_id}' is not defined for scope '{scope}' on profile '{profile_id}'")
            continue
        status = implementation.get("status")
        if status == "opted-out":
            failures.append(f"{context}: opted-out controls are non-compliant and must be addressed or removed")
            continue
        if status == "not-applicable":
            if semantics.get("requirementMode") != "conditional" or semantics.get("naAllowed") is not True:
                failures.append(f"{context}: only conditional controls that allow N/A may use status 'not-applicable'")
            implementations_by_key[(str(profile_id), str(control_id))] = implementation
            continue
        mechanism = implementation.get("mechanism")
        valid_answer_types = semantics.get("validAnswerTypes", [])
        if mechanism not in valid_answer_types:
            failures.append(f"{context}: mechanism '{mechanism}' is not allowed by profile '{profile_id}' for control '{control_id}'")
        elif not implementation_resolves(obj, implementation, catalog_by_id):
            failures.append(f"{context}: mechanism '{mechanism}' does not resolve against the current object state")
        implementations_by_key[(str(profile_id), str(control_id))] = implementation

    for profile_id in profiles:
        profile = catalog_by_id.get(str(profile_id))
        if not profile or profile.get("type") != "control_enforcement_profile":
            failures.append(f"{path}: controlEnforcementProfiles references unknown control enforcement profile '{profile_id}'")
            continue
        semantics = [
            semantic for semantic in profile.get("controlSemantics", [])
            if isinstance(semantic, dict) and scope in (semantic.get("appliesTo") or [])
        ]
        for semantic in semantics:
            key = (str(profile_id), str(semantic.get("controlId")))
            if key not in implementations_by_key:
                failures.append(
                    f"{path}: applicable control '{semantic.get('controlId')}' from profile '{profile_id}' has no recorded implementation"
                )


def validate_compliance_controls(
    obj: dict[str, Any],
    path: Path,
    catalog_by_id: dict[str, dict[str, Any]],
    odcs: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    applicable = applicable_checklist_ids(obj, odcs)
    if "checklist.compliance-controls" not in applicable:
        failures.append(f"{path}: compliance controls is missing applicable Definition Checklist 'checklist.compliance-controls'")

    controls = obj.get("controls")
    if controls is None:
        return
    if not isinstance(controls, list):
        failures.append(f"{path}: controls must be a list of control definitions")
        return
    for index, control in enumerate(controls):
        context = f"{path}: controls[{index}]"
        if not isinstance(control, dict):
            failures.append(f"{context}: control entry must be a mapping")
            continue
        control_id = control.get("controlId")
        if not is_non_empty(control_id) or not is_non_empty(control.get("name")):
            failures.append(
                f"{context}: Definition Checklist requirement 'control-identity' not satisfied — every control must declare controlId and name"
            )
        if not is_non_empty(control.get("externalReference")):
            failures.append(
                f"{context}: Definition Checklist requirement 'authoritative-source' not satisfied — every control must declare externalReference"
            )


def validate_service_group_structure(
    obj: dict[str, Any],
    path: Path,
    decision_record_ids: set[str],
    appliance_component_ids: set[str],
    catalog_by_id: dict[str, dict[str, Any]],
    failures: list[str],
    require_deployment_target: bool = True,
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
        if require_deployment_target and not is_non_empty(deployment_target):
            failures.append(f"{path}: serviceGroup '{name}' missing deploymentTarget")

    for group in service_groups:
        if not isinstance(group, dict) or not is_non_empty(group.get("name")):
            continue
        group_name = str(group["name"])
        scaling_unit_name = group.get("scalingUnit")
        if scaling_unit_name and scaling_unit_name not in scaling_unit_names:
            failures.append(f"{path}: serviceGroup '{group_name}' references unknown scalingUnit '{scaling_unit_name}'")

        for entry in group.get("standards", []) or []:
            if not isinstance(entry, dict):
                continue
            ref = entry.get("ref")
            target = catalog_by_id.get(ref) if ref else None
            if ref and (not target or target.get("type") not in STANDARD_TYPES):
                failures.append(f"{path}: serviceGroup '{group_name}' references unknown standard '{ref}'")
            diagram_tier = entry.get("diagramTier")
            if diagram_tier not in VALID_DIAGRAM_TIERS:
                failures.append(
                    f"{path}: serviceGroup '{group_name}' standard '{ref}' must set diagramTier to one of {sorted(VALID_DIAGRAM_TIERS)}"
                )
            risk_ref = entry.get("riskRef")
            if risk_ref and risk_ref not in decision_record_ids:
                failures.append(f"{path}: serviceGroup '{group_name}' standard '{ref}' references unknown Decision Record '{risk_ref}'")
            intent = entry.get("intent")
            if intent and intent not in {"ha", "sa"}:
                failures.append(f"{path}: serviceGroup '{group_name}' standard '{ref}' has invalid intent '{intent}'")

        for entry in group.get("applianceComponents", []) or []:
            if not isinstance(entry, dict):
                continue
            ref = entry.get("ref")
            if ref and ref not in appliance_component_ids:
                failures.append(f"{path}: serviceGroup '{group_name}' references unknown Appliance Component '{ref}'")

        for interaction in group.get("externalInteractions", []) or []:
            if not isinstance(interaction, dict):
                continue
            if interaction.get("type", "external") == "internal":
                ref = interaction.get("ref")
                if not ref or ref not in service_group_names:
                    failures.append(
                        f"{path}: serviceGroup '{group_name}' internal interaction '{interaction.get('name', 'unnamed')}' must reference a valid service group name"
                    )


def validate_service_group_refs(
    obj: dict[str, Any],
    path: Path,
    decision_record_ids: set[str],
    appliance_component_ids: set[str],
    catalog_by_id: dict[str, dict[str, Any]],
    failures: list[str],
    require_deployment_target: bool = True,
) -> None:
    for risk in obj.get("decisionRecords", []):
        if not isinstance(risk, dict):
            continue
        ref = risk.get("ref")
        if ref and ref not in decision_record_ids:
            failures.append(f"{path}: decisionRecords references unknown Decision Record '{ref}'")

    validate_service_group_structure(
        obj,
        path,
        decision_record_ids,
        appliance_component_ids,
        catalog_by_id,
        failures,
        require_deployment_target=require_deployment_target,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    workspace_root = args.workspace.resolve()
    global VALID_CAPABILITIES
    VALID_CAPABILITIES = load_valid_capabilities([BASE_CONFIGURATION_ROOT, workspace_root / "configurations"])

    files = discover_workspace_yaml_files(workspace_root)
    schemas = load_schemas(SCHEMA_ROOT)
    objects: dict[Path, dict[str, Any]] = {}
    failures: list[str] = []
    warnings: list[str] = []

    for path in files:
        try:
            objects[path] = load_yaml(path)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{path}: failed to parse YAML ({exc})")

    objects = apply_object_patches(objects, failures)

    catalog_by_id = {
        obj["id"]: obj
        for obj in objects.values()
        if isinstance(obj, dict) and is_non_empty(obj.get("id"))
    }
    odcs = {object_id: obj for object_id, obj in catalog_by_id.items() if obj.get("type") == "definition_checklist"}
    decision_record_ids = {object_id for object_id, obj in catalog_by_id.items() if obj.get("type") == "decision_record"}
    appliance_component_ids = {
        object_id for object_id, obj in catalog_by_id.items() if obj.get("type") == "appliance_component"
    }
    catalog_ids = set(catalog_by_id.keys())

    for path, obj in objects.items():
        validate_against_schema(obj, path, schemas, failures)
        if obj.get("type") in {"technology_component", "appliance_component"}:
            validate_component(obj, path, odcs, catalog_by_id, failures)
        if obj.get("type") == "decision_record":
            validate_decision_record(obj, path, failures, warnings)
        if obj.get("type") == "drafting_session":
            validate_drafting_session(obj, path, odcs, catalog_by_id, failures)
        if obj.get("type") == "compliance_controls":
            validate_compliance_controls(obj, path, catalog_by_id, odcs, failures)
        if obj.get("type") == "control_enforcement_profile":
            validate_control_enforcement_profile(obj, path, catalog_by_id, odcs, failures)
        if obj.get("type") in STANDARD_TYPES:
            validate_standard(obj, path, odcs, catalog_by_id, catalog_ids, failures, warnings)
        if obj.get("type") == "reference_architecture":
            validate_ra(obj, path, odcs, catalog_by_id, failures)
            validate_service_group_refs(
                obj,
                path,
                decision_record_ids,
                appliance_component_ids,
                catalog_by_id,
                failures,
                require_deployment_target=False,
            )
        if obj.get("type") == "software_deployment_pattern":
            validate_software_deployment_pattern(obj, path, odcs, catalog_by_id, failures)
            validate_service_group_refs(obj, path, decision_record_ids, appliance_component_ids, catalog_by_id, failures)

    failing_paths = {entry.split(":", 1)[0] for entry in failures}
    for path in files:
        if str(path) in failing_paths:
            print(f"FAIL {display_path(path)}")
        else:
            print(f"PASS {display_path(path)}")

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
