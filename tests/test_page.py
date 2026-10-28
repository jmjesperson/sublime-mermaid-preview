import json
import pathlib
import unittest

from mermaid_preview_core.page import build_preview_html, script_json

REPO = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE = (
    "<title>{{TITLE}}</title>"
    "<script>window.MERMAID_PREVIEW = {source: {{SOURCE_JSON}}, config: {{CONFIG_JSON}}};</script>"
)
HOSTILE = 'A["</script><script>alert(1)</script>"] --> B["<!-- x --> & \' \"   \U0001F600 <br/>"]'


def embedded_source(page: str) -> str:
    return json.loads(page.split("source: ", 1)[1].split(", config:", 1)[0])


class ScriptJsonTest(unittest.TestCase):
    def test_script_json_has_no_raw_angle_or_amp(self):
        out = script_json(HOSTILE)
        for ch in "<>&":
            self.assertNotIn(ch, out)

    def test_script_json_round_trips(self):
        self.assertEqual(json.loads(script_json(HOSTILE)), HOSTILE)

    def test_script_json_escapes_line_separator(self):
        self.assertNotIn(" ", script_json(HOSTILE))


class BuildPreviewHtmlTest(unittest.TestCase):
    def test_page_inline_block_cannot_break_out(self):
        page = build_preview_html(TEMPLATE, HOSTILE, {"theme": "default"}, "t")
        block = page.split("window.MERMAID_PREVIEW", 1)[1].split("</script>", 1)[0]
        self.assertNotIn("<", block)
        self.assertEqual(embedded_source(page), HOSTILE)

    def test_title_is_html_escaped(self):
        page = build_preview_html(TEMPLATE, "graph TD", {}, "<arch> & co.mmd")
        self.assertIn("<title>&lt;arch&gt; &amp; co.mmd</title>", page)

    def test_config_embedded(self):
        page = build_preview_html(TEMPLATE, "graph TD", {"theme": "dark"}, "t")
        self.assertIn('"theme": "dark"', page)

    def test_placeholder_text_in_source_is_not_expanded(self):
        page = build_preview_html(TEMPLATE, "A[{{TITLE}}]", {}, "real title")
        self.assertEqual(embedded_source(page), "A[{{TITLE}}]")

    def test_real_template_contract(self):
        t = (REPO / "assets/preview.html").read_text(encoding="utf-8")
        for needle in ['<meta charset="utf-8">', "{{TITLE}}", "{{SOURCE_JSON}}", "{{CONFIG_JSON}}",
                       '<script src="mermaid.min.js"></script>', '<script src="preview.js"></script>',
                       'id="viewport"', 'id="stage"', 'id="toolbar"', 'id="fit"', 'id="zoom"']:
            self.assertIn(needle, t)
        self.assertLess(t.index("{{SOURCE_JSON}}"), t.index('src="preview.js"'))

    def test_real_template_has_content_security_policy(self):
        t = (REPO / "assets/preview.html").read_text(encoding="utf-8")
        self.assertIn('http-equiv="Content-Security-Policy"', t)
        policy = t.split('http-equiv="Content-Security-Policy" content="', 1)[1].split('"', 1)[0]
        self.assertIn("default-src 'none'", policy)
        self.assertIn("img-src data:", policy)
        self.assertNotIn("http", policy.replace("http-equiv", ""))
        self.assertLess(t.index("Content-Security-Policy"), t.index("<script"))

    def test_fixture_round_trips_through_page(self):
        src = (REPO / "tests/fixtures/large-flowchart.mmd").read_text(encoding="utf-8")
        page = build_preview_html(TEMPLATE, src, {}, "t")
        self.assertEqual(embedded_source(page), src)
