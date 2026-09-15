"""Lint tests, including severe tests that try to get a false claim past the checks."""
import json
import shutil
from pathlib import Path

from helpers import DriveTestCase, TODAY, drive, iso, proof_manifest, state_md, verdict

KEY = "expired-token-is-rejected"


class BaselineTests(DriveTestCase):
    def test_fixture_passes_stop_lint(self):
        repo = self.make_run()
        self.assertNoFailure(self.lint(repo, "stop"))

    def test_final_fixture_passes_final_lint(self):
        repo = self.make_final_run()
        self.assertNoFailure(self.lint(repo, "final"))

    def test_cli_exit_codes_and_json(self):
        repo = self.make_run()
        ok = self.run_drive("lint", "--stop", "--json", cwd=repo)
        self.assertEqual(ok.returncode, 0, ok.stdout)
        self.assertTrue(json.loads(ok.stdout)["ok"])
        (repo / ".drive" / "STATE.md").unlink()
        bad = self.run_drive("lint", cwd=repo)
        self.assertEqual(bad.returncode, 1)
        self.assertIn("STATE.md", bad.stdout)
        unknown = self.run_drive("lint", "--gate", "mitigate", cwd=repo)
        self.assertEqual(unknown.returncode, 2)

    def test_missing_drive_directory_fails(self):
        repo = self.new_repo()
        self.assertFails(self.lint(repo), "does not exist")


class LiveProofTests(DriveTestCase):
    def promote_to_live(self, repo, manifest, signed=True):
        text = (repo / ".drive/STATUS.md").read_text()
        text = text.replace("| Local Proof | test:", "| Live Proof | live:.drive/proofs/{}; test:".format(KEY))
        self.write(repo, ".drive/STATUS.md", text)
        self.write(repo, ".drive/proofs/{}/r1/verdict.json".format(KEY), verdict(KEY, rung="Live Proof"))
        self.sign(repo, ".drive/proofs/{}/r1/verdict.json".format(KEY))
        self.write_live_proof(repo, KEY, manifest, signed=signed)

    def test_live_proof_backed_by_simulator_bundle_fails(self):
        repo = self.make_run()
        self.promote_to_live(repo, proof_manifest(KEY, environment="simulator", commit=self.code_sha))
        self.assertFails(self.lint(repo), "local-only work is never Live Proof")

    def test_live_proof_labelled_live_but_pointing_at_localhost_fails(self):
        repo = self.make_run()
        self.promote_to_live(repo, proof_manifest(KEY, target="http://localhost:8787", commit=self.code_sha))
        self.assertFails(self.lint(repo), "is a local address")

    def test_live_proof_without_shim_answer_fails(self):
        repo = self.make_run()
        manifest = proof_manifest(KEY, commit=self.code_sha)
        del manifest["shim_differences"]
        self.promote_to_live(repo, manifest)
        self.assertFails(self.lint(repo), "does not answer shim_differences")

    def test_live_proof_with_empty_shim_answer_and_no_note_fails(self):
        repo = self.make_run()
        self.promote_to_live(repo, proof_manifest(KEY, commit=self.code_sha, shim=[]))
        self.assertFails(self.lint(repo), "empty shim_differences")

    def test_live_proof_for_another_key_fails(self):
        repo = self.make_run()
        manifest = proof_manifest("session-list-shows-active-sessions", commit=self.code_sha)
        self.promote_to_live(repo, manifest)
        self.assertFails(self.lint(repo), "belongs to")

    def test_live_proof_produced_by_the_maker_fails(self):
        repo = self.make_run()
        manifest = proof_manifest(KEY, commit=self.code_sha)
        manifest["produced_by"] = "implementer"
        self.promote_to_live(repo, manifest)
        self.assertFails(self.lint(repo), "not produced by a checker")

    def test_real_live_proof_passes(self):
        repo = self.make_run()
        self.promote_to_live(repo, proof_manifest(KEY, commit=self.code_sha))
        self.assertNoFailure(self.lint(repo))

    def test_live_proof_without_live_token_fails(self):
        repo = self.make_run()
        text = (repo / ".drive/STATUS.md").read_text().replace("| Local Proof |", "| Live Proof |")
        self.write(repo, ".drive/STATUS.md", text)
        self.assertFails(self.lint(repo), "needs live:")


