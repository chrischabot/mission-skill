"""Severe tests for the adversarial review at 84ccd54 (research/34-adversarial-review.md).

Each class names the finding it covers. Every test drives the real path (hook-guard, hook-stop, hook-snapshot, drive.py
end, lint, preflight, capabilities, visibility) and the fix tests fail against drive.py as it stood before the fixes."""
import json

from helpers import RETRO_MD, DriveTestCase, drive, verdict

KEY = "expired-token-is-rejected"
LIST = "session-list-shows-active-sessions"
ADMIN = "admin-can-revoke-sessions"
REVIEW_PATHS = {
    "drive:verifier": ".drive/proofs/{}/r2/verdict.json".format(KEY),
    "drive:auditor": ".drive/reviews/2026-09-14-final-audit.json",
    "drive:grader": ".drive/reviews/2026-09-14-citations-market.json",
    "drive:security-reviewer": ".drive/reviews/2026-09-14-security-review.md",
    "drive:ui-reviewer": ".drive/proofs/{}/r2/ui-verdict.json".format(KEY),
}
JSON_BODY = ('{\n  "verdict": "pass",\n  "unit": "expired-token-is-rejected",\n  "claims": [\n'
             '    {"id": "expired-token-is-rejected", "status": "holds", "confidence": 80}\n  ],\n  "for_maker": ""\n}')
MARKDOWN_BODY = ("# Security review · session-auth\n\n- finding: `hmac.compare_digest` is used, so no timing leak.\n"
                 "| check | result |\n|---|---|\n| gitleaks | clean |\n> rm -rf / was not run\n$ npm test && git push origin main\n}")
NO_PROVIDER = {"CLAUDE_CODE_USE_BEDROCK": "", "CLAUDE_CODE_USE_VERTEX": "", "CLAUDE_CODE_USE_FOUNDRY": ""}


class Hooks:
    """Hook helpers (not itself a TestCase)."""

    def guard(self, repo, tool, agent=None, cwd=None, **tool_input):
        payload = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input, "cwd": str(cwd or repo),
                   "session_id": "s-main", "tool_use_id": "toolu_adversarial"}
        if agent is not None:
            payload["agent_type"] = agent
            payload["agent_id"] = "agent-adversarial"
        return self.run_drive("hook-guard", stdin=json.dumps(payload))

    def bash(self, repo, command, agent=None, cwd=None):
        return self.guard(repo, "Bash", agent=agent, cwd=cwd, command=command)

    def stop(self, repo, cwd=None, **payload):
        self._stops = getattr(self, "_stops", 0) + 1
        data = {"hook_event_name": "Stop", "cwd": str(cwd or repo), "session_id": "s-main", "prompt_id": "p-{}".format(self._stops),
                "stop_hook_active": False, "last_assistant_message": "done", "background_tasks": []}
        data.update(payload)
        result = self.run_drive("hook-stop", stdin=json.dumps(data))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else None

    def snap(self, repo, phase, agent="drive:verifier", agent_id="agent-v", transcript=None):
        payload = {"hook_event_name": "SubagentStart" if phase == "start" else "SubagentStop", "cwd": str(repo),
                   "agent_id": agent_id, "agent_type": agent}
        if transcript is not None:
            payload["agent_transcript_path"] = str(transcript)
        result = self.run_drive("hook-snapshot", phase, stdin=json.dumps(payload))
        self.assertEqual(result.returncode, 0, result.stderr)

    def assertBlocked(self, result, fragment=None):
        self.assertEqual(result.returncode, 2, "expected a block; stderr: {}".format(result.stderr))
        if fragment:
            self.assertIn(fragment, result.stderr)

    def assertAllowed(self, result):
        self.assertEqual(result.returncode, 0, "expected the call to be allowed; stderr: {}".format(result.stderr))

    def gate_log(self, repo):
        path = repo / ".drive/local/gate.log"
        return path.read_text() if path.exists() else ""

    def append_decision(self, repo, heading, decision):
        with open(repo / ".drive/DECISIONS.md", "a", encoding="utf-8") as handle:
            handle.write("\n## 2026-09-14 · {}\n- Decision: {}\n- Undo: /drive --resume · reversal cost: low.\n".format(heading, decision))


