from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

from .paths import DEFAULT_CONFIG_PATH, REPO_ROOT


SECRET_KEY_PARTS = (
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "id_token",
    "client_secret",
    "password",
    "secret",
    "token",
)

DEFAULT_CONFIG: dict[str, Any] = {
    "framework_repo_path": str(REPO_ROOT),
    "content_repo_path": "",
    "provider": {
        "type": "",
        "executable": "",
        "model": "",
        "endpoint": "",
    },
    "preferences": {
        "host": "127.0.0.1",
        "port": 0,
    },
}


def config_path(path: Path | None = None) -> Path:
    return (path or DEFAULT_CONFIG_PATH).expanduser()


def load_config(path: Path | None = None) -> dict[str, Any]:
    target = config_path(path)
    if not target.exists():
        return copy.deepcopy(DEFAULT_CONFIG)
    with target.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config file must contain a mapping: {target}")
    merged = copy.deepcopy(DEFAULT_CONFIG)
    deep_update(merged, data)
    if not (Path(str(merged.get("framework_repo_path") or "")) / "framework" / "tools" / "validate.py").exists():
        merged["framework_repo_path"] = str(REPO_ROOT)
    return merged


def save_config(config: dict[str, Any], path: Path | None = None) -> Path:
    target = config_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    safe_config = strip_unknown_secret_values(config)
    with target.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(safe_config, handle, sort_keys=False, allow_unicode=False)
    try:
        target.chmod(0o600)
    except OSError:
        pass
    return target


def deep_update(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_update(base[key], value)
        else:
            base[key] = value
    return base


def is_secret_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in SECRET_KEY_PARTS)


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if is_secret_key(str(key)) else redact(child)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def strip_unknown_secret_values(config: dict[str, Any]) -> dict[str, Any]:
    cleaned = copy.deepcopy(config)
    remove_secret_keys(cleaned)
    return cleaned


def remove_secret_keys(node: Any) -> None:
    if isinstance(node, dict):
        for key in list(node.keys()):
            if is_secret_key(str(key)):
                node.pop(key)
            else:
                remove_secret_keys(node[key])
    elif isinstance(node, list):
        for item in node:
            remove_secret_keys(item)


def redacted_yaml(config: dict[str, Any]) -> str:
    return yaml.safe_dump(redact(config), sort_keys=False, allow_unicode=False)
