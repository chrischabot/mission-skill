"""Stop gate, re-injection, and tree snapshot hooks."""
import json
from pathlib import Path

from helpers import DriveTestCase, SKILL, drive, state_md, verdict


class StopHookTests(DriveTestCase):
    def stop(self, repo, **payload):
        self._stops = getattr(self, "_stops", 0) + 1
        data = {"hook_event_name": "Stop", "cwd": str(repo), "stop_hook_active": False, "prompt_id": "prompt-{}".format(self._stops),
                "last_assistant_message": "done", "background_tasks": [], "session_crons": []}
        data.update(payload)
        result = self.hook("hook-stop", data)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else None

    def test_without_the_marker_a_running_state_warns_once_and_never_blocks(self):
        repo = self.make_run()
        (repo / ".drive/local/active").unlink()
        first = self.stop(repo, session_id="s-1")
        self.assertNotIn("decision", first)
        self.assertIn(".drive/local/active is missing", first["systemMessage"])
        self.assertIsNone(self.stop(repo, session_id="s-1"))

    def test_inert_without_active_marker_once_the_run_has_ended(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha, status="stopped")
        (repo / ".drive/local/active").unlink()
        self.assertIsNone(self.stop(repo))

    def test_inert_without_cwd(self):
        self.make_run()
        result = self.hook("hook-stop", {"hook_event_name": "Stop"})
        self.assertEqual(result.stdout.strip(), "")

    def test_running_run_blocks_with_next_step(self):
        repo = self.make_run()
        decision = self.stop(repo)
        self.assertEqual(decision["decision"], "block")
        self.assertIn("Run the verifier on the session revocation claim", decision["reason"])
        self.assertIn("BLOCK", (repo / ".drive/local/gate.log").read_text())

    def test_block_reason_includes_lint_findings(self):
        repo = self.make_run()
        self.write(repo, "src/new.py", "x = 1\n")
        decision = self.stop(repo)
        self.assertIn("uncommitted changes", decision["reason"])

    def test_running_subagent_opens_the_gate(self):
        repo = self.make_run()
        tasks = [{"id": "a1", "type": "subagent", "status": "running", "description": "verify", "agent_type": "drive:verifier"}]
        self.assertIsNone(self.stop(repo, background_tasks=tasks))
        self.assertIn("ALLOW background", (repo / ".drive/local/gate.log").read_text())

    def test_workflow_listed_in_flight_opens_the_gate(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha,
                       in_flight="workflow w1 review-panel → expired-token-is-rejected (report at .drive/local/workers/panel/report.md)")
        tasks = [{"id": "w1", "type": "workflow", "status": "running", "name": "review-panel"}]
        self.assertIsNone(self.stop(repo, background_tasks=tasks))

    def test_lone_background_shell_not_in_state_does_not_open_the_gate(self):
        repo = self.make_run()
        tasks = [{"id": "s1", "type": "shell", "status": "running", "description": "dev server", "command": "npm run dev"}]
        self.assertEqual(self.stop(repo, background_tasks=tasks)["decision"], "block")

    def test_background_shell_listed_in_flight_opens_the_gate(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha, in_flight="npm run test:e2e (log at .drive/local/logs/e2e.log)")
        tasks = [{"id": "s1", "type": "shell", "status": "running", "description": "e2e", "command": "npm run test:e2e"}]
        self.assertIsNone(self.stop(repo, background_tasks=tasks))

    def test_caffeinate_never_opens_the_gate_even_when_listed(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha, in_flight="caffeinate -i -w 123")
        tasks = [{"id": "s1", "type": "shell", "status": "running", "description": "keep awake", "command": "caffeinate -i -w 123"}]
        self.assertEqual(self.stop(repo, background_tasks=tasks)["decision"], "block")

    def test_completed_subagent_does_not_open_the_gate(self):
        repo = self.make_run()
        tasks = [{"id": "a1", "type": "subagent", "status": "completed", "agent_type": "drive:verifier"}]
        self.assertEqual(self.stop(repo, background_tasks=tasks)["decision"], "block")

    def test_stall_detection_after_six_unchanged_blocks(self):
        repo = self.make_run()
        for attempt in range(6):
            decision = self.stop(repo)
            self.assertEqual(decision.get("decision"), "block", "attempt {}".format(attempt + 1))
        decision = self.stop(repo)
        self.assertNotIn("decision", decision)
        self.assertIn("stalled", decision["systemMessage"])
        for counted in ("STATE.md", "STATUS.md", "HEAD", "working tree"):
            self.assertIn(counted, decision["systemMessage"])
        self.assertIn("status: stalled", (repo / ".drive/STATE.md").read_text())
        self.assertIn("STALL", (repo / ".drive/local/gate.log").read_text())
        self.assertIsNone(self.stop(repo))

    def test_changing_state_resets_stall_count(self):
        repo = self.make_run()
        for _ in range(5):
            self.stop(repo)
        self.set_state(repo, commit=self.code_sha, in_flight="drive:verifier → admin-can-revoke-sessions")
        for attempt in range(6):
            self.assertEqual(self.stop(repo).get("decision"), "block", "attempt {}".format(attempt + 1))

    def test_blocked_naming_a_stop_condition_with_a_report_allows(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha, status="blocked", blocked="credentials: STAGING_DEPLOY_TOKEN, a production secret only the owner can set")
        self.write(repo, ".drive/REPORT.md", self.report_md(
            {"Local Proof": 1, "Partial": 1, "Missing": 1},
            outcome="Stopped because the deploy needs a production secret only the owner can set."))
        self.assertIsNone(self.stop(repo))

    def test_done_with_failing_final_lint_blocks(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha, status="done")
        decision = self.stop(repo)
        self.assertEqual(decision["decision"], "block")
        self.assertIn("lint --final fails", decision["reason"])

    def test_done_with_passing_final_lint_allows(self):
        repo = self.make_final_run()
        result = self.run_drive("lint", "--final", cwd=repo)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIsNone(self.stop(repo))

    def test_stopped_is_treated_like_done(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha, status="stopped")
        self.assertEqual(self.stop(repo)["decision"], "block")

    def test_missing_state_blocks(self):
        repo = self.make_run()
        (repo / ".drive/STATE.md").unlink()
        self.assertIn("STATE.md is missing", self.stop(repo)["reason"])

    def test_worktree_cwd_resolves_to_main_checkout(self):
        repo = self.make_run()
        wt = self.scratch / "drive-proj-arm"
        self.git(repo, "worktree", "add", "-q", "--detach", str(wt), "HEAD")
        self.assertEqual(self.stop(wt)["decision"], "block")


