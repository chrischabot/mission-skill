"""Severe tests for defects live drive runs found on 2026-09-15.

Each class names the defect it covers. Every test drives the real path (drive.py lint, hook-guard, and hook-snapshot as
subprocesses),
and each class holds tests that fail against drive.py as it stood before the fix."""
import json
from pathlib import Path

from helpers import SKILL, DriveTestCase, drive, proof_manifest, verdict

KEY = "expired-token-is-rejected"
LIST = "session-list-shows-active-sessions"
PLANNED = "planned:tests/test_admin.py::admin revokes a session"


class Cli:
    """Subprocess helpers (not itself a TestCase)."""

    def lint_cli(self, repo, *flags):
        result = self.run_drive("lint", *flags, cwd=repo)
        self.assertIn(result.returncode, (0, 1), result.stderr)
        return [line for line in result.stdout.splitlines() if line.startswith("FAIL ")]

    def failing(self, lines, *fragments):
        return [line for line in lines if all(fragment in line for fragment in fragments)]

    def snap(self, repo, phase, agent_id, agent="drive:verifier", transcript=None):
        payload = {"hook_event_name": "SubagentStart" if phase == "start" else "SubagentStop", "cwd": str(repo),
                   "agent_id": agent_id, "agent_type": agent}
        if transcript is not None:
            payload["agent_transcript_path"] = str(transcript)
        result = self.run_drive("hook-snapshot", phase, stdin=json.dumps(payload))
        self.assertEqual(result.returncode, 0, result.stderr)

    def gate_log(self, repo):
        path = Path(repo) / ".drive/local/gate.log"
        return path.read_text() if path.exists() else ""


class PlannedDuringBuildTests(Cli, DriveTestCase):
    """Defect 1: a Missing row's planned: token failed in every phase after decompose, though its test is not written
    until later in the build."""

    RULE = "planned: tests are allowed only"

    def plan_missing_row(self, repo):
        text = (repo / ".drive/STATUS.md").read_text().replace("| Missing |  |", "| Missing | {} |".format(PLANNED))
        self.write(repo, ".drive/STATUS.md", text)

    def test_a_row_below_partial_may_stay_planned_through_build_verify_and_integrate(self):
        repo = self.make_run()
        self.plan_missing_row(repo)
        for phase in ("build", "verify", "integrate", "live-proof", "fix", "draft", "execute", "test-plan"):
            with self.subTest(phase=phase):
                self.set_state(repo, phase=phase)
                self.assertEqual(self.failing(self.lint_cli(repo), self.RULE), [])

    def test_a_partial_row_with_a_planned_token_still_fails_during_build(self):
        repo = self.make_run()
        text = (repo / ".drive/STATUS.md").read_text().replace(
            "test:tests/test_auth.py::session list shows active sessions;",
            "test:tests/test_auth.py::session list shows active sessions; {};".format(PLANNED))
        self.write(repo, ".drive/STATUS.md", text)
        found = self.failing(self.lint_cli(repo), LIST, self.RULE)
        self.assertEqual(len(found), 1, found)
        self.assertIn("a Partial row", found[0])
        self.assertIn("Replace them with test: once the test exists", found[0])

    def test_a_planned_token_fails_in_harden_and_every_phase_after_the_tests_exist(self):
        repo = self.make_run()
        self.plan_missing_row(repo)
        for phase in ("harden", "docs", "retro", "report", "cutover", "soak", "decommission", "design-qa", "deploy", "observe"):
            with self.subTest(phase=phase):
                self.set_state(repo, phase=phase)
                found = self.failing(self.lint_cli(repo), "admin-can-revoke-sessions", self.RULE)
                self.assertEqual(len(found), 1, found)
                self.assertIn("the {} phase".format(phase), found[0])

    def test_a_planned_token_fails_at_lint_final_even_during_build(self):
        repo = self.make_run()
        self.plan_missing_row(repo)
        self.assertEqual(self.failing(self.lint_cli(repo), self.RULE), [])
        found = self.failing(self.lint_cli(repo, "--final"), "admin-can-revoke-sessions", self.RULE)
        self.assertEqual(len(found), 1, found)
        self.assertIn("lint --final", found[0])


