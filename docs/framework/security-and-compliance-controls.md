# Security and Compliance Controls

## What They Are

This document describes how DRAFT handles Security and Compliance Controls references.

The seed AAGs included in this repo use control IDs in the format `CC.SecurityCompliance.XX.Y.Z`.

## What This Catalog Does With Them

The authoritative source for control definitions lives outside this catalog.

This catalog only references control IDs so that the compliance rationale for an AAG requirement is explicit. When an engineer sees `controlReferences: [CC.SecurityCompliance.06.3.1]` on a security-monitoring requirement, it means satisfying that AAG requirement also satisfies that mapped control.

The architecture catalog does not define or interpret the external controls framework. It maps control IDs to the architecture requirements they drive.

## Where To Go For Full Definitions

For the full control definitions, consult the owning security or compliance team for your environment.
