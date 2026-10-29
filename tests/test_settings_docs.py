"""The settings are described in three places. sublime-package.json (the JSON Schema) is the
source of truth. The default settings file and the README must match it."""

import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_TYPES = {"string": str, "number": (int, float), "integer": int, "null": type(None)}


def read(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return f.read()


def strip_comments(text):
    """Remove // and /* */ comments, as Sublime does, but not inside strings."""
    out, i, in_string = [], 0, False
    while i < len(text):
        c = text[i]
        if in_string:
            out.append(c)
            if c == "\\":
                out.append(text[i + 1])
                i += 1
            elif c == '"':
                in_string = False
        elif c == '"':
            in_string = True
            out.append(c)
        elif text.startswith("//", i):
            i = text.find("\n", i)
            if i == -1:
                break
            continue
        elif text.startswith("/*", i):
            i = text.index("*/", i) + 2
            continue
        else:
            out.append(c)
        i += 1
    return "".join(out)


def schema_properties():
    entries = json.loads(read("sublime-package.json"))["contributions"]["settings"]
    [entry] = [e for e in entries if "/MermaidPreview.sublime-settings" in e.get("file_patterns", [])]
    return entry["schema"]["properties"]


class StripCommentsTest(unittest.TestCase):
    def test_removes_comments_but_not_slashes_in_strings(self):
        text = '// a\n{ /* b */ "u": "http://x/*y*/", // c\n "q": "\\"//" }'
        self.assertEqual(json.loads(strip_comments(text)), {"u": "http://x/*y*/", "q": '"//'})


class SettingsDocsTest(unittest.TestCase):
    def setUp(self):
        self.schema = schema_properties()
        self.settings_text = read("MermaidPreview.sublime-settings")
        self.defaults = json.loads(strip_comments(self.settings_text))

    def test_schema_has_a_description_and_default_for_every_setting(self):
        for key, prop in self.schema.items():
            with self.subTest(key=key):
                self.assertTrue(prop.get("description"))
                self.assertIn("default", prop)

    def test_settings_file_has_the_schema_keys_and_defaults(self):
        self.assertEqual(list(self.defaults), list(self.schema))
        for key, value in self.defaults.items():
            with self.subTest(key=key):
                self.assertEqual(value, self.schema[key]["default"])
                types = self.schema[key]["type"]
                types = types if isinstance(types, list) else [types]
                self.assertIsInstance(value, tuple(JSON_TYPES[t] for t in types))

    def test_every_setting_has_a_comment_above_it(self):
        lines = self.settings_text.splitlines()
        for key in self.schema:
            with self.subTest(key=key):
                [n] = [n for n, line in enumerate(lines) if line.strip().startswith('"{}"'.format(key))]
                self.assertTrue(lines[n - 1].strip().startswith("//"))

    def test_readme_has_a_section_with_the_default_for_every_setting(self):
        readme = read("README.md")
        headings = re.findall(r"^### `([a-z_]+)`$", readme, re.M)
        self.assertEqual(headings, list(self.schema))
        for key, prop in self.schema.items():
            with self.subTest(key=key):
                section = readme.split("### `{}`".format(key), 1)[1].split("\n#", 1)[0]
                self.assertIn("**Default:** `{}`".format(json.dumps(prop["default"])), section)
