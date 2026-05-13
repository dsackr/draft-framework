#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


DEFAULT_FILES = {
    "deploymentTargets": "deployment-targets.yaml",
    "dataClassificationLevels": "data-classification-levels.yaml",
    "teams": "teams.yaml",
    "availabilityTiers": "availability-tiers.yaml",
    "failureDomains": "failure-domains.yaml",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize DRAFT vocabulary_proposal files into reviewable vocabulary entries."
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Workspace root containing .draft/workspace.yaml and configurations/.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report proposed changes without writing vocabulary files.",
    )
    return parser.parse_args()


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def workspace_vocabulary_config(workspace_root: Path) -> dict[str, Any]:
    workspace_config = load_yaml(workspace_root / ".draft" / "workspace.yaml")
    vocabulary = workspace_config.get("vocabulary") or {}
    return vocabulary if isinstance(vocabulary, dict) else {}


def target_path_for(workspace_root: Path, vocabulary_key: str, vocabulary_config: dict[str, Any]) -> Path:
    raw_config = vocabulary_config.get(vocabulary_key)
    source = raw_config.get("source") if isinstance(raw_config, dict) else None
    if source:
        path = Path(str(source))
        return path if path.is_absolute() else workspace_root / path
    return workspace_root / "configurations" / "vocabulary" / DEFAULT_FILES[vocabulary_key]


def proposal_files(workspace_root: Path) -> list[Path]:
    roots = [
        workspace_root / "configurations" / "vocabulary-proposals",
        workspace_root / "catalog" / "vocabulary-proposals",
    ]
    files: list[Path] = []
    for root in roots:
        if root.exists():
            files.extend(sorted(root.rglob("*.yaml")))
    return files


def proposal_entry(proposal: dict[str, Any]) -> dict[str, Any]:
    proposed_id = str(proposal.get("proposedId") or "").strip()
    proposed_name = str(proposal.get("proposedName") or proposed_id).strip()
    entry = proposal.get("entry") if isinstance(proposal.get("entry"), dict) else {}
    value: dict[str, Any] = {**entry}
    value["id"] = proposed_id
    value["name"] = proposed_name
    value["status"] = "proposed"
    if proposal.get("description") and "description" not in value:
        value["description"] = proposal["description"]
    if proposal.get("notes") and "notes" not in value:
        value["notes"] = proposal["notes"]
    if proposal.get("rationale") and "rationale" not in value:
        value["rationale"] = proposal["rationale"]
    return value


def ensure_vocabulary_document(data: dict[str, Any], vocabulary_key: str, path: Path) -> dict[str, Any]:
    if data:
        values = data.get("values")
        if not isinstance(values, list):
            data["values"] = []
        data.setdefault("schemaVersion", "1.0")
        data.setdefault("type", "vocabulary")
        data.setdefault("vocabulary", vocabulary_key)
        data.setdefault("name", path.stem.replace("-", " ").title())
        return data
    return {
        "schemaVersion": "1.0",
        "type": "vocabulary",
        "vocabulary": vocabulary_key,
        "name": path.stem.replace("-", " ").title(),
        "values": [],
    }


def main() -> int:
    args = parse_args()
    workspace_root = args.workspace.resolve()
    vocabulary_config = workspace_vocabulary_config(workspace_root)
    changed_paths: set[Path] = set()
    skipped = 0

    for proposal_path in proposal_files(workspace_root):
        proposal = load_yaml(proposal_path)
        if proposal.get("type") != "vocabulary_proposal":
            continue
        status = str(proposal.get("status") or "proposed")
        if status not in {"draft", "proposed", "submitted"}:
            skipped += 1
            continue
        vocabulary_key = str(proposal.get("vocabulary") or "").strip()
        proposed_id = str(proposal.get("proposedId") or "").strip()
        if vocabulary_key not in DEFAULT_FILES or not proposed_id:
            skipped += 1
            continue

        target_path = target_path_for(workspace_root, vocabulary_key, vocabulary_config)
        document = ensure_vocabulary_document(load_yaml(target_path), vocabulary_key, target_path)
        values = document["values"]
        existing_ids = {str(value.get("id") or "").strip() for value in values if isinstance(value, dict)}
        if proposed_id in existing_ids:
            skipped += 1
            continue
        values.append(proposal_entry(proposal))
        changed_paths.add(target_path)
        if not args.dry_run:
            dump_yaml(target_path, document)
        print(f"Added proposed {vocabulary_key} value '{proposed_id}' to {target_path}")

    if not changed_paths:
        print(f"No vocabulary proposal changes applied. Skipped {skipped} proposal(s).")
        return 0
    print(f"Prepared {len(changed_paths)} vocabulary file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
