"""Severe tests for the review of the adversarial-review fixes (research/37-fix-review.md).

Each class names the finding it covers. Every test drives the real path (hook-guard, hook-stop, hook-snapshot, drive.py
end, install.sh), and each failed against drive.py and install.sh as they stood before these fixes."""
import hashlib
import os
import subprocess

from helpers import DriveTestCase, SKILL, drive, goal_md
from test_adversarial_review import MARKDOWN_BODY, REVIEW_PATHS, Hooks

REVIEW = ".drive/reviews/2026-09-14-notes.md"


class HereStringTests(Hooks, DriveTestCase):
    """H1: a here-string is not a heredoc, so the lines after it are still judged."""

    def setUp(self):
        super().setUp()
        self.repo = self.make_run()

    def test_a_refused_command_on_the_line_after_a_here_string_is_refused(self):
        cases = [(None, "read x <<< \"$y\"\ngit checkout -b feature"), (None, "cat <<< hi\ngit push origin main"),
                 ("drive:verifier", "grep -c x <<<\"hi\"\ngit push origin main"),
                 ("general-purpose", "wc -l <<< hi\nrm .drive/local/active")]
        for agent, command in cases:
            with self.subTest(agent=agent, command=command):
                self.assertBlocked(self.bash(self.repo, command, agent=agent))

    def test_a_here_string_followed_by_a_harmless_line_is_allowed(self):
        self.assertAllowed(self.bash(self.repo, "cat <<< hi\necho ok"))
        self.assertAllowed(self.bash(self.repo, "grep -c x <<< \"hi\"\nwc -l README.md", agent="drive:verifier"))


