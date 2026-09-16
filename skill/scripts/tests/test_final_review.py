"""Severe tests for the final clean review (research/32) and the rulings after it (research/24 section 21).

Each class names the finding it covers; every test fails against drive.py as it stood before those fixes."""
import json
import os
import subprocess
from pathlib import Path

from helpers import DRIVE, GOAL_TEXT, SKILL, TEST_COMMAND, DriveTestCase, drive, verdict

KEY = "expired-token-is-rejected"
LIST = "session-list-shows-active-sessions"
ADMIN = "admin-can-revoke-sessions"


class Hooks:
    """Hook helpers (not itself a TestCase)."""

    def stop(self, repo, env=None, **payload):
        self._stops = getattr(self, "_stops", 0) + 1
        data = {"hook_event_name": "Stop", "cwd": str(repo), "session_id": "s-main", "prompt_id": "p-{}".format(self._stops),
                "stop_hook_active": False, "last_assistant_message": "done", "background_tasks": []}
        data.update(payload)
        result = self.run_drive("hook-stop", stdin=json.dumps(data), env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else None

    def guard(self, repo, tool, agent=None, agent_id=None, cwd=None, env=None, tool_use_id="toolu_final", **tool_input):
        payload = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input, "cwd": str(cwd or repo),
                   "session_id": "s-main", "tool_use_id": tool_use_id}
        if agent is not None:
            payload["agent_type"] = agent
            payload["agent_id"] = agent_id or "agent-final"
        return self.run_drive("hook-guard", stdin=json.dumps(payload), env=env)

    def bash(self, repo, command, agent=None, cwd=None, env=None):
        return self.guard(repo, "Bash", agent=agent, cwd=cwd, env=env, command=command)

    def snap(self, repo, phase, agent="drive:verifier", agent_id="agent-v", transcript=None, env=None):
        payload = {"hook_event_name": "SubagentStart" if phase == "start" else "SubagentStop", "cwd": str(repo),
                   "agent_id": agent_id, "agent_type": agent}
        if transcript is not None:
            payload["agent_transcript_path"] = str(transcript)
        result = self.run_drive("hook-snapshot", phase, stdin=json.dumps(payload), env=env)
        self.assertEqual(result.returncode, 0, result.stderr)

    def assertBlocked(self, result, fragment=None):
        self.assertEqual(result.returncode, 2, "expected a block; stderr: {}".format(result.stderr))
        if fragment:
            self.assertIn(fragment, result.stderr)

    def assertAllowed(self, result):
        self.assertEqual(result.returncode, 0, "expected the call to be allowed; stderr: {}".format(result.stderr))

    def gate_log(self, repo):
        path = Path(repo) / ".drive/local/gate.log"
        return path.read_text() if path.exists() else ""

    def rewrite_verdict(self, repo, data, agent_type="drive:verifier"):
        rel = ".drive/proofs/{}/r1/verdict.json".format(KEY)
        self.write(repo, rel, data)
        self.sign(repo, rel, agent_type=agent_type)


