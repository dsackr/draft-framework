# Requirement Groups

## What A Requirement Group Is

A Requirement Group is the unified DRAFT requirement model. It replaces the old
Requirement Group model and the separate Requirement Groups plus Control
Enforcement Profile model.

Every requirement is both:

- an authoring interview prompt for the Draftsman
- a validation rule for completed architecture objects

There is no translation layer between authoring and validation.

## Activation

Requirement Groups use one of two activation modes:

- `always`: base object-definition requirements that apply whenever the object
  type is in scope
- `workspace`: optional or compliance-driven requirement groups that a company
  explicitly activates in `.draft/workspace.yaml`

Workspace activation uses:

```yaml
requirements:
  activeRequirementGroups:
    - <soc2-requirement-group-uid>
  requireActiveRequirementGroupDisposition: false
```

The presence of a YAML file does not activate a workspace-mode group. Activation
is a build-time workspace decision.

## Requirement Entries

A requirement entry includes:

- `id`
- `description`
- optional `relatedCapability`
- `requirementMode`
- `naAllowed`
- optional `applicability`
- `canBeSatisfiedBy`
- `minimumSatisfactions`
- `validAnswerTypes`

For external controls, DRAFT keeps the source control ID in
`externalControlId`. When a source control ID appears more than once, the DRAFT
requirement `id` is made unique while preserving `externalControlId`.

## Object-Level Evidence

Architecture objects use:

- `requirementGroups` to record workspace-activated groups the object claims or
  explicitly addresses
- `requirementImplementations` to record `satisfied`, `not-compliant`, or
  `not-applicable` evidence for workspace-activated requirements

Always-on requirement groups are applied by object type. Workspace-mode groups
are applied only when activated and claimed by the object, or when strict
workspace disposition is enabled.

## Draftsman Behavior

For every requirement with `relatedCapability`, the Draftsman resolves the
capability before asking the user. The Draftsman reads the capability owner,
then presents `preferred` implementations first and `existing-only` implementations
second as recommended options. The question should not be open-ended unless the
company has not mapped an implementation. If no implementation is mapped, the
Draftsman asks which Technology Component should satisfy the capability and
records that the capability owner must approve the lifecycle entry.