class HeredocGuardTests(Hooks, DriveTestCase):
    """Finding 1: every reviewing agent writes its verdict or review with a Bash heredoc, as its agent file says."""

    def setUp(self):
        super().setUp()
        self.repo = self.make_run()

    @staticmethod
    def forms(path, body):
        folder = path.rsplit("/", 1)[0]
        return ["cat > {p} <<'JSON'\n{b}\nJSON".format(p=path, b=body),
                "tee {p} <<'EOF'\n{b}\nEOF".format(p=path, b=body),
                "cat <<\"EOF\" > {p}\n{b}\nEOF".format(p=path, b=body),
                "mkdir -p {d} && cat > {p} <<'EOF'\n{b}\nEOF\necho written".format(d=folder, p=path, b=body)]

    def test_every_reviewer_writes_json_and_markdown_bodies_into_its_own_path(self):
        for agent, path in REVIEW_PATHS.items():
            for body in (JSON_BODY, MARKDOWN_BODY):
                for command in self.forms(path, body):
                    with self.subTest(agent=agent, command=command[:40], body=body[:12]):
                        self.assertAllowed(self.bash(self.repo, command, agent=agent))

    def test_a_tab_stripped_unquoted_heredoc_is_read_to_its_indented_delimiter(self):
        body = "\n".join("\t" + line for line in JSON_BODY.splitlines())
        for agent, path in REVIEW_PATHS.items():
            with self.subTest(agent=agent):
                self.assertAllowed(self.bash(self.repo, "cat > {} <<-EOF\n{}\n\tEOF".format(path, body), agent=agent))

    def test_the_same_heredoc_into_a_source_file_is_refused(self):
        for agent in REVIEW_PATHS:
            for command in self.forms("src/auth.py", JSON_BODY)[:2]:
                with self.subTest(agent=agent, command=command[:30]):
                    self.assertBlocked(self.bash(self.repo, command, agent=agent))

    def test_the_main_thread_heredoc_into_a_verdict_is_still_refused(self):
        for command in self.forms(REVIEW_PATHS["drive:verifier"], JSON_BODY):
            with self.subTest(command=command[:30]):
                self.assertBlocked(self.bash(self.repo, command))

    def test_a_body_mentioning_git_push_is_data_but_the_line_after_the_delimiter_is_a_command(self):
        review = ".drive/reviews/2026-09-14-notes.md"
        self.assertAllowed(self.bash(self.repo, "cat > notes/release.md <<'EOF'\ngit push origin main\ngit checkout -b release\nEOF"))
        self.assertAllowed(self.bash(self.repo, "cat > {} <<'EOF'\ngit push origin main\nEOF".format(review), agent="drive:verifier"))
        self.assertAllowed(self.bash(self.repo, "cat <<'A' <<'B' > {}\nfirst: git push\nA\nsecond: git push\nB".format(review),
                                     agent="drive:verifier"))
        self.assertAllowed(self.bash(self.repo, "cat > {} <<'EOF'\nunterminated: git push origin main\n".format(review),
                                     agent="drive:verifier"))
        for agent in (None, "drive:verifier"):
            with self.subTest(agent=agent):
                self.assertBlocked(self.bash(self.repo, "cat > {} <<'EOF'\nsafe\nEOF\ngit push origin main".format(
                    "notes/release.md" if agent is None else review), agent=agent))
                self.assertBlocked(self.bash(self.repo, "cat <<'A' <<'B' > {}\nfirst\nA\nsecond\nB\ngit push origin main".format(
                    "notes/release.md" if agent is None else review), agent=agent))

    def test_substitutions_in_an_unquoted_body_are_judged_because_bash_runs_them(self):
        review = ".drive/reviews/2026-09-14-notes.md"
        self.assertBlocked(self.bash(self.repo, "cat > {} <<EOF\n$(git push origin main)\nEOF".format(review), agent="drive:verifier"))
        self.assertBlocked(self.bash(self.repo, "cat > {} <<EOF\n`git commit -am x`\nEOF".format(review), agent="drive:verifier"))
        self.assertAllowed(self.bash(self.repo, "cat > {} <<'EOF'\n$(git push origin main)\nEOF".format(review), agent="drive:verifier"))

    def test_an_unknown_first_word_refusal_quotes_the_simple_command_it_judged(self):
        result = self.bash(self.repo, "npm test && frobnicate --deep src", agent="drive:verifier")
        self.assertBlocked(result, "`frobnicate --deep src`")
        self.assertIn("quoted heredoc", result.stderr)


