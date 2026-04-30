# How To Add Objects

## Start With The Right Question

The fastest way to add a new object correctly is to decide what kind of thing you are modeling before you write YAML.

Are you documenting:

- a vendor product
- a reusable architecture pattern
- a software deployment pattern
- an object-definition checklist

Many mistakes happen because engineers skip that decision and start writing fields immediately.

## AI-First Authoring Workflow

When an AI assistant is connected to this repo, it should start from
[AGENTS.md](../../AGENTS.md), then use [AI_INDEX.md](../../AI_INDEX.md) for
repository discovery.

When creating a new object, prefer the closest file in
[templates/](../../templates/) as a starting point, then replace placeholders
with real architecture facts and run validation. Template files use the
`.yaml.tmpl` extension so they are not treated as live catalog objects.

In a company workspace, generated architecture content belongs under
`catalog/`. Company configuration and extension content belongs under
`configurations/`. The selected framework version lives under
`.draft/framework/`. Edit company YAML directly, keep changes small and
reviewable, and run validation before treating the work as complete.

## Add A Technology Component

1. Decide whether the object is an Operating System, Compute Platform, Software, or Agent Technology Component.
2. Choose the correct ID pattern.
3. Create the YAML file in `catalog/technology-components/`.
4. Fill in the shared base fields.
5. Fill in the required Technology Component fields: `vendor`, `productName`, `productVersion`, and `classification`.
6. Add `capabilities` if the Technology Component itself satisfies reusable host capabilities.
7. Add `configurations` if a named Technology Component configuration satisfies reusable host capabilities.
8. Fill in any remaining Technology Component-specific metadata such as vendor lifecycle and optional platform dependency.
9. If the Technology Component is classified as `agent`, make sure any Standard that uses it also documents the corresponding external interaction or an architectural decision exception under `architecturalDecisions.agentInteractionExceptions`.
10. Run validation.

Technology Components should be specific. If you cannot name the product version clearly, you probably are not ready to create the object yet.

## Add A Host Standard

1. Create the file in `catalog/host-standards/`, `catalog/service-standards/`, or `catalog/database-standards/`.
2. Reference the Operating System and Compute Platform Technology Components explicitly.
3. Add any Agent Technology Components or other internal components that physically live on the host.
4. Document `externalInteractions` for identity, logging, security, monitoring, patching, or other platforms.
5. Add `architecturalDecisions` when the host must answer a Definition Checklist or compliance question that is not expressed directly in the object.
6. Add `controlEnforcementProfiles` only for Control Enforcement Profiles the host explicitly claims to
   satisfy, then add valid `controlImplementations` for every applicable
   control in each declared profile.
7. Add `satisfiesDefinitionChecklist: [checklist.host-standard]`.
8. Run validation.

## Add A Service Standard

1. Create the file in `catalog/host-standards/`, `catalog/service-standards/`, or `catalog/database-standards/`.
2. Reference exactly one `hostStandard` and one `primaryTechnologyComponent`.
3. Add service-level external interactions that go beyond the host baseline.
4. Document the decisions that describe scaling, health, secrets handling, and, for DBMS services, durability and protection.
5. Use `architecturalDecisions` whenever the service must answer a Definition Checklist or compliance question that is not expressed directly in the object.
6. Add `controlEnforcementProfiles` only for Control Enforcement Profiles the service explicitly claims
   to satisfy, then add valid `controlImplementations` for every applicable
   control in each declared profile.
7. Set `satisfiesDefinitionChecklist` to the correct Definition Checklist list.
8. Run validation.

## Add A Definition Checklist

1. Create an `object_patch` override or extension file in
   `configurations/object-patches/`.
2. Define the `appliesTo` scope clearly.
3. Write requirements in the mechanism-based model.
4. For each requirement, explain what capability must be addressed, why it exists, which mechanisms are allowed, and how many satisfactions are required.
5. If the Definition Checklist extends another Definition Checklist, use `inherits`.

Base Definition Checklists live in `.draft/framework/configurations/definition-checklists/` inside a company repo. Company-specific Definition Checklist
changes should be patch-style overlays in the company repo.

A Definition Checklist can target more than Standards. The current catalog includes Definition Checklists for Standards, Reference Architectures, and Software Deployment Patterns. The `appliesTo` block is what tells the validator which object type the Definition Checklist governs.

Keep the requirements focused on architecture outcomes rather than implementation trivia.

## Add A Reference Architecture

1. Create the file in `catalog/reference-architectures/`.
2. Choose a stable `reference-architecture.<pattern-slug>` ID.
3. Populate `serviceGroups` with the reusable building blocks that define the deployment pattern.
4. Set `diagramTier` on every Standard entry and cluster related functionality into the right service group.
5. Add `architecturalDecisions` that explain what non-functional qualities the pattern is meant to deliver and how.
6. Make sure the file satisfies `checklist.reference-architecture` by documenting `patternType`, tiered service groups, and deployment-quality decisions.

