# Naming Conventions

## Why IDs Matter

The catalog relies on stable, predictable IDs because the IDs are the connective tissue between YAML objects, validation logic, browser navigation, and engineer conversation.

A good ID is not just readable. It is durable. Once an ID is in use, other objects will reference it and external tooling may depend on it.

## Convention Table

| Object type | Pattern | Example |
| --- | --- | --- |
| ABB OS | `abb.os.<vendor>-<os>-<major>` | `abb.os.amazon-linux-2` |
| ABB compute platform | `abb.hardware.<vendor>-<product>` | `abb.hardware.amazon-ec2-standard` |
| ABB software | `abb.software.<vendor>-<product>-<ver>` | `abb.software.microsoft-sqlserver-2019` |
| ABB agent | `abb.agent.<vendor>-<product>` | `abb.agent.crowdstrike-falcon` |
| Host RBB | `rbb.host.<os>.<platform>.<variant>` | `rbb.host.windows.2022.ec2.standard` |
| Service RBB | `rbb.service.<category>.<product>` | `rbb.service.dbms.sqlserver-2022` |
| ODC | `odc.<name>` | `odc.host`, `odc.service.dbms` |
| Reference architecture | `ra.<pattern-slug>` | `ra.dotnet.three-tier.ha` |
| Software distribution manifest | `sdm.<product-slug>` | `sdm.student-health` |

## Core Rules

- IDs are lowercase.
- Dot-separated segments define the hierarchy.
- Hyphens are used inside a segment, not instead of dots.
- Do not use spaces or ad hoc punctuation.

The point is to make IDs easy to type, easy to compare in diffs, and easy for tooling to parse.

## How To Handle Version Numbers

Version numbers belong in IDs when the version is part of the architectural identity.

Examples:

- `abb.software.microsoft-sqlserver-2019`
- `abb.software.microsoft-sqlserver-2022`
- `rbb.host.windows.2022.ec2.standard`

The rule of thumb is simple: if changing the version would create a different support, governance, or engineering choice, the version should be explicit in the ID.

## Common Mistakes

### Over-abbreviating

`abb.software.ms-sql-2019` is shorter, but weaker than `abb.software.microsoft-sqlserver-2019` because it introduces an abbreviation future engineers may not interpret consistently.

### Mixing dots and hyphens unpredictably

`rbb.host.windows-2022.ec2-standard` breaks the segment model and makes IDs harder to reason about.

### Omitting a version when the version matters

`abb.software.microsoft-sqlserver` is ambiguous in a catalog that actively tracks 2019 and 2022 as separate standards.

### Putting deployment-specific detail into reusable IDs

Environment names, data-center names, and hostnames do not belong in reusable object IDs. Product-specific instance names belong in SDMs, not in ABB or RBB IDs.