class HandoffPerRoundTests(Cli, DriveTestCase):
    """Defect 2: a later round's handoff named <unit>-r<n>.md was refused, so a round could not keep earlier handoffs."""

    def handoff(self, repo, stem, round_field):
        text = (Path(drive.TEMPLATES) / "handoff.md").read_text().replace("<unit>", KEY).replace(
            "round: <n>/<K>", "round: {}".format(round_field))
        rel = ".drive/handoffs/{}.md".format(stem)
        self.write(repo, rel, text)
        return rel

    def naming_failures(self, lines, rel):
        return self.failing(lines, rel + ":", "is named for")

    def test_a_later_round_handoff_sits_beside_the_first_rounds(self):
        repo = self.make_run()
        (repo / ".drive/packages/export-api").mkdir(parents=True)
        first = self.handoff(repo, KEY, "1/3")
        second = self.handoff(repo, KEY + "-r2", "2/3")
        package = self.handoff(repo, "export-api-r3", "3/3")
        audit = self.handoff(repo, "final-audit-r2", "2/2")
        lines = self.lint_cli(repo)
        for rel in (first, second, package, audit):
            with self.subTest(handoff=rel):
                self.assertEqual(self.naming_failures(lines, rel), [])
                self.assertEqual(self.failing(lines, rel + ":", "round must be written"), [])

    def test_the_round_in_the_name_must_match_the_round_field(self):
        repo = self.make_run()
        rel = self.handoff(repo, KEY + "-r3", "2/3")
        found = self.naming_failures(self.lint_cli(repo), rel)
        self.assertEqual(len(found), 1, found)
        self.assertIn("round 3 but its round: field is 2/3", found[0])

    def test_an_unknown_unit_is_still_refused_with_or_without_a_round_suffix(self):
        repo = self.make_run()
        lines_for = {}
        for stem in ("no-such-claim", "no-such-claim-r2", KEY + "-rtwo", KEY + "-r"):
            lines_for[stem] = self.handoff(repo, stem, "2/3")
        lines = self.lint_cli(repo)
        for stem, rel in lines_for.items():
            with self.subTest(stem=stem):
                found = self.naming_failures(lines, rel)
                self.assertEqual(len(found), 1, found)
                self.assertIn("which is neither a STATUS key nor a package id", found[0])

    def test_a_status_key_that_itself_ends_in_a_round_suffix_is_its_own_unit(self):
        repo = self.make_run()
        text = (repo / ".drive/STATUS.md").read_text().replace("admin-can-revoke-sessions", "retry-after-r2")
        self.write(repo, ".drive/STATUS.md", text)
        rel = self.handoff(repo, "retry-after-r2", "1/3")
        self.assertEqual(self.naming_failures(self.lint_cli(repo), rel), [])


class CommandPlaceholderTests(Cli, DriveTestCase):
    """Defect 3: a verifier recorded a command with <scratch> in place of its temporary directory, then {scratch} to
    dodge the lint. Both are refused; real shell braces are not."""

    RAN_FILE = ".drive/proofs/{}/r2/verdict.json".format(KEY)

    def placeholder_failures(self, repo, cmd, rel=None):
        rel = rel or self.RAN_FILE
        if rel.endswith("proof.json"):
            manifest = proof_manifest(KEY)
            manifest["commands"].append({"cmd": cmd, "exit": 0, "output": "r1/live.md"})
            self.write(repo, rel, manifest)
        else:
            data = verdict(KEY, round_number=2)
            data["ran"].append({"cmd": cmd, "exit": 0, "seconds": 1, "output": "r2/refute.txt"})
            self.write(repo, rel, data)
        return self.failing(self.lint_cli(repo), rel + ":", "template placeholder")

    def test_an_angle_abbreviation_in_a_recorded_command_still_fails(self):
        repo = self.make_run()
        found = self.placeholder_failures(repo, "cd /repo && python3 -m pytest -q <scratch test_refute.py>")
        self.assertEqual(len(found), 1, found)
        self.assertIn("$.ran[1].cmd", found[0])

    def test_a_brace_abbreviation_in_a_recorded_command_fails_and_asks_for_the_real_path(self):
        repo = self.make_run()
        for cmd in ("cd /repo && python3 -m pytest -q -p no:cacheprovider {scratch}/test_refute.py",
                    "cp tests/x.py {scratch dir}/x.py", "ls {tmp_dir}"):
            with self.subTest(cmd=cmd):
                found = self.placeholder_failures(repo, cmd)
                self.assertEqual(len(found), 1, found)
                self.assertIn("$.ran[1].cmd", found[0])
                self.assertIn("real path", found[0])

    def test_a_brace_abbreviation_in_a_live_proof_command_fails(self):
        repo = self.make_run()
        found = self.placeholder_failures(repo, "curl -s {base_url}/session", rel=".drive/proofs/{}/proof.json".format(KEY))
        self.assertEqual(len(found), 1, found)
        self.assertIn("$.commands[1].cmd", found[0])

    def test_real_shell_braces_in_a_recorded_command_pass(self):
        repo = self.make_run()
        for cmd in ("find . -name '*.pyc' -exec rm {} \\;", "find . -name x -exec echo {} +",
                    "echo ${TMPDIR}/x && echo ${HOME}", "cp src/{auth,session}.py /tmp/x/",
                    "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/session",
                    "curl -s -d '{\"token\": \"expired\"}' http://localhost:8000/session",
                    "python3 -c 'print({1: 2})'", "cat tests/test_auth.py"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.placeholder_failures(repo, cmd), [])

    def test_the_reviewer_agents_that_record_commands_are_told_to_record_real_paths(self):
        for name in ("verifier", "ui-reviewer", "auditor"):
            with self.subTest(agent=name):
                text = " ".join((SKILL / "agents" / "{}.md".format(name)).read_text().split())
                self.assertIn("exactly as you ran it, with its real paths", text)
                self.assertIn("`<scratch>` or `{scratch}` reads as an unfilled template placeholder and fails the lint", text)


