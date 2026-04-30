# Definition Checklists

## What A Definition Checklist Is

A Definition Checklist is **a structured checklist of
required questions and answers used to define a complete and correct
architecture object.**

For a repo-level AI interviewing workflow that uses the Definition Checklists together with the
current catalog inventory, see [Draftsman instructions](draftsman.md).

A Definition Checklist exists to help build an object correctly while it is being authored. It
does not redefine the taxonomy of the object. Type, classification, and
structure come from the object schema and the object itself. The Definition Checklist tells the
author which required questions must be answered so the object is complete,
supportable, and reusable.

That means Definition Checklists are not primarily post-hoc governance artifacts. They are the
framework's machine-readable object-definition contract.

Definition Checklists are also meant to be AI-friendly interview checklists. An AI assistant
should be able to use a Definition Checklist to gather answers from user dialogue, uploaded
documents, spreadsheets, diagrams, screenshots, or architecture notes and
translate those answers into the correct DRAFT YAML.

## YAML Shape

Definition Checklists follow the authoritative
[definition-checklist.schema.yaml](../schemas/definition-checklist.schema.yaml) schema and are enforced by
[`framework/tools/validate.py`](../tools/validate.py).

At minimum, a Definition Checklist YAML should include:

- `id`
- `type: definition_checklist`
- `name`
- `description`
- `requirements`

Most Definition Checklists also include `version`, `catalogStatus`, `lifecycleStatus`,
`appliesTo`, and sometimes `inherits`.

## How The Model Works

The framework models Definition Checklists in terms of requirements and satisfaction mechanisms
rather than raw field-path checks. Each requirement has:

- an `id`
- a `description`
- a `rationale`
- a list of `canBeSatisfiedBy` mechanisms
- a `minimumSatisfactions` count

This is more useful than simple field existence because it captures intent. A
Definition Checklist asks the architect the questions that must be answered while the object is
being defined.

## Satisfaction Mechanisms

There are six satisfaction mechanisms.

### `field`

The requirement is satisfied directly by a field on the object itself.

Example: a SaaS Service satisfies data-boundary by setting
`dataLeavesInfrastructure`.

### `internalComponent`

The requirement is satisfied by something deployed inside the Standard.

Example: a host Standard that includes a security or patching agent Technology Component as an
internal component.

### `technologyComponentConfiguration`

The requirement is satisfied by a named configuration carried on one of the
referenced Technology Components, or by a named configuration on the Technology Component itself when the Definition Checklist
applies directly to a Technology Component such as an Appliance Component.

Example: a Windows or Linux Technology Component configuration that defines where host logs are
written and how they are handled operationally.

### `externalInteraction`

The requirement is satisfied by documenting that the object interacts with an
external platform that provides the required capability.

Example: authentication through Active Directory, or logging through a
centralized logging platform.

### `deploymentConfiguration`

The requirement is satisfied by a named deployment configuration on the Standard.

Example: a service Standard may use a deployment configuration to answer
availability, scalability, or recoverability when those qualities are reusable
deployment variants of the same building block.

### `architecturalDecision`

The requirement is satisfied through an explicit answer in the object's
`architecturalDecisions` block.

Example: a service Standard satisfies secrets management by documenting
`secretsManagement`, even if the external secrets platform is not modeled as a
separate interaction.

## Why The Mechanism Model Matters

The mechanism model keeps the framework focused on required answers rather than
forcing one implementation pattern.

A Definition Checklist should not say that authentication must always be modeled as an external
platform dependency. In some cases that is the right representation. In others,
the answer may come from a local Technology Component, a named Technology Component configuration, or a clear
architectural decision entry. The Definition Checklist's job is to say that the capability must be
addressed. It is not the Definition Checklist's job to prescribe the only acceptable shape of
the answer.

## Interviewing Capability Requirements

When a Definition Checklist requirement is written as a capability, the Draftsman should ask
what architecture mechanism satisfies that capability. It should not translate
the capability into an organizational ownership question unless the Definition Checklist
requirement explicitly asks for ownership.

