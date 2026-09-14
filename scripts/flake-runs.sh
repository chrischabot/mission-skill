#!/usr/bin/env bash
# flake-runs.sh — statistical proof of a fix for an intermittent failure (references/debugging.md PRF-02;
# templates/investigation.md P4; references/testing.md E-5). Computes n = ceil(ln(alpha) / ln(1 - p)) consecutive
# clean runs, doubles n when state cannot be fully reset between runs, then runs the command n times and stops at the
# first failure. The verdict comes from exit codes, never from a model. Part of the mission skill (installed into
# .mission/bin/). python3 stdlib for the math. No network, no git writes.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: flake-runs.sh --p <failure-rate> [--alpha <a>] [--no-reset] [--reset <cmd>] [--log-dir <dir>] -- <command...>
       flake-runs.sh --p <failure-rate> [--alpha <a>] [--no-reset] --dry-run
       flake-runs.sh --help

--p RATE       baseline failure rate measured on the UNFIXED code (>=5 observed failures), as a decimal (0.02) or a
               fraction (1/50). 0 < RATE < 1.
--alpha A      risk of wrongly declaring the fix good. Default 0.05. Use 0.01 for money, auth, data integrity or
               concurrency primitives. 0 < A < 1.
--no-reset     state cannot be fully reset between runs (warm caches, reused simulator, persisted DB): n is doubled.
--reset CMD    optional shell command run (bash -c) before every run to reset state; a failing reset aborts with exit 2.
--log-dir DIR  where to keep the failing run's output (default: a temp file whose path is printed).
--dry-run      print n only and exit 0 (the verifier uses this to re-derive n).

n = ceil(ln(alpha) / ln(1 - p)), doubled with --no-reset. Examples (alpha 0.05 / 0.01):
  p = 1/10 -> 29 / 44    p = 1/50 -> 149 / 228    p = 1/200 -> 598 / 919

Runs the command with stdin from /dev/null and output captured per run; wrap it in `timeout` if a run can hang.
Output: "flake-runs: n=<n> ..." then "PASS <n>/<n>", or "FAIL at run <k>" plus the last 20 lines of that run.
Exit: 0 all n runs passed (or --dry-run) · 1 a run failed · 2 usage error, python3 missing or reset failed.
EOF
}

P=""
ALPHA="0.05"
NO_RESET=0
RESET_CMD=""
LOG_DIR=""
DRY_RUN=0
HAVE_CMD=0

while [ "${#}" -gt 0 ]; do
  case "${1}" in
    -h|--help) usage; exit 0 ;;
    --p) [ "${#}" -ge 2 ] || { echo "flake-runs: --p needs a value" >&2; exit 2; }; P="${2}"; shift 2 ;;
    --alpha) [ "${#}" -ge 2 ] || { echo "flake-runs: --alpha needs a value" >&2; exit 2; }; ALPHA="${2}"; shift 2 ;;
    --no-reset) NO_RESET=1; shift ;;
    --reset) [ "${#}" -ge 2 ] || { echo "flake-runs: --reset needs a value" >&2; exit 2; }; RESET_CMD="${2}"; shift 2 ;;
    --log-dir) [ "${#}" -ge 2 ] || { echo "flake-runs: --log-dir needs a value" >&2; exit 2; }; LOG_DIR="${2}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --) shift; HAVE_CMD=1; break ;;
    *) echo "flake-runs: unknown argument ${1} (see --help)" >&2; exit 2 ;;
  esac
done

if [ -z "${P}" ]; then
  echo "flake-runs: --p is required (see --help)" >&2
  exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "flake-runs: python3 is required for the sample-size math" >&2
  exit 2
fi

PY_MATH='
import math
import sys
from fractions import Fraction


def parse(raw, name):
    try:
        value = Fraction(raw.strip())
    except (ValueError, ZeroDivisionError):
        sys.stderr.write("flake-runs: %s must be a decimal or a fraction, got %r\n" % (name, raw))
        sys.exit(2)
    if not (0 < value < 1):
        sys.stderr.write("flake-runs: %s must be strictly between 0 and 1, got %s\n" % (name, raw))
        sys.exit(2)
    return float(value)


p = parse(sys.argv[1], "--p")
alpha = parse(sys.argv[2], "--alpha")
n = math.ceil(math.log(alpha) / math.log(1.0 - p) - 1e-9)
print(max(n, 1))
'

if ! N="$(python3 -c "${PY_MATH}" "${P}" "${ALPHA}")"; then
  exit 2
fi

if [ "${NO_RESET}" -eq 1 ]; then
  N=$((N * 2))
fi

if [ "${DRY_RUN}" -eq 1 ]; then
  echo "${N}"
  exit 0
fi

if [ "${HAVE_CMD}" -ne 1 ] || [ "${#}" -eq 0 ]; then
  echo "flake-runs: missing -- <command...> (or use --dry-run)" >&2
  exit 2
fi
CMD=("${@}")

RESET_LABEL="yes"
if [ "${NO_RESET}" -eq 1 ]; then
  RESET_LABEL="no (n doubled)"
fi
echo "flake-runs: n=${N} p=${P} alpha=${ALPHA} state reset: ${RESET_LABEL}"

LOG="$(mktemp "${TMPDIR:-/tmp}/flake-runs.XXXXXX")"
KEEP_LOG=0
cleanup() {
  if [ "${KEEP_LOG}" -eq 0 ]; then
    rm -f "${LOG}"
  fi
}
trap cleanup EXIT

i=1
while [ "${i}" -le "${N}" ]; do
  if [ -n "${RESET_CMD}" ]; then
    if ! bash -c "${RESET_CMD}" </dev/null >"${LOG}" 2>&1; then
      KEEP_LOG=1
      echo "flake-runs: reset command failed before run ${i} (log: ${LOG})" >&2
      exit 2
    fi
  fi
  if ! "${CMD[@]}" </dev/null >"${LOG}" 2>&1; then
    KEEP_LOG=1
    KEPT="${LOG}"
    if [ -n "${LOG_DIR}" ]; then
      mkdir -p "${LOG_DIR}"
      KEPT="${LOG_DIR}/flake-run-${i}.log"
      cp "${LOG}" "${KEPT}"
      KEEP_LOG=0
    fi
    echo "FAIL at run ${i}"
    echo "flake-runs: ${i} of ${N} runs attempted; log: ${KEPT}"
    echo "--- last 20 lines of run ${i} ---" >&2
    tail -n 20 "${KEPT}" >&2 || true
    exit 1
  fi
  i=$((i + 1))
done

echo "PASS ${N}/${N}"
exit 0
