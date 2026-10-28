"""The two command workflows, with every failure returned as a message instead of raised.

The Sublime layer runs these off the UI thread, where an exception would only reach the
console. Returning the failure lets it be shown to the user.
"""

import json
import os
from dataclasses import dataclass

from .mmdc import build_env, build_mmdc_command, run_mmdc, write_atomically
from .page import build_preview_html
from .preview_files import write_preview


@dataclass
class ExportOutcome:
    ok: bool
    message: str
    command: list[str]
    returncode: int | None


def publish_preview(work_dir: str, template: str, assets: dict[str, str], assets_version: str,
                    source: str, config: dict, title: str) -> tuple[str | None, str | None]:
    """Write the preview page; return (page_path, None) or (None, error message)."""
    page = build_preview_html(template, source, config, title)
    try:
        return write_preview(work_dir, page, assets, assets_version), None
    except OSError as e:
        return None, "could not write the preview to {}: {}".format(work_dir, e)


def export_png(path: str, source: str, config: dict, mmdc: str, scale: int, background: str,
               timeout: object, node_path: str, base_env: dict[str, str], work_dir: str) -> ExportOutcome:
    """Render source to a PNG at path with mmdc. path is replaced only on success."""
    try:
        timeout_seconds = float(timeout)
    except (TypeError, ValueError):
        return ExportOutcome(False, "mmdc_timeout_seconds must be a number, got {!r}".format(timeout), [], None)

    config_path = os.path.join(work_dir, "mmdc-config.json")
    try:
        os.makedirs(work_dir, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f)
    except OSError as e:
        return ExportOutcome(False, "could not write the mmdc config in {}: {}".format(work_dir, e), [], None)

    cmd = build_mmdc_command(mmdc, scale, background, config_path)
    result = run_mmdc(cmd, source, build_env(base_env, mmdc, node_path), work_dir, timeout_seconds)
    if not result.ok:
        return ExportOutcome(False, result.message, cmd, result.returncode)
    try:
        write_atomically(path, result.png)
    except OSError as e:
        return ExportOutcome(False, "could not write {}: {}".format(path, e), cmd, 0)
    return ExportOutcome(True, "wrote " + path, cmd, 0)
