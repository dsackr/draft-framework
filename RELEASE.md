# Release Checklist

Use this checklist whenever DRAFT Framework changes are promoted as a numbered
release.

## Classify The Change

- Current version in `draft-framework.yaml`:
- New version:
- Release phase: pre-1.0 or stable
- Compatibility impact: no migration, optional migration, or required migration
- Object/schema/validation contract changed: yes or no

## Update Release Files

- Update `draft-framework.yaml`.
- Update `CHANGELOG.md` with a numbered release entry.
- Include `Compatibility Impact`, `Added`, `Changed`, `Fixed`, and
  `Migration Notes`.
- Move any applicable notes out of `Unreleased`.
- If a change is not ready for a version bump, document it under `Unreleased`
  using the same section names.
- For pre-1.0 breaking changes, use `0.MINOR.0` and document migration steps.
- For stable breaking changes after `1.0.0`, use a new major version.

## Validate

Run:

```bash
python3 framework/tools/validate.py
python3 -m unittest discover -s tests
python3 framework/tools/check_release_notes.py
python3 framework/tools/generate_ai_index.py
git diff --exit-code AI_INDEX.md
```

If browser-visible YAML, docs, schemas, or templates changed, also run:

```bash
python3 framework/tools/generate_browser.py
git diff --exit-code docs/index.html
```

## Publish

Before `1.0.0`, direct commits to `main` are allowed.

After `1.0.0`, publish through a pull request with branch protection enabled.
When creating a release tag, use `vX.Y.Z` and verify it matches
`draft-framework.yaml`.
