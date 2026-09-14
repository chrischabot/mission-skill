#!/usr/bin/env bash
# protect-frozen.sh — Claude Code PreToolUse hook that blocks writes to frozen paths (tests, goldens, test configs,
# CI, hooks) listed in .mission/frozen-paths.txt. Part of the mission skill (skills/mission/scripts/; installed into
# .mission/bin/). Layer (b) of references/testing.md G-2. Heuristic by design: the sha256 manifest
# (frozen-manifest.sh check) and the test-diff audit are authoritative. No network, no git writes.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: protect-frozen.sh               (hook mode: reads PreToolUse hook JSON on stdin)
       protect-frozen.sh --self-test   (runs sample hook inputs against a temporary project; prints PASS/FAIL)
       protect-frozen.sh --help

Hook wiring (templates/settings.hooks.json):
  "PreToolUse": [{ "matcher": "Edit|Write|MultiEdit|NotebookEdit|Bash",
                   "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.mission/bin/protect-frozen.sh" }] }]

Decision:
  exit 0  allow (tool is not a write, path not frozen, no .mission/frozen-paths.txt, or MISSION_FROZEN_BYPASS=1)
  exit 2  block; the reason is printed on stderr (Claude Code shows it to the model — confirm the exit-2 semantics
          against the current hooks documentation, see references/testing.md "Unverified harness details")

Blocks:
  - Edit / Write / MultiEdit / NotebookEdit whose file_path (or notebook_path) matches a frozen glob
  - Bash commands that redirect or tee into, sed -i / perl -i, rm / rmdir / unlink / shred / truncate / touch,
    mv, cp / ln / install / rsync onto, dd of=, find -delete / -exec rm, or git checkout / restore / rm / mv a frozen
    path or a directory containing one; also inside bash -c / sh -c / eval, with cd and git -C tracked
  - unparseable hook JSON (fail closed)
Always protected once frozen-paths.txt exists: .mission/frozen-paths.txt, .mission/frozen-manifest.sha256 and the
frozen-path scripts in .mission/bin/. Extend the list with `frozen-manifest.sh add '<glob>'` (allowed by this hook).

Glob syntax (one per line, # comments): ** any depth, * and ? within one path segment, trailing / means the whole
directory, a pattern without / matches that basename at any depth, a path is frozen if it or any parent matches.

Project root: CLAUDE_PROJECT_DIR, else the git toplevel of the hook's cwd, else the cwd.
Requires python3 (stdlib only). Without python3 and with frozen paths configured, the hook fails closed.
Known limits: python3 -c / node -e writes, xargs input, variables in paths, scripts written elsewhere and then run.
EOF
}

SELF="${BASH_SOURCE[0]}"
MODE="hook"
case "${1:-}" in
  "") MODE="hook" ;;
  -h|--help) usage; exit 0 ;;
  --self-test) MODE="selftest" ;;
  *) echo "protect-frozen: unknown argument ${1} (see --help)" >&2; exit 2 ;;
esac

IFS= read -r -d '' PY <<'PYEOF' || true
import glob as globmod
import json
import os
import re
import shlex
import subprocess
import sys

ALWAYS = [
    ".mission/frozen-paths.txt",
    ".mission/frozen-manifest.sha256",
    ".mission/bin/protect-frozen.sh",
    ".mission/bin/frozen-manifest.sh",
    ".mission/bin/test-diff-grep.sh",
]
WRITE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")
WILD = "*?["
SEP_CHARS = set(";&|()")
REDIR_CHARS = set("<>&|")
WRAPPERS = {"sudo", "doas", "command", "builtin", "exec", "nohup", "time", "nice", "xargs", "env", "stdbuf"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
DELETERS = {"rm", "rmdir", "unlink", "shred", "truncate", "touch", "mv", "tee"}
COPIERS = {"cp", "ln", "install", "rsync"}
EXEC_MUTATORS = {"rm", "mv", "sed", "gsed", "perl", "truncate", "shred", "unlink", "tee", "cp"}
ASSIGN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=.*", re.S)
MUTATE_HINT = re.compile(
    r"(>|\btee\b|\bsed\b[^|;&]*\s-[A-Za-z]*i|\bperl\b[^|;&]*\s-[A-Za-z]*i|\brm\b|\bmv\b|\bcp\b|\btruncate\b"
    r"|\bgit\b[^|;&]*\b(?:checkout|restore|rm|mv)\b)"
)


def block(reason, path, rule):
    sys.stderr.write(
        "BLOCKED by protect-frozen.sh: %s touches frozen path '%s' (rule '%s').\n" % (reason, path or ".", rule)
        + "Frozen paths may be read and run, never modified, skipped, deleted or special-cased.\n"
        + "If a test appears wrong, contradictory, or impossible, STOP and file a TEST-DISPUTE.\n"
    )
    sys.exit(2)


def fail_closed(msg):
    sys.stderr.write("BLOCKED by protect-frozen.sh (fail closed): %s\n" % msg)
    sys.exit(2)


def glob_regex(pat):
    out = []
    i = 0
    n = len(pat)
    while i < n:
        if pat.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
            continue
        if pat.startswith("**", i):
            out.append(".*")
            i += 2
            continue
        c = pat[i]
        if c == "*":
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(c))
        i += 1
    return re.compile("".join(out), re.S)


