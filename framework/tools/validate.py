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

VALID_REQUIREMENT_SCOPES = {
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

VALID_REQUIREMENT_ANSWER_TYPES = {
    "technologyComponent",
    "technologyComponentConfiguration",
    "deploymentConfiguration",
    "externalInteraction",
    "internalComponent",
    "architecturalDecision",
    "field",
}
VALID_REQUIREMENT_MODES = {"mandatory", "conditional"}
VALID_REQUIREMENT_ACTIVATIONS = {"always", "workspace"}
VALID_IMPLEMENTATION_STATUSES = {"pre-invest", "invest", "maintain", "disinvest", "exit"}
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
    provider_root = workspace_root / ".draft" / "providers"
    if provider_root.exists():
        roots.extend(
            provider_config
            for provider_config in sorted(provider_root.glob("*/configurations"))
            if provider_config.exists()
        )
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


def load_workspace_requirements(workspace_root: Path, failures: list[str]) -> dict[str, Any]:
    config_path = workspace_root / ".draft" / "workspace.yaml"
    if not config_path.exists():
        return {"active_groups": set(), "require_active_group_disposition": False}
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001
        failures.append(f"{config_path}: Fix workspace configuration YAML; parser reported {exc}")
        return {"active_groups": set(), "require_active_group_disposition": False}
    if not isinstance(data, dict):
        failures.append(f"{config_path}: Make workspace configuration a mapping at the top level")
        return {"active_groups": set(), "require_active_group_disposition": False}

    requirements = data.get("requirements") or {}
    if not isinstance(requirements, dict):
        failures.append(f"{config_path}: Make requirements a mapping with activeRequirementGroups")
        return {"active_groups": set(), "require_active_group_disposition": False}

    active = requirements.get("activeRequirementGroups") or []
    if not isinstance(active, list):
        failures.append(f"{config_path}: Set requirements.activeRequirementGroups to a list of requirement_group IDs")
        active = []
    active_groups = {str(group_id) for group_id in active if is_non_empty(group_id)}
    return {
        "active_groups": active_groups,
        "require_active_group_disposition": requirements.get("requireActiveRequirementGroupDisposition") is True,
    }


def validate_workspace_requirements(
    workspace_root: Path,
    active_group_ids: set[str],
    catalog_by_id: dict[str, dict[str, Any]],
    failures: list[str],
) -> None:
    config_path = workspace_root / ".draft" / "workspace.yaml"
    for group_id in sorted(active_group_ids):
        group = catalog_by_id.get(group_id)
        if not group or group.get("type") != "requirement_group":
            failures.append(
                f"{config_path}: Activate only existing workspace-mode requirement groups; '{group_id}' was not found"
            )
        elif group.get("activation") != "workspace":
            failures.append(
                f"{config_path}: Remove '{group_id}' from requirements.activeRequirementGroups; always-on requirement groups do not need workspace activation"
            )


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


def has_required_value(node: dict[str, Any], field: str) -> bool:
    if field not in node or node.get(field) is None:
        return False
    value = node.get(field)
    if isinstance(value, str):
        return bool(value.strip())
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
    field_descriptions = schema.get("fieldDescriptions") if isinstance(schema.get("fieldDescriptions"), dict) else {}
    for field in schema.get("requiredFields", []):
        if not has_required_value(node, field):
            hint = field_descriptions.get(field, "Populate this field with a valid value for the selected schema.")
            failures.append(f"{context}: Add required field '{field}' — {hint}")

    id_pattern = schema.get("idPattern")
    if id_pattern and is_non_empty(node.get("id")) and not re.match(str(id_pattern), str(node.get("id"))):
        failures.append(f"{context}: Rename id '{node.get('id')}' so it matches pattern {id_pattern}")

    for field, allowed_values in (schema.get("enumFields") or {}).items():
        value = node.get(field)
        if value is None or value == "":
            continue
        if value not in allowed_values:
            failures.append(f"{context}: Set {field} to one of {allowed_values}; '{value}' is not valid")

    for field, expected_type in (schema.get("fieldTypes") or {}).items():
        if field not in node or node.get(field) is None:
            continue
        checker = TYPE_CHECKERS.get(str(expected_type))
        if checker and not isinstance(node.get(field), checker):
            failures.append(f"{context}: Change field '{field}' to type {expected_type}")

    for field, allowed_values in (schema.get("enumListFields") or {}).items():
        value = node.get(field)
        if value is None:
            continue
        if not isinstance(value, list):
            failures.append(f"{context}: Change field '{field}' to a list")
            continue
        invalid = [item for item in value if item not in allowed_values]
        if invalid:
            failures.append(f"{context}: Replace invalid {field} values {invalid} with one of {allowed_values}")

    for conditional in schema.get("conditionalRequired", []) or []:
        when = conditional.get("when", {})
        required = conditional.get("require", [])
        if isinstance(when, dict) and matches_conditions(node, when):
            for field in required:
                if not has_required_value(node, field):
                    hint = field_descriptions.get(field, "Populate this conditional field because the matching condition is present.")
                    failures.append(f"{context}: Add required field '{field}' — {hint}")

    for field, section_name in (schema.get("collectionSchemas") or {}).items():
        if field not in node or node.get(field) is None:
            continue
        value = node.get(field)
        if not isinstance(value, list):
            failures.append(f"{context}: Change field '{field}' to a list")
            continue
        child_schema = schema.get(section_name)
        if not isinstance(child_schema, dict):
            continue
        for index, item in enumerate(value):
            if not isinstance(item, dict):
                failures.append(f"{context}: Change '{field}[{index}]' to a mapping")
                continue
            validate_schema_section(item, child_schema, f"{context}: {field}[{index}]", failures)


def resolve_requirement_group_requirements(
    group_id: str,
    requirement_groups: dict[str, dict[str, Any]],
    stack: set[str] | None = None,
) -> list[dict[str, Any]]:
    if group_id not in requirement_groups:
        raise KeyError(f"unknown Requirement Group '{group_id}'")
    stack = stack or set()
    if group_id in stack:
        raise ValueError(f"cyclic Requirement Group inheritance detected at '{group_id}'")
    stack.add(group_id)
    group = requirement_groups[group_id]
    requirements: list[dict[str, Any]] = []
    parent_id = group.get("inherits")
    if parent_id:
        requirements.extend(resolve_requirement_group_requirements(parent_id, requirement_groups, stack))
    requirements.extend(group.get("requirements", []))
    stack.remove(group_id)
    return requirements


def requirement_group_applies_to_object(group: dict[str, Any], obj: dict[str, Any]) -> bool:
    object_type = str(obj.get("type") or "")
    applies_to = group.get("appliesTo") or []
    if not isinstance(applies_to, list) or object_type not in applies_to:
        return False
    qualifiers = group.get("appliesToQualifiers") or {}
    if isinstance(qualifiers, dict):
        for key, expected in qualifiers.items():
            if obj.get(key) != expected:
                return False
    if object_type == "host_standard" and group.get("id") == "requirement-group.host-standard":
        object_id = str(obj.get("id", ""))
        if object_id.startswith("host.serverless.") or object_id.startswith("host.container."):
            return False
    return True


def requirement_applies_to_object(requirement: dict[str, Any], obj: dict[str, Any]) -> bool:
    scoped_to = requirement.get("appliesTo")
    if isinstance(scoped_to, list) and scoped_to and obj.get("type") not in scoped_to:
        return False
    applicability = requirement.get("applicability")
    if isinstance(applicability, dict) and applicability:
        if "allOf" in applicability:
            clauses = applicability.get("allOf")
            return isinstance(clauses, list) and all(applicability_clause_matches(obj, clause) for clause in clauses)
        if "anyOf" in applicability:
            clauses = applicability.get("anyOf")
            return isinstance(clauses, list) and any(applicability_clause_matches(obj, clause) for clause in clauses)
    return True


def applicability_clause_matches(obj: dict[str, Any], clause: Any) -> bool:
    if not isinstance(clause, dict) or not is_non_empty(clause.get("field")):
        return False
    value = get_nested_value(obj, str(clause["field"]))
    if "equals" in clause:
        return value == clause.get("equals")
    if "in" in clause and isinstance(clause.get("in"), list):
        return value in clause.get("in")
    if "contains" in clause:
        return isinstance(value, list) and clause.get("contains") in value
    if "truthy" in clause:
        return bool(value) is bool(clause.get("truthy"))
    return False


def applicable_requirement_group_ids(
    obj: dict[str, Any],
    requirement_groups: dict[str, dict[str, Any]],
    active_group_ids: set[str] | None = None,
    require_active_group_disposition: bool = False,
) -> list[str]:
    active_group_ids = active_group_ids or set()
    declared = obj.get("requirementGroups", [])
    declared_ids = {str(group_id) for group_id in declared} if isinstance(declared, list) else set()
    applicable: set[str] = set()
    for group_id, group in requirement_groups.items():
        if not requirement_group_applies_to_object(group, obj):
            continue
        if group.get("activation") == "always":
            applicable.add(group_id)
        elif group_id in declared_ids:
            applicable.add(group_id)
        elif require_active_group_disposition and group_id in active_group_ids:
            applicable.add(group_id)
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
        if capability == "any":
            return bool(obj.get("externalInteractions"))
        # Check if any interaction has the required capability in its capabilities list
        for interaction in obj.get("externalInteractions", []) or []:
            if not isinstance(interaction, dict):
                continue
            caps = interaction.get("capabilities", [])
            if isinstance(caps, list) and capability in caps:
                return True
        return False
    if mechanism_type == "technologyComponent":
        criteria = mechanism.get("criteria", {})
        capability = criteria.get("capability") or criteria.get("concern")
        classification = criteria.get("classification")
        ref = mechanism.get("ref")
        for component in referenced_technology_components(obj, catalog_by_id):
            if ref and component.get("id") != ref:
                continue
            if classification and component.get("classification") != classification:
                continue
            caps = component.get("capabilities", [])
            if not capability or (isinstance(caps, list) and capability in caps):
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


def validate_requirement(
    obj: dict[str, Any],
    requirement: dict[str, Any],
    group_id: str,
    catalog_by_id: dict[str, dict[str, Any]],
) -> tuple[bool, str]:
    requirement_id = requirement.get("id", "unknown")
    valid_answer_types = requirement.get("validAnswerTypes", [])
    for implementation in obj.get("requirementImplementations", []) or []:
        if not isinstance(implementation, dict):
            continue
        if implementation.get("requirementGroup") != group_id or implementation.get("requirementId") != requirement_id:
            continue
        status = implementation.get("status")
        if status == "not-applicable" and requirement.get("naAllowed") is True:
            return True, ""
        mechanism = implementation.get("mechanism")
        if (
            status == "satisfied"
            and mechanism in valid_answer_types
            and implementation_resolves(obj, implementation, catalog_by_id)
        ):
            return True, ""

    mechanisms = requirement.get("canBeSatisfiedBy", [])
    minimum = int(requirement.get("minimumSatisfactions", 1))
    satisfied = [mechanism for mechanism in mechanisms if mechanism_satisfied(obj, mechanism, catalog_by_id)]
    if len(satisfied) >= minimum:
        return True, ""

    related = requirement.get("relatedCapability")
    mechanism_text = " or ".join(mechanism_description(mechanism) for mechanism in mechanisms)
    if minimum > 1:
        mechanism_text = f"at least {minimum} of {mechanism_text}"
    related_text = f" — see capability {related} for approved implementations" if related else ""
    return (
        False,
        f"[{obj.get('id', 'unknown')}] Satisfy requirement '{requirement_id}' from {group_id} using {mechanism_text}{related_text}",
    )


def validate_against_schema(obj: dict[str, Any], path: Path, schemas: list[dict[str, Any]], failures: list[str]) -> None:
    schema = select_schema(obj, schemas)
    if schema is None:
        failures.append(f"{path}: no schema found for type '{obj.get('type')}'")
        return
    validate_schema_section(obj, schema, str(path), failures)


def record_requirement_gap(
    obj: dict[str, Any],
    path: Path,
    message: str,
    failures: list[str],
    warnings: list[str],
) -> None:
    entry = f"{path}: {message}"
    if obj.get("catalogStatus") == "approved":
        failures.append(entry)
    else:
        warnings.append(entry)


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
    requirement_groups: dict[str, dict[str, Any]],
    catalog_by_id: dict[str, dict[str, Any]],
    capability_ids: set[str],
    failures: list[str],
    warnings: list[str],
    active_group_ids: set[str] | None = None,
    require_active_group_disposition: bool = False,
) -> None:
    classification = obj.get("classification")
    if classification not in VALID_TECHNOLOGY_COMPONENT_CLASSIFICATIONS:
        failures.append(
            f"{path}: Set Technology Component classification to one of {sorted(VALID_TECHNOLOGY_COMPONENT_CLASSIFICATIONS)}"
        )
    capabilities = obj.get("capabilities", [])
    if capabilities is not None:
        if not isinstance(capabilities, list):
            failures.append(f"{path}: Change capabilities to a list of capability IDs")
        else:
            invalid = [cap for cap in capabilities if cap not in capability_ids]
            if invalid:
                failures.append(
                    f"{path}: Replace invalid capability references {invalid} with capability object IDs from configurations/capabilities"
                )
    configurations = obj.get("configurations", [])
    if configurations is not None:
        if not isinstance(configurations, list):
            failures.append(f"{path}: Change configurations to a list")
        else:
            for index, configuration in enumerate(configurations):
                if not isinstance(configuration, dict):
                    failures.append(f"{path}: Change configurations[{index}] to a mapping")
                    continue
                config_caps = configuration.get("capabilities", [])
                if not isinstance(config_caps, list):
                    failures.append(f"{path}: Change configurations[{index}].capabilities to a list of capability IDs")
                    continue
                invalid = [cap for cap in config_caps if cap not in capability_ids]
                if invalid:
                    failures.append(
                        f"{path}: Replace invalid configuration capability references {invalid} with capability object IDs from configurations/capabilities"
                    )

    validate_applicable_requirements(
        obj,
        path,
        requirement_groups,
        catalog_by_id,
        capability_ids,
        failures,
        warnings,
        active_group_ids,
        require_active_group_disposition,
    )


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
    requirement_groups: dict[str, dict[str, Any]],
    catalog_by_id: dict[str, dict[str, Any]],
    catalog_ids: set[str],
    capability_ids: set[str],
    failures: list[str],
    warnings: list[str],
    active_group_ids: set[str] | None = None,
    require_active_group_disposition: bool = False,
) -> None:
    validate_applicable_requirements(
        obj,
        path,
        requirement_groups,
        catalog_by_id,
        capability_ids,
        failures,
        warnings,
        active_group_ids,
        require_active_group_disposition,
    )

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


