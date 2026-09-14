#!/usr/bin/env bash
# check.sh: run the executable acceptance checks of one milestone (or all) from <mission dir>/acceptance.json, save
# each output to <mission dir>/logs/<AC-id>-<timestamp>.log, print a summary table, exit non-zero if any check fails.
# NEVER modifies acceptance.json: flipping "passes" is a verifier's job (references/orchestration.md GT4, S7).
# Part of the mission skill (skills/mission/scripts/check.sh; init-mission.sh copies it to .mission/check.sh).
# Needs bash and python3 (stdlib only). Makes no network calls and no git writes itself; it runs the checks' commands.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: check.sh <milestone|all> [--mission-dir DIR]
       check.sh --help

Runs every check in <mission dir>/acceptance.json whose "type" is "executable" and whose "milestone" equals
<milestone> (every executable check for "all"). Each check's "command" runs with bash from the project root (the
parent directory of the mission dir), stdin from /dev/null. An optional numeric "timeout_sec" is enforced when the
`timeout` utility exists (exit 124 = timed out = FAIL). A check without a "command" string counts as FAIL (exit=127).
Output (stdout and stderr) goes to <mission dir>/logs/<AC-id>-<UTC timestamp>.log.

Prints one line per check:  <AC-id> PASS|FAIL exit=<n> log=<path>
then one totals line. Non-executable checks (rubric, live, human) are counted, never run: verifiers grade them.

  --mission-dir DIR   mission directory. Default: ./.mission if it exists; otherwise the directory holding this
                      script (or its parent) when it contains acceptance.json; otherwise ./.mission
  -h, --help          show this help

Exit status: 0 every selected check passed · 1 at least one check failed · 2 usage or input error (missing file,
invalid JSON, no "checks" array, python3 missing) · 3 no executable check matched <milestone> · 4 acceptance.json
changed while the checks ran (tamper guard: treat as stop rule S5, STOP-GUARDRAIL).
A green run is evidence for a verifier, not a verdict. This script never edits acceptance.json.
EOF
}

MILESTONE=""
MISSION_DIR=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --mission-dir)
      if [ "$#" -lt 2 ]; then echo "check.sh: --mission-dir needs a value" >&2; exit 2; fi
      MISSION_DIR="$2"; shift 2 ;;
    --mission-dir=*) MISSION_DIR="${1#--mission-dir=}"; shift ;;
    -*) echo "check.sh: unknown option $1 (see --help)" >&2; exit 2 ;;
    *)
      if [ -n "${MILESTONE}" ]; then echo "check.sh: only one milestone argument is allowed (see --help)" >&2; exit 2; fi
      MILESTONE="$1"; shift ;;
  esac
done
if [ -z "${MILESTONE}" ]; then usage >&2; exit 2; fi

if [ -z "${MISSION_DIR}" ]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [ -d ".mission" ]; then
    MISSION_DIR=".mission"
  elif [ -f "${SCRIPT_DIR}/acceptance.json" ]; then
    MISSION_DIR="${SCRIPT_DIR}"
  elif [ -f "${SCRIPT_DIR}/../acceptance.json" ]; then
    MISSION_DIR="${SCRIPT_DIR}/.."
  else
    MISSION_DIR=".mission"
  fi
fi

if [ ! -f "${MISSION_DIR}/acceptance.json" ]; then
  echo "check.sh: acceptance.json not found in ${MISSION_DIR} (use --mission-dir)" >&2
  exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "check.sh: python3 is required to parse acceptance.json" >&2
  exit 2
fi

MISSION_DIR="$(cd "${MISSION_DIR}" && pwd)"
ACCEPTANCE="${MISSION_DIR}/acceptance.json"
ROOT="$(dirname "${MISSION_DIR}")"
LOG_DIR="${MISSION_DIR}/logs"
mkdir -p "${LOG_DIR}"

BEFORE="$(cksum < "${ACCEPTANCE}")"

LIST="$(mktemp "${TMPDIR:-/tmp}/check-sh.XXXXXX")"
trap 'rm -f "${LIST}"' EXIT

# Emits NUL-separated records: first the count of skipped non-executable checks, then id, command, timeout per check.
if ! python3 - "${ACCEPTANCE}" "${MILESTONE}" > "${LIST}" <<'PY'
import json
import sys

path, milestone = sys.argv[1], sys.argv[2]
try:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
except (OSError, ValueError) as exc:
    sys.stderr.write("check.sh: cannot parse %s: %s\n" % (path, exc))
    sys.exit(2)

checks = data.get("checks") if isinstance(data, dict) else None
if not isinstance(checks, list):
    sys.stderr.write("check.sh: %s has no \"checks\" array\n" % path)
    sys.exit(2)

