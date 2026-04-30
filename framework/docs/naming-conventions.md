# Naming Conventions

## Why IDs Matter

The catalog relies on stable, predictable IDs because the IDs are the connective tissue between YAML objects, validation logic, browser navigation, and engineer conversation.

A good ID is not just readable. It is durable. Once an ID is in use, other objects will reference it and external tooling may depend on it.

## Convention Table

| Object type | Pattern | Example |
| --- | --- | --- |
| Technology Component OS | `technology.os.<vendor>-<os>-<major>` | `technology.os.amazon-linux-2` |
| Technology Component compute platform | `technology.compute.<vendor>-<product>` | `technology.compute.amazon-ec2-standard` |
| Technology Component software | `technology.software.<vendor>-<product>-<ver>` | `technology.software.microsoft-sqlserver-2019` |
| Technology Component agent | `technology.agent.<vendor>-<product>` | `technology.agent.crowdstrike-falcon` |
| Host Standard | `host.<os>.<platform>.<variant>` | `host.windows.2022.ec2.standard` |
| Service Standard | `service.<category>.<product>` | `service.web.nginx-126` |
| Database Standard | `database.<engine-version>` | `database.sqlserver-2022` |
| Definition Checklist | `checklist.<name>` | `checklist.host-standard`, `checklist.database-standard` |
| Reference architecture | `reference-architecture.<pattern-slug>` | `reference-architecture.dotnet.three-tier.ha` |
| Software Deployment Pattern | `software-deployment.<product-slug>` | `software-deployment.student-health` |

## Core Rules

- IDs are lowercase.
- Dot-separated segments define the hierarchy.
- Hyphens are used inside a segment, not instead of dots.
- Do not use spaces or ad hoc punctuation.

The point is to make IDs easy to type, easy to compare in diffs, and easy for tooling to parse.

## How To Handle Version Numbers

Version numbers belong in IDs when the version is part of the architectural identity.

Examples:

- `technology.software.microsoft-sqlserver-2019`
- `technology.software.microsoft-sqlserver-2022`
- `host.windows.2022.ec2.standard`

The rule of thumb is simple: if changing the version would create a different support, governance, or engineering choice, the version should be explicit in the ID.

## Common Mistakes

### Over-abbreviating

`technology.software.ms-sql-2019` is shorter, but weaker than `technology.software.microsoft-sqlserver-2019` because it introduces an abbreviation future engineers may not interpret consistently.

### Mixing dots and hyphens unpredictably

`host.windows-2022.ec2-standard` breaks the segment model and makes IDs harder to reason about.

### Omitting a version when the version matters

`technology.software.microsoft-sqlserver` is ambiguous in a catalog that actively tracks 2019 and 2022 as separate standards.

### Putting deployment-specific detail into reusable IDs

Environment names, data-center names, and hostnames do not belong in reusable object IDs. Product-specific instance names belong in Software Deployment Patterns, not in Technology Component or Standard IDs.
