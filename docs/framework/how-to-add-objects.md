# How To Add Objects

## Start With The Right Question

The fastest way to add a new object correctly is to decide what kind of thing you are modeling before you write YAML.

Are you documenting:

- a vendor product
- a reusable architecture pattern
- a software distribution manifest
- a governance rule

Many mistakes happen because engineers skip that decision and start writing fields immediately.

## Add An ABB

1. Decide whether the object is an OS, hardware, software, or agent ABB.
2. Choose the correct ID pattern.
3. Create the YAML file in the matching `abbs/` subfolder.
4. Fill in the shared base fields.
5. Fill in the ABB-specific metadata such as vendor lifecycle, product version, and optional platform dependency.
6. Run validation.

ABBs should be specific. If you cannot name the product version clearly, you probably are not ready to create the object yet.

## Add A Host RBB

1. Create the file in `rbbs/host/`.
2. Reference the OS and hardware ABBs explicitly.
3. Add any agent ABBs or other internal components that physically live on the host.
4. Document `externalInteractions` for identity, logging, security, monitoring, patching, or other platforms.
5. Add `variants` and make sure each supported variant contains the architectural decisions needed to satisfy `aag.host`. The variant keys are open-ended. `ha` and `sa` are examples, not the only valid names.
6. Add `satisfiesAAG: [aag.host]`.
7. Run validation.

## Add A Service RBB

1. Create the file in the appropriate `rbbs/service/` subfolder.
2. Reference exactly one `hostRbb` and one `functionAbb`.
3. Add service-level external interactions that go beyond the host baseline.
4. Add the named variants that describe the service meaningfully. `ha` and `sa` are common examples, but keys such as `hp`, `sp`, `geo-redundant`, or `single-region` are also valid.
5. Document the decisions that describe scaling, health, secrets handling, and, for DBMS services, durability and protection.
6. Set `satisfiesAAG` to the correct AAG list.
7. Run validation.

## Add An AAG

1. Create the YAML file in `aags/`.
2. Define the `appliesTo` scope clearly.
3. Write requirements in the mechanism-based model.
4. For each requirement, explain what concern must be addressed, why it exists, which mechanisms are allowed, and how many satisfactions are required.
5. If the AAG extends another AAG, use `inherits`.

An AAG can target more than RBBs. The current catalog includes AAGs for RBBs, reference architectures, and software distribution manifests. The `appliesTo` block is what tells the validator which object type the AAG governs.

Keep the requirements focused on architecture outcomes rather than implementation trivia.

## Add A Reference Architecture

1. Create the file in `reference-architectures/`.
2. Choose a stable `ra.<pattern-slug>` ID.
3. Populate `requiredRBBs` with the reusable building blocks that define the pattern.
4. Include the required variants and roles.
5. Add `architecturalDecisions` that explain what the pattern assumes.
6. Make sure the file satisfies `aag.ra` by documenting `patternType`, required RBB roles, and pattern-level decisions.

An RA should be generic enough to guide many products, not just one.

## Add A Software Distribution Manifest

1. Create the file in `sdms/`.
2. Choose a product-focused `sdm.<product-slug>` ID.
3. Set `appliesPattern` if the product aligns with an existing RA.
4. Define any `scalingUnits` needed to express replicable or shared deployment boundaries.
5. Build the manifest out through `serviceGroups`, then place Product Services, RBBs, Appliance ABBs, and SaaS Services into the appropriate groups.
6. Use `intent` only when the architect is explicitly deviating from the Reference Architecture or when no Reference Architecture exists.
7. Add product-level `architecturalDecisions`, including availability requirement and data classification, so the SDM satisfies `aag.sdm`.

## Run The Tools

Validate locally:

```bash
python3 tools/validate.py
```

Regenerate the browser when needed:

```bash
python3 tools/generate_browser.py
```

## What The GitHub Actions Workflows Do

- `validate-catalog.yml` runs on pushes and pull requests to make sure the YAML parses, base fields are valid, RBBs satisfy their AAGs, and RA/SDM objects satisfy their applicable AAG checks.
- `generate-browser.yml` runs on pushes to `main` that change YAML content and regenerates `docs/index.html` so the published browser stays synchronized with the source data.

## How To Advance `catalogStatus`

`catalogStatus` should be treated as a maturity progression, not as a cosmetic label.

- `stub` means the object exists but is skeletal.
- `draft` means the structure and major fields are present and the object is ready for review.
- `approved` means the object is complete enough to be trusted by other engineers.

For RBBs, approved means the applicable AAG requirements are satisfied. For every object type, it also means the description, ownership, lifecycle, and relationships are clear enough that another engineer could use the object without guessing what it means.