A Reference Architecture should be generic enough to guide many products, not just one.

## Add A Software Deployment Pattern

1. Create the file in `catalog/software-deployment-patterns/`.
2. Choose a product-focused `software-deployment.<product-slug>` ID.
3. Set `followsReferenceArchitecture` if the product aligns with an existing Reference Architecture.
4. Define any `scalingUnits` needed to express replicable or shared deployment boundaries.
5. Build the manifest out through `serviceGroups`, then place Product Services, Standards, Appliance Components, and SaaS Services into the appropriate groups.
   Product Service is not a starting-point Definition Checklist object; use it here only when the Software Deployment Pattern needs to express a distinct first-party runtime-behavior component deployed on a substrate.
6. Set `diagramTier` on every Product Service and Standard entry using one of `presentation`, `application`, `data`, or `utility`.
7. Use `intent` only when the architect is explicitly deviating from the Reference Architecture or when no Reference Architecture exists.
8. Add product-level `architecturalDecisions`, including availability requirement and data classification, so the Software Deployment Pattern satisfies `checklist.software-deployment-pattern`.

## Add A Drafting Session

1. Create the file in `catalog/sessions/`.
2. Choose a stable `session.<topic>` ID.
3. Record the target object type in `primaryObjectType` and, if it already exists, `primaryObjectId`.
4. Add the source material that informed the current work under `sourceArtifacts`.
5. Record the YAML objects that were created, proposed, or stubbed under `generatedObjects`.
6. Record every unresolved question explicitly, including the current best guess and impact when useful.
7. Add `nextSteps` so the session can be resumed later without re-reading the entire intake.
8. Run validation.

## Add A Compliance Controls

1. Create the file in `configurations/compliance-controls/`.
2. Define the control catalog metadata such as `id`, `name`, `controlsKind`, and lifecycle fields.
3. Add controls inline under `controls`.
4. For each control, record only:
   - `controlId`
   - `name`
   - `externalReference`
   - optional `notes`
5. Run validation.

## Add A Control Enforcement Profile

1. Create the file in `configurations/control-enforcement-profiles/`.
2. Reference the backing control catalog in `controls`.
3. Add `controlSemantics`.
4. For each semantic entry, answer the `checklist.control-enforcement-profile` checklist:
   - control reference
   - requirement mode
   - DRAFT applicability
   - valid DRAFT answer types
   - conditional applicability when relevant
   - optional related capability
5. Use `requirementMode: conditional` only when the control is not always in scope and explicitly allow `N/A`.
6. Run validation.

An AI should be able to translate a source control catalog into this shape as
long as the source provides control facts and the profile docs provide the
DRAFT applicability rules.

## Add Object-Level Compliance Claims

1. Add `controlEnforcementProfiles` only for the profiles the artifact explicitly
   claims.
2. Add one `controlImplementations` entry for every control in each declared
   profile that applies to the artifact's DRAFT scope.
3. Use `not-applicable` only when the profile marks the control conditional and
   allows `N/A`.
4. Do not add `controlImplementations` for profiles the artifact has not
   declared.
5. Run validation.

Artifacts with no declared profile are unclaimed inventory, not failed
inventory. They should not be selected as compliant off-the-shelf building
blocks when a solution requires a specific control profile.

## Run The Tools

Validate locally:

```bash
python3 framework/tools/validate.py
```

Validate a company workspace:

```bash
python3 framework/tools/validate.py --workspace /path/to/company-draft-workspace
```

From inside a company repo, use the vendored framework copy:

```bash
python3 .draft/framework/tools/validate.py --workspace .
```

Regenerate the AI framework index after framework docs, schemas, Definition Checklists,
templates, or catalog YAML change:

```bash
python3 framework/tools/generate_ai_index.py
```

Regenerate the browser when needed:

```bash
python3 framework/tools/generate_browser.py
```

## What The GitHub Actions Workflows Do

- `validate-catalog.yml` runs on pushes and pull requests to make sure the YAML parses, base fields are valid, Standards satisfy their Definition Checklists, and Reference Architecture/Software Deployment Pattern objects satisfy their applicable Definition Checklist checks.
- `generate-browser.yml` runs on pushes to `main` that change YAML content and regenerates `docs/index.html` so the published browser stays synchronized with the source data.

## How To Advance `catalogStatus`

`catalogStatus` should be treated as a maturity progression, not as a cosmetic label.

- `stub` means the object exists but is skeletal.
- `draft` means the structure and major fields are present and the object is ready for review.
- `approved` means the object is complete enough to be trusted by other engineers.

For Standards, approved means the applicable Definition Checklist requirements are satisfied. For every object type, it also means the description, ownership, lifecycle, and relationships are clear enough that another engineer could use the object without guessing what it means.

The catalog uses flat folders by object family inside `catalog/`. Do not create
nested taxonomy folders under `catalog/technology-components/` or `catalog/host-standards/`, `catalog/service-standards/`, or `catalog/database-standards/`; the YAML
content already carries the object classification.
