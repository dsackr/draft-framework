# YAML Schema Reference

This page is the quickest way to understand how to build a valid YAML object in
DRAFT.

The framework uses two sources of truth for YAML validation:

- `schemas/` for the authoritative object contract of every first-class type
- `tools/validate.py` for executable cross-reference, inheritance, and
  relationship checks

If an engineer wants to add a new object, start here, then open the referenced
schema file or object guide before writing YAML. The schema file is the
authoritative source for object shape.

## Object Families

| Object type | Folder | Schema source | Notes |
|---|---|---|---|
| ABB | `abbs/` | object guide + validator | ABBs use typed IDs such as `abb.os.*`, `abb.software.*`, and `abb.agent.*`. Appliance ABBs also follow [abb-appliance.schema.yaml](../../schemas/abb-appliance.schema.yaml). |
| RBB | `rbbs/` | object guide + validator | RBB rules are enforced in `tools/validate.py`. Host and service RBBs have different required relationships. |
| Reference Architecture | `reference-architectures/` | object guide + validator | RA validation is enforced in `tools/validate.py` and `aag.ra`. |
| Software Service | `product-services/` | [ps.schema.yaml](../../schemas/ps.schema.yaml) | Framework term is Software Service; object type remains `product_service`. |
| Software Distribution Manifest | `sdms/` | [sdm.schema.yaml](../../schemas/sdm.schema.yaml) | Includes `serviceGroups`, optional `scalingUnits`, and service-first topology metadata. |
| Deployment Risk or Decision | `ards/` | [ard.schema.yaml](../../schemas/ard.schema.yaml) | Object type remains `ard`. |
| SaaS Service | `saas-services/` | [saas-service.schema.yaml](../../schemas/saas-service.schema.yaml) | Use when vendor-managed traffic or data leaves the infrastructure boundary. |
| AAG | `aags/` | object guide + validator | AAGs are rule objects. Their shape is validated in `tools/validate.py`. |
| Compliance Framework | `compliance-frameworks/` | [compliance-framework.schema.yaml](../../schemas/compliance-framework.schema.yaml) | Requirement-to-control mappings live inline in `requirementMappings`. |

## Minimum Guidance By Type

### ABB

Use the ABB guide for the conceptual model and the validator for exact field
expectations. Appliance ABBs additionally follow the dedicated appliance schema.

- Guide: [abbs.md](abbs.md)
- Appliance schema: [abb-appliance.schema.yaml](../../schemas/abb-appliance.schema.yaml)

### RBB

RBBs do not currently have a separate schema file. The executable contract
lives in the validator and in the object guide.

- Guide: [rbbs.md](rbbs.md)
- Validation rules: [`tools/validate.py`](../../tools/validate.py)

### Reference Architecture

Reference Architectures are validated against their structure and `aag.ra`.

- Guide: [reference-architectures.md](reference-architectures.md)
- Validation rules: [`tools/validate.py`](../../tools/validate.py)

### Software Service

Software Services follow the Product Service schema file, because the
underlying object type remains `product_service`.

- Guide: [product-services.md](product-services.md)
- Schema: [ps.schema.yaml](../../schemas/ps.schema.yaml)

### Software Distribution Manifest

SDMs use the dedicated schema file and the SDM guide.

- Guide: [software-distribution-manifests.md](software-distribution-manifests.md)
- Schema: [sdm.schema.yaml](../../schemas/sdm.schema.yaml)

### Deployment Risks and Decisions

- Schema: [ard.schema.yaml](../../schemas/ard.schema.yaml)

### SaaS Service

- Guide: [saas-services.md](saas-services.md)
- Schema: [saas-service.schema.yaml](../../schemas/saas-service.schema.yaml)

### AAG

AAGs are defined by the validator and the AAG guide.

- Guide: [aags.md](aags.md)
- Validation rules: [`tools/validate.py`](../../tools/validate.py)

### Compliance Framework

Compliance frameworks are single-file objects. They carry both metadata and
inline `requirementMappings`.

- Guide: [security-and-compliance-controls.md](security-and-compliance-controls.md)
- Schema: [compliance-framework.schema.yaml](../../schemas/compliance-framework.schema.yaml)

## Practical Rule

If you are unsure how to build a YAML object correctly:

1. Open the relevant object guide in `docs/framework/`.
2. Open the matching file in `schemas/` if one exists.
3. Run `python3 tools/validate.py`.

The validator reads the schema files to enforce object shape, then applies the
higher-order relationship checks that schemas alone cannot express.