class TranscriptProvenanceTests(Hooks, DriveTestCase):
    """Blocking finding 1 and ruling 2: provenance rests on the reviewer's own transcript."""

    def test_a_hand_appended_ledger_line_never_counts(self):
        repo = self.make_run(signed=False)
        rel = ".drive/proofs/{}/r1/verdict.json".format(KEY)
        entry = {"kind": "evidence", "path": rel, "sha256": drive.file_sha256(repo / rel), "agent_type": "drive:verifier",
                 "role": "verifier", "agent_id": "forged-1"}
        drive.ledger_append(repo, entry)
        self.assertFails(self.lint(repo), "has no transcript-backed provenance")
        empty = self.transcript(repo, command="python3 -m pytest -q", agent_id="forged-2")
        sha, size = drive.transcript_digest(empty)
        drive.ledger_append(repo, dict(entry, agent_id="forged-2", transcript=str(empty), transcript_sha256=sha, transcript_size=size))
        self.assertFails(self.lint(repo), "holds no successful Write, Edit, or shell command")

    def test_record_evidence_needs_a_transcript_that_wrote_that_exact_path(self):
        repo = self.make_run(signed=False)
        rel = ".drive/proofs/{}/r1/verdict.json".format(KEY)
        self.assertFalse(drive.record_evidence(repo, rel, "drive:verifier", "v-1"))
        other = self.transcript(repo, ".drive/proofs/{}/r2/verdict.json".format(KEY), agent_id="v-2")
        self.assertFalse(drive.record_evidence(repo, rel, "drive:verifier", "v-2", transcript=str(other)))
        refused = self.transcript(repo, rel, agent_id="v-3", is_error=True)
        self.assertFalse(drive.record_evidence(repo, rel, "drive:verifier", "v-3", transcript=str(refused)))
        outside = self.scratch / "agent-v-4.jsonl"
        outside.write_text(self.transcript(repo, rel, agent_id="v-4").read_text())
        self.assertFalse(drive.record_evidence(repo, rel, "drive:verifier", "v-4", transcript=str(outside)))
        grader = self.transcript(repo, rel, agent_type="drive:grader", agent_id="g-1")
        self.assertFalse(drive.record_evidence(repo, rel, "drive:verifier", "g-1", transcript=str(grader)))
        written = self.transcript(repo, rel, agent_id="v-5", tool="Write")
        self.assertTrue(drive.record_evidence(repo, rel, "drive:verifier", "v-5", transcript=str(written)))
        self.assertNoFailure(self.lint(repo), "provenance")

    def test_a_transcript_rewritten_or_deleted_after_recording_stops_the_evidence_counting(self):
        repo = self.make_run()
        rel = ".drive/proofs/{}/r1/verdict.json".format(KEY)
        entry = [e for e in drive.ledger_entries(repo, "evidence") if e["path"] == rel][-1]
        transcript = Path(entry["transcript"])
        original = transcript.read_text()
        with open(transcript, "a") as handle:
            handle.write(json.dumps({"type": "assistant", "agentId": "agent-verifier", "message": {"content": "resumed later"}}) + "\n")
        self.assertNoFailure(self.lint(repo), "provenance")
        transcript.write_text(original.replace("Verify the claim.", "Verify nothing at all."))
        self.assertFails(self.lint(repo), "changed since the entry was recorded")
        transcript.unlink()
        self.assertFails(self.lint(repo), "no longer exists")

    def test_subagent_stop_records_only_what_the_reviewers_transcript_shows_it_writing(self):
        repo = self.make_run()
        self.snap(repo, "start")
        ours = ".drive/proofs/{}/r2/verdict.json".format(KEY)
        theirs = ".drive/proofs/{}/r2/severe-cases.json".format(KEY)
        self.write(repo, ours, verdict(KEY, round_number=2))
        self.write(repo, theirs, {"cases": ["written by the severe tester during the window"]})
        transcript = self.transcript(repo, ours, agent_id="agent-v")
        self.snap(repo, "stop", transcript=transcript)
        recorded = {e["path"] for e in drive.ledger_entries(repo, "evidence") if e.get("agent_id") == "agent-v"}
        self.assertEqual(recorded, {ours})
        self.assertIn("PROVENANCE REFUSED verifier agent-v {}".format(theirs), self.gate_log(repo))

    def test_a_hand_run_subagent_stop_without_a_real_transcript_records_nothing(self):
        repo = self.make_run(signed=False)
        rel = ".drive/proofs/{}/r1/verdict.json".format(KEY)
        forged = self.scratch / "agent-forged.jsonl"
        forged.write_text(self.transcript(repo, rel, agent_id="forged").read_text())
        for transcript in (None, forged):
            payload = {"hook_event_name": "SubagentStop", "cwd": str(repo), "agent_id": "forged", "agent_type": "drive:verifier"}
            if transcript:
                payload["agent_transcript_path"] = str(transcript)
            self.assertEqual(self.run_drive("hook-snapshot", "stop", stdin=json.dumps(payload)).returncode, 0)
        self.assertEqual(drive.ledger_entries(repo, "evidence"), [])
        self.assertFails(self.lint(repo), "has no provenance")

    def test_hook_subcommands_are_refused_under_any_script_name(self):
        repo = self.make_run()
        copy = self.scratch / "d.py"
        for agent in (None, "drive:verifier", "drive:implementer"):
            for command in ("cp {} {} && python3 {} hook-snapshot stop < /dev/null".format(DRIVE, copy, copy),
                            "D={}; echo '{{}}' | python3 \"$D\" hook-stop".format(DRIVE),
                            "python3 tools/runner.py hook-guard"):
                with self.subTest(agent=agent, command=command):
                    self.assertBlocked(self.bash(repo, command, agent=agent), "drive hook subcommand")

    def test_transcripts_are_out_of_reach_of_tool_calls_but_memory_notes_are_not(self):
        repo = self.make_run()
        transcript = self.home / ".claude/projects/p/s-1/subagents/agent-x.jsonl"
        self.assertBlocked(self.guard(repo, "Write", file_path=str(transcript), content="{}"), "session transcript")
        self.assertBlocked(self.bash(repo, "echo '{{}}' >> {}".format(transcript)))
        self.assertBlocked(self.guard(repo, "Write", agent="drive:implementer", file_path=str(transcript), content="{}"))
        self.assertAllowed(self.guard(repo, "Write", file_path=str(self.home / ".claude/projects/p/memory/MEMORY.md"), content="x"))


