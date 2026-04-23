# Framework Overview

This page is the object map for the framework. It groups the catalog object
types by the role they play in the model.

## Architecture Content

| Object Type | Purpose |
|---|---|
| RBB | The only reusable building-block architecture type in the framework. An RBB captures a reusable runtime or service pattern. |
| Reference Architecture | A reusable pattern defined in terms of required RBBs, roles, and expected deployment posture. It is the pattern-level contract that a Software Distribution Manifest may adopt or deviate from. |
| Software Distribution Manifest | The top-level declaration of how a real product is distributed and deployed. It assembles deployed services, reusable building blocks, and deployment-scoped risks or decisions into one product view. |

## RBB Classifications

| Object Type | Purpose |
|---|---|
| Host | The runtime substrate on which reusable or product-specific services run. |
| General Service | A reusable non-database service pattern that runs on a host or equivalent managed substrate. |
| Database Service | A reusable data-platform service pattern with durability, recovery, and access-control concerns. |
| SaaS Service | A vendor-managed service classification used when traffic or data may leave the infrastructure boundary. It is modeled as an RBB with `category: service` and `serviceCategory: saas`. |
| Product Service | A first-party service classification used when organization-authored code runs on an RBB or blackbox host pattern. It is modeled as an RBB with `category: service` and `serviceCategory: product`. |

## Supporting Model Objects

| Object Type | Purpose |
|---|---|
| ABB | The smallest vendor component in the catalog. ABBs are used to compose RBBs but are not peer architecture content types. This category also includes Appliance ABBs for blackbox vendor-managed components deployed inside the infrastructure boundary. |
| Deployment Risk / Decision | A deployment-scoped record of a known risk or accepted decision attached to an SDM or deployed service. The current machine-readable object type remains `ard`. |

## Extensible Framework Content

| Object Type | Purpose |
|---|---|
| ODCs | Structured checklists of required questions and answers used to define a complete and correct architecture object. They help build the object once the object taxonomy has been chosen. |
| Security and Compliance Controls | The selectable control catalogs and requirement-to-control mappings that sit beside the architecture model. They let the same ODC requirement set be viewed through different compliance frameworks without changing the architecture objects themselves. |
