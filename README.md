# Deployable Reference Architecture Framework Toolkit (DRAFT)

## What This Repo Is

This repository is the entry point for DRAFT — Deployable Reference Architecture Framework Toolkit. It stores reusable architecture data as YAML, validates that data in CI, and generates the browser published through GitHub Pages.

If you are new to the repo, start with the framework documents below before editing any catalog objects.

The current framework validates RBBs, RAs, and SDMs against Architecture Analysis Guidelines. ABBs remain governed by their schema and lifecycle metadata rather than an AAG.

Compliance mappings are plug-and-play. AAGs define architecture requirements, while separate compliance framework and mapping objects determine which controls are shown for a selected framework such as a baseline controls pack, NIST CSF, SOC 2, or an organization-specific overlay.

## Start Here

- [AI rebuild prompt](docs/ai-rebuild-prompt.md)
- [Framework overview](docs/framework/overview.md)
- [ABBs](docs/framework/abbs.md)
- [Product services](docs/framework/product-services.md)
- [SaaS services](docs/framework/saas-services.md)
- [RBBs](docs/framework/rbbs.md)
- [AAGs](docs/framework/aags.md)
- [Reference architectures](docs/framework/reference-architectures.md)
- [Software distribution manifests](docs/framework/software-distribution-manifests.md)
- [SDM structure](docs/framework/da-structure.md)
- [Naming conventions](docs/framework/naming-conventions.md)
- [How to add objects](docs/framework/how-to-add-objects.md)
- [Security and compliance controls](docs/framework/security-and-compliance-controls.md)

## Repository Structure

```text
abbs/                       Architecture Building Blocks
saas-services/              Vendor-managed SaaS service objects
rbbs/                       Reusable host and service building blocks
aags/                       Architecture Analysis Guidelines
ards/                       Architecture Risks and Decisions
compliance-frameworks/      Selectable compliance frameworks
compliance-mappings/        Requirement-to-control mappings per framework
product-services/           first-party product services
reference-architectures/    Pattern-level architecture definitions
sdms/                       Product-specific software distribution manifests
docs/                       Generated browser and framework documentation
tools/                      Validator and browser generator
schemas/                    Reserved for schema artifacts
```

Each object family uses a flat folder. The file path is organizational only. The
authoritative object identity and semantics come from the YAML fields such as
`id`, `type`, `subtype`, `category`, and `serviceCategory`, not from nested
directory placement.

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
