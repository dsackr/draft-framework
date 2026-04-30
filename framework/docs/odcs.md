# ODCs

## What An ODC Is

An Object Definition Checklist, or ODC, is **a structured checklist of
required questions and answers used to define a complete and correct
architecture object.**

For a repo-level AI interviewing workflow that uses the ODCs together with the
current catalog inventory, see [Draftsman instructions](draftsman.md).

An ODC exists to help build an object correctly while it is being authored. It
does not redefine the taxonomy of the object. Type, classification, and
structure come from the object schema and the object itself. The ODC tells the
author which required questions must be answered so the object is complete,
supportable, and reusable.

That means ODCs are not primarily post-hoc governance artifacts. They are the
framework's machine-readable object-definition contract.

ODCs are also meant to be AI-friendly interview checklists. An AI assistant
should be able to use an ODC to gather answers from user dialogue, uploaded
documents, spreadsheets, diagrams, screenshots, or architecture notes and
translate those answers into the correct DRAFT YAML.

## YAML Shape

ODCs follow the authoritative
[odc.schema.yaml](../schemas/odc.schema.yaml) schema and are enforced by
[`framework/tools/validate.py`](../tools/validate.py).

At minimum, an ODC YAML should include:

- `id`
- `type: odc`
- `name`
- `description`
- `requirements`

Most ODCs also include `version`, `catalogStatus`, `lifecycleStatus`,
`appliesTo`, and sometimes `inherits`.

## How The Model Works

The framework models ODCs in terms of requirements and satisfaction mechanisms
rather than raw field-path checks. Each requirement has:

- an `id`
- a `description`
- a `rationale`
- a list of `canBeSatisfiedBy` mechanisms
- a `minimumSatisfactions` count

This is more useful than simple field existence because it captures intent. An
ODC asks the architect the questions that must be answered while the object is
being defined.

## Satisfaction Mechanisms

There are six satisfaction mechanisms.

### `field`

The requirement is satisfied directly by a field on the object itself.

Example: a SaaS Service satisfies data-boundary by setting
`dataLeavesInfrastructure`.

### `internalComponent`

The requirement is satisfied by something deployed inside the RBB.

Example: a host RBB that includes a security or patching agent ABB as an
internal component.

### `abbConfiguration`

The requirement is satisfied by a named configuration carried on one of the
referenced ABBs, or by a named configuration on the ABB itself when the ODC
applies directly to an ABB such as an Appliance ABB.

Example: a Windows or Linux ABB configuration that defines where host logs are
written and how they are handled operationally.

### `externalInteraction`

The requirement is satisfied by documenting that the object interacts with an
external platform that provides the required capability.

Example: authentication through Active Directory, or logging through a
centralized logging platform.

### `deploymentConfiguration`

The requirement is satisfied by a named deployment configuration on the RBB.

Example: a service RBB may use a deployment configuration to answer
availability, scalability, or recoverability when those qualities are reusable
deployment variants of the same building block.

### `architecturalDecision`

The requirement is satisfied through an explicit answer in the object's
`architecturalDecisions` block.

Example: a service RBB satisfies secrets management by documenting
`secretsManagement`, even if the external secrets platform is not modeled as a
separate interaction.

## Why The Mechanism Model Matters

The mechanism model keeps the framework focused on required answers rather than
forcing one implementation pattern.

An ODC should not say that authentication must always be modeled as an external
platform dependency. In some cases that is the right representation. In others,
the answer may come from a local ABB, a named ABB configuration, or a clear
architectural decision. The ODC's job is to say that the capability must be
addressed. It is not the ODC's job to prescribe the only acceptable shape of
the answer.

## Interviewing Capability Requirements

When an ODC requirement is written as a capability, the Draftsman should ask
what architecture mechanism satisfies that capability. It should not translate
the capability into an organizational ownership question unless the ODC
requirement explicitly asks for ownership.

For host baseline capabilities such as authentication, log management, health
monitoring, security monitoring, and patch management, ask which one of these
mechanisms applies:

