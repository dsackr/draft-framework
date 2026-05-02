# AI Framework Index

This generated file gives AI assistants a fast map of the DRAFT framework checkout.
It is intentionally framework-first: this upstream repository is a reusable template,
not a complete company architecture catalog. Organization-specific architecture content
belongs in private company DRAFT repos that vendor this framework under `.draft/framework/`.

Regenerate with:

```bash
python3 framework/tools/generate_ai_index.py
```

## Draftsman Bootstrap

When a user says "I need a draftsman", the AI should immediately assume the
Draftsman role defined in `framework/docs/draftsman.md`, then use this index,
the selected framework schemas/configurations, provider packs, and workspace YAML to guide the conversation and edits.

## Framework Entrypoints

| Path | Purpose |
|---|---|
| AGENTS.md | Canonical AI bootstrap instructions for this repository. |
| draft-framework.yaml | Machine-readable DRAFT Framework version and compatibility manifest. |
| VERSIONING.md | Framework semantic versioning and compatibility policy. |
| CHANGELOG.md | Required release notes for every framework release. |
| RELEASE.md | Release checklist for version, changelog, validation, and publishing steps. |
| pyproject.toml | Python packaging and draft-table CLI entry point. |
| draft_table | Local-first DRAFT Table CLI and web shell. |
| security.md | DRAFT Table credential and local security boundary. |
| framework/docs/draftsman.md | Draftsman role, intent routing, and authoring rules. |
| framework/docs/overview.md | Framework concepts and object family overview. |
| framework/docs/yaml-schema-reference.md | Quick map from object families to schemas. |
| framework/docs/how-to-add-objects.md | Practical object authoring workflow. |
| framework/docs/workspaces.md | Private workspace layout and source-based workflow. |
| framework/docs/requirement-groups.md | Unified requirement group authoring and validation behavior. |
| framework/docs/capabilities.md | Capability object model and implementation lookup behavior. |
| framework/docs/drafting-sessions.md | How to persist incomplete authoring work. |
| framework/tools/validate.py | Executable validation for schemas, Requirement Groups, capabilities, and references. |
| framework/tools/generate_browser.py | Static GitHub Pages browser generator. |
| install-draft-table.sh | Local DRAFT Table installer and onboarding launcher. |

## Framework Docs

| Path | Title | Summary |
|---|---|---|
| framework/docs/capabilities.md | Capabilities | A Capability is a first-class framework object that names an architecture |
| framework/docs/decision-records.md | Decision Records | Decision Records are first-class records for known risks, |
| framework/docs/drafting-sessions.md | Drafting Sessions | A Drafting Session is a machine-readable record of partial architecture work. |
| framework/docs/draftsman-ai-configuration.md | Draftsman AI Guidance | DRAFT does not include a built-in AI runtime. The Draftsman is an external AI |
| framework/docs/draftsman.md | Draftsman Instructions | The Draftsman is an AI architecture-authoring agent for DRAFT. It interviews the |
| framework/docs/how-to-add-objects.md | How To Add Objects | The fastest way to add a new object correctly is to decide what kind of thing you are modeling before you write YAML. |
| framework/docs/naming-conventions.md | Naming Conventions | The catalog relies on stable, predictable IDs because the IDs are the connective tissue between YAML objects, validat... |
| framework/docs/overview.md | Framework Overview | This page is the object map for the framework. It groups the catalog object |
| framework/docs/paas-service-standards.md | PaaS Service Standards | A PaaS Service is a vendor-managed platform capability that stays inside the |
| framework/docs/product-service.md | Product Service | A Product Service is the Standard classification used to represent a first-party |
| framework/docs/reference-architectures.md | Reference Architectures | A Reference Architecture is a deployment pattern. It tells application |
| framework/docs/requirement-groups.md | Requirement Groups | A Requirement Group is the unified DRAFT requirement model. It replaces the old |
| framework/docs/saas-service-standards.md | SaaS Service Standards | A SaaS Service is a vendor-managed service that the adopting organization |
| framework/docs/security-and-compliance-controls.md | Security And Compliance Requirement Groups | DRAFT treats compliance as an explicitly activated authoring and validation layer. |
| framework/docs/software-deployment-patterns.md | Software Deployment Patterns | A Software Deployment Pattern is a declaration that a specific product is intended |
| framework/docs/standards.md | Standards | A Standard is a reusable architecture object. It is the layer where the catalog defines |
| framework/docs/technology-components.md | Technology Components | A Technology Component is a discrete third-party product object. It records one |
| framework/docs/workspaces.md | Workspaces | DRAFT separates the upstream framework from private company implementation |
| framework/docs/yaml-schema-reference.md | YAML Schema Reference | This page is the quickest way to understand how to build a valid YAML object in |

