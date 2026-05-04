# Framework Overview

This page is the high-level object map for DRAFT. For the complete object type
contract, see [DRAFT Object Types](object-types.md).

For a step-by-step company adoption path, see
[Company Onboarding Tutorial](company-onboarding.md).

If an AI assistant is using this repo directly to author content, start with
[Draftsman instructions](draftsman.md).

## Deployable Architecture

| Object Type | Purpose |
|---|---|
| Technology Component | A discrete vendor product, agent, operating system, compute platform, software package, or appliance product at a specific product/version level. |
| Host | An operational platform that combines an operating system, compute platform, and required host capabilities. |
| Runtime Service | Reusable runtime behavior such as web, app, cache, worker, messaging, or serverless runtime. |
| Data-at-Rest Service | Durable data behavior such as database, file, object, search, analytics, or storage. |
| Edge/Gateway Service | Boundary behavior such as WAF, firewall, API gateway, load balancer, ingress, proxy, or traffic inspection. |
| Product Service | A first-party custom binary or black-box service that runs on a selected deployable object. |
| Software Deployment Pattern | The intended assembly of deployable objects for a product or product capability. |

## Non-Deployable Architecture

| Object Type | Purpose |
|---|---|
| Capability | A first-class architecture capability such as authentication, log management, operating system, or patch management. Frameworks and providers define the vocabulary; company capability owners approve Technology Component implementations. |
| Requirement Group | The unified requirement model for DRAFT. Always-on groups define required questions for object completeness. Workspace-mode groups represent explicitly activated compliance or company requirements. |
| Domain | A strategy grouping for related capabilities, used by the Draftsman to navigate from requirement to capability to approved implementation. |
| Reference Architecture | A reusable deployment approach that Software Deployment Patterns may follow. |
| Decision Record | A record of a known risk, accepted decision, mitigation path, or follow-up attached to architecture content. |
| Drafting Session | A machine-readable work-in-progress record that captures partial authoring state, generated objects, assumptions, and unresolved follow-up questions. |
| Object Patch | A workspace overlay that changes selected fields on a framework-owned object without copying the full object. |

## Delivery Models

PaaS, SaaS, appliance, and self-managed describe how a Runtime Service,
Data-at-Rest Service, or Edge/Gateway Service is delivered. They are not
separate object types.
