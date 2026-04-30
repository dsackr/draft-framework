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
| pyproject.toml | Python packaging and draft-table CLI entry point. |
| draft_table | Local-first DRAFT Table CLI and web shell. |
| security.md | DRAFT Table credential and local security boundary. |
| framework/docs/draftsman.md | Draftsman role, intent routing, and authoring rules. |
| framework/docs/overview.md | Framework concepts and object family overview. |
| framework/docs/yaml-schema-reference.md | Quick map from object families to schemas. |
| framework/docs/how-to-add-objects.md | Practical object authoring workflow. |
| framework/docs/workspaces.md | Private workspace layout and source-based workflow. |
| framework/docs/definition-checklists.md | Definition Checklist model and validation behavior. |
| framework/docs/drafting-sessions.md | How to persist incomplete authoring work. |
| framework/tools/validate.py | Executable validation for schemas, Definition Checklists, references, and controls. |
| framework/tools/generate_browser.py | Static GitHub Pages browser generator. |
| install-draft-table.sh | Local DRAFT Table installer and onboarding launcher. |

## Framework Docs

| Path | Title | Summary |
|---|---|---|
| framework/docs/decision-records.md | Decision Records | Decision Records are first-class records for known risks, |
| framework/docs/definition-checklists.md | Definition Checklists | A Definition Checklist is **a structured checklist of |
| framework/docs/drafting-sessions.md | Drafting Sessions | A Drafting Session is a machine-readable record of partial architecture work. |
| framework/docs/draftsman-ai-configuration.md | Draftsman AI Guidance | DRAFT does not include a built-in AI runtime. The Draftsman is an external AI |
| framework/docs/draftsman.md | Draftsman Instructions | This document is written for an AI assistant that is using this repository as |
| framework/docs/how-to-add-objects.md | How To Add Objects | The fastest way to add a new object correctly is to decide what kind of thing you are modeling before you write YAML. |
| framework/docs/naming-conventions.md | Naming Conventions | The catalog relies on stable, predictable IDs because the IDs are the connective tissue between YAML objects, validat... |
| framework/docs/overview.md | Framework Overview | This page is the object map for the framework. It groups the catalog object |
| framework/docs/paas-service-standards.md | PaaS Service Standards | A PaaS Service is a vendor-managed platform capability that stays inside the |
| framework/docs/product-service.md | Product Service | A Product Service is the Standard classification used to represent a first-party |
| framework/docs/reference-architectures.md | Reference Architectures | A Reference Architecture is a deployment pattern. It tells application |
| framework/docs/saas-service-standards.md | SaaS Service Standards | A SaaS Service is a vendor-managed service that the adopting organization |
| framework/docs/security-and-compliance-controls.md | Security and Compliance Controls | DRAFT treats compliance as an explicitly activated authoring layer rather than |
| framework/docs/software-deployment-patterns.md | Software Deployment Patterns | A Software Deployment Pattern is a declaration that a specific product is intended |
| framework/docs/standards.md | Standards | A Standard is a reusable architecture object. It is the layer where the catalog defines |
| framework/docs/technology-components.md | Technology Components | A Technology Component is a discrete third-party product object. It records one |
| framework/docs/workspaces.md | Workspaces | DRAFT separates the upstream framework from private company implementation |
| framework/docs/yaml-schema-reference.md | YAML Schema Reference | This page is the quickest way to understand how to build a valid YAML object in |

## Schemas

| Path | Scope | Required Fields |
|---|---|---|
| framework/schemas/appliance-component.schema.yaml | appliance_component | schemaVersion, id, type, name, vendor, productName, productVersion, classification, catalogStatus, lifecycleStatus |
| framework/schemas/compliance-controls.schema.yaml | compliance_controls | schemaVersion, id, type, name, controlsKind, catalogStatus, lifecycleStatus |
| framework/schemas/control-enforcement-profile.schema.yaml | control_enforcement_profile | schemaVersion, id, type, name, controls, catalogStatus, lifecycleStatus |
| framework/schemas/database-standard.schema.yaml | database_standard | schemaVersion, id, type, name, hostStandard, primaryTechnologyComponent, internalComponents, catalogStatus, lifecycleStatus |
| framework/schemas/decision-record.schema.yaml | decision_record | schemaVersion, id, type, name, category, status, catalogStatus, lifecycleStatus |
| framework/schemas/definition-checklist.schema.yaml | definition_checklist | schemaVersion, id, type, name, description, requirements |
| framework/schemas/domain.schema.yaml | domain | schemaVersion, id, type, name, capabilities |
| framework/schemas/drafting-session.schema.yaml | drafting_session | schemaVersion, id, type, name, catalogStatus, lifecycleStatus, sessionStatus, primaryObjectType, sourceArtifacts, generatedObjects, unresolvedQuestions |
| framework/schemas/host-standard.schema.yaml | host_standard | schemaVersion, id, type, name, catalogStatus, lifecycleStatus |
| framework/schemas/object-patch.schema.yaml | object_patch | schemaVersion, id, type, name, target, patch, catalogStatus, lifecycleStatus |
| framework/schemas/paas-service-standard.schema.yaml | paas_service_standard | schemaVersion, id, type, name, vendor, catalogStatus, lifecycleStatus |
| framework/schemas/product-service.schema.yaml | product_service | schemaVersion, id, type, name, product, runsOn, catalogStatus, lifecycleStatus |
| framework/schemas/reference-architecture.schema.yaml | reference_architecture | schemaVersion, id, type, name, catalogStatus, lifecycleStatus |
| framework/schemas/saas-service-standard.schema.yaml | saas_service_standard | schemaVersion, id, type, name, vendor, dataLeavesInfrastructure, catalogStatus, lifecycleStatus |
| framework/schemas/service-standard.schema.yaml | service_standard | schemaVersion, id, type, name, hostStandard, primaryTechnologyComponent, internalComponents, catalogStatus, lifecycleStatus |
| framework/schemas/software-deployment-pattern.schema.yaml | software_deployment_pattern | schemaVersion, id, type, name, catalogStatus, lifecycleStatus |
| framework/schemas/technology-component.schema.yaml | technology_component | schemaVersion, id, type, name, vendor, productName, productVersion, classification, catalogStatus, lifecycleStatus |

