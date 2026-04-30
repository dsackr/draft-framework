# AI Framework Index

This generated file gives AI assistants a fast map of the DRAFT framework checkout.
It is intentionally framework-first: this upstream repository is a reusable template,
not a complete company architecture catalog. Organization-specific architecture content
belongs in downstream private clones.

Regenerate with:

```bash
python3 framework/tools/generate_ai_index.py
```

## Draftsman Bootstrap

When a user says "I need a draftsman", the AI should immediately assume the
Draftsman role defined in `framework/docs/draftsman.md`, then use this index,
`framework/schemas/`, `framework/configurations/`, and workspace YAML to guide the conversation and edits.

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
| framework/docs/odcs.md | Object Definition Checklist model and validation behavior. |
| framework/docs/drafting-sessions.md | How to persist incomplete authoring work. |
| framework/tools/validate.py | Executable validation for schemas, ODCs, references, and controls. |
| framework/tools/generate_browser.py | Static GitHub Pages browser generator. |
| install-draft-table.sh | Local DRAFT Table installer and onboarding launcher. |

## Framework Docs

| Path | Title | Summary |
|---|---|---|
| framework/docs/abbs.md | ABBs | An Architecture Building Block, or ABB, is a discrete third-party product |
| framework/docs/deployment-risks-and-decisions.md | Deployment Risks And Decisions | Deployment Risks and Decisions are first-class records for known risks, |
| framework/docs/drafting-sessions.md | Drafting Sessions | A Drafting Session is a machine-readable record of partial architecture work. |
| framework/docs/draftsman-ai-configuration.md | Draftsman AI Guidance | DRAFT does not include a built-in AI runtime. The Draftsman is an external AI |
| framework/docs/draftsman.md | Draftsman Instructions | This document is written for an AI assistant that is using this repository as |
| framework/docs/how-to-add-objects.md | How To Add Objects | The fastest way to add a new object correctly is to decide what kind of thing you are modeling before you write YAML. |
| framework/docs/naming-conventions.md | Naming Conventions | The catalog relies on stable, predictable IDs because the IDs are the connective tissue between YAML objects, validat... |
| framework/docs/odcs.md | ODCs | An Object Definition Checklist, or ODC, is **a structured checklist of |
| framework/docs/overview.md | Framework Overview | This page is the object map for the framework. It groups the catalog object |
| framework/docs/paas-services.md | PaaS Services | A PaaS Service is a vendor-managed platform capability that stays inside the |
| framework/docs/product-service.md | Product Service | A Product Service is the RBB classification used to represent a first-party |
| framework/docs/rbbs.md | RBBs | An RBB, or Reference Building Block, is the framework's only reusable |
| framework/docs/reference-architectures.md | Reference Architectures | A Reference Architecture, or RA, is a deployment pattern. It tells application |
| framework/docs/saas-services.md | SaaS Services | A SaaS Service is a vendor-managed service that the adopting organization |
| framework/docs/security-and-compliance-controls.md | Security and Compliance Controls | DRAFT treats compliance as a pluggable layer rather than a fixed property of |
| framework/docs/software-distribution-manifests.md | Software Distribution Manifests | A Software Distribution Manifest, or SDM, is a declaration that a specific product is distributed and deployed accord... |
| framework/docs/workspaces.md | Workspaces | DRAFT separates the public framework from private company content. |
| framework/docs/yaml-schema-reference.md | YAML Schema Reference | This page is the quickest way to understand how to build a valid YAML object in |

## Schemas

