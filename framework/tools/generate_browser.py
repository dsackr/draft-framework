#!/usr/bin/env python3
# ARCHITECTURE CONTRACT
# This generator is data-driven. The following must remain true:
# 1. No catalog object UIDs are hardcoded in this file.
# 2. No product names (accelify, hrlinks, etc.) appear in rendering logic.
# 3. All relationships are derived from the cross-reference index built at load time.
# 4. All object types are rendered via type dispatch — unknown types get a generic fallback.
# 5. Adding a new catalog object type requires only: (a) a new YAML file, (b) optionally a new renderer.
#    No other changes to this file are required for the new type to appear in list view.
# Note: location icon inference uses generic string heuristics only; unknown patterns always fall back to a generic icon.
from __future__ import annotations

import argparse
import base64
import copy
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


FRAMEWORK_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = FRAMEWORK_ROOT.parent
OUTPUT_PATH = REPO_ROOT / "docs" / "index.html"
SCHEMA_ROOT = FRAMEWORK_ROOT / "schemas"
BASE_CONFIGURATION_ROOT = FRAMEWORK_ROOT / "configurations"
DEFAULT_WORKSPACE_ROOT = REPO_ROOT / "examples"
LOGO_PATH = REPO_ROOT / "draft-logo.png"
LEGACY_LOGO_PATH = REPO_ROOT / "draftlogo.png"
CATALOG_FOLDERS = [
    "capabilities",
    "requirement-groups",
    "object-patches",
    "technology-components",
    "edge-gateway-services",
    "hosts",
    "runtime-services",
    "data-at-rest-services",
    "product-services",
    "decision-records",
    "objects",
    "object-types",
    "automation-targets",
    "sessions",
    "software-deployment-patterns",
    "reference-architectures",
    "domains",
]
LIFECYCLE_COLORS = {
    "preferred": "1f8a5b",
    "existing-only": "2a6fdb",
    "deprecated": "c47a14",
    "retired": "b93a3a",
    "candidate": "7c3a6b",
    "unknown": "7a6e60",
}
REF_CONTAINER_KEYS = {
    "ref",
    "runsOn",
    "followsReferenceArchitecture",
    "host",
    "primaryTechnologyComponent",
    "operatingSystemComponent",
    "computePlatformComponent",
    "inherits",
    "platformDependency",
    "linkedSoftwareDeployment",
    "primaryObjectUid",
    "riskRef",
    "controls",
    "domain",
    "relatedCapability",
    "requirementGroup",
    "target",
}
UID_PATTERN = re.compile(r"^[0-9A-HJKMNP-TV-Z]{10}-[0-9A-HJKMNP-TV-Z]{4}$")


def is_product_service_classification(obj: dict[str, Any]) -> bool:
    return obj.get("type") == "product_service"


def is_saas_service_classification(obj: dict[str, Any]) -> bool:
    return obj.get("type") in {"runtime_service", "data_at_rest_service", "edge_gateway_service"} and obj.get("deliveryModel") == "saas"


def is_paas_service_classification(obj: dict[str, Any]) -> bool:
    return obj.get("type") in {"runtime_service", "data_at_rest_service", "edge_gateway_service"} and obj.get("deliveryModel") == "paas"


def is_database_service(obj: dict[str, Any]) -> bool:
    return obj.get("type") == "data_at_rest_service"


def is_general_service(obj: dict[str, Any]) -> bool:
    return obj.get("type") == "runtime_service"


def discover_yaml_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for folder_name in CATALOG_FOLDERS:
        folder = root / folder_name
        if not folder.exists():
            continue
        files.extend(sorted(folder.rglob("*.yaml")))
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


def display_path(path: Path) -> str:
    for root in (REPO_ROOT, Path.cwd()):
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            continue
    return path.as_posix()


def load_workspace_requirements(workspace_root: Path) -> dict[str, Any]:
    config_path = workspace_root / ".draft" / "workspace.yaml"
    if not config_path.exists():
        return {"activeRequirementGroups": [], "requireActiveRequirementGroupDisposition": False}
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {"activeRequirementGroups": [], "requireActiveRequirementGroupDisposition": False}
    if not isinstance(data, dict):
        return {"activeRequirementGroups": [], "requireActiveRequirementGroupDisposition": False}
    requirements = data.get("requirements") or {}
    if not isinstance(requirements, dict):
        return {"activeRequirementGroups": [], "requireActiveRequirementGroupDisposition": False}
    active = requirements.get("activeRequirementGroups") or []
    active_groups = [str(group_id) for group_id in active if str(group_id).strip()] if isinstance(active, list) else []
    return {
        "activeRequirementGroups": active_groups,
        "requireActiveRequirementGroupDisposition": requirements.get("requireActiveRequirementGroupDisposition") is True,
    }


def load_workspace_business_taxonomy(workspace_root: Path) -> dict[str, Any]:
    config_path = workspace_root / ".draft" / "workspace.yaml"
    if not config_path.exists():
        return {"pillars": [], "requireSoftwareDeploymentPatternPillar": False}
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {"pillars": [], "requireSoftwareDeploymentPatternPillar": False}
    if not isinstance(data, dict):
        return {"pillars": [], "requireSoftwareDeploymentPatternPillar": False}
    taxonomy = data.get("businessTaxonomy") or {}
    if not isinstance(taxonomy, dict):
        return {"pillars": [], "requireSoftwareDeploymentPatternPillar": False}
    pillars = taxonomy.get("pillars") or []
    if not isinstance(pillars, list):
        pillars = []
    return {
        "pillars": [pillar for pillar in pillars if isinstance(pillar, dict) and str(pillar.get("id") or "").strip()],
        "requireSoftwareDeploymentPatternPillar": taxonomy.get("requireSoftwareDeploymentPatternPillar") is True,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the static DRAFT browser for a workspace.")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=DEFAULT_WORKSPACE_ROOT,
        help="Workspace root containing catalog/ and configurations/. Defaults to examples/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
        help="HTML output path. Defaults to docs/index.html.",
    )
    return parser.parse_args(argv)


def load_objects(workspace_root: Path) -> dict[str, dict[str, Any]]:
    objects: dict[str, dict[str, Any]] = {}
    for root in workspace_yaml_roots(workspace_root):
        for path in discover_yaml_files(root):
            with path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
            if isinstance(data, dict) and data.get("uid"):
                data["_source"] = display_path(path)
                objects[str(data["uid"])] = data
    return apply_object_patches(objects)


def deep_merge(base: Any, patch: Any) -> Any:
    if isinstance(base, dict) and isinstance(patch, dict):
        merged = copy.deepcopy(base)
        for key, value in patch.items():
            if key in {"uid", "id", "type"}:
                continue
            merged[key] = deep_merge(merged.get(key), value)
        return merged
    return copy.deepcopy(patch)