class VerdictTests(DriveTestCase):
    def rewrite_verdict(self, repo, data, round_dir="r1"):
        self.write(repo, ".drive/proofs/{}/{}/verdict.json".format(KEY, round_dir), data)
        self.sign(repo, ".drive/proofs/{}/{}/verdict.json".format(KEY, round_dir))

    def test_pass_verdict_with_empty_ran_fails(self):
        repo = self.make_run()
        self.rewrite_verdict(repo, verdict(KEY, ran=[]))
        self.assertFails(self.lint(repo), "ran no commands")

    def test_pass_verdict_without_the_full_suite_fails(self):
        repo = self.make_run()
        self.rewrite_verdict(repo, verdict(KEY, ran=[{"cmd": "echo ok", "exit": 0}]))
        self.assertFails(self.lint(repo), "does not show the full-suite command")

    def test_failing_verdict_cannot_back_local_proof(self):
        repo = self.make_run()
        self.rewrite_verdict(repo, verdict(KEY, verdict_value="fail"))
        self.assertFails(self.lint(repo), "not pass")

    def test_claim_without_refutation_attempt_fails(self):
        repo = self.make_run()
        data = verdict(KEY)
        data["claims"][0]["refutations_attempted"] = []
        self.rewrite_verdict(repo, data)
        self.assertFails(self.lint(repo), "records no refutation attempt")

    def test_blocking_gap_in_pass_verdict_fails(self):
        repo = self.make_run()
        gap = {"id": "cache-leak", "claim": KEY, "severity": "blocking", "what": "tokens survive logout",
               "where": "src/auth.py:2", "repro": ["pytest -k logout"], "confidence": 75}
        self.rewrite_verdict(repo, verdict(KEY, gaps=[gap]))
        self.assertFails(self.lint(repo), "blocking gap")

    def test_unresolved_harness_kindness_fails(self):
        repo = self.make_run()
        data = verdict(KEY)
        data["harness_kindness"] = [{"shim": "in-memory store", "kinder_than_production_how": "no expiry", "severity": "blocking"}]
        self.rewrite_verdict(repo, data)
        self.assertFails(self.lint(repo), "kinder than production")

    def test_verdict_for_another_unit_fails(self):
        repo = self.make_run()
        self.rewrite_verdict(repo, verdict("session-list-shows-active-sessions"))
        self.assertFails(self.lint(repo), "does not cover")

    def test_citing_an_older_round_when_a_later_one_exists_fails(self):
        repo = self.make_run()
        self.rewrite_verdict(repo, verdict(KEY, verdict_value="fail", round_number=2), round_dir="r2")
        self.assertFails(self.lint(repo), "is not the latest round")

    def test_missing_verdict_fails(self):
        repo = self.make_run()
        text = (repo / ".drive/STATUS.md").read_text().replace(
            "verdict:.drive/proofs/{}/r1/verdict.json; ".format(KEY), "")
        self.write(repo, ".drive/STATUS.md", text)
        self.assertFails(self.lint(repo), "needs a verdict:")

    def test_verdict_outside_the_repository_fails(self):
        repo = self.make_run()
        outside = self.tmp / "elsewhere" / "verdict.json"
        self.write(self.tmp, "elsewhere/verdict.json", verdict(KEY))
        text = (repo / ".drive/STATUS.md").read_text().replace(
            ".drive/proofs/{}/r1/verdict.json".format(KEY), str(outside))
        self.write(repo, ".drive/STATUS.md", text)
        self.assertFails(self.lint(repo), "outside the repository")


