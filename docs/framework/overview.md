# Framework Overview

This page is the object map for the framework. It groups the catalog object
types by the role they play in the model.

## Architecture Content

### ABB

An ABB is the smallest reusable vendor component in the catalog. ABBs define
what a technology is, not how a full architecture pattern is assembled from it.
This category also includes Appliance ABBs, which model blackbox
vendor-managed components deployed inside the infrastructure boundary.

### RBB

An RBB is a reusable architecture pattern built from ABBs. Host RBBs describe
the runtime foundation. Service RBBs describe a reusable service pattern that
runs on that foundation.

### Reference Architecture

A Reference Architecture defines a reusable pattern in terms of required RBBs,
roles, and expected deployment posture. It is the pattern-level contract that a
Software Distribution Manifest may adopt or deviate from.

## Software Content

### Software Service

A Software Service is first-party code deployed on an RBB or an equivalent
blackbox host pattern. The underlying documentation and file path still use
`product-services`, but the framework meaning is software content authored by
the adopting organization.

### Software Distribution Manifest

A Software Distribution Manifest describes how a real product is distributed and
deployed. It assembles Software Services, RBBs, Appliance ABBs, SaaS Services,
scaling units, service groups, and explicit external interactions into one
deployable view.

### Deployment Risks and Decisions

Deployment Risks and Decisions capture explicit architectural risk and decision
records attached to deployed software. The underlying object type remains `ard`,
but the framework meaning is a deployment-scoped record of either a known risk
or an accepted decision.

## Extensible Framework Content

### AAGs

AAGs define the requirement sets that catalog objects must satisfy before they
can be considered complete enough for approval. They are the framework’s
analysis and governance layer.

### Security and Compliance Controls

Security and Compliance Controls are the selectable control catalogs and
requirement-to-control mappings that sit beside the architecture model. They
let the same AAG requirement set be viewed through different compliance
frameworks without changing the architecture objects themselves.