def validate_ra(
    obj: dict[str, Any],
    path: Path,
    requirement_groups: dict[str, dict[str, Any]],
    catalog_by_id: dict[str, dict[str, Any]],
    capability_ids: set[str],
    failures: list[str],
    warnings: list[str],
    active_group_ids: set[str] | None = None,
    require_active_group_disposition: bool = False,
) -> None:
    validate_applicable_requirements(
        obj,
        path,
        requirement_groups,
        catalog_by_id,
        capability_ids,
        failures,
        warnings,
        active_group_ids,
        require_active_group_disposition,
    )

    object_id = obj.get("id", "unknown")
    if not is_non_empty(obj.get("patternType")):
        record_requirement_gap(
            obj,
            path,
            f"[{object_id}] Add patternType to satisfy requirement-group.reference-architecture requirement 'pattern-type'",
            failures,
            warnings,
        )

    service_groups = obj.get("serviceGroups", [])
    if not isinstance(service_groups, list) or not service_groups:
        record_requirement_gap(
            obj,
            path,
            f"[{object_id}] Add serviceGroups with tiered Standard entries to satisfy requirement-group.reference-architecture requirement 'service-groups'",
            failures,
            warnings,
        )
    else:
        groups_without_rbbs = [
            group.get("name", "unknown")
            for group in service_groups
            if isinstance(group, dict) and not isinstance(group.get("standards"), list)
        ]
        if groups_without_rbbs:
            record_requirement_gap(
                obj,
                path,
                f"[{object_id}] Add standards to every service group to satisfy requirement-group.reference-architecture requirement 'service-groups' (missing on: {', '.join(groups_without_rbbs)})",
                failures,
                warnings,
            )

    if not is_non_empty(obj.get("architecturalDecisions")):
        record_requirement_gap(
            obj,
            path,
            f"[{object_id}] Add architecturalDecisions to satisfy requirement-group.reference-architecture requirement 'deployment-qualities'",
            failures,
            warnings,
        )


