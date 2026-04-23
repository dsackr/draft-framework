# RBBs

## What An RBB Is

An RBB, or Reference Building Block, is the framework's only reusable
building-block architecture type. It is the layer where the catalog defines
reusable runtime and service patterns that can be referenced by Reference
Architectures and Software Distribution Manifests.

RAs and SDMs are built from RBBs, not directly from ABBs, because the RBB is
where the framework captures the reusable architecture contract: what the thing
is made of, what it interacts with, and which Architecture Decisions explain
the pattern.

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
- `externalInteractions`

`architecturalDecisions` is optional at the schema level, but it becomes
required whenever an ODC requirement or attached compliance control needs an
answer that the object does not provide directly.

RBBs may also declare `deploymentConfigurations`. These are optional reusable
deployment overlays on the RBB itself. A deployment configuration can carry
named availability, scalability, or recoverability patterns without turning
those qualities into separate object types.

## RBB Classifications

The framework taxonomy organizes RBBs into these classifications:

| Classification | Purpose |
|---|---|
| Host | The runtime substrate on which reusable or product-specific services run. |
| General Service | A reusable non-database service pattern that runs on a host or equivalent managed substrate. |
| Database Service | A reusable data-platform service pattern with durability, recovery, and access-control concerns. |
| SaaS Service | A vendor-managed service classification used when traffic or data may leave the infrastructure boundary. It is modeled as an RBB with `category: service` and `serviceCategory: saas`. |
| Product Service | A first-party service classification used when organization-authored code runs on an RBB or blackbox host pattern. It is modeled as an RBB with `category: service` and `serviceCategory: product`. |

RA and SDM are top-level architecture objects. They are not RBB
classifications.

## The Three Core RBB Concepts

Every RBB uses the same three architecture concepts.

### Internal Components

Internal Components are the ABBs or RBBs that exist inside the boundary of the
RBB being described.

For a host RBB, that means the operating system, hardware substrate, and any
agents installed on the host. For a service RBB, that means the host pattern it
runs on and the function-defining component that gives the service its purpose.

Because ABB classifications are machine-readable, RBB validation can reason
about what kind of vendor product has been attached. A host RBB can therefore
be checked against Operating System, Compute Platform, Software, and Agent ABB
semantics instead of relying only on naming conventions.

### External Interactions

External Interactions declare systems, services, or platforms outside the RBB
boundary that the RBB communicates with or depends on. An external interaction
may optionally point to another catalog object with `ref`, but that is
enrichment, not a prerequisite for completeness.

### Architecture Decisions

Architecture Decisions are where the object explains required answers that are
not otherwise expressed directly in the object shape, and where it justifies
non-obvious additions.

An Architecture Decision is required when:

- an ODC question or compliance control requires an answer and the object does
  not provide that answer directly
- an internal component is added that is not required by an ODC or compliance
  control
- an external interaction is added that is not required by an ODC or
  compliance control

Architecture Decisions should reference the triggering ODC requirement,
compliance control, or added component or interaction.

## Host Classification

A host RBB represents a standardized host platform. It typically includes:

- one Operating System ABB
- one Compute Platform ABB
- any Agent ABBs physically installed on the host
- any host-baseline Architecture Decisions needed to answer ODC or compliance
  questions that are not otherwise explicit

Those are not the same thing as external interactions. An internal component is
part of the host. An external interaction is something outside the host
boundary that the host depends on or communicates with.

If an Agent ABB is present on the host, the host RBB must also document the
corresponding external interaction unless an Architecture Decision explicitly
records the exception. The machine-readable exception path is
`architecturalDecisions.agentInteractionExceptions`. Software ABBs do not carry
that requirement.

Required host concerns such as logging, monitoring, security monitoring, and
patch management may be satisfied through an Agent ABB, a Software ABB, a
named ABB configuration, an external interaction, or an architectural decision.

Host ODCs should define the host itself and its baseline controls. They should
not force service or data concerns such as backup strategy onto the host object.

## General Service And Database Service Classifications

A General Service or Database Service RBB composes a host or managed substrate
with the function-defining component that gives the service its purpose. This
is the framework’s way of saying that a reusable service capability is not just
software in the abstract. It is software running on a specific pattern with
specific interactions and decisions layered on top.

General Service and Database Service are both service-side classifications of
the same reusable building-block concept. The difference is scope:

- General Service captures reusable non-database service patterns.
- Database Service captures reusable database patterns with explicit data
  durability and protection concerns.

For a General Service, the structural baseline is:

- one `hostRbb`
- one `functionAbb`

The General Service ODC then asks for the required service answers:

- service authentication
- secrets management
- service logging
- health and welfare monitoring
- availability
- scalability
- recoverability
- failure domain

Availability, scalability, and recoverability can be answered through direct
Architecture Decisions or by selecting a named `deploymentConfiguration` on the
RBB. Failure domain is treated as an explicit architectural property rather
than a deployment configuration.

## Product Service And SaaS Service Classifications

Product Service and SaaS Service are also RBB classifications.

- Product Service is used when organization-authored code runs on an RBB or
  blackbox host pattern.
- SaaS Service is used when a vendor-managed service may route data or traffic
  outside the infrastructure boundary.

These are not separate peer object types in the architecture taxonomy. They are
service-side RBB classifications with additional metadata fields.

## External Interactions As Black Boxes

External interactions are treated as black boxes by design.

An RBB is complete if it documents the fact that it interacts with
authentication, logging, monitoring, patching, or another platform, regardless
of whether the interacted-with thing exists in the catalog as a first-class
object. The `ref` field is optional enrichment, not a prerequisite for
completeness.

That means a host RBB can be complete even if its logging platform is not
modeled elsewhere in the repo. The point is to declare the dependency clearly,
not to block architecture documentation until every connected platform has been
cataloged.

## How To Add A New RBB

1. Decide which RBB classification you are modeling.
2. Choose the correct ID convention and folder.
3. Add the shared base fields.
4. If the RBB is a host, specify the internal components that live on the host.
5. If it is a service, specify the host or managed substrate it runs on and the
   function-defining component that gives the service its purpose.
6. Add any Architecture Decisions required by the ODC or attached compliance
  framework when the object does not answer the question directly.
7. Set `satisfiesODC` and run validation.

The validation step matters more for RBBs than for any other object type
because this is where the checklist and compliance model are enforced.

## FAQ

### What is the difference between an internal component and an external interaction?

If the thing is deployed on or inside the object, it is an internal component.
If the object talks to it across a boundary, it is an external interaction.

### Where do Product Services and SaaS Services fit?

They are RBB classifications.

- Use Product Service when the object represents organization-authored code.
- Use SaaS Service when the object represents a vendor-managed service that may
  carry data or traffic outside the infrastructure boundary.
- Use the other RBB classifications for reusable host and reusable service
  patterns that are not first-party workloads or SaaS dependencies.

### Why does an agent ABB appear as both an internal component and enable an external interaction?

That is not duplication. The internal component tells you what is physically
present on the host. The `enabledBy` field on the external interaction tells
you which internal component makes the external dependency possible.
