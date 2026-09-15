"""Severe tests for the gaps the linkkeeper run review (research/40) found in what drive checks.

Each class names the gap it covers. Every test drives the real CLI (drive.py lint and drive.py init as subprocesses), and
each class holds tests that fail against drive.py as it stood before the change."""
import json
import re
from pathlib import Path

from helpers import DriveTestCase, TODAY, drive, fill_lines, goal_md, verdict

AUDIT = ".drive/reviews/2026-09-14-final-audit.json"
REVIEW = "# REVIEW · {phase} · round {n}\nverdict: {verdict}\nround: {n}/{bound}\n\n## Blocking\n- none\n\n## Should fix\n- none\n\n## Notes\n- none\n"


class Cli:
    def lint_lines(self, repo, *flags):
        result = self.run_drive("lint", *flags, cwd=repo)
        self.assertIn(result.returncode, (0, 1), result.stderr)
        return result.stdout.splitlines()

    def fails(self, lines, *fragments):
        return [l for l in lines if l.startswith("FAIL ") and all(f in l for f in fragments)]

    def warns(self, lines, *fragments):
        return [l for l in lines if l.startswith("warn ") and all(f in l for f in fragments)]

    def review(self, repo, phase, n=1, bound=2, verdict_value="ready", name=None, text=None):
        rel = ".drive/reviews/{}".format(name or "{}-{}-review-r{}.md".format(TODAY, phase, n))
        self.write(repo, rel, text if text is not None else REVIEW.format(phase=phase, n=n, bound=bound, verdict=verdict_value))

    def edit_goal(self, repo, old, new):
        path = Path(repo) / ".drive/GOAL.md"
        text = path.read_text()
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1))