class StatusRowTests(DriveTestCase):
    def test_deleted_row_compared_with_head_fails(self):
        repo = self.make_run()
        lines = [l for l in (repo / ".drive/STATUS.md").read_text().splitlines() if not l.startswith("| admin-can-revoke-sessions")]
        self.write(repo, ".drive/STATUS.md", "\n".join(lines) + "\n")
        self.assertFails(self.lint(repo), "existed at HEAD and is gone")

    def test_done_row_without_review_fails(self):
        repo = self.make_run()
        text = (repo / ".drive/STATUS.md").read_text().replace("| Local Proof |", "| Done |").replace("| KEY | y |", "")
        text = text.replace("| An expired token is rejected with 401 | y |", "| An expired token is rejected with 401 | n |")
        self.write(repo, ".drive/STATUS.md", text)
        self.assertFails(self.lint(repo), "Done needs review:")

    def test_local_proof_without_severe_test_fails(self):
        repo = self.make_run()
        text = (repo / ".drive/STATUS.md").read_text().replace("severe:tests/test_auth.py::forged expiry is rejected; ", "")
        self.write(repo, ".drive/STATUS.md", text)
        self.assertFails(self.lint(repo), "needs a severe: test")

    def test_ui_row_at_local_proof_needs_a_screenshot(self):
        repo = self.make_run()
        text = (repo / ".drive/STATUS.md").read_text().replace("| An expired token", "| [ui] An expired token")
        self.write(repo, ".drive/STATUS.md", text)
        self.assertFails(self.lint(repo), "needs shot:")

    def test_test_name_must_match_as_written_not_as_slug(self):
        repo = self.make_run()
        text = (repo / ".drive/STATUS.md").read_text().replace("::session list shows active sessions", "::session_list_shows_active_sessions")
        self.write(repo, ".drive/STATUS.md", text)
        self.assertFails(self.lint(repo), "does not appear in tests/test_auth.py")

    def test_commit_that_does_not_exist_fails(self):
        repo = self.make_run()
        text = (repo / ".drive/STATUS.md").read_text().replace("commit:{}".format(self.code_sha), "commit:deadbee", 1)
        self.write(repo, ".drive/STATUS.md", text)
        self.assertFails(self.lint(repo), "commit deadbee does not exist")

    def test_unknown_token_fails(self):
        repo = self.make_run()
        text = (repo / ".drive/STATUS.md").read_text().replace("| Missing |  |", "| Missing | pr:#12 |")
        self.write(repo, ".drive/STATUS.md", text)
        self.assertFails(self.lint(repo), "is not an evidence token")

    def test_planned_test_on_partial_row_fails(self):
        repo = self.make_run()
        text = (repo / ".drive/STATUS.md").read_text().replace(
            "test:tests/test_auth.py::session list shows active sessions;",
            "test:tests/test_auth.py::session list shows active sessions; planned:tests/test_list.py::hides revoked sessions;")
        self.write(repo, ".drive/STATUS.md", text)
        self.assertFails(self.lint(repo), "planned: tests are allowed only on rows below Partial")

    def test_dropped_row_without_why_fails(self):
        repo = self.make_run()
        text = (repo / ".drive/STATUS.md").read_text().replace("| Missing |  |", "| Dropped |  |")
        self.write(repo, ".drive/STATUS.md", text)
        self.assertFails(self.lint(repo), "Dropped without why:")

    def test_device_only_row_may_sit_at_local_proof_but_never_done(self):
        repo = self.make_run()
        text = (repo / ".drive/STATUS.md").read_text().replace("commit:{} |".format(self.code_sha),
                                                               "commit:{}; why:device-only:needs a physical phone |".format(self.code_sha), 1)
        self.write(repo, ".drive/STATUS.md", text)
        self.assertNoFailure(self.lint(repo))
        self.write(repo, ".drive/STATUS.md", text.replace("| Local Proof |", "| Done |"))
        self.assertFails(self.lint(repo), "never Done")

    def test_work_verb_claim_warns(self):
        repo = self.make_run()
        text = (repo / ".drive/STATUS.md").read_text().replace("| An admin can revoke any session |", "| Implement session revocation |")
        self.write(repo, ".drive/STATUS.md", text)
        findings = self.lint(repo)
        self.assertIn("describes work", self.messages(findings, "warn"))

    def test_citations_json_under_reviews_is_accepted_as_test(self):
        repo = self.make_run()
        self.write(repo, ".drive/reviews/2026-09-14-citations-pricing.json", {"verdict": "pass"})
        self.sign(repo, ".drive/reviews/2026-09-14-citations-pricing.json", agent_type="drive:grader")
        text = (repo / ".drive/STATUS.md").read_text().replace(
            "test:tests/test_auth.py::session list shows active sessions",
            "test:.drive/reviews/2026-09-14-citations-pricing.json::every citation resolves")
        self.write(repo, ".drive/STATUS.md", text)
        self.assertNoFailure(self.lint(repo))


