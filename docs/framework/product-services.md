# Software Services

## What A Software Service Is

A Software Service, or SS, is the framework object used to represent first-party
application code. The definition is strict: a PS exists when and only when
organization-authored code is deployed on an RBB or blackbox host pattern.

That means the boundary between PS and RBB is not based on uniqueness,
complexity, or whether another product happens to reuse the component today. The
boundary is based on authorship.

- If the deployed component contains first-party code, it is a Software Service.
- If the component is vendor software that could be reused across products, it
  is an RBB, even when its purpose is product-specific.

## The Locked Definition

The locked framework definition is:

**SS = deployment context + first-party code package running on an RBB or
equivalent host pattern.**

This definition is deliberate because it keeps the reusable infrastructure model
separate from the product implementation model.

An IIS web tier is an RBB. A specific web application deployed on that IIS tier
is a Software Service. An AWS Lambda serverless host is an RBB. A specific
function package deployed to that Lambda host is a Software Service.

## What A Software Service Documents

A Software Service captures:

- the owning product
- the RBB or host pattern it runs on via `runsOn`
- lifecycle and catalog status
- the named variants that matter for the service itself
- descriptive notes about the service's purpose

Version 1 of DRAFT does not require enumeration of every internal package,
library, or repository that contributes code to the service. The framework only
needs to know that first-party code exists and where it is deployed.

## Software Service Versus RBB

This distinction is often the place where architects hesitate, so the rule needs
to stay simple.

An RBB describes reusable architecture behavior. It is the standardized host or
service pattern. It remains an RBB even when only one product currently uses it.

A Software Service describes the first-party workload that runs on top of that
pattern. It is where product identity enters the model.

If a component contains no first-party code, it is not a Software Service.

## Variants

Software Service variants follow the same open-ended map model used elsewhere in
the framework. `ha` and `sa` are common examples, but any descriptive key is
valid. Software Service variants typically capture operational notes, expected
deployment posture, or service-level distinctions rather than infrastructure
implementation details.

The underlying file path and object type still use `product-services` and
`product_service`. The framework term presented to engineers is Software
Service.
