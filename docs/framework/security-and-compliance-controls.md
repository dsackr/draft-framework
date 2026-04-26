# Security and Compliance Controls

## What This Layer Does

DRAFT treats compliance as a pluggable layer rather than a fixed property of
the ODC files.

For the AI-facing interview and translation rules that turn external control
catalogs into SCC YAML in this repo, see [Draftsman instructions](draftsman.md).

The ODCs define the required capabilitys for the architecture object. Compliance
profiles define the required controls that extend those ODCs at runtime.

That split exists so the same architecture model can be reused under multiple compliance regimes. One team may want to work from a baseline controls pack. Another may want to align the same requirements to NIST CSF, SOC 2, or an internal control framework that is specific to their organization.

## How The Model Is Structured

Each control catalog is a YAML file in `compliance-frameworks/`.
The framework object contains only control identity data and is governed by
`odc.compliance-framework`.

Each control catalog entry defines:

- `controlId`
- `name`
- `externalReference`
- optional `notes`

Each DRAFT implementation profile is a YAML file in `compliance-profiles/`.
The profile is governed by `odc.compliance-profile` and carries the DRAFT
semantics for the controls in a backing framework catalog.

Each profile semantic entry defines:

- `controlId`
- `appliesTo`
- `relatedCapability` when the control refines an existing ODC capability
- `requirementMode` as `mandatory` or `conditional`
- `naAllowed` so conditional frameworks can explicitly permit `N/A`
- optional `applicability` rules for scope handling
- `validAnswerTypes`

To add a new control group cleanly:

1. add or update the pure control catalog in `compliance-frameworks/`
2. add or update the DRAFT implementation profile in `compliance-profiles/`
3. record object-level control implementations on the affected artifacts

This is intentionally AI-friendly. A security specialist or uploaded source
document may give the AI the control ID, friendly name, and source link. The
profile ODC then tells the AI what DRAFT-specific metadata it still has to derive:

- which DRAFT object scopes the control applies to
- which DRAFT answer types are valid
- whether the control is mandatory or conditional
- whether the control refines an existing ODC capability

## What Ships In The Repo

The framework includes one baseline required-controls pack:

- Security and Compliance Controls

It also includes starter framework definitions for common external frameworks
and for an organization-specific overlay. Those framework objects exist so
implementers can add controls without changing the core architecture model.

## How The Browser Uses It

The browser exposes a compliance profile selector in the sidebar. When the
architect changes the selected profile, the ODC detail view and the RBB
ODC-satisfaction panels re-render using the controls defined for that
profile.

Mandatory controls are treated as always in scope once that framework is
selected. Conditional controls stay visible, but the framework can explicitly
signal that `N/A` is an acceptable response when the product or deployment is
out of scope for that control set. This is the intended model for frameworks
such as TX-RAMP, PCI, HIPAA, and FedRAMP.

If the selected profile has no controls for a given scope or capability, the
browser shows that no required controls were added by that framework. That is
intentional. Missing controls are data gaps to fill, not rendering failures.

## Where To Go For Full Definitions

The authoritative source for any specific control definition still lives
outside this catalog. DRAFT stores:

- the pure control catalog
- the DRAFT implementation profile
- the object-level recorded implementation

It does not replace the source policy, audit, or controls system for your
environment.
