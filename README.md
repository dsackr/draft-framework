![DRAFT Logo](./draftlogo.png)

# Deployable Reference Architecture Framework Toolkit (DRAFT)

> [!IMPORTANT]
> **AI Assistants / Agents:** You are expected to act as **The Draftsman**. 
> Before proceeding, you **MUST** read [AGENTS.md](AGENTS.md), then the
> [Draftsman Instructions](docs/framework/draftsman.md).
> Proactively offer to start a [Drafting Session](docs/framework/drafting-sessions.md) when assisting a user.

DRAFT — Deployable Reference Architecture Framework Toolkit — is a Git-based
architecture catalog. It stores machine-readable YAML objects, validates their
relationships and governance rules, and generates a browser for inspection and
discovery.

This repository is the framework template. Organization-specific architecture
content belongs in downstream company-owned clones. A downstream clone can start
empty, then use the Draftsman workflow, schemas, ODCs, and templates to build a
private architecture catalog.

Use this page as the entry point. The framework details live in the documents
linked below.

## AI-First Setup

- [AGENTS.md](AGENTS.md) is the canonical bootstrap for AI agents.
- [AI_INDEX.md](AI_INDEX.md) is a generated map of framework docs, schemas,
  ODCs, templates, and any YAML objects present in the current checkout.
- [GEMINI.md](GEMINI.md), [CLAUDE.md](CLAUDE.md), and
  [.github/copilot-instructions.md](.github/copilot-instructions.md) are thin
  provider-specific pointers back to `AGENTS.md`.
- [llms.txt](llms.txt) exposes the same entry points in a lightweight,
  web-friendly form.

When a user connected to this repo says "I need a draftsman", the AI should
immediately assume the Draftsman role and guide the user through creating,
updating, or validating DRAFT artifacts.

## Start Here

### Framework Basics

- [Framework overview](docs/framework/overview.md)
- [AI agent bootstrap](AGENTS.md)
- [AI framework index](AI_INDEX.md)
- [Draftsman instructions for AI](docs/framework/draftsman.md)
- [YAML schema reference](docs/framework/yaml-schema-reference.md)
- [Naming conventions](docs/framework/naming-conventions.md)
- [How to add objects](docs/framework/how-to-add-objects.md)
- [Authoring templates](templates/)

### Architecture Content

- [Reference Building Blocks (RBBs)](docs/framework/rbbs.md)
- [Reference Architectures (RAs)](docs/framework/reference-architectures.md)
- [Software Distribution Manifests (SDMs)](docs/framework/software-distribution-manifests.md)

### RBB Classifications

- [Product Service](docs/framework/product-service.md)
- [PaaS Service](docs/framework/paas-services.md)
- [SaaS Service](docs/framework/saas-services.md)

### Supporting Model Objects

- [Architecture Building Blocks (ABBs)](docs/framework/abbs.md)
- [Deployment Risks and Decisions (DRDs)](docs/framework/deployment-risks-and-decisions.md)
- [Drafting Sessions](docs/framework/drafting-sessions.md)

### Extensible Framework Content

- [Object Definition Checklists (ODCs)](docs/framework/odcs.md)
- [Security and Compliance Controls (SCCs)](docs/framework/security-and-compliance-controls.md)

## Compliance Claims

Architecture artifacts declare framework compliance explicitly with
`complianceProfiles`. When a profile is declared, every applicable control from
that profile must have a valid `controlImplementations` entry or validation
fails.

Artifacts without a declared profile are not labeled non-compliant. They are
unclaimed inventory and should not be treated as compliant off-the-shelf
building blocks for solutions that require that framework.

## Browser

The generated browser is published at:

[https://dsackr.github.io/draft-framework/](https://dsackr.github.io/draft-framework/)

The browser includes an in-page editor for existing objects. It is static and
cannot write back to GitHub Pages directly, but it can generate, copy, and
download updated YAML so changes can be committed or proposed through GitHub.
