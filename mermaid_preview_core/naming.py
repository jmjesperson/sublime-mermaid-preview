"""Names derived from the source file: the default PNG name and the preview page title."""

import os

UNSAVED_TITLE = "Mermaid preview"


def default_png_name(file_name: str | None) -> str | None:
    """Base name for the PNG save dialog, or None for an unsaved buffer."""
    if not file_name:
        return None
    stem, _ = os.path.splitext(os.path.basename(file_name))
    return stem + ".png"


def page_title(file_name: str | None) -> str:
    """Unescaped page title: the source file's base name, or a generic title."""
    return os.path.basename(file_name) if file_name else UNSAVED_TITLE
