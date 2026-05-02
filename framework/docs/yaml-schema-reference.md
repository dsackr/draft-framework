# YAML Schema Reference

This page is the quickest way to understand how to build a valid YAML object in
DRAFT.

The framework uses two sources of truth for YAML validation:

- `framework/schemas/` for the authoritative object contract of every
  first-class type
- `framework/tools/validate.py` for executable relationship, capability, and
  Requirement Group checks

## Object Families

| Object type | Folder | Schema source | Notes |
|---|---|---|---|
| Technology Component | `catalog/technology-components/` | [technology-component.schema.yaml](../schemas/technology-component.schema.yaml) | Discrete vendor product with vendor facts and capability references. Company adoption lives on capability implementation mappings, not top-level lifecycle status. |
| Appliance Component | `catalog/appliance-components/` | [appliance-component.schema.yaml](../schemas/appliance-component.schema.yaml) | Vendor product that behaves like a service but has no modeled host, so it answers service-like requirements directly. |
| Host Standard | `catalog/host-standards/` | [host-standard.schema.yaml](../schemas/host-standard.schema.yaml) | Runtime substrate built from an operating system and compute platform. |
| Service Standard | `catalog/service-standards/` | [service-standard.schema.yaml](../schemas/service-standard.schema.yaml) | Reusable service pattern built from a host and primary Technology Component. |
| Database Standard | `catalog/database-standards/` | [database-standard.schema.yaml](../schemas/database-standard.schema.yaml) | Data-platform service pattern with durability, recovery, and access-control requirements. |
| Reference Architecture | `catalog/reference-architectures/` | [reference-architecture.schema.yaml](../schemas/reference-architecture.schema.yaml) | Reusable deployment pattern that Software Deployment Patterns can follow. |
| Software Deployment Pattern | `catalog/software-deployment-patterns/` | [software-deployment-pattern.schema.yaml](../schemas/software-deployment-pattern.schema.yaml) | Intended product deployment architecture with service groups and topology metadata. |
| Product Service | `catalog/product-services/` | [product-service.schema.yaml](../schemas/product-service.schema.yaml) | Product-specific runtime behavior used inside a Software Deployment Pattern. |
| PaaS Service Standard | `catalog/paas-services/` | [paas-service-standard.schema.yaml](../schemas/paas-service-standard.schema.yaml) | Vendor-managed platform service inside the cloud boundary. |
| SaaS Service Standard | `catalog/saas-services/` | [saas-service-standard.schema.yaml](../schemas/saas-service-standard.schema.yaml) | Vendor-managed external service where data or traffic may leave the infrastructure boundary. |
| Decision Record | `catalog/decision-records/` | [decision-record.schema.yaml](../schemas/decision-record.schema.yaml) | Risk, decision, mitigation, or follow-up record. |
| Drafting Session | `catalog/sessions/` | [drafting-session.schema.yaml](../schemas/drafting-session.schema.yaml) | Incomplete authoring state, generated objects, assumptions, and unresolved questions. |
| Capability | `configurations/capabilities/` | [capability.schema.yaml](../schemas/capability.schema.yaml) | First-class capability with a definition owner, optional company owner, and company-approved Technology Component implementations. |
| Requirement Group | `configurations/requirement-groups/` | [requirement-group.schema.yaml](../schemas/requirement-group.schema.yaml) | Unified authoring and validation requirements, including always-on definition requirements and workspace-activated compliance requirements. |
| Domain | `configurations/domains/` | [domain.schema.yaml](../schemas/domain.schema.yaml) | Groups capability IDs for strategy navigation. |
| Object Patch | `configurations/object-patches/` | [object-patch.schema.yaml](../schemas/object-patch.schema.yaml) | Workspace overlay that deep-merges selected fields into a base framework object. |

## Requirement And Capability Flow

When a requirement names `relatedCapability`, resolve:

1. Requirement Group requirement
2. `relatedCapability`
3. capability object
4. company capability `owner`
5. capability `implementations`
6. recommended Technology Component or configuration

Workspace-mode Requirement Groups are activated in `.draft/workspace.yaml` under
`requirements.activeRequirementGroups`.

## Practical Rule

If you are unsure how to build a YAML object correctly:

1. Open the relevant guide in `framework/docs/`.
2. Open the matching file in `framework/schemas/`.
3. Resolve applicable Requirement Groups and capabilities.
4. Run `python3 framework/tools/validate.py`.