class StdinScriptTests(Hooks, DriveTestCase):
    """H2: a heredoc, here-string, or file a shell or interpreter reads on standard input is judged as the code it is."""

    def setUp(self):
        super().setUp()
        self.repo = self.make_run()

    def test_a_heredoc_fed_to_a_shell_is_judged_as_a_script(self):
        for agent, command in ((None, "sh <<'EOF'\ngit push origin main\nEOF"),
                               (None, "bash -s <<'EOF'\ngit checkout -b feature\nEOF"),
                               (None, "cat <<'EOF' | bash\ngit reset --hard HEAD~1\nEOF"),
                               (None, "zsh <<EOF\ngit push origin main\nEOF"),
                               ("general-purpose", "bash <<'EOF'\nrm .drive/local/active\nEOF"),
                               ("drive:verifier", "bash <<'EOF'\ngit commit -am x\nEOF"),
                               ("drive:verifier", "cat <<'EOF' | sh -s\ngit commit -am x\nEOF"),
                               ("drive:implementer", "bash -o pipefail <<'EOF'\ngit commit -am x\nEOF"),
                               (None, "bash <<< 'git push origin main'")):
            with self.subTest(agent=agent, command=command):
                self.assertBlocked(self.bash(self.repo, command, agent=agent))

    def test_a_shell_heredoc_from_an_outside_agent_is_judged_as_bash_c_would_be(self):
        for command in ("bash -c 'git push origin main'", "bash <<'EOF'\ngit push origin main\nEOF"):
            with self.subTest(command=command):
                self.assertBlocked(self.bash(self.repo, command, agent="general-purpose"))
        # An outside-roster subagent keeps the main thread's rules, under which a commit is allowed in every spelling.
        for command in ("git commit -am x", "bash -c 'git commit -am x'", "bash <<'EOF'\ngit commit -am x\nEOF"):
            with self.subTest(command=command):
                self.assertAllowed(self.bash(self.repo, command, agent="general-purpose"))

    def test_a_heredoc_fed_to_an_interpreter_gets_the_inline_code_analysis(self):
        for command in ("node - <<'JS'\nrequire('fs').writeFileSync('src/auth.py','x')\nJS",
                        "python3 - <<'PY'\nopen('src/auth.py','w').write('x')\nPY",
                        "python3 <<'PY'\nopen('src/auth.py','w').write('x')\nPY",
                        "cat <<'PY' | python3 -\nimport subprocess\nPY",
                        "ruby - <<'RB'\nFile.write('src/auth.py', 'x')\nRB",
                        "perl - <<'PL'\nunlink 'src/auth.py'\nPL"):
            with self.subTest(command=command):
                self.assertBlocked(self.bash(self.repo, command, agent="drive:verifier"))
        self.assertAllowed(self.bash(self.repo, "python3 - <<'PY'\nimport json\nprint(json.dumps({'a': 1}))\nPY", agent="drive:verifier"))
        self.assertBlocked(self.bash(self.repo, "python3 - <<'PY'\nimport subprocess\nsubprocess.run(['git', 'push'])\nPY",
                                     agent="drive:implementer"))

    def test_a_file_redirected_into_a_shell_is_judged_as_a_script(self):
        self.write(self.repo, "run.sh", "git push origin main\n")
        self.write(self.repo, "ok.sh", "echo hello\n")
        for agent in (None, "drive:verifier"):
            with self.subTest(agent=agent):
                self.assertBlocked(self.bash(self.repo, "bash < run.sh", agent=agent))
                self.assertBlocked(self.bash(self.repo, "sh 0< run.sh", agent=agent))
        self.assertBlocked(self.bash(self.repo, "bash < missing.sh"), "cannot read")
        self.assertAllowed(self.bash(self.repo, "bash < ok.sh"))
        self.assertAllowed(self.bash(self.repo, "bash run.sh --help < /dev/null".replace("run.sh", "ok.sh")))

    def test_harmless_shell_heredocs_and_reviewer_writes_stay_allowed(self):
        self.assertAllowed(self.bash(self.repo, "bash <<'EOF'\necho hello\nls src\nEOF"))
        self.assertAllowed(self.bash(self.repo, "cat <<'EOF' | sh\nls\nEOF"))
        self.assertAllowed(self.bash(self.repo, "bash scripts/none.sh <<'EOF'\ngit push origin main\nEOF", agent="drive:implementer"))
        for agent, path in REVIEW_PATHS.items():
            for command in ("cat > {} <<'EOF'\n{}\nEOF".format(path, MARKDOWN_BODY), "tee {} <<'EOF'\n{}\nEOF".format(path, MARKDOWN_BODY),
                            "cat <<'EOF' > {}\nrm -rf /\ngit push origin main\nEOF".format(path)):
                with self.subTest(agent=agent, command=command[:30]):
                    self.assertAllowed(self.bash(self.repo, command, agent=agent))


class SubstitutionHeredocTests(Hooks, DriveTestCase):
    """M1: a heredoc inside $(...) is skipped as a heredoc, so its apostrophes and parentheses hide nothing."""

    def setUp(self):
        super().setUp()
        self.repo = self.make_run()

    def test_the_commit_message_form_does_not_hide_a_following_push(self):
        for command in ("git commit -m \"$(cat <<'EOF'\nfix: don't\nEOF\n)\" && git push origin main",
                        "git commit -m \"$(cat <<'EOF'\nfix (see #3\nEOF\n)\" && git push origin main",
                        "git commit -m \"$(cat <<'EOF'\nfix: don't\nEOF\n)\"\ngit push origin main"):
            with self.subTest(command=command):
                self.assertBlocked(self.bash(self.repo, command), "git push")

    def test_the_commit_message_form_without_a_push_is_allowed(self):
        self.assertAllowed(self.bash(self.repo, "git commit -m \"$(cat <<'EOF'\nfix: don't\n\nCo-Authored-By: x\nEOF\n)\""))
        self.assertAllowed(self.bash(self.repo, "git commit -m \"$(cat <<'EOF'\nfix (see #3\nEOF\n)\""))


