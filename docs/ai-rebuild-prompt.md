# DRAFT Rebuild Prompt

Use this document as the canonical prompt for rebuilding DRAFT — Deployable Reference Architecture Framework Toolkit — in the `draft-framework` repository. It describes the framework, the catalog object model, the schema rules, the validation behavior, and the browser UI contract in enough detail that an engineer or coding agent can reconstruct the project without relying on the current implementation files. This document intentionally excludes concrete ABB, RBB, Reference Architecture, and Software Distribution Manifest instances. It does include the ODC definitions because those are framework rules rather than environment-specific examples.

## What This Repository Is

The repository is a Git-as-source-of-truth architecture catalog. All architecture data is stored as YAML. Python tooling validates the YAML and generates a static browser UI that is published through GitHub Pages. There is no database, no Node.js runtime, and no server-side rendering. The catalog is deliberately designed so that architecture objects can be reviewed in pull requests, versioned over time, and consumed later by automation.

The purpose of the catalog is to describe reusable architecture primitives, product-specific services, architecture patterns, deployment declarations, and governance requirements in a consistent machine-readable model. The repository is not a diagram repository and not a CMDB. It is a structured architecture knowledge base.

## Core Principles

DRAFT is built around a few strict principles. First, Git is the system of record for architecture content. Second, every meaningful architecture concept should be represented as a first-class YAML object rather than as unstructured prose. Third, validation rules should be deterministic and machine-readable wherever possible. Fourth, the browser must be data-driven: it should discover objects and relationships from YAML alone, not from hardcoded IDs, products, or location names. Fifth, the catalog must support future automation, so known decision keys must remain constrained and not drift into prose.

## Repository Structure

The repository should contain these top-level folders:

- `abbs/` for Architecture Building Blocks
- `rbbs/` for SaaS Service RBB classifications
- `rbbs/` for Reusable Building Blocks
- `odcs/` for Object Definition Checklists
- `ards/` for Architecture Risks and Decisions
- `compliance-frameworks/` for selectable compliance framework objects
- `rbbs/` for Product Service RBB classifications
- `reference-architectures/` for Reference Architecture objects
- `sdms/` for Software Distribution Manifest objects
- `schemas/` for schema notes and simple YAML schema artifacts
- `tools/` for Python validation and browser generation
- `docs/` for generated browser output and DRAFT documentation

The browser generator should discover YAML files by walking the catalog folders listed above, not by hardcoded filenames. Every YAML file under those folders is part of the catalog.

Each object family folder should remain flat. Do not create nested taxonomy
folders such as `abbs/os/` or `rbbs/service/web/`. The object's YAML fields and
ID encode its type and category already, so nested directories would only
duplicate metadata.

## Shared Object Contract

All first-class catalog objects share a common base model. Every object should include:

- `schemaVersion`
- `id`
- `type`
- `name`
- `description`
- `version`
- `catalogStatus`
- `lifecycleStatus`
- `owner.team`
- `owner.contact`
- `tags`

The validator must enforce valid `catalogStatus` values of `stub`, `draft`, or `approved`, and valid `lifecycleStatus` values of `pre-invest`, `invest`, `maintain`, `disinvest`, or `exit`.

ID immutability is part of the DRAFT contract. Once an object reaches `catalogStatus: approved`, its `id` should be treated as permanent. Downstream tooling and future IaC workflows will reference catalog objects by ID.

## Object Types

### ABB

An ABB, or Architecture Building Block, is a configuration document for a specific vendor product at a specific version. ABBs represent installable, vendor-provided building blocks such as operating systems, infrastructure hardware profiles, vendor software, or agents. An ABB is not a deployment, not a pattern, and not first-party product code. It is the catalog’s unit of reusable vendor technology definition.

ABBs carry vendor lifecycle metadata and framework lifecycle intent. Every ABB must declare `vendor`, `productName`, `productVersion`, and exactly one `classification`. ABB classifications are `operating-system`, `compute-platform`, `software`, and `agent`. ABBs may declare a `platformDependency` when they depend on another platform or external system.

ABBs may also use `subtype: appliance`. Appliance ABBs model blackbox
vendor-managed components that are still deployed inside the adopter's
infrastructure boundary.

### SaaS Service

A SaaS Service is a vendor-managed subscribed service. It exists as a
first-class object because it can move data through vendor-managed
infrastructure outside the adopter's boundary, making data governance a primary
architecture concern.

### RBB

An RBB, or Reusable Building Block, is a reusable architecture pattern that Reference Architectures and Software Distribution Manifests are assembled from. There are two categories: `host` and `service`.