class ShellToolTests(Hooks, DriveTestCase):
    """Should-fix 3 and ruling 2: Monitor and PowerShell run shell commands; EnterWorktree makes a branch."""

    def test_monitor_and_powershell_commands_are_guarded_like_bash(self):
        repo = self.make_run()
        self.assertBlocked(self.guard(repo, "Monitor", agent="drive:implementer", command="git commit -am x", description="watch"))
        self.assertBlocked(self.guard(repo, "Monitor", command="git push origin main", description="watch"), "git push")
        self.assertBlocked(self.guard(repo, "PowerShell", command="git push origin main"), "git push")
        self.assertBlocked(self.guard(repo, "Monitor", agent="drive:verifier", command="echo x > src/auth.py"))
        self.assertAllowed(self.guard(repo, "Monitor", command="tail -f .drive/local/logs/build.log", description="build log"))
        self.assertAllowed(self.guard(repo, "Monitor", ws={"url": "wss://example.test/feed"}, description="feed"))

    def test_enter_worktree_is_refused_while_a_run_is_active(self):
        repo = self.make_run()
        for agent in (None, "drive:implementer", "drive:investigator"):
            with self.subTest(agent=agent):
                self.assertBlocked(self.guard(repo, "EnterWorktree", agent=agent, name="side"), "EnterWorktree")
        (repo / ".drive/local/active").unlink()
        self.assertAllowed(self.guard(repo, "EnterWorktree", agent="drive:implementer", name="side"))


class SharedRefsTests(Hooks, DriveTestCase):
    """Blocking finding 2 and ruling 3: no pushes and no branch or tag changes in any worktree sharing the run's refs."""

    def linked(self, repo):
        worktree = self.scratch / "drvrev-wt"
        self.git(repo, "worktree", "add", "-q", "--detach", str(worktree), "HEAD")
        return worktree

    def test_pushes_and_ref_changes_from_a_scratch_worktree_are_refused_for_everyone(self):
        repo = self.make_run()
        wt = self.linked(repo)
        cases = [
            (None, "git -C {} checkout -b evil".format(wt)), (None, "git -C {} update-ref refs/heads/main HEAD".format(wt)),
            (None, "git -C {} push origin HEAD:refs/heads/evil3".format(wt)), (None, "cd {} && git switch -c evil".format(wt)),
            (None, "git -C {} tag v9".format(wt)), (None, "git -C {} branch -f main HEAD".format(wt)),
            (None, "git -C {} symbolic-ref HEAD refs/heads/x".format(wt)), (None, "git push origin main"),
            ("drive:investigator", "git -C {} branch -f main HEAD".format(wt)), ("drive:investigator", "cd {} && git checkout -b hyp".format(wt)),
            ("drive:investigator", "git -C {} push origin HEAD".format(wt)), ("drive:verifier", "git -C {} push origin HEAD:refs/heads/main".format(wt)),
            ("drive:verifier", "git -C {} tag v1".format(wt)), ("drive:auditor", "cd {} && git checkout -b audit".format(wt)),
            ("drive:security-reviewer", "git -C {} branch evil-from-scratch-worktree".format(wt)),
        ]
        for agent, command in cases:
            with self.subTest(agent=agent, command=command):
                self.assertBlocked(self.bash(repo, command, agent=agent))
        for agent, command in ((None, "git -C {} commit -qam experiment".format(wt)),
                               ("drive:investigator", "git -C {} bisect start HEAD HEAD~1".format(wt)),
                               (None, "git -C {} log --oneline -1".format(wt))):
            with self.subTest(agent=agent, allowed=command):
                self.assertAllowed(self.bash(repo, command, agent=agent))

    def test_a_separate_clone_may_branch_but_never_push(self):
        repo = self.make_run()
        clone = self.scratch / "clone"
        clone.mkdir()
        self.git(clone, "init", "-q", "-b", "main")
        for agent in (None, "drive:investigator"):
            with self.subTest(agent=agent):
                self.assertAllowed(self.bash(repo, "git -C {} checkout -b experiment".format(clone), agent=agent))
                self.assertBlocked(self.bash(repo, "git -C {} push origin experiment".format(clone), agent=agent), "git push")

    def test_the_main_threads_git_aliases_are_resolved(self):
        repo = self.make_run()
        self.git(repo, "config", "alias.pp", "push")
        self.git(repo, "config", "alias.nb", "checkout -b")
        self.assertBlocked(self.bash(repo, "git pp origin main"), "git push")
        self.assertBlocked(self.bash(repo, "git nb feature"), "creating a branch")
        self.assertBlocked(self.bash(repo, "git -c alias.pp=push pp origin main"), "alias")

    def test_github_writes_need_a_deploy_line_naming_them(self):
        repo = self.make_run()
        for command in ("gh pr create --fill", "gh release create v1.2.0", "gh repo edit --visibility public", "gh -R o/r pr merge 3"):
            with self.subTest(command=command):
                self.assertBlocked(self.bash(repo, command), "refused")
        self.assertAllowed(self.bash(repo, "gh pr view 3"))
        line = "- [ ] deploy · artifact: the GitHub release · exit: gh release create v1.2.0 published and downloadable · checker: verifier"
        goal = (repo / ".drive/GOAL.md").read_text().replace("\n## Re-plans", line + "\n\n## Re-plans")
        self.write(repo, ".drive/GOAL.md", goal)
        self.assertAllowed(self.bash(repo, "gh release create v1.2.0 --notes-file notes.md"))
        self.assertBlocked(self.bash(repo, "gh pr create --fill"), "refused")

    def test_hygiene_fails_on_any_branch_the_baseline_does_not_list(self):
        repo = self.make_run()
        self.git(repo, "branch", "owner-topic")
        drive.write_baseline(repo)
        self.assertNoFailure(self.lint(repo, "stop"))
        self.git(repo, "branch", "evil-from-scratch-worktree")
        findings = self.lint(repo, "stop")
        self.assertFails(findings, "does not list: evil-from-scratch-worktree")
        self.assertNotIn("owner-topic", self.messages(findings))


