# DRAFT Framework Toolkit

## What This Repo Is

This repository is the entry point for DRAFT — Deployable Reference Architecture Framework Toolkit. It stores reusable architecture data as YAML, validates that data in CI, and generates the browser published through GitHub Pages.

If you are new to the repo, start with the framework documents below before editing any catalog objects.

The current framework validates RBBs, RAs, and DAs against Architecture Analysis Guidelines. ABBs remain governed by their schema and lifecycle metadata rather than an AAG.

## Start Here

- [AI rebuild prompt](docs/ai-rebuild-prompt.md)
- [Framework overview](docs/framework/overview.md)
- [ABBs](docs/framework/abbs.md)
- [RBBs](docs/framework/rbbs.md)
- [AAGs](docs/framework/aags.md)
- [Reference architectures](docs/framework/reference-architectures.md)
- [Deployment architectures](docs/framework/deployment-architectures.md)
- [Naming conventions](docs/framework/naming-conventions.md)
- [How to add objects](docs/framework/how-to-add-objects.md)
- [Security and compliance controls](docs/framework/security-and-compliance-controls.md)

## Repository Structure

```text
abbs/                       Architecture Building Blocks
rbbs/                       Reusable host and service building blocks
aags/                       Architecture Analysis Guidelines
ards/                       Architecture Risks and Decisions
product-services/           first-party product services
reference-architectures/    Pattern-level architecture definitions
deployment-architectures/   Product-specific deployment declarations
docs/                       Generated browser and framework documentation
tools/                      Validator and browser generator
schemas/                    Reserved for schema artifacts
adrs/                       Architecture decision records
```

## Running The Tools

Install the only Python dependency:

```bash
python3 -m pip install pyyaml
```

Validate the catalog:

```bash
python3 tools/validate.py
```

Regenerate the browser:

```bash
python3 tools/generate_browser.py
```

Important: `architecturalDecisions` values must be machine-readable. Use the constrained enums defined in the schema for known keys. Do not use prose values. These fields are intended to drive IaC automation in a future phase.

`variants` is an open-ended map. `ha` and `sa` are common examples, but they are not the only valid keys. Use the variant names that best describe the operating posture of the object.

## Automation

- `.github/workflows/validate-catalog.yml` runs validation on pushes and pull requests.
- `.github/workflows/generate-browser.yml` regenerates `docs/index.html` on `main` when YAML content changes.

## Published Browser

The generated site is published at:

`https://dsackr.github.io/draft-framework/`