def apply_object_patches(objects: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    patched = dict(objects)
    for obj in objects.values():
        if obj.get("type") != "object_patch":
            continue
        target_id = str(obj.get("target", ""))
        patch = obj.get("patch")
        if not target_id or target_id not in patched or not isinstance(patch, dict):
            continue
        patched[target_id] = deep_merge(patched[target_id], patch)
    return patched


def load_schemas(root: Path) -> list[dict[str, Any]]:
    schemas: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        if isinstance(data, dict):
            data["_schema_path"] = display_path(path)
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


def schema_specificity(schema: dict[str, Any]) -> int:
    return sum(1 for key in ("subtype", "category", "deliveryModel") if is_non_empty(schema.get(key)))


def select_schema(obj: dict[str, Any], schemas: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates: list[dict[str, Any]] = []
    for schema in schemas:
        if schema.get("type") != obj.get("type"):
            continue
        if is_non_empty(schema.get("subtype")) and schema.get("subtype") != obj.get("subtype"):
            continue
        if is_non_empty(schema.get("category")) and schema.get("category") != obj.get("category"):
            continue
        if is_non_empty(schema.get("deliveryModel")) and schema.get("deliveryModel") != obj.get("deliveryModel"):
            continue
        candidates.append(schema)
    if not candidates:
        return None
    return sorted(candidates, key=schema_specificity, reverse=True)[0]


def repository_web_url(root: Path) -> str:
    try:
        remote = subprocess.check_output(
            ["git", "-C", str(root), "config", "--get", "remote.origin.url"],
            text=True,
        ).strip()
    except Exception:  # noqa: BLE001
        return ""
    if remote.startswith("git@github.com:"):
        remote = "https://github.com/" + remote[len("git@github.com:"):]
    if remote.endswith(".git"):
        remote = remote[:-4]
    return remote if remote.startswith("https://github.com/") else ""


def repository_name_from_url(url: str) -> str:
    if not url:
        return ""
    return url.rstrip("/").split("/")[-1] or ""


def workspace_repository_name(workspace_root: Path) -> str:
    config_path = workspace_root / ".draft" / "workspace.yaml"
    if config_path.exists():
        try:
            config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001
            config = {}
        repository = config.get("repository") if isinstance(config, dict) else {}
        if isinstance(repository, dict):
            owner = str(repository.get("owner") or "").strip()
            name = str(repository.get("name") or "").strip()
            if owner and name:
                return f"{owner}/{name}"
            if name:
                return name
    workspace_url = repository_web_url(workspace_root)
    if workspace_url:
        parts = workspace_url.rstrip("/").split("/")
        if len(parts) >= 2:
            return "/".join(parts[-2:])
    framework_url = repository_web_url(REPO_ROOT)
    return repository_name_from_url(framework_url) or workspace_root.name


def logo_data_uri() -> str:
    logo_path = LOGO_PATH if LOGO_PATH.exists() else LEGACY_LOGO_PATH
    if not logo_path.exists():
        return ""
    encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def is_probable_reference_key(path: str) -> bool:
    key = path.rsplit(".", 1)[-1]
    return key in REF_CONTAINER_KEYS or key.endswith("Refs")


def is_object_ref(value: Any, path: str, known_uids: set[str]) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    if value in known_uids:
        return True
    return is_probable_reference_key(path) and bool(UID_PATTERN.match(value))


def extract_refs(node: Any, known_uids: set[str], path: str = "") -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            child_path = f"{path}.{key}" if path else key
            if key in REF_CONTAINER_KEYS and is_object_ref(value, child_path, known_uids):
                refs.append((value, child_path))
            elif key.endswith("Refs") and isinstance(value, list):
                for index, item in enumerate(value):
                    if is_object_ref(item, f"{child_path}[{index}]", known_uids):
                        refs.append((item, f"{child_path}[{index}]"))
            else:
                refs.extend(extract_refs(value, known_uids, child_path))
    elif isinstance(node, list):
        if path.endswith(".appliesTo"):
            return refs
        for index, item in enumerate(node):
            item_path = f"{path}[{index}]"
            if is_object_ref(item, item_path, known_uids):
                refs.append((item, f"{path}[{index}]"))
            else:
                refs.extend(extract_refs(item, known_uids, item_path))
    return refs


def build_reference_index(registry: dict[str, dict[str, Any]]) -> tuple[dict[str, list[dict[str, str]]], dict[str, list[dict[str, str]]], list[str]]:
    outbound: dict[str, list[dict[str, str]]] = {}
    referenced_by: dict[str, list[dict[str, str]]] = {}
    warnings: list[str] = []
    known_uids = set(registry)
    for object_uid, obj in registry.items():
        refs = extract_refs(obj, known_uids)
        outbound[object_uid] = [{"target": target, "path": ref_path} for target, ref_path in refs]
        for target, ref_path in refs:
            referenced_by.setdefault(target, []).append({"source": object_uid, "path": ref_path})
            if target not in registry:
                warnings.append(f"Warning: {object_uid} references missing object '{target}' via {ref_path}")
    return outbound, referenced_by, warnings


def shape_for(obj: dict[str, Any]) -> str:
    if obj["type"] == "reference_architecture":
        return "hexagon"
    if obj["type"] == "software_deployment_pattern":
        return "star"
    if obj["type"] == "drafting_session":
        return "round-rectangle"
    if obj["type"] == "capability":
        return "ellipse"
    if obj["type"] == "requirement_group":
        return "barrel"
    if obj["type"] == "decision_record":
        return "round-rectangle"
    if obj["type"] == "technology_component":
        return "ellipse"
    if obj["type"] == "edge_gateway_service":
        return "diamond"
    if obj["type"] in {"host", "runtime_service", "data_at_rest_service", "product_service"}:
        return "round-rectangle" if obj["type"] == "host" else "diamond"
    return "round-rectangle"


def to_json(value: Any) -> str:
    return json.dumps(value, indent=2, default=str)


def humanize_slug(value: str) -> str:
    return value.replace("-", " ").title()


def filter_type_for(obj: dict[str, Any]) -> str:
    return str(obj.get("type", "unknown"))


def type_label_for(obj: dict[str, Any]) -> str:
    if obj["type"] == "technology_component":
        classification = humanize_slug(str(obj.get("classification", "unknown")))
        return f"Technology Component / {classification}"
    if obj["type"] == "edge_gateway_service":
        delivery_model = str(obj.get("deliveryModel", "self-managed")).replace("-", " ").title()
        return f"Edge/Gateway Service / {delivery_model}"
    if obj["type"] == "capability":
        return "Capability"
    if obj["type"] == "requirement_group":
        return "Requirement Group"
    if obj["type"] == "decision_record":
        return f"Decision Record / {obj.get('category', 'risk')}"
    if obj["type"] == "reference_architecture":
        return "Reference Architecture"
    if obj["type"] == "software_deployment_pattern":
        return "Software Deployment Pattern"
    if obj["type"] == "drafting_session":
        return "Drafting Session"
    if obj["type"] == "host":
        return "Host"
    if obj["type"] == "runtime_service":
        delivery_model = str(obj.get("deliveryModel", "")).replace("-", " ").title()
        return f"Runtime Service / {delivery_model}" if delivery_model else "Runtime Service"
    if obj["type"] == "data_at_rest_service":
        delivery_model = str(obj.get("deliveryModel", "")).replace("-", " ").title()
        return f"Data-at-Rest Service / {delivery_model}" if delivery_model else "Data-at-Rest Service"
    if is_product_service_classification(obj):
        return "Product Service"
    if obj["type"] == "domain":
        return "Strategy Domain"
    return str(obj.get("type", "unknown")).replace("_", " ").title()


def internal_component_refs(obj: dict[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    seen: set[str] = set()

    for component in obj.get("internalComponents", []):
        ref = component.get("ref")
        if ref and ref not in seen:
            refs.append({"ref": ref, "role": component.get("role", "component")})
            seen.add(ref)

    for field_name, role in (
        ("operatingSystemComponent", "os"),
        ("computePlatformComponent", "hardware"),
        ("host", "host"),
        ("primaryTechnologyComponent", "function"),
    ):
        ref = obj.get(field_name)
        if ref and ref not in seen:
            refs.append({"ref": ref, "role": role})
            seen.add(ref)

    return refs


def build_requirement_payload(registry: dict[str, dict[str, Any]], workspace_root: Path) -> dict[str, Any]:
    workspace_requirements = load_workspace_requirements(workspace_root)
    groups = sorted(
        [obj for obj in registry.values() if obj.get("type") == "requirement_group"],
        key=lambda item: item.get("name", ""),
    )
    active_ids = set(workspace_requirements["activeRequirementGroups"])
    return {
        "groups": [
            {
                "id": group["uid"],
                "uid": group["uid"],
                "name": group.get("name", group["uid"]),
                "activation": group.get("activation", ""),
                "catalogStatus": group.get("catalogStatus", ""),
                "provider": group.get("provider", {}),
                "authority": group.get("authority", {}),
                "active": group["uid"] in active_ids,
                "description": group.get("description", ""),
                "requirementCount": len(group.get("requirements", [])) if isinstance(group.get("requirements"), list) else 0,
            }
            for group in groups
        ],
        "activeRequirementGroups": workspace_requirements["activeRequirementGroups"],
        "requireActiveRequirementGroupDisposition": workspace_requirements["requireActiveRequirementGroupDisposition"],
    }


def build_browser_payload(registry: dict[str, dict[str, Any]], workspace_root: Path) -> dict[str, Any]:
    objects = list(registry.values())
    schemas = load_schemas(SCHEMA_ROOT)
    outbound_refs, referenced_by, warnings = build_reference_index(registry)
    risk_marked_rbb_ids = {
        deployed.get("ref")
        for obj in objects
        if obj.get("type") == "software_deployment_pattern"
        for group in obj.get("serviceGroups", [])
        if isinstance(group, dict)
        for deployed in group.get("deployableObjects", [])
        if isinstance(deployed, dict) and deployed.get("riskRef")
    }
    browser_objects: list[dict[str, Any]] = []

    def browser_lifecycle_status(obj: dict[str, Any]) -> str:
        if obj.get("type") == "technology_component":
            return ""
        return obj.get("lifecycleStatus", "unknown")

    def browser_lifecycle_color(status: str) -> str:
        if not status:
            return "#64748b"
        return f"#{LIFECYCLE_COLORS.get(status, LIFECYCLE_COLORS['unknown'])}"

    for obj in objects:
        object_id = obj["uid"]
        schema = select_schema(obj, schemas) or {}
        lifecycle_status = browser_lifecycle_status(obj)
        schema_meta = {
            "requiredFields": schema.get("requiredFields", []),
            "optionalFields": schema.get("optionalFields", []),
            "fieldTypes": schema.get("fieldTypes", {}),
            "enumFields": schema.get("enumFields", {}),
            "enumListFields": schema.get("enumListFields", {}),
            "collectionSchemas": schema.get("collectionSchemas", {}),
            "schemaPath": schema.get("_schema_path", ""),
        }
        browser_objects.append(
            {
                "id": object_id,
                "uid": object_id,
                "name": obj["name"],
                "aliases": obj.get("aliases", []),
                "type": obj["type"],
                "typeLabel": type_label_for(obj),
                "filterType": filter_type_for(obj),
                "category": obj.get("category", ""),
                "deliveryModel": obj.get("deliveryModel", ""),
                "domain": obj.get("domain", ""),
                "description": obj.get("description", ""),
                "version": obj.get("version", ""),
                "catalogStatus": obj.get("catalogStatus", ""),
                "lifecycleStatus": lifecycle_status,
                "status": obj.get("status", ""),
                "businessContext": obj.get("businessContext", {}),
                "product": obj.get("product", ""),
                "runsOn": obj.get("runsOn", ""),
                "subtype": obj.get("subtype", ""),
                "vendor": obj.get("vendor", ""),
                "productName": obj.get("productName", ""),
                "productVersion": obj.get("productVersion", ""),
                "classification": obj.get("classification", ""),
                "platformDependency": obj.get("platformDependency", ""),
                "capabilities": obj.get("capabilities", []),
                "configurations": obj.get("configurations", []),
                "networkPlacement": obj.get("networkPlacement", ""),
                "patchingOwner": obj.get("patchingOwner", ""),
                "complianceCerts": obj.get("complianceCerts", []),
                "requirementGroups": obj.get("requirementGroups", []),
                "requirementImplementations": obj.get("requirementImplementations", []),
                "dataLeavesInfrastructure": obj.get("dataLeavesInfrastructure", None),
                "dataResidencyCommitment": obj.get("dataResidencyCommitment", ""),
                "dpaNotes": obj.get("dpaNotes", ""),
                "vendorSLA": obj.get("vendorSLA", ""),
                "authenticationModel": obj.get("authenticationModel", ""),
                "incidentNotificationProcess": obj.get("incidentNotificationProcess", ""),
                "owner": obj.get("owner", {}),
                "definitionOwner": obj.get("definitionOwner", {}),
                "provider": obj.get("provider", {}),
                "authority": obj.get("authority", {}),
                "shape": shape_for(obj),
                "color": browser_lifecycle_color(lifecycle_status),
                "source": obj.get("_source", ""),
                "tags": obj.get("tags", []),
                "ardCategory": obj.get("category", "") if obj.get("type") == "decision_record" else "",
                "internalComponents": internal_component_refs(obj),
                "externalInteractions": obj.get("externalInteractions", []),
                "architecturalDecisions": obj.get("architecturalDecisions", {}),
                "requirements": obj.get("requirements", []),
                "implementations": obj.get("implementations", []),
                "appliesTo": obj.get("appliesTo", {}),
                "inherits": obj.get("inherits", ""),
                "scalingUnits": obj.get("scalingUnits", []),
                "serviceGroups": obj.get("serviceGroups", []),
                "followsReferenceArchitecture": obj.get("followsReferenceArchitecture", ""),
                "decisionRecords": obj.get("decisionRecords", []),
                "affectedComponent": obj.get("affectedComponent", ""),
                "impact": obj.get("impact", ""),
                "mitigationPath": obj.get("mitigationPath", ""),
                "decisionRationale": obj.get("decisionRationale", ""),
                "relatedDecisionRecords": obj.get("relatedDecisionRecords", []),
                "linkedSoftwareDeployment": obj.get("linkedSoftwareDeployment", ""),
                "primaryObjectType": obj.get("primaryObjectType", ""),
                "primaryObjectUid": obj.get("primaryObjectUid", ""),
                "generatedObjects": obj.get("generatedObjects", []),
                "unresolvedQuestions": obj.get("unresolvedQuestions", []),
                "assumptions": obj.get("assumptions", []),
                "nextSteps": obj.get("nextSteps", []),
                "defaultSelection": obj.get("defaultSelection", False),
                "requirementCount": len(obj.get("requirements", [])) if obj.get("type") == "requirement_group" and isinstance(obj.get("requirements"), list) else 0,
                "hasRiskRef": object_id in risk_marked_rbb_ids,
                "outboundRefs": outbound_refs.get(object_id, []),
                "referencedBy": referenced_by.get(object_id, []),
                "editorSchema": schema_meta,
                "detail": to_json(obj),
                "existsInCatalog": True,
            }
        )

    browser_lookup = {obj["uid"]: obj for obj in browser_objects}
    filter_values = sorted({obj["type"] for obj in objects})
    impact_lifecycle_types = {
        "reference_architecture",
        "software_deployment_pattern",
        "host",
        "runtime_service",
        "data_at_rest_service",
        "edge_gateway_service",
        "product_service",
    }
    lifecycle_values = sorted(
        {obj.get("lifecycleStatus", "unknown") for obj in objects if obj.get("type") in impact_lifecycle_types},
        key=lambda value: ["preferred", "existing-only", "candidate", "deprecated", "retired", "unknown"].index(value)
        if value in {"preferred", "existing-only", "candidate", "deprecated", "retired", "unknown"}
        else 999,
    )
    return {
        "objects": browser_objects,
        "lookup": browser_lookup,
        "lifecycleColors": LIFECYCLE_COLORS,
        "filterValues": filter_values,
        "lifecycleValues": lifecycle_values,
        "referencedBy": referenced_by,
        "warnings": warnings,
        "requirements": build_requirement_payload(registry, workspace_root),
        "businessTaxonomy": load_workspace_business_taxonomy(workspace_root),
        "repoUrl": repository_web_url(workspace_root) or repository_web_url(REPO_ROOT),
        "catalogName": workspace_repository_name(workspace_root),
        "logoDataUri": logo_data_uri(),
    }


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DRAFT Framework Toolkit</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.29.2/cytoscape.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/js-yaml@4.1.0/dist/js-yaml.min.js"></script>
  <style>
    :root {
      color-scheme: light;
      /* Light + plum theme tokens (re-skin v1) */
      --page: #f6f4ef;       /* warm off-white background */
      --panel: #ffffff;      /* sidebar / panel surfaces */
      --card: #ffffff;       /* card surface */
      --surface: #faf8f3;        /* default soft surface for inset bands */
      --surface-soft: #f3efe6;   /* slightly tinted soft surface */
      --surface-strong: #ffffff; /* solid surface for prominent panels */
      --border: #e7e1d6;     /* warm hairline */
      --border-strong: #d6cfc1;
      --muted: #7a6e60;      /* secondary text */
      --text: #1f1a14;       /* primary text */
      --subtle: #3a342c;     /* tertiary headings / strong copy */
      --accent: #7c3a6b;     /* plum primary */
      --accent-soft: rgba(124, 58, 107, 0.10);
      --accent-strong: #5d2950;
      --shadow-sm: 0 1px 2px rgba(31, 26, 20, 0.04), 0 1px 3px rgba(31, 26, 20, 0.06);
      --shadow-md: 0 4px 12px rgba(31, 26, 20, 0.06), 0 2px 4px rgba(31, 26, 20, 0.04);
      --shadow-lg: 0 12px 28px rgba(31, 26, 20, 0.08), 0 4px 10px rgba(31, 26, 20, 0.05);
      /* Lifecycle accents (consistent across views) */
      --lc-preferred: #1f8a5b;
      --lc-existing: #2a6fdb;
      --lc-deprecated: #c47a14;
      --lc-retired: #b93a3a;
      --lc-candidate: #7c3a6b;
      --lc-unknown: #7a6e60;
    }
    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      min-height: 100%;
      background: var(--page);
      color: var(--text);
      font-family: "SF Pro Display", "Segoe UI", sans-serif;
    }
    .page-shell {
      min-height: 100vh;
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr);
      gap: 1px;
      background: var(--border);
    }
    .sidebar,
    .main {
      background: #ffffff;
    }
    .sidebar {
      padding: 24px 20px;
      border-right: 1px solid #e7e1d6;
    }
    .sidebar h1 {
      margin: 0;
      font-size: 18px;
      letter-spacing: 0.02em;
    }
    .browser-brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .browser-logo {
      width: 48px;
      height: 48px;
      object-fit: contain;
      flex: 0 0 auto;
    }
    .catalog-name {
      color: var(--subtle);
      font-size: 13px;
      margin-top: 4px;
      overflow-wrap: anywhere;
    }
    .mode-badge {
      display: inline-flex;
      width: fit-content;
      margin-top: 10px;
      padding: 5px 9px;
      border: 1px solid rgba(124, 58, 107, 0.5);
      border-radius: 999px;
      color: #7c3a6b;
      background: rgba(124, 58, 107, 0.10);
      font-size: 11px;
      font-weight: 700;
    }
    .sidebar p {
      margin: 10px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.6;
    }
    .sidebar-stack {
      display: grid;
      gap: 18px;
    }
    .sidebar-block,
    .legend-block {
      margin-top: 28px;
      padding-top: 20px;
      border-top: 1px solid #d6cfc1;
    }
    .legend-title {
      margin: 0 0 12px;
      font-size: 12px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .legend-list {
      display: grid;
      gap: 10px;
    }
    .legend-item,
    .current-filter {
      display: flex;
      align-items: center;
      gap: 10px;
      color: var(--subtle);
      font-size: 13px;
    }
    .dot {
      width: 12px;
      height: 12px;
      border-radius: 999px;
      border: 1px solid rgba(31, 26, 20, 0.15);
      flex: 0 0 auto;
    }
    .main {
      padding: 28px;
    }
    .view-shell {
      display: grid;
      gap: 22px;
    }
    .dashboard-alerts {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 12px;
    }
    .alert-card {
      display: grid;
      grid-template-columns: auto 1fr;
      grid-template-rows: auto auto;
      column-gap: 12px;
      row-gap: 4px;
      align-items: baseline;
      text-align: left;
      padding: 14px 16px;
      border: 1px solid var(--border);
      border-radius: 12px;
      background: var(--card);
      box-shadow: var(--shadow-sm);
      cursor: pointer;
      font: inherit;
      color: var(--text);
      transition: border-color 120ms ease, transform 120ms ease, box-shadow 120ms ease;
    }
    .alert-card:hover {
      border-color: var(--border-strong);
      transform: translateY(-1px);
      box-shadow: var(--shadow-md);
    }
    .alert-card:focus-visible {
      outline: 2px solid var(--accent);
      outline-offset: 2px;
    }
    .alert-card.sev-critical { border-left: 4px solid #b91c1c; }
    .alert-card.sev-warning  { border-left: 4px solid #b45309; }
    .alert-card.sev-info     { border-left: 4px solid var(--accent); }
    .alert-sev {
      grid-column: 1;
      grid-row: 1;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .alert-card.sev-critical .alert-sev { color: #b91c1c; }
    .alert-card.sev-warning  .alert-sev { color: #b45309; }
    .alert-card.sev-info     .alert-sev { color: var(--accent); }
    .alert-label {
      grid-column: 2;
      grid-row: 1;
      font-size: 14px;
      font-weight: 600;
    }
    .alert-detail {
      grid-column: 1 / -1;
      grid-row: 2;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }
    .executive-hero {
      position: relative;
      overflow: hidden;
      border: 1px solid rgba(124, 58, 107, 0.32);
      border-radius: 18px;
      padding: 30px;
      min-height: 260px;
      background:
        linear-gradient(135deg, rgba(124, 58, 107, 0.12), #ffffff 46%, rgba(217, 119, 87, 0.10)),
        repeating-linear-gradient(90deg, rgba(122, 110, 96, 0.05) 0, rgba(122, 110, 96, 0.05) 1px, transparent 1px, transparent 34px);
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(260px, 0.65fr);
      gap: 26px;
      align-items: end;
      box-shadow: 0 18px 42px rgba(31, 26, 20, 0.08);
    }
    .executive-hero h2 {
      margin: 0;
      font-size: 42px;
      line-height: 1.06;
      letter-spacing: 0;
    }
    .executive-hero-copy {
      display: grid;
      grid-template-columns: 132px minmax(0, 1fr);
      align-items: start;
      gap: 24px;
    }
    .executive-hero-logo {
      width: 132px;
      height: 132px;
      object-fit: contain;
      flex: 0 0 auto;
      filter: drop-shadow(0 12px 22px rgba(31, 26, 20, 0.08));
    }
    .executive-hero p {
      margin: 14px 0 0;
      color: var(--subtle);
      line-height: 1.6;
      max-width: 780px;
    }
    .executive-hero-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 22px;
    }
    .executive-snapshot {
      display: grid;
      gap: 12px;
      padding: 18px;
      border: 1px solid rgba(122, 110, 96, 0.18);
      border-radius: 16px;
      background: #ffffff;
    }
    .executive-snapshot-row {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 16px;
      color: var(--subtle);
      font-size: 13px;
    }
    .executive-snapshot-row strong {
      color: var(--text);
      font-size: 20px;
    }
    .executive-mosaic {
      display: grid;
      grid-template-columns: repeat(12, minmax(0, 1fr));
      gap: 16px;
      align-items: stretch;
    }
    .executive-tile,
    .executive-panel {
      border: 1px solid var(--border);
      border-radius: 18px;
      background: #ffffff;
      box-shadow: 0 12px 28px rgba(31, 26, 20, 0.06);
    }
    .executive-tile {
      min-height: 148px;
      padding: 18px;
      display: grid;
      gap: 16px;
      align-content: space-between;
      cursor: pointer;
      transition: border-color 120ms ease, transform 120ms ease, box-shadow 120ms ease;
    }
    .executive-tile:hover {
      border-color: rgba(124, 58, 107, 0.7);
      transform: translateY(-2px);
      box-shadow: 0 16px 34px rgba(31, 26, 20, 0.08);
    }
    .executive-tile:focus-visible {
      outline: 2px solid rgba(124, 58, 107, 0.85);
      outline-offset: 2px;
    }
    .executive-tile.large { grid-column: span 5; min-height: 190px; }
    .executive-tile.wide { grid-column: span 6; }
    .executive-tile.medium { grid-column: span 4; }
    .executive-tile.small { grid-column: span 3; }
    .executive-tile.full { grid-column: span 12; }
    .executive-number {
      margin: 0;
      font-size: 58px;
      line-height: 1;
      font-weight: 800;
      letter-spacing: 0;
    }
    .executive-number.big {
      font-size: 58px;
    }
    .executive-tile-title {
      display: grid;
      gap: 8px;
    }
    .executive-tile-title h3 {
      margin: 0;
      font-size: 18px;
      line-height: 1.3;
    }
    .executive-tile-title .executive-number {
      color: var(--text);
      font-size: 58px;
      line-height: 1;
    }
    .executive-tile > p {
      margin: 0;
      color: var(--muted);
      line-height: 1.45;
      font-size: 13px;
    }
    .executive-accent-cyan {
      border-color: rgba(124, 58, 107, 0.55);
      background: linear-gradient(135deg, rgba(124, 58, 107, 0.24), #ffffff 62%);
    }
    .executive-accent-green {
      border-color: rgba(34,197,94,0.38);
      background: linear-gradient(135deg, rgba(34,197,94,0.18), #ffffff 62%);
    }
    .executive-accent-amber {
      border-color: rgba(245,158,11,0.42);
      background: linear-gradient(135deg, rgba(245,158,11,0.20), #ffffff 62%);
    }
    .executive-accent-violet {
      border-color: rgba(168,85,247,0.42);
      background: linear-gradient(135deg, rgba(168,85,247,0.18), #ffffff 62%);
    }
    .executive-accent-rose {
      border-color: rgba(244,63,94,0.38);
      background: linear-gradient(135deg, rgba(244,63,94,0.18), #ffffff 62%);
    }
    .executive-accent-teal {
      border-color: rgba(20,184,166,0.42);
      background: linear-gradient(135deg, rgba(20,184,166,0.20), #ffffff 62%);
    }
    .executive-panel {
      padding: 18px;
      display: grid;
      gap: 14px;
    }
    .executive-panel h3 {
      margin: 0;
      font-size: 15px;
    }
    .executive-panel.wide { grid-column: span 6; }
    .executive-panel.full { grid-column: span 12; }
    .executive-bars {
      display: grid;
      gap: 10px;
    }
    .executive-bar-row {
      display: grid;
      grid-template-columns: 110px minmax(0, 1fr) 42px;
      gap: 10px;
      align-items: center;
      color: var(--subtle);
      font-size: 13px;
    }
    .executive-bar-track {
      height: 10px;
      border-radius: 999px;
      background: #f6f4ef;
      border: 1px solid rgba(122, 110, 96, 0.14);
      overflow: hidden;
    }
    .executive-bar-fill {
      height: 100%;
      min-width: 3px;
      border-radius: 999px;
      background: var(--accent);
    }
    .executive-drilldown {
      display: grid;
      gap: 14px;
    }
    .top-nav {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .nav-button {
      border: 1px solid var(--border);
      border-radius: 999px;
      background: #ffffff;
      color: var(--text);
      padding: 10px 16px;
      font: inherit;
      cursor: pointer;
      transition: border-color 120ms ease, background 120ms ease, transform 120ms ease;
    }
    .nav-button:hover {
      border-color: rgba(124, 58, 107, 0.65);
      transform: translateY(-1px);
    }
    .nav-button.active {
      background: rgba(124, 58, 107, 0.18);
      border-color: rgba(124, 58, 107, 0.7);
      color: #5d2950;
    }
    .nav-button:disabled {
      cursor: default;
      opacity: 0.45;
      transform: none;
    }
    .tab-row,
    .filter-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .tab-button,
    .filter-button,
    .back-button {
      border: 1px solid var(--border);
      border-radius: 999px;
      background: #ffffff;
      color: var(--text);
      padding: 10px 16px;
      font: inherit;
      cursor: pointer;
      transition: border-color 120ms ease, background 120ms ease, transform 120ms ease;
    }
    .tab-button {
      padding: 12px 18px;
      background: #ffffff;
      font-weight: 600;
    }
    .tab-button:hover,
    .filter-button:hover,
    .back-button:hover {
      border-color: rgba(124, 58, 107, 0.65);
      transform: translateY(-1px);
    }
    .tab-button.active,
    .filter-button.active {
      background: rgba(124, 58, 107, 0.18);
      border-color: rgba(124, 58, 107, 0.7);
      color: #5d2950;
    }
    .content-rows {
      display: grid;
      gap: 24px;
    }
    .content-row {
      display: grid;
      gap: 14px;
    }
    .content-row-header {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 16px;
      padding-bottom: 10px;
      border-bottom: 1px solid #e7e1d6;
    }
    .content-row-title {
      margin: 0;
      font-size: 15px;
      letter-spacing: 0.02em;
    }
    .content-row-count {
      color: var(--muted);
      font-size: 12px;
      white-space: nowrap;
    }
    .cards-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: 18px;
    }
    .business-pillar-groups {
      display: grid;
      gap: 18px;
    }
    .business-pillar-group {
      display: grid;
      gap: 12px;
    }
    .business-pillar-header {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 16px;
      padding: 10px 12px;
      border: 1px solid rgba(122, 110, 96, 0.14);
      border-radius: 8px;
      background: #fbfaf6;
    }
    .business-pillar-title {
      margin: 0;
      font-size: 14px;
      color: var(--text);
    }
    .business-pillar-meta {
      color: var(--muted);
      font-size: 12px;
      white-space: nowrap;
    }
    .object-card,
    .interaction-card,
    .decision-card,
    .empty-card,
    .header-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 18px;
    }
    .object-card {
      padding: 18px;
      display: grid;
      gap: 12px;
      cursor: pointer;
      min-height: 168px;
      transition: border-color 120ms ease, transform 120ms ease, box-shadow 120ms ease;
    }
    .object-card:hover {
      border-color: rgba(56,189,248,0.5);
      transform: translateY(-2px);
      box-shadow: 0 12px 24px rgba(2,6,23,0.22);
    }
    .object-card h3 {
      margin: 0;
      font-size: 16px;
      line-height: 1.35;
    }
    .object-id {
      color: var(--muted);
      font-size: 12px;
      word-break: break-word;
    }
    .badges {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 10px;
      border-radius: 999px;
      font-size: 12px;
      border: 1px solid var(--border-strong);
      background: rgba(231,225,214,0.45);
      color: var(--subtle);
    }
    .catalog-approved { border-color: rgba(31,138,91,0.45); color: #1f5b3a; background: rgba(31,138,91,0.10); }
    .catalog-draft { border-color: rgba(196,122,20,0.45); color: #7a4a0c; background: rgba(196,122,20,0.10); }
    .catalog-stub { border-color: rgba(148,163,184,0.35); color: #3a342c; background: rgba(231,225,214,0.45); }
    .ard-risk { border-color: rgba(196,122,20,0.45); color: #7a4a0c; background: rgba(196,122,20,0.10); }
    .ard-decision { border-color: rgba(42,111,219,0.45); color: #1d4f9e; background: rgba(42,111,219,0.10); }
    .ard-status { border-color: rgba(148,163,184,0.35); color: #3a342c; background: rgba(231,225,214,0.45); }
    .ps-badge {
      border-color: rgba(20,184,166,0.45);
      color: #0e6b62;
      background: rgba(20,184,166,0.12);
    }
    .saas-badge {
      border-color: rgba(124,58,107,0.45);
      color: var(--accent-strong);
      background: rgba(124,58,107,0.10);
    }
    .paas-badge {
      border-color: rgba(42,111,219,0.45);
      color: #1d4f9e;
      background: rgba(42,111,219,0.10);
      background: rgba(59,130,246,0.14);
    }
    .appliance-badge {
      border-color: rgba(245,158,11,0.45);
      color: #fde68a;
      background: rgba(245,158,11,0.14);
    }
    .info-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border-radius: 999px;
      padding: 4px 10px;
      font-size: 11px;
      background: rgba(59,130,246,0.18);
      border: 1px solid rgba(59,130,246,0.38);
      color: #bfdbfe;
      width: fit-content;
    }
    .intent-ha {
      border-color: rgba(16,185,129,0.45);
      color: #bbf7d0;
      background: rgba(16,185,129,0.14);
    }
    .intent-sa {
      border-color: rgba(245,158,11,0.45);
      color: #fde68a;
      background: rgba(245,158,11,0.14);
    }
    .ard-link {
      color: #93c5fd;
      cursor: pointer;
      text-decoration: underline;
      text-decoration-color: rgba(147,197,253,0.45);
      text-underline-offset: 2px;
    }
    .ard-link:hover { color: #dbeafe; }
    .risk-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border-radius: 999px;
      padding: 4px 10px;
      font-size: 11px;
      background: rgba(245,158,11,0.18);
      border: 1px solid rgba(245,158,11,0.38);
      color: #fde68a;
      cursor: pointer;
      width: fit-content;
    }
    .risk-badge:hover { border-color: rgba(245,158,11,0.62); }
    .data-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    .data-table th,
    .data-table td {
      padding: 12px 10px;
      border-bottom: 1px solid rgba(51,65,85,0.75);
      text-align: left;
      vertical-align: top;
    }
    .data-table th {
      color: var(--muted);
      font-weight: 600;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .table-scroll {
      width: 100%;
      overflow-x: auto;
    }
    .acceptable-use-table {
      min-width: 860px;
    }
    .acceptable-use-table th:nth-child(1) { width: 18%; }
    .acceptable-use-table th:nth-child(2) { width: 31%; }
    .acceptable-use-table th:nth-child(3) { width: 12%; }
    .acceptable-use-table th:nth-child(4) { width: 18%; }
    .acceptable-use-table th:nth-child(5) { width: 21%; }
    .acceptable-use-table .object-id {
      margin-top: 4px;
    }
    .acceptable-use-table .muted-cell {
      color: var(--muted);
    }
    .acceptable-use-capability {
      display: grid;
      gap: 12px;
      margin-top: 18px;
      padding-top: 16px;
      border-top: 1px solid rgba(51,65,85,0.75);
    }
    .acceptable-use-capability:first-of-type {
      margin-top: 16px;
    }
    .acceptable-use-capability-header {
      display: flex;
      justify-content: space-between;
      gap: 18px;
      align-items: flex-start;
    }
    .acceptable-use-capability-title {
      display: flex;
      flex-wrap: wrap;
      gap: 6px 10px;
      align-items: center;
    }
    .acceptable-use-capability-title .object-id {
      flex-basis: 100%;
    }
    .acceptable-use-owner {
      display: grid;
      gap: 4px;
      min-width: 220px;
      text-align: right;
      color: var(--muted);
      font-size: 12px;
    }
    .ard-detail-card {
      display: grid;
      gap: 16px;
      padding: 22px;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 18px;
    }
    .ard-detail-title {
      margin: 0;
      font-size: 24px;
      line-height: 1.25;
    }
    .ard-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      color: var(--subtle);
      font-size: 13px;
    }
    .ard-section {
      display: grid;
      gap: 8px;
    }
    .ard-section h3 {
      margin: 0;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }
    .ard-section p,
    .ard-section div {
      margin: 0;
      color: var(--subtle);
      line-height: 1.6;
    }
    .view-title {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 14px;
      color: var(--muted);
      font-size: 14px;
    }
    .detail-layout {
      display: grid;
      gap: 22px;
    }
    .detail-tabs {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }
    .detail-tab {
      border: 1px solid var(--border);
      border-radius: 999px;
      background: #ffffff;
      color: var(--text);
      padding: 10px 16px;
      font: inherit;
      cursor: pointer;
    }
    .detail-tab.active {
      background: rgba(124, 58, 107, 0.18);
      border-color: rgba(124, 58, 107, 0.7);
      color: #5d2950;
    }
    .detail-panel[hidden] {
      display: none !important;
    }
    .detail-disclosures {
      display: grid;
      gap: 12px;
    }
    .detail-disclosure {
      border: 1px solid var(--border);
      border-radius: 14px;
      background: var(--surface);
    }
    .detail-disclosure summary {
      cursor: pointer;
      padding: 14px 16px;
      font-weight: 700;
      color: var(--text);
    }
    .detail-disclosure-content {
      display: grid;
      gap: 14px;
      padding: 0 16px 16px;
    }
    .header-card {
      padding: 22px;
      display: grid;
      gap: 14px;
    }
    .header-top {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
      justify-content: space-between;
    }
    .header-title h2 {
      margin: 0;
      font-size: 28px;
      line-height: 1.15;
    }
    .header-title .object-id {
      margin-top: 6px;
      font-size: 13px;
    }
    .header-description {
      color: var(--subtle);
      line-height: 1.6;
      font-size: 14px;
    }
    .header-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 4px;
    }
    .action-button {
      border: 1px solid var(--border);
      border-radius: 12px;
      background: #ffffff;
      color: var(--text);
      padding: 10px 14px;
      font: inherit;
      cursor: pointer;
      transition: border-color 120ms ease, background 120ms ease, transform 120ms ease;
      text-decoration: none;
    }
    .action-button:hover {
      border-color: rgba(124, 58, 107, 0.65);
      transform: translateY(-1px);
    }
    .action-button.secondary {
      background: var(--surface-strong);
    }
    .owner-line {
      display: flex;
      flex-wrap: wrap;
      gap: 18px;
      color: var(--muted);
      font-size: 13px;
    }
    .middle-grid {
      display: grid;
      grid-template-columns: 3fr 2fr;
      gap: 22px;
      align-items: start;
    }
    .section-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 18px;
    }
    .section-card h3 {
      margin: 0 0 14px;
      font-size: 16px;
    }
    #detail-cy {
      width: 100%;
      height: 350px;
      border-radius: 14px;
      border: 1px solid rgba(51,65,85,0.85);
      background: #f6f4ef;
    }
    .interactions-list {
      display: grid;
      gap: 12px;
    }
    .interaction-card {
      padding: 14px;
      display: grid;
      gap: 10px;
    }
    .requirement-card,
    .odc-card {
      padding: 14px;
      display: grid;
      gap: 10px;
      background: var(--surface);
      border: 1px solid rgba(51,65,85,0.85);
      border-radius: 14px;
    }
    .interaction-top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
    }
    .interaction-name {
      font-weight: 600;
      line-height: 1.4;
    }
    .interaction-notes {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }
    .interaction-ref {
      color: #7dd3fc;
      font-size: 12px;
      word-break: break-word;
    }
    .requirement-name,
    .odc-name {
      font-weight: 600;
      line-height: 1.4;
    }
    .requirement-name {
      font-size: 17px;
      color: var(--text);
    }
    .requirement-description,
    .requirement-rationale,
    .mechanism-line,
    .odc-requirement-line {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }
    .requirement-rationale-label,
    .mechanism-label {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .mechanism-list {
      display: grid;
      gap: 10px;
    }
    .mechanism-item {
      padding: 12px;
      border-radius: 12px;
      border: 1px solid rgba(51,65,85,0.85);
      background: var(--surface-soft);
      display: grid;
      gap: 6px;
    }
    .mechanism-text {
      color: var(--subtle);
      font-size: 13px;
      line-height: 1.5;
    }
    .mechanism-example {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
    }
    .requirement-badges,
    .odc-requirement-badges {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }
    .requirement-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 11px;
      background: #1e3a5f;
      border: 1px solid #3b82f6;
      color: #93c5fd;
    }
    .requirement-badge.conditional {
      background: #4a3414;
      border-color: #f59e0b;
      color: #fcd34d;
    }
    .requirement-mode {
      display: inline-block;
      padding: 1px 8px;
      border-radius: 999px;
      background: rgba(15, 23, 42, 0.32);
      color: inherit;
      font-size: 11px;
      white-space: nowrap;
    }
    .section-stack {
      display: grid;
      gap: 12px;
    }
    .topology-layout {
      display: grid;
      gap: 18px;
    }
    .topology-strip,
    .scaling-unit-box,
    .service-group-box,
    .deployment-target-cluster {
      background: var(--surface);
      border-radius: 18px;
    }
    .topology-strip {
      border: 1px solid var(--border);
      padding: 16px;
      display: grid;
      gap: 12px;
    }
    .topology-strip-grid {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
    .topology-interaction {
      min-width: 120px;
      display: grid;
      gap: 6px;
      padding: 12px;
      border-radius: 14px;
      border: 1px solid #d6cfc1;
      background: var(--surface-strong);
    }
    .topology-interaction-icon,
    .topology-node-icon {
      width: 96px;
      height: 96px;
      border-radius: 18px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 52px;
      background: rgba(249,115,22,0.18);
      color: #fdba74;
      border: 1px solid rgba(249,115,22,0.35);
    }
    .topology-interaction-icon svg,
    .topology-node-icon svg {
      width: 52px;
      height: 52px;
      fill: none;
      stroke: currentColor;
      stroke-width: 2.1;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    .topology-interaction-icon.network {
      background: rgba(16,185,129,0.18);
      border-color: rgba(16,185,129,0.35);
      color: #bbf7d0;
    }
    .topology-interaction-icon.storage {
      background: rgba(59,130,246,0.18);
      border-color: rgba(59,130,246,0.35);
      color: #bfdbfe;
    }
    .topology-interaction-icon.compute {
      background: rgba(168,85,247,0.18);
      border-color: rgba(168,85,247,0.35);
      color: #e9d5ff;
    }
    .topology-interaction-icon.cloud {
      background: rgba(148,163,184,0.18);
      border-color: rgba(148,163,184,0.35);
      color: #1f1a14;
    }
    .topology-node-icon.technology {
      background: rgba(249,115,22,0.18);
      border-color: rgba(249,115,22,0.35);
      color: #fdba74;
    }
    .topology-node-icon.host,
    .topology-node-icon.pod {
      background: rgba(59,130,246,0.18);
      color: #93c5fd;
      border-color: rgba(59,130,246,0.35);
    }
    .topology-node-icon.runtime,
    .topology-node-icon.product {
      background: rgba(20,184,166,0.18);
      color: #5eead4;
      border-color: rgba(20,184,166,0.35);
    }
    .topology-node-icon.data {
      background: rgba(168,85,247,0.18);
      color: #d8b4fe;
      border-color: rgba(168,85,247,0.35);
    }
    .topology-node-icon.gateway {
      background: rgba(34,197,94,0.18);
      color: #86efac;
      border-color: rgba(34,197,94,0.35);
    }
    .topology-node-icon.cloud,
    .topology-node-icon.appliance {
      background: rgba(148,163,184,0.18);
      color: #3a342c;
      border-color: rgba(148,163,184,0.35);
    }
    .related-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 20px;
      height: 20px;
      color: #93c5fd;
      flex: 0 0 auto;
    }
    .related-icon svg {
      width: 18px;
      height: 18px;
      fill: none;
      stroke: currentColor;
      stroke-width: 2.1;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    .topology-scaling-units,
    .topology-unscoped-groups {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 18px;
      align-items: start;
    }
    .topology-toolbar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 12px 14px;
      border: 1px solid rgba(51,65,85,0.85);
      border-radius: 14px;
      background: #ffffff;
    }
    .topology-filter-buttons {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .topology-filter-button {
      padding: 8px 12px;
      border-radius: 999px;
      border: 1px solid rgba(71,85,105,0.8);
      background: var(--surface-strong);
      color: #1f1a14;
      font-size: 14px;
      cursor: pointer;
      transition: border-color 0.15s ease, background 0.15s ease, color 0.15s ease;
    }
    .topology-filter-button.active {
      border-color: rgba(14,165,233,0.65);
      background: rgba(14,165,233,0.16);
      color: #7c3a6b;
    }
    .topology-filter-help {
      color: var(--muted);
      font-size: 14px;
    }
    .scaling-unit-header,
    .deployment-target-header,
    .service-group-header,
    .service-group-section-header {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }
    .scaling-unit-title,
    .deployment-target-title,
    .service-group-title,
    .service-group-section-title {
      font-size: 15px;
      font-weight: 700;
      color: #f8fafc;
    }
    .location-badge,
    .lane-label,
    .scaling-unit-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 5px 10px;
      border-radius: 999px;
      font-size: 11px;
      background: var(--surface);
      border: 1px solid rgba(148,163,184,0.3);
      color: #1f1a14;
    }
    .location-badge.aws {
      border-color: rgba(233,30,140,0.45);
      color: #fbcfe8;
    }
    .scaling-unit-content,
    .deployment-target-content,
    .service-group-content {
      display: grid;
      gap: 14px;
    }
    .deployment-target-columns {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      align-items: start;
    }
    .topology-tier-column {
      display: grid;
      gap: 12px;
      min-width: 0;
      padding: 12px;
      border-radius: 16px;
      border: 1px solid rgba(71,85,105,0.82);
      background: var(--surface-soft);
    }
    .topology-tier-header {
      padding: 10px 12px;
      border-radius: 12px;
      border: 1px solid rgba(71,85,105,0.8);
      background: #ffffff;
      font-size: 14px;
      font-weight: 700;
      color: #f8fafc;
      letter-spacing: 0.03em;
    }
    .topology-tier-header.presentation {
      border-color: rgba(249,115,22,0.45);
      color: #fdba74;
    }
    .topology-tier-column:has(.topology-tier-header.presentation) {
      border-color: rgba(249,115,22,0.52);
      background: linear-gradient(180deg, rgba(249,115,22,0.24) 0%, rgba(249,115,22,0.12) 26%, rgba(15,23,42,0.68) 58%, rgba(15,23,42,0.54) 100%);
    }
    .topology-tier-header.application {
      border-color: rgba(20,184,166,0.45);
      color: #99f6e4;
    }
    .topology-tier-column:has(.topology-tier-header.application) {
      border-color: rgba(20,184,166,0.52);
      background: linear-gradient(180deg, rgba(20,184,166,0.24) 0%, rgba(20,184,166,0.12) 26%, rgba(15,23,42,0.68) 58%, rgba(15,23,42,0.54) 100%);
    }
    .topology-tier-header.data {
      border-color: rgba(59,130,246,0.45);
      color: #bfdbfe;
    }
    .topology-tier-column:has(.topology-tier-header.data) {
      border-color: rgba(59,130,246,0.52);
      background: linear-gradient(180deg, rgba(59,130,246,0.24) 0%, rgba(59,130,246,0.12) 26%, rgba(15,23,42,0.68) 58%, rgba(15,23,42,0.54) 100%);
    }
    .topology-tier-header.utility {
      border-color: rgba(168,85,247,0.45);
      color: #e9d5ff;
    }
    .topology-tier-column:has(.topology-tier-header.utility) {
      border-color: rgba(168,85,247,0.52);
      background: linear-gradient(180deg, rgba(168,85,247,0.24) 0%, rgba(168,85,247,0.12) 26%, rgba(15,23,42,0.68) 58%, rgba(15,23,42,0.54) 100%);
    }
    .topology-column-stack {
      display: grid;
      gap: 12px;
    }
    .deployment-target-cluster {
      padding: 14px;
      border: 1px solid rgba(51,65,85,0.9);
      display: grid;
      gap: 12px;
    }
    .service-group-section {
      display: grid;
      gap: 12px;
      padding: 14px;
      border-radius: 16px;
      border: 1px solid rgba(71,85,105,0.85);
      border-left: 6px solid var(--scaling-accent, rgba(71,85,105,0.9));
      background: var(--surface-strong);
      transition: opacity 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
    }
    .service-group-section-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      color: var(--muted);
      font-size: 14px;
    }
    .service-group-section.dimmed {
      opacity: 0.22;
    }
    .service-group-section.highlighted {
      box-shadow: 0 0 0 1px rgba(14,165,233,0.35);
    }
    .service-group-support {
      display: grid;
      gap: 10px;
    }
    .service-group-box {
      padding: 14px;
      border: 1px solid rgba(71,85,105,0.9);
      display: grid;
      gap: 12px;
      background: var(--surface-strong);
    }
    .service-group-lanes {
      display: grid;
      gap: 12px;
    }
    .service-group-lane {
      display: grid;
      gap: 10px;
      padding-top: 8px;
      border-top: 1px solid rgba(51,65,85,0.55);
    }
    .lane-label.ps { color: #99f6e4; border-color: rgba(20,184,166,0.38); }
    .lane-label.rbb { color: #bfdbfe; border-color: rgba(59,130,246,0.38); }
    .lane-label.appliance { color: #d1d5db; border-color: rgba(148,163,184,0.38); }
    .lane-label.saas { color: #e9d5ff; border-color: rgba(168,85,247,0.38); }
    .cluster-box {
      padding: 14px;
      border: 2px dashed rgba(249,115,22,0.7);
      background: rgba(249,115,22,0.06);
      display: grid;
      gap: 12px;
    }
    .cluster-label,
    .eks-label {
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.04em;
      color: #fdba74;
    }
    .eks-box {
      padding: 14px;
      border: 2px dashed rgba(71,85,105,0.9);
      background: var(--surface);
      display: grid;
      gap: 12px;
    }
    .eks-label {
      color: #3a342c;
    }
    .node-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 12px;
    }
    .topology-node {
      position: relative;
      padding: 12px;
      border-radius: 14px;
      border: 1px solid rgba(71,85,105,0.85);
      background: var(--surface-strong);
      display: grid;
      gap: 10px;
      min-width: 180px;
      min-height: 100px;
      cursor: pointer;
      transition: border-color 120ms ease, transform 120ms ease, box-shadow 120ms ease, opacity 120ms ease;
    }
    .topology-node:hover {
      border-color: rgba(56,189,248,0.45);
      transform: translateY(-1px);
      box-shadow: 0 10px 18px rgba(2,6,23,0.2);
    }
    .topology-node.dimmed {
      opacity: 0.2;
    }
    .topology-node.highlighted {
      border-color: rgba(56,189,248,0.75);
      box-shadow: 0 0 0 1px rgba(56,189,248,0.35);
    }
    .topology-node.ps-node {
      background: rgba(45,66,74,0.95);
      border-color: rgba(20,184,166,0.35);
    }
    .topology-node.rbb-node {
      border-left: 4px solid rgba(59,130,246,0.75);
    }
    .topology-node.appliance-node {
      border-left: 4px solid rgba(148,163,184,0.75);
      background: rgba(42,50,66,0.95);
    }
    .topology-node.saas-node {
      border-left: 4px solid rgba(168,85,247,0.78);
      background: rgba(58,45,74,0.95);
    }
    .topology-node.pod {
      border-color: rgba(59,130,246,0.45);
      background: var(--surface-strong);
    }
    .topology-node-label {
      font-size: 13px;
      font-weight: 600;
      color: #f8fafc;
      line-height: 1.35;
    }
    .topology-node-flags {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }
    .ps-corner {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 30px;
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.05em;
      background: rgba(20,184,166,0.18);
      border: 1px solid rgba(20,184,166,0.4);
      color: #99f6e4;
    }
    .topology-node-meta {
      font-size: 11px;
      color: var(--muted);
      line-height: 1.45;
    }
    .topology-risk {
      position: absolute;
      top: 8px;
      right: 8px;
      width: 26px;
      height: 26px;
      border-radius: 999px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: rgba(245,158,11,0.18);
      border: 1px solid rgba(245,158,11,0.42);
      color: #fde68a;
      cursor: pointer;
      font-size: 13px;
    }
    .topology-risk:hover {
      border-color: rgba(245,158,11,0.72);
    }
    .topology-info {
      position: absolute;
      top: 8px;
      right: 40px;
      width: 26px;
      height: 26px;
      border-radius: 999px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: rgba(59,130,246,0.18);
      border: 1px solid rgba(59,130,246,0.42);
      color: #bfdbfe;
      font-size: 13px;
    }
    .topology-internal-interactions {
      display: grid;
      gap: 8px;
    }
    .topology-internal-link {
      padding: 10px 12px;
      border-radius: 12px;
      border: 1px dashed rgba(148,163,184,0.45);
      color: var(--subtle);
      background: var(--surface-soft);
      font-size: 13px;
      line-height: 1.5;
    }
    .impact-sidebar {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 18px;
      display: grid;
      gap: 14px;
      max-height: calc(100vh - 160px);
      overflow: auto;
    }
    .impact-search {
      width: 100%;
      border: 1px solid rgba(148,163,184,0.18);
      border-radius: 12px;
      background: var(--surface);
      color: var(--text);
      padding: 11px 12px;
      font: inherit;
    }
    .search-results,
    .impact-group-list {
      display: grid;
      gap: 8px;
    }
    .search-result,
    .impact-item {
      border: 1px solid rgba(51,65,85,0.85);
      border-radius: 12px;
      background: var(--surface);
      padding: 10px 12px;
      cursor: pointer;
      display: grid;
      gap: 4px;
    }
    .search-result:hover,
    .impact-item:hover {
      border-color: rgba(56,189,248,0.45);
    }
    .impact-item-top {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .impact-group {
      display: grid;
      gap: 10px;
    }
    .impact-group h4 {
      margin: 0;
      font-size: 12px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .impact-graph-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 18px;
      display: grid;
      gap: 14px;
      min-width: 0;
      overflow: hidden;
    }
    .impact-graph-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
      min-width: 0;
    }
    .lifecycle-filter-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      min-width: 0;
    }
    .lifecycle-filter-button {
      border: 1px solid rgba(51,65,85,0.9);
      border-radius: 999px;
      background: var(--surface);
      color: var(--subtle);
      padding: 8px 12px;
      font: inherit;
      font-size: 12px;
      cursor: pointer;
      transition: transform 120ms ease, border-color 120ms ease, opacity 120ms ease;
      opacity: 0.78;
    }
    .lifecycle-filter-button:hover {
      transform: translateY(-1px);
      border-color: rgba(148,163,184,0.45);
    }
    .lifecycle-filter-button.active {
      color: #f8fafc;
      border-color: transparent;
      opacity: 1;
    }
    .lifecycle-filter-button.retired-filter {
      border-style: dashed;
      opacity: 0.55;
    }
    .lifecycle-filter-button.retired-filter:not(.active) {
      text-decoration: line-through;
    }
    #impact-cy {
      width: 100%;
      min-width: 0;
      height: 720px;
      border-radius: 14px;
      border: 1px solid rgba(51,65,85,0.85);
      background: #f6f4ef;
      overflow: hidden;
    }
    .impact-dot {
      width: 10px;
      height: 10px;
      border-radius: 999px;
      flex: 0 0 auto;
    }
    .sidebar-select {
      width: 100%;
      margin-top: 10px;
      border-radius: 12px;
      border: 1px solid rgba(71, 85, 105, 0.9);
      background: rgba(15, 23, 42, 0.95);
      color: var(--text);
      padding: 10px 12px;
      font: inherit;
    }
    .sidebar-help {
      margin-top: 8px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
    }
    .editor-overlay {
      position: fixed;
      inset: 0;
      z-index: 1000;
      display: none;
      align-items: stretch;
      justify-content: flex-end;
      background: rgba(2,6,23,0.72);
      backdrop-filter: blur(2px);
    }
    .editor-overlay.open {
      display: flex;
    }
    .editor-panel {
      width: min(960px, 100vw);
      height: 100vh;
      overflow: auto;
      background: linear-gradient(180deg, rgba(15,23,42,0.99), rgba(17,24,39,0.99));
      border-left: 1px solid rgba(51,65,85,0.85);
      padding: 26px;
      display: grid;
      gap: 18px;
    }
    .editor-header {
      display: flex;
      justify-content: space-between;
      gap: 18px;
      align-items: flex-start;
    }
    .editor-title h3 {
      margin: 0;
      font-size: 18px;
    }
    .editor-title p {
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.6;
    }
    .editor-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: flex-end;
    }
    .editor-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.1fr) minmax(360px, 0.9fr);
      gap: 18px;
      align-items: start;
    }
    .editor-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 18px;
      display: grid;
      gap: 14px;
    }
    .editor-card h4 {
      margin: 0;
      font-size: 14px;
    }
    .editor-form {
      display: grid;
      gap: 14px;
    }
    .editor-field {
      display: grid;
      gap: 8px;
    }
    .editor-field label {
      font-size: 14px;
      color: var(--subtle);
    }
    .editor-required {
      color: #fda4af;
      margin-left: 6px;
    }
    .editor-field input,
    .editor-field textarea,
    .editor-field select {
      width: 100%;
      border: 1px solid rgba(51,65,85,0.9);
      border-radius: 12px;
      background: #f6f4ef;
      color: var(--text);
      font: inherit;
      padding: 12px 14px;
    }
    .editor-field textarea {
      min-height: 120px;
      resize: vertical;
      font-family: "SF Mono", Menlo, monospace;
      line-height: 1.55;
    }
    .editor-field input[type="checkbox"] {
      width: 18px;
      height: 18px;
      padding: 0;
    }
    .editor-checkbox {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .editor-help,
    .editor-meta,
    .editor-error {
      font-size: 14px;
      line-height: 1.6;
    }
    .editor-help,
    .editor-meta {
      color: var(--muted);
    }
    .editor-error {
      color: #fca5a5;
      min-height: 22px;
    }
    .editor-scroll {
      display: grid;
      gap: 14px;
      max-height: 60vh;
      overflow: auto;
      padding-right: 4px;
    }
    .import-card {
      border: 1px solid rgba(71,85,105,0.78);
      border-radius: 16px;
      padding: 16px;
      background: var(--surface-soft);
      display: grid;
      gap: 14px;
    }
    .import-card-header {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
    }
    .import-card-title {
      display: grid;
      gap: 4px;
    }
    .import-card-title h5 {
      margin: 0;
      font-size: 14px;
    }
    .import-card-meta {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }
    .editor-subgrid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    .editor-checkbox-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .editor-choice {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 12px;
      border: 1px solid rgba(71,85,105,0.72);
      border-radius: 12px;
      background: #ffffff;
      color: var(--text);
      font-size: 14px;
    }
    .editor-choice input[type="checkbox"] {
      width: 18px;
      height: 18px;
      margin: 0;
    }
    .editor-inline-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }
    .editor-divider {
      height: 1px;
      background: rgba(71,85,105,0.75);
      margin: 4px 0;
    }
    .editor-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      font-size: 13px;
      color: #dbeafe;
      background: rgba(37,99,235,0.2);
      border: 1px solid rgba(96,165,250,0.32);
    }
    .editor-note {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.55;
    }
    .structured-preview {
      white-space: pre-wrap;
      word-break: break-word;
      font-family: "SF Mono", Menlo, monospace;
      font-size: 13px;
      line-height: 1.65;
      margin: 0;
      color: #dbeafe;
    }
    .decisions-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 18px;
      display: grid;
      gap: 14px;
    }
    .decisions-grid {
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .decisions-grid.single {
      grid-template-columns: 1fr;
    }
    .decision-card {
      padding: 16px;
    }
    .decision-card h4 {
      margin: 0 0 12px;
      font-size: 15px;
    }
    .definition-list {
      display: grid;
      grid-template-columns: minmax(120px, 180px) 1fr;
      gap: 10px 14px;
      margin: 0;
      font-size: 13px;
    }
    .definition-list dt {
      color: var(--muted);
      font-weight: 600;
    }
    .definition-list dd {
      margin: 0;
      color: var(--subtle);
      word-break: break-word;
    }
    .empty-card {
      padding: 18px;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.6;
    }
    .cap-authentication { background: rgba(139,92,246,0.18); border-color: rgba(139,92,246,0.4); color: #ddd6fe; }
    .cap-logging { background: rgba(59,130,246,0.18); border-color: rgba(59,130,246,0.4); color: #bfdbfe; }
    .cap-security { background: rgba(239,68,68,0.18); border-color: rgba(239,68,68,0.4); color: #fecaca; }
    .cap-monitoring { background: rgba(16,185,129,0.18); border-color: rgba(16,185,129,0.4); color: #bbf7d0; }
    .cap-patch-management { background: rgba(245,158,11,0.18); border-color: rgba(245,158,11,0.4); color: #fde68a; }
    .cap-default { background: rgba(100,116,139,0.18); border-color: rgba(100,116,139,0.4); color: #3a342c; }
    .sidebar p,
    .legend-title,
    .legend-item,
    .current-filter,
    .content-row-count,
    .object-id,
    .badge,
    .info-badge,
    .risk-badge,
    .data-table,
    .data-table th,
    .ard-meta,
    .ard-section h3,
    .header-title .object-id,
    .owner-line,
    .interaction-notes,
    .interaction-ref,
    .requirement-description,
    .requirement-rationale,
    .mechanism-line,
    .odc-requirement-line,
    .requirement-rationale-label,
    .mechanism-label,
    .mechanism-text,
    .mechanism-example,
    .requirement-badge,
    .location-badge,
    .lane-label,
    .scaling-unit-badge,
    .cluster-label,
    .eks-label,
    .topology-node-label,
    .ps-corner,
    .topology-node-meta,
    .topology-risk,
    .topology-info,
    .topology-internal-link,
    .impact-group h4,
    .lifecycle-filter-button,
    .sidebar-help,
    .definition-list {
      font-size: 14px;
    }
    @media (max-width: 1200px) {
      .middle-grid { grid-template-columns: 1fr; }
      .deployment-target-columns { grid-template-columns: 1fr; }
      .executive-hero { grid-template-columns: 1fr; }
      .executive-tile.large,
      .executive-tile.wide,
      .executive-tile.medium,
      .executive-panel.wide {
        grid-column: span 6;
      }
    }
    @media (max-width: 980px) {
      .page-shell { grid-template-columns: 1fr; }
      .sidebar { border-right: 0; border-bottom: 1px solid #e7e1d6; }
      .main { padding: 20px; }
      .decisions-grid { grid-template-columns: 1fr; }
      .definition-list { grid-template-columns: 1fr; }
      .acceptable-use-capability-header { flex-direction: column; }
      .acceptable-use-owner { text-align: left; }
      .executive-mosaic { grid-template-columns: 1fr; }
      .executive-tile.large,
      .executive-tile.wide,
      .executive-tile.medium,
      .executive-tile.small,
      .executive-tile.full,
      .executive-panel.wide,
      .executive-panel.full {
        grid-column: 1;
      }
      .executive-hero { padding: 22px; }
      .executive-hero h2 { font-size: 34px; }
      .executive-hero-copy { grid-template-columns: 92px minmax(0, 1fr); gap: 16px; }
      .executive-hero-logo { width: 92px; height: 92px; }
      .executive-number.big,
      .executive-number { font-size: 46px; }
      .executive-bar-row { grid-template-columns: 86px minmax(0, 1fr) 34px; }
    }
  </style>
</head>
<body>
  <div class="page-shell">
    <aside class="sidebar">
      <div class="browser-brand">
        <img id="draft-logo" class="browser-logo" alt="DRAFT">
        <div>
          <h1>DRAFT Catalog</h1>
          <div class="catalog-name" id="catalog-name"></div>
          <div class="mode-badge" id="browser-mode"></div>
        </div>
      </div>
      <p>Review architecture inventory, deployable objects, requirements, relationships, and decisions.</p>
      <div class="sidebar-stack">
        <div id="sidebar-content"></div>
        <div class="legend-block">
          <div class="legend-title">Lifecycle Legend</div>
          <div class="legend-list" id="legend"></div>
        </div>
      </div>
    </aside>
    <main class="main">
      <div id="page-root"></div>
    </main>
  </div>
  <div id="editor-overlay" class="editor-overlay"></div>
  <script>
    const browserData = __BROWSER_DATA__;
    const lifecycleColors = browserData.lifecycleColors;
    const allObjects = browserData.objects.slice().sort((a, b) => a.name.localeCompare(b.name));
    const objectLookup = browserData.lookup;
    const referencedByIndex = browserData.referencedBy || {};
    const repoUrl = browserData.repoUrl || '';
    const businessTaxonomy = browserData.businessTaxonomy || { pillars: [] };
    const businessPillarLookup = Object.fromEntries((businessTaxonomy.pillars || []).map(pillar => [pillar.id, pillar]));
    const pageRoot = document.getElementById('page-root');
    const sidebarContent = document.getElementById('sidebar-content');
    const legend = document.getElementById('legend');
    const editorOverlay = document.getElementById('editor-overlay');
    document.getElementById('draft-logo').src = browserData.logoDataUri || 'draftlogo.png';
    document.getElementById('catalog-name').textContent = browserData.catalogName || 'Catalog';
    document.getElementById('browser-mode').textContent = 'GitHub Pages';
    let editorState = null;
    let requirementImportState = null;
    const DEPLOYABLE_OBJECT_TYPES = [
      'technology_component',
      'host',
      'runtime_service',
      'data_at_rest_service',
      'edge_gateway_service',
      'product_service',
      'software_deployment_pattern'
    ];
    const SERVICE_OBJECT_TYPES = ['runtime_service', 'data_at_rest_service', 'edge_gateway_service'];
    const DEPLOYABLE_STANDARD_TYPES = ['host', 'runtime_service', 'data_at_rest_service', 'edge_gateway_service', 'product_service'];
    const CATEGORY_CONFIG = [
      {
        id: 'architecture',
        label: 'Architecture Content',
        filters: [
          { id: 'all', label: 'All', types: ['software_deployment_pattern', 'reference_architecture', 'host', 'runtime_service', 'data_at_rest_service', 'edge_gateway_service', 'product_service'] },
          { id: 'software_deployment_pattern', label: 'Software Deployment Patterns', types: ['software_deployment_pattern'] },
          { id: 'reference_architecture', label: 'Reference Architectures', types: ['reference_architecture'] },
          { id: 'deployable_objects', label: 'Deployable Objects', types: DEPLOYABLE_STANDARD_TYPES }
        ],
        rows: [
          { id: 'software_deployment_pattern', label: 'Software Deployment Patterns', types: ['software_deployment_pattern'] },
          { id: 'reference_architecture', label: 'Reference Architectures', types: ['reference_architecture'] },
          { id: 'host', label: 'Hosts', types: ['host'] },
          { id: 'runtime_service', label: 'Runtime Services', types: ['runtime_service'] },
          { id: 'data_at_rest_service', label: 'Data-at-Rest Services', types: ['data_at_rest_service'] },
          { id: 'edge_gateway_service', label: 'Edge/Gateway Services', types: ['edge_gateway_service'] },
          { id: 'product_service', label: 'Product Services', types: ['product_service'] }
        ]
      },
      {
        id: 'supporting',
        label: 'Supporting Content',
        filters: [
          { id: 'all', label: 'All', types: ['technology_component', 'decision_record'] },
          { id: 'technology_component', label: 'Technology Components', types: ['technology_component'] },
          { id: 'decision_record', label: 'Decision Records', types: ['decision_record'] }
        ],
        rows: [
          { id: 'technology_component', label: 'Technology Components', types: ['technology_component'] },
          { id: 'decision_record', label: 'Decision Records', types: ['decision_record'] }
        ]
      },
      {
        id: 'framework',
        label: 'Framework Content',
        filters: [
          { id: 'all', label: 'All', types: ['capability', 'requirement_group', 'domain'] },
          { id: 'capability', label: 'Capabilities', types: ['capability'] },
          { id: 'requirement_group', label: 'Requirement Groups', types: ['requirement_group'] },
          { id: 'domain', label: 'Strategy Map', types: ['domain'] }
        ],
        rows: [
          { id: 'capability', label: 'Capabilities', types: ['capability'] },
          { id: 'requirement_group', label: 'Requirement Groups', types: ['requirement_group'] },
          { id: 'domain', label: 'Strategy Domains', types: ['domain'] }
        ]
      }
    ];
    const lifecycleValues = browserData.lifecycleValues || [];
    const deployableTypes = new Set([
      'software_deployment_pattern',
      'reference_architecture',
      'host',
      'runtime_service',
      'data_at_rest_service',
      'edge_gateway_service',
      'product_service'
    ]);
    const impactOrder = [
      'software_deployment_pattern',
      'reference_architecture',
      'host',
      'runtime_service',
      'data_at_rest_service',
      'edge_gateway_service',
      'product_service'
    ];
    const impactLifecycleOrder = lifecycleValues;
    let activeCategory = 'architecture';
    let activeFilter = 'all';
    let currentDetailId = null;
    let currentMode = 'executive';
    let executiveDrilldown = null;
    const navHistory = [];
    let detailCy = null;
    let impactCy = null;
    let impactSelectedId = null;
    let impactSearchTerm = '';
    let currentSdmScalingFilter = 'all';
    let suppressHashSync = false;
    let impactLifecycleFilters = Object.fromEntries(
      impactLifecycleOrder.map(status => [status, status !== 'retired'])
    );

    Object.entries(lifecycleColors).forEach(([label, value]) => {
      const item = document.createElement('div');
      item.className = 'legend-item';
      item.innerHTML = `<span class="dot" style="background:${'#' + value}"></span><span>${label}</span>`;
      legend.appendChild(item);
    });

    function escapeHtml(value) {
      return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    function formatTitleCase(value) {
      return String(value || '')
        .split(/[-_]/g)
        .filter(Boolean)
        .map(part => part.charAt(0).toUpperCase() + part.slice(1))
        .join(' ');
    }

    function formatKeyLabel(value) {
      return formatTitleCase(String(value || '').replace(/\./g, '-'));
    }

    function formatNumber(value) {
      return Number(value || 0).toLocaleString();
    }

    function pluralize(count, singular, plural = `${singular}s`) {
      return `${formatNumber(count)} ${count === 1 ? singular : plural}`;
    }

    function relatedCapabilityOptions() {
      const values = new Set();
      allObjects
        .filter(object => object.type === 'requirement_group')
        .forEach(object => {
          (object.requirements || []).forEach(requirement => {
            if (requirement?.id) {
              values.add(String(requirement.id));
            }
          });
        });
      return Array.from(values).sort((a, b) => a.localeCompare(b));
    }

    function formatTypeLabel(typeValue) {
      const normalized = String(typeValue || '');
      if (normalized === 'technology_component') return 'Technology Component';
      if (normalized === 'edge_gateway_service') return 'Edge/Gateway Service';
      if (normalized === 'host') return 'Host';
      if (normalized === 'runtime_service') return 'Runtime Service';
      if (normalized === 'data_at_rest_service') return 'Data-at-Rest Service';
      if (normalized === 'capability') return 'Capability';
      if (normalized === 'requirement_group') return 'Requirement Group';
      if (normalized === 'decision_record') return 'Decision Record';
      if (normalized === 'software_deployment_pattern') return 'Software Deployment Pattern';
      if (normalized === 'reference_architecture') return 'Reference Architecture';
      return formatTitleCase(normalized.replace(/[._-]/g, ' '));
    }

    function capabilityClass(capability) {
      return ({
        'authentication': 'cap-authentication',
        'logging': 'cap-logging',
        'security': 'cap-security',
        'monitoring': 'cap-monitoring',
        'patch-management': 'cap-patch-management'
      }[capability] || 'cap-default');
    }

    function catalogStatusClass(status) {
      return ({
        'approved': 'catalog-approved',
        'draft': 'catalog-draft',
        'stub': 'catalog-stub'
      }[status] || 'catalog-stub');
    }

    function lifecycleBadge(status) {
      if (!status) return '';
      const color = '#' + (lifecycleColors[status] || lifecycleColors.unknown);
      return `<span class="badge"><span class="dot" style="background:${color}"></span>${escapeHtml(status)}</span>`;
    }

    function catalogBadge(status) {
      return `<span class="badge ${catalogStatusClass(status)}">${escapeHtml(status)}</span>`;
    }

    function ardCategoryBadge(category) {
      const normalized = category === 'decision' ? 'decision' : 'risk';
      return `<span class="badge ard-${normalized}">${escapeHtml(normalized)}</span>`;
    }

    function ardStatusBadge(status) {
      return `<span class="badge ard-status">${escapeHtml(status || 'unknown')}</span>`;
    }

    function productBadge(product) {
      return `<span class="badge ps-badge">${escapeHtml(product || 'unknown product')}</span>`;
    }

    function saasBadge() {
      return '<span class="badge saas-badge">SaaS</span>';
    }

    function paasBadge() {
      return '<span class="badge paas-badge">PaaS</span>';
    }

    function applianceBadge() {
      return '<span class="badge appliance-badge">appliance</span>';
    }

    function deliveryModelBadge(object) {
      if (!SERVICE_OBJECT_TYPES.includes(object?.type)) return '';
      const deliveryModel = object.deliveryModel || 'self-managed';
      if (deliveryModel === 'saas') return saasBadge();
      if (deliveryModel === 'paas') return paasBadge();
      if (deliveryModel === 'appliance') return applianceBadge();
      return '<span class="badge">self-managed</span>';
    }

    function intentBadge(intent) {
      const normalized = String(intent || '').toLowerCase();
      const cls = normalized === 'ha' ? 'intent-ha' : normalized === 'sa' ? 'intent-sa' : '';
      return `<span class="badge ${cls}">${escapeHtml((intent || '').toUpperCase())}</span>`;
    }

    function boolBadge(value, trueLabel = 'true', falseLabel = 'false') {
      const active = value === true;
      const text = active ? trueLabel : falseLabel;
      const cls = active ? 'saas-badge' : 'catalog-stub';
      return `<span class="badge ${cls}">${escapeHtml(text)}</span>`;
    }

    function currentHashState() {
      const raw = window.location.hash.replace(/^#/, '');
      return new URLSearchParams(raw);
    }

    function setHashState(values) {
      if (suppressHashSync) return;
      const params = new URLSearchParams();
      Object.entries(values).forEach(([key, value]) => {
        if (value !== null && value !== undefined && String(value).trim() !== '') {
          params.set(key, value);
        }
      });
      const nextHash = params.toString();
      const currentHash = window.location.hash.replace(/^#/, '');
      if (nextHash === currentHash) return;
      suppressHashSync = true;
      window.location.hash = nextHash;
      window.setTimeout(() => {
        suppressHashSync = false;
      }, 0);
    }

    function categoryConfig(categoryId = activeCategory) {
      return CATEGORY_CONFIG.find(category => category.id === categoryId) || CATEGORY_CONFIG[0];
    }

    function activeFilterConfig() {
      const category = categoryConfig();
      return category.filters.find(filter => filter.id === activeFilter) || category.filters[0];
    }

    function formatListFilterLabel(filterId) {
      const category = categoryConfig();
      const filter = category.filters.find(item => item.id === filterId);
      return filter?.label || 'All';
    }

    function syncHashForExecutiveView() {
      setHashState({
        view: 'executive',
        drill: executiveDrilldown || null
      });
    }

    function syncHashForListView() {
      setHashState({
        view: 'list',
        category: activeCategory !== 'architecture' ? activeCategory : null,
        filter: activeFilter !== 'all' ? activeFilter : null
      });
    }

    function syncHashForDetailView(id) {
      setHashState({ view: 'detail', id });
    }

    function syncHashForImpactView() {
      setHashState({ view: 'impact', id: impactSelectedId, q: impactSearchTerm || null });
    }

    function syncHashForAcceptableUseView() {
      setHashState({ view: 'acceptable-use' });
    }

    function syncHashForObjectTypesView() {
      setHashState({ view: 'object-types' });
    }

    function syncHashForOnboardingView() {
      setHashState({ view: 'onboarding' });
    }

    function applyRouteFromHash() {
      if (suppressHashSync) return;
      const params = currentHashState();
      const view = params.get('view');
      if (view === 'executive' || (!view && !params.get('category') && !params.get('filter'))) {
        executiveDrilldown = params.get('drill') || null;
        currentDetailId = null;
        renderExecutiveView();
        return;
      }
      if (view === 'detail') {
        const objectId = params.get('id');
        if (objectId && objectLookup[objectId]) {
          currentDetailId = objectId;
          navHistory.length = 0;
          renderDetailView();
          return;
        }
      }
      if (view === 'impact') {
        const objectId = params.get('id');
        impactSelectedId = objectId && objectLookup[objectId] ? objectId : null;
        impactSearchTerm = params.get('q') || '';
        renderImpactView();
        return;
      }
      if (view === 'acceptable-use') {
        renderAcceptableUseView();
        return;
      }
      if (view === 'object-types') {
        renderObjectTypesView();
        return;
      }
      if (view === 'onboarding') {
        renderCompanyOnboardingView();
        return;
      }
      executiveDrilldown = null;
      const category = params.get('category');
      activeCategory = CATEGORY_CONFIG.some(item => item.id === category) ? category : 'architecture';
      const requestedFilter = params.get('filter');
      const categoryFilters = categoryConfig(activeCategory).filters;
      activeFilter = categoryFilters.some(item => item.id === requestedFilter)
        ? requestedFilter
        : requestedFilter && categoryFilters.some(item => item.types.includes(requestedFilter))
          ? requestedFilter
          : 'all';
      currentDetailId = null;
      renderListView();
    }

    function topNavMarkup() {
      return `
        <div class="top-nav">
          <button class="nav-button ${currentMode === 'executive' ? 'active' : ''}" data-nav="executive">DRAFT Overview</button>
          <button class="nav-button ${currentMode === 'onboarding' ? 'active' : ''}" data-nav="onboarding">Onboarding</button>
          <button class="nav-button ${currentMode === 'object-types' ? 'active' : ''}" data-nav="object-types">Object Types</button>
          <button class="nav-button ${currentMode === 'list' ? 'active' : ''}" data-nav="list">Drafting Table</button>
          <button class="nav-button ${currentMode === 'detail' ? 'active' : ''}" data-nav="detail" ${currentDetailId ? '' : 'disabled'}>Detail View</button>
          <button class="nav-button ${currentMode === 'acceptable-use' ? 'active' : ''}" data-nav="acceptable-use">Acceptable Use</button>
          <button class="nav-button ${currentMode === 'impact' ? 'active' : ''}" data-nav="impact">Impact Analysis</button>
        </div>
      `;
    }

    function renderSidebarContent(contentHtml) {
      sidebarContent.innerHTML = contentHtml;
    }

    function currentFilterMarkup() {
      return `
        <div class="sidebar-block">
          <div class="legend-title">Current Filter</div>
          <div class="current-filter"><span class="dot" style="background:#7c3a6b"></span><span>${escapeHtml(categoryConfig().label)} / ${escapeHtml(formatListFilterLabel(activeFilter))}</span></div>
        </div>
      `;
    }

    function sidebarMarkup(extraMarkup = '') {
      return `${currentFilterMarkup()}${extraMarkup}`;
    }

    function rerenderCurrentView() {
      if (currentMode === 'executive') {
        renderExecutiveView();
        return;
      }
      if (currentMode === 'detail') {
        renderDetailView();
        return;
      }
      if (currentMode === 'acceptable-use') {
        renderAcceptableUseView();
        return;
      }
      if (currentMode === 'object-types') {
        renderObjectTypesView();
        return;
      }
      if (currentMode === 'onboarding') {
        renderCompanyOnboardingView();
        return;
      }
      if (currentMode === 'impact') {
        renderImpactView();
        return;
      }
      renderListView();
    }

    function attachSidebarHandlers() {}

    function attachTopNavHandlers() {
      pageRoot.querySelectorAll('[data-nav]').forEach(button => {
        button.addEventListener('click', () => {
          const nav = button.dataset.nav;
          if (nav === 'executive') {
            destroyImpactCy();
            executiveDrilldown = null;
            renderExecutiveView();
            return;
          }
          if (nav === 'list') {
            destroyImpactCy();
            renderListView();
            return;
          }
          if (nav === 'object-types') {
            destroyImpactCy();
            renderObjectTypesView();
            return;
          }
          if (nav === 'onboarding') {
            destroyImpactCy();
            renderCompanyOnboardingView();
            return;
          }
          if (nav === 'detail' && currentDetailId) {
            destroyImpactCy();
            renderDetailView();
            return;
          }
          if (nav === 'impact') {
            renderImpactView();
            return;
          }
          if (nav === 'acceptable-use') {
            renderAcceptableUseView();
          }
        });
      });
    }

    function impactGroupForObject(object) {
      return object.type || 'unknown';
    }

    function destroyImpactCy() {
      if (impactCy) {
        impactCy.destroy();
        impactCy = null;
      }
    }

    function filterObjectsByTypes(types) {
      const allowed = new Set(types);
      return allObjects.filter(object => allowed.has(object.type));
    }

    function filterObjects() {
      return filterObjectsByTypes(activeFilterConfig().types);
    }

    function objectSearchText(object) {
      const aliases = Array.isArray(object.aliases) ? object.aliases.join(' ') : '';
      return `${object.name} ${object.id} ${aliases}`.toLowerCase();
    }

    function businessPillarForObject(object) {
      const pillarId = object.businessContext?.pillar || '';
      const pillar = pillarId ? businessPillarLookup[pillarId] : null;
      return {
        id: pillarId || 'unassigned',
        name: pillar?.name || (pillarId ? formatTitleCase(pillarId.replace(/^business-pillar\\./, '').replace(/-/g, ' ')) : 'Unassigned Business Pillar'),
        owner: pillar?.owner || null
      };
    }

    function businessPillarBadge(object) {
      if (object.type !== 'software_deployment_pattern') {
        return '';
      }
      const pillar = businessPillarForObject(object);
      return `<div class="badge">${escapeHtml(pillar.name)}</div>`;
    }

    function businessPillarSidebarMarkup(objects) {
      if (activeFilter !== 'software_deployment_pattern') {
        return '';
      }
      const groups = groupSoftwareDeploymentPatternsByPillar(objects);
      return `
        <div class="sidebar-block">
          <div class="legend-title">Business Pillars</div>
          ${groups.map(group => `
            <div class="current-filter">
              <span class="dot" style="background:#f59e0b"></span>
              <span>${escapeHtml(group.pillar.name)}: ${group.objects.length}</span>
            </div>
          `).join('')}
        </div>
      `;
    }

    function groupSoftwareDeploymentPatternsByPillar(objects) {
      const groupsById = new Map();
      objects.forEach(object => {
        const pillar = businessPillarForObject(object);
        if (!groupsById.has(pillar.id)) {
          groupsById.set(pillar.id, { pillar, objects: [] });
        }
        groupsById.get(pillar.id).objects.push(object);
      });
      const order = new Map((businessTaxonomy.pillars || []).map((pillar, index) => [pillar.id, index]));
      return Array.from(groupsById.values()).sort((a, b) => {
        const aRank = order.has(a.pillar.id) ? order.get(a.pillar.id) : 999;
        const bRank = order.has(b.pillar.id) ? order.get(b.pillar.id) : 999;
        if (aRank !== bRank) return aRank - bRank;
        return a.pillar.name.localeCompare(b.pillar.name);
      });
    }

    function listRowMarkup(row, objects) {
      if (!objects.length) {
        return '';
      }
      if (row.id === 'software_deployment_pattern') {
        return softwareDeploymentPatternRowMarkup(row, objects);
      }
      return `
        <section class="content-row">
          <div class="content-row-header">
            <h2 class="content-row-title">${escapeHtml(row.label)}</h2>
            <span class="content-row-count">${objects.length} objects</span>
          </div>
          <div class="cards-grid">
            ${objects.map(object => objectCardMarkup(object)).join('')}
          </div>
        </section>
      `;
    }

    function softwareDeploymentPatternRowMarkup(row, objects) {
      const groups = groupSoftwareDeploymentPatternsByPillar(objects);
      return `
        <section class="content-row">
          <div class="content-row-header">
            <h2 class="content-row-title">${escapeHtml(row.label)}</h2>
            <span class="content-row-count">${objects.length} objects</span>
          </div>
          <div class="business-pillar-groups">
            ${groups.map(group => `
              <div class="business-pillar-group">
                <div class="business-pillar-header">
                  <h3 class="business-pillar-title">${escapeHtml(group.pillar.name)}</h3>
                  <span class="business-pillar-meta">${group.objects.length} ${group.objects.length === 1 ? 'pattern' : 'patterns'}</span>
                </div>
                <div class="cards-grid">
                  ${group.objects.map(object => objectCardMarkup(object)).join('')}
                </div>
              </div>
            `).join('')}
          </div>
        </section>
      `;
    }

    function objectCardTitle(object) {
      if (object.type !== 'requirement_group') {
        return object.name;
      }
      const trimmed = String(object.name || '').replace(/\s+Requirement Group$/i, '');
      if (trimmed === 'Edge/Gateway Service') {
        return 'Appliance';
      }
      return trimmed;
    }

    function objectCardMarkup(object) {
      return `
        <article class="object-card" data-object-id="${object.id}">
          <div>
            <h3>${escapeHtml(objectCardTitle(object))}</h3>
            <div class="object-id">${escapeHtml(object.id)}</div>
          </div>
          <div class="badges">
            ${lifecycleBadge(object.lifecycleStatus)}
            ${catalogBadge(object.catalogStatus)}
            ${object.type === 'decision_record' ? ardCategoryBadge(object.ardCategory) : ''}
            ${object.type === 'decision_record' ? ardStatusBadge(object.status) : ''}
            ${object.type === 'product_service' ? productBadge(object.product) : ''}
            ${deliveryModelBadge(object)}
            ${businessPillarBadge(object)}
          </div>
          <div class="badges">
            <div class="badge">${escapeHtml(object.typeLabel)}</div>
            ${object.type === 'product_service' ? `<div class="object-id">${escapeHtml(object.product)}</div>` : ''}
          </div>
        </article>
      `;
    }

    function abbClassificationLabel(value) {
      return formatTitleCase(String(value || 'unknown').replace(/-/g, ' '));
    }

    function lifecycleSortRank(status) {
      return ({
        'preferred': 0,
        'existing-only': 1,
        'candidate': 2,
        'deprecated': 3,
        'retired': 4
      }[status] ?? 99);
    }

    function implementationConfigurationLabel(technology, implementation) {
      const configurationId = implementation?.configuration || '';
      if (!configurationId) return '';
      const configuration = (technology?.configurations || [])
        .find(item => item && item.id === configurationId);
      if (!configuration) return configurationId;
      return `${configuration.name || configuration.id} (${configurationId})`;
    }

    function acceptableUseGroups() {
      const groups = new Map();
      allObjects
        .filter(object => object.type === 'capability')
        .sort((a, b) => {
          const domainA = objectLookup[a.domain]?.name || a.domain || '';
          const domainB = objectLookup[b.domain]?.name || b.domain || '';
          return domainA.localeCompare(domainB) || a.name.localeCompare(b.name);
        })
        .forEach(capability => {
          const implementations = Array.isArray(capability.implementations)
            ? capability.implementations.slice().sort((a, b) => {
                const objectA = objectLookup[a.ref] || {};
                const objectB = objectLookup[b.ref] || {};
                const vendorA = objectA.vendor || '';
                const vendorB = objectB.vendor || '';
                const techA = objectA.name || a.ref || '';
                const techB = objectB.name || b.ref || '';
                return vendorA.localeCompare(vendorB)
                  || techA.localeCompare(techB)
                  || lifecycleSortRank(a.lifecycleStatus) - lifecycleSortRank(b.lifecycleStatus)
                  || (a.lifecycleStatus || '').localeCompare(b.lifecycleStatus || '');
              })
            : [];
          if (!implementations.length) {
            return;
          }
          const domainId = capability.domain || 'domain.unassigned';
          const domain = objectLookup[domainId] || {
            id: domainId,
            name: capability.domain || 'Unassigned Domain',
            description: ''
          };
          if (!groups.has(domainId)) {
            groups.set(domainId, { domain, rows: [] });
          }
          const rows = groups.get(domainId).rows;
          implementations.forEach(implementation => {
            rows.push({
              capability,
              implementation,
              technology: objectLookup[implementation.ref] || null
            });
          });
        });
      return Array.from(groups.values())
        .sort((a, b) => (a.domain.name || a.domain.id).localeCompare(b.domain.name || b.domain.id));
    }

    function requirementEvidenceRows() {
      const rows = [];
      allObjects.forEach(object => {
        (object.requirementImplementations || []).forEach(implementation => {
          if (!implementation) return;
          const requirementGroup = objectLookup[implementation.requirementGroup] || null;
          const requirement = findRequirementInGroup(requirementGroup, implementation.requirementId);
          rows.push({
            object,
            implementation,
            requirementGroup,
            requirement,
            label: requirementDisplayLabel(requirementGroup, requirement || { id: implementation.requirementId })
          });
        });
      });
      return rows;
    }

    function requirementGroupName(group) {
      if (!group) return 'Requirement Group';
      return String(group.name || group.id || 'Requirement Group').replace(/\s+Requirement Group$/i, '').trim() || 'Requirement Group';
    }

    function requirementAuthorityPrefix(group) {
      const authority = group?.authority || {};
      const provider = group?.provider || {};
      return authority.shortName || authority.name || provider.shortName || provider.name || provider.id || '';
    }

    function findRequirementInGroup(group, requirementId) {
      if (!group || !Array.isArray(group.requirements)) return null;
      return group.requirements.find(requirement => requirement && requirement.id === requirementId) || null;
    }

    function requirementDisplayLabel(group, requirement) {
      const requirementId = requirement?.id || requirement?.externalControlId || 'unknown';
      if (requirement?.externalControlId) {
        const prefix = requirementAuthorityPrefix(group);
        return prefix ? `${prefix}.${requirementId}` : requirementId;
      }
      const prefix = requirementAuthorityPrefix(group);
      return prefix ? `${prefix} ${requirementGroupName(group)} / ${requirementId}` : `${requirementGroupName(group)} / ${requirementId}`;
    }

    function requirementSourceText(group) {
      if (!group) return 'Unknown Requirement Group';
      const source = group.authority?.source || group.name || group.id;
      const authority = group.authority?.name;
      if (authority && source && authority !== source) {
        return `${authority} - ${source}`;
      }
      return source || authority || group.id;
    }

    function executiveStats() {
      const acceptableGroups = acceptableUseGroups();
      const acceptableRows = acceptableGroups.flatMap(group => group.rows);
      const uniqueMappedTech = new Set(
        acceptableRows
          .map(row => row.implementation?.ref)
          .filter(Boolean)
      );
      const requirementGroups = browserData.requirements?.groups || [];
      const requirementEvidence = requirementEvidenceRows();
      const domainStats = acceptableGroups.map(group => {
        const capabilityIds = new Set(group.rows.map(row => row.capability.id));
        const technologyRefs = new Set(
          group.rows
            .map(row => row.implementation?.ref)
            .filter(Boolean)
        );
        return {
          domain: group.domain,
          capabilityCount: capabilityIds.size,
          technologyCount: technologyRefs.size
        };
      }).sort((a, b) => b.technologyCount - a.technologyCount || b.capabilityCount - a.capabilityCount);
      const lifecycleCounts = {};
      acceptableRows.forEach(row => {
        const status = row.implementation?.lifecycleStatus || 'unknown';
        lifecycleCounts[status] = (lifecycleCounts[status] || 0) + 1;
      });
      const objectTypes = {
        softwareDeploymentPatterns: allObjects.filter(object => object.type === 'software_deployment_pattern').length,
        referenceArchitectures: allObjects.filter(object => object.type === 'reference_architecture').length,
        hosts: allObjects.filter(object => object.type === 'host').length,
        runtimeServices: allObjects.filter(object => object.type === 'runtime_service').length,
        dataAtRestServices: allObjects.filter(object => object.type === 'data_at_rest_service').length,
        edgeGatewayServices: allObjects.filter(object => object.type === 'edge_gateway_service').length,
        productServices: allObjects.filter(object => object.type === 'product_service').length
      };
      return {
        objectCount: allObjects.length,
        technologyCount: allObjects.filter(object => object.type === 'technology_component').length,
        capabilityCount: allObjects.filter(object => object.type === 'capability').length,
        softwareDeploymentPatternCount: objectTypes.softwareDeploymentPatterns,
        referenceArchitectureCount: objectTypes.referenceArchitectures,
        requirementGroupCount: requirementGroups.length,
        activeRequirementGroupCount: requirementGroups.filter(group => group.active || group.activation === 'always').length,
        requirementDefinitionCount: requirementGroups.reduce((count, group) => count + (group.requirementCount || 0), 0),
        controlEvidenceCount: requirementEvidence.length,
        controlEvidenceObjectCount: new Set(requirementEvidence.map(row => row.object.id)).size,
        acceptableUseMappingCount: acceptableRows.length,
        acceptableUseTechnologyCount: uniqueMappedTech.size,
        domainCount: allObjects.filter(object => object.type === 'domain').length,
        domainStats,
        lifecycleCounts,
        objectTypes,
        requirementEvidence
      };
    }

    function executiveMetricTile({ target, value, label, description, size = 'medium', accent = 'cyan', big = false }) {
      return `
        <article class="executive-tile ${size} executive-accent-${accent}" role="button" tabindex="0" data-executive-target="${escapeHtml(target)}">
          <div class="executive-tile-title">
            <p class="executive-number ${big ? 'big' : ''}">${formatNumber(value)}</p>
            <h3>${escapeHtml(label)}</h3>
          </div>
          <p>${escapeHtml(description)}</p>
        </article>
      `;
    }

    function executiveSidebarMarkup(stats) {
      return `
        <div class="sidebar-block">
          <div class="legend-title">DRAFT Overview</div>
          <div class="current-filter"><span class="dot" style="background:#7c3a6b"></span><span>${pluralize(stats.objectCount, 'catalog object')}</span></div>
          <div class="current-filter"><span class="dot" style="background:#22c55e"></span><span>${pluralize(stats.acceptableUseTechnologyCount, 'mapped Technology Component')}</span></div>
          <div class="current-filter"><span class="dot" style="background:#f59e0b"></span><span>${pluralize(stats.controlEvidenceCount, 'control answer')}</span></div>
        </div>
      `;
    }

    function executiveLifecyclePanelMarkup(stats) {
      const orderedStatuses = ['preferred', 'existing-only', 'candidate', 'deprecated', 'retired', 'unknown'];
      const rows = orderedStatuses
        .filter(status => stats.lifecycleCounts[status])
        .map(status => ({ status, count: stats.lifecycleCounts[status] }));
      const maxCount = Math.max(...rows.map(row => row.count), 1);
      return `
        <section class="executive-panel wide">
          <h3>Technology Lifecycle Mix</h3>
          <div class="executive-bars">
            ${rows.map(row => {
              const color = '#' + (lifecycleColors[row.status] || lifecycleColors.unknown);
              const width = Math.max(6, Math.round((row.count / maxCount) * 100));
              return `
                <div class="executive-bar-row">
                  <span>${escapeHtml(row.status)}</span>
                  <span class="executive-bar-track"><span class="executive-bar-fill" style="width:${width}%;background:${color};"></span></span>
                  <strong>${formatNumber(row.count)}</strong>
                </div>
              `;
            }).join('') || '<div class="empty-card">No lifecycle mappings are available.</div>'}
          </div>
        </section>
      `;
    }

    function executiveDomainPanelMarkup(stats) {
      return `
        <section class="executive-panel wide">
          <h3>Capability Domains</h3>
          <div class="executive-bars">
            ${stats.domainStats.slice(0, 6).map(item => `
              <div class="executive-snapshot-row">
                <span>${escapeHtml(item.domain.name || item.domain.id)}</span>
                <strong>${pluralize(item.technologyCount, 'tech')}</strong>
              </div>
              <div class="object-id">${pluralize(item.capabilityCount, 'capability', 'capabilities')}</div>
            `).join('') || '<div class="empty-card">No mapped capability domains are available.</div>'}
          </div>
        </section>
      `;
    }

    function executiveArchitecturePanelMarkup(stats) {
      const rows = [
        ['Software Deployment Patterns', stats.objectTypes.softwareDeploymentPatterns],
        ['Reference Architectures', stats.objectTypes.referenceArchitectures],
        ['Hosts', stats.objectTypes.hosts],
        ['Runtime Services', stats.objectTypes.runtimeServices],
        ['Data-at-Rest Services', stats.objectTypes.dataAtRestServices],
        ['Edge/Gateway Services', stats.objectTypes.edgeGatewayServices],
        ['Product Services', stats.objectTypes.productServices]
      ];
      const maxCount = Math.max(...rows.map(row => row[1]), 1);
      return `
        <section class="executive-panel wide">
          <h3>Architecture Inventory Mix</h3>
          <div class="executive-bars">
            ${rows.map(([label, count]) => {
              const width = Math.max(5, Math.round((count / maxCount) * 100));
              return `
                <div class="executive-bar-row">
                  <span>${escapeHtml(label)}</span>
                  <span class="executive-bar-track"><span class="executive-bar-fill" style="width:${width}%;"></span></span>
                  <strong>${formatNumber(count)}</strong>
                </div>
              `;
            }).join('')}
          </div>
        </section>
      `;
    }

    function executiveControlDrilldownMarkup(stats) {
      if (executiveDrilldown !== 'controls') {
        return '';
      }
      const grouped = new Map();
      stats.requirementEvidence.forEach(row => {
        const existing = grouped.get(row.object.id) || {
          object: row.object,
          count: 0,
          groups: new Set(),
          requirements: new Set(),
          statuses: {}
        };
        existing.count += 1;
        if (row.implementation.requirementGroup) {
          existing.groups.add(requirementGroupName(row.requirementGroup));
        }
        existing.requirements.add(row.label);
        const status = row.implementation.status || 'unknown';
        existing.statuses[status] = (existing.statuses[status] || 0) + 1;
        grouped.set(row.object.id, existing);
      });
      const rows = Array.from(grouped.values())
        .sort((a, b) => b.count - a.count || a.object.name.localeCompare(b.object.name));
      const requirementGroups = browserData.requirements?.groups || [];
      return `
        <section class="executive-panel full executive-drilldown">
          <div class="header-top">
            <div>
              <h3>Control Evidence Drill-Down</h3>
              <div class="object-id">${pluralize(stats.controlEvidenceCount, 'requirement evidence record')} across ${pluralize(stats.controlEvidenceObjectCount, 'catalog object')}</div>
            </div>
            <button class="action-button secondary" data-executive-target="clear-drilldown">Close</button>
          </div>
          ${rows.length ? `
            <div class="table-scroll">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Artifact</th>
                    <th>Type</th>
                    <th>Requirement Groups</th>
                    <th>Requirements</th>
                    <th>Evidence</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  ${rows.map(row => `
                    <tr>
                      <td>
                        <span class="ard-link" data-object-link="${escapeHtml(row.object.id)}">${escapeHtml(row.object.name)}</span>
                        <div class="object-id">${escapeHtml(row.object.id)}</div>
                      </td>
                      <td>${escapeHtml(row.object.typeLabel)}</td>
                      <td>${Array.from(row.groups).map(groupName => `<span class="badge">${escapeHtml(groupName)}</span>`).join('')}</td>
                      <td>${Array.from(row.requirements).slice(0, 4).map(label => `<span class="badge">${escapeHtml(label)}</span>`).join('')}${row.requirements.size > 4 ? `<div class="object-id">+${formatNumber(row.requirements.size - 4)} more</div>` : ''}</td>
                      <td>${formatNumber(row.count)}</td>
                      <td>${Object.entries(row.statuses).map(([status, count]) => `<span class="badge">${escapeHtml(status)}: ${formatNumber(count)}</span>`).join('')}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          ` : `
            <div class="empty-card">
              No object-level requirement evidence has been recorded yet. ${pluralize(stats.requirementDefinitionCount, 'requirement')} are available across ${pluralize(requirementGroups.length, 'Requirement Group')}.
            </div>
          `}
        </section>
      `;
    }

    function renderExecutiveView() {
      currentMode = 'executive';
      currentDetailId = null;
      destroyDetailCy();
      destroyImpactCy();
      syncHashForExecutiveView();
      const stats = executiveStats();
      renderSidebarContent(executiveSidebarMarkup(stats));
      // --- v1 dashboard alert banner: derive from real catalog state ---
      const _openRisks = (browserData.objects || []).filter(o => o.type === 'decision_record' && o.category === 'risk' && (o.status === 'open' || o.status === 'accepted'));
      const _retiredInUse = (browserData.objects || []).filter(o => o.lifecycleStatus === 'retired' && (o.referencedBy || []).length > 0);
      const _stubs = (browserData.objects || []).filter(o => o.catalogStatus === 'stub');
      const _alerts = [];
      if (_openRisks.length) _alerts.push({ severity: 'critical', label: `${_openRisks.length} open risk${_openRisks.length === 1 ? '' : 's'}`, detail: 'Decision records with open or accepted-but-unmitigated risk', target: 'risks' });
      if (_retiredInUse.length) _alerts.push({ severity: 'warning', label: `${_retiredInUse.length} retired component${_retiredInUse.length === 1 ? '' : 's'} still referenced`, detail: 'Lifecycle = retired but inbound references exist', target: 'retired' });
      if (_stubs.length) _alerts.push({ severity: 'info', label: `${_stubs.length} stub${_stubs.length === 1 ? '' : 's'} in drafting table`, detail: 'Catalog status = stub; awaiting authoring', target: 'drafting-table' });
      const _alertSeverity = sev => ({ critical: '#b93a3a', warning: '#c47a14', info: '#2a6fdb' }[sev] || '#7a6e60');
      const _alertBanner = _alerts.length ? `
        <section class="dashboard-alerts" aria-label="Catalog posture alerts">
          ${_alerts.map(a => `
            <button class="alert-card alert-${a.severity}" data-executive-target="${escapeHtml(a.target)}" style="border-left:4px solid ${_alertSeverity(a.severity)};">
              <span class="alert-sev" style="color:${_alertSeverity(a.severity)};">${a.severity.toUpperCase()}</span>
              <span class="alert-label">${escapeHtml(a.label)}</span>
              <span class="alert-detail">${escapeHtml(a.detail)}</span>
            </button>
          `).join('')}
        </section>
      ` : '';
      pageRoot.innerHTML = `
        <div class="view-shell">
          ${topNavMarkup()}
          ${_alertBanner}
          <section class="executive-hero">
            <div class="executive-hero-copy">
              <img class="executive-hero-logo" src="${escapeHtml(browserData.logoDataUri || 'draft-logo.png')}" alt="DRAFT">
              <div>
                <h2>${escapeHtml(browserData.catalogName || 'DRAFT')} catalog overview</h2>
                <p>${escapeHtml(browserData.catalogName || 'This catalog')} connects deployable architecture, technology lifecycle decisions, requirements, and deployment patterns so teams can draft systems from governed building blocks.</p>
                <div class="executive-hero-actions">
                  <button class="action-button" data-executive-target="drafting-table">Open Drafting Table</button>
                  <button class="action-button secondary" data-executive-target="acceptable-use">Acceptable Use Technology</button>
                </div>
              </div>
            </div>
            <div class="executive-snapshot">
              <div class="executive-snapshot-row"><span>Catalog Objects</span><strong>${formatNumber(stats.objectCount)}</strong></div>
              <div class="executive-snapshot-row"><span>Active Requirement Groups</span><strong>${formatNumber(stats.activeRequirementGroupCount)}</strong></div>
              <div class="executive-snapshot-row"><span>Mapped Technologies</span><strong>${formatNumber(stats.acceptableUseTechnologyCount)}</strong></div>
            </div>
          </section>
          <section class="executive-mosaic">
            ${executiveMetricTile({
              target: 'controls',
              value: stats.controlEvidenceCount,
              label: 'Controls Addressed',
              description: `${pluralize(stats.controlEvidenceObjectCount, 'artifact')} with recorded requirement evidence.`,
              size: 'large',
              accent: 'green',
              big: true
            })}
            ${executiveMetricTile({
              target: 'technologies',
              value: stats.technologyCount,
              label: 'Technology Components',
              description: 'Discrete vendor products and versions available to compose deployable objects.',
              size: 'medium',
              accent: 'cyan'
            })}
            ${executiveMetricTile({
              target: 'capabilities',
              value: stats.capabilityCount,
              label: 'Capabilities',
              description: 'The named abilities requirements resolve through before technology is selected.',
              size: 'small',
              accent: 'teal'
            })}
            ${executiveMetricTile({
              target: 'deployments',
              value: stats.softwareDeploymentPatternCount,
              label: 'Software Deployment Patterns',
              description: 'Intentional product deployment shapes documented in this catalog.',
              size: 'wide',
              accent: 'amber'
            })}
            ${executiveMetricTile({
              target: 'requirements',
              value: stats.requirementDefinitionCount,
              label: 'Requirement Definitions',
              description: `${pluralize(stats.requirementGroupCount, 'Requirement Group')} available for interviews and validation.`,
              size: 'medium',
              accent: 'violet'
            })}
            ${executiveMetricTile({
              target: 'acceptable-use',
              value: stats.acceptableUseMappingCount,
              label: 'Acceptable Use Mappings',
              description: `${pluralize(stats.acceptableUseTechnologyCount, 'unique Technology Component')} mapped to capability lifecycle decisions.`,
              size: 'small',
              accent: 'rose'
            })}
            ${executiveLifecyclePanelMarkup(stats)}
            ${executiveDomainPanelMarkup(stats)}
            ${executiveArchitecturePanelMarkup(stats)}
            ${executiveControlDrilldownMarkup(stats)}
          </section>
          ${(() => {
            const _stubObjects = (browserData.objects || []).filter(o => o.catalogStatus === 'stub');
            if (!_stubObjects.length) return '';
            const _statusFor = o => {
              if (o.type === 'decision_record' && o.status === 'open') return { label: 'blocked', tone: 'warn' };
              if ((o.unresolvedQuestions || []).length > 0) return { label: 'review', tone: 'info' };
              return { label: 'drafting', tone: 'neutral' };
            };
            return `
              <section class="section-card" id="drafting-table-section" aria-label="Drafting table queue">
                <div class="header-top">
                  <div class="header-title">
                    <h3>Drafting Table</h3>
                    <div class="object-id">${pluralize(_stubObjects.length, 'stub')} awaiting authoring</div>
                  </div>
                </div>
                <div class="table-wrap">
                  <table class="data-table">
                    <thead><tr><th>Object</th><th>Type</th><th>Status</th><th>Owner</th></tr></thead>
                    <tbody>
                      ${_stubObjects.map(o => {
                        const s = _statusFor(o);
                        const ownerName = (o.owner && (o.owner.name || o.owner.team)) || (o.definitionOwner && (o.definitionOwner.name || o.definitionOwner.team)) || '—';
                        return `
                          <tr>
                            <td><a href="#" class="object-link" data-object-id="${escapeHtml(o.uid)}"><strong>${escapeHtml(o.name)}</strong></a><div class="object-id">${escapeHtml(o.uid)}</div></td>
                            <td>${escapeHtml(o.typeLabel)}</td>
                            <td><span class="badge tone-${s.tone}">${s.label}</span></td>
                            <td>${escapeHtml(ownerName)}</td>
                          </tr>
                        `;
                      }).join('')}
                    </tbody>
                  </table>
                </div>
              </section>
            `;
          })()}
          ${(() => {
            const _today = Date.now();
            const _DAY = 86400000;
            const _parse = d => { if (!d) return null; const t = Date.parse(d); return isNaN(t) ? null : t; };
            const _runwayItems = (browserData.objects || [])
              .filter(o => o.type === 'technology_component')
              .map(o => {
                const vl = o.vendorLifecycle || {};
                const eol = _parse(vl.endOfLifeDate) || _parse(vl.endOfSupportDate);
                const mig = _parse(o.targetMigrationDate);
                return { o, eol, mig };
              })
              .filter(r => r.eol || r.mig)
              .sort((a, b) => (a.eol || a.mig || Infinity) - (b.eol || b.mig || Infinity));
            if (!_runwayItems.length) return '';
            const _fmtDays = ms => {
              const days = Math.round(ms / _DAY);
              if (Math.abs(days) < 60) return `${days >= 0 ? 'in ' : ''}${days} day${Math.abs(days) === 1 ? '' : 's'}${days < 0 ? ' ago' : ''}`;
              const months = Math.round(days / 30);
              return `${months >= 0 ? 'in ' : ''}${months} mo${Math.abs(months) === 1 ? '' : 's'}${months < 0 ? ' ago' : ''}`;
            };
            const _tone = ms => ms == null ? 'neutral' : ms < 0 ? 'warn' : ms < 90 * _DAY ? 'warn' : ms < 365 * _DAY ? 'info' : 'neutral';
            return `
              <section class="section-card" id="eol-runway-section" aria-label="EOL and migration runway">
                <div class="header-top">
                  <div class="header-title">
                    <h3>EOL &amp; Migration Runway</h3>
                    <div class="object-id">${pluralize(_runwayItems.length, 'technology component')} with vendor end-of-life or planned migration dates</div>
                  </div>
                </div>
                <div class="table-wrap">
                  <table class="data-table">
                    <thead><tr><th>Component</th><th>Vendor EOL</th><th>Target Migration</th><th>Lifecycle</th></tr></thead>
                    <tbody>
                      ${_runwayItems.map(r => {
                        const eolDelta = r.eol == null ? null : r.eol - _today;
                        const migDelta = r.mig == null ? null : r.mig - _today;
                        return `
                          <tr>
                            <td><a href="#" class="object-link" data-object-id="${escapeHtml(r.o.uid)}"><strong>${escapeHtml(r.o.name)}</strong></a><div class="object-id">${escapeHtml(r.o.classification || r.o.subtype || '')}</div></td>
                            <td>${r.eol ? `<span class="badge tone-${_tone(eolDelta)}">${_fmtDays(eolDelta)}</span>` : '<span class="object-id">—</span>'}</td>
                            <td>${r.mig ? `<span class="badge tone-${_tone(migDelta)}">${_fmtDays(migDelta)}</span>` : '<span class="object-id">unset</span>'}</td>
                            <td><span class="badge">${escapeHtml(r.o.lifecycleStatus || 'unknown')}</span></td>
                          </tr>
                        `;
                      }).join('')}
                    </tbody>
                  </table>
                </div>
              </section>
            `;
          })()}
        </div>
      `;
      attachTopNavHandlers();
      attachExecutiveHandlers();
      attachObjectLinkHandlers(pageRoot);
    }

    const OBJECT_TYPE_GUIDE = {
      deployable: [
        {
          type: 'technology_component',
          label: 'Technology Component',
          purpose: 'A discrete vendor product, agent, operating system, platform, or software package with a specific product/version lifecycle.',
          deployableRole: 'Deployed as an ingredient inside Hosts and service objects.'
        },
        {
          type: 'host',
          label: 'Host',
          purpose: 'An operational platform that combines an operating system, compute platform, and required host capabilities.',
          deployableRole: 'Deploys the runtime substrate for self-managed services.'
        },
        {
          type: 'runtime_service',
          label: 'Runtime Service',
          purpose: 'A reusable behavioral service such as web, app, cache, worker, messaging, or serverless runtime.',
          deployableRole: 'Deploys runtime behavior on a host or through PaaS, SaaS, or appliance delivery.'
        },
        {
          type: 'data_at_rest_service',
          label: 'Data-at-Rest Service',
          purpose: 'A reusable service for durable data such as database, file, object, search, analytics, or storage.',
          deployableRole: 'Deploys persistence behavior on a host or through PaaS, SaaS, or appliance delivery.'
        },
        {
          type: 'edge_gateway_service',
          label: 'Edge/Gateway Service',
          purpose: 'A reusable boundary service such as WAF, firewall, API gateway, load balancer, ingress, or proxy.',
          deployableRole: 'Deploys traffic control behavior at a product or network boundary.'
        },
        {
          type: 'product_service',
          label: 'Product Service',
          purpose: 'A first-party custom binary or black-box service that runs on a selected deployable object.',
          deployableRole: 'Deploys company-authored application behavior.'
        },
        {
          type: 'software_deployment_pattern',
          label: 'Software Deployment Pattern',
          purpose: 'The intended assembly of deployable objects for a product or product capability.',
          deployableRole: 'Defines the deployable package shape that automation can target.'
        }
      ],
      nonDeployable: [
        { type: 'capability', label: 'Capability', purpose: 'Names an ability required by architecture and records company-approved Technology Components for it.' },
        { type: 'requirement_group', label: 'Requirement Group', purpose: 'Groups requirements used by the Draftsman during interviews and by validation after authoring.' },
        { type: 'domain', label: 'Domain', purpose: 'Groups capabilities into a planning area such as compute, observability, identity, or data.' },
        { type: 'reference_architecture', label: 'Reference Architecture', purpose: 'Documents a reusable deployment approach that Software Deployment Patterns may follow.' },
        { type: 'decision_record', label: 'Decision Record', purpose: 'Records an architecture decision, risk, exception, or rationale.' },
        { type: 'drafting_session', label: 'Drafting Session', purpose: 'Stores interview memory, assumptions, unresolved questions, and generated work while drafting.' },
        { type: 'object_patch', label: 'Object Patch', purpose: 'A workspace overlay that changes selected fields on a framework-owned object without copying the full object.' }
      ]
    };

    function objectTypeCount(type) {
      return allObjects.filter(object => object.type === type).length;
    }

    function objectTypeRowsMarkup(rows, deployable = false) {
      return rows.map(row => `
        <tr>
          <td><strong>${escapeHtml(row.label)}</strong><div class="object-id">${escapeHtml(row.type)}</div></td>
          <td>${escapeHtml(row.purpose)}</td>
          ${deployable ? `<td>${escapeHtml(row.deployableRole)}</td>` : ''}
          <td>${formatNumber(objectTypeCount(row.type))}</td>
        </tr>
      `).join('');
    }

    function objectTypesSidebarMarkup() {
      const deployableCount = OBJECT_TYPE_GUIDE.deployable.reduce((count, row) => count + objectTypeCount(row.type), 0);
      const nonDeployableCount = OBJECT_TYPE_GUIDE.nonDeployable.reduce((count, row) => count + objectTypeCount(row.type), 0);
      return `
        <div class="sidebar-block">
          <div class="legend-title">Object Types</div>
          <div class="current-filter"><span class="dot" style="background:#22c55e"></span><span>${pluralize(deployableCount, 'deployable object')}</span></div>
          <div class="current-filter"><span class="dot" style="background:#64748b"></span><span>${pluralize(nonDeployableCount, 'non-deployable object')}</span></div>
        </div>
      `;
    }

    function renderObjectTypesView() {
      currentMode = 'object-types';
      currentDetailId = null;
      destroyDetailCy();
      destroyImpactCy();
      syncHashForObjectTypesView();
      renderSidebarContent(objectTypesSidebarMarkup());
      pageRoot.innerHTML = `
        <div class="view-shell">
          ${topNavMarkup()}
          <section class="header-card">
            <div class="header-top">
              <div class="header-title">
                <h2>DRAFT Object Types</h2>
                <div class="object-id">Deployable architecture versus framework content</div>
              </div>
            </div>
            <div class="header-description">Deployable objects describe architecture that can eventually become automation inputs. Non-deployable objects guide, govern, remember, or explain how deployable architecture is drafted.</div>
          </section>
          <section class="section-card">
            <h3>Deployable Architecture</h3>
            <div class="table-wrap">
              <table class="data-table">
                <thead><tr><th>Object Type</th><th>Purpose</th><th>Deployable Role</th><th>Catalog Count</th></tr></thead>
                <tbody>${objectTypeRowsMarkup(OBJECT_TYPE_GUIDE.deployable, true)}</tbody>
              </table>
            </div>
          </section>
          <section class="section-card">
            <h3>Non-Deployable Architecture</h3>
            <div class="table-wrap">
              <table class="data-table">
                <thead><tr><th>Object Type</th><th>Purpose</th><th>Catalog Count</th></tr></thead>
                <tbody>${objectTypeRowsMarkup(OBJECT_TYPE_GUIDE.nonDeployable, false)}</tbody>
              </table>
            </div>
          </section>
          <section class="section-card">
            <h3>Delivery Models</h3>
            <div class="header-description">PaaS, SaaS, appliance, and self-managed are delivery models on Runtime Service, Data-at-Rest Service, and Edge/Gateway Service objects. They are not separate object types.</div>
          </section>
        </div>
      `;
      attachTopNavHandlers();
    }

    function companyOnboardingSidebarMarkup() {
      return `
        <div class="sidebar-block">
          <div class="legend-title">Onboarding Path</div>
          <div class="current-filter"><span class="dot" style="background:#22c55e"></span><span>Install and create workspace</span></div>
          <div class="current-filter"><span class="dot" style="background:#7c3a6b"></span><span>Activate requirements</span></div>
          <div class="current-filter"><span class="dot" style="background:#8b5cf6"></span><span>Map acceptable-use technology</span></div>
          <div class="current-filter"><span class="dot" style="background:#f59e0b"></span><span>Draft deployable architecture</span></div>
        </div>
      `;
    }

    function onboardingStepMarkup(number, title, description, items = []) {
      return `
        <article class="object-card">
          <div>
            <h3>${number}. ${escapeHtml(title)}</h3>
            <div class="object-id">${escapeHtml(description)}</div>
          </div>
          ${items.length ? `<ul>${items.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul>` : ''}
        </article>
      `;
    }

    function renderCompanyOnboardingView() {
      currentMode = 'onboarding';
      currentDetailId = null;
      destroyDetailCy();
      destroyImpactCy();
      syncHashForOnboardingView();
      renderSidebarContent(companyOnboardingSidebarMarkup());
      const steps = [
        ['Install', 'Install DRAFT Table and select or create a private company DRAFT repo.', ['Run draft-table onboard', 'Vendor the selected framework copy into .draft/framework/', 'Commit workspace bootstrap files']],
        ['Decide Governance', 'Make build-time workspace decisions before drafting product architecture.', ['Define business taxonomy in .draft/workspace.yaml', 'Activate Requirement Groups explicitly', 'Choose whether strict active-group disposition is enabled']],
        ['Assign Capability Owners', 'Name the company decision authority for each mapped capability.', ['Authentication, operating systems, compute, logging, monitoring, patching, and security monitoring need clear owners', 'Owners approve acceptable-use lifecycle changes']],
        ['Map Acceptable Use', 'Connect capabilities to approved Technology Components and lifecycle states.', ['Use preferred, candidate, existing-only, deprecated, and retired deliberately', 'Technology Components carry vendor lifecycle; capability mappings carry company lifecycle']],
        ['Draft Deployable Objects', 'Create reusable deployable architecture from behavior first, delivery model second.', ['Host', 'Runtime Service', 'Data-at-Rest Service', 'Edge/Gateway Service', 'Product Service', 'Software Deployment Pattern']],
        ['Validate And Publish', 'Run validation, regenerate the browser, review the Git diff, and commit source plus generated output.', ['draft-table validate', 'generate_browser.py --workspace . --output docs/index.html', 'Review warnings as implementation gaps']]
      ];
      const gapSignals = [
        'Requirement Groups are unclear as object definitions, delivery overlays, or workspace governance.',
        'The Draftsman asks open-ended capability questions when approved implementations exist.',
        'Technology Components appear to have company lifecycle outside capability mappings.',
        'Approved capabilities have no requirement trace.',
        'PaaS, SaaS, or appliance language sounds like object types instead of delivery models.',
        'Validation failures do not tell the Draftsman exactly what to add or where to look next.'
      ];
      pageRoot.innerHTML = `
        <div class="view-shell">
          ${topNavMarkup()}
          <section class="header-card">
            <div class="header-top">
              <div class="header-title">
                <h2>Company Onboarding Tutorial</h2>
                <div class="object-id">From empty private repo to governed DRAFT catalog</div>
              </div>
            </div>
            <div class="header-description">A company implements DRAFT by vendoring the framework into a private repo, activating the Requirement Groups it architects against, assigning capability owners, mapping acceptable-use Technology Components, and drafting deployable architecture through validation.</div>
          </section>
          <section class="section-card">
            <h3>Operating Model</h3>
            <div class="table-wrap">
              <table class="data-table">
                <thead><tr><th>Area</th><th>Owned By</th><th>Purpose</th></tr></thead>
                <tbody>
                  <tr><td>Upstream Framework</td><td>DRAFT project</td><td>Schemas, base Requirement Groups, base capabilities, templates, tools, examples, and Draftsman guidance.</td></tr>
                  <tr><td>Vendored Framework</td><td>Company repo</td><td>The reviewed framework copy under .draft/framework/ used for normal private Draftsman work.</td></tr>
                  <tr><td>Workspace Configuration</td><td>Company repo</td><td>Business taxonomy, active Requirement Groups, capability owners, implementation mappings, and overlays.</td></tr>
                  <tr><td>Architecture Catalog</td><td>Company repo</td><td>Technology Components, deployable objects, Reference Architectures, Software Deployment Patterns, decisions, and Drafting Sessions.</td></tr>
                </tbody>
              </table>
            </div>
          </section>
          <section class="section-card">
            <h3>Implementation Path</h3>
            <div class="object-grid">
              ${steps.map((step, index) => onboardingStepMarkup(index + 1, step[0], step[1], step[2])).join('')}
            </div>
          </section>
          <section class="section-card">
            <h3>Readiness Checklist</h3>
            <ul>
              <li>Private repo contains .draft/framework/ and .draft/framework.lock.</li>
              <li>.draft/workspace.yaml declares business taxonomy and active Requirement Groups.</li>
              <li>Capability owners are identified wherever implementations are mapped.</li>
              <li>Approved capabilities are referenced by Requirement Group requirements.</li>
              <li>Acceptable-use Technology Components are mapped by capability.</li>
              <li>Baseline Hosts, Runtime Services, Data-at-Rest Services, and Edge/Gateway Services exist for common deployment patterns.</li>
              <li>Validation passes and the generated browser reflects the catalog.</li>
            </ul>
          </section>
          <section class="section-card">
            <h3>Gap Signals Before 1.0</h3>
            <ul>${gapSignals.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul>
          </section>
        </div>
      `;
      attachTopNavHandlers();
    }

    function navigateExecutiveTarget(target) {
      if (target === 'drafting-table') {
        activeCategory = 'architecture';
        activeFilter = 'all';
        executiveDrilldown = null;
        renderListView();
        return;
      }
      if (target === 'technologies') {
        activeCategory = 'supporting';
        activeFilter = 'technology_component';
        executiveDrilldown = null;
        renderListView();
        return;
      }
      if (target === 'capabilities') {
        activeCategory = 'framework';
        activeFilter = 'capability';
        executiveDrilldown = null;
        renderListView();
        return;
      }
      if (target === 'deployments') {
        activeCategory = 'architecture';
        activeFilter = 'software_deployment_pattern';
        executiveDrilldown = null;
        renderListView();
        return;
      }
      if (target === 'requirements') {
        activeCategory = 'framework';
        activeFilter = 'requirement_group';
        executiveDrilldown = null;
        renderListView();
        return;
      }
      if (target === 'acceptable-use') {
        executiveDrilldown = null;
        renderAcceptableUseView();
        return;
      }
      if (target === 'controls') {
        executiveDrilldown = 'controls';
        renderExecutiveView();
        return;
      }
      if (target === 'clear-drilldown') {
        executiveDrilldown = null;
        renderExecutiveView();
      }
    }

    function attachExecutiveHandlers() {
      pageRoot.querySelectorAll('[data-executive-target]').forEach(item => {
        item.addEventListener('click', () => {
          navigateExecutiveTarget(item.dataset.executiveTarget);
        });
        item.addEventListener('keydown', event => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            navigateExecutiveTarget(item.dataset.executiveTarget);
          }
        });
      });
    }

    function acceptableUseSidebarMarkup(groups, mappedCount) {
      const capabilityCount = groups.reduce((count, group) => {
        const ids = new Set(group.rows.map(row => row.capability.id));
        return count + ids.size;
      }, 0);
      return `
        <div class="sidebar-block">
          <div class="legend-title">Acceptable Use Technology</div>
          <div class="current-filter"><span class="dot" style="background:#7c3a6b"></span><span>${mappedCount} mapped Technology Components</span></div>
          <div class="current-filter"><span class="dot" style="background:#22c55e"></span><span>${capabilityCount} capability groups</span></div>
          <div class="current-filter"><span class="dot" style="background:#f59e0b"></span><span>${groups.length} domain groups</span></div>
        </div>
      `;
    }

    function acceptableUseOwnerMarkup(owner) {
      if (!owner?.team && !owner?.contact) {
        return '<span>Owner: Not assigned</span><span>No contact documented</span>';
      }
      return `
        <span>Owner: ${escapeHtml(owner.team || 'Not assigned')}</span>
        <span>${escapeHtml(owner.contact || 'No contact documented')}</span>
      `;
    }

    function acceptableUseTechnologyMarkup(technology, implementation) {
      if (!technology) {
        return `<span class="muted-cell">${escapeHtml(implementation.ref || 'Unknown Technology Component')}</span>`;
      }
      return `
        <span class="ard-link" data-object-link="${escapeHtml(technology.id)}">${escapeHtml(technology.name)}</span>
        <div class="object-id">${escapeHtml(technology.id)}</div>
      `;
    }

    function acceptableUseCapabilityCount(rows) {
      const uniqueRefs = new Set(
        rows
          .map(row => row.implementation?.ref)
          .filter(Boolean)
      );
      const count = uniqueRefs.size;
      return `${count} ${count === 1 ? 'Technology Component' : 'Technology Components'}`;
    }

    function acceptableUseDomainMarkup(group) {
      const capabilityGroups = [];
      group.rows.forEach(row => {
        let capabilityGroup = capabilityGroups[capabilityGroups.length - 1];
        if (!capabilityGroup || capabilityGroup.capability.id !== row.capability.id) {
          capabilityGroup = { capability: row.capability, rows: [] };
          capabilityGroups.push(capabilityGroup);
        }
        capabilityGroup.rows.push(row);
      });
      return `
        <section class="section-card">
          <h3>${escapeHtml(group.domain.name || group.domain.id)}</h3>
          <div class="object-id">${escapeHtml(group.domain.id || '')}</div>
          ${group.domain.description ? `<div class="header-description">${escapeHtml(group.domain.description)}</div>` : ''}
          ${capabilityGroups.map(capabilityGroup => {
            const capability = capabilityGroup.capability;
            return `
              <div class="acceptable-use-capability">
                <div class="acceptable-use-capability-header">
                  <div class="acceptable-use-capability-title">
                    <span class="ard-link" data-object-link="${escapeHtml(capability.id)}">${escapeHtml(capability.name)}</span>
                    <span class="badge">${acceptableUseCapabilityCount(capabilityGroup.rows)}</span>
                    <span class="object-id">${escapeHtml(capability.id)}</span>
                  </div>
                  <div class="acceptable-use-owner">${acceptableUseOwnerMarkup(capability.owner)}</div>
                </div>
                <div class="table-scroll">
                  <table class="data-table acceptable-use-table">
                    <thead>
                      <tr>
                        <th>Vendor</th>
                        <th>Technology Component</th>
                        <th>Status</th>
                        <th>Configuration</th>
                        <th>Notes</th>
                      </tr>
                    </thead>
                    <tbody>
                      ${capabilityGroup.rows.map(row => {
                        const implementation = row.implementation;
                        const technology = row.technology;
                        const configuration = implementationConfigurationLabel(technology, implementation);
                        return `
                          <tr>
                            <td>${technology?.vendor ? escapeHtml(technology.vendor) : '<span class="muted-cell">Not documented</span>'}</td>
                            <td>${acceptableUseTechnologyMarkup(technology, implementation)}</td>
                            <td>${lifecycleBadge(implementation.lifecycleStatus || 'unknown')}</td>
                            <td>${configuration ? escapeHtml(configuration) : '<span class="muted-cell">Default</span>'}</td>
                            <td>${implementation?.notes ? escapeHtml(implementation.notes) : '<span class="muted-cell">No notes</span>'}</td>
                          </tr>
                        `;
                      }).join('')}
                    </tbody>
                  </table>
                </div>
              </div>
            `;
          }).join('')}
        </section>
      `;
    }

    function renderAcceptableUseView() {
      currentMode = 'acceptable-use';
      currentDetailId = null;
      executiveDrilldown = null;
      destroyDetailCy();
      destroyImpactCy();
      syncHashForAcceptableUseView();
      const groups = acceptableUseGroups();
      const mappedCount = groups.reduce(
        (count, group) => count + group.rows.filter(row => row.implementation).length,
        0
      );
      const capabilityCount = groups.reduce((count, group) => {
        const ids = new Set(group.rows.map(row => row.capability.id));
        return count + ids.size;
      }, 0);
      renderSidebarContent(acceptableUseSidebarMarkup(groups, mappedCount));
      pageRoot.innerHTML = `
        <div class="view-shell">
          ${topNavMarkup()}
          <section class="header-card">
            <div class="header-top">
              <div class="header-title">
                <h2>Acceptable Use Technology</h2>
                <div class="object-id">Technology Component lifecycle map</div>
              </div>
              <div class="badges">
                <span class="badge">${mappedCount} mapped Technology Components</span>
                <span class="badge">${capabilityCount} capability groups</span>
                <span class="badge">${groups.length} domain groups</span>
              </div>
            </div>
            <div class="header-description">
              Technology Components grouped by governing domain and capability. Contact the capability owner when a Technology Component needs to be added, retired, or moved to a different lifecycle status.
            </div>
          </section>
          <div class="content-rows">
            ${groups.map(acceptableUseDomainMarkup).join('') || '<div class="empty-card" style="padding:24px;">No Technology Component implementations are mapped.</div>'}
          </div>
        </div>
      `;
      attachTopNavHandlers();
      attachObjectLinkHandlers(pageRoot);
    }

    function renderListView() {
      currentMode = 'list';
      currentDetailId = null;
      executiveDrilldown = null;
      destroyDetailCy();
      destroyImpactCy();
      const category = categoryConfig();
      const filtered = filterObjects();
      const rows = activeFilter === 'all'
        ? category.rows.map(row => ({ row, objects: filterObjectsByTypes(row.types) })).filter(section => section.objects.length)
        : (() => {
            const filter = activeFilterConfig();
            const row = category.rows.find(item => item.id === activeFilter)
              || { id: filter.id, label: filter.label, types: filter.types };
            return [{ row, objects: filtered }];
          })();
      syncHashForListView();
      renderSidebarContent(sidebarMarkup(businessPillarSidebarMarkup(filtered)));
      pageRoot.innerHTML = `
        <div class="view-shell">
          ${topNavMarkup()}
          <div class="tab-row">
            ${CATEGORY_CONFIG.map(categoryItem => `<button class="tab-button ${categoryItem.id === activeCategory ? 'active' : ''}" data-category-tab="${categoryItem.id}">${escapeHtml(categoryItem.label)}</button>`).join('')}
          </div>
          <div class="filter-row">
            ${category.filters.map(filter => `<button class="filter-button ${filter.id === activeFilter ? 'active' : ''}" data-filter="${filter.id}">${escapeHtml(filter.label)}</button>`).join('')}
          </div>
          <div class="view-title">
            <span>${filtered.length} objects</span>
            <span>Showing ${escapeHtml(category.label)}${activeFilter === 'all' ? '' : ` / ${escapeHtml(formatListFilterLabel(activeFilter))}`}</span>
          </div>
          <div class="content-rows">
            ${rows.map(section => listRowMarkup(section.row, section.objects)).join('') || `<div class="empty-card" style="padding:24px;">No objects in this view.</div>`}
          </div>
        </div>
      `;

      pageRoot.querySelectorAll('[data-category-tab]').forEach(button => {
        button.addEventListener('click', () => {
          activeCategory = button.dataset.categoryTab;
          activeFilter = 'all';
          renderListView();
        });
      });

      pageRoot.querySelectorAll('[data-filter]').forEach(button => {
        button.addEventListener('click', () => {
          activeFilter = button.dataset.filter;
          renderListView();
        });
      });

      pageRoot.querySelectorAll('[data-object-id]').forEach(card => {
        card.addEventListener('click', () => {
          showDetailView(card.dataset.objectId);
        });
      });

      attachTopNavHandlers();
      attachSidebarHandlers();
    }

    function flattenDecisionEntries(prefix, value, entries) {
      if (Array.isArray(value)) {
        if (value.every(item => item && typeof item === 'object' && !Array.isArray(item))) {
          value.forEach((item, index) => {
            flattenDecisionEntries(`${prefix}[${index + 1}]`, item, entries);
          });
        } else {
          entries.push({ key: prefix, value: value.join(', ') });
        }
        return;
      }
      if (value && typeof value === 'object' && !Array.isArray(value)) {
        Object.entries(value).forEach(([childKey, childValue]) => {
          flattenDecisionEntries(prefix ? `${prefix}.${childKey}` : childKey, childValue, entries);
        });
        return;
      }
      entries.push({ key: prefix, value: String(value) });
    }

    function decisionMarkup(object, excludedRootKeys = []) {
      const excluded = new Set(excludedRootKeys);
      const decisions = Object.fromEntries(
        Object.entries(object.architecturalDecisions || {}).filter(([key]) => !excluded.has(key))
      );
      const entries = [];
      flattenDecisionEntries('', decisions, entries);
      if (!entries.length) {
        return '<div class="empty-card">No architectural decisions are defined for this object.</div>';
      }
      return `
        <div class="decisions-grid single">
          <section class="decision-card">
            <h4>Architecture Decisions</h4>
            <dl class="definition-list">
              ${entries.map(entry => `<dt>${escapeHtml(entry.key)}</dt><dd>${escapeHtml(entry.value)}</dd>`).join('')}
            </dl>
          </section>
        </div>
      `;
    }

    function businessContextMarkup(object) {
      if (object.type !== 'software_deployment_pattern') {
        return '';
      }
      const context = object.businessContext || {};
      if (!context.pillar && !context.productFamily && !context.notes) {
        return '';
      }
      const pillar = businessPillarForObject(object);
      const additional = Array.isArray(context.additionalPillars)
        ? context.additionalPillars.map(id => businessPillarLookup[id]?.name || formatTitleCase(String(id).replace(/^business-pillar\\./, '').replace(/-/g, ' ')))
        : [];
      return `
        <section class="section-card">
          <h3>Business Context</h3>
          <dl class="definition-list">
            <dt>Primary Pillar</dt>
            <dd>${escapeHtml(pillar.name)}</dd>
            ${additional.length ? `<dt>Additional Pillars</dt><dd>${escapeHtml(additional.join(', '))}</dd>` : ''}
            ${context.productFamily ? `<dt>Product Family</dt><dd>${escapeHtml(context.productFamily)}</dd>` : ''}
            ${context.notes ? `<dt>Notes</dt><dd>${escapeHtml(context.notes)}</dd>` : ''}
          </dl>
        </section>
      `;
    }

    function sourceRepositoryMarkup(object) {
      const repos = object.architecturalDecisions?.sourceRepositories || [];
      if (!Array.isArray(repos) || !repos.length) {
        return '';
      }
      return `
        <section class="section-card">
          <h3>Source Repositories</h3>
          <div class="table-scroll">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Repository</th>
                  <th>Product Service</th>
                  <th>Language</th>
                  <th>Signals</th>
                </tr>
              </thead>
              <tbody>
                ${repos.map(repo => {
                  const productService = repo.productService || '';
                  const service = productService ? objectLookup[productService] : null;
                  const repoName = repo.repositoryName || repo.sourceRepository || 'Unknown repository';
                  const repoUrl = repo.sourceRepository || '';
                  return `
                    <tr>
                      <td>
                        ${repoUrl ? `<a href="${escapeHtml(repoUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(repoName)}</a>` : escapeHtml(repoName)}
                        ${repoUrl && repoUrl !== repoName ? `<div class="object-id">${escapeHtml(repoUrl)}</div>` : ''}
                      </td>
                      <td>
                        ${service ? `<span class="ard-link" data-object-link="${escapeHtml(productService)}">${escapeHtml(service.name)}</span>` : escapeHtml(productService || 'Not linked')}
                        ${productService ? `<div class="object-id">${escapeHtml(productService)}</div>` : ''}
                      </td>
                      <td>${escapeHtml(repo.repositoryPrimaryLanguage || '')}</td>
                      <td>${escapeHtml(repo.observedRuntimeSignals || '')}</td>
                    </tr>
                  `;
                }).join('')}
              </tbody>
            </table>
          </div>
        </section>
      `;
    }

    function interactionMarkup(object) {
      const interactions = object.externalInteractions || [];
      if (!interactions.length) {
        return '<div class="empty-card">No external interactions are documented for this object.</div>';
      }
      return `
        <div class="interactions-list">
          ${interactions.map(interaction => `
            <article class="interaction-card">
              <div class="interaction-top">
                <div class="interaction-name">${escapeHtml(interaction.name || 'External Interaction')}</div>
                ${(interaction.capabilities || []).map(cap => `<span class="badge ${capabilityClass(cap)}">${escapeHtml(cap)}</span>`).join(' ')}
              </div>
              ${interaction.notes ? `<div class="interaction-notes">${escapeHtml(interaction.notes)}</div>` : ''}
              ${interaction.ref ? `<div class="interaction-ref">${escapeHtml(interaction.ref)}</div>` : ''}
            </article>
          `).join('')}
        </div>
      `;
    }

    function requirementMechanismSentence(mechanism) {
      if (mechanism.mechanism === 'externalInteraction') {
        return `externalInteraction(capability=${mechanism.criteria?.capability || 'unknown'})`;
      }
      if (mechanism.mechanism === 'internalComponent') {
        return `internalComponent(role=${mechanism.criteria?.role || 'unknown'})`;
      }
      if (mechanism.mechanism === 'architecturalDecision') {
        return `architecturalDecision(key=${mechanism.key || 'unknown'})`;
      }
      return mechanism.mechanism || 'unknown';
    }

    function odcRequirementsMarkup(object) {
      const requirements = object.requirements || [];
      if (!requirements.length) {
        return '<div class="empty-card">No requirements are documented for this Requirement Group.</div>';
      }
      return `
        <section class="section-card">
          <h3>Requirements</h3>
          <div class="section-stack">
            ${requirements.map(requirement => `
              <article class="requirement-card">
                <div class="requirement-name">${escapeHtml(requirementDisplayLabel(object, requirement))}</div>
                <div class="requirement-badges">
                  ${requirement.externalControlId ? `<span class="requirement-badge">${escapeHtml(requirementSourceText(object))}</span>` : ''}
                  ${requirement.relatedCapability ? `<span class="requirement-badge">${escapeHtml(requirement.relatedCapability)}</span>` : ''}
                  <span class="requirement-badge ${requirement.requirementMode === 'conditional' ? 'conditional' : ''}">${escapeHtml(requirement.requirementMode || 'mandatory')}</span>
                  ${requirement.naAllowed ? '<span class="requirement-badge conditional">N/A allowed</span>' : ''}
                </div>
                <div class="requirement-description">${escapeHtml(requirement.description || '')}</div>
                ${requirement.rationale ? `
                  <div class="requirement-rationale-label">Rationale</div>
                  <div class="requirement-rationale">${escapeHtml(requirement.rationale)}</div>
                ` : ''}
                <div class="mechanism-label">Can be satisfied by</div>
                <div class="mechanism-list">
                  ${(requirement.canBeSatisfiedBy || []).map(mechanism => `
                    <div class="mechanism-item">
                      <div class="mechanism-text">${escapeHtml(requirementMechanismSentence(mechanism))}</div>
                      ${mechanism.example ? `<div class="mechanism-example">${escapeHtml(mechanism.example)}</div>` : ''}
                    </div>
                  `).join('')}
                </div>
              </article>
            `).join('')}
          </div>
        </section>
      `;
    }

    function requirementEvidenceMarkup(object) {
      const implementations = object.requirementImplementations || [];
      if (!implementations.length) {
        return '';
      }
      return `
        <section class="section-card">
          <h3>Requirement Evidence</h3>
          <div class="table-scroll">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Requirement</th>
                  <th>Status</th>
                  <th>Mechanism</th>
                  <th>Evidence</th>
                </tr>
              </thead>
              <tbody>
                ${implementations.map(implementation => {
                  const group = objectLookup[implementation.requirementGroup] || null;
                  const requirement = findRequirementInGroup(group, implementation.requirementId);
                  const refObject = implementation.ref ? objectLookup[implementation.ref] : null;
                  const evidence = refObject
                    ? `<span class="ard-link" data-object-link="${escapeHtml(refObject.id)}">${escapeHtml(refObject.name)}</span>`
                    : escapeHtml(implementation.ref || implementation.key || implementation.notes || 'Not documented');
                  return `
                    <tr>
                      <td>
                        <strong>${escapeHtml(requirementDisplayLabel(group, requirement || { id: implementation.requirementId }))}</strong>
                        <div class="object-id">${escapeHtml(requirementSourceText(group))}</div>
                      </td>
                      <td><span class="badge">${escapeHtml(implementation.status || 'unknown')}</span></td>
                      <td>${escapeHtml(implementation.mechanism || 'unknown')}</td>
                      <td>${evidence}</td>
                    </tr>
                  `;
                }).join('')}
              </tbody>
            </table>
          </div>
        </section>
      `;
    }

    function requirementGroupByName(name) {
      return allObjects.find(object => object.type === 'requirement_group' && object.name === name) || null;
    }

    function sdmRisksMarkup(object) {
      const references = object.decisionRecords || [];
      if (!references.length) {
        return '';
      }
      return `
        <section class="section-card">
          <h3>Decision Records</h3>
          <div class="section-stack">
            ${references.map(entry => {
              const ard = objectLookup[entry.ref];
              return `
                <article class="odc-card">
                  <div class="odc-name">
                    ${ard ? `<span class="ard-link" data-object-link="${ard.id}">${escapeHtml(ard.name)}</span>` : escapeHtml(entry.ref || 'Unknown Decision Record')}
                  </div>
                  <div class="object-id">${escapeHtml(entry.ref || '')}</div>
                </article>
              `;
            }).join('')}
          </div>
        </section>
      `;
    }

    function sdmServiceGroupsMarkup(object) {
      const groups = object.serviceGroups || [];
      const scalingUnits = new Map((object.scalingUnits || []).map(unit => [unit.name, unit]));
      if (!groups.length) {
        return '<div class="empty-card">No service groups are documented for this Software Deployment Pattern.</div>';
      }
      return `
        <section class="section-card">
          <h3>Service Groups</h3>
          <div class="section-stack">
            ${groups.map(group => {
              const scalingUnit = group.scalingUnit ? scalingUnits.get(group.scalingUnit) : null;
              const externalInteractions = (group.externalInteractions || []).filter(item => (item.type || 'external') !== 'internal');
              const internalInteractions = (group.externalInteractions || []).filter(item => (item.type || 'external') === 'internal');
              const deployableEntries = group.deployableObjects || [];
              const productCount = deployableEntries.filter(entry => objectLookup[entry.ref]?.type === 'product_service').length;
              const paasCount = deployableEntries.filter(entry => objectLookup[entry.ref]?.deliveryModel === 'paas').length;
              const saasCount = deployableEntries.filter(entry => objectLookup[entry.ref]?.deliveryModel === 'saas').length;
              const applianceCount = deployableEntries.filter(entry => objectLookup[entry.ref]?.deliveryModel === 'appliance').length;
              const reusableCount = deployableEntries.filter(entry => objectLookup[entry.ref] && objectLookup[entry.ref]?.type !== 'product_service').length;
              return `
                <article class="odc-card">
                  <div class="odc-name">${escapeHtml(group.name || 'Unnamed Service Group')}</div>
                  <div class="interaction-notes">${escapeHtml(group.deploymentTarget || 'Unspecified deployment target')}</div>
                  <div class="badges">
                    ${group.scalingUnit ? `<span class="badge">${escapeHtml(group.scalingUnit)}</span>` : '<span class="badge">unscoped</span>'}
                    ${scalingUnit?.type ? `<span class="badge">${escapeHtml(scalingUnit.type)}</span>` : ''}
                    ${productCount ? `<span class="badge ps-badge">${productCount} PS</span>` : ''}
                    ${paasCount ? `<span class="badge paas-badge">${paasCount} PaaS</span>` : ''}
                    ${reusableCount ? `<span class="badge">${reusableCount} deployable</span>` : ''}
                    ${applianceCount ? applianceBadge() : ''}
                    ${saasCount ? saasBadge() : ''}
                  </div>
                  ${externalInteractions.length ? `<div class="interaction-notes"><strong>External:</strong> ${escapeHtml(externalInteractions.map(item => item.name).join(', '))}</div>` : ''}
                  ${internalInteractions.length ? `<div class="interaction-notes"><strong>Internal:</strong> ${escapeHtml(internalInteractions.map(item => `${item.name} → ${item.ref || 'unknown'}`).join(', '))}</div>` : ''}
                </article>
              `;
            }).join('')}
          </div>
        </section>
      `;
    }

    function productServiceDetailMarkup(object) {
      const runsOnObject = object.runsOn ? objectLookup[object.runsOn] : null;
      return `
        <section class="section-card">
          <h3>Product Service Classification</h3>
          <div class="section-stack">
            <div class="badges">
              ${productBadge(object.product)}
              ${lifecycleBadge(object.lifecycleStatus)}
              ${catalogBadge(object.catalogStatus)}
            </div>
            <dl class="definition-list">
              <dt>UID</dt><dd><span class="object-id">${escapeHtml(object.id)}</span></dd>
              <dt>Product</dt><dd>${escapeHtml(object.product || '')}</dd>
              <dt>Runs On</dt><dd>${runsOnObject ? `<span class="ard-link" data-object-link="${object.runsOn}">${escapeHtml(runsOnObject.name)}</span>` : escapeHtml(object.runsOn || '')}</dd>
              <dt>Underlying Deployable Object</dt><dd>${escapeHtml(object.runsOn || 'Not documented')}</dd>
            </dl>
            <div class="header-description">${escapeHtml(object.description || 'No description provided.')}</div>
          </div>
        </section>
      `;
    }

    function preferredInteractionSource(object, fallbackObject) {
      const ownInteractions = object?.externalInteractions || [];
      if (ownInteractions.length) {
        return object;
      }
      return fallbackObject;
    }

    function preferredDecisionSource(object, fallbackObject) {
      const ownDecisions = object?.architecturalDecisions || {};
      if (Object.keys(ownDecisions).length) {
        return object;
      }
      return fallbackObject;
    }

    function abbDetailMarkup(object) {
      return `
        <section class="section-card">
          <h3>Technology Component</h3>
          <div class="section-stack">
            <div class="badges">
              ${object.lifecycleStatus ? lifecycleBadge(object.lifecycleStatus) : ''}
              ${catalogBadge(object.catalogStatus)}
            </div>
            <dl class="definition-list">
              <dt>Vendor</dt><dd>${escapeHtml(object.vendor || '')}</dd>
              <dt>Product Name</dt><dd>${escapeHtml(object.productName || '')}</dd>
              <dt>Product Version</dt><dd>${escapeHtml(object.productVersion || '')}</dd>
              <dt>Classification</dt><dd>${escapeHtml(abbClassificationLabel(object.classification))}</dd>
              ${object.capabilities?.length ? `<dt>Capabilities</dt><dd>${escapeHtml(object.capabilities.map(abbClassificationLabel).join(', '))}</dd>` : ''}
              ${object.platformDependency ? `<dt>Platform Dependency</dt><dd>${escapeHtml(object.platformDependency)}</dd>` : ''}
              ${object.networkPlacement ? `<dt>Network Placement</dt><dd>${escapeHtml(object.networkPlacement || '')}</dd>` : ''}
              ${object.patchingOwner ? `<dt>Patching Owner</dt><dd>${escapeHtml(object.patchingOwner || '')}</dd>` : ''}
              <dt>Compliance Certs</dt><dd>${escapeHtml((object.complianceCerts || []).join(', ') || 'None documented')}</dd>
            </dl>
            ${object.configurations?.length ? `
              <div class="interaction-notes"><strong>Configurations:</strong></div>
              <div class="section-stack">
              ${object.configurations.map(configuration => `
                  <article class="odc-card">
                    <div class="odc-name">${escapeHtml(configuration.name || configuration.id || 'Configuration')}</div>
                    <div class="interaction-notes">${escapeHtml(configuration.description || '')}</div>
                    <div class="object-id">${escapeHtml((configuration.capabilities || []).map(abbClassificationLabel).join(', '))}</div>
                  </article>
                `).join('')}
              </div>
            ` : ''}
          </div>
        </section>
      `;
    }

    function deploymentConfigurationsMarkup(object) {
      const configurations = object.deploymentConfigurations || [];
      if (!configurations.length) {
        return '';
      }
      return `
        <section class="section-card">
          <h3>Deployment Configurations</h3>
          <div class="section-stack">
            ${configurations.map(configuration => `
              <article class="odc-card">
                <div class="odc-name">${escapeHtml(configuration.name || configuration.id || 'Deployment Configuration')}</div>
                <div class="interaction-notes">${escapeHtml(configuration.description || '')}</div>
                ${configuration.addressesQualities?.length ? `<div class="object-id">${escapeHtml(configuration.addressesQualities.join(', '))}</div>` : ''}
              </article>
            `).join('')}
          </div>
        </section>
      `;
    }

    function deliveryModelDetailMarkup(object) {
      if (!SERVICE_OBJECT_TYPES.includes(object.type)) {
        return '';
      }
      if (object.deliveryModel === 'saas') {
      return `
        <section class="section-card">
          <h3>SaaS Delivery</h3>
          <div class="section-stack">
            <div class="badges">
              ${saasBadge()}
              ${lifecycleBadge(object.lifecycleStatus)}
              ${catalogBadge(object.catalogStatus)}
              ${boolBadge(object.dataLeavesInfrastructure === true, 'Data Leaves Infrastructure', 'Data Stays In Boundary')}
            </div>
            <dl class="definition-list">
              <dt>Vendor</dt><dd>${escapeHtml(object.vendor || '')}</dd>
              ${object.capabilities?.length ? `<dt>Capabilities</dt><dd>${escapeHtml(object.capabilities.join(', '))}</dd>` : ''}
              <dt>Data Residency</dt><dd>${escapeHtml(object.dataResidencyCommitment || 'Not documented')}</dd>
              <dt>DPA Notes</dt><dd>${escapeHtml(object.dpaNotes || 'Not documented')}</dd>
              <dt>Vendor SLA</dt><dd>${escapeHtml(object.vendorSLA || 'Not documented')}</dd>
              <dt>Authentication Model</dt><dd>${escapeHtml(object.authenticationModel || 'Not documented')}</dd>
              <dt>Compliance Certs</dt><dd>${escapeHtml((object.complianceCerts || []).join(', ') || 'None documented')}</dd>
            </dl>
            ${object.incidentNotificationProcess ? `<div class="interaction-notes"><strong>Incident Notification:</strong> ${escapeHtml(object.incidentNotificationProcess)}</div>` : ''}
          </div>
        </section>
        ${requirementGroupByName('SaaS Delivery Requirement Group') ? odcRequirementsMarkup(requirementGroupByName('SaaS Delivery Requirement Group')) : ''}
      `;
    }
      if (object.deliveryModel === 'paas') {
      return `
        <section class="section-card">
          <h3>PaaS Delivery</h3>
          <div class="section-stack">
            <div class="badges">
              ${paasBadge()}
              ${lifecycleBadge(object.lifecycleStatus)}
              ${catalogBadge(object.catalogStatus)}
            </div>
            <dl class="definition-list">
              <dt>Vendor</dt><dd>${escapeHtml(object.vendor || '')}</dd>
              ${object.capabilities?.length ? `<dt>Capabilities</dt><dd>${escapeHtml(object.capabilities.join(', '))}</dd>` : ''}
              <dt>Authentication Model</dt><dd>${escapeHtml(object.authenticationModel || 'Not documented')}</dd>
              <dt>Vendor SLA</dt><dd>${escapeHtml(object.vendorSLA || 'Not documented')}</dd>
              <dt>Compliance Certs</dt><dd>${escapeHtml((object.complianceCerts || []).join(', ') || 'None documented')}</dd>
            </dl>
          </div>
        </section>
        ${requirementGroupByName('PaaS Delivery Requirement Group') ? odcRequirementsMarkup(requirementGroupByName('PaaS Delivery Requirement Group')) : ''}
      `;
      }
      if (object.deliveryModel === 'appliance') {
        return `
          <section class="section-card">
            <h3>Appliance Delivery</h3>
            <div class="section-stack">
              <div class="badges">
                ${applianceBadge()}
                ${lifecycleBadge(object.lifecycleStatus)}
                ${catalogBadge(object.catalogStatus)}
              </div>
              <dl class="definition-list">
                <dt>Vendor</dt><dd>${escapeHtml(object.vendor || '')}</dd>
                ${object.capabilities?.length ? `<dt>Capabilities</dt><dd>${escapeHtml(object.capabilities.join(', '))}</dd>` : ''}
                <dt>Network Placement</dt><dd>${escapeHtml(object.networkPlacement || 'Not documented')}</dd>
                <dt>Patching Owner</dt><dd>${escapeHtml(object.patchingOwner || 'Not documented')}</dd>
                <dt>Compliance Certs</dt><dd>${escapeHtml((object.complianceCerts || []).join(', ') || 'None documented')}</dd>
              </dl>
            </div>
          </section>
          ${requirementGroupByName('Appliance Delivery Requirement Group') ? odcRequirementsMarkup(requirementGroupByName('Appliance Delivery Requirement Group')) : ''}
        `;
      }
      return '';
    }

    function domainDetailMarkup(object) {
      const domainCaps = object.capabilities || [];
      return `
        <section class="section-card">
          <h3>Capability Map: ${escapeHtml(object.name)}</h3>
          <div class="section-stack">
            ${domainCaps.map(cap => {
              const capId = String(cap);
              const capability = objectLookup[capId] || {};
              return `
                <article class="odc-card">
                  <div class="odc-name">${capability.id ? `<span class="ard-link" data-object-link="${capability.id}">${escapeHtml(capability.name || capId)}</span>` : escapeHtml(capId)}</div>
                  <div class="header-description">${escapeHtml(capability.description || '')}</div>
                  <div class="interaction-notes"><strong>Lifecycle implementations:</strong></div>
                  <div class="related-list">
                    ${(capability.implementations || []).length ? capability.implementations.map(implementation => {
                      const implObject = objectLookup[implementation.ref] || {};
                      return `
                      <a href="#${escapeHtml(implementation.ref)}" class="related-link">
                        <span class="related-icon">${topologyNodeIcon({ref: implementation.ref}, 'host').icon}</span>
                        ${escapeHtml(implObject.name || implementation.ref)}
                        <span class="badge">${escapeHtml(implementation.lifecycleStatus || '')}</span>
                      </a>
                    `}).join('') : '<div class="empty-card">No workspace implementations are mapped for this capability.</div>'}
                  </div>
                </article>
              `;
            }).join('')}
          </div>
        </section>
      `;
    }

    function capabilityDetailMarkup(object) {
      return `
        <section class="section-card">
          <h3>Capability</h3>
          <div class="section-stack">
            <dl class="definition-list">
              <dt>Domain</dt><dd>${object.domain && objectLookup[object.domain] ? `<span class="ard-link" data-object-link="${object.domain}">${escapeHtml(objectLookup[object.domain].name)}</span>` : escapeHtml(object.domain || 'Not documented')}</dd>
              <dt>Definition owner</dt><dd>${escapeHtml(object.definitionOwner?.team || object.definitionOwner?.provider || 'Not documented')}</dd>
              <dt>Company owner</dt><dd>${escapeHtml(object.owner?.team || 'Not assigned')}</dd>
              <dt>Implementations</dt><dd>${escapeHtml(String((object.implementations || []).length))}</dd>
            </dl>
            <div class="related-list">
              ${(object.implementations || []).length ? object.implementations.map(implementation => {
                const implObject = objectLookup[implementation.ref] || {};
                return `
                  <a href="#${escapeHtml(implementation.ref)}" class="related-link">
                    <span class="related-icon">${topologyNodeIcon({ref: implementation.ref}, 'host').icon}</span>
                    ${escapeHtml(implObject.name || implementation.ref)}
                    <span class="badge">${escapeHtml(implementation.lifecycleStatus || '')}</span>
                  </a>
                `;
              }).join('') : '<div class="empty-card">No workspace implementations are mapped for this capability.</div>'}
            </div>
          </div>
        </section>
      `;
    }

    function instanceLabel(value) {
      return formatTitleCase(String(value || 'unnamed').replace(/\./g, ' ').replace(/_/g, ' '));
    }

    function shortRefLabel(ref) {
      const object = objectLookup[ref];
      if (!object) {
        return formatTitleCase((ref || '').split('.').slice(-1)[0] || 'service');
      }
      return object.name
        .replace(/\s+(Web Service|Application Service|Database Service|Service)$/i, '')
        .replace(/\s+Standard$/i, '');
    }

    const SOFTWARE_DEPLOYMENT_PATTERN_TIERS = ['presentation', 'application', 'data', 'utility'];
    const SOFTWARE_DEPLOYMENT_PATTERN_TIER_LABELS = {
      presentation: 'Presentation Services',
      application: 'Application Services',
      data: 'Data Services',
      utility: 'Utility Services'
    };

    function isContainerHostObject(object) {
      return !!object && object.type === 'host' && String(object.id || '').startsWith('host.container.');
    }

    function objectIconSvg(name) {
      const icons = {
        document: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24"><path d="M6 2.8h8.2L18 6.6v14.6H6z"></path><path d="M14 2.8v4h4"></path><path d="M9 10h6"></path><path d="M9 13.4h6"></path><path d="M9 16.8h4"></path></svg>',
        monitor: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24"><rect x="3.4" y="4.4" width="17.2" height="11.8" rx="1.8"></rect><path d="M9 20h6"></path><path d="M12 16.2V20"></path><path d="M6.8 7.8h10.4"></path></svg>',
        gear: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3.2"></circle><path d="M12 2.9v2.3"></path><path d="M12 18.8v2.3"></path><path d="M2.9 12h2.3"></path><path d="M18.8 12h2.3"></path><path d="M5.6 5.6l1.7 1.7"></path><path d="M16.7 16.7l1.7 1.7"></path><path d="M18.4 5.6l-1.7 1.7"></path><path d="M7.3 16.7l-1.7 1.7"></path></svg>',
        database: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24"><ellipse cx="12" cy="5.6" rx="7" ry="3"></ellipse><path d="M5 5.6v12.8c0 1.7 3.1 3 7 3s7-1.3 7-3V5.6"></path><path d="M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3"></path></svg>',
        gateway: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24"><path d="M4 8h13"></path><path d="M13.5 4.5L17 8l-3.5 3.5"></path><path d="M20 16H7"></path><path d="M10.5 12.5L7 16l3.5 3.5"></path></svg>',
        cloud: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24"><path d="M7.6 18h9.4a4.2 4.2 0 0 0 .2-8.4 6.2 6.2 0 0 0-11.8 2A3.4 3.4 0 0 0 7.6 18z"></path></svg>',
        code: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24"><path d="M9.5 8.2L5.7 12l3.8 3.8"></path><path d="M14.5 8.2l3.8 3.8-3.8 3.8"></path><path d="M12.8 6.5l-1.6 11"></path></svg>',
        container: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24"><path d="M12 3.5l7.4 4.25v8.5L12 20.5l-7.4-4.25v-8.5z"></path><path d="M12 12l7.1-4.1"></path><path d="M12 12v8.2"></path><path d="M12 12L4.9 7.9"></path></svg>',
        wrench: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24"><path d="M14.7 5.3a4.6 4.6 0 0 0 4.4 6.1l-7.7 7.7a2.5 2.5 0 0 1-3.5-3.5l7.7-7.7a4.6 4.6 0 0 0-.9-2.6z"></path><path d="M7.3 17.9l-2 2"></path></svg>'
      };
      return icons[name] || icons.gear;
    }

    function objectIconStroke(cls) {
      if (cls === 'technology') return '#fdba74';
      if (cls === 'host' || cls === 'pod') return '#93c5fd';
      if (cls === 'runtime' || cls === 'product') return '#5eead4';
      if (cls === 'data') return '#d8b4fe';
      if (cls === 'gateway') return '#86efac';
      if (cls === 'cloud' || cls === 'appliance') return '#3a342c';
      return '#1f1a14';
    }

    function objectIconDataUri(svgMarkup, cls) {
      const stroke = objectIconStroke(cls);
      const source = svgMarkup.replace(
        '<svg ',
        `<svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="${stroke}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" `
      );
      return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(source)}`;
    }

    function topologyNodeIcon(entry, objectType = 'host') {
      const ref = entry.ref || '';
      const object = objectLookup[ref];
      const serviceObject = object?.type === 'product_service' && object?.runsOn ? objectLookup[object.runsOn] : object;
      if (objectType === 'appliance') {
        const caps = object?.capabilities || [];
        if (caps.some(c => ['file-storage', 'data-persistence', 'storage'].includes(c))) return { icon: objectIconSvg('database'), cls: 'data' };
        return { icon: objectIconSvg('wrench'), cls: 'appliance' };
      }
      if (object?.type === 'technology_component') return { icon: objectIconSvg('document'), cls: 'technology' };
      if (object?.type === 'host') return { icon: objectIconSvg('monitor'), cls: 'host' };
      if (object?.deliveryModel === 'saas') return { icon: objectIconSvg('cloud'), cls: 'cloud' };
      if (object?.deliveryModel === 'paas') return { icon: objectIconSvg('cloud'), cls: 'cloud' };
      if (object?.type === 'product_service' && isContainerHostObject(objectLookup[object?.runsOn])) {
        return { icon: objectIconSvg('container'), cls: 'pod' };
      }
      if (object?.type === 'product_service') return { icon: objectIconSvg('code'), cls: 'product' };
      if (object?.type === 'edge_gateway_service') return { icon: objectIconSvg('gateway'), cls: 'gateway' };
      if (serviceObject?.type === 'data_at_rest_service') return { icon: objectIconSvg('database'), cls: 'data' };
      if (serviceObject?.type === 'runtime_service') return { icon: objectIconSvg('gear'), cls: 'runtime' };
      return { icon: objectIconSvg('gear'), cls: 'runtime' };
    }

    function deploymentTargetPresentation(location) {
      const text = String(location || 'Unspecified');
      if (/AWS/i.test(text)) {
        return { cls: 'aws', badge: 'AWS', icon: objectIconSvg('cloud') };
      }
      if (/Datacenter|\\bDC\\b/i.test(text)) {
        return { cls: 'datacenter', badge: 'DC', icon: objectIconSvg('cloud') };
      }
      return { cls: 'generic', badge: 'Host', icon: objectIconSvg('monitor') };
    }

    function detailNodeVisual(object) {
      const icon = topologyNodeIcon({ref: object.id});
      return {
        image: objectIconDataUri(icon.icon, icon.cls),
        borderColor: object.color || '#e7e1d6'
      };
    }

    function colorForToken(value) {
      const palette = ['#7c3a6b', '#22c55e', '#f59e0b', '#a855f7', '#ef4444', '#14b8a6', '#e879f9', '#64748b'];
      const token = String(value || '');
      let hash = 0;
      for (let index = 0; index < token.length; index += 1) {
        hash = ((hash << 5) - hash) + token.charCodeAt(index);
        hash |= 0;
      }
      return palette[Math.abs(hash) % palette.length];
    }

    function entryDiagramTier(entry) {
      return SOFTWARE_DEPLOYMENT_PATTERN_TIERS.includes(entry?.diagramTier) ? entry.diagramTier : 'application';
    }

    function supportEntryTier(entry, objectType) {
      const object = objectLookup[entry?.ref];
      const capability = object?.capability || '';
      if (objectType === 'appliance') {
        if (capability === 'load-balancing') return 'presentation';
        if (['file-storage', 'data-persistence'].includes(capability)) return 'data';
        return 'utility';
      }
      if (object?.type === 'data_at_rest_service') return 'data';
      if (object?.type === 'edge_gateway_service') return 'presentation';
      return 'utility';
    }

    function entryLabel(entry) {
      if (entry?.instance) return instanceLabel(entry.instance);
      const object = objectLookup[entry?.ref];
      return object?.name || instanceLabel(entry?.ref);
    }

    function topologyBadgeMarkup(entry) {
      if (!entry) return '';
      const ard = entry.riskRef ? objectLookup[entry.riskRef] : null;
      if (entry.riskRef) {
        if (ard) {
          const isDecision = ard.ardCategory === 'decision' && ard.status === 'accepted';
          const cls = isDecision ? 'topology-info' : 'topology-risk';
          const symbol = isDecision ? 'ⓘ' : '⚠';
          return `<span class="${cls}" data-object-link="${ard.id}" title="${escapeHtml(ard.name)}">${symbol}</span>`;
        }
        return '<span class="topology-risk" title="Missing Decision Record reference">?</span>';
      }
      if (String(entry.intent || '').toLowerCase() === 'sa') {
        return '<span class="topology-info" title="Explicit architecture decision">ⓘ</span>';
      }
      return '';
    }

    function topologyNodeMarkup(entry, options = {}) {
      const {
        objectType = 'host',
        overrideLabel = null,
        meta = '',
        intent = entry.intent || '',
        badgeLabel = '',
        scalingUnit = '',
      } = options;
      const icon = topologyNodeIcon(entry, objectType);
      const targetId = entry.ref || '';
      const classes = ['topology-node'];
      if (objectType === 'product') classes.push('ps-node');
      if (objectType === 'host') classes.push('rbb-node');
      if (objectType === 'appliance') classes.push('appliance-node');
      if (objectType === 'paas') classes.push('cloud');
      if (objectType === 'saas') classes.push('saas-node');
      if (icon.cls) classes.push(icon.cls);
      return `
        <article class="${classes.join(' ')}" ${targetId && objectLookup[targetId] ? `data-object-link="${escapeHtml(targetId)}"` : ''} ${scalingUnit ? `data-scaling-unit="${escapeHtml(scalingUnit)}"` : ''}>
          ${topologyBadgeMarkup(entry)}
          <div class="topology-node-flags">
            ${badgeLabel ? `<span class="ps-corner">${escapeHtml(badgeLabel)}</span>` : '<span></span>'}
            ${intent ? intentBadge(intent) : '<span></span>'}
          </div>
          <span class="topology-node-icon ${icon.cls}">${icon.icon}</span>
          <div class="topology-node-label">${escapeHtml(overrideLabel || entryLabel(entry))}</div>
          ${meta ? `<div class="topology-node-meta">${escapeHtml(meta)}</div>` : ''}
        </article>
      `;
    }

    function serviceGroupSectionMarkup(group, tier) {
      const scalingUnit = group.scalingUnit || '';
      const accent = colorForToken(scalingUnit || group.name || tier);
      const groupMeta = [
        group.deploymentTarget || 'Unspecified deployment target',
        scalingUnit || 'No scaling unit'
      ].join(' • ');
      const topologyNodes = [];

      (group.deployableObjects || [])
        .filter(entry => entryDiagramTier(entry) === tier)
        .forEach(entry => {
          const target = objectLookup[entry.ref] || {};
          const deliveryModel = target.deliveryModel || '';
          const objectType = target.type === 'product_service'
            ? 'product'
            : (deliveryModel === 'paas' ? 'paas' : (deliveryModel === 'saas' ? 'saas' : (deliveryModel === 'appliance' ? 'appliance' : 'host')));
          const badgeLabel = target.type === 'product_service'
            ? 'PS'
            : (deliveryModel === 'paas' ? 'PaaS' : (deliveryModel === 'saas' ? 'SaaS' : (deliveryModel === 'appliance' ? 'APPL' : '')));
          topologyNodes.push(topologyNodeMarkup(entry, {
            objectType,
            badgeLabel,
            scalingUnit,
            meta: `${group.name} • ${groupMeta}`
          }));
        });

      if (!topologyNodes.length) {
        return '';
      }

      const internalInteractions = (group.externalInteractions || []).filter(item => (item.type || 'external') === 'internal');
      const externalInteractions = (group.externalInteractions || []).filter(item => (item.type || 'external') !== 'internal');

      return `
        <section class="service-group-section" style="--scaling-accent:${accent}" ${scalingUnit ? `data-scaling-unit-group="${escapeHtml(scalingUnit)}"` : ''}>
          <div class="service-group-section-header">
            <div class="service-group-section-title">${escapeHtml(group.name || 'Unnamed Service Group')}</div>
            <div class="service-group-section-meta">
              <span class="location-badge">${escapeHtml(tier)}</span>
              ${scalingUnit ? `<span class="scaling-unit-badge">${escapeHtml(scalingUnit)}</span>` : '<span class="scaling-unit-badge">unscoped</span>'}
            </div>
          </div>
          <div class="node-grid">
            ${topologyNodes.join('')}
          </div>
          ${(internalInteractions.length || externalInteractions.length) ? `
            <div class="service-group-support">
              ${internalInteractions.map(interaction => `<div class="topology-internal-link">${escapeHtml(interaction.name || 'Internal interaction')} → ${escapeHtml(interaction.ref || 'unknown')}</div>`).join('')}
              ${externalInteractions.map(interaction => `<div class="topology-internal-link">${escapeHtml(interaction.name || 'External interaction')} • ${escapeHtml(interaction.capability || 'other')}</div>`).join('')}
            </div>
          ` : ''}
        </section>
      `;
    }

    function tierColumnsMarkup(groups) {
      const columns = Object.fromEntries(SOFTWARE_DEPLOYMENT_PATTERN_TIERS.map(tier => [tier, []]));
      groups.forEach(group => {
        SOFTWARE_DEPLOYMENT_PATTERN_TIERS.forEach(tier => {
          const markup = serviceGroupSectionMarkup(group, tier);
          if (markup) {
            columns[tier].push(markup);
          }
        });
      });
      return `
        <div class="deployment-target-columns">
          ${SOFTWARE_DEPLOYMENT_PATTERN_TIERS.map(tier => `
            <section class="topology-tier-column">
              <div class="topology-tier-header ${escapeHtml(tier)}">${escapeHtml(SOFTWARE_DEPLOYMENT_PATTERN_TIER_LABELS[tier])}</div>
              <div class="topology-column-stack">
                ${columns[tier].join('') || `<div class="empty-card">No ${escapeHtml(tier)} services.</div>`}
              </div>
            </section>
          `).join('')}
        </div>
      `;
    }

    function renderDeploymentTopology(object) {
      const serviceGroups = object.serviceGroups || [];

      if (!serviceGroups.length) {
        return `
          <div class="topology-layout">
            <div class="empty-card">No topology data is available for this object.</div>
          </div>
        `;
      }

      const scalingUnits = [...new Set(serviceGroups.map(group => group.scalingUnit).filter(Boolean))];
      const topologyToolbar = object.type === 'software_deployment_pattern' ? `
        <div class="topology-toolbar">
          <div class="topology-filter-buttons">
            <button class="topology-filter-button ${currentSdmScalingFilter === 'all' ? 'active' : ''}" data-scaling-filter="all">All scaling units</button>
            ${scalingUnits.map(unit => `<button class="topology-filter-button ${currentSdmScalingFilter === unit ? 'active' : ''}" data-scaling-filter="${escapeHtml(unit)}">${escapeHtml(unit)}</button>`).join('')}
          </div>
          <div class="topology-filter-help">Select a scaling unit to highlight participating services.</div>
        </div>
      ` : '';

      return `
        <div class="topology-layout">
          ${topologyToolbar}
          <div class="topology-scaling-units">
            ${tierColumnsMarkup(serviceGroups)}
          </div>
        </div>
      `;
    }

    function ardDetailMarkup(object) {
      return `
        <section class="ard-detail-card">
          <h2 class="ard-detail-title">${escapeHtml(object.name)}</h2>
          <div class="ard-meta">
            <span>${escapeHtml(object.id)}</span>
            ${ardCategoryBadge(object.ardCategory)}
            ${ardStatusBadge(object.status)}
            ${object.linkedSoftwareDeployment && objectLookup[object.linkedSoftwareDeployment] ? `<span>Linked Software Deployment Pattern: <span class="ard-link" data-object-link="${object.linkedSoftwareDeployment}">${escapeHtml(object.linkedSoftwareDeployment)}</span></span>` : object.linkedSoftwareDeployment ? `<span>Linked Software Deployment Pattern: ${escapeHtml(object.linkedSoftwareDeployment)}</span>` : ''}
          </div>
          <section class="ard-section">
            <h3>Description</h3>
            <p>${escapeHtml(object.description || '')}</p>
          </section>
          <section class="ard-section">
            <h3>Affected Component</h3>
            <div>${escapeHtml(object.affectedComponent || '')}</div>
          </section>
          <section class="ard-section">
            <h3>Impact</h3>
            <p>${escapeHtml(object.impact || '')}</p>
          </section>
          ${object.mitigationPath ? `
            <section class="ard-section">
              <h3>Mitigation Path</h3>
              <p>${escapeHtml(object.mitigationPath)}</p>
            </section>
          ` : ''}
          ${object.decisionRationale ? `
            <section class="ard-section">
              <h3>Decision Rationale</h3>
              <p>${escapeHtml(object.decisionRationale)}</p>
            </section>
          ` : ''}
          ${(object.relatedDecisionRecords || []).length ? `
            <section class="ard-section">
              <h3>Related Decision Records</h3>
              <div class="section-stack">
                ${object.relatedDecisionRecords.map(ardId => objectLookup[ardId]
                  ? `<span class="ard-link" data-object-link="${ardId}">${escapeHtml(ardId)}</span>`
                  : `<span>${escapeHtml(ardId)}</span>`
                ).join('')}
              </div>
            </section>
          ` : ''}
        </section>
      `;
    }

    function draftingSessionDetailMarkup(object) {
      const generatedObjects = object.generatedObjects || [];
      const unresolvedQuestions = object.unresolvedQuestions || [];
      const assumptions = object.assumptions || [];
      const nextSteps = object.nextSteps || [];
      const sourceArtifacts = object.sourceArtifacts || [];
      const primaryObject = object.primaryObjectUid && objectLookup[object.primaryObjectUid] ? objectLookup[object.primaryObjectUid] : null;

      return `
        <section class="section-card">
          <h3>Session Scope</h3>
          <dl class="definition-list">
            <dt>Session Status</dt>
            <dd>${escapeHtml(object.sessionStatus || 'unknown')}</dd>
            <dt>Primary Object Type</dt>
            <dd>${escapeHtml(object.primaryObjectType || 'unknown')}</dd>
            <dt>Primary Object</dt>
            <dd>${primaryObject ? `<span class="ard-link" data-object-link="${primaryObject.id}">${escapeHtml(primaryObject.name)}</span>` : escapeHtml(object.primaryObjectUid || 'Not created yet')}</dd>
          </dl>
        </section>
        <section class="section-card">
          <h3>Source Artifacts</h3>
          <div class="section-stack">
            ${sourceArtifacts.length ? sourceArtifacts.map(source => `
              <article class="odc-card">
                <div class="odc-name">${escapeHtml(source.name || 'Unnamed source')}</div>
                <div class="interaction-notes">${escapeHtml(source.type || 'source')}</div>
                ${source.location ? `<div class="object-id">${escapeHtml(source.location)}</div>` : ''}
                ${source.notes ? `<div class="interaction-notes">${escapeHtml(source.notes)}</div>` : ''}
              </article>
            `).join('') : '<div class="empty-card">No source artifacts are recorded for this session.</div>'}
          </div>
        </section>
        <section class="section-card">
          <h3>Generated Objects</h3>
          <div class="section-stack">
            ${generatedObjects.length ? generatedObjects.map(entry => `
              <article class="odc-card">
                <div class="odc-name">${escapeHtml(entry.name || 'Generated object')}</div>
                <div class="interaction-notes">${escapeHtml(entry.type || 'unknown')} / ${escapeHtml(entry.status || 'unknown')}</div>
                ${entry.ref && objectLookup[entry.ref] ? `<div class="object-id"><span class="ard-link" data-object-link="${entry.ref}">${escapeHtml(objectLookup[entry.ref].name)}</span></div>` : entry.ref ? `<div class="object-id">${escapeHtml(entry.ref)}</div>` : entry.proposedUid ? `<div class="object-id">${escapeHtml(entry.proposedUid)}</div>` : ''}
                ${entry.notes ? `<div class="interaction-notes">${escapeHtml(entry.notes)}</div>` : ''}
              </article>
            `).join('') : '<div class="empty-card">No generated objects are recorded for this session.</div>'}
          </div>
        </section>
        <section class="section-card">
          <h3>Unresolved Questions</h3>
          <div class="section-stack">
            ${unresolvedQuestions.length ? unresolvedQuestions.map(item => `
              <article class="decision-card">
                <h4>${escapeHtml(item.id || 'question')}</h4>
                <p>${escapeHtml(item.question || '')}</p>
                <dl class="definition-list">
                  <dt>Status</dt>
                  <dd>${escapeHtml(item.status || 'open')}</dd>
                  ${item.reason ? `<dt>Reason</dt><dd>${escapeHtml(item.reason)}</dd>` : ''}
                  ${item.currentBestGuess ? `<dt>Current Best Guess</dt><dd>${escapeHtml(item.currentBestGuess)}</dd>` : ''}
                  ${item.impact ? `<dt>Impact</dt><dd>${escapeHtml(item.impact)}</dd>` : ''}
                </dl>
                ${(item.relatedObjects || []).length ? `<div class="section-stack">${item.relatedObjects.map(refEntry => refEntry.ref && objectLookup[refEntry.ref] ? `<span class="ard-link" data-object-link="${refEntry.ref}">${escapeHtml(refEntry.ref)}</span>` : refEntry.ref ? `<span>${escapeHtml(refEntry.ref)}</span>` : '').join('')}</div>` : ''}
              </article>
            `).join('') : '<div class="empty-card">No unresolved questions are recorded for this session.</div>'}
          </div>
        </section>
        <section class="middle-grid">
          <div class="section-card">
            <h3>Assumptions</h3>
            <div class="section-stack">
              ${assumptions.length ? assumptions.map(item => `
                <article class="decision-card">
                  <h4>${escapeHtml(item.id || 'assumption')}</h4>
                  <p>${escapeHtml(item.statement || '')}</p>
                  ${item.rationale ? `<div class="interaction-notes">${escapeHtml(item.rationale)}</div>` : ''}
                  ${item.impact ? `<div class="interaction-notes">${escapeHtml(item.impact)}</div>` : ''}
                </article>
              `).join('') : '<div class="empty-card">No assumptions are recorded for this session.</div>'}
            </div>
          </div>
          <div class="section-card">
            <h3>Next Steps</h3>
            <div class="section-stack">
              ${nextSteps.length ? nextSteps.map(item => `
                <article class="decision-card">
                  <h4>${escapeHtml(item.id || 'next-step')}</h4>
                  <p>${escapeHtml(item.action || '')}</p>
                  <dl class="definition-list">
                    <dt>Status</dt>
                    <dd>${escapeHtml(item.status || 'open')}</dd>
                    ${item.owner ? `<dt>Owner</dt><dd>${escapeHtml(item.owner)}</dd>` : ''}
                    ${item.notes ? `<dt>Notes</dt><dd>${escapeHtml(item.notes)}</dd>` : ''}
                  </dl>
                </article>
              `).join('') : '<div class="empty-card">No next steps are recorded for this session.</div>'}
            </div>
          </div>
        </section>
      `;
    }

    function usedByMarkup(object) {
      const inbound = object.referencedBy || [];
      if (!inbound.length) {
        return '';
      }
      return `
        <section class="section-card">
          <h3>Used By</h3>
          <div class="section-stack">
            ${inbound.map(reference => {
              const source = objectLookup[reference.source];
              return `
                <article class="odc-card">
                  <div class="odc-name">
                    ${source ? `<span class="ard-link" data-object-link="${source.id}">${escapeHtml(source.name)}</span>` : escapeHtml(reference.source)}
                  </div>
                  <div class="object-id">${escapeHtml(reference.source)}</div>
                  <div class="interaction-notes">${escapeHtml(reference.path || '')}</div>
                </article>
              `;
            }).join('')}
          </div>
        </section>
      `;
    }

    function detailDisclosureMarkup(title, bodyMarkup) {
      const content = String(bodyMarkup || '').trim();
      if (!content) {
        return '';
      }
      return `
        <details class="detail-disclosure">
          <summary>${escapeHtml(title)}</summary>
          <div class="detail-disclosure-content">
            ${content}
          </div>
        </details>
      `;
    }

    function secondaryDetailMarkup(sections) {
      const content = sections
        .map(section => detailDisclosureMarkup(section.title, section.body))
        .filter(Boolean)
        .join('');
      if (!content) {
        return '';
      }
      return `<section class="detail-disclosures">${content}</section>`;
    }

    function referencesMarkup(object) {
      return secondaryDetailMarkup([
        { title: 'References', body: usedByMarkup(object) }
      ]);
    }

    function architectureDetailMarkup(interactionSource, decisionSource, emptyInteractionText, emptyDecisionText) {
      return `
        <section class="middle-grid">
          <div class="section-card">
            <h3>Internal Components</h3>
            <div id="detail-cy"></div>
          </div>
          <div class="section-card">
            <h3>External Interactions</h3>
            ${interactionSource ? interactionMarkup(interactionSource) : `<div class="empty-card">${escapeHtml(emptyInteractionText || 'No external interactions are documented for this object.')}</div>`}
          </div>
        </section>
        <section class="decisions-card">
          <h3>Architecture Decisions</h3>
          ${decisionSource ? decisionMarkup(decisionSource) : `<div class="empty-card">${escapeHtml(emptyDecisionText || 'No architectural decisions are documented for this object.')}</div>`}
        </section>
      `;
    }

    function genericObjectMarkup(object) {
      const detail = JSON.parse(object.detail || '{}');
      const rows = Object.entries(detail)
        .filter(([key]) => !key.startsWith('_'))
        .map(([key, value]) => {
          const rendered = typeof value === 'object' ? JSON.stringify(value) : String(value);
          return `<dt>${escapeHtml(key)}</dt><dd>${escapeHtml(rendered)}</dd>`;
        })
        .join('');
      return `
        <section class="section-card">
          <h3>Object Data</h3>
          <dl class="definition-list">
            ${rows}
          </dl>
        </section>
      `;
    }

    function attachObjectLinkHandlers(root = document) {
      root.querySelectorAll('[data-object-link]').forEach(link => {
        link.addEventListener('click', event => {
          event.stopPropagation();
          showDetailView(link.dataset.objectLink);
        });
      });
    }

    function sanitizeDetailObject(object) {
      const raw = JSON.parse(object.detail || '{}');
      const cleaned = {};
      Object.entries(raw).forEach(([key, value]) => {
        if (!key.startsWith('_')) {
          cleaned[key] = value;
        }
      });
      return cleaned;
    }

    function repoSourceUrl(object) {
      return repoUrl && object.source ? `${repoUrl}/blob/main/${object.source}` : '';
    }

    function orderedEditorFields(object) {
      const schema = object.editorSchema || {};
      const required = schema.requiredFields || [];
      const optional = schema.optionalFields || [];
      const priority = ['schemaVersion', 'uid', 'type', 'name', 'aliases', 'description', 'version', 'catalogStatus', 'lifecycleStatus', 'definitionOwner', 'owner', 'tags'];
      const ordered = [];
      const seen = new Set();
      [...priority, ...required, ...optional, ...Object.keys(sanitizeDetailObject(object))].forEach(field => {
        if (!field || field.startsWith('_') || seen.has(field)) return;
        seen.add(field);
        ordered.push(field);
      });
      return ordered;
    }

    function yamlFieldValue(value) {
      if (value === undefined || value === null) return '';
      if (typeof value === 'string') return value;
      return jsyaml.dump(value, { lineWidth: 100 }).trim();
    }

    function fieldInputMarkup(object, field, value) {
      const schema = object.editorSchema || {};
      const required = new Set(schema.requiredFields || []);
      const fieldTypes = schema.fieldTypes || {};
      const enumFields = schema.enumFields || {};
      const enumListFields = schema.enumListFields || {};
      const expectedType = fieldTypes[field] || '';
      const label = formatKeyLabel(field);
      const requiredText = required.has(field) ? '<span class="editor-required">*</span>' : '';

      if (expectedType === 'bool' || typeof value === 'boolean') {
        return `
          <div class="editor-field">
            <label>${escapeHtml(label)}${requiredText}</label>
            <label class="editor-checkbox">
              <input type="checkbox" data-editor-field="${escapeHtml(field)}" ${value ? 'checked' : ''}>
              <span>${escapeHtml(label)}</span>
            </label>
          </div>
        `;
      }

      if (enumFields[field]) {
        const options = ['<option value=""></option>']
          .concat(enumFields[field].map(option => `<option value="${escapeHtml(option)}" ${value === option ? 'selected' : ''}>${escapeHtml(option)}</option>`));
        return `
          <div class="editor-field">
            <label for="editor-${escapeHtml(field)}">${escapeHtml(label)}${requiredText}</label>
            <select id="editor-${escapeHtml(field)}" data-editor-field="${escapeHtml(field)}">
              ${options.join('')}
            </select>
          </div>
        `;
      }

      if (expectedType === 'dict' || expectedType === 'list' || enumListFields[field] || Array.isArray(value) || (value && typeof value === 'object')) {
        return `
          <div class="editor-field">
            <label for="editor-${escapeHtml(field)}">${escapeHtml(label)}${requiredText}</label>
            <textarea id="editor-${escapeHtml(field)}" data-editor-field="${escapeHtml(field)}" data-editor-complex="true">${escapeHtml(yamlFieldValue(value))}</textarea>
            <div class="editor-help">Edit structured values carefully.</div>
          </div>
        `;
      }

      const stringValue = value === undefined || value === null ? '' : String(value);
      const multiline = stringValue.length > 120 || stringValue.includes('\\\\n') || field === 'description' || field === 'notes';
      return multiline ? `
        <div class="editor-field">
          <label for="editor-${escapeHtml(field)}">${escapeHtml(label)}${requiredText}</label>
          <textarea id="editor-${escapeHtml(field)}" data-editor-field="${escapeHtml(field)}">${escapeHtml(stringValue)}</textarea>
        </div>
      ` : `
        <div class="editor-field">
          <label for="editor-${escapeHtml(field)}">${escapeHtml(label)}${requiredText}</label>
          <input id="editor-${escapeHtml(field)}" type="text" value="${escapeHtml(stringValue)}" data-editor-field="${escapeHtml(field)}">
        </div>
      `;
    }

    function serializeEditorObject(object, fieldValues) {
      const schema = object.editorSchema || {};
      const fieldTypes = schema.fieldTypes || {};
      const enumListFields = schema.enumListFields || {};
      const result = {};
      orderedEditorFields(object).forEach(field => {
        let value = fieldValues[field];
        const expectedType = fieldTypes[field] || '';
        if (value === undefined) return;
        if (typeof value === 'string') {
          if (expectedType === 'dict' || expectedType === 'list' || enumListFields[field]) {
            const trimmed = value.trim();
            if (!trimmed) return;
            result[field] = jsyaml.load(trimmed);
            return;
          }
          const trimmed = value.trim();
          if (!trimmed && field !== 'description') return;
          result[field] = value;
          return;
        }
        if (value === null) return;
        result[field] = value;
      });
      return result;
    }

    function updateEditorPreview(object) {
      const errorNode = editorOverlay.querySelector('#editor-error');
      const previewNode = editorOverlay.querySelector('#editor-structured-preview');
      if (!editorState || !errorNode || !previewNode) return;
      try {
        const serialized = serializeEditorObject(object, editorState.fieldValues);
        editorState.serialized = serialized;
        previewNode.textContent = jsyaml.dump(serialized, { lineWidth: 100, noRefs: true });
        errorNode.textContent = '';
      } catch (error) {
        editorState.serialized = null;
        previewNode.textContent = '';
        errorNode.textContent = error instanceof Error ? error.message : String(error);
      }
    }

    function blankApplicabilityClause() {
      return { field: '', operator: 'equals', value: '', valuesText: '', truthy: 'true' };
    }

    function normalizeApplicabilityClause(clause) {
      if (!clause || typeof clause !== 'object') {
        return blankApplicabilityClause();
      }
      if (Object.prototype.hasOwnProperty.call(clause, 'truthy')) {
        return {
          field: String(clause.field || ''),
          operator: 'truthy',
          value: '',
          valuesText: '',
          truthy: clause.truthy === false ? 'false' : 'true'
        };
      }
      if (Array.isArray(clause.in)) {
        return {
          field: String(clause.field || ''),
          operator: 'in',
          value: '',
          valuesText: clause.in.map(value => String(value)).join(', '),
          truthy: 'true'
        };
      }
      if (Object.prototype.hasOwnProperty.call(clause, 'contains')) {
        return {
          field: String(clause.field || ''),
          operator: 'contains',
          value: String(clause.contains || ''),
          valuesText: '',
          truthy: 'true'
        };
      }
      return {
        field: String(clause.field || ''),
        operator: 'equals',
        value: String(clause.equals || ''),
        valuesText: '',
        truthy: 'true'
      };
    }

    function showDetailView(id, pushHistory = true) {
      if (pushHistory && currentDetailId) {
        navHistory.push(currentDetailId);
      }
      currentDetailId = id;
      destroyImpactCy();
      renderDetailView();
    }

    function renderDetailView() {
      currentMode = 'detail';
      executiveDrilldown = null;
      const object = objectLookup[currentDetailId];
      if (!object) {
        renderListView();
        return;
      }
      syncHashForDetailView(object.id);
      renderSidebarContent(sidebarMarkup());
      const softwareServiceRunsOn = object.type === 'product_service' && object.runsOn ? objectLookup[object.runsOn] : null;
      const detailDiagramSource = softwareServiceRunsOn && DEPLOYABLE_STANDARD_TYPES.includes(softwareServiceRunsOn.type) ? softwareServiceRunsOn : object;
      const headerMarkup = `
        <section class="header-card">
          <div class="header-top">
            <div class="header-title">
              <h2>${escapeHtml(object.name)}</h2>
              <div class="object-id">${escapeHtml(object.id)}</div>
            </div>
            <div class="badges">
              <span class="badge">${escapeHtml(object.typeLabel)}</span>
              ${object.lifecycleStatus ? lifecycleBadge(object.lifecycleStatus) : ''}
              ${catalogBadge(object.catalogStatus)}
            </div>
          </div>
          <div class="header-description">${escapeHtml(object.description || 'No description provided.')}</div>
          ${object.type === 'capability' ? `
            <div class="owner-line">
              <span><strong>Definition owner:</strong> ${escapeHtml(object.definitionOwner?.team || object.definitionOwner?.provider || 'Unknown')}</span>
              <span><strong>Company owner:</strong> ${escapeHtml(object.owner?.team || 'Not assigned')}</span>
            </div>
          ` : `
            <div class="owner-line">
              <span><strong>Owner:</strong> ${escapeHtml(object.owner?.team || 'Unknown')}</span>
              <span><strong>Contact:</strong> ${escapeHtml(object.owner?.contact || 'Unknown')}</span>
            </div>
          `}
        </section>
      `;

      let detailBody = '';
      if (object.type === 'requirement_group') {
        detailBody = `
          ${headerMarkup}
          ${odcRequirementsMarkup(object)}
          ${referencesMarkup(object)}
        `;
      } else if (object.type === 'capability') {
        detailBody = `
          ${headerMarkup}
          ${capabilityDetailMarkup(object)}
          ${referencesMarkup(object)}
        `;
      } else if (object.type === 'domain') {
        detailBody = `
          ${headerMarkup}
          ${domainDetailMarkup(object)}
          ${referencesMarkup(object)}
        `;
      } else if (object.type === 'decision_record') {
        detailBody = `
          ${ardDetailMarkup(object)}
          ${referencesMarkup(object)}
        `;
      } else if (object.type === 'drafting_session') {
        detailBody = `
          ${headerMarkup}
          ${draftingSessionDetailMarkup(object)}
          ${referencesMarkup(object)}
        `;
      } else if (object.type === 'product_service') {
        const interactionSource = preferredInteractionSource(object, softwareServiceRunsOn);
        const decisionSource = preferredDecisionSource(object, softwareServiceRunsOn);
        detailBody = `
          ${headerMarkup}
          ${architectureDetailMarkup(
            interactionSource,
            decisionSource,
            'The underlying deployable object is not available for this Product Service.',
            'No architectural decisions are available because the underlying deployable object is not documented.'
          )}
          ${secondaryDetailMarkup([
            { title: 'Product Service Classification', body: productServiceDetailMarkup(object) },
            { title: 'Requirement Evidence', body: requirementEvidenceMarkup(object) },
            { title: 'References', body: usedByMarkup(object) }
          ])}
        `;
      } else if (object.type === 'software_deployment_pattern') {
        detailBody = `
          ${headerMarkup}
          <div class="detail-tabs">
            <button class="detail-tab active" data-sdm-tab="topology">Deployment Topology</button>
            <button class="detail-tab" data-sdm-tab="details">Governance & Source</button>
          </div>
          <div class="detail-panel" data-sdm-panel="topology">
            <section class="section-card">
              <h3>Deployment Topology</h3>
              <div id="topology-canvas"></div>
            </section>
          </div>
          <div class="detail-panel" data-sdm-panel="details" hidden>
            <section class="section-card">
              <h3>Applied Pattern</h3>
              <div class="section-stack">
                ${object.followsReferenceArchitecture && objectLookup[object.followsReferenceArchitecture]
                  ? `<span class="ard-link" data-object-link="${object.followsReferenceArchitecture}">${escapeHtml(object.followsReferenceArchitecture)}</span>`
                  : `<span class="interaction-notes">${escapeHtml(object.followsReferenceArchitecture || 'No applied reference architecture documented.')}</span>`}
              </div>
            </section>
            ${businessContextMarkup(object)}
            ${requirementEvidenceMarkup(object)}
            ${sdmServiceGroupsMarkup(object)}
            ${sdmRisksMarkup(object)}
            ${sourceRepositoryMarkup(object)}
            <section class="decisions-card">
              <h3>Architecture Decisions</h3>
              ${decisionMarkup(object, ['sourceRepositories'])}
            </section>
          </div>
          ${referencesMarkup(object)}
        `;
      } else if (object.type === 'reference_architecture') {
        detailBody = `
          ${headerMarkup}
          <div class="detail-tabs">
            <button class="detail-tab active" data-sdm-tab="topology">Deployment Pattern</button>
            <button class="detail-tab" data-sdm-tab="details">Governance & Decisions</button>
          </div>
          <div class="detail-panel" data-sdm-panel="details" hidden>
            ${requirementEvidenceMarkup(object)}
            ${sdmServiceGroupsMarkup(object)}
            <section class="decisions-card">
              <h3>Architecture Decisions</h3>
              ${decisionMarkup(object)}
            </section>
          </div>
          <div class="detail-panel" data-sdm-panel="topology">
            <section class="section-card">
              <h3>Deployment Pattern</h3>
              <div id="topology-canvas"></div>
            </section>
          </div>
          ${referencesMarkup(object)}
        `;
      } else if (object.type === 'technology_component') {
        detailBody = `
          ${headerMarkup}
          ${abbDetailMarkup(object)}
          ${referencesMarkup(object)}
        `;
      } else if (DEPLOYABLE_STANDARD_TYPES.includes(object.type)) {
        detailBody = `
          ${headerMarkup}
          ${architectureDetailMarkup(object, object)}
          ${secondaryDetailMarkup([
            { title: 'Delivery Details', body: deliveryModelDetailMarkup(object) },
            { title: 'Requirement Evidence', body: requirementEvidenceMarkup(object) },
            { title: 'Deployment Configurations', body: deploymentConfigurationsMarkup(object) },
            { title: 'References', body: usedByMarkup(object) }
          ])}
        `;
      } else {
        detailBody = `
          ${headerMarkup}
          ${genericObjectMarkup(object)}
          ${referencesMarkup(object)}
        `;
      }

      pageRoot.innerHTML = `
        <div class="detail-layout">
          ${topNavMarkup()}
          <button class="back-button" id="back-button">Back</button>
          ${detailBody}
        </div>
      `;

      document.getElementById('back-button').addEventListener('click', () => {
        destroyDetailCy();
        if (navHistory.length) {
          const previousId = navHistory.pop();
          showDetailView(previousId, false);
          return;
        }
        currentDetailId = null;
        renderListView();
      });
      const openEditorButton = document.getElementById('open-editor-button');
      if (openEditorButton) {
        openEditorButton.addEventListener('click', () => openEditor(object));
      }

      attachTopNavHandlers();
      attachSidebarHandlers();
      attachObjectLinkHandlers(pageRoot);
      if (object.type === 'software_deployment_pattern' || object.type === 'reference_architecture') {
        currentSdmScalingFilter = 'all';
        const applySdmScalingFilter = () => {
          const topologyCanvas = document.getElementById('topology-canvas');
          if (!topologyCanvas) return;
          const filter = currentSdmScalingFilter;
          topologyCanvas.querySelectorAll('.topology-filter-button').forEach(button => {
            button.classList.toggle('active', button.dataset.scalingFilter === filter);
          });
          topologyCanvas.querySelectorAll('.topology-node').forEach(node => {
            const participates = filter === 'all' || node.dataset.scalingUnit === filter;
            node.classList.toggle('dimmed', filter !== 'all' && !participates);
            node.classList.toggle('highlighted', filter !== 'all' && participates);
          });
          topologyCanvas.querySelectorAll('.service-group-section').forEach(section => {
            const participates = filter === 'all' || section.dataset.scalingUnitGroup === filter;
            section.classList.toggle('dimmed', filter !== 'all' && !participates);
            section.classList.toggle('highlighted', filter !== 'all' && participates);
          });
        };

        const renderTopologyIntoCanvas = () => {
          const topologyCanvas = document.getElementById('topology-canvas');
          if (topologyCanvas && !topologyCanvas.dataset.rendered) {
            topologyCanvas.innerHTML = renderDeploymentTopology(object);
            topologyCanvas.dataset.rendered = 'true';
            attachObjectLinkHandlers(topologyCanvas);
            topologyCanvas.querySelectorAll('[data-scaling-filter]').forEach(button => {
              button.addEventListener('click', () => {
                currentSdmScalingFilter = button.dataset.scalingFilter || 'all';
                applySdmScalingFilter();
              });
            });
            applySdmScalingFilter();
          }
        };

        pageRoot.querySelectorAll('[data-sdm-tab]').forEach(button => {
          button.addEventListener('click', () => {
            const nextTab = button.dataset.sdmTab;
            pageRoot.querySelectorAll('[data-sdm-tab]').forEach(tab => {
              tab.classList.toggle('active', tab.dataset.sdmTab === nextTab);
            });
            pageRoot.querySelectorAll('[data-sdm-panel]').forEach(panel => {
              panel.hidden = panel.dataset.sdmPanel !== nextTab;
            });
            if (nextTab === 'topology') {
              renderTopologyIntoCanvas();
            }
          });
        });
        renderTopologyIntoCanvas();
      }
      if (DEPLOYABLE_STANDARD_TYPES.includes(object.type) && !['saas', 'paas', 'appliance'].includes(object.deliveryModel || '')) {
        renderInternalDiagram(detailDiagramSource);
      }
    }

    function destroyDetailCy() {
      if (detailCy) {
        detailCy.destroy();
        detailCy = null;
      }
    }

    function buildDetailElements(object) {
      const objectVisual = detailNodeVisual(object);
      const nodes = [
        {
          data: {
            id: object.id,
            label: object.name,
            color: '#ffffff',
            borderColor: objectVisual.borderColor,
            iconImage: objectVisual.image,
            lifecycleStatus: object.lifecycleStatus,
            nodeWidth: object.type === 'technology_component' || DEPLOYABLE_STANDARD_TYPES.includes(object.type) ? 172 : 160,
            nodeHeight: object.type === 'technology_component' || DEPLOYABLE_STANDARD_TYPES.includes(object.type) ? 132 : 122,
            textMaxWidth: object.type === 'technology_component' || DEPLOYABLE_STANDARD_TYPES.includes(object.type) ? 156 : 146
          },
          classes: object.name.length > 20 ? 'long-label' : ''
        }
      ];
      const edges = [];
      const seen = new Set([object.id]);

      (object.internalComponents || []).forEach((component, index) => {
        const refObject = objectLookup[component.ref];
        if (!refObject || seen.has(refObject.id)) {
          return;
        }
        seen.add(refObject.id);
        const refVisual = detailNodeVisual(refObject);
        nodes.push({
          data: {
            id: refObject.id,
            label: refObject.name,
            color: '#ffffff',
            borderColor: refVisual.borderColor,
            iconImage: refVisual.image,
            lifecycleStatus: refObject.lifecycleStatus,
            nodeWidth: refObject.type === 'technology_component' || DEPLOYABLE_STANDARD_TYPES.includes(refObject.type) ? 162 : 150,
            nodeHeight: refObject.type === 'technology_component' || DEPLOYABLE_STANDARD_TYPES.includes(refObject.type) ? 124 : 114,
            textMaxWidth: refObject.type === 'technology_component' || DEPLOYABLE_STANDARD_TYPES.includes(refObject.type) ? 148 : 138
          },
          classes: refObject.name.length > 20 ? 'long-label' : ''
        });
        edges.push({
          data: {
            id: `${object.id}-${refObject.id}-${index}`,
            source: object.id,
            target: refObject.id,
            label: component.role || 'component'
          }
        });
      });

      return [...nodes, ...edges];
    }

    function renderInternalDiagram(object) {
      destroyDetailCy();
      detailCy = cytoscape({
        container: document.getElementById('detail-cy'),
        elements: buildDetailElements(object),
        userZoomingEnabled: false,
        userPanningEnabled: false,
        boxSelectionEnabled: false,
        autoungrabify: true,
        layout: {
          name: 'breadthfirst',
          directed: true,
          padding: 30,
          spacingFactor: 1.5,
          roots: [object.id]
        },
        style: [
          {
            selector: 'node',
            style: {
              'label': 'data(label)',
              'shape': 'round-rectangle',
              'background-color': 'data(color)',
              'background-image': 'data(iconImage)',
              'background-fit': 'none',
              'background-width': 40,
              'background-height': 40,
              'background-position-x': '50%',
              'background-position-y': '28%',
              'border-width': 1,
              'border-color': 'data(borderColor)',
              'color': '#1f1a14',
              'font-size': 11,
              'font-weight': 600,
              'text-wrap': 'wrap',
              'text-max-width': 'data(textMaxWidth)',
              'text-valign': 'center',
              'text-halign': 'center',
              'text-margin-y': 36,
              'text-outline-width': 2,
              'text-outline-color': '#fbf8f3',
              'width': 'data(nodeWidth)',
              'height': 'data(nodeHeight)',
              'cursor': 'pointer'
            }
          },
          {
            selector: 'node.long-label',
            style: {
              'font-size': 10
            }
          },
          {
            selector: 'edge',
            style: {
              'curve-style': 'bezier',
              'width': 2,
              'line-color': '#a89784',
              'target-arrow-color': '#a89784',
              'target-arrow-shape': 'triangle'
            }
          }
        ]
      });
      detailCy.on('tap', 'node', function(evt) {
        const nodeId = evt.target.data('id');
        const obj = objectLookup[nodeId];
        if (obj) {
          showDetailView(nodeId);
        }
      });
      detailCy.resize();
      detailCy.fit(detailCy.elements(), 28);
    }

    function outboundCatalogRefs(object) {
      return (object?.outboundRefs || [])
        .map(reference => objectLookup[reference.target])
        .filter(Boolean);
    }

    function inboundCatalogRefs(object) {
      return (referencedByIndex[object?.id] || [])
        .map(reference => objectLookup[reference.source])
        .filter(Boolean);
    }

    function traverseDown(object, visited, collector) {
      outboundCatalogRefs(object).forEach(target => {
        if (visited.has(target.id) || !deployableTypes.has(target.type)) {
          return;
        }
        visited.add(target.id);
        collector.add(target.id);
        traverseDown(target, visited, collector);
      });
    }

    function traverseUp(object, visited, collector) {
      inboundCatalogRefs(object).forEach(source => {
        if (visited.has(source.id) || !deployableTypes.has(source.type)) {
          return;
        }
        visited.add(source.id);
        collector.add(source.id);
        traverseUp(source, visited, collector);
      });
    }

    function computeImpactSelection(selectedId) {
      const selected = objectLookup[selectedId];
      const impacted = new Set();
      const siblings = new Set();

      if (!selected || !deployableTypes.has(selected.type)) {
        return { selected, impacted, siblings, supported: false };
      }

      if (selected.type === 'software_deployment_pattern') {
        traverseDown(selected, new Set([selected.id]), impacted);
      } else {
        traverseDown(selected, new Set([selected.id]), impacted);
        traverseUp(selected, new Set([selected.id]), impacted);
      }

      siblings.delete(selected.id);
      impacted.delete(selected.id);
      return { selected, impacted, siblings, supported: true };
    }

    function impactHighlightColor(kind) {
      if (kind === 'selected') return '#f59e0b';
      if (kind === 'sibling') return '#8b5cf6';
      return '#ef4444';
    }

    function groupedImpactObjects(selection) {
      const grouped = {};
      if (!selection.selected || !selection.supported) {
        return grouped;
      }

      const allIds = new Set([selection.selected.id, ...selection.impacted, ...selection.siblings]);
      [...allIds].forEach(id => {
        const object = objectLookup[id];
        if (!object || !deployableTypes.has(object.type)) {
          return;
        }
        const group = impactGroupForObject(object);
        const kind = id === selection.selected.id ? 'selected' : selection.siblings.has(id) ? 'sibling' : 'impacted';
        if (!grouped[group]) {
          grouped[group] = [];
        }
        grouped[group].push({ object, kind });
      });

      impactOrder.forEach(group => {
        if (grouped[group]) {
          grouped[group].sort((a, b) => a.object.name.localeCompare(b.object.name));
        }
      });
      return grouped;
    }

    function impactSidebarMarkup(selection) {
      const searchMatches = impactSearchTerm
        ? allObjects.filter(object => deployableTypes.has(object.type)).filter(object => {
            return objectSearchText(object).includes(impactSearchTerm.toLowerCase());
          }).slice(0, 8)
        : [];

      const grouped = groupedImpactObjects(selection);
      const orderedGroups = [...impactOrder.filter(group => grouped[group]?.length), ...Object.keys(grouped).filter(group => !impactOrder.includes(group) && grouped[group]?.length)];
      const hasItems = orderedGroups.length > 0;

      return `
        <aside class="impact-sidebar">
          <div>
            <h3 style="margin:0 0 10px">Impact Analysis</h3>
            <input id="impact-search" class="impact-search" type="text" placeholder="Search by name, alias, or UID" value="${escapeHtml(impactSearchTerm)}">
          </div>
          ${searchMatches.length ? `
            <div class="search-results">
              ${searchMatches.map(match => `
                <div class="search-result" data-impact-select="${match.id}">
                  <div class="impact-item-top"><strong>${escapeHtml(match.name)}</strong></div>
                  <div class="object-id">${escapeHtml(match.id)}</div>
                </div>
              `).join('')}
            </div>
          ` : impactSearchTerm ? '<div class="empty-card">No matching catalog objects.</div>' : ''}
          ${!impactSelectedId ? '<div class="empty-card">Search for an object to see its impact chain</div>' : ''}
          ${impactSelectedId && !selection.supported ? '<div class="empty-card">Impact analysis is available for catalog objects that participate in references.</div>' : ''}
          ${impactSelectedId && selection.supported && !hasItems ? '<div class="empty-card">No impacted catalog objects were found for the selected object.</div>' : ''}
          ${impactSelectedId && selection.supported && hasItems ? orderedGroups.map(group => grouped[group].length ? `
            <section class="impact-group">
              <h4>${escapeHtml(formatTypeLabel(group))}</h4>
              <div class="impact-group-list">
                ${grouped[group].map(entry => `
                  <div class="impact-item" data-impact-select="${entry.object.id}">
                    <div class="impact-item-top">
                      <span class="impact-dot" style="background:${impactHighlightColor(entry.kind)}"></span>
                      <strong>${escapeHtml(entry.object.name)}</strong>
                    </div>
                    <div class="object-id">${escapeHtml(entry.object.id)}</div>
                  </div>
                `).join('')}
              </div>
            </section>
          ` : '').join('') : ''}
        </aside>
      `;
    }

    function lifecycleFilterButtonsMarkup() {
      return `
        <div class="lifecycle-filter-row">
          ${impactLifecycleOrder.map(status => {
            const active = !!impactLifecycleFilters[status];
            const color = '#' + lifecycleColors[status];
            const classes = ['lifecycle-filter-button', active ? 'active' : '', status === 'retired' ? 'retired-filter' : '']
              .filter(Boolean)
              .join(' ');
            const style = active ? `background:${color};` : '';
            return `<button class="${classes}" style="${style}" data-impact-lifecycle="${status}">${escapeHtml(status)}</button>`;
          }).join('')}
        </div>
      `;
    }

    function buildImpactElements() {
      const cyNodes = allObjects
        .filter(object => deployableTypes.has(object.type))
        .map(object => ({
          data: {
            id: object.id,
            label: object.hasRiskRef ? `⚠ ${object.name}` : object.name,
            type: object.type,
            category: object.category || '',
            deliveryModel: object.deliveryModel || '',
            lifecycleStatus: object.lifecycleStatus,
            shape: object.type === 'reference_architecture' || object.type === 'software_deployment_pattern' ? 'round-rectangle' : object.shape,
            color: object.color,
            borderStyle: object.type === 'reference_architecture' ? 'dashed' : 'solid',
            nodeWidth: object.type === 'technology_component' || DEPLOYABLE_STANDARD_TYPES.includes(object.type) ? 145 : 150,
            nodeHeight: object.type === 'technology_component' || DEPLOYABLE_STANDARD_TYPES.includes(object.type) ? 86 : 92,
            textMaxWidth: object.type === 'technology_component' || DEPLOYABLE_STANDARD_TYPES.includes(object.type) ? 145 : 150
          },
          classes: object.name.length > 20 ? 'long-label' : ''
        }));

      const edgeIds = new Set();
      const edges = [];
      allObjects.filter(object => deployableTypes.has(object.type)).forEach(object => {
        (object.outboundRefs || []).forEach(reference => {
          if (objectLookup[reference.target] && deployableTypes.has(objectLookup[reference.target].type)) {
            const id = `${object.id}->${reference.target}:${reference.path}`;
            if (!edgeIds.has(id)) {
              edgeIds.add(id);
              edges.push({ data: { id, source: object.id, target: reference.target } });
            }
          }
        });
      });

      return [...cyNodes, ...edges];
    }

    function visibleImpactNodes() {
      return impactCy ? impactCy.nodes(':visible') : cytoscape().collection();
    }

    function serviceRbbNodesSorted(nodes) {
      const order = ['runtime_service', 'data_at_rest_service', 'edge_gateway_service', 'product_service'];
      return nodes
        .filter(node => ['runtime_service', 'data_at_rest_service', 'edge_gateway_service', 'product_service'].includes(node.data('type')))
        .sort((a, b) => {
          const aCategory = a.data('type') || 'other';
          const bCategory = b.data('type') || 'other';
          const aIndex = order.includes(aCategory) ? order.indexOf(aCategory) : order.length;
          const bIndex = order.includes(bCategory) ? order.indexOf(bCategory) : order.length;
          if (aIndex !== bIndex) return aIndex - bIndex;
          return String(a.data('label') || '').localeCompare(String(b.data('label') || ''));
        });
    }

    function computeImpactPositions(nodes, containerWidth) {
      const ROW_HEIGHT = 120;
      const NODE_SPACING = 140;
      const TIER_GAP = 40;
      const safeWidth = Math.max(320, Math.floor(containerWidth));
      const nodeList = nodes.toArray();
      const knownIds = new Set();
      const addTier = tierNodes => {
        tierNodes.forEach(node => knownIds.add(node.id()));
        return tierNodes;
      };
      const tiers = [
        addTier(nodeList.filter(node => node.data('type') === 'software_deployment_pattern')),
        addTier(nodeList.filter(node => node.data('type') === 'reference_architecture')),
        addTier(serviceRbbNodesSorted(nodes)),
        addTier(nodeList.filter(node => node.data('type') === 'host')
          .sort((a, b) => String(a.data('label') || '').localeCompare(String(b.data('label') || '')))),
        addTier(nodeList.filter(node => !knownIds.has(node.id()))
          .sort((a, b) => String(a.data('label') || '').localeCompare(String(b.data('label') || ''))))
      ];

      const positions = {};
      let currentY = 60;

      tiers.forEach(tierNodes => {
        if (!tierNodes.length) return;
        const nodesPerRow = Math.max(1, Math.floor(safeWidth / NODE_SPACING));
        tierNodes.forEach((node, index) => {
          const row = Math.floor(index / nodesPerRow);
          const col = index % nodesPerRow;
          const rowCount = Math.min(nodesPerRow, tierNodes.length - row * nodesPerRow);
          const contentWidth = Math.max(NODE_SPACING, (rowCount - 1) * NODE_SPACING);
          const startX = Math.max(40, (safeWidth - contentWidth) / 2);
          positions[node.id()] = {
            x: startX + col * NODE_SPACING,
            y: currentY + row * ROW_HEIGHT
          };
        });
        const rowsInTier = Math.ceil(tierNodes.length / nodesPerRow);
        currentY += rowsInTier * ROW_HEIGHT + TIER_GAP;
      });

      return positions;
    }

    function applyImpactLifecycleVisibility() {
      if (!impactCy) return;
      impactLifecycleOrder.forEach(status => {
        const selector = `node[lifecycleStatus = "${status}"]`;
        if (impactLifecycleFilters[status]) {
          impactCy.nodes(selector).show();
        } else {
          impactCy.nodes(selector).hide();
        }
      });
      impactCy.edges().forEach(edge => {
        if (edge.source().visible() && edge.target().visible()) {
          edge.show();
        } else {
          edge.hide();
        }
      });
    }

    function rerunImpactLayout() {
      if (!impactCy) return;
      impactCy.resize();
      applyImpactLifecycleVisibility();
      const container = document.getElementById('impact-cy');
      const containerWidth = (container?.clientWidth || impactCy.width() || 960) - 24;
      const visibleNodes = impactCy.nodes(':visible');
      const positions = computeImpactPositions(visibleNodes, containerWidth);
      impactCy.layout({
        name: 'preset',
        positions
      }).run();
      impactCy.resize();
    }

    function applyImpactStyles(selection) {
      if (!impactCy) return;
      impactCy.nodes().removeClass('selected-impact impacted-impact sibling-impact dim-impact base-impact');
      impactCy.edges().removeClass('active-edge dim-edge');

      if (!impactSelectedId || !selection.supported || !selection.selected || !impactCy.getElementById(selection.selected.id).nonempty()) {
        impactCy.nodes(':visible').addClass('base-impact');
        return;
      }

      impactCy.nodes(':visible').removeClass('base-impact').addClass('dim-impact');
      impactCy.edges().addClass('dim-edge');

      const highlighted = new Set([selection.selected.id, ...selection.impacted, ...selection.siblings]);
      highlighted.forEach(id => {
        const node = impactCy.getElementById(id);
        if (!node.nonempty()) return;
        node.removeClass('dim-impact');
        if (id === selection.selected.id) {
          node.addClass('selected-impact');
        } else if (selection.siblings.has(id)) {
          node.addClass('sibling-impact');
        } else {
          node.addClass('impacted-impact');
        }
      });

      impactCy.edges().forEach(edge => {
        if (highlighted.has(edge.source().id()) && highlighted.has(edge.target().id())) {
          edge.removeClass('dim-edge').addClass('active-edge');
        }
      });
    }

    function renderImpactGraph(selection) {
      destroyDetailCy();
      destroyImpactCy();
      impactCy = cytoscape({
        container: document.getElementById('impact-cy'),
        elements: buildImpactElements(),
        layout: { name: 'preset', positions: {} },
        style: [
          {
            selector: 'node',
            style: {
              'label': 'data(label)',
              'shape': 'data(shape)',
              'background-color': 'data(color)',
              'border-width': 2,
              'border-style': 'data(borderStyle)',
              'border-color': '#a89784',
              'color': '#1f1a14',
              'font-size': 10,
              'text-wrap': 'wrap',
              'text-max-width': 'data(textMaxWidth)',
              'text-valign': 'center',
              'text-halign': 'center',
              'text-outline-width': 2,
              'text-outline-color': '#fbf8f3',
              'width': 'data(nodeWidth)',
              'height': 'data(nodeHeight)',
              'cursor': 'pointer',
              'opacity': 1
            }
          },
          {
            selector: 'edge',
            style: {
              'curve-style': 'bezier',
              'width': 1.8,
              'line-color': '#a89784',
              'target-arrow-color': '#a89784',
              'target-arrow-shape': 'triangle',
              'opacity': 0.35
            }
          },
          {
            selector: 'node.base-impact',
            style: {
              'opacity': 1
            }
          },
          {
            selector: 'node.dim-impact',
            style: {
              'opacity': 0.15
            }
          },
          {
            selector: 'node.selected-impact',
            style: {
              'opacity': 1,
              'border-color': '#b45309',
              'border-width': 4
            }
          },
          {
            selector: 'node.impacted-impact',
            style: {
              'opacity': 1,
              'border-color': '#b91c1c',
              'border-width': 3
            }
          },
          {
            selector: 'node.sibling-impact',
            style: {
              'opacity': 1,
              'border-color': '#7a3a8a',
              'border-width': 3
            }
          },
          {
            selector: 'edge.active-edge',
            style: {
              'opacity': 0.75
            }
          },
          {
            selector: 'edge.dim-edge',
            style: {
              'opacity': 0.1
            }
          }
        ]
      });
      impactCy.on('tap', 'node', evt => {
        selectImpactObject(evt.target.data('id'));
      });
      applyImpactLifecycleVisibility();
      applyImpactStyles(selection);
      rerunImpactLayout();
    }

    function runImpactAnalysis(id) {
      impactSelectedId = id;
      renderImpactView();
    }

    function selectImpactObject(id, promoteToSearch = false) {
      if (promoteToSearch && objectLookup[id]) {
        impactSearchTerm = objectLookup[id].name;
      }
      runImpactAnalysis(id);
    }

    function renderImpactView() {
      currentMode = 'impact';
      executiveDrilldown = null;
      syncHashForImpactView();
      const selection = impactSelectedId ? computeImpactSelection(impactSelectedId) : { selected: null, impacted: new Set(), siblings: new Set(), supported: false };
      renderSidebarContent(sidebarMarkup(impactSidebarMarkup(selection)));
      pageRoot.innerHTML = `
        <div class="view-shell">
          ${topNavMarkup()}
          <section class="impact-graph-card">
            <div class="impact-graph-top">
              <h3 style="margin:0">Impact Graph</h3>
              ${lifecycleFilterButtonsMarkup()}
            </div>
            <div id="impact-cy"></div>
          </section>
        </div>
      `;

      attachTopNavHandlers();
      const searchInput = document.getElementById('impact-search');
      if (searchInput) {
        searchInput.addEventListener('input', event => {
          impactSearchTerm = event.target.value;
          const cursorStart = event.target.selectionStart ?? impactSearchTerm.length;
          const cursorEnd = event.target.selectionEnd ?? impactSearchTerm.length;
          renderImpactView();
          const refreshedInput = document.getElementById('impact-search');
          if (refreshedInput) {
            refreshedInput.focus();
            refreshedInput.setSelectionRange(cursorStart, cursorEnd);
          }
        });
        searchInput.addEventListener('keydown', event => {
          if (event.key === 'Enter') {
            const firstMatch = allObjects.find(object => deployableTypes.has(object.type) && objectSearchText(object).includes(impactSearchTerm.toLowerCase()));
            if (firstMatch) {
              runImpactAnalysis(firstMatch.id);
            }
          }
        });
      }
      pageRoot.querySelectorAll('[data-impact-select]').forEach(item => {
        item.addEventListener('click', () => {
          selectImpactObject(item.dataset.impactSelect);
        });
        item.addEventListener('dblclick', () => {
          selectImpactObject(item.dataset.impactSelect, true);
        });
      });
      pageRoot.querySelectorAll('[data-impact-lifecycle]').forEach(button => {
        button.addEventListener('click', () => {
          const status = button.dataset.impactLifecycle;
          impactLifecycleFilters[status] = !impactLifecycleFilters[status];
          renderImpactView();
        });
      });
      renderImpactGraph(selection);
      attachSidebarHandlers();
    }

    window.addEventListener('resize', () => {
      if (detailCy) {
        detailCy.resize();
        detailCy.fit(detailCy.elements(), 28);
      }
      if (impactCy) {
        rerunImpactLayout();
      }
    });

    window.addEventListener('hashchange', () => {
      applyRouteFromHash();
    });

    applyRouteFromHash();
  </script>
</body>
</html>
"""


def write_browser(payload: dict[str, Any], output_path: Path) -> None:
    html = HTML_TEMPLATE.replace("__BROWSER_DATA__", json.dumps(payload, default=str))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    output_path = args.output.resolve()
    registry = load_objects(args.workspace.resolve())
    payload = build_browser_payload(registry, args.workspace.resolve())
    write_browser(payload, output_path)
    for warning in payload.get("warnings", []):
        print(warning, file=sys.stderr)
    print(f"Generated {display_path(output_path)} with {len(payload['objects'])} objects.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
