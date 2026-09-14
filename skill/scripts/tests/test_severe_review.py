"""Severe tests for the clean review (research/29) and the enforcement audit (research/31).

Each test reproduces an attack or a false result the reviews observed in a scratch repository, and fails
against the code as it stood before the fix."""
import json
import os
import re
import shlex
import time
from pathlib import Path
from unittest import mock

from helpers import DRIVE, GOAL_TEXT, SKILL, SUITE_OK, TEST_COMMAND, TODAY, DriveTestCase, drive, goal_md, iso, proof_manifest, verdict

KEY = "expired-token-is-rejected"
LIST = "session-list-shows-active-sessions"
ADMIN = "admin-can-revoke-sessions"


class Severe:
    """Hook and evidence helpers shared by the classes below (not itself a TestCase)."""

    def stop(self, repo, **payload):
        self._stops = getattr(self, "_stops", 0) + 1
        data = {"hook_event_name": "Stop", "cwd": str(repo), "stop_hook_active": False, "session_id": "s-main",
                "prompt_id": "prompt-{}".format(self._stops), "last_assistant_message": "done", "background_tasks": [],
                "session_crons": []}
        data.update(payload)
        result = self.hook("hook-stop", data)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else None

    def guard(self, repo, tool, agent=None, agent_id=None, cwd=None, env=None, **tool_input):
        payload = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input, "cwd": str(cwd or repo),
                   "session_id": "s-main", "tool_use_id": "toolu_severe"}
        if agent is not None:
            payload["agent_type"] = agent
        if agent_id is not None:
            payload["agent_id"] = agent_id
        return self.run_drive("hook-guard", stdin=json.dumps(payload), env=env)

    def bash(self, repo, command, agent=None, agent_id=None, cwd=None, env=None):
        if agent and agent_id is None:
            agent_id = "agent-severe"
        return self.guard(repo, "Bash", agent=agent, agent_id=agent_id, cwd=cwd, env=env, command=command)

    def assertBlocked(self, result, fragment=None):
        self.assertEqual(result.returncode, 2, "expected a block; stderr: {}".format(result.stderr))
        if fragment:
            self.assertIn(fragment, result.stderr)

    def assertAllowed(self, result):
        self.assertEqual(result.returncode, 0, "expected the call to be allowed; stderr: {}".format(result.stderr))

    def promote(self, repo, produced_by="verifier", commit=None, rung="Live Proof", status="Live Proof"):
        text = (repo / ".drive/STATUS.md").read_text().replace(
            "| Local Proof | test:", "| {} | live:.drive/proofs/{}; test:".format(status, KEY))
        self.write(repo, ".drive/STATUS.md", text)
        self.write(repo, ".drive/proofs/{}/r1/verdict.json".format(KEY), verdict(KEY, rung=rung))
        self.sign(repo, ".drive/proofs/{}/r1/verdict.json".format(KEY))
        manifest = proof_manifest(KEY, commit=commit or self.code_sha)
        manifest["produced_by"] = produced_by
        self.write_live_proof(repo, KEY, manifest)
        return manifest


class ProvenanceTests(Severe, DriveTestCase):
    def test_hand_written_verdicts_and_audit_cannot_close_a_run_that_did_no_work(self):
        repo = self.make_final_run(signed=False)
        self.assertFails(self.lint(repo, "final"), "has no provenance")
        self.assertEqual(self.stop(repo)["decision"], "block")
        result = self.run_drive("end", cwd=repo)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertTrue((repo / ".drive/local/active").exists())

    def test_a_verdict_edited_after_the_verifier_wrote_it_is_refused(self):
        repo = self.make_run()
        rel = ".drive/proofs/{}/r1/verdict.json".format(KEY)
        data = json.loads((repo / rel).read_text())
        data["claims"][0]["confidence"] = 100
        self.write(repo, rel, data)
        self.assertFails(self.lint(repo), "changed after drive:verifier wrote it")

    def test_a_verdict_recorded_for_another_agent_type_is_refused(self):
        repo = self.make_run(signed=False)
        self.sign(repo, ".drive/proofs/{}/r1/verdict.json".format(KEY), agent_type="drive:grader")
        self.assertFails(self.lint(repo), "was written by drive:grader")

    def test_a_final_audit_a_grader_wrote_is_refused(self):
        repo = self.make_final_run()
        audit = verdict("final-audit", claims=[KEY, LIST], rung="Operational")
        audit["for_maker"] = "graded rather than audited"
        self.write(repo, ".drive/reviews/2026-09-14-final-audit.json", audit)
        self.sign(repo, ".drive/reviews/2026-09-14-final-audit.json", agent_type="drive:grader")
        self.commit(repo, "drive: audit")
        self.assertFails(self.lint(repo, "final"), "not by drive:auditor or drive:verifier")

    def test_a_live_proof_the_orchestrator_produced_is_refused(self):
        repo = self.make_run()
        self.promote(repo, produced_by="orchestrator")
        self.assertFails(self.lint(repo), "not produced by a checker")

    def test_the_proof_template_offers_only_checkers_as_producers(self):
        manifest = json.loads((SKILL / "templates" / "proof.json").read_text())
        self.assertNotIn("orchestrator", manifest["produced_by"])

    def test_final_runs_the_recorded_suite_and_fails_when_it_is_red(self):
        repo = self.make_final_run()
        self.write(repo, "tests/suite.py", "import sys\nsys.exit(3)\n")
        self.commit(repo, "test: the suite is red")
        self.assertFails(self.lint(repo, "final"), "exited 3 when drive.py ran it")

    def test_the_stop_hook_needs_a_recorded_passing_suite_and_never_runs_one(self):
        repo = self.make_final_run()
        decision = self.stop(repo)
        self.assertIn("no passing run of '{}' is recorded".format(TEST_COMMAND), decision["reason"])
        self.assertEqual(self.run_drive("lint", "--final", cwd=repo).returncode, 0)
        self.assertIsNone(self.stop(repo))

    def test_shapes_without_a_suite_skip_it_and_other_shapes_must_record_one(self):
        repo = self.make_final_run()
        goal = (repo / ".drive/GOAL.md").read_text()
        no_suite = goal.replace('test_command: "{}"'.format(TEST_COMMAND), 'test_command: "none"')
        self.write(repo, ".drive/GOAL.md", no_suite.replace("shape: feature", "shape: report"))
        self.assertNoFailure(self.lint(repo, "final"), "records no full-suite command")
        self.write(repo, ".drive/GOAL.md", no_suite)
        self.assertFails(self.lint(repo, "final"), "records no full-suite command")

    def test_changing_the_suite_command_needs_a_decision_naming_it(self):
        repo = self.make_final_run()
        goal = (repo / ".drive/GOAL.md").read_text().replace('test_command: "{}"'.format(TEST_COMMAND), 'test_command: "true"')
        self.write(repo, ".drive/GOAL.md", goal)
        self.assertFails(self.lint(repo, "final"), "changed from '{}' at intake to 'true'".format(TEST_COMMAND))

    def test_nobody_can_call_drives_hooks_by_hand(self):
        repo = self.make_run()
        forged = json.dumps({"hook_event_name": "SubagentStop", "cwd": str(repo), "agent_id": "forged", "agent_type": "drive:verifier"})
        for agent in (None, "drive:verifier", "drive:implementer"):
            with self.subTest(agent=agent):
                self.assertBlocked(self.bash(repo, "echo '{}' | python3 {} hook-snapshot stop".format(forged, DRIVE), agent=agent),
                                   "run only by Claude Code's hooks")
                self.assertBlocked(self.bash(repo, "python3 {} hook-stop < /dev/null".format(DRIVE), agent=agent))

    def test_the_main_thread_cannot_write_reviewer_evidence_or_the_ledger(self):
        repo = self.make_run()
        for tool, path in (("Write", ".drive/proofs/{}/r1/verdict.json".format(KEY)), ("Edit", ".drive/reviews/2026-09-14-final-audit.json"),
                           ("Write", ".drive/proofs/{}/proof.json".format(KEY)), ("Write", ".drive/reviews/2026-09-14-citations-pricing.json")):
            with self.subTest(tool=tool, path=path):
                self.assertBlocked(self.guard(repo, tool, file_path=str(repo / path), content="{}", old_string="a", new_string="b"),
                                   "evidence a reviewer produces")
        blocked = ["cat > .drive/reviews/2026-09-14-final-audit.json <<'EOF'\n{}\nEOF",
                   "cp {}/v.json .drive/proofs/{}/r1/verdict.json".format(self.scratch, KEY),
                   "python3 -c \"open('.drive/proofs/{}/r1/verdict.json','w').write('{{}}')\"".format(KEY),
                   "rm -rf .drive/proofs/{}/r2".format(KEY),
                   "mv {}/p.json .drive/proofs/{}/proof.json".format(self.scratch, KEY),
                   "jq . x.json | tee .drive/reviews/2026-09-14-citations-pricing.json",
                   "echo forged >> {}/.claude/drive/ledger/x/ledger.jsonl".format(self.home)]
        for command in blocked:
            with self.subTest(command=command):
                self.assertBlocked(self.bash(repo, command))
        for command in ("cat .drive/proofs/{}/r1/verdict.json".format(KEY), "git add -A .drive && git commit -qm state",
                        "python3 {} lint --final".format(DRIVE), "echo note >> .drive/STATE.md"):
            with self.subTest(command=command):
                self.assertAllowed(self.bash(repo, command))
        self.assertAllowed(self.guard(repo, "Edit", file_path=str(repo / ".drive/STATE.md"), old_string="a", new_string="b"))

    def test_subagents_outside_the_roster_get_the_main_threads_evidence_rules(self):
        repo = self.make_run()
        self.assertBlocked(self.guard(repo, "Write", agent="general-purpose", agent_id="gp-1",
                                      file_path=str(repo / ".drive/proofs/{}/r1/verdict.json".format(KEY)), content="{}"))