class ReinjectTests(DriveTestCase):
    def test_prints_nothing_without_a_run(self):
        repo = self.new_repo()
        result = self.hook("hook-reinject", {"hook_event_name": "SessionStart", "source": "compact", "cwd": str(repo)})
        self.assertEqual(result.stdout, "")

    def test_prints_start_view_and_skill_tail(self):
        repo = self.make_run()
        result = self.hook("hook-reinject", {"hook_event_name": "SessionStart", "source": "compact", "cwd": str(repo)})
        self.assertIn("DRIVE · START", result.stdout)
        self.assertIn("next: Run the verifier", result.stdout)
        # make_run is a rigorous run: SKILL.md's standing rules, then references/rigorous.md's contract, delegation, and
        # section 7 to the end.
        self.assertIn("rigorous mode", result.stdout)
        self.assertIn("## Standing rules", result.stdout)
        rigorous = (SKILL / "references" / "rigorous.md").read_text().splitlines()
        for prefix in ("## 1. ", "## 6. ", "## 7. ", "## 9. ", "## Reference index"):
            heading = next((line for line in rigorous if line.startswith(prefix)), None)
            self.assertIsNotNone(heading, "references/rigorous.md has a {!r} section".format(prefix))
            self.assertIn(heading, result.stdout)
        for prefix in ("## 2. ", "## 3. ", "## 4. ", "## 5. "):
            heading = next(line for line in rigorous if line.startswith(prefix))
            self.assertNotIn(heading, result.stdout)
        skill = (SKILL / "SKILL.md").read_text().splitlines()
        self.assertNotIn(next(line for line in skill if line.startswith("## 3. ")), result.stdout)
        self.assertNotIn("argument-hint:", result.stdout)
        last = next(line for line in reversed(rigorous) if line.strip())
        self.assertIn(last, result.stdout)

    def test_start_command_without_run(self):
        repo = self.new_repo()
        result = self.run_drive("start", cwd=repo)
        self.assertEqual(result.returncode, 0)
        self.assertIn("No drive run", result.stdout)

    def test_start_view_lists_open_rows_and_repeated_workarounds(self):
        repo = self.make_run()
        text = state_md(self.code_sha).replace("|---|---|---|---|---|",
                                               "|---|---|---|---|---|\n| store timeout | raised timeout | implementer | 2026-09-14 | 2 |")
        self.write(repo, ".drive/STATE.md", text)
        result = self.run_drive("start", cwd=repo)
        self.assertEqual(result.returncode, 0)
        self.assertIn("admin-can-revoke-sessions · Missing", result.stdout)
        self.assertIn("store timeout", result.stdout)
        self.assertIn("Lint (stop checks)", result.stdout)


