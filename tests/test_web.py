from __future__ import annotations

import unittest

from draft_table.web import INDEX_HTML


class WebTests(unittest.TestCase):
    def test_chat_ui_replaces_thinking_on_errors(self) -> None:
        self.assertIn("replaceLastDraftsmanMessage", INDEX_HTML)
        self.assertIn("The Draftsman request failed", INDEX_HTML)
        self.assertIn("readJson(response)", INDEX_HTML)


if __name__ == "__main__":
    unittest.main()
