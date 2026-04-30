# YAML Schema Reference

This page is the quickest way to understand how to build a valid YAML object in
DRAFT.

The framework uses two sources of truth for YAML validation:

- `framework/schemas/` for the authoritative object contract of every
  first-class type
- `framework/tools/validate.py` for executable cross-reference, inheritance, and
  relationship checks

If an engineer wants to add a new object, start here, then open the referenced
schema file or object guide before writing YAML. The schema file is the
authoritative source for object shape.

## Object Families

| Object type | Folder | Schema source | Notes |
|---|---|---|---|
| Technology Component | `catalog/technology-components/` | [technology-component.schema.yaml](../schemas/technology-component.schema.yaml) | Technology Components are discrete third-party product objects with required `vendor`, `productName`, `productVersion`, and `classification`. Appliance Components also follow [appliance-component.schema.yaml](../schemas/appliance-component.schema.yaml). |
| Host Standard | `catalog/host-standards/` | [host-standard.schema.yaml](../schemas/host-standard.schema.yaml) | Runtime substrate that requires an operating system component and compute platform component unless it is a blackbox managed host. |
| Service Standard | `catalog/service-standards/` | [service-standard.schema.yaml](../schemas/service-standard.schema.yaml) | Reusable service pattern that combines a host standard with a primary technology component. |
| Database Standard | `catalog/database-standards/` | [database-standard.schema.yaml](../schemas/database-standard.schema.yaml) | Data-platform service pattern with durability, recovery, and access-control requirements. |
| Reference Architecture | `catalog/reference-architectures/` | [reference-architecture.schema.yaml](../schemas/reference-architecture.schema.yaml) | Reference Architecture validation is enforced in `framework/tools/validate.py` and `checklist.reference-architecture`. |
| Product Service | `catalog/product-services/` | [product-service.schema.yaml](../schemas/product-service.schema.yaml) | Product Services emerge in a Software Deployment Pattern rather than as starting-point Definition Checklist objects. |
| PaaS Service Standard | `catalog/paas-services/` | [paas-service-standard.schema.yaml](../schemas/paas-service-standard.schema.yaml) | Vendor-managed platform service inside the organization's cloud boundary. |
| Software Deployment Pattern | `catalog/software-deployment-patterns/` | [software-deployment-pattern.schema.yaml](../schemas/software-deployment-pattern.schema.yaml) | Includes `serviceGroups`, optional `scalingUnits`, and service-first topology metadata. |
| Drafting Session | `catalog/sessions/` | [drafting-session.schema.yaml](../schemas/drafting-session.schema.yaml) | Stores partial authoring state, generated objects, assumptions, and unresolved questions so work can be resumed later. |
| Decision Record | `catalog/decision-records/` | [decision-record.schema.yaml](../schemas/decision-record.schema.yaml) | First-class risk or decision object. |
| SaaS Service Standard | `catalog/saas-services/` | [saas-service-standard.schema.yaml](../schemas/saas-service-standard.schema.yaml) | Vendor-managed external service where traffic or data may leave the infrastructure boundary. |
| Definition Checklist | `configurations/definition-checklists/` | [definition-checklist.schema.yaml](../schemas/definition-checklist.schema.yaml) | Definition Checklists are framework-owned checklist objects. |
| Compliance Controls | `configurations/compliance-controls/` | [compliance-controls.schema.yaml](../schemas/compliance-controls.schema.yaml) | Pure control catalog with control identity only. |
| Control Enforcement Profile | `configurations/control-enforcement-profiles/` | [control-enforcement-profile.schema.yaml](../schemas/control-enforcement-profile.schema.yaml) | DRAFT semantics for a control catalog: applicability, valid answer types, and conditionality. |
| Object Patch | `configurations/object-patches/` | [object-patch.schema.yaml](../schemas/object-patch.schema.yaml) | Patch-style override object used to alter base framework objects without copying them. |

## Minimum Guidance By Type

### Technology Component

Use the Technology Component guide for the conceptual model. Appliance Components additionally follow
the dedicated appliance schema.

- Guide: [technology-components.md](technology-components.md)
- Appliance schema: [appliance-component.schema.yaml](../schemas/appliance-component.schema.yaml)

### Standard

- Guide: [standards.md](standards.md)
- Schema: [host-standard.schema.yaml](../schemas/host-standard.schema.yaml)

### Reference Architecture

Reference Architectures are validated against their structure and `checklist.reference-architecture`.

- Guide: [reference-architectures.md](reference-architectures.md)
- Validation rules: [`framework/tools/validate.py`](../tools/validate.py)

### Product Service

Product Services follow the Product Service schema file as a Standard
classification with product metadata. They do not have a dedicated Definition Checklist.

- Guide: [product-service.md](product-service.md)
- Schema: [product-service.schema.yaml](../schemas/product-service.schema.yaml)

### PaaS Service

- Guide: [paas-service-standards.md](paas-service-standards.md)
- Schema: [paas-service-standard.schema.yaml](../schemas/paas-service-standard.schema.yaml)

### Software Deployment Pattern

Software Deployment Patterns use the dedicated schema file and the Software Deployment Pattern guide.

- Guide: [software-deployment-patterns.md](software-deployment-patterns.md)
- Schema: [software-deployment-pattern.schema.yaml](../schemas/software-deployment-pattern.schema.yaml)

### Drafting Session

- Guide: [drafting-sessions.md](drafting-sessions.md)
- Schema: [drafting-session.schema.yaml](../schemas/drafting-session.schema.yaml)

### Decision Records

- Guide: [decision-records.md](decision-records.md)
- Schema: [decision-record.schema.yaml](../schemas/decision-record.schema.yaml)

### SaaS Service

- Guide: [saas-service-standards.md](saas-service-standards.md)
- Schema: [saas-service-standard.schema.yaml](../schemas/saas-service-standard.schema.yaml)

### Definition Checklist

- Guide: [definition-checklists.md](definition-checklists.md)
- Schema: [definition-checklist.schema.yaml](../schemas/definition-checklist.schema.yaml)

### Object Patch

Object patches target an existing object and deep-merge selected fields into the
effective model. They are the preferred mechanism for company overrides of base
framework objects.

- Schema: [object-patch.schema.yaml](../schemas/object-patch.schema.yaml)

### Compliance Controls

Compliance Controls are pure control catalogs. They carry metadata and a
`controls` list containing only control identity fields.

- Guide: [security-and-compliance-controls.md](security-and-compliance-controls.md)
- Schema: [compliance-controls.schema.yaml](../schemas/compliance-controls.schema.yaml)

### Control Enforcement Profile

Control Enforcement Profiles carry the DRAFT-specific semantics for a control catalog.
They define:

- where a control applies
- which answer mechanisms are valid
- whether a control is mandatory or conditional
- whether `N/A` is allowed and under what applicability rules

- Guide: [security-and-compliance-controls.md](security-and-compliance-controls.md)
- Schema: [control-enforcement-profile.schema.yaml](../schemas/control-enforcement-profile.schema.yaml)

### Object-Level Compliance Claims

Architecture artifacts use `controlEnforcementProfiles` to claim compliance with a
Control Enforcement Profile. Each declared profile requires matching `controlImplementations` for
every applicable control. A missing profile is an absence of a compliance claim,
not a failed control state.

## Practical Rule

If you are unsure how to build a YAML object correctly:

1. Open the relevant object guide in `framework/docs/`.
2. Open the matching file in `framework/schemas/` if one exists.
3. Run `python3 framework/tools/validate.py`.

The validator reads the schema files to enforce object shape, then applies the
higher-order relationship checks that schemas alone cannot express.
