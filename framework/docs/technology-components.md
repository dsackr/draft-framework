# Technology Components

## What A Technology Component Is

A Technology Component is a discrete third-party product object. It records one
vendor product at one product version so that Standards can
compose real products instead of generic categories.

That definition matters. A Technology Component is not “Windows Server” in the abstract. It is
`technology.os.microsoft-windowsserver-2022`. It is not “SQL Server” as a general
category. It is `technology.software.microsoft-sqlserver-2019` or
`technology.software.microsoft-sqlserver-2022`.

The framework uses that level of specificity because architecture standards
become misleading very quickly if version and vendor lifecycle are left
implicit.

## YAML Shape

Technology Components follow the authoritative
[technology-component.schema.yaml](../schemas/technology-component.schema.yaml) schema. Appliance Components
additionally follow
[appliance-component.schema.yaml](../schemas/appliance-component.schema.yaml).

At minimum, a Technology Component YAML should include:

- `id`
- `type: technology_component`
- `name`
- `vendor`
- `productName`
- `productVersion`
- `classification`
- `catalogStatus`

These fields are not optional modeling guidance. The validator enforces them.

## What Goes In A Technology Component

A Technology Component records the information engineers need in order to make technology
choices responsibly. It includes:

- vendor name
- product name
- product version
- Technology Component classification
- vendor lifecycle dates when those dates are known
- optional `platformDependency`
- capability references when the product itself can satisfy a capability

## Technology Component Classifications

Every Technology Component must declare exactly one classification.

| Classification | Meaning |
|---|---|
| Operating System | A vendor product that is the operating system. |
| Compute Platform | A vendor product that provides the physical or virtual compute substrate the operating system runs on. |
| Software | A vendor product that runs locally and does not require an external interaction. |
| Agent | A vendor product that runs locally and requires an external interaction. |

These classifications are machine-readable semantics, not just documentation
labels. The validator can use them when checking whether a Standard is built from
the right kinds of Technology Components.

Technology Components may also carry reusable capability metadata:

- `capabilities` when the Technology Component itself satisfies one or more host capabilities
- `configurations` when a named Technology Component configuration satisfies one or more host
  capabilities

A good example is the CrowdStrike Falcon agent. The Technology Component captures the fact that
the agent is installed locally on a host, but it also acknowledges that the
agent exists to connect the host to the CrowdStrike platform by providing
the `capability.security-monitoring` capability.

Company adoption of a Technology Component is not recorded as top-level
`lifecycleStatus` on the Technology Component. It is recorded on the relevant
Capability implementation entry, because one company may invest in the product
for one capability and only maintain it for another.

## What A Technology Component Is Not

A Technology Component is not a deployment artifact. It does not say where or how many times a product is deployed.

A Technology Component is not a Standard. It does not describe a reusable architecture pattern built from multiple components.

A Technology Component is not a running system. If an organization has a production SQL Server cluster, the Technology Component is not the cluster. The Technology Component is the reusable standard describing the SQL Server version that a cluster or service Standard may depend on.

## Naming Convention

The naming convention is intentionally rigid.

- Operating System Technology Components typically follow `technology.os.<vendor>-<os>-<major>`
- Compute Platform Technology Components typically follow `technology.hardware.<vendor>-<product>`
- Software Technology Components typically follow `technology.software.<vendor>-<product>-<ver>`
- Agent Technology Components typically follow `technology.agent.<vendor>-<product>`

Examples:

- `technology.os.amazon-linux-2`
- `technology.os.microsoft-windowsserver-2022`
- `technology.hardware.amazon-ec2-standard`
- `technology.software.microsoft-sqlserver-2019`
- `technology.agent.crowdstrike-falcon`

The rule is to stay lowercase, keep the segments dot-separated, and use hyphens inside segments.

## How Technology Components Are Used

Technology Components become useful when they are referenced as internal components in Standards.

- A host Standard uses an Operating System Technology Component and a Compute Platform Technology Component as
  foundational components, then adds any Agent Technology Components physically installed on the
  host.
- A service Standard references one function Technology Component that provides the service capability, such as IIS or SQL Server.

This separation makes the architecture easier to reason about. For example,
`database.sqlserver-2022` does not need to redefine what SQL Server
2022 is. It can simply reference
`technology.software.microsoft-sqlserver-2022` as its function Technology Component and focus on the
architectural decisions that matter at the service level.