class SupersededRoundPlaceholderTests(Cli, DriveTestCase):
    """Defect 3, follow-up: a committed earlier round with a placeholder failed the lint forever, though a later round
    replaced it and historical evidence should not be rewritten to satisfy a lint."""

    def round_verdict(self, repo, key, number, cmd=None):
        data = verdict(key, round_number=number)
        if cmd:
            data["ran"].append({"cmd": cmd, "exit": 0, "seconds": 1, "output": "r{}/refute.txt".format(number)})
        rel = ".drive/proofs/{}/r{}/verdict.json".format(key, number)
        self.write(repo, rel, data)
        return rel

    def placeholder_failures(self, repo, rel):
        return self.failing(self.lint_cli(repo), rel + ":", "template placeholder")

    def test_an_uncited_earlier_round_with_a_placeholder_is_skipped_when_a_later_round_exists(self):
        repo = self.make_run()
        first = self.round_verdict(repo, LIST, 1, "pytest <scratch>/test_refute.py")
        second = self.round_verdict(repo, LIST, 2)
        lines = self.lint_cli(repo)
        self.assertEqual(self.failing(lines, first + ":", "template placeholder"), [])
        self.assertEqual(self.failing(lines, second + ":", "template placeholder"), [])

    def test_the_highest_round_with_a_placeholder_fails(self):
        repo = self.make_run()
        self.round_verdict(repo, LIST, 1)
        second = self.round_verdict(repo, LIST, 2, "pytest <scratch>/test_refute.py")
        self.assertEqual(len(self.placeholder_failures(repo, second)), 1)

    def test_an_earlier_round_a_status_row_cites_still_fails(self):
        repo = self.make_run()
        first = self.round_verdict(repo, KEY, 1, "pytest {scratch}/test_refute.py")
        self.round_verdict(repo, KEY, 2)
        self.assertIn("verdict:" + first, (repo / ".drive/STATUS.md").read_text())
        self.assertEqual(len(self.placeholder_failures(repo, first)), 1)

    def test_an_earlier_round_that_does_not_parse_still_fails(self):
        repo = self.make_run()
        first = ".drive/proofs/{}/r1/verdict.json".format(LIST)
        self.write(repo, first, "{not json\n")
        self.round_verdict(repo, LIST, 2)
        self.assertEqual(len(self.failing(self.lint_cli(repo), first + ":")), 1)

    def test_reviews_json_is_checked_whatever_the_rounds(self):
        repo = self.make_run()
        rel = ".drive/reviews/2026-09-14-final-audit.json"
        data = verdict("final-audit", claims=[KEY])
        data["ran"].append({"cmd": "pytest {scratch}/x.py", "exit": 0})
        self.write(repo, rel, data)
        self.round_verdict(repo, KEY, 2)
        self.assertEqual(len(self.placeholder_failures(repo, rel)), 1)


