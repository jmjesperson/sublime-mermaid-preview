import json
import os
import tempfile
import unittest
from unittest import mock

from mermaid_preview_core.config import ConfigError, load_effective_config

DEFAULT = '{"theme": "default"}'


class LoadEffectiveConfigTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, text):
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def test_non_string_setting_is_a_config_error(self):
        for value in (42, ["a.json"], {"theme": "dark"}, True):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ConfigError, "mermaid_config must be a file path"):
                    load_effective_config(DEFAULT, value)

    def test_null_setting_gives_default(self):
        self.assertEqual(load_effective_config(DEFAULT, None), {"theme": "default"})

    def test_empty_path_gives_default(self):
        self.assertEqual(load_effective_config(DEFAULT, ""), {"theme": "default"})

    def test_user_file_replaces_default_entirely(self):
        path = self.write("c.json", json.dumps({"flowchart": {"curve": "basis"}}))
        self.assertEqual(load_effective_config(DEFAULT, path), {"flowchart": {"curve": "basis"}})

    def test_missing_file_names_path(self):
        path = os.path.join(self.dir, "missing.json")
        with self.assertRaises(ConfigError) as cm:
            load_effective_config(DEFAULT, path)
        self.assertIn(path, str(cm.exception))

    def test_invalid_json_names_path(self):
        path = self.write("bad.json", "{theme: dark")
        with self.assertRaises(ConfigError) as cm:
            load_effective_config(DEFAULT, path)
        self.assertIn(path, str(cm.exception))

    def test_non_object_names_path(self):
        path = self.write("list.json", "[1]")
        with self.assertRaises(ConfigError) as cm:
            load_effective_config(DEFAULT, path)
        self.assertIn(path, str(cm.exception))

    def test_tilde_expanded(self):
        self.write("c.json", '{"theme": "dark"}')
        with mock.patch.dict(os.environ, {"HOME": self.dir}):
            self.assertEqual(load_effective_config(DEFAULT, "~/c.json"), {"theme": "dark"})
