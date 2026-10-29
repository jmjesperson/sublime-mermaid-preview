# MermaidPreview

MermaidPreview is a Sublime Text package. It shows the raw Mermaid text from the current
document (or the selection) as a diagram in the browser, with zoom and drag. It can also export
a PNG with `mmdc`, which is optional. The design is in
`docs/superpowers/specs/2026-10-28-mermaid-preview-design.md`. Read it before you change how the
package behaves.

## Scope

This file has all the rules for this repository. If this repository is inside another folder
that has its own `CLAUDE.md`, those instructions are for other work and do not apply here. Some
general rules still apply:

- Always write full dates, for example 2026-10-28.
- Never invent names or identifiers.
- Ask before any action that other people can see, such as a push, an issue, or a release.

## Rules

- **Runtime code uses only the Python standard library.** Sublime runs plugins on its own
  Python 3.14. pip and virtual environments are not available there. Do not add Python
  dependencies.
- **Do not use a virtual environment or third-party development tools.** This is a project
  decision. Tests use the standard library `unittest`.
- **Write code for Python 3.14.** The tests run on the system `python3`, which was 3.15 on
  2026-10-28. Do not use features that are newer than 3.14.
- **`mermaid_preview_core/` never imports `sublime` or `sublime_plugin`.** Put all logic that
  can be tested there. Keep `mermaid_preview.py` as a small Sublime layer.
- **Plugin `.py` files go only in the package root folder.** Import the core with relative
  imports.
- **Read package files with `sublime.load_resource(PACKAGE + "...")`.** `PACKAGE` in
  `mermaid_preview.py` is built from `__package__`, so it is correct for any install name. Do
  not write `Packages/MermaidPreview/` in code. Do not use file system paths. The package can be
  installed as a zip file.
- **Diagram text never leaves the computer.** Do not use online renderers. Do not load anything
  from a CDN when the diagram renders. JavaScript files are copied into `assets/`.
- **Test diagrams must be invented.** They must not look like any real system, because the
  repository is public.
- **Never commit** `.pyc` files, `__pycache__/`, `package-metadata.json`, or
  `.sublime-workspace` files.
- **Do not add default key bindings.** The README shows users how to add one.
- **Follow `RELEASING.md` for releases.** Use GitHub Flow: make each change on a branch, and
  open a pull request. CI must pass. A release is a version tag on `main`, without a `v` (for
  example `0.2.0`). Every release needs `messages/<version>.txt` and a line for it in
  `messages.json`. Never move or delete a tag after it is pushed.
- **For every change that users can see, add a line under `## [Unreleased]` in
  `CHANGELOG.md`.** Use the Keep a Changelog sections: Added, Changed, Fixed, Removed. Use
  Semantic Versioning. Before version 1.0.0, any change to behaviour or settings needs a new
  minor version.
- **Every setting is described in three places:** `sublime-package.json` (the JSON Schema, the
  source of truth), the comments in `MermaidPreview.sublime-settings`, and the README section
  "Settings". When you add or change a setting, change all three.
  `tests/test_settings_docs.py` checks that the keys and the defaults match.
- **Write documentation in plain English.** Many readers speak English as a second language.
  Use short sentences and common words. Do not use contractions or idioms. Do not use personal
  names in the documentation. Write "the maintainer", "users" or "contributors".

## Commands

```sh
python3 -m unittest discover tests            # unit tests, from the repository root
python3 scripts/preview_fixture.py [f.mmd]    # make and open a preview without Sublime (--no-open: only print the path)
scripts/dev.sh on|zip [REF]|off|status        # switch Sublime between this clone and the Package Control copy
```

When a plugin `.py` file is saved, Sublime reloads it. Look in `View → Show Console` for load
errors.

## Which copy does Sublime use?

The maintainer's normal copy of the package is the Package Control copy, the same as for every
user. That copy runs only released code. Changes in this repository are visible in Sublime only
after `scripts/dev.sh on` and a restart of Sublime.

**Run `scripts/dev.sh status` before you test anything in Sublime.** Also run it when someone
says that a change is not visible. It checks the files on disk and prints one of these results:

