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
| ABB | `abbs/` | [abb.schema.yaml](../../schemas/abb.schema.yaml) | ABBs use typed IDs such as `abb.os.*`, `abb.software.*`, and `abb.agent.*`. Appliance ABBs also follow [abb-appliance.schema.yaml](../../schemas/abb-appliance.schema.yaml). |
| RBB | `rbbs/` | [rbb.schema.yaml](../../schemas/rbb.schema.yaml) | RBB is the reusable building-block type. The schema defines the shared contract; the validator applies relationship checks. |
| Reference Architecture | `reference-architectures/` | [reference-architecture.schema.yaml](../../schemas/reference-architecture.schema.yaml) | RA validation is enforced in `tools/validate.py` and `odc.ra`. |
| Product Service | `rbbs/` | [ps.schema.yaml](../../schemas/ps.schema.yaml) | Product Services are RBBs with `category: service` and `serviceCategory: product`. |
| Software Distribution Manifest | `sdms/` | [sdm.schema.yaml](../../schemas/sdm.schema.yaml) | Includes `serviceGroups`, optional `scalingUnits`, and service-first topology metadata. |
| Deployment Risk or Decision | `ards/` | [ard.schema.yaml](../../schemas/ard.schema.yaml) | Object type remains `ard`. |
| SaaS Service | `rbbs/` | [saas-service.schema.yaml](../../schemas/saas-service.schema.yaml) | SaaS Services are RBBs with `category: service` and `serviceCategory: saas`. |
| ODC | `odcs/` | [odc.schema.yaml](../../schemas/odc.schema.yaml) | ODCs are checklist objects. Their shape is enforced by schema and their satisfaction logic by the validator. |
| Compliance Framework | `compliance-frameworks/` | [compliance-framework.schema.yaml](../../schemas/compliance-framework.schema.yaml) | Requirement-to-control mappings live inline in `requirementMappings`. |

## Minimum Guidance By Type

### ABB

Use the ABB guide for the conceptual model. Appliance ABBs additionally follow
the dedicated appliance schema.

- Guide: [abbs.md](abbs.md)
- Appliance schema: [abb-appliance.schema.yaml](../../schemas/abb-appliance.schema.yaml)

### RBB

- Guide: [rbbs.md](rbbs.md)
- Schema: [rbb.schema.yaml](../../schemas/rbb.schema.yaml)

### Reference Architecture

Reference Architectures are validated against their structure and `odc.ra`.

- Guide: [reference-architectures.md](reference-architectures.md)
- Validation rules: [`tools/validate.py`](../../tools/validate.py)

### Product Service

Product Services follow the Product Service schema file as an RBB
classification with product metadata.

- Guide: [product-service.md](product-service.md)
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

### ODC

- Guide: [odcs.md](odcs.md)
- Schema: [odc.schema.yaml](../../schemas/odc.schema.yaml)

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
