# DRAFT Versioning

DRAFT uses semantic version numbers for the framework, but the compatibility
promise changes before and after `1.0.0`.

The current framework version is recorded in `draft-framework.yaml`. DRAFT Table
has its own package version in `pyproject.toml`.

## Before 1.0.0

DRAFT is currently in pre-1.0 framework formation mode.

Version format:

```text
0.MINOR.PATCH
```

Rules:

- `0.MINOR.0` may include object model changes, schema changes, renamed
  concepts, validation changes, and migration work.
- `0.MINOR.0` may break existing workspaces, but the compatibility impact and
  migration steps must be documented in `CHANGELOG.md`.
- `0.MINOR.PATCH` is reserved for fixes, documentation corrections, generated UI
  corrections, validator bug fixes, packaging fixes, and small non-breaking
  cleanup.
- Patch releases must not intentionally change the object contract.
- Every release, including patch releases, requires release notes.
- Every object, schema, Definition Checklist, compliance, or validation contract
  change requires a compatibility statement.

## At 1.0.0

`1.0.0` declares the first stable DRAFT compatibility baseline.

After `1.0.0`:

- `MAJOR` means existing valid company workspaces may require migration.
- `MINOR` means new capability with backward compatibility.
- `PATCH` means fixes only, with no intended behavior or contract change.

If updating the framework can make a previously valid company workspace fail
validation without the company opting into a stricter mode, that is a breaking
change. Before `1.0.0`, it belongs in a `0.MINOR.0` release. After `1.0.0`, it
requires a `MAJOR` release.

## Required Release Notes

Every numbered release entry in `CHANGELOG.md` must include:

- `Compatibility Impact`
- `Added`
- `Changed`
- `Fixed`
- `Migration Notes`

`Compatibility Impact` must say whether migration is required. `Migration
Notes` must say what a company workspace owner should do after refreshing the
framework. If no migration is required, say that explicitly.

Pull requests or direct commits that change governed framework files but do not
advance `draft-framework.yaml` must put the same quality of notes under
`Unreleased`. When a version is assigned, move those notes into the numbered
release entry.

## Main Branch Rules

Before `1.0.0`, direct commits to `main` are allowed, but release-note checks
still run in CI so missing notes are visible immediately.

After `1.0.0`, changes to `main` should be made through pull requests only.
GitHub branch protection should require:

- a pull request before merging
- passing validation and release-note checks
- at least one approving review
- no unresolved conversations

Branch protection is the GitHub enforcement point for "PR only"; CI enforces
the repository-local release-note and compatibility rules.
