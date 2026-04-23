# Product Service

## What A Product Service Is

A Product Service, or PS, is the framework object used to represent first-party
application code. The definition is strict: a Product Service exists when and
only when organization-authored code is deployed on an RBB or blackbox host
pattern.

That means the boundary between PS and RBB is not based on uniqueness,
complexity, or whether another product happens to reuse the component today. The
boundary is based on authorship.

- If the deployed component contains first-party code, it is a Product Service.
- If the component is vendor software that could be reused across products, it
  is an RBB, even when its purpose is product-specific.

## The Locked Definition

The locked framework definition is:

**PS = deployment context + first-party code package running on an RBB or
equivalent host pattern.**

This definition is deliberate because it keeps the reusable infrastructure model
separate from the product implementation model.

An IIS web tier is an RBB. A specific web application deployed on that IIS tier
is a Product Service. An AWS Lambda serverless host is an RBB. A specific
function package deployed to that Lambda host is a Product Service.

## YAML Shape

Product Services use the
[ps.schema.yaml](../../schemas/ps.schema.yaml) schema and are modeled as a
specialized RBB classification.

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

Most Product Services also include `description` and a non-empty `variants`
map.

## What A Product Service Documents

A Product Service captures:

- the owning product
- the RBB or host pattern it runs on via `runsOn`
- lifecycle and catalog status
- the named variants that matter for the service itself
- descriptive notes about the service's purpose

Version 1 of DRAFT does not require enumeration of every internal package,
library, or repository that contributes code to the service. The framework only
needs to know that first-party code exists and where it is deployed.

## Product Service Versus RBB

This distinction is often the place where architects hesitate, so the rule needs
to stay simple.

An RBB describes reusable architecture behavior. It is the standardized host or
service pattern. It remains an RBB even when only one product currently uses it.

A Product Service describes the first-party workload that runs on top of that
pattern. It is where product identity enters the model.

If a component contains no first-party code, it is not a Product Service.

## Variants

Product Service variants follow the same open-ended map model used elsewhere in
the framework. `ha` and `sa` are common examples, but any descriptive key is
valid. Product Service variants typically capture operational notes, expected
deployment posture, or service-level distinctions rather than infrastructure
implementation details.

Machine-readably, a Product Service is an RBB classification with product
ownership and `runsOn` metadata layered onto the base RBB contract.
