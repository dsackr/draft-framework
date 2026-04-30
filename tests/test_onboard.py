from __future__ import annotations

import unittest
from contextlib import redirect_stdout
from io import StringIO

from draft_table.onboard import ONBOARDING_BANNER, print_banner


class OnboardingTests(unittest.TestCase):
    def test_onboarding_banner_is_ascii(self) -> None:
        ONBOARDING_BANNER.encode("ascii")

    def test_print_banner_shows_draft_table(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            print_banner()

        text = output.getvalue()
        self.assertIn("DRAFT TABLE", text)
        self.assertIn("D R A F T", text)
        self.assertIn("Local Architecture Drafting Table", text)


if __name__ == "__main__":
    unittest.main()
