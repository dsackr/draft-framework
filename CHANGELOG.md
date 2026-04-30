# Changelog

All notable DRAFT Framework changes are recorded here. Every release requires
notes, including patch releases.

## Unreleased

Use this section for work that has not been assigned to a release yet. Move the
notes into a numbered release section before changing `draft-framework.yaml`.

## 0.5.0 - 2026-04-30

### Compatibility Impact

No workspace object migration is required. Company workspaces can adopt this
release by refreshing their vendored framework and adding the optional update
workflow.

### Added

- Added a default company-side GitHub Actions workflow template that checks for
  newer DRAFT Framework versions, opens an update branch and pull request,
  refreshes `.draft/framework/`, updates `.draft/framework.lock`, and records
  validation status.
- Added blocked update PR behavior for failed workspace validation so companies
  can repair migration issues on the update branch instead of losing the
  attempted framework update.

### Changed

- Updated DRAFT Table workspace bootstrap so new company workspaces receive the
  framework update workflow by default.
- Documented the company framework update notification and PR workflow.

### Fixed

- No fixes in this release.

### Migration Notes

- Existing company workspaces can copy
  `templates/workspace/.github/workflows/draft-framework-update.yml.tmpl` to
  `.github/workflows/draft-framework-update.yml`.
- The workflow is optional. Disable it in GitHub Actions or delete the workflow
  file if the company wants to manage framework updates manually.

## 0.4.0 - 2026-04-30

### Compatibility Impact

Breaking workspace migration may be required for workspaces created from earlier
pre-1.0 framework commits. This release is still in the pre-1.0 framework
formation phase, so object model changes are allowed when documented here.

### Added

- Added DRAFT Table as the local-first Draftsman web and CLI experience.
- Added company workspace bootstrapping with a vendored `.draft/framework/`
  copy and explicit framework refresh behavior.
- Added provider-scoped compliance controls and Control Enforcement Profiles.
- Added active compliance profile configuration in `.draft/workspace.yaml`.
- Added the current framework version manifest at `draft-framework.yaml`.

### Changed

- Renamed the primary DRAFT terminology around Technology Components,
  Appliance Components, Host Standards, Service Standards, Database Standards,
  Reference Architectures, Software Deployment Patterns, Definition Checklists,
  Decision Records, Compliance Controls, and Control Enforcement Profiles.
- Updated compliance activation so framework, third-party, and company control
  providers can coexist without filename or ownership ambiguity.
- Updated appliance component guidance so service-like required capabilities are
  captured directly on the appliance component.
- Updated Draftsman guidance so capability questions ask what satisfies the
  capability, not which organization team performs the work.

### Fixed

- Fixed DRAFT Table onboarding behavior for piped installers and local content
  repo creation.
- Fixed Draftsman chat route diagnostics and provider timeout surfacing.
- Fixed browser and DRAFT Table UI alignment with the GitHub Pages experience.

### Migration Notes

- Refresh the vendored framework copy in each company workspace through
  `draft-table framework refresh` or the equivalent repository process.
- Review object and file naming against the updated terminology before treating
  old workspace content as current.
- Update any references to framework-provided compliance profiles to the
  provider-scoped IDs such as `control-enforcement.draft-soc2`.
- Use `controlEnforcementProfiles` and `controlImplementations` to record active
  compliance disposition; `opted-out` has been replaced by `not-compliant`.
- Run validation after refresh with
  `python3 .draft/framework/tools/validate.py --workspace .`.