For host baseline capabilities such as authentication, log management, health
monitoring, security monitoring, and patch management, ask which one of these
mechanisms applies:

- an internal component Technology Component installed on the host
- a named Technology Component configuration on the selected OS, hardware, agent, or software Technology Component
- an external interaction with a platform service
- an architectural decision entry that documents the approach when no separate
  object is modeled

For example, host patch management asks how patches are orchestrated and what
mechanism applies updates. Good follow-up questions are:

- Is patching handled by an external patch platform such as Automox, WSUS, SCCM,
  AWS Systems Manager, or another service?
- Is patch execution handled by an installed agent or software Technology Component?
- Does the selected OS Technology Component have a named configuration that defines the patching
  approach?
- If none of those are modeled, what architectural decision entry describes the patch
  orchestration model?

Do not ask "which team owns patching?" for `checklist.host-standard` patch management. Team
ownership may be useful object metadata, but it is not the host patch-management
capability answer.

## The Current Definition Checklist Set

### `checklist.host-standard`

This is the host baseline. In plain language, it requires a host Standard to
address:

- operating system
- compute platform
- authentication
- log management
- health and welfare monitoring
- security monitoring
- patch management

Backup is intentionally not a host-baseline requirement. Recovery and
protection capabilities belong to the service or data layer unless a selected
Control Enforcement Profile adds stricter security or compliance requirements.

For managed hosts, Operating System and Compute Platform are expected to be
answered by selecting the correct Technology Components. The other capabilities may be answered
through Agent Technology Components, Software Technology Components, Technology Component configurations, external interactions,
or architectural decision entries.

In interview form, ask:

- Which Operating System Technology Component defines this host?
- Which Compute Platform Technology Component defines this host?
- For authentication, logging, monitoring, security monitoring, and patching,
  which mechanism satisfies each capability: internal component, Technology Component
  configuration, external interaction, or architectural decision?
- For patch management specifically, what platform, agent, configuration, or
  documented orchestration model applies updates?

### `checklist.service-standard`

This is the generic service baseline. In plain language, it requires a service
Standard to explain:

- service authentication
- secrets management
- service logging
- health and welfare monitoring
- availability
- scalability
- recoverability
- failure domain

The structural service shape is still enforced separately by schema and
validator rules:

- one `hostStandard`
- one `primaryTechnologyComponent`

The Definition Checklist is responsible for the required answers, not for restating the
structural contract.

Availability, scalability, and recoverability may be answered either through
direct architectural decision entries or through a named `deploymentConfiguration`
defined on the Standard. Failure domain is always treated as an explicit
architectural answer.

In interview form, ask:

- Which host Standard runs this service?
- Which function Technology Component defines the service software?
- How are authentication, secrets, service logging, and health monitoring addressed?
- What are the service's availability, scalability, recoverability, and failure-domain answers?

### `checklist.database-standard`

This extends the service baseline for database services. In plain language, it
requires a DBMS service Standard to document:

- backup strategy
- recovery time objective
- recovery point objective
- HA / replication mechanism
- encryption at rest
- access-control model

In interview form, ask:

- How are backup and recovery objectives defined?
- What HA or replication mechanism exists?
- How are encryption at rest and database access control handled?

### `checklist.appliance-component`

This Definition Checklist applies to appliance Technology Components. Appliance Components are Technology Components by product identity
because they map directly to a discrete vendor product and version. They are
not normal Standards because there is no separable host, operating system, compute
platform, or function Technology Component that the framework can compose.

An appliance therefore behaves like a service-like deployed capability without
inheriting `checklist.host-standard` or `checklist.service-standard`. For that reason, this Definition Checklist asks the
required consumer-facing capability questions directly on the appliance Technology Component.

It treats the appliance as a blackbox component inside the adopter's
infrastructure boundary and requires the object to document:

- what capability the appliance provides
- how access to the appliance is authenticated
- what log or audit visibility the adopter gets
- how health, status, incidents, or operational telemetry are observed
- who or what applies firmware, software, and hidden host updates
- how resilient it is
- where it sits in the network
- what configuration surface the adopter actually controls
- what failure domain it creates
- what compliance posture it carries

