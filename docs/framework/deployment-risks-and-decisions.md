# Deployment Risks And Decisions

Deployment Risks and Decisions are first-class records for known risks,
accepted decisions, mitigations, and follow-up paths tied to deployed
architecture.

The current machine-readable object type is `ard` because the object originally
used the Architecture Risk/Decision name. DRAFT documentation may refer to the
family as DRDs, but YAML objects still use `type: ard` and IDs matching
`ard.<scope>.<number>`.

## When To Use One

Create a DRD/ARD when architecture work needs to preserve one of these facts:

- a known runtime risk such as a single point of failure, unsupported platform,
  security gap, or migration dependency
- an accepted architectural decision with rationale
- a mitigation path that is not yet complete
- a product-specific exception attached to an SDM or service group

Do not use a DRD/ARD as a dumping ground for ordinary implementation notes.
If the detail is a stable reusable behavior, it likely belongs on an RBB,
deployment configuration, ABB configuration, or SDM.

## YAML Shape

The authoritative schema is [ard.schema.yaml](../../schemas/ard.schema.yaml).

At minimum, a DRD/ARD includes:

- `id`
- `type: ard`
- `name`
- `category`
- `status`
- `description`
- `affectedComponent`
- `impact`

Decision records also require `decisionRationale`.

## Relationship To SDMs

An SDM can reference DRDs/ARDs under `architectureRisksAndDecisions`. Use this
when a product deployment needs visible risk or decision context without
overloading the SDM prose.
