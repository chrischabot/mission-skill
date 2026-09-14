#!/usr/bin/env bash
# frozen-manifest.sh — write / check the sha256 manifest of frozen files (.mission/frozen-manifest.sha256) selected by
# the globs in .mission/frozen-paths.txt. Layer (c) of references/testing.md G-2: the only layer that also catches
# edits made outside Claude Code. Part of the mission skill (skills/mission/scripts/; installed into .mission/bin/).
# python3 stdlib only. No network, no git writes (reads `git ls-files` when the root is a git work tree).
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: frozen-manifest.sh write [--force] [--root DIR]
       frozen-manifest.sh check [--manifest FILE] [--root DIR]
       frozen-manifest.sh add   [--root DIR] <glob> [<glob> ...]
       frozen-manifest.sh list  [--root DIR]
       frozen-manifest.sh --help

write   Hash every file matching .mission/frozen-paths.txt (plus frozen-paths.txt itself and the frozen-path scripts
        in .mission/bin/) into .mission/frozen-manifest.sha256 ("<sha256>  <path>", sorted; sha256sum -c compatible).
        Refuses (exit 1) when an existing manifest lists files that changed or disappeared, because re-freezing would
        bless the change. --force overrides: only for an accepted TEST-DISPUTE, with a D-entry.
check   Compare the current tree with a manifest (default .mission/frozen-manifest.sha256). Use the base commit's copy
        so a maker cannot re-bless its own edits:
          git show <base>:.mission/frozen-manifest.sha256 > .mission/tmp/base-manifest
          frozen-manifest.sh check --manifest .mission/tmp/base-manifest
        Reports CHANGED, MISSING (listed, file gone) and ADDED (matches a frozen glob, not listed). exit 1 on any.
add     Append globs to .mission/frozen-paths.txt (skipping ones already present), then run write (no --force).
        Adding globs only tightens the freeze, so protect-frozen.sh allows this command.
list    Print the files the current globs select.

Root: --root, else CLAUDE_PROJECT_DIR, else the git toplevel, else the current directory.
Files come from `git ls-files --cached --others --exclude-standard` inside a git work tree, else from a walk that
skips .git, node_modules, .mission/tmp, .wrangler, DerivedData and .build.
Glob syntax: see protect-frozen.sh --help (same matcher).
Exit: 0 ok · 1 check found changes / write refused · 2 usage error, missing frozen-paths.txt or manifest.
EOF
}

if [ "$#" -lt 1 ]; then
  usage >&2
  exit 2
fi
case "$1" in
  -h|--help) usage; exit 0 ;;
  write|check|add|list) ;;
  *) echo "frozen-manifest: unknown command $1 (see --help)" >&2; exit 2 ;;
esac

if ! command -v python3 >/dev/null 2>&1; then
  echo "frozen-manifest: python3 not found" >&2
  exit 2
fi

IFS= read -r -d '' PY <<'PYEOF' || true
import hashlib
import os
import re
import subprocess
import sys

ALWAYS = [
    ".mission/frozen-paths.txt",
    ".mission/bin/protect-frozen.sh",
    ".mission/bin/frozen-manifest.sh",
    ".mission/bin/test-diff-grep.sh",
]
MANIFEST = ".mission/frozen-manifest.sha256"
PATHS = ".mission/frozen-paths.txt"
WILD = "*?["
SKIP_DIRS = {".git", "node_modules", ".wrangler", "DerivedData", ".build"}


def die(msg, code=2):
    sys.stderr.write("frozen-manifest: %s\n" % msg)
    sys.exit(code)


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


def compile_rule(raw):
    p = raw.strip()
    while p.startswith("./"):
        p = p[2:]
    p = p.lstrip("/")
    if p.endswith("/"):
        p = p + "**"
    if "/" not in p:
        p = "**/" + p
    return glob_regex(p)


def git_toplevel(cwd):
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd, capture_output=True, text=True, timeout=10)
    except Exception:
        return None
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def read_globs(root):
    path = os.path.join(root, PATHS)
    if not os.path.isfile(path):
        die("%s not found under %s (run init-mission.sh or frozen-manifest.sh add)" % (PATHS, root))
    globs = []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            s = line.strip()
            if s and not s.startswith("#"):
                globs.append(s)
    return globs


def candidate_files(root):
    files = None
    if git_toplevel(root):
        try:
            r = subprocess.run(
                ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                cwd=root, capture_output=True, timeout=120,
            )
            if r.returncode == 0:
                files = [f.decode("utf-8", "surrogateescape") for f in r.stdout.split(b"\0") if f]
        except Exception:
            files = None
    if files is None:
        files = []
        for dirpath, dirnames, filenames in os.walk(root):
            rel_dir = os.path.relpath(dirpath, root).replace(os.sep, "/")
            rel_dir = "" if rel_dir == "." else rel_dir
            dirnames[:] = [
                d for d in dirnames
                if d not in SKIP_DIRS and (rel_dir + "/" + d).lstrip("/") != ".mission/tmp"
            ]
            for fn in filenames:
                files.append((rel_dir + "/" + fn).lstrip("/"))
    out = set()
    for f in files:
        if os.path.isfile(os.path.join(root, f)):
            out.add(f)
    return out


