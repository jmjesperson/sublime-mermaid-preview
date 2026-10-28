#!/usr/bin/env bash
# Install MermaidPreview locally by symlinking this repo into Sublime's Packages folder.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
target="$HOME/Library/Application Support/Sublime Text/Packages/MermaidPreview"

if [ -L "$target" ]; then
    if [ "$(cd "$target" && pwd -P)" = "$repo_root" ]; then
        echo "already installed: $target -> $repo_root"
        exit 0
    fi
    echo "error: $target is a symlink to somewhere else; remove it first" >&2
    exit 1
fi
if [ -e "$target" ]; then
    echo "error: $target exists and is not a symlink; not touching it" >&2
    exit 1
fi

ln -s "$repo_root" "$target"
echo "installed: $target -> $repo_root"
