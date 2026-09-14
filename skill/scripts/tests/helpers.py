"""Shared fixtures for the drive.py tests: temporary git repositories with `.drive/` trees."""
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1]
SKILL = SCRIPTS.parent
DRIVE = SCRIPTS / "drive.py"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import drive  # noqa: E402

TODAY = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
GOAL_TEXT = "Reject expired tokens and let admins revoke sessions."
TEST_COMMAND = "python3 tests/suite.py"
SUITE_OK = "import sys\nsys.exit(0)\n"


def iso(offset_seconds=0):
    stamp = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=offset_seconds)
    return stamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def fill_lines(text, replacements):
    """Replace every line starting with a key by its value (None deletes the line)."""
    out = []
    for line in text.splitlines():
        for prefix, new in replacements.items():
            if line.startswith(prefix):
                if new is not None:
                    out.append(new)
                break
        else:
            out.append(line)
    return "\n".join(out) + "\n"


def goal_md(baseline, slug="session-auth", size="M", plan_done=False):
    tick = "x" if plan_done else " "
    return """# GOAL · {slug}
goal: "{goal}"
live means: the staging deployment at https://staging.example.test exercised with curl
budget: 40 turns · 8 subagents · 3 h · 20 usd

## Restate
- outcome: "Reject expired tokens"
- user: assumption: API clients and administrators
- why now: assumption: a security review asked for it
- success: "let admins revoke sessions"
- constraints: assumption: no new runtime dependency
- out of scope: assumption: single sign-on

## Classification
```yaml
shape: feature
variant: null
size: {size}
size_set_by: "several modules: token check, session store, admin screen"
traits: {{ confirmed: [existing-code, api, auth], suspected: [ui] }}
suspected_because: {{ ui: "admins revoke sessions from a screen" }}
probe:
  repo: /repo
  stacks: [python]
  build_command: "none"
  focused_test_command: "python3 -m pytest tests/test_auth.py"
  test_command: "{tests}"
  baseline_sha: {baseline}
  claude_md: absent
  system_tools: none
assumptions: []
not_asked: []
classified_at: 2026-09-14T09:00:00Z
reclassifications: []
```

## Plan
- [x] intake · artifact: .drive/GOAL.md · exit: committed as drive(intake): {slug} · checker: orchestrator
- [{tick}] build · artifact: code and tests · exit: gates green · checker: verifier
- [{tick}] verify · artifact: .drive/proofs · exit: every row at Local Proof · checker: verifier
- [{tick}] report · artifact: .drive/REPORT.md · exit: final audit go; lint --final passes · checker: verifier

## Re-plans
""".format(slug=slug, goal=GOAL_TEXT, size=size, baseline=baseline, tests=TEST_COMMAND, tick=tick)


def state_md(commit, status="running", phase="build", updated=None, in_flight="none", extra_facts="",
             blocked="none", open_failures=""):
    return """# STATE · proj · session-auth
status: {status}
phase: {phase}
next: Run the verifier on the session revocation claim.
updated: {updated}
commit: {commit}
session: drive-session-auth
model: claude-fable-5-1 · high

## Resume here
Why: the revocation claim has no independent verdict yet.
Blocked on: {blocked}
In flight: {in_flight}

## Verified facts
- The suite runs with python3 -m pytest. Verified: ran it on 2026-09-14.
{extra_facts}
## Rules in force
- Compare tokens in constant time. Because: timing differences leak token prefixes. From: 2026-09-14-token-compare.

## Open failures
{open_failures}
## Discoveries

## Workaround ledger
| obstacle | workaround | by | when | count |
|---|---|---|---|---|

## Boundary events
""".format(status=status, phase=phase, updated=updated or iso(), commit=commit, in_flight=in_flight,
           extra_facts=extra_facts, blocked=blocked, open_failures=open_failures)


def verdict(unit, claims=None, verdict_value="pass", ran=None, rung="Local Proof", gaps=None, round_number=1):
    claims = claims if claims is not None else [unit]
    return {
        "verdict": verdict_value,
        "unit": unit,
        "round": round_number,
        "scope": {"range": "abc1234..def5678", "path": "/repo"},
        "surface": "pytest",
        "ran": ran if ran is not None else [{"cmd": TEST_COMMAND, "exit": 0, "seconds": 3, "output": "r1/pytest.txt"}],
        "claims": [{"id": c, "status": "holds", "oracle": "the token library's expiry check",
                    "refutations_attempted": ["sent a token that expired one second ago; it was rejected"],
                    "evidence": ["tests/test_auth.py"], "confidence": 75} for c in claims],
        "gaps": gaps or [],
        "harness_kindness": [],
        "not_checked": [],
        "rung_supported": rung,
        "for_maker": "",
    }