def validate_software_deployment_pattern(
    obj: dict[str, Any],
    path: Path,
    requirement_groups: dict[str, dict[str, Any]],
    catalog_by_id: dict[str, dict[str, Any]],
    capability_ids: set[str],
    failures: list[str],
    warnings: list[str],
    active_group_ids: set[str] | None = None,
    require_active_group_disposition: bool = False,
) -> None:
    validate_applicable_requirements(
        obj,
        path,
        requirement_groups,
        catalog_by_id,
        capability_ids,
        failures,
        warnings,
        active_group_ids,
        require_active_group_disposition,
    )

    object_id = obj.get("id", "unknown")
    if not is_non_empty(obj.get("followsReferenceArchitecture")) and not is_non_empty(obj.get("architecturalDecisions", {}).get("noApplicablePattern") if isinstance(obj.get("architecturalDecisions"), dict) else None):
        record_requirement_gap(
            obj,
            path,
            f"[{object_id}] Add followsReferenceArchitecture or architecturalDecisions.noApplicablePattern to satisfy requirement-group.software-deployment-pattern requirement 'reference-architecture-conformance'",
            failures,
            warnings,
        )

    service_groups = obj.get("serviceGroups", [])
    if not isinstance(service_groups, list):
        service_groups = []

    if not service_groups:
        record_requirement_gap(
            obj,
            path,
            f"[{object_id}] Add serviceGroups to satisfy requirement-group.software-deployment-pattern requirement 'service-groups'",
            failures,
            warnings,
        )

    architectural_decisions = obj.get("architecturalDecisions", {})
    if not isinstance(architectural_decisions, dict):
        architectural_decisions = {}

    if not is_non_empty(architectural_decisions.get("deploymentTargets")):
        record_requirement_gap(
            obj,
            path,
            f"[{object_id}] Add architecturalDecisions.deploymentTargets to satisfy requirement-group.software-deployment-pattern requirement 'deployment-targets'",
            failures,
            warnings,
        )

    if not is_non_empty(architectural_decisions.get("availabilityRequirement")):
        record_requirement_gap(
            obj,
            path,
            f"[{object_id}] Add architecturalDecisions.availabilityRequirement to satisfy requirement-group.software-deployment-pattern requirement 'availability-requirement'",
            failures,
            warnings,
        )

    has_additional_interactions = any(
        isinstance(group, dict)
        and isinstance(group.get("externalInteractions"), list)
        and len(group.get("externalInteractions", [])) > 0
        for group in service_groups
    ) or (isinstance(obj.get("externalInteractions"), list) and len(obj.get("externalInteractions", [])) > 0)
    if not has_additional_interactions and not is_non_empty(architectural_decisions.get("noAdditionalInteractions")):
        record_requirement_gap(
            obj,
            path,
            f"[{object_id}] Add an external interaction or architecturalDecisions.noAdditionalInteractions to satisfy requirement-group.software-deployment-pattern requirement 'additional-interactions'",
            failures,
            warnings,
        )

    if not is_non_empty(architectural_decisions.get("dataClassification")):
        record_requirement_gap(
            obj,
            path,
            f"[{object_id}] Add architecturalDecisions.dataClassification to satisfy requirement-group.software-deployment-pattern requirement 'data-classification'",
            failures,
            warnings,
        )

    if not is_non_empty(architectural_decisions.get("failureDomain")):
        record_requirement_gap(
            obj,
            path,
            f"[{object_id}] Add architecturalDecisions.failureDomain to satisfy requirement-group.software-deployment-pattern requirement 'failure-domain'",
            failures,
            warnings,
        )

    if not is_non_empty(architectural_decisions.get("patternDeviations")) and not is_non_empty(architectural_decisions.get("noPatternDeviations")):
        record_requirement_gap(
            obj,
            path,
            f"[{object_id}] Add architecturalDecisions.patternDeviations or noPatternDeviations to satisfy requirement-group.software-deployment-pattern requirement 'pattern-deviations'",
            failures,
            warnings,
        )


