#!/usr/bin/env bash
# check-ownership.sh — fail when the owned globs of two lanes in one wave can overlap (references/swarms.md SW11, P2).
# Part of the mission skill (skills/mission/scripts/; installed into .mission/bin/). Read-only: no network, no git
# writes, no file changes outside a private temp dir that is removed on exit. Idempotent.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: check-ownership.sh [--no-git] [--files FILE] [--root DIR] <wave-file>
       check-ownership.sh --help

Wave file: one lane per line, whitespace-separated:
    <lane-id> <glob> [<glob> ...]
  e.g.
    T-014 apps/api/src/outfits/** tests/unit/outfits/**
    T-015 apps/ios/Features/Grid/**
  Blank lines and lines starting with # are ignored. A lane id may appear on several lines (globs accumulate).
  Globs cannot contain spaces. Paths are relative to the repository root. Each lane also owns
  .mission/lanes/<lane-id>/** implicitly; do not list it.

Two independent detectors; any hit fails the check:
  1. Literal prefix comparison (always). The literal prefix of a glob is its leading path segments before the first
     segment containing * ? [ or {. Two globs of different lanes conflict when one prefix equals the other or is an
     ancestor directory of it (apps/api/** vs apps/api/src/** -> apps/api is an ancestor of apps/api/src). This is
     conservative: apps/api/*.json vs apps/api/src/** is reported too. Resolve by listing literal paths.
  2. Expansion against real files (inside a git work tree, unless --no-git): every path from
     `git ls-files --cached --others --exclude-standard` (plus --files FILE, one path per line, for declared new
     paths) is matched against every glob; a path matched by two lanes is a conflict. Glob syntax for this detector:
     ** crosses directories, * and ? stay within one segment, [..] and [!..] are classes, a glob without
     metacharacters matches the path itself and everything below it.

Output: one OVERLAP line per conflicting glob pair, then CONFLICT lines per lane pair, then a PASS/FAIL line.
Exit: 0 no overlap · 1 overlap found · 2 usage error (missing file, lane without globs, bad lane id).
EOF
}

NO_GIT=0
EXTRA_FILES=""
ROOT=""
WAVE=""

while [ "${#}" -gt 0 ]; do
  case "${1}" in
    -h|--help) usage; exit 0 ;;
    --no-git) NO_GIT=1; shift ;;
    --files)
      [ "${#}" -ge 2 ] || { echo "check-ownership: --files needs a path" >&2; exit 2; }
      EXTRA_FILES="${2}"; shift 2 ;;
    --root)
      [ "${#}" -ge 2 ] || { echo "check-ownership: --root needs a directory" >&2; exit 2; }
      ROOT="${2}"; shift 2 ;;
    -*) echo "check-ownership: unknown option ${1} (see --help)" >&2; exit 2 ;;
    *)
      [ -z "${WAVE}" ] || { echo "check-ownership: only one wave file allowed" >&2; exit 2; }
      WAVE="${1}"; shift ;;
  esac
done

[ -n "${WAVE}" ] || { usage >&2; exit 2; }
[ -f "${WAVE}" ] || { echo "check-ownership: wave file not found: ${WAVE}" >&2; exit 2; }
if [ -n "${EXTRA_FILES}" ] && [ ! -f "${EXTRA_FILES}" ]; then
  echo "check-ownership: --files not found: ${EXTRA_FILES}" >&2
  exit 2
fi
command -v awk >/dev/null 2>&1 || { echo "check-ownership: awk not found" >&2; exit 2; }

TMP="$(mktemp -d "${TMPDIR:-/tmp}/check-ownership.XXXXXX")"
cleanup() { rm -rf "${TMP}"; }
trap cleanup EXIT

GLOBS_TSV="${TMP}/globs.tsv"
PATHS_TXT="${TMP}/paths.txt"
PAIRS_TXT="${TMP}/pairs.txt"
: > "${GLOBS_TSV}"
: > "${PATHS_TXT}"
: > "${PAIRS_TXT}"

# ---- parse the wave file into parallel arrays (bash 3.2 compatible: no associative arrays) ----
G_LANE=()
G_GLOB=()
LANE_COUNT=0
SEEN_LANES=" "
line_no=0
while IFS= read -r raw || [ -n "${raw}" ]; do
  line_no=$((line_no + 1))
  line="${raw%%#*}"
  # shellcheck disable=SC2086
  set -f
  set -- ${line}
  set +f
  [ "${#}" -gt 0 ] || continue
  lane="${1}"
  shift
  case "${lane}" in
    *[!A-Za-z0-9._-]*) echo "check-ownership: line ${line_no}: bad lane id '${lane}'" >&2; exit 2 ;;
  esac
  if [ "${#}" -eq 0 ]; then
    echo "check-ownership: line ${line_no}: lane ${lane} has no globs" >&2
    exit 2
  fi
  case "${SEEN_LANES}" in
    *" ${lane} "*) ;;
    *) SEEN_LANES="${SEEN_LANES}${lane} "; LANE_COUNT=$((LANE_COUNT + 1)) ;;
  esac
  for g in "${@}"; do
    g="${g#./}"
    G_LANE+=("${lane}")
    G_GLOB+=("${g}")
    printf '%s\t%s\n' "${lane}" "${g}" >> "${GLOBS_TSV}"
  done
done < "${WAVE}"

GLOB_COUNT="${#G_GLOB[@]}"
if [ "${GLOB_COUNT}" -eq 0 ]; then
  echo "check-ownership: no lanes in ${WAVE}" >&2
  exit 2
fi

# ---- detector 1: literal prefix comparison ----
literal_prefix() {
  local rest="${1}" out="" seg
  while [ -n "${rest}" ]; do
    seg="${rest%%/*}"
    if [ "${seg}" = "${rest}" ]; then rest=""; else rest="${rest#*/}"; fi
    case "${seg}" in
      *'*'*|*'?'*|*'['*|*'{'*) break ;;
    esac
    [ -n "${seg}" ] || continue
    if [ -z "${out}" ]; then out="${seg}"; else out="${out}/${seg}"; fi
  done
  printf '%s' "${out}"
}