In interview form, ask:

- What capability does the appliance provide?
- How are appliance access, log/audit visibility, and health/status visibility handled?
- What patch or update model applies to the firmware, software, and hidden host?
- Where is it placed, and what can the adopter configure?
- How resilient is it, what failure domain does it create, and what compliance posture is known?

### `checklist.saas-service-standard`

This Definition Checklist applies to SaaS Service Standard objects. It treats the vendor platform as a
blackbox and requires the architect to document:

- what capability the service provides
- whether data leaves the infrastructure boundary
- what data residency commitments the vendor makes
- whether a DPA is in place
- how the organization authenticates to the service
- what compliance certifications the vendor carries
- what audit or logging visibility the consumer has
- how the consumer observes health, status, or incidents
- what failure domain the dependency creates
- what SLA the vendor offers

In interview form, ask:

- What capability is being consumed from the vendor?
- What data, residency, authentication, audit visibility, and health visibility commitments are known?
- What failure domain and SLA does the dependency create?

### `checklist.paas-service-standard`

This Definition Checklist applies to PaaS Service Standard objects. It treats the managed platform as a
black-box service that remains inside the organization's cloud boundary and
requires the architect to document:

- what capability the platform provides
- what resilience model the platform gives by default
- how access to the platform is authenticated
- what configuration surface the adopter controls
- what failure domain the dependency creates

In interview form, ask:

- What capability is being consumed from the managed platform?
- What resilience model does the platform provide?
- How is the service authenticated?
- What can the adopter configure directly?
- What failure domain does the dependency create?

### `checklist.compliance-controls`

This Definition Checklist applies to Compliance Controls catalogs. It requires a
control author to translate each source control into DRAFT-specific control
metadata:

- source control identity
- authoritative source link
- mandatory vs conditional scope
- DRAFT object applicability
- valid DRAFT answer types
- optional related Definition Checklist capability
- conditional applicability metadata when the control is not always in scope

In interview form, ask:

- What is the control ID and friendly name?
- Where is the authoritative source for the control?
- Is the control mandatory or conditional?
- Which DRAFT object scopes does it apply to?
- What answer types are valid in DRAFT?
- If conditional, when is it in scope and is `N/A` allowed?

### `checklist.drafting-session`

This Definition Checklist applies to drafting-session objects. It exists to make partial
authoring state machine-readable and easy to revisit later. In plain language,
it requires the session to document:

- what object it is trying to build
- what source material informed the session
- what YAML objects were created or proposed
- what questions remain unresolved
- what next steps are needed to continue

In interview form, ask:

- What object is this session trying to produce?
- What source artifacts or interviews informed the current draft?
- What objects were created, proposed, or stubbed in this session?
- What questions remain open?
- What follow-up actions are needed to close the gaps?
- If it refines an existing Definition Checklist capability, which one?

### `checklist.reference-architecture`

This Definition Checklist applies to Reference Architectures. It requires a Reference Architecture to declare:

- the supported deployment pattern it represents
- the service groups and tiered Standards required to realize that pattern
- the pattern-level decisions that deliver the intended non-functional
  qualities

In interview form, ask:

- What deployment pattern does this Reference Architecture define?
- What service groups and tiered Standards make up the pattern?
- Which deployment qualities does the pattern intentionally deliver?

### `checklist.software-deployment-pattern`

This Definition Checklist applies to software deployment patterns. It requires a Software Deployment Pattern to
declare:

- which Reference Architecture it follows, or why no applicable Reference Architecture exists
- which service groups make up the deployed product
- where those service groups run
- what availability target the product is built for
- whether it has product-specific external interactions beyond its component
  Standards
- what data classification it handles
- what deployment-level failure domain it creates
- what intentional deviations from the selected Reference Architecture exist

In interview form, ask:

- Which Reference Architecture does this product follow, or why is no Reference Architecture applicable?
- What service groups and deployment targets make up the real deployment?
- What availability target, data classification, and failure domain does the deployment have?
- What additional interactions or intentional pattern deviations exist?