## Schemas

| Path | Scope | Required Fields |
|---|---|---|
| framework/schemas/appliance-component.schema.yaml | appliance_component | schemaVersion, id, type, name, vendor, productName, productVersion, classification, catalogStatus, lifecycleStatus |
| framework/schemas/capability.schema.yaml | capability | schemaVersion, id, type, name, description, catalogStatus, definitionOwner, domain, implementations |
| framework/schemas/database-standard.schema.yaml | database_standard | schemaVersion, id, type, name, hostStandard, primaryTechnologyComponent, internalComponents, catalogStatus, lifecycleStatus |
| framework/schemas/decision-record.schema.yaml | decision_record | schemaVersion, id, type, name, category, status, catalogStatus, lifecycleStatus |
| framework/schemas/domain.schema.yaml | domain | schemaVersion, id, type, name, capabilities |
| framework/schemas/drafting-session.schema.yaml | drafting_session | schemaVersion, id, type, name, catalogStatus, lifecycleStatus, sessionStatus, primaryObjectType, sourceArtifacts, generatedObjects, unresolvedQuestions |
| framework/schemas/host-standard.schema.yaml | host_standard | schemaVersion, id, type, name, catalogStatus, lifecycleStatus |
| framework/schemas/object-patch.schema.yaml | object_patch | schemaVersion, id, type, name, target, patch, catalogStatus, lifecycleStatus |
| framework/schemas/paas-service-standard.schema.yaml | paas_service_standard | schemaVersion, id, type, name, vendor, catalogStatus, lifecycleStatus |
| framework/schemas/product-service.schema.yaml | product_service | schemaVersion, id, type, name, product, runsOn, catalogStatus, lifecycleStatus |
| framework/schemas/reference-architecture.schema.yaml | reference_architecture | schemaVersion, id, type, name, catalogStatus, lifecycleStatus |
| framework/schemas/requirement-group.schema.yaml | requirement_group | schemaVersion, id, type, name, description, catalogStatus, owner, activation, appliesTo, requirements |
| framework/schemas/saas-service-standard.schema.yaml | saas_service_standard | schemaVersion, id, type, name, vendor, dataLeavesInfrastructure, catalogStatus, lifecycleStatus |
| framework/schemas/service-standard.schema.yaml | service_standard | schemaVersion, id, type, name, hostStandard, primaryTechnologyComponent, internalComponents, catalogStatus, lifecycleStatus |
| framework/schemas/software-deployment-pattern.schema.yaml | software_deployment_pattern | schemaVersion, id, type, name, catalogStatus, lifecycleStatus |
| framework/schemas/technology-component.schema.yaml | technology_component | schemaVersion, id, type, name, vendor, productName, productVersion, classification, catalogStatus |

## Base Configurations

These YAML files are framework-owned base configurations. Company workspaces add third-party packs under `.draft/providers/` and company behavior through their private `configurations/` folder while keeping the vendored framework copy under `.draft/framework/` refreshable.