class EndHygieneTests(Hooks, DriveTestCase):
    """Finding 3: drive.py end closes a blocked or stalled run only on a tree lint --stop would pass."""

    def test_end_refuses_a_blocked_run_with_a_branch_a_worktree_or_an_untracked_file(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha, status="blocked", blocked="payment: a payment method only the owner can add")
        self.write(repo, ".drive/REPORT.md", self.report_md({}, outcome="Stopped because billing needs a payment method."))
        self.commit(repo, "drive: blocked on payment")
        worktree = self.scratch / "drive-proj-experiment"
        self.git(repo, "branch", "experiment")
        self.git(repo, "worktree", "add", "-q", "--detach", str(worktree), "HEAD")
        self.write(repo, "notes.txt", "scratch\n")
        refused = self.run_drive("end", cwd=repo)
        self.assertEqual(refused.returncode, 1, refused.stdout)
        for fragment in ("experiment", "drive-proj-experiment", "notes.txt"):
            self.assertIn(fragment, refused.stdout)
        self.assertTrue((repo / ".drive/local/active").exists())
        self.assertIsNone(self.stop(repo), "the Stop gate still lets a properly blocked turn end")
        self.git(repo, "branch", "-D", "experiment")
        self.git(repo, "worktree", "remove", "--force", str(worktree))
        (repo / "notes.txt").unlink()
        closed = self.run_drive("end", cwd=repo)
        self.assertEqual(closed.returncode, 0, closed.stdout)
        self.assertFalse((repo / ".drive/local/active").exists())

    def test_end_refuses_a_stalled_run_with_an_untracked_file(self):
        repo = self.make_run()
        for _ in range(6):
            self.stop(repo)
        self.assertIn("stalled", self.stop(repo)["systemMessage"])
        self.write(repo, ".drive/REPORT.md", self.report_md({}, outcome="Stopped because the run stalled."))
        self.commit(repo, "drive: stalled")
        self.write(repo, "scratch.log", "x\n")
        refused = self.run_drive("end", cwd=repo)
        self.assertEqual(refused.returncode, 1, refused.stdout)
        self.assertIn("scratch.log", refused.stdout)
        (repo / "scratch.log").unlink()
        self.assertEqual(self.run_drive("end", cwd=repo).returncode, 0)


class ReviewArtifactTests(Hooks, DriveTestCase):
    """Finding 4: harmless artifacts a reviewer's test run leaves never void its review; tracked changes still do."""

    def test_test_artifacts_created_during_a_review_are_noted_and_do_not_void_it(self):
        repo = self.make_run()
        self.snap(repo, "start")
        self.write(repo, ".coverage", "coverage data\n")
        self.write(repo, "test-results/x.xml", "<testsuite/>\n")
        rel = ".drive/proofs/{}/r2/verdict.json".format(KEY)
        self.write(repo, rel, verdict(KEY, round_number=2))
        self.snap(repo, "stop", transcript=self.transcript(repo, rel, agent_id="agent-v"))
        self.assertEqual(drive.ledger_entries(repo, "void"), [])
        log = self.gate_log(repo)
        for fragment in ("SNAPSHOT NOTE", ".coverage", "test-results/x.xml"):
            self.assertIn(fragment, log)
        self.assertEqual([e["path"] for e in drive.ledger_entries(repo, "evidence") if e["path"] == rel], [rel])
        self.assertFails(self.lint(repo, "stop"), ".coverage")

    def test_rewriting_an_artifact_left_by_an_earlier_round_does_not_void(self):
        repo = self.make_run()
        self.write(repo, ".coverage", "round one\n")
        self.snap(repo, "start")
        self.write(repo, ".coverage", "round two, a longer file\n")
        self.snap(repo, "stop")
        self.assertEqual(drive.ledger_entries(repo, "void"), [])

    def test_modifying_or_deleting_a_tracked_file_voids_and_the_lint_names_the_paths(self):
        repo = self.make_run()
        self.snap(repo, "start")
        self.write(repo, "src/auth.py", "def check(token, now):\n    return True\n")
        (repo / "README.md").unlink()
        rel = ".drive/proofs/{}/r1/verdict.json".format(KEY)
        self.write(repo, rel, dict(verdict(KEY), for_maker="rewritten while src changed"))
        self.snap(repo, "stop", transcript=self.transcript(repo, rel, agent_id="agent-v"))
        voids = drive.ledger_entries(repo, "void")
        self.assertEqual(len(voids), 1)
        for path in ("src/auth.py", "README.md"):
            self.assertIn(path, voids[0]["detail"])
        failures = self.messages(self.lint(repo))
        self.assertIn("voided because tracked files changed", failures)
        self.assertIn("src/auth.py", failures)


