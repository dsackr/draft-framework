# Reference Architectures

## What An RA Is

A Reference Architecture, or RA, is a deployment pattern. It tells application
teams which reusable building blocks and pattern-level decisions they should
adopt when they need a supported set of non-functional outcomes such as high
availability, recoverability, security posture, or scaling behavior.

If an engineer asks, "what deployment pattern should I adopt so my application
gets the right operational qualities here," the answer belongs in an RA. If
the engineer asks, "what does a specific product actually deploy today," the
answer belongs in an SDM.

## YAML Shape

Reference Architectures are validated by
[`framework/tools/validate.py`](../tools/validate.py) and `odc.ra`.

At minimum, an RA YAML should include:

- `id`
- `type: reference_architecture`
- `name`
- `catalogStatus`
- `lifecycleStatus`
- `serviceGroups`

Most RAs also include `description`, `patternType`, and
`architecturalDecisions`.

## What `serviceGroups` Means

The core field in an RA is `serviceGroups`. Each group clusters the required
services that work together in the deployment pattern. Inside each group, the
pattern declares:

- the RBBs that must exist
- the `diagramTier` each RBB belongs to
- any group-local interactions or notes that matter to the pattern

This does more than list ingredients. It shows how the pattern is meant to be
assembled using the same tiered service-group grammar the SDM uses later.

## Concrete Example

A representative reference architecture says that a three-tier .NET
high-availability pattern includes service groups such as:

- `Frontend UI` with presentation-tier web services
- `Application Runtime Services` with application-tier runtime services
- `Data Services` with data-tier DBMS services

The RA also carries architectural decisions that explain what the deployment
pattern assumes, such as web-tier autoscaling and AlwaysOn on the data tier.

## Why An RA Is Never A Node In An SDM Diagram

An RA is not a deployed thing. It is a deployment-pattern declaration.

An SDM may say `appliesPattern: ra.dotnet.three-tier.ha`, but that field is
metadata about conformance, not a deployed runtime element. The visual
question for an SDM is "what RBBs are deployed here?" The guidance question
is "which RA deployment pattern does this solution claim to follow?"

## Why RAs Matter

RAs create shared vocabulary and deployment guidance across engineering teams.

- Infrastructure teams can see which deployment patterns are supported.
- Product teams can see which reusable components and pattern decisions they are expected to adopt.
- Architecture can make non-functional expectations explicit instead of relying on oral tradition.

An RA makes it possible to say, "this is the standard deployment pattern the
framework recognizes for this class of workload."

## FAQ

### What is the difference between an RA and an SDM?

An RA is generic and an SDM is specific. An RA says what reusable building
blocks and pattern-level decisions should be adopted to achieve a supported
deployment posture. An SDM says which building blocks a specific product
actually deploys.

### Can a product deviate from its RA?

Yes, but that should be treated as an explicit exception rather than invisible drift. If a product cannot follow the pattern, engineers should either document the exception clearly in the SDM, propose a new RA, or revise the existing RA.

### Who owns RAs?

RAs are architecture-owned artifacts, usually written in collaboration with infrastructure, product, database, security, and platform teams so that they reflect both desired standards and actual supportable patterns.
