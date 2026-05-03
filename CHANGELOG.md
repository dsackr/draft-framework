# Changelog

All notable DRAFT Framework changes are recorded here. Every release requires
notes, including patch releases.

## 0.9.0 - 2026-05-03

### Compatibility Impact

Breaking pre-1.0 object identity migration required. First-class catalog and
configuration objects now use generated `uid` values instead of semantic
top-level `id` values. Existing workspaces must run UID repair and regenerate
derived browser/index output. Workspaces remain free to opt into
`businessTaxonomy.requireSoftwareDeploymentPatternPillar` separately.

### Added

- Added optional `businessContext` support to Software Deployment Patterns so
  company workspaces can identify the primary business pillar, additional
  pillars, and product family for a deployment pattern.
- Added workspace `businessTaxonomy.pillars` validation through
  `.draft/workspace.yaml`.
- Added generated browser grouping and badges for Software Deployment Patterns
  by workspace-defined business pillar.
- Added generated UID validation for first-class objects. Validation now
  reports missing, malformed, duplicate, and legacy top-level object identity
  with a suggested UID and an explicit repair command.
- Added `framework/tools/repair_uids.py` and `framework/tools/uid_utils.py` to
  generate object UIDs, remove legacy top-level `id`, rewrite exact object
  references, and migrate legacy Drafting Session UID field names.
- Added optional `aliases` to first-class object schemas so prior or alternate
  human-readable names can resolve to the same stable object.

### Changed

- Updated Draftsman and workspace documentation so company business taxonomy is
  resolved from `.draft/workspace.yaml`, not tags, capabilities, or Strategy
  Domains.
- Changed first-class object identity from semantic `id` to generated opaque
  `uid`. Human-facing object resolution should use name, aliases, path, close
  match, and only then UID.
- Changed object reference validation, object patching, browser generation, and
  AI index generation to use generated UIDs as the machine reference key.
- Changed Drafting Session object-reference fields from `primaryObjectId` and
  `proposedId` to `primaryObjectUid` and `proposedUid`.

### Fixed

- Fixed the Software Deployment Pattern browsing experience so product
  deployment patterns can be scanned by company portfolio ownership instead of
  only by object type.
- Fixed generated browser reference discovery so generated UID references are
  indexed without depending on semantic object prefixes.

### Migration Notes

- Run `python3 framework/tools/repair_uids.py --workspace examples` in the
  framework repo, or `python3 .draft/framework/tools/repair_uids.py --workspace
  .` from a company repo, to add generated `uid` values, remove legacy
  top-level `id`, and rewrite exact object references.
- Regenerate `AI_INDEX.md` and `docs/index.html` after UID repair.
- If validation reports a missing, malformed, duplicate, or legacy identity,
  run the exact repair command it prints; the command includes the suggested
  UID when repairing a single file.
- To use the business taxonomy feature, declare `businessTaxonomy.pillars` in
  `.draft/workspace.yaml`, then add `businessContext.pillar` to each Software
  Deployment Pattern. Set
  `businessTaxonomy.requireSoftwareDeploymentPatternPillar: true` only after the
  workspace is ready to enforce the field.

## 0.8.2 - 2026-05-03

### Compatibility Impact

No schema, validation, or catalog object compatibility impact. Existing
workspaces remain valid.

### Added

- Added generated browser rendering for Software Deployment Pattern source
  repositories when repository provenance is recorded on the object.

### Changed

- Updated Draftsman guidance so repository-discovered artifacts record
  provenance on each generated object, not only in a shared Drafting Session.

### Fixed

- Fixed generated browser rendering for nested architectural decision arrays so
  structured provenance entries do not appear as `[object Object]`.

### Migration Notes

No workspace data migration is required. Repository-discovered Software
Deployment Patterns can optionally add
`architecturalDecisions.sourceRepositories` to make per-pattern provenance
visible in the generated browser.

## 0.8.1 - 2026-05-03

### Compatibility Impact

No schema, validation, or catalog object compatibility impact. Existing
workspaces can continue using 0.8.0 content and only need to refresh generated
browser assets to receive the updated welcome-page branding.

### Added

- Added the transparent 512x512 `draft-logo.png` asset to the framework so
  generated browser pages can use the official DRAFT logo.
- Added automated version-bump enforcement to the release-note checker so
  release-impacting framework changes must advance `draft-framework.yaml`.