def proof_manifest(key, environment="live", target="https://staging.example.test", commit="", verdict_value="pass",
                   shim=None):
    return {
        "key": key,
        "claim": "An expired token is rejected with 401",
        "environment": environment,
        "target": target,
        "commit": commit,
        "produced_by": "verifier",
        "started": iso(),
        "latest_round": "r1",
        "commands": [{"cmd": "curl -s -o /dev/null -w '%{http_code}' https://staging.example.test/session", "exit": 0,
                      "output": "r1/live.md"}],
        "artifacts": [{"path": "r1/live.md", "sha256": "0" * 64, "kind": "response"}],
        "shim_differences": shim if shim is not None else ["Local tests use an in-memory session store; this proof ran against staging."],
        "shim_differences_note": "",
        "verdict": verdict_value,
        "notes": "",
    }


class DriveTestCase(unittest.TestCase):
    """Each test gets its own temporary HOME, scratch root, and git configuration."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="drive-test-")).resolve()
        self.home = self.tmp / "home"
        self.scratch = self.tmp / "scratch"
        self.home.mkdir()
        self.scratch.mkdir()
        gitconfig = self.home / ".gitconfig"
        gitconfig.write_text("[user]\n\tname = Drive Test\n\temail = drive-test@example.invalid\n"
                             "[init]\n\tdefaultBranch = main\n[commit]\n\tgpgsign = false\n[core]\n\thooksPath = /dev/null\n")
        env = {
            "HOME": str(self.home),
            "GIT_CONFIG_GLOBAL": str(gitconfig),
            "GIT_CONFIG_NOSYSTEM": "1",
            "DRIVE_TMP_ROOTS": str(self.scratch),
            # Transcript fixtures are complete when written; a live SubagentStop waits for Claude Code's asynchronous write.
            "DRIVE_TRANSCRIPT_SETTLE": "0",
        }
        self.env_patch = mock.patch.dict(os.environ, env)
        self.env_patch.start()
        for name in ("CLAUDE_PROJECT_DIR", "CLAUDE_PLUGIN_DATA", "CLAUDE_CODE_SESSION_ID", "TMPDIR"):
            os.environ.pop(name, None)
        drive._SCHEMAS.clear()

    def tearDown(self):
        self.env_patch.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    # git and files
    def git(self, repo, *args, env=None):
        full = dict(os.environ)
        full.update(env or {})
        proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=full)
        if proc.returncode != 0:
            raise AssertionError("git {} failed: {}".format(" ".join(args), proc.stderr))
        return proc.stdout.strip()

    def write(self, repo, rel, content):
        path = Path(repo) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, (dict, list)):
            content = json.dumps(content, indent=2) + "\n"
        path.write_text(content, encoding="utf-8")
        return path

    def commit(self, repo, message, paths=(".",), offset_seconds=None):
        self.git(repo, "add", "-A", "--", *paths)
        env = {}
        if offset_seconds is not None:
            stamp = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=offset_seconds)).strftime("%Y-%m-%dT%H:%M:%S+0000")
            env = {"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp}
        self.git(repo, "commit", "-q", "-m", message, env=env)
        return self.git(repo, "rev-parse", "--short", "HEAD")

    def new_repo(self, name="proj"):
        repo = self.tmp / name
        repo.mkdir()
        self.git(repo, "init", "-q", "-b", "main")
        return repo

    # drive
    def run_drive(self, *args, cwd=None, stdin=None, env=None):
        full = dict(os.environ)
        full.update(env or {})
        return subprocess.run([sys.executable, str(DRIVE), *args], cwd=str(cwd or self.tmp), input=stdin,
                              capture_output=True, text=True, env=full, timeout=120)

    def hook(self, name, payload, *extra):
        return self.run_drive(name, *extra, stdin=json.dumps(payload))

    def lint(self, repo, mode="base", gate=None):
        drive._SCHEMAS.clear()
        return drive.run_lint(Path(repo), mode, gate)[1]

    def messages(self, findings, level="fail"):
        return "\n".join("{}: {}".format(i["file"], i["message"]) for i in findings.items if i["level"] == level)

    def assertFails(self, findings, fragment):
        text = self.messages(findings)
        self.assertIn(fragment, text, "expected a failure containing {!r}; failures were:\n{}".format(fragment, text))

    def assertNoFailure(self, findings, fragment=None):
        text = self.messages(findings)
        if fragment is None:
            self.assertFalse(findings.failed, "expected no failures; got:\n{}".format(text))
        else:
            self.assertNotIn(fragment, text)

    # fixtures
    def transcript(self, repo, rel=None, agent_type="drive:verifier", agent_id="agent-test", tool="Bash", session="s-test",
                   command=None, is_error=False, meta=True, tool_input=None):
        """Append one tool call to a subagent transcript shaped like Claude Code's: ~/.claude/projects/<project>/<session>/
        subagents/agent-<id>.jsonl, one JSON object per line (a user prompt, then assistant tool_use items with id, name,
        and input, each followed by a user tool_result), with agent-<id>.meta.json beside it. Returns the path."""
        folder = self.home / ".claude" / "projects" / str(Path(repo)).replace("/", "-") / session / "subagents"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "agent-{}.jsonl".format(agent_id)
        base = {"isSidechain": True, "agentId": agent_id, "cwd": str(repo), "sessionId": session, "userType": "external",
                "version": "2.1.270", "gitBranch": "main"}
        lines = []
        if not path.exists():
            lines.append(dict(base, type="user", uuid="u-0", parentUuid=None, message={"role": "user", "content": "Verify the claim."}))
        count = len(path.read_text().splitlines()) if path.exists() else 0
        call_id = "toolu_{}_{}".format(agent_id, count)
        if tool_input is None:
            if tool in ("Write", "Edit"):
                tool_input = {"file_path": str(Path(repo) / rel), "content": "{}"}
            else:
                tool_input = {"command": command or "cat > {} <<'EOF'\n{{}}\nEOF".format(rel)}
        lines.append(dict(base, type="assistant", uuid="a-{}".format(count), parentUuid="u-0",
                          message={"role": "assistant", "content": [{"type": "tool_use", "id": call_id, "name": tool,
                                                                     "input": tool_input, "caller": {"type": "direct"}}]}))
        lines.append(dict(base, type="user", uuid="r-{}".format(count), parentUuid="a-{}".format(count),
                          message={"role": "user", "content": [{"type": "tool_result", "tool_use_id": call_id,
                                                                "content": "error" if is_error else "", "is_error": is_error}]}))
        with open(path, "a", encoding="utf-8") as handle:
            for line in lines:
                handle.write(json.dumps(line) + "\n")
        if meta:
            (folder / "agent-{}.meta.json".format(agent_id)).write_text(json.dumps({"agentType": agent_type, "description": "review"}))
        return path

    def sign(self, repo, rel, agent_type="drive:verifier", agent_id=None):
        """Record `rel` in the provenance ledger as the SubagentStop hook would for `agent_type`, backed by a transcript
        in which that agent wrote the file."""
        agent_id = agent_id or "agent-{}".format(agent_type.split(":")[-1])
        path = self.transcript(repo, rel, agent_type=agent_type, agent_id=agent_id)
        self.assertTrue(drive.record_evidence(Path(repo), rel, agent_type, agent_id, transcript=str(path)),
                        "could not sign {}".format(rel))

    def write_live_proof(self, repo, key, manifest, signed=True, agent_type="drive:verifier"):
        """Write r1/live.md, record its real sha256 in the manifest, write proof.json, and sign it."""
        live = self.write(repo, ".drive/proofs/{}/r1/live.md".format(key), "401 from https://staging.example.test/session\n")
        for artifact in manifest.get("artifacts") or []:
            if artifact.get("path") == "r1/live.md":
                artifact["sha256"] = drive.file_sha256(live)
        self.write(repo, ".drive/proofs/{}/proof.json".format(key), manifest)
        if signed:
            self.sign(repo, ".drive/proofs/{}/proof.json".format(key), agent_type=agent_type)

    def make_run(self, status="running", signed=True):
        """A feature run at size M with three claims: Local Proof, Partial, and Missing.

        It passes `lint --stop` as built; each test breaks one thing. With signed=False no evidence
        file is recorded in the provenance ledger, as when the orchestrator wrote it by hand."""
        repo = self.new_repo()
        self.write(repo, "README.md", "# proj\n")
        self.write(repo, ".gitignore", ".drive/local/\n")
        base = self.commit(repo, "chore: start")
        self.write(repo, ".drive/GOAL.md", goal_md(base))
        self.commit(repo, "drive(intake): session-auth")
        self.write(repo, "src/auth.py", "def check(token, now):\n    return token.expires_at > now\n")
        self.write(repo, "tests/test_auth.py",
                   "def test_expired():\n    'expired token is rejected'\n\n"
                   "def test_forged():\n    'forged expiry is rejected'\n\n"
                   "def test_list():\n    'session list shows active sessions'\n")
        self.write(repo, "tests/suite.py", SUITE_OK)
        code = self.commit(repo, "feat(auth): reject expired tokens")
        self.code_sha = code
        key = "expired-token-is-rejected"
        self.write(repo, ".drive/proofs/{}/r1/verdict.json".format(key), verdict(key))
        if signed:
            self.sign(repo, ".drive/proofs/{}/r1/verdict.json".format(key))
        self.write(repo, ".drive/STATUS.md", self.status_md([
            (key, "An expired token is rejected with 401", "y", "Local Proof",
             "test:tests/test_auth.py::expired token is rejected; severe:tests/test_auth.py::forged expiry is rejected; "
             "verdict:.drive/proofs/{}/r1/verdict.json; commit:{}".format(key, code)),
            ("session-list-shows-active-sessions", "The session list shows only active sessions", "n", "Partial",
             "test:tests/test_auth.py::session list shows active sessions; commit:{}".format(code)),
            ("admin-can-revoke-sessions", "An admin can revoke any session", "y", "Missing", ""),
        ]))
        self.write(repo, ".drive/DECISIONS.md", "# DECISIONS · proj\n\n## 2026-09-14 · Compare tokens in constant time\n"
                   "- Context: expired-token-is-rejected compares token strings.\n- Decision: use hmac.compare_digest.\n"
                   "- Rejected: plain equality, because it leaks timing.\n- Undo: revert the auth commit · reversal cost: low.\n"
                   "- Evidence: none\n- Narrows: none\n")
        self.write(repo, ".drive/STATE.md", state_md(code, status=status))
        self.commit(repo, "drive(build): state after the auth package")
        self.write(repo, ".drive/local/active", json.dumps({"slug": "session-auth"}) + "\n")
        drive.write_baseline(repo)
        return repo

    def status_md(self, rows):
        lines = ["# STATUS · proj",
                 "ladder: Missing → Scaffold → Partial → Local Proof → Live Proof → Operational → Done   (Dropped needs why:)",
                 "", "| key | claim | live | status | evidence | updated |", "|-----|-------|------|--------|----------|---------|"]
        for key, claim, live, status, evidence in rows:
            lines.append("| {} | {} | {} | {} | {} | {} |".format(key, claim, live, status, evidence, TODAY))
        return "\n".join(lines) + "\n"

    def set_state(self, repo, **kwargs):
        kwargs.setdefault("commit", self.git(repo, "rev-parse", "--short", "HEAD"))
        self.write(repo, ".drive/STATE.md", state_md(**kwargs))

    def make_final_run(self, status="done", signed=True):
        """A finished run: two Done rows and one Dropped row, final audit, report, and retro committed.

        With signed=False, every verdict, the live proof, and the final audit are hand-written: schema-valid
        and claiming a green suite, but never recorded by a reviewing agent."""
        repo = self.make_run(signed=signed)
        code = self.code_sha
        live_key, list_key, drop_key = "expired-token-is-rejected", "session-list-shows-active-sessions", "admin-can-revoke-sessions"
        self.write(repo, ".drive/proofs/{}/r1/verdict.json".format(live_key), verdict(live_key, rung="Live Proof"))
        self.write(repo, ".drive/proofs/{}/r1/verdict.json".format(list_key), verdict(list_key))
        self.write_live_proof(repo, live_key, proof_manifest(live_key, commit=code), signed=signed)
        audit = verdict("final-audit", claims=[live_key, list_key], rung="Operational")
        self.write(repo, ".drive/reviews/2026-09-14-final-audit.json", audit)
        if signed:
            self.sign(repo, ".drive/proofs/{}/r1/verdict.json".format(live_key))
            self.sign(repo, ".drive/proofs/{}/r1/verdict.json".format(list_key))
            self.sign(repo, ".drive/reviews/2026-09-14-final-audit.json", agent_type="drive:auditor", agent_id="agent-audit")
        audit_ref = "review:.drive/reviews/2026-09-14-final-audit.json"
        self.write(repo, ".drive/STATUS.md", self.status_md([
            (live_key, "An expired token is rejected with 401", "y", "Done",
             "test:tests/test_auth.py::expired token is rejected; severe:tests/test_auth.py::forged expiry is rejected; "
             "verdict:.drive/proofs/{k}/r1/verdict.json; live:.drive/proofs/{k}; {a}; commit:{c}".format(k=live_key, a=audit_ref, c=code)),
            (list_key, "The session list shows only active sessions", "n", "Done",
             "test:tests/test_auth.py::session list shows active sessions; severe:tests/test_auth.py::forged expiry is rejected; "
             "verdict:.drive/proofs/{k}/r1/verdict.json; {a}; commit:{c}".format(k=list_key, a=audit_ref, c=code)),
            (drop_key, "An admin can revoke any session", "y", "Dropped", "why:the owner moved revocation to the next release"),
        ]))
        with open(repo / ".drive" / "DECISIONS.md", "a", encoding="utf-8") as handle:
            handle.write("\n## 2026-09-14 · Drop admin revocation from this run\n- Context: admin-can-revoke-sessions needs a screen.\n"
                         "- Decision: drop it from this run.\n- Rejected: building the screen now, because the budget is spent.\n"
                         "- Undo: add the row back as Missing · reversal cost: low.\n- Evidence: none\n"
                         "- Narrows: admin-can-revoke-sessions Dropped\n")
        self.write(repo, ".drive/REPORT.md", self.report_md({"Done": 2, "Dropped": 1}))
        self.write(repo, ".drive/reviews/2026-09-14-retro.md", RETRO_MD)
        self.write(repo, ".drive/GOAL.md", goal_md(self.git(repo, "rev-list", "--max-parents=0", "--abbrev-commit", "HEAD"), plan_done=True))
        self.write(repo, ".drive/STATE.md", state_md(code, status=status, phase="report"))
        self.commit(repo, "drive(report): final state")
        return repo

    def report_md(self, counts, outcome="Expired tokens are rejected on staging at the final commit."):
        ladder = "\n".join("| {} | {} |".format(r, counts.get(r, 0)) for r in drive.LADDER + ["Dropped"])
        return REPORT_MD.format(outcome=outcome, ladder=ladder)


RETRO_MD = """# RETRO · session-auth · 2026-09-14