class StopGateTests(Severe, DriveTestCase):
    def test_blocked_on_nothing_does_not_end_the_turn(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha, status="blocked")
        self.assertIn("Blocked on names nothing", self.stop(repo)["reason"])

    def test_blocked_without_a_report_does_not_end_the_turn(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha, status="blocked", blocked="credentials: production credentials only the owner holds")
        self.assertIn("Stopped because", self.stop(repo)["reason"])

    def test_blocked_on_ordinary_work_does_not_end_the_turn(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha, status="blocked", blocked="the verifier has not run yet")
        self.write(repo, ".drive/REPORT.md", self.report_md({}, outcome="Stopped because the verifier has not run."))
        self.assertIn("names no stop condition", self.stop(repo)["reason"])

    def test_aborted_needs_a_report_and_a_decision(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha, status="aborted")
        self.write(repo, ".drive/REPORT.md", self.report_md({}, outcome="Stopped because the owner ended the run."))
        self.assertIn("DECISIONS.md has no entry", self.stop(repo)["reason"])
        with open(repo / ".drive/DECISIONS.md", "a", encoding="utf-8") as handle:
            handle.write("\n## 2026-09-14 · Abort the run at the owner's request\n- Decision: abort.\n- Undo: /drive --resume · reversal cost: low.\n")
        self.assertIsNone(self.stop(repo))

    def test_a_self_declared_stall_does_not_end_the_turn(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha, status="stalled")
        self.assertIn("did not set this stalled status", self.stop(repo)["reason"])

    def test_unrelated_background_work_does_not_end_the_turn(self):
        repo = self.make_run()
        for task in ({"id": "a1", "type": "subagent", "status": "running", "agent_type": "Explore", "description": "look around"},
                     {"id": "w1", "type": "workflow", "status": "running", "name": "review-panel"}):
            with self.subTest(task=task["type"]):
                self.assertEqual(self.stop(repo, background_tasks=[task])["decision"], "block")

    def test_rewriting_only_the_timestamp_does_not_reset_stall_detection(self):
        repo = self.make_run()
        # Offsets far from the committed timestamp, so every rewrite differs from HEAD only in updated:.
        for attempt in range(6):
            self.set_state(repo, commit=self.code_sha, updated=iso(1000 + attempt * 2))
            self.assertEqual(self.stop(repo).get("decision"), "block", "attempt {}".format(attempt + 1))
        self.set_state(repo, commit=self.code_sha, updated=iso(2000))
        self.assertIn("stalled", self.stop(repo)["systemMessage"])

    def test_a_stall_the_gate_set_ends_the_turn_and_end_closes_it_as_stopped(self):
        repo = self.make_run()
        for _ in range(6):
            self.stop(repo)
        self.assertIn("stalled", self.stop(repo)["systemMessage"])
        self.assertIsNone(self.stop(repo))
        self.assertEqual(self.run_drive("end", cwd=repo).returncode, 1)
        self.write(repo, ".drive/REPORT.md", self.report_md({}, outcome="Stopped because the run stalled with STATE.md unchanged."))
        self.commit(repo, "drive: stalled")
        closed = self.run_drive("end", cwd=repo)
        self.assertEqual(closed.returncode, 0, closed.stdout)
        self.assertIn("closed as stopped", closed.stdout)
        self.assertFalse((repo / ".drive/local/active").exists())

    def test_end_closes_a_properly_blocked_run_and_refuses_an_empty_one(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha, status="blocked")
        self.assertEqual(self.run_drive("end", cwd=repo).returncode, 1)
        self.set_state(repo, commit=self.code_sha, status="blocked", blocked="payment: a payment method only the owner can add")
        self.write(repo, ".drive/REPORT.md", self.report_md({}, outcome="Stopped because billing needs a payment method."))
        self.commit(repo, "drive: blocked on payment")
        result = self.run_drive("end", cwd=repo)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertFalse((repo / ".drive/local/active").exists())

    def test_the_stop_hook_never_waits_for_the_registry(self):
        repo = self.make_final_run()
        state = (repo / ".drive/STATE.md").read_text().replace(
            "model: claude-fable-5-1 · high", "model: claude-fable-5-1 · high\nregistry: python3 -c \"import time; time.sleep(90)\"")
        self.write(repo, ".drive/STATE.md", state)
        started = time.time()
        decision = self.stop(repo)
        self.assertLess(time.time() - started, 30)
        self.assertIn("registry", decision["reason"])

    def test_reinjection_stays_quiet_in_sessions_that_never_ran_drive(self):
        repo = self.make_run()
        self.write(repo, ".drive/local/active", json.dumps({"slug": "session-auth", "sessions": ["s-drive"]}) + "\n")
        payload = {"hook_event_name": "SessionStart", "source": "resume", "cwd": str(repo)}
        self.assertEqual(self.hook("hook-reinject", dict(payload, session_id="s-other")).stdout, "")
        self.assertIn("DRIVE · START", self.hook("hook-reinject", dict(payload, session_id="s-drive")).stdout)

    def test_init_records_the_drive_session_and_stop_and_start_register_nothing(self):
        repo = self.make_run()
        self.stop(repo, session_id="s-7")
        self.assertEqual(drive.read_marker(repo).get("sessions") or [], [])
        self.run_drive("start", cwd=repo, env={"CLAUDE_CODE_SESSION_ID": "s-8"})
        self.assertEqual(drive.read_marker(repo).get("sessions") or [], [])
        resumed = self.run_drive("init", "--goal", "-", cwd=repo, stdin=GOAL_TEXT, env={"CLAUDE_CODE_SESSION_ID": "s-9"})
        self.assertEqual(resumed.returncode, 0, resumed.stdout + resumed.stderr)
        self.assertEqual(drive.read_marker(repo)["sessions"], ["s-9"])

    def test_a_stale_marker_in_the_session_project_never_gates_another_repository(self):
        repo = self.make_run()
        other = self.new_repo("xs-fix")
        env = {"CLAUDE_PROJECT_DIR": str(repo)}
        result = self.run_drive("hook-stop", stdin=json.dumps({"hook_event_name": "Stop", "cwd": str(other)}), env=env)
        self.assertEqual(result.stdout.strip(), "")
        self.assertAllowed(self.bash(other, "git commit -am x", agent="drive:verifier", env=env))