| Path | Scope | Required Fields |
|---|---|---|
| framework/schemas/abb-appliance.schema.yaml | abb.appliance | schemaVersion, id, type, name, vendor, productName, productVersion, classification, catalogStatus, lifecycleStatus |
| framework/schemas/abb.schema.yaml | abb | schemaVersion, id, type, name, vendor, productName, productVersion, classification, catalogStatus, lifecycleStatus |
| framework/schemas/ard.schema.yaml | ard | schemaVersion, id, type, name, category, status, description, affectedComponent, impact |
| framework/schemas/compliance-framework.schema.yaml | compliance_framework | schemaVersion, id, type, name, frameworkKind, catalogStatus, lifecycleStatus |
| framework/schemas/compliance-profile.schema.yaml | compliance_profile | schemaVersion, id, type, name, framework, catalogStatus, lifecycleStatus |
| framework/schemas/domain.schema.yaml | domain | schemaVersion, id, type, name, capabilities |
| framework/schemas/drafting-session.schema.yaml | drafting_session | schemaVersion, id, type, name, catalogStatus, lifecycleStatus, sessionStatus, primaryObjectType, sourceArtifacts, generatedObjects, unresolvedQuestions |
| framework/schemas/object-patch.schema.yaml | object_patch | schemaVersion, id, type, name, target, patch, catalogStatus, lifecycleStatus |
| framework/schemas/odc.schema.yaml | odc | schemaVersion, id, type, name, description, requirements |
| framework/schemas/paas-service.schema.yaml | rbb.service.paas | schemaVersion, id, type, category, serviceCategory, name, vendor, catalogStatus, lifecycleStatus |
| framework/schemas/ps.schema.yaml | rbb.service.product | schemaVersion, id, type, category, serviceCategory, name, product, runsOn, catalogStatus, lifecycleStatus |
| framework/schemas/rbb.schema.yaml | rbb | schemaVersion, id, type, name, catalogStatus, lifecycleStatus, category |
| framework/schemas/reference-architecture.schema.yaml | reference_architecture | schemaVersion, id, type, name, catalogStatus, lifecycleStatus, serviceGroups |
| framework/schemas/saas-service.schema.yaml | rbb.service.saas | schemaVersion, id, type, category, serviceCategory, name, vendor, catalogStatus, lifecycleStatus, dataLeavesInfrastructure |
| framework/schemas/sdm.schema.yaml | software_distribution_manifest | schemaVersion, id, type, name, catalogStatus, lifecycleStatus |

## Base Configurations

These YAML files are framework-owned base configurations. Company workspaces add or override behavior through their private `configurations/` folder.

