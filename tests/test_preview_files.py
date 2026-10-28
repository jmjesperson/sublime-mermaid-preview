import os
import tempfile
import unittest
from pathlib import Path

from mermaid_preview_core.preview_files import write_preview


class WritePreviewTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def test_writes_page_and_assets_utf8(self):
        p = write_preview(self.dir, "<p>é</p>", {"preview.js": "// é"}, "v1")
        self.assertEqual(p, os.path.join(self.dir, "preview.html"))
        self.assertEqual(Path(p).read_text(encoding="utf-8"), "<p>é</p>")
        self.assertEqual((Path(self.dir) / "preview.js").read_text(encoding="utf-8"), "// é")

    def test_page_overwritten_every_time(self):
        write_preview(self.dir, "one", {}, "v1")
        p = write_preview(self.dir, "two", {}, "v1")
        self.assertEqual(Path(p).read_text(encoding="utf-8"), "two")

    def test_assets_skipped_when_version_unchanged(self):
        write_preview(self.dir, "x", {"preview.js": "orig"}, "v1")
        (Path(self.dir) / "preview.js").write_text("tampered", encoding="utf-8")
        write_preview(self.dir, "x", {"preview.js": "orig"}, "v1")
        self.assertEqual((Path(self.dir) / "preview.js").read_text(encoding="utf-8"), "tampered")

    def test_assets_rewritten_when_version_changes(self):
        write_preview(self.dir, "x", {"preview.js": "orig"}, "v1")
        (Path(self.dir) / "preview.js").write_text("tampered", encoding="utf-8")
        write_preview(self.dir, "x", {"preview.js": "orig"}, "v2")
        self.assertEqual((Path(self.dir) / "preview.js").read_text(encoding="utf-8"), "orig")

    def test_creates_missing_directory(self):
        nested = os.path.join(self.dir, "a", "b")
        p = write_preview(nested, "x", {}, "v1")
        self.assertTrue(os.path.isfile(p))

    def test_missing_asset_rewritten_even_when_version_unchanged(self):
        write_preview(self.dir, "x", {"mermaid.min.js": "lib", "preview.js": "js"}, "v1")
        os.remove(os.path.join(self.dir, "mermaid.min.js"))
        write_preview(self.dir, "x", {"mermaid.min.js": "lib", "preview.js": "js"}, "v1")
        self.assertEqual((Path(self.dir) / "mermaid.min.js").read_text(encoding="utf-8"), "lib")
