#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "AI_INDEX.md"

FRAMEWORK_ENTRYPOINTS = [
    ("AGENTS.md", "Canonical AI bootstrap instructions for this repository."),
    ("docs/framework/draftsman.md", "Draftsman role, intent routing, and authoring rules."),
    ("docs/framework/overview.md", "Framework concepts and object family overview."),
    ("docs/framework/yaml-schema-reference.md", "Quick map from object families to schemas."),
    ("docs/framework/how-to-add-objects.md", "Practical object authoring workflow."),
    ("docs/framework/odcs.md", "Object Definition Checklist model and validation behavior."),
    ("docs/framework/drafting-sessions.md", "How to persist incomplete authoring work."),
    ("tools/validate.py", "Executable validation for schemas, ODCs, references, and controls."),
]

CATALOG_FOLDERS = [
    "abbs",
    "rbbs",
    "reference-architectures",
    "sdms",
    "product-services",
    "saas-services",
    "ards",
    "compliance-frameworks",
    "compliance-profiles",
    "sessions",
]


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data if isinstance(data, dict) else {}


def oneline(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).replace("\n", " ").strip()
    while "  " in text:
        text = text.replace("  ", " ")
    return text or fallback


def truncate(text: str, limit: int = 120) -> str:
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def yaml_row(path: Path) -> tuple[str, str, str, str, str, str]:
    data = read_yaml(path)
    tags = data.get("tags", [])
    tag_text = ", ".join(str(tag) for tag in tags) if isinstance(tags, list) else ""
    return (
        oneline(data.get("id"), path.stem),
        oneline(data.get("name"), path.stem),
        oneline(data.get("type"), "yaml"),
        tag_text,
        truncate(oneline(data.get("description"), "")),
        rel(path),
    )


def append_table(lines: list[str], headers: list[str], rows: list[tuple[Any, ...]]) -> None:
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join("---" for _ in headers) + "|")
    for row in rows:
        escaped = [str(cell).replace("|", "\\|") for cell in row]
        lines.append("| " + " | ".join(escaped) + " |")


def yaml_files(folder_name: str) -> list[Path]:
    folder = REPO_ROOT / folder_name
    if not folder.exists():
        return []
    return sorted(path for path in folder.rglob("*.yaml") if path.is_file())


def template_files() -> list[Path]:
    folder = REPO_ROOT / "templates"
    if not folder.exists():
        return []
    return sorted(path for path in folder.rglob("*.tmpl") if path.is_file())


def main() -> None:
    lines: list[str] = [
        "# AI Framework Index",
        "",
        "This generated file gives AI assistants a fast map of the DRAFT framework checkout.",
        "It is intentionally framework-first: this upstream repository is a reusable template,",
        "not a complete company architecture catalog. Organization-specific architecture content",
        "belongs in downstream private clones.",
        "",
        "Regenerate with:",
        "",
        "```bash",
        "python3 tools/generate_ai_index.py",
        "```",
        "",
        "## Draftsman Bootstrap",
        "",
        "When a user says \"I need a draftsman\", the AI should immediately assume the",
        "Draftsman role defined in `docs/framework/draftsman.md`, then use this index,",
        "`schemas/`, and `odcs/` to guide the conversation and edits.",
        "",
        "## Framework Entrypoints",
        "",
    ]

    append_table(
        lines,
        ["Path", "Purpose"],
        [(path, purpose) for path, purpose in FRAMEWORK_ENTRYPOINTS if (REPO_ROOT / path).exists()],
    )

    lines.extend(["", "## Framework Docs", ""])
    doc_rows = []
    docs_dir = REPO_ROOT / "docs" / "framework"
    if docs_dir.exists():
        for path in sorted(docs_dir.glob("*.md")):
            doc_rows.append((rel(path), markdown_title(path), markdown_summary(path)))
    append_table(lines, ["Path", "Title", "Summary"], doc_rows)

    lines.extend(["", "## Schemas", ""])
    schema_rows = []
    for path in sorted((REPO_ROOT / "schemas").glob("*.yaml")):
        data = read_yaml(path)
        scope = data.get("type", path.stem)
        if data.get("category"):
            scope = f"{scope}.{data.get('category')}"
        if data.get("serviceCategory"):
            scope = f"{scope}.{data.get('serviceCategory')}"
        if data.get("subtype"):
            scope = f"{scope}.{data.get('subtype')}"
        schema_rows.append((rel(path), scope, ", ".join(data.get("requiredFields", []) or [])))
    append_table(lines, ["Path", "Scope", "Required Fields"], schema_rows)

    lines.extend(["", "## Object Definition Checklists", ""])
    odc_rows = [yaml_row(path) for path in yaml_files("odcs")]
    append_table(lines, ["ID", "Name", "Type", "Tags", "Description", "Path"], odc_rows)

    lines.extend(["", "## Current YAML Inventory", ""])
    lines.append(
        "These are the YAML objects present in this checkout. In the upstream framework repo, "
        "this inventory is framework seed material, not a company-specific architecture catalog."
    )
    lines.append("")
    inventory_rows = []
    for folder_name in CATALOG_FOLDERS:
        for path in yaml_files(folder_name):
            inventory_rows.append(yaml_row(path))
    if inventory_rows:
        append_table(lines, ["ID", "Name", "Type", "Tags", "Description", "Path"], inventory_rows)
    else:
        lines.append("No YAML catalog objects are present in this checkout yet.")

    lines.extend(["", "## Content Folder Counts", ""])
    append_table(
        lines,
        ["Folder", "YAML Count"],
        [(folder_name, len(yaml_files(folder_name))) for folder_name in CATALOG_FOLDERS],
    )

    lines.extend(["", "## Templates", ""])
    templates = template_files()
    if templates:
        append_table(
            lines,
            ["Path", "Purpose"],
            [(rel(path), oneline(first_comment(path), "Reusable YAML authoring template.")) for path in templates],
        )
    else:
        lines.append("No templates are present in this checkout yet.")

    lines.extend(["", "## Validation", "", "- Validate catalog objects: `python3 tools/validate.py`"])
    if (REPO_ROOT / "tools" / "generate_browser.py").exists():
        lines.append("- Regenerate browser after YAML changes: `python3 tools/generate_browser.py`")
    lines.append("- Regenerate this index after framework or YAML changes: `python3 tools/generate_ai_index.py`")
    lines.append("")

    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"{rel(OUTPUT_PATH)} generated successfully.")


def first_comment(path: Path) -> str:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()
            if stripped:
                return ""
    return ""


def markdown_title(path: Path) -> str:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped.lstrip("#").strip()
    return path.stem.replace("-", " ").title()


def markdown_summary(path: Path) -> str:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            return truncate(stripped, 120)
    return ""


if __name__ == "__main__":
    main()
