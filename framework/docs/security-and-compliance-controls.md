# Security and Compliance Controls

## What This Layer Does

DRAFT treats compliance as an explicitly activated authoring layer rather than
a fixed property of the Definition Checklist files or a browser display filter.

For the AI-facing interview and translation rules that turn external control
catalogs into DRAFT YAML in this repo, see [Draftsman instructions](draftsman.md).

The Definition Checklists define the required capabilities for the architecture
object. Control Enforcement Profiles define the required controls that extend
those Definition Checklists during drafting and validation when a workspace
activates the profile.

That split exists so the same architecture model can be reused under multiple
compliance regimes. One team may activate a DRAFT-provided SOC 2 mapping.
Another may activate a third-party SOC 2 mapping or its own company-maintained
SOC 2 mapping. The selected profile identity records which interpretation the
object was drafted against.

## How The Model Is Structured

Each DRAFT-provided control catalog is a YAML file in
`framework/configurations/compliance-controls/`. Company control catalogs live
in the company repo under `configurations/compliance-controls/`. Optional
third-party control packs may be vendored under
`.draft/providers/<provider>/configurations/compliance-controls/`.
The Compliance Controls object contains only control identity data and is governed by
`checklist.compliance-controls`.

Control catalogs carry provider and authority metadata. Provider identifies who
authored the DRAFT control pack. Authority identifies the real-world source or
program the pack maps to. For example, `controls.draft-soc2` is a DRAFT
Framework-provided control catalog whose authority is AICPA SOC 2.

Each control catalog entry defines:

- `controlId`
- `name`
- `externalReference`
- optional `notes`

Each Control Enforcement Profile is a YAML file in
`framework/configurations/control-enforcement-profiles/` for DRAFT-provided
profiles, `.draft/providers/<provider>/configurations/control-enforcement-profiles/`
for third-party profiles, or `configurations/control-enforcement-profiles/`
for company profiles.
The profile is governed by `checklist.control-enforcement-profile` and carries the DRAFT
semantics for the controls in a backing control catalog.

A profile existing in any of those folders does not make it active. Workspace
activation makes a profile part of the company's drafting contract:

```yaml
compliance:
  activeControlEnforcementProfiles:
    - control-enforcement.draft-soc2
    - control-enforcement.frontline-roper
  requireActiveProfileDisposition: false
```

`requireActiveProfileDisposition: false` supports incremental migration:
Draftsman should push active profile questions for new and updated objects, but
validation does not fail every existing object that has not yet been
re-interviewed. Setting it to `true` makes validation require every object in
scope to record disposition against every active profile.

Each profile semantic entry defines:

- `controlId`
- `appliesTo`
- `relatedCapability` when the control refines an existing Definition Checklist capability
- `requirementMode` as `mandatory` or `conditional`
- `naAllowed` so conditional frameworks can explicitly permit `N/A`
- optional `applicability` rules for scope handling
- `validAnswerTypes`

To add a new company or third-party control group cleanly:

1. add or update the pure control catalog in the provider or workspace
   `configurations/compliance-controls/`
2. add or update the Control Enforcement Profile in the matching
   `configurations/control-enforcement-profiles/`
3. activate the profile in `.draft/workspace.yaml`
4. declare object-level `controlEnforcementProfiles` on artifacts that explicitly claim
   compliance with the profile
5. record object-level `controlImplementations` for each applicable control on
   those claimed artifacts

This is intentionally AI-friendly. A security specialist or uploaded source
document may give the AI the control ID, friendly name, and source link. The
profile Definition Checklist then tells the AI what DRAFT-specific metadata it still has to derive:

- which DRAFT object scopes the control applies to
- which DRAFT answer types are valid
- whether the control is mandatory or conditional
- whether the control refines an existing Definition Checklist capability

## What Ships In The Repo

The framework includes DRAFT-provided control packs. Their IDs include the
provider namespace so a company or third party can provide a different
interpretation without silently replacing them:

- `controls.draft-security-compliance`
- `controls.draft-soc2`
- `controls.draft-nist-csf`
- `controls.draft-tx-ramp`

The DRAFT Framework owns and maintains these as drafting aids. It does not claim
that using them makes a company compliant with SOC 2, NIST CSF, TX-RAMP, or any
external program. The authoritative source remains the control owner, auditor,
regulator, or company compliance program.

## How The Browser Uses It

The browser shows the workspace-active Control Enforcement Profiles from
`.draft/workspace.yaml`. If no profiles are active, it shows available profiles
for reference only.

When the architect changes the selected profile in the browser, the Definition
Checklist detail view and satisfaction panels re-render using that profile's
controls. That selector is a viewing aid; it is not the workspace activation
mechanism. Activation belongs in `.draft/workspace.yaml`.

Mandatory controls are treated as always in scope once that Control Enforcement Profile is
activated and attached to an object. Conditional controls stay visible, but the profile can explicitly
signal that `N/A` is an acceptable response when the product or deployment is
out of scope for that control set. This is the intended model for frameworks
such as TX-RAMP, PCI, HIPAA, and FedRAMP.

At the object level, `controlEnforcementProfiles` is the compliance claim. An artifact
that declares a profile must provide valid `controlImplementations` for every
applicable control in that profile. An artifact that does not declare a profile
is not labeled non-compliant; it is simply not counted as compliant inventory
for that control profile. Control implementations are evidence for declared
profiles only. If a workspace has active profiles, object claims should use
those active profiles rather than available-but-inactive profiles.

Control implementation status uses:

- `satisfied` when the object has a valid answer for the control
- `not-applicable` when a conditional control explicitly allows `N/A`
- `not-compliant` when the gap is known and must remain visible until fixed

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
