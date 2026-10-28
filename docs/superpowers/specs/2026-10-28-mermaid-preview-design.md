# MermaidPreview — design

Date: 2026-10-28
Status: approved by the maintainer on 2026-10-28

## Intent

The maintainer regularly works with raw Mermaid text, often large flowcharts of 25+ nodes with
subgraphs, `<br/>` labels and three edge styles (`-->`, `-.->`, `==>`). Today he has to leave
Sublime Text to see it: paste into an online editor, or run
`pbpaste | mmdc -i - -o diagram.png -s 8`. Online editors also mean pasting private diagrams
into a third-party site.

MermaidPreview is a Sublime Text package that renders the Mermaid in the current document
without leaving the editor, in two ways:

1. **Preview in browser.** Opens the diagram in the default browser with zoom and drag. Needs no
   installs.
2. **Export PNG.** Writes a high-resolution PNG via `mmdc`, which is an optional prerequisite.

Its model is the MarkdownPreview package the maintainer already uses: render to HTML, open the browser,
keep the package light.

## Goals

- Preview the current document or selection in the browser with one Command Palette command.
- The preview looks like the plain Mermaid rendering the maintainer already likes: the default theme,
  HTML labels and an inline error display (see "Look and feel").
- Zoom (wheel or pinch, toward the cursor), drag to pan, and a fit-to-screen control. Opens fit
  to screen.
- Export a PNG equivalent to `mmdc -s 8`, with a save dialog every time.
- Installs locally on a Mac without Package Control, and is structured so that publishing
  to Package Control later adds files without restructuring.

## Non-goals (first version)

- Markdown input. **Raw Mermaid only**: no ```` ```mermaid ```` fence extraction, decided by the maintainer.
- Live reload while typing. Each render opens a new browser tab, decided by the maintainer.
- A download button in the browser page. This is a planned add-on once the core works, decided
  by the maintainer. When it comes, SVG only (see "Later").
- PNG export from the browser.
- Publishing to Package Control. That's a later step.
- Syntax highlighting. The existing `Mermaid` package on Package Control
  (https://github.com/SublimeText/Mermaid) provides it, and this package must work alongside it.
- Windows or Linux testing. Code should stay portable (standard library only) but is verified on
  macOS only.

## Anti-goals (failure even if it works)

- **Diagram text sent to any online service.** No mermaid.ink, no Kroki, no CDN at render time.
  The preview works offline.
- **Node required for the preview.** Only PNG export may need Node or `mmdc`.
- **Silent failure or a stale image.** Every failure shows a visible message that says what to
  do.
- **A heavy package.** It has no Python dependencies, no binaries, and nothing for Package
  Control to install.

## Constraints and facts (checked 2026-10-28)

- **Sublime Text build 4215** runs plugins on an embedded **Python 3.14**
  (`plugin_host-3.14`; the legacy 3.3 host is deprecated). A package selects 3.14 with a
  `.python-version` file containing `3.14` in the package root. Without that file it gets 3.3.
  Source: https://www.sublimetext.com/docs/api_environments.html
- Plugins can't use venvs or pip. **Runtime code is standard library only.** The maintainer decided
  against a venv for development as well.
- Plugin `.py` files load only from the package root, as `<PackageName>.<module>`. Subpackages
  imported from a root plugin are allowed.
- **Package Control expectations** (to respect now, so publishing later is easy):
  - The repo root is the package root.
  - The name has no "Sublime" and no period.
  - Releases are semver tags.
  - No `.pyc` files or `package-metadata.json` committed.
  - `messages.json` is valid JSON if present.
  - No default key bindings that override Sublime's defaults.

  Sources: https://packagecontrol.io/docs/submitting_a_package,
  https://github.com/packagecontrol/st_package_reviewer/wiki/Package-checks
- **The reference look** the maintainer wants the preview to match:
  - Mermaid configured with only `mermaid.initialize({ startOnLoad: false, theme: 'default' })`.
  - No other config, so HTML labels stay at Mermaid's default (on).
  - On error, "Mermaid render error: <message>" in red, then the source in a `<pre>`.
  - That renderer used Mermaid 11.17.2 and had no zoom or pan.
- **`mmdc`** (mermaid-cli) 12.0.0 bundles Mermaid **12.2.0**. It's typically installed in a Node
  version manager's folder or a Homebrew prefix.
  - Sublime launched from the Dock often doesn't have that directory on `PATH`.
  - `mmdc` is a Node script (`#!/usr/bin/env node`), so even an absolute `mmdc` path fails unless
    `node` is also findable.