def literal_dir(pat):
    segs = []
    for s in pat.split("/"):
        if any(ch in s for ch in WILD):
            break
        segs.append(s)
    return "/".join(segs)


def compile_rule(raw):
    p = raw.strip()
    while p.startswith("./"):
        p = p[2:]
    p = p.lstrip("/")
    if p.endswith("/"):
        p = p + "**"
    if "/" not in p:
        return (raw, glob_regex("**/" + p), "")
    return (raw, glob_regex(p), literal_dir(p))


def load_rules(root):
    path = os.path.join(root, ".mission", "frozen-paths.txt")
    if not os.path.isfile(path):
        return None
    pats = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            s = line.strip()
            if s and not s.startswith("#"):
                pats.append(s)
    return [compile_rule(p) for p in pats + ALWAYS]


def to_rel(path, cwd, root):
    if not path:
        return None
    path = os.path.expanduser(str(path))
    if not os.path.isabs(path):
        path = os.path.join(cwd, path)
    rel = os.path.relpath(os.path.realpath(path), root)
    if rel == ".":
        return ""
    if rel == ".." or rel.startswith(".." + os.sep):
        return None
    return rel.replace(os.sep, "/")


def frozen_hit(rel, rules, as_dir=False):
    if rel is None:
        return None
    parts = rel.split("/") if rel else []
    prefixes = ["/".join(parts[:k]) for k in range(1, len(parts) + 1)]
    for raw, rx, lit in rules:
        for pre in prefixes:
            if rx.fullmatch(pre):
                return raw
        if as_dir:
            if rel == "":
                return raw
            if lit and (lit == rel or lit.startswith(rel + "/")):
                return raw
    return None


def expand_candidates(arg, cwd):
    paths = [arg]
    if any(ch in arg for ch in WILD):
        full = arg if os.path.isabs(arg) else os.path.join(cwd, arg)
        paths.extend(globmod.glob(os.path.expanduser(full)))
        base = literal_dir(arg)
        if base:
            paths.append(base)
    return paths


def check_targets(cands, cwd, root, rules, reason):
    for c in cands:
        if not c or c == "-" or c.startswith("/dev/"):
            continue
        for p in expand_candidates(c, cwd):
            rel = to_rel(p, cwd, root)
            hit = frozen_hit(rel, rules, as_dir=True)
            if hit:
                block(reason, rel, hit)


def operands(args):
    out = []
    rest = False
    for a in args:
        if rest:
            out.append(a)
        elif a == "--":
            rest = True
        elif a.startswith("-") and a != "-":
            continue
        else:
            out.append(a)
    return out


def option_value(args, names):
    for k, a in enumerate(args):
        if a in names and k + 1 < len(args):
            return args[k + 1]
        for name in names:
            if name.startswith("--") and a.startswith(name + "="):
                return a[len(name) + 1:]
    return None


def in_place(args):
    for a in args:
        if a == "--":
            break
        if a.startswith("--in-place"):
            return True
        if a.startswith("-") and not a.startswith("--") and "i" in a[1:]:
            return True
    return False


def longest_literal(raw):
    chunks = re.split(r"[*?\[\]]+", raw)
    best = max((c.strip("/") for c in chunks), key=len, default="")
    return best


def fallback(cmd, rules):
    if not MUTATE_HINT.search(cmd):
        return
    for raw, rx, lit in rules:
        needle = lit or longest_literal(raw)
        if needle and len(needle) >= 3 and needle in cmd:
            block("unparseable shell command (conservative match)", needle, raw)


