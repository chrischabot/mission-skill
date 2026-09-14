"""drive.py freeze and the guard's freeze enforcement, including the cases ported from mission's protect-frozen.sh self-test."""
import json

from helpers import DRIVE, SKILL, DriveTestCase, drive

KEY = "expired-token-is-rejected"
ORIGINAL_TEST = "it('rejects expired tokens', () => { expect(check(token, now)).toBe(false) })\n"


class FreezeFixture:
    def frozen_repo(self):
        repo = self.make_run()
        self.write(repo, "tests/acceptance/a.test.ts", ORIGINAL_TEST)
        self.write(repo, "playwright.config.ts", "export default { retries: 0 }\n")
        self.write(repo, "src/app.ts", "export const x = 1\n")
        result = self.run_drive("freeze", "add", "tests/acceptance", "playwright.config.ts", cwd=repo)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return repo

    def call(self, repo, tool, agent=None, agent_id=None, env=None, **tool_input):
        payload = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input, "cwd": str(repo),
                   "session_id": "s-freeze", "tool_use_id": "t-freeze"}
        if agent:
            payload["agent_type"] = agent
            payload["agent_id"] = agent_id or "agent-freeze"
        return self.run_drive("hook-guard", stdin=json.dumps(payload), env=env).returncode

    def sh(self, repo, command, agent=None):
        return self.call(repo, "Bash", agent=agent, command=command)

    def check(self, repo, *extra):
        return self.run_drive("freeze", "check", *extra, cwd=repo)


class ProtectFrozenPortTests(FreezeFixture, DriveTestCase):
    """The protect-frozen.sh self-test cases, adapted to drive's paths (a frozen directory instead of a glob)."""

    def test_tool_calls(self):
        repo = self.frozen_repo()
        root = str(repo)
        cases = [
            (2, "Write to frozen test (absolute path)", "Write", {"file_path": root + "/tests/acceptance/a.test.ts", "content": "x"}),
            (2, "Edit frozen test (relative path)", "Edit", {"file_path": "tests/acceptance/a.test.ts", "old_string": "a", "new_string": "b"}),
            (2, "MultiEdit frozen config", "MultiEdit", {"file_path": root + "/playwright.config.ts"}),
            (2, "NotebookEdit under frozen dir", "NotebookEdit", {"notebook_path": root + "/tests/acceptance/n.ipynb"}),
            (2, "Write always-protected frozen.txt", "Write", {"file_path": root + "/.drive/frozen.txt", "content": "x"}),
            (2, "Write always-protected manifest", "Write", {"file_path": root + "/.drive/frozen.sha256", "content": "x"}),
            (0, "Edit source file", "Edit", {"file_path": root + "/src/app.ts", "old_string": "a", "new_string": "b"}),
            (0, "Write unit test (not frozen)", "Write", {"file_path": root + "/tests/unit/b.test.ts", "content": "x"}),
            (0, "Write outside project", "Write", {"file_path": str(self.scratch / "elsewhere.txt"), "content": "x"}),
            (0, "Read tool on frozen path", "Read", {"file_path": root + "/tests/acceptance/a.test.ts"}),
        ]
        for want, description, tool, tool_input in cases:
            with self.subTest(description):
                self.assertEqual(self.call(repo, tool, **tool_input), want, description)

    def test_shell_commands(self):
        repo = self.frozen_repo()
        cases = [
            (2, "echo x >> tests/acceptance/a.test.ts"), (2, "echo x>tests/acceptance/a.test.ts"),
            (2, "sed -i 's/a/b/' tests/acceptance/a.test.ts"), (2, "perl -pi -e 's/2/9/' playwright.config.ts"),
            (2, "printf x | tee -a tests/acceptance/a.test.ts"), (2, "rm -rf tests"), (2, "rm tests/acceptance/*.ts"),
            (2, "mv tests/acceptance/a.test.ts {}/a.ts".format(self.scratch)), (2, "cp {}/x.ts tests/acceptance/a.test.ts".format(self.scratch)),
            (2, "git checkout HEAD~1 -- tests/acceptance/a.test.ts"), (2, "git restore tests/acceptance"),
            (2, "git -C tests rm acceptance/a.test.ts"), (2, "cd tests && rm -f acceptance/a.test.ts"),
            (2, "bash -c 'rm tests/acceptance/a.test.ts'"), (2, "find tests -name '*.ts' -delete"),
            (2, "FOO=1 truncate -s 0 tests/acceptance/a.test.ts"),
            (0, "cat tests/acceptance/a.test.ts"),
            (0, "npx vitest run tests/acceptance --reporter=json > .drive/local/vitest.json 2>&1"),
            (0, "cp tests/acceptance/a.test.ts {}/copy.ts".format(self.scratch)), (0, "ls tests 2>/dev/null"),
            (0, "git checkout -- src/app.ts"), (0, "rm -rf node_modules .drive/local/tmp/run1"),
            (0, "python3 {} freeze add tests/regression".format(DRIVE)), (0, "find tests -name '*.ts' -exec cat {} ;"),
        ]
        for want, command in cases:
            with self.subTest(command=command):
                self.assertEqual(self.sh(repo, command), want, command)

    def test_invalid_hook_input_fails_closed_while_a_run_is_active(self):
        repo = self.frozen_repo()
        self.assertEqual(self.run_drive("hook-guard", stdin="not json", env={"CLAUDE_PROJECT_DIR": str(repo)}).returncode, 2)
        self.assertEqual(self.run_drive("hook-guard", stdin="not json").returncode, 0)

    def test_no_environment_variable_bypasses_the_freeze(self):
        repo = self.frozen_repo()
        payload = json.dumps({"tool_name": "Write", "cwd": str(repo),
                              "tool_input": {"file_path": str(repo / "tests/acceptance/a.test.ts"), "content": "x"}})
        for name in ("MISSION_FROZEN_BYPASS", "DRIVE_FROZEN_BYPASS", "DRIVE_FORCE"):
            with self.subTest(name=name):
                self.assertEqual(self.run_drive("hook-guard", stdin=payload, env={name: "1"}).returncode, 2)

    def test_without_a_frozen_list_the_same_write_is_allowed(self):
        repo = self.frozen_repo()
        (repo / ".drive/frozen.txt").unlink()
        self.assertEqual(self.call(repo, "Write", file_path=str(repo / "tests/acceptance/a.test.ts"), content="x"), 0)


