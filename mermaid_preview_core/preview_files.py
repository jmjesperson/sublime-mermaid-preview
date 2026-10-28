"""Write the preview page and its assets into the preview folder."""

import os

_VERSION_MARKER = ".assets-version"


def _write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _read_text(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def write_preview(directory: str, page_html: str, assets: dict[str, str], assets_version: str) -> str:
    """Write preview.html every time; rewrite assets when assets_version changes or one is missing."""
    os.makedirs(directory, exist_ok=True)
    marker = os.path.join(directory, _VERSION_MARKER)
    missing = any(not os.path.isfile(os.path.join(directory, name)) for name in assets)
    if missing or _read_text(marker) != assets_version:
        for name, text in assets.items():
            _write_text(os.path.join(directory, name), text)
        _write_text(marker, assets_version)
    page_path = os.path.join(directory, "preview.html")
    _write_text(page_path, page_html)
    return page_path
