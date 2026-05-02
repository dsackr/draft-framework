# Standards

## What A Standard Is

A Standard is a reusable architecture object. It is the layer where the catalog defines
reusable runtime and service patterns that can be referenced by Reference
Architectures and Software Deployment Patterns.

Reference Architectures and Software Deployment Patterns are built from Standards, not directly from Technology Components, because the Standard is
where the framework captures the reusable architecture contract: what the thing
is made of, what it interacts with, and which architectural decision entries explain
the pattern.

## YAML Shape

Standards follow the authoritative
schema for their specific kind, such as
[host-standard.schema.yaml](../schemas/host-standard.schema.yaml),
[service-standard.schema.yaml](../schemas/service-standard.schema.yaml), or
[database-standard.schema.yaml](../schemas/database-standard.schema.yaml), and are enforced by
[`framework/tools/validate.py`](../tools/validate.py).

At minimum, a Standard YAML should include:

- `id`
- `type: host_standard`, `service_standard`, or `database_standard`
- `name`
- `catalogStatus`
- `lifecycleStatus`
- `internalComponents`
- `externalInteractions`

`architecturalDecisions` is optional at the schema level, but it becomes
required whenever a Requirement Group requirement needs an answer that the
object does not provide directly.

Standards may also declare `deploymentConfigurations`. These are optional reusable
deployment overlays on the Standard itself. A deployment configuration can carry
named availability, scalability, or recoverability patterns without turning
those qualities into separate object types.

## Standard Classifications

The framework taxonomy organizes Standards into these classifications:

| Classification | Purpose |
|---|---|
| Host | The runtime substrate on which reusable or product-specific services run. |
| General Service | A reusable non-database service pattern that runs on a host or equivalent managed substrate. |
| Database Service | A reusable data-platform service pattern with durability, recovery, and access-control capabilities. |
| PaaS Service | A vendor-managed platform service classification used when the managed capability stays inside the organization's cloud boundary. It uses `type: paas_service_standard`. |
| SaaS Service | A vendor-managed service classification used when traffic or data may leave the infrastructure boundary. It uses `type: saas_service_standard`. |
| Product Service | A first-party service classification used when a Software Deployment Pattern needs to express a distinct runtime-behavior component deployed on a Standard or blackbox host pattern. It uses `type: product_service`. |

Reference Architectures and Software Deployment Patterns are top-level architecture objects. They are not Standard
classifications.

## The Three Core Standard Concepts

Every Standard uses the same three architecture concepts.

### Internal Components

Internal Components are the Technology Components or Standards that exist inside the boundary of the
Standard being described.

For a host Standard, that means the operating system, hardware substrate, and any
agents installed on the host. For a service Standard, that means the host pattern it
runs on and the function-defining component that gives the service its purpose.

Because Technology Component classifications are machine-readable, Standard validation can reason
about what kind of vendor product has been attached. A host Standard can therefore
be checked against Operating System, Compute Platform, Software, and Agent Technology Component
semantics instead of relying only on naming conventions.

### External Interactions

External Interactions declare systems, services, or platforms outside the Standard
boundary that the Standard communicates with or depends on. An external interaction
may optionally point to another catalog object with `ref`, but that is
enrichment, not a prerequisite for completeness.

### Architectural Decision Entries

Architectural decision entries are where the object explains required answers that are
not otherwise expressed directly in the object shape, and where it justifies
non-obvious additions.

An architectural decision entry is required when:

- a Requirement Group requirement requires an answer and the object does not
  provide that answer directly
- an internal component is added that is not required by a Requirement Group
- an external interaction is added that is not required by a Requirement Group or
  requirement evidence

Architectural decision entries should reference the triggering Requirement Group requirement,
or added component or interaction.

## Host Classification

A host Standard represents a standardized host platform. It typically includes:

- one Operating System Technology Component
- one Compute Platform Technology Component
- any Agent Technology Components physically installed on the host
- any host-baseline architectural decision entries needed to answer Requirement Group or compliance
  questions that are not otherwise explicit

Those are not the same thing as external interactions. An internal component is
part of the host. An external interaction is something outside the host
boundary that the host depends on or communicates with.

If an Agent Technology Component is present on the host, the host Standard must also document the
corresponding external interaction unless an architectural decision entry explicitly
records the exception. The machine-readable exception path is
`architecturalDecisions.agentInteractionExceptions`. Software Technology Components do not carry
that requirement.

