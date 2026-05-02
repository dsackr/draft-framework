# Product Service

## What A Product Service Is

A Product Service is the Standard classification used to represent a first-party
deployable runtime-behavior component when a Software Deployment Pattern needs to express that it is
being deployed on a Standard or blackbox host pattern.

That means the boundary between Product Service and the other Standard
classifications is not based on uniqueness, complexity, or whether another
product happens to reuse the component today. The boundary is based on whether
the Software Deployment Pattern needs to communicate a distinct first-party deployable component with
its own runtime behavior.

## The Locked Definition

The locked framework definition is:

**Product Service = first-party deployable runtime-behavior component expressed
through a Software Deployment Pattern on top of a Standard or equivalent host pattern.**

This definition is deliberate because it keeps the reusable architecture model
separate from product-specific deployment expression.

An IIS web tier is a Standard. A product-specific API, worker, or scheduler
deployed on that substrate may be a Product Service. An AWS Lambda serverless
host is a Standard. A specific function package deployed to that Lambda host may
be a Product Service.

## YAML Shape

Product Services use the
[product-service.schema.yaml](../schemas/product-service.schema.yaml) schema and are modeled as a Standard
classification.

Product Service does not have its own Requirement Group because it is not a starting-point
architecture interview object. It emerges only when a Software Deployment Pattern expresses that a
specific first-party component is deployed on a reusable runtime/service
substrate.

At minimum, a Product Service YAML should include:

- `id`
- `type: product_service`
- `category: service`
- `serviceCategory: product`
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
- the Standard or host pattern it runs on via `runsOn`
- lifecycle and catalog status
- descriptive notes about the component's purpose
- any architectural decision entries needed to explain required answers or
  non-obvious additions

Version 1 of DRAFT does not require enumeration of every internal package,
library, or repository that contributes code to the component. The framework
only needs to know that a first-party deployable component exists and where it
is deployed.

## Product Service Versus Other Standard Classifications

This distinction is often the place where architects hesitate, so the rule
needs to stay simple.

The other Standard classifications describe reusable architecture behavior. They are
the standardized host or service patterns. They remain reusable Standards even when
only one product currently uses them.

A Product Service describes the first-party deployable component that runs on
top of one of those patterns. It is where product-specific deployment identity
enters the model.

If a component contains no first-party code, it is not necessarily a Product
Service. If it is only site content, static assets, database schema, or simple
product-specific configuration, it should not be elevated to Product Service
just because CI/CD can deploy it.

## Architectural Decision Entries

Product Services are useful only when they add deployability value. A Product
Service should exist when the Software Deployment Pattern needs to communicate which first-party
runtime-behavior package is pushed onto which runtime package.

Machine-readably, a Product Service is a Standard classification with product
ownership and `runsOn` metadata layered onto the base Standard contract.