class HygieneBaselineTests(Severe, DriveTestCase):
    def owner_state(self, repo):
        worktree = self.scratch / "owner-worktree"
        self.git(repo, "worktree", "add", "-q", "-b", "worktree-foo", str(worktree), "HEAD")
        self.write(repo, "notes-owner.txt", "the owner's notes\n")
        return worktree

    def test_the_owners_worktree_branch_and_notes_are_not_the_runs_debris(self):
        repo = self.make_run()
        self.owner_state(repo)
        drive.write_baseline(repo)
        self.assertNoFailure(self.lint(repo, "stop"))
        self.write(repo, "src/new.py", "x = 1\n")
        text = self.messages(self.lint(repo, "stop"))
        self.assertIn("made during the run: src/new.py", text)
        self.assertNotIn("notes-owner.txt", text)
        self.assertNotIn("worktree-foo", text)

    def test_init_records_the_owners_baseline(self):
        repo = self.new_repo()
        self.write(repo, "README.md", "x\n")
        self.commit(repo, "chore: start")
        worktree = self.owner_state(repo)
        result = self.run_drive("init", "--goal", "Add CSV export", "--size", "M", cwd=repo)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        baseline = json.loads((repo / ".drive/local/baseline.json").read_text())
        self.assertIn("notes-owner.txt", baseline["dirty"])
        self.assertIn(os.path.realpath(str(worktree)), baseline["worktrees"])
        self.assertIn("worktree-foo", baseline["branches"])
        self.assertEqual(baseline["branch"], "main")
        self.assertFalse(any(p.startswith(".drive/") for p in baseline["dirty"]))

    def test_a_harness_branch_that_appears_mid_run_fails(self):
        repo = self.make_run()
        self.git(repo, "branch", "worktree-bar")
        self.assertFails(self.lint(repo, "stop"), "does not list: worktree-bar")


class InitAndPlanTests(Severe, DriveTestCase):
    def fresh(self, name="proj"):
        repo = self.new_repo(name)
        self.write(repo, "README.md", "x\n")
        self.commit(repo, "chore: start")
        return repo

    def test_a_new_run_without_a_size_is_refused(self):
        repo = self.fresh()
        result = self.run_drive("init", "--goal", "add a usage dashboard to the admin area", cwd=repo)
        self.assertEqual(result.returncode, 2)
        self.assertIn("--size", result.stderr)
        self.assertFalse((repo / ".drive").exists())

    def test_a_goal_with_quotes_dollars_and_backticks_survives_stdin_and_a_file(self):
        goal = 'Fix "quoted" $HOME and `ticks` in the export'
        repo = self.fresh()
        result = self.run_drive("init", "--goal", "-", "--size", "S", cwd=repo, stdin=goal)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(json.dumps(goal), (repo / ".drive/GOAL.md").read_text())
        other = self.fresh("other")
        path = self.write(self.scratch, "goal.txt", goal + "\n")
        result = self.run_drive("init", "--goal-file", str(path), "--size", "S", cwd=other)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(json.dumps(goal), (other / ".drive/GOAL.md").read_text())

    def test_an_operate_plan_line_with_its_step_parses(self):
        repo = self.make_run()
        line = "- [ ] execute · rotate the api key · artifact: .drive/proofs/api-key-rotation · exit: the old key is rejected · checker: verifier"
        goal = (repo / ".drive/GOAL.md").read_text().replace("\n## Re-plans", line + "\n\n## Re-plans")
        self.write(repo, ".drive/GOAL.md", goal)
        self.assertNoFailure(self.lint(repo), "plan line")
        self.assertEqual(drive.PLAN_RE.match(line).group("step"), "rotate the api key")

    def test_size_is_the_largest_across_sub_goals(self):
        text = goal_md("abc1234", size="S") + "\n## Classification · second\n```yaml\nshape: build\nsize: L\n```\n"
        self.assertEqual(drive.Goal(text).size, "L")

    def test_spawns_past_twice_the_budget_fail_the_gate(self):
        repo = self.make_run()
        payload = {"hook_event_name": "SubagentStart", "cwd": str(repo), "agent_id": "i-hook", "agent_type": "drive:implementer"}
        self.assertEqual(self.hook("hook-snapshot", payload, "start").returncode, 0)
        for number in range(16):
            drive.ledger_append(repo, {"kind": "spawn", "agent_type": "drive:implementer", "agent_id": "i-{}".format(number)})
        self.assertFails(self.lint(repo, gate="build"), "past twice its envelope")

    def test_the_state_template_lists_stopped(self):
        self.assertIn("stopped", (SKILL / "templates" / "STATE.md").read_text().split("## Resume here")[0])


class ReviewerGuardTests(Severe, DriveTestCase):
    def test_interpreters_variables_archives_and_editors_cannot_write_for_a_reviewer(self):
        repo = self.make_run()
        self.write(repo, "Makefile", "test:\n\tpython3 tests/suite.py\n\ninstall:\n\tcp src/auth.py /usr/local/lib/auth.py\n")
        self.write(self.scratch, "forge.py", "open('src/auth.py', 'w').write('x')\n")
        cases = [
            ("drive:verifier", "python3 -c \"open('src/auth.py','w').write('pwned')\""),
            ("drive:verifier", "node -e \"require('fs').writeFileSync('src/auth.py','x')\""),
            ("drive:verifier", "perl -pi -e 's/1/2/' src/auth.py"),
            ("drive:verifier", "ruby -i -pe 'gsub(/a/, \"b\")' src/auth.py"),
            ("drive:auditor", "g=git; $g commit -am x"),
            ("drive:verifier", "C='git commit -am x'; bash -c \"$C\""),
            ("drive:verifier", "tar -xf x.tar -C src"),
            ("drive:verifier", "make install"),
            ("drive:verifier", "awk 'BEGIN { print \"x\" > \"src/auth.py\" }'"),
            ("drive:verifier", "sed -n 'w src/auth.py' README.md"),
            ("drive:verifier", "sqlite3 app.db 'drop table sessions'"),
            ("drive:severe-tester", "python3 -c \"open('src/auth.py','w').write('x')\""),
            ("drive:grader", "python3 {}/forge.py".format(self.scratch)),
        ]
        for agent, command in cases:
            with self.subTest(agent=agent, command=command):
                self.assertBlocked(self.bash(repo, command, agent=agent))
        allowed = [
            "python3 -c \"import json,sys; print(json.load(open('.drive/proofs/{}/r1/verdict.json'))['verdict'])\"".format(KEY),
            "jq -r .verdict .drive/proofs/{}/r1/verdict.json".format(KEY),
            "sed -n '1,5p' README.md", "awk '$1 > 0 {print $1}' README.md", TEST_COMMAND, "python3 -m pytest -q", "make test",
        ]
        for command in allowed:
            with self.subTest(command=command):
                self.assertAllowed(self.bash(repo, command, agent="drive:verifier"))
        self.assertAllowed(self.bash(repo, "xcrun simctl io booted screenshot .drive/local/ui/home.png", agent="drive:ui-reviewer"))

    def test_guard_messages_name_this_machines_scratch_directory(self):
        repo = self.make_run()
        result = self.bash(repo, "rm -rf src", agent="drive:verifier")
        self.assertBlocked(result)
        self.assertIn(str(self.scratch), result.stderr)
        self.assertNotIn("/private/tmp", result.stderr)

    def test_a_project_under_a_scratch_root_keeps_its_guard(self):
        repo = self.make_run()
        env = {"DRIVE_TMP_ROOTS": str(self.tmp)}
        self.assertBlocked(self.bash(repo, "echo x > src/auth.py", agent="drive:verifier", env=env))
        self.assertBlocked(self.bash(repo, "git commit -am x", agent="drive:verifier", env=env))
        self.assertBlocked(self.guard(repo, "Write", agent="drive:architect", agent_id="a-1", env=env,
                                      file_path=str(repo / "src/auth.py"), content="x"))


