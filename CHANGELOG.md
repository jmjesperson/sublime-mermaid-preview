# Changelog

All notable changes to MermaidPreview are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Until 1.0.0,
minor versions may change behaviour or settings.

## [Unreleased]

## [0.2.1] - 2026-10-29

### Changed

- **The default settings file explains each setting** in a comment: what it does, its values,
  and an example.
- **New JSON Schema for the settings** (`sublime-package.json`). With the LSP-json package,
  Sublime shows descriptions and marks wrong values and unknown setting names in your User
  settings file.
- **The README describes each setting** with its type, default, an example, and what happens
  with a wrong value.

## [0.2.0] - 2026-10-29

### Added

- **New setting `save_folder`:** the folder where the save dialog opens, for example
  `"~/Downloads"`. If it is empty, the dialog opens in the document's folder, as before. If the
  folder does not exist, the dialog uses the document's folder and the status bar shows a
  message.

## [0.1.1] - 2026-10-29

### Fixed

- **Resizing the browser window keeps your zoom and position.** The diagram fits the window
  again only if you have not zoomed or moved it.
- **Mouse wheels that scroll by lines or pages zoom at a normal speed.**
- **Dragging stops correctly** when the browser takes the pointer away, for example when you
  switch windows during a drag.
- **Fit works for a diagram that has no size,** instead of making the view invalid.
- **A failed PNG export shows only the information it has.** It no longer shows
  "Exit code: None" after a timeout.
- **A `mermaid_config` setting that is not text shows a clear error.** A `null` value uses the
  default config.
- **The package works if it is installed under a different name,** for example after
  **Add Repository** with the GitHub page URL.
- **PNG export runs on its own thread,** so it does not block other packages while `mmdc` runs.
- **The first preview does not pause Sublime** while it loads the Mermaid file.

## [0.1.0] - 2026-10-28

First release.

### Added

- **`MermaidPreview: Preview in Browser`** renders the raw Mermaid in the document, or the first
  non-empty selection, in the default browser.
  - It uses the bundled Mermaid 12.2.0 and works offline.
  - Zoom with the wheel or a pinch, toward the pointer.
  - Drag to pan.
  - Fit with the button or the `0` key, with a zoom percentage shown.
  - Syntax errors show Mermaid's message in red, then the source.
- **`MermaidPreview: Export PNG…`** renders a PNG with mermaid-cli (`mmdc`), which is optional.
  - It always asks where to save, and pre-fills `<name>.png` for saved files.
  - It replaces the file atomically: a failed export never touches an existing file, and the
    file's permissions are kept.
  - Failures appear in the `MermaidPreview` output panel.
- **Finding `mmdc`:** the `mmdc_path` setting (if it is set, no other place is searched), then `PATH`, then
  Homebrew and mise shims. The folder containing `mmdc` goes at the front of `PATH`, so
  `node` is found when Sublime runs from the Dock.
- **Settings:** `mmdc_path`, `node_path`, `mmdc_scale` (default 8), `mmdc_background`,
  `mmdc_timeout_seconds` and `mermaid_config`.
- **One shared Mermaid config** for both the preview and `mmdc -c`, so the two render the same.
- **Install and upgrade messages,** through `messages.json`.
- **CI on every pull request:** unit tests on Python 3.14, the `messages.json` check, and
  Package Control's `st_package_reviewer`. A release workflow creates a GitHub Release for
  each semver tag.

### Security

- **The preview page has a Content-Security-Policy:** no network access, scripts only from the
  local files, images only inline.
- **Preview files are written to Sublime's per-user cache folder,** not the shared system temp
  folder.
- **The README documents the risk of loosening Mermaid's `securityLevel`.**
- **CI actions and tools are pinned:** actions and checked-out scripts to commit SHAs,
  `st-package-reviewer` to an exact version, and checkouts do not keep the token.

[Unreleased]: https://github.com/jmjesperson/sublime-mermaid-preview/compare/0.2.1...HEAD
[0.2.1]: https://github.com/jmjesperson/sublime-mermaid-preview/compare/0.2.0...0.2.1
[0.2.0]: https://github.com/jmjesperson/sublime-mermaid-preview/compare/0.1.1...0.2.0
[0.1.1]: https://github.com/jmjesperson/sublime-mermaid-preview/compare/0.1.0...0.1.1
[0.1.0]: https://github.com/jmjesperson/sublime-mermaid-preview/releases/tag/0.1.0