| ID | Name | Type | Tags | Description | Path |
|---|---|---|---|---|---|
| odc.appliance-abb | Appliance ABB Object Definition Checklist | odc | appliance, checklist, definition | Structured checklist of required questions and answers used to define a complete and correct Appliance ABB. An Applia... | framework/configurations/odcs/odc-appliance-abb.yaml |
| odc.paas-service | PaaS Service Object Definition Checklist | odc | paas, checklist, definition | Structured checklist of required questions and answers used to define a complete and correct PaaS Service. A PaaS Ser... | framework/configurations/odcs/odc-paas-service.yaml |
| odc.saas-service | SaaS Service Object Definition Checklist | odc | saas, checklist, definition | Structured checklist of required questions and answers used to define a complete and correct SaaS Service. A SaaS Ser... | framework/configurations/odcs/odc-saas-service.yaml |
| odc.compliance-framework | Compliance Framework ODC | odc | odc, compliance | Structured checklist for defining a pure control catalog in DRAFT. This ODC is focused on the control facts themselve... | framework/configurations/odcs/odc.compliance-framework.yaml |
| odc.compliance-profile | Compliance Profile ODC | odc | odc, compliance, profile | Structured checklist for defining how a pure control catalog is applied in DRAFT. This ODC captures DRAFT-specific se... | framework/configurations/odcs/odc.compliance-profile.yaml |
| odc.drafting-session | Drafting Session Object Definition Checklist | odc | drafting-session, checklist, intake | Structured checklist used to capture partial architecture-authoring sessions, generated outputs, and unresolved follo... | framework/configurations/odcs/odc.drafting-session.yaml |
| odc.host | Host Object Definition Checklist | odc | host, checklist, definition | Structured checklist of required questions and answers used to define a complete and correct host RBB. | framework/configurations/odcs/odc.host.yaml |
| odc.ra | Reference Architecture Object Definition Checklist | odc | ra, checklist, definition | Structured checklist of required questions and answers used to define a complete and correct Reference Architecture. | framework/configurations/odcs/odc.ra.yaml |
| odc.sdm | Software Distribution Manifest Object Definition Checklist | odc | sdm, checklist, definition | Structured checklist of required questions and answers used to define a complete and correct software distribution ma... | framework/configurations/odcs/odc.sdm.yaml |
| odc.service.dbms | DBMS Service Object Definition Checklist | odc | service, dbms, checklist, definition | Additional DBMS service checklist items extending the generic service ODC for data durability, protection, and control. | framework/configurations/odcs/odc.service.dbms.yaml |
| odc.service | General Service Object Definition Checklist | odc | service, checklist, definition | Structured checklist of required questions and answers used to define a complete and correct general service RBB. | framework/configurations/odcs/odc.service.yaml |
| framework.nist-csf | NIST Cybersecurity Framework | compliance_framework | compliance, nist, starter-pack | Initial NIST Cybersecurity Framework (CSF) 2.0 control pack scoped to the outcomes that can be meaningfully answered... | framework/configurations/compliance-frameworks/framework-nist-csf.yaml |
| framework.organization-controls | Organization Controls Overlay | compliance_framework | compliance, organizational, extensibility | Template framework for organization-specific controls. Clone this file, rename the id and name, and populate controls... | framework/configurations/compliance-frameworks/framework-organization-controls.yaml |
| framework.security-compliance-controls | Security and Compliance Controls | compliance_framework | compliance, controls, baseline | Baseline controls pack bundled with DRAFT. Required controls are defined inline and are applied to matching ODCs at r... | framework/configurations/compliance-frameworks/framework-security-compliance-controls.yaml |
| framework.soc2 | SOC 2 | compliance_framework | compliance, soc2, starter-pack | Initial SOC 2 control pack based on the AICPA Trust Services Criteria. These controls use DRAFT applicability metadat... | framework/configurations/compliance-frameworks/framework-soc2.yaml |
| framework.tx-ramp | TX-RAMP | compliance_framework | compliance, tx-ramp, starter-pack | Starter TX-RAMP control pack for DRAFT. This file is intended to map TX-RAMP control expectations onto the existing D... | framework/configurations/compliance-frameworks/framework-tx-ramp.yaml |
| profile.nist-csf | NIST Cybersecurity Framework Profile | compliance_profile | compliance, nist, starter-pack, profile | DRAFT implementation profile for NIST Cybersecurity Framework. | framework/configurations/compliance-profiles/profile-nist-csf.yaml |
| profile.organization-controls | Organization Controls Overlay Profile | compliance_profile | compliance, organizational, extensibility, profile | DRAFT implementation profile for Organization Controls Overlay. | framework/configurations/compliance-profiles/profile-organization-controls.yaml |
| profile.security-compliance-controls | Security and Compliance Controls Profile | compliance_profile | compliance, controls, baseline, profile | DRAFT implementation profile for Security and Compliance Controls. | framework/configurations/compliance-profiles/profile-security-compliance-controls.yaml |
| profile.soc2 | SOC 2 Profile | compliance_profile | compliance, soc2, starter-pack, profile | DRAFT implementation profile for SOC 2. | framework/configurations/compliance-profiles/profile-soc2.yaml |
| profile.tx-ramp | TX-RAMP Profile | compliance_profile | compliance, tx-ramp, starter-pack, profile | DRAFT implementation profile for TX-RAMP. | framework/configurations/compliance-profiles/profile-tx-ramp.yaml |
| domain.compute | Compute & Runtime | domain |  | Strategic domain covering application runtimes, serverless functions, and physical/virtual compute resources. | framework/configurations/domains/compute.yaml |
| domain.observability | Observability & Monitoring | domain |  | Strategic domain covering logging, metrics, tracing, and health monitoring across the infrastructure and application... | framework/configurations/domains/observability.yaml |
| domain.testing | Testing & Quality | domain |  | Strategic domain covering all aspects of software testing, quality assurance, and release gates. | framework/configurations/domains/testing.yaml |

## Example Catalog Inventory

These are sample catalog objects used to validate and demonstrate the framework. Company-specific content belongs in a private workspace `catalog/` folder.