def validate_decision_record(obj: dict[str, Any], path: Path, failures: list[str], warnings: list[str]) -> None:
    if obj.get("category") == "decision" and not is_non_empty(obj.get("decisionRationale")):
        warnings.append(f"{path}: decision Decision Records should include decisionRationale")


def validate_drafting_session(
    obj: dict[str, Any],
    path: Path,
    requirement_groups: dict[str, dict[str, Any]],
    catalog_by_id: dict[str, dict[str, Any]],
    capability_ids: set[str],
    failures: list[str],
    warnings: list[str],
    active_group_ids: set[str] | None = None,
    require_active_group_disposition: bool = False,
) -> None:
    validate_applicable_requirements(
        obj,
        path,
        requirement_groups,
        catalog_by_id,
        capability_ids,
        failures,
        warnings,
        active_group_ids,
        require_active_group_disposition,
    )

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
    if object_type in VALID_REQUIREMENT_SCOPES:
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



def validate_capability(
    obj: dict[str, Any],
    path: Path,
    catalog_by_id: dict[str, dict[str, Any]],
    domain_ids: set[str],
    failures: list[str],
) -> None:
    domain_id = obj.get("domain")
    if domain_id not in domain_ids:
        failures.append(f"{path}: Set domain to an existing domain object ID; '{domain_id}' was not found")
    implementations = obj.get("implementations", [])
    if not isinstance(implementations, list):
        failures.append(f"{path}: Change implementations to a list of Technology Component mappings")
        return
    for index, implementation in enumerate(implementations):
        context = f"{path}: implementations[{index}]"
        if not isinstance(implementation, dict):
            failures.append(f"{context}: Change implementation entry to a mapping")
            continue
        ref = implementation.get("ref")
        target = catalog_by_id.get(str(ref)) if is_non_empty(ref) else None
        if not target or target.get("type") != "technology_component":
            failures.append(f"{context}: Set ref to an existing Technology Component ID")
        lifecycle_status = implementation.get("lifecycleStatus")
        if lifecycle_status not in VALID_IMPLEMENTATION_STATUSES:
            failures.append(
                f"{context}: Set lifecycleStatus to one of {sorted(VALID_IMPLEMENTATION_STATUSES)}"
            )
        configuration = implementation.get("configuration")
        if configuration and target:
            configs = target.get("configurations", [])
            if not any(isinstance(config, dict) and config.get("id") == configuration for config in configs):
                failures.append(
                    f"{context}: Set configuration to a configuration id that exists on Technology Component '{ref}'"
                )


