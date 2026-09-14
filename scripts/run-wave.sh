#!/usr/bin/env bash
# run-wave.sh — headless lane runner: one `claude -p` process per lane of a wave, bounded concurrency, time box,
# per-lane result files, summary table (references/swarms.md SW7, SW8, SW22, SW28, P4).
# Part of the mission skill (skills/mission/scripts/; installed into .mission/bin/). No network of its own (the
# `claude` processes it starts do use the network), no destructive git operations, never `--bare`.
#
# Flags passed to `claude`, and why each is justified:
#   -p "<brief>"            print/headless mode (https://code.claude.com/docs/en/headless)
#   --model <full id>       pin the model by full ID; aliases drift (conventions §6)
#   --output-format json    JSON result incl. total_cost_usd for the BUDGET ledger (headless docs)
#   --max-budget-usd <usd>  only when --max-budget-usd is given here; version-dependent, UNVERIFIED for your install:
#                           check `claude --help` first (models-and-cost.md, orchestration.md L5)
#   --worktree <lane-id>    isolated checkout .claude/worktrees/<lane-id> (https://code.claude.com/docs/en/worktrees).
#                           UNVERIFIED: whether an existing worktree name is reused; this script therefore runs an
#                           existing .claude/worktrees/<lane-id> in place (cd) without --worktree.
# Deliberately NOT used: --bare (skips skills, agents, hooks, CLAUDE.md; orchestration.md L6), --agent (UNVERIFIED for
# headless), permission-bypass flags (pre-allowlist commands in .claude/settings.json instead; swarms.md SW10).
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: run-wave.sh --wave FILE [--parallel N] [--timeout-min M] [--model ID] [--max-budget-usd USD]
                   [--lanes-dir DIR] [--only LANE[,LANE...]] [--force] [--skip-ownership-check] [--dry-run]
       run-wave.sh --help

Runs every lane of a wave headless, from the PRIMARY checkout, one `claude -p` process per lane:
  - wave file: same format as check-ownership.sh (`<lane-id> <glob> [<glob> ...]`, # comments)
  - prompt:    the full content of <lanes-dir>/<lane-id>/brief.md (brief.md + lane-contract.md, filled)
  - model:     <lanes-dir>/<lane-id>/model (one line, full ID) if present, else --model (default claude-sonnet-4-6).
               Allowed: claude-sonnet-4-6, claude-opus-4-8, claude-fable-5-1 (Fable lanes print a warning: SWM1)
  - isolation: existing .claude/worktrees/<lane-id> → run inside it (cd, no --worktree). RECOMMENDED: pre-create each
               lane worktree from the primary checkout so the lane branch starts at the integration tip (SW12):
                 git worktree add .claude/worktrees/<lane-id> -b claude/<mission>/<lane-id>-<slug> claude/<mission>/integration
               No worktree yet → `claude -p ... --worktree <lane-id>` (Claude Code picks the base and names the branch
               worktree-<lane-id>; the brief must then tell the lane which branch to create)
  - time box:  `timeout` (or `gtimeout`) sends SIGTERM after M minutes (Claude Code exits 143 and leaves a resumable
               turn), SIGKILL 60 s later; absent → no time box (warned). SIGTERM, not SIGINT: background jobs of a
               non-interactive shell ignore SIGINT
Writes per lane (in the primary checkout): result.json (claude stdout), stderr.log, exit_code, run.meta
  (key=value: lane, model, started, ended, seconds, exit_code, cost_usd).
Idempotent: a lane whose exit_code is 0 and result.json exists is skipped unless --force. Retrying a failed lane
  reruns it in its existing worktree, where the lane resumes from .mission/lanes/<lane-id>/progress.md.

Options:
  --wave FILE              wave file (required)
  --parallel N             max concurrent lanes (default 4; keep within the class writer cap S2 · M4 · L8 · XL12)
  --timeout-min M          time box per lane in minutes (default 60)
  --model ID               default model for lanes without a model file (default claude-sonnet-4-6)
  --max-budget-usd USD     pass --max-budget-usd USD to every lane (per-lane cap)
  --lanes-dir DIR          default .mission/lanes (relative to the repository root)
  --only LIST              comma-separated lane ids to run (others skipped)
  --force                  rerun lanes that already exited 0
  --skip-ownership-check   do not run check-ownership.sh first (reader-only waves)
  --dry-run                print the commands that would run; start nothing, write nothing

Exit: 0 all lanes exit 0 (or skipped) · 1 at least one lane failed or timed out · 2 usage or preflight error ·
      3 ownership overlap (check-ownership.sh exit 1)
After the wave: validate each return (swarms.md P5), dispatch verifiers, integrate serially, clean up worktrees:
  git worktree unlock .claude/worktrees/<lane-id>; git worktree remove .claude/worktrees/<lane-id>   (SW18)
EOF
}

