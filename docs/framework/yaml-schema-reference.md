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
| ABB | `abbs/` | [abb.schema.yaml](../../schemas/abb.schema.yaml) | ABBs are discrete third-party product objects with required `vendor`, `productName`, `productVersion`, and `classification`. Appliance ABBs also follow [abb-appliance.schema.yaml](../../schemas/abb-appliance.schema.yaml). |
| RBB | `rbbs/` | [rbb.schema.yaml](../../schemas/rbb.schema.yaml) | RBB is the reusable building-block type. The schema defines the shared contract, including optional `deploymentConfigurations`; the validator applies relationship checks. |
| Reference Architecture | `reference-architectures/` | [reference-architecture.schema.yaml](../../schemas/reference-architecture.schema.yaml) | RA validation is enforced in `tools/validate.py` and `odc.ra`. |
| Product Service | `rbbs/` | [ps.schema.yaml](../../schemas/ps.schema.yaml) | Product Services are RBBs with `category: service` and `serviceCategory: product`. They emerge in an SDM rather than as starting-point ODC objects. |
| Software Distribution Manifest | `sdms/` | [sdm.schema.yaml](../../schemas/sdm.schema.yaml) | Includes `serviceGroups`, optional `scalingUnits`, and service-first topology metadata. |
| Drafting Session | `sessions/` | [drafting-session.schema.yaml](../../schemas/drafting-session.schema.yaml) | Stores partial authoring state, generated objects, assumptions, and unresolved questions so work can be resumed later. |
| Deployment Risk or Decision | `ards/` | [ard.schema.yaml](../../schemas/ard.schema.yaml) | Object type remains `ard`. |
| SaaS Service | `rbbs/` | [saas-service.schema.yaml](../../schemas/saas-service.schema.yaml) | SaaS Services are RBBs with `category: service` and `serviceCategory: saas`. |
| ODC | `odcs/` | [odc.schema.yaml](../../schemas/odc.schema.yaml) | ODCs are checklist objects. Their shape is enforced by schema and their satisfaction logic by the validator. |
| Compliance Framework | `compliance-frameworks/` | [compliance-framework.schema.yaml](../../schemas/compliance-framework.schema.yaml) | Pure control catalog with control identity only. |
| Compliance Profile | `compliance-profiles/` | [compliance-profile.schema.yaml](../../schemas/compliance-profile.schema.yaml) | DRAFT semantics for a control catalog: applicability, valid answer types, and conditionality. |

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
classification with product metadata. They do not have a dedicated ODC.

- Guide: [product-service.md](product-service.md)
- Schema: [ps.schema.yaml](../../schemas/ps.schema.yaml)

### Software Distribution Manifest

SDMs use the dedicated schema file and the SDM guide.

- Guide: [software-distribution-manifests.md](software-distribution-manifests.md)
- Schema: [sdm.schema.yaml](../../schemas/sdm.schema.yaml)

### Drafting Session

- Guide: [drafting-sessions.md](drafting-sessions.md)
- Schema: [drafting-session.schema.yaml](../../schemas/drafting-session.schema.yaml)

### Deployment Risks and Decisions

- Schema: [ard.schema.yaml](../../schemas/ard.schema.yaml)

### SaaS Service

- Guide: [saas-services.md](saas-services.md)
- Schema: [saas-service.schema.yaml](../../schemas/saas-service.schema.yaml)

### ODC

- Guide: [odcs.md](odcs.md)
- Schema: [odc.schema.yaml](../../schemas/odc.schema.yaml)

### Compliance Framework

Compliance frameworks are pure control catalogs. They carry metadata and a
`controls` list containing only control identity fields.

- Guide: [security-and-compliance-controls.md](security-and-compliance-controls.md)
- Schema: [compliance-framework.schema.yaml](../../schemas/compliance-framework.schema.yaml)

### Compliance Profile

Compliance profiles carry the DRAFT-specific semantics for a control catalog.
They define:

- where a control applies
- which answer mechanisms are valid
- whether a control is mandatory or conditional
- whether `N/A` is allowed and under what applicability rules

- Guide: [security-and-compliance-controls.md](security-and-compliance-controls.md)
- Schema: [compliance-profile.schema.yaml](../../schemas/compliance-profile.schema.yaml)

## Practical Rule

If you are unsure how to build a YAML object correctly:

1. Open the relevant object guide in `docs/framework/`.
2. Open the matching file in `schemas/` if one exists.
3. Run `python3 tools/validate.py`.

The validator reads the schema files to enforce object shape, then applies the
higher-order relationship checks that schemas alone cannot express.