## Architectural Decision Entry Trigger Rules

Architectural decision entries exist to answer required questions that are not
otherwise resolved directly by the object shape, and to explain exceptions or
extensions beyond what the Definition Checklists and selected Control Enforcement Profiles ask for.

Use an architectural decision entry when:

- a Definition Checklist requirement or compliance control needs an answer and the object does
  not provide that answer directly through a field, internal component, or
  external interaction
- an internal component is added that was not explicitly required by a Definition Checklist or
  selected Control Enforcement Profile
- an external interaction is added that was not explicitly required by a Definition Checklist
  or selected Control Enforcement Profile

An architectural decision entry should reference the thing that triggered it:

- the Definition Checklist requirement ID
- the compliance control ID
- or the specific added component or interaction

## Security And Compliance Controls

Required controls do not live inside the Definition Checklist files themselves. DRAFT models
security and compliance as a separate profile layer. A selected Control
Enforcement Profile can add required controls to a Definition Checklist at runtime without modifying the
Definition Checklist YAML.

That separation matters because the same Definition Checklist can be viewed under multiple
control catalogs. One organization might want to use the baseline Security and
Compliance Controls pack. Another might want to extend the same Definition Checklist with NIST
CSF, SOC 2, or an internal controls overlay. The capability does not change. The
selected Control Enforcement Profile adds the required controls that apply.

In practice, the browser lets the architect select a Control Enforcement Profile. The
profile selector then drives which required controls are displayed under each
capability and in each Standard Definition Checklist satisfaction panel.

## Inheritance

Inheritance works the same way in Definition Checklists as it does in many programming models.

`checklist.database-standard` declares `inherits: checklist.service-standard`, which means every DBMS
service Standard is evaluated against both the generic service requirements and the
DBMS-specific requirements.

## How Validation Works

`framework/tools/validate.py` evaluates Definition Checklist satisfaction in three ways. For Standards, it
loads every Definition Checklist referenced in the object's `satisfiesDefinitionChecklist` list, resolves
inheritance, and then tests each requirement's permitted mechanisms. For Reference Architectures,
Software Deployment Patterns, Appliance Components, and compliance controls, it applies the Definition Checklist identified
by `appliesTo.type` and checks the explicit validation rules for those object
types.

- An `externalInteraction` mechanism is satisfied when the object has an
  `externalInteractions` entry whose capability matches the requirement
  criteria.
- An `internalComponent` mechanism is satisfied when the object has a
  referenced Technology Component whose capability metadata matches the requirement criteria, or an
  `internalComponents` entry whose role matches the requirement criteria when
  the Definition Checklist uses role-based matching.
- A `technologyComponentConfiguration` mechanism is satisfied when a referenced Technology Component has a
  named configuration whose capability metadata matches the requirement criteria.
- An `architecturalDecision` mechanism is satisfied when the required key
  exists and is non-empty in the object's `architecturalDecisions` map.
- A `field` mechanism is satisfied when the specified object field is
  populated, or equals the expected value when the mechanism declares `equals`.
- A `deploymentConfiguration` mechanism is satisfied when the object declares a
  named deployment configuration whose `addressesQualities` covers the required
  quality.

If the number of satisfied mechanisms is less than `minimumSatisfactions`, the
validator emits a failure.

Example:

```text
[host.windows.2022.ec2.standard] Definition Checklist requirement 'authentication' not satisfied — needs externalInteraction(capability=authentication) or architecturalDecision(authenticationApproach)
```

## FAQ

### Can I satisfy an authentication requirement with an architectural decision instead of an external interaction?

Yes, if the Definition Checklist explicitly allows that mechanism.

### What happens if my object is in draft status and does not satisfy all Definition Checklist requirements?

Validation will still flag the missing requirement. Draft status is acceptable
for work in progress, but the object is not ready for approval until the
missing requirements are addressed.

### Who writes Definition Checklists?

In practice, Definition Checklists are authored and maintained by the architecture function,
usually with input from infrastructure, security, database, and platform teams.
A good Definition Checklist captures the recurring questions those teams need answered before
they can safely support a reusable component.