class ResumeTests(Hooks, DriveTestCase):
    """Blocking findings 3 and 4, should-fix 14, and ruling 4."""

    def test_resume_recreates_the_marker_without_archiving(self):
        repo = self.make_run()
        (repo / ".drive/local/active").unlink()
        drive.baseline_path(repo).unlink()
        result = self.run_drive("init", "--goal", "-", cwd=repo, stdin=GOAL_TEXT + "\n", env={"CLAUDE_CODE_SESSION_ID": "s-new"})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Re-created .drive/local/active", result.stdout)
        marker = drive.read_marker(repo)
        self.assertEqual((marker["slug"], marker["sessions"]), ("session-auth", ["s-new"]))
        intake = self.git(repo, "log", "--grep", "^drive(intake): session-auth$", "--format=%cI", "-1")
        self.assertEqual(drive.parse_iso(marker["started"]), drive.parse_iso(intake))
        self.assertFalse((repo / ".drive/runs").exists())
        self.assertTrue(drive.baseline_path(repo).is_file())
        self.assertEqual(self.stop(repo, session_id="s-new")["decision"], "block")

    def test_a_goal_with_quotes_resumes_through_stdin(self):
        goal = 'Fix "quoted" $HOME and `ticks` in the export'
        repo = self.new_repo()
        self.write(repo, "README.md", "x\n")
        self.commit(repo, "chore: start")
        self.assertEqual(self.run_drive("init", "--goal", "-", "--size", "S", cwd=repo, stdin=goal).returncode, 0)
        (repo / ".drive/local/active").unlink()
        result = self.run_drive("init", "--goal", "-", cwd=repo, stdin=goal)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Same goal", result.stdout)
        self.assertFalse((repo / ".drive/runs").exists())

    def test_a_launch_preflight_stop_needs_a_failure_preflight_recorded(self):
        repo = self.make_run()
        relaunch = ("launch preflight: Manual mode; relaunched as `cd {} && claude --bg --name drive-session-auth --permission-mode "
                    "auto --settings \"$DRIVE_SETTINGS\" '/drive --resume'`".format(repo))
        self.set_state(repo, commit=self.code_sha, status="blocked", blocked=relaunch)
        self.assertIn("no failed drive.py preflight", self.stop(repo)["reason"])
        failed = self.run_drive("preflight", "--permission-mode", "default", cwd=repo, env={"CLAUDE_CODE_SESSION_ID": "s-main"})
        self.assertEqual(failed.returncode, 1, failed.stdout)
        self.assertIsNone(self.stop(repo))
        passed = self.run_drive("preflight", "--permission-mode", "auto", cwd=repo, env={"CLAUDE_CODE_SESSION_ID": "s-main"})
        self.assertEqual(passed.returncode, 0, passed.stdout)
        self.assertIn("no failed drive.py preflight", self.stop(repo)["reason"])

    def test_resume_says_how_to_leave_blocked_and_stalled(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha, status="stalled")
        self.assertIn("drive.py end", self.run_drive("init", "--goal", "-", cwd=repo, stdin=GOAL_TEXT).stdout)
        self.set_state(repo, commit=self.code_sha, status="blocked", blocked="credentials: the owner's deploy token")
        self.assertIn("one DECISIONS.md entry naming the evidence", self.run_drive("init", "--goal", "-", cwd=repo, stdin=GOAL_TEXT).stdout)

    def test_leaving_blocked_needs_a_decision_and_a_stalled_run_never_runs_again(self):
        repo = self.make_run()
        self.set_state(repo, status="blocked", blocked="credentials: the owner's deploy token")
        self.commit(repo, "drive: blocked")
        self.set_state(repo, status="running")
        self.assertFails(self.lint(repo), "no new DECISIONS.md entry")
        with open(repo / ".drive/DECISIONS.md", "a", encoding="utf-8") as handle:
            handle.write("\n## 2026-09-14 · Continue after the deploy token arrived\n- Decision: continue the run.\n"
                         "- Evidence: wrangler whoami succeeds with the token.\n- Undo: set blocked again · reversal cost: low.\n")
        self.assertNoFailure(self.lint(repo), "no new DECISIONS.md entry")
        self.set_state(repo, status="stalled")
        self.commit(repo, "drive: stalled")
        self.set_state(repo, status="running")
        self.assertFails(self.lint(repo), "status was stalled at HEAD")