class StopTokenWordingTests(Hooks, DriveTestCase):
    """M2, M3, L5, L1: credentials:, budget:, and Abort need the words the rule names, not a mention."""

    def blocked(self, repo, blocked_on):
        self.set_state(repo, commit=self.code_sha, status="blocked", blocked=blocked_on)
        self.write(repo, ".drive/REPORT.md", self.report_md({}, outcome="Stopped because the owner must act."))
        return self.stop(repo)

    def test_credentials_refuses_words_that_name_no_secret(self):
        repo = self.make_run()
        for blocked_on in ("credentials: NONE", "credentials: TBD", "credentials: TODO", "credentials: API access",
                           "credentials: the AWS account", 'credentials: " "', "credentials: 'x'", "credentials: `?`",
                           'credentials: "N/A"', "credentials: `unknown`", "credentials: none needed",
                           "credentials: owner's key", "credentials: github_token", "credentials: `x`"):
            with self.subTest(blocked_on=blocked_on):
                self.assertIn("must name the secret", self.blocked(repo, blocked_on)["reason"])
        for blocked_on in ("credentials: CLOUDFLARE_API_TOKEN", "credentials: GITHUB_PAT", 'credentials: "Apple notarization password"',
                           "credentials: the `stripe live key` in the vault", "credentials: STRIPE_SECRET for billing"):
            with self.subTest(blocked_on=blocked_on):
                self.assertIsNone(self.blocked(repo, blocked_on))

    def test_budget_refuses_a_decision_that_only_mentions_the_budget(self):
        repo = self.make_run()
        self.append_decision(repo, "Keep going", "continue; the budget is fine.")
        self.assertIn("counts only once", self.blocked(repo, "budget: done enough")["reason"])
        self.append_decision(repo, "Narrow to the token check", "Narrow the run to the token check; the budget no longer covers the admin screen.")
        self.assertIsNone(self.blocked(repo, "budget: done enough"))

    def test_a_budget_stop_that_reuses_an_intake_heading_counts(self):
        repo = self.make_run()
        # Re-anchor intake after DECISIONS.md holds "Compare tokens in constant time".
        self.git(repo, "commit", "-q", "--allow-empty", "-m", "drive(intake): session-auth")
        self.append_decision(repo, "Compare tokens in constant time", "stop; the budget no longer covers more.")
        self.assertIsNone(self.blocked(repo, "budget: done enough"))

    def test_a_budget_decision_present_at_intake_still_does_not_count(self):
        repo = self.make_run()
        self.append_decision(repo, "Stop early", "stop; the budget no longer covers more.")
        self.commit(repo, "drive(intake): session-auth")
        self.assertIn("counts only once", self.blocked(repo, "budget: done enough")["reason"])

    def test_abort_refuses_a_negation_and_accepts_abort_with_punctuation(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha, status="aborted")
        self.write(repo, ".drive/REPORT.md", self.report_md({}, outcome="Stopped because the owner cancelled the migration."))
        self.append_decision(repo, "Not needed", "Abort not needed; continue.")
        self.append_decision(repo, "Plan", "Abort-ish plan")
        self.assertIn("must begin with 'Abort' or 'Aborted'", self.stop(repo)["reason"])
        self.append_decision(repo, "End the migration", "Abort; the owner cancelled the migration.")
        self.assertIsNone(self.stop(repo))


