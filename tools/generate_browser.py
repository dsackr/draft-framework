#!/usr/bin/env python3
# ARCHITECTURE CONTRACT
# This generator is data-driven. The following must remain true:
# 1. No catalog object IDs are hardcoded in this file.
# 2. No product names (accelify, hrlinks, etc.) appear in rendering logic.
# 3. All relationships are derived from the cross-reference index built at load time.
# 4. All object types are rendered via type dispatch — unknown types get a generic fallback.
# 5. Adding a new catalog object type requires only: (a) a new YAML file, (b) optionally a new renderer.
#    No other changes to this file are required for the new type to appear in list view.
# Note: location icon inference uses generic string heuristics only; unknown patterns always fall back to a generic icon.
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "docs" / "index.html"
SCHEMA_ROOT = REPO_ROOT / "schemas"
CATALOG_FOLDERS = [
    "odcs",
    "abbs",
    "ards",
    "compliance-frameworks",
    "sdms",
    "rbbs",
    "reference-architectures",
]
LIFECYCLE_COLORS = {
    "invest": "10b981",
    "maintain": "3b82f6",
    "disinvest": "f59e0b",
    "exit": "ef4444",
    "pre-invest": "8b5cf6",
    "unknown": "475569",
}
REF_CONTAINER_KEYS = {
    "ref",
    "runsOn",
    "appliesPattern",
    "hostRbb",
    "functionAbb",
    "osAbb",
    "hardwareAbb",
    "inherits",
    "platformDependency",
    "linkedSDM",
    "riskRef",
    "framework",
}
CATALOG_ID_PREFIXES = ("abb.", "rbb.", "odc.", "ard.", "ps.", "ra.", "sdm.", "framework.", "saas.")


def is_product_service_classification(obj: dict[str, Any]) -> bool:
    return obj.get("type") == "rbb" and obj.get("category") == "service" and obj.get("serviceCategory") == "product"


def is_saas_service_classification(obj: dict[str, Any]) -> bool:
    return obj.get("type") == "rbb" and obj.get("category") == "service" and obj.get("serviceCategory") == "saas"


def is_database_service(obj: dict[str, Any]) -> bool:
    return obj.get("type") == "rbb" and obj.get("category") == "service" and obj.get("serviceCategory") == "database"


def is_general_service(obj: dict[str, Any]) -> bool:
    return obj.get("type") == "rbb" and obj.get("category") == "service" and obj.get("serviceCategory") == "general"


def discover_yaml_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for folder_name in CATALOG_FOLDERS:
        folder = root / folder_name
        if not folder.exists():
            continue
        files.extend(sorted(folder.rglob("*.yaml")))
    return files


def load_objects() -> dict[str, dict[str, Any]]:
    objects: dict[str, dict[str, Any]] = {}
    for path in discover_yaml_files(REPO_ROOT):
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        if isinstance(data, dict) and data.get("id"):
            data["_source"] = str(path.relative_to(REPO_ROOT))
            objects[str(data["id"])] = data
    return objects


def load_schemas(root: Path) -> list[dict[str, Any]]:
    schemas: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        if isinstance(data, dict):
            data["_schema_path"] = str(path.relative_to(REPO_ROOT))
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


def extract_refs(node: Any, path: str = "") -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            child_path = f"{path}.{key}" if path else key
            if key in REF_CONTAINER_KEYS and isinstance(value, str) and value.startswith(CATALOG_ID_PREFIXES):
                refs.append((value, child_path))
            elif key.endswith("Refs") and isinstance(value, list):
                for index, item in enumerate(value):
                    if isinstance(item, str) and item.startswith(CATALOG_ID_PREFIXES):
                        refs.append((item, f"{child_path}[{index}]"))
            else:
                refs.extend(extract_refs(value, child_path))
    elif isinstance(node, list):
        if path.endswith(".appliesTo"):
            return refs
        for index, item in enumerate(node):
            if isinstance(item, str) and item.startswith(CATALOG_ID_PREFIXES):
                refs.append((item, f"{path}[{index}]"))
            else:
                refs.extend(extract_refs(item, f"{path}[{index}]"))
    return refs


def build_reference_index(registry: dict[str, dict[str, Any]]) -> tuple[dict[str, list[dict[str, str]]], dict[str, list[dict[str, str]]], list[str]]:
    outbound: dict[str, list[dict[str, str]]] = {}
    referenced_by: dict[str, list[dict[str, str]]] = {}
    warnings: list[str] = []
    for object_id, obj in registry.items():
        refs = extract_refs(obj)
        outbound[object_id] = [{"target": target, "path": ref_path} for target, ref_path in refs]
        for target, ref_path in refs:
            referenced_by.setdefault(target, []).append({"source": object_id, "path": ref_path})
            if target not in registry:
                warnings.append(f"Warning: {object_id} references missing object '{target}' via {ref_path}")
    return outbound, referenced_by, warnings


def shape_for(obj: dict[str, Any]) -> str:
    if obj["type"] == "reference_architecture":
        return "hexagon"
    if obj["type"] == "software_distribution_manifest":
        return "star"
    if obj["type"] == "odc":
        return "barrel"
    if obj["type"] == "compliance_framework":
        return "hexagon"
    if obj["type"] == "ard":
        return "round-rectangle"
    if obj["type"] == "abb":
        return "ellipse"
    if obj["type"] == "rbb":
        if is_product_service_classification(obj) or is_saas_service_classification(obj):
            return "round-rectangle"
        return "round-rectangle" if obj.get("category") == "host" else "diamond"
    return "round-rectangle"


def to_json(value: Any) -> str:
    return json.dumps(value, indent=2, default=str)


def humanize_slug(value: str) -> str:
    return value.replace("-", " ").title()


def filter_type_for(obj: dict[str, Any]) -> str:
    return str(obj.get("type", "unknown"))


def type_label_for(obj: dict[str, Any]) -> str:
    if obj["type"] == "abb":
        classification = humanize_slug(str(obj.get("classification", "unknown")))
        suffix = f" / appliance / {classification}" if obj.get("subtype") == "appliance" else f" / {classification}"
        return f"ABB{suffix}"
    if obj["type"] == "odc":
        return "ODC"
    if obj["type"] == "compliance_framework":
        return "Compliance Framework"
    if obj["type"] == "ard":
        return f"ARD / {obj.get('category', 'risk')}"
    if obj["type"] == "reference_architecture":
        return "Reference Architecture"
    if obj["type"] == "software_distribution_manifest":
        return "Software Distribution Manifest"
    if obj["type"] == "rbb":
        if obj.get("category") == "host":
            return "Host RBB"
        if is_product_service_classification(obj):
            return "Product Service"
        if is_saas_service_classification(obj):
            return "SaaS Service"
        if is_database_service(obj):
            return "Database Service RBB"
        if is_general_service(obj):
            return "General Service RBB"
        return "Host RBB"
    return obj.get("type", "Unknown")