Required host capabilities such as logging, monitoring, security monitoring, and
patch management may be satisfied through an Agent Technology Component, a Software Technology Component, a
named Technology Component configuration, an external interaction, or an architectural decision.

Host Requirement Groups should define the host itself and its baseline controls. They should
not force service or data capabilities such as backup strategy onto the host object.

## General Service And Database Service Classifications

A General Service or Database Service Standard composes a host or managed substrate
with the function-defining component that gives the service its purpose. This
is the framework’s way of saying that a reusable service capability is not just
software in the abstract. It is software running on a specific pattern with
specific interactions and decisions layered on top.

General Service and Database Service are both service-side classifications of
the same reusable building-block concept. The difference is scope:

- General Service captures reusable non-database service patterns.
- Database Service captures reusable database patterns with explicit data
  durability and protection capabilities.

For a General Service, the structural baseline is:

- one `hostStandard`
- one `primaryTechnologyComponent`

The General Service Requirement Group then asks for the required service answers:

- service authentication
- secrets management
- service logging
- health and welfare monitoring
- availability
- scalability
- recoverability
- failure domain

Availability, scalability, and recoverability can be answered through direct
architectural decision entries or by selecting a named `deploymentConfiguration` on the
Standard. Failure domain is treated as an explicit architectural property rather
than a deployment configuration.

## Product Service, PaaS Service, And SaaS Service Classifications

Product Service, PaaS Service, and SaaS Service are also Standard classifications.

- Product Service is used when a Software Deployment Pattern needs to express a distinct first-party
  runtime-behavior component deployed on a Standard or blackbox host pattern.
- PaaS Service is used when a vendor-managed platform capability is adopted
  inside the organization's cloud boundary.
- SaaS Service is used when a vendor-managed service may route data or traffic
  outside the infrastructure boundary.

These are not separate peer object types in the architecture taxonomy. They are
service-side Standard classifications with additional metadata fields.

Appliance Components are the deliberate exception to the Standard composition path. They
are Technology Components because they map directly to vendor products, but they provide a
deployed service-like capability without exposing a host Standard or service Standard
wrapper. Because they do not inherit `requirement-group.host-standard` or `requirement-group.service-standard`, the appliance
Requirement Group asks the required operating and governance capability questions directly on
the appliance Technology Component.

## External Interactions As Black Boxes

External interactions are treated as black boxes by design.

A Standard is complete if it documents the fact that it interacts with
authentication, logging, monitoring, patching, or another platform, regardless
of whether the interacted-with thing exists in the catalog as a first-class
object. The `ref` field is optional enrichment, not a prerequisite for
completeness.

That means a host Standard can be complete even if its logging platform is not
modeled elsewhere in the repo. The point is to declare the dependency clearly,
not to block architecture documentation until every connected platform has been
cataloged.

## How To Add A New Standard

1. Decide which Standard classification you are modeling.
2. Choose the correct ID convention and folder.
3. Add the shared base fields.
4. If the Standard is a host, specify the internal components that live on the host.
5. If it is a service, specify the host or managed substrate it runs on and the
   function-defining component that gives the service its purpose.
6. Add any architectural decision entries required by the Requirement Group or attached compliance
   profile when the object does not answer the question directly.
7. Add `requirementGroups` only for Requirement Groups the Standard explicitly claims to
   satisfy, then add valid `requirementImplementations` for every applicable
   control in each declared profile.
8. Set `requirementGroups` and run validation.

The validation step matters more for Standards than for any other object type
because this is where the checklist and compliance model are enforced.

## FAQ

### What is the difference between an internal component and an external interaction?

If the thing is deployed on or inside the object, it is an internal component.
If the object talks to it across a boundary, it is an external interaction.

### Where do Product Services, PaaS Services, and SaaS Services fit?

They are Standard classifications.

- Use Product Service when the object represents organization-authored code.
- Use PaaS Service when the object represents a managed cloud platform adopted
  inside the organization's boundary.
- Use SaaS Service when the object represents a vendor-managed service that may
  carry data or traffic outside the infrastructure boundary.
- Use the other Standard classifications for reusable host and reusable service
  patterns that are not first-party workloads or SaaS dependencies.

### Why does an agent Technology Component appear as both an internal component and enable an external interaction?

That is not duplication. The internal component tells you what is physically
present on the host. The `enabledBy` field on the external interaction tells
you which internal component makes the external dependency possible.