class ReviewRoundLeavesAFileTests(Cli, DriveTestCase):
    """The intake classification review and six spec, design, and test-plan review rounds left no file under
    .drive/reviews/, so no auditor could check them."""

    def test_spec_design_and_test_plan_gates_fail_without_their_review_file(self):
        repo = self.make_run()
        for phase in ("spec", "design", "test-plan"):
            lines = self.lint_lines(repo, "--gate", phase)
            self.assertTrue(self.fails(lines, ".drive/reviews", "no review for the {} gate".format(phase)), "\n".join(lines))

    def test_a_review_file_satisfies_only_its_own_phase(self):
        repo = self.make_run()
        self.review(repo, "spec")
        self.assertFalse(self.fails(self.lint_lines(repo, "--gate", "spec"), "no review for"))
        self.assertTrue(self.fails(self.lint_lines(repo, "--gate", "design"), "no review for the design gate"))
        self.assertTrue(self.fails(self.lint_lines(repo, "--gate", "test-plan"), "no review for the test-plan gate"))

    def test_intake_gate_needs_the_classification_review_at_m_but_not_at_s(self):
        repo = self.make_run()
        self.assertTrue(self.fails(self.lint_lines(repo, "--gate", "intake"), "no review for the intake gate"))
        self.review(repo, "intake")
        self.assertFalse(self.fails(self.lint_lines(repo, "--gate", "intake"), "no review for"))
        repo.rename(self.tmp / "first")
        small = self.make_run()
        self.write(small, ".drive/GOAL.md", goal_md(self.git(small, "rev-list", "--max-parents=0", "--abbrev-commit", "HEAD"), size="S"))
        self.assertFalse(self.fails(self.lint_lines(small, "--gate", "intake"), "no review for"))

    def test_a_plan_line_naming_the_architect_or_a_fresh_review_needs_a_review_file(self):
        repo = self.make_run()
        self.edit_goal(repo, "- [ ] verify ·",
                       "- [ ] decompose · artifact: .drive/packages/ · exit: no two packages share a path · checker: architect\n"
                       "- [ ] harden · artifact: .drive/reviews/ · exit: a fresh security review has no blocking finding · checker: security-reviewer\n"
                       "- [ ] verify ·")
        self.assertTrue(self.fails(self.lint_lines(repo, "--gate", "decompose"), "no review for the decompose gate", "checker: architect"))
        self.assertTrue(self.fails(self.lint_lines(repo, "--gate", "harden"), "no review for the harden gate", "fresh review"))
        self.review(repo, "decompose")
        self.assertFalse(self.fails(self.lint_lines(repo, "--gate", "decompose"), "no review for"))
        # A phase with neither an architect checker nor a fresh-review exit needs no review file.
        self.assertFalse(self.fails(self.lint_lines(repo, "--gate", "build"), "no review for"))

    def test_a_review_that_does_not_open_with_its_verdict_and_round_fails(self):
        repo = self.make_run()
        legacy = "# Spec review · .drive/SPEC.md · round 1\nreviewer: drive:architect\n## Findings\n" + "| a | b |\n" * 12 + \
                 "## Verdict\nverdict: ready\nreason: fine\n"
        self.review(repo, "spec", name="{}-spec-review-round-1.md".format(TODAY), text=legacy)
        self.assertTrue(self.fails(self.lint_lines(repo, "--gate", "spec"), "spec-review-round-1.md", "verdict: ready"))

    def test_round_must_be_within_its_bound_and_match_the_file_name(self):
        repo = self.make_run()
        self.review(repo, "spec", n=3, bound=2)
        self.review(repo, "design", name="{}-design-review-r2.md".format(TODAY),
                    text=REVIEW.format(phase="design", n=1, bound=2, verdict="not ready"))
        self.review(repo, "test-plan", text=REVIEW.format(phase="test-plan", n=1, bound=2, verdict="maybe"))
        self.assertTrue(self.fails(self.lint_lines(repo, "--gate", "spec"), "outside its bound of 2"))
        self.assertTrue(self.fails(self.lint_lines(repo, "--gate", "design"), "says round 1 but its name says r2"))
        self.assertTrue(self.fails(self.lint_lines(repo, "--gate", "test-plan"), "verdict: not ready"))

    def test_a_json_review_with_verdict_and_round_fields_counts(self):
        repo = self.make_run()
        self.write(repo, ".drive/reviews/{}-design-review-r1.json".format(TODAY), {"verdict": "not ready", "round": "1/2"})
        self.assertFalse(self.fails(self.lint_lines(repo, "--gate", "design"), "review"))

    def test_the_filled_review_template_passes_the_gate(self):
        repo = self.make_run()
        template = (Path(drive.TEMPLATES) / "review.md").read_text(encoding="utf-8")
        filled = fill_lines(template, {
            "# REVIEW": "# REVIEW · spec · round 1",
            "verdict:": "verdict: not ready",
            "round:": "round: 1/2",
            "artifact:": "artifact: .drive/SPEC.md at abc1234",
            "reviewer:": "reviewer: drive:architect · model: claude-opus-5",
            "- <where>": "- none",
            "- <anything": "- none",
        })
        self.assertEqual(drive.find_placeholders(filled), [])
        for section in ("## Blocking", "## Should fix", "## Notes"):
            self.assertIn(section, filled)
        self.review(repo, "spec", text=filled)
        self.assertFalse(self.fails(self.lint_lines(repo, "--gate", "spec"), "review"))


