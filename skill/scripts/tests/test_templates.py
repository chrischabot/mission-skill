"""Every template, filled with placeholder-free sample values, lints cleanly; left unfilled, it fails."""
import json
import shutil
from pathlib import Path

from helpers import DriveTestCase, GOAL_TEXT, TODAY, drive, fill_lines, verdict

T = Path(drive.TEMPLATES)
KEY = "export-keeps-list-totals"


def template(name):
    return (T / name).read_text(encoding="utf-8")


class TemplateFillTests(DriveTestCase):
    def assertNoPlaceholders(self, name, text):
        left = drive.find_placeholders(text)
        self.assertEqual(left, [], "{} still has placeholders after filling: {}".format(name, left))

    def place(self, repo, rel, text):
        if not rel.endswith(".json"):
            self.assertNoPlaceholders(rel, text)
        self.write(repo, rel, text)

    def test_all_templates_filled_lint_cleanly(self):
        repo = self.new_repo()
        self.write(repo, "README.md", "# proj\n")
        self.commit(repo, "chore: start")
        result = self.run_drive("init", "--goal", GOAL_TEXT, "--slug", "session-auth", "--size", "M", cwd=repo)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        drive_dir = repo / ".drive"

        goal = fill_lines((drive_dir / "GOAL.md").read_text(), {
            "live means:": "live means: the staging deployment at https://staging.example.test",
            "budget:": "budget: 40 turns · 8 subagents · 3 h · 20 usd",
            "- outcome:": '- outcome: "Reject expired tokens"',
            "- user:": "- user: assumption: API clients and administrators",
            "- why now:": "- why now: assumption: a security review asked for it",
            "- success:": '- success: "let admins revoke sessions"',
            "- constraints:": "- constraints: assumption: no new runtime dependency",
            "- out of scope:": "- out of scope: assumption: single sign-on",
            "shape:": "shape: feature",
            "size:": "size: M",
            "size_set_by:": 'size_set_by: "several modules: token check, session store, export"',
            "  repo:": "  repo: /repo",
            "  build_command:": '  build_command: "none"',
            "  focused_test_command:": '  focused_test_command: "python3 -m pytest tests/test_export.py"',
            "  test_command:": '  test_command: "python3 -m pytest"',
            "  claude_md:": "  claude_md: absent",
        })
        self.assertIn("variant: null", goal)
        self.place(repo, ".drive/GOAL.md", goal)

        state = fill_lines((drive_dir / "STATE.md").read_text(), {
            "next:": "next: Write the spec for the export claim.",
            "session:": "session: drive-session-auth",
            "model:": "model: claude-fable-5-1 · high",
            "Why:": "Why: the export claim has no spec yet.",
        })
        self.place(repo, ".drive/STATE.md", state)

        status = (drive_dir / "STATUS.md").read_text() + "| {} | The export keeps the list totals | y | Missing |  | {} |\n".format(KEY, TODAY)
        self.place(repo, ".drive/STATUS.md", status)

        decisions = (drive_dir / "DECISIONS.md").read_text() + (
            "\n## 2026-09-14 · Stream the export from the existing query\n- Context: {} needs large exports.\n"
            "- Decision: stream rows from the list query.\n- Rejected: a new table, because it duplicates the list.\n"
            "- Undo: revert the export commit · reversal cost: low.\n- Evidence: none\n- Narrows: none\n").format(KEY)
        self.place(repo, ".drive/DECISIONS.md", decisions)

        lesson = fill_lines(template("lesson.md"), {
            "### ": "### Before trusting a green run against a local database double, list the limits it does not enforce",
            "- When:": "- When: tests run against an in-memory database that stands in for the hosted one.",
            "- Do:": "- Do: list the hosted database's documented limits and make the double or the code enforce each.",
            "- Because:": "- Because: a double more permissive than production certifies code that fails live.",
            "- Check:": "- Check: the kindness ledger in TESTPLAN.md",
            "- Verified by:": "- Verified by: the export failed live at 101 bound parameters after passing locally, 2026-09-14.",
            "- Applies to:": "- Applies to: this project's export and list queries.",
            "- Not for:": "- Not for: pure functions with no database.",
            "- Seen:": "- Seen: 1 (2026-09-14) · Added: 2026-09-14 · Confirmed by: auditor, claude-fable-5-1",
        })
        self.assertEqual(drive.lesson_entry_problems(*drive.parse_lessons(lesson)[0][1:]), [])
        self.place(repo, ".drive/LESSONS.md", (drive_dir / "LESSONS.md").read_text() + "\n" + lesson)

        constraints = fill_lines((drive_dir / "CONSTRAINTS.md").read_text(), {
            "measured:": "measured: abc1234 · 2026-09-14 · by drive:architect · rules: references/testing.md section 8",
            "project's own constraints:": "project's own constraints: none",
            "| Type errors |": "| Type errors | `mypy src` | 0 | must not grow | 0 | 0 | the code is typed | abc1234 · 2026-09-14 |",
            "| Lint violations |": "| Lint violations | `ruff check . --statistics` | 4 | must not grow | 0 | none | legacy module | abc1234 · 2026-09-14 |",
            "| Test suite passing |": "| Test suite passing | `python3 -m pytest -q` | 12/12 | must not fall | 0 | all | the suite is the floor | abc1234 · 2026-09-14 |",
            "| Dependency vulnerabilities": "| Dependency vulnerabilities at high or above | `pip-audit` | 0 | must not grow | 0 | 0 | outside check: vulnerability database | abc1234 · 2026-09-14 |",
            "| <rule in words>": None, "| <metric in words>": None, "| <rule> |": None, "| <YYYY-MM-DD> |": None,
        })
        self.place(repo, ".drive/CONSTRAINTS.md", constraints)
        self.commit(repo, "drive(intake): session-auth")

        investigation = fill_lines(template("investigation.md"), {
            "# ": "# The export endpoint returned 500 for 101 invoices on staging",
            "Status:": "Status: distilled",
            "Trigger:": "Trigger: green-check-failed",
            "Detected:": "Detected: 2026-09-14T10:00:00Z by drive:verifier via the live check",
            "Got past:": "Got past: the local suite, whose database double has no parameter limit",
            "Timebox:": "Timebox: 60 minutes",
            "- Observed:": "- Observed: HTTP 500, too many SQL variables, exit 0 from curl",
            "- Expected:": "- Expected: a CSV with 101 rows",
            "- Reproduction:": "- Reproduction: python3 -m pytest tests/test_export.py -k many, deterministic",
            "  1. ": "  1. the parameter limit · separated by: 100 rows pass and 101 fail",
            "  2. ": "  2. a timeout · separated by: the failure is immediate",
            "  3. ": "  3. bad data in one row · separated by: any 101 rows fail",
            "- Observations and what they eliminated:": "- Observations and what they eliminated: the failure is size-bound, which rules out data and timing",
            "- Mechanism:": "- Mechanism: the hosted database rejects statements with more than 100 bound parameters and the double accepts any number",
            "- Prediction:": "- Prediction: the list endpoint fails the same way at 101 invoices",
            "- Check run:": "- Check run: python3 -m pytest tests/test_list.py -k many, output .drive/local/logs/list.txt",
            "- Revert check:": "- Revert check: yes, reverting the chunking restores the 500",
            "- Change:": "- Change: 1a2b3c4",
            "- Regression test:": "- Regression test: test:tests/test_export.py::export keeps list totals",
            "- Harness now enforces:": "- Harness now enforces: the double rejects statements above 100 parameters",
            "- Candidate lesson:": "- Candidate lesson: Before trusting a green run against a local database double, list the limits it does not enforce",
            "- Routing:": "- Routing: procedural-rule",
            "- Dedupe verdict:": "- Dedupe verdict: distinct",
            "- Auditor verdict:": "- Auditor verdict: accepted",
            "- Written to:": "- Written to: references/lessons/general.md at 5d6e7f8",
            "- fail recorded": "- fail recorded 2026-09-14T10:00:00Z verifier\n- investigate closed 2026-09-14T10:40:00Z investigator\n"
                              "- verify closed 2026-09-14T11:00:00Z investigator\n- distill closed 2026-09-14T11:30:00Z orchestrator",
        })
        postmortem = fill_lines(template("postmortem.md"), {
            "- <ISO UTC>": "- 2026-09-14T09:40:00Z · the live check returned 500 for a 101-invoice export",
            "<Who or what": "Finance could not export invoices on staging for 80 minutes; production was not affected.",
            "- How it was noticed:": "- How it was noticed: agent check",
            "- Time undetected:": "- Time undetected: 80 minutes",
            "- What should have noticed it first:": "- What should have noticed it first: a severe test with 101 rows",
            "- <gate the work passed>": "- local suite: passed because the double accepts any number of parameters",
            "- <test, check,": "- a severe test exporting 101 invoices · 1a2b3c4",
            "<One paragraph.>": "List the hosted database's limits before writing the first query against its double.",
        })
        self.place(repo, ".drive/investigations/2026-09-14-export-500.md", investigation + "\n" + postmortem)

        retro = fill_lines(template("retro.md"), {
            "# RETRO": "# RETRO · session-auth · 2026-09-14",
            "| <.drive/investigations/": "| .drive/investigations/2026-09-14-export-500.md | distilled | lesson routed to general |",
            "- <candidate rule heading>": "- Before trusting a green run against a local database double, list the limits it does not enforce · dedupe: distinct · auditor: accepted · destination: references/lessons/general.md",
            "- <lesson heading>": "- When the same obstacle needs a workaround a second time, stop and re-diagnose · in briefs: 2 · cited by a verifier: 1",
            "- <none, or the passage": "- none · eval case: none",
            "- <not due": "- not due: the last consolidation was 2026-09-01",
            "- <heading> →": "- Before trusting a green run against a local database double, list the limits it does not enforce → references/lessons/general.md (5d6e7f8)",
        })
        self.place(repo, ".drive/reviews/2026-09-14-retro.md", retro)

        report = fill_lines(template("REPORT.md"), {
            "# REPORT": "# REPORT · session-auth",
            "<One paragraph: what was asked": "Admins asked for a CSV export; it is specified and not yet built, so its claim is Missing.",
            "<none, or the single decision": "none",
            "<The one or two things": ".drive/investigations/2026-09-14-export-500.md",
            "| Missing |": "| Missing | 1 |", "| Scaffold |": "| Scaffold | 0 |", "| Partial |": "| Partial | 0 |",
            "| Local Proof |": "| Local Proof | 0 |", "| Live Proof |": "| Live Proof | 0 |", "| Operational |": "| Operational | 0 |",
            "| Done |": "| Done | 0 |", "| Dropped |": "| Dropped | 0 |",
            "- <claim words> · <rung> ·": "- nothing shipped yet",
            "- Live:": "- Live: none",
            "- Local only:": "- Local only: none",
            "- Where a harness": "- Where a harness was kinder than production: the database double has no parameter limit",
            "- <claim words> · <rung reached>": "- The export keeps the list totals · Missing · build the export endpoint",
            "- <decision in plain words>": "- Stream the export from the existing query · undo: revert the export commit · 2026-09-14",
            "- <symptom>": "- none",
            "- <rule heading>": "- Before trusting a green run against a local database double, list the limits it does not enforce → references/lessons/general.md (5d6e7f8)",
            "<exact commands, each": "python3 -m pytest",
            "<none, or the .drive/runs/": "none",
            "<turns, subagents": "12 turns, 3 subagents, 40 minutes",
        })
        self.place(repo, ".drive/REPORT.md", report)

        handoff = fill_lines(template("handoff.md"), {
            "# Handoff": "# Handoff · {}".format(KEY),
            "I'm working on": "I'm working on invoice exports for the finance team. They need an export they can trust at quarter close. "
                              "With that in mind: verify every claim below against the scope, run the validation commands yourself, and try to refute each claim.",
            "goal:": 'goal: "{}"'.format(GOAL_TEXT),
            "repository root:": "repository root: /private/tmp/drive-fixture/repo",
            "skill directory:": "skill directory: /private/tmp/drive-fixture/skill",
            "round:": "round: 1/3",
            "rubric:": "rubric: .drive/rubrics/feature.md at abc1234",
            "spec:": "spec: .drive/SPEC.md, section Requirements",
            "previous gaps:": "previous gaps: none",
            "output:": "output: templates/verdict.schema.json · proof directory .drive/proofs/{}/r1/".format(KEY),
            "### <claim key>": "### {}".format(KEY),
            "Claim:": "Claim: The export keeps the list totals",
            "What must be true:": "What must be true: an export of 101 invoices has the same total as the filtered list",
            "range:": "range: abc1234..def5678",
            "checkout:": "checkout: /repo",
            "- <path from git diff": "- src/export/api.py",
            "build:": "build: `none`", "typecheck:": "typecheck: `mypy src`", "lint:": "lint: `ruff check .`",
            "tests:": "tests: `python3 -m pytest`", "live:": "live: `curl -s https://staging.example.test/invoices/export`",
            "- <test path, severe:": "- tests/test_export.py",
            "- <rule heading verbatim": "- none",
        })
        self.place(repo, ".drive/handoffs/{}.md".format(KEY), handoff)

        brief = fill_lines(template("package-brief.md"), {
            "# Package": "# Package export-api",
            "I'm working on": "I'm working on invoice exports for the finance team. They need the export endpoint before the screen can call it. "
                              "With that in mind: build this package in the shared checkout, where other agents are working in other directories at the same time.",
            "repository root:": "repository root: /private/tmp/drive-fixture/repo",
            "skill directory:": "skill directory: /private/tmp/drive-fixture/skill",
            "<What exists when": "GET /invoices/export returns the filtered invoices as CSV.",
            "key:": "key: {}".format(KEY),
            "claim:": "claim: The export keeps the list totals",
            "what would prove it wrong:": "what would prove it wrong: an export of 101 invoices whose total differs from the list",
            "- `<path>`": "- `src/models/invoice.py` (already on main; read it, do not modify it)",
            "<The shapes other": "GET /invoices/export returns text/csv with the list's columns.",
            "- `<path or glob>` (owned by": "- `src/app.py` (owned by the integrator)",
            "- `<path or glob>`": "- `src/export/**`",
            "- <test path>::": "- tests/test_export.py::export keeps list totals",
            "- Production constraints": "- Production constraints the harness must enforce: at most 100 bound parameters per statement",
            "- Focused test:": "- Focused test: `python3 -m pytest tests/test_export.py`",
            "- Build directory:": "- Build directory: `none`",
            "- <rule heading, verbatim": "- Before trusting a green run against a local database double, list the limits it does not enforce",
            "<turns> turns": "120 turns and 90 minutes. At eighty percent of either without converging, stop and report partial with the exact remaining items.",
        }).replace("<package id>", "export-api")
        self.place(repo, ".drive/packages/export-api/brief.md", brief)
        index = fill_lines(template("packages-index.md"), {
            "# Packages": "# Packages · session-auth",
            "| <package id>": "| export-api | 1 | {} | `src/export/**` | none | no | planned |".format(KEY),
            "- `<entry point": "- `pyproject.toml`",
        })
        self.place(repo, ".drive/packages/index.md", index)
        report_json = {"package": "export-api", "status": "complete", "files": ["src/export/api.py"],
                       "tests": ["tests/test_export.py::export keeps list totals"],
                       "gates_run": [{"cmd": "python3 -m pytest tests/test_export.py", "exit": 0, "tail": "3 passed"}],
                       "wiring_needed": [{"file": "src/app.py", "patch": "app.include_router(export_router)"}],
                       "deps_requested": [], "honest_gaps": ["not run against staging"], "follow_ups": [],
                       "noticed_not_touched": [{"file": "src/models/invoice.py", "problem": "totals use float", "reason": "outside ownership"}],
                       "concerns": [], "summary": "Export endpoint streams the filtered list as CSV.", "model": "claude-sonnet-5"}
        schema = json.loads(template("package-report.schema.json"))
        self.assertEqual(drive.schema_errors(report_json, schema), [])
        self.write(repo, ".drive/packages/export-api/report.json", report_json)

        proof = json.loads(template("proof.json"))
        proof.update({"key": KEY, "claim": "The export keeps the list totals", "environment": "live",
                      "target": "https://staging.example.test/invoices/export", "commit": "abc1234", "produced_by": "verifier",
                      "started": "2026-09-14T12:00:00Z", "latest_round": "r1",
                      "commands": [{"cmd": "curl -s https://staging.example.test/invoices/export", "exit": 0, "output": "r1/live.md"}],
                      "artifacts": [{"path": "r1/live.md", "sha256": "0" * 64, "kind": "response"}],
                      "shim_differences": ["the local double has no parameter limit; this proof ran on staging"], "verdict": "pass"})
        self.assertEqual(drive.json_placeholders(proof), [])
        self.write(repo, ".drive/proofs/{}/proof.json".format(KEY), proof)

        findings = self.lint(repo)
        self.assertNoFailure(findings)
        self.assertNoFailure(self.lint(repo, gate="report"))
        self.assertNoFailure(self.lint(repo, gate="decompose"))

    def test_verdict_schema_accepts_a_valid_verdict_and_rejects_malformed_ones(self):
        schema = json.loads(template("verdict.schema.json"))
        good = verdict(KEY)
        self.assertEqual(drive.schema_errors(good, schema), [])
        for mutate, fragment in [(lambda v: v.pop("ran"), "missing ran"),
                                 (lambda v: v.update(verdict="maybe"), "$.verdict must be one of"),
                                 (lambda v: v["claims"][0].update(status="probably"), "status must be one of"),
                                 (lambda v: v["claims"][0].update(confidence=80), "confidence must be one of"),
                                 (lambda v: v.update(rung_supported="Done"), "rung_supported must be one of"),
                                 (lambda v: v.update(extra=1), "unexpected field extra")]:
            bad = verdict(KEY)
            mutate(bad)
            self.assertTrue(any(fragment in e for e in drive.schema_errors(bad, schema)), fragment)

    def test_package_report_schema_requires_the_new_fields(self):
        schema = json.loads(template("package-report.schema.json"))
        report = {"package": "export-api", "status": "complete", "files": [], "tests": [], "gates_run": [], "wiring_needed": [],
                  "deps_requested": [], "honest_gaps": [], "follow_ups": [], "concerns": [], "summary": "x" * 1501, "model": "claude-sonnet-5"}
        errors = drive.schema_errors(report, schema)
        self.assertTrue(any("missing noticed_not_touched" in e for e in errors))
        self.assertTrue(any("longer than 1500" in e for e in errors))

    def test_unfilled_templates_fail_lint(self):
        repo = self.make_run()
        placements = {
            "DECISIONS.md": ".drive/DECISIONS.md",
            "LESSONS.md": ".drive/LESSONS.md",
            "CONSTRAINTS.md": ".drive/CONSTRAINTS.md",
            "REPORT.md": ".drive/REPORT.md",
            "investigation.md": ".drive/investigations/2026-09-14-raw.md",
            "retro.md": ".drive/reviews/2026-09-14-retro.md",
            "handoff.md": ".drive/handoffs/expired-token-is-rejected.md",
            "package-brief.md": ".drive/packages/raw-package/brief.md",
            "packages-index.md": ".drive/packages/index.md",
            "proof.json": ".drive/proofs/expired-token-is-rejected/proof.json",
        }
        for name, rel in placements.items():
            shutil.copy(T / name, repo / rel) if (repo / rel).parent.exists() else self.write(repo, rel, template(name))
        findings = self.lint(repo)
        failed_files = {item["file"] for item in findings.items if item["level"] == "fail"}
        for rel in placements.values():
            self.assertIn(rel, failed_files, "an unfilled {} passed the lint".format(rel))

    def test_every_template_named_by_the_task_exists(self):
        for name in ("GOAL.md", "STATE.md", "STATUS.md", "DECISIONS.md", "LESSONS.md", "investigation.md", "lesson.md",
                     "postmortem.md", "retro.md", "REPORT.md", "handoff.md", "proof.json", "verdict.schema.json",
                     "package-brief.md", "package-report.schema.json", "packages-index.md", "CONSTRAINTS.md"):
            self.assertTrue((T / name).is_file(), name)
        for name in ("proof.json", "verdict.schema.json", "package-report.schema.json"):
            json.loads(template(name))