- `mmdc` reads a Mermaid config JSON (`-c`), CSS (`-C`) and Puppeteer config (`-p`) from files.
  Scale (`-s`), background (`-b`), theme (`-t`) and format are command-line flags only.
- This is its own git repo, published at https://github.com/jmjesperson/sublime-mermaid-preview.

## How it works

### Commands

Commands are exposed through `Default.sublime-commands` (Command Palette). No default key
bindings ship; the README shows how to add one in the User package.

| Palette caption | Command | Behaviour |
|---|---|---|
| `MermaidPreview: Preview in Browser` | `mermaid_preview_browser` | Renders in the browser |
| `MermaidPreview: Export PNG…` | `mermaid_preview_export_png` | Renders to a PNG via `mmdc` |

Both commands are `TextCommand`s and work in any view, whatever its syntax.

### Input (both commands)

- If any selection is non-empty, render **only the selected text**, decided by the maintainer. With
  several non-empty selections, render the first and show a status-bar note that only the first
  was used (*design choice*).
- Otherwise render the **whole document**.
- If the text is empty or whitespace only, show a status-bar message and stop.
- The text is passed to Mermaid as-is: no fence stripping and no rewriting.

### Preview in browser

1. Build one self-contained HTML page from a template:
   - the bundled Mermaid library (inlined or copied alongside, see below);
   - the pan-and-zoom code;
   - the effective Mermaid config;
   - the diagram source.
2. Write it to `<sublime.cache_path()>/MermaidPreview/preview.html`, overwritten on every render,
   decided by the maintainer. It goes in the per-user cache, not the system temp folder, which is shared on
   Linux (`/tmp`). Files never pile up next to the source.
3. Open it with Python's `webbrowser.open` as a `file://` URL. Each render opens a new tab.
   - On macOS, Sublime's bundled `webbrowser` asks the system for the **http** handler, so the
     page opens in the default browser and not in whatever app owns
     `.html`.
   - Don't use Sublime's `open_url`; its handling of `file://` is unverified.

Page behaviour:

- Mermaid renders the source with `mermaid.render(...)` and the config from
  "Shared Mermaid config".
- The diagram opens fit to screen (*design choice*).
- **Zoom** is mouse wheel or trackpad pinch, centred on the cursor. **Pan** is click-drag. A
  visible **Fit** button resets the view (*design choice*: also the `0` key).
- **Zoom and pan transform only the view** (a CSS transform on a wrapper, or the SVG `viewBox`),
  never the SVG content. This keeps the later Download SVG add-on simple.
- **On a render error**, the page shows "Mermaid render error: <message>" in red, then the source
  in a `<pre>`, as in the reference look.
- The page title is the source file's name, or "Mermaid preview" for an unsaved buffer.

**Embedding the source safely.** Put the diagram text into the page as a JSON string literal
inside a `<script>` block:

1. Encode it with `json.dumps(source)`.
2. Then replace each `<`, `>` and `&` with the JSON escapes `\u003c`, `\u003e` and `\u0026`
   (backslash, `u`, four hex digits).

Labels containing `</script>` or `<br/>` then can't break out. Never put the text in as raw HTML.
A unit test asserts that the generated script block contains no `</` and that the source
round-trips exactly.

**Getting the bundled JS into the page.** Don't inline it:

- Read assets with `sublime.load_resource("Packages/MermaidPreview/...")`, not filesystem paths,
  because the package may be installed zipped as a `.sublime-package`. Its 16 MB size limit is
  fine.
- Write `mermaid.min.js` and `preview.js` **next to `preview.html`** in the preview folder, and load
  them with `<script src="...">`. Rewrite them only when the package version changes (*design choice*).
