# Product Service

## What A Product Service Is

A Product Service represents a first-party custom binary or black-box component
that a Software Deployment Pattern deploys on a selected deployable object.

The boundary is not based on how complex the component is or whether another
product reuses it. The boundary is whether the Software Deployment Pattern needs
to communicate a distinct first-party deployable unit with its own runtime
behavior.

## The Locked Definition

**Product Service = first-party deployable runtime behavior expressed through a
Software Deployment Pattern on top of a Host, Runtime Service, Data-at-Rest
Service, Edge/Gateway Service, or equivalent deployable object.**

An IIS runtime is a Runtime Service. A product-specific API, worker, or
scheduler deployed on that runtime may be a Product Service. An AWS Lambda
serverless runtime is a Runtime Service with `deliveryModel: paas`. A specific
function package deployed to that runtime may be a Product Service.

## YAML Shape

Product Services use
[product-service.schema.yaml](../schemas/product-service.schema.yaml).

At minimum, a Product Service YAML should include:

- `schemaVersion`
- `uid`
- `type: product_service`
- `name`
- `product`
- `runsOn`
- `catalogStatus`
- `lifecycleStatus`

Most Product Services also include `description`, `internalProcesses`,
`apiEndpoints`, `internalComponents`, `externalInteractions`, or
`deploymentConfigurations` when the first-party service has meaningful internal
architecture to document. `architecturalDecisions` is used when the Software
Deployment Pattern, an attached Requirement Group, or a modeled dependency needs
an answer that is not otherwise expressed directly in the YAML.

## What A Product Service Documents

A Product Service captures:

- the owning product
- the deployable object it runs on via `runsOn`
- lifecycle and catalog status
- named first-party processes via `internalProcesses`
- exposed API or protocol surfaces via `apiEndpoints`
- consumed Technology Components or deployable objects via `internalComponents`
- outbound or external platform calls via `externalInteractions`
- meaningful deployment variants via `deploymentConfigurations`
- descriptive notes about the component's purpose
- any architectural decision entries needed to explain required answers or
  non-obvious additions

DRAFT does not require enumeration of every internal package, library, or
repository that contributes code to the component. The framework only needs to
know the first-party deployable boundary, the important process/API surfaces,
and any dependencies that are architecturally relevant.

## Internal Process And API Modeling

Use `internalProcesses` for named runtime units inside the Product Service, such
as an API process, worker, scheduler, conductor, or queue processor. Use
`apiEndpoints` to document externally meaningful interfaces. If an endpoint sets
`exposedBy`, the value must match an `internalProcesses[].name` value.

Example:

```yaml
internalProcesses:
  - name: orders-api
    role: api
    exposesApi: true
    communicationModel: both
apiEndpoints:
  - name: Orders REST API
    path: /orders
    protocol: REST
    authenticationModel: oauth
    exposedBy: orders-api
```

## Product Dependencies

Use `internalComponents` when the Product Service consumes a specific
Technology Component or deployable object inside its runtime boundary. When the
referenced object is a Technology Component, `configuration` can point to a
specific named Technology Component configuration.

Use `externalInteractions` for outbound calls or external platforms the Product
Service depends on. Product Service dependencies follow the same validation rule
as other deployable objects: if an internal component or external interaction
does not directly satisfy an applicable requirement, explain why it exists under
`architecturalDecisions.internalComponentRationales` or
`architecturalDecisions.externalInteractionRationales`.

## Product Service Versus Reusable Services

Runtime Service, Data-at-Rest Service, and Edge/Gateway Service objects describe
reusable architecture behavior. A Product Service describes the first-party
deployable component that runs on top of one of those reusable objects.

If a component contains no first-party code, it is not necessarily a Product
Service. If it is only site content, static assets, database schema, or simple
product-specific configuration, it should not be elevated to Product Service
just because CI/CD can deploy it.
