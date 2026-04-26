# ABBs

## What An ABB Is

An Architecture Building Block, or ABB, is a discrete third-party product
object. It records one vendor product at one product version so that RBBs can
compose real products instead of generic categories.

That definition matters. An ABB is not “Windows Server” in the abstract. It is
`abb.os.microsoft-windowsserver-2022`. It is not “SQL Server” as a general
category. It is `abb.software.microsoft-sqlserver-2019` or
`abb.software.microsoft-sqlserver-2022`.

The framework uses that level of specificity because architecture standards
become misleading very quickly if version and vendor lifecycle are left
implicit.

## YAML Shape

ABBs follow the authoritative
[abb.schema.yaml](../../schemas/abb.schema.yaml) schema. Appliance ABBs
additionally follow
[abb-appliance.schema.yaml](../../schemas/abb-appliance.schema.yaml).

At minimum, an ABB YAML should include:

- `id`
- `type: abb`
- `name`
- `vendor`
- `productName`
- `productVersion`
- `classification`
- `catalogStatus`
- `lifecycleStatus`

These fields are not optional modeling guidance. The validator enforces them.

## What Goes In An ABB

An ABB records the information engineers need in order to make technology
choices responsibly. It includes:

- vendor name
- product name
- product version
- ABB classification
- framework lifecycle status
- vendor lifecycle dates when those dates are known
- optional `platformDependency`

## ABB Classifications

Every ABB must declare exactly one classification.

| Classification | Meaning |
|---|---|
| Operating System | A vendor product that is the operating system. |
| Compute Platform | A vendor product that provides the physical or virtual compute substrate the operating system runs on. |
| Software | A vendor product that runs locally and does not require an external interaction. |
| Agent | A vendor product that runs locally and requires an external interaction. |

These classifications are machine-readable semantics, not just documentation
labels. The validator can use them when checking whether an RBB is built from
the right kinds of ABBs.

ABBs may also carry reusable host-control metadata:

- `capabilities` when the ABB itself satisfies one or more host capabilities
- `configurations` when a named ABB configuration satisfies one or more host
  capabilities

A good example is the CrowdStrike Falcon agent. The ABB captures the fact that
the agent is installed locally on a host, but it also acknowledges that the
agent exists to connect the host to the CrowdStrike platform by providing
the `security-monitoring` capability.

## What An ABB Is Not

An ABB is not a deployment artifact. It does not say where or how many times a product is deployed.

An ABB is not an RBB. It does not describe a reusable architecture pattern built from multiple components.

An ABB is not a running system. If an organization has a production SQL Server cluster, the ABB is not the cluster. The ABB is the reusable standard describing the SQL Server version that a cluster or service RBB may depend on.

## Naming Convention

The naming convention is intentionally rigid.

- Operating System ABBs typically follow `abb.os.<vendor>-<os>-<major>`
- Compute Platform ABBs typically follow `abb.hardware.<vendor>-<product>`
- Software ABBs typically follow `abb.software.<vendor>-<product>-<ver>`
- Agent ABBs typically follow `abb.agent.<vendor>-<product>`

Examples:

- `abb.os.amazon-linux-2`
- `abb.os.microsoft-windowsserver-2022`
- `abb.hardware.amazon-ec2-standard`
- `abb.software.microsoft-sqlserver-2019`
- `abb.agent.crowdstrike-falcon`

The rule is to stay lowercase, keep the segments dot-separated, and use hyphens inside segments.

## How ABBs Are Used

ABBs become useful when they are referenced as internal components in RBBs.

- A host RBB uses an Operating System ABB and a Compute Platform ABB as
  foundational components, then adds any Agent ABBs physically installed on the
  host.
- A service RBB references one function ABB that provides the service capability, such as IIS or SQL Server.

This separation makes the architecture easier to reason about. For example,
`rbb.service.dbms.sqlserver-2022` does not need to redefine what SQL Server
2022 is. It can simply reference
`abb.software.microsoft-sqlserver-2022` as its function ABB and focus on the
architectural decisions that matter at the service level.

When an Agent ABB is used inside an RBB, the RBB must also declare the
corresponding `externalInteractions` that the agent depends on, unless an
Architecture Decision explains why the interaction is intentionally omitted.
That requirement does not apply to Software ABBs.

When a capability is satisfied by configuration rather than by a separate product,
the configuration should be named on the ABB itself. For example, an Operating
System ABB may declare a log-management configuration that redirects system
generated logs to a dedicated log volume.

## Appliance ABBs

An Appliance ABB is a special ABB subtype for a vendor-managed component whose
host is blackbox, but which is still deployed inside the adopter's
infrastructure boundary. The key idea is that there is no separable host for
the architect to model. The appliance and the underlying host are effectively
the same thing from the framework's perspective.

Use an Appliance ABB when the organization configures the component and places
it in its own AWS account, VPC, or datacenter, but does not manage the
underlying operating system, firmware, or host lifecycle directly.

Do not use an Appliance ABB when the component is just software installed on a
managed host. In that case it remains a
regular ABB and should appear as part of an RBB.

Do not use an Appliance ABB for a subscribed vendor service where traffic or
data leaves the adopter's infrastructure boundary and is processed in the
vendor's environment. That is a SaaS Service, not an Appliance ABB.

Good examples of Appliance ABBs are load balancers, blackbox runtime
hosts, managed file appliances, or vendor appliances with opaque host internals.
The catalog captures capabilities, network placement, patching ownership, the
configuration surface the adopter controls, failure domain, and compliance
posture instead of trying to invent a host model the architect does not
actually control.

## How To Add A New ABB

1. Decide whether the object is an Operating System, Compute Platform, Software, or Agent ABB.
2. Choose the correct ID pattern and make sure the ID is lowercase.
3. Create the YAML file in the correct folder.
4. Fill in the shared base fields: schema version, ID, type, name, description, version, catalog status, lifecycle status, owner, and tags.
5. Fill in the ABB-specific fields: `classification`, `vendor`, `productName`, `productVersion`, optional `platformDependency`, and vendor lifecycle.
6. Add `capabilities` if the ABB itself satisfies reusable host capabilities.
7. Add `configurations` if a named ABB configuration satisfies reusable host capabilities.
8. If the vendor publishes lifecycle dates, include them. If the vendor does not publish them, say so explicitly in `vendorLifecycle.notes` and leave the dates null rather than guessing.
9. Run `python3 tools/validate.py`.

## FAQ

### Do I need an ABB for every piece of software?

The rule is simple: if it must be installed and configured on a host or service, it needs an ABB. There is no judgment call about architectural significance.

This includes server software, agents, runtimes, open source projects, and vendor-bundled components that require separate installation. For example, IIS is not installed by default on Windows Server. It must be added and configured, so it gets its own ABB just like Apache or nginx would.

What does not need an ABB: code that is compiled or bundled into an application, such as libraries, frameworks, and packages, and anything with nothing to install. If there is no installation and configuration step on a host or service, there is no ABB.

### What if the vendor does not publish EOL dates?

Do not guess. Record that fact in `vendorLifecycle.notes` and leave the lifecycle dates null. A null date with a clear note is better than fake precision.

### What is `platformDependency`?

It records the platform an ABB assumes exists. For an agent ABB, that might be the SaaS platform the agent reports to. For specialized software, it might be an external service the product cannot function without. It does not replace `externalInteractions` on an RBB. It complements them.
