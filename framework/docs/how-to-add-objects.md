# How To Add Objects

## Start With The Right Question

The fastest way to add a new object correctly is to decide what kind of thing you are modeling before you write YAML.

Are you documenting:

- a vendor product
- a reusable architecture pattern
- a software distribution manifest
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
`configurations/`. The app/API should create and update those files; direct YAML
editing is a recovery path, not the preferred authoring path.

## Add An ABB

1. Decide whether the object is an Operating System, Compute Platform, Software, or Agent ABB.
2. Choose the correct ID pattern.
3. Create the YAML file in `catalog/abbs/`.
4. Fill in the shared base fields.
5. Fill in the required ABB fields: `vendor`, `productName`, `productVersion`, and `classification`.
6. Add `capabilities` if the ABB itself satisfies reusable host capabilitys.
7. Add `configurations` if a named ABB configuration satisfies reusable host capabilitys.
8. Fill in any remaining ABB-specific metadata such as vendor lifecycle and optional platform dependency.
9. If the ABB is classified as `agent`, make sure any RBB that uses it also documents the corresponding external interaction or an Architecture Decision exception under `architecturalDecisions.agentInteractionExceptions`.
10. Run validation.

ABBs should be specific. If you cannot name the product version clearly, you probably are not ready to create the object yet.

## Add A Host RBB

1. Create the file in `catalog/rbbs/`.
2. Reference the Operating System and Compute Platform ABBs explicitly.
3. Add any Agent ABBs or other internal components that physically live on the host.
4. Document `externalInteractions` for identity, logging, security, monitoring, patching, or other platforms.
5. Add `architecturalDecisions` when the host must answer an ODC or compliance question that is not expressed directly in the object.
6. Add `complianceProfiles` only for frameworks the host explicitly claims to
   satisfy, then add valid `controlImplementations` for every applicable
   control in each declared profile.
7. Add `satisfiesODC: [odc.host]`.
8. Run validation.

## Add A Service RBB

1. Create the file in `catalog/rbbs/`.
2. Reference exactly one `hostRbb` and one `functionAbb`.
3. Add service-level external interactions that go beyond the host baseline.
4. Document the decisions that describe scaling, health, secrets handling, and, for DBMS services, durability and protection.
5. Use `architecturalDecisions` whenever the service must answer an ODC or compliance question that is not expressed directly in the object.
6. Add `complianceProfiles` only for frameworks the service explicitly claims
   to satisfy, then add valid `controlImplementations` for every applicable
   control in each declared profile.
7. Set `satisfiesODC` to the correct ODC list.
8. Run validation.

## Add An ODC

1. Create an `object_patch` override or extension file through the app/API in
   `configurations/object-patches/`.
2. Define the `appliesTo` scope clearly.
3. Write requirements in the mechanism-based model.
4. For each requirement, explain what capability must be addressed, why it exists, which mechanisms are allowed, and how many satisfactions are required.
5. If the ODC extends another ODC, use `inherits`.

Base ODCs live in `framework/configurations/odcs/`. Company-specific ODC
changes should be patch-style overlays created through the app/API.

An ODC can target more than RBBs. The current catalog includes ODCs for RBBs, reference architectures, and software distribution manifests. The `appliesTo` block is what tells the validator which object type the ODC governs.

Keep the requirements focused on architecture outcomes rather than implementation trivia.

## Add A Reference Architecture

1. Create the file in `catalog/reference-architectures/`.
2. Choose a stable `ra.<pattern-slug>` ID.
3. Populate `serviceGroups` with the reusable building blocks that define the deployment pattern.
4. Set `diagramTier` on every RBB entry and cluster related functionality into the right service group.
5. Add `architecturalDecisions` that explain what non-functional qualities the pattern is meant to deliver and how.
6. Make sure the file satisfies `odc.ra` by documenting `patternType`, tiered service groups, and deployment-quality decisions.

An RA should be generic enough to guide many products, not just one.

## Add A Software Distribution Manifest

1. Create the file in `catalog/sdms/`.
2. Choose a product-focused `sdm.<product-slug>` ID.
3. Set `appliesPattern` if the product aligns with an existing RA.
4. Define any `scalingUnits` needed to express replicable or shared deployment boundaries.
5. Build the manifest out through `serviceGroups`, then place Product Services, RBBs, Appliance ABBs, and SaaS Services into the appropriate groups.
   Product Service is not a starting-point ODC object; use it here only when the SDM needs to express a distinct first-party runtime-behavior component deployed on a substrate.
6. Set `diagramTier` on every Product Service and RBB entry using one of `presentation`, `application`, `data`, or `utility`.
7. Use `intent` only when the architect is explicitly deviating from the Reference Architecture or when no Reference Architecture exists.
8. Add product-level `architecturalDecisions`, including availability requirement and data classification, so the SDM satisfies `odc.sdm`.

## Add A Drafting Session

1. Create the file in `catalog/sessions/`.
2. Choose a stable `session.<topic>` ID.
3. Record the target object type in `primaryObjectType` and, if it already exists, `primaryObjectId`.
4. Add the source material that informed the current work under `sourceArtifacts`.
5. Record the YAML objects that were created, proposed, or stubbed under `generatedObjects`.
6. Record every unresolved question explicitly, including the current best guess and impact when useful.
7. Add `nextSteps` so the session can be resumed later without re-reading the entire intake.
8. Run validation.

## Add A Compliance Framework

1. Create the file in `configurations/compliance-frameworks/`.
2. Define the framework metadata such as `id`, `name`, `frameworkKind`, and lifecycle fields.
3. Add controls inline under `controls`.
4. For each control, record only:
   - `controlId`
   - `name`
   - `externalReference`
   - optional `notes`
5. Run validation.

## Add A Compliance Profile

1. Create the file in `configurations/compliance-profiles/`.
2. Reference the backing control catalog in `framework`.
3. Add `controlSemantics`.
4. For each semantic entry, answer the `odc.compliance-profile` checklist:
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

1. Add `complianceProfiles` only for the profiles the artifact explicitly
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
blocks when a solution requires a specific framework.

## Run The Tools

Validate locally:

```bash
python3 framework/tools/validate.py
```

Validate a company workspace:

```bash
python3 framework/tools/validate.py --workspace /path/to/company-draft-workspace
```

Regenerate the AI framework index after framework docs, schemas, ODCs,
templates, or catalog YAML change:

```bash
python3 framework/tools/generate_ai_index.py
```

Regenerate the browser when needed:

```bash
python3 framework/tools/generate_browser.py
```

## What The GitHub Actions Workflows Do

- `validate-catalog.yml` runs on pushes and pull requests to make sure the YAML parses, base fields are valid, RBBs satisfy their ODCs, and RA/SDM objects satisfy their applicable ODC checks.
- `generate-browser.yml` runs on pushes to `main` that change YAML content and regenerates `docs/index.html` so the published browser stays synchronized with the source data.

## How To Advance `catalogStatus`

`catalogStatus` should be treated as a maturity progression, not as a cosmetic label.

- `stub` means the object exists but is skeletal.
- `draft` means the structure and major fields are present and the object is ready for review.
- `approved` means the object is complete enough to be trusted by other engineers.

For RBBs, approved means the applicable ODC requirements are satisfied. For every object type, it also means the description, ownership, lifecycle, and relationships are clear enough that another engineer could use the object without guessing what it means.

The catalog uses flat folders by object family inside `catalog/`. Do not create
nested taxonomy folders under `catalog/abbs/` or `catalog/rbbs/`; the YAML
content already carries the object classification.
