import unittest

from mermaid_preview_core.selection import pick_source


class PickSourceTest(unittest.TestCase):
    def test_no_selection_uses_whole_text(self):
        self.assertEqual(pick_source([""], "graph TD\nA-->B"), ("graph TD\nA-->B", None))

    def test_empty_selection_list_uses_whole_text(self):
        self.assertEqual(pick_source([], "graph TD"), ("graph TD", None))

    def test_single_selection_used_verbatim(self):
        self.assertEqual(pick_source(["A-->B"], "whole"), ("A-->B", None))

    def test_first_of_several_selections_with_note(self):
        text, note = pick_source(["", "first", "second"], "whole")
        self.assertEqual(text, "first")
        self.assertIn("first", note)

    def test_whitespace_only_is_nothing(self):
        text, note = pick_source([""], "  \n\t ")
        self.assertIsNone(text)
        self.assertIsNotNone(note)

    def test_whitespace_selection_is_nothing_not_whole_doc(self):
        text, note = pick_source(["   "], "graph TD")
        self.assertIsNone(text)
        self.assertIsNotNone(note)

    def test_text_not_stripped(self):
        self.assertEqual(pick_source([], "\ngraph TD\n")[0], "\ngraph TD\n")