class NarrowingTests(DriveTestCase):
    def flip_live(self, repo):
        text = (repo / ".drive/STATUS.md").read_text().replace(
            "| An admin can revoke any session | y |", "| An admin can revoke any session | n |")
        self.write(repo, ".drive/STATUS.md", text)

    def test_live_flip_without_decision_fails(self):
        repo = self.make_run()
        self.flip_live(repo)
        self.assertFails(self.lint(repo), "live changed from y to n since HEAD without a DECISIONS.md entry")

    def test_live_flip_with_decision_passes(self):
        repo = self.make_run()
        self.flip_live(repo)
        with open(repo / ".drive/DECISIONS.md", "a") as handle:
            handle.write("\n## 2026-09-14 · Prove revocation locally only\n- Context: no staging admin account.\n"
                         "- Decision: lower live to n.\n- Rejected: waiting for an account.\n"
                         "- Undo: set live back to y · reversal cost: low.\n- Evidence: none\n"
                         "- Narrows: live y→n on admin-can-revoke-sessions\n")
        self.assertNoFailure(self.lint(repo))

    def test_new_dropped_row_without_decision_fails(self):
        repo = self.make_run()
        text = (repo / ".drive/STATUS.md").read_text().replace("| Missing |  |", "| Dropped | why:out of budget |")
        self.write(repo, ".drive/STATUS.md", text)
        self.assertFails(self.lint(repo), "became Dropped since HEAD without a DECISIONS.md entry")

    def test_removed_plan_phase_without_decision_fails(self):
        repo = self.make_run()
        text = "\n".join(l for l in (repo / ".drive/GOAL.md").read_text().splitlines() if "· verify ·" not in l and not l.startswith("- [ ] verify")) + "\n"
        self.write(repo, ".drive/GOAL.md", text)
        self.assertFails(self.lint(repo), "lost the verify phase")

    def test_decision_entry_altered_after_commit_fails(self):
        repo = self.make_run()
        text = (repo / ".drive/DECISIONS.md").read_text().replace("use hmac.compare_digest", "use plain equality")
        self.write(repo, ".drive/DECISIONS.md", text)
        self.assertFails(self.lint(repo), "was altered after it was committed")


class StateTests(DriveTestCase):
    def test_stale_state_after_a_code_commit_fails(self):
        repo = self.make_run()
        self.write(repo, "src/auth.py", "def check(token, now):\n    return token.expires_at >= now\n")
        self.commit(repo, "fix(auth): boundary", offset_seconds=3600)
        self.assertFails(self.lint(repo), "is stale")

    def test_state_commit_two_code_commits_behind_fails(self):
        repo = self.make_run()
        for number in (1, 2):
            self.write(repo, "src/extra{}.py".format(number), "x = {}\n".format(number))
            self.commit(repo, "feat: extra {}".format(number))
        self.set_state(repo, commit=self.code_sha)
        self.assertFails(self.lint(repo), "code commits behind HEAD")

    def test_secret_shaped_string_in_state_fails(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha,
                       extra_facts="- The staging key is sk-ant-api03-AAAAAAAAAAAAAAAAAAAAAAAAAAAA. Verified: copied from the dashboard.\n")
        self.assertFails(self.lint(repo), "looks like an API key")

    def test_github_token_in_a_proof_fails(self):
        repo = self.make_run()
        self.write(repo, ".drive/proofs/{}/r1/commands.log".format(KEY), "curl -H 'Authorization: token ghp_" + "a" * 36 + "'\n")
        self.assertFails(self.lint(repo), "GitHub token")

    def test_secret_under_local_is_not_scanned(self):
        repo = self.make_run()
        self.write(repo, ".drive/local/logs/raw.log", "sk-ant-api03-AAAAAAAAAAAAAAAAAAAAAAAAAAAA\n")
        self.assertNoFailure(self.lint(repo), "looks like an API key")

    def test_state_over_budget_fails(self):
        repo = self.make_run()
        facts = "".join("- Fact {} holds. Verified: checked on 2026-09-14.\n".format(n) for n in range(160))
        self.set_state(repo, commit=self.code_sha, extra_facts=facts)
        self.assertFails(self.lint(repo), "the budget is 150")

    def test_unknown_status_fails(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha, status="finished")
        self.assertFails(self.lint(repo), "status 'finished' must be one of")

    def test_fact_without_verification_fails(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha, extra_facts="- The cache is safe.\n")
        self.assertFails(self.lint(repo), "every verified fact names how it was verified")

    def test_second_workaround_without_investigation_fails(self):
        repo = self.make_run()
        text = state_md(self.code_sha).replace("|---|---|---|---|---|",
                                               "|---|---|---|---|---|\n| session store times out in tests | raised the timeout | implementer | 2026-09-14 | 2 |")
        self.write(repo, ".drive/STATE.md", text)
        self.assertFails(self.lint(repo), "Second time is the bug")

    def test_template_placeholder_left_in_state_header_fails(self):
        repo = self.make_run()
        text = state_md(self.code_sha).replace("next: Run the verifier on the session revocation claim.", "next: <one imperative sentence>")
        self.write(repo, ".drive/STATE.md", text)
        self.assertFails(self.lint(repo), "still holds a template placeholder")