def tokenize(cmd):
    lex = shlex.shlex(cmd.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    lex.commenters = ""
    return list(lex)


def analyze(cmd, cwd, root, rules, depth=0):
    if depth > 4:
        return
    try:
        toks = tokenize(cmd)
    except ValueError:
        fallback(cmd, rules)
        return
    segs = [[]]
    for t in toks:
        if t and set(t) <= SEP_CHARS:
            segs.append([])
        elif t and ">" in t and set(t) <= (SEP_CHARS | REDIR_CHARS) and set(t) & set(";()"):
            k = max(t.rfind(c) for c in ";()")
            segs.append([t[k + 1:]])
        else:
            segs[-1].append(t)
    for seg in segs:
        cwd = analyze_segment(seg, cwd, root, rules, depth)


def git_segment(args, cwd, root, rules):
    k = 0
    while k < len(args) and args[k].startswith("-"):
        a = args[k]
        if a == "-C" and k + 1 < len(args):
            cwd = os.path.join(cwd, os.path.expanduser(args[k + 1]))
            k += 2
            continue
        if a in ("-c", "--git-dir", "--work-tree", "--namespace") and k + 1 < len(args):
            k += 2
            continue
        k += 1
    if k >= len(args):
        return
    sub = args[k]
    if sub in ("checkout", "restore", "rm", "mv"):
        check_targets(operands(args[k + 1:]), cwd, root, rules, "git " + sub)


def analyze_segment(seg, cwd, root, rules, depth):
    words = []
    i = 0
    while i < len(seg):
        t = seg[i]
        if ">" in t and set(t) <= REDIR_CHARS:
            if i + 1 < len(seg):
                tgt = seg[i + 1]
                if not (t.endswith("&") and tgt.isdigit()):
                    check_targets([tgt], cwd, root, rules, "shell redirect")
            i += 2
            continue
        words.append(t)
        i += 1
    j = 0
    while j < len(words):
        w = words[j]
        if ASSIGN.fullmatch(w):
            j += 1
            continue
        base = os.path.basename(w)
        if base in WRAPPERS:
            j += 1
            while j < len(words) and (words[j].startswith("-") or ASSIGN.fullmatch(words[j])):
                j += 1
            continue
        if base == "timeout":
            j += 1
            while j < len(words) and words[j].startswith("-"):
                j += 1
            j += 1
            continue
        break
    words = words[j:]
    if not words:
        return cwd
    name = os.path.basename(words[0])
    args = words[1:]
    if name == "cd":
        if args and args[0] != "-":
            cwd = os.path.join(cwd, os.path.expanduser(args[0]))
        return cwd
    if name == "eval":
        analyze(" ".join(args), cwd, root, rules, depth + 1)
    elif name in SHELLS:
        for k, a in enumerate(args):
            if a.startswith("-") and not a.startswith("--") and "c" in a[1:]:
                if k + 1 < len(args):
                    analyze(args[k + 1], cwd, root, rules, depth + 1)
                break
    elif name in DELETERS:
        check_targets(operands(args), cwd, root, rules, name)
    elif name in COPIERS:
        tdir = option_value(args, ("-t", "--target-directory"))
        ops = operands(args)
        if tdir:
            check_targets([tdir], cwd, root, rules, name)
        elif ops:
            check_targets([ops[-1]], cwd, root, rules, name)
    elif name in ("sed", "gsed", "perl"):
        if in_place(args):
            check_targets(operands(args), cwd, root, rules, name + " -i")
    elif name == "dd":
        check_targets([a[3:] for a in args if a.startswith("of=")], cwd, root, rules, "dd of=")
    elif name == "git":
        git_segment(args, cwd, root, rules)
    elif name == "find":
        mutating = "-delete" in args
        for k, a in enumerate(args):
            if a in ("-exec", "-execdir", "-ok", "-okdir") and k + 1 < len(args):
                if os.path.basename(args[k + 1]) in EXEC_MUTATORS:
                    mutating = True
        if mutating:
            roots = []
            for a in args:
                if a.startswith("-") or a in ("(", "!", ")"):
                    break
                roots.append(a)
            check_targets(roots or ["."], cwd, root, rules, "find -delete/-exec")
    return cwd


def git_toplevel(cwd):
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd, capture_output=True, text=True, timeout=5)
    except Exception:
        return None
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except ValueError:
        fail_closed("hook input is not valid JSON")
    if not isinstance(data, dict):
        fail_closed("hook input is not a JSON object")
    tool = data.get("tool_name") or ""
    if tool not in WRITE_TOOLS and tool != "Bash":
        return 0
    cwd = data.get("cwd") or os.getcwd()
    root = os.environ.get("CLAUDE_PROJECT_DIR") or git_toplevel(cwd) or cwd
    root = os.path.realpath(root)
    rules = load_rules(root)
    if rules is None:
        return 0
    ti = data.get("tool_input")
    if not isinstance(ti, dict):
        fail_closed("%s call without tool_input object" % tool)
    if tool in WRITE_TOOLS:
        path = ti.get("file_path") or ti.get("notebook_path") or ti.get("path")
        if not path:
            fail_closed("%s call without file_path" % tool)
        rel = to_rel(path, cwd, root)
        hit = frozen_hit(rel, rules)
        if hit:
            block(tool, rel, hit)
        return 0
    cmd = ti.get("command")
    if not isinstance(cmd, str):
        fail_closed("Bash call without command string")
    analyze(cmd, cwd, root, rules)
    return 0