class OverlappingReviewerProvenanceTests(Cli, DriveTestCase):
    """Defect 4: when two reviewer windows overlapped, the second reviewer's stop logged PROVENANCE REFUSED for a verdict
    the first had written and already recorded."""

    REL = ".drive/proofs/{}/r2/verdict.json".format(KEY)

    def overlap(self, repo):
        self.snap(repo, "start", "agent-a")
        self.snap(repo, "start", "agent-b")
        self.write(repo, self.REL, verdict(KEY, round_number=2))
        self.snap(repo, "stop", "agent-a", transcript=self.transcript(repo, self.REL, agent_id="agent-a"))

    def stop_b(self, repo):
        other = ".drive/proofs/{}/r2/pytest.txt".format(LIST)
        self.snap(repo, "stop", "agent-b", transcript=self.transcript(repo, other, agent_id="agent-b"))

    def test_the_second_reviewer_notes_a_verdict_the_first_recorded_and_the_lint_accepts_it(self):
        repo = self.make_run()
        self.overlap(repo)
        self.stop_b(repo)
        log = self.gate_log(repo)
        self.assertIn("PROVENANCE verifier agent-a wrote {}".format(self.REL), log)
        self.assertIn("PROVENANCE NOTE verifier agent-b {}: already recorded for drive:verifier agent-a".format(self.REL), log)
        self.assertNotIn("PROVENANCE REFUSED", log)
        writers = [e.get("agent_id") for e in drive.ledger_entries(repo, "evidence") if e.get("path") == self.REL]
        self.assertEqual(writers, ["agent-a"])
        text = (repo / ".drive/STATUS.md").read_text().replace(
            "verdict:.drive/proofs/{}/r1/verdict.json".format(KEY), "verdict:" + self.REL)
        self.write(repo, ".drive/STATUS.md", text)
        lines = self.lint_cli(repo)
        self.assertEqual(self.failing(lines, "provenance"), [])
        self.assertEqual(self.failing(lines, "r2/verdict.json"), [])

    def test_a_verdict_rewritten_after_the_first_reviewer_recorded_it_is_still_refused(self):
        repo = self.make_run()
        self.overlap(repo)
        self.write(repo, self.REL, dict(verdict(KEY, round_number=2), for_maker="edited by hand after the review"))
        self.stop_b(repo)
        log = self.gate_log(repo)
        self.assertIn("PROVENANCE REFUSED verifier agent-b {}".format(self.REL), log)
        self.assertNotIn("PROVENANCE NOTE", log)

    def test_a_file_no_reviewer_wrote_is_refused_for_both_overlapping_reviewers(self):
        repo = self.make_run()
        rel = ".drive/proofs/{}/r2/verdict.json".format(LIST)
        self.snap(repo, "start", "agent-a")
        self.snap(repo, "start", "agent-b")
        self.write(repo, rel, verdict(LIST, round_number=2))
        self.snap(repo, "stop", "agent-a", transcript=self.transcript(repo, ".drive/proofs/x/r2/a.txt", agent_id="agent-a"))
        self.stop_b(repo)
        log = self.gate_log(repo)
        self.assertIn("PROVENANCE REFUSED verifier agent-a {}".format(rel), log)
        self.assertIn("PROVENANCE REFUSED verifier agent-b {}".format(rel), log)
        self.assertNotIn("PROVENANCE NOTE", log)

    def test_the_same_reviewer_stopping_twice_does_not_note_its_own_entry(self):
        repo = self.make_run()
        self.snap(repo, "start", "agent-a")
        self.write(repo, self.REL, verdict(KEY, round_number=2))
        self.snap(repo, "stop", "agent-a", transcript=self.transcript(repo, self.REL, agent_id="agent-a"))
        self.snap(repo, "stop", "agent-a", transcript=Path(str(self.home)) / "missing.jsonl")
        log = self.gate_log(repo)
        self.assertNotIn("PROVENANCE NOTE verifier agent-a {}".format(self.REL), log)
        self.assertIn("PROVENANCE REFUSED verifier agent-a {}".format(self.REL), log)


