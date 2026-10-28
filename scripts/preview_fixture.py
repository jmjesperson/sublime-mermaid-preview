"""Dev helper: build the preview page for a .mmd file and open it, without Sublime.

Usage: python3 scripts/preview_fixture.py [path.mmd] [--no-open]
"""

import json
import os
import sys
import tempfile
import time
import urllib.request
import webbrowser

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from mermaid_preview_core.naming import page_title  # noqa: E402
from mermaid_preview_core.page import build_preview_html  # noqa: E402
from mermaid_preview_core.preview_files import write_preview  # noqa: E402


def read(rel: str) -> str:
    with open(os.path.join(REPO, rel), encoding="utf-8") as f:
        return f.read()


def main(argv: list[str]) -> str:
    args = [a for a in argv if a != "--no-open"]
    source_path = args[0] if args else os.path.join(REPO, "tests", "fixtures", "large-flowchart.mmd")
    with open(source_path, encoding="utf-8") as f:
        source = f.read()
    config_path = os.path.join(REPO, "mermaid-config.json")
    config = json.loads(read("mermaid-config.json")) if os.path.exists(config_path) else {"theme": "default"}
    page = build_preview_html(read("assets/preview.html"), source, config, page_title(source_path))
    assets = {"preview.js": read("assets/preview.js"), "mermaid.min.js": read("assets/mermaid.min.js")}
    out_dir = os.path.join(tempfile.gettempdir(), "MermaidPreview-dev")
    path = write_preview(out_dir, page, assets, "dev-" + str(time.time()))
    if "--no-open" not in argv:
        webbrowser.open("file://" + urllib.request.pathname2url(path))
    print(path)
    return path


if __name__ == "__main__":
    main(sys.argv[1:])
