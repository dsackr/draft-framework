# Control References

## What They Are

This document describes how DRAFT handles external control references.

The seed AAGs included in this repo use control IDs in the format `CC.Frontline.XX.Y.Z` because the original source material used that scheme.

## What This Catalog Does With Them

The authoritative source for control definitions lives outside this catalog.

This catalog only references control IDs so that the compliance rationale for an AAG requirement is explicit. When an engineer sees `controlReferences: [CC.Frontline.06.3.1]` on a security-monitoring requirement, it means satisfying that AAG requirement also satisfies that mapped control.

The architecture catalog does not define or interpret the external controls framework. It maps control IDs to the architecture requirements they drive.

## Where To Go For Full Definitions

For the full control definitions, consult the owning security or compliance team for your environment.
