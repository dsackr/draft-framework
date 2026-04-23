# RBBs

## What An RBB Is

An RA Building Block, or RBB, is the framework's only reusable building-block
architecture type. This is the level where the catalog stops describing
individual products and starts describing reusable runtime and service patterns.

RAs and SDMs are built from RBBs, not directly from ABBs, because the RBB is where the framework captures structure, interactions, and decisions.

## YAML Shape

RBBs follow the authoritative
[rbb.schema.yaml](../../schemas/rbb.schema.yaml) schema and are enforced by
[`tools/validate.py`](../../tools/validate.py).

At minimum, an RBB YAML should include:

- `id`
- `type: rbb`
- `name`
- `catalogStatus`
- `lifecycleStatus`
- `internalComponents`
- `variants`

## RBB Classifications

The framework taxonomy organizes reusable and deployed service patterns around
these classifications:

| Classification | Purpose |
|---|---|
| Host | The runtime substrate on which services run. |
| General Service | A reusable non-database service pattern that runs on a host or managed substrate. |
| Database Service | A reusable data-platform service pattern with durability, recovery, and access-control concerns. |
| SaaS Service | A vendor-managed service classification used when traffic or data may leave the infrastructure boundary. The current machine-readable object type remains `saas_service` because it carries vendor and data-governance metadata. |
| Product Service | A first-party service classification used when organization-authored code runs on an RBB or blackbox host pattern. The current machine-readable object type remains `product_service` because it carries product ownership and deployment metadata. |

The current machine-readable repo represents Host, General Service, and Database
Service directly as `rbb` objects. SaaS Service and Product Service are modeled
as adjacent first-class objects because they need additional metadata, but they
still belong to the same service taxonomy discussion when architects choose how
to model a deployed service.

## Host Classification

A host RBB represents a standardized host platform. It includes:

- the operating system ABB
- the hardware ABB
- any agent ABBs physically installed on the host
- `externalInteractions` with platforms the host communicates with

Those are not the same thing as internal components. An internal component is part of the host. An external interaction is something outside the host boundary that the host depends on or communicates with.

Concrete example: `rbb.host.windows.2022.ec2.standard` includes CrowdStrike Falcon, Automox, and Dynatrace agents as internal components because they are installed on the host. It also declares external interactions with the CrowdStrike platform, Automox patch management, Dynatrace, centralized logging, and Active Directory because those systems exist outside the host boundary.

## General Service And Database Service Classifications

A service RBB composes a host RBB with one function ABB. This is the
framework’s way of saying that a reusable service capability is not just
software in the abstract. It is software running on a specific host pattern
with specific interactions and decisions layered on top.

Concrete example: `rbb.service.dbms.sqlserver-2022` references `rbb.host.windows.2022.ec2.standard` as `hostRbb` and `abb.software.microsoft-sqlserver-2022` as `functionAbb`. That tells an engineer two important things immediately:

- the database service is built on the standard Windows 2022 EC2 host pattern
- the function-defining software is SQL Server 2022

From there, the service RBB adds database-specific external interactions and
variant-specific architectural decisions such as backup strategy, RTO, RPO, and
HA mechanism.

General Service and Database Service are both service-side classifications of
the same reusable building-block concept. The difference is scope:

- General Service captures reusable non-database service patterns.
- Database Service captures reusable database patterns with explicit data
  durability and protection concerns.

## Variants And Architectural Decisions

Variants are a core part of the RBB model. The keys under `variants` are open-ended and descriptive. `ha` and `sa` are common examples, but they are not the only valid values. Other valid examples include `hp`, `sp`, `geo-redundant`, and `single-region`. Each named variant has its own `architecturalDecisions` map.

Those decisions capture the operating posture of that variant: node counts, patching cadence, backup approach, autoscaling expectations, and any other design choices that matter.

Important: `architecturalDecisions` values must be machine-readable. Use the constrained enums defined in the schema for known keys. Do not use prose values. These fields are intended to drive IaC automation in a future phase.

### Common Variant Examples

A high-availability variant is intended for workloads that need resilience against node or instance failure. It usually implies more nodes, explicit failover or traffic management behavior, and tighter recovery expectations.

A standard-availability variant is intended for less demanding or less complex use cases. It may still be production-grade, but it accepts a simpler failure model and usually lower operational overhead.

The important rule is not that HA must always mean three nodes or that SA must always mean one node. The important rule is that the YAML must document the decisions that define the posture of the named variant. The validator cares that at least one named variant exists and that the variant carries architectural decisions. It does not require specific keys like `ha` or `sa`.

## External Interactions As Black Boxes

External interactions are treated as black boxes by design.

An RBB is complete if it documents the fact that it interacts with authentication, logging, monitoring, patching, or another platform, regardless of whether the interacted-with thing exists in the catalog as a first-class object. The `ref` field is optional enrichment, not a prerequisite for completeness.

That means a host RBB can be complete even if its logging platform is not modeled elsewhere in the repo. The point is to declare the dependency clearly, not to block architecture documentation until every connected platform has been cataloged.

## How To Add A New RBB

1. Decide whether you are modeling a Host, General Service, or Database Service
   RBB.
2. Choose the correct ID convention and folder.
3. Add the shared base fields.
4. If the RBB is a host, specify `osAbb`, `hardwareAbb`, and the internal
   components that live on the host.
5. If it is a service, specify `hostRbb`, `functionAbb`, and any service-level
   external interactions that go beyond the host already declares.
6. Add `variants` and document the architectural decisions for each supported variant.
7. Set `satisfiesAAG` and run validation.

The validation step matters more for RBBs than for any other object type because this is where the governance model is enforced.

## FAQ

### Can a service RBB reference multiple host RBBs?

No. A service RBB is meant to describe one reusable service pattern composed from one host pattern and one function ABB. If a service really needs materially different host substrates, that is usually a sign that you need separate service RBBs.

### What is the difference between an internal component and an external interaction?

If the thing is deployed on or inside the object, it is an internal component. If the object talks to it across a boundary, it is an external interaction.

### Where do Product Services and SaaS Services fit?

They are part of the service taxonomy, but they are not modeled as reusable
`rbb` objects in the current machine-readable repo.

- Use an RBB when you are defining a reusable host or service pattern.
- Use a Product Service when you are documenting first-party code deployed on a
  reusable pattern.
- Use a SaaS Service when the service is vendor-managed and may carry data
  outside the infrastructure boundary.

### Why does an agent ABB appear as both an internal component and enable an external interaction?

That is not duplication. The internal component tells you what is physically present on the host. The `enabledBy` field on the external interaction tells you which internal component makes the external dependency possible.
