# Security and Compliance Controls

## What This Layer Does

DRAFT treats compliance as a pluggable layer rather than a fixed property of
the Definition Checklist files.

For the AI-facing interview and translation rules that turn external control
catalogs into DRAFT YAML in this repo, see [Draftsman instructions](draftsman.md).

The Definition Checklists define the required capabilities for the architecture
object. Control Enforcement Profiles define the required controls that extend
those Definition Checklists at runtime.

That split exists so the same architecture model can be reused under multiple
compliance regimes. One team may want to work from a baseline control catalog.
Another may want to align the same requirements to NIST CSF, SOC 2, or an
internal control catalog that is specific to their organization.

## How The Model Is Structured

Each base control catalog is a YAML file in
`framework/configurations/compliance-controls/`. Company control catalogs live
in the private workspace under `configurations/compliance-controls/`.
The Compliance Controls object contains only control identity data and is governed by
`checklist.compliance-controls`.

Each control catalog entry defines:

- `controlId`
- `name`
- `externalReference`
- optional `notes`

Each Control Enforcement Profile is a YAML file in
`framework/configurations/control-enforcement-profiles/` for base profiles or
`configurations/control-enforcement-profiles/` for company profiles.
The profile is governed by `checklist.control-enforcement-profile` and carries the DRAFT
semantics for the controls in a backing control catalog.

Each profile semantic entry defines:

- `controlId`
- `appliesTo`
- `relatedCapability` when the control refines an existing Definition Checklist capability
- `requirementMode` as `mandatory` or `conditional`
- `naAllowed` so conditional frameworks can explicitly permit `N/A`
- optional `applicability` rules for scope handling
- `validAnswerTypes`

To add a new control group cleanly:

1. add or update the pure control catalog in `configurations/compliance-controls/`
2. add or update the Control Enforcement Profile in `configurations/control-enforcement-profiles/`
3. declare object-level `controlEnforcementProfiles` on artifacts that explicitly claim
   compliance with the profile
4. record object-level `controlImplementations` for each applicable control on
   those claimed artifacts

This is intentionally AI-friendly. A security specialist or uploaded source
document may give the AI the control ID, friendly name, and source link. The
profile Definition Checklist then tells the AI what DRAFT-specific metadata it still has to derive:

- which DRAFT object scopes the control applies to
- which DRAFT answer types are valid
- whether the control is mandatory or conditional
- whether the control refines an existing Definition Checklist capability

## What Ships In The Repo

The framework includes one baseline required-control catalog:

- Security and Compliance Controls

It also includes starter Compliance Controls for common external control sources
and for an organization-specific overlay. Those control catalog objects exist so
implementers can add controls without changing the core architecture model.

## How The Browser Uses It

The browser exposes a Control Enforcement Profile selector in the sidebar. When the
architect changes the selected profile, the Definition Checklist detail view and the Standard
Definition Checklist satisfaction panels re-render using the controls defined for that
profile.

Mandatory controls are treated as always in scope once that Control Enforcement Profile is
selected. Conditional controls stay visible, but the profile can explicitly
signal that `N/A` is an acceptable response when the product or deployment is
out of scope for that control set. This is the intended model for frameworks
such as TX-RAMP, PCI, HIPAA, and FedRAMP.

At the object level, `controlEnforcementProfiles` is the compliance claim. An artifact
that declares a profile must provide valid `controlImplementations` for every
applicable control in that profile. An artifact that does not declare a profile
is not labeled non-compliant; it is simply not counted as compliant inventory
for that control profile. Control implementations are evidence for declared profiles
only.

Artifact detail headers also show declared control enforcement profiles so architects
can identify claimed compliant inventory directly.

If the selected profile has no controls for a given scope or capability, the
browser shows that no required controls were added by that Control Enforcement Profile. That is
intentional. Missing controls are data gaps to fill, not rendering failures.

## Where To Go For Full Definitions

The authoritative source for any specific control definition still lives
outside this catalog. DRAFT stores:

- the pure control catalog
- the Control Enforcement Profile
- the object-level recorded implementation

It does not replace the source policy, audit, or controls system for your
environment.