def selected(root):
    rules = [compile_rule(g) for g in read_globs(root)] + [compile_rule(a) for a in ALWAYS]
    picked = set()
    for f in candidate_files(root):
        if f == MANIFEST or f.startswith(".mission/tmp/"):
            continue
        parts = f.split("/")
        prefixes = ["/".join(parts[:k]) for k in range(1, len(parts) + 1)]
        if any(rx.fullmatch(pre) for rx in rules for pre in prefixes):
            picked.add(f)
    return picked


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(path):
    entries = {}
    with open(path, encoding="utf-8", errors="surrogateescape") as fh:
        for n, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            m = re.match(r"([0-9a-f]{64}) [ *](.+)", line)
            if not m:
                die("%s:%d is not '<sha256>  <path>'" % (path, n))
            entries[m.group(2)] = m.group(1)
    return entries


def compare(root, entries, current):
    findings = []
    for rel in sorted(entries):
        full = os.path.join(root, rel)
        if not os.path.isfile(full):
            findings.append(("MISSING", rel))
        elif sha256(full) != entries[rel]:
            findings.append(("CHANGED", rel))
    for rel in sorted(current - set(entries)):
        findings.append(("ADDED", rel))
    return findings


def cmd_write(root, force):
    mpath = os.path.join(root, MANIFEST)
    current = selected(root)
    if os.path.isfile(mpath) and not force:
        stale = [f for f in compare(root, load_manifest(mpath), set()) if f[0] in ("CHANGED", "MISSING")]
        if stale:
            for kind, rel in stale:
                print("%s %s" % (kind, rel))
            die("refusing to re-freeze: %d frozen file(s) changed or disappeared since the last freeze. "
                "Use --force only for an accepted TEST-DISPUTE (record a D-entry)." % len(stale), 1)
    lines = ["%s  %s\n" % (sha256(os.path.join(root, rel)), rel) for rel in sorted(current)]
    os.makedirs(os.path.dirname(mpath), exist_ok=True)
    tmp = mpath + ".tmp"
    with open(tmp, "w", encoding="utf-8", errors="surrogateescape") as fh:
        fh.writelines(lines)
    os.replace(tmp, mpath)
    print("frozen-manifest: wrote %d entr%s to %s%s" % (
        len(lines), "y" if len(lines) == 1 else "ies", MANIFEST, " (forced)" if force else ""))
    if not lines:
        print("frozen-manifest: warning: no files match the frozen globs")
    return 0


def cmd_check(root, manifest):
    mpath = manifest or os.path.join(root, MANIFEST)
    if not os.path.isfile(mpath):
        die("manifest not found: %s" % mpath)
    entries = load_manifest(mpath)
    findings = compare(root, entries, selected(root))
    for kind, rel in findings:
        print("%s %s" % (kind, rel))
    if findings:
        print("frozen-manifest: FAIL (%d finding(s) against %s)" % (len(findings), mpath))
        return 1
    print("frozen-manifest: OK (%d files match %s)" % (len(entries), mpath))
    return 0


def cmd_add(root, globs):
    if not globs:
        die("add needs at least one glob")
    path = os.path.join(root, PATHS)
    existing = []
    if os.path.isfile(path):
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        existing = [l.strip() for l in text.splitlines()]
        if text and not text.endswith("\n"):
            with open(path, "a", encoding="utf-8") as fh:
                fh.write("\n")
    else:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("# Globs the implementer may read but not write. One per line (references/testing.md G-1).\n")
    added = 0
    with open(path, "a", encoding="utf-8") as fh:
        for g in globs:
            g = g.strip()
            if not g or g.startswith("#") or g in existing:
                continue
            fh.write(g + "\n")
            existing.append(g)
            added += 1
    print("frozen-manifest: added %d glob(s) to %s" % (added, PATHS))
    return cmd_write(root, False)


def cmd_list(root):
    for rel in sorted(selected(root)):
        print(rel)
    return 0


def main(argv):
    cmd = argv[0]
    root = None
    manifest = None
    force = False
    rest = []
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--root" and i + 1 < len(argv):
            root = argv[i + 1]
            i += 2
            continue
        if a == "--manifest" and i + 1 < len(argv):
            manifest = argv[i + 1]
            i += 2
            continue
        if a == "--force":
            force = True
        elif a.startswith("--"):
            die("unknown option %s (see --help)" % a)
        else:
            rest.append(a)
        i += 1
    if rest and cmd != "add":
        die("unexpected argument(s) for %s: %s" % (cmd, " ".join(rest)))
    if force and cmd != "write":
        die("--force is only valid with write")
    if manifest and cmd != "check":
        die("--manifest is only valid with check")
    if not root:
        root = os.environ.get("CLAUDE_PROJECT_DIR") or git_toplevel(os.getcwd()) or os.getcwd()
    if not os.path.isdir(root):
        die("root not found: %s" % root)
    root = os.path.realpath(root)
    if manifest:
        manifest = os.path.realpath(manifest)
    if cmd == "write":
        return cmd_write(root, force)
    if cmd == "check":
        return cmd_check(root, manifest)
    if cmd == "add":
        return cmd_add(root, rest)
    return cmd_list(root)


sys.exit(main(sys.argv[1:]))
PYEOF

python3 -c "${PY}" "$@"