class FreezeEnforcementTests(FreezeFixture, DriveTestCase):
    def test_every_role_and_the_main_thread_are_held_off_frozen_files(self):
        repo = self.frozen_repo()
        target = str(repo / "tests/acceptance/a.test.ts")
        for agent in (None, "drive:implementer", "drive:writer", "drive:severe-tester", "drive:investigator", "drive:architect",
                      "drive:verifier", "drive:ui-reviewer", "general-purpose"):
            with self.subTest(agent=agent):
                self.assertEqual(self.call(repo, "Write", agent=agent, file_path=target, content="x"), 2)
                self.assertEqual(self.sh(repo, "echo x >> tests/acceptance/a.test.ts", agent=agent), 2)

    def test_git_stash_reset_clean_apply_patch_and_inline_code_cannot_touch_frozen_tests(self):
        repo = self.frozen_repo()
        self.write(repo, "change.diff", "--- a/tests/acceptance/a.test.ts\n+++ b/tests/acceptance/a.test.ts\n@@ -1 +1 @@\n-x\n+y\n")
        self.write(repo, "other.diff", "--- a/src/app.ts\n+++ b/src/app.ts\n@@ -1 +1 @@\n-x\n+y\n")
        blocked = ["git stash -u", "git stash", "git reset --hard", "git clean -fdx", "git apply change.diff", "patch -p1 < change.diff",
                   "python3 -c \"open('tests/acceptance/a.test.ts', 'w').write('')\"",
                   "node -e \"require('fs').writeFileSync('playwright.config.ts', '')\""]
        for agent in (None, "drive:implementer", "drive:investigator"):
            for command in blocked:
                with self.subTest(agent=agent, command=command):
                    self.assertEqual(self.sh(repo, command, agent=agent), 2)
        for command in ("git apply --check change.diff", "git apply other.diff", "git stash list", "git clean -n"):
            with self.subTest(command=command):
                self.assertEqual(self.sh(repo, command), 0)

    def test_drive_py_hooks_json_and_the_manifest_are_protected_from_everyone(self):
        repo = self.frozen_repo()
        for agent in (None, "drive:implementer", "drive:severe-tester", "general-purpose"):
            with self.subTest(agent=agent):
                self.assertEqual(self.call(repo, "Edit", agent=agent, file_path=str(SKILL / "scripts" / "drive.py"), old_string="a",
                                           new_string="b"), 2)
                self.assertEqual(self.call(repo, "Write", agent=agent, file_path=str(SKILL / "hooks" / "hooks.json"), content="{}"), 2)
                self.assertEqual(self.sh(repo, "echo '{{}}' > {}".format(SKILL / "hooks" / "hooks.json"), agent=agent), 2)
                self.assertEqual(self.sh(repo, "sed -i 's/a/b/' .drive/frozen.sha256", agent=agent), 2)

    def test_only_a_severe_tester_under_an_open_amendment_may_change_a_frozen_test(self):
        repo = self.make_run()
        self.assertEqual(self.run_drive("freeze", "add", "tests/test_auth.py", cwd=repo).returncode, 0)
        target = str(repo / "tests/test_auth.py")

        def tester():
            return self.call(repo, "Edit", agent="drive:severe-tester", agent_id="s-1", file_path=target, old_string="a", new_string="b")
        self.assertEqual(tester(), 2)
        self.assertEqual(self.run_drive("freeze", "amend", "--open", KEY, cwd=repo).returncode, 1)
        self.write(repo, ".drive/reviews/2026-09-14-dispute-{}.md".format(KEY), "# Dispute · {}\nRuling: not_a_defect\n".format(KEY))
        self.assertEqual(self.run_drive("freeze", "amend", "--open", KEY, cwd=repo).returncode, 1)
        with open(repo / ".drive/DECISIONS.md", "a", encoding="utf-8") as handle:
            handle.write("\n## 2026-09-14 · Amend the frozen test for {}\n- Decision: amend it after the not_a_defect ruling.\n"
                         "- Undo: restore the test from git · reversal cost: low.\n".format(KEY))
        opened = self.run_drive("freeze", "amend", "--open", KEY, cwd=repo)
        self.assertEqual(opened.returncode, 0, opened.stdout)
        self.assertEqual(tester(), 0)
        self.assertEqual(self.call(repo, "Edit", agent="drive:implementer", agent_id="i-1", file_path=target, old_string="a",
                                   new_string="b"), 2)
        self.assertEqual(self.sh(repo, "sed -i 's/a/b/' tests/test_auth.py"), 2)
        self.write(repo, "tests/test_auth.py", (repo / "tests/test_auth.py").read_text() + "\ndef test_amended():\n    'amended'\n")
        self.assertEqual(self.check(repo).returncode, 1)
        closed = self.run_drive("freeze", "amend", KEY, "--close", cwd=repo)
        self.assertEqual(closed.returncode, 0, closed.stdout)
        self.assertEqual(self.check(repo).returncode, 0, self.check(repo).stdout)
        self.assertEqual(tester(), 2)


