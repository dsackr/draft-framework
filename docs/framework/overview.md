# Framework Overview

This page is the object map for the framework. It groups the catalog object
types by the role they play in the model.

If an AI assistant is using this repo directly to author content, start with
[Draftsman instructions](draftsman.md).

## Architecture Content

| Object Type | Purpose |
|---|---|
| RBB | The only reusable building-block architecture type in the framework. An RBB captures a reusable runtime or service pattern. |
| Reference Architecture | A deployment pattern defined in terms of required RBBs, roles, and pattern-level decisions. It is the contract an SDM may adopt to achieve supported non-functional outcomes such as availability, recoverability, and security posture. |
| Software Distribution Manifest | The top-level declaration of how a real product is distributed and deployed. It assembles deployed services, reusable building blocks, and deployment-scoped risks or decisions into one product view. |

## RBB Classifications

| Object Type | Purpose |
|---|---|
| Host | The runtime substrate on which reusable or product-specific services run. |
| General Service | A reusable non-database service pattern that runs on a host or equivalent managed substrate. |
| Database Service | A reusable data-platform service pattern with durability, recovery, and access-control concerns. |
| PaaS Service | A vendor-managed platform service that runs inside the organization's cloud boundary. It is modeled as an RBB with `category: service` and `serviceCategory: paas`. |
| SaaS Service | A vendor-managed service classification used when traffic or data may leave the infrastructure boundary. It is modeled as an RBB with `category: service` and `serviceCategory: saas`. |
| Product Service | A first-party service classification used when an SDM needs to express a distinct runtime-behavior component deployed on an RBB or blackbox host pattern. It is modeled as an RBB with `category: service` and `serviceCategory: product`. |

## Supporting Model Objects

| Object Type | Purpose |
|---|---|
| ABB | A discrete third-party product object used to compose RBBs. Every ABB declares vendor, product name, product version, and exactly one ABB classification. Appliance ABBs remain a subtype of ABB, not a separate peer architecture content type. |
| Deployment Risk / Decision | A deployment-scoped record of a known risk or accepted decision attached to an SDM or deployed service. The current machine-readable object type remains `ard`. |
| Drafting Session | A machine-readable work-in-progress session record that captures partial authoring state, generated objects, assumptions, and unresolved follow-up questions so the work can be resumed later. |

## Extensible Framework Content

| Object Type | Purpose |
|---|---|
| ODCs | Structured checklists of required questions and answers used to define a complete and correct architecture object. They are written to work as human or AI interview checklists once the object taxonomy has been chosen. |
| Security and Compliance Controls | The selectable control catalogs that sit beside the architecture model. They let the same ODC concern set be extended with framework-specific required controls without changing the architecture objects themselves. Compliance frameworks are themselves governed by `odc.compliance-framework`. |