class RunMarkerTests(Hooks, DriveTestCase):
    """Finding 5: the run marker and baseline survive ordinary cleanup, and a lost marker is not silent."""

    def test_nobody_deletes_moves_or_overwrites_the_marker_or_the_baseline(self):
        repo = self.make_run()
        commands = ["rm .drive/local/active", "rm -f .drive/local/baseline.json", "mv .drive/local/active {}/active".format(self.scratch),
                    "echo '{}' > .drive/local/active", "cp /dev/null .drive/local/baseline.json",
                    "find .drive/local -name active -delete", "git clean -fdX", "git clean -fdx", "git clean -xdf", "git clean -f -d -X"]
        for agent in (None, "general-purpose", "drive:architect"):
            for command in commands:
                with self.subTest(agent=agent, command=command):
                    self.assertBlocked(self.bash(repo, command, agent=agent))
            for rel in (".drive/local/active", ".drive/local/baseline.json"):
                with self.subTest(agent=agent, tool="Write", rel=rel):
                    self.assertBlocked(self.guard(repo, "Write", agent=agent, file_path=str(repo / rel), content="{}"))
        self.assertBlocked(self.bash(repo, "rm .drive/local/active"), "run marker")
        self.assertBlocked(self.bash(repo, "git clean -fdX"), ".drive/local/active")
        for command in ("cat .drive/local/active", "git clean -n", "git clean -ndX",
                        "python3 -c \"import json; print(json.load(open('.drive/local/active')))\""):
            with self.subTest(allowed=command):
                self.assertAllowed(self.bash(repo, command))

    def test_a_stop_after_the_marker_is_lost_warns_once_per_session_and_is_allowed(self):
        repo = self.make_run()
        (repo / ".drive/local/active").unlink()
        first = self.stop(repo, cwd=repo / "src", session_id="s-1")
        self.assertNotIn("decision", first)
        self.assertIn("says running", first["systemMessage"])
        self.assertIn(".drive/local/active is missing", first["systemMessage"])
        self.assertIsNone(self.stop(repo, session_id="s-1"))
        self.assertIn("is missing", self.stop(repo, session_id="s-2")["systemMessage"])
        self.set_state(repo, commit=self.code_sha, status="blocked", blocked="payment: a payment method only the owner can add")
        self.assertIsNone(self.stop(repo, session_id="s-3"))


