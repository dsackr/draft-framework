# Framework Overview

## What This Catalog Is

DRAFT — Deployable Reference Architecture Framework Toolkit — exists to make architecture decisions explicit, reviewable, and reusable. It is a Git-based catalog of YAML objects that describe the building blocks engineering teams are allowed to assemble, the patterns those building blocks support, the deployment declarations that map those patterns to real products, and the analysis rules that determine whether an architecture description is complete enough to be approved.

The point is not to create documentation for its own sake. The point is to give Cloud Ops, Product Engineering, Security, and Architecture a shared source of truth that can be validated automatically and browsed consistently.

## The Six Object Types

The catalog contains six object types.

- ABBs define discrete vendor products at specific versions.
- RBBs define reusable architecture components built from ABBs.
- AAGs define the requirements a catalog object must satisfy before it can be approved. In practice the current AAG set covers RBBs, RAs, and DAs.
- RAs define reusable patterns in terms of required RBBs and roles.
- DAs define how a specific product is deployed using those RBBs.
- External interactions define the black-box systems a component depends on, whether or not those systems exist elsewhere in the catalog.

## How The Objects Relate

The relationship model is deliberate.

- ABBs are the smallest reusable units.
- Host RBBs are assembled from OS, hardware, and agent ABBs plus platform interactions.
- Service RBBs compose a host RBB with one function ABB.
- RAs say which RBBs, in which named variants, are required for a given pattern.
- DAs say which RBBs are actually deployed for a specific product.
- AAGs define what must be addressed before a reusable architecture component or pattern declaration can be approved.

A useful way to think about the catalog is this: ABBs define what a component is, RBBs define how it behaves architecturally, RAs define which components a pattern requires, DAs define what a product actually uses, and AAGs define what questions must be answered before the component can be trusted.

## Lifecycle Status

Lifecycle status describes the framework's strategic stance toward a technology or pattern.

### `pre-invest`

The technology is being explored but is not yet a standard. Engineers can evaluate it, but should not assume it is ready for broad production adoption.

### `invest`

Frontline wants new work to move in this direction. If you are starting a new workload and an invest-status option fits, that is usually the default choice.

### `maintain`

The technology is supported and acceptable for current use, but it is not the preferred destination for new strategic work.

### `disinvest`

The technology is still supported for now, but engineers should plan migrations away from it and avoid creating new dependencies on it.

### `exit`

The technology is beyond its useful life for Frontline and should be removed as quickly as practical.

Concrete example: Windows Server 2012 R2 still appears in the catalog because it exists in the estate, but its lifecycle status makes the engineering direction unambiguous.

## Catalog Status

Catalog status describes documentation maturity rather than strategic direction.

### `stub`

The object exists only in skeletal form. It may reserve an ID or establish intent, but it is not complete enough to guide engineering decisions.

### `draft`

The object has meaningful content and can be reviewed, but it has not yet satisfied all governance expectations.

### `approved`

The object has passed the framework’s validation bar and is ready to be used as a reference point for engineering decisions.

For RBBs, the most important gate is the relationship to AAGs. An RBB can only be considered truly complete when it satisfies the AAGs listed in `satisfiesAAG`. RAs and DAs are also validated against their applicable AAGs, even though those relationships are determined by `appliesTo` rather than an explicit `satisfiesAAG` list on the object.

ID immutability: once an object reaches `catalogStatus: approved`, its `id` field must never change. Downstream tooling, including future IaC pipelines, will reference objects by ID. Renaming an approved object is a breaking change.

## Git As The Source Of Truth

Git is the source of truth for this framework. That matters because architecture changes are not hidden in slide decks or wiki pages. They are versioned, reviewable, and diffable.

When an engineer updates an ABB, adds a new RBB variant, or introduces a new AAG requirement, that change follows the same path as a code change:

1. Edit files locally.
2. Run validation.
3. Open a pull request.
4. Review the diff.
5. Merge to `main`.
6. Let automation regenerate the browser.

The validator in `tools/validate.py` enforces schema and AAG satisfaction rules. The browser generator in `tools/generate_browser.py` reads the catalog objects and emits `docs/index.html`, which becomes the published browsing experience on GitHub Pages.

## Why This Matters In Practice

The browser and validator support engineering judgment. They do not replace it.

- Validation catches missing requirements and broken references.
- The browser improves discoverability and makes the catalog easier to inspect.
- Git history preserves what changed, when it changed, and who changed it.

Taken together, those pieces make the framework durable. An engineer joining a product team can read the docs, browse the current standards, inspect the YAML, and understand not just what the standard is, but how it should evolve.
