from __future__ import annotations

import textwrap
import unittest

from framework.tools import check_release_notes


class ReleaseNotesTests(unittest.TestCase):
    def test_current_release_notes_are_valid(self) -> None:
        self.assertEqual(check_release_notes.validate(), [])

    def test_governed_change_requires_changelog_update(self) -> None:
        entries = check_release_notes.parse_changelog(
            textwrap.dedent(
                """
            ## 0.4.0 - 2026-04-30
            ### Compatibility Impact
            No migration required.
            ### Added
            None.
            ### Changed
            Updated docs.
            ### Fixed
            None.
            ### Migration Notes
            No workspace migration required.
            """
            )
        )

        errors = check_release_notes.validate_changed_files(
            ["framework/docs/overview.md"],
            check_release_notes.Version(0, 4, 0),
            entries,
            None,
        )

        self.assertIn("CHANGELOG.md was not updated", "\n".join(errors))

    def test_patch_release_rejects_contract_changes(self) -> None:
        entries = check_release_notes.parse_changelog(
            textwrap.dedent(
                """
            ## 0.4.1 - 2026-05-01
            ### Compatibility Impact
            No migration required.
            ### Added
            None.
            ### Changed
            None.
            ### Fixed
            Fixed validator wording.
            ### Migration Notes
            No workspace migration required.
            """
            )
        )

        errors = check_release_notes.validate_changed_files(
            ["framework/schemas/host-standard.schema.yaml", "CHANGELOG.md"],
            check_release_notes.Version(0, 4, 1),
            entries,
            check_release_notes.Version(0, 4, 0),
        )

        self.assertIn("Patch releases must not include", "\n".join(errors))

    def test_changelog_update_for_unreleased_change_requires_quality_notes(self) -> None:
        entries = check_release_notes.parse_changelog(
            textwrap.dedent(
                """
            ## Unreleased
            No notes yet.

            ## 0.4.0 - 2026-04-30
            ### Compatibility Impact
            No migration required.
            ### Added
            None.
            ### Changed
            Updated docs.
            ### Fixed
            None.
            ### Migration Notes
            No workspace migration required.
            """
            )
        )

        errors = check_release_notes.validate_changed_files(
            ["framework/docs/overview.md", "CHANGELOG.md"],
            check_release_notes.Version(0, 4, 0),
            entries,
            None,
        )

        self.assertIn("Unreleased needs a meaningful Compatibility Impact", "\n".join(errors))


if __name__ == "__main__":
    unittest.main()
