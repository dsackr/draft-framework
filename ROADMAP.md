# DRAFT v1.0 Readiness Roadmap

This roadmap tracks the remaining MVP work needed to move DRAFT from a credible
architecture catalog framework to a version 1.0 deployable architecture
platform.

The v1.0 goal is narrow and concrete: a Draftsman conversation should produce a
complete, compliant, reviewable architecture graph that can be translated into a
deployment plan without hiding operational or security gaps.

## Tracking Model

Track execution in GitHub with:

- milestone: `v1.0`
- core labels: `v1.0`, `mvp`
- area labels: `deployment`, `automation`, `catalog`, `compliance`,
  `draftsman`

The canonical v1.0 work items are GitHub issues #3, #4, and #5. Keep this file
as the stable narrative and use GitHub Issues for execution, discussion, and
ownership.

## Issue 1: v1.0: executable deployment contract

Problem:

DRAFT currently captures deployable architecture facts, but deployable is still
mostly a semantic promise. The framework needs one explicit path from approved
DRAFT objects to a generated deployment plan.

MVP outcome:

Define a minimal executable deployment contract that can translate one approved
Software Deployment Pattern graph into a deployment manifest and dry-run plan.

Acceptance criteria:

- Add a machine-readable deployment target and environment binding contract.
- Generate a deployment manifest from an approved Software Deployment Pattern
  and its closed deployable object graph.
- Add one narrow adapter path for dry-run output, even if the first adapter only
  emits a neutral plan format rather than applying infrastructure.
- Block deployment plan generation when the graph contains unresolved Drafting
  Session questions, invalid references, not-compliant requirements, or
  unapproved required objects.
- Represent secrets only as references, never as literal values.
- Add validator coverage and documentation for the contract.

Recommended labels: `v1.0`, `mvp`, `deployment`, `automation`

## Issue 2: v1.0: complete golden reference workspace

Problem:

The framework has strong schemas, Requirement Groups, and validation logic, but
the example catalog does not yet prove a complete product deployment path with
compliance evidence.

MVP outcome:

Ship one complete golden workspace that demonstrates the intended DRAFT loop end
to end.

Acceptance criteria:

- Include Technology Components, Host, Runtime Service, Data-at-Rest Service,
  Edge/Gateway Service, Product Service, Reference Architecture, Software
  Deployment Pattern, Decision Record, and Drafting Session examples.
- Activate at least one workspace-mode security or compliance Requirement
  Group.
- Record valid `requirementImplementations` evidence for the active group.
- Demonstrate acceptable-use Technology Component mappings through
  capabilities.
- Ensure the golden workspace validates without warnings.
- Regenerate the browser so topology, relationships, requirements, evidence,
  and acceptable-use views can be inspected.
- Document how maintainers should use the golden workspace as a regression
  target for v1.0 changes.

Recommended labels: `v1.0`, `mvp`, `catalog`, `compliance`

## Issue 3: v1.0: deterministic Draftsman production workflow

Problem:

DRAFT Table has the first Draftsman loop, but production authoring still depends
too much on provider-generated YAML and post-write validation.

MVP outcome:

Make Draftsman output structured, reviewable, repairable, and safe enough for
governed company workspaces.

Acceptance criteria:

- Replace opaque YAML proposal content with a structured proposal model that can
  be validated before writing files.
- Show schema-aware review cards and diffs before apply.
- Map validation failures to actionable repair steps that the Draftsman can
  propose or perform.
- Record source provenance on every generated or materially updated artifact.
- Preserve Drafting Session state so interrupted work can resume without relying
  on chat history.
- Add branch, commit, and pull request workflow from DRAFT Table or document the
  minimum supported CLI path.
- Add tests that cover proposal validation, failed validation recovery,
  provenance capture, and resumable sessions.

Recommended labels: `v1.0`, `mvp`, `draftsman`, `compliance`
