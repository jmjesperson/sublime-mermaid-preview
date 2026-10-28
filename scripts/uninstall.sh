#!/usr/bin/env bash
# Remove the MermaidPreview symlink from Sublime's Packages folder. Never removes a real folder.
set -euo pipefail

target="$HOME/Library/Application Support/Sublime Text/Packages/MermaidPreview"

if [ -L "$target" ]; then
    rm "$target"
    echo "uninstalled: $target"
elif [ -e "$target" ]; then
    echo "error: $target is not a symlink; not touching it" >&2
    exit 1
else
    echo "not installed"
fi
