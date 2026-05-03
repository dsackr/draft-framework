# Decision Records

Decision Records are first-class records for known risks,
accepted decisions, mitigations, and follow-up paths tied to deployed
architecture.

The machine-readable object type is `decision_record`. The generated `uid` is
the stable machine reference; use `name` and `aliases` for human resolution.

## When To Use One

Create a Decision Record when architecture work needs to preserve one of these facts:

- a known runtime risk such as a single point of failure, unsupported platform,
  security gap, or migration dependency
- an accepted architectural decision with rationale
- a mitigation path that is not yet complete
- a product-specific exception attached to a Software Deployment Pattern or service group

Do not use a Decision Record as a dumping ground for ordinary implementation notes.
If the detail is a stable reusable behavior, it likely belongs on a Standard,
deployment configuration, Technology Component configuration, or Software Deployment Pattern.

## YAML Shape

The authoritative schema is [decision-record.schema.yaml](../schemas/decision-record.schema.yaml).

At minimum, a Decision Record includes:

- `uid`
- `type: decision_record`
- `name`
- `category`
- `status`
- `description`
- `affectedComponent`
- `impact`

Decision records also require `decisionRationale`.

## Relationship To Software Deployment Patterns

A Software Deployment Pattern can reference Decision Records under `decisionRecords`. Use this
when a product deployment needs visible risk or decision context without
overloading the Software Deployment Pattern prose.