records = []
skipped = 0
seen = set()
for index, check in enumerate(checks):
    if not isinstance(check, dict):
        sys.stderr.write("check.sh: checks[%d] is not an object (ignored)\n" % index)
        continue
    if milestone != "all" and str(check.get("milestone", "")) != milestone:
        continue
    if check.get("type") != "executable":
        skipped += 1
        continue
    check_id = str(check.get("id") or "checks-%d" % index)
    if check_id in seen:
        sys.stderr.write("check.sh: duplicate check id %s (both run)\n" % check_id)
    seen.add(check_id)
    command = check.get("command")
    if not isinstance(command, str):
        command = ""
    timeout = check.get("timeout_sec")
    try:
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not timeout > 0:
            timeout = ""
        else:
            timeout = str(max(1, int(timeout)))
    except (OverflowError, ValueError):
        timeout = ""
    records.append((check_id, command, timeout))

out = sys.stdout.buffer
out.write(str(skipped).encode("utf-8") + b"\0")
for record in records:
    for field in record:
        out.write(field.replace("\0", "").encode("utf-8") + b"\0")
PY
then
  exit 2
fi

HAVE_TIMEOUT=0
if command -v timeout >/dev/null 2>&1; then HAVE_TIMEOUT=1; fi
TS="$(date -u +%Y%m%dT%H%M%SZ)"

PASSED=0
FAILED=0
TOTAL=0
SUMMARY=""

exec 3< "${LIST}"
SKIPPED=0
IFS= read -r -d '' SKIPPED <&3 || SKIPPED=0

while IFS= read -r -d '' ID <&3 && IFS= read -r -d '' CMD <&3 && IFS= read -r -d '' TMO <&3; do
  TOTAL=$((TOTAL + 1))
  SAFE_ID="$(printf '%s' "${ID}" | tr -c 'A-Za-z0-9._-' '_')"
  LOG="${LOG_DIR}/${SAFE_ID}-${TS}.log"
  n=1
  while [ -e "${LOG}" ]; do
    n=$((n + 1))
    LOG="${LOG_DIR}/${SAFE_ID}-${TS}-${n}.log"
  done
  {
    printf '# check.sh %s · milestone %s\n' "${ID}" "${MILESTONE}"
    printf '# cwd: %s\n' "${ROOT}"
    printf '# started: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf '# timeout_sec: %s\n' "${TMO:-none}"
    printf '# command: %s\n' "${CMD}"
    printf '# ---\n'
  } > "${LOG}"

  if [ -z "${CMD}" ]; then
    printf 'check.sh: this check has no "command" string; counted as FAIL\n' >> "${LOG}"
    RC=127
  elif [ -n "${TMO}" ] && [ "${HAVE_TIMEOUT}" -eq 1 ]; then
    if (cd "${ROOT}" && timeout "${TMO}" bash -c "${CMD}") < /dev/null 3<&- >> "${LOG}" 2>&1; then RC=0; else RC=$?; fi
  else
    if [ -n "${TMO}" ]; then
      printf 'check.sh: timeout utility not found; timeout_sec not enforced\n' >> "${LOG}"
    fi
    if (cd "${ROOT}" && bash -c "${CMD}") < /dev/null 3<&- >> "${LOG}" 2>&1; then RC=0; else RC=$?; fi
  fi

  printf '# ---\n# exit: %s\n# finished: %s\n' "${RC}" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "${LOG}"

  if [ "${RC}" -eq 0 ]; then
    RESULT="PASS"
    PASSED=$((PASSED + 1))
  else
    RESULT="FAIL"
    FAILED=$((FAILED + 1))
  fi
  REL_LOG="${LOG#"${ROOT}"/}"
  LINE="$(printf '%-12s %-4s exit=%-3s log=%s' "${ID}" "${RESULT}" "${RC}" "${REL_LOG}")"
  SUMMARY="${SUMMARY}${LINE}
"
done
exec 3<&-

AFTER="$(cksum < "${ACCEPTANCE}")"

if [ "${TOTAL}" -gt 0 ]; then
  printf '%s' "${SUMMARY}"
fi
printf 'check.sh: milestone=%s passed=%s failed=%s total=%s non-executable-skipped=%s logs=%s\n' \
  "${MILESTONE}" "${PASSED}" "${FAILED}" "${TOTAL}" "${SKIPPED}" "${LOG_DIR#"${ROOT}"/}"

if [ "${BEFORE}" != "${AFTER}" ]; then
  echo "check.sh: TAMPER: acceptance.json changed while checks ran; results are void (stop rule S5)" >&2
  exit 4
fi
if [ "${TOTAL}" -eq 0 ]; then
  echo "check.sh: no executable checks for milestone ${MILESTONE}; nothing proven" >&2
  exit 3
fi
if [ "${FAILED}" -gt 0 ]; then
  exit 1
fi
exit 0