class HeadRewriteTests(Hooks, DriveTestCase):
    """M4: while a run is active the main thread does not move HEAD by reset or update-ref in the shared checkout."""

    def test_reset_to_another_commit_and_update_ref_head_are_refused(self):
        repo = self.make_run()
        sha = self.git(repo, "rev-parse", "HEAD~1")
        for command in ("git reset HEAD~1", "git reset HEAD^", "git reset {}".format(sha), "git reset --soft HEAD~1",
                        "git reset --mixed HEAD~1", "git reset -q --soft HEAD~1 && git commit -m redo",
                        "git update-ref HEAD HEAD~1", "git update-ref -m x HEAD {}".format(sha)):
            with self.subTest(command=command):
                self.assertBlocked(self.bash(repo, command), "rewrites HEAD")

    def test_index_only_resets_and_scratch_copies_stay_allowed(self):
        repo = self.make_run()
        copy = self.scratch / "drive-proj-copy"
        for command in ("git reset", "git reset HEAD", "git reset -q", "git reset -- src/auth.py", "git reset HEAD -- src/auth.py",
                        "git reset src/auth.py", "git -C {} reset --soft HEAD~1".format(copy),
                        "git -C {} update-ref HEAD HEAD~1".format(copy)):
            with self.subTest(command=command):
                self.assertAllowed(self.bash(repo, command))


class MarkerDeleteTests(Hooks, DriveTestCase):
    """L2: deleting the run marker through an interpreter or rsync --delete is refused like rm."""

    def test_interpreter_and_rsync_deletes_of_the_marker_are_refused(self):
        repo = self.make_run()
        commands = ["python3 -c \"import os; os.remove('.drive/local/active')\"",
                    "python3 -c \"import os; os.unlink('.drive/local/baseline.json')\"",
                    "python3 -c \"import shutil; shutil.rmtree('.drive/local')\"",
                    "python3 -c \"from pathlib import Path; Path('.drive/local/active').unlink()\"",
                    "node -e \"require('fs').rmSync('.drive/local', {recursive: true})\"",
                    "node -e \"require('fs').unlinkSync('.drive/local/active')\"",
                    "node -e \"require('fs').rmdirSync('.drive/local')\"",
                    "rsync -a --delete /dev/null/ .drive/local/", "rsync -a --delete-after empty/ .drive/"]
        for agent in (None, "general-purpose"):
            for command in commands:
                with self.subTest(agent=agent, command=command):
                    # A delete of the whole folder names the first protected file it would take (as find -delete does).
                    self.assertBlocked(self.bash(repo, command, agent=agent), None if "rsync" in command else "run marker")
        for command in ("python3 -c \"import json; print(json.load(open('.drive/local/active')))\"",
                        "python3 -c \"import os; os.remove('build/out.txt')\"", "rsync -a --delete build/ dist/",
                        "rsync -a .drive/local/baseline.json {}/".format(self.scratch)):
            with self.subTest(allowed=command):
                self.assertAllowed(self.bash(repo, command))


class IndexTransitionTests(Hooks, DriveTestCase):
    """L3: staging an untracked file outside the hooks does not void; unstaging a tracked file does."""

    def test_staging_an_untracked_file_outside_the_hooks_does_not_void(self):
        repo = self.make_run()
        self.write(repo, "src/new.py", "x = 1\n")
        self.snap(repo, "start")
        self.git(repo, "add", "src/new.py")
        self.snap(repo, "stop")
        self.assertEqual(drive.ledger_entries(repo, "void"), [])
        self.assertIn("src/new.py", self.gate_log(repo))

    def test_removing_a_tracked_file_from_the_index_outside_the_hooks_voids(self):
        repo = self.make_run()
        self.snap(repo, "start")
        self.git(repo, "rm", "-q", "--cached", "README.md")
        self.snap(repo, "stop")
        voids = drive.ledger_entries(repo, "void")
        self.assertEqual(len(voids), 1)
        self.assertIn("README.md", voids[0]["detail"])


