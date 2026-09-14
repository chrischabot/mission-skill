#!/usr/bin/env bash
# test-diff-grep.sh — deterministic grep pre-pass of the test-diff audit (references/testing.md G-4, G-5;
# templates/test-diff-audit.md §A). Flags added focus/skip markers, test-only production branches, weakened test
# configs, deleted or renamed test files and dropped @req citations. A model cannot override its exit code; the
# verifier may only cite a quarantine row or D-entry for a flag. Part of the mission skill (installed into
# .mission/bin/). python3 stdlib only. No network, no git writes.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: test-diff-grep.sh --base <ref> [--head <ref>] [--repo DIR]
       test-diff-grep.sh --diff-file <file | ->
       test-diff-grep.sh --help

--base REF     scan `git diff -M <REF>` (working tree incl. uncommitted tracked changes), or `git diff -M REF HEAD`
               when --head is given. Untracked files are not in a git diff: commit or `git add -N` them first.
--diff-file F  scan a unified diff from a file, or stdin with "-".

Flags (added lines unless stated):
  only            .only( · fit( · fdescribe( · test.only
  skip            .skip( / .skipIf( · xit( · xdescribe( · xtest( · test.fixme · XCTSkip · #[ignore] ·
                  @pytest.mark.skip / skipif / xfail · pytest.skip( · t.Skip( · @Disabled · @Ignore
  config          passWithNoTests · retries set above 2 · forbidOnly removed (removed line)
  test-branch     NODE_ENV compared with 'test' · isTesting · isRunningTests · process.env.VITEST ·
                  process.env.JEST_WORKER_ID · XCTestConfigurationFilePath · #if DEBUG_TEST  (non-test files)
  deleted-test    a test file deleted (tests/, __tests__/, *Tests/, *.test.*, *.spec.*, *_test.*, test_*.py,
                  *Tests.swift, golden/ and __snapshots__/ fixtures)
  renamed-test    a test file renamed or moved
  req-dropped     an @req:<ID> citation removed more often than re-added in the diff

Output: one "FLAG <kind> <file>:<line> <text>" per finding, then a summary line.
Exit: 0 clean · 1 at least one flag · 2 usage error or git failure.
EOF
}

BASE=""
HEAD=""
REPO="."
DIFF_FILE=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --base) [ "$#" -ge 2 ] || { echo "test-diff-grep: --base needs a value" >&2; exit 2; }; BASE="$2"; shift 2 ;;
    --head) [ "$#" -ge 2 ] || { echo "test-diff-grep: --head needs a value" >&2; exit 2; }; HEAD="$2"; shift 2 ;;
    --repo) [ "$#" -ge 2 ] || { echo "test-diff-grep: --repo needs a value" >&2; exit 2; }; REPO="$2"; shift 2 ;;
    --diff-file) [ "$#" -ge 2 ] || { echo "test-diff-grep: --diff-file needs a value" >&2; exit 2; }; DIFF_FILE="$2"; shift 2 ;;
    *) echo "test-diff-grep: unknown argument $1 (see --help)" >&2; exit 2 ;;
  esac
done

if [ -z "${BASE}" ] && [ -z "${DIFF_FILE}" ]; then
  echo "test-diff-grep: give --base <ref> or --diff-file <file>" >&2
  usage >&2
  exit 2
fi
if [ -n "${BASE}" ] && [ -n "${DIFF_FILE}" ]; then
  echo "test-diff-grep: --base and --diff-file are mutually exclusive" >&2
  exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "test-diff-grep: python3 not found" >&2
  exit 2
fi

TMP_DIFF=""
cleanup() {
  if [ -n "${TMP_DIFF}" ]; then
    rm -f "${TMP_DIFF}"
  fi
}
trap cleanup EXIT

if [ -n "${BASE}" ]; then
  TMP_DIFF="$(mktemp "${TMPDIR:-/tmp}/test-diff-grep.XXXXXX")"
  if [ -n "${HEAD}" ]; then
    git -C "${REPO}" diff --no-color --no-ext-diff -M "${BASE}" "${HEAD}" > "${TMP_DIFF}" || { echo "test-diff-grep: git diff failed" >&2; exit 2; }
  else
    git -C "${REPO}" diff --no-color --no-ext-diff -M "${BASE}" > "${TMP_DIFF}" || { echo "test-diff-grep: git diff failed" >&2; exit 2; }
  fi
  DIFF_FILE="${TMP_DIFF}"
elif [ "${DIFF_FILE}" != "-" ] && [ ! -f "${DIFF_FILE}" ]; then
  echo "test-diff-grep: diff file not found: ${DIFF_FILE}" >&2
  exit 2
fi

IFS= read -r -d '' PY <<'PYEOF' || true
import re
import sys
from collections import Counter

TEST_PATH = re.compile(
    r"(?:^|/)(?:tests?|__tests__|specs?|e2e|golden|__snapshots__|[A-Za-z0-9_]+Tests)/"
    r"|\.(?:test|spec)\.[A-Za-z0-9]+\Z|_test\.[A-Za-z0-9]+\Z|(?:^|/)test_[^/]*\.py\Z|Tests?\.swift\Z"
)
ADDED = [
    ("only", re.compile(r"\.only\s*\(|\bfit\s*\(|\bfdescribe\s*\(")),
    ("skip", re.compile(
        r"\.skip(?:If|Unless)?\s*\(|\bxit\s*\(|\bxdescribe\s*\(|\bxtest\s*\(|test\.fixme\b|\bXCTSkip"
        r"|#\[ignore\]|@pytest\.mark\.(?:skip|skipif|xfail)\b|\bpytest\.skip\s*\(|\bt\.Skip(?:Now|f)?\s*\("
        r"|@Disabled\b|@Ignore\b")),
    ("config", re.compile(r"passWithNoTests|\bretries\s*[:=]\s*(?:[3-9]|\d{2,})\b")),
]
BRANCH = re.compile(
    r"NODE_ENV\s*[!=]==?\s*['\"`]test['\"`]|['\"`]test['\"`]\s*[!=]==?\s*process\.env\.NODE_ENV"
    r"|\bisTesting\b|\bisRunningTests\b|process\.env\.VITEST\b|process\.env\.JEST_WORKER_ID\b"
    r"|XCTestConfigurationFilePath|#if\s+DEBUG_TEST"
)
REMOVED_GUARD = re.compile(r"\bforbidOnly\b")
REQ = re.compile(r"@req:([A-Za-z][A-Za-z0-9]*-\d+)")


def strip_prefix(p):
    p = p.strip()
    if p.startswith('"') and p.endswith('"'):
        p = p[1:-1]
    if p.startswith("a/") or p.startswith("b/"):
        p = p[2:]
    return p


def main(path):
    fh = sys.stdin if path == "-" else open(path, encoding="utf-8", errors="replace")
    flags = []
    req_added = Counter()
    req_removed = Counter()
    old_file = new_file = None
    deleted = False
    old_left = new_left = 0
    new_line = 0
    files = set()
    scanned = 0
    for raw in fh:
        line = raw.rstrip("\n")
        if old_left > 0 or new_left > 0:
            if line.startswith("\\"):
                continue
            tag = line[:1]
            body = line[1:]
            if tag == "+":
                new_left -= 1
                scanned += 1
                target = new_file or old_file or "?"
                for kind, rx in ADDED:
                    if rx.search(body):
                        flags.append((kind, "%s:%d" % (target, new_line), body.strip()))
                if not TEST_PATH.search(target) and BRANCH.search(body):
                    flags.append(("test-branch", "%s:%d" % (target, new_line), body.strip()))
                for rid in REQ.findall(body):
                    req_added[rid] += 1
                new_line += 1
                continue
            if tag == "-":
                old_left -= 1
                target = old_file or new_file or "?"
                if REMOVED_GUARD.search(body):
                    flags.append(("config", "%s (removed line)" % target, body.strip()))
                for rid in REQ.findall(body):
                    req_removed[rid] += 1
                continue
            old_left -= 1
            new_left -= 1
            new_line += 1
            continue
        if line.startswith("diff --git "):
            rest = line[len("diff --git "):]
            idx = rest.rfind(" b/")
            old_file = strip_prefix(rest[:idx]) if idx > 0 else None
            new_file = strip_prefix(rest[idx + 1:]) if idx > 0 else None
            deleted = False
            if new_file:
                files.add(new_file)
            continue
        if line.startswith("deleted file mode"):
            deleted = True
            if old_file and TEST_PATH.search(old_file):
                flags.append(("deleted-test", old_file, "file deleted"))
            continue
        if line.startswith("rename from "):
            src = strip_prefix(line[len("rename from "):])
            if TEST_PATH.search(src):
                flags.append(("renamed-test", src, "file renamed or moved"))
            continue
        if line.startswith("--- "):
            p = line[4:].split("\t")[0]
            old_file = None if p.strip() == "/dev/null" else strip_prefix(p)
            continue
        if line.startswith("+++ "):
            p = line[4:].split("\t")[0]
            if p.strip() == "/dev/null":
                if not deleted and old_file and TEST_PATH.search(old_file):
                    flags.append(("deleted-test", old_file, "file deleted"))
                deleted = True
                new_file = None
            else:
                new_file = strip_prefix(p)
                files.add(new_file)
            continue
        m = re.match(r"@@ -\d+(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
        if m:
            old_left = int(m.group(1)) if m.group(1) is not None else 1
            new_line = int(m.group(2))
            new_left = int(m.group(3)) if m.group(3) is not None else 1
            continue
    if fh is not sys.stdin:
        fh.close()
    for rid in sorted(req_removed):
        if req_removed[rid] > req_added[rid]:
            flags.append(("req-dropped", "@req:%s" % rid, "removed %d, added %d" % (req_removed[rid], req_added[rid])))
    for kind, where, text in flags:
        print("FLAG %s %s %s" % (kind, where, text[:160]))
    if flags:
        counts = Counter(k for k, _, _ in flags)
        detail = ", ".join("%s %d" % (k, counts[k]) for k in sorted(counts))
        print("test-diff-grep: %d flag(s) (%s). Each flag is BLOCKING unless the verifier cites a quarantine row "
              "or D-entry." % (len(flags), detail))
        return 1
    print("test-diff-grep: clean (%d file(s), %d added line(s) scanned)" % (len(files), scanned))
    return 0


sys.exit(main(sys.argv[1]))
PYEOF

python3 -c "${PY}" "${DIFF_FILE}"
