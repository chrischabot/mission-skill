#!/usr/bin/env bash
# preflight.sh — mission model/agent preflight. Local checks only: no network, no writes.
# Rules: references/models-and-cost.md (MR1, MR7, PF1, PF2). Canonical models: references/conventions.md §6–§7.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: preflight.sh [--repo <path>] [--allow-degraded] [-h|--help]

Checks, for the target repository:
  1. CLAUDE_CODE_SUBAGENT_MODEL is unset (WARN otherwise: it can override agent models).
  2. `claude --version` (if claude is on PATH) meets the floors:
     claude-fable-5-1 needs >= v2.1.257, claude-opus-4-8 needs >= v2.1.154.
  3. .claude/agents/ holds the 12 roster files (Explore.md, mission-*.md), each with name = file stem,
     a full model ID (aliases opus|sonnet|fable|haiku|best|default|opusplan|inherit fail; Haiku is banned),
     the roster model and effort, and no Edit/Write tools on read-only agents.
  4. Prints the model table and the roster.

Options:
  --repo <path>      Target repository (default: current directory; when run from <repo>/.mission/bin
                     without .claude/ in the current directory, the repo containing the script).
  --allow-degraded   Version floors below requirement become WARN (use with the Degraded profile + D-entry).
  -h, --help         Show this help.

Exit codes: 0 no hard failures (warnings allowed) · 1 hard failures · 2 usage error.
Not checked here (do by hand, PF1): one probe spawn per model ID confirming the answering model.
EOF
}

REPO=""
ALLOW_DEGRADED=0
while [ "$#" -gt 0 ]; do
  case "${1}" in
    --repo)
      [ "$#" -ge 2 ] || { echo "preflight: --repo needs a value" >&2; exit 2; }
      REPO="${2}"; shift 2 ;;
    --repo=*) REPO="${1#--repo=}"; shift ;;
    --allow-degraded) ALLOW_DEGRADED=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "preflight: unknown argument: ${1}" >&2; usage >&2; exit 2 ;;
  esac
done

if [ -z "${REPO}" ]; then
  REPO="."
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  case "${SCRIPT_DIR}" in
    */.mission/bin)
      if [ ! -d "./.claude" ] && [ ! -d "./.mission" ]; then
        REPO="${SCRIPT_DIR%/.mission/bin}"
      fi ;;
  esac
fi
[ -d "${REPO}" ] || { echo "preflight: repo not found: ${REPO}" >&2; exit 2; }

# Canonical data. When models change: edit conventions.md §6/§7, the agent files, and these two tables.
ALLOWED_MODELS="claude-fable-5-1 claude-opus-4-8 claude-sonnet-4-6"
FABLE_MIN="2.1.257"
OPUS_MIN="2.1.154"
# name|model|effort|access (ro = read-only, rw = write)
EXPECTED="Explore|claude-sonnet-4-6|low|ro
mission-scout|claude-sonnet-4-6|low|ro
mission-checker|claude-sonnet-4-6|low|ro
mission-worker|claude-sonnet-4-6|medium|rw
mission-worker-high|claude-sonnet-4-6|high|rw
mission-verifier|claude-sonnet-4-6|high|ro
mission-builder|claude-opus-4-8|high|rw
mission-integrator|claude-opus-4-8|medium|rw
mission-reviewer|claude-opus-4-8|medium|ro
mission-critic|claude-opus-4-8|high|ro
mission-strategist|claude-fable-5-1|high|rw
mission-strategist-review|claude-fable-5-1|medium|ro"

FAILS=0
WARNS=0
pass() { printf 'PASS  %s\n' "${1}"; }
warn() { printf 'WARN  %s\n' "${1}"; WARNS=$((WARNS + 1)); }
fail() { printf 'FAIL  %s\n' "${1}"; FAILS=$((FAILS + 1)); }

# ver_ge A B → success when version A >= version B (numeric major.minor.patch)
ver_ge() {
  local IFS=.
  local -a a b
  read -r -a a <<< "${1}"
  read -r -a b <<< "${2}"
  local i x y
  for i in 0 1 2; do
    x="${a[i]:-0}"; y="${b[i]:-0}"
    if [ "${x}" -gt "${y}" ]; then return 0; fi
    if [ "${x}" -lt "${y}" ]; then return 1; fi
  done
  return 0
}

