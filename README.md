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

If the user is asking for company architecture content while connected only to
this upstream framework repo, the AI should not write that content into
`examples/` or framework-owned paths. It should ask for the company-specific
DRAFT repo path first, then make content changes in that workspace after the
framework has been vendored there.

## Repository Layout

```text
framework/              # Core schemas, tools, docs, and base configurations
framework/browser/      # Static browser shell, CSS, JavaScript, and theme assets
framework/configurations/
                        # Base capabilities, Requirement Groups, and domains
examples/catalog/       # Sample content used to validate and demo the framework
templates/              # Object and company repo templates
docs/index.html         # Generated static browser for the example workspace
docs/assets/            # Generated browser data plus copied browser assets
docs/user-manual.html   # Generated DRAFT user manual
docs/company-vocabulary.html
                        # Generated company vocabulary guide
draft_table/            # Experimental local app prototype; post-v1.0
```

A company private DRAFT repo should use this shape:

```text
.draft/framework/      # Vendored DRAFT framework copy used by that company
.draft/providers/      # Optional third-party control packs
.draft/workspace.yaml  # Tracked workspace metadata
.draft/framework.lock  # Upstream source and synced framework commit
catalog/                # Company architecture content
configurations/         # Company Requirement Group, compliance, domain, and patch overlays
configurations/vocabulary/
                        # Optional company governed vocabulary source files
configurations/vocabulary-proposals/
                        # Draftsman proposals for non-standard values
configurations/object-patches/
                        # Patch objects for framework or catalog overrides
```

The effective model is resolved by reading `.draft/framework/configurations/`
first, then optional `.draft/providers/*/configurations/`, then workspace
configuration overlays, then workspace catalog content. The public repo is an
update source, not a runtime dependency for a company's Draftsman.

## Repo-First v1.0 Operating Model

DRAFT v1.0 is repo-first. It does not require a DRAFT application, hosted
service, local daemon, or DRAFT-specific CLI. The user experience is:

1. Create a private company DRAFT repo.
2. Vendor a reviewed framework copy under `.draft/framework/`.
3. Add the root AI bootstrap files from `templates/workspace/`.
4. Connect the AI tool the company already uses, such as ChatGPT, Claude,
   Gemini, Copilot, Codex, or another code-capable assistant.
5. Ask the AI to act as the Draftsman and follow `AGENTS.md`.
6. Review all changes as ordinary Git diffs and pull requests.

The Draftsman conversation is still the intended authoring experience, but it
happens through the AI tool connected to the repo. The framework supplies the
prompts, schemas, templates, docs, validation tools, generated browser, and
GitHub Actions workflows that make that AI behavior deterministic and
reviewable.

For a new company workspace, ask the connected AI to start setup mode. Setup
mode walks the enterprise architecture team through the minimum steps needed to
make the repo useful: workspace readiness, business taxonomy, company
vocabulary lists, active Requirement Groups, capability owners, acceptable-use
technology, baseline deployable standards, and one real first Drafting Session.
It keeps the user aware of the current step, next step, remaining work, and
revisit-later items.

The local DRAFT Table app and `draft-table` CLI are retained in the repository
as an experimental prototype, but they are not part of the v1.0 launch path.
Future releases may revive them as optional convenience tooling after the
repo-first workflow is stable.

### Framework Update Workflow

New company workspaces include an optional GitHub Actions workflow at
`.github/workflows/draft-framework-update.yml`. The workflow checks for newer
DRAFT Framework version tags, creates an update branch, refreshes the vendored
`.draft/framework/` copy, updates `.draft/framework.lock`, validates the
workspace, and opens a pull request.

If validation succeeds, the PR is titled as a normal framework update. If
validation fails, the workflow still opens the PR but marks it blocked so the
company can repair catalog or configuration issues on that branch. Companies can
disable this behavior by disabling the workflow in GitHub Actions or deleting
the workflow file.