A host RBB represents a compute platform configuration. It defines internal components such as an Operating System ABB, a Compute Platform ABB, and installable Agent ABBs, plus external interactions such as authentication, logging, monitoring, security, and patching platforms.

A service RBB represents a reusable service pattern. It composes a host RBB together with a function ABB, then adds any service-specific external interactions and architecture decisions on top. Service RBBs are categorized further by `serviceCategory`, such as `general`, `database`, `product`, or `saas`.

The distinction between ABB and RBB is important. An ABB is an individual vendor technology definition. An RBB is a reusable architecture pattern that uses ABBs and possibly other RBBs.

### ODC

An ODC, or Object Definition Checklist, is a first-class catalog object that defines the required questions and answers needed to build a complete and correct architecture object. ODCs are not deployed runtime components. They are structured object-definition checklists.

In the current DRAFT implementation, ODCs are written for host RBBs, service
RBBs, DBMS service RBBs, appliance ABBs, SaaS Services, reference
architectures, software distribution manifests, and product services.

### Compliance Framework

A Compliance Framework is a first-class catalog object that defines a selectable control catalog. It exists so the same architecture requirement model can be viewed under different compliance regimes without rewriting the ODCs themselves.

Common examples include a baseline controls pack, NIST CSF, SOC 2, or an organization-specific overlay.

### ARD

An ARD, or Architecture Risks and Decisions object, is a first-class catalog object for capturing either a known risk or a documented decision. It replaces the older tendency to bury architecture risks inside free-form notes. An ARD can describe an SPOF, a technical debt tradeoff, a security gap, or a design decision with rationale.

ARDs can be linked from software distribution manifests and rendered directly in the browser. AuditBoard or another controls platform may consume ARD relationships later, but the catalog itself remains the YAML source of truth.

### Reference Architecture

A Reference Architecture defines a pattern, not a deployment. It answers the question: which reusable building blocks, in which roles, make up a supported architecture pattern? It never represents a specific product environment.

Reference Architectures point to required RBBs and define pattern-level decisions. They should be thought of as reusable blueprints for governance and discovery.

### Software Distribution Manifest

A Software Distribution Manifest declares how a specific product is deployed. It
references a Reference Architecture via `appliesPattern`, groups deployable
components into service groups and scaling units, and links any architecture
risks and decisions.

The SDM is where pattern intent becomes deployment reality. The SDM can declare deviations from a pattern, and those deviations should be documented via ARDs rather than hidden in prose.

### Product Service

A Product Service, or PS, is a first-class catalog object for a first-party service. If a workload contains organization-authored code, it is a Product Service. If it is vendor software that could be reused across products, it is an RBB, even if only one product currently uses it.

A Product Service does not enumerate code packages in version 1 of DRAFT. Instead, it declares the owning product and the reusable pattern it runs on via `runsOn`.

## Schema-Specific Rules

### ABB Schema

ABB objects include product-specific metadata:

- `classification`
- `vendor`
- `productName`
- `productVersion`
- `platformDependency` (optional)
- `vendorLifecycle.mainstreamSupportEnd`
- `vendorLifecycle.extendedSupportEnd`
- `vendorLifecycle.notes`

ABB IDs follow the pattern families defined by the naming convention, such as `abb.os.<vendor>-<os>-<version>`, `abb.software.<vendor>-<product>-<version>`, and similar.

### RBB Schema

RBB objects include:

- `category`: `host` or `service`
- `serviceCategory` when category is `service`
- `satisfiesODC`
- `internalComponents`
- `externalInteractions`
- `architecturalDecisions`

Host RBBs additionally include:

- `osAbb`
- `hardwareAbb`

Service RBBs additionally include:

- `hostRbb`
- `functionAbb`

`architecturalDecisions` is used when an object must answer an ODC or compliance question that is not otherwise expressed directly in the object.

Known `architecturalDecisions` keys must remain machine-readable. When `autoscaling` or `loadBalancer` are present, they must use the enum values `required`, `optional`, or `none`. When `minNodes` is present, it must be an integer.

### ODC Schema

ODC objects include:

- `appliesTo`
- `inherits` (optional)
- `requirements`

Each requirement is mechanism-based rather than field-path-based. A requirement includes:

- `id`
- `description`
- `rationale`
- `canBeSatisfiedBy`
- `minimumSatisfactions`

Each satisfaction mechanism is one of:

- `externalInteraction`
- `internalComponent`
- `architecturalDecision`