- Inlining is ruled out because the Mermaid 12.2.0 bundle contains `<!--` sequences. Under the
  HTML parser's script rules, those can swallow the rest of the page (found by the reviewer).
- Vendor the classic **IIFE build** `mermaid.min.js`, which sets `globalThis.mermaid`. Do not
  vendor the ESM build (`mermaid.esm.min.mjs`). It lazy-loads chunks as modules, and Chromium
  browsers block module scripts from `file://` pages.

**Encoding.** The page starts with `<meta charset="utf-8">`, and every file is written with
`encoding="utf-8"`. A `file://` page gets no charset header, and both Mermaid and diagram labels
contain non-ASCII text.

### Export PNG

1. Find `mmdc` (see "Finding mmdc"). If it's missing, show an error dialog that names the setting
   and links to the README setup section, then stop.
2. Open `sublime.save_dialog` every time, decided by the maintainer.
   - Name pre-filled with the source file's base name plus `.png` when the view has a file name.
     No pre-filled name for an unsaved buffer.
   - Starting directory is the source file's directory. For an unsaved buffer, Sublime's default
     (*design choice*).
   - If the user cancels, do nothing.
3. Run, off the UI thread (`sublime.set_timeout_async`):

   ```text
   <mmdc> -i - -o - -e png -s <mmdc_scale> -b <mmdc_background> -c <effective-config.json> -q
   ```

   - The source goes in on stdin, matching the maintainer's `pbpaste | mmdc -i -` habit.
   - Timeout: 120 s (*design choice*).
   - **Write the PNG to stdout:** run with `-o - -e png` and capture it. Only on exit 0, write the
     bytes to a temp file in the target directory and `os.replace` it onto the chosen path. A
     failed run never touches an existing file, so a stale image can't happen. The reviewer
     verified that `mmdc -i - -o - -e png` works.
   - **Pass an explicit `cwd`,** the per-user preview folder. Some Node version managers choose
     the Node version from a `.nvmrc` or `.node-version` in the working directory, which could
     select a Node that has no `mmdc`.
   - The subprocess `PATH` is the normal one with **the directory containing `mmdc` added in
     front**, so `#!/usr/bin/env node` finds the `node` installed next to it. A `node_path` setting overrides this
     when `node` is somewhere else.
4. On success, the status bar shows `MermaidPreview: wrote <path>`.
5. On failure (non-zero exit or timeout), an output panel `MermaidPreview` shows the command, the
   exit code and `mmdc`'s stderr. Any existing file at the chosen path is left untouched.

### Finding mmdc

1. If the `mmdc_path` setting is set (an absolute path, with `~` expanded), use it.
2. Otherwise use `shutil.which("mmdc")` on Sublime's `PATH`.
3. Otherwise, as a convenience, search well-known locations: `/opt/homebrew/bin`,
   `/usr/local/bin`, and mise's Node shims and installs (`~/.local/share/mise/shims`). *Design choice:*
   check the shims directory rather than globbing version folders, because version folders
   change on every Node upgrade.
4. If nothing is found, show the "not found" error from Export PNG step 1.

### Shared Mermaid config

- A package resource, `mermaid-config.json`, holds the default Mermaid config:
  `{"theme": "default"}`, matching the reference look. `startOnLoad: false` is browser-only and added by
  the page, not stored in the file.
- The `mermaid_config` setting (a path, empty by default) lets the user point at their own JSON
  file, which replaces the default.
- **The same effective config goes to both renderers:** the page passes it to
  `mermaid.initialize`, and Export PNG writes it to a temp file and passes it to `mmdc -c`. Then
  the preview and the PNG agree on theme and layout settings.

### Settings (`MermaidPreview.sublime-settings`)

| Key | Default | Purpose |
|---|---|---|
| `mmdc_path` | `""` | Absolute path to `mmdc`. Empty means search, as in "Finding mmdc". |
| `node_path` | `""` | Directory containing `node`, if it isn't next to `mmdc`. |
| `mmdc_scale` | `8` | `-s` scale, matching the maintainer's habit. |
| `mmdc_background` | `"white"` | `-b` background. |
| `mmdc_timeout_seconds` | `120` | Subprocess timeout. |
| `mermaid_config` | `""` | Path to a user Mermaid config JSON. Empty means the bundled default. |

