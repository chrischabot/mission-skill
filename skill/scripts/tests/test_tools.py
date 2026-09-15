"""init, end, capabilities, selfcheck, worktree-land, the floor guard, and the lesson commands."""
import json
import os
from pathlib import Path

from helpers import GOAL_TEXT, DriveTestCase, TODAY, drive

LESSON = """### Before trusting a green run against a local database double, list the limits it does not enforce
- When: tests run against an in-memory or emulated database that stands in for a hosted one.
- Do: list the hosted database's documented limits and make the double or the code enforce each one.
- Because: a double more permissive than production certifies code that fails live.
- Check: the kindness ledger in TESTPLAN.md
- Verified by: a query passed locally with 101 bound parameters and failed live at the limit of 100, 2026-07-25.
- Applies to: runs with a hosted database and a local double.
- Not for: pure in-process code with no hosted counterpart.
- Seen: 1 (2026-07-25) · Added: 2026-09-14 · Confirmed by: auditor, claude-fable-5-1
"""


class InitEndTests(DriveTestCase):
    def test_init_creates_state_ignore_and_marker(self):
        repo = self.new_repo()
        self.write(repo, "README.md", "x\n")
        self.commit(repo, "chore: start")
        result = self.run_drive("init", "--goal", "Add CSV export to invoices", "--size", "M", cwd=repo)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for name in ("GOAL.md", "STATE.md", "STATUS.md", "DECISIONS.md", "LESSONS.md", "CONSTRAINTS.md"):
            self.assertTrue((repo / ".drive" / name).is_file(), name)
        for folder in ("proofs", "reviews", "investigations", "handoffs", "packages"):
            self.assertTrue((repo / ".drive" / folder).is_dir(), folder)
        self.assertTrue((repo / ".drive/local/active").is_file())
        ignore = (repo / ".gitignore").read_text()
        self.assertIn(".drive/local/", ignore)
        self.assertIn("!.drive/proofs/*/r*/shots/**/*.review.png", ignore)
        goal = (repo / ".drive/GOAL.md").read_text()
        self.assertIn('goal: "Add CSV export to invoices"', goal)
        self.assertIn("# GOAL · csv-export", goal)
        self.assertIn("status: running", (repo / ".drive/STATE.md").read_text())

    def test_init_refuses_xs(self):
        repo = self.new_repo()
        result = self.run_drive("init", "--goal", "Fix a typo", "--size", "XS", cwd=repo)
        self.assertEqual(result.returncode, 1)
        self.assertFalse((repo / ".drive").exists())

    def test_init_with_same_goal_resumes(self):
        repo = self.make_run()
        result = self.run_drive("init", "--goal", "  " + GOAL_TEXT.upper().replace(" ", "\n  "), cwd=repo)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Same goal", result.stdout)
        self.assertTrue((repo / ".drive/STATUS.md").is_file())

    def test_a_different_goal_sharing_its_first_fifty_characters_is_not_a_resume(self):
        repo = self.new_repo()
        self.write(repo, "README.md", "x\n")
        self.commit(repo, "chore: start")
        first = "Add a CSV export to the invoices page for the accountants, with totals per customer"
        second = "Add a CSV export to the invoices page for the accountants, with a PDF fallback for auditors"
        self.assertEqual(drive.slugify(first, 50), drive.slugify(second, 50))
        self.assertEqual(self.run_drive("init", "--goal", first, "--size", "S", cwd=repo).returncode, 0)
        result = self.run_drive("init", "--goal", second, "--size", "S", cwd=repo)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("Same goal", result.stdout)
        self.assertIn("Paused the previous run", result.stdout)

    def test_an_older_goal_file_without_goal_text_still_resumes_by_slug(self):
        repo = self.make_run()
        goal = (repo / ".drive/GOAL.md").read_text().replace('goal: "{}"\n'.format(GOAL_TEXT), "")
        self.write(repo, ".drive/GOAL.md", goal)
        result = self.run_drive("init", "--goal", "anything", "--slug", "session-auth", cwd=repo)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Same goal", result.stdout)

    def test_init_archives_a_run_for_a_different_goal(self):
        repo = self.make_run()
        result = self.run_drive("init", "--goal", "Add an audit log", "--size", "S", cwd=repo)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        archive = repo / ".drive" / "runs" / "{}-session-auth".format(TODAY)
        self.assertTrue((archive / "STATUS.md").is_file())
        self.assertTrue((archive / "RESTORE.md").is_file())
        self.assertTrue((repo / ".drive/local/archive/{}-session-auth/active".format(TODAY)).is_file())
        self.assertIn("# GOAL · audit-log", (repo / ".drive/GOAL.md").read_text())
        decisions = (repo / ".drive/DECISIONS.md").read_text()
        self.assertIn("Pause the unfinished run for a different goal", decisions)
        self.assertIn(".drive/runs/{}-session-auth".format(TODAY), decisions)
        self.assertIn('"slug": "audit-log"', (repo / ".drive/local/active").read_text())

    def test_end_refuses_unfinished_run(self):
        repo = self.make_run()
        result = self.run_drive("end", cwd=repo)
        self.assertEqual(result.returncode, 1)
        self.assertTrue((repo / ".drive/local/active").exists())

    def test_end_closes_a_done_run(self):
        repo = self.make_final_run()
        result = self.run_drive("end", cwd=repo)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertFalse((repo / ".drive/local/active").exists())

    def test_end_with_failing_final_lint_keeps_marker(self):
        repo = self.make_final_run()
        (repo / ".drive/REPORT.md").unlink()
        self.commit(repo, "drive: lose report")
        result = self.run_drive("end", cwd=repo)
        self.assertEqual(result.returncode, 1)
        self.assertIn("REPORT.md", result.stdout)
        self.assertTrue((repo / ".drive/local/active").exists())

    def test_every_subcommand_accepts_root(self):
        repo = self.make_run()
        result = self.run_drive("lint", "--stop", "--root", str(repo), cwd=self.tmp)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("DRIVE · START", self.run_drive("start", "--root", str(repo), cwd=self.tmp).stdout)


