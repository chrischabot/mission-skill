#!/usr/bin/env python3
"""drive.py: the deterministic backbone of the /drive skill.

Standard library only; runs on the Python 3.9 that macOS ships. Every subcommand reads the
project's `.drive/` directory (or the skill repository for the lesson commands) and never calls a
model. Run `drive.py <subcommand> --help` for arguments.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import difflib
import fnmatch
import glob as globmod
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATES = SKILL_DIR / "templates"

LADDER = ["Missing", "Scaffold", "Partial", "Local Proof", "Live Proof", "Operational", "Done"]
DROPPED = "Dropped"
RUN_STATUSES = ["running", "verifying", "blocked", "stalled", "done", "stopped", "aborted"]
GATE_CLOSED = {"running", "verifying"}
PHASES = [
    "intake", "archaeology", "research", "spec", "design", "test-plan", "decompose", "build",
    "verify", "integrate", "live-proof", "harden", "docs", "retro", "report",
    "reproduce", "diagnose", "fix",
    "inventory", "characterize", "cutover", "soak", "decommission",
    "content-plan", "draft", "design-qa", "deploy",
    "plan", "execute", "observe",
]
PRE_BUILD_PHASES = {"intake", "archaeology", "research", "spec", "design", "test-plan", "decompose",
                    "reproduce", "diagnose", "inventory", "characterize", "content-plan", "plan"}
# Phases that come after every test a row names should exist: harden and every phase PHASES lists after it, except the
# pre-build phases and build's counterparts in other shapes (fix, draft, execute). A planned: token fails in them at
# any rung; in build, verify, and integrate it fails only on a row at Partial or above.
POST_TEST_PHASES = {p for p in PHASES[PHASES.index("harden"):] if p not in PRE_BUILD_PHASES} - {"fix", "draft", "execute"}
SHAPES = ["build", "feature", "fix", "move", "publish", "report", "operate"]
VARIANTS = {"fix/incident", "fix/perf", "move/migration", "move/refactor", "move/upgrade"}
TRAITS = ["ui", "api", "auth", "data", "existing-code", "multi-repo", "external-systems",
          "async-scheduled", "concurrency", "native-platform", "prose-content", "public-api", "cli",
          "perf", "research-needed", "deploy-infra", "ai-llm", "large-surface", "generated-code"]
SIZES = ["XS", "S", "M", "L", "XL"]
CHECKERS = {"orchestrator", "researcher", "architect", "designer", "implementer", "writer", "verifier", "severe-tester",
            "security-reviewer", "ui-reviewer", "grader", "investigator", "auditor"}
TOKEN_TYPES = ["test", "severe", "verdict", "proof", "shot", "live", "ops", "review", "commit",
               "doc", "why", "planned", "sub"]
# The only words a self-declared `blocked` status may begin its Blocked on line with (SKILL.md section 9).
BLOCKED_TOKENS = ("budget:", "impossible:", "destructive:", "credentials:", "payment:", "legal:", "account:",
                  "two-diagnoses:", "soak:")
HOOK_ARG_RE = re.compile(r"^hook-(stop|guard|post|snapshot|reinject)$")
STATUS_COLUMNS = ["key", "claim", "live", "status", "evidence", "updated"]
WORK_VERBS = ("implement", "add", "create", "set up", "wire", "refactor", "build")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LEFTOVER_BRANCH_PATTERNS = ["drive/*", "pkg/*"]
HARNESS_BRANCH_PATTERNS = ["worktree-*"]
NO_SUITE_SHAPES = {"report", "operate"}
SUITE_TIMEOUT = 1800
# Which agent types may produce each kind of evidence the lint counts.
EVIDENCE_ROLES = {
    "verdict": {"verifier", "ui-reviewer"},
    "final-audit": {"auditor", "verifier"},
    "live-proof": {"verifier", "ui-reviewer"},
    "citations": {"grader"},
    "refutation": {"verifier"},
}
CHECKER_PRODUCERS = {"verifier", "ui-reviewer"}
KNOWN_DRIVE_ENTRIES = {
    "GOAL.md", "STATE.md", "STATUS.md", "DECISIONS.md", "LESSONS.md", "CONSTRAINTS.md",
    "capabilities.json", "capability-map.md", "SPEC.md", "DESIGN.md", "TESTPLAN.md", "RESEARCH.md",
    "HUNT.md", "MIGRATION.md", "how-it-works.md", "REPORT.md", "handoffs", "rubrics", "packages",
    "proofs", "reviews", "investigations", "local", "runs", "content-plan",
}
SECRET_PATTERNS = [
    ("an API key starting with sk-", re.compile(r"\bsk-(?:ant-|proj-|live-)?[A-Za-z0-9_\-]{20,}")),
    ("an AWS access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("a GitHub token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{40,}")),
    ("a Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("a Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("a private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("a bearer token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/\-]{24,}=*")),
    ("a JSON web token", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
]
HTML_TAGS = {"a", "b", "i", "p", "br", "hr", "div", "span", "img", "ul", "ol", "li", "em", "strong",
             "code", "pre", "table", "tr", "td", "th", "head", "body", "html", "title", "script",
             "style", "input", "button", "form", "label", "select", "option", "details", "summary",
             "sup", "sub", "kbd", "nav", "main", "section", "header", "footer", "svg", "path"}
_RAW_PLACEHOLDER = re.compile(r"<(?![/!])([A-Za-z][A-Za-z0-9 _.,'/|·:+\-]{0,400})>")


class _PlaceholderMatcher:
    """Template placeholders such as <goal slug>, <YYYY-MM-DD>, or <S|M|L|XL>, but not <div> or <Button>."""

    @staticmethod
    def _is_placeholder(match):
        inner = match.group(1).strip()
        if not inner:
            return False
        if inner.split(" ")[0].lower() in HTML_TAGS and "|" not in inner:
            return False
        if inner[0].isupper() and " " not in inner and "|" not in inner and not inner.replace("-", "").isupper():
            return False
        return True

    def finditer(self, text):
        return (m for m in _RAW_PLACEHOLDER.finditer(text or "") if self._is_placeholder(m))

    def search(self, text):
        return next(self.finditer(text), None)


PLACEHOLDER_RE = _PlaceholderMatcher()


# ----------------------------------------------------------------------------------------------
# Small utilities


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso_now() -> str:
    return now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(value: str):
    """Parse an ISO 8601 timestamp; a naive value is taken as UTC. Returns None when unparseable."""
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        stamp = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=dt.timezone.utc)
    return stamp


def parse_date(value: str):
    if not value or not DATE_RE.match(value.strip()):
        return None
    try:
        return dt.date.fromisoformat(value.strip())
    except ValueError:
        return None


def slugify(text: str, limit=None) -> str:
    """Lowercase, every run of non-alphanumeric characters replaced by one hyphen, ends trimmed."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if limit:
        slug = slug[:limit].rstrip("-")
    return slug


def read_text(path: Path):
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def load_json(path: Path):
    """Return (data, error)."""
    text = read_text(path)
    if text is None:
        return None, "cannot be read"
    try:
        return json.loads(text), None
    except json.JSONDecodeError as exc:
        return None, "is not valid JSON ({})".format(exc.msg)


def run(cmd, cwd=None, timeout=60, input_text=None, env=None):
    """Run a command without a shell. Returns (exit code, stdout, stderr); never raises."""
    try:
        proc = subprocess.run(cmd, cwd=str(cwd) if cwd else None, input=input_text,
                              capture_output=True, text=True, timeout=timeout, env=env)
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return 127, "", "{} not found".format(cmd[0])
    except subprocess.TimeoutExpired:
        return 124, "", "timed out after {}s".format(timeout)
    except OSError as exc:
        return 126, "", str(exc)


def git(root, *args, timeout=60):
    return run(["git", "-C", str(root), *args], timeout=timeout)


def git_out(root, *args):
    code, out, _ = git(root, *args)
    return out.strip() if code == 0 else None


def is_git_repo(path) -> bool:
    return git_out(path, "rev-parse", "--is-inside-work-tree") == "true"


def has_head(root) -> bool:
    return git(root, "rev-parse", "--verify", "--quiet", "HEAD")[0] == 0


def commit_exists(root, sha: str) -> bool:
    if not re.match(r"^[0-9a-fA-F]{4,40}$", sha or ""):
        return False
    return git(root, "cat-file", "-e", sha + "^{commit}")[0] == 0


def show_at(root, rev: str, relpath: str):
    code, out, _ = git(root, "show", "{}:{}".format(rev, relpath))
    return out if code == 0 else None


def find_root(start) -> Path:
    """The project root: the nearest ancestor holding `.drive/`, else the git top level, else start."""
    path = Path(start).resolve()
    for candidate in [path, *path.parents]:
        if (candidate / ".drive").is_dir():
            return candidate
    top = git_out(path, "rev-parse", "--show-toplevel")
    return Path(top).resolve() if top else path


def main_worktree_root(start):
    # --path-format=absolute needs git 2.31; an older git echoes the unknown option and prints a
    # relative path, which is resolved against `start` here.
    out = git_out(start, "rev-parse", "--path-format=absolute", "--git-common-dir")
    lines = [l for l in (out or "").splitlines() if l.strip() and not l.startswith("--")]
    if not lines:
        return None
    common = lines[-1].strip()
    if not os.path.isabs(common):
        base = Path(start) if Path(start).is_dir() else Path(start).parent
        common = str(base / common)
    common_path = Path(common).resolve()
    return common_path.parent if common_path.name == ".git" else None


def _query_quietly(path, query) -> bool:
    """One filesystem query that answers False instead of raising for a name the OS rejects: a component longer than
    NAME_MAX, a path longer than PATH_MAX (both ENAMETOOLONG), or a NUL byte. The hooks meet such names whenever they
    treat a command word or a code string literal from a tool call as a path, and a raise there refuses the call."""
    try:
        return query(Path(path))
    except (OSError, ValueError):
        return False


def exists_quietly(path) -> bool:
    """Path.exists(), answering False for a name the OS rejects."""
    return _query_quietly(path, Path.exists)


def is_file_quietly(path) -> bool:
    """Path.is_file(), answering False for a name the OS rejects."""
    return _query_quietly(path, Path.is_file)


def is_dir_quietly(path) -> bool:
    """Path.is_dir(), answering False for a name the OS rejects."""
    return _query_quietly(path, Path.is_dir)


def small_file_text(path, limit):
    """The text of a regular file smaller than `limit` bytes, or None when it is missing, unreadable, that large or
    larger, or named in a way the OS rejects, so an over-long name reads like a missing file."""
    try:
        path = Path(path)
        if not path.is_file() or path.stat().st_size >= limit:
            return None
    except (OSError, ValueError):
        return None
    return read_text(path)


def realpath_loose(path) -> Path:
    """Resolve symlinks on the longest existing prefix, then append the rest normalised."""
    path = Path(os.path.normpath(str(path)))
    existing = path
    tail = []
    while not exists_quietly(existing) and existing != existing.parent:
        tail.append(existing.name)
        existing = existing.parent
    resolved = Path(os.path.realpath(str(existing)))
    for part in reversed(tail):
        resolved = resolved / part
    return Path(os.path.normpath(str(resolved)))


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


TMP_ROOTS = [Path("/private/tmp"), Path("/tmp")]


def tmp_roots():
    """The throwaway roots: /private/tmp, /tmp, and $TMPDIR, or DRIVE_TMP_ROOTS (colon-separated) when set."""
    configured = os.environ.get("DRIVE_TMP_ROOTS")
    if configured:
        bases = [Path(p) for p in configured.split(os.pathsep) if p]
    else:
        bases = list(TMP_ROOTS)
        system_tmp = os.environ.get("TMPDIR") or tempfile.gettempdir()
        if system_tmp:
            bases.append(Path(system_tmp))
    roots = []
    for root in bases:
        for candidate in (root, Path(os.path.realpath(str(root)))):
            if candidate not in roots and str(candidate) not in ("/", ""):
                roots.append(candidate)
    return roots


def scratch_words():
    """How messages name the scratch directory: the first throwaway root on this machine."""
    roots = tmp_roots()
    return str(roots[0]) if roots else "a scratch directory"


def is_tmp_path(path: Path, exclude=None) -> bool:
    """True for a path under a throwaway root, but never for a path inside `exclude` (the active
    project), so a project checked out under /private/tmp is not treated as scratch."""
    resolved = realpath_loose(path)
    if exclude is not None and is_within(resolved, realpath_loose(exclude)):
        return False
    return any(is_within(resolved, root) and resolved != root for root in tmp_roots())


def derived_path_ok(target, allowed_roots, evidence: bool):
    """The derived-path rule for anything drive.py deletes or moves.

    The symlink-resolved target must sit under an allowlisted root, at least one level below it,
    and the caller must hold ownership evidence it read before the operation. Returns (ok, reason).
    """
    resolved = Path(os.path.realpath(str(target)))
    for root in allowed_roots:
        real_root = Path(os.path.realpath(str(root)))
        if is_within(resolved, real_root) and resolved != real_root:
            if not evidence:
                return False, "{} has no ownership evidence recorded before the operation".format(resolved)
            return True, ""
    return False, "{} is not under an allowlisted root ({})".format(
        resolved, ", ".join(str(r) for r in allowed_roots))


# ----------------------------------------------------------------------------------------------
# The provenance ledger: an append-only record outside `.drive/`, written by drive's hooks and by the
# commands drive.py itself runs, of who produced each piece of evidence the lint counts.


def file_sha256(path: Path):
    try:
        digest = hashlib.sha256()
        with open(str(path), "rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def repo_key(root) -> str:
    return hashlib.sha256(os.path.realpath(str(root)).encode("utf-8")).hexdigest()


def home_dir() -> Path:
    return Path(os.path.expanduser("~"))


def ledger_base_dirs():
    """Every directory a ledger may live under: ${CLAUDE_PLUGIN_DATA}/ledger when that is set (hooks
    get it; a Bash call may not), the documented plugin data directories for drive, and the fallback
    ~/.claude/drive/ledger. Writers use the first; readers read them all."""
    bases = []
    data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if data:
        bases.append(Path(data) / "ledger")
    home = home_dir()
    for found in sorted(globmod.glob(str(home / ".claude" / "plugins" / "data" / "drive*" / "ledger"))):
        if Path(found) not in bases:
            bases.append(Path(found))
    fallback = home / ".claude" / "drive" / "ledger"
    if fallback not in bases:
        bases.append(fallback)
    return bases


def ledger_guard_roots():
    """Paths no agent and no main-thread tool call may write: every ledger location."""
    home = home_dir()
    roots = [home / ".claude" / "drive", home / ".claude" / "plugins" / "data"]
    data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if data:
        roots.append(Path(data))
    return roots


def transcript_roots():
    """Where Claude Code keeps session and subagent transcripts: ~/.claude/projects, or CLAUDE_CONFIG_DIR/projects."""
    roots = [home_dir() / ".claude" / "projects"]
    config = os.environ.get("CLAUDE_CONFIG_DIR")
    if config and Path(config) / "projects" not in roots:
        roots.append(Path(config) / "projects")
    return roots


def is_transcript_path(path) -> bool:
    """A transcript file under a transcript root: a .jsonl file, or anything under a subagents/ directory. Memory
    notes under the same root are not transcripts."""
    resolved = realpath_loose(path)
    for root in transcript_roots():
        if is_within(resolved, realpath_loose(root)) and (resolved.suffix == ".jsonl" or "subagents" in resolved.parts):
            return True
    return False


def ledger_file(root) -> Path:
    return ledger_base_dirs()[0] / repo_key(root) / "ledger.jsonl"


def ledger_append(root, entry):
    entry = dict(entry)
    entry.setdefault("time", iso_now())
    entry.setdefault("ts", time.time())
    entry["repo"] = os.path.realpath(str(root))
    path = ledger_file(root)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(str(path), "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
        return True
    except OSError:
        return False


def ledger_entries(root, kind=None):
    key = repo_key(root)
    seen, out = set(), []
    for base in ledger_base_dirs():
        text = read_text(base / key / "ledger.jsonl")
        if not text:
            continue
        for line in text.splitlines():
            if not line.strip() or line in seen:
                continue
            seen.add(line)
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(entry, dict) and (kind is None or entry.get("kind") == kind):
                out.append(entry)
    out.sort(key=lambda e: float(e.get("ts") or 0))
    return out


def evidence_files(root):
    """{relative path: sha256} for every JSON file under .drive/proofs/ and .drive/reviews/."""
    out = {}
    drive = Path(root) / ".drive"
    for folder in ("proofs", "reviews"):
        base = drive / folder
        if not base.is_dir():
            continue
        for path in base.rglob("*.json"):
            if path.is_file() and not path.is_symlink():
                digest = file_sha256(path)
                if digest:
                    out[str(path.relative_to(root)).replace("\\", "/")] = digest
    return out


TRANSCRIPT_EDIT_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
TRANSCRIPT_SHELL_TOOLS = {"Bash", "PowerShell"}
_TRANSCRIPT_CACHE = {}


def transcript_digest(path, size=None):
    """(sha256, bytes hashed) of the first `size` bytes of a transcript, or of the whole file when size is None. A
    subagent resumed later appends to its transcript, so a recorded prefix keeps its hash; a rewrite does not."""
    try:
        with open(str(path), "rb") as handle:
            data = handle.read() if size is None else handle.read(int(size))
    except (OSError, ValueError, TypeError):
        return None, None
    if size is not None and len(data) < int(size):
        return None, len(data)
    return hashlib.sha256(data).hexdigest(), len(data)


def transcript_tool_calls(path, agent_id=None):
    """[(tool name, tool input, cwd)] for every tool call an assistant turn in the transcript made whose result was not
    an error (a call the guard refused comes back as an error). Lines are JSON objects with `type`, `agentId`, `cwd`,
    and `message.content` items of type tool_use (`id`, `name`, `input`) or tool_result (`tool_use_id`, `is_error`)."""
    path = Path(path)
    try:
        stat = path.stat()
    except OSError:
        return []
    key = (str(path), stat.st_size, stat.st_mtime_ns, agent_id)
    if key in _TRANSCRIPT_CACHE:
        return _TRANSCRIPT_CACHE[key]
    text = read_text(path) or ""
    entries = []
    for line in text.splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if isinstance(entry, dict):
            entries.append(entry)
    # The transcript is one agent's own file; filter by agentId only when the file records that id at all, so a
    # difference in how the hook and the transcript spell the id never discards every call.
    if agent_id and any(e.get("agentId") == agent_id for e in entries):
        entries = [e for e in entries if e.get("agentId") in (None, agent_id)]
    calls, failed = [], {}
    for entry in entries:
        message = entry.get("message") if isinstance(entry.get("message"), dict) else {}
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "tool_use" and entry.get("type") == "assistant":
                tool_input = item.get("input") if isinstance(item.get("input"), dict) else {}
                calls.append((str(item.get("id")), str(item.get("name")), tool_input, entry.get("cwd")))
            elif item.get("type") == "tool_result" and item.get("is_error"):
                result = item.get("content")
                if isinstance(result, list):
                    result = "\n".join(str(part.get("text", "")) for part in result if isinstance(part, dict))
                failed[str(item.get("tool_use_id"))] = str(result or "")
    # A shell call that ran and exited non-zero (a later check in the same command failed) still wrote what it wrote;
    # a call the guard refused, or that never ran, did not.
    out = [(name, tool_input, cwd) for call_id, name, tool_input, cwd in calls
           if call_id not in failed or (name in SHELL_TOOLS and failed[call_id].lstrip().startswith("Exit code"))]
    _TRANSCRIPT_CACHE[key] = out
    return out


def call_writes_path(name, tool_input, call_cwd, root, rel):
    """True when one tool call wrote `rel`: an Edit or Write whose file_path resolves to it, or a shell command that
    names the path (relative to the repository root, or absolute)."""
    target = realpath_loose(Path(root) / rel)
    if name in TRANSCRIPT_EDIT_TOOLS:
        raw = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
        if not raw:
            return False
        path = Path(os.path.expanduser(raw))
        if not path.is_absolute():
            path = Path(call_cwd or root) / path
        return realpath_loose(path) == target
    if name in TRANSCRIPT_SHELL_TOOLS:
        command = str(tool_input.get("command") or "")
        names = {rel, "./" + rel, str(target), os.path.join(os.path.realpath(str(root)), rel), os.path.join(str(root), rel)}
        return any(re.search(r"(?<![\w.\-]){}(?![\w.\-])".format(re.escape(n)), command) for n in names)
    return False


def meta_agent_type(transcript):
    """The agentType Claude Code recorded beside a subagent transcript (agent-<id>.meta.json), or None."""
    path = Path(transcript)
    meta = path.with_name(path.stem + ".meta.json")
    data, _ = load_json(meta) if is_file_quietly(meta) else (None, None)
    value = data.get("agentType") if isinstance(data, dict) else None
    return value if isinstance(value, str) and value else None


def agent_types_match(recorded, agent_type):
    agent_type = str(agent_type or "")
    return recorded == agent_type or recorded == agent_type.split(":", 1)[-1] or agent_type.endswith(":" + recorded)


def transcript_problem(root, rel, transcript, agent_type=None, agent_id=None, sha=None, size=None):
    """Why a transcript does not back the claim that this agent wrote `rel` (None when it does): it must exist under
    Claude Code's transcript directory, belong to the agent type, still hash as recorded, and hold a successful tool
    call that wrote exactly that path."""
    if not transcript:
        return "no subagent transcript was recorded with it"
    path = Path(str(transcript))
    if not path.is_absolute() or not is_transcript_path(path):
        return "its transcript {} is not a Claude Code transcript under {}".format(
            transcript, " or ".join(str(r) for r in transcript_roots()))
    if not is_file_quietly(path):
        return "its transcript {} no longer exists (Claude Code deletes transcripts after cleanupPeriodDays)".format(transcript)
    recorded_type = meta_agent_type(path)
    if recorded_type and agent_type and not agent_types_match(recorded_type, agent_type):
        return "its transcript belongs to {}, not {}".format(recorded_type, agent_type)
    if sha is not None:
        digest, _ = transcript_digest(path, size)
        if digest != sha:
            return "its transcript {} changed since the entry was recorded".format(transcript)
    for name, tool_input, cwd in transcript_tool_calls(path, agent_id):
        if call_writes_path(name, tool_input, cwd, root, rel):
            return None
    return "its transcript {} holds no successful Write, Edit, or shell command by that agent naming {}".format(transcript, rel)


def record_evidence(root, rel, agent_type, agent_id, started=None, started_ts=None, transcript=None):
    """Append an evidence entry, only when the agent's transcript shows it wrote the file. Returns True when recorded."""
    digest = file_sha256(Path(root) / rel)
    if not digest:
        return False
    if transcript_problem(root, rel, transcript, agent_type, agent_id) is not None:
        return False
    transcript_sha, transcript_size = transcript_digest(transcript)
    return ledger_append(root, {"kind": "evidence", "path": rel, "sha256": digest, "agent_type": agent_type,
                                "role": role_of(agent_type), "agent_id": agent_id, "started": started,
                                "started_ts": started_ts, "transcript": str(transcript),
                                "transcript_sha256": transcript_sha, "transcript_size": transcript_size})


def void_windows(root):
    """Voided review windows from the ledger and from .drive/local/ro/*.void markers."""
    windows = [e for e in ledger_entries(root, "void")]
    folder = Path(root) / ".drive" / "local" / "ro"
    if folder.is_dir():
        for marker in folder.glob("*.void"):
            data, _ = load_json(marker)
            if isinstance(data, dict):
                windows.append(data)
    return windows


def evidence_kind(rel):
    name = rel.rsplit("/", 1)[-1]
    if rel.startswith(".drive/reviews/") and name.endswith("-final-audit.json"):
        return "final-audit"
    if rel.startswith(".drive/reviews/") and "-citations-" in name and name.endswith(".json"):
        return "citations"
    if name == "proof.json":
        return "live-proof"
    return "verdict"


def provenance_problem(root, path: Path, kind, cache=None):
    """Why this evidence file does not count: None when a drive agent of the right type wrote exactly
    these bytes during a review that was not voided."""
    roles = EVIDENCE_ROLES[kind]
    rel = str(realpath_loose(path).relative_to(realpath_loose(root))).replace("\\", "/")
    names = " or ".join("drive:" + r for r in sorted(roles))
    digest = file_sha256(path)
    entries = cache if cache is not None else ledger_entries(root, "evidence")
    recorded = [e for e in entries if e.get("path") == rel]
    matches = [e for e in recorded if e.get("sha256") == digest]
    if not matches:
        if recorded:
            return ("{} changed after {} wrote it: its sha256 no longer matches the provenance ledger. Only the file "
                    "as the reviewing agent left it counts; spawn a fresh {} instead of editing it").format(
                rel, recorded[-1].get("agent_type") or "the agent", names)
        return ("{} has no provenance: no {} was recorded writing it when that agent finished. A verdict, final audit, "
                "live proof, or citation check counts only when the agent that produced it wrote it").format(rel, names)
    good = [e for e in matches if e.get("role") in roles]
    if not good:
        return "{} was written by {}, not by {}".format(
            rel, ", ".join(sorted({str(e.get("agent_type")) for e in matches})), names)
    reasons = []
    backed = []
    for entry in good:
        if not entry.get("transcript_sha256"):
            reasons.append("no subagent transcript was recorded with it")
            continue
        why = transcript_problem(root, rel, entry.get("transcript"), entry.get("agent_type"), entry.get("agent_id"),
                                 entry.get("transcript_sha256"), entry.get("transcript_size"))
        if why:
            reasons.append(why)
        else:
            backed.append(entry)
    if not backed:
        return ("{} has no transcript-backed provenance: {}. A ledger entry counts only when the reviewing agent's own "
                "transcript shows it writing the file; spawn a fresh {} instead").format(rel, reasons[-1], names)
    good = backed
    windows = void_windows(root)
    voided_ids = {str(w.get("agent_id")) for w in windows if w.get("agent_id")}
    clean = [e for e in good if str(e.get("agent_id")) not in voided_ids]
    if not clean:
        window = next(w for w in windows if str(w.get("agent_id")) == str(good[-1].get("agent_id")))
        return ("{} was written by {} {}, whose review was voided because tracked files changed while it ran ({}). "
                "Spawn a fresh reviewer").format(rel, good[-1].get("agent_type"), good[-1].get("agent_id"), window.get("detail", "?"))
    try:
        mtime = path.stat().st_mtime
    except OSError:
        mtime = None
    for window in windows:
        start, stop = window.get("started_ts"), window.get("stopped_ts")
        if mtime is not None and isinstance(start, (int, float)) and isinstance(stop, (int, float)) and start - 1 <= mtime <= stop + 1:
            return ("{} was written while a read-only review ({} {}) was voided because tracked files changed under it ({}). "
                    "Spawn a fresh reviewer").format(rel, window.get("agent_type"), window.get("agent_id"), window.get("detail", "?"))
    return None


def current_code_sha(root):
    if not has_head(root):
        return None
    out = git_out(root, "log", "-1", "--format=%H", "--", ".", ":(top,exclude).drive")
    return out or git_out(root, "rev-parse", "HEAD")


# ----------------------------------------------------------------------------------------------
# The run marker, sessions, and the hygiene baseline


def marker_path(root) -> Path:
    return Path(root) / ".drive" / "local" / "active"


def read_marker(root):
    data, _ = load_json(marker_path(root))
    return data if isinstance(data, dict) else {}


def register_session(root, session_id):
    """Record a session that is running /drive in this repository, so hooks that fire in every session
    (re-injection) can stay quiet in the others."""
    if not session_id or not marker_path(root).is_file():
        return
    data = read_marker(root)
    sessions = data.get("sessions") if isinstance(data.get("sessions"), list) else []
    if session_id in sessions:
        return
    sessions.append(session_id)
    data["sessions"] = sessions[-20:]
    try:
        marker_path(root).write_text(json.dumps(data) + "\n", encoding="utf-8")
    except OSError:
        pass


def session_is_drive(root, session_id):
    sessions = read_marker(root).get("sessions")
    if not isinstance(sessions, list) or not sessions or not session_id:
        return True
    return session_id in sessions


def local_branches(root):
    out = git_out(root, "for-each-ref", "--format=%(refname:short)", "refs/heads") or ""
    return [b.strip() for b in out.splitlines() if b.strip()]


def capture_baseline(root):
    """The owner's state when the run started: worktrees, local branches, and uncommitted paths."""
    code, out, _ = git(root, "status", "--porcelain=v1", "--untracked-files=normal", "-z")
    untracked_dirs = []
    if code == 0:
        for record in out.split("\0"):
            if record.startswith("?? ") and record.endswith("/") and not record[3:].startswith(".drive"):
                untracked_dirs.append(record[3:])
    return {
        "captured": iso_now(),
        "head": git_out(root, "rev-parse", "HEAD") if has_head(root) else None,
        "branch": git_out(root, "symbolic-ref", "--short", "-q", "HEAD"),
        "worktrees": [os.path.realpath(e.get("worktree", "")) for e in worktree_entries(root)[1:]],
        "branches": local_branches(root),
        # The run's own state is never the owner's work, even when it is uncommitted at capture time.
        "dirty": [p for _, p in (porcelain_paths(root) or []) if not p.startswith(".drive/") and p != ".gitignore"],
        "untracked_dirs": untracked_dirs,
    }


def baseline_path(root) -> Path:
    return Path(root) / ".drive" / "local" / "baseline.json"


def write_baseline(root):
    path = baseline_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(capture_baseline(root), indent=2) + "\n", encoding="utf-8")
    return path


def read_baseline(root):
    data, _ = load_json(baseline_path(root)) if baseline_path(root).is_file() else (None, None)
    return data if isinstance(data, dict) else None


# ----------------------------------------------------------------------------------------------
# Findings


class Findings:
    def __init__(self):
        self.items = []

    def add(self, level, file, message):
        self.items.append({"level": level, "file": file, "message": message})

    def fail(self, file, message):
        self.add("fail", file, message)

    def warn(self, file, message):
        self.add("warn", file, message)

    @property
    def failed(self) -> bool:
        return any(item["level"] == "fail" for item in self.items)

    def lines(self):
        return ["{} {}: {}".format("FAIL" if i["level"] == "fail" else "warn", i["file"], i["message"])
                for i in self.items]


# ----------------------------------------------------------------------------------------------
# Markdown parsing


class Doc:
    """A Markdown file split into its title, header lines, and `## ` sections."""

    def __init__(self, text: str):
        self.text = text
        self.lines = text.splitlines()
        self.title = ""
        self.header = []
        self.sections = {}
        self.section_order = []
        current = None
        in_fence = False
        for number, line in enumerate(self.lines, 1):
            if line.strip().startswith("```"):
                in_fence = not in_fence
            if not in_fence and line.startswith("# ") and not self.title and current is None:
                self.title = line[2:].strip()
                continue
            if not in_fence and line.startswith("## "):
                current = line[3:].strip()
                self.sections.setdefault(current, [])
                self.section_order.append(current)
                continue
            if current is None:
                self.header.append((number, line))
            else:
                self.sections[current].append((number, line))

    def fields(self, lines=None):
        out = {}
        for _, line in (self.header if lines is None else lines):
            match = re.match(r"^([A-Za-z][A-Za-z _\-]*):\s?(.*)$", line)
            if match:
                out.setdefault(match.group(1).strip().lower(), match.group(2).strip())
        return out

    def section(self, name):
        return self.sections.get(name)

    def bullets(self, name):
        return [(n, line) for n, line in self.sections.get(name, []) if line.startswith("- ")]


def split_row(line: str):
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    cells = re.split(r"(?<!\\)\|", body)
    return [cell.strip().replace("\\|", "|") for cell in cells]


def parse_table(lines):
    """Parse the first pipe table in (lineno, text) pairs. Returns (header, rows) or (None, [])."""
    index = 0
    while index < len(lines) and not lines[index][1].lstrip().startswith("|"):
        index += 1
    if index >= len(lines):
        return None, []
    header = [cell.lower() for cell in split_row(lines[index][1])]
    rows = []
    index += 1
    if index < len(lines) and re.match(r"^\s*\|[\s:\-|]+\|?\s*$", lines[index][1]):
        index += 1
    while index < len(lines) and lines[index][1].lstrip().startswith("|"):
        rows.append((lines[index][0], split_row(lines[index][1])))
        index += 1
    return header, rows


def strip_inline_code(line: str) -> str:
    return re.sub(r"`[^`]*`", "", line)


def strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text or "", flags=re.S)


def find_placeholders(text: str, include_yaml_fences=True):
    """Template placeholders left unfilled, as (lineno, placeholder)."""
    found = []
    fence_lang = None
    text = re.sub(r"<!--.*?-->", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            fence_lang = None if fence_lang is not None else (stripped[3:].strip() or "plain")
            continue
        if fence_lang is not None and not (include_yaml_fences and fence_lang == "yaml"):
            continue
        for match in PLACEHOLDER_RE.finditer(strip_inline_code(line)):
            inner = match.group(1).strip()
            if inner.split(" ")[0] in HTML_TAGS and "|" not in inner:
                continue
            found.append((number, match.group(0)))
    return found


# A brace word in a recorded command, such as {scratch}/test_refute.py, stands in for a path the command really used.
# ${VAR}, curl's -w %{http_code}, find's {}, and brace expansion with a comma ({a,b}) are real syntax and do not match.
BRACE_PLACEHOLDER_RE = re.compile(r"(?<![$%])\{[A-Za-z_][A-Za-z0-9_ -]*\}")
# The command fields a verdict (ran[].cmd) and a live proof.json (commands[].cmd) record.
COMMAND_FIELD_RE = re.compile(r"^\$\.(?:ran|commands)\[\d+\]\.cmd$")


def json_placeholders(data, path="$"):
    found = []
    if isinstance(data, dict):
        for key, value in data.items():
            found.extend(json_placeholders(value, "{}.{}".format(path, key)))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            found.extend(json_placeholders(value, "{}[{}]".format(path, index)))
    elif isinstance(data, str):
        match = PLACEHOLDER_RE.search(data)
        if not match and COMMAND_FIELD_RE.match(path):
            match = BRACE_PLACEHOLDER_RE.search(data)
        if match:
            found.append((path, match.group(0)))
    return found


# ----------------------------------------------------------------------------------------------
# A small YAML flow-style reader for GOAL.md's classification block


class FlowParser:
    """Reads `{ a: [x, y], b: "q" }` style values, the only YAML the classification block uses."""

    def __init__(self, text):
        self.text = text
        self.pos = 0

    def parse(self):
        value = self.value()
        self.skip()
        return value

    def skip(self):
        while self.pos < len(self.text) and self.text[self.pos] in " \t\n\r":
            self.pos += 1

    def value(self):
        self.skip()
        if self.pos >= len(self.text):
            return None
        char = self.text[self.pos]
        if char == "{":
            return self.mapping()
        if char == "[":
            return self.sequence()
        if char in "\"'":
            return self.quoted(char)
        return self.bare()

    def mapping(self):
        self.pos += 1
        out = {}
        while True:
            self.skip()
            if self.pos >= len(self.text):
                raise ValueError("unclosed mapping")
            if self.text[self.pos] == "}":
                self.pos += 1
                return out
            key = self.value()
            self.skip()
            if self.pos >= len(self.text) or self.text[self.pos] != ":":
                raise ValueError("expected ':' in mapping")
            self.pos += 1
            out[str(key)] = self.value()
            self.skip()
            if self.pos < len(self.text) and self.text[self.pos] == ",":
                self.pos += 1

    def sequence(self):
        self.pos += 1
        out = []
        while True:
            self.skip()
            if self.pos >= len(self.text):
                raise ValueError("unclosed sequence")
            if self.text[self.pos] == "]":
                self.pos += 1
                return out
            out.append(self.value())
            self.skip()
            if self.pos < len(self.text) and self.text[self.pos] == ",":
                self.pos += 1

    def quoted(self, quote):
        end = self.pos + 1
        chars = []
        while end < len(self.text):
            if self.text[end] == "\\" and quote == '"' and end + 1 < len(self.text):
                chars.append(self.text[end + 1])
                end += 2
                continue
            if self.text[end] == quote:
                self.pos = end + 1
                return "".join(chars)
            chars.append(self.text[end])
            end += 1
        raise ValueError("unclosed quote")

    def bare(self):
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos] not in ",}]":
            if self.text[self.pos] == ":" and (self.pos + 1 >= len(self.text) or self.text[self.pos + 1] in " \t"):
                break
            self.pos += 1
        token = self.text[start:self.pos].strip()
        if token in ("null", "~", ""):
            return None
        if token in ("true", "false"):
            return token == "true"
        # Only a canonical integer becomes an int. A digit run with a leading zero, such as the short sha 0970287, stays
        # the string it was written as: int() would drop the zero and name a commit that does not exist.
        if re.match(r"^-?(0|[1-9]\d*)$", token):
            return int(token)
        return token


_EMPTY = object()


def parse_yaml_block(block_lines):
    """Top-level keys of a YAML block. Flow values are parsed (null, true, false, integers, quoted
    strings, [lists], and {maps}); an indented block under a key becomes a mapping (`k: v` lines) or a
    list (`- item` lines, with continuation lines ignored). A key with nothing under it is an empty list."""
    out = {}
    current = None
    for line in block_lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        top = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if top and not line.startswith((" ", "\t")):
            key, raw = top.group(1), top.group(2).strip()
            current = key
            if raw == "":
                out[key] = _EMPTY
                continue
            try:
                out[key] = FlowParser(raw).parse()
            except ValueError as exc:
                out[key] = ValueError(str(exc))
            continue
        if current is None:
            continue
        item = re.match(r"^\s+-\s*(.*)$", line)
        if item and (out.get(current) is _EMPTY or isinstance(out.get(current), list)):
            if out.get(current) is _EMPTY:
                out[current] = []
            out[current].append(item.group(1))
            continue
        nested = re.match(r"^\s+([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if nested and (out.get(current) is _EMPTY or isinstance(out.get(current), dict)):
            if out.get(current) is _EMPTY:
                out[current] = {}
            try:
                out[current][nested.group(1)] = FlowParser(nested.group(2).strip()).parse()
            except ValueError:
                out[current][nested.group(1)] = nested.group(2).strip()
    for key, value in list(out.items()):
        if value is _EMPTY:
            out[key] = []
    return out


# ----------------------------------------------------------------------------------------------
# State models

TOKEN_SPLIT_RE = re.compile(r";\s*(?=(?:{}):)".format("|".join(TOKEN_TYPES)))


class Row:
    def __init__(self, lineno, cells):
        self.lineno = lineno
        self.cells = cells
        padded = cells + [""] * (6 - len(cells))
        self.key, self.claim, self.live, self.status, self.evidence_raw, self.updated = padded[:6]
        self.tokens = []
        self.bad_tokens = []
        raw = self.evidence_raw.strip()
        if raw:
            for part in TOKEN_SPLIT_RE.split(raw):
                part = part.strip().rstrip(";").strip()
                if not part:
                    continue
                match = re.match(r"^([a-z]+):(.*)$", part, re.S)
                if not match or match.group(1) not in TOKEN_TYPES:
                    self.bad_tokens.append(part)
                    continue
                self.tokens.append((match.group(1), match.group(2).strip()))

    @property
    def ui(self) -> bool:
        return self.claim.startswith("[ui]")

    def values(self, kind):
        return [value for token, value in self.tokens if token == kind]

    @property
    def rung(self) -> int:
        return LADDER.index(self.status) if self.status in LADDER else -1


class Status:
    def __init__(self, text: str):
        self.doc = Doc(text)
        self.header_ok = self.doc.title.startswith("STATUS ·")
        self.fields = self.doc.fields()
        self.columns, raw_rows = parse_table(self.doc.header + [
            item for name in self.doc.section_order for item in self.doc.sections[name]])
        self.rows = [Row(n, cells) for n, cells in raw_rows]

    def by_key(self):
        return {row.key: row for row in self.rows}


class State:
    def __init__(self, text: str):
        self.text = text
        self.doc = Doc(text)
        self.fields = self.doc.fields()
        resume = self.doc.section("Resume here") or []
        self.resume = self.doc.fields(resume)

    @property
    def status(self):
        return self.fields.get("status", "")

    @property
    def in_flight(self):
        return self.resume.get("in flight", "")

    def ledger(self):
        return parse_table(self.doc.section("Workaround ledger") or [])


class Goal:
    """GOAL.md. Sub-goals repeat `## Classification · <slug>` and `## Plan · <slug>` sections."""

    def __init__(self, text: str):
        self.text = text
        self.doc = Doc(text)
        self.fields = self.doc.fields()
        restate = [(n, l[2:] if l.startswith("- ") else l) for n, l in self.doc.section("Restate") or []]
        self.restate = self.doc.fields(restate)
        self.classifications = []
        self.plan = []
        for name in self.doc.section_order:
            base = name.split("·", 1)[0].strip()
            if base == "Classification":
                self.classifications.append((name, self._yaml(self.doc.sections[name])))
            elif base == "Plan":
                self.plan.extend((n, l) for n, l in self.doc.sections[name] if l.startswith("- ["))
        self.classification = self.classifications[0][1] if self.classifications else {}
        self.classification_error = None if self.classifications else "has no Classification section"
        if self.classifications and any(c is None for _, c in self.classifications):
            self.classification_error = "a Classification section has no fenced yaml block"
            self.classifications = [(n, c or {}) for n, c in self.classifications]
            self.classification = self.classifications[0][1]

    @staticmethod
    def _yaml(lines):
        block, in_fence, seen = [], False, False
        for _, line in lines:
            if line.strip().startswith("```"):
                if in_fence:
                    break
                in_fence, seen = True, True
                continue
            if in_fence:
                block.append(line)
        if not seen:
            return None
        return parse_yaml_block(block)

    def probe(self):
        probe = self.classification.get("probe")
        return probe if isinstance(probe, dict) else {}

    @property
    def size(self):
        """The largest size across every sub-goal's classification."""
        sizes = [c.get("size") for _, c in self.classifications if c.get("size") in SIZES]
        if not sizes:
            return self.classification.get("size")
        return max(sizes, key=SIZES.index)

    def sub_classification(self, slug):
        for name, cls in self.classifications:
            if "·" in name and name.split("·", 1)[1].strip() == slug:
                return cls
        return None

    @property
    def shapes(self):
        return {c.get("shape") for _, c in self.classifications if c.get("shape")}

    def repos(self):
        """Absolute repository paths listed under probe.repos in any classification."""
        out = []
        for _, cls in self.classifications:
            probe = cls.get("probe") if isinstance(cls.get("probe"), dict) else {}
            value = probe.get("repos")
            for item in value if isinstance(value, list) else []:
                if isinstance(item, str) and item.startswith("/") and Path(item).is_dir():
                    out.append(Path(item))
        return out

    @property
    def slug(self):
        title = self.doc.title
        return title.split("·", 1)[1].strip() if "·" in title else ""


# A plan line; an optional step segment after the phase lets an operate plan read
# `- [ ] execute · rotate the api key · artifact: ... · exit: ... · checker: ...`.
PLAN_RE = re.compile(r"^- \[(?P<tick> |x|X|-)\] (?P<phase>[a-z\-]+)(?: · (?!artifact: )(?P<step>.+?))?"
                     r" · artifact: (?P<artifact>.+?) · exit: (?P<exit>.+?) · checker: (?P<checker>(?:drive:)?[a-z\-]+)\s*$")


class Ctx:
    """Everything a lint pass needs, loaded once."""

    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.drive = self.root / ".drive"
        self.today_utc = now_utc().date()
        self.today_local = dt.date.today()
        self.git = is_git_repo(self.root)
        self.head = self.git and has_head(self.root)
        self.goal = self._load(Goal, "GOAL.md")
        self.state = self._load(State, "STATE.md")
        self.status = self._load(Status, "STATUS.md")
        self.run_commands = True
        self.suite_timeout = SUITE_TIMEOUT
        self.sub = None
        self._evidence = None

    def evidence_entries(self):
        if self._evidence is None:
            self._evidence = ledger_entries(self.root, "evidence")
        return self._evidence

    def provenance(self, path, kind):
        return provenance_problem(self.root, path, kind, cache=self.evidence_entries())

    def _load(self, cls, name):
        text = read_text(self.drive / name)
        return cls(text) if text is not None else None

    def rel(self, path: Path) -> str:
        try:
            return str(Path(path).resolve().relative_to(self.root))
        except ValueError:
            return str(path)

    def resolve(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else self.root / path

    def today_ok(self, date) -> bool:
        return date in (self.today_utc, self.today_local)

    @property
    def test_command(self):
        """The probe's full-suite command, or None when it is missing, a placeholder, or `none`."""
        return suite_command(self.goal.probe() if self.goal else {})

    def suite_for(self, sub=None):
        """The full-suite command a verdict must show, or None when there is no suite to show: the probe records none,
        or every shape in scope (the sub-goal's own, when the row names one) has no suite."""
        if self.goal is None:
            return None
        cls = self.goal.sub_classification(sub) if sub else None
        shapes = {cls.get("shape")} if cls and cls.get("shape") else self.goal.shapes
        if shapes and shapes <= NO_SUITE_SHAPES:
            return None
        probe = cls.get("probe") if cls and isinstance(cls.get("probe"), dict) else {}
        return suite_command(probe) if suite_command_key(probe) else self.test_command


SUITE_KEYS = ("full_suite", "full_suite_command", "test_command", "tests")


def suite_command_key(probe):
    return next((k for k in SUITE_KEYS if isinstance(probe.get(k), str) and probe.get(k).strip()), None)


def suite_command(probe):
    """A probe's full-suite command; `none` (or `none yet`) means the project has no suite, so it returns None."""
    for key in SUITE_KEYS:
        value = probe.get(key)
        if isinstance(value, str) and value.strip() and not PLACEHOLDER_RE.search(value):
            return None if re.match(r"(?i)^none\b", value.strip()) else value.strip()
    return None


# ----------------------------------------------------------------------------------------------
# A JSON Schema subset validator (type, enum, const, required, properties, additionalProperties,
# items, minItems, maxItems, minLength, maxLength, pattern, minimum, maximum, $ref to #/$defs)

_SCHEMAS = {}


def load_schema(name):
    if name not in _SCHEMAS:
        data, _ = load_json(TEMPLATES / name)
        _SCHEMAS[name] = data if isinstance(data, dict) else None
    return _SCHEMAS[name]


def _type_ok(value, kind):
    if kind == "string":
        return isinstance(value, str)
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == "boolean":
        return isinstance(value, bool)
    if kind == "array":
        return isinstance(value, list)
    if kind == "object":
        return isinstance(value, dict)
    if kind == "null":
        return value is None
    return True


def schema_errors(data, schema, root=None, path="$"):
    root = root if root is not None else schema
    if "$ref" in schema:
        target = root
        for part in schema["$ref"].lstrip("#/").split("/"):
            target = target.get(part, {})
        return schema_errors(data, target, root, path)
    kinds = schema.get("type")
    if kinds:
        kinds = kinds if isinstance(kinds, list) else [kinds]
        if not any(_type_ok(data, kind) for kind in kinds):
            return ["{} should be {}".format(path, " or ".join(kinds))]
    errors = []
    if "enum" in schema and data not in schema["enum"]:
        errors.append("{} must be one of {}".format(path, ", ".join(json.dumps(v) for v in schema["enum"])))
    if "const" in schema and data != schema["const"]:
        errors.append("{} must be {}".format(path, json.dumps(schema["const"])))
    if isinstance(data, str):
        if len(data) < schema.get("minLength", 0):
            errors.append("{} must not be empty".format(path) if schema.get("minLength") == 1
                          else "{} is shorter than {} characters".format(path, schema["minLength"]))
        if "maxLength" in schema and len(data) > schema["maxLength"]:
            errors.append("{} is longer than {} characters".format(path, schema["maxLength"]))
        if "pattern" in schema and not re.search(schema["pattern"], data):
            errors.append("{} does not match {}".format(path, schema["pattern"]))
    if isinstance(data, (int, float)) and not isinstance(data, bool):
        if "minimum" in schema and data < schema["minimum"]:
            errors.append("{} is below {}".format(path, schema["minimum"]))
        if "maximum" in schema and data > schema["maximum"]:
            errors.append("{} is above {}".format(path, schema["maximum"]))
    if isinstance(data, list):
        if len(data) < schema.get("minItems", 0):
            errors.append("{} needs at least {} item(s)".format(path, schema["minItems"]))
        if "maxItems" in schema and len(data) > schema["maxItems"]:
            errors.append("{} has more than {} items".format(path, schema["maxItems"]))
        if isinstance(schema.get("items"), dict):
            for index, item in enumerate(data):
                errors.extend(schema_errors(item, schema["items"], root, "{}[{}]".format(path, index)))
    if isinstance(data, dict):
        for key in schema.get("required", []):
            if key not in data:
                errors.append("{} is missing {}".format(path, key))
        props = schema.get("properties", {})
        for key, value in data.items():
            if key in props:
                errors.extend(schema_errors(value, props[key], root, "{}.{}".format(path, key)))
            elif schema.get("additionalProperties") is False:
                errors.append("{} has an unexpected field {}".format(path, key))
            elif isinstance(schema.get("additionalProperties"), dict):
                errors.extend(schema_errors(value, schema["additionalProperties"], root, "{}.{}".format(path, key)))
    return errors


# ----------------------------------------------------------------------------------------------
# Evidence checks

MAKER_ROLES = {"implementer", "writer", "designer", "architect", "researcher"}
LOCALHOST_RE = re.compile(r"(?i)\b(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|::1|[a-z0-9\-]+\.local)\b")


def evidence_path(ctx, value):
    """Resolve an evidence path; returns (path, problem)."""
    clean = value.split("#", 1)[0].strip()
    if not clean:
        return None, "an empty path"
    path = realpath_loose(ctx.resolve(clean))
    if not is_within(path, realpath_loose(ctx.root)):
        return None, "{} is outside the repository, so nobody else can check it".format(clean)
    return path, None


def test_token_problem(ctx, kind, value):
    if "::" not in value:
        return "{}:{} must be written as {}:<path>::<test name>".format(kind, value, kind)
    rel, name = value.split("::", 1)
    path, problem = evidence_path(ctx, rel)
    if problem:
        return problem
    if not is_file_quietly(path):
        return "{}: the file {} does not exist".format(kind, rel)
    if kind == "test" and rel.startswith(".drive/reviews/") and rel.endswith(".json"):
        _, error = load_json(path)
        if error:
            return "{}: {} {}".format(kind, rel, error)
        return ctx.provenance(path, "citations")
    text = read_text(path)
    if text is None or name.strip() not in text:
        return "{}: the test name '{}' does not appear in {}".format(kind, name.strip(), rel)
    return None


def latest_round_problem(ctx, path: Path):
    match = re.match(r"^r(\d+)$", path.parent.name)
    if not match:
        return None
    current = int(match.group(1))
    later = []
    for sibling in path.parent.parent.iterdir():
        other = re.match(r"^r(\d+)$", sibling.name)
        if other and int(other.group(1)) > current and (sibling / "verdict.json").is_file():
            later.append(sibling.name)
    if later:
        return "{} is not the latest round; {} has a newer verdict. Cite the latest round".format(
            ctx.rel(path), sorted(later)[-1])
    unit_dir = ctx.rel(path.parent.parent)
    for entry in ctx.evidence_entries():
        recorded = str(entry.get("path", ""))
        found = re.match(r"^{}/r(\d+)/verdict\.json$".format(re.escape(unit_dir)), recorded)
        if found and int(found.group(1)) > current and not (ctx.root / recorded).is_file():
            return "{} is not the latest round: {} recorded {} and that verdict has been deleted since. Cite the latest round".format(
                ctx.rel(path), entry.get("agent_type") or "a reviewer", recorded)
    return None


def verdict_problems(ctx, value, key, sub=None):
    """Why a `verdict:` token does not prove a pass for this key (empty list means it does)."""
    path, problem = evidence_path(ctx, value)
    if problem:
        return [problem]
    if not is_file_quietly(path):
        return ["the verdict file {} does not exist".format(value)]
    data, error = load_json(path)
    if error:
        return ["{} {}".format(value, error)]
    if not isinstance(data, dict):
        return ["{} is not a JSON object".format(value)]
    problems = []
    schema = load_schema("verdict.schema.json")
    if schema:
        problems.extend("{} {}".format(value, e) for e in schema_errors(data, schema)[:6])
    refuted = refuted_gap_ids(ctx, path, data)
    blocking = [g for g in (data.get("gaps") or []) if isinstance(g, dict) and g.get("severity") == "blocking"]
    refuted_fail = data.get("verdict") == "fail" and bool(blocking) and all(str(g.get("id")) in refuted for g in blocking)
    if data.get("verdict") != "pass" and not refuted_fail:
        problems.append("{} records verdict {}, not pass".format(value, json.dumps(data.get("verdict"))))
    claims = data.get("claims") if isinstance(data.get("claims"), list) else []
    if data.get("unit") != key and not any(isinstance(c, dict) and c.get("id") == key for c in claims):
        problems.append("{} does not cover {}: neither unit nor any claim id is that key".format(value, key))
    ran = data.get("ran") if isinstance(data.get("ran"), list) else []
    if not ran:
        problems.append("{} ran no commands; a verdict that ran nothing proves nothing".format(value))
    else:
        clean = [r for r in ran if isinstance(r, dict) and isinstance(r.get("cmd"), str) and r.get("cmd").strip()]
        if len(clean) != len(ran):
            problems.append("{} has ran entries without a command".format(value))
        if not any(r.get("exit") == 0 for r in clean):
            problems.append("{} has no command that exited 0".format(value))
        suite = ctx.suite_for(sub)
        if suite and not any(suite in r.get("cmd", "") and r.get("exit") == 0 for r in clean):
            problems.append("{} does not show the full-suite command '{}' at exit 0".format(value, suite))
    if not claims:
        problems.append("{} has no claims".format(value))
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        label = claim.get("id", "?")
        if claim.get("status") != "holds":
            problems.append("{} claim {} is {}, not holds".format(value, label, claim.get("status")))
        confidence = claim.get("confidence")
        if not isinstance(confidence, (int, float)) or confidence < 75:
            problems.append("{} claim {} has confidence below 75".format(value, label))
        if not claim.get("refutations_attempted"):
            problems.append("{} claim {} records no refutation attempt".format(value, label))
    for gap in data.get("gaps") or []:
        if isinstance(gap, dict) and gap.get("severity") == "blocking" and str(gap.get("id")) not in refuted:
            problems.append("{} still has a blocking gap: {}".format(value, gap.get("what", "?")))
    for entry in data.get("harness_kindness") or []:
        if isinstance(entry, dict) and entry.get("severity") in ("blocking", "should_fix") and not entry.get("resolved"):
            problems.append("{} names a harness kinder than production that is not resolved: {}".format(
                value, entry.get("shim", "?")))
    rung = data.get("rung_supported")
    if rung not in LADDER or LADDER.index(rung) < LADDER.index("Local Proof"):
        problems.append("{} supports only {}, below Local Proof".format(value, rung))
    later = latest_round_problem(ctx, path)
    if later:
        problems.append(later)
    provenance = ctx.provenance(path, "verdict")
    if provenance:
        problems.append(provenance)
    return problems


GAP_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-]*$")


def refuted_gap_ids(ctx, verdict_path, data):
    """Blocking gap ids that a separate drive:verifier refuted: refute-<gap id>.json beside the verdict with result
    refuted, recorded in the provenance ledger for a verifier other than the one that wrote the verdict."""
    rel_verdict = ctx.rel(verdict_path)
    digest = file_sha256(verdict_path)
    authors = {str(e.get("agent_id")) for e in ctx.evidence_entries() if e.get("path") == rel_verdict and e.get("sha256") == digest}
    out = set()
    for gap in data.get("gaps") or []:
        if not isinstance(gap, dict) or gap.get("severity") != "blocking" or not GAP_ID_RE.match(str(gap.get("id", ""))):
            continue
        refute = verdict_path.parent / "refute-{}.json".format(gap["id"])
        body, error = load_json(refute) if refute.is_file() else (None, "missing")
        if error or not isinstance(body, dict) or body.get("result") != "refuted" or ctx.provenance(refute, "refutation"):
            continue
        rel, sha = ctx.rel(refute), file_sha256(refute)
        refuters = {str(e.get("agent_id")) for e in ctx.evidence_entries()
                    if e.get("path") == rel and e.get("sha256") == sha and e.get("role") == "verifier"}
        if refuters - authors:
            out.add(str(gap["id"]))
    return out


def verdict_rung(ctx, value, key):
    """The rung a verdict supports for this key: the claim's own rung_supported when it names one, else the
    verdict's. A verdict never grants Done, so Done reads as Operational."""
    path, problem = evidence_path(ctx, value)
    data, _ = load_json(path) if path is not None and path.is_file() else (None, None)
    if not isinstance(data, dict):
        return "Missing"
    rung = data.get("rung_supported")
    for claim in data.get("claims") if isinstance(data.get("claims"), list) else []:
        if isinstance(claim, dict) and claim.get("id") == key and claim.get("rung_supported") in LADDER:
            rung = claim["rung_supported"]
    if rung == "Done":
        rung = "Operational"
    return rung if rung in LADDER else "Missing"


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".heic"}


def live_problems(ctx, value, key):
    """Why a `live:` token does not prove the claim in a live environment."""
    path, problem = evidence_path(ctx, value)
    if problem:
        return [problem]
    manifest = path / "proof.json" if is_dir_quietly(path) else path
    if not is_file_quietly(manifest):
        return ["live:{} has no proof.json".format(value)]
    data, error = load_json(manifest)
    if error or not isinstance(data, dict):
        return ["{} {}".format(ctx.rel(manifest), error or "is not a JSON object")]
    where = ctx.rel(manifest)
    problems = []
    env = data.get("environment")
    if env not in ("live", "device"):
        problems.append("local-only work is never Live Proof: {} records environment {}".format(where, json.dumps(env)))
    if env == "live" and LOCALHOST_RE.search(str(data.get("target", ""))):
        problems.append("{} says live but its target {} is a local address".format(where, data.get("target")))
    if not str(data.get("target", "")).strip():
        problems.append("{} names no target".format(where))
    if data.get("key") != key:
        problems.append("{} belongs to {}, not {}".format(where, json.dumps(data.get("key")), key))
    if data.get("verdict") != "pass":
        problems.append("{} records verdict {}, not pass".format(where, json.dumps(data.get("verdict"))))
    if "shim_differences" not in data or not isinstance(data.get("shim_differences"), list):
        problems.append("{} does not answer shim_differences (where is the harness kinder than production)".format(where))
    elif not data["shim_differences"] and not str(data.get("shim_differences_note", "")).strip():
        problems.append("{} has an empty shim_differences without a shim_differences_note".format(where))
    commands = data.get("commands")
    if not isinstance(commands, list) or not commands or not all(
            isinstance(c, dict) and str(c.get("cmd", "")).strip() and "exit" in c for c in commands):
        problems.append("{} lists no commands with their exit codes".format(where))
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        problems.append("{} lists no captured artifacts (the live.md, response, log, or screenshot the proof rests on, each with its sha256)".format(where))
    else:
        for artifact in artifacts:
            if not isinstance(artifact, dict) or not str(artifact.get("path", "")).strip():
                problems.append("{} has an artifact without a path".format(where))
                continue
            target = realpath_loose(manifest.parent / str(artifact["path"]))
            if not is_within(target, realpath_loose(ctx.root)) or not is_file_quietly(target):
                problems.append("{} names the artifact {}, which does not exist beside it".format(where, artifact["path"]))
            elif file_sha256(target) != str(artifact.get("sha256", "")).lower():
                problems.append("{} records a sha256 for {} that does not match the file".format(where, artifact["path"]))
    commit = str(data.get("commit", ""))
    if ctx.git and not commit_exists(ctx.root, commit):
        problems.append("{} names commit {} which does not exist".format(where, commit or "(none)"))
    if str(data.get("produced_by", "")).split(":", 1)[-1] not in CHECKER_PRODUCERS:
        problems.append("{} was not produced by a checker (produced_by is {}; only verifier or ui-reviewer)".format(
            where, json.dumps(data.get("produced_by"))))
    provenance = ctx.provenance(manifest, "live-proof")
    if provenance:
        problems.append(provenance)
    return problems


def status_rows_at(ctx, rev):
    text = show_at(ctx.root, rev, ".drive/STATUS.md")
    return Status(text).by_key() if text is not None else None


def check_status(ctx, f, mode):
    name = "STATUS.md"
    status = ctx.status
    if status is None:
        f.fail(name, "is missing. Create it from templates/STATUS.md.")
        return
    registry = ctx.state.fields.get("registry") if ctx.state else None
    if registry:
        if "registry" not in status.fields:
            f.fail(name, "must carry the 'registry: <command>' line when STATE.md names a registry.")
        return
    if not status.header_ok:
        f.fail(name, "must start with '# STATUS · <project>'.")
    if "ladder" not in status.fields:
        f.fail(name, "is missing the 'ladder:' line.")
    if status.columns is None:
        f.fail(name, "has no table. Add the table header: | key | claim | live | status | evidence | updated |.")
        return
    if status.columns != STATUS_COLUMNS:
        f.fail(name, "table columns must be exactly: key | claim | live | status | evidence | updated.")
        return
    phase = ctx.state.fields.get("phase", "") if ctx.state else ""
    seen = set()
    oracle_use = {}
    for row in status.rows:
        label = "STATUS {}".format(row.key or "line {}".format(row.lineno))
        if len(row.cells) != 6:
            f.fail(label, "has {} cells; every row needs six.".format(len(row.cells)))
            continue
        if not SLUG_RE.match(row.key):
            f.fail(label, "the key must be a lowercase slug of the claim's words.")
        if row.key in seen:
            f.fail(label, "the key appears twice; keys are unique.")
        seen.add(row.key)
        claim = row.claim[4:].strip() if row.ui else row.claim
        if not claim:
            f.fail(label, "has no claim.")
        elif claim.lower().startswith(WORK_VERBS):
            f.warn(label, "the claim describes work, not behaviour. Name what a test could refute.")
        if row.live not in ("y", "n"):
            f.fail(label, "live must be y or n.")
        if row.status not in LADDER and row.status != DROPPED:
            f.fail(label, "status '{}' is not a ladder rung or Dropped.".format(row.status))
            continue
        updated = parse_date(row.updated)
        if updated is None:
            f.fail(label, "updated must be a date like 2026-09-14.")
        elif updated > ctx.today_utc + dt.timedelta(days=1):
            f.fail(label, "updated is in the future.")
        for bad in row.bad_tokens:
            f.fail(label, "'{}' is not an evidence token. Use test:, severe:, verdict:, proof:, shot:, live:, ops:, review:, commit:, doc:, why:, planned:, or sub:.".format(bad[:60]))
        for kind, value in row.tokens:
            if not value:
                f.fail(label, "{}: has no value.".format(kind))
                continue
            problem = None
            if kind in ("test", "severe"):
                problem = test_token_problem(ctx, kind, value)
                oracle_use.setdefault(value, []).append(row.key)
            elif kind == "sub":
                if not SLUG_RE.match(value) or ctx.goal is None or ctx.goal.sub_classification(value) is None:
                    problem = "sub:{} names no '## Classification · {}' section in GOAL.md".format(value, value)
            elif kind == "planned":
                if "::" not in value:
                    problem = "planned:{} must be written as planned:<path>::<test name>".format(value)
            elif kind == "commit":
                if not ctx.git or not commit_exists(ctx.root, value):
                    problem = "commit {} does not exist in this repository".format(value)
            elif kind in ("proof", "shot", "review", "doc"):
                path, problem = evidence_path(ctx, value)
                if not problem and not exists_quietly(path):
                    problem = "{}: {} does not exist".format(kind, value)
                elif not problem and kind == "shot":
                    images = [path] if path.is_file() else [p for p in path.rglob("*") if p.is_file()]
                    if not any(p.suffix.lower() in IMAGE_SUFFIXES for p in images):
                        problem = "shot: {} is not a screenshot (no .png, .jpg, .webp, .gif, or .heic file)".format(value)
            elif kind == "ops":
                if not re.match(r"^https?://", value):
                    path, problem = evidence_path(ctx, value)
                    if not problem and not exists_quietly(path):
                        problem = "ops: {} is neither a URL nor an existing path".format(value)
            if problem:
                f.fail(label, problem + ".")
        tests, severes = row.values("test"), row.values("severe")
        verdicts, lives = row.values("verdict"), row.values("live")
        whys = row.values("why")
        device_only = any(w.startswith("device-only:") for w in whys)
        if row.status == DROPPED:
            if not whys:
                f.fail(label, "is Dropped without why:. Record the reason.")
            continue
        rung = row.rung
        if row.values("planned"):
            where = ("a {} row".format(row.status) if rung >= LADDER.index("Partial") else "lint --final" if mode == "final"
                     else "the {} phase".format(phase) if phase in POST_TEST_PHASES else None)
            if where:
                f.fail(label, "planned: tests are allowed only on rows below Partial and before the harden phase, never at {}, "
                              "and are never evidence. Replace them with test: once the test exists.".format(where))
        if rung >= LADDER.index("Scaffold") and not row.values("commit"):
            f.fail(label, "{} needs commit:.".format(row.status))
        if rung >= LADDER.index("Partial") and not tests:
            f.fail(label, "{} needs at least one test:. Lower the row or cite the test.".format(row.status))
        if rung >= LADDER.index("Local Proof"):
            if not severes:
                f.fail(label, "{} needs a severe: test that tries to refute the claim. Add one or lower the row to Partial.".format(row.status))
            if row.ui and not row.values("shot"):
                f.fail(label, "{} is a [ui] row and needs shot:.".format(row.status))
            if not verdicts:
                f.fail(label, "{} needs a verdict: from an independent verifier. Only a verifier's pass moves a row to Local Proof.".format(row.status))
            else:
                reasons = [verdict_problems(ctx, v, row.key, (row.values("sub") or [None])[0]) for v in verdicts]
                if all(reasons):
                    for problem in reasons[0][:4]:
                        f.fail(label, problem + ".")
                else:
                    supported = max((verdict_rung(ctx, v, row.key) for v, r in zip(verdicts, reasons) if not r), key=LADDER.index)
                    required = row.status if row.status in ("Live Proof", "Operational") else (
                        "Live Proof" if row.status == "Done" and row.live == "y" else "Local Proof")
                    if LADDER.index(supported) < LADDER.index(required):
                        f.fail(label, "is {} but its verdict supports only {}. A row never sits above the rung its verdict supports: "
                               "lower the row, or have the verifier verify it at {}.".format(row.status, supported, required))
        need_live = (LADDER.index("Live Proof") <= rung <= LADDER.index("Operational")) or (
            row.status == "Done" and row.live == "y")
        if need_live:
            if not lives:
                f.fail(label, "{} needs live: evidence from the real environment. Local-only work is never Live Proof.".format(row.status))
            else:
                reasons = [live_problems(ctx, v, row.key) for v in lives]
                if all(reasons):
                    for problem in reasons[0][:4]:
                        f.fail(label, problem + ".")
        if rung >= LADDER.index("Operational") and row.status != "Done" and not row.values("ops"):
            f.fail(label, "Operational needs ops:.")
        if row.status == "Done":
            if not row.values("review"):
                f.fail(label, "Done needs review: pointing at the final audit.")
            if not row.values("doc"):
                f.warn(label, "is Done with no doc: token. When user-facing behaviour changed, Done needs the doc that describes it.")
            if device_only:
                f.fail(label, "carries why:device-only, so it can reach Local Proof but never Done. Get the live proof or keep the row at Local Proof.")
    for value, keys in oracle_use.items():
        if len(keys) > 5:
            f.warn(name, "the test {} is the evidence for {} rows; one oracle should not carry that many claims.".format(value, len(keys)))
    check_status_history(ctx, f, mode)


def check_status_history(ctx, f, mode):
    """Row retention, today's date on changed rows, and target narrowing."""
    if not ctx.head or ctx.status is None:
        return
    current = ctx.status.by_key()
    head_rows = status_rows_at(ctx, "HEAD")
    if head_rows:
        for key, old in head_rows.items():
            new = current.get(key)
            if new is None:
                f.fail("STATUS {}".format(key), "existed at HEAD and is gone. Rows are never deleted; restore it, or mark it Dropped with why: and a DECISIONS.md entry.")
                continue
            if new.status != old.status and not ctx.today_ok(parse_date(new.updated)):
                f.warn("STATUS {}".format(key), "changed status since HEAD; set updated to today.")
    bases = [("HEAD", head_rows)]
    if mode == "final":
        intake = ctx.intake_commit()
        if intake:
            bases.append((intake, status_rows_at(ctx, intake)))
    if mode == "final":
        intake = ctx.intake_commit()
        if intake:
            has_parent = git(ctx.root, "rev-parse", "--verify", "--quiet", intake + "^")[0] == 0
            span = "{}^..HEAD".format(intake) if has_parent else "HEAD"
            first_seen = {}
            for rev in (git_out(ctx.root, "log", "--format=%H", span, "--", ".drive/STATUS.md") or "").split():
                for key in status_rows_at(ctx, rev) or {}:
                    first_seen[key] = rev
            for key, rev in sorted(first_seen.items()):
                if key not in current and key not in (head_rows or {}):
                    f.fail("STATUS {}".format(key), "was committed in {} and is gone. Rows are never deleted, even in a later commit; "
                           "restore it, or mark it Dropped with why: and a DECISIONS.md entry.".format(rev[:7]))
    goal_path = ".drive/GOAL.md"
    for rev, old_rows in bases:
        narrowed = []
        for key, old in (old_rows or {}).items():
            new = current.get(key)
            if new is None:
                if rev != "HEAD":
                    f.fail("STATUS {}".format(key), "was recorded at intake and is gone. Rows are never deleted.")
                continue
            if old.live == "y" and new.live == "n":
                narrowed.append((key, key, "live changed from y to n"))
            if new.status == DROPPED and old.status != DROPPED:
                narrowed.append((key, key, "became Dropped"))
        old_goal = show_at(ctx.root, rev, goal_path)
        if old_goal is not None and ctx.goal is not None:
            old_phases = {PLAN_RE.match(l).group("phase") for _, l in Goal(old_goal).plan if PLAN_RE.match(l)}
            new_phases = {PLAN_RE.match(l).group("phase") for _, l in ctx.goal.plan if PLAN_RE.match(l)}
            for phase in sorted(old_phases - new_phases):
                narrowed.append((None, phase, "lost the {} phase".format(phase)))
        if not narrowed:
            continue
        before = show_at(ctx.root, rev, ".drive/DECISIONS.md")
        now = read_text(ctx.drive / "DECISIONS.md")
        where = "HEAD" if rev == "HEAD" else "the intake commit"
        added = "" if now is None or now == before else (now if before is None else now[len(os.path.commonprefix([before, now])):])
        for key, needle, what in narrowed:
            label = "STATUS {}".format(key) if key else "GOAL.md"
            if not added:
                f.fail(label, "{} since {} without a DECISIONS.md entry. Lowering a target needs a decision with its undo in the same commit.".format(what, where))
            elif not re.search(r"(?<![A-Za-z0-9\-]){}(?![A-Za-z0-9\-])".format(re.escape(needle)), added):
                f.fail(label, "{} since {}, and no new DECISIONS.md entry names {}. A decision excuses only the narrowing it names on its "
                       "Narrows line.".format(what, where, "the key " + needle if key else "the " + needle + " phase"))


def decision_entries(text):
    doc = Doc(text)
    return doc, [(name, doc.sections[name]) for name in doc.section_order]


def check_decisions(ctx, f):
    path = ctx.drive / "DECISIONS.md"
    text = read_text(path)
    if text is None:
        return
    doc, entries = decision_entries(text)
    if not doc.title.startswith("DECISIONS ·"):
        f.fail("DECISIONS.md", "must start with '# DECISIONS · <project>'.")
    for heading, lines in entries:
        label = "DECISIONS {}".format(heading[:60])
        if not re.match(r"^\d{4}-\d{2}-\d{2} · \S", heading):
            f.fail(label, "headings must read '## <YYYY-MM-DD> · <the decision in plain words>'.")
        fields = doc.fields([(n, l[2:]) for n, l in lines if l.startswith("- ")])
        for field in ("decision", "undo"):
            if not fields.get(field):
                f.fail(label, "needs a '- {}:' line.".format(field.capitalize()))
    if ctx.head:
        before = show_at(ctx.root, "HEAD", ".drive/DECISIONS.md")
        if before:
            _, old_entries = decision_entries(before)
            current = {h: [l.rstrip() for _, l in ls if l.strip()] for h, ls in entries}
            for heading, lines in old_entries:
                old_body = [l.rstrip() for _, l in lines if l.strip()]
                if heading not in current:
                    f.fail("DECISIONS.md", "the entry '{}' existed at HEAD and is gone. DECISIONS.md is append-only; a reversal is a new entry.".format(heading[:60]))
                elif current[heading][:len(old_body)] != old_body:
                    f.fail("DECISIONS.md", "the entry '{}' was altered after it was committed. Append a new entry instead.".format(heading[:60]))


# ----------------------------------------------------------------------------------------------
# GOAL.md, STATE.md, and the other run files

RESTATE_KEYS = ["outcome", "user", "why now", "success", "constraints", "out of scope"]
PROBE_COMMAND_KEYS = ["build_command", "focused_test_command", "test_command"]


def header_placeholders(fields):
    return [key for key, value in fields.items() if PLACEHOLDER_RE.search(value or "")]


def check_goal(ctx, f, mode):
    name = "GOAL.md"
    goal = ctx.goal
    if goal is None:
        f.fail(name, "is missing. Write it at intake from templates/GOAL.md.")
        return
    if not goal.doc.title.startswith("GOAL ·") or not SLUG_RE.match(goal.slug):
        f.fail(name, "must start with '# GOAL · <goal slug>' where the slug is lowercase words joined by hyphens.")
    for field in ("goal", "live means", "budget"):
        if not goal.fields.get(field):
            f.fail(name, "is missing the '{}:' line.".format(field))
    if goal.fields.get("goal") and not goal.fields["goal"].startswith('"'):
        f.fail(name, "the goal line must quote the prompt verbatim in double quotes.")
    for key in header_placeholders(goal.fields):
        f.fail(name, "the '{}:' line still holds a template placeholder.".format(key))
    if goal.doc.section("Restate") is None:
        f.fail(name, "has no Restate section (outcome, user, why now, success, constraints, out of scope).")
    else:
        for key in RESTATE_KEYS:
            value = goal.restate.get(key, "")
            if not value:
                f.fail(name, "Restate is missing '{}:'.".format(key))
            elif not (value.startswith('"') or value.lower().startswith("assumption:")) or PLACEHOLDER_RE.search(value):
                f.fail(name, "Restate '{}' must be quoted from the goal or begin with 'assumption:'.".format(key))
    if goal.classification_error:
        f.fail(name, goal.classification_error + ".")
    for section, cls in goal.classifications:
        label = "{} {}".format(name, section)
        for key, value in cls.items():
            if isinstance(value, ValueError):
                f.fail(label, "'{}' does not parse: {}.".format(key, value))
        if cls.get("shape") not in SHAPES:
            f.fail(label, "shape must be one of {}.".format(", ".join(SHAPES)))
        variant = cls.get("variant")
        if variant is not None:
            full = variant if "/" in str(variant) else "{}/{}".format(cls.get("shape"), variant)
            if full not in VARIANTS:
                f.fail(label, "variant '{}' is not one of {} or null.".format(variant, ", ".join(sorted(VARIANTS))))
        if cls.get("size") not in SIZES:
            f.fail(label, "size must be one of XS, S, M, L, XL.")
        if not cls.get("size_set_by"):
            f.fail(label, "size_set_by must name the structural trigger that set the size.")
        traits = cls.get("traits")
        if not isinstance(traits, dict):
            f.fail(label, "traits must be written as { confirmed: [...], suspected: [...] }.")
        else:
            for group in ("confirmed", "suspected"):
                values = traits.get(group, [])
                if not isinstance(values, list):
                    f.fail(label, "traits.{} must be a list.".format(group))
                    continue
                for trait in values:
                    if trait not in TRAITS:
                        f.fail(label, "'{}' is not a trait from the vocabulary.".format(trait))
        probe = cls.get("probe")
        if not isinstance(probe, dict):
            f.fail(label, "probe must be a mapping with repo, baseline_sha, and the build, focused-test, and full-suite commands.")
        else:
            for key in PROBE_COMMAND_KEYS + ["baseline_sha"]:
                if key not in probe:
                    f.fail(label, "probe is missing {} (write none when the project has no such command).".format(key))
            baseline = str(probe.get("baseline_sha") or "")
            if baseline and baseline != "none" and ctx.head and not commit_exists(ctx.root, baseline):
                f.fail(label, "probe baseline_sha {} does not exist in this repository.".format(baseline))
        if parse_iso(str(cls.get("classified_at", ""))) is None:
            f.fail(label, "classified_at must be an ISO UTC timestamp.")
        if not isinstance(cls.get("reclassifications"), list):
            f.fail(label, "reclassifications must be a list (write [] when there are none).")
    if not goal.plan:
        f.fail(name, "has no plan lines.")
    for number, line in goal.plan:
        match = PLAN_RE.match(line)
        if not match:
            f.fail(name, "plan line {} must read '- [ ] <phase> · artifact: <path> · exit: <condition> · checker: <role>'.".format(number))
            continue
        if match.group("phase") not in PHASES:
            f.fail(name, "plan line {} names '{}', which is not a canonical phase.".format(number, match.group("phase")))
        if match.group("checker").split(":", 1)[-1] not in CHECKERS:
            f.fail(name, "plan line {} names checker '{}'; use {}.".format(number, match.group("checker"), ", ".join(sorted(CHECKERS))))
        if PLACEHOLDER_RE.search(line):
            f.fail(name, "plan line {} still holds a template placeholder.".format(number))
        if mode == "final" and match.group("tick") == " " and not (ctx.state and ctx.state.status == "stopped"):
            f.fail(name, "plan line {} ({}) is not ticked. Tick it, or mark it [-] with a Re-plans line saying why.".format(number, match.group("phase")))
    if goal.doc.section("Re-plans") is None:
        f.fail(name, "has no Re-plans section.")
    if ctx.head:
        tracked = git_out(ctx.root, "ls-files", "--", ".drive") or ""
        others = [p for p in tracked.splitlines() if p not in (".drive/GOAL.md", ".drive/capabilities.json")
                  and not p.startswith(".drive/runs/")]
        intake = ctx.intake_commit()
        if intake is None and others:
            f.fail(name, "has no drive(intake): {} commit while other run files are committed. GOAL.md is committed first, with that message.".format(goal.slug or "<slug>"))
        elif intake:
            earlier = git_out(ctx.root, "log", "--diff-filter=A", "--name-only", "--format=", intake + "^", "--", ".drive") \
                if git(ctx.root, "rev-parse", "--verify", "--quiet", intake + "^")[0] == 0 else ""
            early = [p for p in (earlier or "").splitlines() if p.strip() and p not in (".drive/capabilities.json",)
                     and not p.startswith(".drive/runs/")]
            if early:
                f.fail(name, "was committed after other run files ({}). GOAL.md is committed before any other work.".format(", ".join(early[:3])))


def intake_commit(ctx):
    """The commit named `drive(intake): <slug>`, found by its message and never by file history."""
    if not ctx.head or ctx.goal is None or not ctx.goal.slug:
        return None
    found = git_out(ctx.root, "log", "--grep", "^drive(intake): {}$".format(ctx.goal.slug), "--format=%H", "-1")
    return found or None


Ctx.intake_commit = intake_commit


def latest_code_commit(ctx):
    """(sha, committer unix time) of the newest commit touching anything outside `.drive/`."""
    if not ctx.head:
        return None
    out = git_out(ctx.root, "log", "-1", "--format=%H %ct", "--", ".", ":(top,exclude).drive")
    if not out:
        return None
    sha, stamp = out.split()
    return sha, int(stamp)


def is_ancestor(ctx, older, newer):
    return git(ctx.root, "merge-base", "--is-ancestor", older, newer)[0] == 0


STATE_SECTIONS = ["Resume here", "Verified facts", "Rules in force", "Open failures", "Workaround ledger", "Boundary events"]


def check_state(ctx, f, mode):
    name = "STATE.md"
    state = ctx.state
    if state is None:
        f.fail(name, "is missing. Write it from templates/STATE.md.")
        return
    if not state.doc.title.startswith("STATE ·"):
        f.fail(name, "must start with '# STATE · <project> · <goal slug>'.")
    fields = state.fields
    for field in ("status", "phase", "next", "updated", "commit", "session", "model"):
        if not fields.get(field):
            f.fail(name, "is missing the '{}:' header line.".format(field))
    for key in header_placeholders(fields):
        f.fail(name, "the '{}:' line still holds a template placeholder.".format(key))
    if fields.get("status") and fields["status"] not in RUN_STATUSES:
        f.fail(name, "status '{}' must be one of {}.".format(fields["status"], ", ".join(RUN_STATUSES)))
    if fields.get("phase") and fields["phase"] not in PHASES:
        f.fail(name, "phase '{}' is not a canonical phase name.".format(fields["phase"]))
    updated = parse_iso(fields.get("updated", ""))
    if fields.get("updated") and updated is None:
        f.fail(name, "updated must be an ISO UTC timestamp such as 2026-09-14T09:12:04Z.")
    elif updated is not None and updated > now_utc() + dt.timedelta(minutes=15):
        # A timestamp ahead of the clock would pass the staleness check below for as long as it stays ahead.
        f.fail(name, "updated {} is ahead of the clock ({}). Write the time from `date -u +%Y-%m-%dT%H:%M:%SZ`, not an estimate.".format(
            fields.get("updated"), iso_now()))
    commit = fields.get("commit", "")
    if commit:
        if not ctx.head:
            if commit != "none":
                f.fail(name, "commit must be 'none' until the repository has a commit.")
        elif not commit_exists(ctx.root, commit):
            f.fail(name, "commit {} does not exist in this repository.".format(commit))
        elif not is_ancestor(ctx, commit, "HEAD"):
            f.fail(name, "commit {} is not an ancestor of HEAD.".format(commit))
        else:
            count = git_out(ctx.root, "rev-list", "--count", "{}..HEAD".format(commit), "--", ".", ":(top,exclude).drive")
            if count and int(count) > 1:
                f.fail(name, "commit {} is {} code commits behind HEAD. Rewrite STATE.md with the current commit and next step.".format(commit, count))
    latest = latest_code_commit(ctx)
    if latest and updated:
        state_commit = git_out(ctx.root, "log", "-1", "--format=%H", "--", ".drive/STATE.md")
        fresh = state_commit and is_ancestor(ctx, latest[0], state_commit)
        if not fresh and updated.timestamp() < latest[1]:
            f.fail(name, "is stale: updated {} is older than the latest code commit {}. Rewrite Resume here, next, updated, and commit.".format(
                fields.get("updated"), latest[0][:7]))
    for section in STATE_SECTIONS:
        if state.doc.section(section) is None:
            f.fail(name, "is missing the '## {}' section.".format(section))
    if state.doc.section("Discoveries") is None:
        f.warn(name, "has no '## Discoveries' section for noticed-but-untouched items.")
    for field in ("why", "blocked on", "in flight"):
        if not state.resume.get(field):
            f.fail(name, "Resume here needs a non-empty '{}:' line.".format(field.capitalize()))
    for number, line in state.doc.bullets("Verified facts"):
        if "Verified:" not in line:
            f.fail(name, "line {}: every verified fact names how it was verified with 'Verified:'.".format(number))
    for number, line in state.doc.bullets("Rules in force"):
        if "Because:" not in line or "From:" not in line:
            f.fail(name, "line {}: every rule in force carries 'Because:' and 'From:'.".format(number))
    for number, line in state.doc.bullets("Open failures"):
        if not re.match(r"^- \d{4}-\d{2}-\d{2} [a-z0-9][a-z0-9\-]*: \S", line) or not re.search(r"Repro:|Observed:", line):
            f.fail(name, "line {}: an open failure reads '- <date> <slug>: <symptom>. Repro: <...> | Observed: <n of m>. Next: <step>.'".format(number))
    for number, line in state.doc.bullets("Boundary events"):
        if len(line.split(" · ")) < 5:
            f.warn(name, "line {}: a boundary event has five parts: time · step · category · action · result.".format(number))
    header, rows = state.ledger()
    if state.doc.section("Workaround ledger") is not None:
        if header is None:
            f.fail(name, "the workaround ledger needs its table header: | obstacle | workaround | by | when | count |.")
        elif header[:5] != ["obstacle", "workaround", "by", "when", "count"]:
            f.fail(name, "the workaround ledger columns must be obstacle | workaround | by | when | count.")
        else:
            records = [read_text(p) or "" for p in sorted((ctx.drive / "investigations").glob("*.md"))]
            for number, cells in rows:
                count = cells[4] if len(cells) > 4 else ""
                if not re.match(r"^\d+$", count):
                    f.fail(name, "line {}: the workaround count must be a whole number.".format(number))
                    continue
                if int(count) >= 2:
                    obstacle = cells[0].lower()
                    if not any("repeated-workaround" in r and obstacle in r.lower() for r in records):
                        f.fail(name, "line {}: the workaround for '{}' was needed twice and no investigation with Trigger repeated-workaround names it. Second time is the bug: open the record now.".format(number, cells[0]))
    if ctx.head and fields.get("status") in GATE_CLOSED:
        before = show_at(ctx.root, "HEAD", ".drive/STATE.md")
        old_status = State(before).status if before else ""
        if old_status == "stalled":
            f.fail(name, "status was stalled at HEAD and is {} now. A stalled run does no more work: write REPORT.md saying "
                   "'Stopped because' and naming the stall, then run drive.py end; new work is a new run.".format(fields["status"]))
        elif old_status == "blocked":
            old_entries = decision_entries(show_at(ctx.root, "HEAD", ".drive/DECISIONS.md") or "")[1]
            new_entries = decision_entries(read_text(ctx.drive / "DECISIONS.md") or "")[1]
            if len(new_entries) <= len(old_entries):
                f.fail(name, "status was blocked at HEAD and is {} now with no new DECISIONS.md entry. A blocked run continues "
                       "only after one DECISIONS.md entry names the evidence that its blocking condition cleared.".format(fields["status"]))
    lines = state.text.count("\n") + 1
    if lines > 150 or len(state.text.encode("utf-8")) > 12000:
        f.fail(name, "has {} lines; the budget is 150. Move closed failures out and delete what git already records.".format(lines))
    elif lines > 120:
        f.warn(name, "has {} lines and is nearing the 150-line budget.".format(lines))


def check_secrets(ctx, f):
    for path in sorted(ctx.drive.rglob("*")):
        rel = path.relative_to(ctx.drive).parts
        if not path.is_file() or rel[0] == "local" or path.stat().st_size > 2_000_000:
            continue
        text = read_text(path)
        if text is None:
            continue
        for number, line in enumerate(text.splitlines(), 1):
            for label, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    f.fail(ctx.rel(path), "line {} holds what looks like {}. Remove it and rotate the secret; nothing secret goes in .drive/.".format(number, label))
                    break


PROOF_ROUND_RE = re.compile(r"^r(\d+)$")


def superseded_round_file(ctx, path, cited):
    """True for a file under .drive/proofs/<key>/r<n>/ when a higher round exists for that key and no STATUS verdict:
    token cites it: historical evidence a later round replaced, which nobody should rewrite to satisfy the lint."""
    parts = path.relative_to(ctx.drive).parts
    match = PROOF_ROUND_RE.match(parts[2]) if len(parts) >= 4 and parts[0] == "proofs" else None
    if not match:
        return False
    try:
        rounds = [int(m.group(1)) for m in (PROOF_ROUND_RE.match(p.name) for p in (ctx.drive / "proofs" / parts[1]).iterdir()
                                             if p.is_dir()) if m]
    except OSError:
        return False
    return int(match.group(1)) < max(rounds or [0]) and realpath_loose(path) not in cited


def check_placeholders(ctx, f):
    cited = set()
    for row in (ctx.status.rows if ctx.status else []):
        for value in row.values("verdict"):
            resolved, _ = evidence_path(ctx, value)
            if resolved is not None:
                cited.add(resolved)
    for path in sorted(ctx.drive.rglob("*")):
        rel = path.relative_to(ctx.drive).parts
        if not path.is_file() or rel[0] in ("local", "runs") or path.suffix not in (".md", ".json"):
            continue
        if path.name in ("GOAL.md", "STATE.md"):
            continue
        text = read_text(path)
        if text is None:
            continue
        if path.suffix == ".json":
            data, error = load_json(path)
            if error:
                f.fail(ctx.rel(path), error + ".")
                continue
            if superseded_round_file(ctx, path, cited):
                continue
            for where, token in json_placeholders(data)[:3]:
                advice = (" Record the command exactly as it ran, with the real path it used in place of {}.".format(token)
                          if COMMAND_FIELD_RE.match(where) else "")
                f.fail(ctx.rel(path), "{} still holds the template placeholder {}.{}".format(where, token, advice))
            continue
        for number, token in find_placeholders(text, include_yaml_fences=False)[:3]:
            f.fail(ctx.rel(path), "line {} still holds the template placeholder {}.".format(number, token))


LESSON_FIELDS = ["When", "Do", "Because", "Check", "Verified by", "Applies to", "Not for", "Seen"]


def parse_lessons(text, section=None):
    """Lesson entries as (lineno, heading, fields). With `section`, only entries under that `## ` heading."""
    entries, current, active, in_fence = [], None, section is None, False
    for number, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
        if in_fence:
            continue
        if line.startswith("## "):
            if section is not None:
                active = re.sub(r"^\d+\.\s*", "", line[3:].strip()) == section
            current = None
            continue
        if not active:
            continue
        if line.startswith("### "):
            current = (number, line[4:].strip(), {})
            entries.append(current)
            continue
        match = re.match(r"^- ([A-Z][A-Za-z ]+?):\s*(.*)$", line)
        if current and match:
            current[2].setdefault(match.group(1), match.group(2).strip())
    return entries


def lesson_entry_problems(heading, fields, project=False):
    problems = []
    for field in LESSON_FIELDS:
        if not fields.get(field):
            problems.append("is missing '- {}:'".format(field))
    seen = fields.get("Seen", "")
    if seen and not re.match(r"^\d+", seen):
        problems.append("Seen must start with a count")
    if PLACEHOLDER_RE.search(strip_inline_code(heading)) or any(PLACEHOLDER_RE.search(strip_inline_code(v)) for v in fields.values()):
        problems.append("still holds a template placeholder")
    if not project and (re.search(r"[\w\-]+/[\w\-./]+\.\w+", heading) or re.search(r"\b[0-9a-f]{7,40}\b", heading)):
        problems.append("its heading names a path or a hash; a rule is a sentence, not a fix")
    return problems


def check_project_lessons(ctx, f):
    text = read_text(ctx.drive / "LESSONS.md")
    if text is None:
        return
    if not text.startswith("# LESSONS ·"):
        f.fail("LESSONS.md", "must start with '# LESSONS · <project>'.")
    entries = parse_lessons(text)
    for number, heading, fields in entries:
        for problem in lesson_entry_problems(heading, fields, project=True):
            f.fail("LESSONS.md", "line {} '{}' {}.".format(number, heading[:50], problem))
    if len(entries) > 40:
        f.fail("LESSONS.md", "has {} entries; the cap is 40. Consolidate now.".format(len(entries)))


INVESTIGATION_STATUSES = ["open", "diagnosed", "verified", "fixed", "distilled", "closed-no-lesson"]
TRIGGERS = ["green-check-failed", "verifier-rejection", "false-assumption", "repeated-workaround",
            "check-relaxed", "incident", "eval-regression", "budget-overrun"]
INVESTIGATION_SECTIONS = ["Fail", "Investigate", "Verify", "Fix", "Distill", "Gate log"]
POSTMORTEM_SECTIONS = ["Timeline", "Impact", "Detection", "Why the gates did not catch it",
                       "Gate changes made now", "What to do differently in the first hour"]
VAGUE_MECHANISMS = {"flaky", "flakiness", "race condition", "a race condition", "tooling", "tooling issue",
                    "environment", "environment issue", "model error", "the model misunderstood",
                    "unknown", "intermittent", "timing", "network issue"}


def field_in(doc, section, name):
    for _, line in doc.sections.get(section, []):
        match = re.match(r"^\s*-\s*{}:\s*(.*)$".format(re.escape(name)), line)
        if match:
            return match.group(1).strip()
    return ""


def check_investigations(ctx, f, mode):
    folder = ctx.drive / "investigations"
    if not folder.is_dir():
        return
    for path in sorted(folder.glob("*.md")):
        label = ctx.rel(path)
        doc = Doc(read_text(path) or "")
        if not re.match(r"^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9\-]*\.md$", path.name):
            f.fail(label, "investigation files are named <YYYY-MM-DD>-<slug>.md.")
        fields = doc.fields()
        status = fields.get("status", "")
        base_status = status.split(" (", 1)[0].strip()
        if base_status not in INVESTIGATION_STATUSES:
            f.fail(label, "Status must be one of {}.".format(", ".join(INVESTIGATION_STATUSES)))
            continue
        if fields.get("trigger") not in TRIGGERS:
            f.fail(label, "Trigger must be one of {}.".format(", ".join(TRIGGERS)))
        for field in ("detected", "got past", "timebox"):
            if not fields.get(field):
                f.fail(label, "is missing '{}:'.".format(field.capitalize()))
        for section in INVESTIGATION_SECTIONS:
            if doc.section(section) is None:
                f.fail(label, "is missing the '## {}' section.".format(section))
        rank = INVESTIGATION_STATUSES.index(base_status)
        if rank >= 1 and base_status != "closed-no-lesson" or base_status == "closed-no-lesson" and field_in(doc, "Investigate", "Mechanism"):
            mechanism = field_in(doc, "Investigate", "Mechanism")
            if not mechanism or PLACEHOLDER_RE.search(mechanism):
                f.fail(label, "is {} but names no mechanism.".format(base_status))
            elif mechanism.lower().strip(" .") in VAGUE_MECHANISMS:
                f.fail(label, "the mechanism '{}' is a place to look, not a cause. Name the line, limit, ordering, race between two named operations, or environment difference.".format(mechanism))
            candidates = [l for _, l in doc.sections.get("Investigate", []) if re.match(r"^\s+\d+\.\s+\S", l)]
            if len(candidates) < 3:
                f.fail(label, "Investigate lists {} candidate causes; it needs at least three.".format(len(candidates)))
        if base_status in ("verified", "fixed", "distilled"):
            for field in ("Prediction", "Check run", "Revert check"):
                if not field_in(doc, "Verify", field):
                    f.fail(label, "is {} but Verify has no '{}:'.".format(base_status, field))
        if base_status in ("fixed", "distilled"):
            if not field_in(doc, "Fix", "Change"):
                f.fail(label, "is {} but Fix names no change.".format(base_status))
        if base_status in ("distilled", "closed-no-lesson"):
            if not field_in(doc, "Distill", "Candidate lesson") and not field_in(doc, "Distill", "Candidate lessons"):
                f.fail(label, "is {} but Distill records no decision. Write the lesson or 'none' with the reason.".format(base_status))
        if base_status != "open" and not doc.bullets("Gate log"):
            f.fail(label, "has no Gate log lines.")
        if doc.section("Timeline") is not None:
            for section in POSTMORTEM_SECTIONS:
                if doc.section(section) is None:
                    f.fail(label, "extends into a post-mortem but lacks '## {}'.".format(section))
        if mode == "final":
            run_status = ctx.state.status if ctx.state else ""
            if run_status == "stopped" and base_status == "open":
                f.fail(label, "is still open. A stopped run closes or explains every investigation.")
            elif run_status != "stopped" and base_status not in ("distilled", "closed-no-lesson"):
                f.fail(label, "is still {}. Close it as distilled or closed-no-lesson before Done.".format(status))


RETRO_SECTIONS = ["Investigations", "Repeated workarounds", "Candidates", "Lessons consulted",
                  "Skill instructions at fault", "Consolidation", "Lessons committed"]


def retro_files(ctx):
    return sorted((ctx.drive / "reviews").glob("*-retro.md")) if (ctx.drive / "reviews").is_dir() else []


def check_retros(ctx, f):
    for path in retro_files(ctx):
        doc = Doc(read_text(path) or "")
        for section in RETRO_SECTIONS:
            if doc.section(section) is None:
                f.fail(ctx.rel(path), "is missing the '## {}' section.".format(section))
        if not doc.section("Lessons committed") or not any(l.strip() for _, l in doc.section("Lessons committed")):
            f.fail(ctx.rel(path), "Lessons committed is empty; list each lesson with its commit, or write none with the reason.")


HANDOFF_FIELDS = ["goal", "round", "rubric", "spec", "previous gaps", "output"]
HANDOFF_SECTIONS = ["Claims", "Scope", "Validation", "Evidence inputs", "Lessons that apply to this task", "What to return"]
MAKER_LEAK_RE = re.compile(r"(?i)\b(the maker (says|reports|claims)|implementer (says|reports|claims)|tests pass(ed)? according|i (fixed|made)|honest_gaps|summary from)\b")
OPENING_RE = re.compile(r"I'm working on .+ for .+\. They need .+\. With that in mind:")


def check_handoffs(ctx, f):
    folder = ctx.drive / "handoffs"
    if not folder.is_dir():
        return
    keys = set(ctx.status.by_key()) if ctx.status else set()
    packages = {p.name for p in (ctx.drive / "packages").iterdir() if p.is_dir()} if (ctx.drive / "packages").is_dir() else set()
    for path in sorted(folder.glob("*.md")):
        label = ctx.rel(path)
        text = read_text(path) or ""
        doc = Doc(text)
        if not OPENING_RE.search(text):
            f.fail(label, "must open with \"I'm working on <larger task> for <who>. They need <what the output enables>. With that in mind:\".")
        fields = doc.fields()
        for field in HANDOFF_FIELDS:
            if not fields.get(field):
                f.fail(label, "is missing '{}:'.".format(field))
        if fields.get("round") and not re.match(r"^\d+/\d+$", fields["round"]):
            f.fail(label, "round must be written n/K.")
        for section in HANDOFF_SECTIONS:
            if doc.section(section) is None:
                f.fail(label, "is missing '## {}'.".format(section))
        unit = path.stem
        known = keys | packages | {"final-audit"}
        # A later verification round keeps earlier rounds' handoffs by naming its own <unit>-r<n>.md.
        per_round = re.match(r"^(.+)-r(\d+)$", unit) if unit not in known else None
        if keys and unit not in known and not (per_round and per_round.group(1) in known):
            f.fail(label, "is named for '{}', which is neither a STATUS key nor a package id, nor one of those followed by "
                          "-r<n> for a later round.".format(unit))
        round_numbers = re.match(r"^(\d+)/\d+$", fields.get("round") or "")
        if per_round and round_numbers and int(per_round.group(2)) != int(round_numbers.group(1)):
            f.fail(label, "is named for round {} but its round: field is {}. Name a round's handoff <unit>-r<n>.md with n "
                          "the round's first number.".format(int(per_round.group(2)), fields["round"]))
        for number, line in doc.sections.get("Claims", []):
            if line.startswith("### ") and keys and line[4:].strip() not in keys:
                f.fail(label, "line {}: claim '{}' is not a STATUS key.".format(number, line[4:].strip()))
        if MAKER_LEAK_RE.search(strip_comments(text)):
            f.fail(label, "carries the maker's own account of its work. A handoff is built from files only.")


PACKAGE_SECTIONS = ["Goal", "Claim", "Inputs you rely on", "Contract", "Files you own", "Files you must not touch",
                    "Tests to make pass", "Commands you may run", "Lessons that apply to this task", "Done means",
                    "Budget", "Rules", "Report"]
PACKAGE_STATES = ["planned", "running", "complete", "partial", "blocked", "integrated", "verified", "failed"]
INDEX_COLUMNS = ["id", "wave", "claim key", "owns", "depends on", "hard", "status"]
SELF_CHECK_RE = re.compile(r"(?i)\b(double-check|self-verify|verify your own|review your own|spawn (a )?reviewer|check your work)\b")


def globs_under(text, heading):
    out, on = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            on = line.strip() == heading
        elif on:
            out.extend(re.findall(r"`([^`]+)`", line))
    return out


def glob_matches(path, pattern):
    pattern = pattern.rstrip("/")
    if fnmatch.fnmatchcase(path, pattern):
        return True
    if pattern.endswith("/**") and (path == pattern[:-3] or path.startswith(pattern[:-2])):
        return True
    return path == pattern or path.startswith(pattern + "/")


def globs_overlap(a, b):
    pa, pb = a.split("*")[0], b.split("*")[0]
    return pa.startswith(pb) or pb.startswith(pa)


def check_packages(ctx, f, gate=None):
    folder = ctx.drive / "packages"
    if not folder.is_dir():
        if gate == "decompose":
            f.fail(".drive/packages", "does not exist. Write packages/index.md and one brief per package.")
        return
    keys = set(ctx.status.by_key()) if ctx.status else set()
    owners = {}
    dirs = sorted(p for p in folder.iterdir() if p.is_dir())
    for pkg in dirs:
        brief_path = pkg / "brief.md"
        label = ctx.rel(brief_path)
        text = read_text(brief_path)
        if text is None:
            f.fail(label, "is missing; every package directory holds its brief.")
            continue
        doc = Doc(text)
        if doc.title != "Package {}".format(pkg.name):
            f.fail(label, "must start with '# Package {}'.".format(pkg.name))
        if not SLUG_RE.match(pkg.name):
            f.fail(label, "package ids are slugs of what they deliver, never numbers.")
        if not OPENING_RE.search(text):
            f.fail(label, "must open with \"I'm working on <larger task> for <who>. They need <what the output enables>. With that in mind:\".")
        for section in PACKAGE_SECTIONS:
            if doc.section(section) is None:
                f.fail(label, "is missing '## {}'.".format(section))
        if SELF_CHECK_RE.search(strip_comments(text)):
            f.fail(label, "tells the maker to check its own work or spawn reviewers. Verification is scheduled by the orchestrator; remove that instruction.")
        owned = globs_under(text, "## Files you own")
        if not owned:
            f.fail(label, "lists no backticked path or glob under '## Files you own'.")
        owners[pkg.name] = owned
        report_path = pkg / "report.json"
        if report_path.exists():
            data, error = load_json(report_path)
            rlabel = ctx.rel(report_path)
            if error:
                f.fail(rlabel, error + ".")
                continue
            schema = load_schema("package-report.schema.json")
            for problem in (schema_errors(data, schema) if schema else [])[:6]:
                f.fail(rlabel, problem + ".")
            if not isinstance(data, dict):
                continue
            if data.get("package") not in (None, pkg.name):
                f.fail(rlabel, "names package {} but lives under {}.".format(data.get("package"), pkg.name))
            if data.get("status") == "complete" and not data.get("gates_run"):
                f.fail(rlabel, "says complete with an empty gates_run; that counts as partial.")
            for changed in data.get("files") or []:
                if isinstance(changed, str) and owned and not any(glob_matches(changed, g) for g in owned):
                    f.fail(rlabel, "lists {} which is outside the package's owned paths. Revert it or move the change to wiring_needed.".format(changed))
    index_path = folder / "index.md"
    index = read_text(index_path)
    if index is None:
        if dirs:
            f.fail(ctx.rel(index_path), "is missing; the wave table lives there.")
        return
    doc = Doc(index)
    header, rows = parse_table(doc.header + [i for n in doc.section_order for i in doc.sections[n]])
    if header != INDEX_COLUMNS:
        f.fail(ctx.rel(index_path), "table columns must be id | wave | claim key | owns | depends on | hard | status.")
    else:
        ids = set()
        for number, cells in rows:
            cells = cells + [""] * (7 - len(cells))
            ids.add(cells[0])
            if cells[0] not in owners:
                f.fail(ctx.rel(index_path), "line {}: package {} has no brief directory.".format(number, cells[0]))
            if cells[6] not in PACKAGE_STATES:
                f.fail(ctx.rel(index_path), "line {}: status must be one of {}.".format(number, ", ".join(PACKAGE_STATES)))
            if keys and cells[2] not in ("-", "none", "") and cells[2] not in keys:
                f.fail(ctx.rel(index_path), "line {}: claim key {} is not in STATUS.md.".format(number, cells[2]))
        for name in owners:
            if name not in ids:
                f.fail(ctx.rel(index_path), "has no row for package {}.".format(name))
    if doc.section("Integrator-owned") is None:
        f.fail(ctx.rel(index_path), "is missing '## Integrator-owned'.")
    owners_all = dict(owners)
    owners_all["integrator"] = globs_under(index, "## Integrator-owned")
    names = sorted(owners_all)
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            for ga in owners_all[left]:
                for gb in owners_all[right]:
                    if globs_overlap(ga, gb):
                        f.fail(ctx.rel(index_path), "ownership overlaps: {} {} and {} {}. Split or merge the packages.".format(left, ga, right, gb))


CONSTRAINT_DIRECTIONS = {"must not fall", "must not grow"}
NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


def constraint_tables(text):
    """{section: {rule: {column: value}}} for the Enforced and Measured only tables."""
    doc = Doc(text)
    out = {}
    for section in ("Enforced", "Measured only", "Exceptions"):
        header, rows = parse_table(doc.sections.get(section, []))
        table = {}
        if header:
            for _, cells in rows:
                cells = cells + [""] * (len(header) - len(cells))
                table[cells[0]] = dict(zip(header, cells))
        out[section] = table
    out["floor"] = [l[2:].strip() for _, l in doc.bullets("Floor")]
    return out


def decision_keys(text):
    """DECISIONS.md entry keys as <YYYY-MM-DD>-<slug of the decision words>."""
    keys = set()
    for heading in Doc(text or "").section_order:
        match = re.match(r"^(\d{4}-\d{2}-\d{2}) · (.+)$", heading)
        if match:
            keys.add("{}-{}".format(match.group(1), slugify(match.group(2))))
    return keys


def decision_reference_ok(reference, keys):
    match = re.search(r"(\d{4}-\d{2}-\d{2}-[a-z0-9\-]+)", reference or "")
    if not match:
        return False
    ref = match.group(1).rstrip("-")
    return any(key == ref or key.startswith(ref) or ref.startswith(key) for key in keys)


def check_constraints(ctx, f):
    text = read_text(ctx.drive / "CONSTRAINTS.md")
    if text is None:
        return
    label = "CONSTRAINTS.md"
    tables = constraint_tables(text)
    if not tables["floor"]:
        f.fail(label, "has no '## Floor' rules.")
    for section in ("Enforced", "Measured only"):
        for rule, row in tables[section].items():
            if not row.get("command"):
                f.fail(label, "{} row '{}' names no command; a number with no command is an aspiration.".format(section, rule))
            if row.get("direction") not in CONSTRAINT_DIRECTIONS:
                f.fail(label, "{} row '{}' direction must be 'must not fall' or 'must not grow'.".format(section, rule))
            if not NUMBER_RE.search(row.get("measured", "")):
                f.fail(label, "{} row '{}' has no measured value.".format(section, rule))
    keys = decision_keys(read_text(ctx.drive / "DECISIONS.md"))
    for rule, row in tables["Exceptions"].items():
        for column in ("path", "reason", "undo", "decision"):
            if not row.get(column):
                f.fail(label, "exception '{}' is missing {}.".format(rule, column))
        if row.get("decision") and not decision_reference_ok(row["decision"], keys):
            f.fail(label, "exception '{}' names no DECISIONS.md entry that exists; an exception without a decision is unrecorded.".format(rule))


# ----------------------------------------------------------------------------------------------
# Gates, hygiene, and the final check

CLAIM_SECTIONS = ("Requirements", "Must not change", "Invariants", "Claims")


def claim_headings(ctx):
    """Claim headings from SPEC.md, MIGRATION.md, HUNT.md, and RESEARCH.md questions."""
    found = []
    for name in ("SPEC.md", "MIGRATION.md", "HUNT.md", "RESEARCH.md"):
        text = read_text(ctx.drive / name)
        if text is None:
            continue
        section, current, in_fence = "", None, False
        for number, line in enumerate(text.splitlines(), 1):
            if line.strip().startswith("```"):
                in_fence = not in_fence
            if in_fence:
                continue
            if line.startswith("## "):
                section, current = line[3:].strip(), None
                continue
            base = section.split("·", 1)[0].strip()
            if line.startswith("### "):
                heading = line[4:].strip()
                current = None
                if name == "RESEARCH.md" and base == "Questions":
                    match = re.match(r"^([a-z0-9][a-z0-9\-]*):\s*(.+)$", heading)
                    if match:
                        current = {"source": name, "heading": match.group(2), "line": number,
                                   "keys": {match.group(1)}, "question": True, "refutes": True, "lines": []}
                elif base in CLAIM_SECTIONS:
                    current = {"source": name, "heading": heading, "line": number, "keys": {slugify(heading)},
                               "question": False, "refutes": False, "lines": []}
                if current:
                    found.append(current)
                continue
            if current is None:
                continue
            current["lines"].append(line)
            former = re.match(r'^Formerly:\s*"(.+)"\s*$', line.strip())
            if former:
                current["keys"].add(slugify(former.group(1)))
    for item in found:
        if item["question"]:
            continue
        lines = [l.strip() for l in item["lines"]]
        if "What would prove this wrong" in lines:
            after = lines[lines.index("What would prove this wrong") + 1:]
            item["refutes"] = any(re.match(r"^\*\*.+\*\*$", l) for l in after)
    return found


def check_spec_gate(ctx, f):
    headings = claim_headings(ctx)
    if not headings:
        f.fail("SPEC.md", "no claim headings found in SPEC.md, MIGRATION.md, HUNT.md, or RESEARCH.md questions.")
        return
    rows = ctx.status.by_key() if ctx.status else {}
    seen = {}
    all_keys = set()
    for item in headings:
        label = "{} '{}'".format(item["source"], item["heading"][:60])
        all_keys |= item["keys"]
        primary = slugify(item["heading"]) if not item["question"] else next(iter(item["keys"]))
        if primary in seen:
            f.fail(label, "duplicates the heading on line {}; headings are unique.".format(seen[primary]))
        seen[primary] = item["line"]
        if not item["question"]:
            words = len(item["heading"].split())
            if words < 3 or words > 8:
                f.warn(label, "a claim heading has three to eight words.")
            if not item["refutes"]:
                f.fail(label, "has no 'What would prove this wrong' line followed by a scenario.")
        matching = [rows[k] for k in item["keys"] if k in rows]
        if not matching:
            f.fail(label, "has no STATUS row. Add one keyed {} with live fixed now.".format(primary))
        elif matching[0].live not in ("y", "n"):
            f.fail(label, "its STATUS row has no live value.")
    for key, row in rows.items():
        if row.status != DROPPED and key not in all_keys:
            f.fail("STATUS {}".format(key), "maps to no claim heading in SPEC.md, MIGRATION.md, HUNT.md, or RESEARCH.md.")


def check_hunt_gate(ctx, f, phase):
    text = read_text(ctx.drive / "HUNT.md")
    if text is None:
        f.fail("HUNT.md", "is missing; a fix keeps its hunt there.")
        return
    doc = Doc(text)
    if phase == "reproduce":
        header_line = next((l for _, l in doc.header if "pre-fix commit:" in l), "")
        match = re.search(r"pre-fix commit:\s*([0-9a-f]{7,40})", header_line)
        if not match or not commit_exists(ctx.root, match.group(1)):
            f.fail("HUNT.md", "the header must record an existing pre-fix commit.")
        command = field_value(doc.sections.get("Reproduction", []), "Command")
        exit_match = re.search(r"exit (\d+)", command or "")
        if not command or "`" not in command or not exit_match or exit_match.group(1) == "0" or PLACEHOLDER_RE.search(command):
            f.fail("HUNT.md", "Reproduction needs 'Command: `<repro>` · exit <non-zero>' recorded from a real run.")
    if phase == "diagnose":
        header, rows = parse_table(doc.sections.get("Hypothesis ledger", []))
        if not header or "status" not in header:
            f.fail("HUNT.md", "the hypothesis ledger table is missing.")
            return
        column = header.index("status")
        if not any(len(cells) > column and cells[column].strip().lower() == "confirmed" for _, cells in rows):
            f.fail("HUNT.md", "no hypothesis is confirmed. Diagnose ends with one confirmed row.")


def field_value(lines, name):
    for _, line in lines:
        match = re.match(r"^{}:\s*(.*)$".format(re.escape(name)), line.strip())
        if match:
            return match.group(1).strip()
    return None


def active_rows(ctx):
    """Rows a gate checks: every row that is not Dropped, or with --sub only the rows carrying sub:<slug>. A row without
    a sub: token belongs to the single goal."""
    rows = [r for r in (ctx.status.rows if ctx.status else []) if r.status != DROPPED]
    if getattr(ctx, "sub", None):
        rows = [r for r in rows if ctx.sub in r.values("sub")]
    return rows


def require_rung(ctx, f, rung, only_live=False):
    for row in active_rows(ctx):
        if only_live and row.live != "y":
            continue
        target = rung
        if only_live and any(w.startswith("device-only:") for w in row.values("why")):
            target = "Local Proof"
        if row.rung < LADDER.index(target):
            f.fail("STATUS {}".format(row.key), "is {}; this gate needs {} or above.".format(row.status, target))


def overrun_recorded(ctx):
    """A DECISIONS.md entry that records the budget overrun and names on its Narrows: line what was cut."""
    _, entries = decision_entries(read_text(ctx.drive / "DECISIONS.md") or "")
    for heading, lines in entries:
        body = heading + "\n" + "\n".join(l for _, l in lines)
        narrows = next((l.split(":", 1)[1].strip() for _, l in lines if l.strip().startswith("- Narrows:")), "")
        if re.search(r"(?i)budget|overrun|envelope", body) and narrows and narrows.lower().rstrip(".") != "none":
            return True
    return False


def spawn_budget_check(ctx, f):
    """GOAL.md's subagent budget counts maker spawns (implementer, writer, designer, architect, researcher): reviews are
    the ceremony a size requires and never the reason to cut work. Warn past the budget; fail past twice it until
    DECISIONS.md records the overrun with a Narrows: line naming what was cut."""
    allowed, makers, reviewers = maker_spawn_counts(ctx.root, ctx.goal)
    if allowed is None:
        return
    if makers > 2 * allowed and not overrun_recorded(ctx):
        f.fail("GOAL.md budget", "{} maker subagents have started against a budget of {} (reviewers, {} so far, are not counted); "
               "the run is past twice its envelope. Record the overrun in DECISIONS.md with a Narrows: line naming what "
               "was cut, then continue with the narrower plan or stop.".format(makers, allowed, reviewers))
    elif makers > allowed:
        f.warn("GOAL.md budget", "{} maker subagents have started against a budget of {} (reviewers, {} so far, are not "
               "counted). Log the overrun and narrow before spawning more.".format(makers, allowed, reviewers))


def maker_spawn_counts(root, goal):
    """(GOAL.md's subagent budget figure or None, maker spawns, reviewer spawns) since the run marker's start."""
    budget = goal.fields.get("budget", "") if goal else ""
    match = re.search(r"(\d+)\s*subagents?", budget)
    started = parse_iso(str(read_marker(root).get("started", "")))
    since = started.timestamp() if started else 0
    spawns = [e for e in ledger_entries(root, "spawn") if float(e.get("ts") or 0) >= since]
    makers = sum(1 for e in spawns if role_of(e.get("agent_type")) in MAKER_ROLES)
    return (int(match.group(1)) if match else None), makers, len(spawns) - makers


def check_gate(ctx, f, phase, sub=None):
    size = ctx.goal.size if ctx.goal else None
    if sub:
        cls = ctx.goal.sub_classification(sub) if ctx.goal else None
        if cls is None:
            f.fail("GOAL.md", "has no '## Classification · {}' section for --sub {}.".format(sub, sub))
        elif cls.get("size") in SIZES:
            size = cls.get("size")
    big = size in ("M", "L", "XL")
    spawn_budget_check(ctx, f)
    if phase == "intake":
        if big and not (ctx.drive / "capabilities.json").exists():
            f.fail("capabilities.json", "is missing. Run drive.py capabilities at intake for M and above.")
        if big and not (ctx.drive / "CONSTRAINTS.md").exists():
            f.warn("CONSTRAINTS.md", "is missing; record the measured quality floor before the build.")
    elif phase == "archaeology":
        text = read_text(ctx.drive / "how-it-works.md")
        if text is None:
            f.fail("how-it-works.md", "is missing; archaeology writes it.")
        else:
            if text.count("\n") + 1 > 150:
                f.fail("how-it-works.md", "is over 150 lines.")
            if not re.search(r"^\|", text, re.M):
                f.fail("how-it-works.md", "has no drift table.")
    elif phase == "research":
        if not (ctx.drive / "RESEARCH.md").exists():
            f.fail("RESEARCH.md", "is missing.")
    elif phase == "spec":
        check_spec_gate(ctx, f)
    elif phase == "design":
        if not (ctx.drive / "DESIGN.md").exists() and not (ctx.root / "design" / "DESIGN.md").exists():
            f.fail("DESIGN.md", "is missing.")
    elif phase == "test-plan":
        if not (ctx.drive / "TESTPLAN.md").exists():
            f.fail("TESTPLAN.md", "is missing.")
        for row in active_rows(ctx):
            if not (row.values("test") or row.values("severe") or row.values("planned")):
                f.fail("STATUS {}".format(row.key), "has no test:, severe:, or planned: token.")
    elif phase == "decompose":
        check_packages(ctx, f, gate="decompose")
    elif phase in ("build", "fix", "draft", "execute"):
        require_rung(ctx, f, "Partial")
        if big and not (ctx.drive / "CONSTRAINTS.md").exists():
            f.fail("CONSTRAINTS.md", "is missing; M and above record the quality floor before building.")
    elif phase in ("verify", "harden", "design-qa"):
        require_rung(ctx, f, "Local Proof")
        reviews = ctx.drive / "reviews"
        if phase == "harden" and not (reviews.is_dir() and any(reviews.iterdir())):
            f.fail(".drive/reviews", "holds no review; hardening records its reviews there.")
    elif phase == "integrate":
        require_rung(ctx, f, "Local Proof")
        check_hygiene(ctx, f)
    elif phase in ("live-proof", "deploy", "cutover"):
        require_rung(ctx, f, "Live Proof", only_live=True)
    elif phase == "retro":
        if not retro_files(ctx):
            f.fail(".drive/reviews", "has no <date>-retro.md.")
        check_investigations(ctx, f, "final")
    elif phase == "report":
        check_report(ctx, f)
    elif phase in ("reproduce", "diagnose"):
        check_hunt_gate(ctx, f, phase)
    elif phase == "content-plan":
        folder = ctx.drive / "content-plan"
        if not folder.is_dir() or not any(folder.iterdir()):
            f.fail(".drive/content-plan", "is missing or empty.")
    elif phase in ("inventory", "characterize"):
        if not (ctx.drive / "MIGRATION.md").exists():
            f.fail("MIGRATION.md", "is missing.")


def porcelain_paths(root):
    code, out, err = git(root, "status", "--porcelain=v1", "--untracked-files=all", "-z")
    if code != 0:
        return None
    records = out.split("\0")
    paths, index = [], 0
    while index < len(records):
        record = records[index]
        index += 1
        if len(record) < 4:
            continue
        status, path = record[:2], record[3:]
        paths.append((status, path))
        if "R" in status or "C" in status:
            index += 1
    return paths


def worktree_entries(root):
    out = git_out(root, "worktree", "list", "--porcelain") or ""
    entries, current = [], {}
    for line in out.splitlines() + [""]:
        if not line.strip():
            if current:
                entries.append(current)
            current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    return entries


def listing(items, limit=8):
    return "{}{}".format(", ".join(items[:limit]), " and {} more".format(len(items) - limit) if len(items) > limit else "")


def check_hygiene(ctx, f):
    """Fail on repository state the run created: uncommitted paths, worktrees, and run branches that
    were not there when `drive.py init` recorded the owner's baseline. The owner's own work is never
    the run's to commit or remove."""
    if not ctx.git:
        f.fail("repository", "is not a git repository.")
        return
    baseline = read_baseline(ctx.root)
    paths = porcelain_paths(ctx.root)
    dirty = [p for s, p in (paths or []) if not p.startswith(".drive/local/")]
    if baseline is None:
        if dirty:
            f.fail("repository", "has uncommitted changes: {}. No baseline was recorded at init, so drive cannot tell the owner's "
                   "changes from the run's; commit or revert only what this run changed, and record a baseline by re-running "
                   "drive.py init for a new run.".format(listing(dirty)))
    else:
        owned = set(baseline.get("dirty") or [])
        prefixes = [d for d in baseline.get("untracked_dirs") or [] if d]
        new = [p for p in dirty if p not in owned and not any(p.startswith(d) for d in prefixes)]
        if new:
            f.fail("repository", "has uncommitted changes made during the run: {}. Commit them to main or revert them; "
                   "paths that were already uncommitted when the run started are the owner's and stay as they are.".format(listing(new)))
    if (ctx.drive / "local").exists() and git(ctx.root, "check-ignore", "-q", ".drive/local/active")[0] != 0:
        f.fail(".gitignore", "does not ignore .drive/local/. Add the line .drive/local/.")
    entries = worktree_entries(ctx.root)
    known = set(baseline.get("worktrees") or []) if baseline else set()
    extra = [e.get("worktree", "?") for e in entries[1:] if os.path.realpath(e.get("worktree", "")) not in known]
    if extra:
        harness = [w for w in extra if "/.claude/worktrees/" in w.replace("\\", "/") + "/"]
        hint = (" A background session moved into {}: relaunch with the per-run settings that set worktree.bgIsolation to none "
                "(drive.py preflight checks this).".format(", ".join(harness))) if harness else ""
        removals = "; ".join("git worktree remove {}".format(shlex.quote(w)) for w in extra[:8])
        f.fail("repository", "has worktree(s) created during the run: {}. Land an arm with drive.py worktree-land <path> <sha>, or "
               "remove it now with: {}. No worktree this run creates survives its step.{}".format(listing(extra), removals, hint))
    before = set(baseline.get("branches") or []) if baseline else set()
    unmerged = (" If git refuses because the commits were landed by cherry-pick rather than merged, name 'git branch -D <branch>' "
                "in REPORT.md's \"Needed from you\"; the guard never lets the run force-delete a branch.")
    if baseline is not None:
        created = [b for b in local_branches(ctx.root) if b not in before]
    else:
        listed = git_out(ctx.root, "branch", "--list", *(LEFTOVER_BRANCH_PATTERNS + HARNESS_BRANCH_PATTERNS)) or ""
        created = [b.strip(" *+") for b in listed.splitlines() if b.strip()]
    if created:
        f.fail("repository", "has local branch(es) that .drive/local/baseline.json does not list: {}. A run never creates a "
               "branch; land any commits on the branch the run started on and delete them with: {}. A branch a background "
               "session or another tool created fails here too, because nothing may be left for the owner to "
               "clean up.{}".format(listing(created), "; ".join("git branch -d " + b for b in created[:8]), unmerged))
    updated = parse_iso(ctx.state.fields.get("updated", "")) if ctx.state else None
    workers = ctx.drive / "local" / "workers"
    if updated and workers.is_dir():
        for report in workers.glob("*/report.md"):
            if report.stat().st_mtime > updated.timestamp():
                f.fail(ctx.rel(report), "is newer than STATE.md; merge the worker's report into the state files.")


REPORT_SECTIONS = ["Outcome", "Needed from you", "What to look at first", "Ladder", "What shipped",
                   "Proven live and proven locally", "Not done", "Decisions taken on your behalf",
                   "Open failures", "Lessons", "Verify from a clean checkout", "Paused run", "Spend"]


def check_report(ctx, f):
    text = read_text(ctx.drive / "REPORT.md")
    if text is None:
        f.fail("REPORT.md", "is missing. Write it from templates/REPORT.md, derived from the files.")
        return
    doc = Doc(text)
    for section in REPORT_SECTIONS:
        if doc.section(section) is None:
            f.fail("REPORT.md", "is missing '## {}'.".format(section))
    if doc.section_order[:2] != ["Outcome", "Needed from you"]:
        f.fail("REPORT.md", "must open with '## Outcome' and then '## Needed from you', for a reader who saw none of the work.")
    header, rows = parse_table(doc.sections.get("Ladder", []))
    counts = {r: 0 for r in LADDER + [DROPPED]}
    for row in (ctx.status.rows if ctx.status else []):
        if row.status in counts:
            counts[row.status] += 1
    reported = {}
    for _, cells in rows:
        if cells and cells[0] in counts and len(cells) > 1 and re.match(r"^\d+$", cells[1]):
            reported[cells[0]] = int(cells[1])
    for rung, count in counts.items():
        if reported.get(rung) != count:
            f.fail("REPORT.md", "the Ladder table says {} {} but STATUS.md has {}.".format(reported.get(rung, "nothing for"), rung, count))
    runs = ctx.drive / "runs"
    if runs.is_dir():
        for paused in runs.iterdir():
            if paused.is_dir() and paused.name not in text:
                f.fail("REPORT.md", "does not name the paused run {}.".format(paused.name))


def final_audit_problems(ctx):
    reviews = ctx.drive / "reviews"
    audits = sorted(reviews.glob("*-final-audit.json")) if reviews.is_dir() else []
    if not audits:
        return ["no .drive/reviews/<date>-final-audit.json exists"]
    path = audits[-1]
    data, error = load_json(path)
    if error or not isinstance(data, dict):
        return ["{} {}".format(ctx.rel(path), error or "is not an object")]
    problems = []
    schema = load_schema("verdict.schema.json")
    if schema:
        problems.extend("{} {}".format(ctx.rel(path), e) for e in schema_errors(data, schema)[:4])
    if data.get("verdict") != "pass":
        problems.append("{} is not a go (verdict {})".format(ctx.rel(path), data.get("verdict")))
    provenance = ctx.provenance(path, "final-audit")
    if provenance:
        problems.append(provenance)
    latest = latest_code_commit(ctx)
    if latest:
        audit_commit = git_out(ctx.root, "log", "-1", "--format=%H", "--", str(path.relative_to(ctx.root)))
        if audit_commit:
            if not is_ancestor(ctx, latest[0], audit_commit):
                problems.append("{} predates the latest code commit {}".format(ctx.rel(path), latest[0][:7]))
        elif path.stat().st_mtime < latest[1]:
            problems.append("{} predates the latest code commit {}".format(ctx.rel(path), latest[0][:7]))
    return problems


def row_has_reason(ctx, row):
    """A row below Done in a stopped run carries its reason somewhere a reader will find it."""
    if row.values("why"):
        return True
    if ctx.state:
        if any(row.key in line for _, line in ctx.state.doc.bullets("Open failures")):
            return True
        if row.key in ctx.state.resume.get("blocked on", ""):
            return True
    decisions = read_text(ctx.drive / "DECISIONS.md") or ""
    return any(row.key in line for line in decisions.splitlines() if line.strip().startswith("- Narrows:"))


def check_final(ctx, f):
    status = ctx.state.status if ctx.state else ""
    if status not in ("done", "stopped"):
        f.fail("STATE.md", "status is {}; the final check applies to a run marked done or stopped.".format(status or "missing"))
    rows = ctx.status.rows if ctx.status else []
    registry = ctx.state.fields.get("registry") if ctx.state else None
    if not registry:
        if not rows:
            f.fail("STATUS.md", "has no rows; a finished run has at least one claim.")
        for row in rows:
            if row.status in ("Done", DROPPED):
                continue
            if status == "stopped":
                if not row_has_reason(ctx, row):
                    f.fail("STATUS {}".format(row.key), "is {} in a stopped run with no recorded reason. Add a why: token, an Open failure or Blocked on line naming the key, or a DECISIONS.md narrowing.".format(row.status))
            else:
                f.fail("STATUS {}".format(row.key), "is {}; every row of a done run ends Done or Dropped. If the run stopped short, set status: stopped and record each reason.".format(row.status))
        done = [r for r in rows if r.status == "Done"]
        # A stopped run whose rows reached anything above Missing is audited like a done run, so its report cannot pass
        # a plan off as a result; with no rows, or every row still Missing, there is nothing to audit.
        stopped_with_work = status == "stopped" and any(r.rung > 0 for r in rows)
        if done or stopped_with_work:
            why = "" if done else " (a stopped run with any row above Missing is audited like a done run)"
            for problem in final_audit_problems(ctx):
                f.fail("final audit", problem + why + ".")
            for row in done:
                if not any("final-audit" in v for v in row.values("review")):
                    f.fail("STATUS {}".format(row.key), "is Done but its review: does not point at the final audit.")
    check_report(ctx, f)
    if status == "stopped":
        report = Doc(read_text(ctx.drive / "REPORT.md") or "")
        opening = next((l.strip() for _, l in report.sections.get("Outcome", []) if l.strip() and not l.strip().startswith("<!--")), "")
        if not opening.startswith("Stopped because"):
            f.fail("REPORT.md", "a stopped run's Outcome opens with 'Stopped because'.")
    if not retro_files(ctx):
        f.fail(".drive/reviews", "has no <date>-retro.md; the run is not finished until the retro is committed.")
    if ctx.state and ctx.state.doc.bullets("Open failures") and status == "done":
        f.warn("STATE.md", "still lists open failures; the report must name each with the step that would close it.")
    for problem in scheduled_deletion_problems(ctx):
        f.fail("REPORT.md", problem)


SCHEDULED_DELETE_RE = re.compile(r"(?i)\bschedul\w*\b[^\n]{0,160}\b(delet|drop|destroy|purg|wip)\w*|"
                                 r"\b(delet|drop|destroy|purg|wip)\w*\b[^\n]{0,160}\bschedul\w*")
DELETE_WORD_RE = re.compile(r"(?i)\b(delet|drop|destroy|purg|wip)\w*")


def scheduled_deletion_problems(ctx):
    """A finished run that leaves a scheduled deletion behind. drive.py end removes the marker and every hook goes inert,
    so the deletion must be the owner's step in REPORT.md, or the run stays open (Blocked on: soak:) until it ran."""
    found = []
    for name in ("DECISIONS.md", "STATE.md", "MIGRATION.md"):
        body = strip_comments(read_text(ctx.drive / name) or "")
        for number, line in enumerate(body.splitlines(), 1):
            if SCHEDULED_DELETE_RE.search(line):
                found.append("{} line {}".format(name, number))
    if not found:
        return []
    report = Doc(read_text(ctx.drive / "REPORT.md") or "")
    needed = strip_comments("\n".join(l for _, l in report.sections.get("Needed from you", [])))
    if DELETE_WORD_RE.search(needed):
        return []
    return ["{} record{} a scheduled deletion. drive.py end removes .drive/local/active and every drive hook goes inert, so a "
            "scheduled prompt that deletes data would run with no guard and no reviewer. Keep the run open with 'Blocked on: "
            "soak: <window>' until the deletion check has run, or name the deletion under 'Needed from you' as the owner's "
            "step, with the export and restore commands already verified.".format(", ".join(found[:4]), "s" if len(found) == 1 else "")]


def code_tree_clean(ctx):
    return not [p for _, p in (porcelain_paths(ctx.root) or []) if not p.startswith(".drive/")]


def recorded_pass(ctx, kind, command):
    """A ledger record that `command` exited 0 against the current latest code commit."""
    sha = current_code_sha(ctx.root)
    return any(e.get("command") == command and e.get("exit") == 0 and e.get("code_sha") == sha
               for e in ledger_entries(ctx.root, kind))


def run_and_record(ctx, f, kind, label, command, timeout):
    started = time.time()
    code, out, err = run(["/bin/sh", "-c", command], cwd=ctx.root, timeout=timeout)
    tail = " | ".join((out + err).strip().splitlines()[-3:])
    if code != 0:
        f.fail(label, "'{}' exited {} when drive.py ran it{}: {}".format(
            command, code, " (its {}s timeout)".format(timeout) if code == 124 else "", tail))
    if code_tree_clean(ctx):
        ledger_append(ctx.root, {"kind": kind, "command": command, "exit": code, "code_sha": current_code_sha(ctx.root),
                                 "seconds": round(time.time() - started, 1)})


def check_suite(ctx, f):
    """At --final, run the full-suite command GOAL.md records, once, and fail on a non-zero exit. The
    Stop hook cannot wait for a suite, so there it accepts only a passing run already recorded for the
    latest code commit. Shapes with no test suite (report, operate) are exempt."""
    if ctx.goal is None:
        return
    shapes = ctx.goal.shapes
    if shapes and shapes <= NO_SUITE_SHAPES:
        return
    command = ctx.test_command
    if not command or command.lower() == "none":
        f.fail("GOAL.md", "records no full-suite command (probe.test_command), so the final check cannot run it. A {} run "
               "records the exact command at intake.".format("/".join(sorted(shapes)) or "code"))
        return
    intake = ctx.intake_commit()
    old_text = show_at(ctx.root, intake, ".drive/GOAL.md") if intake else None
    if old_text is not None:
        old = Goal(old_text)
        old_ctx_probe = old.probe()
        before = next((str(old_ctx_probe.get(k)).strip() for k in ("full_suite", "full_suite_command", "test_command", "tests")
                       if isinstance(old_ctx_probe.get(k), str) and old_ctx_probe.get(k).strip()), None)
        if before and before != command and command not in (read_text(ctx.drive / "DECISIONS.md") or ""):
            f.fail("GOAL.md", "the full-suite command changed from '{}' at intake to '{}' without a DECISIONS.md entry naming "
                   "the new command.".format(before, command))
    if ctx.run_commands:
        run_and_record(ctx, f, "suite", "full suite", command, ctx.suite_timeout)
    elif not recorded_pass(ctx, "suite", command):
        f.fail("full suite", "no passing run of '{}' is recorded for the latest code commit {}. Run drive.py lint --final, "
               "which runs the suite once and records the result.".format(command, (current_code_sha(ctx.root) or "none")[:7]))


def run_registry(ctx, f):
    command = ctx.state.fields.get("registry") if ctx.state else None
    if not command:
        return
    if ctx.run_commands:
        run_and_record(ctx, f, "registry", "registry", command, 600)
    elif not recorded_pass(ctx, "registry", command):
        f.fail("registry", "no passing run of '{}' is recorded for the latest code commit; run drive.py lint --final or "
               "--gate, which runs it and records the result.".format(command))


def default_guard_base(root):
    """The run's baseline: GOAL.md's probe baseline_sha when it names a commit, else HEAD. Comparing with HEAD
    alone would miss every loosening already committed."""
    text = read_text(Path(root) / ".drive" / "GOAL.md")
    if text:
        sha = str(Goal(text).probe().get("baseline_sha") or "").strip()
        if sha and commit_exists(root, sha):
            return sha
    return "HEAD"


def check_frozen(ctx, f):
    """The freeze manifest against the tree and the provenance ledger, whenever the run has frozen tests."""
    if not (ctx.root / FROZEN_LIST).is_file() and not (ctx.root / FROZEN_MANIFEST).is_file():
        return
    for problem in freeze_problems(ctx.root):
        f.fail("frozen", problem + ".")


def check_floor(ctx, f):
    """The constraints floor against the run's baseline, at the integrate and harden gates and at --final."""
    if not ctx.head:
        return
    base = default_guard_base(ctx.root)
    violations, error = run_floor_guard(ctx.root, base)
    if error:
        f.fail("guard", "could not run against {}: {}.".format(base, error))
        return
    for rule, where, message in violations:
        f.fail("guard", "{} · {} · {} since the baseline {}. Fix the code, or record a genuine exception in CONSTRAINTS.md with its "
               "DECISIONS.md entry.".format(rule, where, message, base[:7]))


def run_lint(root, mode="base", gate=None, run_commands=True, sub=None, suite_timeout=SUITE_TIMEOUT):
    ctx = Ctx(root)
    ctx.run_commands = run_commands
    ctx.suite_timeout = suite_timeout
    ctx.sub = sub
    f = Findings()
    if not ctx.drive.is_dir():
        f.fail(".drive", "does not exist in {}.".format(ctx.root))
        return ctx, f
    check_goal(ctx, f, mode)
    check_state(ctx, f, mode)
    check_status(ctx, f, mode)
    check_decisions(ctx, f)
    check_project_lessons(ctx, f)
    check_investigations(ctx, f, mode)
    check_retros(ctx, f)
    check_handoffs(ctx, f)
    check_packages(ctx, f)
    check_constraints(ctx, f)
    check_secrets(ctx, f)
    check_placeholders(ctx, f)
    check_frozen(ctx, f)
    if mode in ("stop", "final"):
        check_hygiene(ctx, f)
    if mode == "final":
        check_final(ctx, f)
        check_floor(ctx, f)
        check_suite(ctx, f)
        run_registry(ctx, f)
    if gate:
        check_gate(ctx, f, gate, sub)
        if gate in ("integrate", "harden"):
            check_floor(ctx, f)
        run_registry(ctx, f)
    return ctx, f


def cmd_lint(args):
    if args.gate and args.gate not in PHASES:
        print("Unknown phase '{}'. Use one of: {}.".format(args.gate, ", ".join(PHASES)), file=sys.stderr)
        return 2
    if args.sub and not args.gate:
        print("--sub scopes a gate; pass it with --gate <phase>.", file=sys.stderr)
        return 2
    mode = "final" if args.final else "stop" if args.stop else "base"
    root = find_root(args.root or os.getcwd())
    _, f = run_lint(root, mode, args.gate, sub=args.sub, suite_timeout=args.suite_timeout)
    if args.json:
        print(json.dumps({"ok": not f.failed, "mode": mode, "gate": args.gate, "root": str(root), "findings": f.items}, indent=2))
    else:
        for line in f.lines():
            print(line)
        failures = sum(1 for i in f.items if i["level"] == "fail")
        print("drive lint{}: {}".format(" --gate " + args.gate if args.gate else "" if mode == "base" else " --" + mode,
                                         "ok" if not f.failed else "{} failure(s)".format(failures)))
    return 1 if f.failed else 0


# ----------------------------------------------------------------------------------------------
# start, init, end


def start_view(root):
    root = Path(root)
    drive = root / ".drive"
    if not drive.is_dir():
        return "No drive run in {}.".format(root)
    ctx, f = run_lint(root, "stop")
    out = ["DRIVE · START · {}".format(root)]
    if ctx.state:
        out.append("")
        out.extend(line for _, line in ctx.state.doc.header if line.strip())
        out.append("")
        out.append("Resume here")
        out.extend(line for _, line in ctx.state.doc.sections.get("Resume here", []) if line.strip())
        counter = stop_counter(root)[1]
        consecutive, cap = int(counter.get("consecutive", 0) or 0), int(counter.get("cap", 0) or 0)
        if ctx.state.status in GATE_CLOSED and cap and consecutive >= cap:
            out.append("")
            out.append("Warning: the last turn ended while the Stop gate was still blocking ({} consecutive blocked stops, "
                       "CLAUDE_CODE_STOP_HOOK_BLOCK_CAP {}). Claude Code's block cap ended that turn, not the run; "
                       ".drive/local/gate.log has the blocks. Continue from next:.".format(consecutive, cap))
    else:
        out.append("STATE.md is missing.")
    if ctx.status:
        counts = {r: 0 for r in LADDER + [DROPPED]}
        for row in ctx.status.rows:
            if row.status in counts:
                counts[row.status] += 1
        out.append("")
        out.append("Rungs: " + " · ".join("{} {}".format(r, n) for r, n in counts.items()))
        open_rows = [r for r in ctx.status.rows if r.status not in ("Done", DROPPED)]
        out.append("Open rows ({}):".format(len(open_rows)))
        out.extend("- {} · {} · live {} · {}".format(r.key, r.status, r.live, r.claim) for r in open_rows[:40])
        if len(open_rows) > 40:
            out.append("- and {} more; grep STATUS.md".format(len(open_rows) - 40))
    if ctx.state:
        failures = ctx.state.doc.bullets("Open failures")
        out.append("Open failures ({}):".format(len(failures)))
        out.extend(line for _, line in failures)
        header, rows = ctx.state.ledger()
        repeated = [cells for _, cells in rows if len(cells) > 4 and re.match(r"^\d+$", cells[4]) and int(cells[4]) >= 2]
        out.append("Workarounds used twice or more ({}):".format(len(repeated)))
        out.extend("- {} · {} · count {}".format(c[0], c[1], c[4]) for c in repeated)
    fails = [i for i in f.items if i["level"] == "fail"]
    warns = [i for i in f.items if i["level"] == "warn"]
    out.append("Lint (stop checks): {} failure(s), {} warning(s)".format(len(fails), len(warns)))
    out.extend("- " + line for line in f.lines()[:20])
    if len(f.items) > 20:
        out.append("- and {} more; run drive.py lint --stop".format(len(f.items) - 20))
    return "\n".join(out)


def cmd_start(args):
    try:
        # Printing the view registers nothing: an XS /drive in a repository that holds another run's marker must not
        # become that run's session. drive.py init (a new run, or a resume) registers the session.
        root = find_root(args.root or os.getcwd())
        print(start_view(root))
    except Exception as exc:  # the start view must never fail a session
        print("drive start could not read the run: {}".format(exc))
    return 0


GITIGNORE_LINES = [
    ".drive/local/",
    ".drive/proofs/*/r*/shots/**/*.png",
    "!.drive/proofs/*/r*/shots/**/*.review.png",
    "!.drive/proofs/*/r*/shots/**/*.crop-*.png",
]
SIZE_FILES = {
    "S": ["GOAL.md", "STATE.md", "STATUS.md"],
    "M": ["GOAL.md", "STATE.md", "STATUS.md", "DECISIONS.md", "LESSONS.md", "CONSTRAINTS.md"],
}
SIZE_DIRS = ["proofs", "reviews", "investigations", "handoffs", "packages"]


def fill_template(name, values):
    text = read_text(TEMPLATES / name)
    if text is None:
        raise SystemExit("drive init: templates/{} is missing from the skill.".format(name))
    for placeholder, value in values.items():
        text = text.replace(placeholder, value)
    return text


def gate_log(root, line):
    local = Path(root) / ".drive" / "local"
    try:
        local.mkdir(parents=True, exist_ok=True)
        with open(local / "gate.log", "a", encoding="utf-8") as handle:
            handle.write("{} · {}\n".format(iso_now(), line.replace("\n", " ")))
    except OSError:
        pass


def ensure_gitignore(root):
    path = Path(root) / ".gitignore"
    existing = read_text(path) or ""
    lines = existing.splitlines()
    missing = [l for l in GITIGNORE_LINES if l not in lines]
    if missing:
        with open(path, "a", encoding="utf-8") as handle:
            if existing and not existing.endswith("\n"):
                handle.write("\n")
            handle.write("\n".join(missing) + "\n")
    return missing


def goal_text_of(goal):
    """GOAL.md's goal line as the owner wrote it: init writes it as a JSON string, so quotes and backslashes round-trip."""
    raw = goal.fields.get("goal", "").strip()
    if raw.startswith('"'):
        try:
            value = json.loads(raw)
            if isinstance(value, str):
                return value
        except ValueError:
            pass
    return raw.strip('"')


def same_goal(old_goal, new_text, new_slug):
    """A resume when the goal text GOAL.md recorded at init matches the new goal, ignoring case and runs of whitespace.
    The slug is cut at 50 characters, so two goals sharing their opening would match on it; it decides only for an older
    GOAL.md that records no goal text."""
    if old_goal is None:
        return True
    old_text = goal_text_of(old_goal)
    norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()  # noqa: E731
    if norm(old_text) not in ("", "<verbatim prompt>"):
        return norm(old_text) == norm(new_text)
    return old_goal.slug == new_slug


def archive_run(root, old_goal):
    """Move the tracked state of a run for a different goal to .drive/runs/<date>-<slug>/."""
    drive = Path(root) / ".drive"
    runs = drive / "runs"
    slug = old_goal.slug or "previous-run"
    date = now_utc().strftime("%Y-%m-%d")
    dest = runs / "{}-{}".format(date, slug)
    suffix = 2
    while dest.exists():
        dest = runs / "{}-{}-{}".format(date, slug, suffix)
        suffix += 1
    evidence = (drive / "GOAL.md").is_file() and bool(old_goal.slug)
    ok, reason = derived_path_ok(dest, [runs], evidence)
    if not ok:
        gate_log(root, "INIT REFUSED archive {}".format(reason))
        raise SystemExit("drive init refused to archive: {}".format(reason))
    dest.mkdir(parents=True)
    moved = []
    for entry in sorted(drive.iterdir()):
        if entry.name in ("local", "runs"):
            continue
        entry.rename(dest / entry.name)
        moved.append(entry.name)
    local = drive / "local"
    if local.is_dir():
        parked = local / "archive" / dest.name
        parked.mkdir(parents=True, exist_ok=True)
        for entry in sorted(local.iterdir()):
            if entry.name != "archive":
                entry.rename(parked / entry.name)
    rel = dest.relative_to(root)
    (dest / "RESTORE.md").write_text(
        "# Paused run · {}\n"
        "archived: {}\n"
        "status when paused: {}\n\n"
        "To restore: run `drive.py init --goal` for this goal's text again after archiving the current run the same way, "
        "or by hand: move every file from {} back into .drive/ and move .drive/local/archive/{}/ back into .drive/local/, "
        "then commit.\n".format(slug, iso_now(), "unknown" if not old_goal else "see STATE.md here", rel, dest.name),
        encoding="utf-8")
    return dest, moved


def read_goal_argument(args):
    """The goal from --goal, from --goal-file, or from stdin with --goal -. Returns (text, error)."""
    if args.goal_file:
        text = read_text(Path(args.goal_file))
        if text is None:
            return None, "--goal-file {} cannot be read".format(args.goal_file)
        return text.strip(), None
    if args.goal == "-":
        try:
            return sys.stdin.read().strip(), None
        except (OSError, ValueError):
            return None, "--goal - could not read stdin"
    if args.goal is None:
        return None, "pass the goal with --goal, --goal-file <path>, or --goal - on stdin"
    return args.goal.strip(), None


def cmd_init(args):
    root = find_root(args.root or os.getcwd())
    if (root / ".drive").is_dir() is False and not is_git_repo(root):
        print("drive init: {} is not a git repository.".format(root), file=sys.stderr)
        return 1
    goal_text, error = read_goal_argument(args)
    if error or not goal_text:
        print("drive init: {}.".format(error or "the goal is empty"), file=sys.stderr)
        return 2
    slug = args.slug or slugify(goal_text, 50) or "goal"
    if not SLUG_RE.match(slug):
        print("drive init: --slug must be lowercase words joined by hyphens.", file=sys.stderr)
        return 1
    drive = root / ".drive"
    existing = read_text(drive / "GOAL.md")
    old_goal = Goal(existing) if existing is not None else None
    session_id = os.environ.get("CLAUDE_CODE_SESSION_ID")
    archived = None
    if old_goal is not None and same_goal(old_goal, goal_text, slug):
        # A resume: re-create the marker (missing after a fresh clone, a cloud hand-off, git clean -X, or drive.py end),
        # register this session, and archive nothing.
        (drive / "local").mkdir(parents=True, exist_ok=True)
        notes = []
        if not marker_path(root).exists():
            intake = git_out(root, "log", "--grep", "^drive(intake): {}$".format(old_goal.slug), "--format=%cI", "-1") \
                if old_goal.slug and has_head(root) else None
            marker_path(root).write_text(json.dumps({"slug": old_goal.slug, "goal": goal_text_of(old_goal), "resumed": iso_now(),
                                                     "started": intake or iso_now(), "size": old_goal.size,
                                                     "sessions": [session_id] if session_id else []}) + "\n")
            notes.append("Re-created .drive/local/active for {}; nothing was archived.".format(old_goal.slug))
            gate_log(root, "RESUME marker re-created for {}".format(old_goal.slug))
        register_session(root, session_id)
        if not baseline_path(root).is_file():
            baseline_path(root).write_text(json.dumps(capture_baseline(root), indent=2) + "\n", encoding="utf-8")
            notes.append("Recorded a hygiene baseline, because .drive/local/baseline.json was missing; paths uncommitted now "
                         "count as the owner's.")
        print("Same goal as the run already in .drive/ ({}). Resume it with drive.py start.".format(old_goal.slug))
        for note in notes:
            print(note)
        state_text = read_text(drive / "STATE.md")
        state = State(state_text) if state_text is not None else None
        if state is None:
            print("STATE.md is missing: write it from templates/STATE.md with the real next step before any other work.")
        elif state.status == "stalled":
            print("STATE.md says stalled. A stalled run does no more work: write REPORT.md saying 'Stopped because' and naming "
                  "the stall, then run drive.py end.")
        elif state.status == "blocked":
            print("STATE.md says blocked on '{}'. If that condition has cleared, append one DECISIONS.md entry naming the "
                  "evidence, set status: running, and continue from next:. Otherwise the run stays blocked and the turn "
                  "ends.".format(state.resume.get("blocked on", "")[:160]))
        return 0
    size = args.size
    if size is None:
        print("drive init: pass --size S, M, L, or XL from the classification. A new run's files and directories depend on its "
              "size, and a missing --size used to create an S run for every goal.", file=sys.stderr)
        return 2
    if size == "XS":
        print("drive init: XS runs create no .drive/. Record the claim and its evidence in the commit body instead.")
        return 1
    if old_goal is not None:
        archived, _ = archive_run(root, old_goal)
    drive.mkdir(exist_ok=True)
    (drive / "local").mkdir(exist_ok=True)
    head = git_out(root, "rev-parse", "--short", "HEAD") if has_head(root) else None
    today = now_utc().strftime("%Y-%m-%d")
    values = {
        "<goal slug>": slug,
        "<project>": root.name,
        '"<verbatim prompt>"': json.dumps(goal_text, ensure_ascii=False),
        "<ISO UTC>": iso_now(),
        "<short sha>": head or "none",
        "<today>": today,
    }
    names = SIZE_FILES["S"] if size == "S" else SIZE_FILES["M"]
    if archived and "DECISIONS.md" not in names:
        names = names + ["DECISIONS.md"]
    created = []
    for name in names:
        target = drive / name
        if target.exists():
            continue
        target.write_text(fill_template(name, values), encoding="utf-8")
        created.append(name)
    if size != "S":
        for folder in SIZE_DIRS:
            (drive / folder).mkdir(exist_ok=True)
    if archived:
        rel = archived.relative_to(root)
        with open(drive / "DECISIONS.md", "a", encoding="utf-8") as handle:
            handle.write(
                "\n## {} · Pause the unfinished run for a different goal\n"
                "- Context: .drive/ held a run for another goal when this goal arrived.\n"
                "- Decision: moved its tracked state to {} and its local files to .drive/local/archive/{}/.\n"
                "- Rejected: overwriting the old run (loses work); refusing the new goal (blocks the owner).\n"
                "- Undo: archive this run the same way, move the files in {} back into .drive/, and commit · reversal cost: low.\n"
                "- Evidence: {}/RESTORE.md\n"
                "- Narrows: none\n".format(today, rel, archived.name, rel, rel))
    baseline = capture_baseline(root)
    ignored = ensure_gitignore(root)
    marker_path(root).write_text(json.dumps({"slug": slug, "goal": goal_text, "started": iso_now(), "size": size,
                                             "sessions": [session_id] if session_id else []}) + "\n")
    baseline_path(root).write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")

    gate_log(root, "INIT {} size {}".format(slug, size))
    print("Initialised .drive/ for {} (size {}).".format(slug, size))
    if created:
        print("Created: {}.".format(", ".join(created)))
    if archived:
        print("Paused the previous run at {}; its restore steps are in RESTORE.md and DECISIONS.md.".format(archived.relative_to(root)))
    if ignored:
        print("Added to .gitignore: {}.".format(", ".join(ignored)))
    print("Next: fill GOAL.md (restate, classification, probe, plan), then commit it as drive(intake): {}.".format(slug))
    return 0


# Abort or Aborted, then punctuation or the end of the line: "Abort; the owner ended the run", never "Abort not needed".
ABORT_DECISION_RE = re.compile(r"(?i)^abort(ed)?\s*([;:,.]|$)")
BUDGET_DECISION_RE = re.compile(r"(?i)^(stop|narrow)")
# A named secret after credentials:: an uppercase identifier that contains an underscore or ends in a secret word, or a
# name of at least two letters in backquotes or double quotes. Words that name nothing are refused in every form.
SECRET_IDENTIFIER_RE = re.compile(r"(?<![A-Za-z0-9_])[A-Z][A-Z0-9_]*(?![A-Za-z0-9_])")
SECRET_QUOTED_RE = re.compile(r"`([^`\n]*)`|\"([^\"\n]*)\"")
SECRET_WORDS = ("TOKEN", "KEY", "SECRET", "PASSWORD", "PAT", "CREDENTIALS", "CERT")
SECRET_STOPLIST = {"NONE", "TBD", "TODO", "N/A", "NA", "UNKNOWN"}


def names_secret(text):
    for match in SECRET_IDENTIFIER_RE.finditer(text):
        word = match.group(0)
        if word not in SECRET_STOPLIST and ("_" in word or word.endswith(SECRET_WORDS)):
            return True
    for match in SECRET_QUOTED_RE.finditer(text):
        name = (match.group(1) if match.group(1) is not None else match.group(2)).strip()
        if len(re.findall(r"[A-Za-z]", name)) >= 2 and name.upper() not in SECRET_STOPLIST:
            return True
    return False


def decision_occurrences(text):
    """[(heading, [(number, line)])] for every `## ` entry in DECISIONS.md in order, one item per occurrence: Doc merges
    sections that share a heading, and an append-only log may repeat one."""
    entries, current, in_fence = [], None, False
    for number, line in enumerate((text or "").splitlines(), 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
        if not in_fence and line.startswith("## "):
            current = (line[3:].strip(), [])
            entries.append(current)
        elif current is not None:
            current[1].append((number, line))
    return entries


def decision_fields(lines):
    return Doc("").fields([(n, l[2:]) for n, l in lines if l.startswith("- ")])


def decisions_since_intake(root, goal):
    """[(heading, fields)] for the DECISIONS.md entries added since the drive(intake) commit. Entries are compared by
    heading and body, each intake entry matching one current entry, so a new entry that reuses an old heading counts."""
    text = read_text(Path(root) / ".drive" / "DECISIONS.md") or ""
    before = {}
    if goal is not None and goal.slug and has_head(root):
        intake = git_out(root, "log", "--grep", "^drive(intake): {}$".format(goal.slug), "--format=%H", "-1")
        old = show_at(root, intake, ".drive/DECISIONS.md") if intake else None
        for heading, lines in decision_occurrences(old or ""):
            key = (heading, tuple(l.rstrip() for _, l in lines if l.strip()))
            before[key] = before.get(key, 0) + 1
    added = []
    for heading, lines in decision_occurrences(text):
        key = (heading, tuple(l.rstrip() for _, l in lines if l.strip()))
        if before.get(key):
            before[key] -= 1
            continue
        added.append((heading, decision_fields(lines)))
    return added


def budget_stop_problems(root):
    """Why 'Blocked on: budget:' does not count yet: the maker spawns have not reached GOAL.md's subagent figure and no
    DECISIONS.md entry since intake has a Decision: line that begins with Stop or Narrow and names the budget."""
    goal_text = read_text(Path(root) / ".drive" / "GOAL.md")
    goal = Goal(goal_text) if goal_text is not None else None
    allowed, makers, _ = maker_spawn_counts(root, goal)
    if allowed is not None and makers >= allowed:
        return []
    for _, fields in decisions_since_intake(root, goal):
        decision = fields.get("decision", "").strip()
        if BUDGET_DECISION_RE.match(decision) and re.search(r"(?i)\bbudget", decision):
            return []
    return ["Blocked on 'budget:' counts only once the budget is spent: {} maker subagent(s) have started against {}, and no "
            "DECISIONS.md entry added since intake has a Decision: line that begins with 'Stop' or 'Narrow' and names the "
            "budget. Continue the work, or record that decision (for example 'Decision: Stop; the budget no longer covers "
            "the admin screen') before stopping on it".format(
                makers, "GOAL.md's budget of {} subagents".format(allowed) if allowed is not None else
                "a GOAL.md budget line with no subagent figure")]


def stopped_because(root):
    text = read_text(Path(root) / ".drive" / "REPORT.md")
    return text is not None and "Stopped because" in text


def launch_preflight_failed(root, session_id=None):
    """True when the latest drive.py preflight recorded for this session (or, when none is, the latest recorded without
    a session) reported a failure."""
    entries = ledger_entries(root, "preflight")
    if session_id:
        mine = [e for e in entries if e.get("session_id") == session_id] or [e for e in entries if not e.get("session_id")]
    else:
        mine = entries
    return bool(mine) and mine[-1].get("ok") is False


def blocked_problems(root, state, session_id=None):
    """Why a self-declared `blocked` status does not end the turn (empty list means it may)."""
    problems = []
    blocked_on = (state.resume.get("blocked on", "") if state else "").strip()
    lowered = blocked_on.lower()
    if lowered.startswith("launch preflight"):
        # A failed launch preflight stops the run before there is anything to report; the quoted relaunch command is the
        # owner's one step. It counts only when drive.py preflight itself recorded the failure.
        if not re.search(r"`[^`]*\bclaude\b[^`]*`|\"[^\"]*\bclaude\b[^\"]*\"|'[^']*\bclaude\b[^']*'", blocked_on):
            problems.append("Blocked on names the launch preflight but does not quote the relaunch command, for example "
                            "`claude --bg --name drive-<slug> --permission-mode auto --settings \"$DRIVE_SETTINGS\" '/drive --resume'`")
        if not launch_preflight_failed(root, session_id):
            problems.append("no failed drive.py preflight is recorded for this session, so the launch exception does not apply. "
                            "Run drive.py preflight: when it fails, the relaunch line ends the turn; when it passes, the launch "
                            "is fine and the run continues")
        return problems
    if not blocked_on or lowered.rstrip(".") == "none":
        problems.append("Blocked on names nothing. Name the single stop condition, who can unblock it, and the default taken meanwhile")
    elif not any(lowered.startswith(t) and blocked_on[len(t):].strip() for t in BLOCKED_TOKENS):
        problems.append("Blocked on ('{}') names no stop condition: it must begin with one of {} followed by the condition in "
                        "words (or 'launch preflight:' after a failed drive.py preflight). Anything else is work to do "
                        "now".format(blocked_on[:120], ", ".join(BLOCKED_TOKENS)))
    elif lowered.startswith("budget:"):
        problems.extend(budget_stop_problems(root))
    elif lowered.startswith("credentials:") and not names_secret(blocked_on[len("credentials:"):]):
        problems.append("Blocked on 'credentials:' must name the secret the owner has to provide: an environment variable such "
                        "as CLOUDFLARE_API_TOKEN (uppercase, containing an underscore or ending in TOKEN, KEY, SECRET, "
                        "PASSWORD, PAT, CREDENTIALS, or CERT), or the secret's name in backquotes or double quotes; NONE, "
                        "TBD, TODO, N/A, NA, and UNKNOWN name nothing")
    if not stopped_because(root):
        problems.append("REPORT.md does not exist or does not say 'Stopped because'. Finish every independent piece of work, then write "
                        "the report before stopping")
    return problems


def aborted_problems(root):
    problems = []
    if not (Path(root) / ".drive" / "REPORT.md").exists():
        problems.append("REPORT.md is missing; an aborted run still reports what stopped it")
    decisions = read_text(Path(root) / ".drive" / "DECISIONS.md") or ""
    recorded = False
    for _, lines in decision_occurrences(decisions):
        decision = decision_fields(lines).get("decision", "")
        if ABORT_DECISION_RE.match(decision.strip()):
            recorded = True
    if not recorded:
        problems.append("DECISIONS.md has no entry whose Decision: line records that the run was aborted: the line must begin "
                        "with 'Abort' or 'Aborted' followed by a semicolon, colon, comma, period, or the end of the line, for "
                        "example 'Decision: Abort; the owner ended the run'")
    return problems


def stall_recorded(root, state_text):
    """A stall counts only when the Stop gate itself set it, recorded in the ledger against these exact STATE.md bytes."""
    digest = hashlib.sha256((state_text or "").encode("utf-8")).hexdigest()
    return any(e.get("state_sha256") == digest for e in ledger_entries(root, "stall"))


def close_marker(root, how):
    marker = marker_path(root)
    if marker.is_file() and marker.parent == (Path(root) / ".drive" / "local"):
        marker.unlink()
    gate_log(root, "END run closed as {}".format(how))
    ledger_append(root, {"kind": "end", "how": how})


def cmd_end(args):
    root = find_root(args.root or os.getcwd())
    ctx = Ctx(root)
    status = ctx.state.status if ctx.state else ""
    if status == "aborted":
        _, f = run_lint(root, "stop")
        for problem in aborted_problems(root):
            f.fail("end", problem + ".")
    elif status in ("done", "stopped"):
        _, f = run_lint(root, "final", suite_timeout=args.suite_timeout)
    elif status == "blocked":
        f = Findings()
        for problem in blocked_problems(root, ctx.state, os.environ.get("CLAUDE_CODE_SESSION_ID")):
            f.fail("end", problem + ".")
    elif status == "stalled":
        f = Findings()
        if not stall_recorded(root, read_text(root / ".drive" / "STATE.md")):
            f.fail("end", "STATE.md says stalled, but the Stop gate did not set it (or STATE.md changed since). Set the status "
                   "the evidence supports: running and do next, or stopped with REPORT.md saying 'Stopped because'.")
        if not stopped_because(root):
            f.fail("end", "REPORT.md does not exist or does not say 'Stopped because'; a stalled run's report names the stall.")
    else:
        print("drive end: STATE.md status is {}. A run ends as done or stopped after lint --final passes, as aborted, or as "
              "blocked or stalled once the report says why it stopped.".format(status or "missing"))
        return 1
    if status in ("blocked", "stalled"):
        # Closing the run switches every hook off, so it needs the clean tree lint --stop requires: no branch, worktree,
        # or uncommitted path the run created. The Stop gate may still let a blocked turn end on a dirty tree.
        check_hygiene(ctx, f)
    if f.failed:
        for line in f.lines():
            print(line)
        print("drive end: the run cannot end until these are fixed.")
        return 1
    how = status if status in ("done", "stopped", "aborted") else "stopped (STATE.md says {})".format(status)
    close_marker(root, how)
    print("Run closed as {}: .drive/local/active removed, so drive's hooks are inert in this repository. The final state was already "
          "committed, as the checks required; /drive --resume re-creates the marker.".format(how))
    return 0


# ----------------------------------------------------------------------------------------------
# capabilities and selfcheck

EXPECTED_SKILLS = ["writing", "deep-research", "severe-testing", "frontend-design", "web-design-guidelines",
                   "code-review", "security-review", "simplify", "run", "workflow-authoring", "claude-api",
                   "tavily-search", "tavily-extract", "tavily-research", "tavily-dynamic-search",
                   "google-dev-docs-style", "dataviz", "imagegen", "rust-refinement",
                   "vercel-react-best-practices", "react-component-performance", "agent-browser"]


def cmd_capabilities(args):
    root = find_root(args.root or os.getcwd())
    home = Path(os.environ.get("HOME", str(Path.home())))
    out = {}
    try:
        skills = home / ".claude" / "skills"
        names = set(EXPECTED_SKILLS)
        if skills.is_dir():
            names |= {p.name for p in skills.iterdir()}
        for name in sorted(names):
            path = skills / name
            if path.is_symlink() and not path.exists():
                out["skill:" + name] = "dangling"
            else:
                out["skill:" + name] = (path / "SKILL.md").is_file()
        cache = home / ".claude" / "plugins" / "cache"
        if cache.is_dir():
            for skill_md in sorted(cache.glob("*/*/*/skills/*/SKILL.md")):
                plugin = skill_md.parents[3].name
                out["plugin-skill:{}:{}".format(plugin, skill_md.parent.name)] = True
    except OSError as exc:
        out["skill:error"] = str(exc)

    def which(name):
        return shutil.which(name) is not None

    try:
        if which("gh"):
            out["cli:gh"] = run(["gh", "auth", "status"], timeout=8)[0] == 0 or "unauthenticated"
        else:
            out["cli:gh"] = False
        for name in ("tvly", "imagegen", "wrangler", "agent-browser"):
            out["cli:" + name] = which(name)
        out["cli:xcodebuild"] = which("xcodebuild") and run(["xcodebuild", "-version"], timeout=15)[0] == 0
        booted = False
        if which("xcrun"):
            code, text, _ = run(["xcrun", "simctl", "list", "devices", "booted", "-j"], timeout=15)
            if code == 0:
                try:
                    devices = [d for group in json.loads(text).get("devices", {}).values() for d in group
                               if d.get("state") == "Booted"]
                    booted = devices[0]["name"] if devices else False
                except (ValueError, KeyError, IndexError, AttributeError):
                    booted = False
        out["cli:simctl"] = booted
    except Exception as exc:  # capabilities never fails
        out["cli:error"] = str(exc)
    out["git:origin"] = git_out(root, "remote", "get-url", "origin") if is_git_repo(root) else None
    try:
        out["git:visibility"], out["git:visibility_reason"] = repo_visibility(root)
    except Exception as exc:  # capabilities never fails; an unknown visibility is public
        out["git:visibility"], out["git:visibility_reason"] = "PUBLIC", "could not be established ({})".format(exc)
    out["env:provider"] = api_provider()[0]
    out["skill:drive_dir"] = str(SKILL_DIR)
    path = root / ".drive" / "capabilities.json"
    previous, _ = load_json(path) if path.exists() else (None, None)
    baseline = previous.get("git:baseline_sha") if isinstance(previous, dict) else None
    if not baseline and is_git_repo(root) and has_head(root):
        baseline = git_out(root, "rev-parse", "--short", "HEAD")
    out["git:baseline_sha"] = baseline
    out["checked_at"] = iso_now()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("Wrote {} ({} keys).".format(path, len(out)))
    except OSError as exc:
        print("drive capabilities could not write {}: {}".format(path, exc))
        print(json.dumps(out, indent=2, sort_keys=True))
    missing = [k for k, v in out.items() if v in (False, "dangling", "unauthenticated")]
    if missing:
        print("Missing or broken: {}.".format(", ".join(missing)))
    return 0


SELF_PATH_RE = re.compile(r"(?:(?<=[\s`(\"'\[|])|^|(?<=drive/)|(?<=skill/))((?:references|templates|scripts)/[A-Za-z0-9_\-./]*)")


def cmd_selfcheck(args):
    skill = Path(args.skill_dir).resolve() if args.skill_dir else SKILL_DIR
    sources = [skill / "SKILL.md"] + sorted((skill / "agents").glob("*.md")) + sorted((skill / "references").rglob("*.md"))
    missing = {}
    for source in sources:
        text = read_text(source)
        if text is None:
            if source.name == "SKILL.md":
                missing.setdefault("SKILL.md", []).append("(the skill directory)")
            continue
        for match in SELF_PATH_RE.finditer(text):
            token = match.group(1).rstrip(".,:;)")
            prefix = text[max(0, match.start() - 6):match.start()]
            if token.startswith("scripts/") and not (token.startswith(("scripts/drive", "scripts/tests"))
                                                     or prefix.endswith(("drive/", "skill/"))):
                continue
            if token.count("/") == 1 and token.endswith("/") is False and "." not in token.split("/")[1]:
                token = token + "/"
            if not (skill / token).exists():
                missing.setdefault(token, []).append(str(source.relative_to(skill)))
    over = False
    skill_md = read_text(skill / "SKILL.md")
    if skill_md is not None and skill_md.count("\n") + 1 > 450:
        over = True
        print("SKILL.md has {} lines; the cap is 450.".format(skill_md.count("\n") + 1))
    for token in sorted(missing):
        print("missing {} (named in {})".format(token, ", ".join(sorted(set(missing[token]))[:4])))
    if missing or over:
        print("selfcheck: {} missing path(s){}.".format(len(missing), ", SKILL.md over its cap" if over else ""))
        return 1
    print("selfcheck: every named path exists and SKILL.md is within its cap.")
    return 0


# ----------------------------------------------------------------------------------------------
# Hooks


def read_hook_input():
    try:
        raw = sys.stdin.read()
    except (OSError, ValueError):
        return {}
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def active_root(cwd):
    """The run root for a hook, resolved from the hook input's cwd: that directory's project, or the
    main checkout when cwd is inside a linked worktree, when it holds `.drive/local/active`. When the
    cwd has moved outside any active project (a persisted cd into /private/tmp), the session's
    project directory is used if it is active. Otherwise None, and the hook is inert."""
    if not cwd:
        return None
    candidates = []
    try:
        candidates.append(find_root(cwd))
        main = main_worktree_root(cwd)
        if main:
            candidates.append(main)
    except OSError:
        pass
    env_root = os.environ.get("CLAUDE_PROJECT_DIR")
    # Fall back to the session's project only when cwd left every repository (a cd into a scratch
    # directory). A cwd inside another repository belongs to that repository, so a stale marker in the
    # session's project never gates work there.
    if env_root and (is_tmp_path(Path(cwd)) or not git_out(cwd, "rev-parse", "--show-toplevel")):
        candidates.append(Path(env_root))
    for candidate in candidates:
        if (Path(candidate) / ".drive" / "local" / "active").is_file():
            return Path(candidate).resolve()
    return None


REINJECT_SECTIONS = re.compile(r"^(1\.|Standing rules|6\.|[7-9]\.|\d\d\.|Reference index)")


def skill_tail():
    """The parts of SKILL.md re-read after compaction: the contract (section 1), the standing rules,
    delegation (section 6), and section 7 to the end. Compaction keeps only the first 5,000 tokens of
    an invoked skill and may drop an older skill entirely, so the contract and delegation rules are
    re-printed rather than trusted to survive."""
    text = read_text(SKILL_DIR / "SKILL.md")
    if not text:
        return ""
    kept, keep = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            keep = bool(REINJECT_SECTIONS.match(line[3:].strip()))
        if keep:
            kept.append(line)
    return "\n".join(kept).rstrip()


def cmd_hook_reinject(args):
    data = read_hook_input()
    root = active_root(data.get("cwd"))
    if root is None:
        return 0
    if not session_is_drive(root, data.get("session_id")):
        return 0
    if data.get("source") == "resume":
        print("This conversation was resumed. drive's hooks, the Stop gate included, come from the plugin and apply again. "
              "Run `python3 {} preflight` before any other step.\n".format(SCRIPT_DIR / "drive.py"))
    try:
        view = start_view(root)
    except Exception as exc:
        view = "drive start could not read the run: {}".format(exc)
    print("This session is running /drive. The run's state lives in .drive/ and outranks any summary of "
          "earlier turns. Re-read .drive/STATE.md and .drive/GOAL.md, then continue from next:.\n")
    print(view)
    tail = skill_tail()
    if tail:
        print("")
        print(tail)
    return 0


NEVER_OPENS_GATE = re.compile(r"^\s*(caffeinate|sleep|yes|tail\s+-f|true)\b")


def listed_in_flight(task, flight):
    """A background task belongs to the run when STATE.md's In flight line names its id, or its whole command."""
    if flight in ("", "none"):
        return False
    task_id = str(task.get("id") or "").strip().lower()
    if task_id and re.search(r"(?<![\w\-]){}(?![\w\-])".format(re.escape(task_id)), flight):
        return True
    command = re.sub(r"\s+", " ", str(task.get("command") or "")).strip().lower()
    return len(command) >= 4 and command in flight


def background_allows(tasks, in_flight):
    """Background work lets a turn end only when it belongs to the run: a drive: subagent, or a task whose id or whole
    command is written under In flight. A description or name is not enough (a task described as "run build" can run
    anything), and an unrelated Explore agent, a workflow nobody recorded, or a task from before the run keeps the gate
    closed."""
    flight = re.sub(r"\s+", " ", in_flight or "").strip().lower()
    for task in tasks if isinstance(tasks, list) else []:
        if not isinstance(task, dict):
            continue
        state = str(task.get("status", "running")).lower()
        if state in ("completed", "complete", "failed", "killed", "stopped", "done", "cancelled"):
            continue
        kind = str(task.get("type", "")).lower()
        agent_type = str(task.get("agent_type") or "")
        label = agent_type or task.get("name") or task.get("description") or task.get("id") or kind
        if kind == "subagent" and agent_type.startswith("drive:"):
            return True, "subagent {} is running".format(label)
        if kind in ("shell", "monitor", "mcp task") and NEVER_OPENS_GATE.match(str(task.get("command") or task.get("description") or "")):
            continue
        if listed_in_flight(task, flight):
            return True, "{} '{}' is running and listed under In flight".format(kind, str(task.get("command") or task.get("id"))[:80])
    return False, ""


def progress_digest(root, text):
    """What counts as progress between two blocked stops: STATE.md apart from its updated: line, STATUS.md,
    HEAD, and the working tree's changes. Rewriting only the timestamp is not progress."""
    parts = [re.sub(r"(?m)^updated:.*$", "", text or ""), read_text(Path(root) / ".drive" / "STATUS.md") or "",
             git_out(root, "rev-parse", "HEAD") or "", git(root, "status", "--porcelain=v1", "-z")[1]]
    return hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()


def stop_counter(root):
    path = root / ".drive" / "local" / "stop-gate.json"
    data, _ = load_json(path) if path.exists() else (None, None)
    return path, data if isinstance(data, dict) else {}


def save_counter(path, data):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data) + "\n", encoding="utf-8")
    except OSError:
        pass


def hook_stop(root, data):
    """The Stop gate's decision. The Stop event is registered once, in the plugin's hooks.json, but a delivery can still
    repeat, so an identical event within a few seconds repeats the first decision instead of counting a second block."""
    counter_path, counter = stop_counter(root)
    key = stop_event_key(root, data)
    last = counter.get("last") if isinstance(counter.get("last"), dict) else {}
    if last.get("key") == key and time.time() - float(last.get("ts") or 0) < 3:
        return last.get("result")
    result = stop_decision(root, data)
    _, counter = stop_counter(root)
    counter["last"] = {"key": key, "ts": time.time(), "result": result}
    save_counter(counter_path, counter)
    return result


def stop_event_key(root, data):
    """The Stop event and the state it is judged against: the hook input, the run files a decision reads, and the
    ledger's size. A repeat within seconds with the same key is the same event delivered twice."""
    parts = [json.dumps(data, sort_keys=True, default=str)]
    for path in [Path(root) / ".drive" / n for n in ("STATE.md", "STATUS.md", "REPORT.md", "DECISIONS.md", "GOAL.md")] + [ledger_file(root)]:
        try:
            stat = path.stat()
            parts.append("{}:{}:{}".format(path.name, stat.st_size, stat.st_mtime_ns))
        except OSError:
            parts.append(path.name + ":missing")
    return hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()


def block_cap():
    try:
        return max(1, int(os.environ.get("CLAUDE_CODE_STOP_HOOK_BLOCK_CAP") or 8))
    except ValueError:
        return 8


def stop_decision(root, data):
    state_path = root / ".drive" / "STATE.md"
    text = read_text(state_path)
    counter_path, counter = stop_counter(root)
    state = State(text) if text is not None else None
    allowed, why = background_allows(data.get("background_tasks"), state.in_flight if state else "")
    if allowed:
        save_counter(counter_path, {})
        gate_log(root, "ALLOW background: {}".format(why))
        return None
    if state is None:
        reason = "The drive run is active but .drive/STATE.md is missing. Write it from templates/STATE.md with the real next step before stopping."
    else:
        status = state.status
        gate_problems = None
        if status == "blocked":
            gate_problems = blocked_problems(root, state, data.get("session_id"))
        elif status == "aborted":
            gate_problems = aborted_problems(root)
        elif status == "stalled":
            gate_problems = [] if stall_recorded(root, text) else [
                "the Stop gate did not set this stalled status (or STATE.md changed after it did). Set the status the evidence "
                "supports: running with the real next step, or stopped with REPORT.md saying 'Stopped because'"]
        if gate_problems == []:
            save_counter(counter_path, {})
            gate_log(root, "ALLOW status {}".format(status))
            return None
        if gate_problems:
            reason = "STATE.md says {}, which does not end the run yet: {}.".format(status, "; ".join(gate_problems))
        elif status in ("done", "stopped"):
            _, f = run_lint(root, "final", run_commands=False)
            if not f.failed:
                save_counter(counter_path, {})
                gate_log(root, "ALLOW {}; lint --final passes".format(status))
                return None
            reason = ("STATE.md says " + status + ", but drive.py lint --final fails. Fix these, or set the status the evidence "
                      "supports: " + " ".join(i["message"] if i["file"] in i["message"] else "{}: {}".format(i["file"], i["message"])
                                               for i in f.items if i["level"] == "fail")[:1500])
        elif status in GATE_CLOSED:
            _, f = run_lint(root, "stop")
            nxt = state.fields.get("next") or "(no next step is recorded; write one)"
            reason = ("The drive run is still {}. Do the next step now with tool calls: {} Then update STATE.md "
                      "(next, updated, commit) before you stop again.".format(status, nxt.rstrip(".") + "."))
            failures = ["{}: {}".format(i["file"], i["message"]) for i in f.items if i["level"] == "fail"]
            if failures:
                reason += " Also fix these lint findings: " + " ".join(failures[:8])
                if len(failures) > 8:
                    reason += " (and {} more; run drive.py lint --stop).".format(len(failures) - 8)
        else:
            reason = "STATE.md status '{}' is not one of running, verifying, blocked, stalled, done, stopped, aborted. Set the status the run is really in.".format(status)
    digest = progress_digest(root, text)
    if counter.get("hash") == digest and int(counter.get("count", 0)) >= 6:
        if text is not None:
            new_text = re.sub(r"^status:.*$", "status: stalled", text, count=1, flags=re.M)
            try:
                state_path.write_text(new_text, encoding="utf-8")
                ledger_append(root, {"kind": "stall", "state_sha256": hashlib.sha256(new_text.encode("utf-8")).hexdigest(),
                                     "session_id": data.get("session_id")})
            except OSError:
                pass
        save_counter(counter_path, {"stalled_by_hook": iso_now()})
        gate_log(root, "STALL six blocks with STATE.md, STATUS.md, HEAD, and the working tree unchanged; status set to stalled")
        return {"systemMessage": "drive: nothing that counts as progress (STATE.md apart from its updated: line, STATUS.md, HEAD, "
                                 "and the working tree) changed across six blocked stops, so the run is marked stalled. "
                                 "Write REPORT.md saying 'Stopped because' and naming the stall, then drive.py end closes it."}
    count = int(counter.get("count", 0)) + 1 if counter.get("hash") == digest else 1
    consecutive, cap = int(counter.get("consecutive", 0)) + 1, block_cap()
    save_counter(counter_path, {"hash": digest, "count": count, "consecutive": consecutive, "cap": cap})
    gate_log(root, "BLOCK ({} with this STATE.md, {} in a row) {}".format(count, consecutive, reason[:300]))
    if consecutive >= cap:
        # Claude Code overrides the block and ends the turn once the cap is reached; record it so the next start view
        # and resume say the turn ended on the cap, not because the run was finished.
        gate_log(root, "CAP {} consecutive blocks reached CLAUDE_CODE_STOP_HOOK_BLOCK_CAP ({}); Claude Code ends the turn anyway".format(consecutive, cap))
        ledger_append(root, {"kind": "stop-cap", "consecutive": consecutive, "cap": cap, "session_id": data.get("session_id")})
    return {"decision": "block", "reason": reason}


def lost_marker_warning(data):
    """A warning, once per session, when .drive/STATE.md (found from the hook's cwd up to the git top level) says running or
    verifying but .drive/local/active is gone, so every drive hook is inert (a git clean -X, or a marker deleted by hand).
    The stop is still allowed."""
    cwd = data.get("cwd")
    if not cwd or not is_dir_quietly(cwd):
        return None
    try:
        start = Path(cwd).resolve()
        top = git_out(start, "rev-parse", "--show-toplevel")
        limit = Path(top).resolve() if top else start
        candidates = []
        for candidate in [start, *start.parents]:
            candidates.append(candidate)
            if candidate == limit:
                break
        main = main_worktree_root(start)
        if main and main not in candidates:
            candidates.append(Path(main))
    except OSError:
        return None
    for root in candidates:
        text = read_text(root / ".drive" / "STATE.md")
        if text is None:
            continue
        status = State(text).status
        if (root / ".drive" / "local" / "active").is_file() or status not in GATE_CLOSED:
            return None
        record = root / ".drive" / "local" / "lost-marker-warned.json"
        seen, _ = load_json(record) if record.is_file() else (None, None)
        sessions = seen.get("sessions") if isinstance(seen, dict) and isinstance(seen.get("sessions"), list) else []
        session = str(data.get("session_id") or "unknown")
        if session in sessions:
            return None
        try:
            record.parent.mkdir(parents=True, exist_ok=True)
            record.write_text(json.dumps({"sessions": (sessions + [session])[-50:]}) + "\n", encoding="utf-8")
        except OSError:
            pass
        return ("drive: {}/.drive/STATE.md says {}, but .drive/local/active is missing, so drive's guard and Stop gate are off "
                "in this repository and this stop was not checked. If the run is still going, resume it with /drive --resume "
                "(drive.py init --goal - with GOAL.md's goal re-creates the marker); if it has ended, set the status the "
                "evidence supports.".format(root, status))
    return None


def cmd_hook_stop(args):
    data = read_hook_input()
    root = active_root(data.get("cwd"))
    if root is None:
        warning = lost_marker_warning(data)
        if warning:
            print(warning, file=sys.stderr)
            print(json.dumps({"systemMessage": warning}))
        return 0
    sessions = read_marker(root).get("sessions")
    session = data.get("session_id")
    if isinstance(sessions, list) and sessions and session and session not in sessions:
        # Another session in this repository (an XS fix, or a session that never ran this goal) is not this run's to hold.
        return 0
    record_session_mode(root, data)
    lock = None
    try:
        try:
            import fcntl
            (root / ".drive" / "local").mkdir(parents=True, exist_ok=True)
            lock = open(str(root / ".drive" / "local" / "stop-gate.lock"), "a")
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        except (ImportError, OSError):
            lock = None
        result = hook_stop(root, data)
    except Exception as exc:
        gate_log(root, "ERROR stop gate raised {}: {}".format(type(exc).__name__, exc))
        print(json.dumps({"systemMessage": "drive stop gate failed ({}); the stop was allowed. Run drive.py lint --stop.".format(exc)}))
        return 0
    finally:
        if lock is not None:
            lock.close()
    if result:
        print(json.dumps(result))
    return 0


# --- hook-guard: per-agent rules -------------------------------------------------------------

ROLES = {"researcher", "architect", "designer", "implementer", "writer", "verifier", "severe-tester",
         "security-reviewer", "ui-reviewer", "grader", "investigator", "auditor"}
READ_ONLY = {"verifier", "security-reviewer", "grader", "auditor"}
BASH_WRITE_SCOPE = {
    "verifier": [".drive/proofs/", ".drive/reviews/", ".drive/local/ios/"],
    "grader": [".drive/proofs/", ".drive/reviews/"],
    "auditor": [".drive/proofs/", ".drive/reviews/"],
    "security-reviewer": [".drive/proofs/", ".drive/reviews/"],
    "ui-reviewer": [".drive/proofs/", ".drive/reviews/", ".drive/local/ui/", ".drive/local/ios/"],
}
TOOL_WRITE_SCOPE = {
    "architect": [".drive/", "docs/", "design/", "src/content/claims/"],
    "designer": ["design/", ".drive/"],
    "researcher": [".drive/"],
    "investigator": [".drive/"],
    "ui-reviewer": [".drive/proofs/", ".drive/local/"],
    "severe-tester": [],
}
ROLE_WORDS = {
    "verifier": "The verifier checks work and changes nothing",
    "security-reviewer": "The security reviewer reads and reports and changes nothing",
    "grader": "The grader reads and grades and changes nothing",
    "auditor": "The auditor reads and rules and changes nothing",
    "ui-reviewer": "The UI reviewer captures evidence and changes no product files",
    "severe-tester": "The severe tester writes only tests, fixtures, and its own proof files (severe*.md, commands.log, red/)",
    "architect": "The architect writes only .drive/, docs/, design/, and src/content/claims/",
    "designer": "The designer writes only design/ and .drive/",
    "researcher": "The researcher writes only under .drive/",
    "investigator": "The investigator writes only .drive/ and throwaway worktrees under a scratch directory",
    "implementer": "The implementer edits its owned files and never touches git",
    "writer": "The writer edits its owned files and never touches git",
}
TEST_DIRS = {"test", "tests", "__tests__", "spec", "specs", "fixtures", "__fixtures__", "testdata", "test-data",
             "e2e", "__snapshots__", "testing", "uitests", "test_data"}
TEST_NAME_RE = re.compile(r"(^test_|_test\.|\.test\.|\.spec\.|_spec\.|^severe_|Tests?\.(swift|java|kt|kts|cs|m)$|^test\.|-test\.)")


def is_test_path(rel):
    parts = rel.replace("\\", "/").split("/")
    for part in parts[:-1]:
        if part.lower() in TEST_DIRS or part.endswith("Tests") or part.endswith("Test"):
            return True
    return bool(TEST_NAME_RE.search(parts[-1]))


MAKERS = {"implementer", "writer"}
INLINE_CHECKED = READ_ONLY | {"ui-reviewer", "severe-tester", "architect", "designer", "researcher", "investigator"}
ROLE_WORDS["orchestrator"] = ("The orchestrator never writes verdicts, final audits, live proofs, citation checks, or the provenance "
                              "ledger; the reviewing agents write them and drive's hooks record them")
EVIDENCE_MARKERS = re.compile(r"verdict\.json|final-audit|proof\.json|-citations-|\.drive/proofs|\.drive/reviews|\.drive/local/ro\b|"
                              r"\.claude/drive\b|plugins/data\b|CLAUDE_PLUGIN_DATA")


def role_of(agent_type):
    """A drive roster role, only for the plugin-scoped `drive:<name>` agent type. A bare `verifier` is some
    other agent, and drive's hooks leave it alone."""
    name = str(agent_type or "")
    if not name.startswith("drive:"):
        return None
    name = name[len("drive:"):]
    return name if name in ROLES else None




def rel_in_root(path: Path, root: Path):
    try:
        return str(realpath_loose(path).relative_to(realpath_loose(root))).replace("\\", "/")
    except ValueError:
        return None


def harness_worktree_roots(root):
    """Linked worktrees under <root>/.claude/worktrees/, where a background session edits when worktree
    isolation is on. Paths inside one are judged relative to that worktree, not the main checkout."""
    base = realpath_loose(Path(root) / ".claude" / "worktrees")
    out = []
    for entry in worktree_entries(root)[1:]:
        path = realpath_loose(Path(entry.get("worktree", "")))
        if is_within(path, base) and path != base:
            out.append(path)
    return out


def guard_rel(path: Path, root: Path, role=None):
    """(relative path, the root it is relative to) for a guarded write, or (None, None) outside every root."""
    roots = harness_worktree_roots(root) + [Path(root)]
    if role in MAKERS:
        ctx_goal = read_text(Path(root) / ".drive" / "GOAL.md")
        if ctx_goal:
            roots.extend(Goal(ctx_goal).repos())
    for candidate in roots:
        rel = rel_in_root(path, candidate)
        if rel is not None:
            return rel, candidate
    return None, None


def in_scope(rel, prefixes):
    if rel is None:
        return False
    probe = rel + "/" if not rel.endswith("/") else rel
    return any(probe.startswith(p) or rel == p.rstrip("/") for p in prefixes)


def protected_evidence_rel(rel):
    """Files only a reviewing agent writes: every JSON file under .drive/proofs/ and .drive/reviews/, and
    the void markers under .drive/local/ro/."""
    if rel is None:
        return False
    name = rel.rsplit("/", 1)[-1]
    if rel.startswith((".drive/proofs/", ".drive/reviews/")) and name.endswith(".json"):
        return True
    if rel.startswith(".drive/") and name in ("verdict.json", "proof.json"):
        return True
    return rel.startswith(".drive/local/ro/")


REVIEWER_COMMANDS = {
    "cat", "head", "tail", "grep", "egrep", "fgrep", "rg", "ag", "ls", "tree", "find", "wc", "sort", "uniq", "cut", "tr", "diff",
    "cmp", "comm", "file", "stat", "du", "df", "pwd", "echo", "printf", "true", "false", "test", "[", "date", "printenv", "which",
    "type", "basename", "dirname", "realpath", "readlink", "jq", "yq", "sed", "gsed", "awk", "gawk", "mawk", "xxd", "od", "hexdump",
    "base64", "shasum", "sha256sum", "sha1sum", "md5", "md5sum", "cksum", "column", "nl", "fold", "paste", "join", "seq", "sleep",
    "cd", "pushd", "popd", "set", "export", "unset", "read", "wait", "exit", "return", "local", "declare", "ps", "pgrep", "lsof",
    "uname", "sw_vers", "id", "whoami", "hostname", "nproc", "sysctl", "tee", "mkdir", "touch", "cp", "mv", "rm", "rmdir", "ln",
    "tar", "unzip", "zip", "gzip", "gunzip", "git", "gh", "curl", "wget", "dig", "nslookup", "ping", "openssl", "sh", "bash",
    "zsh", "eval", "source", ".", "python", "python3", "node", "deno", "bun", "npm", "npx", "pnpm", "yarn", "make", "gmake",
    "pytest", "jest", "vitest", "mocha", "playwright", "go", "cargo", "rustc", "swift", "swiftc", "xcodebuild", "xcrun", "gradle",
    "gradlew", "mvn", "dotnet", "bundle", "rake", "rspec", "mix", "ruby", "perl", "php", "composer", "tsc", "eslint", "prettier",
    "ruff", "mypy", "black", "flake8", "pylint", "golangci-lint", "swiftlint", "wrangler", "terraform", "kubectl", "docker",
    "screencapture", "sips", "magick", "ffprobe", "lighthouse", "agent-browser", "tvly", "tox",
    "nox", "coverage", "time", "timeout", "gtimeout", "vercel", "netlify", "firebase", "fastlane", "twine", "gem", "pod", "helm",
    "pulumi", "aws", "gcloud", "cargo-nextest", "stat", "xmllint", "plutil", "defaults", "log",
}
REVIEWER_MAKE_TARGETS = {"test", "tests", "check", "lint", "build", "verify", "ci", "typecheck", "type-check", "fmt-check",
                         "format-check", "all"}
AWK_WRITE_RE = re.compile(r"(?:print|printf)\b[^;}\n]*>|system\s*\(|\|\s*getline|\"\s*\|\s*getline|\|&|fflush\s*\(")
SED_WRITE_RE = re.compile(r"(?:^|[;{}\n])\s*[wWe](?:\s|$)|/[gpIiMm0-9]*[wWe]\s")


FROZEN_LIST = ".drive/frozen.txt"
FROZEN_MANIFEST = ".drive/frozen.sha256"
FROZEN_PARKED = ".drive/local/frozen-parked"
ALWAYS_PROTECTED_REL = (FROZEN_LIST, FROZEN_MANIFEST, FROZEN_PARKED)
# The run marker every hook checks, and the owner's hygiene baseline. While a run is active nobody deletes, moves, or
# overwrites them; drive.py init writes them and drive.py end removes the marker.
RUN_CONTROL_REL = (".drive/local/active", ".drive/local/baseline.json")
# Delete calls in inline code: with a literal naming the run marker, the baseline, or .drive/local, they are refused like rm.
CODE_DELETE_RE = re.compile(r"\bos\.(?:remove|unlink|rmdir|removedirs)\s*\(|\bshutil\.rmtree\s*\(|\.unlink\s*\(|"
                            r"\b(?:rmSync|unlinkSync|rmdirSync)\s*\(|\bfs(?:\.promises)?\.(?:rm|unlink|rmdir)\s*\(|"
                            r"\bunlink\b|\bFile\.delete\b|\bFileUtils\.rm")


def normalise_rel(value):
    rel = str(value or "").strip().replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    return rel.rstrip("/")


def frozen_entries(root):
    """The paths .drive/frozen.txt lists (files or directories), relative to the root."""
    text = read_text(Path(root) / FROZEN_LIST)
    return [normalise_rel(l) for l in (text or "").splitlines() if l.strip() and not l.strip().startswith("#")]


def frozen_manifest(root, text=None):
    """{relative path: sha256} from .drive/frozen.sha256, or from `text` (a manifest read at another commit)."""
    text = read_text(Path(root) / FROZEN_MANIFEST) if text is None else text
    out = {}
    for line in (text or "").splitlines():
        match = re.match(r"^([0-9a-f]{64})\s+(.+)$", line.strip())
        if match:
            out[normalise_rel(match.group(2))] = match.group(1)
    return out


def write_manifest(root, manifest):
    lines = ["{}  {}".format(manifest[p], p) for p in sorted(manifest)]
    (Path(root) / FROZEN_MANIFEST).write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def files_under(root, rel):
    path = Path(root) / rel
    if path.is_file():
        return [rel]
    if path.is_dir():
        return sorted(str(p.relative_to(root)).replace("\\", "/") for p in path.rglob("*") if p.is_file())
    return []


def frozen_test_paths(root):
    """Every file the freeze covers: each path .drive/frozen.txt lists, with a listed directory's files."""
    out = set()
    for entry in frozen_entries(root):
        out.update(files_under(root, entry) or [entry])
    return out


def open_amendments(root):
    """{frozen path: claim key} for paths whose latest amendment record is open."""
    latest = {}
    for entry in ledger_entries(root, "freeze-amend"):
        for path in entry.get("paths") or []:
            latest[path] = entry
    return {p: e.get("key") for p, e in latest.items() if e.get("state") == "open"}


def enforcement_files():
    return [SKILL_DIR / "scripts" / "drive.py", SKILL_DIR / "hooks" / "hooks.json"]


def frozen_match(root, path, container=False, entries=None, run_control=True):
    """The frozen entry, manifest file, enforcement file, or (with run_control) run marker or baseline a write to `path`
    would change. With container, also the entries a delete or move of the directory `path` would take with it."""
    real = realpath_loose(path)
    for protected in enforcement_files():
        target = realpath_loose(protected)
        if real == target or (container and is_within(target, real)):
            return str(protected)
    rel = rel_in_root(real, root)
    if rel is None:
        return None
    rel = "" if rel == "." else rel
    extra = list(ALWAYS_PROTECTED_REL) + (list(RUN_CONTROL_REL) if run_control else [])
    for entry in list(frozen_entries(root) if entries is None else entries) + extra:
        if not entry:
            continue
        if rel == entry or rel.startswith(entry + "/"):
            return entry
        if container and (rel == "" or entry.startswith(rel + "/")):
            return entry
    return None


def frozen_block_reason(root, path, role, container=False, entries=None, run_control=True):
    hit = frozen_match(root, path, container, entries, run_control)
    if hit is None:
        return None
    if hit in RUN_CONTROL_REL:
        what = "run marker" if hit.endswith("active") else "hygiene baseline"
        return ("{} is the drive run's {}. While a run is active no agent and not the main thread deletes, moves, or overwrites "
                "it: without the marker every drive hook switches off, and without the baseline the hygiene lint cannot tell "
                "the owner's files from the run's. drive.py end removes the marker when the run closes; to clean build output, "
                "remove the named paths or ignore them in .gitignore.".format(hit, what))
    enforcement = hit in ALWAYS_PROTECTED_REL or hit in {str(p) for p in enforcement_files()}
    if role == "severe-tester" and not enforcement:
        rel = rel_in_root(realpath_loose(path), root)
        if rel and any(rel == p or rel.startswith(p + "/") for p in open_amendments(root)):
            return None
    if enforcement:
        return ("{} is part of drive's enforcement (the freeze manifest, drive.py, or hooks.json); no agent and not the main "
                "thread changes it during a run, and only drive.py freeze writes the manifest.".format(hit))
    return ("{} is frozen (listed in .drive/frozen.txt). A frozen test is read and run, never modified, moved, skipped, or "
            "deleted; a test that looks wrong is a test dispute (references/testing.md section 9), and only drive:severe-tester "
            "changes it while an amendment is open.".format(hit))


def without_sed_backup_suffix(args):
    """sed arguments without a backup suffix given as its own argument: BSD sed reads `sed -i '' 's/a/b/' file` and
    `sed -i .bak ...` as -i with the suffix '' or .bak, so an empty argument or one starting with '.' right after an exact
    -i is neither the script nor a file. GNU's attached -i.bak is an ordinary flag. Perl never takes a separate suffix, so
    its arguments are not passed through this."""
    out, skip = [], False
    for index, arg in enumerate(args):
        if skip:
            skip = False
            continue
        out.append(arg)
        if arg == "-i" and index + 1 < len(args) and (args[index + 1] == "" or args[index + 1].startswith(".")):
            skip = True
    return out


def in_place_targets(base, args):
    """The files an in-place sed, perl, or ruby edit writes: never its script. A script comes from -e, --expression,
    -f, or --file (whose values are skipped), or else is the first operand. A BSD sed backup suffix given as its own
    argument after -i is skipped too."""
    if base in ("sed", "gsed"):
        args = without_sed_backup_suffix(args)
    value_flags = ("-e", "--expression", "-f", "--file") if base in ("sed", "gsed") else ("-e", "-E")
    operands, scripted, skip, rest = [], False, False, False
    for arg in args:
        if skip:
            skip = False
            continue
        if rest:
            operands.append(arg)
        elif arg == "--":
            rest = True
        elif arg in value_flags:
            scripted, skip = True, True
        elif arg.startswith(("--expression=", "--file=")):
            scripted = True
        elif arg.startswith("-") and arg != "-":
            continue
        else:
            operands.append(arg)
    return operands if scripted else operands[1:]


def plain_operands(args):
    out, rest = [], False
    for arg in args:
        if rest:
            out.append(arg)
        elif arg == "--":
            rest = True
        elif arg.startswith("-") and arg != "-":
            continue
        else:
            out.append(arg)
    return out


def in_ledger_roots(path: Path):
    """The provenance ledger, or a Claude Code transcript that provenance rests on."""
    resolved = realpath_loose(path)
    return any(is_within(resolved, realpath_loose(r)) for r in ledger_guard_roots()) or is_transcript_path(resolved)


def main_write_reason(raw_path, root, cwd):
    if not raw_path:
        return None
    path = Path(raw_path.replace("\\", "/"))
    if not path.is_absolute():
        path = Path(cwd or root) / path
    if in_ledger_roots(path):
        return "{}. {} is the provenance ledger or a session transcript, which only drive's hooks and Claude Code write.".format(ROLE_WORDS["orchestrator"], raw_path)
    rel = rel_in_root(path, root)
    if protected_evidence_rel(rel):
        return ("{}. {} is evidence a reviewer produces; spawn the verifier, ui-reviewer, auditor, or grader whose brief names "
                "that file instead of writing it.").format(ROLE_WORDS["orchestrator"], rel)
    if rel in frozen_test_paths(root):
        return ("{} is a frozen test: a severe: refutation test or a test a package must make pass. Only drive:severe-tester "
                "changes it; a test that is wrong is a finding for the verifier, not an edit.").format(rel)
    return None


def record_session_mode(root, data):
    """Remember the permission mode the hooks last saw for this session, for `drive.py preflight`."""
    mode = data.get("permission_mode")
    if not mode or data.get("agent_id"):
        return
    path = Path(root) / ".drive" / "local" / "session.json"
    record = {"session_id": data.get("session_id"), "permission_mode": mode}
    previous, _ = load_json(path) if path.is_file() else (None, None)
    if isinstance(previous, dict) and all(previous.get(k) == v for k, v in record.items()):
        return
    record["seen"] = iso_now()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    except OSError:
        pass


SAFE_PY_MODULES = {"json", "sys", "re", "math", "collections", "itertools", "functools", "datetime", "time", "statistics",
                   "hashlib", "textwrap", "string", "pprint", "difflib", "decimal", "fractions", "csv", "glob", "fnmatch",
                   "unicodedata", "operator", "typing", "dataclasses", "enum", "heapq", "bisect", "copy", "numbers", "random",
                   "uuid", "base64", "binascii", "struct", "html", "shlex", "ipaddress", "calendar", "os", "os.path",
                   "posixpath", "urllib.parse", "email.utils", "sysconfig", "platform", "importlib.util", "sqlite3"}
IMAGE_MODULES = {"PIL", "PIL.Image", "PIL.ImageDraw", "PIL.ImageOps", "PIL.ImageFont", "PIL.ImageChops", "PIL.ImageFilter",
                 "PIL.ImageStat", "PIL.ImageEnhance"}
PY_BLOCKED_NAMES = {"exec", "eval", "compile", "__import__", "getattr", "setattr", "delattr", "globals", "locals", "vars",
                    "breakpoint", "input", "memoryview", "help"}
PY_BLOCKED_ATTRS = {"modules", "system", "popen", "remove", "unlink", "rmdir", "removedirs", "rename", "renames", "replace",
                    "mkdir", "makedirs", "chmod", "lchmod", "chown", "lchown", "chflags", "link", "symlink", "truncate", "ftruncate",
                    "write", "writelines", "write_text", "write_bytes", "open", "fdopen", "fork", "forkpty", "kill", "killpg",
                    "putenv", "unsetenv", "utime", "mkfifo", "mknod", "startfile", "posix_spawn", "posix_spawnp", "dup2",
                    "pipe", "chroot", "setuid", "setgid", "load_module", "exec_module", "copyfile", "move", "rmtree",
                    "settrace", "setprofile", "execv", "execve", "execl", "execle", "execlp", "execlpe", "execvp", "execvpe",
                    "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe", "lchflags",
                    "setxattr", "removexattr", "enable_load_extension", "load_extension", "spec_from_file_location",
                    "module_from_spec"}
# A UI reviewer's pixel diff may use numpy on images it reads. These numpy and PIL names write files, map memory,
# unpickle, fetch URLs into the working directory, compile, run code, or open a viewer, so they stay refused.
NUMPY_MODULES = {"numpy"}
IMAGE_BLOCKED_ATTRS = {"memmap", "open_memmap", "DataSource", "f2py", "distutils", "ctypeslib", "ctypes", "testing",
                       "genfromtxt", "loadtxt", "fromregex", "recfromtxt", "recfromcsv", "show"}
# Calls that write their first argument (or the named file keyword): allowed only to a constant path write_ok accepts.
IMAGE_OUTPUT_ATTRS = {"save", "savez", "savez_compressed", "savetxt", "tofile", "dump"}
OUTPUT_FILE_KEYWORDS = ("fp", "file", "fname", "fid")


def import_bindings(tree):
    """Each name the code binds only by importing, mapped to what it imports (`from PIL import Image` maps Image to
    PIL.Image). A name also bound any other way (an assignment, an argument, a def, or an import of something else,
    as in `import os as Image`) is left out, so it never passes for the module it shadows."""
    bound, other = {}, set()
    for node in ast.walk(tree):
        pairs = []
        if isinstance(node, ast.Import):
            pairs = [(a.asname, a.name) if a.asname else (a.name.split(".")[0], a.name.split(".")[0]) for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            pairs = [(a.asname or a.name, "{}.{}".format(node.module or "", a.name)) for a in node.names]
        elif isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Load):
            other.add(node.id)
        elif isinstance(node, ast.arg):
            other.add(node.arg)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            other.add(node.name)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            other.add(node.name)
        for name, module in pairs:
            if bound.get(name, module) != module:
                other.add(name)
            bound[name] = module
    return {name: module for name, module in bound.items() if name not in other}


def python_code_reason(code, write_ok=None, extra_modules=()):
    """Why inline Python may write, delete, or run something (None when it can only read and print). With write_ok, a
    write to a constant path it accepts is allowed (a UI reviewer's image crops and pixel diffs into its own output
    directories)."""
    allowed = SAFE_PY_MODULES | set(extra_modules)
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return "it does not parse as Python the guard can check"
    bindings = import_bindings(tree)
    called = {id(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}

    def constant_output(first):
        return bool(write_ok and isinstance(first, ast.Constant) and isinstance(first.value, str) and write_ok(first.value))

    # sqlite3 is allowed for probes on an in-memory database: a file path, an ATTACH, or VACUUM INTO would write a file.
    uses_sqlite = any((isinstance(n, ast.Import) and any(a.name == "sqlite3" for a in n.names))
                      or (isinstance(n, ast.ImportFrom) and n.module == "sqlite3") for n in ast.walk(tree))
    if uses_sqlite:
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "connect" and isinstance(node.value, ast.Name) \
                    and bindings.get(node.value.id) == "sqlite3" and id(node) not in called:
                return "it passes sqlite3.connect around instead of calling it"
            if isinstance(node, ast.Name) and bindings.get(node.id) == "sqlite3.connect" and id(node) not in called:
                return "it passes sqlite3.connect around instead of calling it"
            if isinstance(node, ast.Call):
                func = node.func
                direct = isinstance(func, ast.Attribute) and func.attr == "connect" and isinstance(func.value, ast.Name) \
                    and bindings.get(func.value.id) == "sqlite3"
                imported = isinstance(func, ast.Name) and bindings.get(func.id) == "sqlite3.connect"
                if direct or imported:
                    memory = (len(node.args) == 1 and isinstance(node.args[0], ast.Constant) and node.args[0].value == ":memory:"
                              and all(k.arg in ("timeout", "isolation_level", "check_same_thread", "detect_types")
                                      for k in node.keywords))
                    if not memory:
                        return "it opens a SQLite database other than ':memory:'"
            if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                    and re.search(r"(?i)\battach\b|\bvacuum\s+into\b", node.value):
                return "it attaches or writes a database file"
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in allowed:
                    return "it imports {}".format(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "") not in allowed or any(a.name == "*" for a in node.names):
                return "it imports from {}".format(node.module)
            for alias in node.names:
                if alias.name in PY_BLOCKED_ATTRS or alias.name in PY_BLOCKED_NAMES:
                    return "it imports {}".format(alias.name)
        elif isinstance(node, ast.Name):
            if node.id in PY_BLOCKED_NAMES or node.id.startswith("__"):
                return "it uses {}".format(node.id)
            if node.id == "open" and id(node) not in called:
                return "it passes open around instead of calling it"
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("__"):
                return "it reaches {}".format(node.attr)
            if extra_modules and node.attr in IMAGE_BLOCKED_ATTRS:
                return "it uses .{}".format(node.attr)
            if node.attr in PY_BLOCKED_ATTRS:
                target = node.value
                console = (node.attr in ("write", "writelines") and isinstance(target, ast.Attribute)
                           and target.attr in ("stdout", "stderr") and isinstance(target.value, ast.Name) and target.value.id == "sys")
                image_open = bool(extra_modules) and node.attr == "open" and (
                    (isinstance(target, ast.Name) and bindings.get(target.id) == "PIL.Image")
                    or (isinstance(target, ast.Attribute) and target.attr == "Image"
                        and isinstance(target.value, ast.Name) and bindings.get(target.value.id) == "PIL"))
                handle_write = write_ok is not None and node.attr in ("write", "writelines")
                if not (console or image_open or handle_write):
                    return "it calls .{}".format(node.attr)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
            if any(isinstance(a, ast.Starred) for a in node.args) or any(k.arg is None for k in node.keywords):
                return "it passes open() unpacked arguments the guard cannot check"
            mode = node.args[1] if len(node.args) > 1 else next((k.value for k in node.keywords if k.arg == "mode"), None)
            if mode is not None:
                value = getattr(mode, "value", None) if isinstance(mode, ast.Constant) else None
                if not isinstance(value, str) or set(value) - set("rbt"):
                    if not constant_output(node.args[0] if node.args else None):
                        return "it opens a file for writing"
            if any(k.arg not in ("mode", "encoding", "errors", "newline") for k in node.keywords):
                return "it passes open() an argument the guard cannot check"
        elif extra_modules and isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            if any(k.arg == "allow_pickle" and not (isinstance(k.value, ast.Constant) and k.value.value is False)
                   for k in node.keywords):
                return "it loads with allow_pickle, which can run code"
            json_dump = attr == "dump" and isinstance(node.func.value, ast.Name) and bindings.get(node.func.value.id) == "json"
            if attr in IMAGE_OUTPUT_ATTRS and not json_dump:
                first = node.args[0] if node.args else next((k.value for k in node.keywords if k.arg in OUTPUT_FILE_KEYWORDS), None)
                if not constant_output(first):
                    return "it writes with .{} to a path outside its output directories".format(attr)
    return None


JS_BLOCKED_RE = re.compile(r"\b(require|import|process|child_process|fs|eval|Function|constructor|globalThis|global|Deno|Bun|module|"
                           r"exports|Reflect|Proxy|WebAssembly|fetch|Worker|spawn|exec)\b|__|\\x|\\u|\[\s*['\"`]")


def interpreter_kind(base):
    if re.match(r"^python(\d(\.\d+)?)?$", base):
        return "python"
    if base in ("node", "deno", "bun"):
        return "js"
    if base in ("perl", "ruby"):
        return base
    return None


INTERPRETER_CODE_FLAGS = {"python": ("-c",), "js": ("-e", "--eval", "-p", "--print"), "perl": ("-e", "-E"), "ruby": ("-e",)}


def interpreter_inputs(kind, argv, stdin=()):
    """(inline code parts, script operand or None) for an interpreter call. Code comes from -c or -e, or, when the
    interpreter reads its program on standard input (an operand '-', or no script operand and no -m), from the
    here-documents and here-strings it reads; a file redirected into it with < is its script operand."""
    flags = INTERPRETER_CODE_FLAGS[kind]
    code_parts = []
    for index, arg in enumerate(argv[1:], 1):
        if arg in flags and index + 1 < len(argv):
            code_parts.append(argv[index + 1])
        elif kind in ("perl", "ruby") and re.match(r"^-\w*[eE]$", arg) and index + 1 < len(argv):
            code_parts.append(argv[index + 1])
    if code_parts:
        return code_parts, None
    positional = [a for a in argv[1:] if not a.startswith("-")]
    first = argv.index(positional[0]) if positional else len(argv)
    if kind == "python" and "-m" in argv[1:first]:
        return [], None
    dash = argv.index("-", 1) if "-" in argv[1:] else None
    if positional and (dash is None or dash > first):
        return [], positional[0]
    texts = [value for what, value in stdin if what == "text"]
    files = [value for what, value in stdin if what == "file"]
    return texts, (files[0] if files and not texts else None)


def tool_write_reason(role, raw_path, root, cwd):
    if not raw_path:
        return None
    path = Path(raw_path.replace("\\", "/"))
    if not path.is_absolute():
        path = Path(cwd) / path
    words = ROLE_WORDS.get(role, "This agent")
    if role in READ_ONLY:
        return "{}, so the Edit and Write tools are blocked. Put what you found in your result or verdict instead of editing {}.".format(words, raw_path)
    if in_ledger_roots(path):
        return "{}. {} is the provenance ledger or a session transcript, which only drive's hooks and Claude Code write.".format(words, raw_path)
    if is_tmp_path(path, exclude=root):
        return None
    rel, _ = guard_rel(path, root, role)
    if rel is None:
        return "{}. {} is outside the project, so the edit is blocked. Write inside your allowed paths or under {}.".format(words, raw_path, scratch_words())
    if role in MAKERS:
        if rel == ".git" or rel.startswith(".git/"):
            return "{}. {} is git's own data; never edit it.".format(words, rel)
        if rel in frozen_test_paths(root):
            return ("{}. {} is a frozen test (a severe: refutation test or a test your package must make pass); make the code pass "
                    "it, and put a test you believe is wrong in your report.".format(words, rel))
        if rel.startswith(".drive/") and not (re.match(r"^\.drive/packages/[^/]+/report\.json$", rel) or rel.startswith(".drive/local/workers/")):
            return "{}. The orchestrator is the only writer of .drive/ state; put state changes in your report at .drive/packages/<id>/report.json instead of editing {}.".format(words, rel)
        return None
    if protected_evidence_rel(rel) and role not in ("ui-reviewer", "severe-tester"):
        return "{}. {} is evidence a reviewer writes through its own round.".format(words, rel)
    if role == "severe-tester":
        if severe_write_ok(rel):
            return None
        return ("{}. {} is not a test, fixture, or proof path the severe tester owns (under .drive/proofs/ only severe*.md, "
                "commands.log, and red/). Write the refutation as a test; report a needed product change in your result "
                "instead.".format(words, rel))
    if in_scope(rel, TOOL_WRITE_SCOPE.get(role, [])):
        return None
    return "{}. {} is outside that scope, so the edit is blocked. Describe the change in your result for the agent that owns the file.".format(words, rel)


def heredoc_body(text, index, word, strip_tabs):
    """Read one here-document body starting at text[index] (the start of the line after its operator): (body, index
    after the delimiter line). An unterminated body runs to the end, as in bash."""
    body, size = [], len(text)
    while index < size:
        end = text.find("\n", index)
        line = text[index:] if end < 0 else text[index:end]
        index = size if end < 0 else end + 1
        if (line.lstrip("\t") if strip_tabs else line).rstrip("\r") == word:
            break
        body.append(line)
    return "\n".join(body), index


def extract_paren(text, open_index):
    """Given text[open_index] == '(', return (inner text, index after the matching ')'). A here-document inside is
    skipped at the newline after its operator, so an apostrophe or parenthesis in its body does not unbalance the scan."""
    depth, index, quote, pending = 0, open_index, None, []
    while index < len(text):
        char = text[index]
        if quote:
            if char == "\\" and quote == '"':
                index += 2
                continue
            if char == quote:
                quote = None
        elif char in "'\"":
            quote = char
        elif char == "\\":
            index += 2
            continue
        elif text.startswith("<<<", index):
            index += 3
            continue
        elif text.startswith("<<", index) and heredoc_operator(text, index):
            word, strip_tabs, _, end = heredoc_operator(text, index)
            pending.append((word, strip_tabs))
            index = end
            continue
        elif char == "\n" and pending:
            index += 1
            for word, strip_tabs in pending:
                _, index = heredoc_body(text, index, word, strip_tabs)
            pending = []
            continue
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[open_index + 1:index], index + 1
        index += 1
    return text[open_index + 1:], len(text)


def heredoc_operator(command, index):
    """At command[index:] == '<<' (not '<<<'): (delimiter, strip leading tabs, delimiter quoted, index after the delimiter
    word), or None when no delimiter follows."""
    pos, size = index + 2, len(command)
    strip = pos < size and command[pos] == "-"
    if strip:
        pos += 1
    while pos < size and command[pos] in " \t":
        pos += 1
    word, quoted = "", False
    while pos < size and command[pos] not in " \t\r\n;&|<>()":
        char = command[pos]
        if char in "'\"":
            close = command.find(char, pos + 1)
            if close < 0:
                return None
            word += command[pos + 1:close]
            quoted = True
            pos = close + 1
            continue
        if char == "\\" and pos + 1 < size:
            word += command[pos + 1]
            quoted = True
            pos += 2
            continue
        word += char
        pos += 1
    return (word, strip, quoted, pos) if word else None


def heredoc_substitutions(body, depth):
    """The commands bash runs while expanding an unquoted here-document body: its $(...) and backtick substitutions."""
    out, index, size = [], 0, len(body)
    while index < size:
        char = body[index]
        if char == "\\":
            index += 2
            continue
        if body.startswith("$(", index):
            inner, index = extract_paren(body, index + 1)
            out.extend(split_shell_records(inner, depth + 1))
            continue
        if char == "`":
            end = body.find("`", index + 1)
            end = size if end < 0 else end
            out.extend(split_shell_records(body[index + 1:end], depth + 1))
            index = end + 1
            continue
        index += 1
    return out


def split_shell(command, depth=0):
    """The simple commands in a shell string (see split_shell_records)."""
    return [record["text"] for record in split_shell_records(command, depth)]


NO_EXPANSION = (-1, 0, False)


def split_shell_records(command, depth=0, outer=None):
    """Simple commands in a shell string, including those inside $(...), backticks, and subshells, each as
    {"text", "stdin", "upstream", "at", "nested", "grouped", "end", "piped"}. A here-document's body is data, not
    commands: after the line holding `<<WORD` (or <<'WORD', <<"WORD", <<-WORD), the lines up to the delimiter are skipped,
    several here-documents on one line in order, and an unterminated one runs to the end, as in bash. Each body is kept
    in "stdin" of the simple command that owns the operator, and "upstream" holds the bodies of the earlier commands in
    the same pipeline, so a shell or interpreter reading one can be judged for it. A here-string (<<<) is not a
    here-document. The command line itself, with its redirections, is still judged, and so are the $(...) and backtick
    substitutions bash expands in an unquoted body.

    "at" places a command in the top-level command line as (list, step, and_only): lists are separated by ;, a newline,
    or &, steps within a list by && and ||, and and_only says every step before it in its list was joined by &&. A newline
    right after &&, ||, or | continues the list. A command inside a substitution or subshell is "nested" and carries the
    place of the top-level step holding it (`outer`); one inside a { } group is "grouped"; "end" is the operator after it,
    and "piped" marks a member of a pipeline of two or more. Substitutions in a here-document body run when its command
    does, not where the body sits, so they carry NO_EXPANSION. Guard.check_command reads these places to decide whether a
    literal variable assignment has certainly run before a later use."""
    if depth > 8:
        return [{"text": command, "stdin": [], "upstream": [], "at": outer or NO_EXPANSION, "nested": True,
                 "grouped": False, "end": "", "piped": False}]
    segments, current, index, quote = [], [], 0, None
    size = len(command)
    pending = []
    state = {"bodies": [], "pipeline": []}
    pipelines = [state["pipeline"]]
    place = {"list": 0, "step": 0, "and_only": True, "last": ";", "fresh": True, "braces": 0}

    def at():
        return outer if outer is not None else (place["list"], place["step"], place["and_only"])

    def flush(connector=""):
        piece = "".join(current).strip()
        if piece:
            record = {"text": piece, "stdin": state["bodies"], "upstream": [], "at": at(), "nested": depth > 0,
                      "grouped": place["braces"] > 0, "end": connector, "piped": False}
            segments.append(record)
            state["pipeline"].append(record)
            place["fresh"] = False
        state["bodies"] = []
        current.clear()
        if connector != "|":
            state["pipeline"] = []
            pipelines.append(state["pipeline"])
        if not connector:
            return
        if connector == ";" and place["fresh"] and place["last"] in ("&&", "||", "|"):
            return
        if connector in (";", "&"):
            place.update(list=place["list"] + 1, step=0, and_only=True)
        elif connector in ("&&", "||"):
            place["step"] += 1
            place["and_only"] = place["and_only"] and connector == "&&"
        place.update(last=connector, fresh=True)

    while index < size:
        char = command[index]
        if quote == "'":
            current.append(char)
            if char == "'":
                quote = None
            index += 1
            continue
        if char == "\\" and index + 1 < size:
            current.append(command[index:index + 2])
            index += 2
            continue
        if quote == '"':
            if char == '"':
                quote = None
                current.append(char)
                index += 1
                continue
            if command.startswith("$(", index):
                inner, index = extract_paren(command, index + 1)
                segments.extend(split_shell_records(inner, depth + 1, at()))
                current.append("SUBST")
                continue
            if char == "`":
                end = command.find("`", index + 1)
                end = size if end < 0 else end
                segments.extend(split_shell_records(command[index + 1:end], depth + 1, at()))
                current.append("SUBST")
                index = end + 1
                continue
            current.append(char)
            index += 1
            continue
        if char in "'\"":
            quote = char
            current.append(char)
            index += 1
            continue
        if command.startswith("<<<", index):
            # A here-string: its word is an ordinary argument, and nothing on the following lines is its body.
            current.append("<<<")
            index += 3
            continue
        if command.startswith("<<", index):
            found = heredoc_operator(command, index)
            if found:
                word, strip_tabs, quoted, end = found
                current.append(command[index:end])
                pending.append((word, strip_tabs, quoted, state["bodies"]))
                index = end
                continue
        if command.startswith(("$(", "<(", ">("), index):
            inner, index = extract_paren(command, index + 1)
            segments.extend(split_shell_records(inner, depth + 1, at()))
            current.append("SUBST")
            continue
        if char == "(":
            inner, index = extract_paren(command, index)
            flush()
            segments.extend(split_shell_records(inner, depth + 1, at()))
            place["fresh"] = False
            continue
        if char == "`":
            end = command.find("`", index + 1)
            end = size if end < 0 else end
            segments.extend(split_shell_records(command[index + 1:end], depth + 1, at()))
            current.append("SUBST")
            index = end + 1
            continue
        if char in ";\n":
            flush(";")
            index += 1
            if char == "\n":
                while pending:
                    word, strip_tabs, quoted, owner = pending.pop(0)
                    body, index = heredoc_body(command, index, word, strip_tabs)
                    owner.append(body)
                    if not quoted:
                        for record in heredoc_substitutions(body, depth):
                            record["at"] = NO_EXPANSION
                            segments.append(record)
            continue
        if char == "&":
            before = command[index - 1] if index else ""
            after = command[index + 1] if index + 1 < size else ""
            if before in "<>" or after == ">":
                current.append(char)
                index += 1
            elif after == "&":
                flush("&&")
                index += 2
            else:
                flush("&")
                index += 1
            continue
        if char == "|":
            before = command[index - 1] if index else ""
            if before == ">":
                current.append(char)
                index += 1
            elif command.startswith("||", index):
                flush("||")
                index += 2
            else:
                flush("|")
                index += 2 if command.startswith("|&", index) else 1
            continue
        if char in "{}" and (index == 0 or command[index - 1] in " \t;&|\n") and (index + 1 >= size or command[index + 1] in " \t;\n"):
            flush()
            place["braces"] = place["braces"] + 1 if char == "{" else max(0, place["braces"] - 1)
            place["fresh"] = False
            index += 1
            continue
        if char == "#" and (index == 0 or command[index - 1] in " \t\n;&|"):
            end = command.find("\n", index)
            index = size if end < 0 else end
            continue
        current.append(char)
        index += 1
    flush()
    for pipeline in pipelines:
        for position, record in enumerate(pipeline):
            record["upstream"] = [body for earlier in pipeline[:position] for body in earlier["stdin"]]
            record["piped"] = len(pipeline) > 1
    return segments


def shell_words(segment):
    """Split one simple command into words (quotes removed) and redirections [(operator, target)]."""
    words, redirects = [], []
    current, has, quote, pending = "", False, None, None
    index, size = 0, len(segment)

    def push():
        nonlocal current, has, pending
        if has:
            if pending is not None:
                redirects.append((pending, current))
                pending = None
            else:
                words.append(current)
        current, has = "", False

    while index < size:
        char = segment[index]
        if quote:
            if char == quote:
                quote = None
            elif char == "\\" and quote == '"' and index + 1 < size and segment[index + 1] in '"\\$`':
                current += segment[index + 1]
                index += 1
            else:
                current += char
            index += 1
            continue
        if char in "'\"":
            quote, has = char, True
            index += 1
            continue
        if char == "\\" and index + 1 < size:
            current += segment[index + 1]
            has = True
            index += 2
            continue
        if char in " \t\r\n":
            push()
            index += 1
            continue
        if char in "<>":
            if has and re.fullmatch(r"\d+|&", current):
                current, has = "", False
            else:
                push()
            end = index
            while end < size and segment[end] in "<>|&":
                end += 1
            pending = segment[index:end]
            index = end
            continue
        current += char
        has = True
        index += 1
    push()
    return words, redirects


ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
# A value the guard substitutes for a later $NAME: no spaces, quotes, globs, tildes, or expansions, so pasting it into the
# command text reads exactly as bash's expansion of it would.
LITERAL_VALUE_RE = re.compile(r"^[A-Za-z0-9_./@%+=:,-]+$")
SHELL_KEYWORDS = {"if", "then", "else", "elif", "do", "while", "until", "!", "fi", "done", "esac"}
BLOCK_OPENERS = {"if", "while", "until", "for", "select", "case"}
BLOCK_CLOSERS = {"fi", "done", "esac"}
VARIABLE_BINDERS = {"read", "unset", "export", "declare", "typeset", "local", "readonly", "getopts", "mapfile", "readarray",
                    "printf", "for", "select", "let"}
AWK_REGEX_START = {"", "(", "{", "}", ",", ";", "!", "~", "&", "|", "?", ":", "=", "\n"}


def assignment_reaches(assigned, used):
    """Whether an assignment at place `assigned` has certainly run whenever a command at place `used` runs, with places
    as split_shell_records gives them. The first step of a list always runs, so it reaches everything after it; a later
    step reaches only the later steps of its own list, and only when every step from the list's start was joined by &&."""
    if assigned[0] < 0 or used[0] < 0 or tuple(used[:2]) <= tuple(assigned[:2]):
        return False
    if assigned[1] == 0:
        return True
    return used[0] == assigned[0] and bool(used[2])


def expand_literal_variables(text, values):
    """`text` with each $NAME and ${NAME} whose NAME is in `values` replaced by its literal value, where bash would expand
    it: outside single quotes and not after a backslash. Every other expansion is left as written, and stays unknowable."""
    out, index, size, quote = [], 0, len(text), None
    while index < size:
        char = text[index]
        if quote == "'":
            out.append(char)
            if char == "'":
                quote = None
            index += 1
            continue
        if char == "\\" and index + 1 < size:
            out.append(text[index:index + 2])
            index += 2
            continue
        if char in "'\"":
            if char == "'" and quote is None:
                quote = "'"
            elif char == '"':
                quote = None if quote == '"' else '"'
            out.append(char)
            index += 1
            continue
        if char == "$":
            match = re.match(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))", text[index:])
            name = (match.group(1) or match.group(2)) if match else None
            if name in values:
                out.append(values[name])
                index += match.end()
                continue
        out.append(char)
        index += 1
    return "".join(out)


def update_literal_variables(known, record, words, in_block):
    """After one simple command, remember the literal assignments later commands in the same command line may rely on
    ({name: (value, place)}), and forget every variable the command may bind any other way. An assignment counts only as
    a command of its own at the top level: not inside a substitution, subshell, { } group, if, loop, or case, not in a
    pipeline or backgrounded, and with a value holding no $, backtick, or substitution. A prefix assignment (S=x cmd),
    export, read, unset, a for variable, and the like make the name unknowable; eval, source, and . forget them all."""
    rest = list(words)
    while rest and rest[0] in SHELL_KEYWORDS:
        rest = rest[1:]
    if rest and all(ASSIGNMENT_RE.match(word) for word in rest):
        certain = not (in_block or record.get("nested") or record.get("grouped") or record.get("piped")
                       or record.get("end") == "&" or any(mark in record["text"] for mark in ("$", "`", "SUBST")))
        for word in rest:
            name, value = word.split("=", 1)
            if certain and LITERAL_VALUE_RE.match(value):
                known[name] = (value, record.get("at") or NO_EXPANSION)
            else:
                known.pop(name, None)
        return
    base = os.path.basename(rest[0]) if rest else ""
    if base in ("eval", "source", "."):
        known.clear()
        return
    for name in list(known):
        if any(re.match(r"^{}(\+?=|\[)".format(name), word) for word in words) or (base in VARIABLE_BINDERS and name in words):
            known.pop(name)


def awk_program_without_literals(program):
    """The awk program with each string literal emptied to "" and each regular-expression literal to //, so a > or | in
    quoted text ("x > 0") is not read as output redirection or a pipe. A / opens a regex literal where an operand starts
    (at the beginning, or after one of ( { } , ; ! ~ & | ? : = or a newline) and is division elsewhere. An unterminated
    literal is left as written, so the rest of the program is still matched."""
    out, index, size, last = [], 0, len(program), ""
    while index < size:
        char = program[index]
        if char == '"' or (char == "/" and last in AWK_REGEX_START):
            end, bracket = index + 1, False
            while end < size:
                inner = program[end]
                if inner == "\\":
                    end += 2
                    continue
                if inner == "\n":
                    break
                if char == "/" and inner == "[":
                    bracket = True
                elif char == "/" and inner == "]":
                    bracket = False
                elif inner == char and not bracket:
                    break
                end += 1
            if end >= size or program[end] != char:
                out.append(program[index:])
                break
            out.append(char * 2)
            last = char
            index = end + 1
            continue
        out.append(char)
        if char == "\n" or not char.isspace():
            last = char
        index += 1
    return "".join(out)


SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "fish"}
INTERPRETERS = {"python", "python3", "node", "ruby", "perl", "deno", "bun"}
GIT_READ_ONLY = {"status", "log", "diff", "show", "rev-parse", "ls-files", "ls-tree", "blame", "grep", "archive",
                 "cat-file", "describe", "merge-base", "rev-list", "shortlog", "for-each-ref", "name-rev",
                 "check-ignore", "version", "help", "count-objects", "fsck", "whatchanged", "show-ref", "var",
                 "cherry", "range-diff", "diff-tree", "diff-files", "diff-index", "verify-commit", "verify-tag",
                 "annotate", "check-attr", "ls-remote", "show-branch", "get-tar-commit-id", "--version", "--help"}
GIT_WORKER_BLOCKED = {"add", "commit", "push", "checkout", "switch", "reset", "stash", "rebase", "merge", "worktree",
                      "cherry-pick", "revert", "am", "pull", "clean", "rm", "mv", "update-ref", "filter-branch",
                      "filter-repo", "replace", "commit-tree", "fast-import", "bisect", "update-index", "read-tree",
                      "checkout-index", "restore", "gc", "prune"}
GIT_OPTIONS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env", "--super-prefix"}
DEPLOY_PATTERNS = [
    (("npm", "pnpm", "yarn", "bun"), re.compile(r"^(publish|deploy)$")),
    (("cargo",), re.compile(r"^(publish|yank|owner)$")),
    (("twine",), re.compile(r"^upload$")),
    (("gem",), re.compile(r"^(push|yank)$")),
    (("pod",), re.compile(r"^trunk$")),
    (("fastlane",), re.compile(r".*")),
    (("netlify", "firebase", "fly", "flyctl", "heroku", "surge"), re.compile(r"^(deploy|release|push|apps:destroy)$")),
    (("vercel",), re.compile(r"^(deploy|--prod|promote|rollback|remove|rm)$")),
    (("terraform", "tofu"), re.compile(r"^(apply|destroy|import|taint)$")),
    (("pulumi",), re.compile(r"^(up|destroy|refresh)$")),
    (("kubectl",), re.compile(r"^(apply|create|delete|replace|patch|scale|rollout|edit|set|annotate|label)$")),
    (("helm",), re.compile(r"^(install|upgrade|uninstall|rollback|delete)$")),
    (("docker", "podman"), re.compile(r"^push$")),
    (("mvn",), re.compile(r"^deploy$")),
    (("gradle", "gradlew", "./gradlew"), re.compile(r"^publish")),
    (("dotnet",), re.compile(r"^nuget$")),
]


def deploy_reason(argv):
    base = os.path.basename(argv[0])
    rest = [a for a in argv[1:] if not a.startswith("-")] or argv[1:]
    if base == "wrangler":
        joined = " ".join(a for a in argv[1:] if not a.startswith("--"))
        if re.search(r"^(deploy|publish|rollback|delete)\b|^pages (deploy|project delete)|^versions (deploy|upload)|^secret (put|delete|bulk)|"
                     r"^kv (key|namespace) (put|delete)|^kv:key (put|delete)|^r2 (object (put|delete)|bucket delete)|^d1 (migrations apply|delete)|"
                     r"^queues (create|delete)|^triggers deploy", joined):
            if "d1 migrations apply" in joined and "--local" in argv:
                return None
            return "wrangler {}".format(joined.split(" ")[0])
        return None
    if base == "gh":
        joined = " ".join(argv[1:3])
        if re.match(r"^(pr (create|merge|close|comment|review|edit)|release (create|upload|delete|edit)|repo (create|delete|edit|rename)|issue (create|comment|close|edit)|workflow run|secret (set|delete))", joined):
            return "gh " + joined
        if len(argv) > 1 and argv[1] == "api" and re.search(r"(?i)(-X|--method)\s*(POST|PUT|PATCH|DELETE)", " ".join(argv)):
            return "gh api with a write method"
        return None
    if base == "xcrun" and len(argv) > 1 and argv[1] in ("altool", "notarytool"):
        return "xcrun " + argv[1]
    if base in ("aws",) and len(argv) > 2 and argv[1] in ("s3", "lambda", "cloudformation", "ecs") and \
            re.match(r"^(cp|sync|rm|mv|deploy|update-function-code|update-service|create-stack|delete-stack|put-object)$", argv[2]):
        return "aws {} {}".format(argv[1], argv[2])
    if base == "gcloud" and re.search(r"\b(deploy|delete)\b", " ".join(argv[1:])):
        return "gcloud deploy or delete"
    for names, pattern in DEPLOY_PATTERNS:
        if base in names and rest and pattern.match(rest[0]):
            return "{} {}".format(base, rest[0])
    return None


def strip_wrappers(words):
    argv = list(words)
    while argv:
        head = os.path.basename(argv[0])
        if ASSIGNMENT_RE.match(argv[0]):
            argv = argv[1:]
        elif head in ("if", "then", "else", "elif", "do", "while", "until", "!", "fi", "done", "esac"):
            argv = argv[1:]
        elif head in ("for", "select"):
            # `for NAME in WORDS` runs nothing itself: its substitutions and body are simple commands of their own.
            return []
        elif head in ("npx", "bunx") or (head in ("pnpm", "yarn", "bun") and len(argv) > 1 and argv[1] in ("dlx", "exec", "x")) \
                or (head == "npm" and len(argv) > 1 and argv[1] in ("exec", "x")):
            argv = argv[1:] if head in ("npx", "bunx") else argv[2:]
            while argv and argv[0].startswith("-"):
                argv = argv[2:] if argv[0] in ("-p", "--package", "-c", "--call") else argv[1:]
        elif head in ("sudo", "doas"):
            argv = argv[1:]
            while argv and argv[0].startswith("-"):
                takes = argv[0] in ("-u", "-g", "-C", "-h", "-p")
                argv = argv[2:] if takes else argv[1:]
        elif head == "env":
            argv = argv[1:]
            while argv and (argv[0].startswith("-") or ASSIGNMENT_RE.match(argv[0])):
                if argv[0] in ("-S", "--split-string") and len(argv) > 1:
                    argv = shell_words(argv[1])[0] + argv[2:]
                    continue
                argv = argv[2:] if argv[0] in ("-u", "--unset", "-C", "--chdir") else argv[1:]
        elif head in ("command", "builtin"):
            if len(argv) > 1 and argv[1] in ("-v", "-V"):
                return []
            argv = argv[1:]
        elif head in ("exec", "nohup", "time", "noglob", "unbuffer", "chronic"):
            argv = argv[1:]
            while argv and argv[0].startswith("-"):
                argv = argv[1:]
        elif head in ("nice", "ionice", "stdbuf", "caffeinate", "watch", "flock", "timeout", "gtimeout", "xargs"):
            argv = argv[1:]
            with_value = {"nice": {"-n"}, "ionice": {"-c", "-n"}, "caffeinate": {"-t", "-w"}, "watch": {"-n", "-d"},
                          "timeout": {"-s", "-k", "--signal", "--kill-after"}, "gtimeout": {"-s", "-k"},
                          "xargs": {"-I", "-n", "-P", "-L", "-s", "-d", "-E", "-a", "-J", "-R"}, "flock": {"-w", "-E"},
                          "stdbuf": set()}.get(head, set())
            while argv and argv[0].startswith("-"):
                argv = argv[2:] if argv[0] in with_value else argv[1:]
            if head in ("timeout", "gtimeout") and argv:
                argv = argv[1:]
            if head == "flock" and argv:
                argv = argv[1:]
        else:
            break
    return argv


def severe_write_ok(rel):
    """The severe tester writes test files and fixtures in the project, and under .drive/proofs/ only its own record:
    severe*.md, commands.log, and red/ output. Verdicts, proofs, refutations, audits, and citations are other agents'."""
    if rel is None:
        return False
    if rel.startswith(".drive/"):
        if not rel.startswith(".drive/proofs/"):
            return False
        name = rel.rsplit("/", 1)[-1]
        if name in ("verdict.json", "proof.json") or name.startswith("refute-") or "final-audit" in name or "-citations-" in name:
            return False
        return (name.startswith("severe") and name.endswith(".md")) or name == "commands.log" or "/red/" in rel
    return is_test_path(rel)


REVIEWER_PY_MODULES = {"unittest", "pytest", "json.tool"}


def formatter_write_reason(base, argv):
    """The write form of a formatter or linter a reviewer might run (None for its check form)."""
    args = argv[1:]
    if any(a in ("--version", "-V", "--help", "-h") for a in args):
        return None
    positional = [a for a in args if not a.startswith("-")]

    def flag(*names):
        return any(a in names or any(n.startswith("--") and a.startswith(n + "=") for n in names) for a in args)
    if base == "prettier" and flag("--write", "-w"):
        return "prettier --write"
    if base == "eslint" and flag("--fix"):
        return "eslint --fix"
    if base == "ruff":
        if flag("--fix") and not flag("--no-fix"):
            return "ruff --fix"
        if positional[:1] == ["format"] and not flag("--check", "--diff"):
            return "ruff format without --check"
    if base == "black" and not flag("--check", "--diff"):
        return "black without --check"
    if base == "gofmt" and flag("-w"):
        return "gofmt -w"
    if base == "golangci-lint" and flag("--fix"):
        return "golangci-lint --fix"
    if base == "swiftlint" and (flag("--fix", "--autocorrect") or positional[:1] == ["autocorrect"]):
        return "swiftlint --fix"
    if base == "cargo":
        if positional[:1] == ["fmt"] and not flag("--check"):
            return "cargo fmt without --check"
        if positional[:1] == ["clippy"] and flag("--fix"):
            return "cargo clippy --fix"
    if base == "go" and positional[:1] == ["fmt"]:
        return "go fmt"
    return None


def code_literals(kind, code):
    """The string literals in inline code: every str constant for Python, quoted runs for the others."""
    if kind == "python":
        try:
            tree = ast.parse(code)
        except (SyntaxError, ValueError):
            tree = None
        if tree is not None:
            return [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    return [m.group(2) for m in re.finditer(r"(['\"`])((?:\\.|(?!\1).)*)\1", code)]


GH_WRITE_RE = re.compile(r"^(pr (create|merge|close|comment|review|edit|ready|reopen)|release (create|upload|delete|edit|delete-asset)|"
                         r"repo (create|delete|edit|rename|archive|unarchive|fork|sync|set-default|deploy-key))$")


def goal_records_deploy(root, command_words):
    """True when GOAL.md's plan has a deploy line naming this command (for example `gh release create`)."""
    text = read_text(Path(root) / ".drive" / "GOAL.md")
    if not text:
        return False
    for _, line in Goal(text).plan:
        match = PLAN_RE.match(line)
        if match and match.group("phase") == "deploy" and command_words in re.sub(r"\s+", " ", line):
            return True
    return False


def ref_change(sub, args):
    """What a git command does to branches or tags (None when it changes neither)."""
    positional = [a for a in args if not a.startswith("-")]
    if sub in ("checkout", "switch"):
        if any(a in ("-b", "-B", "--orphan", "-c", "-C", "--create", "--force-create") or re.match(r"^-[bBcC].", a)
               or a.startswith(("--create=", "--force-create=", "--orphan=")) for a in args):
            return "'git {}' creating a branch".format(sub)
    if sub == "branch" and not Guard.git_read_only(sub, args):
        flags = [a for a in args if a.startswith("-")]
        deleting = any(a in ("-d", "-D", "--delete") or re.match(r"^-[^-]*[dD]", a) for a in flags)
        if not deleting or any(a in ("-f", "--force", "-m", "-M", "--move", "-c", "-C", "--copy") for a in flags):
            return "'git branch {}'".format(" ".join(args)[:60])
    if sub == "update-ref" and ("--stdin" in args or any(p.startswith("refs/heads/") or p.startswith("refs/tags/") for p in positional)):
        return "'git update-ref' on a branch or tag"
    if sub == "symbolic-ref" and len(positional) >= 2:
        return "'git symbolic-ref' moving HEAD"
    if sub == "tag" and not Guard.git_read_only(sub, args):
        return "'git tag {}'".format(" ".join(args)[:60])
    return None


class Guard:
    def __init__(self, role, root, cwd):
        self.role = role
        self.root = Path(root)
        self.cwd = Path(cwd or root)
        self.depth = 0

    # path helpers
    def resolve(self, raw, cwd):
        if raw.startswith("~"):
            raw = os.path.expanduser(raw)
        path = Path(raw)
        return path if path.is_absolute() else Path(cwd) / path

    def unknowable(self, raw):
        return "$" in raw or "SUBST" in raw or "`" in raw

    def write_ok(self, raw, cwd, deleting=False):
        if raw in ("/dev/null", "/dev/stdout", "/dev/stderr", "/dev/tty", "-") or raw.startswith("/dev/fd/"):
            return True
        if self.role == "orchestrator":
            return self.orchestrator_write_ok(raw, cwd, deleting)
        if self.unknowable(raw):
            return False
        path = self.resolve(raw, cwd)
        if in_ledger_roots(path):
            return False
        if is_tmp_path(path, exclude=self.root):
            return True
        if self.role in MAKERS:
            return self.maker_write_ok(path, deleting)
        if self.role in READ_ONLY or self.role == "ui-reviewer":
            if deleting:
                return False
            return in_scope(rel_in_root(path, self.root), BASH_WRITE_SCOPE[self.role])
        rel, _ = guard_rel(path, self.root, self.role)
        if rel is None:
            return False
        if in_scope(rel, [".drive/local/"]) and not rel.startswith(".drive/local/ro/"):
            return True
        if self.role == "severe-tester":
            return severe_write_ok(rel)
        return in_scope(rel, TOOL_WRITE_SCOPE.get(self.role, [])) and not protected_evidence_rel(rel)

    def maker_write_ok(self, path, deleting):
        rel, base = guard_rel(path, self.root, self.role)
        if rel is None:
            return False
        if rel in ("", ".") or rel == ".git" or rel.startswith(".git/"):
            return False
        if rel in frozen_test_paths(self.root):
            return False
        if rel == ".drive" or rel.startswith(".drive/"):
            return rel.startswith(".drive/local/workers/") or bool(re.match(r"^\.drive/packages/[^/]+/report\.json$", rel))
        if realpath_loose(base) != realpath_loose(self.root):
            return True
        owned = self.owned_globs()
        return not owned or any(glob_matches(rel, g) for g in owned)

    def owned_globs(self):
        """Every path any package brief owns. A maker's shell writes stay inside the packages' ownership."""
        if not hasattr(self, "_owned"):
            self._owned = []
            folder = self.root / ".drive" / "packages"
            if folder.is_dir():
                for brief in sorted(folder.glob("*/brief.md")):
                    self._owned.extend(g for g in globs_under(read_text(brief) or "", "## Files you own") if not PLACEHOLDER_RE.search(g))
        return self._owned

    def orchestrator_write_ok(self, raw, cwd, deleting):
        """The main thread may write anything except reviewer evidence, void markers, and the ledger, and may
        not delete or move proofs or reviews."""
        if self.unknowable(raw):
            return not EVIDENCE_MARKERS.search(raw)
        path = self.resolve(raw, cwd)
        if in_ledger_roots(path):
            return False
        rel = rel_in_root(path, self.root)
        if rel is None:
            return True
        if deleting:
            guarded = (".drive/proofs", ".drive/reviews", ".drive/local/ro")
            if rel in ("", ".", ".drive") or any(rel == g or rel.startswith(g + "/") for g in guarded):
                return False
            return True
        return not protected_evidence_rel(rel) and rel not in frozen_test_paths(self.root)

    @property
    def restricted_paths(self):
        return True

    def scope_words(self):
        scratch = scratch_words()
        if self.role == "orchestrator":
            return "anywhere except reviewer evidence under .drive/proofs/ and .drive/reviews/, frozen tests, and the provenance ledger"
        if self.role in MAKERS:
            owned = self.owned_globs()
            return "in the packages' owned paths ({}), .drive/local/workers/, a package report, or {}".format(
                ", ".join(owned[:6]), scratch) if owned else "inside the project (not .git/, .drive/ state, or frozen tests) or {}".format(scratch)
        if self.role in READ_ONLY or self.role == "ui-reviewer":
            return "under {} or {}".format(", ".join(BASH_WRITE_SCOPE[self.role]), scratch)
        if self.role == "severe-tester":
            return "in test paths, fixtures, severe*.md, commands.log, or red/ under .drive/proofs/, .drive/local/, or {}".format(scratch)
        return "under {}, .drive/local/, or {}".format(", ".join(TOOL_WRITE_SCOPE.get(self.role, [])), scratch)

    # analysis
    def check_command(self, command, cwd=None, script=False):
        self.depth += 1
        if self.depth > 12:
            return "The command nests shells too deeply for the drive guard to check. Run the steps as separate plain commands."
        cwd = Path(cwd or self.cwd)
        # The orchestrator's own scripts are checked like its commands; for agents a project script's
        # writes are the project's, and only its git, deploy, and hook calls are checked.
        paths_checked = self.restricted_paths and (not script or self.role == "orchestrator")
        # NAME=<literal> earlier in the same command line is substituted into later commands it has certainly reached
        # (S=/tmp/x && mkdir -p "$S"); if, while, until, for, select, and case bodies are tracked so an assignment inside
        # one, which may not run, is never relied on.
        known, block = {}, 0
        for record in split_shell_records(command):
            place = record.get("at") or NO_EXPANSION
            values = {name: value for name, (value, assigned) in known.items() if assignment_reaches(assigned, place)}
            words, redirects = shell_words(expand_literal_variables(record["text"], values) if values else record["text"])
            head = words[0] if words else ""
            in_block = block > 0 or head in BLOCK_OPENERS
            if head in BLOCK_OPENERS:
                block += 1
            elif head in BLOCK_CLOSERS:
                block = max(0, block - 1)
            update_literal_variables(known, record, words, in_block)
            argv = strip_wrappers(words)
            stdin = self.stdin_inputs(record, redirects)
            reason = self.frozen_reason(argv, redirects, cwd, stdin)
            if reason:
                return reason
            if paths_checked:
                for operator, target in redirects:
                    if ">" in operator and not re.fullmatch(r"&?\d+|&?-", target):
                        if not self.write_ok(target, cwd):
                            return "{}. Redirecting output into {} is a write outside its scope; write {} instead.".format(
                                ROLE_WORDS[self.role], target, self.scope_words())
            if not argv:
                continue
            reason = self.check_argv(argv, cwd, script, stdin)
            if reason:
                return reason
            if argv[0] == "cd":
                target = argv[1] if len(argv) > 1 else os.path.expanduser("~")
                cwd = self.resolve(target, cwd) if not self.unknowable(target) else Path("/nonexistent-dynamic-cd")
        return None

    GIT_MUTATION_RE = re.compile(r"""(?i)['"]git['"]\s*,\s*['"](commit|push|reset|checkout|switch|rebase|merge|stash|add|worktree|branch|restore|clean|cherry-pick|revert|tag|update-ref)['"]|\bgit\s+(-C\s+\S+\s+|-c\s+\S+\s+)*(commit|push|reset|checkout|switch|rebase|merge|stash|worktree|add|restore|clean|cherry-pick|revert|update-ref)\b""")
    DEPLOY_TEXT_RE = re.compile(r"(?i)\b(wrangler\s+(deploy|publish|pages\s+deploy|versions\s+deploy|secret\s+put)|(npm|pnpm|yarn|bun)\s+publish|"
                                r"cargo\s+publish|twine\s+upload|gh\s+(release\s+create|pr\s+(create|merge))|terraform\s+(apply|destroy)|"
                                r"kubectl\s+(apply|delete)|docker\s+push|fastlane\b|vercel\s+(deploy|--prod))")

    def hook_call_reason(self, argv):
        for arg in argv:
            if HOOK_ARG_RE.match(arg):
                return ("{}. '{}' is a drive hook subcommand, run only by Claude Code's hooks; calling it by hand, under any "
                        "script name, would forge the provenance ledger or the Stop gate's records.".format(ROLE_WORDS[self.role], arg))
        return None

    @staticmethod
    def stdin_inputs(record, redirects):
        """What a simple command reads on standard input: [("text", body)] for its here-documents and here-strings, or
        [("file", path)] for a < redirect; with none of its own, the here-document bodies of earlier commands in its
        pipeline (cat <<'EOF' | bash)."""
        own = [("text", body) for body in record.get("stdin") or []]
        for operator, target in redirects:
            if operator == "<<<":
                own.append(("text", target))
            elif operator == "<":
                own.append(("file", target))
        return own or [("text", body) for body in record.get("upstream") or []]

    def shell_stdin_reason(self, base, stdin, cwd, script):
        """A shell with no script operand runs what it reads on standard input: judge a here-document or here-string as
        bash -c would be judged, and a redirected file as bash <file> would be."""
        for kind, value in stdin:
            if kind == "text":
                reason = self.check_command(value, cwd, script)
            else:
                if value == "/dev/null":
                    continue
                path = None if self.unknowable(value) else self.resolve(value, cwd)
                text = small_file_text(path, 256_000) if path is not None else None
                if text is None:
                    return ("{}. '{} < {}' runs a script the guard cannot read (missing, named through a variable, or 256 KB "
                            "or larger), so it is refused while a drive run is active. Run the commands directly, or pass a "
                            "readable script as '{} <file>'.".format(ROLE_WORDS[self.role], base, value[:60], base))
                reason = self.check_command(text, cwd, script=True)
            if reason:
                return reason
        return None

    def check_argv(self, argv, cwd, script, stdin=()):
        base = os.path.basename(argv[0])
        words = ROLE_WORDS[self.role]
        reason = self.hook_call_reason(argv)
        if reason:
            return reason
        if self.unknowable(argv[0]) and self.role != "orchestrator":
            return ("{}. '{}' takes its command name from a variable or a substitution, so the guard cannot see what runs. "
                    "Write the command name out.".format(words, argv[0][:40]))
        if base in SHELLS:
            skip = False
            for index, arg in enumerate(argv[1:], 1):
                if skip:
                    skip = False
                    continue
                if arg in ("-o", "+o", "-O", "+O", "--rcfile", "--init-file"):
                    skip = True
                    continue
                if arg.startswith("-") and not arg.startswith("--") and "c" in arg[1:]:
                    if index + 1 < len(argv):
                        return self.check_command(argv[index + 1], cwd, script)
                    return None
                if arg.startswith("-") and not arg.startswith("--") and "s" in arg[1:]:
                    break
                if not arg.startswith(("-", "+")):
                    return self.check_script(arg, cwd)
            return self.shell_stdin_reason(base, stdin, cwd, script)
        if base in ("eval",):
            return self.check_command(" ".join(argv[1:]), cwd, script)
        if base in ("source", "."):
            return self.check_script(argv[1], cwd) if len(argv) > 1 else None
        if self.role in READ_ONLY or self.role == "ui-reviewer":
            handled, reason = self.reviewer_shape(base, argv, cwd, script)
            if handled:
                return reason
        kind = interpreter_kind(base)
        if kind:
            return self.check_interpreter(kind, base, argv, cwd, script, stdin)
        if base == "find":
            reason = self.check_find(argv, cwd, script)
            if reason:
                return reason
        if self.role == "orchestrator":
            if base == "git":
                return self.orchestrator_git(argv, cwd)
            if base == "gh":
                reason = self.gh_reason(argv)
                if reason:
                    return reason
            return self.check_file_command(base, argv, cwd)
        deploy = deploy_reason(argv)
        if deploy:
            return "{}, and no drive agent deploys or publishes. '{}' is blocked; the orchestrator runs deploys and records them.".format(words, deploy)
        reason = self.check_package_script(base, argv, cwd) or self.check_make(base, argv, cwd)
        if reason:
            return reason
        if base == "git":
            return self.check_git(argv, cwd)
        if script or not self.restricted_paths:
            return None
        return self.check_file_command(base, argv, cwd)

    def check_interpreter(self, kind, base, argv, cwd, script, stdin=()):
        words = ROLE_WORDS[self.role]
        code_parts, operand = interpreter_inputs(kind, argv, stdin)
        code = "\n".join(code_parts)
        script_path = None
        if operand is not None:
            script_path = self.resolve(operand, cwd) if not self.unknowable(operand) else None
        text = code
        if script_path is not None and is_file_quietly(script_path):
            try:
                text = read_text(script_path) if script_path.stat().st_size < 256_000 else ""
            except OSError:
                text = ""
            text = text or ""
        if script_path is not None and is_within(realpath_loose(script_path), realpath_loose(SKILL_DIR)):
            return None
        if self.role == "orchestrator":
            if text and EVIDENCE_MARKERS.search(text):
                return ("{}. The {} it runs names reviewer evidence or the ledger; read evidence with cat or drive.py lint, "
                        "and let the reviewer write it. To change a state file whose text mentions those paths, such as GOAL.md's plan, "
                        "use the Edit tool.".format(words, "script" if script_path else "code"))
            return None
        if text and self.GIT_MUTATION_RE.search(text):
            return "{}. The {} run by {} runs a git command that changes the repository. Leave git to the orchestrator.".format(
                words, "script" if script_path else "code", base)
        if text and self.DEPLOY_TEXT_RE.search(text):
            return "{}, and no drive agent deploys or publishes. The {} run by {} deploys or publishes.".format(
                words, "script" if script_path else "code", base)
        if kind in ("perl", "ruby") and any(re.match(r"^-\w*i", a) for a in argv[1:]) and not script:
            operands = [a for a in argv[1:] if not a.startswith("-") and a not in code_parts]
            for target in operands or ["."]:
                if not self.write_ok(target, cwd):
                    return "{}. {} -i edits {} in place, which is outside its scope; write only {}.".format(words, base, target, self.scope_words())
        if self.role not in INLINE_CHECKED:
            return None
        scratch = script_path is not None and (is_tmp_path(script_path, exclude=self.root)
                                               or in_scope(rel_in_root(script_path, self.root), [".drive/"]))
        if not code_parts and not scratch:
            return None
        body = code if code_parts else text
        if kind == "python":
            if self.role == "ui-reviewer":
                def image_write_ok(raw, _cwd=cwd):
                    return in_scope(rel_in_root(self.resolve(raw, _cwd), self.root), [".drive/proofs/", ".drive/local/ui/"])
                why = python_code_reason(body, write_ok=image_write_ok, extra_modules=IMAGE_MODULES | NUMPY_MODULES)
            else:
                why = python_code_reason(body)
        elif kind == "js":
            found = JS_BLOCKED_RE.search(body)
            why = "it uses {}".format(found.group(0)) if found else None
        else:
            why = "inline {} can write any file".format(kind)
        if why:
            return ("{}. The {} passed to {} could write, delete, or run something ({}), and the guard cannot confine it to "
                    "{}. Use a read-only one-liner, a shell redirect into your own output path, or the project's own test "
                    "command.".format(words, "inline code" if code_parts else "scratch script", base, why, self.scope_words()))
        return None

    def check_package_script(self, base, argv, cwd):
        """npm, pnpm, yarn, and bun run a package.json script; check its body (and its pre and post scripts)."""
        if base not in ("npm", "pnpm", "yarn", "bun") or len(argv) < 2:
            return None
        rest = [a for a in argv[1:] if not a.startswith("-")]
        if not rest:
            return None
        name = None
        if rest[0] in ("run", "run-script", "rum", "urn") and len(rest) > 1:
            name = rest[1]
        elif base == "npm" and rest[0] in ("start", "test", "stop", "restart", "t", "tst"):
            name = {"t": "test", "tst": "test"}.get(rest[0], rest[0])
        elif base in ("pnpm", "yarn", "bun"):
            name = rest[0]
        if not name:
            return None
        manifest = None
        for folder in [Path(cwd), *Path(cwd).parents]:
            if is_file_quietly(folder / "package.json"):
                manifest = folder / "package.json"
                break
            if realpath_loose(folder) == realpath_loose(self.root):
                break
        data, _ = load_json(manifest) if manifest else (None, None)
        scripts = data.get("scripts") if isinstance(data, dict) and isinstance(data.get("scripts"), dict) else {}
        for script_name in ("pre" + name, name, "post" + name):
            body = scripts.get(script_name)
            if isinstance(body, str) and body.strip():
                reason = self.check_command(body, manifest.parent, script=True)
                if reason:
                    return "The package script '{}' ({}) is blocked: {}".format(script_name, body[:80], reason)
        return None

    def check_make(self, base, argv, cwd):
        if base not in ("make", "gmake"):
            return None
        folder, makefile, targets, skip = Path(cwd), None, [], False
        for index, arg in enumerate(argv[1:], 1):
            if skip:
                skip = False
                continue
            if arg in ("-C", "--directory") and index + 1 < len(argv):
                folder, skip = self.resolve(argv[index + 1], cwd), True
            elif arg in ("-f", "--file", "--makefile") and index + 1 < len(argv):
                makefile, skip = argv[index + 1], True
            elif not arg.startswith("-") and "=" not in arg:
                targets.append(arg)
        path = self.resolve(makefile, folder) if makefile else next(
            (folder / n for n in ("GNUmakefile", "makefile", "Makefile") if is_file_quietly(folder / n)), None)
        text = read_text(path) if path is not None and is_file_quietly(path) else None
        for target in targets:
            if re.match(r"(?i)^(deploy|publish|release|ship|push)\b", target):
                return "{}, and no drive agent deploys or publishes. 'make {}' is blocked; the orchestrator runs it.".format(ROLE_WORDS[self.role], target)
        if self.role in READ_ONLY or self.role == "ui-reviewer":
            _, recorded = self.project_command_words()
            for target in targets:
                if target not in REVIEWER_MAKE_TARGETS and target not in recorded:
                    return ("{}. 'make {}' is not a recorded check; reviewers run make only for test, check, lint, build, or a "
                            "target GOAL.md records.".format(ROLE_WORDS[self.role], target))
        if not text:
            return None
        recipes, current = {}, None
        for line in text.splitlines():
            header = re.match(r"^([A-Za-z0-9_.\-/ ]+):(?!=)", line)
            if header and not line.startswith("\t"):
                names = header.group(1).split()
                current = names
                for name in names:
                    recipes.setdefault(name, [])
                if not targets:
                    targets = [n for n in names if not n.startswith(".")][:1]
                continue
            if line.startswith("\t") and current:
                for name in current:
                    recipes[name].append(line.strip().lstrip("@-+").strip())
            elif line.strip() and not line.startswith("#"):
                current = None
        if self.role in READ_ONLY or self.role == "ui-reviewer":
            _, recorded = self.project_command_words()
            for target in targets:
                if target not in REVIEWER_MAKE_TARGETS and target not in recorded:
                    return ("{}. 'make {}' is not a recorded check; reviewers run make only for test, check, lint, build, or a "
                            "target GOAL.md records.".format(ROLE_WORDS[self.role], target))
        for target in targets:
            for recipe in recipes.get(target, []):
                reason = self.check_command(recipe, folder, script=True)
                if reason:
                    return "The make target '{}' runs '{}', which is blocked: {}".format(target, recipe[:80], reason)
        return None

    def project_command_words(self):
        """Command names and make targets the project records as its own checks: GOAL.md's build, focused-test,
        and full-suite commands and CONSTRAINTS.md's commands. Reviewers may run these."""
        if not hasattr(self, "_project_words"):
            commands = []
            goal = read_text(self.root / ".drive" / "GOAL.md")
            if goal:
                for _, cls in Goal(goal).classifications:
                    probe = cls.get("probe") if isinstance(cls.get("probe"), dict) else {}
                    commands.extend(str(probe.get(k)) for k in PROBE_COMMAND_KEYS if isinstance(probe.get(k), str))
            constraints = read_text(self.root / ".drive" / "CONSTRAINTS.md")
            if constraints:
                for section in ("Enforced", "Measured only"):
                    commands.extend(row.get("command", "").strip("` ") for row in constraint_tables(constraints)[section].values())
            words, targets, modules = set(), set(), set()
            for command in commands:
                if not command or command.lower() == "none":
                    continue
                for segment in split_shell(command):
                    argv = strip_wrappers(shell_words(segment)[0])
                    if argv:
                        words.add(os.path.basename(argv[0]))
                        if interpreter_kind(os.path.basename(argv[0])) == "python" and "-m" in argv[1:-1]:
                            modules.add(argv[argv.index("-m") + 1])
                        if os.path.basename(argv[0]) in ("make", "gmake"):
                            targets.update(a for a in argv[1:] if not a.startswith("-") and "=" not in a)
            self._project_words = (words, targets)
            self._project_modules = modules
        return self._project_words

    def project_modules(self):
        self.project_command_words()
        return self._project_modules

    def reviewer_shape(self, base, argv, cwd, script):
        """Read-only reviewers run an allowlist of command shapes: reading and searching, the project's recorded
        checks and test runners, git and gh (checked further), and writes into their own output paths.
        Returns (handled, reason): handled means the decision is final."""
        words = ROLE_WORDS[self.role]
        formatter = formatter_write_reason(base, argv)
        if formatter:
            return True, ("{}. '{}' rewrites files; a reviewer runs formatters and linters only in their check form "
                          "(--check, --diff, or without --fix and --write).".format(words, formatter))
        if script:
            return False, None
        if base == "gitleaks" and self.role == "security-reviewer":
            return True, self.gitleaks_reason(argv, cwd)
        project_words, _ = self.project_command_words()
        if interpreter_kind(base) == "python" and "-m" in argv[1:]:
            index = argv.index("-m")
            module = argv[index + 1] if index + 1 < len(argv) else ""
            operands = [a for a in argv[index + 2:] if not a.startswith("-")]
            if module not in REVIEWER_PY_MODULES and module not in self.project_modules():
                return True, ("{}. 'python -m {}' is not a read-only module run; reviewers run python -m only for {} or a "
                              "module GOAL.md records as a check.".format(words, module, ", ".join(sorted(REVIEWER_PY_MODULES))))
            if module == "json.tool" and len(operands) > 1:
                return True, "{}. 'python -m json.tool' with an output file writes that file; let it print instead.".format(words)
        if "/" in argv[0] and base not in REVIEWER_COMMANDS and base not in project_words:
            path = self.resolve(argv[0], cwd)
            if is_file_quietly(path):
                return True, self.check_script(argv[0], cwd)
        if base not in REVIEWER_COMMANDS and base not in project_words:
            judged = " ".join(argv)
            judged = judged if len(judged) <= 160 else judged[:157] + "..."
            return True, ("{}. '{}' is not on the reviewer's list of read-only command shapes (reading, searching, the project's "
                          "recorded checks, test runners, and writes into its own output paths); the guard judged it as the first "
                          "word of the simple command `{}`. If verification needs it, the orchestrator records it as the build, "
                          "focused-test, or full-suite command in GOAL.md. A verdict or review file is written with a quoted "
                          "heredoc into your own output path, for example cat > .drive/reviews/<file> <<'JSON'.".format(words, base, judged))
        if base in ("awk", "gawk", "mawk"):
            operands = [a for a in argv[1:] if not a.startswith("-")]
            # String and regex literals are emptied in the program (the first operand) only, so "x > 0" is not a write.
            program = " ".join([awk_program_without_literals(operands[0])] + operands[1:] if operands else [])[:4000]
            if "-f" in argv or AWK_WRITE_RE.search(program):
                return True, "{}. This awk program can write files or run commands; use it only to read and print.".format(words)
        if base in ("sed", "gsed"):
            scripts = [argv[i + 1] for i, a in enumerate(argv[:-1]) if a in ("-e", "--expression")]
            positional = [a for a in without_sed_backup_suffix(argv[1:]) if not a.startswith("-")]
            scripts = scripts or positional[:1]
            if "-f" in argv or any(SED_WRITE_RE.search(s) for s in scripts):
                return True, "{}. This sed script can write files or run commands (w, W, or e); use sed only to read and print.".format(words)
        return False, None

    GITLEAKS_VALUE_FLAGS = {"--source": "--source", "-s": "--source", "--log-opts": "--log-opts", "--report-path": "--report-path",
                            "-r": "--report-path", "--report-format": "--report-format", "-f": "--report-format",
                            "--config": "--config", "-c": "--config", "--baseline-path": "--baseline-path", "-b": "--baseline-path",
                            "--exit-code": "--exit-code", "--log-level": "--log-level", "-l": "--log-level",
                            "--max-target-megabytes": "--max-target-megabytes", "--gitleaks-ignore-path": "--gitleaks-ignore-path",
                            "-i": "--gitleaks-ignore-path", "--enable-rule": "--enable-rule", "--max-decode-depth": "--max-decode-depth",
                            "--timeout": "--timeout"}
    GITLEAKS_BOOL_FLAGS = {"--no-git", "--redact", "--no-banner", "--no-color", "-v", "--verbose", "--follow-symlinks",
                           "--ignore-gitleaks-allow"}
    GITLEAKS_LOG_FLAGS = {"--all", "--no-merges", "--first-parent"}
    REV_RANGE_RE = re.compile(r"^[A-Za-z0-9_^][A-Za-z0-9_./~^@{}:+\-]*$")

    def gitleaks_reason(self, argv, cwd):
        """The security reviewer's secret scan: 'gitleaks detect --redact --no-git --source <path>' or 'gitleaks detect --redact
        --source <path> --log-opts <range>', with only read-only flags and a report written under .drive/reviews/ or a
        scratch directory."""
        words = ROLE_WORDS[self.role]

        def refuse(why):
            return ("{}. gitleaks runs only as 'gitleaks detect --redact --no-git --source <path>' or 'gitleaks detect --redact "
                    "--source <path> --log-opts <range>', with --report-path under .drive/reviews/ or {}; {}. Where gitleaks "
                    "cannot run, search the range with grep for the patterns in references/security.md section 8.".format(
                        words, scratch_words(), why))
        args = argv[1:]
        if len(args) == 1 and args[0] in ("version", "--version", "help", "--help", "-h"):
            return None
        if args[:1] != ["detect"]:
            return refuse("'gitleaks {}' is blocked".format(args[0][:30] if args else ""))
        values, flags, index = {}, set(), 1
        while index < len(args):
            arg = args[index]
            name, eq, inline = arg.partition("=")
            if name in self.GITLEAKS_BOOL_FLAGS:
                flags.add(name)
            elif name in self.GITLEAKS_VALUE_FLAGS:
                if not eq:
                    index += 1
                    if index >= len(args):
                        return refuse("{} has no value".format(name))
                    inline = args[index]
                values.setdefault(self.GITLEAKS_VALUE_FLAGS[name], []).append(inline)
            else:
                return refuse("'{}' is not one of its read-only flags".format(arg[:40]))
            index += 1
        if "--redact" not in flags:
            return refuse("--redact is required, so no secret value reaches the transcript or a report")
        if "--source" not in values:
            return refuse("--source is required")
        if ("--no-git" in flags) == ("--log-opts" in values):
            return refuse("a scan is either --no-git over a path or a git scan limited by --log-opts to the run's range")
        for raw in values.get("--report-path", []):
            if self.unknowable(raw):
                return refuse("the report path is named through a variable")
            path = self.resolve(raw, cwd)
            if not (is_tmp_path(path, exclude=self.root) or in_scope(rel_in_root(path, self.root), [".drive/reviews/"])):
                return refuse("--report-path {} is outside them".format(raw))
        for raw in values.get("--log-opts", []):
            try:
                tokens = [] if self.unknowable(raw) else shlex.split(raw)
            except ValueError:
                tokens = []
            if not tokens or any(t not in self.GITLEAKS_LOG_FLAGS and not self.REV_RANGE_RE.match(t) for t in tokens):
                return refuse("--log-opts takes only a revision range written out, such as <baseline_sha>..HEAD")
        return None

    def gh_reason(self, argv):
        """The main thread's GitHub writes: pull requests, releases, and repository changes are refused unless GOAL.md's
        plan records a deploy line naming the command."""
        positional, skip = [], False
        for arg in argv[1:]:
            if skip:
                skip = False
            elif arg in ("-R", "--repo", "--hostname"):
                skip = True
            elif not arg.startswith("-"):
                positional.append(arg)
        joined = " ".join(positional[:2])
        if not GH_WRITE_RE.match(joined) or goal_records_deploy(self.root, "gh " + joined):
            return None
        return ("The run never opens pull requests, publishes releases, or changes the repository on GitHub, so 'gh {}' is "
                "refused. A deploy that needs it names 'gh {}' in a deploy plan line in GOAL.md; otherwise it is an owner step "
                "in REPORT.md.".format(joined, joined))

    def shares_refs(self, git_cwd):
        """True when git run in git_cwd changes the run repository's refs: its common git directory is the run's (the main
        checkout or any linked worktree, wherever it lives), or the directory cannot be known."""
        text = str(git_cwd)
        if text.startswith("/nonexistent"):
            return True
        cache = self.__dict__.setdefault("_shares", {})
        if text not in cache:
            run_main = main_worktree_root(self.root) or self.root
            main = main_worktree_root(git_cwd) if exists_quietly(git_cwd) else None
            if main is None:
                cache[text] = rel_in_root(Path(git_cwd), self.root) is not None
            else:
                cache[text] = realpath_loose(main) == realpath_loose(run_main)
        return cache[text]

    def shared_refs_reason(self, sub, args, git_cwd):
        if sub == "push":
            return ("'git push' is blocked: nothing in a drive run pushes, from any directory, for any agent or the main thread; "
                    "a push is an owner step named in REPORT.md")
        what = ref_change(sub, args)
        if what and self.shares_refs(git_cwd):
            return ("{} is blocked: this directory shares the run repository's refs (the same git common directory), so it "
                    "would create or move a branch or tag in the owner's repository".format(what))
        return None

    def orchestrator_git(self, argv, cwd):
        """The main thread commits on the branch the run started on. It never pushes, never creates or moves a branch or tag
        in any worktree that shares the run's refs, and adds worktrees only detached under a scratch directory."""
        sub, args, git_cwd = self.git_parts(argv, cwd)
        if not sub:
            return None
        prefix = argv[:argv.index(sub)] if sub in argv else argv
        configs = [prefix[i + 1] for i, a in enumerate(prefix[:-1]) if a == "-c"] + \
                  [a[2:] for a in prefix if a.startswith("-c") and len(a) > 2 and not a.startswith("--")]
        if any(c.lower().startswith("alias.") for c in configs) or any(a.startswith("--config-env") for a in prefix):
            return "'git -c alias...' can rename any git command, so the guard refuses it; run the git command by its own name."
        if sub not in self.KNOWN_GIT:
            alias = git_out(git_cwd if is_dir_quietly(git_cwd) else self.root, "config", "--get", "alias." + sub)
            if alias:
                if alias.startswith("!"):
                    return self.check_command(alias[1:], cwd)
                try:
                    expanded = shlex.split(alias)
                except ValueError:
                    return "The git alias '{}' cannot be read by the guard; run the git command by its own name.".format(sub)
                if expanded and expanded[0] != sub:
                    return self.orchestrator_git(["git"] + prefix[1:] + expanded + args, cwd)
        positional = [a for a in args if not a.startswith("-")]

        def blocked(what):
            return ("The run commits on the branch it started on and never creates, switches, or pushes branches or leaves a "
                    "worktree outside a scratch directory, so {} is blocked.".format(what))
        refs = self.shared_refs_reason(sub, args, git_cwd)
        if refs:
            return "The run commits on the branch it started on. {}.".format(refs[0].upper() + refs[1:])
        if sub == "worktree" and positional[:1] == ["add"]:
            # Judged wherever git runs: from inside a linked worktree under a scratch directory, a new branch still lands
            # in the repository's refs.
            what = self.worktree_add_problem(args, git_cwd, allow_unknowable=True)
            if what:
                return blocked(what)
        if rel_in_root(git_cwd, self.root) is None:
            return None
        if sub == "stash" and (not positional or positional[0] not in ("list", "show")):
            return ("'git stash' is refused while a drive run is active (git stash list and git stash show still run): makers "
                    "and reviewers work in this one checkout, and a stash takes their uncommitted work out of the tree. Commit "
                    "the run's own changes, or leave the tree as it is.")
        if sub == "clean" and not any(a in ("-n", "--dry-run") or re.match(r"^-[a-zA-Z]*n", a) for a in args):
            return ("'git clean' is refused while a drive run is active (git clean -n or --dry-run still runs): it deletes "
                    "untracked files, and a maker's new files stay untracked until the orchestrator commits them. Remove named "
                    "build output with rm, or ignore it in .gitignore.")
        if sub == "commit" and any(a == "--amend" or (a.startswith("--am") and "--amend".startswith(a)) for a in args):
            return ("'git commit --amend' is refused while a drive run is active: it rewrites HEAD, which voids every review "
                    "running now (HEAD was rewritten) and can rewrite the drive(intake) commit the lint and the final audit "
                    "anchor on. Make a new commit instead.")
        current = git_out(self.root, "symbolic-ref", "--short", "-q", "HEAD")
        if sub in ("checkout", "switch"):
            if any(a in ("-b", "-B", "--orphan", "-c", "-C", "--create", "--force-create") or re.match(r"^-[bBcC].", a) for a in args):
                return blocked("'git {}' creating a branch".format(sub))
            if "--detach" in args:
                return blocked("'git {} --detach' in the shared checkout".format(sub))
            if sub == "switch" and positional and positional[0] != current:
                return blocked("'git switch {}'".format(positional[0]))
            if sub == "checkout" and "--" not in args and positional and positional[0] != current:
                target = positional[0]
                is_branch = git(self.root, "show-ref", "--verify", "--quiet", "refs/heads/" + target)[0] == 0
                is_commit_only = len(positional) == 1 and commit_exists(self.root, target) and not exists_quietly(Path(cwd) / target)
                if is_branch or is_commit_only:
                    return blocked("'git checkout {}'".format(target))
        if sub == "branch" and not self.git_read_only(sub, args):
            reason = self.branch_delete_reason(args, positional, current, blocked)
            if reason:
                return reason
        if sub == "worktree" and positional[:1] == ["remove"]:
            reason = self.worktree_remove_reason(positional[1:], git_cwd)
            if reason:
                return reason
        if sub == "reset" and any(a in ("--hard", "--merge") for a in args):
            return blocked("'git reset --hard' in the shared checkout")
        rewrite = self.head_rewrite(sub, args, git_cwd)
        if rewrite:
            return ("'{}' is refused while a drive run is active: it rewrites HEAD, which voids every review running now "
                    "(HEAD was rewritten) and can drop the drive(intake) commit the lint and the final audit anchor on. Make a "
                    "new commit instead; git reset, git reset HEAD, and git reset -- <paths> still unstage.".format(rewrite))
        if sub == "symbolic-ref" and len(positional) >= 2:
            return blocked("'git symbolic-ref' moving HEAD")
        if sub == "update-ref" and any(p.startswith("refs/heads/") for p in positional):
            return blocked("'git update-ref' on a branch")
        if sub == "rebase" and not any(a in ("--abort", "--continue", "--quit", "--skip") for a in args):
            return blocked("'git rebase' in the shared checkout")
        return None

    def head_rewrite(self, sub, args, git_cwd):
        """The command, when a git reset or update-ref moves HEAD to another commit (None when it only unstages or does
        not touch HEAD). A reset's first operand is a commit unless it is HEAD, an existing path, or pathspecs follow it."""
        if sub == "reset":
            before = args[:args.index("--")] if "--" in args else args
            positional = [a for a in before if not a.startswith("-")]
            if not positional or positional[0] in ("HEAD", "@") or len(positional) > 1 or "--" in args:
                return None
            if not self.unknowable(positional[0]) and exists_quietly(self.resolve(positional[0], git_cwd)):
                return None
            return "git reset {}".format(" ".join(args)[:60])
        if sub == "update-ref":
            positional, skip = [], False
            for arg in args:
                if skip:
                    skip = False
                elif arg == "-m":
                    skip = True
                elif not arg.startswith("-"):
                    positional.append(arg)
            if positional[:1] == ["HEAD"]:
                return "git update-ref {}".format(" ".join(args)[:60])
        return None

    def worktree_add_problem(self, args, git_cwd, allow_unknowable=False):
        """What makes a 'git worktree add' create a branch or land outside a scratch directory (None when it is a detached
        worktree under one). Every agent and the main thread are held to the same form; only the main thread may name
        the path through a variable."""
        rest = args[args.index("add") + 1:] if "add" in args else list(args)
        for arg in rest:
            if arg == "--orphan" or re.match(r"^-[^-]*[bB]", arg):
                return "'git worktree add {}' (which creates a branch)".format(arg[:20])
        if "--detach" not in rest:
            return "'git worktree add' without --detach (which creates a branch)"
        paths, skip = [], False
        for arg in rest:
            if skip:
                skip = False
            elif arg == "--reason":
                skip = True
            elif not arg.startswith("-"):
                paths.append(arg)
        if not paths:
            return "'git worktree add' with no path"
        if self.unknowable(paths[0]):
            return None if allow_unknowable else "'git worktree add' to a path named through a variable"
        if not is_tmp_path(self.resolve(paths[0], git_cwd), exclude=self.root):
            return "'git worktree add' outside a scratch directory"
        return None

    def branch_delete_reason(self, args, positional, current, blocked):
        """The main thread deletes a branch only with 'git branch -d', which refuses to drop unmerged commits, and only a
        branch the run created: one .drive/local/baseline.json does not list. Without a baseline, only drive/* and pkg/*."""
        flags = [a for a in args if a.startswith("-")]
        if not any(a in ("-d", "-D", "--delete") or re.match(r"^-[^-]*[dD]", a) for a in flags):
            return blocked("'git branch {}'".format(" ".join(args)[:60]))
        if any(a not in ("-d", "--delete", "-q", "--quiet") for a in flags) or not positional:
            return ("The run deletes a branch only with 'git branch -d <branch>', which refuses to drop commits that are not "
                    "merged, so 'git branch {}' is blocked. Land the branch's commits first; a branch git will not delete goes "
                    "to REPORT.md's \"Needed from you\" as 'git branch -D <branch>' for the owner.".format(" ".join(args)[:60]))
        baseline = read_baseline(self.root)
        owned = set(baseline.get("branches") or []) if baseline else None
        for name in positional:
            if self.unknowable(name):
                return "'git branch -d {}' names the branch through a variable, so the guard cannot check it is the run's; write the name out.".format(name[:40])
            if name == current:
                return "{} is the branch the run commits on, so 'git branch -d {}' is blocked.".format(name, name)
            if owned is not None and name in owned:
                return ("{} was there when the run started (.drive/local/baseline.json lists it), so it belongs to the owner and "
                        "stays; 'git branch -d {}' is blocked.".format(name, name))
            if owned is None and not any(fnmatch.fnmatchcase(name, p) for p in LEFTOVER_BRANCH_PATTERNS):
                return ("No baseline was recorded at init, so drive cannot tell whether {} is the owner's; without one the run "
                        "deletes only drive/* and pkg/* branches.".format(name))
        return None

    def worktree_remove_reason(self, targets, git_cwd):
        """The main thread removes only worktrees the run created: never the main checkout, and never one
        .drive/local/baseline.json lists. Without a baseline, only worktrees under a scratch directory."""
        entries = worktree_entries(self.root)
        main = os.path.realpath(entries[0].get("worktree", "")) if entries else os.path.realpath(str(self.root))
        baseline = read_baseline(self.root)
        owned = set(baseline.get("worktrees") or []) if baseline else None
        registered = [os.path.realpath(e.get("worktree", "")) for e in entries]
        for raw in (t for t in targets if not t.startswith("-")):
            if self.unknowable(raw):
                continue
            resolved = os.path.realpath(str(self.resolve(raw, git_cwd)))
            suffix = "/" + raw.strip("/")
            # git also accepts the unique trailing components of a worktree's path.
            matches = [p for p, e in zip(registered, entries) if p == resolved or (
                not os.path.isabs(raw) and suffix != "/" and (p.endswith(suffix) or e.get("worktree", "").endswith(suffix)))]
            for path in matches or [resolved]:
                if path == main:
                    return "{} is the main checkout, so 'git worktree remove' on it is blocked.".format(path)
                if owned is not None and path in owned:
                    return ("{} was there when the run started (.drive/local/baseline.json lists it), so it belongs to the owner "
                            "and stays; 'git worktree remove' on it is blocked.".format(path))
                if owned is None and not is_tmp_path(Path(path), exclude=self.root):
                    return ("No baseline was recorded at init, so drive cannot tell whether {} is the owner's; without one the "
                            "run removes only worktrees under {}.".format(path, scratch_words()))
        return None

    def frozen_list(self):
        if not hasattr(self, "_frozen"):
            self._frozen = frozen_entries(self.root)
        return self._frozen

    def frozen_hit_for(self, raw, cwd, container=False):
        if not raw or raw == "-" or raw.startswith("/dev/"):
            return None
        if self.unknowable(raw):
            names = [e for e in self.frozen_list() + list(ALWAYS_PROTECTED_REL) + list(RUN_CONTROL_REL) if len(e) >= 3]
            hit = next((e for e in names if e in raw), None)
            return frozen_block_reason(self.root, self.root / hit, self.role, container, self.frozen_list()) if hit else None
        candidates = [raw]
        if any(ch in raw for ch in "*?["):
            expanded = os.path.expanduser(raw)
            candidates.extend(globmod.glob(expanded if os.path.isabs(expanded) else str(Path(cwd) / raw)))
        for candidate in candidates:
            reason = frozen_block_reason(self.root, self.resolve(candidate, cwd), self.role, container, self.frozen_list())
            if reason:
                return reason
        return None

    def patch_touches_frozen(self, raw, cwd):
        if self.unknowable(raw):
            return "The patch {} is named through a variable, so the guard cannot check it for frozen paths.".format(raw)
        text = small_file_text(self.resolve(raw, cwd), 1_000_000)
        if text is None:
            if not self.frozen_list():
                return None
            return ("The patch {} is missing or 1 MB or larger, so the guard cannot read it for frozen paths while tests are "
                    "frozen. Split it into smaller patches, or apply it after the frozen tests' package lands.".format(raw))
        names = []
        for match in re.finditer(r"^(?:\+\+\+|---)\s+(\S+)", text, re.M):
            name = match.group(1)
            names.append(name[2:] if re.match(r"^[ab]/", name) else name)
        # A pure rename, copy, or mode change has no ---/+++ lines; its paths are on the diff --git and rename lines.
        for match in re.finditer(r"^diff --git a/(\S+) b/(\S+)\s*$", text, re.M):
            names.extend(match.groups())
        names.extend(m.group(1) for m in re.finditer(r"^(?:rename|copy) (?:from|to) (\S.*?)\s*$", text, re.M))
        for name in names:
            if name == "/dev/null":
                continue
            reason = frozen_block_reason(self.root, self.root / name, self.role, entries=self.frozen_list())
            if reason:
                return reason
        return None

    def frozen_reason(self, argv, redirects, cwd, stdin=()):
        """Every route a shell command could change a frozen file, the manifest, drive.py, or hooks.json by, for every
        role and the main thread."""
        for operator, target in redirects:
            if ">" in operator and not re.fullmatch(r"&?\d+|&?-", target):
                reason = self.frozen_hit_for(target, cwd)
                if reason:
                    return reason
            elif "<" in operator and argv and os.path.basename(argv[0]) == "patch" and "--dry-run" not in argv:
                reason = self.patch_touches_frozen(target, cwd)
                if reason:
                    return reason
        if not argv:
            return None
        base = os.path.basename(argv[0])
        args = argv[1:]
        ops = plain_operands(args)
        checks = []
        if base in ("rm", "rmdir", "unlink", "shred", "srm", "trash", "mv"):
            checks = [(t, True) for t in ops]
        elif base in ("truncate", "touch", "tee"):
            checks = [(t, False) for t in ops]
        elif base in ("chmod", "chown", "chgrp"):
            checks = [(t, False) for t in ops[1:]]
        elif base in ("cp", "ln", "install", "rsync", "ditto", "scp"):
            target_dir = next((args[i + 1] for i, a in enumerate(args[:-1]) if a in ("-t", "--target-directory")), None)
            checks = [(target_dir, False)] if target_dir else ([(ops[-1], False)] if len(ops) >= 2 else [])
            if base == "rsync" and any(a == "--del" or a.startswith("--delete") for a in args):
                # --delete removes whatever the destination holds that the source lacks.
                checks = [(target, True) for target, _ in checks]
        elif base == "dd":
            checks = [(a[3:], False) for a in args if a.startswith("of=")]
        elif base in ("sed", "gsed", "perl", "ruby") and any(
                a.startswith("--in-place") or (a.startswith("-") and not a.startswith("--") and "i" in a[1:]) for a in args):
            checks = [(t, False) for t in in_place_targets(base, args)]
        elif base in ("tar", "gtar", "bsdtar", "unzip"):
            extracting = base == "unzip" or "--extract" in args or any(re.match(r"^-?[a-wyzA-Z]*x", a) for a in args[:1]) \
                or any(re.match(r"^-[a-zA-Z]*x", a) for a in args)
            directory = next((args[i + 1] for i, a in enumerate(args[:-1]) if a in ("-C", "--directory", "-d")), ".")
            checks = [(directory, True)] if extracting and "-l" not in args else []
        elif base == "find":
            mutators = ("rm", "mv", "sed", "gsed", "perl", "truncate", "shred", "unlink", "tee", "cp")
            if "-delete" in args or any(a in ("-exec", "-execdir", "-ok", "-okdir") and i + 1 < len(args)
                                        and os.path.basename(args[i + 1]) in mutators for i, a in enumerate(args)):
                roots = []
                for a in args:
                    if a.startswith(("-", "(", "!")):
                        break
                    roots.append(a)
                checks = [(r, True) for r in roots or ["."]]
        elif base == "patch" and "--dry-run" not in args:
            patch_file = next((args[i + 1] for i, a in enumerate(args[:-1]) if a in ("-i", "--input")), None)
            if patch_file:
                reason = self.patch_touches_frozen(patch_file, cwd)
                if reason:
                    return reason
            checks = [(ops[0], False)] if ops and not patch_file else []
        elif base == "git":
            return self.git_frozen_reason(argv, cwd)
        for target, container in checks:
            reason = self.frozen_hit_for(target, cwd, container)
            if reason:
                return reason
        kind = interpreter_kind(base)
        if kind:
            code = " ".join(interpreter_inputs(kind, argv, stdin)[0])
            if code:
                for entry in self.frozen_list() + list(ALWAYS_PROTECTED_REL) + [str(p) for p in enforcement_files()]:
                    if entry and entry in code:
                        target = Path(entry) if os.path.isabs(entry) else self.root / entry
                        reason = frozen_block_reason(self.root, target, self.role, entries=self.frozen_list())
                        if reason:
                            return reason
                # A literal path relative to where the code runs (cd tests && python3 -c "open('test_x.py', 'w')").
                deleting = bool(CODE_DELETE_RE.search(code))
                for literal in code_literals(kind, code):
                    if len(literal) < 3 or "\n" in literal or any(ch in literal for ch in "*?[$`"):
                        continue
                    # A literal naming the run marker is usually a read (json.load(open(...))), so only frozen paths count
                    # here, unless the code also calls a delete: then the marker, the baseline, or a folder holding them counts.
                    path = self.resolve(literal, cwd)
                    reason = frozen_block_reason(self.root, path, self.role, entries=self.frozen_list(), run_control=False)
                    if not reason and deleting and rel_in_root(path, self.root) in (".drive", ".drive/local") + RUN_CONTROL_REL:
                        reason = frozen_block_reason(self.root, self.root / RUN_CONTROL_REL[0], self.role, entries=[])
                    if reason:
                        return reason
        return None

    def git_frozen_reason(self, argv, cwd):
        sub, args, git_cwd = self.git_parts(argv, cwd)
        if not sub:
            return None
        ops = plain_operands(args)
        words = "The freeze holds frozen tests out of git's reach too"
        if sub in ("checkout", "restore", "rm", "mv"):
            for target in (args[args.index("--") + 1:] if "--" in args else ops):
                reason = self.frozen_hit_for(target, git_cwd, container=True)
                if reason:
                    return reason
        if sub == "clean" and rel_in_root(git_cwd, self.root) is not None \
                and not any(a in ("-n", "--dry-run") or re.match(r"^-[a-zA-Z]*n", a) for a in args) \
                and any(re.match(r"^-[a-zA-Z]*[xX]", a) for a in args):
            return ("'git clean {}' removes ignored files, and .drive/local/ is ignored: it holds the run marker "
                    ".drive/local/active, baseline.json, the review snapshots, and gate.log, and without the marker every drive "
                    "hook switches off mid-run. Remove named build output with rm, or ignore it in .gitignore.".format(" ".join(args)[:40]))
        if not self.frozen_list():
            return None
        positional = [a for a in args if not a.startswith("-")]
        if sub == "stash" and (not positional or positional[0] not in ("list", "show")):
            return "{}: 'git stash' would carry uncommitted frozen tests out of the tree, so it is blocked while .drive/frozen.txt lists any.".format(words)
        if sub == "reset":
            if any(a in ("--hard", "--merge", "--keep") for a in args):
                return "{}: 'git reset {}' can overwrite frozen tests, so it is blocked.".format(words, " ".join(args)[:40])
            for target in (args[args.index("--") + 1:] if "--" in args else []):
                reason = self.frozen_hit_for(target, git_cwd, container=True)
                if reason:
                    return reason
        if sub == "clean" and not any(a in ("-n", "--dry-run") or re.match(r"^-[a-zA-Z]*n", a) for a in args):
            return "{}: 'git clean' deletes untracked files, and frozen tests stay untracked until their package lands.".format(words)
        if sub in ("apply", "am") and not any(a in ("--check", "--stat", "--numstat", "--summary") for a in args):
            files = [a for a in args if not a.startswith("-")]
            if not files:
                return "{}: 'git {}' from standard input cannot be checked for frozen paths; pass the patch file.".format(words, sub)
            for name in files:
                reason = self.patch_touches_frozen(name, git_cwd)
                if reason:
                    return reason
        return None

    def check_script(self, raw, cwd):
        if self.unknowable(raw):
            return None
        text = small_file_text(self.resolve(raw, cwd), 256_000)
        if text is None:
            return None
        return self.check_command(text, cwd, script=True)

    def check_find(self, argv, cwd, script):
        roots = []
        for arg in argv[1:]:
            if arg.startswith(("-", "(", "!")):
                break
            roots.append(arg)
        if "-delete" in argv and self.restricted_paths and not script:
            for target in roots or ["."]:
                if not self.write_ok(target, cwd, deleting=True):
                    return "{}. find -delete on {} deletes outside its scope; delete only {}.".format(ROLE_WORDS[self.role], target, "under " + scratch_words() if self.role in READ_ONLY else self.scope_words())
        for flag in ("-exec", "-execdir", "-ok", "-okdir"):
            if flag in argv:
                start = argv.index(flag) + 1
                inner = []
                for arg in argv[start:]:
                    if arg in (";", "+", "\\;"):
                        break
                    inner.append(arg)
                if inner:
                    reason = self.check_argv(strip_wrappers(inner), cwd, script)
                    if reason:
                        return reason
        return None

    def git_parts(self, argv, cwd):
        index, git_cwd = 1, cwd
        while index < len(argv) and argv[index].startswith("-"):
            option = argv[index]
            if option in GIT_OPTIONS_WITH_VALUE and index + 1 < len(argv):
                if option in ("-C", "--git-dir", "--work-tree"):
                    git_cwd = self.resolve(argv[index + 1], git_cwd) if not self.unknowable(argv[index + 1]) else Path("/nonexistent")
                index += 2
                continue
            if option.startswith(("--git-dir=", "--work-tree=")):
                value = option.split("=", 1)[1]
                git_cwd = self.resolve(value, git_cwd) if not self.unknowable(value) else Path("/nonexistent")
            index += 1
        sub = argv[index] if index < len(argv) else ""
        return sub, argv[index + 1:], git_cwd

    KNOWN_GIT = GIT_READ_ONLY | GIT_WORKER_BLOCKED | {"branch", "tag", "config", "remote", "reflog", "notes", "submodule",
                                                      "symbolic-ref", "clone", "fetch", "init", "apply", "format-patch",
                                                      "mergetool", "difftool", "lfs", "sparse-checkout", "maintenance"}

    def check_git(self, argv, cwd):
        sub, args, git_cwd = self.git_parts(argv, cwd)
        words = ROLE_WORDS[self.role]
        if not sub:
            return None
        prefix = argv[:argv.index(sub)] if sub in argv else argv
        configs = [prefix[i + 1] for i, a in enumerate(prefix[:-1]) if a == "-c"] + \
                  [a[2:] for a in prefix if a.startswith("-c") and len(a) > 2 and not a.startswith("--")]
        if any(c.lower().startswith("alias.") for c in configs) or any(a.startswith("--config-env") for a in prefix):
            return "{}. 'git -c alias...' can rename any git command, so the guard blocks it; run the git command by its own name.".format(words)
        if sub == "worktree" and [a for a in args if not a.startswith("-")][:1] == ["add"]:
            # Checked before the scratch-directory allowance: a linked worktree under a scratch directory shares the
            # repository's refs, so a branch created from inside it is a branch in the owner's repository.
            what = self.worktree_add_problem(args, git_cwd)
            if what:
                return ("{}. Worktrees are created only under {}, detached ('git worktree add --detach <path> <sha>'), so no "
                        "branch is ever created; {} is blocked.".format(words, scratch_words(), what))
        in_tmp = is_tmp_path(git_cwd, exclude=self.root)
        if sub not in self.KNOWN_GIT:
            alias = git_out(git_cwd if is_dir_quietly(git_cwd) else self.root, "config", "--get", "alias." + sub)
            if alias:
                if alias.startswith("!"):
                    return self.check_command(alias[1:], cwd)
                try:
                    expanded = shlex.split(alias)
                except ValueError:
                    return "{}. The git alias '{}' cannot be read by the guard.".format(words, sub)
                if expanded and expanded[0] != sub:
                    return self.check_git(["git"] + prefix[1:] + expanded + args, cwd)
        refs = self.shared_refs_reason(sub, args, git_cwd)
        if refs:
            return "{}, and {}.".format(words, refs)
        if sub == "archive":
            outputs = [a.split("=", 1)[1] for a in args if a.startswith("--output=")] + \
                      [args[i + 1] for i, a in enumerate(args[:-1]) if a in ("-o", "--output")]
            for target in outputs:
                if not self.write_ok(target, cwd):
                    return "{}. git archive may write only {}.".format(words, self.scope_words())
            return None
        if self.role in READ_ONLY or self.role == "ui-reviewer":
            if in_tmp:
                return None
            if self.git_read_only(sub, args):
                return None
            if sub == "clone":
                targets = [a for a in args if not a.startswith("-")]
                if len(targets) >= 2 and is_tmp_path(self.resolve(targets[-1], cwd), exclude=self.root):
                    return None
            return ("{}, so 'git {}' is blocked. Report what should change in your result; use git status, log, diff, "
                    "show, or archive into {} to inspect.".format(words, sub, scratch_words()))
        if self.role == "investigator":
            if in_tmp:
                return None
            if sub == "worktree":
                action = args[0] if args else ""
                if action in ("list", "prune"):
                    return None
                if action in ("add", "remove"):
                    paths = [a for a in args[1:] if not a.startswith("-")]
                    if action == "add":
                        values_after = {"-b", "-B", "--reason"}
                        cleaned, skip = [], False
                        for a in args[1:]:
                            if skip:
                                skip = False
                                continue
                            if a in values_after:
                                skip = True
                                continue
                            if not a.startswith("-"):
                                cleaned.append(a)
                        paths = cleaned[:1]
                    if paths and all(is_tmp_path(self.resolve(p, cwd), exclude=self.root) for p in paths):
                        return None
                return "{}. Worktrees are created and removed only under {}; 'git worktree {}' outside it is blocked.".format(words, scratch_words(), action)
            if sub == "branch" and any(a in ("-d", "-D", "--delete") for a in args):
                names = [a for a in args if not a.startswith("-")]
                if names and all(re.match(r"^(drive|hyp|arm|bisect)/", n) for n in names):
                    return None
        positional_args = [a for a in args if not a.startswith("-")]
        if sub == "branch" and not self.git_read_only(sub, args) and not any(a in ("-d", "-D", "--delete") for a in args):
            return "{}, so 'git branch {}' is blocked: no drive agent creates or renames a branch.".format(words, " ".join(args)[:60])
        if sub == "symbolic-ref" and len(positional_args) >= 2:
            return "{}, so 'git symbolic-ref' that moves HEAD is blocked.".format(words)
        if sub in GIT_WORKER_BLOCKED or (sub == "branch" and any(a in ("-d", "-D", "--delete", "-m", "-M", "--move", "-f", "--force") for a in args)) \
                or (sub == "tag" and args and not any(a in ("-l", "--list") for a in args)) \
                or (sub == "config" and args and not any(a.startswith(("--get", "--list", "-l")) for a in args) and len([a for a in args if not a.startswith("-")]) >= 2):
            if sub == "restore" and not any(a in ("--staged", "-S", "--source") or a.startswith("--source=") for a in args) \
                    and self.role in ("implementer", "writer"):
                return self.maker_restore_reason(args, git_cwd)
            hint = " To discard your own edit to a file you own, use git restore <path>." if sub == "checkout" and self.role in ("implementer", "writer") else ""
            return "{}, so 'git {}' is blocked. The orchestrator integrates and commits; list what should be committed in your report.{}".format(words, sub, hint)
        return None

    def maker_restore_reason(self, args, git_cwd):
        """A maker restores only paths a package brief owns, named one by one: 'git restore' anywhere else discards a
        sibling package's uncommitted work."""
        targets = args[args.index("--") + 1:] if "--" in args else [a for a in args if not a.startswith("-")]
        owned = self.owned_globs()
        ok = bool(targets) and bool(owned)
        for target in targets:
            rel = None if self.unknowable(target) or any(ch in target for ch in "*?[") else rel_in_root(self.resolve(target, git_cwd), self.root)
            if not rel or rel == "." or not any(glob_matches(rel, g) for g in owned):
                ok = False
        if ok:
            return None
        return ("{}, so 'git restore {}' is refused: with several makers in one checkout it can discard another package's "
                "uncommitted work. Restore only files a package brief owns ({}), named one by one; list any other accidental "
                "change in your report's files field marked 'accidental'.".format(
                    ROLE_WORDS[self.role], " ".join(targets)[:60], ", ".join(owned[:4]) if owned else "no brief owns a path yet"))

    @staticmethod
    def git_read_only(sub, args):
        positional = [a for a in args if not a.startswith("-")]
        if sub in GIT_READ_ONLY:
            return True
        if sub == "branch":
            return not positional or any(a in ("-l", "--list", "-a", "-r", "-v", "-vv", "--show-current", "--contains", "--merged", "--no-merged") for a in args) \
                and not any(a in ("-d", "-D", "--delete", "-m", "-M", "-c", "-C", "-f", "--force") for a in args)
        if sub == "tag":
            return not positional or any(a in ("-l", "--list") for a in args)
        if sub == "stash":
            return bool(positional) and positional[0] in ("list", "show")
        if sub == "worktree":
            return bool(positional) and positional[0] == "list"
        if sub == "config":
            return any(a.startswith(("--get", "--list", "-l", "--show")) for a in args) or len(positional) <= 1
        if sub == "remote":
            return not positional or positional[0] in ("show", "get-url")
        if sub == "reflog":
            return not positional or positional[0] == "show"
        if sub == "bisect":
            return bool(positional) and positional[0] in ("log", "view", "visualize")
        if sub == "notes":
            return not positional or positional[0] in ("list", "show")
        if sub == "submodule":
            return not positional or positional[0] in ("status", "summary")
        if sub == "symbolic-ref":
            return len(positional) <= 1
        return False

    def check_file_command(self, base, argv, cwd):
        words = ROLE_WORDS[self.role]
        operands = []
        after_dashdash = False
        for arg in argv[1:]:
            if arg == "--" and not after_dashdash:
                after_dashdash = True
                continue
            if arg.startswith("-") and not after_dashdash:
                continue
            operands.append(arg)
        deleting = base in ("rm", "rmdir", "unlink", "shred", "srm", "trash")
        if deleting or base == "mv":
            if not operands:
                if self.role == "orchestrator":
                    return None
                return "{}. '{}' with no visible paths cannot be checked; name the paths directly.".format(words, base)
            for target in operands:
                if not self.write_ok(target, cwd, deleting=True):
                    return "{}. '{}' on {} deletes or moves outside {}{}. Leave the file in place and report it.".format(
                        words, base, target, scratch_words(), "" if self.role in READ_ONLY else " or its scope")
            return None
        targets = []
        if base in ("cp", "install", "ln", "rsync", "ditto", "scp"):
            targets = operands[-1:] if len(operands) >= 2 else operands
        elif base in ("tee", "touch", "truncate", "mkdir", "chmod", "chown", "chgrp"):
            targets = operands[1:] if base in ("chmod", "chown", "chgrp") else operands
        elif base == "dd":
            targets = [a[3:] for a in argv[1:] if a.startswith("of=")]
        elif base in ("sed", "gsed") and any(a == "-i" or a.startswith("-i") or a.startswith("--in-place") for a in argv[1:]):
            targets = in_place_targets(base, argv[1:])
        elif base == "perl" and any(re.match(r"^-\w*i", a) for a in argv[1:]):
            targets = operands[1:]
        elif base in ("curl",):
            targets = [argv[i + 1] for i, a in enumerate(argv[:-1]) if a in ("-o", "--output")]
        elif base in ("wget",):
            targets = [argv[i + 1] for i, a in enumerate(argv[:-1]) if a in ("-O", "--output-document")]
        elif base == "patch":
            targets = [argv[i + 1] for i, a in enumerate(argv[:-1]) if a == "-o"] or ["."]
        elif base in ("tar", "gtar", "bsdtar"):
            first = argv[1] if len(argv) > 1 else ""
            cluster = first.lstrip("-") if not first.startswith("--") else ""
            extracting = "x" in cluster or any(a in ("-x", "--extract", "--get") for a in argv[1:]) or any(re.match(r"^-[a-wyzA-Z]*x", a) for a in argv[1:])
            creating = "c" in cluster or "r" in cluster or "u" in cluster or any(re.match(r"^-[a-zA-Z]*[cru]", a) or a in ("--create", "--append", "--update") for a in argv[1:])
            directory = next((argv[i + 1] for i, a in enumerate(argv[:-1]) if a in ("-C", "--directory")),
                             next((a.split("=", 1)[1] for a in argv if a.startswith("--directory=")), "."))
            archive = next((argv[i + 1] for i, a in enumerate(argv[:-1]) if a in ("-f", "--file") or (re.match(r"^-?[a-zA-Z]*f$", a) and i == 1)),
                           next((a.split("=", 1)[1] for a in argv if a.startswith("--file=")), None))
            if extracting:
                targets = [directory]
            elif creating and archive:
                targets = [archive]
        elif base == "unzip":
            targets = [next((argv[i + 1] for i, a in enumerate(argv[:-1]) if a == "-d"), ".")] if "-l" not in argv else []
        elif base == "zip":
            targets = operands[:1]
        elif base in ("gzip", "gunzip", "bzip2", "bunzip2", "xz", "unxz", "zstd"):
            targets = [] if any(a in ("-c", "--stdout", "-l", "-t") for a in argv[1:]) else operands
        for target in targets:
            if not self.write_ok(target, cwd):
                return "{}. '{}' writes {} outside its scope; write only {}.".format(words, base, target, self.scope_words())
        return None


SHELL_TOOLS = ("Bash", "PowerShell", "Monitor")
HOOK_TREE_BUDGET = 4.0


def reviewers_running(root):
    folder = Path(root) / ".drive" / "local" / "ro"
    return folder.is_dir() and any(folder.glob("*.json"))


def pre_head_path(root, tool_use_id):
    safe = re.sub(r"[^A-Za-z0-9_.\-]", "_", str(tool_use_id))[:100]
    return Path(root) / ".drive" / "local" / "ro" / "pre-{}".format(safe)


def read_hook_payload():
    """(hook input, whether it parsed as a JSON object)."""
    try:
        raw = sys.stdin.read()
    except (OSError, ValueError):
        return {}, False
    if not raw.strip():
        return {}, True
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}, False
    return (data, True) if isinstance(data, dict) else ({}, False)


def cmd_hook_guard(args):
    data, valid = read_hook_payload()
    if not valid:
        env_root = os.environ.get("CLAUDE_PROJECT_DIR")
        if env_root and (Path(env_root) / ".drive" / "local" / "active").is_file():
            print("The drive guard could not read this tool call's hook input, so the call is refused while a drive run is active.",
                  file=sys.stderr)
            return 2
        return 0
    role = role_of(data.get("agent_type"))
    # The main thread is a call with no agent_id and no drive role (a `claude --agent drive:<role>` session
    # has no agent_id but is that role). Any other subagent is not drive's to guard.
    main_thread = not data.get("agent_id") and role is None
    # A subagent outside drive's roster (general-purpose, Explore, another plugin's) gets the main thread's rules:
    # it may not write reviewer evidence, frozen tests, or the ledger, or create, switch, or push branches.
    cwd = data.get("cwd")
    root = active_root(cwd)
    if root is None:
        return 0
    tool = data.get("tool_name")
    tool_input = data.get("tool_input") if isinstance(data.get("tool_input"), dict) else {}
    if main_thread:
        record_session_mode(root, data)
    try:
        if tool in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
            raw = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
            target = Path(raw) if os.path.isabs(raw) else Path(cwd or root) / raw
            reason = frozen_block_reason(root, target, role) if raw else None
            if not reason:
                reason = main_write_reason(raw, root, cwd) if role is None else tool_write_reason(role, raw, root, cwd)
        elif tool in SHELL_TOOLS:
            command = tool_input.get("command")
            reason = Guard("orchestrator" if role is None else role, root, cwd).check_command(command) \
                if isinstance(command, str) and command.strip() else None
        elif tool == "EnterWorktree":
            reason = ("{}. A drive run works in the one shared checkout, or in a detached scratch worktree made with 'git worktree "
                      "add --detach <scratch path> <sha>'. EnterWorktree creates or enters a harness worktree on its own branch, "
                      "so it is refused while a run is active.".format(ROLE_WORDS["orchestrator" if role is None else role]))
        else:
            reason = None
    except Exception as exc:
        reason = "The drive guard could not check this call ({}). Run the steps as separate plain commands.".format(type(exc).__name__)
    if reason:
        print(reason, file=sys.stderr)
        return 2
    if tool in ("Edit", "Write", "NotebookEdit", "MultiEdit") and role not in SNAPSHOT_ROLES:
        # A write another agent makes while a reviewer runs is recorded, so the reviewer is not blamed for it.
        raw = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
        if raw:
            target = Path(raw) if Path(raw).is_absolute() else Path(cwd or root) / raw
            rel = rel_in_root(target, root)
            if rel is not None:
                ledger_append(root, {"kind": "edit", "path": rel, "agent_type": data.get("agent_type") or "main thread",
                                     "agent_id": data.get("agent_id")})
    if role not in SNAPSHOT_ROLES and tool in ("Bash", "PowerShell") and data.get("tool_use_id"):
        # HEAD, and while a reviewer runs the dirty tree too, so hook-post can record what this call changed as the
        # caller's edits instead of voiding the review.
        try:
            marker = pre_head_path(root, data["tool_use_id"])
            marker.parent.mkdir(parents=True, exist_ok=True)
            pre = {"head": git_out(root, "rev-parse", "HEAD") or "none"}
            if reviewers_running(root):
                pre["files"] = tracked_state(root, budget=HOOK_TREE_BUDGET)["files"]
            marker.write_text(json.dumps(pre) + "\n", encoding="utf-8")
        except OSError:
            pass
    return 0


def cmd_hook_post(args):
    """PostToolUse on shell calls by the main thread and every agent that is not a read-only reviewer: record every
    commit the main thread made, and every tracked file the call changed while a reviewer ran, so the review is not
    voided for the lead's or a maker's own work."""
    data = read_hook_input()
    if data.get("tool_name") not in ("Bash", "PowerShell") or not data.get("tool_use_id"):
        return 0
    role = role_of(data.get("agent_type"))
    if role in SNAPSHOT_ROLES:
        return 0
    root = active_root(data.get("cwd"))
    if root is None:
        return 0
    marker = pre_head_path(root, data["tool_use_id"])
    raw = (read_text(marker) or "").strip()
    try:
        marker.unlink()
    except OSError:
        pass
    try:
        pre = json.loads(raw) if raw.startswith("{") else {"head": raw}
    except ValueError:
        pre = {"head": raw}
    before_files = pre.get("files") if isinstance(pre, dict) else None
    if isinstance(before_files, dict):
        after_files = tracked_state(root, budget=HOOK_TREE_BUDGET, like=before_files)["files"]
        changed = sorted(rel for rel in set(before_files) | set(after_files) if before_files.get(rel) != after_files.get(rel))
        for rel in changed[:500]:
            ledger_append(root, {"kind": "edit", "path": rel, "agent_type": data.get("agent_type") or "main thread",
                                 "agent_id": data.get("agent_id"), "via": data.get("tool_name")})
    if data.get("agent_id") or role is not None:
        return 0
    before = str(pre.get("head") or "") if isinstance(pre, dict) else ""
    after = git_out(root, "rev-parse", "HEAD")
    if not after or not before or before == after:
        return 0
    if before == "none":
        new = (git_out(root, "rev-list", "--max-count=200", after) or "").split()
    elif git(root, "merge-base", "--is-ancestor", before, after)[0] == 0:
        new = (git_out(root, "rev-list", "--max-count=200", "{}..{}".format(before, after)) or "").split()
    else:
        new = [after]
    for sha in new:
        ledger_append(root, {"kind": "main-commit", "sha": sha, "session_id": data.get("session_id")})
    return 0


# --- hook-snapshot: the tree snapshot around read-only agents ----------------------------------

SNAPSHOT_ROLES = {"verifier", "grader", "ui-reviewer", "auditor", "security-reviewer"}


SNAPSHOT_MAX_FILES = 5000
SNAPSHOT_MAX_BYTES = 8000000
SNAPSHOT_BUDGET = 6.0


def tracked_state(root, budget=None, like=None):
    """HEAD and a digest of every tracked file with uncommitted changes and every untracked file git does not ignore,
    outside `.drive/` (the orchestrator rewrites state files while reviewers run, and that is not the reviewer's doing).
    A file past the file-count cap, larger than SNAPSHOT_MAX_BYTES, or reached after `budget` seconds is compared by size
    and modification time instead of content, so a large build tree cannot time the hook out. With `like` (an earlier
    snapshot), each file is digested in the form it had there."""
    head = git_out(root, "rev-parse", "HEAD") or "none"
    code, out, _ = git(root, "status", "--porcelain=v1", "--untracked-files=all", "-z")
    files, by_stat, hashed = {}, 0, 0
    try:
        max_files = int(os.environ.get("DRIVE_SNAPSHOT_MAX_FILES") or SNAPSHOT_MAX_FILES)
    except ValueError:
        max_files = SNAPSHOT_MAX_FILES
    deadline = time.time() + budget if budget else None
    like = like or {}
    if code == 0:
        records = out.split("\0")
        index = 0
        while index < len(records):
            record = records[index]
            index += 1
            if len(record) < 4:
                continue
            status, rel = record[:2], record[3:]
            if "R" in status or "C" in status:
                index += 1
            if rel.startswith(".drive/"):
                continue
            if status == "??" and rel in files:
                # git rm --cached lists a tracked path twice, "D " then "??"; the index deletion is what counts.
                continue
            path = Path(root) / rel
            try:
                if not path.is_file():
                    digest = "missing"
                else:
                    stat = path.stat()
                    earlier = str(like.get(rel, "")).split(" ", 1)[-1]
                    if earlier.startswith("stat:") or (rel not in like and (
                            hashed >= max_files or stat.st_size > SNAPSHOT_MAX_BYTES or (deadline and time.time() > deadline))):
                        digest = "stat:{}:{}".format(stat.st_size, stat.st_mtime_ns)
                        by_stat += 1
                    else:
                        digest = hashlib.sha1(path.read_bytes()).hexdigest()
                        hashed += 1
            except OSError:
                digest = "unreadable"
            files[rel] = "{} {}".format(status, digest)
    return {"head": head, "files": files, "by_stat": by_stat}


def blob_sha1(root, rev, rel):
    try:
        proc = subprocess.run(["git", "-C", str(root), "cat-file", "blob", "{}:{}".format(rev, rel)], capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return hashlib.sha1(proc.stdout).hexdigest() if proc.returncode == 0 else None


def snapshot_changes(root, before, after):
    """(tracked paths that changed under a read-only agent, notes about HEAD, untracked paths that appeared, changed, or
    went away). An untracked path never voids a review: a test run leaves harmless artifacts (.coverage, junit XML,
    screenshots), and lint --stop and --final report any the run leaves uncommitted. Commits the main thread
    made (recorded by hook-post) and commits that touch only `.drive/` are the orchestrator's, and a
    file that was uncommitted at the start and is committed unchanged by such a commit did not change."""
    notes = []
    head_before, head_after = str(before.get("head")), after["head"]
    main_moved = False
    if head_before != head_after:
        if head_before == "none" or git(root, "merge-base", "--is-ancestor", head_before, head_after)[0] != 0:
            notes.append("HEAD moved from {} to {} by a rewrite".format(head_before[:7], head_after[:7]))
        else:
            recorded = {str(e.get("sha")) for e in ledger_entries(root, "main-commit")}
            foreign = []
            for sha in (git_out(root, "rev-list", "{}..{}".format(head_before, head_after)) or "").split():
                if sha in recorded:
                    continue
                touched = [t for t in (git_out(root, "diff-tree", "--no-commit-id", "--name-only", "-r", sha) or "").splitlines() if t.strip()]
                if touched and all(t.startswith(".drive/") for t in touched):
                    continue
                foreign.append(sha)
            if foreign:
                notes.append("HEAD moved from {} to {} by commits the main thread did not make: {}".format(
                    head_before[:7], head_after[:7], ", ".join(s[:7] for s in foreign[:5])))
            else:
                main_moved = True
    changed, untracked = [], []
    files_before, files_after = before.get("files", {}) or {}, after["files"]
    since = float(before.get("started_ts") or 0) - 1
    edited = {str(e.get("path")) for e in ledger_entries(root, "edit") if float(e.get("ts") or 0) >= since}
    for rel in sorted(set(files_before) | set(files_after)):
        if files_before.get(rel) == files_after.get(rel):
            continue
        if rel in edited:
            continue
        state_before = str(files_before[rel])[:2] if rel in files_before else None
        state_after = str(files_after[rel])[:2] if rel in files_after else None
        # Untracked for void purposes: untracked throughout, or untracked (or absent) at the start and newly staged
        # since. A tracked path removed from the index ("D ") is a deletion and is judged below.
        if all(s in (None, "??") for s in (state_before, state_after)) or (
                state_before in (None, "??") and state_after is not None and state_after[0] == "A"):
            untracked.append(rel)
            continue
        if main_moved and rel in files_before and rel not in files_after:
            old = str(files_before[rel]).split(" ", 1)[-1]
            now = blob_sha1(root, head_after, rel)
            if now == old or (old == "missing" and now is None):
                continue
        changed.append(rel)
    return changed, notes, untracked


def transcript_settle_seconds():
    try:
        return max(0.0, float(os.environ.get("DRIVE_TRANSCRIPT_SETTLE") or 3))
    except ValueError:
        return 3.0


def cmd_hook_snapshot(args):
    """SubagentStart records a spawn for every drive agent and, for read-only reviewers, a snapshot of the tracked tree
    and of every evidence JSON. SubagentStop records in the provenance ledger each evidence file that changed during the
    review and that the reviewer's own transcript (agent_transcript_path) shows it writing, and voids the review when
    tracked files changed under it. It never blocks: a block would send the reviewer an instruction about changes it did
    not make."""
    data = read_hook_input()
    agent_type = data.get("agent_type")
    role = role_of(agent_type)
    if role is None:
        return 0
    root = active_root(data.get("cwd"))
    if root is None:
        return 0
    agent = re.sub(r"[^A-Za-z0-9_.\-]", "_", str(data.get("agent_id") or "unknown"))[:80] or "unknown"
    folder = root / ".drive" / "local" / "ro"
    path = folder / "{}.json".format(agent)
    if args.phase == "start":
        ledger_append(root, {"kind": "spawn", "agent_type": agent_type, "agent_id": data.get("agent_id")})
        if role not in SNAPSHOT_ROLES:
            return 0
        folder.mkdir(parents=True, exist_ok=True)
        record = {"role": role, "agent_type": agent_type, "agent_id": data.get("agent_id"), "started": iso_now(),
                  "started_ts": time.time(), "evidence": evidence_files(root), "head": git_out(root, "rev-parse", "HEAD") or "none",
                  "files": {}, "partial": True}
        # Written before the tree is read, so a hook killed by its timeout still leaves a start record that says so.
        path.write_text(json.dumps(record) + "\n", encoding="utf-8")
        snapshot = tracked_state(root, budget=SNAPSHOT_BUDGET)
        record.update(snapshot)
        record.pop("partial", None)
        path.write_text(json.dumps(record) + "\n", encoding="utf-8")
        if snapshot["by_stat"]:
            gate_log(root, "SNAPSHOT {} {}: {} dirty file(s) compared by size and modification time, not content (past the "
                           "{}-file, {}-byte, or {:g}-second budget)".format(role, agent, snapshot["by_stat"], SNAPSHOT_MAX_FILES,
                                                                              SNAPSHOT_MAX_BYTES, SNAPSHOT_BUDGET))
        return 0
    if role not in SNAPSHOT_ROLES:
        return 0
    before, _ = load_json(path) if path.is_file() else (None, None)
    before = before if isinstance(before, dict) else None
    stopped_ts = time.time()
    transcript = data.get("agent_transcript_path")
    now_evidence = evidence_files(root)
    before_evidence = before.get("evidence") if before and isinstance(before.get("evidence"), dict) else None
    if before_evidence is None:
        gate_log(root, "SNAPSHOT no start record for {} {}; its evidence is recorded from its transcript alone and the review is "
                       "not judged for tree changes".format(role, agent))
        candidates = sorted(now_evidence)
    else:
        candidates = sorted(rel for rel, digest in now_evidence.items() if before_evidence.get(rel) != digest)
    # Claude Code writes transcripts asynchronously; give the last tool calls a moment to land before judging.
    deadline = time.time() + transcript_settle_seconds()
    while True:
        problems = {rel: transcript_problem(root, rel, transcript, agent_type, data.get("agent_id")) for rel in candidates}
        if not any(problems.values()) or time.time() >= deadline:
            break
        time.sleep(0.25)
    recorded = []
    ledger = None
    for rel in candidates:
        if problems.get(rel) is None and record_evidence(root, rel, agent_type, data.get("agent_id"),
                                                         (before or {}).get("started"), (before or {}).get("started_ts"), transcript):
            recorded.append(rel)
            continue
        # Overlapping reviewer windows: another reviewer wrote this file and its own stop already recorded these bytes.
        ledger = ledger_entries(root, "evidence") if ledger is None else ledger
        digest = file_sha256(root / rel)
        other = next((e for e in reversed(ledger) if digest and e.get("path") == rel and e.get("sha256") == digest
                      and e.get("agent_id") and str(e.get("agent_id")) != str(data.get("agent_id"))), None)
        if other:
            gate_log(root, "PROVENANCE NOTE {} {} {}: already recorded for {} {}".format(
                role, agent, rel, other.get("agent_type"), other.get("agent_id")))
        else:
            gate_log(root, "PROVENANCE REFUSED {} {} {}: {}".format(role, agent, rel, problems.get(rel) or "the file could not be read"))
    if recorded:
        gate_log(root, "PROVENANCE {} {} wrote {}".format(role, agent, ", ".join(recorded[:10])))
    if before is None:
        pass
    elif before.get("partial"):
        gate_log(root, "SNAPSHOT start for {} {} did not finish (the hook timed out); the review is not judged for tree changes".format(role, agent))
    else:
        changed, notes, untracked = snapshot_changes(root, before, tracked_state(root, like=before.get("files") or {}))
        if untracked:
            gate_log(root, "SNAPSHOT NOTE {} {}: untracked path(s) appeared, changed, or went away during the review and do not "
                           "void it: {}. lint --stop and --final report any the run leaves uncommitted; ignore build and test "
                           "artifacts in .gitignore".format(role, agent, listing(untracked, 20)))
        if changed or notes:
            detail = ", ".join(changed[:20] + notes)
            window = {"kind": "void", "agent_type": agent_type, "role": role, "agent_id": data.get("agent_id"),
                      "started": before.get("started"), "started_ts": before.get("started_ts"), "stopped": iso_now(),
                      "stopped_ts": stopped_ts, "detail": detail}
            ledger_append(root, window)
            try:
                (folder / "{}.void".format(agent)).write_text(json.dumps(window) + "\n", encoding="utf-8")
            except OSError:
                pass
            gate_log(root, "SNAPSHOT VOID {} {} changed: {}".format(role, agent, detail))
    ok, _ = derived_path_ok(path, [folder], evidence=True)
    if ok and path.is_file():
        path.unlink()
    return 0


# ----------------------------------------------------------------------------------------------
# guard: the constraints floor over staged, unstaged, and untracked files

SUPPRESSION_RE = re.compile(r"@ts-ignore|@ts-expect-error|@ts-nocheck|eslint-disable|#\s*noqa\b|#\s*type:\s*ignore|pylint:\s*disable|"
                            r"//\s*nolint|#!?\[allow\(|@SuppressWarnings|swiftlint:disable|rubocop:disable|istanbul ignore|"
                            r"\bc8 ignore|\bv8 ignore|pragma: no cover|#\s*nosec\b|NOSONAR|gitleaks:allow|nosemgrep|@Suppress\(|"
                            r"stryker disable|biome-ignore|deno-lint-ignore|phpcs:ignore|@phpstan-ignore|@psalm-suppress")
SKIP_RE = re.compile(r"\b(it|test|describe|context|suite|scenario)\.(skip|only|todo|fixme)\s*\(|\bx(it|describe|test|context)\s*\(|"
                     r"\bf(it|describe)\s*\(|@pytest\.mark\.(skip|skipif|xfail)\b|\bpytest\.skip\(|@unittest\.skip|\bunittest\.skip|"
                     r"\bself\.skipTest\(|@skip(If|Unless)?\b|^\s*from\s+unittest\s+import\s+[^\n]*\bskip|\bt\.Skip(Now|f)?\(|"
                     r"#\[ignore\]|\bXCTSkip|@Disabled\b|@Ignore\b|\bpending\s*\(|\bskip\s*:\s*true")
TRIVIAL_ASSERT_RE = re.compile(r"\bassert\s+(True|1)\s*(#.*)?$|assertTrue\(\s*(True|1)\s*\)|assert\.ok\(\s*true\s*\)|"
                               r"expect\(\s*true\s*\)\.(toBe|toEqual)\(\s*true\s*\)|XCTAssertTrue\(\s*true\s*\)|#expect\(\s*true\s*\)|"
                               r"\bassert!\(\s*true\s*\)")
SELF_EQUAL_RE = re.compile(r"assert(Equal|Equals|_eq!|Same)\(\s*([\w.\[\]'\"]+)\s*,\s*\2\s*\)|expect\(\s*([\w.]+)\s*\)\.(toBe|toEqual)\(\s*\3\s*\)")
EARLY_RETURN_RE = re.compile(r"^\s*return\s*;?\s*$")
TEST_HEADER_RE = re.compile(r"^\s*(async\s+)?def\s+test\w*\s*\(|^\s*(it|test)\s*\(|^\s*func\s+test\w*\s*\(|^\s*fn\s+test_\w*\s*\(|"
                            r"^\s*(public\s+)?void\s+test\w*\s*\(")
COLLECTION_CONFIG_RE = re.compile(r"^(conftest\.py|pytest\.ini|pyproject\.toml|setup\.cfg|tox\.ini|\.coveragerc|package\.json|"
                                  r"(jest|vitest|playwright|karma)\.config\.\w+)$")
COLLECTION_RE = re.compile(r"collect_ignore|--deselect|addopts[^\n]*(-k\s*['\"]?\s*not\b|--ignore)|testPathIgnorePatterns|"
                           r"modulePathIgnorePatterns|--cov-fail-under[= ]0\b|fail_under\s*=\s*0\b|passWithNoTests")
FAIL_UNDER_RE = re.compile(r"(?:fail_under|fail-under|--cov-fail-under)\s*[= ]\s*(\d+(?:\.\d+)?)")
DOC_SUFFIXES = {".md", ".mdx", ".markdown", ".rst", ".txt", ".adoc"}
EXACT_MATCHER_RE = re.compile(r"\.(toEqual|toStrictEqual|toBe)\(|\bassertEquals?\(|\bXCTAssertEqual\(|\bassert_eq!\(|\bassert\s+[^=\n#]+==")
LOOSE_MATCHER_RE = re.compile(r"\.(toBeDefined|toContain|toBeTruthy|toBeFalsy|toMatchObject|toBeGreaterThan|toBeLessThan)\(|"
                              r"\bassertTrue\(|\bassertIsNotNone\(|\bXCTAssertNotNil\(|\bassert\s+[\w.\[\]()'\"]+\s*(#.*)?$")
PRECISION_RE = re.compile(r"(?:toBeCloseTo\([^,()]+(?:\([^()]*\))?[^,()]*,\s*|\bplaces\s*=\s*|\bdecimal\s*=\s*)(\d+)")
TOLERANCE_RE = re.compile(r"\b(?:delta|abs_tol|rel_tol|tolerance|epsilon|accuracy|maxDiffPixels|maxDiffPixelRatio|threshold)\s*[=:]\s*"
                          r"(\d+(?:\.\d+)?(?:[eE]-?\d+)?)")
RETRY_RE = re.compile(r"\b(?:retries|retryTimes|reruns)\s*[=:(]\s*(\d+)|jest\.retryTimes\(\s*(\d+)|@pytest\.mark\.flaky\b|@flaky\b")
TRY_RE = re.compile(r"^\s*try\s*(:|\{)?\s*$|^\s*try\s*\{")
RUNNER_CONFIG_RE = re.compile(r"^(jest|vitest|playwright|karma)\.config\.\w+$")
SUITE_EXCLUDE_RE = re.compile(r"\b(testPathIgnorePatterns|testIgnore|exclude)\b\s*[:=]")
SUITE_SCOPE_KEYS = ("testMatch", "testRegex", "include", "testDir")
QUOTED_RE = re.compile(r"['\"`][^'\"`]+['\"`]")
TEST_ONLY_BRANCH_RE = re.compile(r"NODE_ENV\s*[!=]==?\s*['\"]test['\"]|process\.env\.(VITEST|JEST_WORKER_ID)\b|"
                                 r"['\"]pytest['\"]\s+in\s+sys\.modules|XCTestConfigurationFilePath")
SOURCE_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".py", ".swift", ".go", ".rb", ".kt", ".java", ".m", ".rs", ".cs", ".php"}


def is_number(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def test_header_before(lines, number):
    """True when the line before `number` (1-based), skipping blank lines, comments, and a docstring, opens a test."""
    index, steps = number - 2, 0
    while index >= 0 and steps < 5:
        text = lines[index].strip()
        if not text or text.startswith(("#", "//")) or text[:1] in ("'", '"'):
            index -= 1
            steps += 1
            continue
        return bool(TEST_HEADER_RE.match(lines[index]))
    return False
STUB_RE = re.compile(r"(?i)raise\s+NotImplementedError|throw\s+new\s+Error\s*\(\s*['\"`]\s*(not\s+implemented|todo|unimplemented)|"
                     r"NotImplementedException\s*\(|\bunimplemented!\s*\(|\btodo!\s*\(|fatalError\s*\(\s*\"(not implemented|todo|unimplemented)|"
                     r"panic\s*\(\s*\"(todo|not implemented|unimplemented)|\b(TODO|FIXME)\b:?\s*implement")
EMPTY_CATCH_RE = re.compile(r"catch\s*(\([^)]*\))?\s*\{\s*\}|\.catch\(\s*(\(\s*\w*\s*\)|\w+)\s*=>\s*\{\s*\}\s*\)|"
                            r"except(\s+[\w.,\s()]+)?\s*:\s*pass\b|rescue\s*(=>\s*\w+)?\s*nil\b|if\s+err\s*!=\s*nil\s*\{\s*\}")
OPEN_CATCH_RE = re.compile(r"(catch\s*(\([^)]*\))?\s*\{|except(\s+[\w.,\s()]+)?\s*:)\s*$")
ASSERT_RE = re.compile(r"\bassert|\bexpect\s*\(|XCTAssert|#expect\s*\(|#require\s*\(|\.should\b|\bshould\.|\brequire\.\w+\(|"
                       r"\bt\.(Error|Errorf|Fatal|Fatalf|Fail)\b|\.to(Be|Equal|Have|Throw|Match|Contain|StrictEqual)|\brefute\b")
CONSTRAINT_FILES = (".drive/CONSTRAINTS.md", "CONSTRAINTS.md")


class GuardError(Exception):
    pass


def diff_changes(root, base):
    code, out, err = git(root, "-c", "core.quotePath=false", "diff", "--no-color", "--no-ext-diff", "-U0", "-M", base, "--")
    if code != 0:
        raise GuardError(err.strip() or "git diff failed")
    changes, current, new_line, in_hunk = [], None, 0, False
    for line in out.splitlines():
        if line.startswith("diff --git "):
            match = re.match(r"^diff --git a/(.+) b/(.+)$", line)
            current = {"path": match.group(2) if match else line.rsplit(" b/", 1)[-1], "status": "M", "added": [], "removed": [],
                       "old_path": match.group(1) if match else None}
            changes.append(current)
            in_hunk = False
            continue
        if current is None:
            continue
        if not in_hunk:
            if line.startswith("new file mode"):
                current["status"] = "A"
            elif line.startswith("deleted file mode"):
                current["status"] = "D"
            elif line.startswith("Binary files"):
                current["binary"] = True
        if line.startswith("@@"):
            match = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            new_line = int(match.group(1)) if match else 0
            in_hunk = True
            continue
        if not in_hunk:
            continue
        if line.startswith("+"):
            current["added"].append((new_line, line[1:]))
            new_line += 1
        elif line.startswith("-"):
            current["removed"].append(line[1:])
    return changes


def untracked_changes(root):
    code, out, err = git(root, "ls-files", "--others", "--exclude-standard", "-z")
    if code != 0:
        raise GuardError(err.strip() or "git ls-files failed")
    changes = []
    for rel in [p for p in out.split("\0") if p]:
        path = Path(root) / rel
        try:
            if not path.is_file() or path.stat().st_size > 2_000_000:
                continue
            data = path.read_bytes()
        except OSError:
            continue
        if b"\0" in data[:8192]:
            continue
        text = data.decode("utf-8", errors="replace")
        changes.append({"path": rel, "status": "?", "added": list(enumerate(text.splitlines(), 1)), "removed": []})
    return changes


def first_number(value):
    match = NUMBER_RE.search(value or "")
    return float(match.group(0)) if match else None


def constraint_loosenings(old_text, new_text):
    """Loosening moves between two versions of CONSTRAINTS.md. Numbers are compared only in the
    measured, tolerance, and target columns; dates are never compared."""
    old, new = constraint_tables(old_text), constraint_tables(new_text)
    out = []
    for rule in old["floor"]:
        if rule not in new["floor"]:
            out.append("the floor rule '{}' was removed or reworded".format(rule[:80]))
    for section in ("Enforced", "Measured only"):
        for rule, row in old[section].items():
            now = new[section].get(rule)
            if now is None:
                out.append("{} row '{}' was removed".format(section, rule))
                continue
            direction = row.get("direction") or ""
            if (now.get("direction") or "") != direction:
                out.append("{} row '{}' changed direction".format(section, rule))
            if (now.get("command") or "").strip() != (row.get("command") or "").strip():
                out.append("{} row '{}' changed its command".format(section, rule))
            if section != "Enforced":
                continue
            for column in ("measured", "target"):
                before, after = first_number(row.get(column)), first_number(now.get(column))
                if before is None or after is None:
                    continue
                if direction == "must not fall" and after < before:
                    out.append("Enforced row '{}' lowered its {} from {} to {}".format(rule, column, row.get(column), now.get(column)))
                if direction == "must not grow" and after > before:
                    out.append("Enforced row '{}' raised its {} from {} to {}".format(rule, column, row.get(column), now.get(column)))
            t_before, t_after = first_number(row.get("tolerance")), first_number(now.get("tolerance"))
            if t_before is not None and t_after is not None and t_after > t_before:
                out.append("Enforced row '{}' widened its tolerance from {} to {}".format(rule, row.get("tolerance"), now.get("tolerance")))
    return out


def active_exceptions(text, decisions_text):
    """(rule, path glob) for each recorded exception; a path cell may name several globs separated by commas."""
    rows = constraint_tables(text or "")["Exceptions"] if text else {}
    keys = decision_keys(decisions_text)
    out = []
    for rule, row in rows.items():
        if row.get("path") and row.get("reason") and decision_reference_ok(row.get("decision", ""), keys):
            out.extend((rule.strip(), glob) for glob in (part.strip().strip("`").strip() for part in row["path"].split(",")) if glob)
    return out


BROAD_EXCEPTIONS = {"Exception", "BaseException", "AssertionError"}
CATCH_WORD_RE = re.compile(r"\b(catch|except|rescue)\b")


def python_swallowing_try_lines(text):
    """Line numbers of Python try statements whose body asserts and whose broad handler (bare, Exception,
    BaseException, or AssertionError) does not re-raise, so a failing assertion would be swallowed. A try with only
    finally, or with a narrow handler, cannot swallow one. None when the text does not parse."""
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return None
    try_types = (ast.Try,) + ((ast.TryStar,) if hasattr(ast, "TryStar") else ())
    lines = set()
    for node in ast.walk(tree):
        if not isinstance(node, try_types) or not node.handlers:
            continue
        asserts = any(isinstance(n, ast.Assert) or (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                                                    and n.func.attr.startswith(("assert", "fail")))
                      for part in node.body for n in ast.walk(part))
        if not asserts:
            continue
        for handler in node.handlers:
            kinds = list(handler.type.elts) if isinstance(handler.type, ast.Tuple) else [handler.type]
            broad = handler.type is None or any(
                (isinstance(k, ast.Name) and k.id in BROAD_EXCEPTIONS) or (isinstance(k, ast.Attribute) and k.attr in BROAD_EXCEPTIONS)
                for k in kinds)
            if broad and not any(isinstance(n, ast.Raise) for part in handler.body for n in ast.walk(part)):
                lines.add(node.lineno)
    return lines


def run_floor_guard(root, base="HEAD"):
    """Returns (violations, error). Each violation is (rule, location, message)."""
    if not is_git_repo(root):
        return [], "{} is not a git repository".format(root)
    if git(root, "rev-parse", "--verify", "--quiet", base + "^{commit}")[0] != 0:
        return [], "the base {} does not resolve to a commit".format(base)
    try:
        changes = diff_changes(root, base) + untracked_changes(root)
    except GuardError as exc:
        return [], str(exc)
    today = now_utc().date()
    violations = []
    for change in changes:
        rel = change["path"]
        if change.get("binary"):
            continue
        if rel in CONSTRAINT_FILES:
            old_text = show_at(root, base, rel)
            new_text = read_text(Path(root) / rel)
            if old_text is not None and new_text is not None:
                for what in constraint_loosenings(old_text, new_text):
                    violations.append(("loosened-constraint", rel, what + "; a loosening is its own commit with evidence"))
            old_exceptions = constraint_tables(old_text or "")["Exceptions"]
            keys = decision_keys(read_text(Path(root) / ".drive" / "DECISIONS.md"))
            for rule, row in constraint_tables(new_text or "")["Exceptions"].items():
                if rule in old_exceptions:
                    continue
                if not (row.get("path") and row.get("reason") and row.get("undo")) or not decision_reference_ok(row.get("decision", ""), keys):
                    violations.append(("exception", rel, "the new exception '{}' needs a path, a reason, an undo, and a DECISIONS.md entry that exists".format(rule)))
            continue
        if rel.startswith(".drive/"):
            continue
        test = is_test_path(rel)
        old_path = change.get("old_path")
        if old_path and old_path != rel and is_test_path(old_path) and not test:
            violations.append(("test-moved", rel, "a test file was moved out of test discovery ({} to {})".format(old_path, rel)))
        if change["status"] == "D":
            if test:
                violations.append(("deleted-test", rel, "a test file was deleted"))
            continue
        added = change["added"]
        doc = Path(rel).suffix.lower() in DOC_SUFFIXES
        config = bool(COLLECTION_CONFIG_RE.match(rel.rsplit("/", 1)[-1]))
        new_lines = (read_text(Path(root) / rel) or "").splitlines() if test else []
        for index, (number, text) in enumerate(added):
            where = "{}:{}".format(rel, number)
            if not doc and SUPPRESSION_RE.search(text):
                violations.append(("suppression", where, "a suppression comment was added"))
            if test and SKIP_RE.search(text):
                violations.append(("skip", where, "a test was skipped or focused"))
            if test and (TRIVIAL_ASSERT_RE.search(text) or SELF_EQUAL_RE.search(text)):
                violations.append(("trivial-assertion", where, "an assertion that cannot fail was added"))
            if test and EARLY_RETURN_RE.match(text) and test_header_before(new_lines, number):
                violations.append(("early-return", where, "a test now returns before it asserts anything"))
            if config and COLLECTION_RE.search(text):
                violations.append(("test-collection", where, "tests were excluded from collection or the coverage floor was zeroed"))
            if not doc and STUB_RE.search(text):
                violations.append(("stub", where, "a stub or not-implemented placeholder was added"))
            if doc:
                pass
            elif EMPTY_CATCH_RE.search(text):
                violations.append(("empty-catch", where, "an empty catch was added"))
            elif OPEN_CATCH_RE.search(text) and index + 1 < len(added) and added[index + 1][0] == number + 1 \
                    and added[index + 1][1].strip() in ("}", "pass", "} catch {}", "end"):
                violations.append(("empty-catch", where, "an empty catch was added"))
            for label, pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    violations.append(("secret", where, "what looks like {} was added (value not shown)".format(label)))
                    break
        runner_config = bool(RUNNER_CONFIG_RE.match(rel.rsplit("/", 1)[-1]))
        if test and change["status"] == "M":
            added_text = [line for _, line in added]
            exact_lost = sum(1 for l in change["removed"] if EXACT_MATCHER_RE.search(l)) - sum(1 for l in added_text if EXACT_MATCHER_RE.search(l))
            loose_gained = sum(1 for l in added_text if LOOSE_MATCHER_RE.search(l)) - sum(1 for l in change["removed"] if LOOSE_MATCHER_RE.search(l))
            if exact_lost > 0 and loose_gained > 0:
                violations.append(("weakened-assertion", rel, "{} exact assertion(s) replaced by looser matchers".format(exact_lost)))
        if test or config:
            for label, pattern, lower_is_looser in (("precision", PRECISION_RE, True), ("tolerance", TOLERANCE_RE, False)):
                old = [float(v) for line in change["removed"] for v in pattern.findall(line) if is_number(v)]
                if not old:
                    continue
                for number, text in added:
                    for value in (float(v) for v in pattern.findall(text) if is_number(v)):
                        if (lower_is_looser and value < min(old)) or (not lower_is_looser and value > max(old)):
                            violations.append(("loosened-" + label, "{}:{}".format(rel, number), "a {} was loosened from {:g} to {:g}".format(
                                label, min(old) if lower_is_looser else max(old), value)))
            for number, text in added:
                found = RETRY_RE.search(text)
                if found:
                    values = [int(g) for g in found.groups() if g and g.isdigit()]
                    if not values or max(values) > 2:
                        violations.append(("retry-added", "{}:{}".format(rel, number), "a retry was added or raised above 2"))
        if test:
            swallowing = python_swallowing_try_lines("\n".join(new_lines)) if rel.endswith(".py") else None
            for index, (number, text) in enumerate(added):
                if not TRY_RE.match(text):
                    continue
                if swallowing is not None:
                    wrapped = number in swallowing
                else:
                    # Outside Python, a try with only finally cannot swallow an assertion; require a catch after it.
                    wrapped = any(ASSERT_RE.search(line) for n, line in added[index + 1:index + 4] if n <= number + 3) \
                        and any(CATCH_WORD_RE.search(line) for line in new_lines[number:number + 30])
                if wrapped:
                    violations.append(("wrapped-assertion", "{}:{}".format(rel, number),
                                       "an assertion was wrapped in try with a handler that swallows its failure"))
        if runner_config:
            for number, text in added:
                if SUITE_EXCLUDE_RE.search(text):
                    violations.append(("suite-narrowed", "{}:{}".format(rel, number), "tests were excluded from discovery"))
            for key in SUITE_SCOPE_KEYS:
                key_re = re.compile(r"\b{}\b\s*[:=]".format(key))
                old = [len(QUOTED_RE.findall(l)) for l in change["removed"] if key_re.search(l)]
                for number, text in added:
                    if key_re.search(text) and old and len(QUOTED_RE.findall(text)) < max(old):
                        violations.append(("suite-narrowed", "{}:{}".format(rel, number), "{} now matches fewer test files".format(key)))
        if not test and not doc and not config and Path(rel).suffix.lower() in SOURCE_SUFFIXES:
            for number, text in added:
                if TEST_ONLY_BRANCH_RE.search(text):
                    violations.append(("test-only-branch", "{}:{}".format(rel, number), "production code now branches on running under a test"))
        if config:
            before = [float(m.group(1)) for line in change["removed"] for m in [FAIL_UNDER_RE.search(line)] if m]
            for number, text in added:
                found = FAIL_UNDER_RE.search(text)
                if found and before and float(found.group(1)) < max(before):
                    violations.append(("coverage-floor", "{}:{}".format(rel, number), "the coverage floor was lowered from {:g} to {:g}".format(
                        max(before), float(found.group(1)))))
        if test and change["status"] == "M":
            removed = sum(1 for line in change["removed"] if ASSERT_RE.search(line))
            gained = sum(1 for _, line in added if ASSERT_RE.search(line))
            if removed > gained:
                violations.append(("removed-assertion", rel, "{} assertion line(s) removed and not replaced".format(removed - gained)))
    exceptions = []
    decisions = read_text(Path(root) / ".drive" / "DECISIONS.md")
    for name in CONSTRAINT_FILES:
        exceptions.extend(active_exceptions(read_text(Path(root) / name), decisions))
    kept = []
    for rule, where, message in violations:
        path = where.split(":", 1)[0]
        if any(rule == r and p and glob_matches(path, p) for r, p in exceptions):
            continue
        kept.append((rule, where, message))
    return kept, None


def cmd_guard(args):
    start = Path(args.root or os.getcwd())
    top = git_out(start, "rev-parse", "--show-toplevel")
    if not top:
        print("drive guard could not run: {} is not inside a git repository. Treat this as a failure.".format(start))
        return 2
    base = args.base or default_guard_base(Path(top))
    violations, error = run_floor_guard(Path(top), base)
    if error:
        print("drive guard could not run: {}. Treat this as a failure.".format(error))
        return 2
    for rule, where, message in violations:
        print("{} · {} · {}".format(rule, where, message))
    if violations:
        print("drive guard: {} violation(s) against {}. Fix the code rather than lowering the bar; a genuine exception goes in CONSTRAINTS.md with a reason, an undo, and its DECISIONS.md entry.".format(len(violations), base))
        return 1
    print("drive guard: clean against {}.".format(base))
    return 0


# ----------------------------------------------------------------------------------------------
# worktree-land


def cmd_worktree_land(args):
    """Land an experiment arm: a detached worktree whose HEAD is the recorded sha. Its commits are
    cherry-picked onto the main checkout's current branch, the worktree is removed and pruned, and no
    branch is created, merged, or left behind."""
    cwd = Path(args.root or os.getcwd())
    top = git_out(cwd, "rev-parse", "--show-toplevel")
    main = main_worktree_root(cwd)
    if not top or not main or Path(top).resolve() != main.resolve():
        print("drive worktree-land: run it from the main checkout, not from inside a worktree.")
        return 1
    root = main
    raw, sha = args.worktree, args.sha
    entries = worktree_entries(root)
    matches = [e for e in entries[1:] if os.path.realpath(e.get("worktree", "")) == os.path.realpath(raw)]
    if not matches:
        if git_out(root, "rev-parse", "--verify", "--quiet", "refs/heads/" + raw):
            print("drive worktree-land: {} is a branch. Pass the arm's worktree path instead: arms are detached worktrees "
                  "(git worktree add --detach <path> HEAD) and land by cherry-picking their commits, so no branch is created "
                  "or left behind.".format(raw))
        else:
            print("drive worktree-land: {} is not a registered worktree of {}.".format(raw, root))
        return 1
    entry = matches[0]
    wt_path = Path(entry["worktree"])
    expected = git_out(root, "rev-parse", "--verify", "--quiet", sha + "^{commit}")
    if not expected:
        print("drive worktree-land: {} is not a commit.".format(sha))
        return 1
    tip = git_out(wt_path, "rev-parse", "HEAD")
    if tip != expected:
        gate_log(root, "LAND REFUSED {} moved from {} to {}".format(wt_path, expected[:7], (tip or "?")[:7]))
        print("drive worktree-land: the worktree {} moved after {} was recorded (it is now at {}). Read the new work, record "
              "its sha, and land again.".format(wt_path, sha, (tip or "?")[:7]))
        return 2
    wt_dirty = porcelain_paths(wt_path) or []
    if wt_dirty:
        print("drive worktree-land: the worktree {} has uncommitted changes ({}). Commit the reported paths in the worktree, or "
              "remove it deliberately.".format(wt_path, ", ".join(p for _, p in wt_dirty[:5])))
        return 1
    dirty = [p for _, p in (porcelain_paths(root) or []) if not p.startswith(".drive/local/")]
    if dirty:
        print("drive worktree-land: the main checkout has uncommitted changes ({}). Commit or restore them first.".format(", ".join(dirty[:5])))
        return 1
    current_branch = git_out(root, "symbolic-ref", "--short", "-q", "HEAD")
    started_on = (read_baseline(root) or {}).get("branch")
    if not current_branch:
        print("drive worktree-land: the main checkout is on a detached HEAD. Land onto the branch the run started on{}.".format(
            " ({})".format(started_on) if started_on else ""))
        return 1
    if started_on and current_branch != started_on:
        print("drive worktree-land: the main checkout is on {}, but the run started on {}. Runs never change branches; switch back "
              "before landing.".format(current_branch, started_on))
        return 1
    ok, reason = derived_path_ok(wt_path, tmp_roots() + [root / ".claude" / "worktrees"], evidence=True)
    if not ok:
        gate_log(root, "LAND REFUSED {}".format(reason))
        print("drive worktree-land refused to remove the worktree: {}.".format(reason))
        return 2
    pre = git_out(root, "rev-parse", "HEAD")
    base = git_out(root, "merge-base", pre, expected)
    commits = (git_out(root, "rev-list", "--reverse", "{}..{}".format(base, expected)) or "").split() if base else []
    if not commits:
        print("drive worktree-land: {} holds no commits that are not already on the main checkout.".format(wt_path))
        return 1
    code, out, err = git(root, "cherry-pick", *commits)
    if code != 0:
        git(root, "cherry-pick", "--abort")
        print("drive worktree-land: the arm's commits do not apply cleanly; the cherry-pick was aborted and the worktree kept. "
              "Rebase inside the worktree or re-scope the arm.\n{}".format((out + err).strip()[-800:]))
        return 1
    code, out, err = git(root, "worktree", "remove", "--force", str(wt_path))
    if code != 0:
        print("drive worktree-land: landed, but removing {} failed: {}".format(wt_path, err.strip()))
        return 1
    git(root, "worktree", "prune")
    note = ""
    branch = str(entry.get("branch", ""))
    if branch.startswith("refs/heads/"):
        name = branch[len("refs/heads/"):]
        if fnmatch.fnmatchcase(name, "drive/*"):
            git(root, "branch", "-D", name)
            note = "; deleted the arm's branch {}".format(name)
        else:
            note = "; the worktree was on branch {}, which is left in place".format(name)
    head = git_out(root, "rev-parse", "HEAD")
    gate_log(root, "LAND {} {} commit(s) by cherry-pick (was {}, now {}){}".format(wt_path, len(commits), pre[:7], head[:7], note))
    print("Landed {} commit(s) from {} by cherry-pick (HEAD was {}, now {}); removed the worktree and pruned{}. Undo with: "
          "git revert --no-edit {}..HEAD".format(len(commits), wt_path, pre[:7], head[:7], note, pre[:7]))
    return 0


# ----------------------------------------------------------------------------------------------
# freeze: refutation tests frozen before implementation (references/testing.md section 9)


def parked_files(root):
    latest = {}
    for entry in ledger_entries(root, "freeze-park"):
        for path in entry.get("paths") or []:
            latest[path] = entry
    return {p: e.get("key") for p, e in latest.items() if e.get("action") == "park"}


def paths_for_key(root, key, files):
    """The frozen files tied to a claim key: those its STATUS row cites and those its TESTPLAN.md row names."""
    cited = []
    status = read_text(Path(root) / ".drive" / "STATUS.md")
    if status:
        row = Status(status).by_key().get(key)
        if row is not None:
            for kind in ("test", "severe", "planned"):
                cited.extend(normalise_rel(v.split("::", 1)[0]) for v in row.values(kind))
    for line in (read_text(Path(root) / ".drive" / "TESTPLAN.md") or "").splitlines():
        if re.search(r"(?<![A-Za-z0-9\-]){}(?![A-Za-z0-9\-])".format(re.escape(key)), line):
            cited.extend(f for f in files if f in line)
    return sorted({f for f in files for c in cited if c and (f == c or f.startswith(c + "/"))})


def resolve_cli_path(root, raw):
    path = Path(raw) if os.path.isabs(raw) else Path(os.getcwd()) / raw
    rel = rel_in_root(path, root)
    return normalise_rel(rel) if rel is not None else None


def freeze_problems(root, base=None):
    """Every way the tree, the list, or the manifest departs from what drive.py freeze recorded."""
    root = Path(root)
    problems = []
    entries = frozen_entries(root)
    manifest = frozen_manifest(root)
    recorded = {(e.get("path"), e.get("sha256")) for e in ledger_entries(root, "frozen")}
    parked = parked_files(root)
    for rel, digest in sorted(manifest.items()):
        if rel in parked:
            copy = root / FROZEN_PARKED / str(parked[rel]) / rel
            if not copy.is_file():
                problems.append("MISSING {}: parked for {} and the parked copy is gone".format(rel, parked[rel]))
            elif file_sha256(copy) != digest:
                problems.append("CHANGED {}: the parked copy no longer matches its hash".format(rel))
        elif not (root / rel).is_file():
            problems.append("MISSING {}: hashed in the manifest and gone from the tree".format(rel))
        elif file_sha256(root / rel) != digest:
            problems.append("CHANGED {}: its sha256 differs from the manifest".format(rel))
        if (rel, digest) not in recorded:
            problems.append("UNRECORDED {}: this manifest line was not written by drive.py freeze (no provenance ledger entry)".format(rel))
        if not any(rel == e or rel.startswith(e + "/") for e in entries):
            problems.append("REMOVED {}: hashed in the manifest but no longer listed in .drive/frozen.txt".format(rel))
    for entry in entries:
        if not any(f == entry or f.startswith(entry + "/") for f in manifest):
            problems.append("UNHASHED {}: listed in .drive/frozen.txt with no manifest line; run drive.py freeze add".format(entry))
        for rel in files_under(root, entry):
            if rel not in manifest:
                problems.append("ADDED {}: a file under the frozen {} with no manifest line".format(rel, entry))
    if base:
        base_manifest = frozen_manifest(root, show_at(root, base, FROZEN_MANIFEST) or "")
        base_entries = [normalise_rel(l) for l in (show_at(root, base, FROZEN_LIST) or "").splitlines()
                        if l.strip() and not l.strip().startswith("#")]
        amended = {p for e in ledger_entries(root, "freeze-amend") for p in e.get("paths") or []}
        rehashed = {(e.get("path"), e.get("sha256")) for e in ledger_entries(root, "frozen") if e.get("via") == "amend"}
        for rel, digest in sorted(base_manifest.items()):
            if rel not in manifest:
                if rel not in amended:
                    problems.append("REMOVED {}: frozen at {} and gone from the manifest without an amendment".format(rel, base[:7]))
            elif manifest[rel] != digest and (rel, manifest[rel]) not in rehashed:
                problems.append("REHASHED {}: its manifest hash changed since {} without a closed amendment".format(rel, base[:7]))
        for entry in base_entries:
            if entry not in entries and not any(p == entry or p.startswith(entry + "/") for p in amended):
                problems.append("REMOVED {}: listed in .drive/frozen.txt at {} and no longer listed".format(entry, base[:7]))
    return problems


def freeze_add(root, targets):
    if not targets:
        print("drive freeze add: name the test paths to freeze.")
        return 2
    manifest = frozen_manifest(root)
    resolved = []
    for raw in targets:
        rel = resolve_cli_path(root, raw)
        if not rel or rel == "." or rel == ".drive" or rel.startswith(".drive/") or rel.startswith(".git"):
            print("drive freeze add: {} is not a path inside the project and outside .drive/.".format(raw))
            return 2
        files = files_under(root, rel)
        if not files:
            print("drive freeze add: {} does not exist. Write the test and show it red before freezing it.".format(raw))
            return 2
        resolved.append((rel, files))
    changed = [f for _, files in resolved for f in files if f in manifest and manifest[f] != file_sha256(root / f)]
    if changed:
        print("drive freeze add: {} changed since it was frozen, and freeze add never rehashes a frozen file. Run drive.py freeze "
              "check; a frozen test changes only through an amendment.".format(", ".join(changed)))
        return 1
    entries = frozen_entries(root)
    added = []
    for rel, files in resolved:
        if rel not in entries:
            entries.append(rel)
        for f in files:
            if f not in manifest:
                manifest[f] = file_sha256(root / f)
                ledger_append(root, {"kind": "frozen", "path": f, "sha256": manifest[f], "via": "add"})
                added.append(f)
    (root / FROZEN_LIST).write_text("\n".join(entries) + "\n", encoding="utf-8")
    write_manifest(root, manifest)
    gate_log(root, "FREEZE add {}".format(", ".join(added) or "nothing new"))
    print("Froze {} file(s){}. The guard now refuses every write to them; commit them with the package that turns them green, "
          "together with .drive/frozen.txt and .drive/frozen.sha256.".format(len(added), ": " + ", ".join(added[:10]) if added else ""))
    return 0


def freeze_park(root, key, unpark=False):
    action = "unpark" if unpark else "park"
    manifest = frozen_manifest(root)
    paths = paths_for_key(root, key, sorted(manifest))
    if not paths:
        print("drive freeze {}: no frozen file is tied to {}; cite it in the STATUS row's test: token or the TESTPLAN.md row.".format(action, key))
        return 1
    moves = []
    for rel in paths:
        parked_copy = root / FROZEN_PARKED / key / rel
        src, dst = (parked_copy, root / rel) if unpark else (root / rel, parked_copy)
        if not src.is_file():
            print("drive freeze {}: {} is not there to {}.".format(action, src, action))
            return 1
        if file_sha256(src) != manifest[rel]:
            print("drive freeze {}: {} changed since it was frozen, so {} refuses it.".format(action, rel, action))
            return 1
        if dst.exists():
            print("drive freeze {}: {} already exists; move nothing over it.".format(action, dst))
            return 1
        moves.append((src, dst))
    for src, dst in moves:
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
    ledger_append(root, {"kind": "freeze-park", "action": action, "key": key, "paths": paths})
    gate_log(root, "FREEZE {} {} {}".format(action, key, ", ".join(paths)))
    print("{} {} frozen file(s) for {}: {}.".format("Unparked" if unpark else "Parked", len(paths), key, ", ".join(paths)))
    return 0


def freeze_amend(root, targets, opening, closing, dispute):
    if opening == closing:
        print("drive freeze amend: pass exactly one of --open or --close.")
        return 2
    if len(targets) != 1:
        print("drive freeze amend: name one claim key or one frozen path.")
        return 2
    manifest = frozen_manifest(root)
    rel_target = resolve_cli_path(root, targets[0])
    direct = [f for f in manifest if rel_target and (f == rel_target or f.startswith(rel_target + "/"))]
    key = None if direct else targets[0]
    paths = direct or paths_for_key(root, targets[0], sorted(manifest))
    if not paths:
        print("drive freeze amend: {} is neither a frozen path nor a claim key tied to one.".format(targets[0]))
        return 1
    if opening:
        record = Path(dispute) if dispute and os.path.isabs(dispute) else (Path(os.getcwd()) / dispute if dispute else None)
        if record is None and key:
            found = sorted((root / ".drive" / "reviews").glob("*-dispute-{}.md".format(key)))
            record = found[-1] if found else None
        text = read_text(record) if record is not None else None
        if not text or not re.search(r"\b(not_a_defect|rubric_ambiguous)\b", text):
            print("drive freeze amend --open: needs the test dispute record with the auditor's not_a_defect or rubric_ambiguous ruling "
                  "(--dispute .drive/reviews/<date>-dispute-<key>.md).")
            return 1
        _, decisions = decision_entries(read_text(root / ".drive" / "DECISIONS.md") or "")
        names = ([key] if key else []) + paths
        bodies = [heading + "\n" + "\n".join(l for _, l in lines) for heading, lines in decisions]
        if not any(any(n in body for n in names) and re.search(r"(?i)amend|not_a_defect|rubric_ambiguous", body) for body in bodies):
            print("drive freeze amend --open: DECISIONS.md has no entry recording the amendment of {}; write it first.".format(key or paths[0]))
            return 1
        ledger_append(root, {"kind": "freeze-amend", "state": "open", "key": key, "paths": paths,
                             "dispute": rel_in_root(record, root) or str(record)})
        gate_log(root, "FREEZE amend open {}".format(", ".join(paths)))
        print("Opened an amendment for {}: only drive:severe-tester may change it until drive.py freeze amend --close.".format(", ".join(paths)))
        return 0
    still_open = open_amendments(root)
    if not all(p in still_open for p in paths):
        print("drive freeze amend --close: no amendment is open for {}.".format(", ".join(p for p in paths if p not in still_open)))
        return 1
    missing = [p for p in paths if not (root / p).is_file()]
    if missing:
        print("drive freeze amend --close: {} is missing; the amended test must exist.".format(", ".join(missing)))
        return 1
    for rel in paths:
        manifest[rel] = file_sha256(root / rel)
        ledger_append(root, {"kind": "frozen", "path": rel, "sha256": manifest[rel], "via": "amend"})
    write_manifest(root, manifest)
    ledger_append(root, {"kind": "freeze-amend", "state": "closed", "key": key, "paths": paths})
    gate_log(root, "FREEZE amend close {}".format(", ".join(paths)))
    print("Closed the amendment and rehashed {} file(s): {}.".format(len(paths), ", ".join(paths)))
    return 0


def cmd_freeze(args):
    root = find_root(args.root or os.getcwd())
    if not (root / ".drive").is_dir():
        print("drive freeze: {} has no .drive/ directory.".format(root))
        return 2
    targets = list(args.targets or [])
    if args.action == "add":
        return freeze_add(root, targets)
    if args.action == "check":
        if args.base and not commit_exists(root, args.base):
            print("drive freeze check: --base {} is not a commit.".format(args.base))
            return 2
        if not (root / FROZEN_LIST).is_file() and not (root / FROZEN_MANIFEST).is_file():
            print("drive freeze check: this run has no frozen tests.")
            return 0
        problems = freeze_problems(root, args.base)
        for problem in problems:
            print(problem)
        if problems:
            print("drive freeze check: {} problem(s); each is a blocking gap.".format(len(problems)))
            return 1
        print("drive freeze check: clean ({} frozen file(s){}).".format(len(frozen_manifest(root)), " against " + args.base if args.base else ""))
        return 0
    if args.action in ("park", "unpark"):
        if len(targets) != 1:
            print("drive freeze {}: name one claim key.".format(args.action))
            return 2
        return freeze_park(root, targets[0], unpark=args.action == "unpark")
    return freeze_amend(root, targets, args.open, args.close, args.dispute)


# ----------------------------------------------------------------------------------------------
# visibility and preflight


def parse_remote(url):
    """(host, owner/repository) for a network remote, or None for a local path."""
    if not url or url.startswith("file://") or url.startswith("/") or url.startswith("."):
        return None
    match = re.match(r"^(?:https?|ssh|git)://(?:[^@/]+@)?([\w.\-]+)(?::\d+)?/(.+?)(?:\.git)?/?$", url)
    if match:
        return match.group(1), match.group(2)
    match = re.match(r"^(?:[\w.\-]+@)?([\w.\-]+\.[\w.\-]+):(?!/)(.+?)(?:\.git)?/?$", url)
    if match:
        return match.group(1), match.group(2)
    return None


def http_status(url, timeout=8):
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "drive-visibility-check"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:
        return None


def anonymous_ls_remote(url, timeout=15):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_ASKPASS="/usr/bin/false", SSH_ASKPASS="/usr/bin/false")
    code, _, err = run(["git", "-c", "credential.helper=", "ls-remote", "--heads", url], timeout=timeout, env=env)
    return code, err


def repo_visibility(root, gh=None, http=None, ls_remote=None):
    """("PUBLIC" or "PRIVATE", reason). Anything that cannot be established counts as PUBLIC, so a missing or
    unauthenticated gh never lets proofs and reviews be committed to a public repository."""
    origin = git_out(root, "remote", "get-url", "origin") if is_git_repo(root) else None
    if not origin:
        return "PRIVATE", "the repository has no origin remote, so nothing it commits is published"
    if gh is None:
        gh = (lambda: run(["gh", "repo", "view", "--json", "visibility", "-q", ".visibility"], cwd=root, timeout=15)) \
            if shutil.which("gh") else (lambda: (127, "", "gh is not installed"))
    code, out, err = gh()
    answer = (out or "").strip().upper()
    if code == 0 and answer in ("PUBLIC", "PRIVATE", "INTERNAL"):
        return ("PUBLIC" if answer == "PUBLIC" else "PRIVATE"), "gh repo view reports {}".format(answer)
    parsed = parse_remote(origin)
    if parsed is None:
        return "PRIVATE", "origin {} is a local path".format(origin)
    host, path = parsed
    why_gh = "gh gave no answer ({})".format((err or out or "exit {}".format(code)).strip().splitlines()[0][:80] if (err or out) else "exit {}".format(code))
    if host.lower() == "github.com":
        status = (http or http_status)("https://github.com/{}".format(path))
        if status == 200:
            return "PUBLIC", "{}, and https://github.com/{} is readable without signing in".format(why_gh, path)
        if status == 404:
            return "PRIVATE", "{}, and https://github.com/{} returns 404 without signing in".format(why_gh, path)
        return "PUBLIC", "{}, and https://github.com/{} returned {}; treated as public until checked".format(why_gh, path, status or "no response")
    code, err = (ls_remote or anonymous_ls_remote)("https://{}/{}.git".format(host, path))
    if code == 0:
        return "PUBLIC", "{}, and an anonymous git ls-remote of https://{}/{} succeeds".format(why_gh, host, path)
    if re.search(r"(?i)authentication|could not read username|terminal prompts disabled|\b40[134]\b|not found", err or ""):
        return "PRIVATE", "{}, and an anonymous git ls-remote of https://{}/{} is refused".format(why_gh, host, path)
    return "PUBLIC", "{}, and the anonymous probe of https://{}/{} failed; treated as public until checked".format(why_gh, host, path)


def cmd_visibility(args):
    root = find_root(args.root or os.getcwd())
    answer, reason = repo_visibility(root)
    print(answer)
    print(reason)
    return 0


def api_provider():
    """(provider, the CLAUDE_CODE_USE_* variable that selected it or None): anthropic, bedrock, vertex, or foundry."""
    for name, provider in (("CLAUDE_CODE_USE_BEDROCK", "bedrock"), ("CLAUDE_CODE_USE_VERTEX", "vertex"),
                           ("CLAUDE_CODE_USE_FOUNDRY", "foundry")):
        if str(os.environ.get(name, "")).strip().lower() not in ("", "0", "false", "no", "off"):
            return provider, name
    return "anthropic", None


def settings_files(root):
    home = home_dir()
    return [home / ".claude" / "settings.json", Path(root) / ".claude" / "settings.json", Path(root) / ".claude" / "settings.local.json"]


def cmd_preflight(args):
    """Check the launch this session is running under: that no background worktree holds the session and
    that the permission mode will not stall an unattended run on a prompt."""
    cwd = Path(args.root or os.getcwd()).resolve()
    main = main_worktree_root(cwd) or find_root(cwd)
    results = []
    top = git_out(cwd, "rev-parse", "--show-toplevel")
    harness_base = realpath_loose(Path(main) / ".claude" / "worktrees")
    entries = [os.path.realpath(e.get("worktree", "")) for e in worktree_entries(main)[1:]]
    harness = [e for e in entries if is_within(Path(e), harness_base)]
    baseline = read_baseline(main)
    new = [e for e in harness if baseline is not None and e not in (baseline.get("worktrees") or [])]
    if top and is_within(realpath_loose(Path(top)), harness_base):
        results.append(("FAIL", "worktree isolation", "this session runs inside {}, a background-session worktree, so its edits never reach "
                        "{}. Relaunch with the per-run settings that set worktree.bgIsolation to none.".format(top, main)))
    elif new:
        results.append(("FAIL", "worktree isolation", "git worktree list gained {} since the run started: a background session moved into a "
                        "worktree. Relaunch with worktree.bgIsolation set to none.".format(", ".join(new))))
    else:
        results.append(("ok", "worktree isolation", "checked `git worktree list` in {}: the session works in the main checkout; {} "
                        ".claude/worktrees/ entr{}{}".format(main, len(harness), "y" if len(harness) == 1 else "ies",
                                                            " present before the run or another session's" if harness else "")))
    mode, source = args.permission_mode, "--permission-mode"
    record_path = Path(main) / ".drive" / "local" / "session.json"
    if not mode and record_path.is_file():
        record, _ = load_json(record_path)
        session = os.environ.get("CLAUDE_CODE_SESSION_ID")
        if isinstance(record, dict) and record.get("permission_mode") and (
                not session or not record.get("session_id") or record.get("session_id") == session):
            mode, source = record["permission_mode"], "the mode drive's hooks saw in this session at {}".format(record.get("seen", "?"))
    defaults = []
    isolation = []
    for path in settings_files(main):
        data, _ = load_json(path) if path.is_file() else (None, None)
        if not isinstance(data, dict):
            continue
        permissions = data.get("permissions") if isinstance(data.get("permissions"), dict) else {}
        if permissions.get("defaultMode"):
            defaults.append("{} in {}".format(permissions["defaultMode"], path))
        worktree = data.get("worktree") if isinstance(data.get("worktree"), dict) else {}
        if worktree.get("bgIsolation"):
            isolation.append("{} in {}".format(worktree["bgIsolation"], path))
    if mode:
        lowered = mode.lower()
        if lowered in ("default", "manual", "plan"):
            results.append(("FAIL", "permission mode", "{} (from {}): an unattended run stops at the first prompt nobody answers. "
                            "Relaunch with --permission-mode auto.".format(mode, source)))
        elif lowered == "acceptedits":
            results.append(("warn", "permission mode", "acceptEdits (from {}) still prompts for most shell commands; prefer "
                            "--permission-mode auto.".format(source)))
        else:
            results.append(("ok", "permission mode", "{} (from {})".format(mode, source)))
    else:
        results.append(("info", "permission mode", "not detectable here: pass --permission-mode <mode>, or run preflight after "
                        "drive.py init so the hooks record it. defaultMode in settings files: {}".format(", ".join(defaults) or "not set")))
    results.append(("info", "worktree.bgIsolation", "; ".join(isolation) if isolation else "not set in {}; the per-run --settings JSON "
                    "must carry {{\"worktree\": {{\"bgIsolation\": \"none\"}}}}".format(", ".join(str(p) for p in settings_files(main)))))
    skill_top = git_out(SKILL_DIR, "rev-parse", "--show-toplevel")
    writable = os.access(str(SKILL_DIR / "references" / "lessons"), os.W_OK)
    results.append(("ok" if skill_top and writable else "warn", "skill repository",
                     "skill files at {} (git top level {}, lessons {}); lesson commits use this real path".format(
                         SKILL_DIR, skill_top or "none", "writable" if writable else "not writable")))
    provider, switch = api_provider()
    if switch:
        results.append(("warn", "provider", "{} ({} is set). Model aliases such as opus and sonnet resolve to older models on this "
                        "provider, so drive must not pass a per-call model override to the Agent tool; each drive: agent keeps "
                        "the model its agent file names.".format(provider, switch)))
    else:
        results.append(("ok", "provider", "anthropic (none of CLAUDE_CODE_USE_BEDROCK, CLAUDE_CODE_USE_VERTEX, or "
                        "CLAUDE_CODE_USE_FOUNDRY is set)"))
    failed = [check for level, check, _ in results if level == "FAIL"]
    if (Path(main) / ".drive").is_dir():
        # The Stop gate's launch exception counts only a failure preflight itself recorded.
        ledger_append(main, {"kind": "preflight", "ok": not failed, "failed": failed,
                             "session_id": os.environ.get("CLAUDE_CODE_SESSION_ID")})
    if args.json:
        print(json.dumps({"ok": not any(level == "FAIL" for level, _, _ in results),
                          "checks": [{"level": l, "check": c, "detail": d} for l, c, d in results]}, indent=2))
    else:
        for level, check, detail in results:
            print("{:<5} {}: {}".format(level, check, detail))
        print("drive preflight: {}".format("FAIL" if any(level == "FAIL" for level, _, _ in results) else "ok"))
    return 1 if any(level == "FAIL" for level, _, _ in results) else 0


# ----------------------------------------------------------------------------------------------
# lesson-check and lesson-commit

RETIRED_FIELDS = ["Retired", "Evidence", "Lived in", "Entry"]
REJECTED_FIELDS = ["Rejected", "Reason", "Would change the verdict", "Source"]
HOME_PATH_RE = re.compile(r"/Users/[A-Za-z0-9_.\-]+|/home/[A-Za-z0-9_.\-]+|\b[\w.+\-]+@[\w\-]+\.[\w.\-]+\b")


def normalise_heading(text):
    return re.sub(r"[^a-z0-9 ]+", "", text.lower()).strip()


def lesson_sources(skill):
    sources = []
    general = skill / "references" / "lessons" / "general.md"
    if general.is_file():
        sources.append((general, None, 60))
    for domain in sorted((skill / "references" / "domains").glob("*.md")):
        sources.append((domain, "Learned constraints", 40))
    capabilities = skill / "references" / "capabilities.md"
    if capabilities.is_file():
        sources.append((capabilities, "Learned constraints", 40))
    return sources


def run_lesson_check(skill):
    f = Findings()
    skill = Path(skill)
    general = skill / "references" / "lessons" / "general.md"
    if not general.is_file():
        f.fail("references/lessons/general.md", "is missing.")
    headings = []
    for path, section, cap in lesson_sources(skill):
        rel = str(path.relative_to(skill))
        text = read_text(path) or ""
        entries = parse_lessons(text, section)
        for number, heading, fields in entries:
            for problem in lesson_entry_problems(heading, fields):
                f.fail(rel, "line {} '{}' {}.".format(number, heading[:60], problem))
            headings.append((normalise_heading(heading), heading, rel, number))
        if len(entries) > cap:
            f.fail(rel, "has {} entries; the cap is {}. Consolidate before appending.".format(len(entries), cap))
        if section is None and len(text) / 4 > 4000:
            f.fail(rel, "is about {} tokens; the cap is about 4,000. Consolidate before appending.".format(int(len(text) / 4)))
        body = text if section is None else "\n".join(
            "### {}\n".format(h) + "\n".join("- {}: {}".format(k, v) for k, v in fl.items()) for _, h, fl in entries)
        for number, line in enumerate(body.splitlines(), 1):
            if HOME_PATH_RE.search(line):
                f.fail(rel, "an entry names a home-directory path or an email address; evidence lines carry neither.")
                break
            if any(p.search(line) for _, p in SECRET_PATTERNS):
                f.fail(rel, "an entry holds a secret-shaped string.")
                break
    for index, (norm, heading, rel, number) in enumerate(headings):
        for other_norm, other, other_rel, other_number in headings[index + 1:]:
            if norm == other_norm or difflib.SequenceMatcher(None, norm, other_norm).ratio() >= 0.92:
                f.fail(rel, "line {} '{}' nearly matches '{}' in {} line {}. Merge them through dedupe.".format(
                    number, heading[:50], other[:50], other_rel, other_number))
    for name, fields in (("retired.md", RETIRED_FIELDS), ("rejected.md", REJECTED_FIELDS)):
        path = skill / "references" / "lessons" / name
        text = read_text(path)
        if text is None:
            continue
        for number, heading, entry in parse_lessons(text, "Entries"):
            missing = [field for field in fields if field not in entry]
            if missing:
                f.fail("references/lessons/" + name, "line {} '{}' is missing {}.".format(number, heading[:50], ", ".join(missing)))
    skill_md = read_text(skill / "SKILL.md")
    if skill_md is not None:
        if skill_md.count("\n") + 1 > 450:
            f.fail("SKILL.md", "has {} lines; the cap is 450.".format(skill_md.count("\n") + 1))
        start = skill_md.find("<!-- drive:standing-rules:start -->")
        end = skill_md.find("<!-- drive:standing-rules:end -->")
        if start < 0 or end < start:
            f.fail("SKILL.md", "has no standing-rules block delimited by the drive:standing-rules markers.")
        else:
            block = [l for l in skill_md[start:end].splitlines()[1:] if l.strip()]
            if len(block) > 15:
                f.fail("SKILL.md", "the standing-rules block has {} lines; the cap is 15.".format(len(block)))
    return f


def cmd_lesson_check(args):
    skill = Path(args.skill_dir).resolve() if args.skill_dir else SKILL_DIR
    f = run_lesson_check(skill)
    for line in f.lines():
        print(line)
    print("drive lesson-check: {}".format("ok" if not f.failed else "{} failure(s)".format(sum(1 for i in f.items if i["level"] == "fail"))))
    return 1 if f.failed else 0


def lesson_scope(rel):
    parts = rel.split("/")
    if rel.endswith("references/lessons/general.md"):
        return "general"
    if "domains" in parts:
        return Path(rel).stem
    if rel.endswith("references/capabilities.md"):
        return "capabilities"
    if rel.endswith("references/lessons/retired.md"):
        return "retired"
    if rel.endswith("references/lessons/rejected.md"):
        return "rejected"
    return None


STANDING_RULES_START = "<!-- drive:standing-rules:start -->"
STANDING_RULES_END = "<!-- drive:standing-rules:end -->"


def outside_standing_rules(text):
    """SKILL.md with the standing-rules block's contents removed, or None when the markers are missing."""
    start, end = text.find(STANDING_RULES_START), text.find(STANDING_RULES_END)
    if start < 0 or end < start:
        return None
    return text[:start] + text[end:]


def standing_rules_only_problem(repo, rel):
    """Why a lesson commit may not include this SKILL.md: a change outside the standing-rules block."""
    old = show_at(repo, "HEAD", rel) if has_head(repo) else None
    new = read_text(Path(repo) / rel)
    if old is None or new is None:
        return "{} is not committed, so its change cannot be checked against the standing-rules block.".format(rel)
    new_rest, old_rest = outside_standing_rules(new), outside_standing_rules(old)
    if new_rest is None:
        return "{} has no standing-rules block delimited by the drive:standing-rules markers.".format(rel)
    if old_rest != new_rest:
        return ("{} changes outside the {} ... {} block. A lesson commit changes only the standing rules; the rest of "
                "SKILL.md is edited and reviewed by hand.".format(rel, STANDING_RULES_START, STANDING_RULES_END))
    return None


def cmd_lesson_commit(args):
    skill = Path(args.skill_dir).resolve() if args.skill_dir else SKILL_DIR
    repo = git_out(skill, "rev-parse", "--show-toplevel")
    if not repo:
        print("drive lesson-commit: {} is not inside a git repository.".format(skill))
        return 1
    repo = Path(repo).resolve()
    check = run_lesson_check(skill)
    if check.failed:
        for line in check.lines():
            print(line)
        print("drive lesson-commit: lesson-check fails; fix the entry, never the check.")
        return 1
    rels, scopes = [], set()
    for raw in args.files:
        path = Path(raw)
        path = (path if path.is_absolute() else Path(os.getcwd()) / path).resolve()
        if not is_within(path, repo) or not path.exists():
            print("drive lesson-commit: {} is not a file in the skill repository.".format(raw))
            return 1
        rel = str(path.relative_to(repo))
        skill_rel = str(path.relative_to(skill)) if is_within(path, skill) else ""
        scope = lesson_scope(rel)
        if scope is None and skill_rel != "SKILL.md" and not skill_rel.startswith("evals/"):
            print("drive lesson-commit: {} is not a lessons file, a domain or capabilities file, SKILL.md's standing rules, or an eval case.".format(rel))
            return 1
        if scope:
            scopes.add(scope)
        rels.append(rel)
        if skill_rel == "SKILL.md":
            problem = standing_rules_only_problem(repo, rel)
            if problem:
                print("drive lesson-commit: {}".format(problem))
                return 1
    staged = [p for p in (git_out(repo, "diff", "--cached", "--name-only") or "").splitlines() if p]
    stray = [p for p in staged if p not in rels]
    if stray:
        print("drive lesson-commit: other files are already staged ({}). One lesson, one commit: unstage them first.".format(", ".join(stray[:5])))
        return 1
    added = []
    for rel in rels:
        tracked = git(repo, "ls-files", "--error-unmatch", "--", rel)[0] == 0
        diff = git_out(repo, "diff", "HEAD", "--", rel) if tracked and has_head(repo) else "\n".join("+" + l for l in (read_text(repo / rel) or "").splitlines())
        added.extend(l[5:].strip() for l in (diff or "").splitlines() if l.startswith("+### "))
    if not any(git_out(repo, "status", "--porcelain", "--", rel) for rel in rels):
        print("drive lesson-commit: the named files have no changes to commit.")
        return 1
    heading = args.heading
    if not heading:
        if len(added) != 1:
            print("drive lesson-commit: found {} new lesson headings; pass --heading with the rule heading verbatim.".format(len(added)))
            return 1
        heading = added[0]
    scope = args.scope or (sorted(scopes)[0] if len(scopes) == 1 else None)
    if not scope:
        print("drive lesson-commit: the files span several scopes ({}); pass --scope.".format(", ".join(sorted(scopes)) or "none"))
        return 1
    message = ("lesson({}): {}\n\nTrigger: {} on {}\nInvestigation: {}\nDedupe: {}\nAuditor: accepted ({})\nCheck: {}\n"
               "Project: {}\nRun: {}\n").format(
        scope, heading, args.trigger, args.date or now_utc().strftime("%Y-%m-%d"), args.investigation, args.dedupe,
        args.auditor_model, args.check, args.project, args.run)
    code, _, err = git(repo, "add", "--", *rels)
    if code != 0:
        print("drive lesson-commit: git add failed: {}".format(err.strip()))
        return 1
    code, out, err = git(repo, "commit", "-m", message, "--", *rels)
    if code != 0:
        print("drive lesson-commit: git commit failed: {}".format((out + err).strip()))
        return 1
    sha = git_out(repo, "rev-parse", "--short", "HEAD")
    print("Committed lesson({}): {} as {}. Undo with: git -C {} revert {}".format(scope, heading, sha, repo, sha))
    return 0


# ----------------------------------------------------------------------------------------------
# Entry point


def build_parser():
    parser = argparse.ArgumentParser(prog="drive.py", description="The deterministic backbone of the /drive skill.")
    sub = parser.add_subparsers(dest="command")
    sub.required = True

    def add(name, func, text):
        p = sub.add_parser(name, help=text, description=text)
        p.set_defaults(func=func)
        return p

    p = add("init", cmd_init, "Create .drive/ from the templates, ignore .drive/local/, record the owner's baseline, and mark the run active.")
    p.add_argument("--goal", help="the goal, verbatim; '-' reads it from stdin")
    p.add_argument("--goal-file", help="read the goal from this file (safe for quotes, $, and backticks)")
    p.add_argument("--slug", help="goal slug (default: derived from the goal)")
    p.add_argument("--size", choices=SIZES, help="size from classification; required for a new run")
    p.add_argument("--root", help="project directory (default: current directory)")
    p = add("start", cmd_start, "Print the read-at-start view. Always exits 0.")
    p.add_argument("--root")
    p = add("lint", cmd_lint, "Check .drive/ against the state-file grammar and the evidence rules.")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--gate", metavar="PHASE", help="also check this phase's exit criteria")
    group.add_argument("--stop", action="store_true", help="add freshness and repository hygiene checks")
    group.add_argument("--final", action="store_true", help="add the checks for a finished run, including one run of the full suite")
    p.add_argument("--sub", metavar="SLUG", help="with --gate: the sub-goal whose classification the gate uses")
    p.add_argument("--suite-timeout", type=int, default=SUITE_TIMEOUT, help="seconds the full suite may run at --final")
    p.add_argument("--json", action="store_true", help="print findings as JSON")
    p.add_argument("--root")
    add("hook-stop", cmd_hook_stop, "Stop hook: keep the turn going while the run is unfinished.")
    add("hook-reinject", cmd_hook_reinject, "SessionStart hook: print the start view when a run is active.")
    add("hook-guard", cmd_hook_guard, "PreToolUse hook: per-agent and main-thread write and git rules.")
    add("hook-post", cmd_hook_post, "PostToolUse hook: record the commits a main-thread Bash call made.")
    p = add("hook-snapshot", cmd_hook_snapshot, "SubagentStart/SubagentStop hook: spawn record, provenance ledger, and void markers.")
    p.add_argument("phase", choices=["start", "stop"])
    p = add("end", cmd_end, "Remove .drive/local/active once the run's status and checks allow it.")
    p.add_argument("--suite-timeout", type=int, default=SUITE_TIMEOUT)
    p.add_argument("--root")
    p = add("worktree-land", cmd_worktree_land, "Cherry-pick a detached arm's commits at a recorded sha, then remove the worktree.")
    p.add_argument("worktree", help="the arm's worktree path")
    p.add_argument("sha", help="the sha recorded for the arm's HEAD")
    p.add_argument("--root")
    p = add("preflight", cmd_preflight, "Check the launch: no background worktree holds the session and the permission mode is unattended.")
    p.add_argument("--permission-mode", help="the mode this session was launched with, when the hooks have not recorded it")
    p.add_argument("--json", action="store_true")
    p.add_argument("--root")
    p = add("freeze", cmd_freeze, "Frozen refutation tests: add <paths>, check [--base <sha>], park <key>, unpark <key>, "
                                  "amend --open|--close <key or path> [--dispute <file>]. There is no force option.")
    p.add_argument("action", choices=["add", "check", "park", "unpark", "amend"])
    p.add_argument("targets", nargs="*", help="paths for add; a claim key for park and unpark; a key or frozen path for amend")
    p.add_argument("--base", help="check: also compare with the list and manifest at this commit")
    amend = p.add_mutually_exclusive_group()
    amend.add_argument("--open", action="store_true", help="amend: open an amendment after a not_a_defect ruling")
    amend.add_argument("--close", action="store_true", help="amend: close the amendment and rehash")
    p.add_argument("--dispute", help="amend --open: the test dispute record")
    p.add_argument("--root")
    p = add("visibility", cmd_visibility, "Print PUBLIC or PRIVATE for the repository, treating an unknown answer as PUBLIC.")
    p.add_argument("--root")
    p = add("lesson-check", cmd_lesson_check, "Structural checks on the skill's lessons and Learned constraints.")
    p.add_argument("--skill-dir")
    p = add("lesson-commit", cmd_lesson_commit, "Commit one lesson with the fixed message shape.")
    p.add_argument("files", nargs="+")
    p.add_argument("--trigger", required=True, help="the failure event type")
    p.add_argument("--date", help="date of the failure event (default today)")
    p.add_argument("--investigation", required=True, help="investigation path relative to the project root")
    p.add_argument("--dedupe", required=True, help="the grader's dedupe verdict")
    p.add_argument("--auditor-model", required=True, help="the model the auditor ran as")
    p.add_argument("--check", required=True, help="the check that enforces the lesson, or none")
    p.add_argument("--project", required=True, help="the project's repository directory name")
    p.add_argument("--run", required=True, help="the run's goal slug")
    p.add_argument("--heading", help="the rule heading, when it cannot be read from the diff")
    p.add_argument("--scope", help="general, capabilities, a domain name, retired, or rejected")
    p.add_argument("--skill-dir")
    p = add("capabilities", cmd_capabilities, "Write .drive/capabilities.json. Never fails.")
    p.add_argument("--root")
    p = add("selfcheck", cmd_selfcheck, "Check that every path the skill names exists and SKILL.md is within its cap.")
    p.add_argument("--skill-dir")
    p = add("guard", cmd_guard, "The constraints floor over staged, unstaged, and untracked changes. Exit 0 clean, 1 violation, 2 could not run.")
    p.add_argument("--base", default=None, help="commit to compare against (default: GOAL.md's baseline_sha, else HEAD)")
    p.add_argument("--root")
    return parser


def main(argv=None):
    parser = build_parser()
    args, unknown = parser.parse_known_args(argv)
    if unknown:
        # `freeze amend --open <key>` puts the positional after the flag, which argparse leaves unparsed.
        if getattr(args, "command", None) == "freeze" and not any(u.startswith("-") for u in unknown):
            args.targets = list(args.targets or []) + unknown
        else:
            parser.error("unrecognized arguments: {}".format(" ".join(unknown)))
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