def validate_requirement_group(
    obj: dict[str, Any],
    path: Path,
    capability_ids: set[str],
    failures: list[str],
) -> None:
    activation = obj.get("activation")
    if activation not in VALID_REQUIREMENT_ACTIVATIONS:
        failures.append(f"{path}: Set activation to 'always' or 'workspace'")
    applies_to = obj.get("appliesTo")
    if not isinstance(applies_to, list) or not applies_to:
        failures.append(f"{path}: Add appliesTo with at least one governed object type")
        applies_to = []
    invalid_scopes = [scope for scope in applies_to if scope not in VALID_REQUIREMENT_SCOPES and scope != "drafting_session"]
    if invalid_scopes:
        failures.append(f"{path}: Replace invalid appliesTo values {invalid_scopes} with supported object types")
    requirements = obj.get("requirements")
    if not isinstance(requirements, list):
        failures.append(f"{path}: Change requirements to a list")
        return
    seen: set[str] = set()
    for index, requirement in enumerate(requirements):
        context = f"{path}: requirements[{index}]"
        if not isinstance(requirement, dict):
            failures.append(f"{context}: Change requirement entry to a mapping")
            continue
        requirement_id = requirement.get("id")
        if is_non_empty(requirement_id):
            if str(requirement_id) in seen:
                failures.append(f"{context}: Rename duplicate requirement id '{requirement_id}' so it is unique in this group")
            seen.add(str(requirement_id))
        mode = requirement.get("requirementMode")
        if mode not in VALID_REQUIREMENT_MODES:
            failures.append(f"{context}: Set requirementMode to mandatory or conditional")
        if not isinstance(requirement.get("naAllowed"), bool):
            failures.append(f"{context}: Set naAllowed to true or false")
        related_capability = requirement.get("relatedCapability")
        if is_non_empty(related_capability) and related_capability not in capability_ids:
            failures.append(
                f"{context}: Set relatedCapability to an existing capability object ID; '{related_capability}' was not found"
            )
        requirement_scopes = requirement.get("appliesTo")
        if requirement_scopes is not None:
            if not isinstance(requirement_scopes, list):
                failures.append(f"{context}: Change appliesTo to a list when present")
            else:
                invalid_requirement_scopes = [
                    scope for scope in requirement_scopes if scope not in VALID_REQUIREMENT_SCOPES and scope != "drafting_session"
                ]
                if invalid_requirement_scopes:
                    failures.append(
                        f"{context}: Replace invalid requirement appliesTo values {invalid_requirement_scopes} with supported object types"
                    )
        valid_answer_types = requirement.get("validAnswerTypes")
        if not isinstance(valid_answer_types, list) or not valid_answer_types:
            failures.append(f"{context}: Add validAnswerTypes with at least one satisfaction mechanism")
        else:
            invalid_answer_types = [value for value in valid_answer_types if value not in VALID_REQUIREMENT_ANSWER_TYPES]
            if invalid_answer_types:
                failures.append(
                    f"{context}: Replace invalid validAnswerTypes {invalid_answer_types} with supported mechanisms"
                )
        mechanisms = requirement.get("canBeSatisfiedBy")
        if not isinstance(mechanisms, list) or not mechanisms:
            failures.append(f"{context}: Add canBeSatisfiedBy with at least one satisfaction mechanism")
        else:
            for mechanism_index, mechanism in enumerate(mechanisms):
                mechanism_context = f"{context}: canBeSatisfiedBy[{mechanism_index}]"
                if not isinstance(mechanism, dict):
                    failures.append(f"{mechanism_context}: Change mechanism entry to a mapping")
                    continue
                mechanism_type = mechanism.get("mechanism")
                if mechanism_type not in VALID_REQUIREMENT_ANSWER_TYPES:
                    failures.append(
                        f"{mechanism_context}: Set mechanism to one of {sorted(VALID_REQUIREMENT_ANSWER_TYPES)}"
                    )
                criteria = mechanism.get("criteria")
                if isinstance(criteria, dict):
                    capability = criteria.get("capability") or criteria.get("concern")
                    if capability and capability != "any" and capability not in capability_ids:
                        failures.append(
                            f"{mechanism_context}: Set criteria capability '{capability}' to an existing capability ID"
                        )
        applicability = requirement.get("applicability")
        if applicability is not None:
            validate_applicability_shape(applicability, context, failures)
        elif mode == "conditional":
            failures.append(f"{context}: Add applicability rules for conditional requirements")
        if mode == "conditional" and requirement.get("naAllowed") is not True:
            failures.append(f"{context}: Set naAllowed: true for conditional requirements")