class SuiteAndSubGoalTests(Hooks, DriveTestCase):
    """Blocking findings 5 and 6, rulings 5 and 6."""

    def test_none_means_the_project_has_no_suite(self):
        repo = self.make_run()
        goal = (repo / ".drive/GOAL.md").read_text()
        self.write(repo, ".drive/GOAL.md", goal.replace('test_command: "{}"'.format(TEST_COMMAND), 'test_command: "None yet"'))
        self.assertIsNone(drive.Ctx(repo).test_command)
        self.rewrite_verdict(repo, verdict(KEY, ran=[{"cmd": "python3 -m pytest tests/test_auth.py", "exit": 0}]))
        self.assertNoFailure(self.lint(repo), "does not show the full-suite command")
        self.write(repo, ".drive/GOAL.md", goal)
        self.assertFails(self.lint(repo), "does not show the full-suite command")
        self.write(repo, ".drive/GOAL.md", goal.replace("shape: feature", "shape: report"))
        self.assertNoFailure(self.lint(repo), "does not show the full-suite command")

    def sub_goal_run(self):
        repo = self.make_run()
        extra = ("\n## Classification · market-report\n```yaml\nshape: report\nsize: S\n```\n\n"
                 "## Plan · market-report\n- [ ] verify · artifact: .drive/proofs · exit: every report row at Local Proof · checker: verifier\n\n"
                 "## Classification · site\n```yaml\nshape: publish\nsize: S\n```\n")
        self.write(repo, ".drive/GOAL.md", (repo / ".drive/GOAL.md").read_text() + extra)
        text = (repo / ".drive/STATUS.md").read_text()
        text = text.replace("commit:{} |".format(self.code_sha), "commit:{}; sub:market-report |".format(self.code_sha), 1)
        text = text.replace("session list shows active sessions; commit:{} |".format(self.code_sha),
                            "session list shows active sessions; commit:{}; sub:site |".format(self.code_sha))
        text = text.replace("| Missing |  |", "| Missing | sub:site |")
        self.write(repo, ".drive/STATUS.md", text)
        return repo

    def gate(self, repo, phase, sub=None):
        drive._SCHEMAS.clear()
        return drive.run_lint(Path(repo), "base", phase, sub=sub)[1]

    def test_a_sub_goal_gate_checks_only_that_sub_goals_rows(self):
        repo = self.sub_goal_run()
        self.assertNoFailure(self.gate(repo, "verify", "market-report"), "this gate needs")
        self.assertFails(self.gate(repo, "verify", "site"), "STATUS {}: is Partial; this gate needs Local Proof".format(LIST))
        self.assertFails(self.gate(repo, "verify"), "STATUS {}: is Partial".format(LIST))

    def test_a_report_sub_goals_verdict_skips_the_suite_and_an_unknown_sub_fails(self):
        repo = self.sub_goal_run()
        self.rewrite_verdict(repo, verdict(KEY, ran=[{"cmd": "curl -sI https://example.test/report", "exit": 0}]))
        self.assertNoFailure(self.lint(repo), "does not show the full-suite command")
        text = (repo / ".drive/STATUS.md").read_text().replace("sub:market-report", "sub:nowhere")
        self.write(repo, ".drive/STATUS.md", text)
        findings = self.lint(repo)
        self.assertFails(findings, "sub:nowhere names no '## Classification · nowhere'")
        self.assertFails(findings, "does not show the full-suite command")


