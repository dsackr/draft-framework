# PaaS Service Standards

## What A PaaS Service Is

A PaaS Service is a vendor-managed platform capability that stays inside the
organization's cloud boundary.

Use this classification when the organization intentionally adopts a managed
platform such as managed messaging, object storage, CDN, orchestration, or a
managed data platform that still runs inside the organization's cloud estate.

Examples:

- Amazon S3
- Amazon SQS
- Amazon DynamoDB
- Amazon Neptune
- AWS Lambda runtime
- AWS CloudFront

## What A PaaS Service Is Not

A PaaS Service is not:

- a first-party runtime component
- a reusable host pattern
- a vendor-managed service outside the organization's boundary

If the managed dependency is outside the adopter's cloud boundary, use
`serviceCategory: saas` instead.

## YAML Shape

PaaS Service Standards follow the authoritative
[paas-service-standard.schema.yaml](../schemas/paas-service-standard.schema.yaml) schema and
are governed by `checklist.paas-service-standard`.

They are modeled as Standards with:

- `type: paas_service_standard`
- `category: service`
- `serviceCategory: paas`

At minimum, a PaaS Service Standard should include:

- `id`
- `name`
- `vendor`
- `capability`
- `catalogStatus`
- `lifecycleStatus`

## Required Questions

The PaaS Definition Checklist requires the architect to answer:

- what capability the platform provides
- what resilience model the platform offers
- how access to it is authenticated
- what configuration surface the adopter controls
- what failure domain the dependency creates

These answers are intentionally black-box. The adopter does not document the
provider's hidden infrastructure. The adopter documents the managed contract it
is relying on.

## Boundary Rule

Use PaaS when the platform is:

- vendor-managed
- consumed as a managed platform capability
- deployed inside the organization's cloud boundary

Use SaaS when:

- the dependency is outside the organization's boundary
- vendor-side data handling, residency, DPA, and external attestations are the
  primary capabilities

## Practical Rule

If you are deciding between PaaS and SaaS, ask:

“Is this a managed platform inside our boundary, or an external vendor service
outside it?”

If it stays inside the adopter boundary, model it as PaaS.
