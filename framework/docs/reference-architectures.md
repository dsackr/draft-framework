# Reference Architectures

## What A Reference Architecture Is

A Reference Architecture is a deployment pattern. It tells application
teams which reusable building blocks and pattern-level decisions they should
adopt when they need a supported set of non-functional outcomes such as high
availability, recoverability, security posture, or scaling behavior.

If an engineer asks, "what deployment pattern should I adopt so my application
gets the right operational qualities here," the answer belongs in a Reference Architecture. If
the engineer asks, "what does a specific product actually deploy today," the
answer belongs in a Software Deployment Pattern.

## YAML Shape

Reference Architectures are validated by
[`framework/tools/validate.py`](../tools/validate.py) and the Reference
Architecture Requirement Group.

At minimum, a Reference Architecture YAML should include:

- `uid`
- `type: reference_architecture`
- `name`
- `catalogStatus`
- `lifecycleStatus`
- `serviceGroups`

Most Reference Architectures also include `description`, `patternType`, and
`architecturalDecisions`.

## Lifecycle Policy

The `lifecycleStatus` on a Reference Architecture describes the company's
position on using that deployment pattern:

- `preferred` for cloud-forward or target-state patterns that should be used for
  new architecture
- `candidate` for patterns being evaluated before they become preferred
- `existing-only` for legacy patterns that remain supported for existing systems
- `deprecated` for patterns that should be migrated away from
- `retired` for patterns being actively retired

A Reference Architecture that includes a Technology Component whose
`vendorLifecycle.extendedSupportEnd` date has passed must be marked
`deprecated`. The validator follows the pattern's `serviceGroups` through the
referenced Standards to the underlying Technology Components and enforces this
rule.

A Reference Architecture that includes a Technology Component whose
`vendorLifecycle.mainstreamSupportEnd` date has passed but whose
`extendedSupportEnd` date has not passed is in extended support. The default
position for these patterns is `deprecated`. A company may mark the pattern
`existing-only` while extended support is active, but it must document that exception
in `architecturalDecisions.lifecycleRationale`. Extended-support Technology
Components must not appear in a `preferred` Reference Architecture.

## What `serviceGroups` Means

The core field in a Reference Architecture is `serviceGroups`. Each group clusters the required
services that work together in the deployment pattern. Inside each group, the
pattern declares:

- the Standards that must exist
- the `diagramTier` each Standard belongs to
- any group-local interactions or notes that matter to the pattern

This does more than list ingredients. It shows how the pattern is meant to be
assembled using the same tiered service-group grammar the Software Deployment Pattern uses later.

## Concrete Example

A representative reference architecture says that a three-tier .NET
high-availability pattern includes service groups such as:

- `Frontend UI` with presentation-tier web services
- `Application Runtime Services` with application-tier runtime services
- `Data Services` with data-tier DBMS services

The Reference Architecture also carries architectural decision entries that explain what the deployment
pattern assumes, such as web-tier autoscaling and AlwaysOn on the data tier.

## Why A Reference Architecture Is Never A Node In A Software Deployment Pattern Diagram

A Reference Architecture is not a deployed thing. It is a deployment-pattern declaration.

A Software Deployment Pattern may reference a Reference Architecture UID in
`followsReferenceArchitecture`, but that field is metadata about conformance,
not a deployed runtime element. The visual question for a Software Deployment
Pattern is "what Standards are deployed here?" The guidance question is "which
Reference Architecture does this solution claim to follow?"

## Why Reference Architectures Matter

Reference Architectures create shared vocabulary and deployment guidance across engineering teams.

- Infrastructure teams can see which deployment patterns are supported.
- Product teams can see which reusable components and pattern decisions they are expected to adopt.
- Architecture can make non-functional expectations explicit instead of relying on oral tradition.

A Reference Architecture makes it possible to say, "this is the standard deployment pattern the
framework recognizes for this class of workload."

## FAQ

### What is the difference between a Reference Architecture and a Software Deployment Pattern?

A Reference Architecture is generic and a Software Deployment Pattern is specific. A Reference Architecture says what reusable building
blocks and pattern-level decisions should be adopted to achieve a supported
deployment posture. A Software Deployment Pattern says which building blocks a specific product
actually deploys.

### Can a product deviate from its Reference Architecture?

Yes, but that should be treated as an explicit exception rather than invisible drift. If a product cannot follow the pattern, engineers should either document the exception clearly in the Software Deployment Pattern, propose a new Reference Architecture, or revise the existing Reference Architecture.

### Who owns Reference Architectures?

Reference Architectures are architecture-owned artifacts, usually written in collaboration with infrastructure, product, database, security, and platform teams so that they reflect both desired standards and actual supportable patterns.
