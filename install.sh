#!/usr/bin/env bash
# Install /drive: link skill/ as ~/.claude/skills/drive, validate and enable the plugin, run the
# drive.py tests and selfcheck, and print the per-run launch settings. install.sh writes no settings
# file itself, but `claude plugin enable` records the plugin's enabled state (enabledPlugins) in your
# user settings. Every value a run relies on travels in that run's --settings JSON, so no other
# Claude session on this machine changes behaviour.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$REPO/skill"
DST="$HOME/.claude/skills/drive"
PLUGIN="drive@skills-dir"

for arg in "$@"; do
  case "$arg" in
    --apply-settings)
      echo "install.sh: --apply-settings was removed. It changed every Claude session on this machine; the settings below" >&2
      echo "are passed per run with --settings instead." >&2
      exit 2 ;;
    -h|--help)
      echo "usage: install.sh"
      echo "  Links $SRC to $DST, validates and enables $PLUGIN, runs the tests, and prints the per-run settings."
      exit 0 ;;
    *) echo "install.sh: unknown argument $arg" >&2; exit 2 ;;
  esac
done

command -v python3 >/dev/null || { echo "python3 is not on PATH; drive.py needs it." >&2; exit 1; }
[ -f "$SRC/.claude-plugin/plugin.json" ] || { echo "$SRC/.claude-plugin/plugin.json is missing." >&2; exit 1; }

mkdir -p "$HOME/.claude/skills"
if [ -e "$DST" ] && [ ! -L "$DST" ]; then
  echo "$DST exists and is not a symlink; refusing to replace it. Move it aside and run install.sh again." >&2
  exit 1
fi
if [ -L "$DST" ] && [ "$(readlink "$DST")" != "$SRC" ]; then
  echo "Replacing the symlink $DST (it pointed at $(readlink "$DST"))."
fi
ln -sfn "$SRC" "$DST"
[ -x "$SRC/scripts/drive.py" ] || chmod +x "$SRC/scripts/drive.py"
echo "Linked $DST -> $SRC"

if command -v claude >/dev/null; then
  if claude plugin validate "$SRC"; then
    echo "Plugin manifest and components validate."
  else
    echo "claude plugin validate reported problems; fix them before relying on the plugin." >&2
    exit 1
  fi
  # An earlier uninstall may have disabled the plugin by name, and that state outlives the symlink.
  # Enabling records enabledPlugins for drive in your user settings; nothing else in them changes.
  if claude plugin enable "$PLUGIN" >/dev/null 2>&1; then
    echo "Enabled $PLUGIN (claude plugin enable records this in enabledPlugins in your user settings)."
  else
    echo "claude plugin enable $PLUGIN did not succeed; checking claude plugin list." >&2
  fi
  # A marketplace plugin reports "enabled"; a skills-directory plugin reports "loaded". "disabled" or no entry fails.
  STATUS_LINE="$(claude plugin list 2>/dev/null | awk -v name="$PLUGIN" 'index($0, name) {found=1; next} found && /@/ && !/:/ {found=0} found && /Status:/ {print; exit}')"
  if printf '%s' "$STATUS_LINE" | grep -qiE '(^|[^[:alpha:]])(enabled|loaded)([^[:alpha:]]|$)' && ! printf '%s' "$STATUS_LINE" | grep -qi 'disabled'; then
    echo "$PLUGIN is enabled (status: $STATUS_LINE)."
  else
    echo "claude plugin list does not show $PLUGIN as enabled (status: ${STATUS_LINE:-not listed}). Run: claude plugin enable $PLUGIN" >&2
    exit 1
  fi
else
  echo "claude is not on PATH, so the plugin was not validated or enabled."
fi

command -v jq >/dev/null || echo "warning: jq is not on PATH; the eval commands in skill/evals/README.md use it."
for skill in deep-research severe-testing frontend-design; do
  [ -f "$HOME/.claude/skills/$skill/SKILL.md" ] || echo "warning: the $skill skill that drive's agents preload is not installed under ~/.claude/skills."
done

if [ "${DRIVE_INSTALL_SKIP_TESTS:-0}" != "1" ]; then
  echo "Running the drive.py tests (about three minutes)..."
  TEST_LOG="$(mktemp -t drive-tests.XXXXXX)"
  if python3 -m unittest discover -s "$SRC/scripts/tests" >"$TEST_LOG" 2>&1; then
    tail -n 3 "$TEST_LOG"
    rm -f "$TEST_LOG"
  else
    tail -n 40 "$TEST_LOG"
    echo "The drive.py tests fail (full log: $TEST_LOG); the hooks and lint cannot be trusted until they pass." >&2
    exit 1
  fi
fi
python3 "$SRC/scripts/drive.py" selfcheck

# The per-run settings. CLAUDE_CODE_STOP_HOOK_BLOCK_CAP lets the Stop gate hold a long run;
# BASH_DEFAULT_TIMEOUT_MS gives builds and suites ten minutes; the retry watchdog restarts stalled
# API calls. worktree.bgIsolation "none" keeps a background session in the one shared checkout
# instead of moving it into a .claude/worktrees/ worktree that commits and pushes a branch.
# promptCacheTtl "1h" keeps the orchestrator's cache warm while it waits on subagents; with an API key
# the default is five minutes, and a cold re-read of a large Fable context costs far more than the write.
# Workflow is allowed for read-only fan-outs, and the skill repository is added so lesson commits
# can write there. Never set CLAUDE_CODE_SUBAGENT_MODEL_FORCE: it overrides every agent's model.
SKILL_REPO="$(git -C "$SRC" rev-parse --show-toplevel 2>/dev/null || true)"
DRIVE_SETTINGS="$(SKILL_REPO="$SKILL_REPO" python3 - <<'PY'
import json, os
settings = {
    "env": {
        "CLAUDE_CODE_STOP_HOOK_BLOCK_CAP": "30",
        "BASH_DEFAULT_TIMEOUT_MS": "600000",
        "CLAUDE_CODE_RETRY_WATCHDOG": "1",
    },
    "permissions": {"allow": ["Workflow"]},
    "worktree": {"bgIsolation": "none"},
    "promptCacheTtl": "1h",
}
repo = os.environ.get("SKILL_REPO")
if repo:
    settings["permissions"]["additionalDirectories"] = [repo]
print(json.dumps(settings, separators=(",", ":")))
PY
)"

cat <<EOF

Per-run settings (not applied anywhere; pass them to each run with --settings):
  DRIVE_SETTINGS='$DRIVE_SETTINGS'

Background run, from the repository root (lean by default; for a rigorous run use --effort high and "/drive --rigorous <goal>"):
  claude --bg --name drive-<slug> --model claude-fable-5-1 --effort medium --permission-mode auto --settings "\$DRIVE_SETTINGS" "/drive <goal>"

Headless run (add a finite background-wait ceiling of three hours rather than 0, which waits forever):
  env CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=10800000 claude -p "/drive <goal>" --model claude-fable-5-1 --effort medium \\
    --permission-mode auto --settings "\$DRIVE_SETTINGS" --max-turns <n> --max-budget-usd <usd>

After intake, the run checks its own launch with: python3 ~/.claude/skills/drive/scripts/drive.py preflight

Check the install:
  claude plugin list                                  expect $PLUGIN, enabled or loaded
  python3 ~/.claude/skills/drive/scripts/drive.py selfcheck
In a running session, run /reload-plugins to pick up agent and hook changes.
EOF