class HygieneTests(DriveTestCase):
    def test_leftover_worktree_fails_stop_lint(self):
        repo = self.make_run()
        self.git(repo, "worktree", "add", "-q", "-b", "drive/arm", str(self.tmp / "arm"), "HEAD")
        findings = self.lint(repo, "stop")
        self.assertFails(findings, "worktree(s) created during the run")
        self.assertFails(findings, "local branch(es) that .drive/local/baseline.json does not list: drive/arm")

    def test_uncommitted_change_fails_stop_lint(self):
        repo = self.make_run()
        self.write(repo, "src/new.py", "x = 1\n")
        self.assertFails(self.lint(repo, "stop"), "uncommitted changes made during the run: src/new.py")

    def test_changes_under_local_are_ignored(self):
        repo = self.make_run()
        self.write(repo, ".drive/local/logs/run.log", "noise\n")
        self.assertNoFailure(self.lint(repo, "stop"))

    def test_unmerged_worker_report_fails(self):
        repo = self.make_run()
        self.set_state(repo, commit=self.code_sha, updated="2026-01-01T00:00:00Z")
        self.commit(repo, "drive: state")
        self.write(repo, ".drive/local/workers/implementer-1/report.md", "done\n")
        self.assertFails(self.lint(repo, "stop"), "is newer than STATE.md")

    def test_local_not_ignored_fails(self):
        repo = self.make_run()
        self.write(repo, ".gitignore", "")
        self.commit(repo, "chore: drop ignore")
        self.assertFails(self.lint(repo, "stop"), "does not ignore .drive/local/")


class GoalTests(DriveTestCase):
    def test_restate_line_that_is_neither_quoted_nor_assumption_fails(self):
        repo = self.make_run()
        text = (repo / ".drive/GOAL.md").read_text().replace('- outcome: "Reject expired tokens"', "- outcome: reject expired tokens")
        self.write(repo, ".drive/GOAL.md", text)
        self.assertFails(self.lint(repo), "Restate 'outcome' must be quoted")

    def test_trait_outside_vocabulary_fails(self):
        repo = self.make_run()
        text = (repo / ".drive/GOAL.md").read_text().replace("suspected: [ui]", "suspected: [mobile]")
        self.write(repo, ".drive/GOAL.md", text)
        self.assertFails(self.lint(repo), "'mobile' is not a trait")

    def test_plan_line_grammar_and_roster_checker(self):
        repo = self.make_run()
        text = (repo / ".drive/GOAL.md").read_text()
        good = text.replace("· checker: verifier\n- [ ] report", "· checker: drive:severe-tester\n- [ ] report")
        self.write(repo, ".drive/GOAL.md", good)
        self.assertNoFailure(self.lint(repo), "checker")
        bad = text.replace("- [ ] build · artifact: code and tests · exit: gates green · checker: verifier", "- [ ] build: write the code")
        self.write(repo, ".drive/GOAL.md", bad)
        self.assertFails(self.lint(repo), "plan line")

    def test_missing_intake_commit_fails(self):
        repo = self.make_run()
        self.git(repo, "commit", "-q", "--amend", "-m", "drive: state")
        text = (repo / ".drive/GOAL.md").read_text().replace("GOAL · session-auth", "GOAL · other-goal")
        self.write(repo, ".drive/GOAL.md", text)
        self.assertFails(self.lint(repo), "has no drive(intake): other-goal commit")

    def test_sub_goal_sections_parse(self):
        repo = self.make_run()
        text = (repo / ".drive/GOAL.md").read_text().replace("## Classification", "## Classification · session-auth").replace(
            "## Plan", "## Plan · session-auth")
        self.write(repo, ".drive/GOAL.md", text)
        self.assertNoFailure(self.lint(repo))

    def test_final_requires_ticked_plan_for_done(self):
        repo = self.make_final_run()
        text = (repo / ".drive/GOAL.md").read_text().replace("- [x] verify", "- [ ] verify")
        self.write(repo, ".drive/GOAL.md", text)
        self.assertFails(self.lint(repo, "final"), "is not ticked")