- an internal component ABB installed on the host
- a named ABB configuration on the selected OS, hardware, agent, or software ABB
- an external interaction with a platform service
- an architectural decision that documents the approach when no separate
  object is modeled

For example, host patch management asks how patches are orchestrated and what
mechanism applies updates. Good follow-up questions are:

- Is patching handled by an external patch platform such as Automox, WSUS, SCCM,
  AWS Systems Manager, or another service?
- Is patch execution handled by an installed agent or software ABB?
- Does the selected OS ABB have a named configuration that defines the patching
  approach?
- If none of those are modeled, what architectural decision describes the patch
  orchestration model?

Do not ask "which team owns patching?" for `odc.host` patch management. Team
ownership may be useful object metadata, but it is not the host patch-management
capability answer.

## The Current ODC Set

### `odc.host`

This is the host baseline. In plain language, it requires a host RBB to
address:

- operating system
- compute platform
- authentication
- log management
- health and welfare monitoring
- security monitoring
- patch management

Backup is intentionally not a host-baseline requirement. Recovery and
protection capabilitys belong to the service or data layer unless a selected
security or compliance framework adds stricter expectations through control
requirements.

For managed hosts, Operating System and Compute Platform are expected to be
answered by selecting the correct ABBs. The other capabilitys may be answered
through Agent ABBs, Software ABBs, ABB configurations, external interactions,
or architectural decisions.

In interview form, ask:

- Which Operating System ABB defines this host?
- Which Compute Platform ABB defines this host?
- For authentication, logging, monitoring, security monitoring, and patching,
  which mechanism satisfies each capability: internal component, ABB
  configuration, external interaction, or architectural decision?
- For patch management specifically, what platform, agent, configuration, or
  documented orchestration model applies updates?

### `odc.service`

This is the generic service baseline. In plain language, it requires a service
RBB to explain:

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

- one `hostRbb`
- one `functionAbb`

The ODC is responsible for the required answers, not for restating the
structural contract.

Availability, scalability, and recoverability may be answered either through
direct Architecture Decisions or through a named `deploymentConfiguration`
defined on the RBB. Failure domain is always treated as an explicit
architectural answer.

In interview form, ask:

- Which host RBB runs this service?
- Which function ABB defines the service software?
- How are authentication, secrets, service logging, and health monitoring addressed?
- What are the service's availability, scalability, recoverability, and failure-domain answers?

### `odc.service.dbms`

This extends the service baseline for database services. In plain language, it
requires a DBMS service RBB to document:

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

### `odc.appliance-abb`

This ODC applies to appliance ABBs. Appliance ABBs are ABBs by product identity
because they map directly to a discrete vendor product and version. They are
not normal RBBs because there is no separable host, operating system, compute
platform, or function ABB that the framework can compose.

An appliance therefore behaves like a service-like deployed capability without
inheriting `odc.host` or `odc.service`. For that reason, this ODC asks the
required consumer-facing capability questions directly on the appliance ABB.

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

### `odc.saas-service`

This ODC applies to SaaS Service objects. It treats the vendor platform as a
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

### `odc.paas-service`

This ODC applies to PaaS Service objects. It treats the managed platform as a
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

### `odc.compliance-framework`

This ODC applies to Security and Compliance Control catalogs. It requires a
framework author to translate each source control into DRAFT-specific control
metadata:

- source control identity
- authoritative source link
- mandatory vs conditional scope
- DRAFT object applicability
- valid DRAFT answer types
- optional related ODC capability
- conditional applicability metadata when the control is not always in scope

In interview form, ask:

- What is the control ID and friendly name?
- Where is the authoritative source for the control?
- Is the control mandatory or conditional?
- Which DRAFT object scopes does it apply to?
- What answer types are valid in DRAFT?
- If conditional, when is it in scope and is `N/A` allowed?

### `odc.drafting-session`

This ODC applies to drafting-session objects. It exists to make partial
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
- If it refines an existing ODC capability, which one?

### `odc.ra`

This ODC applies to reference architectures. It requires an RA to declare:

- the supported deployment pattern it represents
- the service groups and tiered RBBs required to realize that pattern
- the pattern-level decisions that deliver the intended non-functional
  qualities

