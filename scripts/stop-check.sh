#!/usr/bin/env bash
# stop-check.sh: Stop hook. When .mission/config has enforce_stop=1, blocks the end of a turn if STATE.md or
# STATUS.md were last written before the latest change to other .mission/ files or the latest commit outside
# .mission/, or if memory-lint fails. Loop-safe: with stop_hook_active=true it records .mission/tmp/memory-debt and
# allows the stop. Part of the mission skill (skills/mission/scripts/). No network, no git writes.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: stop-check.sh [--dir <mission dir>] [--force]

Reads the Stop hook JSON from stdin when stdin is not a terminal. Does nothing (exit 0) unless all hold:
  - <mission dir>/STATE.md and STATUS.md exist
  - <mission dir>/config contains enforce_stop=1 (or --force is given)
Freshness stamp = the older modification time of STATE.md and STATUS.md. Memory is stale when
  (a) any file under <mission dir> other than STATE.md, STATUS.md, HANDOFF.md, tmp/ and archive/ is newer, or
  (b) the latest commit touching paths outside .mission/ is newer than the stamp plus stop_grace_sec (config,
      default 120), or
  (c) memory-lint.sh (next to this script) exits non-zero.
Stale and "stop_hook_active": true in stdin -> writes <mission dir>/tmp/memory-debt, allows the stop.
Stale otherwise -> prints {"decision":"block","reason":"..."} on stdout (the reason is the next instruction).
Fresh -> removes tmp/memory-debt, allows the stop.

Mission dir default: <project>/.mission, where <project> is CLAUDE_PROJECT_DIR, else the git toplevel, else the
current directory. Exit status: 0 (decisions are made through stdout JSON), 2 for a usage error.
EOF
}

DIR=""
FORCE=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --dir) [ "$#" -ge 2 ] || { echo "stop-check: --dir needs a value" >&2; exit 2; }; DIR="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    *) echo "stop-check: unknown argument $1 (see --help)" >&2; exit 2 ;;
  esac
done

if [ -z "$DIR" ]; then
  if [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
    DIR="${CLAUDE_PROJECT_DIR}/.mission"
  else
    DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)/.mission"
  fi
fi
ROOT="$(dirname "$DIR")"

INPUT=""
if [ ! -t 0 ]; then INPUT="$(cat 2>/dev/null || true)"; fi

[ -f "$DIR/STATE.md" ] && [ -f "$DIR/STATUS.md" ] || exit 0
if [ "$FORCE" != 1 ]; then
  grep -Eq '^[[:space:]]*enforce_stop[[:space:]]*=[[:space:]]*1([[:space:]]|$)' "$DIR/config" 2>/dev/null || exit 0
fi

ACTIVE=0
case "$INPUT" in
  *'"stop_hook_active":true'*|*'"stop_hook_active": true'*) ACTIVE=1 ;;
esac

GRACE="$(sed -n 's/^[[:space:]]*stop_grace_sec[[:space:]]*=[[:space:]]*\([0-9][0-9]*\)[[:space:]]*$/\1/p' "$DIR/config" 2>/dev/null | tail -n 1 || true)"
GRACE="${GRACE:-120}"

mtime() { stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null || true; }

OLDER="$DIR/STATE.md"
[ "$DIR/STATUS.md" -ot "$DIR/STATE.md" ] && OLDER="$DIR/STATUS.md"
STAMP="$(mtime "$OLDER")"
case "$STAMP" in ''|*[!0-9]*) exit 0 ;; esac

REASON=""

# (a) other mission files written after the memory files
CHANGED="$(find "$DIR" -type f -newer "$OLDER" \
  ! -path "$DIR/tmp/*" ! -path "$DIR/archive/*" \
  ! -name STATE.md ! -name STATUS.md ! -name HANDOFF.md -print 2>/dev/null | awk 'NR == 1' || true)"
if [ -n "$CHANGED" ]; then
  REASON="${CHANGED#"$ROOT"/} changed after STATE.md/STATUS.md were last written."
fi

# (b) a commit outside .mission/ newer than the memory files
if [ -z "$REASON" ] && git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  COMMIT_TS="$(git -C "$ROOT" log -1 --format=%ct -- . ':(exclude).mission' 2>/dev/null || true)"
  case "$COMMIT_TS" in
    ''|*[!0-9]*) ;;
    *) if [ "$COMMIT_TS" -gt $((STAMP + GRACE)) ]; then
         REASON="commit $(git -C "$ROOT" log -1 --format=%h -- . ':(exclude).mission' 2>/dev/null || true) is newer than STATE.md/STATUS.md."
       fi ;;
  esac
fi

# (c) lint
LINT="$(dirname "$0")/memory-lint.sh"
if [ -z "$REASON" ] && [ -x "$LINT" ]; then
  LINT_OUT="$("$LINT" --quiet "$DIR" 2>&1 >/dev/null || true)"
  if [ -n "$LINT_OUT" ]; then
    REASON="memory-lint failed: $(printf '%s\n' "$LINT_OUT" | awk 'NR <= 3 { printf "%s; ", $0 }')"
  fi
fi

if [ -z "$REASON" ]; then
  rm -f "$DIR/tmp/memory-debt"
  exit 0
fi

if [ "$ACTIVE" = 1 ]; then
  mkdir -p "$DIR/tmp"
  printf '%s stop allowed with stale mission memory: %s\n' "$(date -u +%Y-%m-%dT%H:%MZ)" "$REASON" > "$DIR/tmp/memory-debt"
  exit 0
fi

MSG="Mission memory is stale: ${REASON} Before stopping: update .mission/STATUS.md (board states with evidence, Gates, Updated line) and .mission/STATE.md (Resume with a runnable next action, one ## Last session line, fact/failure deltas with Evidence), run .mission/bin/memory-lint.sh until it exits 0, then stop."
MSG="${MSG//\\/ }"
MSG="${MSG//\"/ }"
MSG="$(printf '%s' "$MSG" | tr '\n\t' '  ')"
printf '{"decision":"block","reason":"%s"}\n' "$MSG"
exit 0