def validate_applicability_shape(applicability: Any, context: str, failures: list[str]) -> None:
    if not isinstance(applicability, dict):
        failures.append(f"{context}: Change applicability to a mapping with anyOf or allOf")
        return
    groups = [key for key in ("anyOf", "allOf") if key in applicability]
    if not groups:
        failures.append(f"{context}: Add applicability.anyOf or applicability.allOf")
        return
    for group in groups:
        clauses = applicability.get(group)
        if not isinstance(clauses, list) or not clauses:
            failures.append(f"{context}: Add at least one applicability.{group} clause")
            continue
        for clause_index, clause in enumerate(clauses):
            clause_context = f"{context}: applicability.{group}[{clause_index}]"
            if not isinstance(clause, dict):
                failures.append(f"{clause_context}: Change clause to a mapping")
                continue
            if not is_non_empty(clause.get("field")):
                failures.append(f"{clause_context}: Add field")
            predicates = [key for key in ("equals", "in", "contains", "truthy") if key in clause]
            if not predicates:
                failures.append(f"{clause_context}: Add equals, in, contains, or truthy")
            if "truthy" in clause and not isinstance(clause.get("truthy"), bool):
                failures.append(f"{clause_context}: Set truthy to true or false")
            if "in" in clause and not isinstance(clause.get("in"), list):
                failures.append(f"{clause_context}: Change in to a list")