In interview form, ask:

- What deployment pattern does this RA define?
- What service groups and tiered RBBs make up the pattern?
- Which deployment qualities does the pattern intentionally deliver?

### `odc.sdm`

This ODC applies to software distribution manifests. It requires an SDM to
declare:

- which RA it conforms to, or why no applicable RA exists
- which service groups make up the deployed product
- where those service groups run
- what availability target the product is built for
- whether it has product-specific external interactions beyond its component
  RBBs
- what data classification it handles
- what deployment-level failure domain it creates
- what intentional deviations from the selected RA exist

In interview form, ask:

- Which RA does this product follow, or why is no RA applicable?
- What service groups and deployment targets make up the real deployment?
- What availability target, data classification, and failure domain does the deployment have?
- What additional interactions or intentional pattern deviations exist?

## Architecture Decision Trigger Rules

Architecture Decisions exist to answer required questions that are not
otherwise resolved directly by the object shape, and to explain exceptions or
extensions beyond what the ODCs and selected compliance frameworks ask for.

Use an Architecture Decision when:

- an ODC requirement or compliance control needs an answer and the object does
  not provide that answer directly through a field, internal component, or
  external interaction
- an internal component is added that was not explicitly required by an ODC or
  selected compliance control
- an external interaction is added that was not explicitly required by an ODC
  or selected compliance control

An Architecture Decision should reference the thing that triggered it:

- the ODC requirement ID
- the compliance control ID
- or the specific added component or interaction

## Security And Compliance Controls

Required controls do not live inside the ODC files themselves. DRAFT models
security and compliance as a separate profile layer. A selected compliance
profile can add required controls to an ODC at runtime without modifying the
ODC YAML.

That separation matters because the same ODC can be viewed under multiple
control catalogs. One organization might want to use the baseline Security and
Compliance Controls pack. Another might want to extend the same ODC with NIST
CSF, SOC 2, or an internal controls overlay. The capability does not change. The
selected profile adds the required controls that apply.

In practice, the browser lets the architect select a compliance profile. The
profile selector then drives which required controls are displayed under each
capability and in each RBB ODC-satisfaction panel.

## Inheritance

Inheritance works the same way in ODCs as it does in many programming models.

`odc.service.dbms` declares `inherits: odc.service`, which means every DBMS
service RBB is evaluated against both the generic service requirements and the
DBMS-specific requirements.

## How Validation Works

`framework/tools/validate.py` evaluates ODC satisfaction in three ways. For RBBs, it
loads every ODC referenced in the object's `satisfiesODC` list, resolves
inheritance, and then tests each requirement's permitted mechanisms. For RAs,
SDMs, Appliance ABBs, and compliance frameworks, it applies the ODC identified
by `appliesTo.type` and checks the explicit validation rules for those object
types.

- An `externalInteraction` mechanism is satisfied when the object has an
  `externalInteractions` entry whose capability matches the requirement
  criteria.
- An `internalComponent` mechanism is satisfied when the object has a
  referenced ABB whose capability metadata matches the requirement criteria, or an
  `internalComponents` entry whose role matches the requirement criteria when
  the ODC uses role-based matching.
- An `abbConfiguration` mechanism is satisfied when a referenced ABB has a
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
[rbb.host.windows.2022.ec2.standard] ODC requirement 'authentication' not satisfied — needs externalInteraction(capability=authentication) or architecturalDecision(authenticationApproach)
```

## FAQ

### Can I satisfy an authentication requirement with an architectural decision instead of an external interaction?

Yes, if the ODC explicitly allows that mechanism.

### What happens if my object is in draft status and does not satisfy all ODC requirements?

Validation will still flag the missing requirement. Draft status is acceptable
for work in progress, but the object is not ready for approval until the
missing requirements are addressed.

### Who writes ODCs?

In practice, ODCs are authored and maintained by the architecture function,
usually with input from infrastructure, security, database, and platform teams.
A good ODC captures the recurring questions those teams need answered before
they can safely support a reusable component.
