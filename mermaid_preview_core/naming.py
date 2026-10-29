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


def png_dialog_folder(file_name: str | None, setting: object) -> tuple[str | None, str | None]:
    """Folder for the PNG save dialog, and a note to show if the png_folder setting was ignored.

    A png_folder value wins over the document's folder. An empty, missing or null value, or a
    value that is not an existing folder, gives the document's folder (None if unsaved).
    """
    fallback = os.path.dirname(file_name) if file_name else None
    if setting is None or (isinstance(setting, str) and not setting.strip()):
        return fallback, None
    if not isinstance(setting, str):
        return fallback, "png_folder must be a folder path (a string), got {!r}".format(setting)
    folder = os.path.expanduser(setting.strip())
    if not os.path.isabs(folder):
        return fallback, "png_folder must be a full path, got {!r}".format(setting)
    if not os.path.isdir(folder):
        return fallback, "png_folder not found: {}".format(folder)
    return folder, None
