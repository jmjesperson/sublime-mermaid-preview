# MermaidPreview

A Sublime Text package that renders raw Mermaid from the current document (or selection) in the
browser, with zoom and drag, and optionally exports a PNG via `mmdc`. The design is in
`docs/superpowers/specs/2026-10-28-mermaid-preview-design.md`. Read it before changing behaviour.

## Scope

This file holds all the rules for this repo. Instructions from `CLAUDE.md` files in enclosing
folders cover other work and don't apply here. Still apply: absolute dates, never inventing
identifiers, and confirming before any outward-facing write (pushes, issues, releases).

## Rules

- **Runtime code is standard library only.** Sublime runs plugins on its embedded Python 3.14;
  pip and venvs aren't available. Don't add Python dependencies.
- **No venv and no third-party dev tools,** by Jonny's choice. Tests use stdlib `unittest`.
- **Write for Python 3.14.** Tests run on the system `python3` (3.15 at the time of writing), so
  don't use anything newer than 3.14.
- **`mermaid_preview_core/` never imports `sublime` or `sublime_plugin`.** All logic that can be
  tested lives there. `mermaid_preview.py` stays a thin Sublime layer.
- **Plugin `.py` files go only in the package root.** Import the core with relative imports.
- **Read package assets with `sublime.load_resource("Packages/MermaidPreview/...")`,** never
  filesystem paths. The package may be installed zipped.
- **Diagram text never leaves the machine.** No online renderers and no CDN at render time;
  JavaScript is vendored under `assets/`.
- **Test diagrams must be synthetic** and resemble no real system. The repo is public.
- **Never commit** `.pyc`, `__pycache__/`, `package-metadata.json`, `.sublime-workspace`.
- **No default key bindings.** The README shows how to add one in the User package.
- **Releases follow `RELEASING.md`.** Use GitHub Flow: change on a branch and open a PR with
  green CI. A semver tag on `main` with no `v` prefix is a release. Every release needs
  `messages/<version>.txt` and an entry in `messages.json`. Never move or delete a pushed tag.
- **Every user-visible change adds a line under `## [Unreleased]` in `CHANGELOG.md`** (Keep a
  Changelog sections: Added, Changed, Fixed, Removed). Use SemVer; before 1.0.0, any change to
  behaviour or settings bumps the minor version.

## Commands

```sh
python3 -m unittest discover tests            # unit tests, from the repo root
python3 scripts/preview_fixture.py [f.mmd]    # build and open a preview without Sublime (--no-open: print path only)
scripts/install.sh                            # symlink into Sublime's Packages/ as MermaidPreview
scripts/uninstall.sh                          # remove that symlink (refuses anything that isn't one)
```

Sublime reloads a plugin when its `.py` file is saved. Check `View → Show Console` for load
errors.

Reloading was checked on 2026-10-28 with Sublime build 4215 and the symlinked install:

- Saving `mermaid_preview.py` reloads it.
- Saving a file in `mermaid_preview_core/` does **not** reload it.
- After a core edit, save (or `touch`) `mermaid_preview.py`. Its top-of-file block drops the
  cached core modules.
- `subl --command <name>` runs a command in the running Sublime, which is useful for scripted
  checks.
- `mermaid_preview_browser` works this way; it acts on the active view.

## Layout

- `mermaid_preview.py`: the only Sublime-facing file. It defines the two `TextCommand`s, reads
  settings, assets and dialogs, and runs work in `set_timeout_async`.
- `mermaid_preview_core/`: pure logic, tested in `tests/`. Modules:
  - `selection.py`: which text to render.
  - `naming.py`: PNG name and page title.
  - `page.py`: builds the page and embeds the source safely. It's named `page.py`, not the
    spec's `html.py`, so it isn't confused with the stdlib `html` module it uses.
  - `preview_files.py`: writes the temp preview folder.
  - `config.py`: the effective Mermaid config.
  - `mmdc.py`: finds `mmdc`, builds its command and env, runs it, and writes the PNG atomically (keeping the file mode).
  - `export.py`: the two command workflows (`publish_preview`, `export_png`). Every failure comes back as a message, never raised, because they run off the UI thread.
- `assets/`: `preview.html` (the template), `preview.js` (render, zoom, pan, fit), and the
  vendored `mermaid.min.js`. The latter is Mermaid 12.2.0, the IIFE build, and must match the
  Mermaid bundled in `mmdc`. Its licence is in `assets/LICENSES.md`.
- `mermaid-config.json`: the default Mermaid config, shared by the preview and `mmdc -c`.

## Verifying without a screen

- **Page render:**
  `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --timeout=8000 --dump-dom file://<preview.html>`.
  Look for `data-rendered="true"`, or "Mermaid render error". A headless browser may hang if
  the same browser is already running normally; use a different one (2026-10-28).
- **`mmdc` under Sublime-like conditions:** run `run_mmdc` with `build_env({"PATH": "/usr/bin:/bin"}, ...)`.
- **Can't be automated:** zoom, drag, the save dialog, and error dialogs need a person.
