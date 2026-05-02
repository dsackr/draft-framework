#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "draft-framework.yaml"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
ENTRY_RE = re.compile(
    r"^##\s+\[?(Unreleased|v?\d+\.\d+\.\d+)\]?(?:\s+-\s+(\d{4}-\d{2}-\d{2}))?\s*$",
    re.MULTILINE,
)
SECTION_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
PLACEHOLDER_RE = re.compile(r"^(tbd|todo|n/a|none|not applicable|no notes)\.?$", re.IGNORECASE)

REQUIRED_RELEASE_SECTIONS = (
    "Compatibility Impact",
    "Added",
    "Changed",
    "Fixed",
    "Migration Notes",
)

GOVERNED_PATHS = (
    ".github/workflows/",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "README.md",
    "llms.txt",
    "security.md",
    "install-draft-table.sh",
    "pyproject.toml",
    "draft-framework.yaml",
    "draft_table/",
    "framework/configurations/",
    "framework/docs/",
    "framework/schemas/",
    "framework/tools/",
    "templates/",
)

CONTRACT_PATHS = (
    "framework/configurations/compliance-controls/",
    "framework/configurations/control-enforcement-profiles/",
    "framework/configurations/definition-checklists/",
    "framework/schemas/",
    "framework/tools/validate.py",
)

RELEASE_GOVERNANCE_PATHS = {
    ".github/pull_request_template.md",
    "CHANGELOG.md",
    "RELEASE.md",
    "VERSIONING.md",
    "docs/index.html",
    "AI_INDEX.md",
}


@dataclass(frozen=True)
class Version:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> "Version":
        if not VERSION_RE.match(value):
            raise ValueError(f"Invalid semantic version: {value}")
        major, minor, patch = (int(part) for part in value.split("."))
        return cls(major, minor, patch)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain a YAML mapping")
    return data


def manifest_version(path: Path = MANIFEST_PATH) -> Version:
    data = load_manifest(path)
    return Version.parse(str(data.get("version", "")).strip())


def manifest_version_at(ref: str) -> Version | None:
    if not ref or set(ref) == {"0"}:
        return None
    result = run_git(["show", f"{ref}:draft-framework.yaml"])
    if result.returncode != 0:
        return None
    data = yaml.safe_load(result.stdout) or {}
    if not isinstance(data, dict) or not data.get("version"):
        return None
    return Version.parse(str(data["version"]).strip())


def normalize_entry_key(value: str) -> str:
    key = value.strip()
    if key.lower() == "unreleased":
        return "Unreleased"
    if key.startswith("v") and VERSION_RE.match(key[1:]):
        return key[1:]
    return key


def parse_changelog(text: str) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    matches = list(ENTRY_RE.finditer(text))
    for index, match in enumerate(matches):
        key = normalize_entry_key(match.group(1))
        body_start = match.end()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()
        entries[key] = {
            "date": match.group(2) or "",
            "body": body,
            "sections": parse_sections(body),
        }
    return entries


def parse_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    matches = list(SECTION_RE.finditer(text))
    for index, match in enumerate(matches):
        name = match.group(1).strip()
        body_start = match.end()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[name] = text[body_start:body_end].strip()
    return sections


def meaningful_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        line = line.removeprefix("-").strip()
        if line:
            lines.append(line)
    return lines


def is_meaningful(text: str) -> bool:
    lines = meaningful_lines(text)
    if not lines:
        return False
    return any(not PLACEHOLDER_RE.match(line) for line in lines)


