# AI Framework Index

This generated file gives AI assistants a fast map of the DRAFT framework checkout.
It is intentionally framework-first: this upstream repository is a reusable template,
not a complete company architecture catalog. Organization-specific architecture content
belongs in downstream private clones.

Regenerate with:

```bash
python3 tools/generate_ai_index.py
```

## Draftsman Bootstrap

When a user says "I need a draftsman", the AI should immediately assume the
Draftsman role defined in `docs/framework/draftsman.md`, then use this index,
`schemas/`, and `odcs/` to guide the conversation and edits.

## Framework Entrypoints

| Path | Purpose |
|---|---|
| AGENTS.md | Canonical AI bootstrap instructions for this repository. |
| docs/framework/draftsman.md | Draftsman role, intent routing, and authoring rules. |
| docs/framework/overview.md | Framework concepts and object family overview. |
| docs/framework/yaml-schema-reference.md | Quick map from object families to schemas. |
| docs/framework/how-to-add-objects.md | Practical object authoring workflow. |
| docs/framework/odcs.md | Object Definition Checklist model and validation behavior. |
| docs/framework/drafting-sessions.md | How to persist incomplete authoring work. |
| tools/validate.py | Executable validation for schemas, ODCs, references, and controls. |

## Framework Docs

| Path | Title | Summary |
|---|---|---|
| docs/framework/abbs.md | ABBs | An Architecture Building Block, or ABB, is a discrete third-party product |
| docs/framework/deployment-risks-and-decisions.md | Deployment Risks And Decisions | Deployment Risks and Decisions are first-class records for known risks, |
| docs/framework/drafting-sessions.md | Drafting Sessions | A Drafting Session is a machine-readable record of partial architecture work. |
| docs/framework/draftsman.md | Draftsman Instructions | This document is written for an AI assistant that is using this repository as |
| docs/framework/how-to-add-objects.md | How To Add Objects | The fastest way to add a new object correctly is to decide what kind of thing you are modeling before you write YAML. |
| docs/framework/naming-conventions.md | Naming Conventions | The catalog relies on stable, predictable IDs because the IDs are the connective tissue between YAML objects, validat... |
| docs/framework/odcs.md | ODCs | An Object Definition Checklist, or ODC, is **a structured checklist of |
| docs/framework/overview.md | Framework Overview | This page is the object map for the framework. It groups the catalog object |
| docs/framework/paas-services.md | PaaS Services | A PaaS Service is a vendor-managed platform capability that stays inside the |
| docs/framework/product-service.md | Product Service | A Product Service is the RBB classification used to represent a first-party |
| docs/framework/rbbs.md | RBBs | An RBB, or Reference Building Block, is the framework's only reusable |
| docs/framework/reference-architectures.md | Reference Architectures | A Reference Architecture, or RA, is a deployment pattern. It tells application |
| docs/framework/saas-services.md | SaaS Services | A SaaS Service is a vendor-managed service that the adopting organization |
| docs/framework/security-and-compliance-controls.md | Security and Compliance Controls | DRAFT treats compliance as a pluggable layer rather than a fixed property of |
| docs/framework/software-distribution-manifests.md | Software Distribution Manifests | A Software Distribution Manifest, or SDM, is a declaration that a specific product is distributed and deployed accord... |
| docs/framework/yaml-schema-reference.md | YAML Schema Reference | This page is the quickest way to understand how to build a valid YAML object in |

## Schemas