class NonZeroShellWriteTests(DriveTestCase):
    """The linkkeeper run on 2026-09-15: a verifier wrote its verdict with a heredoc and then, in the same Bash call, ran
    `grep -c '[<>]'`, which exits 1 on no match; the call was recorded as failed and the verdict it wrote was refused."""

    REL = ".drive/proofs/concurrent-api-requests-lose-no-writes/r1/verdict.json"

    def setUp(self):
        super().setUp()
        self.repo = self.make_run()
        self.write(self.repo, self.REL, verdict("concurrent-api-requests-lose-no-writes"))
        self.command = "cat > {} <<'JSON'\n{{}}\nJSON\ngrep -c '[<>]' {}".format(self.REL, self.REL)

    def test_a_write_in_a_call_that_ran_and_exited_non_zero_is_credited(self):
        path = self.transcript(self.repo, command=self.command, agent_id="agent-v", is_error=True, result_text="Exit code 1\n0")
        self.assertIsNone(drive.transcript_problem(self.repo, self.REL, str(path), "drive:verifier", "agent-v"))

    def test_a_write_the_guard_refused_is_still_not_credited(self):
        path = self.transcript(self.repo, command=self.command, agent_id="agent-v", is_error=True,
                               result_text="PreToolUse:Bash hook error: the verifier writes only its proof round")
        self.assertIsNotNone(drive.transcript_problem(self.repo, self.REL, str(path), "drive:verifier", "agent-v"))

    def test_a_failed_write_tool_is_still_not_credited(self):
        path = self.transcript(self.repo, self.REL, tool="Write", agent_id="agent-v", is_error=True, result_text="Exit code 1")
        self.assertIsNotNone(drive.transcript_problem(self.repo, self.REL, str(path), "drive:verifier", "agent-v"))


class WrappedAssertionShapeTests(DriveTestCase):
    """The linkkeeper run on 2026-09-15 widened a wrapped-assertion exception to all of tests/ because the guard flagged
    try/finally cleanup blocks, which cannot swallow an assertion, and an exception row could name only one glob."""

    def repo_with(self, files):
        from helpers import goal_md
        self.count = getattr(self, "count", 0) + 1
        repo = self.new_repo("wrapped-{}".format(self.count))
        for rel, content in files.items():
            self.write(repo, rel, content)
        base = self.commit(repo, "chore: baseline")
        self.write(repo, ".drive/GOAL.md", goal_md(base))
        self.commit(repo, "drive(intake): session-auth")
        return repo

    def guard_after(self, rel, after, extra=None):
        repo = self.repo_with(dict({rel: "def test_ratio():\n    assert ratio() == 0.5\n"}, **(extra or {})))
        self.write(repo, rel, after)
        return self.run_drive("guard", cwd=repo)

    def test_cleanup_and_narrow_or_reraising_handlers_are_not_wrapped_assertions(self):
        cases = {
            "finally only": "def test_ratio():\n    conn = open_db()\n    try:\n        assert ratio(conn) == 0.5\n    finally:\n        conn.close()\n",
            "narrow handler": "def test_ratio():\n    try:\n        assert ratio() == 0.5\n    except ValueError:\n        pass\n",
            "re-raised": "def test_ratio():\n    try:\n        assert ratio() == 0.5\n    except Exception:\n        log('x')\n        raise\n",
        }
        for name, after in cases.items():
            with self.subTest(case=name):
                result = self.guard_after("tests/test_calc.py", after)
                self.assertNotIn("wrapped-assertion", result.stdout)
        js = self.repo_with({"tests/app.test.ts": "it('adds', () => {\n  expect(add(1, 2)).toEqual(3);\n});\n"})
        self.write(js, "tests/app.test.ts", "it('adds', () => {\n  const s = start();\n  try {\n    expect(add(1, 2)).toEqual(3);\n  } finally {\n    s.stop();\n  }\n});\n")
        self.assertNotIn("wrapped-assertion", self.run_drive("guard", cwd=js).stdout)

    def test_swallowing_handlers_are_still_wrapped_assertions(self):
        cases = {
            "bare except": "def test_ratio():\n    try:\n        assert ratio() == 0.5\n    except:\n        print('ignored')\n",
            "Exception": "def test_ratio():\n    try:\n        self.assertEqual(ratio(), 0.5)\n    except Exception:\n        print('ignored')\n",
            "tuple with AssertionError": "def test_ratio():\n    try:\n        assert ratio() == 0.5\n    except (ValueError, AssertionError):\n        print('ignored')\n",
        }
        for name, after in cases.items():
            with self.subTest(case=name):
                self.assertIn("wrapped-assertion · ", self.guard_after("tests/test_calc.py", after).stdout)
        js = self.repo_with({"tests/app.test.ts": "it('adds', () => {\n  expect(add(1, 2)).toEqual(3);\n});\n"})
        self.write(js, "tests/app.test.ts", "it('adds', () => {\n  try {\n    expect(add(1, 2)).toEqual(3);\n  } catch (e) {\n    console.log(e);\n  }\n});\n")
        self.assertIn("wrapped-assertion · ", self.run_drive("guard", cwd=js).stdout)

    def test_an_exception_row_may_name_several_files(self):
        swallow = "def test_ratio():\n    try:\n        assert ratio() == 0.5\n    except Exception:\n        print('ignored')\n"
        start = "def test_ratio():\n    assert ratio() == 0.5\n"
        constraints = ("# CONSTRAINTS · proj\n\n## Exceptions\n\n| rule | path | reason | undo | decision |\n|---|---|---|---|---|\n"
                       "| wrapped-assertion | `tests/test_a.py`, `tests/test_b.py` | legacy probes | rewrite them | DECISIONS.md 2026-09-15-allow-legacy-probes |\n")
        decisions = "# DECISIONS · proj\n\n## 2026-09-15 · Allow legacy probes\n- Decision: allow.\n- Undo: rewrite · reversal cost: low.\n- Narrows: none\n"
        repo = self.repo_with({"tests/test_a.py": start, "tests/test_b.py": start, "tests/test_c.py": start,
                               ".drive/CONSTRAINTS.md": constraints, ".drive/DECISIONS.md": decisions})
        for name in ("test_a", "test_b", "test_c"):
            self.write(repo, "tests/{}.py".format(name), swallow)
        out = self.run_drive("guard", cwd=repo).stdout
        self.assertNotIn("tests/test_a.py", out)
        self.assertNotIn("tests/test_b.py", out)
        self.assertIn("wrapped-assertion · tests/test_c.py", out)