This model matters because an ODC defines what must be addressed, not necessarily the exact implementation path. For example, authentication can be satisfied by an explicit external identity interaction or by a documented architectural decision, depending on the object type.

### Compliance Framework Schema

Compliance framework objects include:

- `frameworkKind`
- optional `controlIdNamespace`
- optional `defaultSelection`
- optional `extends`
- optional `requirementMappings`

These objects make compliance selection data-driven. A framework may extend another framework so an organization-specific overlay can inherit a baseline control pack and override only the differences.

When present, `requirementMappings` is a nested map of `odc-id ->
requirement-id -> [control ids]`. This keeps ODCs architecture-focused while
allowing control catalogs to be refreshed independently.

### ARD Schema

ARD objects include:

- `category`: `risk` or `decision`
- `status`: `open`, `accepted`, `mitigated`, or `resolved`
- `description`
- `affectedComponent`
- `impact`
- `mitigationPath` (optional)
- `decisionRationale` (required for decision ARDs)
- `relatedARDs` (optional)
- `linkedSDM` (optional)

ARD IDs must match `ard.<domain>.<sequence>`.

### Reference Architecture Schema

Reference Architecture objects include:

- `patternType`
- `requiredRBBs`
- `architecturalDecisions`

Each `requiredRBBs` entry includes:

- `ref`
- `role`
- optional notes

Reference Architectures are validated against `odc.ra`.

### Software Distribution Manifest Schema

Software Distribution Manifest objects include:

- `appliesPattern`
- `architecturalDecisions`
- `scalingUnits`
- `serviceGroups`
- `architectureRisksAndDecisions`

Each service group can include:

- `rbbs`
- `applianceAbbs`
- `externalInteractions`

Deployed RBB entries can use `intent` only when the architect is
making an explicit design decision that deviates from the Reference Architecture
default, or when no Reference Architecture exists.

Software Distribution Manifests are validated against `odc.sdm`. Risk references and ARD lists must resolve to actual ARD objects.

### Product Service Schema

Product Service objects include:

- `product`
- `runsOn`
- `architecturalDecisions`
- optional `notes`

`runsOn` must resolve to a known RBB ID. Product Service IDs must match `ps.<product>.<service-name>`.

## ODC Definitions

### odc.host

The host ODC applies to host RBBs. It requires that the host address authentication, logging, security monitoring, and patch management. Host ODCs validate the host baseline itself; backup belongs to service and data concerns unless an attached compliance framework adds stricter expectations.

### odc.service

The service ODC applies to all service RBBs. It requires that a service document scaling approach, health check behavior, and secrets management. It assumes host posture is inherited from the referenced host RBB rather than duplicated.

### odc.service.dbms

The DBMS service ODC inherits `odc.service` and adds DBMS-specific durability and control requirements. It requires backup strategy, recovery time, recovery point, high-availability mechanism, encryption at rest, and access control model.

### odc.ra

The Reference Architecture ODC requires:

- a non-empty `patternType`
- at least one `requiredRBBs` entry
- a `role` on every required RBB
- pattern-level `architecturalDecisions`
- evidence that pattern-level architecture decisions are covered

### odc.sdm

The Software Distribution Manifest ODC requires:

- a non-empty `appliesPattern`
- `architecturalDecisions.availabilityRequirement`
- either product-level `externalInteractions` or an explicit `noAdditionalInteractions` decision
- `architecturalDecisions.dataClassification`

### odc.product-service

The Product Service ODC defines the minimum modeling contract for a first-party service:

- selection of the RBB pattern via `runsOn`
- a populated `product` field
- explicit declaration that the object is first-party by virtue of being an RBB with `serviceCategory: product`

## Validation Behavior

The validator is a Python script using `pyyaml` as the only dependency. It walks the catalog folders, loads every YAML file, and validates them against the executable rules encoded in `tools/validate.py`.

Validation performs these categories of checks:

- base required field presence
- ID prefix and format rules by object type
- valid lifecycle and catalog status enums
- machine-readable decision enforcement for `autoscaling`, `loadBalancer`, and `minNodes`
- ODC satisfaction checks for applicable object types
- reference resolution checks, such as `runsOn`, `hostRbb`, `functionAbb`, `osAbb`, `hardwareAbb`, and ARD references

The validator exits non-zero on failure and prints pass or fail per file. This output is designed for both local use and CI.

## Naming Conventions

IDs are lowercase, dot-separated, and use hyphens inside segments. The major object families follow these patterns:

- `abb.*` for ABBs
- `rbb.*` for RBBs
- `odc.*` for ODCs
- `ard.*` for ARDs
- `ps.*` for Product Services
- `ra.*` for Reference Architectures
- `sdm.*` for Software Distribution Manifests

The naming system is meant to preserve both machine readability and human scanability. Version identifiers should stay in the ID when the object represents a versioned technology.

## Browser UI Contract

The browser is a fully static HTML document generated by Python. The only client-side library is Cytoscape.js from a CDN, and even then Cytoscape is used only for graph views that benefit from node-edge rendering. List and topology views are implemented as HTML and CSS layouts.

The generator must remain data-driven. It should load objects from YAML, build a single registry keyed by `id`, build a cross-reference index, and embed JSON into the generated HTML.

### List View

List View is the default catalog browsing mode. It shows object cards in a responsive grid. The object-type filter options should be generated from the set of types actually present in the loaded registry rather than from a hardcoded list. Each card should show:

- object name
- object ID
- lifecycle badge
- catalog status badge
- any type-specific secondary badge, such as ARD category or Product Service product label

Clicking any card navigates to that object’s detail view.

### Detail View

Detail View dispatches on `object.type` only. There must be no routing logic based on specific object IDs or product names.

Expected renderers:

- ODC detail: requirements document layout
- ARD detail: structured risk/decision card
- Product Service detail: product, `runsOn`, lifecycle, description, and Architecture Decisions
- Software Distribution Manifest detail: details tab plus deployment topology tab
- RBB and ABB detail: internal components, interactions, decisions, and any ODC or usage panels
- unknown type: generic key-value fallback view

Detail views should also include a `Used By` panel sourced from the reverse cross-reference index wherever references exist.

### Deployment Topology View

The SDM topology view is an HTML/CSS spatial layout, not a Cytoscape graph. It should be completely rebuildable from SDM YAML plus resolved references.

Rendering rules:

- external interactions render as a horizontal strip across the top
- every distinct `location` found in deployed Product Services and deployed RBBs creates a location box
- unknown location patterns must still render with a generic badge and icon
- Product Services render as topology cards with a `PS` badge, optional intent badge, and optional ARD warning badge
- topology cards are clickable and navigate via the shared ID-based navigation path
- Product Services that run on a resolved host RBB whose ID starts with `rbb.host.container.` are grouped into an inner EKS-style container
- SDM topology layout is driven by `diagramTier`, with deployment targets as the primary containers and scaling units as optional grouping overlays
- if a `riskRef` does not resolve, the view must show a broken or missing indicator rather than silently omitting it

### Impact Analysis

Impact Analysis is a separate mode that uses the cross-reference graph rather than fixed hardcoded relationship lists. It should operate recursively over outbound and inbound references. The presentation can still order types for readability, but the traversal itself must be generic.

Impact Analysis includes:

- a search box
- a grouped impacted-object list
- a graph view
- lifecycle visibility toggles generated from lifecycle values present in the registry

### Navigation

Navigation uses object IDs universally. Clicking a card, diagram node, topology node, ARD badge, or cross-reference link always routes through the same detail navigation function and history stack. Back navigation walks the actual object history rather than reconstructing state ad hoc.

## Generator Contract

The browser generator should follow these rules:

- load all YAML objects from the catalog folders
- register each object in a single `id -> object` registry
- build outbound and inbound reference indexes
- build a compliance index from `compliance_framework` objects
- warn on unresolved references instead of crashing
- generate list filters from data
- generate lifecycle filters from data
- render all known object types by `type`
- provide a generic fallback for unknown types
- avoid hardcoded product names, IDs, filenames, and location names in rendering logic

## Tooling Constraints

The repository should remain Python-only. `pyyaml` is the only required dependency. No Node.js, npm, bundlers, or local JavaScript build chain should be introduced. The browser output should always be generated into `docs/index.html`, and that HTML file should be treated as generated output rather than hand-edited source.

## Rebuild Summary

If you are rebuilding this repository from scratch, the required deliverables are:

1. A YAML catalog folder structure containing the object families described above.
2. A validator that enforces base fields, type-specific IDs, machine-readable decisions, reference resolution, and ODC satisfaction.
3. A browser generator that loads YAML into a registry, builds cross-reference indexes, and renders list, detail, impact, and deployment topology views from data.
4. Framework documentation that explains the object model, naming rules, and governance intent.
5. GitHub automation that runs validation and regenerates the browser on catalog changes.

If those pieces exist and follow the rules in this document, DRAFT — Deployable Reference Architecture Framework Toolkit — has been rebuilt faithfully in the `draft-framework` repository.