class CapabilitiesTests(DriveTestCase):
    def test_skills_plugins_dangling_links_and_baseline(self):
        repo = self.make_run()
        skills = self.home / ".claude" / "skills"
        (skills / "writing").mkdir(parents=True)
        (skills / "writing" / "SKILL.md").write_text("---\nname: writing\n---\n")
        (skills / "half-installed").mkdir()
        (skills / "severe-testing").symlink_to(self.tmp / "gone")
        plugin = self.home / ".claude" / "plugins" / "cache" / "market" / "arcplug" / "1.0.0" / "skills" / "writing"
        plugin.mkdir(parents=True)
        (plugin / "SKILL.md").write_text("---\nname: writing\n---\n")
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        git_path = next(Path(p) / "git" for p in os.environ["PATH"].split(os.pathsep) if (Path(p) / "git").is_file())
        (bin_dir / "git").symlink_to(git_path)
        env = {"PATH": str(bin_dir)}
        result = self.run_drive("capabilities", cwd=repo, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads((repo / ".drive/capabilities.json").read_text())
        self.assertIs(data["skill:writing"], True)
        self.assertIs(data["skill:half-installed"], False)
        self.assertEqual(data["skill:severe-testing"], "dangling")
        self.assertIs(data["skill:deep-research"], False)
        self.assertIs(data["plugin-skill:arcplug:writing"], True)
        self.assertIs(data["cli:gh"], False)
        self.assertIs(data["cli:simctl"], False)
        baseline = data["git:baseline_sha"]
        self.assertEqual(baseline, self.git(repo, "rev-parse", "--short", "HEAD"))
        self.assertIn("checked_at", data)
        self.write(repo, "src/later.py", "x = 1\n")
        self.commit(repo, "feat: later")
        self.run_drive("capabilities", cwd=repo, env=env)
        self.assertEqual(json.loads((repo / ".drive/capabilities.json").read_text())["git:baseline_sha"], baseline)

    def test_creates_drive_directory_and_never_fails_outside_git(self):
        folder = self.tmp / "plain"
        folder.mkdir()
        result = self.run_drive("capabilities", cwd=folder)
        self.assertEqual(result.returncode, 0)
        self.assertIsNone(json.loads((folder / ".drive/capabilities.json").read_text())["git:origin"])


class SelfcheckTests(DriveTestCase):
    def test_reports_missing_paths_and_passes_when_present(self):
        skill = self.tmp / "skill"
        (skill / "references").mkdir(parents=True)
        (skill / "agents").mkdir()
        (skill / "SKILL.md").write_text("Read `references/present.md` and references/missing.md, fill templates/GOAL.md,\n"
                                        "run python3 ~/.claude/skills/drive/scripts/drive.py lint, and the project's scripts/ios/run.sh.\n")
        (skill / "references" / "present.md").write_text("See templates/lesson.md.\n")
        result = self.run_drive("selfcheck", "--skill-dir", str(skill))
        self.assertEqual(result.returncode, 1)
        for missing in ("references/missing.md", "templates/GOAL.md", "templates/lesson.md", "scripts/drive.py"):
            self.assertIn(missing, result.stdout)
        self.assertNotIn("scripts/ios", result.stdout)
        for rel in ("references/missing.md", "templates/GOAL.md", "templates/lesson.md", "scripts/drive.py"):
            self.write(skill, rel, "x\n")
        self.assertEqual(self.run_drive("selfcheck", "--skill-dir", str(skill)).returncode, 0)

    def test_skill_md_over_cap_fails(self):
        skill = self.tmp / "skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text("line\n" * 460)
        result = self.run_drive("selfcheck", "--skill-dir", str(skill))
        self.assertEqual(result.returncode, 1)
        self.assertIn("cap is 450", result.stdout)


class WorktreeLandTests(DriveTestCase):
    def arm(self, repo, where=None, rel="src/arm.py", content="x = 1\n"):
        wt = where or self.scratch / "drive-proj-arm"
        self.git(repo, "worktree", "add", "-q", "--detach", str(wt), "HEAD")
        self.write(wt, rel, content)
        self.git(wt, "add", rel)
        self.git(wt, "commit", "-q", "-m", "experiment(arm): try it")
        return wt, self.git(wt, "rev-parse", "HEAD")

    def test_lands_by_cherry_pick_and_leaves_no_branch_or_worktree(self):
        repo = self.make_run()
        branches = self.git(repo, "branch", "--list")
        wt, sha = self.arm(repo)
        result = self.run_drive("worktree-land", str(wt), sha, cwd=repo)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue((repo / "src/arm.py").is_file())
        self.assertFalse(wt.exists())
        self.assertEqual(self.git(repo, "branch", "--list"), branches)
        self.assertEqual(len(self.git(repo, "worktree", "list").splitlines()), 1)
        self.assertEqual(self.git(repo, "log", "-1", "--format=%s"), "experiment(arm): try it")
        self.assertIn("LAND", (repo / ".drive/local/gate.log").read_text())

    def test_refuses_a_branch_name(self):
        repo = self.make_run()
        wt = self.scratch / "drive-proj-branch-arm"
        self.git(repo, "worktree", "add", "-q", "-b", "drive/arm", str(wt), "HEAD")
        sha = self.git(wt, "rev-parse", "HEAD")
        result = self.run_drive("worktree-land", "drive/arm", sha, cwd=repo)
        self.assertEqual(result.returncode, 1)
        self.assertIn("is a branch", result.stdout)

    def test_refuses_when_the_arm_moved(self):
        repo = self.make_run()
        wt, sha = self.arm(repo)
        self.write(wt, "src/arm.py", "x = 2\n")
        self.git(wt, "commit", "-q", "-am", "later")
        head = self.git(repo, "rev-parse", "HEAD")
        result = self.run_drive("worktree-land", str(wt), sha, cwd=repo)
        self.assertEqual(result.returncode, 2)
        self.assertIn("moved", result.stdout)
        self.assertEqual(self.git(repo, "rev-parse", "HEAD"), head)
        self.assertTrue(wt.exists())

    def test_refuses_to_remove_a_worktree_outside_allowlisted_roots(self):
        repo = self.make_run()
        wt, sha = self.arm(repo, where=self.tmp / "beside")
        head = self.git(repo, "rev-parse", "HEAD")
        result = self.run_drive("worktree-land", str(wt), sha, cwd=repo)
        self.assertEqual(result.returncode, 2)
        self.assertIn("not under an allowlisted root", result.stdout)
        self.assertEqual(self.git(repo, "rev-parse", "HEAD"), head)
        self.assertTrue(wt.exists())

    def test_refuses_dirty_worktree(self):
        repo = self.make_run()
        wt, sha = self.arm(repo)
        self.write(wt, "src/uncommitted.py", "y = 1\n")
        result = self.run_drive("worktree-land", str(wt), sha, cwd=repo)
        self.assertEqual(result.returncode, 1)
        self.assertIn("uncommitted changes", result.stdout)

    def test_refuses_to_run_inside_the_worktree(self):
        repo = self.make_run()
        wt, sha = self.arm(repo)
        self.assertEqual(self.run_drive("worktree-land", str(wt), sha, cwd=wt).returncode, 1)

    def test_refuses_when_the_main_checkout_left_the_run_branch(self):
        repo = self.make_run()
        wt, sha = self.arm(repo)
        self.git(repo, "checkout", "-q", "-b", "elsewhere")
        head = self.git(repo, "rev-parse", "HEAD")
        result = self.run_drive("worktree-land", str(wt), sha, cwd=repo)
        self.assertEqual(result.returncode, 1)
        self.assertIn("the run started on main", result.stdout)
        self.assertEqual(self.git(repo, "rev-parse", "HEAD"), head)

    def test_conflicting_arm_aborts_cleanly_and_keeps_the_worktree(self):
        repo = self.make_run()
        wt, sha = self.arm(repo, rel="README.md", content="# arm\n")
        self.write(repo, "README.md", "# main moved on\n")
        head = self.commit(repo, "docs: main moved on")
        result = self.run_drive("worktree-land", str(wt), sha, cwd=repo)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("do not apply cleanly", result.stdout)
        self.assertEqual(self.git(repo, "rev-parse", "--short", "HEAD"), head)
        self.assertFalse((repo / ".git" / "CHERRY_PICK_HEAD").exists())
        self.assertEqual(self.git(repo, "status", "--porcelain"), "")
        self.assertTrue(wt.exists())


class FloorGuardTests(DriveTestCase):
    CONSTRAINTS = """# CONSTRAINTS · proj
Last reviewed: 2026-08-08

## Floor
- No added suppression comments.
- No assertion removed from a test file that still exists.

## Enforced
| rule | command | measured | direction | tolerance | target | reason | measured at |
|---|---|---|---|---|---|---|---|
| Test suite passing | `python3 -m pytest -q` | 42/42 | must not fall | 0 | all | the suite is the floor | abc1234 · 2026-08-08 |
| Type errors | `mypy src` | 3 | must not grow | 0 | 0 | legacy module | abc1234 · 2026-08-08 |

## Measured only
| metric | command | measured | direction | measured at |
|---|---|---|---|---|

## Exceptions
| rule | path | reason | undo | decision |
|---|---|---|---|---|
"""

    def setUp(self):
        super().setUp()
        self.repo = self.new_repo()
        self.write(self.repo, "src/app.ts", "export const x = 1;\n")
        self.write(self.repo, "tests/app.test.ts", "it('adds', () => {\n  expect(add(1, 2)).toBe(3);\n  expect(add(0, 0)).toBe(0);\n});\n")
        self.write(self.repo, ".drive/CONSTRAINTS.md", self.CONSTRAINTS)
        self.write(self.repo, ".drive/DECISIONS.md", "# DECISIONS · proj\n")
        self.commit(self.repo, "chore: baseline")

    def guard(self, *args):
        return self.run_drive("guard", *args, cwd=self.repo)

    def test_clean_tree_passes(self):
        result = self.guard()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_untracked_file_with_suppression_is_caught(self):
        self.write(self.repo, "src/new.ts", "// @ts-ignore\nconst y: number = 'x';\n")
        result = self.guard()
        self.assertEqual(result.returncode, 1)
        self.assertIn("suppression · src/new.ts:1", result.stdout)

    def test_staged_and_unstaged_changes_are_both_checked(self):
        self.write(self.repo, "src/app.ts", "export const x = 1; // eslint-disable-line\n")
        self.git(self.repo, "add", "src/app.ts")
        self.write(self.repo, "src/other.py", "def f():\n    raise NotImplementedError\n")
        self.git(self.repo, "add", "src/other.py")
        self.write(self.repo, "src/other.py", "def f():\n    raise NotImplementedError\n\ntry:\n    f()\nexcept Exception:\n    pass\n")
        result = self.guard()
        self.assertEqual(result.returncode, 1)
        self.assertIn("suppression · src/app.ts:1", result.stdout)
        self.assertIn("stub · src/other.py:2", result.stdout)
        self.assertIn("empty-catch · src/other.py:6", result.stdout)

    def test_removed_assertion_in_surviving_test_is_caught_but_reworded_one_is_not(self):
        self.write(self.repo, "tests/app.test.ts", "it('adds', () => {\n  expect(add(1, 2)).toBe(3);\n});\n")
        self.assertIn("removed-assertion · tests/app.test.ts", self.guard().stdout)
        self.write(self.repo, "tests/app.test.ts", "it('adds', () => {\n  expect(add(1, 2)).toBe(3);\n  expect(add(-1, 1)).toBe(0);\n});\n")
        self.assertEqual(self.guard().returncode, 0)

    def test_added_skip_and_deleted_test_are_caught(self):
        self.write(self.repo, "tests/app.test.ts", "it.skip('adds', () => {\n  expect(add(1, 2)).toBe(3);\n  expect(add(0, 0)).toBe(0);\n});\n")
        self.assertIn("skip · tests/app.test.ts:1", self.guard().stdout)
        (self.repo / "tests/app.test.ts").unlink()
        self.assertIn("deleted-test · tests/app.test.ts", self.guard().stdout)

    def test_lowered_constraint_is_loud_and_tightened_is_silent(self):
        text = self.CONSTRAINTS
        self.write(self.repo, ".drive/CONSTRAINTS.md", text.replace("| 3 | must not grow | 0 | 0 |", "| 5 | must not grow | 0 | 0 |"))
        result = self.guard()
        self.assertEqual(result.returncode, 1)
        self.assertIn("raised its measured from 3 to 5", result.stdout)
        self.write(self.repo, ".drive/CONSTRAINTS.md", text.replace("| 3 | must not grow | 0 | 0 |", "| 2 | must not grow | 0 | 0 |"))
        self.assertEqual(self.guard().returncode, 0)
        self.write(self.repo, ".drive/CONSTRAINTS.md", text.replace("| 3 | must not grow | 0 |", "| 3 | must not grow | 2 |"))
        self.assertIn("widened its tolerance", self.guard().stdout)

    def test_earlier_review_date_is_not_a_lowered_threshold(self):
        text = self.CONSTRAINTS.replace("Last reviewed: 2026-08-08", "Last reviewed: 2026-09-01").replace(
            "abc1234 · 2026-08-08 |\n| Type", "def5678 · 2026-09-01 |\n| Type")
        self.write(self.repo, ".drive/CONSTRAINTS.md", text)
        result = self.guard()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_removed_row_or_changed_command_is_loud(self):
        self.write(self.repo, ".drive/CONSTRAINTS.md", self.CONSTRAINTS.replace("| Type errors | `mypy src` |", "| Type errors | `mypy src --ignore-missing-imports` |"))
        self.assertIn("changed its command", self.guard().stdout)
        self.write(self.repo, ".drive/CONSTRAINTS.md", "\n".join(l for l in self.CONSTRAINTS.splitlines() if not l.startswith("| Type errors")) + "\n")
        self.assertIn("was removed", self.guard().stdout)

    def test_unrecorded_exception_is_blocked_and_recorded_one_suppresses(self):
        row = "| suppression | `src/legacy/**` | vendored code | delete the vendored copy | DECISIONS.md 2026-09-14-allow-legacy-suppressions |\n"
        self.write(self.repo, ".drive/CONSTRAINTS.md", self.CONSTRAINTS + row)
        self.write(self.repo, "src/legacy/old.ts", "// @ts-nocheck\n")
        result = self.guard()
        self.assertIn("exception · .drive/CONSTRAINTS.md", result.stdout)
        self.write(self.repo, ".drive/DECISIONS.md", "# DECISIONS · proj\n\n## 2026-09-14 · Allow legacy suppressions\n- Decision: allow.\n- Undo: delete the copy · reversal cost: low.\n")
        result = self.guard()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_secret_is_reported_without_its_value(self):
        token = "ghp_" + "b" * 36
        self.write(self.repo, "src/config.ts", "export const token = '{}';\n".format(token))
        result = self.guard()
        self.assertIn("secret · src/config.ts:1", result.stdout)
        self.assertNotIn(token, result.stdout)

    def test_could_not_run_exits_two(self):
        plain = self.tmp / "plain"
        plain.mkdir()
        self.assertEqual(self.run_drive("guard", cwd=plain).returncode, 2)
        self.assertEqual(self.guard("--base", "no-such-ref").returncode, 2)


class LessonToolTests(DriveTestCase):
    def skill_repo(self, lessons=LESSON, standing_lines=3):
        repo = self.new_repo("drive-repo")
        skill = repo / "skill"
        block = "\n".join("- rule {}".format(n) for n in range(standing_lines))
        self.write(skill, "SKILL.md", "# drive\n<!-- drive:standing-rules:start -->\n{}\n<!-- drive:standing-rules:end -->\n".format(block))
        self.write(skill, "references/lessons/general.md", "# General lessons\n\n## Entries\n\n" + lessons)
        self.write(skill, "references/lessons/retired.md", "# Retired lessons\n\n```markdown\n### <heading>\n- Retired: <date>\n```\n\n## Entries\n")
        self.write(skill, "references/lessons/rejected.md", "# Rejected lessons\n\n## Entries\n")
        self.write(skill, "references/domains/web.md", "# Web\n\n## 12. Learned constraints\n")
        self.commit(repo, "skill: seed")
        return repo, skill

    def test_valid_lessons_pass(self):
        _, skill = self.skill_repo()
        result = self.run_drive("lesson-check", "--skill-dir", str(skill))
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_command_in_inline_code_is_not_a_placeholder(self):
        _, skill = self.skill_repo(lessons=LESSON.replace("- Do: list", "- Do: land winners with `drive.py worktree-land <branch> <sha>` and list"))
        result = self.run_drive("lesson-check", "--skill-dir", str(skill))
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_missing_check_field_fails(self):
        _, skill = self.skill_repo(lessons=LESSON.replace("- Check: the kindness ledger in TESTPLAN.md\n", ""))
        result = self.run_drive("lesson-check", "--skill-dir", str(skill))
        self.assertEqual(result.returncode, 1)
        self.assertIn("is missing '- Check:'", result.stdout)

    def test_near_duplicate_heading_fails(self):
        dup = LESSON.replace("list the limits it does not enforce", "list the limits it doesn't enforce")
        _, skill = self.skill_repo(lessons=LESSON + "\n" + dup)
        self.assertIn("nearly matches", self.run_drive("lesson-check", "--skill-dir", str(skill)).stdout)

    def test_home_path_and_secret_fail(self):
        _, skill = self.skill_repo(lessons=LESSON.replace("failed live at the limit of 100", "failed live in /Users/someone/app"))
        self.assertIn("home-directory path", self.run_drive("lesson-check", "--skill-dir", str(skill)).stdout)

    def test_domain_learned_constraints_are_checked(self):
        _, skill = self.skill_repo()
        self.write(skill, "references/domains/web.md", "# Web\n\n## 12. Learned constraints\n\n### Preview deploys serve a different build than production\n- When: checking a site.\n")
        self.assertIn("is missing '- Do:'", self.run_drive("lesson-check", "--skill-dir", str(skill)).stdout)

    def test_standing_rules_block_over_fifteen_lines_fails(self):
        _, skill = self.skill_repo(standing_lines=16)
        self.assertIn("standing-rules block has 16 lines", self.run_drive("lesson-check", "--skill-dir", str(skill)).stdout)

    def test_general_cap_fails(self):
        entries = "\n".join(LESSON.replace("list the limits it does not enforce", "variant {} of the rule about database limits".format("x" * n))
                            for n in range(61))
        _, skill = self.skill_repo(lessons=entries)
        self.assertIn("the cap is 60", self.run_drive("lesson-check", "--skill-dir", str(skill)).stdout)

    def test_lesson_commit_uses_fixed_message_and_only_named_files(self):
        repo, skill = self.skill_repo()
        new = LESSON.replace("Before trusting a green run against a local database double, list the limits it does not enforce",
                             "When a workaround is needed a second time, stop and diagnose the mechanism first")
        with open(skill / "references/lessons/general.md", "a") as handle:
            handle.write("\n" + new)
        args = ["lesson-commit", str(skill / "references/lessons/general.md"), "--skill-dir", str(skill),
                "--trigger", "repeated-workaround", "--date", "2026-09-14", "--investigation", ".drive/investigations/2026-09-14-timeout.md",
                "--dedupe", "distinct", "--auditor-model", "claude-fable-5-1", "--check", "the workaround ledger", "--project", "proj", "--run", "session-auth"]
        self.write(repo, "unrelated.txt", "x\n")
        self.git(repo, "add", "unrelated.txt")
        refused = self.run_drive(*args)
        self.assertEqual(refused.returncode, 1)
        self.assertIn("already staged", refused.stdout)
        self.git(repo, "reset", "-q", "unrelated.txt")
        result = self.run_drive(*args)
        self.assertEqual(result.returncode, 0, result.stdout)
        message = self.git(repo, "log", "-1", "--format=%B")
        self.assertTrue(message.startswith("lesson(general): When a workaround is needed a second time, stop and diagnose the mechanism first"))
        for line in ("Trigger: repeated-workaround on 2026-09-14", "Dedupe: distinct", "Auditor: accepted (claude-fable-5-1)",
                     "Check: the workaround ledger", "Project: proj", "Run: session-auth"):
            self.assertIn(line, message)
        self.assertEqual(self.git(repo, "show", "--name-only", "--format=", "HEAD"), "skill/references/lessons/general.md")

    def test_lesson_commit_takes_a_standing_rule_but_refuses_any_other_skill_md_change(self):
        repo, skill = self.skill_repo()
        new = LESSON.replace("Before trusting a green run against a local database double, list the limits it does not enforce",
                             "When a workaround is needed a second time, stop and diagnose the mechanism first")
        with open(skill / "references/lessons/general.md", "a") as handle:
            handle.write("\n" + new)
        args = ["lesson-commit", str(skill / "references/lessons/general.md"), str(skill / "SKILL.md"), "--skill-dir", str(skill),
                "--trigger", "repeated-workaround", "--date", "2026-09-14", "--investigation", ".drive/investigations/2026-09-14-x.md",
                "--dedupe", "distinct", "--auditor-model", "claude-fable-5-1", "--check", "the workaround ledger", "--project", "proj",
                "--run", "session-auth"]
        original = (skill / "SKILL.md").read_text()
        with_rule = original.replace("- rule 2\n", "- rule 2\n- diagnose a repeated workaround before applying it\n")
        self.write(skill, "SKILL.md", with_rule.replace("# drive\n", "# drive, the core text a lesson must not touch\n"))
        refused = self.run_drive(*args)
        self.assertEqual(refused.returncode, 1, refused.stdout)
        self.assertIn("changes outside", refused.stdout)
        self.assertEqual(self.git(repo, "log", "--format=%s", "-1"), "skill: seed")
        self.write(skill, "SKILL.md", with_rule)
        result = self.run_drive(*args)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(sorted(self.git(repo, "show", "--name-only", "--format=", "HEAD").splitlines()),
                         ["skill/SKILL.md", "skill/references/lessons/general.md"])

    def test_lesson_commit_refuses_when_check_fails(self):
        repo, skill = self.skill_repo()
        with open(skill / "references/lessons/general.md", "a") as handle:
            handle.write("\n### An incomplete rule about caches\n- When: always.\n")
        result = self.run_drive("lesson-commit", str(skill / "references/lessons/general.md"), "--skill-dir", str(skill),
                                "--trigger", "t", "--investigation", "i", "--dedupe", "distinct", "--auditor-model", "claude-fable-5-1",
                                "--check", "none", "--project", "p", "--run", "r")
        self.assertEqual(result.returncode, 1)
        self.assertIn("lesson-check fails", result.stdout)