class StopGateFactTests(Hooks, DriveTestCase):
    """Should-fix 2, 8, and 1, and note 10: the Stop gate opens on facts."""

    def report(self, repo, outcome="Stopped because the owner must act."):
        self.write(repo, ".drive/REPORT.md", self.report_md({}, outcome=outcome))

    def test_blocked_on_must_begin_with_a_stop_condition_token(self):
        repo = self.make_run()
        self.report(repo, "Stopped because I felt like it")
        self.set_state(repo, commit=self.code_sha, status="blocked", blocked="updating the license header in src/app.py")
        self.assertIn("names no stop condition", self.stop(repo)["reason"])
        for blocked in ("legal: the dataset licence needs the owner's acceptance", "soak: the seven-day window closes 2026-09-21"):
            with self.subTest(blocked=blocked):
                self.set_state(repo, commit=self.code_sha, status="blocked", blocked=blocked)
                self.assertIsNone(self.stop(repo))
        self.set_state(repo, commit=self.code_sha, status="blocked", blocked="credentials:")
        self.assertIn("names no stop condition", self.stop(repo)["reason"])

    def test_an_abort_counts_only_on_the_decision_line(self):
        repo = self.make_run()
        self.report(repo)
        self.set_state(repo, commit=self.code_sha, status="aborted")
        with open(repo / ".drive/DECISIONS.md", "a", encoding="utf-8") as handle:
            handle.write("\n## 2026-09-14 · Keep going with the cache\n- Decision: keep the cache.\n- Rejected: aborting the run.\n"
                         "- Undo: remove the cache · reversal cost: low.\n")
        self.assertIn("Decision: line records that the run was aborted", self.stop(repo)["reason"])
        with open(repo / ".drive/DECISIONS.md", "a", encoding="utf-8") as handle:
            handle.write("\n## 2026-09-14 · End the run\n- Decision: abort; the owner ended the run.\n- Undo: /drive --resume · reversal cost: low.\n")
        self.assertIsNone(self.stop(repo))

    def test_in_flight_matches_a_task_id_or_its_whole_command_never_its_description(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha, in_flight="npm run build in background (log at .drive/local/logs/build.log)")
        spin = {"id": "bash_7f3", "type": "shell", "status": "running", "description": "run build", "command": "while true; do :; done"}
        self.assertEqual(self.stop(repo, background_tasks=[spin])["decision"], "block")
        self.assertIsNone(self.stop(repo, background_tasks=[dict(spin, command="npm run build")]))
        self.set_state(repo, commit=self.code_sha, in_flight="bash_7f3 → the e2e suite (log at .drive/local/logs/e2e.log)")
        self.assertIsNone(self.stop(repo, background_tasks=[spin]))

    def test_one_stop_event_delivered_twice_counts_once(self):
        repo = self.make_run()
        payload = json.dumps({"hook_event_name": "Stop", "cwd": str(repo), "session_id": "s-main", "prompt_id": "same"})
        first = self.run_drive("hook-stop", stdin=payload)
        second = self.run_drive("hook-stop", stdin=payload)
        self.assertEqual(json.loads(first.stdout), json.loads(second.stdout))
        self.assertEqual(json.loads((repo / ".drive/local/stop-gate.json").read_text())["count"], 1)

    def test_a_turn_ended_by_the_block_cap_is_recorded_and_the_start_view_says_so(self):
        repo = self.make_run()
        env = {"CLAUDE_CODE_STOP_HOOK_BLOCK_CAP": "2"}
        for attempt in range(2):
            self.set_state(repo, commit=self.code_sha, extra_facts="- attempt {}. Verified: the gate log.\n".format(attempt))
            self.assertEqual(self.stop(repo, env=env)["decision"], "block")
        self.assertIn("CAP 2 consecutive blocks", self.gate_log(repo))
        self.assertIn("block cap ended that turn", self.run_drive("start", cwd=repo).stdout)
        self.assertTrue(drive.ledger_entries(repo, "stop-cap"))

    def test_the_stop_gate_holds_only_the_runs_own_sessions(self):
        repo = self.make_run()
        self.write(repo, ".drive/local/active", json.dumps({"slug": "session-auth", "sessions": ["s-run"]}) + "\n")
        self.assertIsNone(self.stop(repo, session_id="s-xs-fix"))
        self.assertEqual(self.stop(repo, session_id="s-run")["decision"], "block")

    def test_hook_commands_exit_zero_when_drive_py_is_missing_and_stop_is_a_plugin_hook(self):
        data = json.loads((SKILL / "hooks" / "hooks.json").read_text())["hooks"]
        self.assertIn("Stop", data)
        for event, entries in data.items():
            for entry in entries:
                for hook in entry["hooks"]:
                    for root, stdin in ((self.tmp / "missing", "{}"), (SKILL, json.dumps({"cwd": str(self.tmp)}))):
                        with self.subTest(event=event, root=str(root)):
                            env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(root))
                            proc = subprocess.run(["sh", "-c", hook["command"]], input=stdin, capture_output=True, text=True,
                                                  env=env, timeout=60)
                            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_a_resumed_drive_session_is_told_to_run_preflight(self):
        repo = self.make_run()
        self.write(repo, ".drive/local/active", json.dumps({"slug": "session-auth", "sessions": ["s-drive"]}) + "\n")
        payload = {"hook_event_name": "SessionStart", "source": "resume", "cwd": str(repo), "session_id": "s-drive"}
        self.assertIn("preflight", self.run_drive("hook-reinject", stdin=json.dumps(payload)).stdout)


