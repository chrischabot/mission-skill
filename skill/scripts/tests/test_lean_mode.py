"""Lean mode, the default: init, the lint, the Stop gate, end, the guard, the snapshot hook, re-injection, and promote.

The point of these tests is that a lean run is never held up by the checks that belong to rigorous mode, while a rigorous
run keeps every one of them."""
import json
import re
from pathlib import Path

from helpers import DriveTestCase, SKILL, drive, iso

GOAL = "Add a --since filter to the notes list command."
LEAN_STATE = """# STATE · proj · notes-since
mode: lean
goal: "{goal}"
status: {status}
phase: build
next: {next}
updated: {updated}
budget: $25 hard stop · 1 h · 12 subagents
spend: not measured
in flight: none

## Open items
"""


class LeanCase(DriveTestCase):
    def make_lean_run(self, status="running", commit=True):
        repo = self.new_repo()
        self.write(repo, "README.md", "# proj\n")
        self.write(repo, "notes/cli.py", "def main():\n    return 0\n")
        self.commit(repo, "chore: start")
        result = self.run_drive("init", "--slug", "notes-since", "--goal", "-", cwd=repo, stdin=GOAL)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.set_lean_state(repo, status=status)
        if commit:
            self.commit(repo, "drive(plan): notes-since")
        return repo

    def set_lean_state(self, repo, status="running", nxt="Spawn drive:implementer for P1.", updated=None):
        self.write(repo, ".drive/STATE.md", LEAN_STATE.format(goal=GOAL, status=status, next=nxt, updated=updated or iso()))

    def stop(self, repo, **payload):
        data = {"hook_event_name": "Stop", "cwd": str(repo), "stop_hook_active": False, "prompt_id": "p-{}".format(id(payload)),
                "last_assistant_message": "done", "background_tasks": [], "session_crons": []}
        data.update(payload)
        result = self.hook("hook-stop", data)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else None


class LeanInitTests(LeanCase):
    def test_init_without_size_writes_lean_files_marker_and_baseline(self):
        repo = self.make_lean_run(commit=False)
        drive_dir = repo / ".drive"
        for name in ("STATE.md", "PLAN.md", "LEARNINGS.md"):
            self.assertTrue((drive_dir / name).is_file(), name)
        for name in ("GOAL.md", "STATUS.md", "SPEC.md", "DESIGN.md", "TESTPLAN.md", "DECISIONS.md"):
            self.assertFalse((drive_dir / name).exists(), name)
        self.assertTrue((drive_dir / "local" / "active").is_file())
        self.assertTrue((drive_dir / "local" / "baseline.json").is_file())
        self.assertEqual(drive.run_mode(repo), "lean")

    def test_lean_init_refuses_a_size(self):
        repo = self.new_repo()
        self.write(repo, "README.md", "x\n")
        self.commit(repo, "chore: start")
        result = self.run_drive("init", "--mode", "lean", "--size", "M", "--goal", GOAL, cwd=repo)
        self.assertEqual(result.returncode, 2)

    def test_size_without_mode_is_still_rigorous(self):
        repo = self.new_repo()
        self.write(repo, "README.md", "x\n")
        self.commit(repo, "chore: start")
        self.assertEqual(self.run_drive("init", "--size", "S", "--goal", GOAL, cwd=repo).returncode, 0)
        self.assertIn("mode: rigorous", (repo / ".drive/GOAL.md").read_text())
        self.assertEqual(drive.run_mode(repo), "rigorous")

    def test_same_goal_resumes_a_lean_run_and_a_new_goal_keeps_learnings(self):
        repo = self.make_lean_run()
        self.write(repo, ".drive/LEARNINGS.md", (repo / ".drive/LEARNINGS.md").read_text() + "\n- kept\n")
        resumed = self.run_drive("init", "--goal", GOAL.upper(), cwd=repo)
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertIn("Same goal", resumed.stdout)
        self.commit(repo, "drive: learnings")
        other = self.run_drive("init", "--goal", "Export notes as JSON.", "--slug", "notes-json", cwd=repo)
        self.assertEqual(other.returncode, 0, other.stdout + other.stderr)
        self.assertIn("- kept", (repo / ".drive/LEARNINGS.md").read_text())
        self.assertTrue(list((repo / ".drive/runs").glob("*-notes-since/STATE.md")))

    def test_mode_resolution(self):
        repo = self.make_run()
        self.assertEqual(drive.run_mode(repo), "rigorous", "a .drive/ with GOAL.md and no mode line is rigorous")
        state = (repo / ".drive/STATE.md").read_text()
        self.write(repo, ".drive/STATE.md", state.replace("status: running", "mode: lean\nstatus: running", 1))
        self.assertEqual(drive.run_mode(repo), "lean", "an explicit mode line wins")


