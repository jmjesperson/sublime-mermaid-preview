import os
import tempfile
import unittest

from mermaid_preview_core.naming import default_png_name, page_title, png_dialog_folder


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


class PngDialogFolderTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.folder = self._tmp.name
        self.addCleanup(self._tmp.cleanup)

    def test_empty_setting_uses_document_folder(self):
        for setting in (None, "", "   "):
            with self.subTest(setting=setting):
                self.assertEqual(png_dialog_folder("/a/b/x.mmd", setting), ("/a/b", None))

    def test_empty_setting_unsaved_document_gives_no_folder(self):
        self.assertEqual(png_dialog_folder(None, ""), (None, None))

    def test_setting_wins_over_document_folder(self):
        self.assertEqual(png_dialog_folder("/a/b/x.mmd", self.folder), (self.folder, None))

    def test_setting_used_for_unsaved_document(self):
        self.assertEqual(png_dialog_folder(None, self.folder), (self.folder, None))

    def test_tilde_is_expanded(self):
        self.assertEqual(png_dialog_folder(None, "~"), (os.path.expanduser("~"), None))

    def test_missing_folder_falls_back_with_note(self):
        missing = os.path.join(self.folder, "nope")
        folder, note = png_dialog_folder("/a/b/x.mmd", missing)
        self.assertEqual(folder, "/a/b")
        self.assertIn(missing, note)
        self.assertIn("not found", note)

    def test_file_instead_of_folder_falls_back_with_note(self):
        path = os.path.join(self.folder, "f.txt")
        open(path, "w").close()
        folder, note = png_dialog_folder(None, path)
        self.assertIsNone(folder)
        self.assertIn("not found", note)

    def test_relative_path_falls_back_with_note(self):
        folder, note = png_dialog_folder("/a/b/x.mmd", "Downloads")
        self.assertEqual(folder, "/a/b")
        self.assertIn("full path", note)

    def test_non_string_falls_back_with_note(self):
        for setting in (42, ["~"], True):
            with self.subTest(setting=setting):
                folder, note = png_dialog_folder("/a/b/x.mmd", setting)
                self.assertEqual(folder, "/a/b")
                self.assertIn("png_folder", note)
