import os
import stat
import tempfile
import unittest

from mermaid_preview_core.mmdc import (
    MmdcResult,
    build_env,
    build_mmdc_command,
    find_mmdc,
    run_mmdc,
    write_atomically,
)

PNG = b"\x89PNG\r\n\x1a\n"


class TempDirTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def script(self, name, body):
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write("#!/bin/sh\n" + body + "\n")
        os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)
        return path


def never_called(_name):
    raise AssertionError("which() must not be consulted when mmdc_path is set")


class FindMmdcTest(TempDirTest):
    def test_setting_executable_returned(self):
        exe = self.script("mmdc", "exit 0")
        self.assertEqual(find_mmdc(exe, which=never_called, home=self.dir)[0], exe)

    def test_setting_missing_file_no_fallback(self):
        path, how = find_mmdc(os.path.join(self.dir, "nope"), which=never_called, home=self.dir)
        self.assertIsNone(path)
        self.assertIn("mmdc_path", how)

    def test_setting_directory_no_fallback(self):
        path, how = find_mmdc(self.dir, which=never_called, home=self.dir)
        self.assertIsNone(path)
        self.assertIn("mmdc_path", how)

    def test_setting_not_executable_no_fallback(self):
        plain = os.path.join(self.dir, "mmdc")
        open(plain, "w").close()
        path, how = find_mmdc(plain, which=never_called, home=self.dir)
        self.assertIsNone(path)
        self.assertIn("mmdc_path", how)

    def test_empty_setting_uses_which(self):
        self.assertEqual(find_mmdc("", which=lambda _: "/x/mmdc", home=self.dir)[0], "/x/mmdc")

    def test_empty_setting_falls_back_to_mise_shim(self):
        shims = os.path.join(self.dir, ".local", "share", "mise", "shims")
        os.makedirs(shims)
        shim = os.path.join(shims, "mmdc")
        with open(shim, "w") as f:
            f.write("#!/bin/sh\n")
        os.chmod(shim, 0o755)
        self.assertEqual(find_mmdc("", which=lambda _: None, home=self.dir, system_dirs=())[0], shim)

    def test_system_dir_checked_before_mise_shim(self):
        sysdir = os.path.join(self.dir, "brew")
        os.makedirs(sysdir)
        exe = os.path.join(sysdir, "mmdc")
        with open(exe, "w") as f:
            f.write("#!/bin/sh\n")
        os.chmod(exe, 0o755)
        self.assertEqual(find_mmdc("", which=lambda _: None, home=self.dir, system_dirs=(sysdir,))[0], exe)

    def test_nothing_found(self):
        path, how = find_mmdc("", which=lambda _: None, home=self.dir, system_dirs=())
        self.assertIsNone(path)
        self.assertIn("not found", how)


class BuildCommandTest(unittest.TestCase):
    def test_exact_command(self):
        self.assertEqual(
            build_mmdc_command("/x/mmdc", 8, "white", "/t/c.json"),
            ["/x/mmdc", "-i", "-", "-o", "-", "-e", "png", "-s", "8", "-b", "white", "-c", "/t/c.json", "-q"],
        )


class BuildEnvTest(unittest.TestCase):
    def test_mmdc_dir_first(self):
        env = build_env({"PATH": "/usr/bin", "HOME": "/h"}, "/m/bin/mmdc", "")
        self.assertEqual(env["PATH"], "/m/bin" + os.pathsep + "/usr/bin")
        self.assertEqual(env["HOME"], "/h")

    def test_node_path_before_mmdc_dir(self):
        env = build_env({"PATH": "/usr/bin"}, "/m/bin/mmdc", "/n/bin")
        self.assertEqual(env["PATH"], os.pathsep.join(["/n/bin", "/m/bin", "/usr/bin"]))

    def test_input_not_mutated(self):
        base = {"PATH": "/usr/bin"}
        build_env(base, "/m/bin/mmdc", "/n/bin")
        self.assertEqual(base, {"PATH": "/usr/bin"})


class RunMmdcTest(TempDirTest):
    def run_script(self, body, source="graph TD", timeout=10.0):
        exe = self.script("fake-mmdc", body)
        return run_mmdc([exe], source, dict(os.environ), self.dir, timeout)

    def test_png_on_stdout_is_ok(self):
        result = self.run_script("printf '\\211PNG\\r\\n\\032\\nDATA'")
        self.assertIsInstance(result, MmdcResult)
        self.assertTrue(result.ok)
        self.assertEqual(result.png, PNG + b"DATA")

    def test_exit_zero_empty_stdout_is_failure(self):
        result = self.run_script("exit 0")
        self.assertFalse(result.ok)

    def test_nonzero_exit_reports_stderr(self):
        result = self.run_script("echo 'Parse error on line 2' >&2; exit 1")
        self.assertFalse(result.ok)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Parse error on line 2", result.message)

    def test_timeout(self):
        result = self.run_script("sleep 5", timeout=0.5)
        self.assertFalse(result.ok)
        self.assertIn("timed out", result.message)

    def test_source_sent_utf8_on_stdin(self):
        out = os.path.join(self.dir, "stdin.txt")
        self.run_script("cat > '%s'" % out, source="A[é] --> B")
        with open(out, encoding="utf-8") as f:
            self.assertEqual(f.read(), "A[é] --> B")

    def test_runs_in_given_cwd(self):
        result = self.run_script("pwd >&2; exit 1")
        self.assertIn(os.path.realpath(self.dir), os.path.realpath(result.message.strip()))


class WriteAtomicallyTest(TempDirTest):
    def test_writes_new_file(self):
        path = os.path.join(self.dir, "out.png")
        write_atomically(path, b"abc")
        with open(path, "rb") as f:
            self.assertEqual(f.read(), b"abc")

    def test_replaces_existing_file(self):
        path = os.path.join(self.dir, "out.png")
        write_atomically(path, b"old")
        write_atomically(path, b"new")
        with open(path, "rb") as f:
            self.assertEqual(f.read(), b"new")

    def test_missing_directory_raises_and_leaves_nothing(self):
        path = os.path.join(self.dir, "nope", "out.png")
        with self.assertRaises(OSError):
            write_atomically(path, b"abc")
        self.assertEqual(os.listdir(self.dir), [])


class WriteAtomicallyModeTest(TempDirTest):
    def test_new_file_gets_umask_default_mode(self):
        old = os.umask(0o022)
        try:
            path = os.path.join(self.dir, "new.png")
            write_atomically(path, b"abc")
        finally:
            os.umask(old)
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o644)

    def test_existing_file_mode_preserved(self):
        path = os.path.join(self.dir, "old.png")
        with open(path, "wb") as f:
            f.write(b"old")
        os.chmod(path, 0o664)
        write_atomically(path, b"new")
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o664)
