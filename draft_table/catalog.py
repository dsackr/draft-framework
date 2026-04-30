from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .paths import REPO_ROOT


CATALOG_FOLDERS = (
    "abbs",
    "ards",
    "compliance-frameworks",
    "compliance-profiles",
    "domains",
    "object-patches",
    "odc-overrides",
    "odcs",
    "reference-architectures",
    "rbbs",
    "sdms",
    "sessions",
)

REFERENCE_KEYS = {
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
    "primaryObjectId",
    "riskRef",
    "framework",
    "target",
}

ID_PREFIXES = (
    "abb.",
    "ard.",
    "framework.",
    "odc.",
    "paas.",
    "patch.",
    "profile.",
    "ra.",
    "rbb.",
    "saas.",
    "sdm.",
    "session.",
)


def load_effective_catalog(workspace: Path | None, framework_repo: Path = REPO_ROOT) -> dict[str, dict[str, Any]]:
    objects: dict[str, dict[str, Any]] = {}
    roots = [framework_repo / "framework" / "configurations"]
    if workspace and workspace.exists():
        workspace_config = workspace / "configurations"
        workspace_catalog = workspace / "catalog"
        if workspace_config.exists():
            roots.append(workspace_config)
        if workspace_catalog.exists():
            roots.append(workspace_catalog)
        elif workspace.name == "catalog":
            roots.append(workspace)
    else:
        roots.append(framework_repo / "examples" / "catalog")

    for root in roots:
        for path in discover_yaml_files(root):
            data = read_yaml(path)
            object_id = data.get("id")
            if object_id:
                data["_source"] = display_path(path, framework_repo)
                objects[str(object_id)] = data
    return apply_object_patches(objects)


def discover_yaml_files(root: Path) -> list[Path]:
    files: list[Path] = []
    if not root.exists():
        return files
    for folder in CATALOG_FOLDERS:
        folder_path = root / folder
        if folder_path.exists():
            files.extend(sorted(folder_path.rglob("*.yaml")))
    if root.name in {"catalog", "configurations"}:
        files.extend(path for path in sorted(root.glob("*.yaml")) if path.is_file())
    return sorted(set(files))


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def display_path(path: Path, framework_repo: Path) -> str:
    for root in (framework_repo, Path.cwd()):
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            continue
    return path.as_posix()


def apply_object_patches(objects: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    patched = dict(objects)
    for obj in objects.values():
        if obj.get("type") != "object_patch":
            continue
        target = str(obj.get("target") or "")
        patch = obj.get("patch")
        if target in patched and isinstance(patch, dict):
            patched[target] = deep_merge(patched[target], patch)
    return patched


def deep_merge(base: Any, patch: Any) -> Any:
    if isinstance(base, dict) and isinstance(patch, dict):
        merged = dict(base)
        for key, value in patch.items():
            if key in {"id", "type"}:
                continue
            merged[key] = deep_merge(merged.get(key), value)
        return merged
    return patch


def build_reference_index(objects: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    referenced_by: dict[str, list[dict[str, str]]] = {}
    for object_id, obj in objects.items():
        for target, ref_path in extract_refs(obj):
            referenced_by.setdefault(target, []).append({"source": object_id, "path": ref_path})
    return referenced_by


def extract_refs(node: Any, path: str = "") -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            child_path = f"{path}.{key}" if path else key
            if key in REFERENCE_KEYS and isinstance(value, str) and value.startswith(ID_PREFIXES):
                refs.append((value, child_path))
            elif key.endswith("Refs") and isinstance(value, list):
                for index, item in enumerate(value):
                    if isinstance(item, str) and item.startswith(ID_PREFIXES):
                        refs.append((item, f"{child_path}[{index}]"))
            else:
                refs.extend(extract_refs(value, child_path))
    elif isinstance(node, list):
        if path.endswith(".appliesTo"):
            return refs
        for index, item in enumerate(node):
            if isinstance(item, str) and item.startswith(ID_PREFIXES):
                refs.append((item, f"{path}[{index}]"))
            else:
                refs.extend(extract_refs(item, f"{path}[{index}]"))
    return refs


def search_objects(objects: dict[str, dict[str, Any]], query: str, limit: int = 8) -> list[dict[str, Any]]:
    tokens = tokenize(query)
    scored: list[tuple[int, dict[str, Any]]] = []
    for obj in objects.values():
        haystack = " ".join(
            str(value)
            for value in (
                obj.get("id", ""),
                obj.get("name", ""),
                obj.get("type", ""),
                obj.get("description", ""),
                " ".join(str(tag) for tag in obj.get("tags", []) if isinstance(obj.get("tags"), list)),
            )
        ).lower()
        score = sum(1 for token in tokens if token in haystack)
        if score:
            scored.append((score, obj))
    return [obj for _score, obj in sorted(scored, key=lambda item: (-item[0], item[1].get("id", "")))[:limit]]


def tokenize(text: str) -> list[str]:
    return [token for token in "".join(ch.lower() if ch.isalnum() else " " for ch in text).split() if len(token) > 2]


def object_summary(obj: dict[str, Any]) -> dict[str, str]:
    return {
        "id": str(obj.get("id", "")),
        "name": str(obj.get("name", obj.get("id", ""))),
        "type": str(obj.get("type", "")),
        "status": str(obj.get("catalogStatus", "")),
        "source": str(obj.get("_source", "")),
        "description": str(obj.get("description", "")).strip(),
    }
