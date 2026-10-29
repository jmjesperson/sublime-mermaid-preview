#!/usr/bin/env bash
# Switch Sublime between the Package Control copy of MermaidPreview (how users install it) and a
# local copy of this repo, for development and for testing before a release.
#
#   scripts/dev.sh on          symlink this repo into Packages/ as MermaidPreview (live code)
#   scripts/dev.sh zip [REF]   install the package zip built from REF (default HEAD), the same
#                              files users download, so export-ignore mistakes show up
#   scripts/dev.sh off         remove the local copy and put the Package Control copy back
#   scripts/dev.sh status      say which copy Sublime loads, and whether it needs a restart
#
# The Package Control copy is moved aside, not deleted, and restored by "off". Restart Sublime
# after switching. Never touches a real (non-symlink) Packages/MermaidPreview folder.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
st="$HOME/Library/Application Support/Sublime Text"
link="$st/Packages/MermaidPreview"
zip="$st/Installed Packages/MermaidPreview.sublime-package"
stash_dir="$HOME/Library/Caches/Sublime Text/MermaidPreview-dev"
stash="$stash_dir/MermaidPreview.sublime-package"
mode_file="$stash_dir/mode"
switched_file="$stash_dir/switched-at"
test_version="9999.0.0"
pc_settings="$st/Packages/User/Package Control.sublime-settings"

mode() { cat "$mode_file" 2>/dev/null || echo release; }

fail() { echo "error: $*" >&2; exit 1; }

refuse_real_folder() {
    if [ -e "$link" ] && [ ! -L "$link" ]; then
        fail "$link is a real folder, not a symlink; not touching it"
    fi
}

# Move the Package Control copy aside, once, when leaving release mode.
stash_release() {
    [ "$(mode)" = release ] || return 0
    [ -e "$stash" ] && fail "$stash already exists from an earlier switch; check it, then delete it"
    if [ -e "$zip" ]; then
        mkdir -p "$stash_dir"
        mv "$zip" "$stash"
        echo "moved the Package Control copy aside: $stash"
    fi
}

set_mode() {
    mkdir -p "$stash_dir"
    echo "$1" > "$mode_file"
    date +%s > "$switched_file"
    echo "restart Sublime to load it"
}

# Package Control runs "git pull" in package folders that contain .git, unless told not to.
# The settings file may span lines, so compare it with whitespace removed.
warn_vcs_upgrade() {
    local flat
    flat=""
    [ -f "$pc_settings" ] && flat="$(tr -d ' \t\n' < "$pc_settings")"
    case "$flat" in
    *'"ignore_vcs_packages":true'* | *'"ignore_vcs_packages":['*'"MermaidPreview"'*) ;;
    *)
        echo "warning: add \"ignore_vcs_packages\": [\"MermaidPreview\"] to Package Control's" >&2
        echo "  settings, or its auto-upgrade will git pull in this repo." >&2
        ;;
    esac
}

# Seconds since the epoch when the running Sublime started, or nothing if it isn't running.
sublime_started_at() {
    local pid
    pid="$(pgrep -x sublime_text | head -1 || true)"
    [ -n "$pid" ] || return 0
    date -j -f "%a %b %d %T %Y" "$(ps -o lstart= -p "$pid" | sed 's/  */ /g; s/ $//')" +%s 2>/dev/null || true
}

# The package-metadata.json inside a zip, if any.
zip_metadata() { unzip -p "$1" package-metadata.json 2>/dev/null || true; }

# The version Package Control recorded inside its copy, if any.
zip_version() {
    zip_metadata "$1" | sed -n 's/.*"version": *"\([^"]*\)".*/\1/p' | head -1
}

# The newest release tag in this clone (run "git fetch --tags" to see new ones).
latest_release() { git -C "$repo_root" tag --list '[0-9]*' --sort=-v:refname | head -1; }

# Warn when a Package Control copy is older than the newest release. After each release, the
# maintainer's own copy must be upgraded, the same way users get it.
warn_if_outdated() {
    local version="$1" latest
    latest="$(latest_release)"
    [ -n "$version" ] && [ -n "$latest" ] && [ "$version" != "$latest" ] || return 0
    [ "$(printf '%s\n%s\n' "$version" "$latest" | sort -V | head -1)" = "$version" ] || return 0
    echo "  OUT OF DATE: the Package Control copy is $version, but the newest release is $latest."
    echo "  With scripts/dev.sh off, restart Sublime and run Package Control: Upgrade Package."
}