class DigitShaTests(DriveTestCase):
    """A short sha made only of digits with a leading zero stays the string it was written as."""

    def digit_commit(self, repo):
        """Write a real commit whose 7-character abbreviation is all digits and starts with 0; return that abbreviation."""
        tree = self.git(repo, "rev-parse", "HEAD^{tree}")
        parent = self.git(repo, "rev-parse", "HEAD")
        for number in range(200000):
            body = ("tree {}\nparent {}\nauthor Drive Test <t@example.invalid> 1700000000 +0000\n"
                    "committer Drive Test <t@example.invalid> 1700000000 +0000\n\nprobe {}\n").format(tree, parent, number).encode()
            sha = hashlib.sha1(b"commit " + str(len(body)).encode() + b"\0" + body).hexdigest()
            if sha[0] == "0" and sha[1:7].isdigit():
                written = subprocess.run(["git", "-C", str(repo), "hash-object", "-t", "commit", "-w", "--stdin"], input=body,
                                         capture_output=True, check=True).stdout.decode().strip()
                self.assertEqual(written, sha)
                return sha[:7]
        self.fail("no digit-only sha found")

    def test_the_parser_keeps_a_leading_zero_digit_run_as_a_string(self):
        block = drive.parse_yaml_block(["probe:", "  baseline_sha: 0970287", "  runs: 3", "flow: { baseline_sha: 0970287, n: 12 }"])
        self.assertEqual(block["probe"], {"baseline_sha": "0970287", "runs": 3})
        self.assertEqual(block["flow"], {"baseline_sha": "0970287", "n": 12})

    def test_lint_finds_a_baseline_commit_whose_short_sha_is_all_digits(self):
        repo = self.make_run()
        short = self.digit_commit(repo)
        for written in (short, '"{}"'.format(short)):
            with self.subTest(written=written):
                self.write(repo, ".drive/GOAL.md", goal_md("BASELINE").replace("baseline_sha: BASELINE", "baseline_sha: " + written))
                self.assertEqual(str(drive.Goal((repo / ".drive/GOAL.md").read_text()).probe()["baseline_sha"]), short)
                self.assertNoFailure(self.lint(repo), "baseline_sha")


FAKE_CLAUDE_NEXT_ENTRY = """#!/bin/sh
if [ "$1 $2" = "plugin list" ]; then
  printf 'Installed plugins:\\n\\n'
  printf '  \\342\\235\\257 drive@skills-dir\\n    Version: 0.1.0\\n    Scope: user\\n'
  printf '  \\342\\235\\257 other@mkt\\n    Version: 1.0.0\\n    Scope: user\\n    Status: \\342\\234\\224 enabled\\n'
fi
exit 0
"""


class InstallStatusTests(DriveTestCase):
    """L4: install.sh reads the Status line of drive's own entry, never the next plugin's."""

    def test_the_next_plugins_status_is_not_read_as_drives(self):
        folder = self.tmp / "bin"
        folder.mkdir()
        claude = folder / "claude"
        claude.write_text(FAKE_CLAUDE_NEXT_ENTRY)
        claude.chmod(0o755)
        env = dict(os.environ, PATH="{}:{}".format(folder, os.environ.get("PATH", "")), DRIVE_INSTALL_SKIP_TESTS="1",
                   HOME=str(self.home))
        result = subprocess.run(["bash", str(SKILL.parent / "install.sh")], capture_output=True, text=True, env=env, timeout=120)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertNotIn("is enabled", result.stdout)
        self.assertIn("not listed", result.stderr)


class LongLiteralTests(Hooks, DriveTestCase):
    """The linkkeeper run on 2026-09-15: a main-thread `python3 - <<'PY'` edit whose string literals were longer than a file
    name may be made the guard's path check raise OSError (ENAMETOOLONG), so a plain edit was refused as uncheckable."""

    def setUp(self):
        super().setUp()
        self.repo = self.make_run()

    def test_inline_code_with_a_literal_longer_than_a_file_name_is_judged_not_refused(self):
        long_text = "the end-to-end check is a fresh clone started with one documented command " * 6
        command = "python3 - <<'PY'\np = 'README.md'; s = open(p).read()\ns = s.replace('proj', '{}')\nprint(len(s))\nPY".format(long_text)
        result = self.bash(self.repo, command)
        self.assertAllowed(result)
        self.assertNotIn("could not check", result.stderr)

    def test_a_marker_delete_beside_a_long_literal_is_still_refused(self):
        long_text = "x" * 400
        command = "python3 - <<'PY'\nimport os\nnote = '{}'\nos.remove('.drive/local/active')\nPY".format(long_text)
        result = self.bash(self.repo, command)
        self.assertBlocked(result)
        self.assertNotIn("could not check", result.stderr)

    def test_inline_code_that_mentions_evidence_paths_points_at_the_edit_tool(self):
        command = ("python3 - <<'PY'\np = '.drive/GOAL.md'; s = open(p).read()\n"
                   "s = s.replace('- [ ] verify', '- [ ] verify · artifact: .drive/proofs/<key>/r<n>/verdict.json')\nPY")
        result = self.bash(self.repo, command)
        self.assertBlocked(result)
        self.assertIn("use the Edit tool", result.stderr)


