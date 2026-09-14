#!/usr/bin/env bash
# init-mission.sh — scaffold .mission/ in a target repository for a mission of a given class.
# Never overwrites existing files. Installs roster agents into .claude/agents/ without overwriting
# (unless --force-agents). Prints the settings snippets to merge; never edits .claude/settings.json itself.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: init-mission.sh --class S|M|L|XL [--repo PATH] [--autonomous] [--force-agents] [--no-agents] [--dry-run]

Creates <repo>/.mission/ with the templates the class needs (references/shapes-and-scope.md §3),
copies the skill's scripts into .mission/bin/ (so hooks and checks also work in cloud runs),
installs roster agents into <repo>/.claude/agents/, adds .mission/tmp/ to .gitignore, and prints
next steps (merge hook + guardrail settings, run preflight).

  --class         mission class (required)
  --repo          target repository (default: current directory)
  --autonomous    write autonomous=1 and enforce_stop=1 to .mission/config
  --force-agents  overwrite existing .claude/agents/mission-*.md and Explore.md
  --no-agents     do not install agents
  --dry-run       print what would be created, change nothing
EOF
}

CLASS=""
REPO="."
AUTONOMOUS=0
FORCE_AGENTS=0
NO_AGENTS=0
DRY_RUN=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --class) CLASS="${2:-}"; shift 2 ;;
    --repo) REPO="${2:-}"; shift 2 ;;
    --autonomous) AUTONOMOUS=1; shift ;;
    --force-agents) FORCE_AGENTS=1; shift ;;
    --no-agents) NO_AGENTS=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

case "${CLASS}" in
  S|M|L|XL) ;;
  *) echo "--class must be S, M, L or XL" >&2; usage >&2; exit 2 ;;
esac
if [ ! -d "${REPO}" ]; then
  echo "repo not found: ${REPO}" >&2
  exit 2
fi

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="$(cd "${REPO}" && pwd)"
MISSION="${REPO}/.mission"
T="${SKILL_DIR}/templates"

created=0
skipped=0
missing=0

run() {
  if [ "${DRY_RUN}" -eq 1 ]; then
    echo "[dry-run] $*"
  else
    "$@"
  fi
}

mkdirp() {
  if [ ! -d "$1" ]; then
    run mkdir -p "$1"
  fi
}

# copy_template <template relative path> <destination relative to .mission>
copy_template() {
  local src="${T}/$1"
  local dst="${MISSION}/$2"
  if [ ! -f "${src}" ]; then
    echo "  missing template (skipped): templates/$1" >&2
    missing=$((missing + 1))
    return 0
  fi
  if [ -e "${dst}" ]; then
    echo "  exists (kept): .mission/$2"
    skipped=$((skipped + 1))
    return 0
  fi
  mkdirp "$(dirname "${dst}")"
  run cp "${src}" "${dst}"
  echo "  created: .mission/$2"
  created=$((created + 1))
}

# copy_script <script name> <destination relative to .mission>
copy_script() {
  local src="${SKILL_DIR}/scripts/$1"
  local dst="${MISSION}/$2"
  if [ ! -f "${src}" ]; then
    echo "  missing script (skipped): scripts/$1" >&2
    missing=$((missing + 1))
    return 0
  fi
  if [ -e "${dst}" ]; then
    echo "  exists (kept): .mission/$2"
    skipped=$((skipped + 1))
    return 0
  fi
  mkdirp "$(dirname "${dst}")"
  run cp "${src}" "${dst}"
  run chmod +x "${dst}"
  echo "  created: .mission/$2"
  created=$((created + 1))
}

write_if_absent() {
  local dst="${MISSION}/$1"
  local content="$2"
  if [ -e "${dst}" ]; then
    echo "  exists (kept): .mission/$1"
    skipped=$((skipped + 1))
    return 0
  fi
  if [ "${DRY_RUN}" -eq 1 ]; then
    echo "[dry-run] write .mission/$1"
  else
    mkdir -p "$(dirname "${dst}")"
    printf '%s\n' "${content}" > "${dst}"
  fi
  echo "  created: .mission/$1"
  created=$((created + 1))
}

echo "Scaffolding .mission/ for class ${CLASS} in ${REPO}"
mkdirp "${MISSION}"
mkdirp "${MISSION}/tmp"
mkdirp "${MISSION}/logs"

write_if_absent "config" "class=${CLASS}
profile=standard
autonomous=${AUTONOMOUS}
enforce_stop=${AUTONOMOUS}"