Also include a `Main.sublime-menu` entry under Preferences → Package Settings → MermaidPreview
that opens the settings with Sublime's `edit_settings` command (*design choice*; it's standard practice).

### Look and feel

- Use Mermaid's default theme on a white page with a small toolbar (Fit, plus the zoom
  percentage), styled minimally.
- HTML labels stay on, as in the reference look, so `<br/>` labels render the way the maintainer is used to.
- **The bundled Mermaid version is 12.2.0,** the same version the maintainer's `mmdc` 12.0.0 uses, so
  the preview and the exported PNG render the same way. This was decided by the maintainer over matching
  the reference look's 11.17.2. Together with the shared config, the preview is "what the PNG will look
  like."
- When the maintainer upgrades `mmdc`, the bundled version can fall behind. The README documents how to
  check `mmdc`'s Mermaid version and update `assets/mermaid.min.js` to match (*design choice*: no
  automatic version check in the plugin).

## Structure

```text
sublime-mermaid-preview/           ← repo root = package root; symlinked as Packages/MermaidPreview
  .python-version                  3.14
  .gitignore                       *.pyc, __pycache__/, .DS_Store
  .gitattributes                   export-ignore for tests/, docs/, scripts/, CLAUDE.md (ready for publishing)
  CLAUDE.md                        build rules for Claude Code sessions (exists already)
  mermaid_preview.py               Sublime layer: commands, settings, dialogs, threads (imports sublime)
  mermaid_preview_core/            pure logic, never imports sublime or sublime_plugin
    __init__.py
    html.py                        build_preview_html(source, config, assets, title) -> str
    mmdc.py                        find_mmdc(...), build_mmdc_command(...), subprocess env
    naming.py                      default_png_name(file_name) -> str | None
    selection.py                   pick_source(selected_texts, whole_text) -> (text, note)
  assets/
    preview.html                   page template
    preview.js                     page logic: render, error display, pan and zoom, fit
    mermaid.min.js                 vendored Mermaid 12.2.0, IIFE build (matches mmdc)
    LICENSES.md                    licences of vendored JS
  mermaid-config.json              default Mermaid config
  MermaidPreview.sublime-settings
  Default.sublime-commands
  Main.sublime-menu
  tests/                           stdlib unittest, run outside Sublime
    __init__.py
    test_html.py  test_mmdc.py  test_naming.py  test_selection.py
    fixtures/large-flowchart.mmd   synthetic, ~25 nodes, subgraphs, <br/>, all 3 edge styles
  scripts/
    dev.sh                         switch Sublime between this clone (symlink or built zip) and the
                                   Package Control copy (replaced install.sh/uninstall.sh on 2026-10-28)
  README.md                        install, usage, optional mmdc setup, key binding example
  LICENSE                          MIT (design choice; matters only at publishing)
```

Notes:

- **The package name is `MermaidPreview`**, which isn't taken on Package Control (checked
  2026-10-28; the existing packages are `Mermaid`, `Formatter` and `MarkdownPreviewEnhanced`).
  The repo folder name doesn't matter, because the symlink carries the package name. Hard-coded
  resource paths must use `Packages/MermaidPreview/`.
- `mermaid_preview.py` imports the core with relative imports (`from .mermaid_preview_core import html`).
  **Core modules import each other relatively too** (`from . import naming`), never as
  `MermaidPreview.mermaid_preview_core...`. Sublime loads the core as
  `MermaidPreview.mermaid_preview_core`, while the tests import it as the top-level
  `mermaid_preview_core`, and only relative imports work under both names.
- **Sublime reloads only root plugin files on save, not subpackages** (unverified). Edits to the
  core may need a restart, or a reload step when the plugin loads. The builder confirms this
  early and documents the result in `CLAUDE.md`.