class FinalTests(DriveTestCase):
    def demote_list_row(self, repo, reason=""):
        text = (repo / ".drive/STATUS.md").read_text()
        lines = []
        for line in text.splitlines():
            if line.startswith("| session-list-shows-active-sessions"):
                line = "| session-list-shows-active-sessions | The session list shows only active sessions | n | Partial | " \
                       "test:tests/test_auth.py::session list shows active sessions; commit:{}{} | {} |".format(self.code_sha, reason, TODAY)
            lines.append(line)
        self.write(repo, ".drive/STATUS.md", "\n".join(lines) + "\n")
        self.write(repo, ".drive/REPORT.md", self.report_md({"Done": 1, "Partial": 1, "Dropped": 1},
                                                             outcome="Stopped because the list query needs a database the budget did not cover."))

    def test_done_with_a_partial_row_fails(self):
        repo = self.make_final_run()
        self.demote_list_row(repo)
        self.commit(repo, "drive: demote")
        self.assertFails(self.lint(repo, "final"), "every row of a done run ends Done or Dropped")

    def test_stopped_with_unexplained_partial_row_fails(self):
        repo = self.make_final_run()
        self.demote_list_row(repo)
        self.set_state(repo, commit=self.code_sha, status="stopped", phase="report")
        self.commit(repo, "drive: stopped")
        self.assertFails(self.lint(repo, "final"), "in a stopped run with no recorded reason")

    def test_stopped_with_why_token_passes(self):
        repo = self.make_final_run()
        self.demote_list_row(repo, reason="; why:the list query needs a staging database")
        self.set_state(repo, commit=self.code_sha, status="stopped", phase="report")
        self.commit(repo, "drive: stopped")
        self.assertNoFailure(self.lint(repo, "final"))

    def test_stopped_report_must_say_stopped_because(self):
        repo = self.make_final_run()
        self.demote_list_row(repo, reason="; why:the list query needs a staging database")
        self.write(repo, ".drive/REPORT.md", self.report_md({"Done": 1, "Partial": 1, "Dropped": 1}))
        self.set_state(repo, commit=self.code_sha, status="stopped", phase="report")
        self.commit(repo, "drive: stopped")
        self.assertFails(self.lint(repo, "final"), "opens with 'Stopped because'")

    def test_report_counts_must_match_status(self):
        repo = self.make_final_run()
        self.write(repo, ".drive/REPORT.md", self.report_md({"Done": 3}))
        self.commit(repo, "drive: wrong report")
        self.assertFails(self.lint(repo, "final"), "the Ladder table says")

    def test_final_requires_retro(self):
        repo = self.make_final_run()
        (repo / ".drive/reviews/2026-09-14-retro.md").unlink()
        self.commit(repo, "drive: no retro")
        self.assertFails(self.lint(repo, "final"), "has no <date>-retro.md")

    def test_final_audit_older_than_last_code_commit_fails(self):
        repo = self.make_final_run()
        self.write(repo, "src/late.py", "x = 1\n")
        sha = self.commit(repo, "feat: late change", offset_seconds=5)
        self.set_state(repo, commit=sha, status="done", phase="report", updated=iso(10))
        self.commit(repo, "drive: state", offset_seconds=10)
        self.assertFails(self.lint(repo, "final"), "predates the latest code commit")

    def test_open_investigation_blocks_final(self):
        repo = self.make_final_run()
        self.write(repo, ".drive/investigations/2026-09-14-login-timeout.md", INVESTIGATION_OPEN)
        self.commit(repo, "drive: investigation")
        self.assertFails(self.lint(repo, "final"), "is still open")

    def test_final_requires_done_or_stopped_status(self):
        repo = self.make_final_run(status="running")
        self.assertFails(self.lint(repo, "final"), "the final check applies to a run marked done or stopped")


