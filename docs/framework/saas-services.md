# SaaS Services

## What A SaaS Service Is

A SaaS Service is a vendor-managed service that the adopting organization
subscribes to. Unlike an Appliance ABB, a SaaS Service may route data through
vendor infrastructure outside the adopter's own boundary. That data-boundary
distinction is the reason SaaS Services need their own distinct RBB
classification.

The framework treats SaaS Services as architecture objects because they affect
data governance, authentication models, compliance posture, and operational
dependency, even when nothing is installed on a host the organization manages.

## When To Use SaaS Service Versus Appliance ABB

Use a SaaS Service when the vendor operates the service in its own environment
and the architecture depends on a subscription relationship.

Use an Appliance ABB when the component is still inside the adopter's
infrastructure boundary, even if the underlying host is opaque and
vendor-managed.

The question to ask is simple: does traffic or data pass into vendor-managed
infrastructure outside the infrastructure boundary? If yes, model it as a SaaS
Service.

## ODC Expectations

The SaaS Service ODC treats the vendor platform as a blackbox. It does not ask
for host, runtime, internal components, or vendor implementation topology. It
focuses only on the answers the consuming organization can know and must
document:

- what function the service provides
- whether data leaves the infrastructure boundary
- the vendor's data residency commitments
- whether a data processing agreement is in place
- what compliance certifications the vendor carries
- how the organization authenticates to the service
- what audit or logging visibility the consumer has
- how the consumer observes health, status, or incidents
- what failure domain the dependency creates
- what SLA the vendor commits to

These are not optional concerns. They are the minimum information needed before
the service can be treated as an understood architecture dependency.

## Architecture Decisions

SaaS Services use the same Architecture Decision trigger logic as every other
RBB classification. If an ODC or compliance control requires an answer and the
object does not provide it directly, an Architecture Decision is required to
explain the answer. The same applies when an internal component or external
interaction is added beyond what the checklist or controls require.

## YAML Shape

SaaS Services use the dedicated
[saas-service.schema.yaml](../../schemas/saas-service.schema.yaml) schema and
are modeled as an RBB classification.

At minimum, a SaaS Service YAML should include:

- `id`
- `type: rbb`
- `category: service`
- `serviceCategory: saas`
- `name`
- `vendor`
- `capability`
- `catalogStatus`
- `lifecycleStatus`
- `dataLeavesInfrastructure`

## Typical Examples

Typical SaaS Service examples include:

- web application firewalls delivered as a subscription
- identity providers
- vendor-hosted monitoring platforms
- integration hubs
- vendor-managed analytics platforms

The exact product set will vary by implementation, but the evaluation model
stays the same.