# Package Control replaces a package that has no package-metadata.json (it calls it
# "unmanaged") with the newest release, each time Sublime starts. It also upgrades a package
# whose version is older than the newest release. So the test zip gets metadata with a
# version that is always newer, and a marker so that "status" can recognise it.
add_test_metadata() {
    local tmp
    tmp="$(mktemp -d)"
    printf '{"name": "MermaidPreview", "version": "%s", "dev_sh_zip": "%s"}\n' \
        "$test_version" "$1" > "$tmp/package-metadata.json"
    (cd "$tmp" && zip -q "$zip" package-metadata.json)
    rm -rf "$tmp"
}

status() {
    # Decided from the files on disk, not from the mode file, so it's right even after a
    # manual change.
    if [ -L "$link" ]; then
        local target
        target="$(cd "$link" && pwd -P)"
        echo "Sublime loads: DEV symlink -> $target"
        echo "  branch $(git -C "$target" branch --show-current 2>/dev/null || echo '?'), commit $(git -C "$target" rev-parse --short HEAD 2>/dev/null || echo '?'); uncommitted edits load too"
        [ -e "$zip" ] && echo "  note: $zip also exists; the symlinked files override it"
    elif [ -e "$link" ]; then
        echo "Sublime loads: a real folder at $link (not managed by this script)"
    elif [ -e "$zip" ]; then
        local version built_from
        version="$(zip_version "$zip")"
        built_from="$(zip_metadata "$zip" | sed -n 's/.*"dev_sh_zip": *"\([^"]*\)".*/\1/p')"
        if [ -n "$built_from" ]; then
            echo "Sublime loads: TEST ZIP built by dev.sh from $built_from"
        elif [ -z "$version" ]; then
            echo "Sublime loads: a zip without Package Control metadata: $zip"
            echo "  Package Control replaces it with the newest release when Sublime starts"
        else
            echo "Sublime loads: PACKAGE CONTROL copy, version $version"
            echo "  changes in this repository are NOT visible until they are released and upgraded"
            warn_if_outdated "$version"
            [ "$(mode)" = zip ] && echo "  warning: Package Control replaced the test zip; run scripts/dev.sh zip again"
        fi
    else
        echo "Sublime loads: nothing; MermaidPreview is not installed"
    fi
    if [ -e "$stash" ]; then
        echo "  set aside: Package Control copy, version $(zip_version "$stash")"
        warn_if_outdated "$(zip_version "$stash")"
    fi

    local started switched
    started="$(sublime_started_at)"
    switched="$(cat "$switched_file" 2>/dev/null || true)"
    if [ -z "$started" ]; then
        echo "Sublime is not running. It loads the copy above when it starts."
    elif [ -n "$switched" ] && [ "$started" -lt "$switched" ]; then
        echo "RESTART NEEDED: Sublime started before the last switch, so it may still run the previous copy"
    fi
    true
}

case "${1:-status}" in
on)
    refuse_real_folder
    stash_release
    [ "$(mode)" = zip ] && rm -f "$zip"
    ln -sfn "$repo_root" "$link"
    echo "dev: $link -> $repo_root"
    set_mode dev
    warn_vcs_upgrade
    ;;
zip)
    ref="${2:-HEAD}"
    refuse_real_folder
    git -C "$repo_root" rev-parse --verify --quiet "$ref^{commit}" >/dev/null || fail "unknown ref: $ref"
    stash_release
    [ -L "$link" ] && rm "$link"
    built_from="$ref ($(git -C "$repo_root" rev-parse --short "$ref"))"
    git -C "$repo_root" archive --format=zip -o "$zip" "$ref"
    add_test_metadata "$built_from"
    echo "zip: $zip built from $built_from"
    set_mode zip
    ;;
off)
    refuse_real_folder
    [ -L "$link" ] && rm "$link" && echo "removed the dev symlink"
    [ "$(mode)" = zip ] && rm -f "$zip" && echo "removed the test zip"
    if [ -e "$stash" ]; then
        mv "$stash" "$zip"
        echo "restored the Package Control copy: $zip"
        warn_if_outdated "$(zip_version "$zip")"
    elif [ "$(mode)" != release ]; then
        echo "no Package Control copy was set aside; run Package Control: Install Package"
    fi
    if [ "$(mode)" != release ]; then
        set_mode release
        rm -f "$mode_file"
    fi
    ;;
status)
    status
    ;;
*)
    fail "usage: scripts/dev.sh on | zip [REF] | off | status"
    ;;
esac