class OverlongNameTests(Hooks, DriveTestCase):
    """The sibling routes to the same ENAMETOOLONG refusal: every place hook-guard asks the filesystem about a command word,
    a cd target, a git -C directory, or a code literal must answer "not found" for a name the OS rejects (a component over
    255 characters or a path of 1,024 bytes or more), so the command gets the verdict a short missing name gets."""

    ROLES = (None, "drive:implementer", "drive:verifier")
    LONG_NAME = "n" * 256
    LONG_PATH = "/".join(["d" * 100] * 10) + "/" + "f" * 20

    def setUp(self):
        super().setUp()
        self.repo = self.make_run()

    def assertSameVerdict(self, template, long_name, short_name):
        self.assertGreater(len(long_name.encode("utf-8")), 255)
        for agent in self.ROLES:
            with self.subTest(agent=agent):
                long_result = self.bash(self.repo, template.format(long_name), agent=agent)
                short_result = self.bash(self.repo, template.format(short_name), agent=agent)
                for result in (long_result, short_result):
                    self.assertIn(result.returncode, (0, 2), result.stderr)
                    self.assertNotIn("could not check", result.stderr)
                self.assertEqual(long_result.returncode, short_result.returncode,
                                 "long: {!r}; short: {!r}".format(long_result.stderr[:300], short_result.stderr[:300]))

    def test_a_heredoc_literal_longer_than_a_file_name(self):
        self.assertSameVerdict("python3 - <<'PY'\nx = '{}'\nprint(len(x))\nPY", self.LONG_NAME, "short-literal")

    def test_a_python_script_operand_longer_than_a_file_name(self):
        self.assertSameVerdict("python3 {}.py", self.LONG_NAME, "missing")

    def test_a_bash_script_operand_longer_than_a_file_name(self):
        self.assertSameVerdict("bash {}", self.LONG_NAME, "missing.sh")

    def test_a_makefile_operand_longer_than_a_file_name(self):
        self.assertSameVerdict("make -f {}", self.LONG_NAME, "missing.mk")

    def test_a_cd_target_longer_than_a_file_name_before_npm_test(self):
        self.assertSameVerdict("cd {} && npm test", self.LONG_NAME, "missing-dir")

    def test_a_git_directory_longer_than_a_file_name(self):
        self.assertSameVerdict("git -C {} status", self.LONG_NAME, "missing-dir")

    def test_a_relative_path_longer_than_path_max(self):
        self.assertEqual(len(self.LONG_PATH.encode("utf-8")), 1030)
        self.assertSameVerdict("cat {}", self.LONG_PATH, "missing-dir/missing.txt")


