# MermaidPreview

MermaidPreview is a package for Sublime Text 4. It shows a diagram from the Mermaid text in the
current document, or in the current selection. It has two commands:

- **Preview in Browser** opens the diagram in your default browser. You can zoom and drag the
  diagram. This command needs no other software. It works offline, and your diagram text stays
  on your computer.
- **Export PNG…** saves the diagram as a high-resolution PNG image. This command is optional.
  It needs `mmdc` (mermaid-cli) and Node.js. See [PNG export (optional)](#png-export-optional).

## Install

You need Sublime Text 4, build 4205 or later, with
[Package Control](https://packagecontrol.io/installation) installed.

MermaidPreview is not in Package Control's default package list. For this reason, a search in
**Install Package** does not find it at first. You must add its repository one time:

1. Open the Command Palette. On macOS, press `⌘⇧P`. On Windows and Linux, press `Ctrl+Shift+P`.
   Run **Package Control: Add Repository**.
2. Paste this URL and press Enter:

   ```text
   https://raw.githubusercontent.com/jmjesperson/sublime-mermaid-preview/main/repository.json
   ```

3. Run **Package Control: Install Package** and select `MermaidPreview`.

Package Control installs the newest release. It also installs new releases automatically, as it
does for other packages.

To uninstall, run **Package Control: Remove Package** and select `MermaidPreview`. You can also
run **Package Control: Remove Repository** and select the URL above.

**Important:** use the `repository.json` URL above. Do not use the URL of the GitHub page. With
the GitHub page URL, Package Control installs unreleased code with the wrong package name
(`sublime-mermaid-preview`). Then the commands do nothing, because the package works only with
the name `MermaidPreview`.

## Usage

Open the Command Palette and run one of these commands:

- `MermaidPreview: Preview in Browser`
- `MermaidPreview: Export PNG…`

Which text is used:

- **If you selected text,** only the selected text is used. If there are several selections,
  only the first one is used.
- **If you did not select text,** the whole document is used.
- **The text must be Mermaid only,** for example `flowchart TB ...`. Markdown files with
  ```` ```mermaid ```` blocks are not supported.

In the browser:

- **Zoom** with the scroll wheel or with two fingers on a trackpad. The zoom is centred on the
  pointer.
- **Move** the diagram by dragging it.
- **Fit**, or the `0` key, makes the whole diagram fit in the window.
- Each preview opens a new browser tab.
- The preview page is a file in Sublime's cache folder. Each preview replaces this file. Nothing
  is saved next to your document.
- If the diagram has a syntax error, the page shows Mermaid's error message in red, then your
  text.

**Export PNG** always asks where to save the file. If your document has a file name, the dialog
opens in the same folder, with a PNG file name already filled in. To open the dialog in a
different folder every time, use the `save_folder` setting. If the export fails, an
existing PNG file is not changed, and the error message appears in the `MermaidPreview` output
panel.

## PNG export (optional)

Export PNG uses `mmdc`, the Mermaid command-line program. `mmdc` needs Node.js. When you
install it, it also downloads a Chromium browser, which is a few hundred MB. The browser
preview does not need any of this.

1. Install Node.js from https://nodejs.org, or with a version manager such as mise.
2. Run `npm install -g @mermaid-js/mermaid-cli`.
3. Test it: `echo 'graph TD; A-->B' | mmdc -i - -o /tmp/test.png`.

**How MermaidPreview finds `mmdc`.** It looks in this order:

1. The `mmdc_path` setting, if it is set. If this path is not a program file, the export stops
   with an error. MermaidPreview does not look in other places.
2. The folders in Sublime's `PATH`.
3. `/opt/homebrew/bin/mmdc`, `/usr/local/bin/mmdc` and `~/.local/share/mise/shims/mmdc`.

**Note for macOS.** When you start Sublime from the Dock or Finder, Sublime does not get the
`PATH` from your terminal. So `mmdc` can work in Terminal but not in Sublime. To fix this, run
`which mmdc` in Terminal, and put the result in the `mmdc_path` setting.

`mmdc` is a Node.js script, so Sublime must also find `node`. MermaidPreview adds the folder
that contains `mmdc` to the start of `PATH`. This works for most installations. If `node` is in
a different folder, put that folder in the `node_path` setting.

## Security

- **The preview page cannot use the network.** It has a Content-Security-Policy. Scripts can
  load only from the local files, and images must be inside the page. For example, if a diagram
  contains `<img src="https://…">`, the browser does not send the request.
- **Mermaid's `securityLevel` is `"strict"`,** which is Mermaid's default. A diagram cannot
  change it. Your own `mermaid_config` file can change it. **Do not set `"loose"` or
  `"antiscript"`** if you preview diagrams that come from other people. These levels let a
  diagram run scripts or click actions, in the browser and in the Chromium that `mmdc` uses.
- **Files are saved only in Sublime's cache folder for your user,** not in a temporary folder
  that other users can share.

## Settings

To change a setting, open **Preferences → Package Settings → MermaidPreview → Settings**, or
run `Preferences: MermaidPreview Settings` from the Command Palette. Sublime opens two files:

- **Left:** the default settings, with a comment for each setting. Do not change this file.
- **Right:** your User file. Copy a setting there and change its value. A value in the User file
  replaces the default. Add only the settings that you want to change.

The settings file is JSON, but Sublime also accepts `//` comments and a comma after the last
value. Example of a User file:

```json
{
    // Save PNG files in Downloads.
    "save_folder": "~/Downloads",
    "mmdc_scale": 4
}
```

| Setting | Type | Default |
|---|---|---|
| [`mmdc_path`](#mmdc_path) | text or `null` | `""` |
| [`node_path`](#node_path) | text or `null` | `""` |
| [`mmdc_scale`](#mmdc_scale) | number greater than 0 | `8` |
| [`mmdc_background`](#mmdc_background) | text | `"white"` |
| [`mmdc_timeout_seconds`](#mmdc_timeout_seconds) | number greater than 0 | `120` |
| [`mermaid_config`](#mermaid_config) | text or `null` | `""` |
| [`save_folder`](#save_folder) | text or `null` | `""` |

**Schema for editors.** The package includes a JSON Schema for these settings, in
`sublime-package.json`. If you install the **LSP-json** package, Sublime uses the schema in your
User file. It shows a description when you hover over a setting, suggests setting names, and
marks a wrong type or an unknown setting name. You do not need LSP-json to use MermaidPreview.

**Paths.** "Full path" means a path that starts with `/`, or with `~`, which means your home
folder (for example `~/Downloads`). `node_path` is different: it does not accept `~`.

### `mmdc_path`

- **Type:** text (a full path), or `null`
- **Default:** `""`
- **Example:** `"/opt/homebrew/bin/mmdc"`

The full path to the `mmdc` program, which Export PNG uses. If it is empty or `null`,
MermaidPreview looks for `mmdc` (see [How MermaidPreview finds `mmdc`](#png-export-optional)).

If you set a path and it is not a program file, Export PNG stops with an error that shows the
path. It does not look in other places.

### `node_path`

- **Type:** text (a full path to a folder), or `null`
- **Default:** `""`
- **Example:** `"/Users/you/.local/share/mise/shims"`

The folder that contains the `node` program. Set it only if `node` is not in the same folder as
`mmdc`. MermaidPreview puts this folder at the start of `PATH` when it runs `mmdc`.

`~` is not expanded in this setting. Write the full path. After this folder, the system still
looks in the folder of `mmdc` and on Sublime's `PATH`. If `node` is in none of them, `mmdc`
cannot start, and the `MermaidPreview` output panel shows the error.

### `mmdc_scale`

- **Type:** number greater than 0
- **Default:** `8`
- **Example:** `4`

The scale factor for the PNG (`mmdc -s`). A higher number makes a larger, sharper image and a
bigger file. It does not change the browser preview.

### `mmdc_background`

- **Type:** text
- **Default:** `"white"`
- **Example:** `"transparent"` or `"#F0F0F0"`

The background colour of the PNG (`mmdc -b`). Use a CSS colour name, a `#` colour code, or
`"transparent"`. It does not change the browser preview.

### `mmdc_timeout_seconds`

- **Type:** number greater than 0
- **Default:** `120`
- **Example:** `300`

The maximum time to wait for `mmdc`, in seconds. If `mmdc` takes longer, the export stops, an
existing PNG file is not changed, and the `MermaidPreview` output panel shows
`mmdc timed out after … seconds`. A very large diagram may need more time.

### `mermaid_config`

- **Type:** text (a full path to a file), or `null`
- **Default:** `""`
- **Example:** `"~/mermaid/dark.json"`

The path to your own Mermaid config file. The file must contain a JSON object, for example
`{"theme": "dark"}`. The keys are Mermaid's own config keys. See the
[Mermaid configuration documentation](https://mermaid.js.org/config/schema-docs/config.html).

- If it is empty or `null`, the package uses its default config, `{"theme": "default"}`.
- Your file replaces the default config. The two are not combined.
- The browser preview and `mmdc -c` use the same config, so the preview and the PNG look the
  same.
- If the file does not exist, is not valid JSON, or does not contain a JSON object, both commands
  stop and show an error. A value that is not text (for example a number) also shows an error.
- See [Security](#security) before you change `securityLevel`.

### `save_folder`

- **Type:** text (a full path to a folder), or `null`
- **Default:** `""`
- **Example:** `"~/Downloads"`

The folder where the save dialog opens. Export PNG uses it now. Other export formats can use it
later.

- If it is set, the dialog opens in this folder, also when the document is saved in another
  folder. The file name still comes from the document.
- If it is empty or `null`, the dialog opens in the document's folder. For an unsaved document,
  Sublime chooses the folder.
- If the folder does not exist, the path is not a full path, or the value is not text, the dialog
  opens in the document's folder, and the status bar shows a message.

## Matching Mermaid versions

The preview includes **Mermaid 12.2.0**. This is the version that mermaid-cli 12.0.0 uses, so
the preview and the PNG look the same. After you update mermaid-cli, check which Mermaid
version it uses:

```sh
grep -m1 '"version"' "$(npm root -g)/@mermaid-js/mermaid-cli/node_modules/mermaid/package.json"
```

If the version is different, update the copy in this package:

1. Copy `"$(npm root -g)/@mermaid-js/mermaid-cli/node_modules/mermaid/dist/mermaid.min.js"` to
   `assets/mermaid.min.js`. Use this file. Do not use the `.esm` file, because it does not load
   from a `file://` page.
2. Change the version number in `assets/LICENSES.md` and in this section.
3. Save `mermaid_preview.py`, or restart Sublime. The next preview then uses the new file.

## Key binding (example)

The package does not add key bindings. To add one, open **Preferences → Key Bindings** and add a
line like this one to the User file. This is only an example. Use any key that is free.

```json
{ "keys": ["ctrl+alt+m"], "command": "mermaid_preview_browser" }
```

## Development

### Use your clone in Sublime

First install the package with Package Control, as described in [Install](#install). This is
your normal copy. When you want to change the code, or test changes before a release, tell
Sublime to use your clone of this repository. When you finish, switch back.

```sh
scripts/dev.sh on          # use this clone. Saved changes load immediately.
scripts/dev.sh zip [REF]   # use a zip built from REF (default: HEAD). This is what users download.
scripts/dev.sh off         # use the Package Control copy again
scripts/dev.sh status      # show which copy Sublime uses
```

- `on` and `zip` move the Package Control copy to a backup folder. `off` moves it back.
- Restart Sublime after each switch.
- `zip` uses only committed files.
- **If you cannot see your change in Sublime,** run `scripts/dev.sh status`. It shows which copy
  Sublime uses, and if Sublime must restart.

Add this line one time to **Preferences → Package Settings → Package Control → Settings**:

```json
"ignore_vcs_packages": ["MermaidPreview"]
```

Without this line, Package Control's automatic upgrade runs `git pull` in your clone while
`dev.sh on` is active, because your clone is a git repository.

### Tests and reloading

```sh
python3 -m unittest discover tests                     # unit tests (standard library only)
python3 scripts/preview_fixture.py [file.mmd]          # make and open a preview without Sublime
```

- When you save `mermaid_preview.py`, Sublime reloads it. When you save a file in
  `mermaid_preview_core/`, Sublime does not reload it.
- After you change a file in `mermaid_preview_core/`, save `mermaid_preview.py` again (or run
  `touch` on it). This reloads all the code.
- `subl --command mermaid_preview_browser` runs the preview from a terminal.

CI runs on every pull request. `RELEASING.md` explains what CI checks and how to make a release.

## Licence

MIT. See `LICENSE`. Mermaid also uses the MIT licence. See `assets/LICENSES.md`.
