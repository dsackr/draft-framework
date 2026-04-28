# AI Agent Instructions

This repository is AI-first. Any AI assistant connected to this repo should use
this file as the bootstrap contract before answering framework or catalog
authoring requests.

## Immediate Bootstrap

1. Read [framework/docs/draftsman.md](framework/docs/draftsman.md).
2. Read [AI_INDEX.md](AI_INDEX.md) to understand the current framework index,
   available schemas, base configurations, templates, and example YAML.
3. Use [framework/schemas/](framework/schemas/) as the authoritative object
   contract.
4. Use [framework/configurations/](framework/configurations/) as the
   authoritative base checklist, compliance, and domain model.
5. Validate changes with `python3 framework/tools/validate.py`.

## Draftsman Activation

When the user says "I need a draftsman", "act as draftsman", or asks to build
or update DRAFT architecture content, immediately assume the Draftsman role
defined in [framework/docs/draftsman.md](framework/docs/draftsman.md).

Do not ask what "draftsman" means. In this repo, it means:

- resolve the user's intent
- search the effective catalog inventory first
- read the matching schema and ODC
- interview the user only for missing architecture facts
- create or update valid YAML through the app/API contract when possible
- preserve unresolved uncertainty in a Drafting Session when needed

## Repository Mode

This upstream repository is the DRAFT framework and app runtime. It includes
framework base configurations, schemas, examples, templates, and the shared
API/UI skeleton. It is not a complete company architecture catalog.

Company-specific artifacts belong in a private workspace repository:

- `catalog/` for architecture content
- `configurations/` for ODC, compliance, object-type, domain, and automation
  overlays
- `.draft/` for tracked workspace configuration and framework pins

Use `examples/catalog/` only as sample content for validating and demonstrating
the framework.

## Source Of Truth Order

When sources disagree, follow this order:

1. Schema files in `framework/schemas/`
2. Framework base configuration in `framework/configurations/`
3. Company workspace configuration in `configurations/`
4. Company workspace catalog content in `catalog/`
5. Framework documentation in `framework/docs/`
6. Generated indexes and browser output

## AI Agent Contract

AI agents should treat DRAFT as a deterministic authoring system:

- Load the effective model: framework base + workspace configurations +
  workspace catalog.
- Use schemas and ODCs to determine required facts.
- Propose object or configuration changes through the app/API contract.
- Run validation before committing.
- Preserve unresolved facts in Drafting Sessions.
- Prefer deployable architecture facts that can later inform automation.

## Compliance Claims

Treat `complianceProfiles` on an artifact as the explicit compliance claim.
`controlImplementations` are evidence for declared profiles only. If a profile
is not declared, the artifact is not non-compliant; it is simply not eligible
as compliant off-the-shelf inventory for that framework.

## Editing Rules

- Keep generated files current by running `python3 framework/tools/generate_ai_index.py`
  when framework docs, schemas, ODCs, templates, or catalog YAML changes.
- Regenerate the browser with `python3 framework/tools/generate_browser.py` when YAML
  catalog content changes.
- Do not invent new object types, fields, lifecycle states, or taxonomy values
  unless the schemas and docs are updated deliberately.
- Prefer framework templates in [templates/](templates/) when creating new
  objects.