WAVE=""
PARALLEL=4
TIMEOUT_MIN=60
DEFAULT_MODEL="claude-sonnet-4-6"
MAX_BUDGET=""
LANES_DIR=".mission/lanes"
ONLY=""
FORCE=0
SKIP_OWNERSHIP=0
DRY_RUN=0

need_arg() {
  if [ "${2}" -lt 2 ]; then
    echo "run-wave: ${1} needs a value (see --help)" >&2
    exit 2
  fi
}

while [ "${#}" -gt 0 ]; do
  case "${1}" in
    -h|--help) usage; exit 0 ;;
    --wave) need_arg "${1}" "${#}"; WAVE="${2}"; shift 2 ;;
    --parallel) need_arg "${1}" "${#}"; PARALLEL="${2}"; shift 2 ;;
    --timeout-min) need_arg "${1}" "${#}"; TIMEOUT_MIN="${2}"; shift 2 ;;
    --model) need_arg "${1}" "${#}"; DEFAULT_MODEL="${2}"; shift 2 ;;
    --max-budget-usd) need_arg "${1}" "${#}"; MAX_BUDGET="${2}"; shift 2 ;;
    --lanes-dir) need_arg "${1}" "${#}"; LANES_DIR="${2}"; shift 2 ;;
    --only) need_arg "${1}" "${#}"; ONLY="${2}"; shift 2 ;;
    --force) FORCE=1; shift ;;
    --skip-ownership-check) SKIP_OWNERSHIP=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) echo "run-wave: unknown argument ${1} (see --help)" >&2; exit 2 ;;
  esac
done

[ -n "${WAVE}" ] || { usage >&2; exit 2; }
[ -f "${WAVE}" ] || { echo "run-wave: wave file not found: ${WAVE}" >&2; exit 2; }
case "${PARALLEL}" in ''|*[!0-9]*|0) echo "run-wave: --parallel must be a positive integer" >&2; exit 2 ;; esac
case "${TIMEOUT_MIN}" in ''|*[!0-9]*|0) echo "run-wave: --timeout-min must be a positive integer" >&2; exit 2 ;; esac
if [ "${PARALLEL}" -gt 16 ]; then
  echo "run-wave: --parallel ${PARALLEL} exceeds 16 (runtime ceiling; swarms.md SW26)" >&2
  exit 2
fi
if [ -n "${MAX_BUDGET}" ]; then
  case "${MAX_BUDGET}" in
    *[!0-9.]*|.|*.*.*) echo "run-wave: --max-budget-usd must be a number like 5 or 2.50" >&2; exit 2 ;;
  esac
fi

check_model() {
  case "${1}" in
    claude-sonnet-4-6|claude-opus-4-8) return 0 ;;
    claude-fable-5-1)
      echo "run-wave: WARNING lane model claude-fable-5-1: lanes never run on Fable by default (swarms.md SWM1)" >&2
      return 0 ;;
    *) echo "run-wave: model '${1}' is not a pinned full ID (claude-sonnet-4-6 | claude-opus-4-8 | claude-fable-5-1)" >&2
       return 1 ;;
  esac
}
check_model "${DEFAULT_MODEL}" || exit 2

