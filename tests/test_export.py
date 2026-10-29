import os
import stat
import tempfile
import unittest

from mermaid_preview_core.export import export_png, failure_report, publish_preview

PNG = b"\x89PNG\r\n\x1a\n"


class ExportTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name
        self.work = os.path.join(self.dir, "work")
        self.target = os.path.join(self.dir, "out.png")

    def tearDown(self):
        self._tmp.cleanup()

    def fake_mmdc(self, body):
        path = os.path.join(self.dir, "mmdc")
        with open(path, "w", encoding="utf-8") as f:
            f.write("#!/bin/sh\n" + body + "\n")
        os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)
        return path

    def export(self, mmdc, timeout=10, target=None):
        return export_png(target or self.target, "graph TD", {"theme": "default"}, mmdc,
                          8, "white", timeout, "", dict(os.environ), self.work)


class ExportPngTest(ExportTestBase):
    def test_success_writes_png(self):
        outcome = self.export(self.fake_mmdc("printf '\\211PNG\\r\\n\\032\\nX'"))
        self.assertTrue(outcome.ok)
        with open(self.target, "rb") as f:
            self.assertEqual(f.read(), PNG + b"X")

    def test_bad_timeout_setting_is_reported_not_raised(self):
        outcome = self.export(self.fake_mmdc("exit 0"), timeout="abc")
        self.assertFalse(outcome.ok)
        self.assertIn("mmdc_timeout_seconds", outcome.message)

    def test_unwritable_work_dir_is_reported_not_raised(self):
        with open(self.work, "w") as f:
            f.write("a file where the work folder should be")
        outcome = self.export(self.fake_mmdc("exit 0"))
        self.assertFalse(outcome.ok)
        self.assertIn(self.work, outcome.message)

    def test_unwritable_target_is_reported_not_raised(self):
        outcome = self.export(self.fake_mmdc("printf '\\211PNG\\r\\n\\032\\nX'"),
                              target=os.path.join(self.dir, "missing", "out.png"))
        self.assertFalse(outcome.ok)
        self.assertIn("could not write", outcome.message)

    def test_mmdc_failure_leaves_target_untouched(self):
        with open(self.target, "wb") as f:
            f.write(b"old")
        outcome = self.export(self.fake_mmdc("echo boom >&2; exit 1"))
        self.assertFalse(outcome.ok)
        self.assertIn("boom", outcome.message)
        with open(self.target, "rb") as f:
            self.assertEqual(f.read(), b"old")


class PublishPreviewTest(ExportTestBase):
    def test_returns_page_path(self):
        path, error = publish_preview(self.work, "{{TITLE}}", {}, "v1", "graph TD", {}, "t")
        self.assertIsNone(error)
        self.assertTrue(os.path.isfile(path))

    def test_unwritable_work_dir_is_reported_not_raised(self):
        with open(self.work, "w") as f:
            f.write("blocker")
        path, error = publish_preview(self.work, "{{TITLE}}", {}, "v1", "graph TD", {}, "t")
        self.assertIsNone(path)
        self.assertIn(self.work, error)


class FailureReportTest(unittest.TestCase):
    def test_includes_command_exit_code_and_message(self):
        text = failure_report(["mmdc", "-i", "-"], 1, "Parse error on line 2")
        self.assertIn("Command: mmdc -i -\n", text)
        self.assertIn("Exit code: 1\n", text)
        self.assertIn("Parse error on line 2", text)
        self.assertIn("The existing file, if any, was not changed.", text)

    def test_timeout_has_no_exit_code_line(self):
        text = failure_report(["mmdc"], None, "mmdc timed out after 120 seconds")
        self.assertNotIn("Exit code", text)
        self.assertIn("mmdc timed out after 120 seconds", text)

    def test_failure_before_running_has_no_command_line(self):
        text = failure_report([], None, "mmdc_timeout_seconds must be a number, got 'x'")
        self.assertNotIn("Command:", text)
        self.assertNotIn("Exit code", text)
