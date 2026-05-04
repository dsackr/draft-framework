# DRAFT Object Types

## Purpose

DRAFT object types are split into deployable architecture and non-deployable
framework content. Deployable objects describe architecture that can eventually
become automation inputs. Non-deployable objects guide, govern, remember, or
explain how deployable architecture is drafted.

PaaS, SaaS, appliance, and self-managed are delivery models. They are not
separate object types.

## Deployable Architecture Objects

| Object type | YAML `type` | What it represents | Deployable role |
|---|---|---|---|
| Technology Component | `technology_component` | A discrete vendor product, agent, operating system, compute platform, software package, or appliance product at a specific product/version level. | Deployed as an ingredient inside Hosts and service objects. |
| Host | `host` | An operational platform that combines an operating system, compute platform, and required host capabilities such as authentication, logging, monitoring, and patching. | Deploys the runtime substrate for self-managed services. |
| Runtime Service | `runtime_service` | Reusable runtime behavior such as web, app, cache, worker, messaging, or serverless runtime. | Deploys runtime behavior on a Host or through PaaS, SaaS, or appliance delivery. |
| Data-at-Rest Service | `data_at_rest_service` | Durable data behavior such as database, file, object, search, analytics, or storage. | Deploys persistence behavior on a Host or through PaaS, SaaS, or appliance delivery. |
| Edge/Gateway Service | `edge_gateway_service` | Boundary behavior such as WAF, firewall, API gateway, load balancer, ingress, proxy, or traffic inspection. | Deploys traffic control behavior at a product or network boundary. |
| Product Service | `product_service` | A first-party custom binary or black-box service that runs on a selected deployable object. | Deploys company-authored application behavior. |
| Software Deployment Pattern | `software_deployment_pattern` | The intended assembly of deployable objects for a product or product capability. | Defines the deployable package shape that automation can target. |

## Non-Deployable Architecture Objects

| Object type | YAML `type` | What it does |
|---|---|---|
| Capability | `capability` | Names an ability required by architecture and records company-approved Technology Components for satisfying that ability. |
| Requirement Group | `requirement_group` | Groups requirements used by the Draftsman during interviews and by validation after authoring. |
| Domain | `domain` | Groups capabilities into a planning area such as compute, observability, identity, or data. |
| Reference Architecture | `reference_architecture` | Documents a reusable deployment approach that Software Deployment Patterns may follow. |
| Decision Record | `decision_record` | Records an architecture decision, risk, exception, or rationale. |
| Drafting Session | `drafting_session` | Stores interview memory, source material, assumptions, unresolved questions, and generated work while drafting. |
| Object Patch | `object_patch` | A workspace overlay that changes selected fields on a framework-owned object without copying the full object. |

## Delivery Models

`runtime_service`, `data_at_rest_service`, and `edge_gateway_service` include a
`deliveryModel` field:

- `self-managed` means the company operates the service on a Host.
- `paas` means a provider-managed platform delivers the service inside the
  company's cloud or infrastructure boundary.
- `saas` means a vendor-managed service may operate outside the company's
  infrastructure boundary.
- `appliance` means the service maps directly to a vendor appliance or
  appliance-like product and must carry service-like operating capability
  answers because there is no Host wrapper.

## Draftsman Rule

When drafting deployable architecture, the Draftsman must choose the object type
from the behavior being modeled first, then choose the delivery model.

For example:

- Amazon RDS PostgreSQL is a Data-at-Rest Service with `deliveryModel: paas`.
- Snowflake is a Data-at-Rest Service with `deliveryModel: saas`.
- F5 BIG-IP WAF is an Edge/Gateway Service with `deliveryModel: appliance`.
- A company-owned Java API is a Product Service that runs on a Runtime Service
  or Host.