# ---- repository root and primary-checkout guard (SW13) ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WAVE_ABS="$(cd "$(dirname "${WAVE}")" && pwd)/$(basename "${WAVE}")"
ROOT=""
if command -v git >/dev/null 2>&1; then
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
fi
if [ -n "${ROOT}" ]; then
  cd "${ROOT}"
  GIT_DIR_ABS="$(cd "$(git rev-parse --git-dir)" && pwd -P)"
  GIT_COMMON_ABS="$(cd "$(git rev-parse --git-common-dir)" && pwd -P)"
  if [ "${GIT_DIR_ABS}" != "${GIT_COMMON_ABS}" ]; then
    if [ "${DRY_RUN}" -eq 1 ]; then
      echo "run-wave: WARNING inside a linked worktree; real runs must start from the primary checkout (SW13)" >&2
    else
      echo "run-wave: refusing to run inside a linked worktree; run from the primary checkout (SW13, issue #47548)" >&2
      exit 2
    fi
  fi
else
  ROOT="$(pwd)"
  echo "run-wave: WARNING not inside a git work tree; --worktree isolation will not work here" >&2
fi
cd "${ROOT}"

if [ -n "${CLAUDE_CODE_SUBAGENT_MODEL:-}" ]; then
  echo "run-wave: WARNING CLAUDE_CODE_SUBAGENT_MODEL is set and overrides sub-agent models (preflight.sh)" >&2
fi

# ---- lanes from the wave file (dedupe, --only filter, id validation) ----
LANES=""
line_no=0
while IFS= read -r raw || [ -n "${raw}" ]; do
  line_no=$((line_no + 1))
  line="${raw%%#*}"
  set -f
  # shellcheck disable=SC2086
  set -- ${line}
  set +f
  [ "${#}" -gt 0 ] || continue
  lane="${1}"
  case "${lane}" in
    *[!A-Za-z0-9._-]*|.*) echo "run-wave: line ${line_no}: bad lane id '${lane}'" >&2; exit 2 ;;
  esac
  if [ -n "${ONLY}" ]; then
    case ",${ONLY}," in *",${lane},"*) ;; *) continue ;; esac
  fi
  case " ${LANES} " in *" ${lane} "*) ;; *) LANES="${LANES} ${lane}" ;; esac
done < "${WAVE_ABS}"
LANES="${LANES# }"
[ -n "${LANES}" ] || { echo "run-wave: no lanes selected from ${WAVE}" >&2; exit 2; }

# ---- ownership check first (SW11) ----
if [ "${SKIP_OWNERSHIP}" -eq 0 ]; then
  if [ -f "${SCRIPT_DIR}/check-ownership.sh" ]; then
    own_rc=0
    bash "${SCRIPT_DIR}/check-ownership.sh" "${WAVE_ABS}" || own_rc="${?}"
    if [ "${own_rc}" -eq 1 ]; then echo "run-wave: NO-GO ownership overlap; re-partition first" >&2; exit 3; fi
    if [ "${own_rc}" -ne 0 ]; then echo "run-wave: check-ownership.sh failed (exit ${own_rc})" >&2; exit 2; fi
  else
    echo "run-wave: WARNING check-ownership.sh not found next to this script; ownership not checked" >&2
  fi
fi

# ---- preflight per lane: brief present, model valid ----
MISSING=0
for lane in ${LANES}; do
  if [ ! -f "${LANES_DIR}/${lane}/brief.md" ]; then
    echo "run-wave: MISSING ${LANES_DIR}/${lane}/brief.md" >&2
    MISSING=1
  fi
  if [ -f "${LANES_DIR}/${lane}/model" ]; then
    lane_model="$(awk 'NF { print; exit }' "${LANES_DIR}/${lane}/model")"
    check_model "${lane_model}" || MISSING=1
  fi
done
if [ "${MISSING}" -eq 1 ] && [ "${DRY_RUN}" -eq 0 ]; then
  echo "run-wave: preflight failed; nothing started" >&2
  exit 2
fi

