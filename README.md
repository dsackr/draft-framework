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

This repository is the upstream framework. Company implementations should keep
a vendored framework copy inside their private DRAFT repo so normal Draftsman
use does not depend on reaching back to the public repo.

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
                        # Base Definition Checklists, Compliance Controls, Control Enforcement Profiles, domains
examples/catalog/       # Sample content used to validate and demo the framework
templates/              # Object and company repo templates
docs/index.html         # Generated static browser for the example workspace
draft_table/            # Local-first DRAFT Table CLI and web shell
```

A company private DRAFT repo should use this shape:

```text
.draft/framework/      # Vendored DRAFT framework copy used by that company
.draft/providers/      # Optional third-party control packs
.draft/workspace.yaml  # Tracked workspace metadata
.draft/framework.lock  # Upstream source and synced framework commit
catalog/                # Company architecture content
configurations/         # Company Definition Checklist, compliance, domain, and patch overlays
configurations/object-patches/
                        # Patch objects for framework or catalog overrides
```

The effective model is resolved by reading `.draft/framework/configurations/`
first, then optional `.draft/providers/*/configurations/`, then workspace
configuration overlays, then workspace catalog content. The public repo is an
update source, not a runtime dependency for a company's Draftsman.

## DRAFT Table

DRAFT Table is the local-first companion UI for working with a private company
DRAFT repo. It is intentionally not an AI credential store and not a hosted
service. The source of truth remains the local filesystem and Git.

DRAFT Table is not a YAML editor. The user experience is the Draftsman
conversation: questions, document intake, architecture interviews, artifact
summaries, validation results, and commit controls. DRAFT Table may write DRAFT
YAML files internally because that is the framework storage format, but it
should not show users raw YAML code.

Install and onboard:

```bash
curl -fsSL https://raw.githubusercontent.com/dsackr/draft-framework/main/install-draft-table.sh | bash
```

The installer clones or updates the framework repo, installs DRAFT Table, runs
onboarding, bootstraps `.draft/framework/` into the selected company repo, and
then starts the local web UI. The web UI is the preferred Draftsman experience.
Run it from an interactive terminal so onboarding can prompt for your company
DRAFT repo and provider preference.

Local development install from this checkout:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
draft-table onboard
draft-table serve
```

The web UI binds to `0.0.0.0` by default so another device on the same LAN can
reach it. Startup output prints both the LAN URL and the local URL. Use
`draft-table serve --host 127.0.0.1` for local-only access.

### DRAFT Table CLI

```bash
draft-table onboard
draft-table serve
draft-table chat
draft-table validate
draft-table ai doctor
draft-table repo status
draft-table framework status
draft-table framework refresh
draft-table commit -m "Update DRAFT catalog"
draft-table doctor
```

DRAFT Table now includes the first Draftsman loop. The web UI is the preferred
experience because it supports source uploads and artifact proposal review. The
`draft-table chat` command is a terminal fallback for a conversational
Draftsman session.

- conversational framework and catalog questions
- local catalog reference lookup, such as "where is this object used?"
- source material upload into a local Draftsman session
- provider-backed architecture interview prompts through the selected CLI
- artifact proposal cards without raw YAML display
- apply-proposal flow that writes DRAFT YAML internally and then validates
- explicit framework refresh into `.draft/framework/` for review and commit

Later phases should deepen document/image extraction, add richer validation
repair loops, and add push and PR workflow.

### Supported AI Providers

DRAFT Table stores only provider type, executable path, optional model name,
local endpoint, company DRAFT repo path, and non-secret preferences in
`~/.draft-table/config.yaml`.

Supported provider selections:

- `codex`
- `claude-code`
- `gemini-cli`
- `local-llm`
- `custom-command`

Provider CLIs own their own authentication. For example, use `codex --login`,
the Claude Code login flow, or the Gemini CLI Google login outside DRAFT Table.
For local models, Phase 1 records an Ollama-compatible localhost endpoint.

See [security.md](security.md) for the threat model and credential boundary.

## Start Here

### Framework Basics

- [Framework overview](framework/docs/overview.md)
- [Framework versioning](VERSIONING.md)
- [Release checklist](RELEASE.md)
- [Changelog](CHANGELOG.md)
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

- [Standards](framework/docs/standards.md)
- [Reference Architectures](framework/docs/reference-architectures.md)
- [Software Deployment Patterns](framework/docs/software-deployment-patterns.md)

### Standard Classifications

- [Product Service](framework/docs/product-service.md)
- [PaaS Service](framework/docs/paas-service-standards.md)
- [SaaS Service](framework/docs/saas-service-standards.md)

### Supporting Model Objects

- [Technology Components](framework/docs/technology-components.md)
- [Decision Records](framework/docs/decision-records.md)
- [Drafting Sessions](framework/docs/drafting-sessions.md)

### Extensible Framework Content

- [Definition Checklists](framework/docs/definition-checklists.md)
- [Compliance Controls and Control Enforcement Profiles](framework/docs/security-and-compliance-controls.md)

## Validate And Generate

Install the only runtime dependency used by the framework tools:

```bash
python3 -m pip install pyyaml
```

Validate the framework base configuration and example catalog:

```bash
python3 framework/tools/validate.py
```

Validate a company repo from the upstream checkout:

```bash
python3 framework/tools/validate.py --workspace /path/to/company-draft-workspace
```

Inside a company repo, validate against the vendored framework copy:

```bash
python3 .draft/framework/tools/validate.py --workspace .
```

Regenerate the static browser and AI index after YAML, docs, schema, or template
changes:

```bash
python3 framework/tools/generate_browser.py
python3 framework/tools/generate_ai_index.py
```

Run the DRAFT Table unit tests:

```bash
python3 -m unittest discover -s tests
```

Check release-note and version metadata:

```bash
python3 framework/tools/check_release_notes.py
```

## Compliance Claims

Control catalogs and Control Enforcement Profiles can be supplied by the DRAFT
framework, third-party providers, or the company workspace. The company
activates the profiles it architects against in `.draft/workspace.yaml`.

Architecture artifacts declare compliance explicitly with
`controlEnforcementProfiles`. When a profile is declared, every applicable
control from that profile must have a valid `controlImplementations` entry or
validation fails.

Artifacts without a declared profile are unclaimed inventory. They are not
labeled non-compliant, but they should not be treated as compliant
off-the-shelf building blocks for solutions that require that control profile.
If `requireActiveProfileDisposition` is enabled in the workspace, validation
also requires every in-scope object to record disposition against every active
profile.

## Catalog Browsing

The generated static browser is published at:

[https://dsackr.github.io/draft-framework/](https://dsackr.github.io/draft-framework/)

GitHub Pages is read-only. It is generated from `framework/configurations/` and
`examples/catalog/` by `framework/tools/generate_browser.py`.