When an Agent Technology Component is used inside a Standard, the Standard must also declare the
corresponding `externalInteractions` that the agent depends on, unless an
architectural decision entry explains why the interaction is intentionally omitted.
That requirement does not apply to Software Technology Components.

When a capability is satisfied by configuration rather than by a separate product,
the configuration should be named on the Technology Component itself. For example, an Operating
System Technology Component may declare a log-management configuration that redirects system
generated logs to a dedicated log volume.

## Appliance Components

An Appliance Component is a special Technology Component subtype for a vendor-managed component whose
host is blackbox, but which is still deployed inside the adopter's
infrastructure boundary. The key idea is that there is no separable host for
the architect to model. The appliance and the underlying host are effectively
the same thing from the framework's perspective.

An Appliance Component is still a Technology Component by identity: it maps directly to a discrete
vendor product and version. It is not a normal Standard because it does not expose a
host, operating system, compute platform, or function Technology Component that the framework can
compose. Architecturally, however, it behaves like a deployed service
capability: adopters depend on it to do useful work inside their infrastructure
boundary.

That blackbox boundary is why the appliance Requirement Group carries service-like operating
questions directly on the Technology Component. A normal host Standard inherits the host baseline
through `requirement-group.host-standard`, and a normal service Standard inherits service requirements
through `requirement-group.service-standard`. An Appliance Component does neither. It must therefore answer
consumer-facing capabilities such as authentication/access, log or audit
visibility, health/status visibility, patch/update model, resilience, network
placement, configurable surface, failure domain, and compliance posture on the
appliance object itself.

Use an Appliance Component when the organization configures the component and places
it in its own AWS account, VPC, or datacenter, but does not manage the
underlying operating system, firmware, or host lifecycle directly.

Do not use an Appliance Component when the component is just software installed on a
managed host. In that case it remains a
regular Technology Component and should appear as part of a Standard.

Do not use an Appliance Component for a subscribed vendor service where traffic or
data leaves the adopter's infrastructure boundary and is processed in the
vendor's environment. That is a SaaS Service, not an Appliance Component.

Good examples of Appliance Components are load balancers, blackbox runtime
hosts, managed file appliances, or vendor appliances with opaque host internals.
The catalog captures capabilities, access model, log and audit visibility,
health and status visibility, patch/update model, network placement, the
configuration surface the adopter controls, failure domain, and compliance
posture instead of trying to invent a host model the architect does not actually
control.

## How To Add A New Technology Component

1. Decide whether the object is an Operating System, Compute Platform, Software, or Agent Technology Component.
2. Choose the correct ID pattern and make sure the ID is lowercase.
3. Create the YAML file in the correct folder.
4. Fill in the shared base fields: schema version, ID, type, name, description, version, catalog status, lifecycle status, owner, and tags.
5. Fill in the Technology Component-specific fields: `classification`, `vendor`, `productName`, `productVersion`, optional `platformDependency`, and vendor lifecycle.
6. Add `capabilities` if the Technology Component itself satisfies reusable host capabilities.
7. Add `configurations` if a named Technology Component configuration satisfies reusable host capabilities.
8. If the vendor publishes lifecycle dates, include them. If the vendor does not publish them, say so explicitly in `vendorLifecycle.notes` and leave the dates null rather than guessing.
9. Run `python3 framework/tools/validate.py`.

## FAQ

### Do I need a Technology Component for every piece of software?

The rule is simple: if it must be installed and configured on a host or service, it needs a Technology Component. There is no judgment call about architectural significance.

This includes server software, agents, runtimes, open source projects, and vendor-bundled components that require separate installation. For example, IIS is not installed by default on Windows Server. It must be added and configured, so it gets its own Technology Component just like Apache or nginx would.

What does not need a Technology Component: code that is compiled or bundled into an application, such as libraries, frameworks, and packages, and anything with nothing to install. If there is no installation and configuration step on a host or service, there is no Technology Component.

### What if the vendor does not publish EOL dates?

Do not guess. Record that fact in `vendorLifecycle.notes` and leave the lifecycle dates null. A null date with a clear note is better than fake precision.

### What is `platformDependency`?

It records the platform a Technology Component assumes exists. For an agent Technology Component, that might be the SaaS platform the agent reports to. For specialized software, it might be an external service the product cannot function without. It does not replace `externalInteractions` on a Standard. It complements them.
