import sys

# Sublime reloads only this root file on save, not the core subpackage. Drop the core's
# cached modules so saving this file picks up core edits too.
for _name in [m for m in sys.modules if m.startswith(__package__ + ".mermaid_preview_core")]:
    del sys.modules[_name]

import hashlib  # noqa: E402
import os  # noqa: E402
import threading  # noqa: E402
import urllib.request  # noqa: E402
import webbrowser  # noqa: E402

import sublime  # noqa: E402
import sublime_plugin  # noqa: E402

from .mermaid_preview_core.config import ConfigError, load_effective_config  # noqa: E402
from .mermaid_preview_core.export import export_png, failure_report, publish_preview  # noqa: E402
from .mermaid_preview_core.mmdc import find_mmdc  # noqa: E402
from .mermaid_preview_core.naming import default_png_name, page_title, save_dialog_folder  # noqa: E402
from .mermaid_preview_core.selection import pick_source  # noqa: E402

# Built from the package's own name, so resources load even if the package is installed under
# another name (for example the repository name, after "Add Repository" with the GitHub URL).
PACKAGE = "Packages/{}/".format(__package__)
SETTINGS_FILE = "MermaidPreview.sublime-settings"
PANEL = "MermaidPreview"
MMDC_HELP = ("Set mmdc_path in Preferences → Package Settings → MermaidPreview. "
             "See the README section 'PNG export (optional)'.")

_assets = None  # (template, {name: text}, version), loaded once per plugin load


def _work_dir():
    """Per-user folder for the preview page and mmdc's config. Not the system temp folder,
    which other local users can write to on Linux (/tmp)."""
    return os.path.join(sublime.cache_path(), "MermaidPreview")


def _status(message):
    sublime.status_message("MermaidPreview: " + message)


def _error(message):
    sublime.set_timeout(lambda: sublime.error_message("MermaidPreview: " + message), 0)


def _load_assets():
    global _assets
    if _assets is None:
        template = sublime.load_resource(PACKAGE + "assets/preview.html")
        files = {name: sublime.load_resource(PACKAGE + "assets/" + name)
                 for name in ("preview.js", "mermaid.min.js")}
        digest = hashlib.sha1()
        for name in sorted(files):
            digest.update(files[name].encode("utf-8"))
        _assets = (template, files, digest.hexdigest())
    return _assets


def _effective_config(settings):
    default_json = sublime.load_resource(PACKAGE + "mermaid-config.json")
    return load_effective_config(default_json, settings.get("mermaid_config", ""))


def _source_from(view):
    """The text to render, or None after telling the user why there is nothing."""
    selected = [view.substr(region) for region in view.sel()]
    whole = view.substr(sublime.Region(0, view.size()))
    text, note = pick_source(selected, whole)
    if note:
        _status(note)
    return text


class MermaidPreviewBrowserCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        source = _source_from(self.view)
        if source is None:
            return
        title = page_title(self.view.file_name())
        settings = sublime.load_settings(SETTINGS_FILE)
        try:
            config = _effective_config(settings)
        except ConfigError as e:
            _error(str(e))
            return
        sublime.set_timeout_async(lambda: self._open(source, config, title), 0)

    def _open(self, source, config, title):
        # Loading and hashing the 5 MB Mermaid bundle happens here, off the UI thread.
        template, files, version = _load_assets()
        path, error = publish_preview(_work_dir(), template, files, version, source, config, title)
        if error:
            _error(error)
            return
        webbrowser.open("file://" + urllib.request.pathname2url(path))
        _status("opened preview in the browser")


class MermaidPreviewExportPngCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        source = _source_from(self.view)
        if source is None:
            return
        settings = sublime.load_settings(SETTINGS_FILE)
        try:
            config = _effective_config(settings)
        except ConfigError as e:
            _error(str(e))
            return
        mmdc, how = find_mmdc(settings.get("mmdc_path", ""))
        if mmdc is None:
            _error(how + "\n\n" + MMDC_HELP)
            return

        file_name = self.view.file_name()
        folder, note = save_dialog_folder(file_name, settings.get("save_folder", ""))
        if note:
            _status(note + "; using the default folder")

        def on_done(path):
            if path is None:
                return
            _status("rendering PNG…")
            # mmdc can take up to mmdc_timeout_seconds. Use a separate thread, not Sublime's
            # shared async thread, so other plugins are not blocked while it runs.
            threading.Thread(target=self._export, args=(path, source, config, mmdc, settings),
                             daemon=True).start()

        sublime.save_dialog(
            on_done,
            file_types=[("PNG", ["png"])],
            directory=folder,
            name=default_png_name(file_name),
            extension="png",
        )

    def _export(self, path, source, config, mmdc, settings):
        outcome = export_png(
            path, source, config, mmdc,
            settings.get("mmdc_scale", 8),
            settings.get("mmdc_background", "white"),
            settings.get("mmdc_timeout_seconds", 120),
            settings.get("node_path", ""),
            dict(os.environ),
            _work_dir(),
        )
        if outcome.ok:
            _status(outcome.message)
        else:
            self._show_failure(outcome.command, outcome.returncode, outcome.message)

    def _show_failure(self, cmd, returncode, message):
        window = self.view.window() or sublime.active_window()
        text = failure_report(cmd, returncode, message)

        def show():
            panel = window.create_output_panel(PANEL)
            panel.run_command("append", {"characters": text})
            window.run_command("show_panel", {"panel": "output." + PANEL})

        sublime.set_timeout(show, 0)
        _status("PNG export failed (see the MermaidPreview panel)")