class InPlaceScriptTextTests(DriveTestCase):
    """The linkkeeper run on 2026-09-15: the orchestrator's `sed -i "s#...#...#" .drive/STATUS.md` was refused because the
    replacement text names a frozen test, as if the sed script were a file the command writes."""

    def setUp(self):
        super().setUp()
        from test_adversarial_review import Hooks
        self.hooks = Hooks()
        self.repo = self.make_run()
        self.write(self.repo, "tests/test_frozen_a.py", "def test_a():\n    assert True is not False\n")
        self.assertEqual(self.run_drive("freeze", "add", "tests/test_frozen_a.py", cwd=self.repo).returncode, 0)

    def bash(self, command):
        import json
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command},
                   "cwd": str(self.repo), "session_id": "s-main", "tool_use_id": "toolu_inplace"}
        return self.run_drive("hook-guard", stdin=json.dumps(payload))

    def test_a_script_that_names_a_frozen_test_does_not_make_the_edit_a_frozen_write(self):
        for command in ['sed -i "s#planned:tests/test_frozen_a.py::test_a#test:tests/test_frozen_a.py::test_a#" .drive/STATUS.md',
                        'V=x && sed -i "s#planned:tests/test_frozen_a.py::test_a#verdict:$V#" .drive/STATUS.md',
                        "sed -i -e 's#tests/test_frozen_a.py#done#' .drive/STATUS.md"]:
            # perl -e code that names a frozen path stays refused: inline interpreter code could open that file.
            with self.subTest(command=command):
                result = self.bash(command)
                self.assertNotIn("is frozen", result.stderr)

    def test_an_in_place_edit_of_the_frozen_test_itself_is_still_refused(self):
        for command in ["sed -i 's/True/False/' tests/test_frozen_a.py",
                        "sed -i -e 's/True/False/' tests/test_frozen_a.py",
                        "perl -pi -e 's/True/False/' tests/test_frozen_a.py"]:
            with self.subTest(command=command):
                result = self.bash(command)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("frozen", result.stderr)