| ID | Name | Type | Tags | Description | Path |
|---|---|---|---|---|---|
| abb.agent.crowdstrike-falcon | CrowdStrike Falcon Agent | abb | abb, agent | Endpoint security agent installed locally on a host that requires communication with the CrowdStrike Falcon platform. | examples/catalog/abbs/abb-agent-crowdstrike-falcon.yaml |
| abb.appliance.aws-lambda-runtime | AWS Lambda Runtime | abb | appliance, lambda | AWS Lambda serverless execution environment. Runs organization-authored function code without requiring host manageme... | examples/catalog/abbs/abb-appliance-aws-lambda-runtime.yaml |
| abb.hardware.amazon-ec2-standard | Amazon EC2 Standard Compute Platform | abb | abb, compute-platform | Standard Amazon EC2 virtual machine substrate used for general-purpose host patterns. | examples/catalog/abbs/abb-hardware-amazon-ec2-standard.yaml |
| abb.os.canonical-ubuntu-2204 | Ubuntu 22.04 LTS | abb | abb, operating-system | Canonical Ubuntu Server 22.04 LTS operating system product definition for Linux host patterns. | examples/catalog/abbs/abb-os-ubuntu-2204.yaml |
| abb.software.nginx-1-26 | nginx 1.26 | abb | abb, software | nginx web server software installed locally on a managed host and used without a required vendor platform interaction. | examples/catalog/abbs/abb-software-nginx-126.yaml |
| rbb.host.serverless.lambda | AWS Lambda Serverless Host | rbb | lambda, serverless | Serverless execution environment provided by AWS Lambda. The host is entirely AWS-managed and blackbox to the organiz... | examples/catalog/rbbs/rbb-host-serverless-lambda.yaml |

## Content Folder Counts

| Folder | YAML Count |
|---|---|
| framework/configurations/odcs | 11 |
| framework/configurations/compliance-frameworks | 5 |
| framework/configurations/compliance-profiles | 5 |
| framework/configurations/domains | 3 |
| examples/catalog/abbs | 5 |
| examples/catalog/rbbs | 1 |
| examples/catalog/reference-architectures | 0 |
| examples/catalog/sdms | 0 |
| examples/catalog/product-services | 0 |
| examples/catalog/saas-services | 0 |
| examples/catalog/ards | 0 |
| examples/catalog/sessions | 0 |

## Templates

| Path | Purpose |
|---|---|
| templates/abb.yaml.tmpl | Template for a standard Architecture Building Block. |
| templates/appliance-abb.yaml.tmpl | Template for an Appliance ABB. |
| templates/compliance-framework.yaml.tmpl | Template for a pure Compliance Framework control catalog. |
| templates/compliance-profile.yaml.tmpl | Template for a Compliance Profile that maps controls to DRAFT semantics. |
| templates/dbms-rbb.yaml.tmpl | Template for a Database Service RBB. |
| templates/deployment-risk-or-decision.yaml.tmpl | Template for a Deployment Risk or Decision. |
| templates/drafting-session.yaml.tmpl | Template for a Drafting Session that preserves incomplete authoring state. |
| templates/host-rbb.yaml.tmpl | Template for a Host RBB. |
| templates/object-patch.yaml.tmpl | Template for a configuration object patch. |
| templates/paas-service-rbb.yaml.tmpl | Template for a PaaS Service RBB. |
| templates/reference-architecture.yaml.tmpl | Template for a Reference Architecture. |
| templates/saas-service-rbb.yaml.tmpl | Template for a SaaS Service RBB. |
| templates/service-rbb.yaml.tmpl | Template for a general Service RBB. |
| templates/software-distribution-manifest.yaml.tmpl | Template for a Software Distribution Manifest. |
| templates/workspace/.draft/framework.lock.tmpl | Reusable YAML authoring template. |
| templates/workspace/.draft/workspace.yaml.tmpl | Reusable YAML authoring template. |
| templates/workspace/.gitignore.tmpl | Reusable YAML authoring template. |

## Validation

- Validate the example workspace: `python3 framework/tools/validate.py`
- Validate a company workspace: `python3 framework/tools/validate.py --workspace /path/to/workspace`
- Regenerate browser after YAML changes: `python3 framework/tools/generate_browser.py`
- Regenerate this index after framework or YAML changes: `python3 framework/tools/generate_ai_index.py`