# fm_value FILE KEY → value of KEY in the leading YAML frontmatter (quotes and trailing comments stripped)
fm_value() {
  awk -v key="${2}" -v q="'" '
    { sub(/\r$/, "") }
    NR == 1 { if ($0 !~ /^---[ \t]*$/) exit; next }
    /^---[ \t]*$/ { exit }
    index($0, key ":") == 1 {
      v = substr($0, length(key) + 2)
      sub(/[ \t]+#.*$/, "", v)
      gsub(/^[ \t]+|[ \t]+$/, "", v)
      if (substr(v, 1, 1) == "\"" || substr(v, 1, 1) == q) v = substr(v, 2)
      if (substr(v, length(v), 1) == "\"" || substr(v, length(v), 1) == q) v = substr(v, 1, length(v) - 1)
      print v
      exit
    }' "${1}"
}

echo "== mission preflight · repo: ${REPO}"

echo
echo "-- 1. Environment"
if [ -n "${CLAUDE_CODE_SUBAGENT_MODEL+x}" ]; then
  warn "CLAUDE_CODE_SUBAGENT_MODEL is set (value: ${CLAUDE_CODE_SUBAGENT_MODEL:-<empty>}); it can override every agent's model. Unset it for the mission (PF1)."
else
  pass "CLAUDE_CODE_SUBAGENT_MODEL is unset"
fi

echo
echo "-- 2. Claude Code version"
version_issue() {
  if [ "${ALLOW_DEGRADED}" -eq 1 ]; then warn "${1} (allowed: --allow-degraded)"; else fail "${1}"; fi
}
if command -v claude >/dev/null 2>&1; then
  if command -v timeout >/dev/null 2>&1; then
    RAW="$(timeout 20 claude --version 2>/dev/null || true)"
  else
    RAW="$(claude --version 2>/dev/null || true)"
  fi
  printf '      claude --version: %s\n' "${RAW:-<no output>}"
  VER="$(printf '%s\n' "${RAW}" | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n 1 || true)"
  if [ -z "${VER}" ]; then
    warn "could not parse a version; check floors by hand (Fable 5.1 >= v${FABLE_MIN}, Opus 4.8 >= v${OPUS_MIN})"
  else
    if ver_ge "${VER}" "${OPUS_MIN}"; then
      pass "v${VER} >= v${OPUS_MIN} (claude-opus-4-8)"
    else
      version_issue "v${VER} < v${OPUS_MIN}: claude-opus-4-8 unsupported → upgrade, or Degraded profile (no Opus 4.8)"
    fi
    if ver_ge "${VER}" "${FABLE_MIN}"; then
      pass "v${VER} >= v${FABLE_MIN} (claude-fable-5-1)"
    else
      version_issue "v${VER} < v${FABLE_MIN}: claude-fable-5-1 unsupported → upgrade, or Degraded profile (no Fable)"
    fi
  fi
else
  warn "claude not on PATH; version floors not checked (Fable 5.1 >= v${FABLE_MIN}, Opus 4.8 >= v${OPUS_MIN})"
fi

# check_model LABEL MODEL → success only for an allowed full model ID
check_model() {
  local label="${1}" m="${2}" lower
  lower="$(printf '%s' "${m}" | tr '[:upper:]' '[:lower:]')"
  if [ -z "${m}" ]; then
    fail "${label}: no model field (the agent would inherit the orchestrator's model)"; return 1
  fi
  case "${lower}" in
    *haiku*) fail "${label}: model ${m}: Haiku is banned; use claude-sonnet-4-6 with effort low"; return 1 ;;
  esac
  if printf '%s\n' "${lower}" | grep -Ex '(opus|sonnet|fable|haiku|best|default|opusplan|inherit)(\[1m\])?' >/dev/null; then
    fail "${label}: model alias ${m}: use a full model ID (aliases resolve to other models)"; return 1
  fi
  case " ${ALLOWED_MODELS} " in
    *" ${m} "*) return 0 ;;
  esac
  fail "${label}: model ${m} is not an allowed full ID (${ALLOWED_MODELS})"
  return 1
}

echo
echo "-- 3. Roster agents in ${REPO}/.claude/agents"
AGENTS_DIR="${REPO}/.claude/agents"
if [ ! -d "${AGENTS_DIR}" ]; then
  fail "missing ${AGENTS_DIR}: install with scripts/init-mission.sh or copy skills/mission/agents/*.md"