try:
    sys.exit(main())
except SystemExit:
    raise
except Exception as exc:
    fail_closed("internal error: %r" % (exc,))
PYEOF

hook() {
  if [ "${MISSION_FROZEN_BYPASS:-0}" = "1" ]; then
    exit 0
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    local root="${CLAUDE_PROJECT_DIR:-}"
    if [ -z "${root}" ]; then
      root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
    fi
    if [ -f "${root}/.mission/frozen-paths.txt" ]; then
      echo "BLOCKED by protect-frozen.sh (fail closed): python3 not found; install python3 or unwire the hook with a D-entry." >&2
      exit 2
    fi
    exit 0
  fi
  python3 -c "${PY}"
}

selftest() {
  local tmp
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/protect-frozen-selftest.XXXXXX")"
  # shellcheck disable=SC2064
  trap "rm -rf '${tmp}'" EXIT
  mkdir -p "${tmp}/.mission/bin" "${tmp}/tests/acceptance" "${tmp}/tests/unit" "${tmp}/src"
  printf '%s\n' '# frozen globs (self-test)' 'tests/acceptance/**' 'playwright.config.*' > "${tmp}/.mission/frozen-paths.txt"
  : > "${tmp}/tests/acceptance/a.test.ts"
  : > "${tmp}/playwright.config.ts"
  local total=0 failed=0
  expect() {
    local want="$1" desc="$2" json="$3" code=0
    total=$((total + 1))
    printf '%s' "${json}" | CLAUDE_PROJECT_DIR="${tmp}" MISSION_FROZEN_BYPASS="${BYPASS:-0}" bash "${SELF}" >/dev/null 2>&1 || code=$?
    if [ "${code}" = "${want}" ]; then
      echo "ok   ${desc} (exit ${code})"
    else
      echo "FAIL ${desc} (want exit ${want}, got ${code})"
      failed=$((failed + 1))
    fi
  }
  bash_json() {
    # $1 = shell command (must not contain double quotes or backslashes)
    printf '{"tool_name":"Bash","tool_input":{"command":"%s"},"cwd":"%s"}' "$1" "${tmp}"
  }
  tool_json() {
    # $1 = tool name, $2 = key, $3 = path
    printf '{"tool_name":"%s","tool_input":{"%s":"%s","content":"x"},"cwd":"%s"}' "$1" "$2" "$3" "${tmp}"
  }

  expect 2 "Write to frozen test (absolute path)" "$(tool_json Write file_path "${tmp}/tests/acceptance/a.test.ts")"
  expect 2 "Edit frozen test (relative path)" "$(tool_json Edit file_path tests/acceptance/a.test.ts)"
  expect 2 "MultiEdit frozen config (basename glob)" "$(tool_json MultiEdit file_path "${tmp}/playwright.config.ts")"
  expect 2 "NotebookEdit under frozen dir" "$(tool_json NotebookEdit notebook_path "${tmp}/tests/acceptance/n.ipynb")"
  expect 2 "Write always-protected frozen-paths.txt" "$(tool_json Write file_path "${tmp}/.mission/frozen-paths.txt")"
  expect 0 "Edit source file" "$(tool_json Edit file_path "${tmp}/src/app.ts")"
  expect 0 "Write unit test (not frozen)" "$(tool_json Write file_path "${tmp}/tests/unit/b.test.ts")"
  expect 0 "Write outside project" "$(tool_json Write file_path /tmp/elsewhere.txt)"
  expect 0 "Read tool on frozen path" "$(tool_json Read file_path "${tmp}/tests/acceptance/a.test.ts")"
  expect 2 "Bash append redirect" "$(bash_json 'echo x >> tests/acceptance/a.test.ts')"
  expect 2 "Bash redirect without spaces" "$(bash_json 'echo x>tests/acceptance/a.test.ts')"
  expect 2 "Bash sed -i" "$(bash_json "sed -i 's/a/b/' tests/acceptance/a.test.ts")"
  expect 2 "Bash perl -pi on config" "$(bash_json "perl -pi -e 's/2/9/' playwright.config.ts")"
  expect 2 "Bash tee -a" "$(bash_json 'printf x | tee -a tests/acceptance/a.test.ts')"
  expect 2 "Bash rm -rf parent dir" "$(bash_json 'rm -rf tests')"
  expect 2 "Bash rm with glob" "$(bash_json 'rm tests/acceptance/*.ts')"
  expect 2 "Bash mv frozen file away" "$(bash_json 'mv tests/acceptance/a.test.ts /tmp/a.ts')"
  expect 2 "Bash cp onto frozen file" "$(bash_json 'cp /tmp/x.ts tests/acceptance/a.test.ts')"
  expect 2 "Bash git checkout -- path" "$(bash_json 'git checkout HEAD~1 -- tests/acceptance/a.test.ts')"
  expect 2 "Bash git restore dir" "$(bash_json 'git restore tests/acceptance')"
  expect 2 "Bash git -C dir rm" "$(bash_json 'git -C tests rm acceptance/a.test.ts')"
  expect 2 "Bash cd then rm" "$(bash_json 'cd tests && rm -f acceptance/a.test.ts')"
  expect 2 "Bash bash -c nested" "$(bash_json "bash -c 'rm tests/acceptance/a.test.ts'")"
  expect 2 "Bash find -delete" "$(bash_json "find tests -name '*.ts' -delete")"
  expect 2 "Bash env-prefixed truncate" "$(bash_json 'FOO=1 truncate -s 0 tests/acceptance/a.test.ts')"
  expect 0 "Bash read frozen file" "$(bash_json 'cat tests/acceptance/a.test.ts')"
  expect 0 "Bash run tests" "$(bash_json 'npx vitest run tests/acceptance --reporter=json > .mission/tmp/vitest.json 2>&1')"
  expect 0 "Bash copy frozen file out" "$(bash_json 'cp tests/acceptance/a.test.ts /tmp/copy.ts')"
  expect 0 "Bash redirect to /dev/null" "$(bash_json 'ls tests 2>/dev/null')"
  expect 0 "Bash git checkout branch" "$(bash_json 'git checkout -b feature/x')"
  expect 0 "Bash rm unrelated dir" "$(bash_json 'rm -rf node_modules .mission/tmp/run1')"
  expect 0 "Bash freeze via frozen-manifest.sh add" "$(bash_json ".mission/bin/frozen-manifest.sh add 'tests/regression/**'")"
  expect 0 "Bash find -exec cat (read only)" "$(bash_json "find tests -name '*.ts' -exec cat {} ;")"
  expect 2 "Invalid JSON fails closed" 'not json'
  BYPASS=1 expect 0 "MISSION_FROZEN_BYPASS=1 allows" "$(tool_json Write file_path "${tmp}/tests/acceptance/a.test.ts")"
  rm -f "${tmp}/.mission/frozen-paths.txt"
  expect 0 "No frozen-paths.txt allows" "$(tool_json Write file_path "${tmp}/tests/acceptance/a.test.ts")"

  if [ "${failed}" -eq 0 ]; then
    echo "self-test: PASS (${total} checks)"
    return 0
  fi
  echo "self-test: FAIL (${failed} of ${total} checks)"
  return 1
}

if [ "${MODE}" = "selftest" ]; then
  if ! command -v python3 >/dev/null 2>&1; then
    echo "self-test: FAIL (python3 not found)"
    exit 1
  fi
  selftest
  exit $?
fi
hook
