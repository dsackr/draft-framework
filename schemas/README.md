# Schema Notes

The catalog uses YAML documents rather than a compiled schema toolchain, so the executable schema lives in three places together: the object documentation, the seed examples, and `tools/validate.py`.

## Machine-Readable Decisions

Known `architecturalDecisions` keys must remain machine-readable. When `autoscaling`, `loadBalancer`, or `minNodes` are present, the validator enforces constrained values so the catalog can support future automation.
