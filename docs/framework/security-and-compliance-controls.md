# Security and Compliance Controls

## What This Layer Does

DRAFT treats compliance as a pluggable layer rather than a fixed property of the AAG files.

The AAGs define the architecture requirements. Compliance framework objects define which controls correspond to those requirements.

That split exists so the same architecture model can be reused under multiple compliance regimes. One team may want to work from a baseline controls pack. Another may want to align the same requirements to NIST CSF, SOC 2, or an internal control framework that is specific to their organization.

## How The Model Is Structured

Each compliance framework is a single YAML file in `compliance-frameworks/`. The
framework object contains both its definition metadata and a
`requirementMappings` block that maps AAG requirement IDs directly to control
IDs for that framework.

To add a new framework or extend an existing one, only that single file needs
to change. No AAG files are modified.

## What Ships In The Repo

The framework includes one baseline mapped controls pack:

- Security and Compliance Controls

It also includes starter framework definitions for common external frameworks and for an organization-specific overlay. Those framework objects exist so implementers can add mappings without changing the core architecture model.

## How The Browser Uses It

The browser exposes a compliance framework selector in the sidebar. When the architect changes the selected framework, the AAG detail view and the RBB AAG-satisfaction panels re-render using the mappings for that framework.

If the selected framework has no mappings for a requirement, the browser shows that no controls are currently mapped. That is intentional. Missing mappings are data gaps to fill, not rendering failures.

## Where To Go For Full Definitions

The authoritative source for any specific control definition still lives outside this catalog. DRAFT stores the mapping between architecture requirements and control IDs, but it does not replace the source policy, audit, or controls system for your environment.