class LeanLintTests(LeanCase):
    def test_every_lint_mode_passes_with_no_rigorous_artifacts(self):
        repo = self.make_lean_run()
        for mode, gate in (("base", None), ("stop", None), ("final", None), ("base", "build"), ("base", "report")):
            findings = self.lint(repo, mode, gate)
            self.assertNoFailure(findings)

    def test_missing_next_or_state_fails(self):
        repo = self.make_lean_run()
        self.set_lean_state(repo, nxt="")
        self.assertFails(self.lint(repo), "next:")
        (repo / ".drive/STATE.md").unlink()
        self.write(repo, ".drive/PLAN.md", "# PLAN · notes-since\n")
        self.assertFails(self.lint(repo), "STATE.md: is missing")

    def test_future_timestamp_fails(self):
        repo = self.make_lean_run()
        self.set_lean_state(repo, updated=iso(3 * 3600))
        self.assertFails(self.lint(repo), "ahead of the clock")

    def test_rigorous_mode_line_keeps_rigorous_checks(self):
        repo = self.make_run()
        (repo / ".drive/GOAL.md").unlink()
        state = (repo / ".drive/STATE.md").read_text()
        self.write(repo, ".drive/STATE.md", state.replace("status: running", "mode: rigorous\nstatus: running", 1))
        self.assertFails(self.lint(repo), "GOAL.md: is missing")


class LeanStopGateTests(LeanCase):
    def test_done_run_ends_without_report_goal_status_or_audit(self):
        repo = self.make_lean_run(status="done")
        self.assertIsNone(self.stop(repo))
        self.assertIn("ALLOW lean status done", (repo / ".drive/local/gate.log").read_text())

    def test_blocked_and_stopped_end_without_rigorous_tokens(self):
        repo = self.make_lean_run(status="blocked")
        self.assertIsNone(self.stop(repo))
        self.set_lean_state(repo, status="stopped")
        self.assertIsNone(self.stop(repo))

    def test_running_run_is_held_to_its_next_step_and_nothing_else(self):
        repo = self.make_lean_run()
        self.write(repo, "notes/new.py", "x = 1\n")  # an uncommitted file fails rigorous hygiene, never a lean stop
        decision = self.stop(repo)
        self.assertEqual(decision["decision"], "block")
        self.assertIn("Spawn drive:implementer for P1", decision["reason"])
        for rigorous in ("GOAL.md", "STATUS", "uncommitted", "final audit", "retro"):
            self.assertNotIn(rigorous, decision["reason"])

    def test_running_drive_agent_lets_the_turn_end(self):
        repo = self.make_lean_run()
        tasks = [{"id": "a1", "type": "subagent", "status": "running", "agent_type": "drive:implementer"}]
        self.assertIsNone(self.stop(repo, background_tasks=tasks))

    def test_state_without_next_blocks(self):
        repo = self.make_lean_run(status="done")
        self.set_lean_state(repo, status="done", nxt="")
        decision = self.stop(repo)
        self.assertEqual(decision["decision"], "block")
        self.assertIn("next:", decision["reason"])


class LeanEndTests(LeanCase):
    def test_end_closes_a_committed_done_run(self):
        repo = self.make_lean_run(status="done")
        result = self.run_drive("end", cwd=repo)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertFalse((repo / ".drive/local/active").exists())

    def test_end_refuses_running_and_dirty_runs(self):
        repo = self.make_lean_run()
        self.assertEqual(self.run_drive("end", cwd=repo).returncode, 1)
        self.set_lean_state(repo, status="done")
        self.commit(repo, "drive(report): notes-since")
        self.write(repo, "notes/stray.py", "x = 1\n")
        result = self.run_drive("end", cwd=repo)
        self.assertEqual(result.returncode, 1)
        self.assertIn("uncommitted", result.stdout)