class SnapshotTests(DriveTestCase):
    def snap(self, repo, phase, agent="drive:verifier", agent_id="agent-1", transcript=None):
        payload = {"hook_event_name": "SubagentStart" if phase == "start" else "SubagentStop", "cwd": str(repo),
                   "agent_id": agent_id, "agent_type": agent}
        if transcript is not None:
            payload["agent_transcript_path"] = str(transcript)
        result = self.hook("hook-snapshot", payload, phase)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "", "the snapshot hook never returns a decision to a reviewer")
        return None

    def voids(self, repo):
        return drive.ledger_entries(Path(repo), "void")

    def main_thread_bash(self, repo, command, tool_use_id="toolu_main_1"):
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_use_id": tool_use_id, "cwd": str(repo),
                   "session_id": "s-main", "tool_input": {"command": command}}
        self.assertEqual(self.hook("hook-guard", payload).returncode, 0)
        return payload

    def test_tracked_change_by_read_only_agent_voids_the_review_without_blocking(self):
        repo = self.make_run()
        self.snap(repo, "start")
        self.write(repo, "src/auth.py", "def check(token, now):\n    return True\n")
        self.snap(repo, "stop")
        voids = self.voids(repo)
        self.assertEqual(len(voids), 1)
        self.assertIn("src/auth.py", voids[0]["detail"])
        self.assertTrue((repo / ".drive/local/ro/agent-1.void").is_file())
        self.assertIn("SNAPSHOT VOID", (repo / ".drive/local/gate.log").read_text())

    def test_orchestrator_rewriting_state_while_a_verifier_runs_is_not_the_verifiers_change(self):
        repo = self.make_run()
        self.snap(repo, "start")
        with open(repo / ".drive/STATE.md", "a", encoding="utf-8") as handle:
            handle.write("- 2026-09-14 · src/auth.py · noticed while the verifier ran · later\n")
        self.snap(repo, "stop")
        self.assertEqual(self.voids(repo), [])

    def test_ignored_build_output_does_not_void(self):
        repo = self.make_run()
        self.write(repo, ".gitignore", ".drive/local/\nbuild/\n")
        self.commit(repo, "chore: ignore build output")
        self.snap(repo, "start")
        self.write(repo, "build/out.js", "compiled\n")
        self.write(repo, ".drive/proofs/expired-token-is-rejected/r2/pytest.txt", "1 passed\n")
        self.snap(repo, "stop")
        self.assertEqual(self.voids(repo), [])

    def test_untracked_file_created_by_a_reviewer_is_noted_and_left_to_the_hygiene_lint(self):
        repo = self.make_run()
        self.snap(repo, "start")
        self.write(repo, "src/new_module.py", "def backdoor():\n    return True\n")
        self.snap(repo, "stop")
        self.assertEqual(self.voids(repo), [])
        log = (repo / ".drive/local/gate.log").read_text()
        self.assertIn("SNAPSHOT NOTE", log)
        self.assertIn("src/new_module.py", log)
        self.assertFails(self.lint(repo, "stop"), "src/new_module.py")

    def test_further_edit_to_an_already_dirty_file_voids(self):
        repo = self.make_run()
        self.write(repo, "src/auth.py", "def check(token, now):\n    return token.expires_at >= now\n")
        self.snap(repo, "start")
        self.write(repo, "src/auth.py", "def check(token, now):\n    return True\n")
        self.snap(repo, "stop")
        self.assertEqual(len(self.voids(repo)), 1)

    def test_commit_the_main_thread_did_not_make_voids(self):
        repo = self.make_run()
        self.snap(repo, "start")
        self.write(repo, "README.md", "# changed\n")
        self.commit(repo, "sneaky")
        self.snap(repo, "stop")
        self.assertIn("did not make", self.voids(repo)[0]["detail"])

    def test_main_thread_commit_while_a_verifier_runs_is_tolerated(self):
        repo = self.make_run()
        self.write(repo, "src/wiring.py", "ROUTES = []\n")
        self.snap(repo, "start")
        payload = self.main_thread_bash(repo, "git add -A && git commit -m wiring")
        self.commit(repo, "feat: wiring")
        post = dict(payload, hook_event_name="PostToolUse")
        self.assertEqual(self.hook("hook-post", post).returncode, 0)
        self.snap(repo, "stop")
        self.assertEqual(self.voids(repo), [])

    def test_main_thread_edit_while_a_verifier_runs_is_not_blamed_on_it(self):
        repo = self.make_run()
        self.snap(repo, "start")
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Edit", "cwd": str(repo), "session_id": "s-main",
                   "tool_input": {"file_path": str(repo / "src/auth.py"), "old_string": "a", "new_string": "b"}}
        self.assertEqual(self.hook("hook-guard", payload).returncode, 0)
        self.write(repo, "src/auth.py", "def check(token, now):\n    return token.expires_at >= now\n")
        self.snap(repo, "stop")
        self.assertEqual(self.voids(repo), [])

    def test_bare_agent_name_is_not_a_drive_reviewer(self):
        repo = self.make_run()
        self.snap(repo, "start", agent="grader")
        self.write(repo, "README.md", "# changed\n")
        self.snap(repo, "stop", agent="grader")
        self.assertEqual(self.voids(repo), [])
        self.assertFalse((repo / ".drive/local/ro/agent-1.json").exists())

    def test_reviewer_evidence_is_recorded_in_the_provenance_ledger(self):
        repo = self.make_run()
        self.snap(repo, "start")
        rel = ".drive/proofs/expired-token-is-rejected/r2/verdict.json"
        path = self.write(repo, rel, verdict("expired-token-is-rejected"))
        transcript = self.transcript(repo, rel, agent_id="agent-1")
        self.snap(repo, "stop", transcript=transcript)
        entries = [e for e in drive.ledger_entries(Path(repo), "evidence") if e["path"] == rel]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["transcript"], str(transcript))
        self.assertEqual(entries[0]["transcript_sha256"], drive.transcript_digest(transcript)[0])
        self.assertEqual(entries[0]["agent_type"], "drive:verifier")
        self.assertEqual(entries[0]["sha256"], drive.file_sha256(path))
        self.assertEqual(entries[0]["agent_id"], "agent-1")

    def test_verdict_written_while_the_review_was_voided_does_not_count(self):
        repo = self.make_run()
        self.snap(repo, "start")
        rel = ".drive/proofs/expired-token-is-rejected/r1/verdict.json"
        self.write(repo, rel, dict(verdict("expired-token-is-rejected", round_number=1), for_maker="rewritten while src changed"))
        self.write(repo, "src/auth.py", "def check(token, now):\n    return True\n")
        self.snap(repo, "stop", transcript=self.transcript(repo, rel, agent_id="agent-1"))
        self.assertFails(self.lint(repo), "was voided because tracked files changed while it ran")

    def test_maker_agents_and_inactive_runs_are_ignored(self):
        repo = self.make_run()
        self.snap(repo, "start", agent="drive:implementer")
        self.write(repo, "README.md", "# changed\n")
        self.snap(repo, "stop", agent="drive:implementer")
        self.assertEqual(self.voids(repo), [])
        (repo / ".drive/local/active").unlink()
        self.snap(repo, "start")
        self.write(repo, "README.md", "# changed again\n")
        self.snap(repo, "stop")
        self.assertEqual(self.voids(repo), [])


