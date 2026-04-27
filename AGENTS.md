# AI Agent Instructions

This repository is AI-first. Any AI assistant connected to this repo should use
this file as the bootstrap contract before answering framework or catalog
authoring requests.

## Immediate Bootstrap

1. Read [docs/framework/draftsman.md](docs/framework/draftsman.md).
2. Read [AI_INDEX.md](AI_INDEX.md) to understand the current framework index,
   available schemas, ODCs, templates, and any YAML objects in this checkout.
3. Use [schemas/](schemas/) as the authoritative object contract.
4. Use [odcs/](odcs/) as the authoritative checklist and interview model.
5. Validate changes with `python3 tools/validate.py`.

## Draftsman Activation

When the user says "I need a draftsman", "act as draftsman", or asks to build
or update DRAFT architecture content, immediately assume the Draftsman role
defined in [docs/framework/draftsman.md](docs/framework/draftsman.md).

Do not ask what "draftsman" means. In this repo, it means:

- resolve the user's intent
- search the current catalog inventory first
- read the matching schema and ODC
- interview the user only for missing architecture facts
- create or update valid YAML
- preserve unresolved uncertainty in a Drafting Session when needed

## Repository Mode

This upstream repository is the DRAFT framework template. It may include
framework seed objects, ODCs, schemas, examples, and templates, but it should not
be treated as a complete company architecture catalog.

Downstream company clones are expected to add organization-specific artifacts in
folders such as `abbs/`, `rbbs/`, `reference-architectures/`, `sdms/`, `ards/`,
`compliance-frameworks/`, and `compliance-profiles/`.

If a folder is empty in this upstream repo, that is not a gap in the framework.
Use `AI_INDEX.md` to determine what exists in the current checkout.

## Source Of Truth Order

When sources disagree, follow this order:

1. Schema files in `schemas/`
2. Current YAML objects in this checkout
3. ODC files in `odcs/`
4. Framework documentation in `docs/framework/`
5. Generated indexes and browser output

## Editing Rules

- Keep generated files current by running `python3 tools/generate_ai_index.py`
  when framework docs, schemas, ODCs, templates, or catalog YAML changes.
- Regenerate the browser with `python3 tools/generate_browser.py` when YAML
  catalog content changes.
- Do not invent new object types, fields, lifecycle states, or taxonomy values
  unless the schemas and docs are updated deliberately.
- Prefer framework templates in [templates/](templates/) when creating new
  objects.