def internal_component_refs(obj: dict[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    seen: set[str] = set()

    for component in obj.get("internalComponents", []):
        ref = component.get("ref")
        if ref and ref not in seen:
            refs.append({"ref": ref, "role": component.get("role", "component")})
            seen.add(ref)

    for field_name, role in (
        ("osAbb", "os"),
        ("hardwareAbb", "hardware"),
        ("hostRbb", "host"),
        ("functionAbb", "function"),
    ):
        ref = obj.get(field_name)
        if ref and ref not in seen:
            refs.append({"ref": ref, "role": role})
            seen.add(ref)

    return refs


def build_compliance_payload(registry: dict[str, dict[str, Any]]) -> dict[str, Any]:
    frameworks = sorted(
        [obj for obj in registry.values() if obj.get("type") == "compliance_framework"],
        key=lambda item: item.get("name", ""),
    )
    frameworks_by_id = {framework["id"]: framework for framework in frameworks}
    local_controls: dict[str, list[dict[str, Any]]] = {}
    for framework in frameworks:
        framework_id = framework["id"]
        raw = framework.get("controls") or []
        if not isinstance(raw, list):
            continue
        normalized_controls: list[dict[str, Any]] = []
        for control in raw:
            if not isinstance(control, dict):
                continue
            normalized_controls.append(
                {
                    "controlId": str(control.get("controlId", "")),
                    "name": str(control.get("name", "")),
                    "description": str(control.get("description", "")),
                    "externalReference": str(control.get("externalReference", "")),
                    "appliesTo": [str(scope) for scope in control.get("appliesTo", []) if str(scope).strip()],
                    "relatedConcern": str(control.get("relatedConcern", "")),
                    "requirementMode": str(control.get("requirementMode", "mandatory")),
                    "naAllowed": bool(control.get("naAllowed", False)),
                    "applicability": control.get("applicability", {}),
                    "validAnswerTypes": [str(value) for value in control.get("validAnswerTypes", []) if str(value).strip()],
                    "notes": str(control.get("notes", "")),
                }
            )
        local_controls[framework_id] = normalized_controls

    resolved_cache: dict[str, list[dict[str, Any]]] = {}

    def control_key(control: dict[str, Any]) -> str:
        applies_to = ",".join(sorted(control.get("appliesTo", [])))
        return f"{control.get('controlId', '')}|{control.get('relatedConcern', '')}|{applies_to}"

    def resolve_framework_controls(framework_id: str, stack: set[str] | None = None) -> list[dict[str, Any]]:
        if framework_id in resolved_cache:
            return resolved_cache[framework_id]
        stack = stack or set()
        if framework_id in stack:
            return []
        stack.add(framework_id)
        framework = frameworks_by_id.get(framework_id, {})
        merged: dict[str, dict[str, Any]] = {}
        for parent_id in framework.get("extends", []) if isinstance(framework.get("extends"), list) else []:
            parent_controls = resolve_framework_controls(str(parent_id), stack)
            for control in parent_controls:
                merged[control_key(control)] = control
        for control in local_controls.get(framework_id, []):
            merged[control_key(control)] = control
        resolved_cache[framework_id] = list(merged.values())
        stack.remove(framework_id)
        return resolved_cache[framework_id]

    default_framework_id = next(
        (framework["id"] for framework in frameworks if framework.get("defaultSelection") is True),
        frameworks[0]["id"] if frameworks else "",
    )

    return {
        "frameworks": [
            {
                "id": framework["id"],
                "name": framework.get("name", framework["id"]),
                "frameworkKind": framework.get("frameworkKind", ""),
                "catalogStatus": framework.get("catalogStatus", ""),
                "lifecycleStatus": framework.get("lifecycleStatus", ""),
                "defaultSelection": framework.get("defaultSelection", False),
                "extends": framework.get("extends", []),
                "description": framework.get("description", ""),
                "controlCount": len(resolve_framework_controls(framework["id"])),
            }
            for framework in frameworks
        ],
        "defaultFrameworkId": default_framework_id,
        "controlsByFramework": {framework["id"]: resolve_framework_controls(framework["id"]) for framework in frameworks},
    }


def build_browser_payload(registry: dict[str, dict[str, Any]]) -> dict[str, Any]:
    objects = list(registry.values())
    schemas = load_schemas(SCHEMA_ROOT)
    outbound_refs, referenced_by, warnings = build_reference_index(registry)
    risk_marked_rbb_ids = {
        deployed.get("ref")
        for obj in objects
        if obj.get("type") == "software_distribution_manifest"
        for group in obj.get("serviceGroups", [])
        if isinstance(group, dict)
        for deployed in group.get("rbbs", [])
        if isinstance(deployed, dict) and deployed.get("riskRef")
    }
    browser_objects: list[dict[str, Any]] = []

    for obj in objects:
        object_id = obj["id"]
        schema = select_schema(obj, schemas) or {}
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
                "name": obj["name"],
                "type": obj["type"],
                "typeLabel": type_label_for(obj),
                "filterType": filter_type_for(obj),
                "category": obj.get("category", ""),
                "serviceCategory": obj.get("serviceCategory", ""),
                "description": obj.get("description", ""),
                "version": obj.get("version", ""),
                "catalogStatus": obj.get("catalogStatus", ""),
                "lifecycleStatus": obj.get("lifecycleStatus", "unknown"),
                "status": obj.get("status", ""),
                "product": obj.get("product", ""),
                "runsOn": obj.get("runsOn", ""),
                "subtype": obj.get("subtype", ""),
                "vendor": obj.get("vendor", ""),
                "productName": obj.get("productName", ""),
                "productVersion": obj.get("productVersion", ""),
                "classification": obj.get("classification", ""),
                "platformDependency": obj.get("platformDependency", ""),
                "addressesConcerns": obj.get("addressesConcerns", []),
                "configurations": obj.get("configurations", []),
                "deploymentConfigurations": obj.get("deploymentConfigurations", []),
                "capability": obj.get("capability", ""),
                "networkPlacement": obj.get("networkPlacement", ""),
                "patchingOwner": obj.get("patchingOwner", ""),
                "complianceCerts": obj.get("complianceCerts", []),
                "dataLeavesInfrastructure": obj.get("dataLeavesInfrastructure", None),
                "dataResidencyCommitment": obj.get("dataResidencyCommitment", ""),
                "dpaNotes": obj.get("dpaNotes", ""),
                "vendorSLA": obj.get("vendorSLA", ""),
                "authenticationModel": obj.get("authenticationModel", ""),
                "incidentNotificationProcess": obj.get("incidentNotificationProcess", ""),
                "owner": obj.get("owner", {}),
                "shape": shape_for(obj),
                "color": f"#{LIFECYCLE_COLORS.get(obj.get('lifecycleStatus'), LIFECYCLE_COLORS['unknown'])}",
                "source": obj.get("_source", ""),
                "tags": obj.get("tags", []),
                "ardCategory": obj.get("category", "") if obj.get("type") == "ard" else "",
                "internalComponents": internal_component_refs(obj),
                "externalInteractions": obj.get("externalInteractions", []),
                "architecturalDecisions": obj.get("architecturalDecisions", {}),
                "requirements": obj.get("requirements", []),
                "satisfiesODC": obj.get("satisfiesODC", []),
                "appliesTo": obj.get("appliesTo", {}),
                "inherits": obj.get("inherits", ""),
                "scalingUnits": obj.get("scalingUnits", []),
                "serviceGroups": obj.get("serviceGroups", []),
                "appliesPattern": obj.get("appliesPattern", ""),
                "architectureRisksAndDecisions": obj.get("architectureRisksAndDecisions", []),
                "affectedComponent": obj.get("affectedComponent", ""),
                "impact": obj.get("impact", ""),
                "mitigationPath": obj.get("mitigationPath", ""),
                "decisionRationale": obj.get("decisionRationale", ""),
                "relatedARDs": obj.get("relatedARDs", []),
                "linkedSDM": obj.get("linkedSDM", ""),
                "frameworkKind": obj.get("frameworkKind", ""),
                "defaultSelection": obj.get("defaultSelection", False),
                "controlCount": len(obj.get("controls", [])) if obj.get("type") == "compliance_framework" and isinstance(obj.get("controls"), list) else 0,
                "hasRiskRef": obj.get("id") in risk_marked_rbb_ids,
                "outboundRefs": outbound_refs.get(object_id, []),
                "referencedBy": referenced_by.get(object_id, []),
                "editorSchema": schema_meta,
                "detail": to_json(obj),
                "existsInCatalog": True,
            }
        )

    browser_lookup = {obj["id"]: obj for obj in browser_objects}
    filter_values = sorted({obj["type"] for obj in objects})
    lifecycle_values = sorted(
        {obj.get("lifecycleStatus", "unknown") for obj in objects},
        key=lambda value: ["pre-invest", "invest", "maintain", "disinvest", "exit", "unknown"].index(value)
        if value in {"pre-invest", "invest", "maintain", "disinvest", "exit", "unknown"}
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
        "compliance": build_compliance_payload(registry),
        "repoUrl": repository_web_url(REPO_ROOT),
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
      color-scheme: dark;
      --page: #0f172a;
      --panel: #111827;
      --card: #1e293b;
      --border: #334155;
      --muted: #94a3b8;
      --text: #e2e8f0;
      --subtle: #cbd5e1;
      --accent: #38bdf8;
    }
    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      min-height: 100%;
      background: var(--page);
      color: var(--text);
      font-family: "SF Pro Display", "Segoe UI", sans-serif;
    }
    .app {
      min-height: 100vh;
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr);
      gap: 1px;
      background: var(--border);
    }
    .sidebar,
    .main {
      background: linear-gradient(180deg, rgba(15,23,42,0.98), rgba(17,24,39,0.98));
    }
    .sidebar {
      padding: 24px 20px;
      border-right: 1px solid rgba(51,65,85,0.7);
    }
    .sidebar h1 {
      margin: 0;
      font-size: 18px;
      letter-spacing: 0.02em;
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
      border-top: 1px solid rgba(51,65,85,0.8);
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
      border: 1px solid rgba(255,255,255,0.18);
      flex: 0 0 auto;
    }
    .main {
      padding: 28px;
    }
    .view-shell {
      display: grid;
      gap: 22px;
    }
    .top-nav {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .nav-button {
      border: 1px solid var(--border);
      border-radius: 999px;
      background: rgba(15,23,42,0.72);
      color: var(--text);
      padding: 10px 16px;
      font: inherit;
      cursor: pointer;
      transition: border-color 120ms ease, background 120ms ease, transform 120ms ease;
    }
    .nav-button:hover {
      border-color: rgba(56,189,248,0.55);
      transform: translateY(-1px);
    }
    .nav-button.active {
      background: rgba(56,189,248,0.18);
      border-color: rgba(56,189,248,0.6);
      color: #dff7ff;
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
      background: rgba(30,41,59,0.78);
      color: var(--text);
      padding: 10px 16px;
      font: inherit;
      cursor: pointer;
      transition: border-color 120ms ease, background 120ms ease, transform 120ms ease;
    }
    .tab-button {
      padding: 12px 18px;
      background: rgba(15,23,42,0.82);
      font-weight: 600;
    }
    .tab-button:hover,
    .filter-button:hover,
    .back-button:hover {
      border-color: rgba(56,189,248,0.55);
      transform: translateY(-1px);
    }
    .tab-button.active,
    .filter-button.active {
      background: rgba(56,189,248,0.18);
      border-color: rgba(56,189,248,0.6);
      color: #dff7ff;
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
      border-bottom: 1px solid rgba(51,65,85,0.72);
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
      border: 1px solid rgba(148,163,184,0.18);
      background: rgba(15,23,42,0.65);
      color: var(--subtle);
    }
    .catalog-approved { border-color: rgba(16,185,129,0.45); color: #d1fae5; }
    .catalog-draft { border-color: rgba(245,158,11,0.45); color: #fde68a; }
    .catalog-stub { border-color: rgba(148,163,184,0.35); color: #cbd5e1; }
    .ard-risk { border-color: rgba(245,158,11,0.45); color: #fde68a; }
    .ard-decision { border-color: rgba(59,130,246,0.45); color: #bfdbfe; }
    .ard-status { border-color: rgba(148,163,184,0.35); color: #cbd5e1; }
    .ps-badge {
      border-color: rgba(20,184,166,0.45);
      color: #99f6e4;
      background: rgba(20,184,166,0.12);
    }
    .saas-badge {
      border-color: rgba(168,85,247,0.45);
      color: #e9d5ff;
      background: rgba(168,85,247,0.14);
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
      background: rgba(30,41,59,0.78);
      color: var(--text);
      padding: 10px 16px;
      font: inherit;
      cursor: pointer;
    }
    .detail-tab.active {
      background: rgba(56,189,248,0.18);
      border-color: rgba(56,189,248,0.6);
      color: #dff7ff;
    }
    .detail-panel[hidden] {
      display: none !important;
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
      background: rgba(15,23,42,0.82);
      color: var(--text);
      padding: 10px 14px;
      font: inherit;
      cursor: pointer;
      transition: border-color 120ms ease, background 120ms ease, transform 120ms ease;
      text-decoration: none;
    }
    .action-button:hover {
      border-color: rgba(56,189,248,0.55);
      transform: translateY(-1px);
    }
    .action-button.secondary {
      background: rgba(30,41,59,0.82);
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
      background: #0f172a;
    }
    .interactions-list {
      display: grid;
      gap: 12px;
      max-height: 350px;
      overflow: auto;
      padding-right: 4px;
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
      background: rgba(15,23,42,0.55);
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
    .odc-control-line {
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
      background: rgba(15,23,42,0.45);
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
    .control-badges,
    .odc-control-badges {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }
    .control-badge {
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
    .control-badge.conditional {
      background: #4a3414;
      border-color: #f59e0b;
      color: #fcd34d;
    }
    .control-mode {
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
      background: rgba(15,23,42,0.78);
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
      border: 1px solid rgba(51,65,85,0.8);
      background: rgba(30,41,59,0.9);
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
      color: #e2e8f0;
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
      background: rgba(15,23,42,0.72);
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
      background: rgba(30,41,59,0.94);
      color: #e2e8f0;
      font-size: 14px;
      cursor: pointer;
      transition: border-color 0.15s ease, background 0.15s ease, color 0.15s ease;
    }
    .topology-filter-button.active {
      border-color: rgba(14,165,233,0.65);
      background: rgba(14,165,233,0.16);
      color: #bae6fd;
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
      background: rgba(15,23,42,0.7);
      border: 1px solid rgba(148,163,184,0.3);
      color: #e2e8f0;
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
      background: rgba(15,23,42,0.52);
    }
    .topology-tier-header {
      padding: 10px 12px;
      border-radius: 12px;
      border: 1px solid rgba(71,85,105,0.8);
      background: rgba(15,23,42,0.72);
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
      background: rgba(30,41,59,0.96);
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
      background: rgba(30,41,59,0.96);
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
      background: rgba(15,23,42,0.74);
      display: grid;
      gap: 12px;
    }
    .eks-label {
      color: #cbd5e1;
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
      background: rgba(30,41,59,0.95);
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
      background: rgba(30,41,59,0.88);
    }
    .topology-node-icon.pod {
      background: rgba(59,130,246,0.18);
      color: #93c5fd;
      border-color: rgba(59,130,246,0.35);
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
      background: rgba(15,23,42,0.5);
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
      background: rgba(15,23,42,0.78);
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
      background: rgba(15,23,42,0.55);
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
      background: rgba(15,23,42,0.78);
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
    .lifecycle-filter-button.exit-filter {
      border-style: dashed;
      opacity: 0.55;
    }
    .lifecycle-filter-button.exit-filter:not(.active) {
      text-decoration: line-through;
    }
    #impact-cy {
      width: 100%;
      min-width: 0;
      height: 720px;
      border-radius: 14px;
      border: 1px solid rgba(51,65,85,0.85);
      background: #0f172a;
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
      background: rgba(15,23,42,0.86);
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
      background: rgba(15,23,42,0.52);
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
      background: rgba(15,23,42,0.72);
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
    .yaml-preview {
      white-space: pre-wrap;
      word-break: break-word;
      font-family: "SF Mono", Menlo, monospace;
      font-size: 13px;
      line-height: 1.65;
      margin: 0;
      color: #dbeafe;
    }
    .decisions-card {
      background: rgba(30,41,59,0.92);
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
    .cap-default { background: rgba(100,116,139,0.18); border-color: rgba(100,116,139,0.4); color: #cbd5e1; }
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
    .odc-control-line,
    .requirement-rationale-label,
    .mechanism-label,
    .mechanism-text,
    .mechanism-example,
    .control-badge,
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
    }
    @media (max-width: 980px) {
      .app { grid-template-columns: 1fr; }
      .sidebar { border-right: 0; border-bottom: 1px solid rgba(51,65,85,0.7); }
      .main { padding: 20px; }
      .decisions-grid { grid-template-columns: 1fr; }
      .definition-list { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <h1>Catalog Browser</h1>
      <p>Browse the catalog by object type, then inspect a single object’s components, interactions, and decisions.</p>
      <div class="sidebar-stack">
        <div id="sidebar-content"></div>
        <div class="legend-block">
          <div class="legend-title">Lifecycle Legend</div>
          <div class="legend-list" id="legend"></div>
        </div>
      </div>
    </aside>
    <main class="main">
      <div id="app-root"></div>
    </main>
  </div>
  <div id="editor-overlay" class="editor-overlay"></div>
  <script>
    const browserData = __BROWSER_DATA__;
    const lifecycleColors = browserData.lifecycleColors;
    const allObjects = browserData.objects.slice().sort((a, b) => a.name.localeCompare(b.name));
    const objectLookup = browserData.lookup;
    const referencedByIndex = browserData.referencedBy || {};
    const complianceData = browserData.compliance || {};
    const repoUrl = browserData.repoUrl || '';
    const appRoot = document.getElementById('app-root');
    const sidebarContent = document.getElementById('sidebar-content');
    const legend = document.getElementById('legend');
    const editorOverlay = document.getElementById('editor-overlay');
    let editorState = null;
    let controlImportState = null;
    const CATEGORY_CONFIG = [
      {
        id: 'architecture',
        label: 'Architecture Content',
        filters: [
          { id: 'all', label: 'All', types: ['software_distribution_manifest', 'reference_architecture', 'rbb'] },
          { id: 'software_distribution_manifest', label: 'SDMs', types: ['software_distribution_manifest'] },
          { id: 'reference_architecture', label: 'RAs', types: ['reference_architecture'] },
          { id: 'rbb', label: 'RBBs', types: ['rbb'] }
        ],
        rows: [
          { id: 'software_distribution_manifest', label: 'Software Distribution Manifests', types: ['software_distribution_manifest'] },
          { id: 'reference_architecture', label: 'Reference Architectures', types: ['reference_architecture'] },
          { id: 'rbb', label: 'RBBs', types: ['rbb'] }
        ]
      },
      {
        id: 'supporting',
        label: 'Supporting Content',
        filters: [
          { id: 'all', label: 'All', types: ['abb', 'ard'] },
          { id: 'abb', label: 'ABBs', types: ['abb'] },
          { id: 'ard', label: 'DRDs', types: ['ard'] }
        ],
        rows: [
          { id: 'abb', label: 'ABBs', types: ['abb'] },
          { id: 'ard', label: 'Deployment Risks and Decisions', types: ['ard'] }
        ]
      },
      {
        id: 'framework',
        label: 'Framework Content',
        filters: [
          { id: 'all', label: 'All', types: ['odc', 'compliance_framework'] },
          { id: 'odc', label: 'ODCs', types: ['odc'] },
          { id: 'compliance_framework', label: 'Compliance Frameworks', types: ['compliance_framework'] }
        ],
        rows: [
          { id: 'odc', label: 'ODCs', types: ['odc'] },
          { id: 'compliance_framework', label: 'Compliance Frameworks', types: ['compliance_framework'] }
        ]
      }
    ];
    const lifecycleValues = browserData.lifecycleValues || [];
    const complianceFrameworks = complianceData.frameworks || [];
    const CONTROL_SCOPE_OPTIONS = [
      { value: 'rbb.host', label: 'Host RBB' },
      { value: 'rbb.service.general', label: 'General Service RBB' },
      { value: 'rbb.service.database', label: 'Database Service RBB' },
      { value: 'rbb.service.product', label: 'Product Service RBB' },
      { value: 'rbb.service.saas', label: 'SaaS Service RBB' },
      { value: 'ra', label: 'Reference Architecture' },
      { value: 'sdm', label: 'Software Distribution Manifest' },
      { value: 'abb.appliance', label: 'Appliance ABB' }
    ];
    const CONTROL_ANSWER_TYPE_OPTIONS = [
      { value: 'abb', label: 'ABB' },
      { value: 'abbConfiguration', label: 'ABB Configuration' },
      { value: 'deploymentConfiguration', label: 'Deployment Configuration' },
      { value: 'externalInteraction', label: 'External Interaction' },
      { value: 'architecturalDecision', label: 'Architectural Decision' },
      { value: 'field', label: 'Direct Field Answer' }
    ];
    const APPLICABILITY_FIELD_OPTIONS = [
      'architecturalContext.soldInTexas',
      'architecturalContext.servesTexasAgencies',
      'architecturalContext.handlesCardholderData',
      'architecturalContext.handlesPHI',
      'architecturalContext.servesFederalCustomers'
    ];
    const deployableTypes = new Set(
      allObjects
        .filter(object => !['odc', 'ard', 'compliance_framework'].includes(object.type))
        .map(object => object.type)
    );
    const impactOrder = ['software_distribution_manifest', 'reference_architecture', 'rbb', 'abb'];
    const impactLifecycleOrder = lifecycleValues;
    let activeCategory = 'architecture';
    let activeFilter = 'all';
    let currentDetailId = null;
    let currentMode = 'list';
    const navHistory = [];
    let detailCy = null;
    let impactCy = null;
    let impactSelectedId = null;
    let impactSearchTerm = '';
    let currentSdmScalingFilter = 'all';
    let suppressHashSync = false;
    let selectedFrameworkId = (() => {
      try {
        const saved = window.localStorage.getItem('draft-framework:selected-framework');
        if (saved && objectLookup[saved]) {
          return saved;
        }
      } catch (error) {}
      return complianceData.defaultFrameworkId || complianceFrameworks[0]?.id || null;
    })();
    let impactLifecycleFilters = Object.fromEntries(
      impactLifecycleOrder.map(status => [status, status !== 'exit'])
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

    function relatedConcernOptions() {
      const values = new Set();
      allObjects
        .filter(object => object.type === 'odc')
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
      if (normalized === 'abb') return 'ABB';
      if (normalized === 'rbb') return 'RBB';
      if (normalized === 'odc') return 'ODC';
      if (normalized === 'ard') return 'ARD';
      if (normalized === 'software_distribution_manifest') return 'Software Distribution Manifest';
      if (normalized === 'reference_architecture') return 'Reference Architecture';
      if (normalized === 'compliance_framework') return 'Compliance Framework';
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

    function applianceBadge() {
      return '<span class="badge appliance-badge">appliance</span>';
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

    function syncHashForListView() {
      setHashState({
        view: 'list',
        category: activeCategory !== 'software' ? activeCategory : null,
        filter: activeFilter !== 'all' ? activeFilter : null
      });
    }

    function syncHashForDetailView(id) {
      setHashState({ view: 'detail', id });
    }

    function syncHashForImpactView() {
      setHashState({ view: 'impact', id: impactSelectedId, q: impactSearchTerm || null });
    }

    function applyRouteFromHash() {
      if (suppressHashSync) return;
      const params = currentHashState();
      const view = params.get('view');
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
      const category = params.get('category');
      activeCategory = CATEGORY_CONFIG.some(item => item.id === category) ? category : 'software';
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
          <button class="nav-button ${currentMode === 'list' ? 'active' : ''}" data-nav="list">List View</button>
          <button class="nav-button ${currentMode === 'detail' ? 'active' : ''}" data-nav="detail" ${currentDetailId ? '' : 'disabled'}>Detail View</button>
          <button class="nav-button ${currentMode === 'impact' ? 'active' : ''}" data-nav="impact">Impact Analysis</button>
        </div>
      `;
    }

    function renderSidebarContent(contentHtml) {
      sidebarContent.innerHTML = contentHtml;
    }

    function selectedFramework() {
      return (selectedFrameworkId && objectLookup[selectedFrameworkId]) || complianceFrameworks[0] || null;
    }

    function selectedFrameworkControls() {
      return complianceData.controlsByFramework?.[selectedFrameworkId] || [];
    }

    function controlModeLabel(control) {
      if ((control.requirementMode || 'mandatory') === 'conditional') {
        return control.naAllowed ? 'Conditional / N-A allowed' : 'Conditional';
      }
      return 'Required';
    }

    function scopeForObject(object) {
      if (!object) return null;
      if (object.type === 'odc') {
        const appliesTo = object.appliesTo || {};
        if (appliesTo.type === 'rbb') {
          if (appliesTo.category === 'host') return 'rbb.host';
          if (appliesTo.category === 'service' && appliesTo.serviceCategory === 'general') return 'rbb.service.general';
          if (appliesTo.category === 'service' && appliesTo.serviceCategory === 'database') return 'rbb.service.database';
          if (appliesTo.category === 'service' && appliesTo.serviceCategory === 'product') return 'rbb.service.product';
          if (appliesTo.category === 'service' && appliesTo.serviceCategory === 'saas') return 'rbb.service.saas';
        }
        if (appliesTo.type === 'reference_architecture') return 'ra';
        if (appliesTo.type === 'software_distribution_manifest') return 'sdm';
        if (appliesTo.type === 'abb' && appliesTo.subtype === 'appliance') return 'abb.appliance';
        return null;
      }
      if (object.type === 'rbb') {
        if (object.category === 'host') return 'rbb.host';
        if (object.category === 'service' && object.serviceCategory === 'general') return 'rbb.service.general';
        if (object.category === 'service' && object.serviceCategory === 'database') return 'rbb.service.database';
        if (object.category === 'service' && object.serviceCategory === 'product') return 'rbb.service.product';
        if (object.category === 'service' && object.serviceCategory === 'saas') return 'rbb.service.saas';
      }
      if (object.type === 'reference_architecture') return 'ra';
      if (object.type === 'software_distribution_manifest') return 'sdm';
      if (object.type === 'abb' && object.subtype === 'appliance') return 'abb.appliance';
      return null;
    }

    function controlsForRequirement(object, requirementId) {
      const scope = scopeForObject(object);
      if (!scope || !requirementId) return [];
      return selectedFrameworkControls().filter(control =>
        (control.appliesTo || []).includes(scope) &&
        (control.relatedConcern || '') === requirementId
      );
    }

    function additionalControlsForObject(object) {
      const scope = scopeForObject(object);
      if (!scope) return [];
      return selectedFrameworkControls().filter(control =>
        (control.appliesTo || []).includes(scope) &&
        !(control.relatedConcern || '').trim()
      );
    }

    function complianceFrameworkMarkup() {
      if (!complianceFrameworks.length) {
        return '';
      }
      const current = selectedFramework();
      return `
        <div class="sidebar-block">
          <div class="legend-title">Compliance Framework</div>
          <select id="framework-select" class="sidebar-select">
            ${complianceFrameworks.map(framework => `
              <option value="${framework.id}" ${framework.id === current?.id ? 'selected' : ''}>${escapeHtml(framework.name)}</option>
            `).join('')}
          </select>
          <div class="sidebar-help">${escapeHtml(current?.description || 'Select the security and compliance controls used to extend the effective ODC checklist.')}</div>
        </div>
      `;
    }

    function currentFilterMarkup() {
      return `
        <div class="sidebar-block">
          <div class="legend-title">Current Filter</div>
          <div class="current-filter"><span class="dot" style="background:#38bdf8"></span><span>${escapeHtml(categoryConfig().label)} / ${escapeHtml(formatListFilterLabel(activeFilter))}</span></div>
        </div>
      `;
    }

    function sidebarMarkup(extraMarkup = '') {
      return `${complianceFrameworkMarkup()}${currentFilterMarkup()}${extraMarkup}`;
    }

    function rerenderCurrentView() {
      if (currentMode === 'detail') {
        renderDetailView();
        return;
      }
      if (currentMode === 'impact') {
        renderImpactView();
        return;
      }
      renderListView();
    }

    function attachSidebarHandlers() {
      const frameworkSelect = document.getElementById('framework-select');
      if (!frameworkSelect) {
        return;
      }
      frameworkSelect.addEventListener('change', event => {
        selectedFrameworkId = event.target.value || complianceData.defaultFrameworkId || complianceFrameworks[0]?.id || null;
        try {
          window.localStorage.setItem('draft-framework:selected-framework', selectedFrameworkId || '');
        } catch (error) {}
        rerenderCurrentView();
      });
    }

    function attachTopNavHandlers() {
      appRoot.querySelectorAll('[data-nav]').forEach(button => {
        button.addEventListener('click', () => {
          const nav = button.dataset.nav;
          if (nav === 'list') {
            destroyImpactCy();
            renderListView();
            return;
          }
          if (nav === 'detail' && currentDetailId) {
            destroyImpactCy();
            renderDetailView();
            return;
          }
          if (nav === 'impact') {
            renderImpactView();
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

    function listRowMarkup(row, objects) {
      if (!objects.length) {
        return '';
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

    function objectCardTitle(object) {
      if (object.type !== 'odc') {
        return object.name;
      }
      const trimmed = String(object.name || '').replace(/\s+Object Definition Checklist$/i, '');
      if (trimmed === 'Appliance ABB') {
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
            ${object.type === 'ard' ? ardCategoryBadge(object.ardCategory) : ''}
            ${object.type === 'ard' ? ardStatusBadge(object.status) : ''}
            ${object.type === 'rbb' && object.serviceCategory === 'product' ? productBadge(object.product) : ''}
            ${object.type === 'rbb' && object.serviceCategory === 'saas' ? saasBadge() : ''}
          </div>
          <div class="badges">
            <div class="badge">${escapeHtml(object.typeLabel)}</div>
            ${object.type === 'rbb' && object.serviceCategory === 'product' ? `<div class="object-id">${escapeHtml(object.product)}</div>` : ''}
            ${object.type === 'abb' && object.subtype === 'appliance' ? applianceBadge() : ''}
          </div>
        </article>
      `;
    }

    function abbClassificationLabel(value) {
      return formatTitleCase(String(value || 'unknown').replace(/-/g, ' '));
    }

    function renderListView() {
      currentMode = 'list';
      currentDetailId = null;
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
      renderSidebarContent(sidebarMarkup());
      appRoot.innerHTML = `
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

      appRoot.querySelectorAll('[data-category-tab]').forEach(button => {
        button.addEventListener('click', () => {
          activeCategory = button.dataset.categoryTab;
          activeFilter = 'all';
          renderListView();
        });
      });

      appRoot.querySelectorAll('[data-filter]').forEach(button => {
        button.addEventListener('click', () => {
          activeFilter = button.dataset.filter;
          renderListView();
        });
      });

      appRoot.querySelectorAll('[data-object-id]').forEach(card => {
        card.addEventListener('click', () => {
          showDetailView(card.dataset.objectId);
        });
      });

      attachTopNavHandlers();
      attachSidebarHandlers();
    }

    function flattenDecisionEntries(prefix, value, entries) {
      if (value && typeof value === 'object' && !Array.isArray(value)) {
        Object.entries(value).forEach(([childKey, childValue]) => {
          flattenDecisionEntries(prefix ? `${prefix}.${childKey}` : childKey, childValue, entries);
        });
        return;
      }
      const rendered = Array.isArray(value) ? value.join(', ') : String(value);
      entries.push({ key: prefix, value: rendered });
    }

    function decisionMarkup(object) {
      const decisions = object.architecturalDecisions || {};
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
                <span class="badge ${capabilityClass(interaction.capability)}">${escapeHtml(interaction.capability || 'other')}</span>
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

    function controlBadges(controls) {
      if (!controls || !controls.length) {
        return '<span class="interaction-notes">No required controls added by the selected framework.</span>';
      }
      return controls.map(control => `
        ${control.externalReference
          ? `<a class="control-badge ${control.requirementMode === 'conditional' ? 'conditional' : ''}" href="${escapeHtml(control.externalReference)}" target="_blank" rel="noopener noreferrer">${escapeHtml(control.controlId || '')}${control.name ? ` - ${escapeHtml(control.name)}` : ''}<span class="control-mode">${escapeHtml(controlModeLabel(control))}</span></a>`
          : `<span class="control-badge ${control.requirementMode === 'conditional' ? 'conditional' : ''}">${escapeHtml(control.controlId || '')}${control.name ? ` - ${escapeHtml(control.name)}` : ''}<span class="control-mode">${escapeHtml(controlModeLabel(control))}</span></span>`}
      `).join('');
    }

    function odcRequirementsMarkup(object) {
      const requirements = object.requirements || [];
      const framework = selectedFramework();
      const extraControls = additionalControlsForObject(object);
      if (!requirements.length) {
        return '<div class="empty-card">No requirements are documented for this ODC.</div>';
      }
      return `
        <section class="section-card">
          <h3>Requirements</h3>
          <div class="section-stack">
            ${requirements.map(requirement => `
              <article class="requirement-card">
                <div class="requirement-name">${escapeHtml(formatTitleCase(requirement.id || 'requirement'))}</div>
                <div class="requirement-description">${escapeHtml(requirement.description || '')}</div>
                ${requirement.rationale ? `
                  <div class="requirement-rationale-label">Rationale</div>
                  <div class="requirement-rationale">${escapeHtml(requirement.rationale)}</div>
                ` : ''}
                <div class="mechanism-label">Required Controls${framework ? ` / ${escapeHtml(framework.name)}` : ''}</div>
                <div class="control-badges">${controlBadges(controlsForRequirement(object, requirement.id || ''))}</div>
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
          ${extraControls.length ? `
            <div class="mechanism-label" style="margin-top:16px;">Additional Framework Controls</div>
            <div class="control-badges">${controlBadges(extraControls)}</div>
          ` : ''}
        </section>
      `;
    }

    function rbbOdcMarkup(object) {
      const odcIds = object.satisfiesODC || [];
      const framework = selectedFramework();
      if (!odcIds.length) {
        return '';
      }
      return `
        <section class="section-card">
          <h3>ODC Satisfaction${framework ? ` / ${escapeHtml(framework.name)}` : ''}</h3>
          <div class="section-stack">
            ${odcIds.map(odcId => {
              const odc = objectLookup[odcId];
              const requirements = odc?.requirements || [];
              return `
                <article class="odc-card">
                  <div class="odc-name">Satisfies: ${escapeHtml(odcId)}</div>
                  ${requirements.length ? requirements.map(requirement => `
                    <div class="odc-control-line">└─ ${escapeHtml(requirement.id || 'requirement')} → ${escapeHtml(controlsForRequirement(odc, requirement.id || '').map(control => control.controlId).join(', ') || 'No required controls')}</div>
                  `).join('') : '<div class="interaction-notes">No requirements found on referenced ODC.</div>'}
                </article>
              `;
            }).join('')}
          </div>
        </section>
      `;
    }

    function sdmRisksMarkup(object) {
      const references = object.architectureRisksAndDecisions || [];
      if (!references.length) {
        return '';
      }
      return `
        <section class="section-card">
          <h3>Architecture Risks and Decisions</h3>
          <div class="section-stack">
            ${references.map(entry => {
              const ard = objectLookup[entry.ref];
              return `
                <article class="odc-card">
                  <div class="odc-name">
                    ${ard ? `<span class="ard-link" data-object-link="${ard.id}">${escapeHtml(ard.name)}</span>` : escapeHtml(entry.ref || 'Unknown ARD')}
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
        return '<div class="empty-card">No service groups are documented for this software distribution manifest.</div>';
      }
      return `
        <section class="section-card">
          <h3>Service Groups</h3>
          <div class="section-stack">
            ${groups.map(group => {
              const scalingUnit = group.scalingUnit ? scalingUnits.get(group.scalingUnit) : null;
              const externalInteractions = (group.externalInteractions || []).filter(item => (item.type || 'external') !== 'internal');
              const internalInteractions = (group.externalInteractions || []).filter(item => (item.type || 'external') === 'internal');
              const rbbEntries = group.rbbs || [];
              const productCount = rbbEntries.filter(entry => objectLookup[entry.ref]?.serviceCategory === 'product').length;
              const saasCount = rbbEntries.filter(entry => objectLookup[entry.ref]?.serviceCategory === 'saas').length;
              const reusableCount = rbbEntries.filter(entry => {
                const serviceCategory = objectLookup[entry.ref]?.serviceCategory;
                return !['product', 'saas'].includes(serviceCategory || '');
              }).length;
              return `
                <article class="odc-card">
                  <div class="odc-name">${escapeHtml(group.name || 'Unnamed Service Group')}</div>
                  <div class="interaction-notes">${escapeHtml(group.deploymentTarget || 'Unspecified deployment target')}</div>
                  <div class="badges">
                    ${group.scalingUnit ? `<span class="badge">${escapeHtml(group.scalingUnit)}</span>` : '<span class="badge">unscoped</span>'}
                    ${scalingUnit?.type ? `<span class="badge">${escapeHtml(scalingUnit.type)}</span>` : ''}
                    ${productCount ? `<span class="badge ps-badge">${productCount} PS</span>` : ''}
                    ${reusableCount ? `<span class="badge">${reusableCount} RBB</span>` : ''}
                    ${(group.applianceAbbs || []).length ? applianceBadge() : ''}
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
              <dt>ID</dt><dd><span class="object-id">${escapeHtml(object.id)}</span></dd>
              <dt>Product</dt><dd>${escapeHtml(object.product || '')}</dd>
              <dt>Runs On</dt><dd>${runsOnObject ? `<span class="ard-link" data-object-link="${object.runsOn}">${escapeHtml(runsOnObject.name)}</span>` : escapeHtml(object.runsOn || '')}</dd>
              <dt>Underlying RBB</dt><dd>${escapeHtml(object.runsOn || 'Not documented')}</dd>
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
      const title = object.subtype === 'appliance' ? 'Appliance ABB' : 'Architecture Building Block';
      return `
        <section class="section-card">
          <h3>${escapeHtml(title)}</h3>
          <div class="section-stack">
            <div class="badges">
              ${object.subtype === 'appliance' ? applianceBadge() : ''}
              ${lifecycleBadge(object.lifecycleStatus)}
              ${catalogBadge(object.catalogStatus)}
            </div>
            <dl class="definition-list">
              <dt>Vendor</dt><dd>${escapeHtml(object.vendor || '')}</dd>
              <dt>Product Name</dt><dd>${escapeHtml(object.productName || '')}</dd>
              <dt>Product Version</dt><dd>${escapeHtml(object.productVersion || '')}</dd>
              <dt>Classification</dt><dd>${escapeHtml(abbClassificationLabel(object.classification))}</dd>
              ${object.addressesConcerns?.length ? `<dt>Addresses Concerns</dt><dd>${escapeHtml(object.addressesConcerns.map(abbClassificationLabel).join(', '))}</dd>` : ''}
              ${object.platformDependency ? `<dt>Platform Dependency</dt><dd>${escapeHtml(object.platformDependency)}</dd>` : ''}
              ${object.capability ? `<dt>Capability</dt><dd>${escapeHtml(object.capability || '')}</dd>` : ''}
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
                    <div class="object-id">${escapeHtml((configuration.addressesConcerns || []).map(abbClassificationLabel).join(', '))}</div>
                  </article>
                `).join('')}
              </div>
            ` : ''}
          </div>
        </section>
        ${object.subtype === 'appliance' && objectLookup['odc.appliance-abb'] ? odcRequirementsMarkup(objectLookup['odc.appliance-abb']) : ''}
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

    function saasServiceDetailMarkup(object) {
      return `
        <section class="section-card">
          <h3>SaaS Service Classification</h3>
          <div class="section-stack">
            <div class="badges">
              ${saasBadge()}
              ${lifecycleBadge(object.lifecycleStatus)}
              ${catalogBadge(object.catalogStatus)}
              ${boolBadge(object.dataLeavesInfrastructure === true, 'Data Leaves Infrastructure', 'Data Stays In Boundary')}
            </div>
            <dl class="definition-list">
              <dt>Vendor</dt><dd>${escapeHtml(object.vendor || '')}</dd>
              <dt>Capability</dt><dd>${escapeHtml(object.capability || '')}</dd>
              <dt>Data Residency</dt><dd>${escapeHtml(object.dataResidencyCommitment || 'Not documented')}</dd>
              <dt>DPA Notes</dt><dd>${escapeHtml(object.dpaNotes || 'Not documented')}</dd>
              <dt>Vendor SLA</dt><dd>${escapeHtml(object.vendorSLA || 'Not documented')}</dd>
              <dt>Authentication Model</dt><dd>${escapeHtml(object.authenticationModel || 'Not documented')}</dd>
              <dt>Compliance Certs</dt><dd>${escapeHtml((object.complianceCerts || []).join(', ') || 'None documented')}</dd>
            </dl>
            ${object.incidentNotificationProcess ? `<div class="interaction-notes"><strong>Incident Notification:</strong> ${escapeHtml(object.incidentNotificationProcess)}</div>` : ''}
          </div>
        </section>
        ${objectLookup['odc.saas-service'] ? odcRequirementsMarkup(objectLookup['odc.saas-service']) : ''}
      `;
    }

    function complianceFrameworkDetailMarkup(object) {
      const parents = Array.isArray(object.extends) ? object.extends : [];
      const frameworkSummary = complianceFrameworks.find(item => item.id === object.id);
      return `
        <section class="section-card">
          <h3>Compliance Framework</h3>
          <div class="section-stack">
            <div class="badges">
              <div class="badge">${escapeHtml(object.frameworkKind || 'common')}</div>
              ${object.defaultSelection ? '<div class="badge">Default Selection</div>' : ''}
              <div class="badge">${escapeHtml(String(frameworkSummary?.controlCount || object.controlCount || 0))} Controls</div>
              ${lifecycleBadge(object.lifecycleStatus)}
            </div>
            <div class="header-description">${escapeHtml(object.description || 'No description provided.')}</div>
            ${parents.length ? `
              <div><strong>Extends:</strong> ${parents.map(parentId => objectLookup[parentId]
                ? `<span class="ard-link" data-object-link="${parentId}">${escapeHtml(parentId)}</span>`
                : escapeHtml(parentId)
              ).join(', ')}</div>
            ` : ''}
            <div class="header-actions">
              <button class="action-button secondary" id="open-control-import-button">Import Controls</button>
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
        .replace(/\s+RBB$/i, '');
    }

    const SDM_TIERS = ['presentation', 'application', 'data', 'utility'];
    const SDM_TIER_LABELS = {
      presentation: 'Presentation Services',
      application: 'Application Services',
      data: 'Data Services',
      utility: 'Utility Services'
    };

    function isContainerHostObject(object) {
      return !!object && object.type === 'rbb' && object.category === 'host' && String(object.id || '').startsWith('rbb.host.container.');
    }

    function topologyNodeIcon(entry, objectType = 'rbb') {
      const ref = entry.ref || '';
      const object = objectLookup[ref];
      const serviceObject = object?.serviceCategory === 'product' && object?.runsOn ? objectLookup[object.runsOn] : object;
      if (objectType === 'appliance') return { icon: '🔧', cls: '' };
      if (object?.serviceCategory === 'saas') return { icon: '☁', cls: 'cloud' };
      if (object?.serviceCategory === 'product' && isContainerHostObject(objectLookup[object?.runsOn])) {
        return { icon: '⬢', cls: 'pod' };
      }
      if (ref.startsWith('rbb.service.web.')) return { icon: '🖥', cls: '' };
      if (ref.startsWith('rbb.service.app.')) return { icon: '🗂', cls: '' };
      if (ref.startsWith('rbb.service.dbms.')) return { icon: '🛢', cls: '' };
      if (ref.startsWith('rbb.service.messaging.')) return { icon: '📬', cls: '' };
      if (serviceObject?.serviceCategory === 'database') return { icon: '🛢', cls: '' };
      return { icon: '🖧', cls: '' };
    }

    function deploymentTargetPresentation(location) {
      const text = String(location || 'Unspecified');
      if (/AWS/i.test(text)) {
        return { cls: 'aws', badge: 'AWS', icon: '🟧' };
      }
      if (/Datacenter|\\bDC\\b/i.test(text)) {
        return { cls: 'datacenter', badge: 'DC', icon: '☁' };
      }
      return { cls: 'generic', badge: 'Host', icon: '🖧' };
    }

    function colorForToken(value) {
      const palette = ['#38bdf8', '#22c55e', '#f59e0b', '#a855f7', '#ef4444', '#14b8a6', '#e879f9', '#64748b'];
      const token = String(value || '');
      let hash = 0;
      for (let index = 0; index < token.length; index += 1) {
        hash = ((hash << 5) - hash) + token.charCodeAt(index);
        hash |= 0;
      }
      return palette[Math.abs(hash) % palette.length];
    }

    function entryDiagramTier(entry) {
      return SDM_TIERS.includes(entry?.diagramTier) ? entry.diagramTier : 'application';
    }

    function supportEntryTier(entry, objectType) {
      const object = objectLookup[entry?.ref];
      const capability = object?.capability || '';
      if (objectType === 'appliance') {
        if (capability === 'load-balancing') return 'presentation';
        if (['file-storage', 'data-persistence'].includes(capability)) return 'data';
        return 'utility';
      }
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
        return '<span class="topology-risk" title="Missing ARD reference">?</span>';
      }
      if (String(entry.intent || '').toLowerCase() === 'sa') {
        return '<span class="topology-info" title="Explicit architecture decision">ⓘ</span>';
      }
      return '';
    }

    function topologyNodeMarkup(entry, options = {}) {
      const {
        objectType = 'rbb',
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
      if (objectType === 'rbb') classes.push('rbb-node');
      if (objectType === 'appliance') classes.push('appliance-node');
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
      const cards = [];

      (group.rbbs || [])
        .filter(entry => entryDiagramTier(entry) === tier)
        .forEach(entry => {
          const target = objectLookup[entry.ref] || {};
          const serviceCategory = target.serviceCategory || '';
          const objectType = serviceCategory === 'product'
            ? 'product'
            : (serviceCategory === 'saas' ? 'saas' : 'rbb');
          const badgeLabel = serviceCategory === 'product'
            ? 'PS'
            : (serviceCategory === 'saas' ? 'SaaS' : 'RBB');
          cards.push(topologyNodeMarkup(entry, {
            objectType,
            badgeLabel,
            scalingUnit,
            meta: `${group.name} • ${groupMeta}`
          }));
        });

      (group.applianceAbbs || [])
        .filter(entry => supportEntryTier(entry, 'appliance') === tier)
        .forEach(entry => {
          cards.push(topologyNodeMarkup(entry, {
            objectType: 'appliance',
            badgeLabel: 'APPL',
            scalingUnit,
            meta: `${group.name} • ${groupMeta}`
          }));
        });

      if (!cards.length) {
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
            ${cards.join('')}
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
      const columns = Object.fromEntries(SDM_TIERS.map(tier => [tier, []]));
      groups.forEach(group => {
        SDM_TIERS.forEach(tier => {
          const markup = serviceGroupSectionMarkup(group, tier);
          if (markup) {
            columns[tier].push(markup);
          }
        });
      });
      return `
        <div class="deployment-target-columns">
          ${SDM_TIERS.map(tier => `
            <section class="topology-tier-column">
              <div class="topology-tier-header ${escapeHtml(tier)}">${escapeHtml(SDM_TIER_LABELS[tier])}</div>
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

      const targets = new Map();
      serviceGroups.forEach(group => {
        const target = group.deploymentTarget || (object.type === 'reference_architecture' ? 'Reference Pattern' : 'Unspecified');
        if (!targets.has(target)) {
          targets.set(target, []);
        }
        targets.get(target).push(group);
      });

      const scalingUnits = [...new Set(serviceGroups.map(group => group.scalingUnit).filter(Boolean))];
      const topologyToolbar = object.type === 'software_distribution_manifest' ? `
        <div class="topology-toolbar">
          <div class="topology-filter-buttons">
            <button class="topology-filter-button ${currentSdmScalingFilter === 'all' ? 'active' : ''}" data-scaling-filter="all">All scaling units</button>
            ${scalingUnits.map(unit => `<button class="topology-filter-button ${currentSdmScalingFilter === unit ? 'active' : ''}" data-scaling-filter="${escapeHtml(unit)}">${escapeHtml(unit)}</button>`).join('')}
          </div>
          <div class="topology-filter-help">Select a scaling unit to highlight participating services.</div>
        </div>
      ` : '';

      const deploymentTargetMarkup = [...targets.entries()].map(([target, grouped]) => {
        const meta = deploymentTargetPresentation(target);
        return `
          <section class="deployment-target-cluster">
            <div class="deployment-target-header">
              <div class="deployment-target-title">${escapeHtml(target)}</div>
              <span class="location-badge ${escapeHtml(meta.cls)}">${meta.icon} ${escapeHtml(meta.badge)}</span>
            </div>
            <div class="deployment-target-content">
              ${tierColumnsMarkup(grouped)}
            </div>
          </section>
        `;
      }).join('');

      return `
        <div class="topology-layout">
          ${topologyToolbar}
          <div class="topology-scaling-units">
            ${deploymentTargetMarkup}
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
            ${object.linkedSDM && objectLookup[object.linkedSDM] ? `<span>Linked SDM: <span class="ard-link" data-object-link="${object.linkedSDM}">${escapeHtml(object.linkedSDM)}</span></span>` : object.linkedSDM ? `<span>Linked SDM: ${escapeHtml(object.linkedSDM)}</span>` : ''}
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
          ${(object.relatedARDs || []).length ? `
            <section class="ard-section">
              <h3>Related ARDs</h3>
              <div class="section-stack">
                ${object.relatedARDs.map(ardId => objectLookup[ardId]
                  ? `<span class="ard-link" data-object-link="${ardId}">${escapeHtml(ardId)}</span>`
                  : `<span>${escapeHtml(ardId)}</span>`
                ).join('')}
              </div>
            </section>
          ` : ''}
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
      const priority = ['schemaVersion', 'id', 'type', 'name', 'description', 'version', 'catalogStatus', 'lifecycleStatus', 'owner', 'tags'];
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
            <div class="editor-help">Edit as YAML for structured data.</div>
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
      const previewNode = editorOverlay.querySelector('#editor-yaml-preview');
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

    function normalizeFrameworkControl(control = {}) {
      const applicability = control.applicability || {};
      const applicabilityMode = Array.isArray(applicability.allOf) && applicability.allOf.length ? 'allOf' : 'anyOf';
      const clauses = Array.isArray(applicability[applicabilityMode]) ? applicability[applicabilityMode] : [];
      return {
        controlId: String(control.controlId || ''),
        name: String(control.name || ''),
        externalReference: String(control.externalReference || ''),
        relatedConcern: String(control.relatedConcern || ''),
        requirementMode: control.requirementMode === 'conditional' ? 'conditional' : 'mandatory',
        appliesTo: Array.isArray(control.appliesTo) ? control.appliesTo.map(value => String(value)) : [],
        validAnswerTypes: Array.isArray(control.validAnswerTypes) ? control.validAnswerTypes.map(value => String(value)) : [],
        applicabilityMode,
        applicabilityClauses: clauses.length ? clauses.map(normalizeApplicabilityClause) : [blankApplicabilityClause()],
        description: String(control.description || ''),
        notes: String(control.notes || '')
      };
    }

    function parseImportedControlSeed(text) {
      const parsed = jsyaml.load(text);
      if (!parsed) return [];
      if (Array.isArray(parsed)) return parsed;
      if (Array.isArray(parsed.controls)) return parsed.controls;
      if (parsed.controlId || parsed.name || parsed.externalReference) return [parsed];
      throw new Error('Imported YAML must be a control list, a { controls: [...] } mapping, or a single control object.');
    }

    function cloneFrameworkControl(control) {
      return {
        ...control,
        appliesTo: [...(control.appliesTo || [])],
        validAnswerTypes: [...(control.validAnswerTypes || [])],
        applicabilityClauses: (control.applicabilityClauses || []).map(clause => ({ ...clause }))
      };
    }

    function mergeImportedControls(existingControls, importedControls) {
      const merged = existingControls.map(cloneFrameworkControl);
      importedControls.forEach(rawControl => {
        const controlId = String(rawControl?.controlId || '').trim();
        const name = String(rawControl?.name || '').trim();
        const externalReference = String(rawControl?.externalReference || '').trim();
        if (!controlId || !name || !externalReference) {
          throw new Error('Each imported control must declare controlId, name, and externalReference.');
        }
        const existingIndex = merged.findIndex(control => control.controlId === controlId);
        if (existingIndex >= 0) {
          merged[existingIndex].name = name;
          merged[existingIndex].externalReference = externalReference;
        } else {
          merged.push({
            ...normalizeFrameworkControl({}),
            controlId,
            name,
            externalReference
          });
        }
      });
      return merged;
    }

    function serializeControlImportFramework(object) {
      const framework = sanitizeDetailObject(object);
      framework.controls = controlImportState.controls.map((control, index) => {
        const controlId = String(control.controlId || '').trim();
        const name = String(control.name || '').trim();
        const externalReference = String(control.externalReference || '').trim();
        if (!controlId || !name || !externalReference) {
          throw new Error(`Control ${index + 1} must include controlId, name, and externalReference.`);
        }
        if (!Array.isArray(control.appliesTo) || !control.appliesTo.length) {
          throw new Error(`Control ${controlId} must declare at least one appliesTo scope.`);
        }
        if (!Array.isArray(control.validAnswerTypes) || !control.validAnswerTypes.length) {
          throw new Error(`Control ${controlId} must declare at least one valid answer type.`);
        }
        const serialized = {
          controlId,
          name,
          externalReference,
          appliesTo: [...control.appliesTo],
          requirementMode: control.requirementMode === 'conditional' ? 'conditional' : 'mandatory',
          validAnswerTypes: [...control.validAnswerTypes]
        };
        const relatedConcern = String(control.relatedConcern || '').trim();
        if (relatedConcern) {
          serialized.relatedConcern = relatedConcern;
        }
        if (control.description) {
          serialized.description = control.description;
        }
        if (control.notes) {
          serialized.notes = control.notes;
        }
        if (serialized.requirementMode === 'conditional') {
          serialized.naAllowed = true;
          const clauses = (control.applicabilityClauses || []).map(clause => {
            const field = String(clause.field || '').trim();
            if (!field) {
              throw new Error(`Control ${controlId} has a conditional applicability rule without a field.`);
            }
            if (clause.operator === 'truthy') {
              return { field, truthy: clause.truthy !== 'false' };
            }
            if (clause.operator === 'in') {
              const values = String(clause.valuesText || '')
                .split(',')
                .map(value => value.trim())
                .filter(Boolean);
              if (!values.length) {
                throw new Error(`Control ${controlId} has an applicability "in" rule without values.`);
              }
              return { field, in: values };
            }
            const value = String(clause.value || '').trim();
            if (!value) {
              throw new Error(`Control ${controlId} has an applicability ${clause.operator} rule without a value.`);
            }
            return clause.operator === 'contains'
              ? { field, contains: value }
              : { field, equals: value };
          });
          if (!clauses.length) {
            throw new Error(`Control ${controlId} must declare at least one applicability rule.`);
          }
          serialized.applicability = {
            [control.applicabilityMode === 'allOf' ? 'allOf' : 'anyOf']: clauses
          };
        }
        return serialized;
      });
      return framework;
    }

    function updateControlImportPreview(object) {
      const errorNode = editorOverlay.querySelector('#control-import-error');
      const previewNode = editorOverlay.querySelector('#control-import-preview');
      if (!controlImportState || !errorNode || !previewNode) return;
      try {
        const serialized = serializeControlImportFramework(object);
        controlImportState.serialized = serialized;
        previewNode.textContent = jsyaml.dump(serialized, { lineWidth: 100, noRefs: true });
        errorNode.textContent = '';
      } catch (error) {
        controlImportState.serialized = null;
        previewNode.textContent = '';
        errorNode.textContent = error instanceof Error ? error.message : String(error);
      }
    }

    function closeEditor() {
      editorOverlay.classList.remove('open');
      editorOverlay.innerHTML = '';
      editorState = null;
      controlImportState = null;
    }

    function openEditor(object) {
      const sourceObject = sanitizeDetailObject(object);
      const fields = orderedEditorFields(object);
      editorState = {
        objectId: object.id,
        fieldValues: { ...sourceObject },
        originalValues: JSON.parse(JSON.stringify(sourceObject)),
        serialized: null,
      };
      editorOverlay.innerHTML = `
        <div class="editor-panel">
          <div class="editor-header">
            <div class="editor-title">
              <h3>Edit ${escapeHtml(object.name)}</h3>
              <p>Static GitHub Pages cannot write back to the repo directly. Use this editor to adjust the object, preview the YAML, and then copy or download the result.</p>
            </div>
            <div class="editor-actions">
              ${repoSourceUrl(object) ? `<a class="action-button secondary" href="${escapeHtml(repoSourceUrl(object))}" target="_blank" rel="noreferrer">Open Source On GitHub</a>` : ''}
              <button class="action-button secondary" id="editor-reset">Reset</button>
              <button class="action-button secondary" id="editor-close">Close</button>
            </div>
          </div>
          <div class="editor-grid">
            <section class="editor-card">
              <h4>Editable Fields</h4>
              <div class="editor-meta">Schema: ${escapeHtml(object.editorSchema?.schemaPath || 'No matching schema found')}</div>
              <div class="editor-form">
                ${fields.map(field => fieldInputMarkup(object, field, sourceObject[field])).join('')}
              </div>
            </section>
            <section class="editor-card">
              <h4>YAML Preview</h4>
              <div class="editor-help">This preview updates as you edit. Complex fields use YAML textareas so lists and maps stay structured.</div>
              <div id="editor-error" class="editor-error"></div>
              <pre id="editor-yaml-preview" class="yaml-preview"></pre>
              <div class="editor-actions">
                <button class="action-button" id="editor-copy">Copy YAML</button>
                <button class="action-button" id="editor-download">Download YAML</button>
              </div>
            </section>
          </div>
        </div>
      `;
      editorOverlay.classList.add('open');

      editorOverlay.querySelectorAll('[data-editor-field]').forEach(input => {
        input.addEventListener('input', () => {
          const field = input.dataset.editorField;
          editorState.fieldValues[field] = input.type === 'checkbox' ? input.checked : input.value;
          updateEditorPreview(object);
        });
        if (input.type === 'checkbox') {
          input.addEventListener('change', () => {
            const field = input.dataset.editorField;
            editorState.fieldValues[field] = input.checked;
            updateEditorPreview(object);
          });
        }
      });

      editorOverlay.querySelector('#editor-close').addEventListener('click', closeEditor);
      editorOverlay.querySelector('#editor-reset').addEventListener('click', () => {
        openEditor(object);
      });
      editorOverlay.querySelector('#editor-copy').addEventListener('click', async () => {
        if (!editorState?.serialized) return;
        const yamlText = jsyaml.dump(editorState.serialized, { lineWidth: 100, noRefs: true });
        await navigator.clipboard.writeText(yamlText);
      });
      editorOverlay.querySelector('#editor-download').addEventListener('click', () => {
        if (!editorState?.serialized) return;
        const yamlText = jsyaml.dump(editorState.serialized, { lineWidth: 100, noRefs: true });
        const blob = new Blob([yamlText], { type: 'text/yaml;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = (object.source || `${object.id}.yaml`).split('/').pop();
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
      });
      editorOverlay.addEventListener('click', event => {
        if (event.target === editorOverlay) {
          closeEditor();
        }
      }, { once: true });
      updateEditorPreview(object);
    }

    function controlCheckboxMarkup(kind, controlIndex, optionValue, optionLabel, selectedValues) {
      return `
        <label class="editor-choice">
          <input type="checkbox" data-control-checkbox="${kind}" data-control-index="${controlIndex}" value="${escapeHtml(optionValue)}" ${selectedValues.includes(optionValue) ? 'checked' : ''}>
          <span>${escapeHtml(optionLabel)}</span>
        </label>
      `;
    }

    function applicabilityClauseMarkup(controlIndex, clauseIndex, clause) {
      const fieldListId = `applicability-fields-${controlIndex}-${clauseIndex}`;
      const operator = clause.operator || 'equals';
      const valueField = operator === 'truthy'
        ? `
          <div class="editor-field">
            <label>Truthy</label>
            <select data-clause-field="truthy" data-control-index="${controlIndex}" data-clause-index="${clauseIndex}">
              <option value="true" ${clause.truthy !== 'false' ? 'selected' : ''}>true</option>
              <option value="false" ${clause.truthy === 'false' ? 'selected' : ''}>false</option>
            </select>
          </div>
        `
        : operator === 'in'
          ? `
            <div class="editor-field">
              <label>Values</label>
              <input type="text" value="${escapeHtml(clause.valuesText || '')}" data-clause-field="valuesText" data-control-index="${controlIndex}" data-clause-index="${clauseIndex}" placeholder="value1, value2">
            </div>
          `
          : `
            <div class="editor-field">
              <label>Value</label>
              <input type="text" value="${escapeHtml(clause.value || '')}" data-clause-field="value" data-control-index="${controlIndex}" data-clause-index="${clauseIndex}">
            </div>
          `;
      return `
        <div class="import-card">
          <div class="import-card-header">
            <div class="import-card-title">
              <h5>Applicability Rule ${clauseIndex + 1}</h5>
              <div class="import-card-meta">Build the condition that makes this control apply.</div>
            </div>
            <button class="action-button secondary" data-remove-clause="${controlIndex}" data-remove-clause-index="${clauseIndex}">Remove Rule</button>
          </div>
          <div class="editor-subgrid">
            <div class="editor-field">
              <label>Field</label>
              <input type="text" value="${escapeHtml(clause.field || '')}" list="${fieldListId}" data-clause-field="field" data-control-index="${controlIndex}" data-clause-index="${clauseIndex}">
              <datalist id="${fieldListId}">
                ${APPLICABILITY_FIELD_OPTIONS.map(option => `<option value="${escapeHtml(option)}"></option>`).join('')}
              </datalist>
            </div>
            <div class="editor-field">
              <label>Operator</label>
              <select data-clause-field="operator" data-control-index="${controlIndex}" data-clause-index="${clauseIndex}">
                <option value="equals" ${operator === 'equals' ? 'selected' : ''}>equals</option>
                <option value="contains" ${operator === 'contains' ? 'selected' : ''}>contains</option>
                <option value="in" ${operator === 'in' ? 'selected' : ''}>in</option>
                <option value="truthy" ${operator === 'truthy' ? 'selected' : ''}>truthy</option>
              </select>
            </div>
          </div>
          ${valueField}
        </div>
      `;
    }

    function controlCardMarkup(control, controlIndex) {
      const concernOptions = ['<option value=""></option>']
        .concat(relatedConcernOptions().map(option => `<option value="${escapeHtml(option)}" ${control.relatedConcern === option ? 'selected' : ''}>${escapeHtml(option)}</option>`))
        .join('');
      const conditional = control.requirementMode === 'conditional';
      return `
        <div class="import-card">
          <div class="import-card-header">
            <div class="import-card-title">
              <h5>${escapeHtml(control.controlId || `New Control ${controlIndex + 1}`)}</h5>
              <div class="import-card-meta">${escapeHtml(control.name || 'Add the control identity, then map the DRAFT semantics below.')}</div>
            </div>
            <button class="action-button secondary" data-remove-control="${controlIndex}">Remove Control</button>
          </div>
          <div class="editor-subgrid">
            <div class="editor-field">
              <label>Control ID</label>
              <input type="text" value="${escapeHtml(control.controlId || '')}" data-control-field="controlId" data-control-index="${controlIndex}">
            </div>
            <div class="editor-field">
              <label>Friendly Name</label>
              <input type="text" value="${escapeHtml(control.name || '')}" data-control-field="name" data-control-index="${controlIndex}">
            </div>
          </div>
          <div class="editor-field">
            <label>External Reference</label>
            <input type="text" value="${escapeHtml(control.externalReference || '')}" data-control-field="externalReference" data-control-index="${controlIndex}">
          </div>
          <div class="editor-subgrid">
            <div class="editor-field">
              <label>Requirement Mode</label>
              <select data-control-field="requirementMode" data-control-index="${controlIndex}">
                <option value="mandatory" ${control.requirementMode === 'mandatory' ? 'selected' : ''}>Mandatory</option>
                <option value="conditional" ${control.requirementMode === 'conditional' ? 'selected' : ''}>Conditional</option>
              </select>
            </div>
            <div class="editor-field">
              <label>Related Concern</label>
              <select data-control-field="relatedConcern" data-control-index="${controlIndex}">
                ${concernOptions}
              </select>
            </div>
          </div>
          <div class="editor-field">
            <label>Applies To</label>
            <div class="editor-checkbox-grid">
              ${CONTROL_SCOPE_OPTIONS.map(option => controlCheckboxMarkup('appliesTo', controlIndex, option.value, option.label, control.appliesTo)).join('')}
            </div>
          </div>
          <div class="editor-field">
            <label>Valid Answer Types</label>
            <div class="editor-checkbox-grid">
              ${CONTROL_ANSWER_TYPE_OPTIONS.map(option => controlCheckboxMarkup('validAnswerTypes', controlIndex, option.value, option.label, control.validAnswerTypes)).join('')}
            </div>
          </div>
          ${conditional ? `
            <div class="editor-divider"></div>
            <div class="editor-inline-actions">
              <span class="editor-pill">Conditional control / N-A allowed</span>
              <div class="editor-field" style="min-width: 220px;">
                <label>Applicability Group</label>
                <select data-control-field="applicabilityMode" data-control-index="${controlIndex}">
                  <option value="anyOf" ${control.applicabilityMode !== 'allOf' ? 'selected' : ''}>anyOf</option>
                  <option value="allOf" ${control.applicabilityMode === 'allOf' ? 'selected' : ''}>allOf</option>
                </select>
              </div>
              <button class="action-button secondary" data-add-clause="${controlIndex}">Add Rule</button>
            </div>
            <div class="editor-note">Use applicability rules to describe when this control is in scope. Conditional controls automatically allow N/A.</div>
            <div class="editor-form">
              ${(control.applicabilityClauses || []).map((clause, clauseIndex) => applicabilityClauseMarkup(controlIndex, clauseIndex, clause)).join('')}
            </div>
          ` : ''}
        </div>
      `;
    }

    function openControlImporter(object) {
      const framework = sanitizeDetailObject(object);
      controlImportState = {
        objectId: object.id,
        framework,
        controls: Array.isArray(framework.controls) ? framework.controls.map(normalizeFrameworkControl) : [],
        serialized: null
      };

      const renderImporter = () => {
        editorOverlay.innerHTML = `
          <div class="editor-panel">
            <div class="editor-header">
              <div class="editor-title">
                <h3>Import Controls Into ${escapeHtml(object.name)}</h3>
                <p>Import minimal control identity data, answer the DRAFT semantics with constrained options, and download the rebuilt framework YAML. GitHub Pages stays read-only.</p>
              </div>
              <div class="editor-actions">
                ${repoSourceUrl(object) ? `<a class="action-button secondary" href="${escapeHtml(repoSourceUrl(object))}" target="_blank" rel="noreferrer">Open Source On GitHub</a>` : ''}
                <button class="action-button secondary" id="control-import-reset">Reset</button>
                <button class="action-button secondary" id="control-import-close">Close</button>
              </div>
            </div>
            <div class="editor-grid">
              <section class="editor-card">
                <h4>Import Source</h4>
                <div class="editor-help">Paste YAML shaped as a list of controls, a single control object, or <code>controls: [...]</code>. Each imported control only needs <code>controlId</code>, <code>name</code>, and <code>externalReference</code>.</div>
                <div class="editor-field">
                  <label for="control-import-source">Control YAML</label>
                  <textarea id="control-import-source" placeholder="- controlId: 4.4.1&#10;  name: Password Policy&#10;  externalReference: https://example.com/control"></textarea>
                </div>
                <div class="editor-inline-actions">
                  <input type="file" id="control-import-file" accept=".yaml,.yml,text/yaml,text/x-yaml">
                  <button class="action-button" id="control-import-parse">Import YAML</button>
                  <button class="action-button secondary" id="control-import-add">Add Control</button>
                </div>
                <div class="editor-divider"></div>
                <h4>Control Semantics</h4>
                <div class="editor-help">Imported controls keep their identity fields. Use the options below to tell DRAFT where each control applies and how an object can answer it.</div>
                <div id="control-import-list" class="editor-scroll">
                  ${controlImportState.controls.length ? controlImportState.controls.map((control, index) => controlCardMarkup(control, index)).join('') : '<div class="editor-help">No controls loaded yet. Import a YAML file or add one control manually.</div>'}
                </div>
              </section>
              <section class="editor-card">
                <h4>Framework YAML Preview</h4>
                <div class="editor-help">This preview updates as you edit control semantics. Download the result and commit it manually for now.</div>
                <div id="control-import-error" class="editor-error"></div>
                <pre id="control-import-preview" class="yaml-preview"></pre>
                <div class="editor-actions">
                  <button class="action-button" id="control-import-copy">Copy YAML</button>
                  <button class="action-button" id="control-import-download">Download YAML</button>
                </div>
              </section>
            </div>
          </div>
        `;
        editorOverlay.classList.add('open');

        const sourceArea = editorOverlay.querySelector('#control-import-source');
        const fileInput = editorOverlay.querySelector('#control-import-file');
        editorOverlay.querySelector('#control-import-close').addEventListener('click', closeEditor);
        editorOverlay.querySelector('#control-import-reset').addEventListener('click', () => openControlImporter(object));
        editorOverlay.querySelector('#control-import-add').addEventListener('click', () => {
          controlImportState.controls.push(normalizeFrameworkControl({}));
          renderImporter();
        });
        editorOverlay.querySelector('#control-import-parse').addEventListener('click', () => {
          try {
            const imported = parseImportedControlSeed(sourceArea.value);
            controlImportState.controls = mergeImportedControls(controlImportState.controls, imported);
            sourceArea.value = '';
            renderImporter();
          } catch (error) {
            const errorNode = editorOverlay.querySelector('#control-import-error');
            if (errorNode) {
              errorNode.textContent = error instanceof Error ? error.message : String(error);
            }
          }
        });
        fileInput.addEventListener('change', async () => {
          const file = fileInput.files?.[0];
          if (!file) return;
          try {
            const text = await file.text();
            sourceArea.value = text;
            const imported = parseImportedControlSeed(text);
            controlImportState.controls = mergeImportedControls(controlImportState.controls, imported);
            sourceArea.value = '';
            renderImporter();
          } catch (error) {
            const errorNode = editorOverlay.querySelector('#control-import-error');
            if (errorNode) {
              errorNode.textContent = error instanceof Error ? error.message : String(error);
            }
          }
        });
        editorOverlay.querySelector('#control-import-copy').addEventListener('click', async () => {
          if (!controlImportState?.serialized) return;
          const yamlText = jsyaml.dump(controlImportState.serialized, { lineWidth: 100, noRefs: true });
          await navigator.clipboard.writeText(yamlText);
        });
        editorOverlay.querySelector('#control-import-download').addEventListener('click', () => {
          if (!controlImportState?.serialized) return;
          const yamlText = jsyaml.dump(controlImportState.serialized, { lineWidth: 100, noRefs: true });
          const blob = new Blob([yamlText], { type: 'text/yaml;charset=utf-8' });
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = (object.source || `${object.id}.yaml`).split('/').pop();
          document.body.appendChild(link);
          link.click();
          link.remove();
          URL.revokeObjectURL(url);
        });

        editorOverlay.querySelectorAll('[data-control-field]').forEach(input => {
          const eventName = input.tagName === 'SELECT' ? 'change' : 'input';
          input.addEventListener(eventName, () => {
            const controlIndex = Number(input.dataset.controlIndex);
            const field = input.dataset.controlField;
            controlImportState.controls[controlIndex][field] = input.value;
            if (field === 'requirementMode') {
              controlImportState.controls[controlIndex].requirementMode = input.value === 'conditional' ? 'conditional' : 'mandatory';
              renderImporter();
              return;
            }
            updateControlImportPreview(object);
          });
        });

        editorOverlay.querySelectorAll('[data-control-checkbox]').forEach(input => {
          input.addEventListener('change', () => {
            const controlIndex = Number(input.dataset.controlIndex);
            const kind = input.dataset.controlCheckbox;
            const bucket = controlImportState.controls[controlIndex][kind];
            if (input.checked) {
              if (!bucket.includes(input.value)) bucket.push(input.value);
            } else {
              controlImportState.controls[controlIndex][kind] = bucket.filter(value => value !== input.value);
            }
            updateControlImportPreview(object);
          });
        });

        editorOverlay.querySelectorAll('[data-clause-field]').forEach(input => {
          const eventName = input.tagName === 'SELECT' ? 'change' : 'input';
          input.addEventListener(eventName, () => {
            const controlIndex = Number(input.dataset.controlIndex);
            const clauseIndex = Number(input.dataset.clauseIndex);
            const field = input.dataset.clauseField;
            controlImportState.controls[controlIndex].applicabilityClauses[clauseIndex][field] = input.value;
            if (field === 'operator') {
              renderImporter();
              return;
            }
            updateControlImportPreview(object);
          });
        });

        editorOverlay.querySelectorAll('[data-remove-control]').forEach(button => {
          button.addEventListener('click', () => {
            const controlIndex = Number(button.dataset.removeControl);
            controlImportState.controls.splice(controlIndex, 1);
            renderImporter();
          });
        });

        editorOverlay.querySelectorAll('[data-add-clause]').forEach(button => {
          button.addEventListener('click', () => {
            const controlIndex = Number(button.dataset.addClause);
            controlImportState.controls[controlIndex].applicabilityClauses.push(blankApplicabilityClause());
            renderImporter();
          });
        });

        editorOverlay.querySelectorAll('[data-remove-clause]').forEach(button => {
          button.addEventListener('click', () => {
            const controlIndex = Number(button.dataset.removeClause);
            const clauseIndex = Number(button.dataset.removeClauseIndex);
            const clauses = controlImportState.controls[controlIndex].applicabilityClauses;
            clauses.splice(clauseIndex, 1);
            if (!clauses.length) clauses.push(blankApplicabilityClause());
            renderImporter();
          });
        });

        editorOverlay.addEventListener('click', event => {
          if (event.target === editorOverlay) {
            closeEditor();
          }
        }, { once: true });

        updateControlImportPreview(object);
      };

      renderImporter();
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
      const object = objectLookup[currentDetailId];
      if (!object) {
        renderListView();
        return;
      }
      syncHashForDetailView(object.id);
      renderSidebarContent(sidebarMarkup());
      const softwareServiceRunsOn = object.type === 'rbb' && object.serviceCategory === 'product' && object.runsOn ? objectLookup[object.runsOn] : null;
      const detailDiagramSource = softwareServiceRunsOn && softwareServiceRunsOn.type === 'rbb' ? softwareServiceRunsOn : object;
      const headerMarkup = `
        <section class="header-card">
          <div class="header-top">
            <div class="header-title">
              <h2>${escapeHtml(object.name)}</h2>
              <div class="object-id">${escapeHtml(object.id)}</div>
            </div>
            <div class="badges">
              <span class="badge">${escapeHtml(object.typeLabel)}</span>
              ${lifecycleBadge(object.lifecycleStatus)}
              ${catalogBadge(object.catalogStatus)}
            </div>
          </div>
          <div class="header-description">${escapeHtml(object.description || 'No description provided.')}</div>
          <div class="owner-line">
            <span><strong>Owner:</strong> ${escapeHtml(object.owner?.team || 'Unknown')}</span>
            <span><strong>Contact:</strong> ${escapeHtml(object.owner?.contact || 'Unknown')}</span>
            <span><strong>Source:</strong> ${escapeHtml(object.source || 'Generated')}</span>
          </div>
          <div class="header-actions">
            <button class="action-button" id="open-editor-button">Edit In Browser</button>
            ${repoSourceUrl(object) ? `<a class="action-button secondary" href="${escapeHtml(repoSourceUrl(object))}" target="_blank" rel="noreferrer">View Source</a>` : ''}
          </div>
        </section>
      `;

      let detailBody = '';
      if (object.type === 'odc') {
        detailBody = `
          ${headerMarkup}
          ${odcRequirementsMarkup(object)}
          ${usedByMarkup(object)}
        `;
      } else if (object.type === 'compliance_framework') {
        detailBody = `
          ${headerMarkup}
          ${complianceFrameworkDetailMarkup(object)}
          ${usedByMarkup(object)}
        `;
      } else if (object.type === 'ard') {
        detailBody = `
          ${ardDetailMarkup(object)}
          ${usedByMarkup(object)}
        `;
      } else if (object.type === 'rbb' && object.serviceCategory === 'product') {
        const interactionSource = preferredInteractionSource(object, softwareServiceRunsOn);
        const decisionSource = preferredDecisionSource(object, softwareServiceRunsOn);
        detailBody = `
          ${headerMarkup}
          ${productServiceDetailMarkup(object)}
          <section class="middle-grid">
            <div class="section-card">
              <h3>Internal Components</h3>
              <div id="detail-cy"></div>
            </div>
            <div class="section-card">
              <h3>External Interactions</h3>
              ${interactionSource ? interactionMarkup(interactionSource) : '<div class="empty-card">The underlying RBB is not available for this software service.</div>'}
            </div>
          </section>
          <section class="decisions-card">
            <h3>Architectural Decisions</h3>
            ${decisionSource ? decisionMarkup(decisionSource) : '<div class="empty-card">No architectural decisions are available because the underlying RBB is not documented.</div>'}
          </section>
          ${usedByMarkup(object)}
        `;
      } else if (object.type === 'rbb' && object.serviceCategory === 'saas') {
        detailBody = `
          ${headerMarkup}
          ${saasServiceDetailMarkup(object)}
          ${usedByMarkup(object)}
        `;
      } else if (object.type === 'software_distribution_manifest') {
        detailBody = `
          ${headerMarkup}
          <div class="detail-tabs">
            <button class="detail-tab" data-sdm-tab="details">Details</button>
            <button class="detail-tab active" data-sdm-tab="topology">Deployment Topology</button>
          </div>
          <div class="detail-panel" data-sdm-panel="details" hidden>
            <section class="section-card">
              <h3>Applied Pattern</h3>
              <div class="section-stack">
                ${object.appliesPattern && objectLookup[object.appliesPattern]
                  ? `<span class="ard-link" data-object-link="${object.appliesPattern}">${escapeHtml(object.appliesPattern)}</span>`
                  : `<span class="interaction-notes">${escapeHtml(object.appliesPattern || 'No applied reference architecture documented.')}</span>`}
              </div>
            </section>
            ${sdmServiceGroupsMarkup(object)}
            ${sdmRisksMarkup(object)}
            <section class="decisions-card">
              <h3>Architectural Decisions</h3>
            ${object.architecturalDecisions && Object.keys(object.architecturalDecisions).length
                ? `<div class="decisions-grid single"><section class="decision-card"><dl class="definition-list">${Object.entries(object.architecturalDecisions).map(([key, value]) => `<dt>${escapeHtml(key)}</dt><dd>${escapeHtml(Array.isArray(value) ? value.join(', ') : String(value))}</dd>`).join('')}</dl></section></div>`
                : '<div class="empty-card">No architectural decisions are defined for this object.</div>'}
            </section>
          </div>
          <div class="detail-panel" data-sdm-panel="topology">
            <section class="section-card">
              <h3>Deployment Topology</h3>
              <div id="topology-canvas"></div>
            </section>
          </div>
          ${usedByMarkup(object)}
        `;
      } else if (object.type === 'reference_architecture') {
        detailBody = `
          ${headerMarkup}
          <div class="detail-tabs">
            <button class="detail-tab" data-sdm-tab="details">Details</button>
            <button class="detail-tab active" data-sdm-tab="topology">Deployment Pattern</button>
          </div>
          <div class="detail-panel" data-sdm-panel="details" hidden>
            ${sdmServiceGroupsMarkup(object)}
            <section class="decisions-card">
              <h3>Architectural Decisions</h3>
            ${object.architecturalDecisions && Object.keys(object.architecturalDecisions).length
                ? `<div class="decisions-grid single"><section class="decision-card"><dl class="definition-list">${Object.entries(object.architecturalDecisions).map(([key, value]) => `<dt>${escapeHtml(key)}</dt><dd>${escapeHtml(Array.isArray(value) ? value.join(', ') : String(value))}</dd>`).join('')}</dl></section></div>`
                : '<div class="empty-card">No architectural decisions are defined for this object.</div>'}
            </section>
          </div>
          <div class="detail-panel" data-sdm-panel="topology">
            <section class="section-card">
              <h3>Deployment Pattern</h3>
              <div id="topology-canvas"></div>
            </section>
          </div>
          ${usedByMarkup(object)}
        `;
      } else if (object.type === 'abb') {
        detailBody = `
          ${headerMarkup}
          ${abbDetailMarkup(object)}
          ${usedByMarkup(object)}
        `;
      } else if (object.type === 'rbb') {
        detailBody = `
          ${headerMarkup}
          <section class="middle-grid">
            <div class="section-card">
              <h3>Internal Components</h3>
              <div id="detail-cy"></div>
            </div>
            <div class="section-card">
              <h3>External Interactions</h3>
              ${interactionMarkup(object)}
            </div>
          </section>
          ${object.type === 'rbb' ? rbbOdcMarkup(object) : ''}
          ${object.type === 'rbb' ? deploymentConfigurationsMarkup(object) : ''}
          <section class="decisions-card">
            <h3>Architectural Decisions</h3>
            ${decisionMarkup(object)}
          </section>
          ${usedByMarkup(object)}
        `;
      } else {
        detailBody = `
          ${headerMarkup}
          ${genericObjectMarkup(object)}
          ${usedByMarkup(object)}
        `;
      }

      appRoot.innerHTML = `
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
      const openControlImportButton = document.getElementById('open-control-import-button');
      if (openControlImportButton) {
        openControlImportButton.addEventListener('click', () => openControlImporter(object));
      }

      attachTopNavHandlers();
      attachSidebarHandlers();
      attachObjectLinkHandlers(appRoot);
      if (object.type === 'software_distribution_manifest' || object.type === 'reference_architecture') {
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

        appRoot.querySelectorAll('[data-sdm-tab]').forEach(button => {
          button.addEventListener('click', () => {
            const nextTab = button.dataset.sdmTab;
            appRoot.querySelectorAll('[data-sdm-tab]').forEach(tab => {
              tab.classList.toggle('active', tab.dataset.sdmTab === nextTab);
            });
            appRoot.querySelectorAll('[data-sdm-panel]').forEach(panel => {
              panel.hidden = panel.dataset.sdmPanel !== nextTab;
            });
            if (nextTab === 'topology') {
              renderTopologyIntoCanvas();
            }
          });
        });
        renderTopologyIntoCanvas();
      }
      if (!['odc', 'ard', 'software_distribution_manifest', 'compliance_framework'].includes(object.type) && !(object.type === 'abb' && object.subtype === 'appliance') && !(object.type === 'rbb' && object.serviceCategory === 'saas')) {
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
      const nodes = [
        {
          data: {
            id: object.id,
            label: object.name,
            shape: object.shape,
            color: object.color,
            lifecycleStatus: object.lifecycleStatus,
            nodeWidth: object.type === 'abb' || object.type === 'rbb' ? 150 : 140,
            nodeHeight: object.type === 'abb' || object.type === 'rbb' ? 90 : 80,
            textMaxWidth: object.type === 'abb' || object.type === 'rbb' ? 150 : 140
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
        nodes.push({
          data: {
            id: refObject.id,
            label: refObject.name,
            shape: refObject.shape,
            color: refObject.color,
            lifecycleStatus: refObject.lifecycleStatus,
            nodeWidth: refObject.type === 'abb' || refObject.type === 'rbb' ? 140 : 130,
            nodeHeight: refObject.type === 'abb' || refObject.type === 'rbb' ? 84 : 78,
            textMaxWidth: refObject.type === 'abb' || refObject.type === 'rbb' ? 140 : 130
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
              'shape': 'data(shape)',
              'background-color': 'data(color)',
              'border-width': 1,
              'border-color': '334155',
              'color': 'e2e8f0',
              'font-size': 11,
              'text-wrap': 'wrap',
              'text-max-width': 'data(textMaxWidth)',
              'text-valign': 'center',
              'text-halign': 'center',
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
              'line-color': '64748b',
              'target-arrow-color': '64748b',
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

      if (selected.type === 'abb') {
        const parentObjects = inboundCatalogRefs(selected).filter(parent => deployableTypes.has(parent.type));
        parentObjects.forEach(parent => {
          impacted.add(parent.id);
          outboundCatalogRefs(parent).forEach(target => {
            if (target.id !== selected.id && deployableTypes.has(target.type)) {
              siblings.add(target.id);
            }
          });
          traverseUp(parent, new Set([selected.id, parent.id]), impacted);
        });
      } else if (selected.type === 'software_distribution_manifest') {
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
        ? allObjects.filter(object => {
            const haystack = `${object.name} ${object.id}`.toLowerCase();
            return haystack.includes(impactSearchTerm.toLowerCase());
          }).slice(0, 8)
        : [];

      const grouped = groupedImpactObjects(selection);
      const orderedGroups = [...impactOrder.filter(group => grouped[group]?.length), ...Object.keys(grouped).filter(group => !impactOrder.includes(group) && grouped[group]?.length)];
      const hasItems = orderedGroups.length > 0;

      return `
        <aside class="impact-sidebar">
          <div>
            <h3 style="margin:0 0 10px">Impact Analysis</h3>
            <input id="impact-search" class="impact-search" type="text" placeholder="Search by name or ID" value="${escapeHtml(impactSearchTerm)}">
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
            const classes = ['lifecycle-filter-button', active ? 'active' : '', status === 'exit' ? 'exit-filter' : '']
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
            serviceCategory: object.serviceCategory || '',
            lifecycleStatus: object.lifecycleStatus,
            shape: object.type === 'reference_architecture' || object.type === 'software_distribution_manifest' ? 'round-rectangle' : object.shape,
            color: object.color,
            borderStyle: object.type === 'reference_architecture' ? 'dashed' : 'solid',
            nodeWidth: object.type === 'abb' || object.type === 'rbb' ? 145 : 150,
            nodeHeight: object.type === 'abb' || object.type === 'rbb' ? 86 : 92,
            textMaxWidth: object.type === 'abb' || object.type === 'rbb' ? 145 : 150
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
      const order = ['product', 'general', 'saas', 'database'];
      return nodes
        .filter(node => node.data('type') === 'rbb' && node.data('category') === 'service')
        .sort((a, b) => {
          const aCategory = a.data('serviceCategory') || 'other';
          const bCategory = b.data('serviceCategory') || 'other';
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
        addTier(nodeList.filter(node => node.data('type') === 'software_distribution_manifest')),
        addTier(nodeList.filter(node => node.data('type') === 'reference_architecture')),
        addTier(serviceRbbNodesSorted(nodes)),
        addTier(nodeList.filter(node => node.data('type') === 'rbb' && node.data('category') === 'host')
          .sort((a, b) => String(a.data('label') || '').localeCompare(String(b.data('label') || '')))),
        addTier(nodeList.filter(node => node.data('type') === 'abb')
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
              'border-color': '334155',
              'color': 'e2e8f0',
              'font-size': 10,
              'text-wrap': 'wrap',
              'text-max-width': 'data(textMaxWidth)',
              'text-valign': 'center',
              'text-halign': 'center',
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
              'line-color': '64748b',
              'target-arrow-color': '64748b',
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
              'border-color': 'f59e0b',
              'border-width': 4
            }
          },
          {
            selector: 'node.impacted-impact',
            style: {
              'opacity': 1,
              'border-color': 'ef4444',
              'border-width': 3
            }
          },
          {
            selector: 'node.sibling-impact',
            style: {
              'opacity': 1,
              'border-color': '8b5cf6',
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
      syncHashForImpactView();
      const selection = impactSelectedId ? computeImpactSelection(impactSelectedId) : { selected: null, impacted: new Set(), siblings: new Set(), supported: false };
      renderSidebarContent(sidebarMarkup(impactSidebarMarkup(selection)));
      appRoot.innerHTML = `
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
            const firstMatch = allObjects.find(object => `${object.name} ${object.id}`.toLowerCase().includes(impactSearchTerm.toLowerCase()));
            if (firstMatch) {
              runImpactAnalysis(firstMatch.id);
            }
          }
        });
      }
      appRoot.querySelectorAll('[data-impact-select]').forEach(item => {
        item.addEventListener('click', () => {
          selectImpactObject(item.dataset.impactSelect);
        });
        item.addEventListener('dblclick', () => {
          selectImpactObject(item.dataset.impactSelect, true);
        });
      });
      appRoot.querySelectorAll('[data-impact-lifecycle]').forEach(button => {
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


def write_browser(payload: dict[str, Any]) -> None:
    html = HTML_TEMPLATE.replace("__BROWSER_DATA__", json.dumps(payload, default=str))
    OUTPUT_PATH.write_text(html, encoding="utf-8")


def main() -> int:
    registry = load_objects()
    payload = build_browser_payload(registry)
    write_browser(payload)
    for warning in payload.get("warnings", []):
        print(warning, file=sys.stderr)
    print(f"Generated {OUTPUT_PATH.relative_to(REPO_ROOT)} with {len(payload['objects'])} objects.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