def validate_applicable_requirements(
    obj: dict[str, Any],
    path: Path,
    requirement_groups: dict[str, dict[str, Any]],
    catalog_by_id: dict[str, dict[str, Any]],
    capability_ids: set[str],
    failures: list[str],
    warnings: list[str],
    active_group_ids: set[str] | None = None,
    require_active_group_disposition: bool = False,
) -> None:
    declared = obj.get("requirementGroups", [])
    if declared is None:
        declared = []
    if not isinstance(declared, list):
        failures.append(f"{path}: Change requirementGroups to a list of requirement_group IDs")
        declared = []
    declared_group_ids = {str(group_id) for group_id in declared if is_non_empty(group_id)}
    for group_id in sorted(declared_group_ids):
        group = requirement_groups.get(group_id)
        if not group:
            failures.append(f"{path}: Replace unknown requirement group '{group_id}' with an existing requirement_group ID")
        elif group.get("activation") == "workspace" and group_id not in active_group_ids:
            failures.append(
                f"{path}: Activate requirement group '{group_id}' in .draft/workspace.yaml or remove the object claim"
            )

    applicable_group_ids = applicable_requirement_group_ids(
        obj,
        requirement_groups,
        active_group_ids,
        require_active_group_disposition,
    )
    for group_id in applicable_group_ids:
        group = requirement_groups[group_id]
        try:
            requirements = resolve_requirement_group_requirements(group_id, requirement_groups)
        except (KeyError, ValueError) as exc:
            failures.append(f"{path}: Fix requirement group inheritance for '{group_id}' ({exc})")
            continue
        for requirement in requirements:
            if not isinstance(requirement, dict) or not requirement_applies_to_object(requirement, obj):
                continue
            valid, message = validate_requirement(obj, requirement, group_id, catalog_by_id)
            if not valid:
                record_requirement_gap(obj, path, message, failures, warnings)
    validate_requirement_implementations(
        obj,
        path,
        requirement_groups,
        catalog_by_id,
        failures,
        warnings,
        active_group_ids,
        require_active_group_disposition,
    )


def validate_requirement_implementations(
    obj: dict[str, Any],
    path: Path,
    requirement_groups: dict[str, dict[str, Any]],
    catalog_by_id: dict[str, dict[str, Any]],
    failures: list[str],
    warnings: list[str],
    active_group_ids: set[str] | None = None,
    require_active_group_disposition: bool = False,
) -> None:
    scope = object_scope(obj)
    if not scope:
        return
    active_group_ids = active_group_ids or set()
    requirement_groups_field = obj.get("requirementGroups", []) or []
    declared_group_ids = {str(group_id) for group_id in requirement_groups_field} if isinstance(requirement_groups_field, list) else set()

    if require_active_group_disposition:
        missing_active = sorted(
            group_id
            for group_id in active_group_ids
            if group_id not in declared_group_ids
            and requirement_group_applies_to_object(requirement_groups.get(group_id, {}), obj)
        )
        if missing_active:
            record_requirement_gap(
                obj,
                path,
                f"[{obj.get('id', 'unknown')}] Add requirementGroups entries for active requirement groups {missing_active} or record not-applicable dispositions",
                failures,
                warnings,
            )

    implementations = obj.get("requirementImplementations", [])
    if implementations is None:
        implementations = []
    if not isinstance(implementations, list):
        failures.append(f"{path}: Change requirementImplementations to a list")
        return

    implementations_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for index, implementation in enumerate(implementations):
        context = f"{path}: requirementImplementations[{index}]"
        if not isinstance(implementation, dict):
            failures.append(f"{context}: Change requirement implementation to a mapping")
            continue
        group_id = implementation.get("requirementGroup")
        requirement_id = implementation.get("requirementId")
        if not is_non_empty(group_id) or not is_non_empty(requirement_id):
            failures.append(f"{context}: Add requirementGroup and requirementId")
            continue
        group = requirement_groups.get(str(group_id))
        if not group:
            failures.append(f"{context}: Set requirementGroup to an existing requirement_group ID")
            continue
        if group.get("activation") == "workspace" and str(group_id) not in declared_group_ids:
            failures.append(f"{context}: Add '{group_id}' to requirementGroups before recording evidence")
            continue
        requirement = find_requirement(group, str(requirement_id), requirement_groups)
        if not requirement or not requirement_applies_to_object(requirement, obj):
            failures.append(f"{context}: Set requirementId to an applicable requirement in '{group_id}'")
            continue
        status = implementation.get("status")
        if status == "not-compliant":
            record_requirement_gap(
                obj,
                path,
                f"[{obj.get('id', 'unknown')}] Resolve not-compliant requirement '{requirement_id}' from {group_id} before approving this object",
                failures,
                warnings,
            )
            implementations_by_key[(str(group_id), str(requirement_id))] = implementation
            continue
        if status == "not-applicable":
            if requirement.get("naAllowed") is not True:
                failures.append(f"{context}: Use not-applicable only when the requirement sets naAllowed: true")
            implementations_by_key[(str(group_id), str(requirement_id))] = implementation
            continue
        if status != "satisfied":
            failures.append(f"{context}: Set status to satisfied, not-applicable, or not-compliant")
            continue
        mechanism = implementation.get("mechanism")
        valid_answer_types = requirement.get("validAnswerTypes", [])
        if mechanism and mechanism not in valid_answer_types:
            failures.append(
                f"{context}: Set mechanism to one of {valid_answer_types} for requirement '{requirement_id}'"
            )
        elif mechanism and not implementation_resolves(obj, implementation, catalog_by_id):
            record_requirement_gap(
                obj,
                path,
                f"[{obj.get('id', 'unknown')}] Update requirementImplementation for '{requirement_id}' because mechanism '{mechanism}' does not resolve against the object",
                failures,
                warnings,
            )
        implementations_by_key[(str(group_id), str(requirement_id))] = implementation

    for group_id in sorted(declared_group_ids & active_group_ids):
        group = requirement_groups.get(group_id)
        if not group or group.get("activation") != "workspace" or not requirement_group_applies_to_object(group, obj):
            continue
        for requirement in resolve_requirement_group_requirements(group_id, requirement_groups):
            if not isinstance(requirement, dict) or not requirement_applies_to_object(requirement, obj):
                continue
            key = (group_id, str(requirement.get("id")))
            if key not in implementations_by_key:
                record_requirement_gap(
                    obj,
                    path,
                    f"[{obj.get('id', 'unknown')}] Add requirementImplementation for active requirement '{requirement.get('id')}' from {group_id}",
                    failures,
                    warnings,
                )