| ID | Name | Type | Tags | Description | Path |
|---|---|---|---|---|---|
| capability.access-control-model | Access Control Model | capability |  | Authorization model that controls access to a service or data platform. | framework/configurations/capabilities/capability-access-control-model.yaml |
| capability.apm | Application Performance Monitoring | capability |  | Tracing and performance analysis of application runtimes. | framework/configurations/capabilities/capability-apm.yaml |
| capability.authentication | Authentication | capability |  | Identity and access authentication capability for users, services, administrators, or workloads. | framework/configurations/capabilities/capability-authentication.yaml |
| capability.backup-strategy | Backup Strategy | capability |  | Backup, restore, and recovery point capability for durable data stores. | framework/configurations/capabilities/capability-backup-strategy.yaml |
| capability.compute-platform | Compute Platform | capability |  | Compute substrate or virtualized platform used to run host standards. | framework/configurations/capabilities/capability-compute-platform.yaml |
| capability.compute | General Purpose Compute | capability |  | Provisioning and execution of arbitrary code on reusable compute substrates. | framework/configurations/capabilities/capability-compute.yaml |
| capability.container-orchestration | Container Orchestration | capability |  | Management of containerized workload lifecycles. | framework/configurations/capabilities/capability-container-orchestration.yaml |
| capability.encryption-at-rest | Encryption At Rest | capability |  | Protection of persisted data through encryption or equivalent storage safeguards. | framework/configurations/capabilities/capability-encryption-at-rest.yaml |
| capability.health-welfare-monitoring | Health and Welfare Monitoring | capability |  | Runtime health, uptime, metrics, and operational welfare visibility. | framework/configurations/capabilities/capability-health-welfare-monitoring.yaml |
| capability.log-management | Log Management | capability |  | Aggregation, retention, searchability, and forwarding of system or application logs. | framework/configurations/capabilities/capability-log-management.yaml |
| capability.operating-system | Operating System | capability |  | Supported operating system product used to define managed host standards. | framework/configurations/capabilities/capability-operating-system.yaml |
| capability.patch-management | Patch Management | capability |  | Patch orchestration and update application capability for managed runtime components. | framework/configurations/capabilities/capability-patch-management.yaml |
| capability.performance-testing | Performance and Load Testing | capability |  | Capabilities to simulate load and measure system behavior under stress. | framework/configurations/capabilities/capability-performance-testing.yaml |
| capability.quality-gates | Quality Gates | capability |  | Promotion criteria and automated checks required for lifecycle transitions. | framework/configurations/capabilities/capability-quality-gates.yaml |
| capability.secrets-management | Secrets Management | capability |  | Secure storage, rotation, and access mediation for secrets and authenticators. | framework/configurations/capabilities/capability-secrets-management.yaml |
| capability.security-monitoring | Security Monitoring | capability |  | Threat detection, intrusion detection, security event monitoring, and audit telemetry. | framework/configurations/capabilities/capability-security-monitoring.yaml |
| capability.serverless-runtime | Serverless Function Runtime | capability |  | Event-driven, scale-to-zero compute runtime capability. | framework/configurations/capabilities/capability-serverless-runtime.yaml |
| capability.test-authoring | Test Authoring | capability |  | Tools and frameworks used to author automated tests. | framework/configurations/capabilities/capability-test-authoring.yaml |
| capability.test-execution | Test Execution and Automation | capability |  | Runtimes and orchestration services used to execute automated tests. | framework/configurations/capabilities/capability-test-execution.yaml |
| requirement-group.appliance-component | Appliance Component Requirement Group | requirement_group | appliance, requirement-group, definition | Structured requirements used to define a complete and correct Appliance Component. An Appliance Component is a vendor... | framework/configurations/requirement-groups/requirement-group-appliance-component.yaml |
| requirement-group.database-standard | DBMS Service Requirement Group | requirement_group | service, dbms, requirement-group, definition | Additional DBMS service checklist items extending the generic service Requirement Group for data durability, protecti... | framework/configurations/requirement-groups/requirement-group-database-standard.yaml |
| requirement-group.draft-nist-csf | NIST Cybersecurity Framework Requirement Group | requirement_group | compliance, nist, starter-pack, requirement-group | Initial NIST Cybersecurity Framework (CSF) 2.0 requirement group scoped to the outcomes that can be meaningfully answ... | framework/configurations/requirement-groups/requirement-group-draft-nist-csf.yaml |
| requirement-group.draft-security-compliance | Security and Security Compliance Requirement Group | requirement_group | compliance, controls, baseline, requirement-group | Baseline security and compliance requirement group bundled with DRAFT. Requirements are applied to matching object ty... | framework/configurations/requirement-groups/requirement-group-draft-security-compliance.yaml |
| requirement-group.draft-soc2 | SOC 2 Requirement Group | requirement_group | compliance, soc2, starter-pack, requirement-group | Initial SOC 2 requirement group based on the AICPA Trust Services Criteria. These requirements use DRAFT applicabilit... | framework/configurations/requirement-groups/requirement-group-draft-soc2.yaml |
| requirement-group.draft-tx-ramp | TX-RAMP Requirement Group | requirement_group | compliance, tx-ramp, starter-pack, requirement-group | Starter TX-RAMP requirement group for DRAFT. This file is intended to map TX-RAMP control expectations onto the unifi... | framework/configurations/requirement-groups/requirement-group-draft-tx-ramp.yaml |
| requirement-group.drafting-session | Drafting Session Requirement Group | requirement_group | drafting-session, requirement-group, intake | Structured checklist used to capture partial architecture-authoring sessions, generated outputs, and unresolved follo... | framework/configurations/requirement-groups/requirement-group-drafting-session.yaml |
| requirement-group.host-standard | Host Requirement Group | requirement_group | host, requirement-group, definition | Structured checklist of required questions and answers used to define a complete and correct Host Standard. | framework/configurations/requirement-groups/requirement-group-host-standard.yaml |
| requirement-group.paas-service-standard | PaaS Service Requirement Group | requirement_group | paas, requirement-group, definition | Structured requirements used to define a complete and correct PaaS Service. A PaaS Service is a vendor-managed platfo... | framework/configurations/requirement-groups/requirement-group-paas-service-standard.yaml |
| requirement-group.reference-architecture | Reference Architecture Requirement Group | requirement_group | reference-architecture, requirement-group, definition | Structured checklist of required questions and answers used to define a complete and correct Reference Architecture. | framework/configurations/requirement-groups/requirement-group-reference-architecture.yaml |
| requirement-group.saas-service-standard | SaaS Service Requirement Group | requirement_group | saas, requirement-group, definition | Structured requirements used to define a complete and correct SaaS Service. A SaaS Service is a vendor-managed offeri... | framework/configurations/requirement-groups/requirement-group-saas-service-standard.yaml |
| requirement-group.service-standard | General Service Requirement Group | requirement_group | service, requirement-group, definition | Structured checklist of required questions and answers used to define a complete and correct general Service Standard. | framework/configurations/requirement-groups/requirement-group-service-standard.yaml |
| requirement-group.software-deployment-pattern | Software Deployment Pattern Requirement Group | requirement_group | software-deployment-pattern, requirement-group, definition | Structured checklist of required questions and answers used to define a complete and correct software deployment patt... | framework/configurations/requirement-groups/requirement-group-software-deployment-pattern.yaml |
| domain.compute | Compute & Runtime | domain |  | Strategic domain covering application runtimes, serverless functions, and physical or virtual compute resources. | framework/configurations/domains/compute.yaml |
| domain.observability | Observability & Monitoring | domain |  | Strategic domain covering logging, metrics, tracing, and health monitoring across infrastructure and application stacks. | framework/configurations/domains/observability.yaml |
| domain.testing | Testing & Quality | domain |  | Strategic domain covering all aspects of software testing, quality assurance, and release gates. | framework/configurations/domains/testing.yaml |

