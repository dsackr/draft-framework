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
`implementations`. A company owns the implementation decisions because
`lifecycleStatus` on an implementation is a company disposition, not a vendor
fact.

## Capability Lookup Procedure

When a requirement names `relatedCapability`, the Draftsman must use this lookup
procedure:

1. Resolve the Requirement Group requirement.
2. Read `relatedCapability`.
3. Resolve the capability object from the effective model, checking workspace
   overlays before framework base.
4. Read `implementations`.
5. Prefer implementations with `lifecycleStatus: invest`, then `maintain`.
6. Recommend the referenced Technology Component or named configuration.
7. If no implementation exists, ask which Technology Component or external
   interaction satisfies the capability.

This keeps interviews grounded in the company's current technology standards.

## Implementation Entries

Each implementation entry contains:

- `ref`: Technology Component ID
- `lifecycleStatus`: company disposition for using that Technology Component
- optional `configuration`: named Technology Component configuration
- optional `notes`

The framework keeps vendor support facts on Technology Components in
`vendorLifecycle`. Company adoption lives here, on the capability mapping.
