# Security And Compliance Requirement Groups

## What This Layer Does

DRAFT treats compliance as an explicitly activated authoring and validation layer.
The layer is implemented with `requirement_group` objects using
`activation: workspace`.

The presence of a requirement group YAML file does not make it active. A company
activates the groups it architects against in `.draft/workspace.yaml`:

```yaml
requirements:
  activeRequirementGroups:
    - requirement-group.draft-soc2
    - requirement-group.company-roper
  requireActiveRequirementGroupDisposition: false
```

`requireActiveRequirementGroupDisposition: false` allows existing inventory to
migrate incrementally. Draftsman still asks active-group questions for new and
updated objects. Setting it to `true` makes validation require every approved
in-scope object to record disposition for every active workspace-mode group.

## Provider And Authority

A workspace-mode Requirement Group may be authored by the framework, a company,
or a third-party provider. Use `provider` to identify who authored the DRAFT
mapping and `authority` to identify the external source or program.

Examples:

- `requirement-group.draft-soc2` is a DRAFT Framework-provided mapping for SOC 2.
- `requirement-group.company-roper` would be a company-owned internal control group.
- A provider pack can publish `requirement-group.vendor-soc2` without replacing
  the framework-provided SOC 2 interpretation.

The framework maintains its included DRAFT-provided mappings as starter
architecture aids. It does not claim that using them makes a company compliant
with SOC 2, NIST CSF, TX-RAMP, or any external program. The authority remains
the auditor, regulator, control owner, or company compliance program.

## Object-Level Evidence

Objects use `requirementGroups` to claim a workspace-mode group and
`requirementImplementations` to record evidence:

- `satisfied`: the object has a valid answer for the requirement
- `not-applicable`: the requirement permits N/A and the object records that disposition
- `not-compliant`: the gap is known and must remain visible until fixed

When a requirement has `relatedCapability`, the Draftsman resolves the capability
object, reads the company capability owner, and recommends `invest` or
`maintain` Technology Component implementations before asking the user. This
means compliance questions are grounded in the same capability model as base
object-definition questions.

## Browser Behavior

The GitHub Pages browser is read-only. It shows Requirement Groups as framework
content and shows declared requirement groups on object detail pages. It does
not provide a runtime compliance display filter or selector. Activation is a
build-time workspace configuration decision in `.draft/workspace.yaml`.