class MakerGuardTests(Severe, DriveTestCase):
    def test_makers_cannot_reach_git_state_home_or_deploys_by_indirection(self):
        repo = self.make_run()
        self.write(repo, "package.json", json.dumps({"scripts": {"deploy": "wrangler deploy", "build": "tsc -p ."}}))
        self.write(repo, "Makefile", "release:\n\tgit push origin main\n\nship-it:\n\tgit push origin main\n")
        self.write(repo, "scripts/commit.py", "import subprocess\nsubprocess.run(['git', 'commit', '-am', 'x'])\n")
        self.git(repo, "config", "alias.ci", "commit")
        blocked = ["rm -rf ~/Projects", "rm -rf ~/Projects/other", "rm -rf .git", "echo x >> ~/.zshrc",
                   "echo '| k | c | n | Done | x | {} |' >> .drive/STATUS.md".format(TODAY), "cp /dev/null .drive/GOAL.md",
                   "git -c alias.ci=commit ci -am x", "git ci -am x", "npm run deploy", "make release", "make ship-it",
                   "python3 scripts/commit.py", "git symbolic-ref HEAD refs/heads/other", "git branch newb"]
        for agent in ("drive:implementer", "drive:writer"):
            for command in blocked:
                with self.subTest(agent=agent, command=command):
                    self.assertBlocked(self.bash(repo, command, agent=agent))
            self.assertAllowed(self.bash(repo, "npm run build", agent=agent))

    def test_maker_shell_writes_stay_inside_the_packages_owned_paths(self):
        repo = self.make_run()
        brief = (Path(drive.TEMPLATES) / "package-brief.md").read_text().replace("<package id>", "export-api").replace(
            "- `<path or glob>`", "- `src/export/**`", 1)
        self.write(repo, ".drive/packages/export-api/brief.md", brief)
        self.assertBlocked(self.bash(repo, "echo x > src/other.py", agent="drive:implementer"))
        self.assertAllowed(self.bash(repo, "echo x > src/export/api.py", agent="drive:implementer"))

    def test_frozen_tests_cannot_be_edited_by_makers_the_main_thread_or_outside_agents(self):
        repo = self.make_run()
        self.assertEqual(self.run_drive("freeze", "add", "tests/test_auth.py", cwd=repo).returncode, 0)
        target = str(repo / "tests/test_auth.py")
        for agent, agent_id in (("drive:implementer", "i-1"), (None, None), ("general-purpose", "gp-1")):
            with self.subTest(agent=agent):
                self.assertBlocked(self.guard(repo, "Edit", agent=agent, agent_id=agent_id, file_path=target, old_string="a",
                                              new_string="b"), "frozen test")
        self.assertBlocked(self.bash(repo, "sed -i 's/rejected/accepted/' tests/test_auth.py", agent="drive:implementer"))
        # A severe tester changes a frozen test only while an amendment is open (test_freeze covers the open case).
        self.assertBlocked(self.guard(repo, "Edit", agent="drive:severe-tester", agent_id="s-1", file_path=target, old_string="a",
                                      new_string="b"))

    def test_the_main_thread_never_creates_switches_or_pushes_branches(self):
        repo = self.make_run()
        for command in ("git checkout -b feature", "git switch -c feature", "git worktree add ../wt HEAD",
                        "git worktree add --detach ../wt HEAD", "git push origin main", "git reset --hard HEAD~1",
                        "git branch newb", "git symbolic-ref HEAD refs/heads/x", "git checkout -b feature && git worktree add ../wt"):
            with self.subTest(command=command):
                self.assertBlocked(self.bash(repo, command))
        for command in ("git commit -am x", "git worktree add --detach {}/drive-proj-arm HEAD".format(self.scratch),
                        "git branch -d drive/old", "git checkout -- src/auth.py", "git -C {}/drive-proj-arm rebase main".format(self.scratch),
                        "git status --porcelain"):
            with self.subTest(command=command):
                self.assertAllowed(self.bash(repo, command))

    def test_maker_edits_inside_a_background_worktree_are_judged_against_that_worktree(self):
        repo = self.make_run()
        worktree = repo / ".claude" / "worktrees" / "bg-1"
        self.git(repo, "worktree", "add", "-q", "--detach", str(worktree), "HEAD")
        self.assertAllowed(self.guard(repo, "Edit", agent="drive:implementer", agent_id="i-1", cwd=worktree,
                                      file_path=str(worktree / "src/auth.py"), old_string="a", new_string="b"))
        self.assertBlocked(self.guard(repo, "Edit", agent="drive:implementer", agent_id="i-1", cwd=worktree,
                                      file_path=str(worktree / ".drive/STATUS.md"), old_string="a", new_string="b"))
        self.assertIn("bgIsolation", self.messages(self.lint(repo, "stop")))

    def test_makers_may_write_repositories_goal_md_lists(self):
        repo = self.make_run()
        other = self.new_repo("platform")
        goal = (repo / ".drive/GOAL.md").read_text().replace("  repo: /repo", "  repo: /repo\n  repos: [{}]".format(other))
        self.write(repo, ".drive/GOAL.md", goal)
        self.assertAllowed(self.guard(repo, "Write", agent="drive:implementer", agent_id="i-1",
                                      file_path=str(other / "src/gateway.py"), content="x"))
        self.assertBlocked(self.guard(repo, "Write", agent="drive:architect", agent_id="a-1",
                                      file_path=str(other / "src/gateway.py"), content="x"), "outside the project")


