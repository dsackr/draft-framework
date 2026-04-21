# Schema Notes

The catalog uses YAML documents rather than a compiled schema toolchain, so the executable schema lives in three places together: the object documentation, the seed examples, and `tools/validate.py`.

## Variant Keys

`variants` is an open-ended map. The keys are descriptive names chosen by the author of the object. `ha` and `sa` remain common examples, but they are not the only valid options.

Valid examples include:

- `ha`
- `sa`
- `hp`
- `sp`
- `geo-redundant`
- `single-region`

The validator does not require specific variant names. It requires that at least one named variant exists and that each documented variant carries an `architecturalDecisions` map.

## Machine-Readable Decisions

Known `architecturalDecisions` keys must remain machine-readable. When `autoscaling`, `loadBalancer`, or `minNodes` are present, the validator enforces constrained values so the catalog can support future automation.
