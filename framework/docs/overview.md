# Framework Overview

This page is the object map for the framework. It groups the catalog object
types by the role they play in the model.

If an AI assistant is using this repo directly to author content, start with
[Draftsman instructions](draftsman.md).

## Architecture Content

| Object Type | Purpose |
|---|---|
| Standard | The only reusable building-block architecture type in DRAFT. A Standard captures a reusable runtime or service pattern. |
| Reference Architecture | A deployment pattern defined in terms of required Standards, roles, and pattern-level decisions. It is the contract a Software Deployment Pattern may adopt to achieve supported non-functional outcomes such as availability, recoverability, and security posture. |
| Software Deployment Pattern | The top-level declaration of how a real product is distributed and deployed. It assembles deployed services, reusable building blocks, and deployment-scoped risks or decisions into one product view. |

## Standard Classifications

| Object Type | Purpose |
|---|---|
| Host | The runtime substrate on which reusable or product-specific services run. |
| General Service | A reusable non-database service pattern that runs on a host or equivalent managed substrate. |
| Database Service | A reusable data-platform service pattern with durability, recovery, and access-control capabilities. |
| PaaS Service | A vendor-managed platform service that runs inside the organization's cloud boundary. It is modeled as a Standard with `category: service` and `serviceCategory: paas`. |
| SaaS Service | A vendor-managed service classification used when traffic or data may leave the infrastructure boundary. It is modeled as a Standard with `category: service` and `serviceCategory: saas`. |
| Product Service | A first-party service classification used when a Software Deployment Pattern needs to express a distinct runtime-behavior component deployed on a Standard or blackbox host pattern. It is modeled as a Standard with `category: service` and `serviceCategory: product`. |

## Supporting Model Objects

| Object Type | Purpose |
|---|---|
| Technology Component | A discrete third-party product object used to compose Standards. Every Technology Component declares vendor, product name, product version, and exactly one Technology Component classification. Appliance Components remain a subtype of Technology Component, not a separate peer architecture content type. |
| Decision Record | A deployment-scoped record of a known risk, accepted decision, mitigation path, or follow-up attached to a Software Deployment Pattern or deployed service. |
| Drafting Session | A machine-readable work-in-progress session record that captures partial authoring state, generated objects, assumptions, and unresolved follow-up questions so the work can be resumed later. |

## Extensible Framework Content

| Object Type | Purpose |
|---|---|
| Capability | A first-class architecture capability such as authentication, log management, operating system, or patch management. Frameworks and providers define the vocabulary; company capability owners approve Technology Component implementations. |
| Requirement Group | The unified requirement model for DRAFT. Always-on groups define the required questions for object completeness. Workspace-mode groups represent explicitly activated compliance or company requirements. |
| Domain | A strategy grouping for related capabilities, used by the Draftsman to navigate from requirement to capability to approved implementation. |
