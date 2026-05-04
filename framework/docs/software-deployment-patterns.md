# Software Deployment Patterns

## What A Software Deployment Pattern Is

A Software Deployment Pattern is a declaration that a specific product is intended
to be distributed and deployed according to a particular pattern.

Unlike a Reference Architecture, which is generic, a Software Deployment Pattern
is tied to a named product. It answers the question “what does this product
deploy?” rather than “what does this class of solution usually require?”

## What A Software Deployment Pattern Contains

The defining structure in a Software Deployment Pattern is no longer a flat deployment list. A Software Deployment Pattern is
organized around:

- `scalingUnits`
- `serviceGroups`
- `businessContext`
- `architecturalDecisions`
- `decisionRecords`

Each service group can contain deployable object references and group-local
external interactions. This is a better fit for real
architecture interview data because it preserves operational grouping and
deployment intent.

Within those service groups, the primary visual objects in the topology are the
deployed object entries themselves.

Each of those entries must declare `diagramTier` as one of:

- `presentation`
- `application`
- `data`
- `utility`

That field is what drives column placement in the topology view. The renderer
should not guess service placement from names or references when the manifest
can state the intended architecture directly.

`scalingUnits` is optional. Use it only when a set of service groups truly
shares a scaling boundary. If a service group does not participate in a scaling
unit, model it directly rather than forcing it into a placeholder group.

## YAML Shape

The canonical schema notes for Software Deployment Patterns live in [software-deployment-pattern.schema.yaml](../schemas/software-deployment-pattern.schema.yaml).

At minimum, a Software Deployment Pattern includes:

- `uid`
- `type: software_deployment_pattern`
- `name`
- `catalogStatus`
- `lifecycleStatus`

The main Software Deployment Pattern structure is:

- optional `followsReferenceArchitecture`
- optional `businessContext`
- optional `architecturalDecisions`
- optional `scalingUnits`
- optional `serviceGroups`
- optional `decisionRecords`

Each scaling unit includes:

- `name`
- `type`
- optional `instanceCount`
- optional `notes`

Each service group includes:

- `name`
- `deploymentTarget`
- optional `scalingUnit`
- optional `deployableObjects`
- optional `externalInteractions`

Each deployable object entry should declare:

- `ref`
- optional `diagramTier`
- optional `intent`
- optional `riskRef`
- optional `notes`

## Business Context

Software Deployment Patterns may include `businessContext` so a company can
quickly see which business pillar, portfolio, or product family a pattern
belongs to. This is intentionally workspace-owned. The framework defines the
field and validation behavior, but the company declares the actual taxonomy in
`.draft/workspace.yaml`.

Example:

```yaml
businessContext:
  pillar: business-pillar.human-capital-management
  additionalPillars:
    - business-pillar.student-management
  productFamily: Absence & Time
  notes: Primary ownership follows the HCM portfolio; student-management impact
    exists through district-facing attendance workflows.
```

If `.draft/workspace.yaml` defines `businessTaxonomy.pillars`, validation checks
that `businessContext.pillar` and any `additionalPillars` use declared pillar
IDs. A workspace can also set
`businessTaxonomy.requireSoftwareDeploymentPatternPillar: true` to require every
Software Deployment Pattern to declare a primary pillar.

## What `followsReferenceArchitecture` Means

The `followsReferenceArchitecture` field tells the reader which Reference Architecture the deployment claims to follow.

This field is metadata only. It is useful because it says whether the product is aligned to a recognized pattern, but it is not itself a deployed object and should not be rendered as a node in a deployment diagram.

If no suitable Reference Architecture exists yet, that gap should be made
explicit through an architectural decision entry rather than hidden.

## Requirement Group Expectations

The Software Deployment Pattern Requirement Group is the deployment-reality checklist. It requires the architect to
document:

- the selected Reference Architecture, or why no applicable Reference Architecture exists
- the deployed service-group structure
- the deployment targets used by those service groups
- the product availability requirement
- any product-specific interactions beyond the component deployable object baseline
- the governing data classification
- the deployment-level failure domain
- any intentional deviations from the selected Reference Architecture, or an explicit statement
  that none exist

## Intent Versus Current State

The `intent` field on deployed object entries exists only for explicit
architecture choice. It should be populated when the architect is intentionally
deviating from the Reference Architecture, or when no Reference Architecture
exists.

It should not be used as a shorthand way to restate current production state.
Current state capabilities belong in Decision Records and notes.

## Structure Rules

`serviceGroup` is the primary structural and visual container. It answers what
role a cluster of deployed components plays in the product.

`deploymentTarget` is metadata on the service group. It answers where that
group runs.

`diagramTier` places deployed objects into one of four columns:

- `presentation`
- `application`
- `data`
- `utility`

`scalingUnit` is secondary and optional. It should be used only when a set of
service groups truly scales together. It is not a generic visual container.

If two services share a deployment target but play different roles, they should
still live in different service groups. Do not use deployment targets as group
names. Good group names describe function, such as `Web Edge Services`,
`Application Services`, or `Data Services`.

Internal and external interactions remain attached to the owning service group:

- `type: internal` means another service group in the same Software Deployment Pattern
- `type: external` means a system outside the Software Deployment Pattern boundary

Internal interactions must reference another service-group name in the same
Software Deployment Pattern. External interactions stay attached to the service group that owns them;
they should not be hoisted to the Software Deployment Pattern top level.

## How The Topology Should Read

The Software Deployment Pattern topology is a service-first placement view.

- `serviceGroup` is the primary container because it answers what a set of
  deployed components does.
- `deploymentTarget` stays visible as metadata on that group.
- `diagramTier` places deployed objects into the
  `presentation`, `application`, `data`, or `utility` column.
- `scalingUnit` is secondary and optional. It should be treated as an overlay
  or highlight concept that answers which services scale together, not as the
  primary layout primitive.

That means one deployment target can host multiple service groups, and each
group can still place its runtime components into different tiers. Scaling
units can be highlighted across multiple groups without taking over the base
layout.

## Long-Term Placement

The v1 catalog contains example Software Deployment Patterns in this central repository because the framework needs real examples.

Long term, that is not the target operating model. Product-specific Software
Deployment Patterns belong closest to the product that owns them, which usually
means the product repository. The central catalog should define reusable
building blocks and reference patterns. Product repos should eventually own the
declarations that map those deployable objects to live product estates.

## Partial Software Deployment Pattern Drafting

When a Software Deployment Pattern interview is incomplete, do not force every unresolved note into the
Software Deployment Pattern itself. Use a Drafting Session to hold:

- source pages and interview context
- provisional assumptions that let the Software Deployment Pattern validate
- unresolved questions that still need answers
- next steps for the follow-up pass

That lets the Software Deployment Pattern stay deployable and reviewable while the open questions remain
easy to revisit later.

## FAQ

### Does every product need a Software Deployment Pattern?

In the long run, yes, if the product has meaningful architecture that needs to be reviewed, supported, or governed. A missing Software Deployment Pattern should usually be treated as a gap to close, not as proof that the framework does not apply.

### What if my product does not fit any existing Reference Architecture?

Do not force the product into an obviously wrong pattern. Treat that as a signal. Either the product is a legitimate exception that needs to be documented clearly, or the catalog is missing a Reference Architecture that should exist.
