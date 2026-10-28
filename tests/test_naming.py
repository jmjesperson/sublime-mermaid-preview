import unittest

from mermaid_preview_core.naming import default_png_name, page_title


class DefaultPngNameTest(unittest.TestCase):
    def test_png_name_from_mmd(self):
        self.assertEqual(default_png_name("/a/b/architecture.mmd"), "architecture.png")

    def test_png_name_no_extension(self):
        self.assertEqual(default_png_name("/a/notes"), "notes.png")

    def test_png_name_unsaved(self):
        self.assertIsNone(default_png_name(None))

    def test_png_name_spaces_unicode(self):
        self.assertEqual(default_png_name("/x/My Diagram é.mmd"), "My Diagram é.png")

    def test_png_name_multi_dot(self):
        self.assertEqual(default_png_name("/x/sys.v2.mmd"), "sys.v2.png")


class PageTitleTest(unittest.TestCase):
    def test_title_saved(self):
        self.assertEqual(page_title("/a/<arch> & co.mmd"), "<arch> & co.mmd")

    def test_title_unsaved(self):
        self.assertEqual(page_title(None), "Mermaid preview")