class LintAuditTests(Severe, DriveTestCase):
    def test_a_row_deleted_in_a_later_commit_is_caught_at_final(self):
        repo = self.make_final_run()
        lines = [l for l in (repo / ".drive/STATUS.md").read_text().splitlines() if not l.startswith("| " + ADMIN)]
        self.write(repo, ".drive/STATUS.md", "\n".join(lines) + "\n")
        self.write(repo, ".drive/REPORT.md", self.report_md({"Done": 2}))
        self.commit(repo, "drive: tidy status")
        self.assertFails(self.lint(repo, "final"), "STATUS {}: was committed in".format(ADMIN))

    def test_a_row_above_the_rung_its_verdict_supports_fails(self):
        repo = self.make_run()
        self.promote(repo, rung="Local Proof")
        self.assertFails(self.lint(repo), "but its verdict supports only Local Proof")

    def test_a_decision_excuses_only_the_narrowing_it_names(self):
        repo = self.make_run()
        text = (repo / ".drive/STATUS.md").read_text().replace("| An admin can revoke any session | y |",
                                                               "| An admin can revoke any session | n |")
        self.write(repo, ".drive/STATUS.md", text)
        with open(repo / ".drive/DECISIONS.md", "a", encoding="utf-8") as handle:
            handle.write("\n## 2026-09-14 · Use a faster hash\n- Decision: switch hashes.\n- Undo: revert · reversal cost: low.\n- Narrows: none\n")
        self.assertFails(self.lint(repo), "no new DECISIONS.md entry names the key {}".format(ADMIN))

    def test_a_removed_phase_needs_a_decision_that_names_it(self):
        repo = self.make_run()
        text = "\n".join(l for l in (repo / ".drive/GOAL.md").read_text().splitlines() if not l.startswith("- [ ] verify")) + "\n"
        self.write(repo, ".drive/GOAL.md", text)
        with open(repo / ".drive/DECISIONS.md", "a", encoding="utf-8") as handle:
            handle.write("\n## 2026-09-14 · Use a faster hash\n- Decision: switch hashes.\n- Undo: revert · reversal cost: low.\n- Narrows: none\n")
        self.assertFails(self.lint(repo), "the verify phase")

    def test_a_narrowing_committed_since_intake_needs_a_decision_naming_it(self):
        repo = self.new_repo()
        self.write(repo, "README.md", "# proj\n")
        self.write(repo, ".gitignore", ".drive/local/\n")
        base = self.commit(repo, "chore: start")
        self.write(repo, ".drive/GOAL.md", goal_md(base))
        self.write(repo, ".drive/STATUS.md", self.status_md([(ADMIN, "An admin can revoke any session", "y", "Missing", "")]))
        self.commit(repo, "drive(intake): session-auth")
        self.write(repo, ".drive/STATUS.md", self.status_md([(ADMIN, "An admin can revoke any session", "n", "Missing", "")]))
        self.write(repo, ".drive/DECISIONS.md", "# DECISIONS · proj\n\n## 2026-09-14 · Use a faster hash\n- Decision: switch.\n"
                                                "- Undo: revert · reversal cost: low.\n- Narrows: none\n")
        self.commit(repo, "drive: narrow quietly")
        self.assertFails(self.lint(repo, "final"), "since the intake commit")

    def test_a_verdict_supporting_less_than_local_proof_fails(self):
        repo = self.make_run()
        self.write(repo, ".drive/proofs/{}/r1/verdict.json".format(KEY), verdict(KEY, rung="Partial"))
        self.sign(repo, ".drive/proofs/{}/r1/verdict.json".format(KEY))
        self.assertFails(self.lint(repo), "supports only Partial, below Local Proof")

    def test_a_claim_below_confidence_75_fails(self):
        repo = self.make_run()
        data = verdict(KEY)
        data["claims"][0]["confidence"] = 50
        self.write(repo, ".drive/proofs/{}/r1/verdict.json".format(KEY), data)
        self.sign(repo, ".drive/proofs/{}/r1/verdict.json".format(KEY))
        self.assertFails(self.lint(repo), "has confidence below 75")

    def test_goal_committed_after_other_run_files_fails(self):
        repo = self.new_repo()
        self.write(repo, "README.md", "# proj\n")
        base = self.commit(repo, "chore: start")
        self.write(repo, ".drive/STATUS.md", self.status_md([(ADMIN, "An admin can revoke any session", "y", "Missing", "")]))
        self.commit(repo, "drive: status before the goal")
        self.write(repo, ".drive/GOAL.md", goal_md(base))
        self.commit(repo, "drive(intake): session-auth")
        self.assertFails(self.lint(repo), "was committed after other run files")

    def test_an_operational_row_without_ops_fails(self):
        repo = self.make_run()
        self.promote(repo, rung="Operational", status="Operational")
        self.assertFails(self.lint(repo), "Operational needs ops:")

    def test_a_live_proof_naming_a_commit_that_does_not_exist_fails(self):
        repo = self.make_run()
        self.promote(repo, commit="deadbee")
        self.assertFails(self.lint(repo), "names commit deadbee which does not exist")

    def test_a_long_placeholder_left_by_init_is_caught(self):
        repo = self.new_repo()
        self.write(repo, "README.md", "x\n")
        self.commit(repo, "chore: start")
        self.assertEqual(self.run_drive("init", "--goal", "Add CSV export", "--size", "S", cwd=repo).returncode, 0)
        self.assertFails(self.lint(repo), "the 'live means:' line still holds a template placeholder")

    def test_a_live_proof_whose_artifact_is_altered_or_missing_fails(self):
        repo = self.make_run()
        self.promote(repo)
        self.write(repo, ".drive/proofs/{}/r1/live.md".format(KEY), "200 OK from a different run\n")
        self.assertFails(self.lint(repo), "does not match the file")
        (repo / ".drive/proofs/{}/r1/live.md".format(KEY)).unlink()
        self.assertFails(self.lint(repo), "which does not exist beside it")

    def test_a_shot_token_must_name_a_screenshot(self):
        repo = self.make_run()
        self.write(repo, ".drive/proofs/{}/r1/notes.txt".format(KEY), "looked fine\n")
        text = (repo / ".drive/STATUS.md").read_text().replace("| An expired token", "| [ui] An expired token").replace(
            "verdict:.drive/proofs/{}/r1/verdict.json".format(KEY),
            "shot:.drive/proofs/{k}/r1/notes.txt; verdict:.drive/proofs/{k}/r1/verdict.json".format(k=KEY))
        self.write(repo, ".drive/STATUS.md", text)
        self.assertFails(self.lint(repo), "is not a screenshot")

    def test_final_lint_runs_the_floor_guard_against_the_baseline(self):
        repo = self.make_final_run()
        self.write(repo, "src/auth.py", "def check(token, now):  # noqa\n    return token.expires_at > now\n")
        self.commit(repo, "chore: silence the linter")
        self.assertFails(self.lint(repo, "final"), "suppression · src/auth.py:1")

    def test_main_worktree_root_survives_a_git_without_path_format(self):
        repo = self.make_run()
        real = drive.git_out

        def old_git(root, *args):
            if "--path-format=absolute" in args:
                return "--path-format=absolute\n.git"
            return real(root, *args)
        with mock.patch.object(drive, "git_out", old_git):
            self.assertEqual(drive.main_worktree_root(repo), repo.resolve())


class FloorGuardAuditTests(Severe, DriveTestCase):
    def guard_repo(self):
        repo = self.new_repo()
        self.write(repo, "src/app.py", "def add(a, b):\n    return a + b\n")
        self.write(repo, "tests/test_app.py", "def test_add():\n    assert add(1, 2) == 3\n    assert add(0, 0) == 0\n")
        self.write(repo, "pyproject.toml", "[tool.coverage.report]\nfail_under = 90\n")
        base = self.commit(repo, "chore: baseline")
        self.write(repo, ".drive/GOAL.md", goal_md(base))
        self.commit(repo, "drive(intake): session-auth")
        return repo

    def floor(self, repo, *args):
        return self.run_drive("guard", *args, cwd=repo)

    def test_the_default_base_is_the_recorded_baseline(self):
        repo = self.guard_repo()
        self.write(repo, "src/app.py", "def add(a, b):  # noqa\n    return a + b\n")
        self.commit(repo, "feat: quiet the linter")
        self.assertEqual(self.floor(repo, "--base", "HEAD").returncode, 0)
        result = self.floor(repo)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("suppression · src/app.py:1", result.stdout)

    def test_test_weakenings_the_old_guard_missed_are_caught(self):
        repo = self.guard_repo()
        cases = [
            ("tests/test_app.py", "from unittest import skip\n\n@skip('later')\ndef test_add():\n    assert add(1, 2) == 3\n    assert add(0, 0) == 0\n", "skip"),
            ("tests/test_app.py", "def test_add():\n    self.assertTrue(True)\n    assert add(0, 0) == 0\n", "trivial-assertion"),
            ("tests/test_app.py", "def test_add():\n    return\n    assert add(1, 2) == 3\n    assert add(0, 0) == 0\n", "early-return"),
            ("conftest.py", "collect_ignore = ['tests/test_app.py']\n", "test-collection"),
            ("pyproject.toml", "[tool.coverage.report]\nfail_under = 0\n", "coverage-floor"),
            ("pyproject.toml", "[tool.coverage.report]\nfail_under = 90\n[tool.pytest.ini_options]\naddopts = \"-k 'not add'\"\n", "test-collection"),
        ]
        for rel, content, rule in cases:
            with self.subTest(rule=rule, rel=rel):
                original = (repo / rel).read_text() if (repo / rel).exists() else None
                self.write(repo, rel, content)
                self.assertIn(rule + " · ", self.floor(repo).stdout)
                if original is None:
                    (repo / rel).unlink()
                else:
                    self.write(repo, rel, original)

    def test_moving_a_test_out_of_discovery_is_caught(self):
        repo = self.guard_repo()
        (repo / "helpers").mkdir()
        self.git(repo, "mv", "tests/test_app.py", "helpers/app_checks.py")
        self.assertIn("test-moved · helpers/app_checks.py", self.floor(repo).stdout)

    def test_documentation_and_unrelated_skip_calls_are_not_violations(self):
        repo = self.guard_repo()
        self.write(repo, "CONTRIBUTING.md", "Never add eslint-disable or raise NotImplementedError; catch {} blocks are banned.\n")
        self.write(repo, "tests/test_reader.py", "def test_reader():\n    r = Reader(b'abc')\n    r.skip(1)\n    assert r.read() == b'bc'\n")
        result = self.floor(repo)
        self.assertEqual(result.returncode, 0, result.stdout)