## Example Catalog Inventory

These are sample catalog objects used to validate and demonstrate the framework. Company-specific content belongs in a private company `catalog/` folder.

| ID | Name | Type | Tags | Description | Path |
|---|---|---|---|---|---|
| technology.agent.crowdstrike-falcon | CrowdStrike Falcon Agent | technology_component | technology-component, agent | Endpoint security agent installed locally on a host that requires communication with the CrowdStrike Falcon platform. | examples/catalog/technology-components/technology-agent-crowdstrike-falcon.yaml |
| technology.compute.amazon-ec2-standard | Amazon EC2 Standard Compute Platform | technology_component | technology-component, compute-platform | Standard Amazon EC2 virtual machine substrate used for general-purpose host patterns. | examples/catalog/technology-components/technology-compute-amazon-ec2-standard.yaml |
| technology.os.canonical-ubuntu-2204 | Ubuntu 22.04 LTS | technology_component | technology-component, operating-system | Canonical Ubuntu Server 22.04 LTS operating system product definition for Linux host patterns. | examples/catalog/technology-components/technology-os-canonical-ubuntu-2204.yaml |
| technology.software.nginx-1-26 | nginx 1.26 | technology_component | technology-component, software | nginx web server software installed locally on a managed host and used without a required vendor platform interaction. | examples/catalog/technology-components/technology-software-nginx-126.yaml |
| appliance.aws-lambda-runtime | AWS Lambda Runtime | appliance_component | appliance, lambda | AWS Lambda serverless execution environment. Runs organization-authored function code without requiring host manageme... | examples/catalog/appliance-components/appliance-aws-lambda-runtime.yaml |
| host.serverless.lambda | AWS Lambda Serverless Host | host_standard | lambda, serverless | Serverless execution environment provided by AWS Lambda. The host is entirely AWS-managed and blackbox to the organiz... | examples/catalog/host-standards/host-serverless-lambda.yaml |