INVESTIGATION_OPEN = """# The login request timed out after 30 seconds on staging
Status: open
Trigger: green-check-failed
Detected: 2026-09-14T10:00:00Z by verifier via the live check
Got past: the local suite, which uses an in-memory store
Timebox: 60 minutes

## Fail
- Observed: curl exited 28 after 30 s
- Expected: a 200 within 800 ms
- Reproduction: curl -m 30 https://staging.example.test/login, 3 of 10 runs

## Investigate
- Candidate causes, each with the observation that separates it from the others:

## Verify

## Fix

## Distill

## Gate log
- fail recorded 2026-09-14T10:00:00Z verifier
"""


class InvestigationTests(DriveTestCase):
    def test_vague_mechanism_fails(self):
        repo = self.make_run()
        text = INVESTIGATION_OPEN.replace("Status: open", "Status: diagnosed").replace(
            "- Candidate causes, each with the observation that separates it from the others:",
            "- Candidate causes, each with the observation that separates it from the others:\n  1. pool size · separated by: pool metrics\n"
            "  2. DNS · separated by: dig timing\n  3. cold start · separated by: warm request\n- Mechanism: flaky")
        self.write(repo, ".drive/investigations/2026-09-14-login-timeout.md", text)
        self.assertFails(self.lint(repo), "is a place to look, not a cause")

    def test_too_few_candidates_fails(self):
        repo = self.make_run()
        text = INVESTIGATION_OPEN.replace("Status: open", "Status: diagnosed").replace(
            "- Candidate causes, each with the observation that separates it from the others:",
            "- Candidate causes, each with the observation that separates it from the others:\n  1. pool size · separated by: pool metrics\n"
            "- Mechanism: the connection pool holds five connections and the sixth request waits for the 30 s pool timeout")
        self.write(repo, ".drive/investigations/2026-09-14-login-timeout.md", text)
        self.assertFails(self.lint(repo), "it needs at least three")


class SpecGateTests(DriveTestCase):
    SPEC = """# Sessions · specification

## Requirements

### Expired token is rejected
Intent.

**Expired token**
Given a token that expired. When it is sent. Then the response is 401.

What would prove this wrong

**Token expiring this second**
Given a token that expires now. When it is sent. Then the response is 401.

### Session list shows active sessions
Intent.

What would prove this wrong

**Revoked session**
Given a revoked session. When the list loads. Then it is absent.

### Admin can revoke sessions
Intent.

What would prove this wrong

**Other tenant**
Given another tenant's session. When an admin revokes it. Then it is revoked.

## Assumptions

### We assume admins are already authenticated
Because: the admin app has its own login.
"""

    def test_spec_and_status_agree(self):
        repo = self.make_run()
        self.write(repo, ".drive/SPEC.md", self.SPEC)
        self.assertNoFailure(self.lint(repo, gate="spec"))

    def test_heading_without_status_row_fails(self):
        repo = self.make_run()
        self.write(repo, ".drive/SPEC.md", self.SPEC + "\n## Requirements · admin\n\n### Revoking a session logs the admin out elsewhere\n\nWhat would prove this wrong\n\n**Two tabs**\nGiven two tabs.\n")
        self.assertFails(self.lint(repo, gate="spec"), "has no STATUS row")

    def test_status_row_without_heading_fails(self):
        repo = self.make_run()
        self.write(repo, ".drive/SPEC.md", self.SPEC.replace("### Admin can revoke sessions", "### Admins may revoke sessions of any tenant"))
        findings = self.lint(repo, gate="spec")
        self.assertFails(findings, "STATUS admin-can-revoke-sessions: maps to no claim heading")

    def test_requirement_without_refutation_fails(self):
        repo = self.make_run()
        spec = self.SPEC.replace("What would prove this wrong\n\n**Other tenant**\nGiven another tenant's session. When an admin revokes it. Then it is revoked.\n", "")
        self.write(repo, ".drive/SPEC.md", spec)
        self.assertFails(self.lint(repo, gate="spec"), "has no 'What would prove this wrong'")

    def test_formerly_line_keeps_the_old_key(self):
        repo = self.make_run()
        spec = self.SPEC.replace("### Session list shows active sessions",
                                 "### Session list shows only the active sessions\nFormerly: \"Session list shows active sessions\"")
        self.write(repo, ".drive/SPEC.md", spec)
        self.assertNoFailure(self.lint(repo, gate="spec"))