TIMEOUT_BIN=""
if command -v timeout >/dev/null 2>&1; then TIMEOUT_BIN="timeout"
elif command -v gtimeout >/dev/null 2>&1; then TIMEOUT_BIN="gtimeout"
else echo "run-wave: WARNING no timeout/gtimeout; lanes have no time box (watch progress.md mtimes, SW22)" >&2
fi
if [ "${DRY_RUN}" -eq 0 ] && ! command -v claude >/dev/null 2>&1; then
  echo "run-wave: claude CLI not found on PATH" >&2
  exit 2
fi

lane_model_of() {
  if [ -f "${LANES_DIR}/${1}/model" ]; then awk 'NF { print; exit }' "${LANES_DIR}/${1}/model"; else printf '%s' "${DEFAULT_MODEL}"; fi
}

already_done() {
  [ "${FORCE}" -eq 0 ] && [ -f "${LANES_DIR}/${1}/result.json" ] && [ -f "${LANES_DIR}/${1}/exit_code" ] &&
    [ "$(awk 'NF { print; exit }' "${LANES_DIR}/${1}/exit_code")" = "0" ]
}

print_cmd() {
  local lane="${1}" model="${2}" wt=".claude/worktrees/${1}" prefix="" suffix=""
  if [ -n "${TIMEOUT_BIN}" ]; then prefix="${TIMEOUT_BIN} -s TERM -k 60 ${TIMEOUT_MIN}m "; fi
  if [ -n "${MAX_BUDGET}" ]; then suffix=" --max-budget-usd ${MAX_BUDGET}"; fi
  if [ -d "${wt}" ]; then
    printf '(cd %s && %sclaude -p "$(cat %s)" --model %s --output-format json%s) < /dev/null > %s 2> %s\n' \
      "${wt}" "${prefix}" "${ROOT}/${LANES_DIR}/${lane}/brief.md" "${model}" "${suffix}" \
      "${LANES_DIR}/${lane}/result.json" "${LANES_DIR}/${lane}/stderr.log"
  else
    printf '%sclaude -p "$(cat %s)" --model %s --output-format json%s --worktree %s < /dev/null > %s 2> %s\n' \
      "${prefix}" "${LANES_DIR}/${lane}/brief.md" "${model}" "${suffix}" "${lane}" \
      "${LANES_DIR}/${lane}/result.json" "${LANES_DIR}/${lane}/stderr.log"
  fi
}