class ReviewerAndMakerWriteTests(Hooks, DriveTestCase):
    """Should-fix 4 and 7, and note 9."""

    def test_reviewers_cannot_install_reformat_or_write_through_a_module_run(self):
        repo = self.make_run()
        for command in ("python3 -m json.tool .drive/local/active src/app.py", "python3 -m pip install requests", "pip install requests",
                        "uv pip install requests", "poetry add requests", "prettier --write src", "npx eslint --fix src",
                        "ruff check --fix src", "ruff format src", "black src", "cargo fmt", "python3 -m http.server"):
            with self.subTest(command=command):
                self.assertBlocked(self.bash(repo, command, agent="drive:verifier"))
        for command in ("python3 -m json.tool .drive/local/active", "python3 -m pytest -q", "python3 -m unittest discover -s tests",
                        "prettier --check src", "ruff check src", "black --check src", "npx eslint src"):
            with self.subTest(allowed=command):
                self.assertAllowed(self.bash(repo, command, agent="drive:verifier"))

    def test_the_severe_tester_writes_only_its_own_proof_files(self):
        repo = self.make_run()
        agent = "drive:severe-tester"
        base = repo / ".drive/proofs/{}/r2".format(KEY)
        for name in ("severe-forged-expiry.md", "commands.log", "red/pytest.txt", "red/cases.json"):
            with self.subTest(allowed=name):
                self.assertAllowed(self.guard(repo, "Write", agent=agent, file_path=str(base / name), content="x"))
        for name in ("verdict.json", "refute-token-replay.json", "notes.md", "../proof.json"):
            with self.subTest(refused=name):
                self.assertBlocked(self.guard(repo, "Write", agent=agent, file_path=str(base / name), content="x"))
        self.assertBlocked(self.bash(repo, "echo '{{}}' > {}".format(base / "verdict.json"), agent=agent))
        self.assertAllowed(self.bash(repo, "python3 -m pytest tests > {} 2>&1".format(base / "commands.log"), agent=agent))

    def test_shell_edits_by_the_lead_or_a_maker_while_a_reviewer_runs_do_not_void_it(self):
        repo = self.make_run()
        self.snap(repo, "start")
        for agent, tool_use_id, line in ((None, "toolu_lead", "# lead\n"), ("drive:implementer", "toolu_maker", "# maker\n")):
            command = "printf '{}' >> src/auth.py".format(line.strip())
            payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_use_id": tool_use_id, "cwd": str(repo),
                       "session_id": "s-main", "tool_input": {"command": command}}
            if agent:
                payload.update(agent_type=agent, agent_id="i-1")
            self.assertEqual(self.run_drive("hook-guard", stdin=json.dumps(payload)).returncode, 0)
            with open(repo / "src/auth.py", "a") as handle:
                handle.write(line)
            post = dict(payload, hook_event_name="PostToolUse")
            self.assertEqual(self.run_drive("hook-post", stdin=json.dumps(post)).returncode, 0)
        self.snap(repo, "stop")
        self.assertEqual(drive.ledger_entries(repo, "void"), [])
        self.snap(repo, "start", agent_id="agent-v2")
        self.write(repo, "README.md", "# changed by the reviewer, recorded by no hook\n")
        self.snap(repo, "stop", agent_id="agent-v2")
        self.assertEqual(len(drive.ledger_entries(repo, "void")), 1)

    def test_a_maker_restores_only_paths_a_brief_owns(self):
        repo = self.make_run()
        self.assertBlocked(self.bash(repo, "git restore src/auth.py", agent="drive:implementer"), "git restore")
        brief = (Path(drive.TEMPLATES) / "package-brief.md").read_text().replace("<package id>", "auth-core").replace(
            "- `<path or glob>`", "- `src/**`", 1)
        self.write(repo, ".drive/packages/auth-core/brief.md", brief)
        self.assertAllowed(self.bash(repo, "git restore src/auth.py", agent="drive:implementer"))
        for command in ("git restore README.md", "git restore 'src/*.py'", "git restore src/auth.py README.md"):
            with self.subTest(command=command):
                self.assertBlocked(self.bash(repo, command, agent="drive:writer"), "git restore")
        # 'git restore .' would also restore drive's own freeze files, and that older rule refuses it first.
        self.assertBlocked(self.bash(repo, "git restore .", agent="drive:writer"))

    def test_inline_code_naming_a_frozen_test_by_a_literal_path_is_refused(self):
        repo = self.make_run()
        self.assertEqual(self.run_drive("freeze", "add", "tests/test_auth.py", cwd=repo).returncode, 0)
        for command in ("python3 -c \"open('tests/test_auth.py', 'w').write('')\"",
                        "cd tests && python3 -c \"open('test_auth.py', 'w').write('')\"",
                        "cd tests && node -e \"require('fs').writeFileSync('./test_auth.py', '')\""):
            with self.subTest(command=command):
                self.assertBlocked(self.bash(repo, command, agent="drive:implementer"), "frozen")
        self.assertAllowed(self.bash(repo, "cd tests && python3 -c \"open('test_other.py', 'w').write('')\"", agent="drive:implementer"))


