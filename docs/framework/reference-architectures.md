# Reference Architectures

## What An RA Is

A Reference Architecture, or RA, is a pattern specification. It describes the architecture shape the framework expects for a class of solutions, but it does not describe an actual deployment.

If an engineer asks, “what does a resilient .NET application stack look like here,” the answer belongs in an RA. If the engineer asks, “what does a specific product actually deploy today,” the answer belongs in an SDM.

## YAML Shape

Reference Architectures are validated by
[`tools/validate.py`](../../tools/validate.py) and `aag.ra`.

At minimum, an RA YAML should include:

- `id`
- `type: reference_architecture`
- `name`
- `catalogStatus`
- `lifecycleStatus`
- `requiredRBBs`

Most RAs also include `description`, `patternType`, and
`architecturalDecisions`.

## What `requiredRBBs` Means

The core field in an RA is `requiredRBBs`. Each entry names:

- the RBB that must exist
- the variant that must be used
- the role the RBB plays in the pattern

This field does more than list ingredients. It says which reusable components must exist, which named variant the pattern expects for that component, and what role the component fills. The variant key is open-ended. `ha` and `sa` are common examples, but the framework does not treat them as the only valid values.

## Concrete Example

A representative reference architecture says that a three-tier .NET high-availability pattern requires:

- a web-tier service RBB using the HA variant of `rbb.service.web.iis-standard`
- a data-tier service RBB using the HA variant of a SQL Server DBMS RBB

The RA also carries architectural decisions that explain what the pattern assumes, such as web-tier autoscaling and AlwaysOn on the data tier.

## Why An RA Is Never A Node In An SDM Diagram

An RA is not a deployed thing. It is a pattern declaration.

An SDM may say `appliesPattern: ra.dotnet.three-tier.ha`, but that field is metadata about conformance, not a deployed runtime element. The visual question for an SDM is “what RBBs are deployed here?” The governance question is “which RA pattern does this deployment claim to follow?”

## Why RAs Matter

RAs create shared vocabulary and discoverability across engineering teams.

- Infrastructure teams can see what patterns are supported.
- Product teams can see which reusable components are expected.
- Architecture can make standards explicit instead of relying on oral tradition.

An RA makes it possible to say, “this is the standard pattern the framework recognizes for this class of workload.”

## FAQ

### What is the difference between an RA and an SDM?

An RA is generic and an SDM is specific. An RA says what kinds of building blocks must exist for a pattern. An SDM says which building blocks a specific product actually deploys.

### Can a product deviate from its RA?

Yes, but that should be treated as an explicit exception rather than invisible drift. If a product cannot follow the pattern, engineers should either document the exception clearly in the SDM, propose a new RA, or revise the existing RA.

### Who owns RAs?

RAs are architecture-owned artifacts, usually written in collaboration with infrastructure, product, database, security, and platform teams so that they reflect both desired standards and actual supportable patterns.
