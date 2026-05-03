# Capabilities

## What A Capability Is

A Capability is a first-class framework object that names an architecture
outcome the Draftsman can reason about. Requirements can point to a capability,
and the Draftsman can then look up the company-approved Technology Components
that implement it.

Capability IDs are namespaced, for example `capability.log-management` and
`capability.operating-system`.

## Where Capabilities Live

Framework base capabilities live in:

```text
framework/configurations/capabilities/
```

Company workspaces add implementation mappings in:

```text
configurations/capabilities/
configurations/object-patches/
```

Framework base capability files intentionally ship with empty
`implementations` and a `definitionOwner`, not a company `owner`. The
definition owner maintains the capability vocabulary. The company owner is the
team accountable for deciding which vendor products may satisfy the capability.

When a workspace assigns any implementation lifecycle entries, the effective
capability must include `owner.team`. That owner is the decision authority for
moving Technology Components through `candidate`, `preferred`, `existing-only`,
`deprecated`, and `retired`.

## Capability Lookup Procedure

When a requirement names `relatedCapability`, the Draftsman must use this lookup
procedure:

1. Resolve the Requirement Group requirement.
2. Read `relatedCapability`.
3. Resolve the capability object from the effective model, checking workspace
   overlays before framework base.
4. Read `owner` to identify the company decision authority.
5. Read `implementations`.
6. Prefer implementations with `lifecycleStatus: preferred`, then `existing-only`.
7. Recommend the referenced Technology Component or named configuration.
8. If no implementation exists, ask which Technology Component should satisfy
   the capability and flag that the capability owner must approve the lifecycle
   entry.

This keeps interviews grounded in the company's current technology standards.

## Implementation Entries

Each implementation entry contains:

- `ref`: Technology Component ID
- `lifecycleStatus`: company disposition for using that Technology Component
- optional `configuration`: named Technology Component configuration
- optional `notes`

The framework keeps vendor support facts on Technology Components in
`vendorLifecycle`. Company adoption lives here, on the capability mapping.
Implementation entries must reference Technology Components, not Standards or
running services, because lifecycle disposition is a decision about a discrete
vendor product and version. If a SaaS platform or managed service is governed by
the lifecycle program, model the vendor product as a Technology Component and
compose the service-facing architecture separately as a Standard.

## Acceptable Use Technology View

The generated browser includes an Acceptable Use Technology view. It groups
capability implementation mappings by domain and shows the capability owner,
contact, lifecycle status, Technology Component, vendor/product/version,
configuration, and notes. This is the human-readable technology lifecycle table
for a company workspace.

If a user wants a Technology Component added, retired, or moved between
`candidate`, `preferred`, `existing-only`, `deprecated`, and `retired`, the capability
owner listed in that view is the contact for the change request.