class HooksJsonTests(DriveTestCase):
    def test_hooks_json_registers_the_expected_commands(self):
        import re
        data = json.loads((SKILL / "hooks" / "hooks.json").read_text())["hooks"]
        self.assertEqual(data["SessionStart"][0]["matcher"], "compact|resume")
        self.assertIn("hook-reinject", data["SessionStart"][0]["hooks"][0]["command"])
        self.assertIn("hook-stop", data["Stop"][0]["hooks"][0]["command"])
        for tool in ("Bash", "PowerShell", "Monitor", "Edit", "Write", "NotebookEdit", "MultiEdit", "EnterWorktree"):
            self.assertTrue(re.fullmatch("(?:{})".format(data["PreToolUse"][0]["matcher"]), tool), tool)
        self.assertFalse(re.fullmatch("(?:{})".format(data["PreToolUse"][0]["matcher"]), "ExitWorktree"))
        self.assertIn("hook-guard", data["PreToolUse"][0]["hooks"][0]["command"])
        self.assertEqual(data["PostToolUse"][0]["matcher"], "Bash|PowerShell")
        self.assertIn("hook-post", data["PostToolUse"][0]["hooks"][0]["command"])
        start, stop = data["SubagentStart"][0], data["SubagentStop"][0]
        self.assertIn("hook-snapshot start", start["hooks"][0]["command"])
        self.assertIn("hook-snapshot stop", stop["hooks"][0]["command"])
        for name in ("drive:verifier", "drive:implementer", "drive:grader"):
            self.assertTrue(re.search(start["matcher"], name), name)
        for name in ("drive:verifier", "drive:grader", "drive:auditor", "drive:ui-reviewer", "drive:security-reviewer"):
            self.assertTrue(re.search(stop["matcher"], name), name)
        self.assertFalse(re.search(stop["matcher"], "drive:security-reviewer-legacy"))
        for entry in (start, stop):
            for name in ("auditor", "verifier", "other-plugin:verifier", "Explore"):
                self.assertFalse(re.search(entry["matcher"], name), name)
        self.assertFalse(re.search(stop["matcher"], "drive:implementer"))
        for event in data.values():
            for entry in event:
                for hook in entry["hooks"]:
                    self.assertIn("timeout", hook)
                    self.assertTrue(hook["command"].startswith('p="${CLAUDE_PLUGIN_ROOT}/scripts/drive.py"; [ -f "$p" ] || exit 0; exec python3 "$p" hook-'),
                                    hook["command"])