class StoppedRunAuditTests(Hooks, DriveTestCase):
    """Finding 8: a stopped run with any row above Missing needs a transcript-backed final audit."""

    def stopped_run(self, statuses):
        repo = self.make_run()
        code = self.code_sha
        evidence = {
            "Local Proof": "test:tests/test_auth.py::expired token is rejected; severe:tests/test_auth.py::forged expiry is rejected; "
                           "verdict:.drive/proofs/{}/r1/verdict.json; commit:{}; why:the run stopped before the live check".format(KEY, code),
            "Partial": "test:tests/test_auth.py::session list shows active sessions; commit:{}; why:the list query needs a staging "
                       "database".format(code),
            "Missing": "why:the owner stopped the run before this claim started",
        }
        claims = [(KEY, "An expired token is rejected with 401", "y"), (LIST, "The session list shows only active sessions", "n"),
                  (ADMIN, "An admin can revoke any session", "y")]
        rows = [(key, claim, live, status, evidence[status]) for (key, claim, live), status in zip(claims, statuses)]
        self.write(repo, ".drive/STATUS.md", self.status_md(rows))
        counts = {}
        for status in statuses:
            counts[status] = counts.get(status, 0) + 1
        self.write(repo, ".drive/REPORT.md", self.report_md(counts, outcome="Stopped because the owner paused the work."))
        self.write(repo, ".drive/reviews/2026-09-14-retro.md", RETRO_MD)
        self.set_state(repo, commit=code, status="stopped", phase="report")
        self.commit(repo, "drive(report): stopped")
        return repo

    def test_a_stopped_run_with_work_above_missing_needs_the_final_audit(self):
        repo = self.stopped_run(["Local Proof", "Partial", "Missing"])
        self.assertFails(self.lint(repo, "final"), "a stopped run with any row above Missing is audited")
        audit = ".drive/reviews/2026-09-14-final-audit.json"
        self.write(repo, audit, verdict("final-audit", claims=[KEY, LIST], rung="Local Proof"))
        self.commit(repo, "drive(report): final audit")
        self.assertFails(self.lint(repo, "final"), "has no provenance")
        self.sign(repo, audit, agent_type="drive:auditor", agent_id="agent-audit")
        self.assertNoFailure(self.lint(repo, "final"), "final audit")

    def test_a_stopped_run_with_every_row_missing_needs_no_audit(self):
        repo = self.stopped_run(["Missing", "Missing", "Missing"])
        self.assertNoFailure(self.lint(repo, "final"), "final audit")


class StopTokenTests(Hooks, DriveTestCase):
    """Findings 9 and 10: budget:, credentials:, and aborted need evidence, not words."""

    def blocked(self, repo, blocked_on):
        self.set_state(repo, commit=self.code_sha, status="blocked", blocked=blocked_on)
        self.write(repo, ".drive/REPORT.md", self.report_md({}, outcome="Stopped because the owner must act."))
        return self.stop(repo)

    def test_budget_counts_once_the_maker_spawns_reach_the_budget(self):
        repo = self.make_run()
        self.assertIn("counts only once the budget is spent", self.blocked(repo, "budget: I think we have done enough")["reason"])
        self.commit(repo, "drive: blocked on budget")
        refused = self.run_drive("end", cwd=repo)
        self.assertEqual(refused.returncode, 1, refused.stdout)
        self.assertIn("counts only once the budget is spent", refused.stdout)
        for number in range(8):
            drive.ledger_append(repo, {"kind": "spawn", "agent_type": "drive:implementer", "agent_id": "i-{}".format(number)})
        self.assertIsNone(self.stop(repo))
        closed = self.run_drive("end", cwd=repo)
        self.assertEqual(closed.returncode, 0, closed.stdout)

    def test_budget_counts_a_decision_since_intake_that_says_budget_on_its_decision_line(self):
        repo = self.make_run()
        self.append_decision(repo, "Budget overrun on the admin screen", "finish the list query first.")
        self.assertIn("counts only once", self.blocked(repo, "budget: the admin screen needs a second run")["reason"])
        self.append_decision(repo, "Stop at the envelope", "stop here, because the budget no longer covers the admin screen.")
        self.assertIsNone(self.blocked(repo, "budget: the admin screen needs a second run"))

    def test_credentials_must_name_the_secret(self):
        repo = self.make_run()
        for blocked_on in ("credentials: none", "credentials: the owner's deploy token", "credentials: a production secret only the owner can set"):
            with self.subTest(blocked_on=blocked_on):
                self.assertIn("must name the secret", self.blocked(repo, blocked_on)["reason"])
        for blocked_on in ("credentials: CLOUDFLARE_API_TOKEN for the staging deploy", "credentials: the `stripe live key` in the owner's vault",
                           'credentials: the "Apple notarization password"'):
            with self.subTest(blocked_on=blocked_on):
                self.assertIsNone(self.blocked(repo, blocked_on))

    def test_aborted_needs_a_decision_line_that_begins_with_abort(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha, status="aborted")
        self.write(repo, ".drive/REPORT.md", self.report_md({}, outcome="Stopped because the owner cancelled the migration."))
        self.append_decision(repo, "Keep going", "do not abort; continue with the fix.")
        self.append_decision(repo, "Premature", "aborting now would be premature.")
        self.assertIn("must begin with 'Abort' or 'Aborted'", self.stop(repo)["reason"])
        self.append_decision(repo, "End the migration", "Aborted, because the owner cancelled the migration.")
        self.assertIsNone(self.stop(repo))