write_if_absent "frozen-paths.txt" "# Globs the implementer may read but not write. One per line. Test author adds paths after proving tests red.
# Examples (uncomment what applies):
# tests/acceptance/**
# tests/regression/**
# tests/golden/**
# playwright.config.*
# vitest.config.*
# .github/workflows/**
# .claude/hooks/**
# .claude/settings.json
# (.mission/acceptance.json is NOT frozen: the orchestrator transcribes verifier verdicts into it; the test-diff
#  audit and check.sh tamper guard protect it instead.)"

# Every class
copy_template "PROFILE.yaml" "PROFILE.yaml"
copy_template "STATUS.md" "STATUS.md"
copy_script "check.sh" "check.sh"
for s in session-start.sh stop-check.sh memory-lint.sh protect-frozen.sh frozen-manifest.sh test-diff-grep.sh \
         flake-runs.sh check-ownership.sh validate-registry.py probe-signals.sh preflight.sh; do
  copy_script "${s}" "bin/${s}"
done

if [ "${CLASS}" = "S" ]; then
  copy_template "TASK-CARD.md" "TASK-CARD.md"
  copy_template "STATE.md" "STATE.md"
else
  for f in CHARTER.md SPEC.md ASSUMPTIONS.md requirements.yaml acceptance.json TEST-PLAN.md STATE.md DECISIONS.md \
           LESSONS-INBOX.md BUDGET.md PLAN.md HANDOFF.md RESEARCH.md; do
    copy_template "${f}" "${f}"
  done
  copy_template "CONTEXT.md" "CONTEXT.md"
  mkdirp "${MISSION}/loops"
  mkdirp "${MISSION}/reviews"
  mkdirp "${MISSION}/investigations"
  mkdirp "${MISSION}/verification"
  mkdirp "${MISSION}/archive"
  mkdirp "${MISSION}/research"
fi

if [ "${CLASS}" = "L" ] || [ "${CLASS}" = "XL" ]; then
  copy_template "CONTRACTS.md" "CONTRACTS.md"
  for f in BACKEND.md FRONTEND.md MIGRATION.md WEBSITE-BRIEF.md; do
    copy_template "design/${f}" "design/templates/${f}"
  done
  copy_template "design/SCREEN.md" "design/templates/SCREEN.md"
  copy_template "design/ADR.md" "design/templates/ADR.md"
  mkdirp "${MISSION}/design/screens"
  mkdirp "${MISSION}/design/adr"
  mkdirp "${MISSION}/lanes"
  copy_template "verification/matrix.web.yaml" "verification/templates/matrix.web.yaml"
  copy_template "verification/matrix.ios.yaml" "verification/templates/matrix.ios.yaml"
fi

# .gitignore
GI="${REPO}/.gitignore"
if [ -f "${GI}" ] && grep -qxF ".mission/tmp/" "${GI}"; then
  :
else
  if [ "${DRY_RUN}" -eq 1 ]; then
    echo "[dry-run] append .mission/tmp/ to .gitignore"
  else
    printf '\n# mission scratch\n.mission/tmp/\n' >> "${GI}"
    echo "  updated: .gitignore (.mission/tmp/)"
  fi
fi

# Agents
if [ "${NO_AGENTS}" -eq 0 ]; then
  AGENTS_SRC="${SKILL_DIR}/agents"
  AGENTS_DST="${REPO}/.claude/agents"
  if [ -d "${AGENTS_SRC}" ]; then
    mkdirp "${AGENTS_DST}"
    for a in "${AGENTS_SRC}"/*.md; do
      [ -f "${a}" ] || continue
      name="$(basename "${a}")"
      if [ -e "${AGENTS_DST}/${name}" ] && [ "${FORCE_AGENTS}" -eq 0 ]; then
        echo "  agent exists (kept): .claude/agents/${name}"
        continue
      fi
      run cp "${a}" "${AGENTS_DST}/${name}"
      echo "  installed agent: .claude/agents/${name}"
    done
  else
    echo "  no agents directory in skill (skipped)" >&2
  fi
fi

echo
echo "Done: ${created} created, ${skipped} kept, ${missing} missing templates/scripts."
cat <<EOF

Next steps (the orchestrator does these; nothing below was applied automatically):
1. Merge hook wiring into .claude/settings.json:          ${T}/settings.hooks.json
2. Merge guardrail permissions into .claude/settings.json: ${T}/settings.guardrails.json
3. Run preflight:                                          .mission/bin/preflight.sh
4. Fill .mission/PROFILE.yaml and the STATUS.md header, then continue Phase 0 in SKILL.md.
EOF
if [ "${missing}" -gt 0 ]; then
  exit 3
fi
