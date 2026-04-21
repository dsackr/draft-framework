# Security and Compliance Controls

## What This Layer Does

DRAFT treats compliance as a pluggable layer rather than a fixed property of the AAG files.

The AAGs define the architecture requirements. Separate compliance framework objects and mapping objects define which controls correspond to those requirements.

That split exists so the same architecture model can be reused under multiple compliance regimes. One team may want to work from a baseline controls pack. Another may want to align the same requirements to NIST CSF, SOC 2, or an internal control framework that is specific to their organization.

## How The Model Is Structured

There are two first-class object types in this layer:

- `compliance_framework` defines a selectable framework, such as a baseline controls pack, NIST CSF, SOC 2, or an organization-specific overlay.
- `aag_control_mapping` maps one AAG's requirement IDs to the control IDs used by a selected framework.

This means the same requirement, such as host logging or DBMS encryption at rest, can be shown under different control catalogs without changing the AAG itself.

## What Ships In The Repo

The framework includes one baseline mapped controls pack:

- Security and Compliance Controls

It also includes starter framework definitions for common external frameworks and for an organization-specific overlay. Those framework objects exist so implementers can add mappings without changing the core architecture model.

## How The Browser Uses It

The browser exposes a compliance framework selector in the sidebar. When the architect changes the selected framework, the AAG detail view and the RBB AAG-satisfaction panels re-render using the mappings for that framework.

If the selected framework has no mappings for a requirement, the browser shows that no controls are currently mapped. That is intentional. Missing mappings are data gaps to fill, not rendering failures.

## Where To Go For Full Definitions

The authoritative source for any specific control definition still lives outside this catalog. DRAFT stores the mapping between architecture requirements and control IDs, but it does not replace the source policy, audit, or controls system for your environment.