class ReauditByAFreshAgentTests(Cli, DriveTestCase):
    """The run reused the drive:auditor instance that wrote the no-go for the final audit's second round."""

    def audit_round(self, repo, verdict_value, round_number, agent_id, how="shell", commit=True):
        data = verdict("final-audit", claims=["expired-token-is-rejected", "session-list-shows-active-sessions"],
                       verdict_value=verdict_value, rung="Operational", round_number=round_number)
        data["for_maker"] = "round {} by {}".format(round_number, agent_id)
        text = json.dumps(data, indent=2) + "\n"
        self.write(repo, AUDIT, text)
        if how == "write":
            transcript = self.transcript(repo, AUDIT, agent_type="drive:auditor", agent_id=agent_id, tool="Write",
                                         tool_input={"file_path": str(Path(repo) / AUDIT), "content": text})
            self.assertTrue(drive.record_evidence(Path(repo), AUDIT, "drive:auditor", agent_id, transcript=str(transcript)))
        else:
            self.sign(repo, AUDIT, agent_type="drive:auditor", agent_id=agent_id)
        if commit:
            self.commit(repo, "drive(report): final audit round {}".format(round_number))

    def test_a_go_from_the_instance_that_wrote_the_no_go_fails(self):
        repo = self.make_final_run(status="stopped")
        self.audit_round(repo, "fail", 1, "agent-audit-1")
        self.audit_round(repo, "pass", 2, "agent-audit-1")
        lines = self.lint_lines(repo, "--final")
        self.assertTrue(self.fails(lines, "final audit", "same agent instance", "agent-audit-1"), "\n".join(lines))

    def test_a_go_from_a_fresh_instance_passes(self):
        repo = self.make_final_run()
        self.audit_round(repo, "fail", 1, "agent-audit-1")
        self.audit_round(repo, "pass", 2, "agent-audit-2")
        lines = self.lint_lines(repo, "--final")
        self.assertFalse(self.fails(lines, "final audit"), "\n".join(lines))

    def test_an_uncommitted_no_go_is_recovered_from_the_agents_write_call(self):
        repo = self.make_final_run()
        self.audit_round(repo, "fail", 1, "agent-audit-1", how="write", commit=False)
        self.audit_round(repo, "pass", 1, "agent-audit-1")
        self.assertTrue(self.fails(self.lint_lines(repo, "--final"), "same agent instance"))

    def test_an_unrecoverable_earlier_round_by_the_same_instance_fails_on_the_round_number(self):
        repo = self.make_final_run()
        self.audit_round(repo, "fail", 1, "agent-audit-1", commit=False)
        self.audit_round(repo, "pass", 2, "agent-audit-1")
        self.assertTrue(self.fails(self.lint_lines(repo, "--final"), "says round 2", "also wrote the round before"))
        repo.rename(self.tmp / "first")
        fresh = self.make_final_run()
        self.audit_round(fresh, "fail", 1, "agent-audit-1", commit=False)
        self.audit_round(fresh, "pass", 2, "agent-audit-2")
        self.assertFalse(self.fails(self.lint_lines(fresh, "--final"), "final audit"))

    def test_an_auditor_correcting_its_own_passing_audit_is_not_a_reaudit(self):
        repo = self.make_final_run()
        self.audit_round(repo, "pass", 1, "agent-audit")
        self.assertFalse(self.fails(self.lint_lines(repo, "--final"), "final audit"))


class SlugNamesTheDeliverableTests(Cli, DriveTestCase):
    """init named the linkkeeper run build-linkkeeper-a-small-self-hosted-bookmarks-man by cutting the goal at 50 characters."""

    def init_slug(self, goal):
        repo = self.new_repo("repo-{}".format(len(list(self.tmp.iterdir()))))
        self.write(repo, "README.md", "x\n")
        self.commit(repo, "chore: start")
        result = self.run_drive("init", "--goal", goal, "--size", "M", cwd=repo)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        title = (repo / ".drive/GOAL.md").read_text().splitlines()[0]
        marker = json.loads((repo / ".drive/local/active").read_text())
        self.assertEqual(title, "# GOAL · " + marker["slug"])
        return repo, marker["slug"]

    def test_the_slug_is_the_first_noun_phrase_after_the_verb(self):
        goal = ("Build linkkeeper, a small self-hosted bookmarks manager with full-text search, browser import and export, "
                "and a web UI.")
        self.assertEqual(self.init_slug(goal)[1], "linkkeeper")
        self.assertEqual(self.init_slug("Fix the flaky bulk lookup test")[1], "flaky-bulk-lookup-test")

    def test_the_slug_stops_at_a_word_boundary_within_forty_characters(self):
        goal = "Write comprehensive administrator documentation handbook chapters covering every deployment option"
        _, slug = self.init_slug(goal)
        self.assertLessEqual(len(slug), 40)
        words = set(re.findall(r"[a-z0-9]+", goal.lower()))
        self.assertTrue(all(part in words for part in slug.split("-")), slug)
        _, hyphenated = self.init_slug("Build self-hosted-multi-tenant-analytics-dashboard-platform-service for teams")
        self.assertLessEqual(len(hyphenated), 40)
        self.assertTrue(all(part in {"self", "hosted", "multi", "tenant", "analytics", "dashboard", "platform", "service"}
                            for part in hyphenated.split("-")), hyphenated)

    def test_the_same_goal_still_resumes_and_an_older_goal_file_resumes_by_its_legacy_slug(self):
        goal = "Build linkkeeper, a small self-hosted bookmarks manager"
        repo, slug = self.init_slug(goal)
        again = self.run_drive("init", "--goal", goal.upper(), cwd=repo)
        self.assertIn("Same goal", again.stdout)
        legacy = drive.slugify(goal, 50)
        text = (repo / ".drive/GOAL.md").read_text().replace("# GOAL · " + slug, "# GOAL · " + legacy)
        text = "\n".join(l for l in text.splitlines() if not l.startswith("goal:")) + "\n"
        self.write(repo, ".drive/GOAL.md", text)
        resumed = self.run_drive("init", "--goal", goal, cwd=repo)
        self.assertEqual(resumed.returncode, 0, resumed.stdout + resumed.stderr)
        self.assertIn("Same goal", resumed.stdout)