## Content Folder Counts

| Folder | YAML Count |
|---|---|
| framework/configurations/capabilities | 19 |
| framework/configurations/requirement-groups | 13 |
| framework/configurations/domains | 3 |
| examples/catalog/technology-components | 4 |
| examples/catalog/appliance-components | 1 |
| examples/catalog/host-standards | 1 |
| examples/catalog/service-standards | 0 |
| examples/catalog/database-standards | 0 |
| examples/catalog/reference-architectures | 0 |
| examples/catalog/software-deployment-patterns | 0 |
| examples/catalog/product-services | 0 |
| examples/catalog/saas-services | 0 |
| examples/catalog/decision-records | 0 |
| examples/catalog/sessions | 0 |

## Templates

| Path | Purpose |
|---|---|
| templates/appliance-component.yaml.tmpl | Reusable YAML authoring template. |
| templates/capability.yaml.tmpl | Reusable YAML authoring template. |
| templates/database-standard.yaml.tmpl | Reusable YAML authoring template. |
| templates/decision-record.yaml.tmpl | Reusable YAML authoring template. |
| templates/drafting-session.yaml.tmpl | Reusable YAML authoring template. |
| templates/host-standard.yaml.tmpl | Reusable YAML authoring template. |
| templates/object-patch.yaml.tmpl | Reusable YAML authoring template. |
| templates/paas-service-standard.yaml.tmpl | Reusable YAML authoring template. |
| templates/reference-architecture.yaml.tmpl | Reusable YAML authoring template. |
| templates/requirement-group.yaml.tmpl | Reusable YAML authoring template. |
| templates/saas-service-standard.yaml.tmpl | Reusable YAML authoring template. |
| templates/service-standard.yaml.tmpl | Reusable YAML authoring template. |
| templates/software-deployment-pattern.yaml.tmpl | Reusable YAML authoring template. |
| templates/technology-component.yaml.tmpl | Reusable YAML authoring template. |
| templates/workspace/.draft/framework.lock.tmpl | Reusable YAML authoring template. |
| templates/workspace/.draft/workspace.yaml.tmpl | Reusable YAML authoring template. |
| templates/workspace/.github/workflows/draft-framework-update.yml.tmpl | Reusable YAML authoring template. |
| templates/workspace/.gitignore.tmpl | Reusable YAML authoring template. |

## Validation

- Validate the example workspace: `python3 framework/tools/validate.py`
- Validate a company workspace: `python3 framework/tools/validate.py --workspace /path/to/workspace`
- Validate from inside a company repo: `python3 .draft/framework/tools/validate.py --workspace .`
- Regenerate browser after YAML changes: `python3 framework/tools/generate_browser.py`
- Regenerate this index after framework or YAML changes: `python3 framework/tools/generate_ai_index.py`