class GateTests(DriveTestCase):
    def test_verify_gate_needs_local_proof(self):
        repo = self.make_run()
        self.assertFails(self.lint(repo, gate="verify"), "this gate needs Local Proof")

    def test_live_proof_gate_accepts_device_only_at_local_proof(self):
        repo = self.make_run()
        text = (repo / ".drive/STATUS.md").read_text().replace("commit:{} |".format(self.code_sha),
                                                               "commit:{}; why:device-only:needs a phone |".format(self.code_sha), 1)
        text = text.replace("| An admin can revoke any session | y |", "| An admin can revoke any session | n |")
        self.write(repo, ".drive/STATUS.md", text)
        with open(repo / ".drive/DECISIONS.md", "a") as handle:
            handle.write("\n## 2026-09-14 · Revocation is local only\n- Decision: lower live.\n- Undo: set y · reversal cost: low.\n- Narrows: live y→n on admin-can-revoke-sessions\n")
        findings = self.lint(repo, gate="live-proof")
        self.assertNoFailure(findings, "STATUS expired-token-is-rejected: is Local Proof")

    def test_decompose_gate_detects_overlap(self):
        repo = self.make_run()
        brief = (Path(drive.TEMPLATES) / "package-brief.md").read_text()
        for pkg, glob in (("export-api", "src/export/**"), ("export-ui", "src/export/ui/**")):
            text = brief.replace("<package id>", pkg).replace("- `<path or glob>`", "- `{}`".format(glob), 1)
            self.write(repo, ".drive/packages/{}/brief.md".format(pkg), text)
        self.write(repo, ".drive/packages/index.md", "# Packages · session-auth\n\n| id | wave | claim key | owns | depends on | hard | status |\n"
                   "|----|------|-----------|------|------------|------|--------|\n"
                   "| export-api | 1 | expired-token-is-rejected | `src/export/**` | none | no | planned |\n"
                   "| export-ui | 1 | expired-token-is-rejected | `src/export/ui/**` | none | no | planned |\n\n## Integrator-owned\n- `.drive/`\n")
        self.assertFails(self.lint(repo, gate="decompose"), "ownership overlaps")

    def test_package_report_listing_unowned_file_fails(self):
        repo = self.make_run()
        self.write(repo, ".drive/packages/export-api/brief.md", "# Package export-api\n")
        self.write(repo, ".drive/packages/export-api/report.json", {"package": "export-api"})
        brief = (Path(drive.TEMPLATES) / "package-brief.md").read_text().replace("<package id>", "export-api").replace(
            "- `<path or glob>`", "- `src/export/**`", 1)
        self.write(repo, ".drive/packages/export-api/brief.md", brief)
        report = {"package": "export-api", "status": "complete", "files": ["src/export/api.py", "src/app.py"],
                  "tests": ["tests/test_export.py::export keeps totals"], "gates_run": [{"cmd": "pytest", "exit": 0, "tail": "1 passed"}],
                  "wiring_needed": [], "deps_requested": [], "honest_gaps": [], "follow_ups": [], "noticed_not_touched": [],
                  "concerns": [], "summary": "ok", "model": "claude-sonnet-5"}
        self.write(repo, ".drive/packages/export-api/report.json", report)
        self.assertFails(self.lint(repo), "src/app.py which is outside the package's owned paths")

    def test_brief_that_asks_maker_to_double_check_fails(self):
        repo = self.make_run()
        brief = (Path(drive.TEMPLATES) / "package-brief.md").read_text().replace("<package id>", "export-api") + "\nDouble-check your work before reporting.\n"
        self.write(repo, ".drive/packages/export-api/brief.md", brief)
        self.assertFails(self.lint(repo), "tells the maker to check its own work")

    def test_handoff_carrying_maker_summary_fails(self):
        repo = self.make_run()
        handoff = (Path(drive.TEMPLATES) / "handoff.md").read_text().replace("<unit>", KEY) + "\nThe maker says the tests pass.\n"
        self.write(repo, ".drive/handoffs/{}.md".format(KEY), handoff)
        self.assertFails(self.lint(repo), "carries the maker's own account")


class PlaceholderTests(DriveTestCase):
    def test_placeholder_detection(self):
        found = [p for _, p in drive.find_placeholders("# STATUS · <project>\nA <div> and <Button> and <YYYY-MM-DD> and <S|M|L|XL>\n<!-- <hidden> -->\n")]
        self.assertEqual(found, ["<project>", "<YYYY-MM-DD>", "<S|M|L|XL>"])