def find_requirement(
    group: dict[str, Any],
    requirement_id: str,
    requirement_groups: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    group_id = str(group.get("id") or "")
    for requirement in resolve_requirement_group_requirements(group_id, requirement_groups):
        if isinstance(requirement, dict) and requirement.get("id") == requirement_id:
            return requirement
    return None


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

    files = discover_workspace_yaml_files(workspace_root)
    schemas = load_schemas(SCHEMA_ROOT)
    objects: dict[Path, dict[str, Any]] = {}
    failures: list[str] = []
    warnings: list[str] = []
    workspace_requirements = load_workspace_requirements(workspace_root, failures)

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
    requirement_groups = {
        object_id: obj for object_id, obj in catalog_by_id.items() if obj.get("type") == "requirement_group"
    }
    capability_ids = {object_id for object_id, obj in catalog_by_id.items() if obj.get("type") == "capability"}
    domain_ids = {object_id for object_id, obj in catalog_by_id.items() if obj.get("type") == "domain"}
    decision_record_ids = {object_id for object_id, obj in catalog_by_id.items() if obj.get("type") == "decision_record"}
    appliance_component_ids = {
        object_id for object_id, obj in catalog_by_id.items() if obj.get("type") == "appliance_component"
    }
    catalog_ids = set(catalog_by_id.keys())
    active_group_ids = workspace_requirements["active_groups"]
    require_active_group_disposition = workspace_requirements["require_active_group_disposition"]
    validate_workspace_requirements(workspace_root, active_group_ids, catalog_by_id, failures)

    for path, obj in objects.items():
        validate_against_schema(obj, path, schemas, failures)
        if obj.get("type") == "capability":
            validate_capability(obj, path, catalog_by_id, domain_ids, failures)
        if obj.get("type") == "requirement_group":
            validate_requirement_group(obj, path, capability_ids, failures)
        if obj.get("type") in {"technology_component", "appliance_component"}:
            validate_component(
                obj,
                path,
                requirement_groups,
                catalog_by_id,
                capability_ids,
                failures,
                warnings,
                active_group_ids,
                require_active_group_disposition,
            )
        if obj.get("type") == "decision_record":
            validate_decision_record(obj, path, failures, warnings)
        if obj.get("type") == "drafting_session":
            validate_drafting_session(
                obj,
                path,
                requirement_groups,
                catalog_by_id,
                capability_ids,
                failures,
                warnings,
                active_group_ids,
                require_active_group_disposition,
            )
        if obj.get("type") in STANDARD_TYPES:
            validate_standard(
                obj,
                path,
                requirement_groups,
                catalog_by_id,
                catalog_ids,
                capability_ids,
                failures,
                warnings,
                active_group_ids,
                require_active_group_disposition,
            )
        if obj.get("type") == "reference_architecture":
            validate_ra(
                obj,
                path,
                requirement_groups,
                catalog_by_id,
                capability_ids,
                failures,
                warnings,
                active_group_ids,
                require_active_group_disposition,
            )
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
            validate_software_deployment_pattern(
                obj,
                path,
                requirement_groups,
                catalog_by_id,
                capability_ids,
                failures,
                warnings,
                active_group_ids,
                require_active_group_disposition,
            )
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