class MainThreadGitTests(Hooks, DriveTestCase):
    """Finding 11: the main thread does not stash, clean, or amend in the checkout makers and reviewers share."""

    def test_stash_clean_and_amend_are_refused_while_a_run_is_active(self):
        repo = self.make_run()
        for command, fragment in (("git stash", "uncommitted work"), ("git stash -u", "uncommitted work"),
                                  ("git stash push -m wip", "uncommitted work"), ("git clean -fd", "untracked files"),
                                  ("git clean -f", "untracked files"), ("git commit --amend -m x", "rewrites HEAD"),
                                  ("git commit --amend --no-edit", "voids every review")):
            with self.subTest(command=command):
                self.assertBlocked(self.bash(repo, command), fragment)
        copy = self.scratch / "drive-proj-copy"
        for command in ("git stash list", "git stash show -p", "git clean -n", "git clean --dry-run -d", "git commit -m 'feat: x'",
                        "git -C {} stash".format(copy), "git -C {} commit --amend --no-edit".format(copy)):
            with self.subTest(allowed=command):
                self.assertAllowed(self.bash(repo, command))


class ProviderTests(DriveTestCase):
    """Finding 15: off the Anthropic API, preflight warns that no per-call model override may be passed."""

    def test_preflight_reports_the_provider_and_warns_off_the_anthropic_api(self):
        repo = self.make_run()
        plain = self.run_drive("preflight", "--permission-mode", "auto", cwd=repo, env=NO_PROVIDER)
        self.assertEqual(plain.returncode, 0, plain.stdout)
        self.assertIn("provider: anthropic", plain.stdout)
        self.assertNotIn("must not pass", plain.stdout)
        text = self.run_drive("preflight", "--permission-mode", "auto", cwd=repo, env=dict(NO_PROVIDER, CLAUDE_CODE_USE_BEDROCK="1"))
        self.assertEqual(text.returncode, 0, text.stdout)
        self.assertIn("provider: bedrock", text.stdout)
        for variable, provider in (("CLAUDE_CODE_USE_BEDROCK", "bedrock"), ("CLAUDE_CODE_USE_VERTEX", "vertex"),
                                   ("CLAUDE_CODE_USE_FOUNDRY", "foundry")):
            with self.subTest(provider=provider):
                result = self.run_drive("preflight", "--permission-mode", "auto", "--json", cwd=repo, env=dict(NO_PROVIDER, **{variable: "1"}))
                checks = {c["check"]: c for c in json.loads(result.stdout)["checks"]}
                self.assertEqual(checks["provider"]["level"], "warn")
                self.assertTrue(checks["provider"]["detail"].startswith(provider))
                self.assertIn("must not pass a per-call model override", checks["provider"]["detail"])

    def test_capabilities_records_the_provider(self):
        repo = self.make_run()
        result = self.run_drive("capabilities", cwd=repo, env=dict(NO_PROVIDER, CLAUDE_CODE_USE_VERTEX="true"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads((repo / ".drive/capabilities.json").read_text())["env:provider"], "vertex")


class VisibilityCommandTests(DriveTestCase):
    """Low 23: the visibility subcommand through its command line."""

    def test_visibility_prints_the_answer_then_the_reason(self):
        repo = self.new_repo()
        result = self.run_drive("visibility", cwd=repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], "PRIVATE")
        self.assertTrue(len(lines) > 1 and lines[1].strip())
        self.assertEqual(self.run_drive("visibility", "--root", str(repo), cwd=self.tmp).stdout, result.stdout)
