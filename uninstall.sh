#!/usr/bin/env bash
# Uninstall /drive: remove the ~/.claude/skills/drive symlink. A skills-directory plugin stops
# loading when its folder is gone, so nothing is disabled by name; a disabled state would outlive
# the symlink and leave a later reinstall switched off. The enabledPlugins entry that `claude plugin
# enable` recorded in your user settings stays, so a later install comes back enabled; no settings
# file is edited here.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DST="$HOME/.claude/skills/drive"

if [ -L "$DST" ]; then
  rm "$DST"
  echo "Removed the symlink $DST."
elif [ -e "$DST" ]; then
  echo "$DST exists and is not a symlink; refusing to remove it. It was not created by install.sh." >&2
  exit 1
else
  echo "$DST does not exist; nothing to remove."
fi

echo "The repository at $REPO is untouched."
echo "The provenance ledger for past runs stays at ~/.claude/drive/ledger/ (or the plugin data directory); delete it by hand if you want it gone."
echo "In a running session, run /reload-plugins."