class LeanGuardTests(LeanCase):
    def guard(self, repo, agent, tool, **tool_input):
        payload = {"hook_event_name": "PreToolUse", "agent_type": agent, "agent_id": "a1", "tool_name": tool,
                   "tool_input": tool_input, "cwd": str(repo)}
        return self.hook("hook-guard", payload)

    APPEND = "cat >> .drive/LEARNINGS.md <<'EOF'\n### 2026-09-15 · implementer · x\n- Failed: y\nEOF"

    def test_implementer_appends_learnings_in_lean(self):
        lean = self.make_lean_run()
        self.assertEqual(self.guard(lean, "drive:implementer", "Bash", command=self.APPEND).returncode, 0)

    def test_implementer_may_not_append_learnings_in_rigorous(self):
        append = self.APPEND
        rigorous = self.make_run()
        self.write(rigorous, ".drive/LEARNINGS.md", "# LEARNINGS · proj\n")
        self.assertEqual(self.guard(rigorous, "drive:implementer", "Bash", command=append).returncode, 2)

    def test_implementer_still_never_touches_git_or_other_state(self):
        repo = self.make_lean_run()
        self.assertEqual(self.guard(repo, "drive:implementer", "Bash", command="git commit -am x").returncode, 2)
        self.assertEqual(self.guard(repo, "drive:implementer", "Write", file_path=str(repo / ".drive/STATE.md"), content="x").returncode, 2)
        self.assertEqual(self.guard(repo, "drive:implementer", "Write", file_path=str(repo / "notes/cli.py"), content="x").returncode, 0)

    def test_reviewer_fixes_code_and_writes_report_but_never_commits(self):
        repo = self.make_lean_run()
        self.assertEqual(self.guard(repo, "drive:reviewer", "Edit", file_path=str(repo / "notes/cli.py"), old_string="a", new_string="b").returncode, 0)
        self.assertEqual(self.guard(repo, "drive:reviewer", "Write", file_path=str(repo / ".drive/REPORT.md"), content="x").returncode, 0)
        self.assertEqual(self.guard(repo, "drive:reviewer", "Write", file_path=str(repo / ".drive/STATE.md"), content="x").returncode, 2)
        self.assertEqual(self.guard(repo, "drive:reviewer", "Bash", command="git commit -am fix").returncode, 2)
        self.assertEqual(self.guard(repo, "drive:reviewer", "Bash", command="git push").returncode, 2)

    def test_planner_writes_only_drive_state(self):
        repo = self.make_lean_run()
        self.assertEqual(self.guard(repo, "drive:planner", "Write", file_path=str(repo / ".drive/PLAN.md"), content="x").returncode, 0)
        self.assertEqual(self.guard(repo, "drive:planner", "Write", file_path=str(repo / "notes/cli.py"), content="x").returncode, 2)

    def test_snapshot_takes_no_tree_snapshot_in_lean(self):
        repo = self.make_lean_run()
        payload = {"hook_event_name": "SubagentStart", "agent_type": "drive:security-reviewer", "agent_id": "sec-1", "cwd": str(repo)}
        self.assertEqual(self.hook("hook-snapshot", payload, "start").returncode, 0)
        self.assertFalse(list((repo / ".drive/local").glob("ro/*.json")))
        spawns = drive.ledger_entries(repo, "spawn")
        self.assertTrue(any(e.get("agent_type") == "drive:security-reviewer" for e in spawns))


class LeanReinjectTests(LeanCase):
    def test_reinject_prints_lean_sections_only(self):
        repo = self.make_lean_run()
        result = self.hook("hook-reinject", {"hook_event_name": "SessionStart", "source": "compact", "cwd": str(repo)})
        self.assertIn("lean mode", result.stdout)
        self.assertIn("DRIVE · START", result.stdout)
        skill = (SKILL / "SKILL.md").read_text().splitlines()
        for prefix in ("## Mode", "## 1. ", "## Standing rules", "## 4. ", "## 5. ", "## 7. ", "## Roster"):
            heading = next(line for line in skill if line.startswith(prefix))
            self.assertIn(heading, result.stdout)
        for prefix in ("## 2. ", "## Run state at invocation"):
            heading = next(line for line in skill if line.startswith(prefix))
            self.assertNotIn(heading, result.stdout)
        self.assertNotIn("## 5. Proof", result.stdout)


ENTRY = """
### 2026-09-15 · {role} · {title}
- Failed: {failed}
- Why: {why}
- Verified: {verified}
- Rule: {rule}
- Scope: {scope}
"""