class PreflightAndVisibilityTests(Severe, DriveTestCase):
    def test_preflight_fails_inside_a_background_worktree(self):
        repo = self.make_run()
        worktree = repo / ".claude" / "worktrees" / "bg-1"
        self.git(repo, "worktree", "add", "-q", "--detach", str(worktree), "HEAD")
        inside = self.run_drive("preflight", "--permission-mode", "auto", cwd=worktree)
        self.assertEqual(inside.returncode, 1, inside.stdout)
        self.assertIn("background-session worktree", inside.stdout)
        from_root = self.run_drive("preflight", "--permission-mode", "auto", cwd=repo)
        self.assertEqual(from_root.returncode, 1, from_root.stdout)
        self.assertIn("gained", from_root.stdout)

    def test_preflight_fails_in_manual_mode_whether_given_or_recorded(self):
        repo = self.make_run()
        self.assertEqual(self.run_drive("preflight", "--permission-mode", "default", cwd=repo).returncode, 1)
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git status"}, "cwd": str(repo),
                   "session_id": "s-9", "permission_mode": "default", "tool_use_id": "t-9"}
        self.assertEqual(self.hook("hook-guard", payload).returncode, 0)
        recorded = self.run_drive("preflight", cwd=repo, env={"CLAUDE_CODE_SESSION_ID": "s-9"})
        self.assertEqual(recorded.returncode, 1, recorded.stdout)
        self.assertIn("default (from the mode drive's hooks saw", recorded.stdout)
        ok = self.run_drive("preflight", "--permission-mode", "auto", cwd=repo)
        self.assertEqual(ok.returncode, 0, ok.stdout)
        for check in ("worktree isolation", "permission mode", "worktree.bgIsolation", "skill repository"):
            self.assertIn(check, ok.stdout)

    def test_an_unanswerable_visibility_counts_as_public(self):
        repo = self.new_repo()
        self.assertEqual(drive.repo_visibility(repo)[0], "PRIVATE")
        self.git(repo, "remote", "add", "origin", "https://github.com/owner/project.git")
        no_gh = lambda: (127, "", "gh is not installed")  # noqa: E731
        self.assertEqual(drive.repo_visibility(repo, gh=no_gh, http=lambda url: None)[0], "PUBLIC")
        self.assertEqual(drive.repo_visibility(repo, gh=no_gh, http=lambda url: 200)[0], "PUBLIC")
        self.assertEqual(drive.repo_visibility(repo, gh=no_gh, http=lambda url: 404)[0], "PRIVATE")
        self.assertEqual(drive.repo_visibility(repo, gh=lambda: (0, "PRIVATE\n", ""), http=lambda url: 200)[0], "PRIVATE")
        self.git(repo, "remote", "set-url", "origin", "git@gitlab.example.com:team/app.git")
        self.assertEqual(drive.repo_visibility(repo, gh=no_gh, ls_remote=lambda url: (128, "fatal: Authentication failed"))[0], "PRIVATE")
        self.assertEqual(drive.repo_visibility(repo, gh=no_gh, ls_remote=lambda url: (128, "Could not resolve host"))[0], "PUBLIC")
        self.assertEqual(drive.repo_visibility(repo, gh=no_gh, ls_remote=lambda url: (0, ""))[0], "PUBLIC")


class PreflightStopTests(Severe, DriveTestCase):
    def test_retired_legacy_twins_are_not_drive_roles(self):
        import re
        repo = self.make_run()
        for agent in ("drive:security-reviewer-legacy", "drive:investigator-legacy"):
            with self.subTest(agent=agent):
                self.assertIsNone(drive.role_of(agent))
                self.assertNotIn(agent.split(":", 1)[1], drive.CHECKERS)
        hooks = json.loads((SKILL / "hooks" / "hooks.json").read_text())["hooks"]
        self.assertFalse(re.search(hooks["SubagentStop"][0]["matcher"], "drive:security-reviewer-legacy"))
        self.assertAllowed(self.bash(repo, "git status --porcelain", agent="drive:investigator"))

    def test_a_failed_launch_preflight_stops_the_run_once_it_quotes_the_relaunch(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha, status="blocked", blocked="launch preflight failed: the session is in Manual mode")
        self.assertIn("relaunch command", self.stop(repo)["reason"])
        relaunch = ("launch preflight failed: Manual mode; the owner relaunches with `cd {} && claude --bg --name drive-session-auth "
                    "--permission-mode auto --settings \"$DRIVE_SETTINGS\" '/drive --resume'`".format(repo))
        self.set_state(repo, commit=self.code_sha, status="blocked", blocked=relaunch)
        self.assertIn("no failed drive.py preflight", self.stop(repo)["reason"])
        drive.ledger_append(repo, {"kind": "preflight", "ok": False, "failed": ["permission mode"], "session_id": "s-main"})
        self.assertIsNone(self.stop(repo))
        self.commit(repo, "drive: blocked on the launch preflight")
        self.assertEqual(self.run_drive("end", cwd=repo).returncode, 0)


class FloorGuardShapeTests(Severe, DriveTestCase):
    def repo_with(self, files):
        self.repos = getattr(self, "repos", 0) + 1
        repo = self.new_repo("shape-{}".format(self.repos))
        for rel, content in files.items():
            self.write(repo, rel, content)
        base = self.commit(repo, "chore: baseline")
        self.write(repo, ".drive/GOAL.md", goal_md(base))
        self.commit(repo, "drive(intake): session-auth")
        return repo

    def test_the_section_8_evasion_shapes_are_caught(self):
        cases = [
            ("tests/app.test.ts", "it('adds', () => {\n  expect(add(1, 2)).toEqual(3);\n});\n",
             "it('adds', () => {\n  expect(add(1, 2)).toBeDefined();\n});\n", "weakened-assertion"),
            ("tests/test_calc.py", "def test_ratio():\n    assertAlmostEqual(ratio(), 0.5, places=4)\n",
             "def test_ratio():\n    assertAlmostEqual(ratio(), 0.5, places=1)\n", "loosened-precision"),
            ("tests/test_calc.py", "def test_ratio():\n    assert math.isclose(ratio(), 0.5, abs_tol=0.001)\n",
             "def test_ratio():\n    assert math.isclose(ratio(), 0.5, abs_tol=0.1)\n", "loosened-tolerance"),
            ("tests/test_calc.py", "def test_ratio():\n    assert ratio() == 0.5\n",
             "def test_ratio():\n    try:\n        assert ratio() == 0.5\n    except AssertionError:\n        print('ignored')\n", "wrapped-assertion"),
            ("playwright.config.ts", "export default { retries: 1 }\n", "export default { retries: 5 }\n", "retry-added"),
            ("src/pay.ts", "export const charge = (n) => gateway.charge(n);\n",
             "export const charge = (n) => process.env.NODE_ENV === 'test' ? 'ok' : gateway.charge(n);\n", "test-only-branch"),
            ("jest.config.js", "module.exports = { testMatch: ['**/*.test.ts', '**/*.spec.ts'] };\n",
             "module.exports = { testMatch: ['**/*.test.ts'] };\n", "suite-narrowed"),
            ("vitest.config.ts", "export default { test: { include: ['src/**/*.test.ts'] } };\n",
             "export default { test: { include: ['src/**/*.test.ts'], passWithNoTests: true } };\n", "test-collection"),
        ]
        for rel, before, after, rule in cases:
            with self.subTest(rule=rule):
                repo = self.repo_with({rel: before})
                self.write(repo, rel, after)
                self.assertIn(rule + " · ", self.run_drive("guard", cwd=repo).stdout)

    def test_a_tightened_test_and_an_unrelated_config_exclude_are_not_violations(self):
        repo = self.repo_with({"tests/app.test.ts": "it('adds', () => {\n  expect(add(1, 2)).toBeDefined();\n});\n",
                               "pyproject.toml": "[tool.ruff]\nline-length = 100\n"})
        self.write(repo, "tests/app.test.ts", "it('adds', () => {\n  expect(add(1, 2)).toEqual(3);\n});\n")
        self.write(repo, "pyproject.toml", "[tool.ruff]\nline-length = 100\nexclude = ['vendor']\n")
        result = self.run_drive("guard", cwd=repo)
        self.assertEqual(result.returncode, 0, result.stdout)


