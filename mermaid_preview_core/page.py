"""Build the preview page from its template, embedding the diagram source safely."""

import html
import json
import re

_SCRIPT_ESCAPES = {
    "<": "\\u003c",
    ">": "\\u003e",
    "&": "\\u0026",
    " ": "\\u2028",
    " ": "\\u2029",
}
_PLACEHOLDER = re.compile(r"\{\{(TITLE|SOURCE_JSON|CONFIG_JSON)\}\}")


def script_json(value: object) -> str:
    """JSON for an inline <script>: no raw <, > or &, so nothing can close the script block."""
    encoded = json.dumps(value, ensure_ascii=False)
    return "".join(_SCRIPT_ESCAPES.get(ch, ch) for ch in encoded)


def build_preview_html(template: str, source: str, config: dict, title: str) -> str:
    """Fill the template's placeholders in one pass, so text inside values is never re-expanded."""
    values = {
        "TITLE": html.escape(title),
        "SOURCE_JSON": script_json(source),
        "CONFIG_JSON": script_json(config),
    }
    return _PLACEHOLDER.sub(lambda m: values[m.group(1)], template)
