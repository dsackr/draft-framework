# ABBs

## What An ABB Is

An Architecture Building Block, or ABB, is the catalog’s smallest reusable unit. It is a configuration document for a specific vendor product at a specific version.

That definition matters. An ABB is not “Windows Server” in the abstract. It is `abb.os.microsoft-windowsserver-2022`. It is not “SQL Server” as a general category. It is `abb.software.microsoft-sqlserver-2019` or `abb.software.microsoft-sqlserver-2022`.

The framework uses that level of specificity because architecture standards become misleading very quickly if version and vendor lifecycle are left implicit.

## What Goes In An ABB

An ABB records the information engineers need in order to make technology choices responsibly. It includes:

- vendor name
- product name
- product version
- framework lifecycle status
- vendor lifecycle dates when those dates are known
- optional `platformDependency`

A good example is the CrowdStrike Falcon agent. The ABB captures the fact that the agent is installed locally on a host, but it also acknowledges that the agent exists to connect the host to the CrowdStrike platform.

## What An ABB Is Not

An ABB is not a deployment artifact. It does not say where or how many times a product is deployed.

An ABB is not an RBB. It does not describe a reusable architecture pattern built from multiple components.

An ABB is not a running system. If an organization has a production SQL Server cluster, the ABB is not the cluster. The ABB is the reusable standard describing the SQL Server version that a cluster or service RBB may depend on.

## Naming Convention

The naming convention is intentionally rigid.

- OS ABBs follow `abb.os.<vendor>-<os>-<major>`
- hardware ABBs follow `abb.hardware.<vendor>-<product>`
- software ABBs follow `abb.software.<vendor>-<product>-<ver>`
- agent ABBs follow `abb.agent.<vendor>-<product>`

Examples:

- `abb.os.amazon-linux-2`
- `abb.os.microsoft-windowsserver-2022`
- `abb.hardware.amazon-ec2-standard`
- `abb.software.microsoft-sqlserver-2019`
- `abb.agent.crowdstrike-falcon`

The rule is to stay lowercase, keep the segments dot-separated, and use hyphens inside segments.

## How ABBs Are Used

ABBs become useful when they are referenced as internal components in RBBs.

- A host RBB uses an OS ABB and a hardware ABB as foundational components, then adds any agent ABBs physically installed on the host.
- A service RBB references one function ABB that provides the service capability, such as IIS or SQL Server.

This separation makes the architecture easier to reason about. For example, `rbb.service.dbms.sqlserver-2022` does not need to redefine what SQL Server 2022 is. It can simply reference `abb.software.microsoft-sqlserver-2022` as its function ABB and focus on the architectural decisions that matter at the service level.

## How To Add A New ABB

1. Decide whether the object is an OS, hardware, software, or agent ABB.
2. Choose the correct ID pattern and make sure the ID is lowercase.
3. Create the YAML file in the correct folder.
4. Fill in the shared base fields: schema version, ID, type, name, description, version, catalog status, lifecycle status, owner, and tags.
5. Fill in the ABB-specific fields: category, vendor, product, product version, optional platform dependency, and vendor lifecycle.
6. If the vendor publishes lifecycle dates, include them. If the vendor does not publish them, say so explicitly in `vendorLifecycle.notes` and leave the dates null rather than guessing.
7. Run `python3 tools/validate.py`.

## FAQ

### Do I need an ABB for every piece of software?

The rule is simple: if it must be installed and configured on a host or service, it needs an ABB. There is no judgment call about architectural significance.

This includes server software, agents, runtimes, open source projects, and vendor-bundled components that require separate installation. For example, IIS is not installed by default on Windows Server. It must be added and configured, so it gets its own ABB just like Apache or nginx would.

What does not need an ABB: code that is compiled or bundled into an application, such as libraries, frameworks, and packages, and anything with nothing to install. If there is no installation and configuration step on a host or service, there is no ABB.

### What if the vendor does not publish EOL dates?

Do not guess. Record that fact in `vendorLifecycle.notes` and leave the lifecycle dates null. A null date with a clear note is better than fake precision.

### What is `platformDependency`?

It records the platform an ABB assumes exists. For an agent ABB, that might be the SaaS platform the agent reports to. For specialized software, it might be an external service the product cannot function without. It does not replace `externalInteractions` on an RBB. It complements them.
