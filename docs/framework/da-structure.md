# SDM Structure

## Why The SDM Model Changed

The Software Distribution Manifest model now centers on service groups and
scaling units rather than a flat list of deployed components. That change makes
the deployment structure closer to how architects actually describe real
platforms during interviews.

Instead of saying only that a product deploys a set of RBBs, the framework can
now express which components belong together, where they are deployed, which
scaling boundary they share when one exists, and which integrations are
external versus internal within the same manifest.

## Scaling Units

A scaling unit is an optional shared scaling boundary. It answers the question:
which sets of services scale together as one operational unit?

Each scaling unit has:

- `name`
- `type`, which is `replicable` or `shared`
- optional `instanceCount`
- optional notes

A scaling unit should be present only when the grouping is architecturally real.
It is not a generic visual container. If a service group does not scale together
with other groups, leave `scalingUnit` unset.

## Service Groups

A service group is the primary structure inside an SDM. It captures a logical
group of deployed components that belong together and share a deployment target.

Each service group has:

- `name`
- `deploymentTarget`
- optional `scalingUnit`
- optional `productServices`
- optional `rbbs`
- optional `applianceAbbs`
- optional `saasServices`
- optional `externalInteractions`

The goal is to let the architect describe the deployment in terms of meaningful
operational groupings rather than forcing everything into one flat table.

## Deployment Target

`deploymentTarget` is free text. It should describe where the service group
lives, such as an AWS account, datacenter, or other meaningful deployment
boundary. In the topology view, deployment target is the primary placement
container. The browser uses string heuristics only to decorate the target
visually. The YAML remains the source of truth.

## Placement And Scaling Hierarchy

The framework should be read in this order:

1. `deploymentTarget`
2. optional `scalingUnit`
3. `serviceGroup`

If two service groups share a deployment target but not a scaling unit, they
should still render together under that deployment target. If two service groups
share a scaling-unit name but live in different deployment targets, they should
render in separate deployment-target containers.

## Intent Field Rules

The `intent` field on Software Service and RBB entries is deliberately narrow.

It is only set when the architect is making an explicit architectural decision
that deviates from the Reference Architecture default, or when there is no
Reference Architecture at all.

That means `intent` should **not** be populated merely to describe the current
production state. Current state belongs in ARDs and notes. Intent is for
deliberate architecture choice.

Examples:

- If the Reference Architecture expects `ha`, and the service is intentionally
  deployed as `sa`, set `intent: sa` and link the relevant ARD.
- If there is no applicable Reference Architecture, `intent` can be used to
  declare the intended posture directly.
- If the deployment simply conforms to the Reference Architecture default, leave
  `intent` unset.

## Internal And External Interactions

Service-group interactions now distinguish between:

- `type: external` for systems outside the manifest boundary
- `type: internal` for connections between service groups in the same manifest

Internal interactions must reference another service-group name in the same SDM.
This gives the topology view enough structure to show inter-group relationships
without inventing new deployment objects. External interactions remain attached
to the service group that owns them; they should not be hoisted to the SDM as a
top-level strip.