prefixes_overlap() {
  local a="${1}" b="${2}"
  if [ -z "${a}" ] || [ -z "${b}" ]; then return 0; fi
  if [ "${a}" = "${b}" ]; then return 0; fi
  case "${b}/" in "${a}/"*) return 0 ;; esac
  case "${a}/" in "${b}/"*) return 0 ;; esac
  return 1
}

G_PREFIX=()
i=0
while [ "${i}" -lt "${GLOB_COUNT}" ]; do
  G_PREFIX+=("$(literal_prefix "${G_GLOB[${i}]}")")
  i=$((i + 1))
done

OVERLAPS=0
i=0
while [ "${i}" -lt "${GLOB_COUNT}" ]; do
  j=$((i + 1))
  while [ "${j}" -lt "${GLOB_COUNT}" ]; do
    if [ "${G_LANE[${i}]}" != "${G_LANE[${j}]}" ] && prefixes_overlap "${G_PREFIX[${i}]}" "${G_PREFIX[${j}]}"; then
      printf 'OVERLAP prefix: %s [%s] <-> %s [%s] (literal prefixes "%s" and "%s")\n' \
        "${G_LANE[${i}]}" "${G_GLOB[${i}]}" "${G_LANE[${j}]}" "${G_GLOB[${j}]}" \
        "${G_PREFIX[${i}]:-<root>}" "${G_PREFIX[${j}]:-<root>}"
      printf '%s\n' "${G_LANE[${i}]} ${G_LANE[${j}]}" >> "${PAIRS_TXT}"
      OVERLAPS=$((OVERLAPS + 1))
    fi
    j=$((j + 1))
  done
  i=$((i + 1))
done

# ---- detector 2: expand globs against real paths ----
FILE_SOURCE="none"
if [ "${NO_GIT}" -eq 0 ] && command -v git >/dev/null 2>&1; then
  if [ -z "${ROOT}" ]; then
    ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  fi
  if [ -n "${ROOT}" ] && git -C "${ROOT}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git -C "${ROOT}" ls-files --cached --others --exclude-standard >> "${PATHS_TXT}"
    FILE_SOURCE="git ls-files"
  fi
fi
if [ -n "${EXTRA_FILES}" ]; then
  cat "${EXTRA_FILES}" >> "${PATHS_TXT}"
  if [ "${FILE_SOURCE}" = "none" ]; then FILE_SOURCE="--files"; else FILE_SOURCE="${FILE_SOURCE} + --files"; fi
fi
PATH_COUNT="$(awk 'END { print NR }' "${PATHS_TXT}")"