class BudgetTests(Hooks, DriveTestCase):
    """The subagent figure counts makers only and is a checkpoint: past it, even past twice it, the lint warns and names
    the checkpoint work, and nothing about spend fails a gate."""

    def test_reviewer_spawns_do_not_count_and_maker_spawns_past_the_figure_only_warn(self):
        repo = self.make_run()
        for number in range(30):
            drive.ledger_append(repo, {"kind": "spawn", "agent_type": "drive:verifier", "agent_id": "v-{}".format(number)})
        findings = self.lint(repo, gate="build")
        self.assertNoFailure(findings, "maker subagents")
        self.assertNotIn("maker subagents", self.messages(findings, "warn"))
        for number in range(17):
            drive.ledger_append(repo, {"kind": "spawn", "agent_type": "drive:implementer", "agent_id": "i-{}".format(number)})
        findings = self.lint(repo, gate="build")
        self.assertNoFailure(findings, "maker subagents")
        warnings = self.messages(findings, "warn")
        self.assertIn("17 maker subagents have started against a target of 8", warnings)
        self.assertIn("checkpoint", warnings)


class SnapshotBudgetTests(Hooks, DriveTestCase):
    """Note 8: the snapshot never reads every dirty file inside its timeout."""

    def test_files_past_the_cap_are_compared_by_size_and_time_and_still_void(self):
        repo = self.make_run()
        # Tracked files with uncommitted changes: untracked paths no longer void a review (research/34 finding 4).
        self.write(repo, "build/a.txt", "a\n")
        self.write(repo, "build/b.txt", "b\n")
        self.commit(repo, "chore: track build notes")
        self.write(repo, "build/a.txt", "a, edited\n")
        self.write(repo, "build/b.txt", "b, edited\n")
        env = {"DRIVE_SNAPSHOT_MAX_FILES": "1"}
        self.snap(repo, "start", env=env)
        self.assertIn("compared by size and modification time", self.gate_log(repo))
        record = json.loads((repo / ".drive/local/ro/agent-v.json").read_text())
        stat_file = next(rel for rel, value in record["files"].items() if " stat:" in value)
        self.write(repo, stat_file, "changed by the reviewer\n")
        self.snap(repo, "stop", env=env)
        voids = drive.ledger_entries(repo, "void")
        self.assertEqual(len(voids), 1)
        self.assertIn(stat_file, voids[0]["detail"])

    def test_a_start_the_hook_never_finished_is_logged_and_does_not_void(self):
        repo = self.make_run()
        folder = repo / ".drive/local/ro"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "agent-v.json").write_text(json.dumps({"started_ts": 0, "evidence": {}, "files": {}, "head": "none", "partial": True}))
        self.write(repo, "src/auth.py", "def check(token, now):\n    return True\n")
        self.snap(repo, "stop")
        self.assertEqual(drive.ledger_entries(repo, "void"), [])
        self.assertIn("did not finish", self.gate_log(repo))


class ScheduledDeletionTests(Hooks, DriveTestCase):
    """Should-fix 15: no scheduled deletion outlives the run's hooks unless it is the owner's step."""

    def test_a_scheduled_deletion_must_be_an_owner_step(self):
        repo = self.make_final_run()
        with open(repo / ".drive/DECISIONS.md", "a", encoding="utf-8") as handle:
            handle.write("\n## 2026-09-14 · Schedule the old store deletion\n- Decision: schedule a check for 2026-10-14 that deletes "
                         "the old D1 database.\n- Undo: cancel the scheduled check · reversal cost: low.\n- Evidence: none\n- Narrows: none\n")
        self.assertFails(self.lint(repo, "final"), "a scheduled deletion")
        report = (repo / ".drive/REPORT.md").read_text().replace(
            "## Needed from you\nnone", "## Needed from you\n- Delete the old D1 database after 2026-10-14 with `wrangler d1 delete "
                                        "old-db`; the export and restore were verified on 2026-09-14.")
        self.write(repo, ".drive/REPORT.md", report)
        self.assertNoFailure(self.lint(repo, "final"), "a scheduled deletion")


class InstallAndTemplateTests(DriveTestCase):
    """Note 7 and note 3."""

    def test_install_states_its_runtime_and_the_settings_write_enable_makes(self):
        text = (SKILL.parent / "install.sh").read_text()
        self.assertIn("about three minutes", text)
        self.assertNotIn("about a minute", text)
        self.assertIn("enabledPlugins", text)
        self.assertNotIn("Nothing is written to any\n# settings file", text)

    def test_the_state_template_asks_for_the_session_id_and_lists_the_stop_tokens(self):
        text = (SKILL / "templates" / "STATE.md").read_text()
        self.assertIn("session: <session id>", text)
        for token in drive.BLOCKED_TOKENS:
            self.assertIn(token, text)
