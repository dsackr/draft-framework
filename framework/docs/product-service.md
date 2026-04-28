# Product Service

## What A Product Service Is

A Product Service is the RBB classification used to represent a first-party
deployable runtime-behavior component when an SDM needs to express that it is
being deployed on an RBB or blackbox host pattern.

That means the boundary between Product Service and the other RBB
classifications is not based on uniqueness, complexity, or whether another
product happens to reuse the component today. The boundary is based on whether
the SDM needs to communicate a distinct first-party deployable component with
its own runtime behavior.

## The Locked Definition

The locked framework definition is:

**Product Service = first-party deployable runtime-behavior component expressed
through an SDM on top of an RBB or equivalent host pattern.**

This definition is deliberate because it keeps the reusable architecture model
separate from product-specific deployment expression.

An IIS web tier is an RBB. A product-specific API, worker, or scheduler
deployed on that substrate may be a Product Service. An AWS Lambda serverless
host is an RBB. A specific function package deployed to that Lambda host may
be a Product Service.

## YAML Shape

Product Services use the
[ps.schema.yaml](../schemas/ps.schema.yaml) schema and are modeled as an RBB
classification.

Product Service does not have its own ODC because it is not a starting-point
architecture interview object. It emerges only when an SDM expresses that a
specific first-party component is deployed on a reusable runtime/service
substrate.

At minimum, a Product Service YAML should include:

- `id`
- `type: rbb`
- `category: service`
- `serviceCategory: product`
- `name`
- `product`
- `runsOn`
- `catalogStatus`
- `lifecycleStatus`

Most Product Services also include `description`. `architecturalDecisions` is
used when the SDM or an attached compliance framework needs an answer that is
not otherwise expressed directly in the YAML.

## What A Product Service Documents

A Product Service captures:

- the owning product
- the RBB or host pattern it runs on via `runsOn`
- lifecycle and catalog status
- descriptive notes about the component's purpose
- any Architecture Decisions needed to explain required answers or
  non-obvious additions

Version 1 of DRAFT does not require enumeration of every internal package,
library, or repository that contributes code to the component. The framework
only needs to know that a first-party deployable component exists and where it
is deployed.

## Product Service Versus Other RBB Classifications

This distinction is often the place where architects hesitate, so the rule
needs to stay simple.

The other RBB classifications describe reusable architecture behavior. They are
the standardized host or service patterns. They remain reusable RBBs even when
only one product currently uses them.

A Product Service describes the first-party deployable component that runs on
top of one of those patterns. It is where product-specific deployment identity
enters the model.

If a component contains no first-party code, it is not necessarily a Product
Service. If it is only site content, static assets, database schema, or simple
product-specific configuration, it should not be elevated to Product Service
just because CI/CD can deploy it.

## Architecture Decisions

Product Services are useful only when they add deployability value. A Product
Service should exist when the SDM needs to communicate which first-party
runtime-behavior package is pushed onto which runtime package.

Machine-readably, a Product Service is an RBB classification with product
ownership and `runsOn` metadata layered onto the base RBB contract.
