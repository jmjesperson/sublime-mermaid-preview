# MermaidPreview

MermaidPreview is a Sublime Text 4 package that renders the raw Mermaid in the current document
(or the current selection) without leaving the editor:

- **Preview in Browser** opens the diagram in your default browser, where you can zoom and drag
  around. It needs nothing installed, works offline, and your diagram text never leaves your
  machine.
- **Export PNG…** writes a high-resolution PNG with `mmdc` (mermaid-cli). This part is optional
  and needs Node; see [PNG export (optional)](#png-export-optional).

## Install

**From GitHub, through Package Control:**

1. Run **Package Control: Add Repository** with
   `https://github.com/jmjesperson/sublime-mermaid-preview`.
2. Run **Package Control: Install Package** and choose `MermaidPreview`.

Package Control installs the newest release tag and keeps it updated.

**For development (local):**

```sh
scripts/install.sh      # symlink this folder into Sublime's Packages/ as MermaidPreview
scripts/uninstall.sh    # remove that symlink (it never deletes a real folder)
```

Sublime picks the package up without a restart.

## Usage

Open the Command Palette (`⌘⇧P`) and run one of these:

- `MermaidPreview: Preview in Browser`
- `MermaidPreview: Export PNG…`

What gets rendered:

- **Selection:** if you've selected text, only the selection renders. With several selections,
  only the first renders.
- **Otherwise:** the whole document renders.
- **Raw Mermaid only:** the text must be Mermaid itself, such as `flowchart TB ...`. Markdown
  with ```` ```mermaid ```` fences isn't supported.

In the browser:

- **Zoom** with the scroll wheel or a trackpad pinch. It zooms toward the pointer.
- **Pan** by dragging.
- **Fit** (or the `0` key) fits the whole diagram on screen.
- Each preview opens a new tab. The page is a file in Sublime's cache folder that gets
  overwritten on every preview, so nothing is written next to your source.
- If the diagram has a syntax error, the page shows Mermaid's error in red, then your source.

Export PNG always asks where to save. When the document has a file name, the dialog starts in
its folder with the PNG name filled in. A failed export never replaces an existing PNG; the
error appears in the `MermaidPreview` output panel.

## PNG export (optional)

Export PNG runs `mmdc`, the Mermaid command-line renderer. It needs Node.js, plus a headless
Chromium that mermaid-cli downloads on install (a few hundred MB). The preview doesn't need any
of this.

1. Install Node.js, from https://nodejs.org or through a version manager such as mise.
2. Run `npm install -g @mermaid-js/mermaid-cli`.
3. Check that it works: `echo 'graph TD; A-->B' | mmdc -i - -o /tmp/test.png`.

**How MermaidPreview finds `mmdc`:**

1. The `mmdc_path` setting, if set. If that path isn't an executable file, export stops with an
   error. It does not search elsewhere.
2. Otherwise, Sublime's `PATH`.
3. Otherwise, `/opt/homebrew/bin/mmdc`, `/usr/local/bin/mmdc` and
   `~/.local/share/mise/shims/mmdc`.

**Why this matters on macOS:** Sublime started from the Dock or Finder doesn't see your shell's
`PATH`, so a `mmdc` that works in Terminal can be "not found" in Sublime. Set `mmdc_path` to the
output of `which mmdc`.

`mmdc` is a Node script (`#!/usr/bin/env node`), so `node` must be findable too.
MermaidPreview puts the folder containing `mmdc` at the front of `PATH`, which covers the usual
installs. If `node` lives somewhere else, set `node_path` to its folder.

## Security

- **The preview page can't reach the network.** It has a Content-Security-Policy: scripts load
  only from the local files, and images only inline. A diagram that embeds a remote image (for
  example `<img src="https://…">` in a label) can't make a request.
- **Mermaid's `securityLevel` stays at its default, `"strict"`.** A diagram can't change it.
  Your `mermaid_config` file can, but **don't set `"loose"` or `"antiscript"`** if you preview
  diagrams from untrusted sources: they let a diagram run script or click handlers, in the
  browser and in `mmdc`'s headless Chromium.
- **Files are written to Sublime's per-user cache folder,** never to a shared temp folder.

## Settings

Open **Preferences → Package Settings → MermaidPreview → Settings**, or run
`Preferences: MermaidPreview Settings` from the Command Palette.

| Setting | Default | Meaning |
|---|---|---|
| `mmdc_path` | `""` | Absolute path to `mmdc`. Empty means search, as described above. |
| `node_path` | `""` | Folder containing `node`, if it isn't next to `mmdc`. |
| `mmdc_scale` | `8` | Scale factor (`mmdc -s`). Higher values give a sharper, larger PNG. |
| `mmdc_background` | `"white"` | PNG background (`mmdc -b`), such as `"transparent"` or `"#F0F0F0"`. |
| `mmdc_timeout_seconds` | `120` | How long to wait for `mmdc`. |
| `mermaid_config` | `""` | Path to your own Mermaid config JSON. Empty means the bundled `{"theme": "default"}`. |

The same Mermaid config goes to both the browser preview and `mmdc -c`, so the two render the
same way. A user config replaces the default; it isn't merged with it.

## Matching Mermaid versions

The preview bundles **Mermaid 12.2.0**, the version that mermaid-cli 12.0.0 uses, so the
preview and the PNG agree. After you upgrade mermaid-cli, check which Mermaid it bundles:

```sh
grep -m1 '"version"' "$(npm root -g)/@mermaid-js/mermaid-cli/node_modules/mermaid/package.json"
```

If the version differs, update the bundled copy:

1. Copy `"$(npm root -g)/@mermaid-js/mermaid-cli/node_modules/mermaid/dist/mermaid.min.js"` to
   `assets/mermaid.min.js`. Use this file, the classic build. The `.esm` build doesn't load from
   a `file://` page.
2. Update the version in `assets/LICENSES.md` and in this section.
3. Save `mermaid_preview.py`, or restart Sublime, so the new file is copied on the next preview.

## Key binding (example)

No key bindings ship with the package. To add one, open **Preferences → Key Bindings** and add
an entry like this to the User file. This is an example only; pick any free key.

```json
{ "keys": ["ctrl+alt+m"], "command": "mermaid_preview_browser" }
```

## Development

```sh
python3 -m unittest discover tests                     # unit tests (standard library only)
python3 scripts/preview_fixture.py [file.mmd]          # build and open a preview without Sublime
```

- Sublime reloads `mermaid_preview.py` when you save it, but not the files in
  `mermaid_preview_core/`.
- After editing the core, save `mermaid_preview.py` (or `touch` it) to reload everything.
- `subl --command mermaid_preview_browser` runs the preview from a shell.

CI runs on every pull request; see `RELEASING.md` for what it checks, the release checklist and
how to publish to Package Control.

## Licence

MIT. See `LICENSE`. Mermaid is MIT-licensed; see `assets/LICENSES.md`.