class PromoteTests(LeanCase):
    def make_skill(self):
        skill = self.tmp / "skillrepo" / "skill"
        (skill / "references" / "lessons").mkdir(parents=True)
        (skill / "references" / "domains").mkdir()
        (skill / "SKILL.md").write_text("# drive\n<!-- drive:standing-rules:start -->\n<!-- drive:standing-rules:end -->\n")
        (skill / "references" / "lessons" / "general.md").write_text(
            (SKILL / "references" / "lessons" / "general.md").read_text())
        (skill / "references" / "lessons" / "learned.md").write_text(
            (SKILL / "references" / "lessons" / "learned.md").read_text())
        top = skill.parent
        self.git(top, "init", "-q", "-b", "main")
        self.commit(top, "skill")
        return skill

    def entry(self, **values):
        base = dict(role="implementer", title="t", failed="f", why="w", verified="ran it", rule="r", scope="project")
        base.update(values)
        return ENTRY.format(**base)

    def test_sorts_entries_and_promotes_verified_general_rules_once(self):
        skill = self.make_skill()
        repo = self.make_lean_run()
        learnings = repo / ".drive/LEARNINGS.md"
        learnings.write_text(learnings.read_text()
                             + self.entry(title="dates are strings", failed="TypeError comparing str and date in notes/cli.py:12",
                                          why="store.all_notes returns created as ISO text", verified="printed type(note['created'])",
                                          rule="Parse stored dates before comparing them", scope="project")
                             + self.entry(role="reviewer", title="expected value from code", failed="a test copied its expected value from the output",
                                          why="the implementer ran the function to get the expected list", verified="broke the filter and the test still passed",
                                          rule="Derive every expected test value from the input data, never from the code under test", scope="general")
                             + self.entry(title="slow suite", failed="the suite took four minutes", why="guess: network calls",
                                          verified="guess", rule="Stub the network", scope="general"))
        result = self.run_drive("promote", "--skill-dir", str(skill), cwd=repo)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        text = learnings.read_text()
        sections = drive.Doc(text).sections
        facts = "\n".join(l for _, l in sections["Verified facts"])
        rules = "\n".join(l for _, l in sections["General rules"])
        failures = "\n".join(l for _, l in sections["Open failures"])
        self.assertIn("ISO text", facts)
        self.assertIn("Parse stored dates before comparing them", rules)
        self.assertIn("slow suite", failures)
        self.assertNotIn("Stub the network", rules, "a guess is never promoted to a rule")
        self.assertFalse([l for _, l in sections["New entries"] if l.startswith("### ")], "processed entries leave New entries")
        learned = (skill / "references/lessons/learned.md").read_text()
        self.assertIn("### Derive every expected test value from the input data, never from the code under test", learned)
        self.assertNotIn("Parse stored dates", learned, "a project rule stays in the project")
        self.assertEqual(self.run_drive("lesson-check", "--skill-dir", str(skill)).returncode, 0)
        log = self.git(skill.parent, "log", "--format=%s", "-1")
        self.assertTrue(log.startswith("lesson(learned): "), log)
        self.assertEqual(self.git(skill.parent, "status", "--porcelain"), "")

        # The same rule from a later run raises its Seen count instead of adding a second entry.
        learnings.write_text(learnings.read_text() + self.entry(
            role="reviewer", title="again", failed="copied expected value", why="ran the function for the expectation",
            verified="mutated the code", rule="Derive every expected test value from the input data, never from the code under test",
            scope="general"))
        self.assertEqual(self.run_drive("promote", "--skill-dir", str(skill), cwd=repo).returncode, 0)
        learned = (skill / "references/lessons/learned.md").read_text()
        self.assertEqual(learned.count("### Derive every expected test value"), 1)
        self.assertRegex(learned, r"- Seen: 2 \(")

    def test_a_rule_already_in_general_md_is_not_added(self):
        skill = self.make_skill()
        repo = self.make_lean_run()
        learnings = repo / ".drive/LEARNINGS.md"
        learnings.write_text(learnings.read_text() + self.entry(
            rule="Remove every worktree a step creates in that same step, and never create a branch", scope="general"))
        self.assertEqual(self.run_drive("promote", "--skill-dir", str(skill), cwd=repo).returncode, 0)
        self.assertNotIn("### Remove every worktree", (skill / "references/lessons/learned.md").read_text())
        self.assertIn("Already in drive's lessons", learnings.read_text())

    def test_rules_naming_paths_or_home_directories_stay_in_the_project(self):
        skill = self.make_skill()
        repo = self.make_lean_run()
        learnings = repo / ".drive/LEARNINGS.md"
        learnings.write_text(learnings.read_text() + self.entry(rule="Always import notes/store.py lazily", scope="general")
                             + self.entry(rule="Keep caches out of the repo", why="it lived in /Users/someone/cache", scope="general"))
        self.assertEqual(self.run_drive("promote", "--skill-dir", str(skill), cwd=repo).returncode, 0)
        learned = (skill / "references/lessons/learned.md").read_text()
        self.assertNotIn("### Always import", learned)
        self.assertNotIn("### Keep caches", learned)
        self.assertEqual(learned.count("\n### "), 0)
        self.assertEqual(len(re.findall("Kept in this project", learnings.read_text())), 2)

    def test_without_a_learning_file_promote_does_nothing(self):
        repo = self.new_repo()
        result = self.run_drive("promote", cwd=repo)
        self.assertEqual(result.returncode, 0)
        self.assertIn("nothing to promote", result.stdout)

    def test_learned_md_entries_are_checked_by_lesson_check(self):
        skill = self.make_skill()
        path = skill / "references/lessons/learned.md"
        path.write_text(path.read_text() + "\n### A rule with no fields\n- Because: nothing else\n")
        result = self.run_drive("lesson-check", "--skill-dir", str(skill))
        self.assertEqual(result.returncode, 1)
        self.assertIn("Verified by", result.stdout)
