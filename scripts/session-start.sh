#!/usr/bin/env bash
# session-start.sh: SessionStart hook (matchers startup|resume|compact). Prints the mission resume pointer into
# context: STATE.md "## Resume" + "## Rules index" + open-failure headlines + STATUS.md header and top board rows,
# expired facts and any memory debt, truncated to a character budget. Silent when there is no .mission directory.
# Part of the mission skill (skills/mission/scripts/). Copied into .mission/bin/ by init. Read-only, no network.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: session-start.sh [--dir <mission dir>] [--budget <chars>] [--board-rows <n>]

Reads the SessionStart hook JSON from stdin when stdin is not a terminal (uses the "source" field if present) and
prints, in order:
  1. a one-line banner
  2. STATE.md  ## Resume, ## Rules index, headline lines of ## Open failures (max 10)
  3. EXPIRED lines for facts whose recheck-by date has passed
  4. STATUS.md header (lines before the first "## "), ## Gates table, first <n> rows of ## Board (default 12)
  5. .mission/tmp/memory-debt, if a previous session ended without a memory update
HTML comment lines are skipped. Output is cut to the budget (default 12000 chars, about 3k tokens; override with
--budget or session_budget_chars=<n> in <mission dir>/config).

Mission dir default: <project>/.mission, where <project> is CLAUDE_PROJECT_DIR, else the git toplevel, else the
current directory. If neither STATE.md nor STATUS.md exists there, prints nothing and exits 0.
Exit status: always 0 except 2 for a usage error (a SessionStart hook must never break session start).
EOF
}

DIR=""
BUDGET=""
BOARD_ROWS=12
while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --dir) [ "$#" -ge 2 ] || { echo "session-start: --dir needs a value" >&2; exit 2; }; DIR="$2"; shift 2 ;;
    --budget) [ "$#" -ge 2 ] || { echo "session-start: --budget needs a value" >&2; exit 2; }; BUDGET="$2"; shift 2 ;;
    --board-rows) [ "$#" -ge 2 ] || { echo "session-start: --board-rows needs a value" >&2; exit 2; }; BOARD_ROWS="$2"; shift 2 ;;
    *) echo "session-start: unknown argument $1 (see --help)" >&2; exit 2 ;;
  esac
done

if [ -z "$DIR" ]; then
  if [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
    DIR="${CLAUDE_PROJECT_DIR}/.mission"
  else
    DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)/.mission"
  fi
fi
[ -f "$DIR/STATE.md" ] || [ -f "$DIR/STATUS.md" ] || exit 0

INPUT=""
if [ ! -t 0 ]; then INPUT="$(cat 2>/dev/null || true)"; fi
SOURCE="$(printf '%s' "$INPUT" | sed -n 's/.*"source"[[:space:]]*:[[:space:]]*"\([a-z_]*\)".*/\1/p' | tail -n 1)"
SOURCE="${SOURCE:-startup}"

if [ -z "$BUDGET" ] && [ -f "$DIR/config" ]; then
  BUDGET="$(sed -n 's/^[[:space:]]*session_budget_chars[[:space:]]*=[[:space:]]*\([0-9][0-9]*\)[[:space:]]*$/\1/p' "$DIR/config" | tail -n 1)"
fi
BUDGET="${BUDGET:-12000}"
case "$BUDGET" in ''|*[!0-9]*) BUDGET=12000 ;; esac
case "$BOARD_ROWS" in ''|*[!0-9]*) BOARD_ROWS=12 ;; esac

# section <file> <heading text> <max lines>: print "## <heading>" and its body up to the next "## ", minus comments.
section() {
  awk -v want="## $2" -v max="$3" '
    { if (incomment) { if (index($0, "-->")) incomment = 0; next }
      if (index($0, "<!--")) { if (!index($0, "-->")) incomment = 1; next } }
    /^## / { on = ($0 == want); if (on) { print; n = 0 }; next }
    on && NF > 0 { if (n < max) print; else if (n == max) print "  [... more in file]"; n++ }
  ' "$1"
}

open_failures() {
  awk '
    { if (incomment) { if (index($0, "-->")) incomment = 0; next }
      if (index($0, "<!--")) { if (!index($0, "-->")) incomment = 1; next } }
    /^## / { on = ($0 == "## Open failures"); if (on) print; next }
    on && /^- O-[0-9]+/ { if (n < 10) print; n++ }
    END { if (n > 10) print "  [" (n - 10) " more open failures in STATE.md]" }
  ' "$1"
}

expired() {
  awk -v today="$(date -u +%Y-%m-%d)" '
    { if (incomment) { if (index($0, "-->")) incomment = 0; next }
      if (index($0, "<!--")) { if (!index($0, "-->")) incomment = 1; next } }
    /^- F-[0-9]+/ && match($0, /recheck-by [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]/) {
      d = substr($0, RSTART + 11, 10)
      if (d < today) { id = $2; sub(/[^A-Z0-9-].*$/, "", id); print "EXPIRED " id " (recheck-by " d "): treat as a hypothesis until re-verified" }
    }
  ' "$1"
}

status_top() {
  awk -v rows="$2" '
    { if (incomment) { if (index($0, "-->")) incomment = 0; next }
      if (index($0, "<!--")) { if (!index($0, "-->")) incomment = 1; next } }
    /^## / { hdr = 1; sec = $0; if (sec == "## Gates" || sec == "## Board") print; next }
    !hdr && NF > 0 { print; next }
    sec == "## Gates" && /^[|]/ { print; next }
    sec == "## Board" && /^[|]/ {
      b++
      if (b <= rows + 2) print
      else if (b == rows + 3) print "[... more board rows in STATUS.md]"
    }
  ' "$1"
}

compose() {
  printf '# Mission memory (auto-injected at %s). Read .mission/HANDOFF.md next; consult rules before re-deriving facts.\n' "$SOURCE"
  if [ -f "$DIR/STATE.md" ]; then
    printf '\n# From .mission/STATE.md\n'
    section "$DIR/STATE.md" "Resume" 20
    section "$DIR/STATE.md" "Rules index" 40
    open_failures "$DIR/STATE.md"
    expired "$DIR/STATE.md"
  fi
  if [ -f "$DIR/STATUS.md" ]; then
    printf '\n# From .mission/STATUS.md\n'
    status_top "$DIR/STATUS.md" "$BOARD_ROWS"
  fi
  if [ -f "$DIR/tmp/memory-debt" ]; then
    printf '\n## MEMORY DEBT: a previous session ended without updating STATE/STATUS. Reconstruct from git log first.\n'
    awk 'NR <= 20' "$DIR/tmp/memory-debt"
  fi
}

OUT="$(compose 2>/dev/null || true)"
if [ "${#OUT}" -gt "$BUDGET" ]; then
  printf '%s\n[session-start: output cut at %s chars; open the files for the rest]\n' "${OUT:0:BUDGET}" "$BUDGET"
else
  printf '%s\n' "$OUT"
fi
exit 0
