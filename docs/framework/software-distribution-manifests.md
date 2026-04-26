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

Each service group can contain deployed RBB entries, Appliance ABBs, and
group-local external interactions. Product Services and SaaS Services are both
RBB classifications, so they appear inside the same `rbbs` collection. This is
a better fit for real
architecture interview data because it preserves operational grouping and
deployment intent.

Within those service groups, the primary visual objects in the topology are the
deployed RBB entries themselves.

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
- optional `rbbs`
- optional `applianceAbbs`
- optional `externalInteractions`

Each deployed RBB entry should declare:

- `ref`
- optional `diagramTier`
- optional `intent`
- optional `riskRef`
- optional `notes`

## What `appliesPattern` Means

The `appliesPattern` field tells the reader which RA the deployment claims to follow.

This field is metadata only. It is useful because it says whether the product is aligned to a recognized pattern, but it is not itself a deployed object and should not be rendered as a node in a deployment diagram.

If no suitable RA exists yet, that gap should be made explicit through an
architectural decision rather than hidden.

## ODC Expectations

The SDM ODC is the deployment-reality checklist. It requires the architect to
document:

- the selected RA, or why no applicable RA exists
- the deployed service-group structure
- the deployment targets used by those service groups
- the product availability requirement
- any product-specific interactions beyond the component RBB baseline
- the governing data classification
- the deployment-level failure domain
- any intentional deviations from the selected RA, or an explicit statement
  that none exist

## Intent Versus Current State

The `intent` field on deployed RBB entries exists only for explicit
architecture choice. It should be populated when the architect is intentionally
deviating from the Reference Architecture, or when no Reference Architecture
exists.

It should not be used as a shorthand way to restate current production state.
Current state capabilitys belong in ARDs and notes.

## Structure Rules

`serviceGroup` is the primary structural and visual container. It answers what
role a cluster of deployed components plays in the product.

`deploymentTarget` is metadata on the service group. It answers where that
group runs.

`diagramTier` places deployed RBBs into one of four columns:

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

- `type: internal` means another service group in the same SDM
- `type: external` means a system outside the SDM boundary

Internal interactions must reference another service-group name in the same
SDM. External interactions stay attached to the service group that owns them;
they should not be hoisted to the SDM top level.

## How The Topology Should Read

The SDM topology is a service-first placement view.

- `serviceGroup` is the primary container because it answers what a set of
  deployed components does.
- `deploymentTarget` stays visible as metadata on that group.
- `diagramTier` places deployed RBBs into the
  `presentation`, `application`, `data`, or `utility` column.
- `scalingUnit` is secondary and optional. It should be treated as an overlay
  or highlight concept that answers which services scale together, not as the
  primary layout primitive.

That means one deployment target can host multiple service groups, and each
group can still place its runtime components into different tiers. Scaling
units can be highlighted across multiple groups without taking over the base
layout.

## Long-Term Placement

The v1 catalog contains example SDMs in this central repository because the framework needs real examples.

Long term, that is not the target operating model. Product-specific software distribution manifests belong closest to the product that owns them, which usually means the product repository. The central catalog should define reusable building blocks and reference patterns. Product repos should eventually own the declarations that map those standards to live product estates.

## Partial SDM Drafting

When an SDM interview is incomplete, do not force every unresolved note into the
SDM itself. Use a Drafting Session to hold:

- source pages and interview context
- provisional assumptions that let the SDM validate
- unresolved questions that still need answers
- next steps for the follow-up pass

That lets the SDM stay deployable and reviewable while the open questions remain
easy to revisit later.

## FAQ

### Does every product need an SDM?

In the long run, yes, if the product has meaningful architecture that needs to be reviewed, supported, or governed. A missing SDM should usually be treated as a gap to close, not as proof that the framework does not apply.

### What if my product does not fit any existing RA?

Do not force the product into an obviously wrong pattern. Treat that as a signal. Either the product is a legitimate exception that needs to be documented clearly, or the catalog is missing an RA that should exist.