class FreezeCommandTests(FreezeFixture, DriveTestCase):
    def test_add_records_the_list_the_manifest_and_the_ledger_and_never_rehashes(self):
        repo = self.frozen_repo()
        self.assertEqual((repo / ".drive/frozen.txt").read_text().split(), ["tests/acceptance", "playwright.config.ts"])
        manifest = drive.frozen_manifest(repo)
        self.assertEqual(sorted(manifest), ["playwright.config.ts", "tests/acceptance/a.test.ts"])
        recorded = {(e["path"], e["sha256"]) for e in drive.ledger_entries(repo, "frozen")}
        self.assertTrue(all((p, h) in recorded for p, h in manifest.items()))
        self.assertEqual(self.run_drive("freeze", "add", "playwright.config.ts", cwd=repo).returncode, 0)
        self.write(repo, "playwright.config.ts", "export default { retries: 5 }\n")
        again = self.run_drive("freeze", "add", "playwright.config.ts", cwd=repo)
        self.assertEqual(again.returncode, 1)
        self.assertIn("never rehashes", again.stdout)
        self.assertEqual(self.run_drive("freeze", "add", "--force", "playwright.config.ts", cwd=repo).returncode, 2)

    def test_check_reports_changed_missing_added_and_unrecorded_files(self):
        repo = self.frozen_repo()
        self.assertEqual(self.check(repo).returncode, 0)
        path = repo / "tests/acceptance/a.test.ts"
        path.write_text("it.skip('rejects expired tokens', () => {})\n")
        self.assertIn("CHANGED tests/acceptance/a.test.ts", self.check(repo).stdout)
        path.unlink()
        self.assertIn("MISSING tests/acceptance/a.test.ts", self.check(repo).stdout)
        path.write_text(ORIGINAL_TEST)
        self.write(repo, "tests/acceptance/b.test.ts", "it('passes', () => {})\n")
        self.assertIn("ADDED tests/acceptance/b.test.ts", self.check(repo).stdout)
        (repo / "tests/acceptance/b.test.ts").unlink()
        self.write(repo, "playwright.config.ts", "export default { retries: 7 }\n")
        manifest = drive.frozen_manifest(repo)
        manifest["playwright.config.ts"] = drive.file_sha256(repo / "playwright.config.ts")
        drive.write_manifest(repo, manifest)
        result = self.check(repo)
        self.assertEqual(result.returncode, 1)
        self.assertIn("UNRECORDED playwright.config.ts", result.stdout)

    def test_check_against_a_base_reports_a_path_quietly_dropped_from_the_freeze(self):
        repo = self.frozen_repo()
        base = self.commit(repo, "test: land the frozen tests")
        (repo / ".drive/frozen.txt").write_text("tests/acceptance\n")
        manifest = drive.frozen_manifest(repo)
        del manifest["playwright.config.ts"]
        drive.write_manifest(repo, manifest)
        self.assertEqual(self.check(repo).returncode, 0)
        result = self.check(repo, "--base", base)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("REMOVED playwright.config.ts", result.stdout)

    def test_park_and_unpark_move_a_claims_frozen_tests_and_refuse_a_changed_file(self):
        repo = self.make_run()
        self.assertEqual(self.run_drive("freeze", "add", "tests/test_auth.py", cwd=repo).returncode, 0)
        original = (repo / "tests/test_auth.py").read_text()
        parked = self.run_drive("freeze", "park", KEY, cwd=repo)
        self.assertEqual(parked.returncode, 0, parked.stdout)
        copy = repo / ".drive/local/frozen-parked" / KEY / "tests/test_auth.py"
        self.assertFalse((repo / "tests/test_auth.py").exists())
        self.assertTrue(copy.is_file())
        self.assertEqual(self.check(repo).returncode, 0, self.check(repo).stdout)
        copy.write_text(original + "# edited while parked\n")
        refused = self.run_drive("freeze", "unpark", KEY, cwd=repo)
        self.assertEqual(refused.returncode, 1)
        self.assertIn("changed since it was frozen", refused.stdout)
        copy.write_text(original)
        self.assertEqual(self.run_drive("freeze", "unpark", KEY, cwd=repo).returncode, 0)
        self.assertEqual((repo / "tests/test_auth.py").read_text(), original)

    def test_lint_fails_on_a_changed_frozen_file(self):
        repo = self.frozen_repo()
        self.assertNoFailure(self.lint(repo), "frozen")
        self.write(repo, "playwright.config.ts", "export default { retries: 9 }\n")
        self.assertFails(self.lint(repo), "CHANGED playwright.config.ts")


