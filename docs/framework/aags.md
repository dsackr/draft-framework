# AAGs

## What An AAG Is

An Architecture Analysis Guideline, or AAG, is the governance layer for catalog objects that need an explicit completeness test. It does not describe the component itself. It describes the concerns that must be addressed before the object is mature enough to be approved.

That distinction matters. The catalog object says what the component or pattern is, what it includes, and what it interacts with. The AAG says what questions that object must answer before the framework should trust it as a reusable standard.

## How The Model Works

The framework models AAGs in terms of requirements and satisfaction mechanisms rather than raw field-path checks. Each requirement has:

- an `id`
- a `description`
- a `rationale`
- a list of `canBeSatisfiedBy` mechanisms
- a `minimumSatisfactions` count

This is more useful than simple field existence because it captures intent. The framework does not care that a field exists for its own sake. It cares that authentication, logging, patching, backup, or access control has actually been addressed.

## Satisfaction Mechanisms

There are three satisfaction mechanisms.

### `internalComponent`

This means the requirement can be satisfied by something deployed inside the RBB.

Example: a host RBB that includes a security or patching agent ABB as an internal component.

### `externalInteraction`

This means the requirement can be satisfied by documenting that the RBB interacts with an external platform that provides the required capability.

Example: authentication through Active Directory, or logging through a centralized logging platform.

### `architecturalDecision`

This means the requirement can be satisfied through an explicit key in a variant’s `architecturalDecisions`.

Example: a service RBB satisfies secrets management by documenting `secretsManagement` in one of its named variants, even if the external secrets platform is not modeled as a separate interaction.

## Why The Mechanism Model Matters

The mechanism model keeps the framework focused on outcomes rather than forcing one implementation pattern.

An AAG should not say that authentication must always be modeled as an external platform dependency. In some cases that is the right representation. In others, a clear architectural decision is enough. The AAG’s job is to say that the concern must be addressed. It is not the AAG’s job to prescribe the only acceptable shape of the answer.

## The Current AAG Set

### `aag.host`

This is the host baseline. In plain language, it requires a host RBB to address:

- authentication
- logging
- security monitoring
- patch management
- at least one supported named variant with both patching cadence and backup approach

Concrete example: a Windows EC2 host satisfies authentication by declaring an external interaction with Active Directory. It satisfies logging by declaring centralized logging. It satisfies security monitoring by including security-related interactions and installed agents. It satisfies patch management by showing Automox and by documenting patching cadence in its variants.

### `aag.service`

This is the generic service baseline. In plain language, it requires a service RBB to explain:

- how the service scales
- how health is checked
- how secrets are managed

Concrete example: a web service RBB satisfies these requirements through architectural decisions such as `scalingApproach`, `healthCheck`, and `secretsManagement`.

### `aag.service.dbms`

This extends the service baseline for database services. In plain language, it requires a DBMS service RBB to document:

- backup strategy, including RTO and RPO
- HA mechanism
- encryption at rest
- access-control model

Concrete example: `rbb.service.dbms.sqlserver-2022` satisfies these requirements through decisions such as `backup.strategy`, `backup.rto`, `backup.rpo`, `ha.mechanism`, `encryption.atRest`, and `accessControl.model`.

### `aag.appliance-abb`

This AAG applies to appliance ABBs. In plain language, it requires the object
to document what capability the appliance provides, how resilient it is, where
it sits in the network, who owns patching, and what compliance posture it
carries.

### `aag.saas-service`

This AAG applies to SaaS Service objects. In plain language, it requires the
architect to document whether data leaves the infrastructure boundary, what data
residency commitments the vendor makes, whether a DPA is in place, how the
organization authenticates to the service, what compliance certifications the
vendor carries, and what SLA the vendor offers.

### `aag.ra`

This AAG applies to reference architectures. In plain language, it requires an RA to declare a clear pattern type, a complete list of required RBBs with roles, and pattern-level decisions that explain why the pattern exists in its current form.

Concrete example: `ra.dotnet.three-tier.ha` satisfies this AAG by declaring `patternType`, listing web-tier and data-tier RBBs with roles, and documenting pattern-level decisions such as web-tier autoscaling and AlwaysOn on the data tier.

### `aag.sdm`

This AAG applies to software distribution manifests. In plain language, it requires an SDM to declare which RA it conforms to, which variant each deployed RBB uses, what availability target the product is built for, whether it has product-specific external interactions beyond its component RBBs, and what data classification it handles.

Concrete example: a software distribution manifest satisfies this AAG by pointing to a reference architecture, selecting a variant for each deployed component, documenting an availability target, and identifying its data classification.

## Compliance Framework Mappings

Control mappings no longer live inside the AAG files themselves. Instead, DRAFT models compliance as a separate framework-and-mapping layer.

That separation matters because the same AAG can be viewed under multiple control catalogs. One organization might want to see the baseline Security and Compliance Controls pack. Another might want to view the same AAG through a NIST CSF mapping, a SOC 2 mapping, or an internal controls overlay. The requirement does not change. Only the mapped controls do.

In practice, the browser lets the architect select a compliance framework. The framework selector then drives which controls are displayed under each requirement and in each RBB AAG-satisfaction panel.

That means the AAG stays architecture-focused while the controls remain maintainable as a separate dataset that can be refreshed independently.

## Inheritance

Inheritance works the same way in AAGs as it does in many programming models.

`aag.service.dbms` declares `inherits: aag.service`, which means every DBMS service RBB is evaluated against both the generic service requirements and the DBMS-specific requirements. That is intentional. A database service does not stop being a service just because it also has data-platform concerns. The DBMS AAG builds on the generic service baseline rather than replacing it.

## How Validation Works

`tools/validate.py` evaluates AAG satisfaction in two ways. For RBBs, it loads every AAG referenced in the object’s `satisfiesAAG` list, resolves inheritance, and then tests each requirement’s permitted mechanisms. For RAs and SDMs, it applies the AAG identified by `appliesTo.type` and checks the explicit validation rules for those object types.

- An `externalInteraction` mechanism is satisfied when the RBB has an `externalInteractions` entry whose capability matches the requirement criteria.
- An `internalComponent` mechanism is satisfied when the RBB has an `internalComponents` entry whose role matches the requirement criteria.
- An `architecturalDecision` mechanism is satisfied when the required key exists and is non-empty in any variant’s `architecturalDecisions` map.

If the number of satisfied mechanisms is less than `minimumSatisfactions`, the validator emits a failure. RA and SDM failures use the same style of message, but the validator checks their rules directly because those objects do not expose the same RBB-specific structures.

Example:

```text
[rbb.host.windows.2022.ec2.standard] AAG requirement 'authentication' not satisfied — needs externalInteraction(capability=authentication) or architecturalDecision(authenticationApproach)
```

## FAQ

### Can I satisfy an authentication requirement with an architectural decision instead of an external interaction?

Yes, if the AAG explicitly allows that mechanism. That is one of the main reasons the requirement model exists.

### What happens if my object is in draft status and does not satisfy all AAG requirements?

Validation will still flag the missing requirement. Draft status is acceptable for work in progress, but the object is not ready for approval until the missing requirements are addressed.

### Who writes AAGs?

In practice, AAGs are authored and maintained by the architecture function, usually with input from infrastructure, security, database, and platform teams. A good AAG captures the recurring questions those teams need answered before they can safely support a reusable component.