class AuditorHookGuard:
    """Runs the real hook-guard subprocess as a read-only reviewer in a fresh run (not itself a TestCase)."""

    def setUp(self):
        super().setUp()
        self.repo = self.make_run()
        # The auditor's scratch copy lived under /private/tmp; the tests' own scratch root stays a throwaway root too.
        self.tmp_env = {"DRIVE_TMP_ROOTS": "{}:/private/tmp".format(self.scratch)}

    def guard_as(self, command, agent="drive:auditor"):
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command},
                   "cwd": str(self.repo), "session_id": "s-main", "tool_use_id": "x", "agent_type": agent,
                   "agent_id": "agent-a"}
        return self.run_drive("hook-guard", stdin=json.dumps(payload), env=self.tmp_env)

    def assertAllowed(self, command, agent="drive:auditor"):
        result = self.guard_as(command, agent)
        self.assertEqual(result.returncode, 0, "{} was refused for {}: {}".format(command, agent, result.stderr))

    def assertRefused(self, command, fragment, agent="drive:auditor"):
        result = self.guard_as(command, agent)
        self.assertEqual(result.returncode, 2, "{} was allowed for {}".format(command, agent))
        self.assertIn(fragment, result.stderr)


class BsdSedBackupSuffixTests(AuditorHookGuard, DriveTestCase):
    """Defect 1 of the linkkeeper final audit: `sed -i '' ...` passes BSD sed's empty backup suffix as its own argument,
    and the guard took the script for the file the edit writes."""

    def test_bsd_sed_in_place_in_a_scratch_copy_is_allowed(self):
        self.assertAllowed("sed -i '' 's/^_HAS_TAG = .*/_HAS_TAG = \"instr(b.tags, ?) > 0\"/' "
                           "/private/tmp/drive-audit-linkkeeper/linkkeeper/search.py")
        self.assertAllowed("sed -i .orig -e 's/a/b/' /private/tmp/drive-audit-linkkeeper/linkkeeper/search.py")

    def test_bsd_sed_in_place_in_the_project_is_still_refused_naming_the_file(self):
        self.assertRefused("sed -i '' 's/a/b/' src/app.py", "writes src/app.py outside its scope")
        self.assertRefused("sed -i .bak 's/a/b/' src/app.py", "writes src/app.py outside its scope")

    def test_gnu_attached_suffix_still_works(self):
        self.assertAllowed("sed -i.bak 's/a/b/' /private/tmp/drive-audit-linkkeeper/file")
        self.assertRefused("sed -i.bak 's/a/b/' src/app.py", "writes src/app.py outside its scope")

    def test_a_sed_write_command_behind_the_empty_suffix_is_still_seen(self):
        self.assertRefused("sed -i '' 's/a/b/w src/leak.txt' /private/tmp/drive-audit-linkkeeper/file", "(w, W, or e)")


class LiteralVariableTests(AuditorHookGuard, DriveTestCase):
    """Defect 2: `S=<scratch> && mkdir -p "$S" && (... > "$S/pytest.txt")` was refused because $S was unknowable, though
    the same command line had just assigned it a literal path."""

    def scratchpad(self):
        return "{}/claude-501/-Users-chabotc-Projects-linkkeeper/0f3c/scratchpad".format(self.scratch)

    def test_a_literal_assigned_earlier_in_the_chain_is_resolved(self):
        self.assertAllowed('S={} && mkdir -p "$S" && (python3 -m pytest -q > "$S/pytest.txt" 2>&1; echo "exit=$?" >> '
                           '"${{S}}/pytest.txt")'.format(self.scratchpad()))
        self.assertAllowed('S={}\nmkdir -p "$S"; cp README.md $S/'.format(self.scratchpad()))

    def test_the_resolved_value_is_judged(self):
        self.assertRefused('S=src && rm -rf "$S"', "'rm' on src deletes or moves")
        self.assertRefused('S={} && S=src && rm -rf "$S"'.format(self.scratchpad()), "'rm' on src deletes or moves")

    def test_a_value_that_may_not_hold_at_the_use_stays_unknowable(self):
        pad = self.scratchpad()
        for command in ['test -d x && S={} ; rm -rf "$S"',
                        'test -d x || S={} && rm -rf "$S"',
                        'test -d x &&\nS={}\nrm -rf "$S"',
                        'S={} && test -d x && S=src; rm -rf "$S"',
                        'S={} ; if test -d x; then S=src; fi; rm -rf "$S"',
                        'S={} ; {{ S=src; }}; rm -rf "$S"',
                        'S={} ; (S=src) ; rm -rf "$S"',
                        'S={} | cat; rm -rf "$S"',
                        'S={} & rm -rf "$S"',
                        'S={} && S=$(pwd) && rm -rf "$S"',
                        'S={} && export S=src && rm -rf "$S"',
                        'S={} && read S && rm -rf "$S"',
                        'S={} && for S in src; do true; done; rm -rf "$S"',
                        "S={} && rm -rf '$S'",
                        'S={} && rm -rf "$SX"']:
            with self.subTest(command=command):
                self.assertRefused(command.format(pad), "deletes or moves")