New company workspaces also include an optional vocabulary proposal workflow at
`.github/workflows/draft-vocabulary-proposals.yml`. When the Draftsman captures
a real answer that is not an approved vocabulary value, it can write a
`vocabulary_proposal` file; the workflow can turn that into a review pull
request against the official company vocabulary list.

### AI Tool Boundary

DRAFT does not store AI credentials. The connected AI tool and Git provider own
authentication. If the AI environment has Git and GitHub access through the
user's credentials, it may branch, commit, push, and open pull requests. If it
does not, it should prepare local changes and give exact review steps.

## Start Here

### Framework Basics

- [Framework overview](framework/docs/overview.md)
- [Framework versioning](VERSIONING.md)
- [Release checklist](RELEASE.md)
- [Changelog](CHANGELOG.md)
- [AI agent bootstrap](AGENTS.md)
- [AI framework index](AI_INDEX.md)
- [User manual](framework/docs/user-manual.md)
- [Draftsman instructions for AI](framework/docs/draftsman.md)
- [Draftsman setup mode](framework/docs/setup-mode.md)
- [Draftsman AI guidance](framework/docs/draftsman-ai-configuration.md)
- [Company onboarding tutorial](framework/docs/company-onboarding.md)
- [Company vocabulary](framework/docs/company-vocabulary.md)
- [DRAFT object types](framework/docs/object-types.md)
- [YAML schema reference](framework/docs/yaml-schema-reference.md)
- [Naming conventions](framework/docs/naming-conventions.md)
- [How to add objects](framework/docs/how-to-add-objects.md)
- [Workspace model](framework/docs/workspaces.md)
- [Authoring templates](templates/)

### Deployable Architecture Content

- [Deployable objects](framework/docs/standards.md)
- [Delivery models](framework/docs/delivery-models.md)
- [Product Service](framework/docs/product-service.md)
- [Reference Architectures](framework/docs/reference-architectures.md)
- [Software Deployment Patterns](framework/docs/software-deployment-patterns.md)

### Supporting Model Objects

- [Technology Components](framework/docs/technology-components.md)
- [Decision Records](framework/docs/decision-records.md)
- [Drafting Sessions](framework/docs/drafting-sessions.md)
- [Capabilities](framework/docs/capabilities.md)

### Extensible Framework Content

- [Requirement Groups](framework/docs/requirement-groups.md)
- [Requirement Groups and Compliance](framework/docs/security-and-compliance-controls.md)

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

Regenerate the static browser, browser assets, user manual, and AI index after
YAML, docs, schema, browser, or template changes:

```bash
python3 framework/tools/generate_browser.py
python3 framework/tools/generate_ai_index.py
```

Run the framework unit tests:

```bash
python3 -m unittest discover -s tests
```

Check release-note and version metadata:

```bash
python3 framework/tools/check_release_notes.py
```

## Compliance Claims

Workspace-mode Requirement Groups can be supplied by the DRAFT framework,
third-party providers, or the company workspace. The company activates the
groups it architects against in `.draft/workspace.yaml`.

Architecture artifacts declare compliance explicitly with
`requirementGroups`. When a workspace-mode group is declared, every applicable
requirement from that group must have a valid `requirementImplementations`
entry before the object can be approved.

Artifacts without a declared group are unclaimed inventory. They are not
labeled non-compliant, but they should not be treated as compliant
off-the-shelf building blocks for solutions that require that requirement group.
If `requireActiveRequirementGroupDisposition` is enabled in the workspace, validation
also requires every in-scope object to record disposition against every active
group.

## Catalog Browsing

The generated static browser is published at:

[https://dsackr.github.io/draft-framework/](https://dsackr.github.io/draft-framework/)

GitHub Pages is read-only. `docs/index.html` is a generated shell. The browser
data is written to `docs/assets/browser-data.js`, and framework-owned CSS,
JavaScript, and default theme assets are copied from `framework/browser/`.
The same generator renders `framework/docs/user-manual.md` to
`docs/user-manual.html`.
