# Product Service

## What A Product Service Is

A Product Service represents a first-party custom binary or black-box component
that a Software Deployment Pattern deploys on a selected deployable object.

The boundary is not based on how complex the component is or whether another
product reuses it. The boundary is whether the Software Deployment Pattern needs
to communicate a distinct first-party deployable unit with its own runtime
behavior.

## The Locked Definition

**Product Service = first-party deployable runtime behavior expressed through a
Software Deployment Pattern on top of a Host, Runtime Service, Data-at-Rest
Service, Edge/Gateway Service, or equivalent deployable object.**

An IIS runtime is a Runtime Service. A product-specific API, worker, or
scheduler deployed on that runtime may be a Product Service. An AWS Lambda
serverless runtime is a Runtime Service with `deliveryModel: paas`. A specific
function package deployed to that runtime may be a Product Service.

## YAML Shape

Product Services use
[product-service.schema.yaml](../schemas/product-service.schema.yaml).

At minimum, a Product Service YAML should include:

- `schemaVersion`
- `uid`
- `type: product_service`
- `name`
- `product`
- `runsOn`
- `catalogStatus`
- `lifecycleStatus`

Most Product Services also include `description`. `architecturalDecisions` is
used when the Software Deployment Pattern or an attached Requirement Group needs
an answer that is not otherwise expressed directly in the YAML.

## What A Product Service Documents

A Product Service captures:

- the owning product
- the deployable object it runs on via `runsOn`
- lifecycle and catalog status
- descriptive notes about the component's purpose
- any architectural decision entries needed to explain required answers or
  non-obvious additions

DRAFT does not require enumeration of every internal package, library, or
repository that contributes code to the component. The framework only needs to
know that a first-party deployable component exists and where it is deployed.

## Product Service Versus Reusable Services

Runtime Service, Data-at-Rest Service, and Edge/Gateway Service objects describe
reusable architecture behavior. A Product Service describes the first-party
deployable component that runs on top of one of those reusable objects.

If a component contains no first-party code, it is not necessarily a Product
Service. If it is only site content, static assets, database schema, or simple
product-specific configuration, it should not be elevated to Product Service
just because CI/CD can deploy it.
