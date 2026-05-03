# Naming Conventions

## UID, Name, And Aliases

DRAFT first-class objects use an opaque generated `uid` for machine identity and
a human-readable `name` for conversation. Humans should not be asked to type or
remember UIDs.

The `uid` exists only so references remain stable when a team renames an object.
It uses this format:

```text
^[0-9A-HJKMNP-TV-Z]{10}-[0-9A-HJKMNP-TV-Z]{4}$
```

When an object is renamed, keep the `uid` unchanged and append the prior display
name to `aliases`. The Draftsman should resolve user references by exact name,
alias, file path, close name match, and only then UID.

## What Still Uses Local IDs

Some nested values still use local `id` fields because they are not first-class
objects. Examples include Requirement Group requirement IDs, Technology
Component configuration IDs, Drafting Session question IDs, provider IDs, and
company business pillar IDs.

These local IDs are scoped to the object or workspace section that contains
them. They are not global object identity.

## File Naming

File names should remain descriptive and stable enough for review:

- `catalog/technology-components/technology-os-microsoft-windows-server-2022.yaml`
- `catalog/host-standards/host-windows-server-2022-ec2.yaml`
- `catalog/software-deployment-patterns/software-deployment-student-health.yaml`

Changing a file name does not change object identity. The `uid` is the stable
reference.

## Repairing UID Problems

Validation reports missing, malformed, duplicate, or legacy object identity and
prints both a suggested UID and an explicit repair command.

To repair one file:

```bash
python3 framework/tools/repair_uids.py --workspace examples --file catalog/example.yaml --uid 01KQQ4Q027-ABCD
```

To repair a company workspace from inside the company repo:

```bash
python3 .draft/framework/tools/repair_uids.py --workspace .
```

The repair tool rewrites exact object references across the workspace. It does
not rewrite narrative prose.