### Changed

- Changed the Executive View welcome hero to place the larger DRAFT logo beside
  the full title, descriptive text, and action area, and retitled the page
  `Welcome to the DRAFTing Table`.
- Documented the AI release decision procedure for choosing pre-1.0 minor
  versus patch releases consistently.

### Fixed

- Fixed framework release metadata so the generated browser branding change is
  recorded as patch release 0.8.1.
- Fixed the validation workflow label to make version-bump enforcement explicit
  in GitHub Actions.

### Migration Notes

No YAML or workspace data migration is required. Regenerate `docs/index.html`
or pull the updated vendored framework files to display the new welcome logo
layout in an existing workspace.

## 0.8.0 - 2026-05-03

### Compatibility Impact

Breaking pre-1.0 lifecycle vocabulary migration required. Workspaces must
replace the old lifecycle labels with the new plain-language labels across
catalog objects and capability implementation mappings: `pre-invest` becomes
`candidate`, `invest` becomes `preferred`, `maintain` becomes `existing-only`,
`disinvest` becomes `deprecated`, and `exit` becomes `retired`.

### Added

- Added an Executive View as the default generated browser landing page, with
  clickable metric tiles for controls addressed, Technology Components,
  Capabilities, Software Deployment Patterns, requirement definitions, and
  acceptable-use mappings.
- Added an Acceptable Use Technology browser view that groups Technology
  Component lifecycle mappings by domain and capability, including owner/contact
  information for change requests.

### Changed

- Renamed lifecycle vocabulary to plainer adopting-company language:
  `candidate`, `preferred`, `existing-only`, `deprecated`, and `retired`.
- Renamed the generated browser list navigation to Drafting Table so the
  executive landing page can hand users into the existing object browser.
- Documented Reference Architecture lifecycle policy: cloud-forward patterns are
  `preferred`, legacy supported patterns are `existing-only`, and patterns containing
  end-of-support Technology Components are `deprecated`. Patterns containing
  extended-support Technology Components default to `deprecated`, may be
  `existing-only` with explicit rationale, and must not be `preferred`.
- Increased Executive View metric and tile heading sizes so each collage tile
  carries equal visual weight.
- Fixed Executive View tile CSS so the shared large metric size is not
  overridden by paragraph styling.
- Documented the Acceptable Use Technology view as the generated human-readable
  table for company technology lifecycle mappings.
- Changed the Acceptable Use Technology table to group Technology Components
  under capability headers, with owner/contact shown on the capability header
  instead of repeated in every row.
- Changed the Acceptable Use Technology view to omit unmapped capabilities and
  empty domain groups so it remains a Technology Component list.
- Clarified Draftsman guidance for overlapping base and workspace-activated
  control requirements that share a capability.
- Added per-capability Technology Component counts to the Acceptable Use
  Technology browser view.

### Fixed

- Fixed generated browser payloads so Capability domain assignments are included
  in the Acceptable Use Technology view instead of appearing as unassigned.
- Fixed Reference Architecture and Software Deployment Pattern requirement
  evidence so `serviceGroups`, `patternType`, and `architecturalDecisions`
  fields satisfy the matching requirement group checks directly.
- Fixed requirement satisfaction for external interactions declared inside
  `serviceGroups`, so nested service group interactions count toward the same
  mechanisms as top-level interactions.
- Fixed Reference Architecture validation so patterns that include Technology
  Components past `vendorLifecycle.extendedSupportEnd` must be marked
  `deprecated`.
- Fixed Reference Architecture validation so patterns that include Technology
  Components past `vendorLifecycle.mainstreamSupportEnd` cannot be marked
  `preferred`; `existing-only` requires an explicit lifecycle rationale.

### Migration Notes

- Replace lifecycle labels in workspace YAML:
  `pre-invest` -> `candidate`, `invest` -> `preferred`,
  `maintain` -> `existing-only`, `disinvest` -> `deprecated`,
  and `exit` -> `retired`.
- Regenerate `docs/index.html` to publish the Acceptable Use Technology view for
  a framework or workspace browser.

## 0.7.0 - 2026-05-02

### Compatibility Impact

Breaking workspace migration is required for capability overlays that assign
Technology Component implementations. DRAFT is still pre-1.0, so breaking
object model changes are allowed in 0.MINOR.0 releases when documented with
migration notes.