| Path | Scope | Required Fields |
|---|---|---|
| schemas/abb-appliance.schema.yaml | abb.appliance | schemaVersion, id, type, name, vendor, productName, productVersion, classification, catalogStatus, lifecycleStatus |
| schemas/abb.schema.yaml | abb | schemaVersion, id, type, name, vendor, productName, productVersion, classification, catalogStatus, lifecycleStatus |
| schemas/ard.schema.yaml | ard | schemaVersion, id, type, name, category, status, description, affectedComponent, impact |
| schemas/compliance-framework.schema.yaml | compliance_framework | schemaVersion, id, type, name, frameworkKind, catalogStatus, lifecycleStatus |
| schemas/compliance-profile.schema.yaml | compliance_profile | schemaVersion, id, type, name, framework, catalogStatus, lifecycleStatus |
| schemas/domain.schema.yaml | domain | schemaVersion, id, type, name, capabilities |
| schemas/drafting-session.schema.yaml | drafting_session | schemaVersion, id, type, name, catalogStatus, lifecycleStatus, sessionStatus, primaryObjectType, sourceArtifacts, generatedObjects, unresolvedQuestions |
| schemas/odc.schema.yaml | odc | schemaVersion, id, type, name, description, requirements |
| schemas/paas-service.schema.yaml | rbb.service.paas | schemaVersion, id, type, category, serviceCategory, name, vendor, catalogStatus, lifecycleStatus |
| schemas/ps.schema.yaml | rbb.service.product | schemaVersion, id, type, category, serviceCategory, name, product, runsOn, catalogStatus, lifecycleStatus |
| schemas/rbb.schema.yaml | rbb | schemaVersion, id, type, name, catalogStatus, lifecycleStatus, category |
| schemas/reference-architecture.schema.yaml | reference_architecture | schemaVersion, id, type, name, catalogStatus, lifecycleStatus, serviceGroups |
| schemas/saas-service.schema.yaml | rbb.service.saas | schemaVersion, id, type, category, serviceCategory, name, vendor, catalogStatus, lifecycleStatus, dataLeavesInfrastructure |
| schemas/sdm.schema.yaml | software_distribution_manifest | schemaVersion, id, type, name, catalogStatus, lifecycleStatus |

## Object Definition Checklists

| ID | Name | Type | Tags | Description | Path |
|---|---|---|---|---|---|
| odc.appliance-abb | Appliance ABB Object Definition Checklist | odc | appliance, checklist, definition | Structured checklist of required questions and answers used to define a complete and correct Appliance ABB. An Applia... | odcs/odc-appliance-abb.yaml |
| odc.paas-service | PaaS Service Object Definition Checklist | odc | paas, checklist, definition | Structured checklist of required questions and answers used to define a complete and correct PaaS Service. A PaaS Ser... | odcs/odc-paas-service.yaml |
| odc.saas-service | SaaS Service Object Definition Checklist | odc | saas, checklist, definition | Structured checklist of required questions and answers used to define a complete and correct SaaS Service. A SaaS Ser... | odcs/odc-saas-service.yaml |
| odc.compliance-framework | Compliance Framework ODC | odc | odc, compliance | Structured checklist for defining a pure control catalog in DRAFT. This ODC is focused on the control facts themselve... | odcs/odc.compliance-framework.yaml |
| odc.compliance-profile | Compliance Profile ODC | odc | odc, compliance, profile | Structured checklist for defining how a pure control catalog is applied in DRAFT. This ODC captures DRAFT-specific se... | odcs/odc.compliance-profile.yaml |
| odc.drafting-session | Drafting Session Object Definition Checklist | odc | drafting-session, checklist, intake | Structured checklist used to capture partial architecture-authoring sessions, generated outputs, and unresolved follo... | odcs/odc.drafting-session.yaml |
| odc.host | Host Object Definition Checklist | odc | host, checklist, definition | Structured checklist of required questions and answers used to define a complete and correct host RBB. | odcs/odc.host.yaml |
| odc.ra | Reference Architecture Object Definition Checklist | odc | ra, checklist, definition | Structured checklist of required questions and answers used to define a complete and correct Reference Architecture. | odcs/odc.ra.yaml |
| odc.sdm | Software Distribution Manifest Object Definition Checklist | odc | sdm, checklist, definition | Structured checklist of required questions and answers used to define a complete and correct software distribution ma... | odcs/odc.sdm.yaml |
| odc.service.dbms | DBMS Service Object Definition Checklist | odc | service, dbms, checklist, definition | Additional DBMS service checklist items extending the generic service ODC for data durability, protection, and control. | odcs/odc.service.dbms.yaml |
| odc.service | General Service Object Definition Checklist | odc | service, checklist, definition | Structured checklist of required questions and answers used to define a complete and correct general service RBB. | odcs/odc.service.yaml |

## Current YAML Inventory

These are the YAML objects present in this checkout. In the upstream framework repo, this inventory is framework seed material, not a company-specific architecture catalog.