class ImageCropTests(Severe, DriveTestCase):
    def test_a_ui_reviewer_may_crop_screenshots_into_its_own_output_paths_only(self):
        repo = self.make_run()
        shot = ".drive/proofs/{}/r1/shots/home.png".format(KEY)
        crop = ("python3 -c \"from PIL import Image; Image.open('{s}').crop((0, 0, 10, 10))"
                ".save('.drive/proofs/{k}/r1/shots/home.crop-1.png')\"").format(s=shot, k=KEY)
        local = "python3 -c \"from PIL import Image; Image.open('{}').save('.drive/local/ui/home-small.png')\"".format(shot)
        leak = "python3 -c \"from PIL import Image; Image.open('{}').save('src/leak.png')\"".format(shot)
        dynamic = "python3 -c \"import sys; from PIL import Image; Image.open('{}').save(sys.argv[1])\" src/leak.png".format(shot)
        text = "python3 -c \"open('src/notes.txt', 'w').write('x')\""
        self.assertAllowed(self.bash(repo, crop, agent="drive:ui-reviewer"))
        self.assertAllowed(self.bash(repo, local, agent="drive:ui-reviewer"))
        for command in (leak, dynamic, text):
            with self.subTest(command=command):
                self.assertBlocked(self.bash(repo, command, agent="drive:ui-reviewer"))
        self.assertBlocked(self.bash(repo, crop, agent="drive:verifier"))


class PixelDiffTests(Severe, DriveTestCase):
    DIFF = ("import json\nfrom PIL import Image, ImageChops\nimport numpy as np\n"
            "a = Image.open('{shots}/home.png').convert('RGB')\nb = Image.open('{shots}/home-before.png').convert('RGB')\n"
            "arr = np.asarray(ImageChops.difference(a, b))\nchanged = int((arr.max(axis=2) > 16).sum())\n"
            "Image.fromarray(((arr.max(axis=2) > 16) * 255).astype('uint8')).save('{out}/diff-home.png')\n"
            "with open('{out}/regression.json', 'w') as fh:\n    json.dump({{'changed': changed}}, fh)\n")

    def test_a_ui_reviewer_pixel_diff_with_numpy_writes_only_its_own_output_paths(self):
        repo = self.make_run()
        agent = "drive:ui-reviewer"
        shots = ".drive/proofs/{}/r1/shots".format(KEY)
        into_proofs = self.DIFF.format(shots=shots, out=".drive/proofs/{}/r1/objective".format(KEY))
        into_local = self.DIFF.format(shots=shots, out=".drive/local/ui")
        into_product = self.DIFF.format(shots=shots, out="src")
        self.write(repo, ".drive/local/ui/pixel_diff.py", into_proofs)
        self.write(repo, ".drive/local/ui/pixel_diff_leak.py", into_product)
        for command in ("python3 -c {}".format(shlex.quote(into_proofs)), "python3 -c {}".format(shlex.quote(into_local)),
                        "python3 .drive/local/ui/pixel_diff.py",
                        "python3 -c \"import numpy; import PIL.Image; print(numpy.asarray(PIL.Image.open('{}/home.png')).shape)\"".format(shots),
                        "python3 -c \"from PIL import Image as I; print(I.open('{}/home.png').size)\"".format(shots)):
            with self.subTest(allowed=command[:70]):
                self.assertAllowed(self.bash(repo, command, agent=agent))
        refused = [
            "python3 -c {}".format(shlex.quote(into_product)),
            "python3 .drive/local/ui/pixel_diff_leak.py",
            "python3 -c \"import numpy as np; np.save('src/diff.npy', np.zeros(3))\"",
            "python3 -c \"import numpy as np; np.zeros(3).tofile('src/raw.bin')\"",
            "python3 -c \"import numpy as np; np.savetxt(fname='src/diff.txt', X=np.zeros(3))\"",
            "python3 -c \"import numpy as np; np.zeros(3).dump('src/diff.pkl')\"",
            "python3 -c \"import numpy as np; np.memmap('.drive/proofs/raw.bin', mode='w+', shape=(3,))\"",
            "python3 -c \"import numpy as np; np.load('.drive/proofs/diff.npy', allow_pickle=True)\"",
            "python3 -c \"import numpy as np; np.genfromtxt('https://example.test/diff.csv')\"",
            "python3 -c \"from PIL import Image; Image.open('{}/home.png').show()\"".format(shots),
            "python3 -c \"import sys; import numpy as np; np.save(sys.argv[1], np.zeros(3))\" src/diff.npy",
            "python3 -c \"o = open; o('src/leak.txt', 'w').write('x')\"",
            "python3 -c \"open(*['src/leak.txt', 'w']).write('x')\"",
            "python3 -c \"import os as Image; Image.open('src/leak.txt', 513)\"",
            "python3 -c \"import numpy as json; json.zeros(3).dump('src/diff.pkl')\"",
            "python3 -c \"import os; os.execv('/bin/rm', ['rm', '-rf', 'src'])\"",
        ]
        for command in refused:
            with self.subTest(refused=command[:70]):
                self.assertBlocked(self.bash(repo, command, agent=agent))
        # numpy and PIL stay the UI reviewer's alone; the verifier's inline Python imports neither.
        self.assertBlocked(self.bash(repo, "python3 -c {}".format(shlex.quote(into_proofs)), agent="drive:verifier"), "imports")
        self.assertBlocked(self.bash(repo, "python3 -c \"import os; os.execv('/bin/rm', ['rm', '-rf', 'src'])\"", agent="drive:verifier"))


class RunCreatedBranchAndWorktreeTests(Severe, DriveTestCase):
    def owner_and_run_state(self):
        repo = self.make_run()
        self.owner_wt = self.tmp / "owner-wt"
        self.owner_scratch_wt = self.scratch / "owner-scratch-wt"
        self.git(repo, "branch", "owner-feature")
        self.git(repo, "worktree", "add", "-q", "--detach", str(self.owner_wt), "HEAD")
        self.git(repo, "worktree", "add", "-q", "--detach", str(self.owner_scratch_wt), "HEAD")
        drive.write_baseline(repo)
        self.run_wt = self.scratch / "drive-proj-arm"
        self.git(repo, "worktree", "add", "-q", "--detach", str(self.run_wt), "HEAD")
        self.git(repo, "branch", "worktree-agent-1")
        self.git(repo, "branch", "drive/arm")
        return repo

    def test_the_commands_the_stop_lint_names_are_the_ones_the_guard_allows(self):
        repo = self.owner_and_run_state()
        findings = self.lint(repo, "stop")
        hints = self.messages(findings) + "\n" + self.messages(findings, "warn")
        for command in ("git worktree remove {}".format(self.run_wt), "git branch -d drive/arm", "git branch -d worktree-agent-1"):
            with self.subTest(command=command):
                self.assertIn(command, hints)
                self.assertAllowed(self.bash(repo, command))
        self.assertAllowed(self.bash(repo, "git branch --delete drive/arm worktree-agent-1"))
        self.assertAllowed(self.bash(repo, "git worktree remove --force {}".format(self.run_wt)))
        self.assertNotIn("owner-feature", hints)
        self.assertNotIn(str(self.owner_wt), hints)

    def test_the_owner_s_branches_and_worktrees_and_force_deletes_stay_refused(self):
        repo = self.owner_and_run_state()
        for command in ("git branch -D worktree-agent-1", "git branch -d -f worktree-agent-1", "git branch --delete --force drive/arm",
                        "git branch -df drive/arm", "git branch -Dq drive/arm", "git branch -d owner-feature",
                        "git branch -d drive/arm owner-feature", "git branch -d main", "git branch -d -r origin/main",
                        "git branch -d \"$BRANCH\"", "git worktree remove {}".format(self.owner_wt),
                        "git worktree remove --force {}".format(self.owner_wt), "git worktree remove ../owner-wt",
                        "git worktree remove owner-scratch-wt", "git worktree remove {} {}".format(self.run_wt, self.owner_scratch_wt),
                        "git worktree remove {}".format(repo)):
            with self.subTest(command=command):
                self.assertBlocked(self.bash(repo, command))

    def test_without_a_baseline_only_drive_branches_and_scratch_worktrees_are_removed(self):
        repo = self.owner_and_run_state()
        drive.baseline_path(repo).unlink()
        self.assertAllowed(self.bash(repo, "git branch -d drive/arm"))
        self.assertAllowed(self.bash(repo, "git worktree remove {}".format(self.run_wt)))
        self.assertBlocked(self.bash(repo, "git branch -d worktree-agent-1"), "No baseline")
        self.assertBlocked(self.bash(repo, "git worktree remove {}".format(self.owner_wt)), "No baseline")