class FrozenPatchTests(FreezeFixture, DriveTestCase):
    """Adversarial review low 27: a patch that renames a frozen test, or changes only its mode, carries no ---/+++ lines."""

    def test_a_patch_that_only_renames_or_changes_the_mode_of_a_frozen_test_is_refused(self):
        repo = self.frozen_repo()
        self.write(repo, "rename.diff", "diff --git a/tests/acceptance/a.test.ts b/tests/unit/a.test.ts\nsimilarity index 100%\n"
                                        "rename from tests/acceptance/a.test.ts\nrename to tests/unit/a.test.ts\n")
        self.write(repo, "mode.diff", "diff --git a/tests/acceptance/a.test.ts b/tests/acceptance/a.test.ts\nold mode 100644\nnew mode 100755\n")
        self.write(repo, "other.diff", "diff --git a/src/app.ts b/src/moved.ts\nsimilarity index 100%\nrename from src/app.ts\nrename to src/moved.ts\n")
        for command in ("git apply rename.diff", "git apply --index mode.diff", "git am rename.diff"):
            with self.subTest(command=command):
                self.assertEqual(self.sh(repo, command), 2)
        self.assertEqual(self.sh(repo, "git apply other.diff"), 0)

    def test_a_patch_the_guard_cannot_read_is_refused_while_tests_are_frozen(self):
        repo = self.frozen_repo()
        self.write(repo, "big.diff", "diff --git a/src/app.ts b/src/app.ts\n" + "+x\n" * 400000)
        for command in ("git apply big.diff", "git apply missing.diff", "patch -p1 < big.diff"):
            with self.subTest(command=command):
                self.assertEqual(self.sh(repo, command), 2)
