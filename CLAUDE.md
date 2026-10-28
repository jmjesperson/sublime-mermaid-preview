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
scripts/dev.sh on|zip [REF]|off|status        # switch Sublime between this clone and the Package Control copy
```

Sublime reloads a plugin when its `.py` file is saved. Check `View → Show Console` for load
errors.

## Which copy is Sublime running?

Jonny's normal copy is the Package Control install, the same as every user's. It runs released
code only. Edits in this repo reach Sublime only after `scripts/dev.sh on` and a Sublime
restart.

**Run `scripts/dev.sh status` before any manual check in Sublime,** and whenever Jonny says a
change doesn't show up. It reads the files on disk and prints one of:

- `DEV symlink -> <path>`, plus the branch and commit. Edits in that clone are live. Check it's
  this clone and the branch you expect.
- `PACKAGE CONTROL copy, version X`. Edits in this repo are **not** visible. To try them, run
  `scripts/dev.sh on` and ask Jonny to restart Sublime.
- `TEST ZIP built by dev.sh`. A frozen build from `dev.sh zip`. Edits since then aren't in it.
- `RESTART NEEDED`. Sublime started before the last switch and may still run the old copy.

Never assume the dev copy. When work in Sublime is finished, ask Jonny whether to run
`scripts/dev.sh off`.

`ignore_vcs_packages` in Package Control's settings must list `MermaidPreview` (set on
2026-10-28). Otherwise Package Control's auto-upgrade runs `git pull` in this clone while it's
symlinked. `dev.sh on` warns if the setting is missing.

## Reloading

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
