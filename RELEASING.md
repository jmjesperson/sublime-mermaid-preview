# Releasing MermaidPreview

This project uses a simple GitHub Flow:

- `main` must always be ready to release.
- Every change goes to `main` through a pull request, and CI must pass.
- **A release is a version tag on `main`,** for example `0.2.0`.

Package Control reads the tags in this repository directly. There is no build step, and you do
not upload any files.

## What CI checks

`.github/workflows/ci.yml` runs for every pull request and every push to `main`:

| Job | What it checks |
|---|---|
| `tests` | The unit tests, on Python 3.14 (the Python version of Sublime's plugin host). It also checks that every resource file is plain JSON. |
| `upgrade-messages` | `messages.json` is valid, and every file that it names exists. This uses the check script from `kaste/upgrade-messages-test-action` v1.1. |
| `package-review` | Package Control's own reviewer (`st_package_reviewer`). Package Control uses the same checks for new packages. |

`.github/workflows/release.yml` runs when you push a version tag. It runs the tests again. Then
it creates a GitHub Release. The release notes are the text of `messages/<tag>.txt`.

## Release checklist

1. **Choose the version number.** Look at the changes under `[Unreleased]` in `CHANGELOG.md`
   and follow [Semantic Versioning](https://semver.org):
   - **patch** (for example `0.1.1`): only bug fixes.
   - **minor** (for example `0.2.0`): new features. Before version 1.0.0, also use a minor
     version for any change to behaviour or settings.
   - **major**: a change that breaks existing use, after version 1.0.0.

   Do not put a `v` before the number. Keep the version below 1.0.0 until the package is
   stable.
2. **Update `CHANGELOG.md`** on a new branch:
   - Change `## [Unreleased]` to `## [<version>] - YYYY-MM-DD`. Use the full release date.
   - Add a new, empty `## [Unreleased]` section above it.
   - Update the links at the end of the file. The `[Unreleased]` link compares
     `<version>...HEAD`. The `[<version>]` link compares the previous tag with `<version>`.
     For the first release, it links to the tag.

   Each pull request adds its own lines under `[Unreleased]`. So in this step you only rename
   the section.
3. **Write the upgrade message** on the same branch:
   - Create `messages/<version>.txt`. Write a short, simple summary of the changelog entry.
     Sublime shows this text to users after they upgrade.
   - Add `"<version>": "messages/<version>.txt"` to `messages.json`.
4. **If you changed the Mermaid file in `assets/`,** check that `assets/LICENSES.md` and the
   README section "Matching Mermaid versions" show the new version.
5. **Open a pull request.** Wait until CI passes, then merge it into `main`.
6. **Before you create the tag, test what users will get.** The download does not include the
   files marked `export-ignore` in `.gitattributes`. Install the same zip file, built from
   `main`:

   ```sh
   git switch main && git pull
   scripts/dev.sh zip main
   ```

   Restart Sublime. Preview the test file `tests/fixtures/large-flowchart.mmd`, and export a
   PNG. Then run `scripts/dev.sh off` to use the Package Control copy again.
7. **Create the tag and push it:**

   ```sh
   git switch main && git pull
   git tag -a <version> -m "MermaidPreview <version>"
   git push origin <version>
   ```

   Check that the `Release` workflow passed, and that the GitHub Release exists.
8. **Check the install that users do.**
   - In your own Sublime, after `scripts/dev.sh off`, run **Package Control: Upgrade Package**
     and select `MermaidPreview`, or wait for the automatic upgrade. Check that the new version
     is installed.
   - On a computer that does not have the package, follow the [Install](README.md#install)
     steps in the README.

**Do not move or delete a tag after you push it.** Users may already have that version. If a
release has a problem, fix it on `main` and release the next patch version.

## How users install the package

Users add `repository.json` with **Package Control: Add Repository** (see the README). This
file gives the package its name, `MermaidPreview`, and tells Package Control to install from
the version tags. Do not move or rename `repository.json`, or remove it from `main`. If you do,
existing users stop getting updates.

Do not tell users to add the GitHub page URL. With that URL, Package Control installs the `main`
branch with the repository name, `sublime-mermaid-preview`, and the package does not work.

## Listing in Package Control's default channel (not done, optional)

The default channel is the list of packages that **Install Package** shows to everyone. This
package is not in the default channel. This was a decision, not a missing step. These notes are
here in case the decision changes.

Packages are added to the default channel with a pull request to
**https://github.com/sublimehq/package_control_channel**. (The `packagecontrol/channel`
repository is only for libraries.) Read the submission guide that the channel's readme links to.

1. Check the latest release with **Add Repository** (step 8 above).
2. Fork the channel repository. Add the entry below to `repository/m.json`, in alphabetical
   order.
3. Open the pull request, and complete the channel's pull request template: the checklist, and
   the line "My package is similar to ...". The channel's CI checks the entry, and then a person
   reviews it. This can take a few weeks. Answer the reviewer yourself. The template says that
   the reviewer checks if the person who submits the package will support it for a long time.

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

- **This entry is the same as the package in `repository.json`.** If you change one, change the
  other.
- **`name`** must be `MermaidPreview`. It is the name of the installed package, and the code
  loads its files from `Packages/MermaidPreview/`. The repository can have a different name.
- **`"tags": true`** means that every version tag (for example `0.2.0`) is a release.
- **`">=4205"`**: Sublime Text started to run plugins on Python 3.14 in build 4205, according
  to https://www.sublimetext.com/docs/api_environments.html. The package needs Python 3.14.
  Older builds would run it on Python 3.3. Check this page again before you submit.
- **Before you submit,** search Package Control for similar packages. The guidelines ask authors
  to think about improving an existing package before they add a new one, and reviewers ask
  about this. The `Mermaid` package (SublimeText/Mermaid) has syntax highlighting, snippets, and
  a build system that runs `mmdc` on a saved file. It has no preview in the editor or the
  browser, it needs `mmdc` for any output, and it works only on saved files.