Existing name-only external interactions remain valid, but shared platforms
should be modeled and referenced when known.

### Added

- Added validation that `externalInteractions[].ref` values point to existing
  catalog objects.
- Added `definitionOwner` to Capability objects so framework, provider, and
  company vocabulary ownership is separate from company implementation
  authority.
- Added validation requiring `owner.team` on the effective Capability whenever
  implementations are assigned.

### Changed

- Changed framework base Capabilities to carry `definitionOwner` only and leave
  company `owner` to workspace overlays.
- Clarified that Capability implementation lifecycle entries must reference
  Technology Components only, because lifecycle disposition applies to a
  discrete vendor product and version.
- Clarified that central logging and other shared enterprise platforms should be
  modeled as Standards or service classifications rather than left as permanent
  name-only external interactions.
- Updated Requirement Group examples and the host template to prefer resolved
  logging platform references.
- Updated the browser to distinguish Capability definition owner from company
  owner.

### Fixed

- Fixed workspace-mode Requirement Group validation so active groups remain
  incremental when `requireActiveRequirementGroupDisposition` is false, while
  still requiring explicit activation before an object can claim them.
- Fixed Requirement Group validation so resolving `requirementImplementations`
  satisfy the matching requirement evidence during workspace control validation.

### Migration Notes

- Refresh the vendored framework copy.
- Add `definitionOwner` to any workspace-owned Capability files.
- Add `patch.owner.team` or full `patch.owner` to object patches that assign
  Capability implementations.
- Keep Capability `implementations[].ref` pointed at Technology Components
  only. If a SaaS or managed service is lifecycle-governed, model the specific
  vendor product and version as a Technology Component and compose the
  service-facing Standard separately.
- Existing black-box external interactions can stay as drafting placeholders.
  When the target platform is known, add or reuse the modeled DRAFT object and
  set `externalInteractions[].ref`.

## 0.6.0 - 2026-05-01

### Compatibility Impact

Breaking workspace migration is required for pre-0.6.0 content that uses
Definition Checklists, Compliance Controls, Control Enforcement Profiles, or
top-level Technology Component `lifecycleStatus`. DRAFT is still pre-1.0, so
breaking object model changes are allowed in 0.MINOR.0 releases when documented
with migration notes.

### Added

- Added first-class `capability` objects in `framework/configurations/capabilities/`.
- Added unified `requirement_group` objects in
  `framework/configurations/requirement-groups/`.
- Added sample workspace capability implementation patches under
  `examples/configurations/object-patches/`.
- Added AI-first schema `aiHint` metadata and required-field descriptions.
- Added a DRAFT Table Guide tab that explains what DRAFT is, how to navigate the
  UI, what the core artifact families mean, and how content updates flow through
  Draftsman, validation, and Git.

### Changed

- Replaced Definition Checklists and Compliance Controls plus Control
  Enforcement Profiles with the unified Requirement Group model.
- Replaced workspace `compliance.activeControlEnforcementProfiles` with
  `requirements.activeRequirementGroups`.
- Replaced object-level `controlEnforcementProfiles` and
  `controlImplementations` with `requirementGroups` and
  `requirementImplementations`.
- Changed Technology Component `capabilities` to reference capability object IDs.
- Removed top-level Technology Component `lifecycleStatus`; company disposition
  now lives on capability implementation mappings.
- Updated the browser to remove the Compliance Build Profile selector and show
  Capabilities and Requirement Groups as framework content.
- Updated Draftsman guidance to use the named requirement-to-capability lookup
  chain before asking users open-ended questions.

### Fixed

- Improved validation failures so missing schema fields and requirement gaps are
  written as actionable instructions.

### Migration Notes

- Move any workspace Definition Checklist files to `requirement_group` objects
  under `configurations/requirement-groups/`.
- Move active compliance profile configuration to:
  `requirements.activeRequirementGroups`.
- Rename object evidence fields from `controlEnforcementProfiles` and
  `controlImplementations` to `requirementGroups` and
  `requirementImplementations`.
- Convert bare capability strings such as `log-management` to namespaced
  capability IDs such as `capability.log-management`.
- Move Technology Component adoption disposition into capability implementation
  mappings. Keep vendor support dates in Technology Component `vendorLifecycle`.
- Refresh the vendored framework copy and run
  `python3 .draft/framework/tools/validate.py --workspace .`.

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