class FutureStateTimestampTests(DriveTestCase):
    """The linkkeeper run on 2026-09-15 wrote STATE.md `updated:` values hours ahead of the real clock, which the staleness
    check compares against the latest code commit, so a future value would hide a stale STATE.md."""

    def test_an_updated_time_ahead_of_the_clock_fails_the_lint(self):
        import datetime as dt
        import re
        repo = self.make_run()
        state = (repo / ".drive/STATE.md").read_text()
        future = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.write(repo, ".drive/STATE.md", re.sub(r"(?m)^updated: .*$", "updated: " + future, state, count=1))
        self.assertFails(self.lint(repo), "ahead of the clock")

    def test_an_updated_time_a_few_minutes_ahead_is_tolerated(self):
        import datetime as dt
        import re
        repo = self.make_run()
        state = (repo / ".drive/STATE.md").read_text()
        soon = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.write(repo, ".drive/STATE.md", re.sub(r"(?m)^updated: .*$", "updated: " + soon, state, count=1))
        self.assertNoFailure(self.lint(repo), "ahead of the clock")


class ReadOnlyProbeTests(Hooks, DriveTestCase):
    """The linkkeeper run on 2026-09-15: the design architect lost eight tool calls to refusals of read-only probes
    (an in-memory SQLite FTS5 check, sysconfig for the stdlib path, importlib.util.find_spec)."""

    def setUp(self):
        super().setUp()
        self.repo = self.make_run()

    def test_in_memory_sqlite_and_introspection_probes_are_allowed(self):
        for code in ["import sqlite3; c = sqlite3.connect(':memory:'); c.execute(\"create virtual table t using fts5(x, tokenize='trigram')\"); print('ok')",
                     "import sqlite3; print(sqlite3.sqlite_version)",
                     "from sqlite3 import connect; print(connect(':memory:').execute('select 1').fetchone())",
                     "import sysconfig; print(sysconfig.get_paths()['stdlib'])",
                     "import importlib.util as u; print(bool(u.find_spec('yaml')))",
                     "import platform; print(platform.python_version())"]:
            for agent in ("drive:architect", "drive:verifier"):
                with self.subTest(agent=agent, code=code):
                    self.assertAllowed(self.bash(self.repo, "python3 -c \"{}\"".format(code.replace('"', '\\"')), agent=agent))

    def test_sqlite_probes_that_could_write_a_file_are_refused(self):
        for code in ["import sqlite3; sqlite3.connect('notes.db').execute('create table t(x)')",
                     "import sqlite3; c = sqlite3.connect(':memory:'); c.execute(\"attach database 'x.db' as x\")",
                     "import sqlite3; c = sqlite3.connect(':memory:'); c.execute(\"vacuum into 'copy.db'\")",
                     "import sqlite3; c = sqlite3.connect(':memory:'); c.enable_load_extension(True)",
                     "import sqlite3; f = sqlite3.connect; f('x.db')",
                     "import sqlite3; sqlite3.connect('file:x.db', uri=True)",
                     "import importlib.util as u; s = u.spec_from_file_location('m', 'm.py')"]:
            with self.subTest(code=code):
                self.assertBlocked(self.bash(self.repo, "python3 -c \"{}\"".format(code.replace('"', '\\"')), agent="drive:architect"))


class ResearcherLedgerEditTests(Hooks, DriveTestCase):
    """The linkkeeper run on 2026-09-15: drive:researcher had Write but no Edit, so a lane rewrote the shared RESEARCH.md
    whole while other lanes write to it; the entries survived only by luck."""

    def setUp(self):
        super().setUp()
        self.repo = self.make_run()

    def test_the_researcher_can_edit_the_ledger_and_is_told_not_to_rewrite_it(self):
        text = (SKILL / "agents/researcher.md").read_text()
        tools = next(line for line in text.splitlines() if line.startswith("tools:"))
        self.assertIn("Edit", [t.strip() for t in tools.split(":", 1)[1].split(",")])
        self.assertIn("never rewrite the whole file with Write", text)
        self.assertAllowed(self.guard(self.repo, "Edit", agent="drive:researcher", file_path=str(self.repo / ".drive/RESEARCH.md"),
                                      old_string="a", new_string="b"))
        self.assertBlocked(self.guard(self.repo, "Edit", agent="drive:researcher", file_path=str(self.repo / "README.md"),
                                      old_string="a", new_string="b"))