- **Verify early that a symlinked package loads and reloads correctly** (unverified; the docs
  don't cover it). This should be one of the first steps of the plan, before building much on it.
- **Pan and zoom:** either hand-write about 100 lines in `preview.js`, or vendor a small
  permissively licensed library (for example `@panzoom/panzoom` 4.6.2, MIT). Either way it's
  vendored, with no CDN. That's the builder's choice.
- **The test fixture must be synthetic**, with no resemblance to any real system. The repo is
  public.

## Testing

- **Unit tests** cover everything in `mermaid_preview_core/`, using `python3 -m unittest discover tests`
  from the repo root with the system Python (3.15 today). There are no third-party tools and no
  venv, decided by the maintainer. The code must also run on Sublime's 3.14, so avoid 3.15-only features.
  Key cases:
  - **Escaping:** a source containing `</script>`, quotes, `<br/>` and non-ASCII text round-trips
    exactly into the page.
  - **Selection:** none, one, several, and whitespace-only.
  - **PNG naming:** `architecture.mmd` gives `architecture.png`, an unsaved buffer gives `None`,
    and a name with no extension gets `.png` added.
  - **mmdc command:** built correctly from settings, and the env `PATH` has the `mmdc` directory
    in front.
  - **find_mmdc order:** checked with a fake filesystem or tmp dirs.
- **Manual acceptance in Sublime**, using the fixture and a real agent-produced diagram:
  1. Preview a whole document and a selection.
  2. Zoom toward the cursor, drag, and use Fit.
  3. Preview a diagram with a syntax error and see the red error with the source.
  4. Export a PNG to a chosen path. It matches `pbpaste | mmdc -i - -o x.png -s 8` output, and its
     layout matches the browser preview of the same source.
  5. Run Export PNG with `mmdc_path` wrong and get a clear error that points to the README.
  6. Cancel the save dialog and nothing happens.
  7. Go offline and the preview still works.
- **Integration tests** with the UnitTesting package (https://github.com/SublimeText/UnitTesting)
  are optional, and deferred to publishing time.

## Implementation plan bookends

- **First:** `CLAUDE.md` already exists, hand-written on 2026-10-28, holding the build rules from
  this design. Follow it from the first line of code.
- **Last step of the plan:** once the package works, refresh `CLAUDE.md` so it matches the code
  as built, decided by the maintainer. Run `/init` against the filled-out project or update the file by
  hand. Keep the hand-written rules, and remove the "don't exist yet" note on the scripts.

## Later (not in the first version)

- **Download SVG** button in the preview. It serializes the rendered SVG, so the result is the
  full diagram regardless of zoom. PNG from the browser is deliberately excluded: HTML labels
  commonly make the canvas export fail (not tested here), and `mmdc` already covers PNG.
- **Publishing:** done on 2026-10-28 as release `0.1.0`, through `repository.json` and
  **Add Repository** rather than the default channel (see the decisions log). CI runs the
  Package Control reviewer, and `messages.json` has an install message. `RELEASING.md` keeps
  the channel submission steps in case that changes. If it does, Package Control asks authors
  to improve an existing package before adding another, so first consider offering this as a
  contribution to `SublimeText/Mermaid`.

## Decisions log

These were decided by the maintainer on 2026-10-28:

- Raw Mermaid only.
- A selection renders only the selection.
- Always ask where to save the PNG.
- The preview HTML lives in a per-user cache folder and is overwritten on each render.
- A new tab per render, with no live reload.
- `mmdc` is optional, with setup instructions.
- Zoom and drag are included; the download button is a later add-on.
- Local install first; publish later.
- No venv.
- The preview bundles the same Mermaid version as `mmdc` (12.2.0).
- The last plan step refreshes `CLAUDE.md`.
- Users install by adding `repository.json` through **Package Control: Add Repository**. The
  package isn't submitted to Package Control's default channel.
- The maintainer uses the same Package Control install day to day, and switches to a local copy
  (`scripts/dev.sh`) only to develop and to test before a release.

## Left to the builder

- Hand-written versus vendored pan and zoom.
- Toolbar styling.
- The exact wording of status and error messages.
- The internal function signatures beyond those named above.