## Investigations
| investigation | final status | reason |
|---|---|---|

## Repeated workarounds
| obstacle | count | investigation |
|---|---|---|

## Candidates
- none proposed; no failure event occurred

## Lessons consulted
- Before trusting green runs, find where each test double is kinder than the real service · in briefs: 1 · cited by a verifier: 1

## Skill instructions at fault
- none · eval case: none

## Consolidation
- not due: no lessons were committed

## Lessons committed
- none: no failure event occurred in this run
"""

REPORT_MD = """# REPORT · session-auth

## Outcome
{outcome}

## Needed from you
none

## What to look at first
.drive/proofs/expired-token-is-rejected/r1/live.md

## Ladder
| rung | rows |
|------|------|
{ladder}

## What shipped
- An expired token is rejected with 401 · Done · .drive/proofs/expired-token-is-rejected/proof.json

## Proven live and proven locally
- Live: An expired token is rejected with 401 · .drive/proofs/expired-token-is-rejected/proof.json

## Not done
- An admin can revoke any session · Dropped · build the admin screen

## Decisions taken on your behalf
- Drop admin revocation from this run · undo: add the row back as Missing · 2026-09-14

## Open failures
- none

## Lessons
- none: no failure event occurred in this run

## Verify from a clean checkout
```bash
python3 -m pytest
```

## Paused run
none

## Spend
38 turns
"""
