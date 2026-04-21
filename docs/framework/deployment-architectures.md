# Deployment Architectures

## What A DA Is

A Deployment Architecture, or DA, is a declaration that a specific product is deployed according to a particular pattern.

Unlike an RA, which is generic, a DA is tied to a named product. It answers the question “what does this product deploy?” rather than “what does this class of solution usually require?”

## What `deployedRBBs` Means

The defining field in a DA is `deployedRBBs`. Each entry identifies:

- the RBB
- the named variant used
- the instance name that gives the deployed role a product-specific identity

A DA does not break those RBBs open and redraw their internal ABBs. The no-grandchildren rule exists to keep deployment views readable. The variant field is open-ended for the same reason it is open-ended on RBBs and RAs. `ha` and `sa` are common values, but a DA can also select variants such as `hp`, `sp`, `geo-redundant`, or other descriptive keys defined by the referenced RBB.

## What `appliesPattern` Means

The `appliesPattern` field tells the reader which RA the deployment claims to follow.

This field is metadata only. It is useful because it says whether the product is aligned to a recognized pattern, but it is not itself a deployed object and should not be rendered as a node in a deployment diagram.

## Why A DA Only Declares Additional External Interactions

A DA only declares external interactions that are not already covered by its component RBBs.

If the host RBB already says it interacts with Active Directory, centralized logging, and patch management, the DA should not repeat those interactions. The DA only adds product-specific interactions that are outside the reusable baseline captured in the RBBs.

This keeps deployment declarations focused on what is unique to the product instead of turning them into copies of lower-level objects.

## Long-Term Placement

The v1 catalog contains example DAs in this central repository because the framework needs real examples.

Long term, that is not the target operating model. Product-specific deployment declarations belong closest to the product that owns them, which usually means the product repository. The central catalog should define reusable building blocks and reference patterns. Product repos should eventually own the declarations that map those standards to live product estates.

## FAQ

### Does every product need a DA?

In the long run, yes, if the product has meaningful architecture that needs to be reviewed, supported, or governed. A missing DA should usually be treated as a gap to close, not as proof that the framework does not apply.

### What if my product does not fit any existing RA?

Do not force the product into an obviously wrong pattern. Treat that as a signal. Either the product is a legitimate exception that needs to be documented clearly, or the catalog is missing an RA that should exist.