- `DEV symlink -> <path>`, with the branch and commit. Changes in that clone are live. Check that
  the path is this clone, and that the branch is the expected branch.
- `PACKAGE CONTROL copy, version X`. Changes in this repository are **not** visible. To test
  them, run `scripts/dev.sh on`, and ask the user to restart Sublime.
- `TEST ZIP built by dev.sh from <ref>`. This is a fixed copy, made by `dev.sh zip`. It does not
  include changes made after it was built. It has a `package-metadata.json` with version
  `9999.0.0`. Without this file, Package Control replaces the zip with the newest release each
  time Sublime starts (seen on 2026-10-29). The high version also stops automatic upgrades.
- `warning: Package Control replaced the test zip`. Run `scripts/dev.sh zip` again.
- `RESTART NEEDED`. Sublime started before the last switch, so it may still use the old copy.

Never assume that Sublime uses the development copy. When the work in Sublime is finished, ask
the user if you should run `scripts/dev.sh off`.

Package Control's settings must include `"ignore_vcs_packages": ["MermaidPreview"]`. This was
set on the maintainer's computer on 2026-10-28. Without it, Package Control's automatic upgrade
runs `git pull` in this clone while the clone is linked into Sublime. `dev.sh on` shows a
warning if the setting is missing.

## Reloading

This was checked on 2026-10-28 with Sublime build 4215 and the linked development copy:

- When `mermaid_preview.py` is saved, Sublime reloads it.
- When a file in `mermaid_preview_core/` is saved, Sublime does **not** reload it.
- After you change a core file, save (or `touch`) `mermaid_preview.py`. The code at the top of
  that file removes the old core modules from memory, so they load again.
- `subl --command <name>` runs a command in the open Sublime. This is useful for checks from a
  script.
- `mermaid_preview_browser` works with `subl --command`. It uses the active view.

## Layout

- `mermaid_preview.py`: the only file that uses the Sublime API. It defines the two
  `TextCommand`s. It reads settings and package files, shows dialogs, and runs work with
  `set_timeout_async`.
- `mermaid_preview_core/`: logic without Sublime, tested in `tests/`. Modules:
  - `selection.py`: chooses which text to render.
  - `naming.py`: the PNG file name and the page title.
  - `page.py`: builds the page and puts the source into it safely. Its name is `page.py`, not
    `html.py` as in the design, so that it is not confused with the standard `html` module
    that it uses.
  - `preview_files.py`: writes the preview folder.
  - `config.py`: the Mermaid config that is used.
  - `mmdc.py`: finds `mmdc`, builds its command and environment, runs it, and writes the PNG
    safely (a failed export does not change an existing file, and the file permissions stay
    the same).
  - `export.py`: the steps of the two commands (`publish_preview`, `export_png`). Every error is
    returned as a message and never raised, because these functions do not run on the UI
    thread.
- `assets/`: `preview.html` (the page template), `preview.js` (render, zoom, move, fit), and
  `mermaid.min.js`. `mermaid.min.js` is Mermaid 12.2.0, the IIFE build. It must be the same
  version as the Mermaid inside `mmdc`. Its licence is in `assets/LICENSES.md`.
- `sublime-package.json`: the JSON Schema for the settings. LSP-json uses it in the User
  settings file.
- `mermaid-config.json`: the default Mermaid config. The preview and `mmdc -c` both use it.
- `repository.json`: tells Package Control the package name and to install from version tags.
  Users add its URL with **Add Repository**. Do not move or rename it.
- `scripts/dev.sh`: switches Sublime between this clone and the Package Control copy.

## Checks without a screen

- **Page render:**
  `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --timeout=8000 --dump-dom file://<preview.html>`.
  Look for `data-rendered="true"` or "Mermaid render error". A headless browser can stop
  responding if the same browser is already open as a normal window. In that case, use a
  different browser (seen on 2026-10-28).
- **`mmdc` in conditions like Sublime's:** run `run_mmdc` with
  `build_env({"PATH": "/usr/bin:/bin"}, ...)`.
- **Cannot be automated:** zoom, drag, the save dialog, and error dialogs. A person must test
  these.
