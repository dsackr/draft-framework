![DRAFT Logo](./draftlogo.png)

# Deployable Reference Architecture Framework Toolkit (DRAFT)

> [!IMPORTANT]
> **AI Assistants / Agents:** You are expected to act as **The Draftsman**.
> Before proceeding, read [AGENTS.md](AGENTS.md), then the
> [Draftsman Instructions](framework/docs/draftsman.md). Proactively offer to
> start a [Drafting Session](framework/docs/drafting-sessions.md) when assisting
> a user.

DRAFT is an AI-first, YAML-first framework for documenting deployable
architecture. It provides schemas, base configuration, authoring guidance,
examples, validation tooling, and a generated static GitHub Pages browser.

This repository is the public framework. Company-specific architecture content
and configuration belong in downstream private workspace repositories.

## AI-First Setup

- [AGENTS.md](AGENTS.md) is the canonical bootstrap for AI agents.
- [AI_INDEX.md](AI_INDEX.md) is a generated map of framework docs, schemas,
  base configurations, templates, and example YAML in the current checkout.
- [GEMINI.md](GEMINI.md), [CLAUDE.md](CLAUDE.md), and
  [.github/copilot-instructions.md](.github/copilot-instructions.md) are thin
  provider-specific pointers back to `AGENTS.md`.
- [llms.txt](llms.txt) exposes the same entry points in a lightweight,
  web-friendly form.

When a user connected to this repo says "I need a draftsman", the AI should
immediately assume the Draftsman role and guide the user through creating,
updating, or validating DRAFT artifacts.

## Repository Layout

```text
framework/              # Core schemas, tools, docs, and base configurations
framework/configurations/
                        # Base ODCs, compliance frameworks, profiles, domains
examples/catalog/       # Sample content used to validate and demo the framework
templates/              # Object and private workspace templates
docs/index.html         # Generated static browser for the example workspace
```

A company private workspace should use this shape:

```text
catalog/                # Company architecture content
configurations/         # Company ODC, compliance, domain, and patch overlays
configurations/object-patches/
                        # Patch objects for framework or catalog overrides
.draft/workspace.yaml   # Optional tracked workspace metadata
.draft/framework.lock   # Optional tracked framework pin
```

The effective model is resolved by reading framework base configuration first,
then workspace configuration overlays, then workspace catalog content.

## Start Here

### Framework Basics

- [Framework overview](framework/docs/overview.md)
- [AI agent bootstrap](AGENTS.md)
- [AI framework index](AI_INDEX.md)
- [Draftsman instructions for AI](framework/docs/draftsman.md)
- [Draftsman AI guidance](framework/docs/draftsman-ai-configuration.md)
- [YAML schema reference](framework/docs/yaml-schema-reference.md)
- [Naming conventions](framework/docs/naming-conventions.md)
- [How to add objects](framework/docs/how-to-add-objects.md)
- [Workspace model](framework/docs/workspaces.md)
- [Authoring templates](templates/)

### Architecture Content

- [Reference Building Blocks (RBBs)](framework/docs/rbbs.md)
- [Reference Architectures (RAs)](framework/docs/reference-architectures.md)
- [Software Distribution Manifests (SDMs)](framework/docs/software-distribution-manifests.md)

### RBB Classifications

- [Product Service](framework/docs/product-service.md)
- [PaaS Service](framework/docs/paas-services.md)
- [SaaS Service](framework/docs/saas-services.md)

### Supporting Model Objects

- [Architecture Building Blocks (ABBs)](framework/docs/abbs.md)
- [Deployment Risks and Decisions (DRDs)](framework/docs/deployment-risks-and-decisions.md)
- [Drafting Sessions](framework/docs/drafting-sessions.md)

### Extensible Framework Content

- [Object Definition Checklists (ODCs)](framework/docs/odcs.md)
- [Security and Compliance Controls (SCCs)](framework/docs/security-and-compliance-controls.md)

## Validate And Generate

Install the only runtime dependency used by the framework tools:

```bash
python3 -m pip install pyyaml
```

Validate the framework base configuration and example catalog:

```bash
python3 framework/tools/validate.py
```

Validate a private workspace:

```bash
python3 framework/tools/validate.py --workspace /path/to/company-draft-workspace
```

Regenerate the static browser and AI index after YAML, docs, schema, or template
changes:

```bash
python3 framework/tools/generate_browser.py
python3 framework/tools/generate_ai_index.py
```

## Compliance Claims

Architecture artifacts declare framework compliance explicitly with
`complianceProfiles`. When a profile is declared, every applicable control from
that profile must have a valid `controlImplementations` entry or validation
fails.

Artifacts without a declared profile are unclaimed inventory. They are not
labeled non-compliant, but they should not be treated as compliant
off-the-shelf building blocks for solutions that require that framework.

## Catalog Browsing

The generated static browser is published at:

[https://dsackr.github.io/draft-framework/](https://dsackr.github.io/draft-framework/)

GitHub Pages is read-only. It is generated from `framework/configurations/` and
`examples/catalog/` by `framework/tools/generate_browser.py`.
