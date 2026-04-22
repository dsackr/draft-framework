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

`scalingUnits` is optional. Use it only when a set of service groups truly
shares a scaling boundary. If a service group does not participate in a scaling
unit, model it directly rather than forcing it into a placeholder group.

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

## How The Topology Should Read

The SDM topology is first a placement view, then a scaling view.

- `deploymentTarget` is the primary container because it answers where a service
  group runs.
- `scalingUnit` is secondary and optional. It is used only when multiple
  service groups genuinely scale together as one unit.
- Service groups with no `scalingUnit` render directly under their deployment
  target.

That means two service groups in the same deployment target can sit side by side
even when only one participates in a scaling unit. It also means the same
scaling-unit name can appear under different deployment targets if the model
requires that, without implying co-location.

## Long-Term Placement

The v1 catalog contains example SDMs in this central repository because the framework needs real examples.

Long term, that is not the target operating model. Product-specific software distribution manifests belong closest to the product that owns them, which usually means the product repository. The central catalog should define reusable building blocks and reference patterns. Product repos should eventually own the declarations that map those standards to live product estates.

## FAQ

### Does every product need an SDM?

In the long run, yes, if the product has meaningful architecture that needs to be reviewed, supported, or governed. A missing SDM should usually be treated as a gap to close, not as proof that the framework does not apply.

### What if my product does not fit any existing RA?

Do not force the product into an obviously wrong pattern. Treat that as a signal. Either the product is a legitimate exception that needs to be documented clearly, or the catalog is missing an RA that should exist.
