# Product Service

## What A Product Service Is

A Product Service is the RBB classification used to represent first-party
application code. The definition is strict: a Product Service exists when and
only when organization-authored code is deployed on an RBB or blackbox host
pattern.

That means the boundary between Product Service and the other RBB
classifications is not based on uniqueness, complexity, or whether another
product happens to reuse the component today. The boundary is based on
authorship.

- If the deployed component contains first-party code, it is a Product Service.
- If the component is vendor software that could be reused across products, it
  is another RBB classification, even when its purpose is product-specific.

## The Locked Definition

The locked framework definition is:

**Product Service = deployment context + first-party code package running on an
RBB or equivalent host pattern.**

This definition is deliberate because it keeps the reusable infrastructure model
separate from the product implementation model.

An IIS web tier is an RBB. A specific web application deployed on that IIS tier
is a Product Service. An AWS Lambda serverless host is an RBB. A specific
function package deployed to that Lambda host is a Product Service.

## YAML Shape

Product Services use the
[ps.schema.yaml](../../schemas/ps.schema.yaml) schema and are modeled as an RBB
classification.

The Product Service ODC inherits the full service baseline from
`odc.service`. That means a Product Service must still answer service
authentication, secrets management, service logging, health and welfare
monitoring, availability, scalability, recoverability, and failure domain. The
Product Service-specific checklist items add only the first-party concerns:
`product`, `runsOn`, and explicit `serviceCategory: product`.

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
used when the object must answer an ODC or compliance question that is not
otherwise expressed directly in the YAML.

## What A Product Service Documents

A Product Service captures:

- the owning product
- the RBB or host pattern it runs on via `runsOn`
- lifecycle and catalog status
- descriptive notes about the service's purpose
- any Architecture Decisions needed to explain required answers or
  non-obvious additions

Version 1 of DRAFT does not require enumeration of every internal package,
library, or repository that contributes code to the service. The framework only
needs to know that first-party code exists and where it is deployed.

## Product Service Versus Other RBB Classifications

This distinction is often the place where architects hesitate, so the rule
needs to stay simple.

The other RBB classifications describe reusable architecture behavior. They are
the standardized host or service patterns. They remain reusable RBBs even when
only one product currently uses them.

A Product Service describes the first-party workload that runs on top of one of
those patterns. It is where product identity enters the model.

If a component contains no first-party code, it is not a Product Service.

## Architecture Decisions

Product Services use the same Architecture Decision trigger logic as other RBB
classifications. If the Product Service must answer an ODC or compliance
question and the answer is not expressed directly in the object, an
Architecture Decision is required. The same applies when internal components or
external interactions are added beyond what the checklist or controls require.

Machine-readably, a Product Service is an RBB classification with product
ownership and `runsOn` metadata layered onto the base RBB contract.