class AgentWorktreeTests(Severe, DriveTestCase):
    def test_no_agent_adds_a_worktree_that_creates_a_branch_or_leaves_the_scratch_root(self):
        repo = self.make_run()
        wt = self.scratch / "drive-proj-hyp"
        linked = self.scratch / "drive-proj-bisect"
        self.git(repo, "worktree", "add", "-q", "--detach", str(linked), "HEAD")
        refused = ["git worktree add {} HEAD".format(wt), "git worktree add {}".format(wt),
                   "git worktree add --detach -b hyp {} HEAD".format(wt), "git worktree add -B hyp --detach {} HEAD".format(wt),
                   "git worktree add --detach -fb hyp {} HEAD".format(wt), "git worktree add --detach --orphan {}".format(wt),
                   "git worktree add --detach ../beside HEAD", "git worktree add --detach \"$WT\" HEAD",
                   "git -C {} worktree add {} HEAD".format(linked, wt), "cd {} && git worktree add -b hyp ../hyp-2 HEAD".format(linked),
                   "sh -c 'cd {} && git worktree add {}'".format(linked, wt)]
        for agent in ("drive:investigator",):
            for command in ("git worktree add --detach {} HEAD".format(wt), "git -C {} worktree add --detach {} HEAD".format(linked, wt)):
                with self.subTest(agent=agent, allowed=command):
                    self.assertAllowed(self.bash(repo, command, agent=agent))
            for command in refused:
                with self.subTest(agent=agent, refused=command):
                    self.assertBlocked(self.bash(repo, command, agent=agent), "detached")
        for agent in ("drive:verifier", "drive:ui-reviewer", "drive:security-reviewer", "drive:severe-tester"):
            with self.subTest(agent=agent):
                self.assertBlocked(self.bash(repo, "git -C {} worktree add -b hyp {}".format(linked, wt), agent=agent))
                self.assertBlocked(self.bash(repo, "cd {} && git worktree add ../hyp-3".format(linked), agent=agent))
        # The main thread is held to the same form from inside a linked scratch worktree, which shares the repository's refs.
        self.assertBlocked(self.bash(repo, "git -C {} worktree add -b hyp {} HEAD".format(linked, wt)), "creates a branch")
        self.assertBlocked(self.bash(repo, "cd {} && git worktree add ../hyp-4".format(linked)), "without --detach")
        self.assertAllowed(self.bash(repo, "git -C {} worktree add --detach {} HEAD".format(linked, wt)))


class SecretScanTests(Severe, DriveTestCase):
    def test_the_security_reviewer_runs_gitleaks_only_in_its_read_only_shapes(self):
        repo = self.make_run()
        span = "{}..HEAD".format(self.code_sha[:12])
        allowed = ["gitleaks detect --redact --no-banner --no-git --source .",
                   "gitleaks detect --redact --source . --log-opts '{}'".format(span),
                   "gitleaks detect --redact -v --source=. --log-opts={} --report-format json --report-path .drive/reviews/{}-gitleaks.json".format(span, TODAY),
                   "gitleaks detect --redact --no-git -s src -r {}/gitleaks.json".format(self.scratch),
                   "/opt/homebrew/bin/gitleaks detect --redact --no-git --source src --exit-code 0",
                   "command -v gitleaks >/dev/null 2>&1 || echo absent", "gitleaks version"]
        refused = ["gitleaks detect --redact --no-git --source . --report-path src/leaks.json",
                   "gitleaks detect --redact --no-git --source . --report-path .drive/proofs/leaks.json",
                   "gitleaks detect --redact --no-git --source . --report-path=../leaks.json",
                   "gitleaks detect --redact --no-git --source . --report-path \"$OUT\"",
                   "gitleaks detect --no-git --source .", "gitleaks detect --redact --no-git",
                   "gitleaks detect --redact --source .", "gitleaks detect --redact --no-git --source . --log-opts '{}'".format(span),
                   "gitleaks detect --redact --source . --log-opts '--output=src/log.txt {}'".format(span),
                   "gitleaks detect --redact --source . --log-opts \"$RANGE\"",
                   "gitleaks detect --redact --no-git --source . --report-template leaks.tmpl",
                   "gitleaks protect --staged --redact", "gitleaks git --redact .", "gitleaks"]
        for agent in ("drive:security-reviewer",):
            for command in allowed:
                with self.subTest(agent=agent, allowed=command):
                    self.assertAllowed(self.bash(repo, command, agent=agent))
            for command in refused:
                with self.subTest(agent=agent, refused=command):
                    self.assertBlocked(self.bash(repo, command, agent=agent), "gitleaks runs only as")
        for agent in ("drive:verifier", "drive:auditor", "drive:grader"):
            with self.subTest(agent=agent):
                self.assertBlocked(self.bash(repo, allowed[0], agent=agent), "not on the reviewer's list")

    def test_the_scan_security_md_documents_runs_with_or_without_gitleaks(self):
        repo = self.make_run()
        text = (SKILL / "references" / "security.md").read_text()
        blocks = [b for b in re.findall(r"```bash\n(.*?)```", text, re.S) if "command -v gitleaks" in b]
        self.assertEqual(len(blocks), 1, "security.md documents one gitleaks scan with its grep fallback")
        self.assertIn("grep", blocks[0].split("command -v gitleaks", 1)[1])
        command = "SECRET_RE='AKIA[0-9A-Z]{16}'\n" + blocks[0].replace("<baseline_sha>", self.code_sha)
        self.assertAllowed(self.bash(repo, command, agent="drive:security-reviewer"))
        fallback = [line for line in blocks[0].splitlines() if "grep" in line and "xargs" in line]
        self.assertTrue(fallback)
        self.assertAllowed(self.bash(repo, "SECRET_RE='AKIA[0-9A-Z]{16}'; git diff --name-only --diff-filter=ACMR -z "
                                           "HEAD~1...HEAD | " + fallback[0].strip(), agent="drive:security-reviewer"))


class RefutationTests(Severe, DriveTestCase):
    def test_a_fail_counts_as_a_pass_only_when_another_verifier_refuted_every_blocking_gap(self):
        repo = self.make_run()
        gap = {"id": "token-replay", "claim": KEY, "severity": "blocking", "what": "a replayed token is accepted",
               "where": "src/auth.py:2", "repro": ["send the same token twice"], "confidence": 50}
        rel = ".drive/proofs/{}/r1/verdict.json".format(KEY)
        self.write(repo, rel, verdict(KEY, verdict_value="fail", gaps=[gap]))
        self.sign(repo, rel, agent_id="reviewer-1")
        self.assertFails(self.lint(repo), 'records verdict "fail", not pass')
        refute_rel = ".drive/proofs/{}/r1/refute-token-replay.json".format(KEY)
        refutation = {"result": "refuted", "proposition": "If a token is replayed, then the request is accepted",
                      "evidence": ["python3 tests/suite.py exit 0"], "guards_checked": ["the nonce table's unique index"],
                      "severity_check": "keep", "pre_existing": False}
        self.write(repo, refute_rel, refutation)
        self.assertFails(self.lint(repo), 'records verdict "fail", not pass')
        self.sign(repo, refute_rel, agent_type="drive:verifier", agent_id="reviewer-1")
        self.assertFails(self.lint(repo), 'records verdict "fail", not pass')
        self.sign(repo, refute_rel, agent_type="drive:verifier", agent_id="refuter-1")
        self.assertNoFailure(self.lint(repo))
        self.write(repo, refute_rel, dict(refutation, result="confirmed"))
        self.sign(repo, refute_rel, agent_type="drive:verifier", agent_id="refuter-1")
        self.assertFails(self.lint(repo), "still has a blocking gap")