## Base Configurations

These YAML files are framework-owned base configurations. Company workspaces add third-party packs under `.draft/providers/` and company behavior through their private `configurations/` folder while keeping the vendored framework copy under `.draft/framework/` refreshable.

| ID | Name | Type | Tags | Description | Path |
|---|---|---|---|---|---|
| checklist.appliance-component | Appliance Component Definition Checklist | definition_checklist | appliance, checklist, definition | Structured checklist of required questions and answers used to define a complete and correct Appliance Component. An... | framework/configurations/definition-checklists/checklist-appliance-component.yaml |
| checklist.compliance-controls | Compliance Controls Definition Checklist | definition_checklist | definition-checklist, compliance | Structured checklist for defining a pure control catalog in DRAFT. This Definition Checklist is focused on the contro... | framework/configurations/definition-checklists/checklist-compliance-controls.yaml |
| checklist.control-enforcement-profile | Control Enforcement Profile Definition Checklist | definition_checklist | definition-checklist, compliance, control-enforcement-profile | Structured checklist for defining how a pure control catalog is applied in DRAFT. This Definition Checklist captures... | framework/configurations/definition-checklists/checklist-control-enforcement-profile.yaml |
| checklist.database-standard | DBMS Service Definition Checklist | definition_checklist | service, dbms, checklist, definition | Additional DBMS service checklist items extending the generic service Definition Checklist for data durability, prote... | framework/configurations/definition-checklists/checklist-database-standard.yaml |
| checklist.drafting-session | Drafting Session Definition Checklist | definition_checklist | drafting-session, checklist, intake | Structured checklist used to capture partial architecture-authoring sessions, generated outputs, and unresolved follo... | framework/configurations/definition-checklists/checklist-drafting-session.yaml |
| checklist.host-standard | Host Definition Checklist | definition_checklist | host, checklist, definition | Structured checklist of required questions and answers used to define a complete and correct Host Standard. | framework/configurations/definition-checklists/checklist-host-standard.yaml |
| checklist.paas-service-standard | PaaS Service Definition Checklist | definition_checklist | paas, checklist, definition | Structured checklist of required questions and answers used to define a complete and correct PaaS Service. A PaaS Ser... | framework/configurations/definition-checklists/checklist-paas-service-standard.yaml |
| checklist.reference-architecture | Reference Architecture Definition Checklist | definition_checklist | reference-architecture, checklist, definition | Structured checklist of required questions and answers used to define a complete and correct Reference Architecture. | framework/configurations/definition-checklists/checklist-reference-architecture.yaml |
| checklist.saas-service-standard | SaaS Service Definition Checklist | definition_checklist | saas, checklist, definition | Structured checklist of required questions and answers used to define a complete and correct SaaS Service. A SaaS Ser... | framework/configurations/definition-checklists/checklist-saas-service-standard.yaml |
| checklist.service-standard | General Service Definition Checklist | definition_checklist | service, checklist, definition | Structured checklist of required questions and answers used to define a complete and correct general Service Standard. | framework/configurations/definition-checklists/checklist-service-standard.yaml |
| checklist.software-deployment-pattern | Software Deployment Pattern Definition Checklist | definition_checklist | software-deployment-pattern, checklist, definition | Structured checklist of required questions and answers used to define a complete and correct software deployment patt... | framework/configurations/definition-checklists/checklist-software-deployment-pattern.yaml |
| controls.draft-nist-csf | NIST Cybersecurity Framework | compliance_controls | compliance, nist, starter-pack | Initial NIST Cybersecurity Framework (CSF) 2.0 control pack scoped to the outcomes that can be meaningfully answered... | framework/configurations/compliance-controls/controls-draft-nist-csf.yaml |
| controls.draft-organization-template | Organization Controls Overlay | compliance_controls | compliance, organizational, extensibility | Template framework for organization-specific controls. Clone this file, rename the id and name, and populate controls... | framework/configurations/compliance-controls/controls-draft-organization-template.yaml |
| controls.draft-security-compliance | Security and Compliance Controls | compliance_controls | compliance, controls, baseline | Baseline controls pack bundled with DRAFT. Required controls are defined inline and are applied to matching Definitio... | framework/configurations/compliance-controls/controls-draft-security-compliance.yaml |
| controls.draft-soc2 | SOC 2 | compliance_controls | compliance, soc2, starter-pack | Initial SOC 2 control pack based on the AICPA Trust Services Criteria. These controls use DRAFT applicability metadat... | framework/configurations/compliance-controls/controls-draft-soc2.yaml |
| controls.draft-tx-ramp | TX-RAMP | compliance_controls | compliance, tx-ramp, starter-pack | Starter TX-RAMP control pack for DRAFT. This file is intended to map TX-RAMP control expectations onto the existing D... | framework/configurations/compliance-controls/controls-draft-tx-ramp.yaml |
| control-enforcement.draft-nist-csf | NIST Cybersecurity Framework Profile | control_enforcement_profile | compliance, nist, starter-pack, control-enforcement-profile | Control Enforcement Profile for NIST Cybersecurity Framework controls. | framework/configurations/control-enforcement-profiles/control-enforcement-draft-nist-csf.yaml |
| control-enforcement.draft-organization-template | Organization Controls Overlay Profile | control_enforcement_profile | compliance, organizational, extensibility, control-enforcement-profile | Control Enforcement Profile for Organization Controls Overlay controls. | framework/configurations/control-enforcement-profiles/control-enforcement-draft-organization-template.yaml |
| control-enforcement.draft-security-compliance | Security and Compliance Controls Profile | control_enforcement_profile | compliance, controls, baseline, control-enforcement-profile | Control Enforcement Profile for Security and Compliance Controls. | framework/configurations/control-enforcement-profiles/control-enforcement-draft-security-compliance.yaml |
| control-enforcement.draft-soc2 | SOC 2 Profile | control_enforcement_profile | compliance, soc2, starter-pack, control-enforcement-profile | Control Enforcement Profile for SOC 2 controls. | framework/configurations/control-enforcement-profiles/control-enforcement-draft-soc2.yaml |
| control-enforcement.draft-tx-ramp | TX-RAMP Profile | control_enforcement_profile | compliance, tx-ramp, starter-pack, control-enforcement-profile | Control Enforcement Profile for TX-RAMP controls. | framework/configurations/control-enforcement-profiles/control-enforcement-draft-tx-ramp.yaml |
| domain.compute | Compute & Runtime | domain |  | Strategic domain covering application runtimes, serverless functions, and physical/virtual compute resources. | framework/configurations/domains/compute.yaml |
| domain.observability | Observability & Monitoring | domain |  | Strategic domain covering logging, metrics, tracing, and health monitoring across the infrastructure and application... | framework/configurations/domains/observability.yaml |
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
| framework/configurations/definition-checklists | 11 |
| framework/configurations/compliance-controls | 5 |
| framework/configurations/control-enforcement-profiles | 5 |
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
| templates/appliance-component.yaml.tmpl | Template for an Appliance Component. |
| templates/compliance-controls.yaml.tmpl | Template for a pure Compliance Controls control catalog. |
| templates/control-enforcement-profile.yaml.tmpl | Template for a Control Enforcement Profile that maps controls to DRAFT semantics. |
| templates/database-standard.yaml.tmpl | Template for a Database Service Standard. |
| templates/decision-record.yaml.tmpl | Template for a Decision Record. |
| templates/drafting-session.yaml.tmpl | Template for a Drafting Session that preserves incomplete authoring state. |
| templates/host-standard.yaml.tmpl | Template for a Host Standard. |
| templates/object-patch.yaml.tmpl | Template for a configuration object patch. |
| templates/paas-service-standard.yaml.tmpl | Template for a PaaS Service Standard. |
| templates/reference-architecture.yaml.tmpl | Template for a Reference Architecture. |
| templates/saas-service-standard.yaml.tmpl | Template for a SaaS Service Standard. |
| templates/service-standard.yaml.tmpl | Template for a general Service Standard. |
| templates/software-deployment-pattern.yaml.tmpl | Template for a Software Deployment Pattern. |
| templates/technology-component.yaml.tmpl | Template for a standard Technology Component. |
| templates/workspace/.draft/framework.lock.tmpl | Reusable YAML authoring template. |
| templates/workspace/.draft/workspace.yaml.tmpl | Reusable YAML authoring template. |
| templates/workspace/.gitignore.tmpl | Reusable YAML authoring template. |

## Validation

- Validate the example workspace: `python3 framework/tools/validate.py`
- Validate a company workspace: `python3 framework/tools/validate.py --workspace /path/to/workspace`
- Validate from inside a company repo: `python3 .draft/framework/tools/validate.py --workspace .`
- Regenerate browser after YAML changes: `python3 framework/tools/generate_browser.py`
- Regenerate this index after framework or YAML changes: `python3 framework/tools/generate_ai_index.py`
