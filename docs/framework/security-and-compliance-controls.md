# Security and Compliance Controls

## What This Layer Does

DRAFT treats compliance as a pluggable layer rather than a fixed property of
the ODC files.

The ODCs define the required concerns for the architecture object. Compliance
framework objects define required controls that extend those ODCs at runtime.

That split exists so the same architecture model can be reused under multiple compliance regimes. One team may want to work from a baseline controls pack. Another may want to align the same requirements to NIST CSF, SOC 2, or an internal control framework that is specific to their organization.

## How The Model Is Structured

Each compliance framework is a single YAML file in `compliance-frameworks/`.
The framework object contains both its definition metadata and a `controls`
list. Compliance frameworks are governed by `odc.compliance-framework`, which
means a valid control catalog in DRAFT is not just a copied spreadsheet. It is
a translated control catalog with DRAFT semantics.

Each control defines:

- `controlId`
- `name`
- `externalReference`
- optional `description`
- `appliesTo`
- `relatedConcern` when the control refines an existing ODC concern
- `requirementMode` as `mandatory` or `conditional`
- `naAllowed` so conditional frameworks can explicitly permit `N/A`
- optional `applicability` rules for future scope evaluation
- `validAnswerTypes`

To add a new framework or extend an existing one, only that single file needs
to change. No ODC files are modified.

This is intentionally AI-friendly. A security specialist or uploaded source
document may give the AI the control ID, friendly name, and source link. The
ODC then tells the AI what DRAFT-specific metadata it still has to derive:

- which DRAFT object scopes the control applies to
- which DRAFT answer types are valid
- whether the control is mandatory or conditional
- whether the control refines an existing ODC concern

## What Ships In The Repo

The framework includes one baseline required-controls pack:

- Security and Compliance Controls

It also includes starter framework definitions for common external frameworks
and for an organization-specific overlay. Those framework objects exist so
implementers can add controls without changing the core architecture model.

## How The Browser Uses It

The browser exposes a compliance framework selector in the sidebar. When the
architect changes the selected framework, the ODC detail view and the RBB
ODC-satisfaction panels re-render using the controls defined for that
framework.

Mandatory controls are treated as always in scope once that framework is
selected. Conditional controls stay visible, but the framework can explicitly
signal that `N/A` is an acceptable response when the product or deployment is
out of scope for that control set. This is the intended model for frameworks
such as TX-RAMP, PCI, HIPAA, and FedRAMP.

If the selected framework has no controls for a given scope or concern, the
browser shows that no required controls were added by that framework. That is
intentional. Missing controls are data gaps to fill, not rendering failures.

## Where To Go For Full Definitions

The authoritative source for any specific control definition still lives
outside this catalog. DRAFT stores the metadata needed to place a required
control onto the right ODC and constrain the acceptable answer types, but it
does not replace the source policy, audit, or controls system for your
environment.
