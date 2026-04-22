# Software Distribution Manifests

## What An SDM Is

A Software Distribution Manifest, or SDM, is a declaration that a specific product is distributed and deployed according to a particular pattern.

Unlike an RA, which is generic, an SDM is tied to a named product. It answers the question “what does this product deploy?” rather than “what does this class of solution usually require?”

## What An SDM Contains

The defining structure in an SDM is no longer a flat deployment list. An SDM is
organized around:

- `scalingUnits`
- `serviceGroups`
- `architecturalDecisions`
- `architectureRisksAndDecisions`

Each service group can contain Software Services, RBBs, Appliance ABBs, SaaS
Services, and group-local external interactions. This is a better fit for real
architecture interview data because it preserves operational grouping and
deployment intent.

Within those service groups, the primary visual objects in the topology are the
deployed services themselves:

- Software Services
- RBBs

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

The canonical schema notes for SDMs live in [sdm.schema.yaml](../../schemas/sdm.schema.yaml).

At minimum, an SDM includes:

- `id`
- `type: software_distribution_manifest`
- `name`
- `catalogStatus`
- `lifecycleStatus`

The main SDM structure is:

- optional `appliesPattern`
- optional `architecturalDecisions`
- optional `scalingUnits`
- optional `serviceGroups`
- optional `architectureRisksAndDecisions`

Each scaling unit includes:

- `name`
- `type`
- optional `instanceCount`
- optional `notes`

Each service group includes:

- `name`
- `deploymentTarget`
- optional `scalingUnit`
- optional `productServices`
- optional `rbbs`
- optional `applianceAbbs`
- optional `saasServices`
- optional `externalInteractions`

Each deployed Software Service or RBB entry should declare:

- `ref`
- optional `diagramTier`
- optional `intent`
- optional `riskRef`
- optional `notes`

## What `appliesPattern` Means

The `appliesPattern` field tells the reader which RA the deployment claims to follow.

This field is metadata only. It is useful because it says whether the product is aligned to a recognized pattern, but it is not itself a deployed object and should not be rendered as a node in a deployment diagram.

## Intent Versus Current State

The `intent` field on Software Service and RBB entries exists only for explicit
architecture choice. It should be populated when the architect is intentionally
deviating from the Reference Architecture, or when no Reference Architecture
exists.

It should not be used as a shorthand way to restate current production state.
Current state concerns belong in ARDs and notes.

## Structure Rules

`deploymentTarget` is the primary placement container. It answers where a
service runs.

`diagramTier` places Software Services and RBBs into one of four columns:

- `presentation`
- `application`
- `data`
- `utility`

`serviceGroup` remains a structural construct in YAML, but it is not the
dominant visual object in the topology.

`scalingUnit` is secondary and optional. It should be used only when a set of
service groups truly scales together. It is not a generic visual container.

If two services share a deployment target but declare different `diagramTier`
values, they render in different columns. If two services share a scaling-unit
name but live in different deployment targets, they still render in separate
deployment-target containers because placement is primary.

Internal and external interactions remain attached to the owning service group:

- `type: internal` means another service group in the same SDM
- `type: external` means a system outside the SDM boundary

Internal interactions must reference another service-group name in the same
SDM. External interactions stay attached to the service group that owns them;
they should not be hoisted to the SDM top level.

## How The Topology Should Read

The SDM topology is a service-first placement view.

- `deploymentTarget` is the primary container because it answers where a
  service runs.
- `diagramTier` places Software Services and RBBs into the
  `presentation`, `application`, `data`, or `utility` column.
- `serviceGroup` remains a structural construct in YAML, but it is not the
  dominant visual object in the topology.
- `scalingUnit` is secondary and optional. It should be treated as an overlay
  or highlight concept that answers which services scale together, not as the
  primary layout primitive.

That means services in the same deployment target can land in different columns
even when they belong to the same service group. It also means a scaling unit
can be highlighted across multiple services without taking over the base
placement model.

## Long-Term Placement

The v1 catalog contains example SDMs in this central repository because the framework needs real examples.

Long term, that is not the target operating model. Product-specific software distribution manifests belong closest to the product that owns them, which usually means the product repository. The central catalog should define reusable building blocks and reference patterns. Product repos should eventually own the declarations that map those standards to live product estates.

## FAQ

### Does every product need an SDM?

In the long run, yes, if the product has meaningful architecture that needs to be reviewed, supported, or governed. A missing SDM should usually be treated as a gap to close, not as proof that the framework does not apply.

### What if my product does not fit any existing RA?

Do not force the product into an obviously wrong pattern. Treat that as a signal. Either the product is a legitimate exception that needs to be documented clearly, or the catalog is missing an RA that should exist.