if [ "${PATH_COUNT}" -gt 0 ]; then
  FILE_OVERLAPS="$(awk -v globsfile="${GLOBS_TSV}" -v pathsfile="${PATHS_TXT}" -v pairsfile="${PAIRS_TXT}" '
    function glob2re(g,    n, i, c, rx, j, cls, meta) {
      sub(/^\.\//, "", g)
      sub(/\/+$/, "", g)
      n = length(g); i = 1; rx = "^"; meta = 0
      while (i <= n) {
        c = substr(g, i, 1)
        if (c == "*") {
          meta = 1
          if (substr(g, i + 1, 1) == "*") {
            if (substr(g, i + 2, 1) == "/") { rx = rx "(.*/)?"; i += 3; continue }
            rx = rx ".*"; i += 2; continue
          }
          rx = rx "[^/]*"; i++; continue
        }
        if (c == "?") { meta = 1; rx = rx "[^/]"; i++; continue }
        if (c == "[") {
          j = index(substr(g, i + 1), "]")
          if (j > 0) {
            meta = 1
            cls = substr(g, i + 1, j - 1)
            if (substr(cls, 1, 1) == "!") cls = "^" substr(cls, 2)
            rx = rx "[" cls "]"; i += j + 1; continue
          }
        }
        if (index(".+()^|{}[]\\", c) > 0 || c == "\044") {
          rx = rx "\\" c; i++; continue
        }
        rx = rx c; i++
      }
      if (!meta) rx = rx "(/.*)?"
      return rx "\044"
    }
    BEGIN {
      ng = 0
      while ((getline line < globsfile) > 0) {
        split(line, f, "\t")
        ng++; lane[ng] = f[1]; glob[ng] = f[2]; re[ng] = glob2re(f[2])
      }
      while ((getline p < pathsfile) > 0) {
        sub(/^\.\//, "", p)
        if (p == "" || seen[p]++) continue
        m = 0
        for (i = 1; i <= ng; i++) if (p ~ re[i]) { m++; hit[m] = i }
        for (a = 1; a <= m; a++) {
          for (b = a + 1; b <= m; b++) {
            ia = hit[a]; ib = hit[b]
            if (lane[ia] == lane[ib]) continue
            if (lane[ia] > lane[ib]) { t = ia; ia = ib; ib = t }
            key = ia SUBSEP ib
            if (!(key in count)) { order[++nk] = key; example[key] = p }
            count[key]++
          }
        }
      }
      for (k = 1; k <= nk; k++) {
        split(order[k], ab, SUBSEP)
        printf "OVERLAP files: %s [%s] <-> %s [%s] · %d path(s), e.g. %s\n", lane[ab[1]], glob[ab[1]], lane[ab[2]], glob[ab[2]], count[order[k]], example[order[k]]
        print lane[ab[1]] " " lane[ab[2]] >> pairsfile
      }
    }
  ')"
  if [ -n "${FILE_OVERLAPS}" ]; then
    printf '%s\n' "${FILE_OVERLAPS}"
    FILE_OVERLAP_COUNT="$(printf '%s\n' "${FILE_OVERLAPS}" | awk 'END { print NR }')"
    OVERLAPS=$((OVERLAPS + FILE_OVERLAP_COUNT))
  fi
fi

# ---- summary ----
if [ "${OVERLAPS}" -gt 0 ]; then
  while IFS=' ' read -r left right; do
    if [ "${left}" \> "${right}" ]; then
      printf '%s %s\n' "${right}" "${left}"
    else
      printf '%s %s\n' "${left}" "${right}"
    fi
  done < "${PAIRS_TXT}" | sort -u > "${TMP}/pairs.sorted"
  PAIR_COUNT=0
  while IFS=' ' read -r left right; do
    [ -n "${left}" ] || continue
    printf 'CONFLICT %s %s\n' "${left}" "${right}"
    PAIR_COUNT=$((PAIR_COUNT + 1))
  done < "${TMP}/pairs.sorted"
  printf 'OWNERSHIP FAIL · %s conflicting lane pair(s) · %s lanes · %s globs · paths checked: %s (%s)\n' \
    "${PAIR_COUNT}" "${LANE_COUNT}" "${GLOB_COUNT}" "${PATH_COUNT}" "${FILE_SOURCE}"
  echo "Next: re-partition (spine lane or CONTRACTS.md shared-path owner), list new directories literally, rerun." >&2
  exit 1
fi

printf 'OWNERSHIP PASS · %s lanes · %s globs · paths checked: %s (%s) · prefix check: clean\n' \
  "${LANE_COUNT}" "${GLOB_COUNT}" "${PATH_COUNT}" "${FILE_SOURCE}"
exit 0