class SpendLineNamesItsSourceTests(Cli, DriveTestCase):
    """RESEARCH.md claimed about $0.35 for a lane of about 85 tool calls; no figure came from a recorded total."""

    MESSAGE = ("a spend figure must come from a recorded total (total_cost_usd, /usage, or the harness budget line) "
               "or say not measured")

    def test_an_unsourced_dollar_figure_warns_and_does_not_fail(self):
        repo = self.make_run()
        self.write(repo, ".drive/RESEARCH.md", "# RESEARCH · proj\n\n## Ledger\n- 2026-09-15 · research · lanes: 1 · "
                   "freshness: measured today · spend: ~85 tool calls, 0 Tavily credits, about $0.35 of the budget\n")
        result = self.run_drive("lint", cwd=repo)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.warns(result.stdout.splitlines(), "RESEARCH.md line 4"),
                         ["warn RESEARCH.md line 4: " + self.MESSAGE])

    def test_report_spend_section_is_judged_sentence_by_sentence(self):
        repo = self.make_final_run()
        report = (repo / ".drive/REPORT.md").read_text().replace(
            "## Spend\n38 turns\n", "## Spend\nAbout $330 of the $400 limit. Maker subagents: 36 starts recorded.\n")
        self.write(repo, ".drive/REPORT.md", report)
        self.assertTrue(self.warns(self.lint_lines(repo), "REPORT.md line", self.MESSAGE))

    def test_recorded_or_unmeasured_spend_does_not_warn(self):
        repo = self.make_run()
        self.write(repo, ".drive/RESEARCH.md", "# RESEARCH · proj\n\n- spend: $12.40 from total_cost_usd in the result event\n"
                   "- spend: not measured; about 85 tool calls\n- spend: 22 tool calls\n")
        state = (repo / ".drive/STATE.md").read_text().replace("## Resume here", "spend: $41 at the harness budget line\n\n## Resume here")
        self.write(repo, ".drive/STATE.md", state)
        self.assertFalse(self.warns(self.lint_lines(repo), "spend figure"))


class PhaseNamesTheEarliestOpenGateTests(Cli, DriveTestCase):
    """STATE.md's phase moved backwards (build, test-plan, decompose) while phases overlapped."""

    def test_a_phase_past_the_earliest_open_plan_line_warns_naming_it(self):
        repo = self.make_run()
        self.set_state(repo, phase="verify")
        result = self.run_drive("lint", cwd=repo)
        self.assertEqual(result.returncode, 0, result.stdout)
        warned = self.warns(result.stdout.splitlines(), "STATE.md", "phase verify is later than the earliest open plan line")
        self.assertTrue(warned, result.stdout)
        self.assertIn("- [ ] build · artifact: code and tests", warned[0])
        self.assertIn("set phase: build", warned[0])

    def test_the_earliest_open_phase_does_not_warn(self):
        repo = self.make_run()
        self.assertFalse(self.warns(self.lint_lines(repo), "earliest open plan line"))

    def test_plan_order_wins_over_phases_order_for_a_fix(self):
        repo = self.make_run()
        self.edit_goal(repo, "- [ ] build · artifact: code and tests · exit: gates green · checker: verifier",
                       "- [x] reproduce · artifact: .drive/HUNT.md · exit: repro fails · checker: orchestrator\n"
                       "- [x] diagnose · artifact: .drive/HUNT.md · exit: one confirmed row · checker: verifier\n"
                       "- [ ] fix · artifact: code and tests · exit: gates green · checker: verifier")
        self.set_state(repo, phase="fix")
        self.assertFalse(self.warns(self.lint_lines(repo), "earliest open plan line"))
        self.set_state(repo, phase="report")
        self.assertTrue(self.warns(self.lint_lines(repo), "phase report is later", "set phase: fix"))
