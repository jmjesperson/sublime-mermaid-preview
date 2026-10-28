# Releasing MermaidPreview

The process is lightweight GitHub Flow. `main` is always releasable, and every change arrives
through a pull request with green CI. **A release is a semver tag on `main`.** Package Control
reads the repo's tags directly; there is no build step and nothing to upload.

## What CI checks

`.github/workflows/ci.yml` runs on every pull request and every push to `main`:

| Job | What it checks |
|---|---|
| `tests` | The unit tests on Python 3.14 (Sublime's plugin host version), and that every resource file is plain JSON |
| `upgrade-messages` | `messages.json` is valid and every file it names exists (the check script from `kaste/upgrade-messages-test-action` v1.1, run directly) |
| `package-review` | Package Control's own reviewer (`st_package_reviewer`), the same checks used on channel submissions |

`.github/workflows/release.yml` runs when a semver tag is pushed. It reruns the tests, then
creates a GitHub Release whose notes are `messages/<tag>.txt`.

## Release checklist

1. **Pick the version** from what's under `[Unreleased]` in `CHANGELOG.md`, following SemVer:
   - **patch** (`0.1.1`) for fixes only;
   - **minor** (`0.2.0`) for new features, or before 1.0.0 any change to behaviour or settings;
   - **major** for a breaking change after 1.0.0.

   Use no `v` prefix. Stay on `0.x` until the package has settled.
2. **Update `CHANGELOG.md`** on a branch:
   - Rename `## [Unreleased]` to `## [<version>] - YYYY-MM-DD` (the absolute release date).
   - Start a new, empty `## [Unreleased]` above it.
   - Update the links at the bottom: `[Unreleased]` compares `<version>...HEAD`, and
     `[<version>]` compares the previous tag to `<version>` (or points at the tag itself for
     the first release).

   Every change should land in `[Unreleased]` with its own pull request, so this step is only
   renaming.
3. **Write the upgrade message** on the same branch:
   - Create `messages/<version>.txt`, a short plain-words version of the changelog entry.
     Sublime shows it to users after they upgrade.
   - Add `"<version>": "messages/<version>.txt"` to `messages.json`.
4. **If you changed the bundled Mermaid,** check that `assets/LICENSES.md` and the README's
   "Matching Mermaid versions" section name the new version.
5. **Open a pull request, wait for green CI, and merge** into `main`.
6. **Test what users will get, before tagging.** The download leaves out everything marked
   `export-ignore` in `.gitattributes`. Build the same zip from `main` and install it:

   ```sh
   scripts/uninstall.sh
   git archive --format=zip -o "$HOME/Library/Application Support/Sublime Text/Installed Packages/MermaidPreview.sublime-package" main
   ```

   Restart Sublime. Preview the test fixture and export a PNG. Then delete that
   `.sublime-package` and run `scripts/install.sh` to go back to the dev symlink.
7. **Tag and push:**

   ```sh
   git switch main && git pull
   git tag -a <version> -m "MermaidPreview <version>"
   git push origin <version>
   ```

   Check that the `Release` workflow succeeded and the GitHub Release exists.
8. **Check the real install path.** In a Sublime without the dev symlink:
   - Run **Package Control: Add Repository** with
     `https://raw.githubusercontent.com/jmjesperson/sublime-mermaid-preview/main/repository.json`.
     Not the plain GitHub URL: Package Control would install `main` under the repo's name.
   - Run **Package Control: Install Package**, then choose `MermaidPreview`.

   `repository.json` names the package and points at the tags, as the channel entry below
   does, so this installs exactly as a published package would. Before the channel entry
   exists, it's also how anyone can install the package.

If a tag turns out to be broken, don't move or delete it; users may already have it. Fix the
problem on `main` and release the next patch version.

## Publishing to Package Control (first time only)

Package Control is the "Install Package" list. Packages are submitted by pull request to
**https://github.com/sublimehq/package_control_channel**. The `packagecontrol/channel` repo is
for libraries only. Follow the channel's submission guide, linked from its readme.

1. Release at least one tag, and check it through **Add Repository** (step 8 above).
2. Fork the channel repo. Add the entry below to `repository/m.json`, keeping the file's
   alphabetical order.
3. Run the channel's own tests, as its readme describes, then open the pull request. A reviewer
   bot and a human will review it.

The channel entry:

```json
{
    "name": "MermaidPreview",
    "details": "https://github.com/jmjesperson/sublime-mermaid-preview",
    "labels": ["mermaid", "diagram", "preview"],
    "releases": [
        {
            "sublime_text": ">=4205",
            "tags": true
        }
    ]
}
```

What the fields mean:

- **`name`** must be `MermaidPreview`. It becomes the installed package's name, and the code
  reads its resources from `Packages/MermaidPreview/`. The repo name doesn't have to match.
  Keep this entry and `repository.json` the same.
- **`"tags": true`** means every plain semver tag is a release.
- **`">=4205"`** is the build where Sublime's plugin host moved to Python 3.14, according to
  https://www.sublimetext.com/docs/api_environments.html. The package needs that host, because
  older builds would run it on Python 3.3. Check the current docs before submitting.
- **Before submitting,** search Package Control for similar packages. The guidelines ask authors
  to consider improving an existing package (`Mermaid` does syntax highlighting, not preview)
  before adding a new one, and reviewers ask about it.