| ID | Name | Type | Tags | Description | Path |
|---|---|---|---|---|---|
| abb.agent.crowdstrike-falcon | CrowdStrike Falcon Agent | abb | abb, agent | Endpoint security agent installed locally on a host that requires communication with the CrowdStrike Falcon platform. | abbs/abb-agent-crowdstrike-falcon.yaml |
| abb.appliance.aws-lambda-runtime | AWS Lambda Runtime | abb | appliance, lambda | AWS Lambda serverless execution environment. Runs organization-authored function code without requiring host manageme... | abbs/abb-appliance-aws-lambda-runtime.yaml |
| abb.hardware.amazon-ec2-standard | Amazon EC2 Standard Compute Platform | abb | abb, compute-platform | Standard Amazon EC2 virtual machine substrate used for general-purpose host patterns. | abbs/abb-hardware-amazon-ec2-standard.yaml |
| abb.os.canonical-ubuntu-2204 | Ubuntu 22.04 LTS | abb | abb, operating-system | Canonical Ubuntu Server 22.04 LTS operating system product definition for Linux host patterns. | abbs/abb-os-ubuntu-2204.yaml |
| abb.software.nginx-1-26 | nginx 1.26 | abb | abb, software | nginx web server software installed locally on a managed host and used without a required vendor platform interaction. | abbs/abb-software-nginx-126.yaml |
| rbb.host.serverless.lambda | AWS Lambda Serverless Host | rbb | lambda, serverless | Serverless execution environment provided by AWS Lambda. The host is entirely AWS-managed and blackbox to the organiz... | rbbs/rbb-host-serverless-lambda.yaml |
| framework.nist-csf | NIST Cybersecurity Framework | compliance_framework | compliance, nist, starter-pack | Initial NIST Cybersecurity Framework (CSF) 2.0 control pack scoped to the outcomes that can be meaningfully answered... | compliance-frameworks/framework-nist-csf.yaml |
| framework.organization-controls | Organization Controls Overlay | compliance_framework | compliance, organizational, extensibility | Template framework for organization-specific controls. Clone this file, rename the id and name, and populate controls... | compliance-frameworks/framework-organization-controls.yaml |
| framework.security-compliance-controls | Security and Compliance Controls | compliance_framework | compliance, controls, baseline | Baseline controls pack bundled with DRAFT. Required controls are defined inline and are applied to matching ODCs at r... | compliance-frameworks/framework-security-compliance-controls.yaml |
| framework.soc2 | SOC 2 | compliance_framework | compliance, soc2, starter-pack | Initial SOC 2 control pack based on the AICPA Trust Services Criteria. These controls use DRAFT applicability metadat... | compliance-frameworks/framework-soc2.yaml |
| framework.tx-ramp | TX-RAMP | compliance_framework | compliance, tx-ramp, starter-pack | Starter TX-RAMP control pack for DRAFT. This file is intended to map TX-RAMP control expectations onto the existing D... | compliance-frameworks/framework-tx-ramp.yaml |
| profile.nist-csf | NIST Cybersecurity Framework Profile | compliance_profile | compliance, nist, starter-pack, profile | DRAFT implementation profile for NIST Cybersecurity Framework. | compliance-profiles/profile-nist-csf.yaml |
| profile.organization-controls | Organization Controls Overlay Profile | compliance_profile | compliance, organizational, extensibility, profile | DRAFT implementation profile for Organization Controls Overlay. | compliance-profiles/profile-organization-controls.yaml |
| profile.security-compliance-controls | Security and Compliance Controls Profile | compliance_profile | compliance, controls, baseline, profile | DRAFT implementation profile for Security and Compliance Controls. | compliance-profiles/profile-security-compliance-controls.yaml |
| profile.soc2 | SOC 2 Profile | compliance_profile | compliance, soc2, starter-pack, profile | DRAFT implementation profile for SOC 2. | compliance-profiles/profile-soc2.yaml |
| profile.tx-ramp | TX-RAMP Profile | compliance_profile | compliance, tx-ramp, starter-pack, profile | DRAFT implementation profile for TX-RAMP. | compliance-profiles/profile-tx-ramp.yaml |

## Content Folder Counts

| Folder | YAML Count |
|---|---|
| abbs | 5 |
| rbbs | 1 |
| reference-architectures | 0 |
| sdms | 0 |
| product-services | 0 |
| saas-services | 0 |
| ards | 0 |
| compliance-frameworks | 5 |
| compliance-profiles | 5 |
| sessions | 0 |

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
| templates/paas-service-rbb.yaml.tmpl | Template for a PaaS Service RBB. |
| templates/reference-architecture.yaml.tmpl | Template for a Reference Architecture. |
| templates/saas-service-rbb.yaml.tmpl | Template for a SaaS Service RBB. |
| templates/service-rbb.yaml.tmpl | Template for a general Service RBB. |
| templates/software-distribution-manifest.yaml.tmpl | Template for a Software Distribution Manifest. |

## Validation

- Validate catalog objects: `python3 tools/validate.py`
- Regenerate browser after YAML changes: `python3 tools/generate_browser.py`
- Regenerate this index after framework or YAML changes: `python3 tools/generate_ai_index.py`
