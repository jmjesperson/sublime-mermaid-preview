# Changelog

All notable changes to MermaidPreview are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Until 1.0.0,
minor versions may change behaviour or settings.

## [Unreleased]

Everything below is planned for the first release, 0.1.0.

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
- **Finding `mmdc`:** the `mmdc_path` setting (with no fallback when it's set), then `PATH`, then
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
  `st-package-reviewer` to an exact version, and checkouts don't keep the token.

[Unreleased]: https://github.com/jmjesperson/sublime-mermaid-preview/commits/main