class ShellLoopTests(AuditorHookGuard, DriveTestCase):
    """Defect 3: a read-only review's `for f in $(find ...); do ...; done` was refused because 'for' was judged as a
    command name."""

    LOOP = ("for f in $(find .drive/proofs -name 'verdict.json' | sort); do echo \"--- $f\"; "
            "jq -c '{unit, verdict, rung_supported}' \"$f\"; done")

    def test_a_read_only_loop_is_allowed_for_the_reviewers(self):
        for agent in ("drive:auditor", "drive:verifier"):
            with self.subTest(agent=agent):
                self.assertAllowed(self.LOOP, agent)
                self.assertAllowed("for f in README.md src/auth.py\ndo\n  wc -l \"$f\"\ndone > /dev/null", agent)
                self.assertAllowed("if test -d .drive/proofs; then ls .drive/proofs; else echo none; fi", agent)
                self.assertAllowed("while read -r line; do echo \"$line\"; done < README.md", agent)

    def test_a_loop_body_or_list_that_writes_outside_scope_stays_refused(self):
        self.assertRefused('for f in src/*.py; do rm "$f"; done', "'rm' on $f deletes or moves")
        self.assertRefused("for f in $(rm -rf src); do echo $f; done", "'rm' on src deletes or moves")
        self.assertRefused("for f in a b; do echo $f > src/out.txt; done", "Redirecting output into src/out.txt")
        self.assertRefused("for f in a; do echo $f; done > src/out.txt", "Redirecting output into src/out.txt")
        self.assertRefused("if true; then touch src/new.py; fi", "'touch' writes src/new.py")


class AwkStringLiteralTests(AuditorHookGuard, DriveTestCase):
    """Defect 4: a `>` inside an awk string literal read as an awk output redirection."""

    REFUSAL = "This awk program can write files or run commands"

    def test_a_greater_than_inside_an_awk_string_is_not_a_write(self):
        self.assertAllowed("awk '/^_HAS_TAG = /{print \"_HAS_TAG = \\\"instr(b.tags, ?) > 0\\\"\"; next} {print}' "
                           "src/auth.py > /private/tmp/drive-audit-linkkeeper/search.py.new")
        self.assertAllowed("awk '$0 ~ /a\"b/ {print \"x | getline\"}' README.md")

    def test_a_real_awk_write_or_command_still_matches(self):
        for program in ['{print > "out.txt"}', '{print "a > b" > "out.txt"}', '{printf "%s", $0 >> "out.txt"}',
                        '{"date" | getline d; print d}', '{print "x" | "sh"; system("rm x")}', '/"/ {print > "o"}',
                        '{print "unterminated > x}']:
            with self.subTest(program=program):
                self.assertRefused("awk '{}' README.md".format(program), self.REFUSAL)

    def test_the_shell_redirect_after_the_program_is_still_judged(self):
        self.assertRefused("awk '{print \"a > b\"}' README.md > src/out.txt", "Redirecting output into src/out.txt")


class VerdictModelTests(Cli, DriveTestCase):
    """Defect 5: verdict.schema.json had no model field, so a verdict could not record which model served the reviewer."""

    def lint_with(self, extra):
        repo = self.make_run()
        rel = ".drive/proofs/{}/r1/verdict.json".format(KEY)
        self.write(repo, rel, dict(verdict(KEY), **extra))
        self.sign(repo, rel)
        return [line for line in self.lint_cli(repo) if "model" in line]

    def test_a_verdict_may_record_its_model(self):
        self.assertEqual(self.lint_with({"model": "claude-opus-5"}), [])

    def test_the_model_is_optional(self):
        self.assertEqual(self.lint_with({}), [])

    def test_the_model_must_be_a_string(self):
        self.assertNotEqual(self.lint_with({"model": 5}), [])

    def test_the_schema_and_the_reviewer_agents_describe_it(self):
        schema = json.loads((SKILL / "templates/verdict.schema.json").read_text())
        self.assertEqual(schema["properties"]["model"]["type"], "string")
        self.assertNotIn("model", schema["required"])
        for name in ("verifier", "auditor", "ui-reviewer"):
            with self.subTest(agent=name):
                self.assertIn("`model`", (SKILL / "agents/{}.md".format(name)).read_text())
