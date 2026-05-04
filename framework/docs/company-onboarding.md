# Company Onboarding Tutorial

## Purpose

This tutorial describes how a company adopts DRAFT from an empty private repo
to a working architecture catalog. It is written to expose implementation gaps
before DRAFT 1.0 by making every setup decision explicit.

The goal is not to fill in forms. The goal is to create a governed drafting
environment where the Draftsman can interview users, read source material,
reuse approved standards, and produce deployable architecture objects that pass
validation.

## Starting Model

A company uses two repositories:

- the upstream DRAFT Framework repo as the update source
- a private company DRAFT repo as the working architecture catalog

The company repo vendors the selected framework copy under `.draft/framework/`.
Normal Draftsman work reads that vendored copy. The public framework repo is
not a runtime dependency.

The company repo owns:

- `.draft/workspace.yaml` for workspace activation and business taxonomy
- `.draft/framework/` for the reviewed framework copy
- `.draft/framework.lock` for the framework source, version, and commit
- `configurations/` for company capability mappings, Requirement Groups,
  object patches, domains, and business-specific configuration
- `catalog/` for deployable architecture content, Technology Components,
  Reference Architectures, Software Deployment Patterns, decisions, and
  Drafting Sessions
- `docs/index.html` for the generated read-only browser

## Phase 1: Install And Create The Workspace

Install DRAFT Table from an interactive terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/dsackr/draft-framework/main/install-draft-table.sh | bash
```

Run onboarding:

```bash
draft-table onboard
```

During onboarding, select or create the private company DRAFT repo. The repo
should be treated as source code: changes are reviewed, validated, committed,
and pushed through normal Git workflow.

After onboarding, confirm the workspace:

```bash
draft-table doctor
draft-table framework status
draft-table validate
```

## Phase 2: Make Workspace Decisions

Before drafting product architecture, decide the company-level controls that
shape every object.

### Business Taxonomy

Define the business pillars or product groupings in `.draft/workspace.yaml`.
Software Deployment Patterns use this taxonomy so executives can navigate
architecture by business ownership.

Example decisions:

- What are the company's business pillars?
- Is every Software Deployment Pattern required to choose a pillar?
- Who owns each pillar?

### Active Requirement Groups

Activate the Requirement Groups the company architects against:

```yaml
requirements:
  activeRequirementGroups:
    - <soc2-requirement-group-uid>
    - <company-requirement-group-uid>
  requireActiveRequirementGroupDisposition: false
```

The presence of a Requirement Group YAML file does not activate it. Activation
is a build-time workspace decision.

Use `requireActiveRequirementGroupDisposition: false` while migrating existing
inventory. Set it to `true` when the company is ready for validation to require
every in-scope object to record disposition against every active group.

### Capability Owners

Every capability with implementation mappings needs a company owner. The owner
is the decision authority for acceptable-use lifecycle entries such as
`candidate`, `preferred`, `existing-only`, `deprecated`, and `retired`.

Example decisions:

- Who owns authentication?
- Who owns operating systems?
- Who owns compute platforms?
- Who owns log management, monitoring, patching, and security monitoring?
- Who can approve a new Technology Component for a capability?

## Phase 3: Build The Acceptable Use Technology Baseline

Technology Components are discrete vendor products and versions. Capabilities
are company-governed abilities. Capability implementation mappings connect the
two.

For each required capability:

1. Confirm the capability exists.
2. Identify the company owner.
3. Add Technology Components that can satisfy the capability.
4. Assign acceptable-use lifecycle status.
5. Record configuration names when only a specific Technology Component
   configuration satisfies the capability.

The generated browser's Acceptable Use Technology view should become the
company-readable technology lifecycle list.

Do not approve a Capability until at least one Requirement Group requirement
references it. Requirements create demand; capabilities provide reusable
answers.

## Phase 4: Draft The First Deployable Standards

Draft reusable deployable objects in this order:

1. Technology Components for the products and versions in use
2. Hosts for operating system plus compute platform combinations
3. Runtime Services for web, app, worker, messaging, cache, or runtime behavior
4. Data-at-Rest Services for database, file, object, analytics, and storage
5. Edge/Gateway Services for WAF, firewall, load balancer, ingress, proxy, or
   API gateway behavior
6. Product Services for first-party custom binaries or black-box services
7. Software Deployment Patterns for complete intended product deployment shapes

Choose object type by behavior first. Then choose delivery model:

- `self-managed`
- `paas`
- `saas`
- `appliance`

PaaS, SaaS, and appliance are not object types. They are delivery-model overlays
that add requirements to Runtime Service, Data-at-Rest Service, and
Edge/Gateway Service objects.

## Phase 5: Conduct The First Drafting Session

The first drafting session should be an interview, not a YAML editing exercise.

Start with a real product, diagram, repository, or source document. The
Draftsman should:

1. identify the product or system being described
2. extract observed components and deployment facts
3. separate observations from assumptions
4. resolve existing Technology Components and deployable objects before making
   new ones
5. identify applicable Requirement Groups from object type, delivery model, and
   active workspace governance
6. ask focused follow-up questions for missing required facts
7. create or update DRAFT objects behind the scenes
8. run validation before presenting completed work

Unresolved facts should be stored in a Drafting Session, not hidden in prose.

## Phase 6: Validate, Review, And Publish

Validation is the contract between conversation and source.

Run:

```bash
draft-table validate
```

or from the company repo:

```bash
python3 .draft/framework/tools/validate.py --workspace .
```

Regenerate the browser:

```bash
python3 .draft/framework/tools/generate_browser.py --workspace . --output docs/index.html
```

Review the Git diff. Commit the source YAML and generated browser together
when the browser is used for GitHub Pages.

## Phase 7: Keep The Framework Current

Framework updates are explicit. A company refreshes `.draft/framework/`, reviews
the diff, validates, and commits the update in the private repo.

Manual update:

```bash
draft-table framework status
draft-table framework refresh
draft-table validate
```

Optional GitHub Actions can automate update branches and pull requests, but the
company still reviews the result before merging.

## Readiness Checklist

A company is ready for serious drafting when:

- the private DRAFT repo has `.draft/framework/` and `.draft/framework.lock`
- `.draft/workspace.yaml` declares business taxonomy and active Requirement
  Groups
- capability owners are identified for mapped capabilities
- approved capabilities are referenced by Requirement Group requirements
- acceptable-use Technology Components are mapped by capability
- baseline Hosts, Runtime Services, Data-at-Rest Services, and Edge/Gateway
  Services exist for common deployment patterns
- the Draftsman can answer framework questions from the vendored docs
- validation passes
- GitHub Pages or DRAFT Table browser shows the generated catalog

## Gap Signals Before 1.0

During onboarding, treat these as framework gaps worth addressing before 1.0:

- a company cannot tell which Requirement Groups are object definitions,
  delivery overlays, or workspace governance
- capability-backed questions do not resolve to the company's approved
  multiple-choice options when approved implementations exist
- Technology Components appear to have company lifecycle outside capability
  mappings
- a company cannot identify the owner for a capability decision
- approved capabilities have no requirement trace
- delivery model language makes PaaS, SaaS, or appliance sound like object
  types
- validation failures do not tell the Draftsman exactly what to add or where to
  look next
- the generated UI shows runtime filters instead of build-time governance
  decisions