def validate_release_entry(version: Version, entries: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    key = str(version)
    entry = entries.get(key)
    if not entry:
        return [f"CHANGELOG.md is missing a release entry for {key}."]

    sections = entry["sections"]
    for section in REQUIRED_RELEASE_SECTIONS:
        if section not in sections:
            errors.append(f"CHANGELOG.md {key} is missing section: {section}.")

    compatibility = sections.get("Compatibility Impact", "")
    if not is_meaningful(compatibility):
        errors.append(f"CHANGELOG.md {key} has an empty or placeholder Compatibility Impact.")

    migration = sections.get("Migration Notes", "")
    if not is_meaningful(migration):
        errors.append(f"CHANGELOG.md {key} has empty or placeholder Migration Notes.")

    change_sections = [
        sections.get("Added", ""),
        sections.get("Changed", ""),
        sections.get("Fixed", ""),
    ]
    if not any(is_meaningful(section) for section in change_sections):
        errors.append(f"CHANGELOG.md {key} must describe at least one added, changed, or fixed item.")

    return errors


def validate_change_notes(entry_key: str, entries: dict[str, dict[str, Any]], require_migration: bool) -> list[str]:
    errors: list[str] = []
    entry = entries.get(entry_key)
    if not entry:
        return [f"CHANGELOG.md is missing a {entry_key} section for the changed files."]

    sections = entry.get("sections", {})
    if not is_meaningful(sections.get("Compatibility Impact", "")):
        errors.append(f"CHANGELOG.md {entry_key} needs a meaningful Compatibility Impact.")

    change_sections = [
        sections.get("Added", ""),
        sections.get("Changed", ""),
        sections.get("Fixed", ""),
    ]
    if not any(is_meaningful(section) for section in change_sections):
        errors.append(f"CHANGELOG.md {entry_key} needs at least one meaningful Added, Changed, or Fixed note.")

    if require_migration and not is_meaningful(sections.get("Migration Notes", "")):
        errors.append(f"CHANGELOG.md {entry_key} needs meaningful Migration Notes for contract changes.")

    return errors


def changed_files(base: str | None, head: str | None) -> list[str]:
    if not base or not head or set(base) == {"0"}:
        return []
    result = run_git(["diff", "--name-only", base, head])
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def is_governed_change(path: str) -> bool:
    if path in RELEASE_GOVERNANCE_PATHS:
        return False
    return path.startswith(GOVERNED_PATHS) or path in GOVERNED_PATHS


def is_contract_change(path: str) -> bool:
    return path.startswith(CONTRACT_PATHS) or path in CONTRACT_PATHS


def validate_changed_files(
    files: list[str],
    current_version: Version,
    entries: dict[str, dict[str, Any]],
    old_version: Version | None,
) -> list[str]:
    errors: list[str] = []
    governed = [path for path in files if is_governed_change(path)]
    contract = [path for path in files if is_contract_change(path)]
    version_changed = old_version is not None and old_version != current_version
    change_entry_key = str(current_version) if version_changed or "draft-framework.yaml" in files else "Unreleased"

    if governed and "CHANGELOG.md" not in files:
        errors.append("Framework-governed files changed, but CHANGELOG.md was not updated.")

    if governed and "CHANGELOG.md" in files:
        errors.extend(validate_change_notes(change_entry_key, entries, bool(contract)))

    if (
        old_version
        and old_version != current_version
        and old_version.major == current_version.major
        and old_version.minor == current_version.minor
        and current_version.patch > old_version.patch
        and contract
    ):
        errors.append("Patch releases must not include schema, requirement group, capability, or validation contract changes.")

    return errors


def validate_tag(tag: str | None, current_version: Version) -> list[str]:
    if not tag:
        return []
    expected = f"v{current_version}"
    if tag != expected:
        return [f"Release tag {tag} does not match draft-framework.yaml version {expected}."]
    return []


def validate(base: str | None = None, head: str | None = None, tag: str | None = None) -> list[str]:
    errors: list[str] = []
    current_version = manifest_version()
    entries = parse_changelog(CHANGELOG_PATH.read_text(encoding="utf-8"))
    errors.extend(validate_release_entry(current_version, entries))
    files = changed_files(base, head)
    old_version = manifest_version_at(base or "") if base else None
    errors.extend(validate_changed_files(files, current_version, entries, old_version))
    errors.extend(validate_tag(tag, current_version))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate DRAFT release notes and version metadata.")
    parser.add_argument("--base", default="", help="Base git ref for changed-file checks.")
    parser.add_argument("--head", default="HEAD", help="Head git ref for changed-file checks.")
    parser.add_argument("--tag", default="", help="Optional release tag to compare with draft-framework.yaml.")
    args = parser.parse_args()

    errors = validate(args.base, args.head, args.tag)
    if errors:
        print("Release note validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Release note validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