run_lane() {
  local lane="${1}" model="${2}"
  local dir="${ROOT}/${LANES_DIR}/${lane}" wt="${ROOT}/.claude/worktrees/${1}" workdir use_wt rc=0
  local started ended started_iso cost=""
  if [ -d "${wt}" ]; then workdir="${wt}"; use_wt=0; else workdir="${ROOT}"; use_wt=1; fi
  set -- -p "$(cat "${dir}/brief.md")" --model "${model}" --output-format json
  if [ -n "${MAX_BUDGET}" ]; then set -- "${@}" --max-budget-usd "${MAX_BUDGET}"; fi
  if [ "${use_wt}" -eq 1 ]; then set -- "${@}" --worktree "${lane}"; fi
  started="$(date +%s)"
  started_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if [ -n "${TIMEOUT_BIN}" ]; then
    ( cd "${workdir}" && "${TIMEOUT_BIN}" -s TERM -k 60 "${TIMEOUT_MIN}m" claude "${@}" ) \
      < /dev/null > "${dir}/result.json.tmp" 2> "${dir}/stderr.log" || rc="${?}"
  else
    ( cd "${workdir}" && claude "${@}" ) < /dev/null > "${dir}/result.json.tmp" 2> "${dir}/stderr.log" || rc="${?}"
  fi
  ended="$(date +%s)"
  mv "${dir}/result.json.tmp" "${dir}/result.json"
  printf '%s\n' "${rc}" > "${dir}/exit_code"
  if command -v jq >/dev/null 2>&1; then
    cost="$(jq -r '.total_cost_usd // empty' "${dir}/result.json" 2>/dev/null || true)"
  elif command -v python3 >/dev/null 2>&1; then
    cost="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("total_cost_usd", ""))' "${dir}/result.json" 2>/dev/null || true)"
  fi
  {
    printf 'lane=%s\nmodel=%s\nstarted=%s\nseconds=%s\nexit_code=%s\ncost_usd=%s\n' \
      "${lane}" "${model}" "${started_iso}" "$((ended - started))" "${rc}" "${cost:-unknown}"
    printf 'ended=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "${dir}/run.meta"
}

# ---- dispatch with bounded concurrency ----
JOBS_DIR="$(mktemp -d "${TMPDIR:-/tmp}/run-wave.XXXXXX")"
trap 'rm -rf "${JOBS_DIR}"' EXIT
RUNNING=0
count_running() {
  jobs -pr > "${JOBS_DIR}/jobs"
  RUNNING="$(awk 'END { print NR }' "${JOBS_DIR}/jobs")"
}

SKIPPED=" "
for lane in ${LANES}; do
  model="$(lane_model_of "${lane}")"
  if already_done "${lane}"; then
    echo "SKIP ${lane} (exit_code 0 and result.json present; --force to rerun)"
    SKIPPED="${SKIPPED}${lane} "
    continue
  fi
  if [ "${DRY_RUN}" -eq 1 ]; then
    print_cmd "${lane}" "${model}"
    continue
  fi
  count_running
  while [ "${RUNNING}" -ge "${PARALLEL}" ]; do
    sleep 2
    count_running
  done
  echo "START ${lane} model=${model} $(date -u +%H:%M:%SZ)"
  run_lane "${lane}" "${model}" &
done
if [ "${DRY_RUN}" -eq 0 ]; then wait; fi

# ---- summary table ----
meta_get() {
  local key="${1}" file="${2}" l
  [ -f "${file}" ] || return 0
  while IFS= read -r l || [ -n "${l}" ]; do
    case "${l}" in "${key}="*) printf '%s' "${l#*=}"; return 0 ;; esac
  done < "${file}"
  return 0
}

FAILED=0
printf '\n%-16s %-18s %-16s %8s %10s  %s\n' "LANE" "MODEL" "STATUS" "SECONDS" "COST_USD" "RESULT"
for lane in ${LANES}; do
  model="$(lane_model_of "${lane}")"
  meta="${LANES_DIR}/${lane}/run.meta"
  secs="-"; cost="-"; result="-"
  case "${SKIPPED}" in
    *" ${lane} "*) status="SKIPPED(done)" ;;
    *)
      if [ "${DRY_RUN}" -eq 1 ]; then
        status="DRY-RUN"
        [ -f "${LANES_DIR}/${lane}/brief.md" ] || status="MISSING-BRIEF"
      else
        rc="$(meta_get exit_code "${meta}")"
        case "${rc}" in
          0) status="OK" ;;
          124|137) status="TIMEOUT(${rc})"; FAILED=1 ;;
          '') status="NO-RESULT"; FAILED=1 ;;
          *) status="FAILED(${rc})"; FAILED=1 ;;
        esac
      fi ;;
  esac
  if [ -f "${meta}" ] && [ "${status}" != "DRY-RUN" ]; then
    secs="$(meta_get seconds "${meta}")"
    cost="$(meta_get cost_usd "${meta}")"
    result="${LANES_DIR}/${lane}/result.json"
  fi
  printf '%-16s %-18s %-16s %8s %10s  %s\n' "${lane}" "${model}" "${status}" "${secs:--}" "${cost:--}" "${result}"
done

echo
if [ "${DRY_RUN}" -eq 1 ]; then
  echo "Dry run: nothing started, nothing written."
  [ "${MISSING}" -eq 0 ] || exit 2
  exit 0
fi
echo "Next: validate each lane return (swarms.md P5), per-lane verifier, serial integration (P7), then clean up:"
for lane in ${LANES}; do
  echo "  git worktree unlock .claude/worktrees/${lane}; git worktree remove .claude/worktrees/${lane}   # after integration"
done
[ "${FAILED}" -eq 0 ] || exit 1
exit 0