else
  while IFS='|' read -r name emodel eeffort access; do
    [ -n "${name}" ] || continue
    f="${AGENTS_DIR}/${name}.md"
    if [ ! -f "${f}" ]; then
      fail "${name}: missing ${f}"
      continue
    fi
    errs=0
    fname="$(fm_value "${f}" name)"
    model="$(fm_value "${f}" model)"
    effort="$(fm_value "${f}" effort)"
    tools="$(fm_value "${f}" tools)"
    if [ "${fname}" != "${name}" ]; then
      fail "${name}: frontmatter name is <${fname:-missing}>, expected ${name}"; errs=1
    fi
    if check_model "${name}" "${model}"; then
      if [ "${model}" != "${emodel}" ]; then
        fail "${name}: model ${model}, roster says ${emodel}"; errs=1
      fi
    else
      errs=1
    fi
    if [ -z "${effort}" ]; then
      fail "${name}: no effort field (defaults to high; roster says ${eeffort})"; errs=1
    elif [ "${effort}" != "${eeffort}" ]; then
      fail "${name}: effort ${effort}, roster says ${eeffort}"; errs=1
    fi
    if [ "${access}" = "ro" ]; then
      if [ -z "${tools}" ]; then
        fail "${name}: read-only agent has no tools field (would inherit write tools)"; errs=1
      else
        norm=",$(printf '%s' "${tools}" | tr -d ' \t'),"
        case "${norm}" in
          *,Edit,*|*,Write,*|*,MultiEdit,*|*,NotebookEdit,*)
            fail "${name}: read-only agent declares write tools (${tools})"; errs=1 ;;
        esac
      fi
    elif [ -z "${tools}" ]; then
      warn "${name}: no tools field (inherits all tools)"
    fi
    if [ "${errs}" -eq 0 ]; then
      pass "${name}: ${model} · ${effort} · ${access}"
    fi
  done <<< "${EXPECTED}"

  for f in "${AGENTS_DIR}"/mission-*.md; do
    [ -f "${f}" ] || continue
    stem="$(basename "${f}" .md)"
    if ! printf '%s\n' "${EXPECTED}" | grep "^${stem}|" >/dev/null; then
      warn "${stem}: not in the roster (conventions §7); do not invent agent names"
      check_model "${stem}" "$(fm_value "${f}" model)" || true
    fi
  done
fi

echo
echo "-- 4. Model table (conventions §6 · USD per MTok: input · cache read · output)"
printf '  %-3s %-18s %-22s %s\n' "Tier" "Model ID" "in · cache · out" "Efforts"
printf '  %-3s %-18s %-22s %s\n' "F" "claude-fable-5-1" "10.00 · 0.25 · 50.00" "medium, high"
printf '  %-3s %-18s %-22s %s\n' "O" "claude-opus-4-8" "5.00 · 0.50 · 25.00" "medium, high, xhigh (degraded orchestrator only)"
printf '  %-3s %-18s %-22s %s\n' "S" "claude-sonnet-4-6" "3.00 · 0.30 · 15.00" "low, medium, high"
echo "  No Haiku. No aliases. The Agent tool may override model per call, never effort."
echo "  Orchestrator: claude-fable-5-1 medium on M/L/XL (high at intake, spec/design gates, adjudication); claude-opus-4-8 high on S."
echo
echo "  Roster (agent · model · effort · access):"
while IFS='|' read -r name emodel eeffort access; do
  printf '  %-26s %-18s %-7s %s\n' "${name}" "${emodel}" "${eeffort}" "${access}"
done <<< "${EXPECTED}"

echo
echo "== Summary: ${FAILS} hard failure(s), ${WARNS} warning(s)"
if [ "${FAILS}" -gt 0 ]; then
  echo "   Fix the failures (or pick the Degraded profile with --allow-degraded and a D-entry), then re-run."
  exit 1
fi
echo "   Next (PF1, M+): spawn one probe per model ID (mission-scout, mission-reviewer, mission-strategist-review;"
echo "   prompt: Reply OK) and confirm the answering models in /usage or headless JSON. Save this output to .mission/logs/preflight.txt."
exit 0
