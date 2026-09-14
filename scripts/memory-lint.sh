#!/usr/bin/env bash
# memory-lint.sh: fail-closed lint for mission memory files (budgets, required fields, duplicate IDs, secrets).
# Part of the mission skill (skills/mission/scripts/). Copied into .mission/bin/ by init. No network, no writes.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: memory-lint.sh [--quiet] [PATH ...]

Lints mission memory. Each PATH is a mission directory (lints STATE.md, state/*.md, STATUS.md, DECISIONS.md and
LESSONS-INBOX.md found inside it) or a single file whose kind comes from its name:

  STATE.md, state/*.md  F- facts need "Evidence:", "Level:" and "verified YYYY-MM-DD"; R- rules need "Applies when:"
                        and "Instances:" citing an F- id; H- hypotheses need "Check:" unless FALSIFIED; O- failures
                        need "Repro:" unless CONTRADICTION. STATE.md: <= 150 lines, "## Resume" with "- Next action:".
  STATUS.md             <= 100 lines; has "## Gates" and "## Board".
  DECISIONS.md          duplicate D- ids.
  LESSONS-INBOX.md      <= 30 open entries (status candidate|verifying); each entry has Lesson:, Applies when:,
                        Does not apply when:, Evidence:.
  lessons.md            <= 40 entries and <= 300 lines; each "### L-NNN" entry has Rule:, Applies when:, Why:,
                        Evidence:, Confidence:.

Every kind: duplicate entry IDs and likely secrets (key patterns). Lines inside HTML comments are ignored, and
"## ... index" sections hold references, not definitions.

Default PATH: <project>/.mission, where <project> is CLAUDE_PROJECT_DIR, else the git toplevel, else the current
directory. A missing default directory is not an error (exit 0).
Budget overrides in <mission dir>/config (key=value): state_max_lines, status_max_lines, inbox_max_open,
lessons_max_entries, lessons_max_lines.

Exit status: 0 clean, 1 violations found, 2 usage error.
EOF
}

QUIET=0
PATHS=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    -q|--quiet) QUIET=1; shift ;;
    --) shift; while [ "$#" -gt 0 ]; do PATHS+=("$1"); shift; done ;;
    -*) printf 'memory-lint: unknown option %s (see --help)\n' "$1" >&2; exit 2 ;;
    *) PATHS+=("$1"); shift ;;
  esac
done

VIOLATIONS=0
ALL_IDS=""
out=""

err() {
  printf 'memory-lint: %s\n' "$*" >&2
  VIOLATIONS=$((VIOLATIONS + 1))
}

project_root() {
  if [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
    printf '%s\n' "${CLAUDE_PROJECT_DIR}"
  else
    git rev-parse --show-toplevel 2>/dev/null || pwd
  fi
}

# cfg_get <config file> <key> <default>: numeric key=value lookup, last assignment wins.
cfg_get() {
  local v=""
  if [ -f "$1" ]; then
    v="$(sed -n "s/^[[:space:]]*$2[[:space:]]*=[[:space:]]*\([0-9][0-9]*\)[[:space:]]*$/\1/p" "$1" | tail -n 1)"
  fi
  printf '%s\n' "${v:-$3}"
}

line_count() { wc -l < "$1" | tr -d ' '; }

# collect <awk output>: lines "ERR <message>" become violations, lines "ID <group> <id> <file:line>" are recorded.
collect() {
  local line
  while IFS= read -r line; do
    case "$line" in
      ERR\ *) err "${line#ERR }" ;;
      ID\ *) printf -v ALL_IDS '%s%s\n' "${ALL_IDS}" "${line#ID }" ;;
    esac
  done <<< "$1"
}

scan_secrets() {
  local f="$1" hits
  hits="$(grep -nE 'sk_live_[0-9A-Za-z]{8,}|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{20,}|xox[abprs]-[0-9A-Za-z-]{10,}|-----BEGIN OPENSSH' "$f" || true)"
  if [ -n "$hits" ]; then
    err "$f: possible secret on line(s) $(printf '%s\n' "$hits" | awk -F: '{printf "%s ", $1}')(record the secret's name, never its value)"
  fi
}

lint_state() { # <file> <main:0|1> <config>
  local f="$1" main="$2" cfg="$3" n max
  if [ "$main" = 1 ]; then
    n="$(line_count "$f")"; max="$(cfg_get "$cfg" state_max_lines 150)"
    [ "$n" -le "$max" ] || err "$f: $n lines > $max (run the curator pass)"
    grep -q '^## Resume' "$f" || err "$f: missing '## Resume' section"
    grep -q '^- Next action:' "$f" || err "$f: '## Resume' has no '- Next action:' line"
  fi
  out="$(awk -v file="$f" '
    function flush() {
      if (id == "") return
      if (id ~ /^F-/) {
        if (!ev) print "ERR " file ":" ln ": " id " missing Evidence:"
        if (!lv) print "ERR " file ":" ln ": " id " missing Level:"
        if (head !~ /verified [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]/) print "ERR " file ":" ln ": " id " missing verified YYYY-MM-DD on its first line"
      } else if (id ~ /^R-/) {
        if (!ap) print "ERR " file ":" ln ": " id " missing Applies when:"
        if (!inst) print "ERR " file ":" ln ": " id " missing Instances: citing at least one F- id"
      } else if (id ~ /^H-/) {
        if (head !~ /FALSIFIED/ && !chk) print "ERR " file ":" ln ": " id " missing discriminating Check:"
      } else if (id ~ /^O-/) {
        if (head !~ /CONTRADICTION/ && !rep) print "ERR " file ":" ln ": " id " missing Repro:"
      }
      id = ""
    }
    function fields(s) {
      if (s ~ /Evidence:/) ev = 1
      if (s ~ /Level:/) lv = 1
      if (s ~ /Applies when:/) ap = 1
      if (s ~ /Instances:.*F-[0-9]/) inst = 1
      if (s ~ /Check:/) chk = 1
      if (s ~ /Repro:/) rep = 1
    }
    {
      if (incomment) { if (index($0, "-->")) incomment = 0; next }
      if (index($0, "<!--")) { if (!index($0, "-->")) incomment = 1; next }
    }
    /^## / { flush(); section = tolower($0); next }
    /^### / { flush(); next }
    /^- [FHRO]-[0-9]+/ {
      flush()
      if (section ~ /index/) next
      id = $2; sub(/[^A-Z0-9-].*$/, "", id)
      head = $0; ln = NR; ev = lv = ap = inst = chk = rep = 0
      fields($0)
      print "ID state " id " " file ":" NR
      next
    }
    /^[ \t]*$/ { next }
    /^[ \t]+/ { if (id != "") fields($0); next }
    { flush() }
    END { flush() }
  ' "$f")" || { err "$f: internal awk error (lint cannot vouch for this file)"; return 0; }
  collect "$out"
  scan_secrets "$f"
}

lint_status() { # <file> <config>
  local f="$1" n max
  n="$(line_count "$f")"; max="$(cfg_get "$2" status_max_lines 100)"
  [ "$n" -le "$max" ] || err "$f: $n lines > $max (roll Done log and Stop-rule log to archive/)"
  grep -q '^## Gates' "$f" || err "$f: missing '## Gates' section"
  grep -q '^## Board' "$f" || err "$f: missing '## Board' section"
  scan_secrets "$f"
}

lint_decisions() { # <file>
  local f="$1"
  out="$(awk -v file="$f" '
    { if (incomment) { if (index($0, "-->")) incomment = 0; next }
      if (index($0, "<!--")) { if (!index($0, "-->")) incomment = 1; next } }
    /^## D-[0-9]+/ { id = $2; sub(/[^A-Z0-9-].*$/, "", id); print "ID decisions " id " " file ":" NR }
  ' "$f")" || { err "$f: internal awk error (lint cannot vouch for this file)"; return 0; }
  collect "$out"
  scan_secrets "$f"
}

lint_inbox() { # <file> <config>
  local f="$1" max
  max="$(cfg_get "$2" inbox_max_open 30)"
  out="$(awk -v file="$f" -v max="$max" '
    function flush() {
      if (id == "") return
      if (!ls) print "ERR " file ":" ln ": " id " missing Lesson:"
      if (!ap) print "ERR " file ":" ln ": " id " missing Applies when:"
      if (!na) print "ERR " file ":" ln ": " id " missing Does not apply when:"
      if (!ev) print "ERR " file ":" ln ": " id " missing Evidence:"
      id = ""
    }
    function fields(s) {
      if (s ~ /Lesson:/) ls = 1
      if (s ~ /Applies when:/) ap = 1
      if (s ~ /Does not apply when:/) na = 1
      if (s ~ /Evidence:/) ev = 1
    }
    { if (incomment) { if (index($0, "-->")) incomment = 0; next }
      if (index($0, "<!--")) { if (!index($0, "-->")) incomment = 1; next } }
    /^#/ { flush(); next }
    /^- L-[0-9]+/ {
      flush(); id = $2; sub(/[^A-Z0-9-].*$/, "", id); ln = NR; ls = ap = na = ev = 0
      if ($0 ~ /status: *(candidate|verifying)/) nopen++
      print "ID inbox " id " " file ":" NR
      next
    }
    /^[ \t]*$/ { next }
    /^[ \t]+/ { if (id != "") fields($0); next }
    { flush() }
    END {
      flush()
      if (nopen + 0 > max + 0) print "ERR " file ": " nopen " open entries > " max " (triage: rejected(stale) / merged-into)"
    }
  ' "$f")" || { err "$f: internal awk error (lint cannot vouch for this file)"; return 0; }
  collect "$out"
  scan_secrets "$f"
}

lint_lessons() { # <file> <config>
  local f="$1" n maxl maxe
  n="$(line_count "$f")"
  maxl="$(cfg_get "$2" lessons_max_lines 300)"; maxe="$(cfg_get "$2" lessons_max_entries 40)"
  [ "$n" -le "$maxl" ] || err "$f: $n lines > $maxl (merge or retire lessons before promoting)"
  out="$(awk -v file="$f" -v maxe="$maxe" '
    function flush() {
      if (id == "") return
      if (!ru) print "ERR " file ":" ln ": " id " missing Rule:"
      if (!ap) print "ERR " file ":" ln ": " id " missing Applies when:"
      if (!wy) print "ERR " file ":" ln ": " id " missing Why:"
      if (!ev) print "ERR " file ":" ln ": " id " missing Evidence:"
      if (!cf) print "ERR " file ":" ln ": " id " missing Confidence:"
      id = ""
    }
    { if (incomment) { if (index($0, "-->")) incomment = 0; next }
      if (index($0, "<!--")) { if (!index($0, "-->")) incomment = 1; next } }
    /^### L-[0-9]+/ {
      flush(); id = $2; sub(/[^A-Z0-9-].*$/, "", id); ln = NR; ru = ap = wy = ev = cf = 0; entries++
      print "ID lessons " id " " file ":" NR
      next
    }
    /^#/ { flush(); next }
    /^- Rule:/ { ru = 1 }
    /^- Applies when:/ { ap = 1 }
    /^- Why:/ { wy = 1 }
    /^- Evidence:/ { ev = 1 }
    /Confidence:/ { cf = 1 }
    END {
      flush()
      if (entries + 0 > maxe + 0) print "ERR " file ": " entries " entries > " maxe " (merge or retire first)"
    }
  ' "$f")" || { err "$f: internal awk error (lint cannot vouch for this file)"; return 0; }
  collect "$out"
  scan_secrets "$f"
}

lint_file() { # <file> <config>
  local f="$1" cfg="$2" base parent
  base="$(basename "$f")"; parent="$(basename "$(dirname "$f")")"
  case "$base" in
    STATE.md) lint_state "$f" 1 "$cfg" ;;
    STATUS.md) lint_status "$f" "$cfg" ;;
    DECISIONS.md) lint_decisions "$f" ;;
    LESSONS-INBOX.md) lint_inbox "$f" "$cfg" ;;
    lessons.md) lint_lessons "$f" "$cfg" ;;
    *.md)
      if [ "$parent" = state ]; then lint_state "$f" 0 "$cfg"
      else err "$f: unknown memory file kind (expected STATE.md, state/*.md, STATUS.md, DECISIONS.md, LESSONS-INBOX.md, lessons.md)"
      fi ;;
    *) err "$f: not a markdown memory file" ;;
  esac
}

lint_dir() { # <mission dir>
  local d="$1" cfg="$1/config" part
  if [ -f "$d/STATE.md" ]; then lint_file "$d/STATE.md" "$cfg"
  else err "$d: no STATE.md"
  fi
  if [ -d "$d/state" ]; then
    for part in "$d"/state/*.md; do
      [ -f "$part" ] && lint_file "$part" "$cfg"
    done
  fi
  for part in STATUS.md DECISIONS.md LESSONS-INBOX.md; do
    [ -f "$d/$part" ] && lint_file "$d/$part" "$cfg"
  done
  return 0
}

if [ "${#PATHS[@]}" -eq 0 ]; then
  default_dir="$(project_root)/.mission"
  if [ ! -d "$default_dir" ]; then
    [ "$QUIET" = 1 ] || printf 'memory-lint: no mission directory at %s; nothing to lint\n' "$default_dir" >&2
    exit 0
  fi
  PATHS=("$default_dir")
fi

for p in "${PATHS[@]}"; do
  if [ -d "$p" ]; then
    lint_dir "$p"
  elif [ -f "$p" ]; then
    lint_file "$p" "$(dirname "$p")/config"
  else
    printf 'memory-lint: no such file or directory: %s\n' "$p" >&2
    exit 2
  fi
done

dups="$(printf '%s' "${ALL_IDS}" | awk '{ k = $1 " " $2; if (k in seen) print $2 " defined twice (" seen[k] " and " $3 ")"; else seen[k] = $3 }')"
if [ -n "$dups" ]; then
  while IFS= read -r d; do err "duplicate ID: $d"; done <<< "$dups"
fi

if [ "$VIOLATIONS" -gt 0 ]; then
  printf 'memory-lint: %s violation(s)\n' "$VIOLATIONS" >&2
  exit 1
fi
[ "$QUIET" = 1 ] || printf 'memory-lint: OK (%s)\n' "${PATHS[*]}" >&2
exit 0
