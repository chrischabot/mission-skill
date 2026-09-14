"""hook-guard: per-agent rules, including severe attempts to smuggle git mutations past the verifier."""
from pathlib import Path

from helpers import DriveTestCase


class GuardCase(DriveTestCase):
    def setUp(self):
        super().setUp()
        self.repo = self.make_run()

    def guard(self, agent, tool, cwd=None, **tool_input):
        payload = {"hook_event_name": "PreToolUse", "agent_type": agent, "agent_id": "a1", "tool_name": tool,
                   "tool_input": tool_input, "cwd": str(cwd or self.repo)}
        return self.hook("hook-guard", payload)

    def bash(self, agent, command, cwd=None):
        return self.guard(agent, "Bash", cwd=cwd, command=command)

    def assertBlocked(self, result, fragment=None):
        self.assertEqual(result.returncode, 2, "expected a block; stderr: {}".format(result.stderr))
        if fragment:
            self.assertIn(fragment, result.stderr)

    def assertAllowed(self, result):
        self.assertEqual(result.returncode, 0, "expected the call to be allowed; stderr: {}".format(result.stderr))


class VerifierBashTests(GuardCase):
    SMUGGLED = [
        "git commit -m 'verified'",
        "bash -c \"git commit -m verified\"",
        "sh -c 'git add -A && git commit -m x'",
        "npm test; git commit -am done",
        "npm test && git commit -am done",
        "npm test || git push origin main",
        "(git commit -am done)",
        "echo $(git commit -am done)",
        "echo `git commit -am done`",
        "env GIT_AUTHOR_NAME=x git commit -am done",
        "GIT_EDITOR=true git commit -a",
        "git -C . commit -am done",
        "/usr/bin/git commit -am done",
        "command git commit -am done",
        "eval 'git commit -am done'",
        "echo hi | xargs git commit -am",
        "timeout 5 git reset --hard HEAD~1",
        "nohup git push &",
        "bash -lc 'cd src && git stash'",
        "git checkout -- src/auth.py",
        "git worktree add /elsewhere HEAD",
        "git branch -D feature",
        "python3 -c \"import subprocess; subprocess.run(['git', 'commit', '-am', 'x'])\"",
        "find . -name '*.py' -exec git add {} \\;",
        "if true; then git commit -am x; fi",
        "{ git commit -am x; }",
    ]

    def test_git_mutations_are_blocked_however_they_are_wrapped(self):
        for command in self.SMUGGLED:
            with self.subTest(command=command):
                self.assertBlocked(self.bash("drive:verifier", command))

    def test_script_file_running_git_commit_is_blocked(self):
        script = self.write(self.repo, "scripts/sneaky.sh", "#!/bin/sh\ngit commit -am sneaky\n")
        self.assertBlocked(self.bash("drive:verifier", "bash scripts/sneaky.sh"))
        self.assertBlocked(self.bash("drive:verifier", "sh {}".format(script)))

    def test_read_only_git_and_tests_are_allowed(self):
        for command in ["git status --porcelain", "git log --oneline -5", "git diff HEAD~1 -- src", "git show HEAD:src/auth.py",
                        "git worktree list", "git branch --show-current", "git stash list", "git rev-parse HEAD",
                        "python3 -m pytest 2>&1 | tee {}/drive-out.txt".format(self.scratch),
                        "python3 -m pytest > .drive/proofs/expired-token-is-rejected/r2/pytest.txt 2>&1",
                        "git archive --format=tar HEAD -o {}/drive-prefix-key.tar".format(self.scratch),
                        "git grep -n expires", "rm -rf {}/drive-copy".format(self.scratch),
                        "grep -rn 'expires' src || true"]:
            with self.subTest(command=command):
                self.assertAllowed(self.bash("drive:verifier", command))

    def test_git_inside_a_scratch_copy_is_allowed(self):
        copy = self.scratch / "drive-prefix-key"
        self.assertAllowed(self.bash("drive:verifier", "git -C {} commit -am mutant".format(copy)))
        self.assertAllowed(self.bash("drive:verifier", "cd {} && git stash".format(copy)))

    def test_deletes_moves_and_writes_outside_scope_are_blocked(self):
        for command, fragment in [("rm -rf src", "deletes or moves"), ("mv src/auth.py src/old.py", "deletes or moves"),
                                  ("rm -rf .drive/proofs/expired-token-is-rejected", "deletes or moves"),
                                  ("echo hacked > src/auth.py", "Redirecting output"), ("sed -i 's/>/>=/' src/auth.py", "writes"),
                                  ("cp /etc/hosts src/hosts", "writes"), ("tee src/auth.py < /dev/null", "writes"),
                                  ("find src -name '*.pyc' -delete", "find -delete"), ("ls | xargs rm", "no visible paths"),
                                  ("rm -rf $TARGET", "deletes or moves")]:
            with self.subTest(command=command):
                self.assertBlocked(self.bash("drive:verifier", command), fragment)

    def test_deploys_and_publishes_are_blocked(self):
        for command in ["npx wrangler deploy", "wrangler deploy --env production", "npm publish", "pnpm publish --access public",
                        "cargo publish", "gh pr create --fill", "gh release create v1", "xcrun altool --upload-app",
                        "terraform apply -auto-approve", "kubectl apply -f k8s.yaml", "docker push registry/app:1",
                        "wrangler secret put API_KEY", "gh api -X POST repos/o/r/issues"]:
            with self.subTest(command=command):
                self.assertBlocked(self.bash("drive:verifier", command), "deploys or publishes")

    def test_local_wrangler_commands_are_allowed(self):
        for command in ["wrangler dev --local", "wrangler d1 migrations apply DB --local", "wrangler d1 execute DB --remote --command 'select 1'"]:
            with self.subTest(command=command):
                self.assertAllowed(self.bash("drive:verifier", command))

    def test_verifier_edit_and_write_tools_are_blocked(self):
        self.assertBlocked(self.guard("drive:verifier", "Edit", file_path=str(self.repo / "src/auth.py"), old_string="a", new_string="b"),
                           "Edit and Write tools are blocked")
        self.assertBlocked(self.guard("drive:verifier", "Write", file_path=str(self.scratch / "note.txt"), content="x"))
        self.assertBlocked(self.guard("drive:auditor", "NotebookEdit", notebook_path=str(self.repo / "nb.ipynb")))

    def test_verifier_may_write_its_review_file_through_bash(self):
        self.assertAllowed(self.bash("drive:verifier", "python3 -c 'print(1)' > .drive/reviews/2026-09-14-final-audit.json"))

    def test_project_scripts_writing_local_ios_are_allowed(self):
        self.write(self.repo, "scripts/ios/capture.sh", "#!/bin/sh\nmkdir -p .drive/local/ios\nrm -f .drive/local/ios/old.png\nxcrun simctl io booted screenshot .drive/local/ios/new.png\n")
        self.assertAllowed(self.bash("drive:verifier", "bash scripts/ios/capture.sh"))
        self.assertAllowed(self.bash("drive:ui-reviewer", "sh scripts/ios/capture.sh > .drive/local/ios/capture.log"))


class RoleTests(GuardCase):
    def test_other_read_only_roles_share_the_rules(self):
        for agent in ("drive:grader", "drive:auditor", "drive:security-reviewer"):
            with self.subTest(agent=agent):
                self.assertBlocked(self.bash(agent, "true && git commit -am x"))
                self.assertBlocked(self.bash(agent, "echo x > src/auth.py"))
                self.assertAllowed(self.bash(agent, "echo '{}' > .drive/reviews/2026-09-14-security-auth.md"))

    def test_severe_tester_writes_tests_fixtures_and_proofs_only(self):
        agent = "drive:severe-tester"
        self.assertAllowed(self.guard(agent, "Write", file_path=str(self.repo / "tests/test_forged.py"), content="x"))
        self.assertAllowed(self.guard(agent, "Write", file_path=str(self.repo / "api/tests/severe_auth.test.ts"), content="x"))
        self.assertAllowed(self.guard(agent, "Write", file_path=str(self.repo / "fixtures/tokens.json"), content="x"))
        self.assertAllowed(self.guard(agent, "Write", file_path=str(self.repo / "AppTests/TokenTests.swift"), content="x"))
        self.assertAllowed(self.guard(agent, "Write", file_path=str(self.repo / ".drive/proofs/k/r1/severe-notes.md"), content="x"))
        self.assertBlocked(self.guard(agent, "Write", file_path=str(self.repo / ".drive/proofs/k/r1/notes.txt"), content="x"))
        self.assertBlocked(self.guard(agent, "Write", file_path=str(self.repo / ".drive/proofs/k/r1/verdict.json"), content="x"))
        self.assertBlocked(self.guard(agent, "Edit", file_path=str(self.repo / "src/auth.py")), "not a test, fixture, or proof path")
        self.assertBlocked(self.guard(agent, "Write", file_path=str(self.repo / "tests/../src/auth.py"), content="x"))
        self.assertBlocked(self.bash(agent, "git commit -am tests"))

    def test_severe_tester_cannot_write_through_a_symlinked_test_directory(self):
        (self.repo / "tests" / "linked").symlink_to(self.repo / "src")
        self.assertBlocked(self.guard("drive:severe-tester", "Write", file_path=str(self.repo / "tests/linked/auth.py"), content="x"))

    def test_architect_scope(self):
        agent = "drive:architect"
        for rel in (".drive/SPEC.md", "docs/design.md", "design/tokens.json", "src/content/claims/pricing.md"):
            with self.subTest(rel=rel):
                self.assertAllowed(self.guard(agent, "Write", file_path=str(self.repo / rel), content="x"))
        self.assertBlocked(self.guard(agent, "Write", file_path=str(self.repo / "src/auth.py"), content="x"), "outside that scope")
        self.assertBlocked(self.guard(agent, "Write", file_path=str(Path.home() / ".bashrc"), content="x"), "outside the project")

    def test_designer_scope(self):
        self.assertAllowed(self.guard("drive:designer", "Write", file_path=str(self.repo / "design/DESIGN.md"), content="x"))
        self.assertBlocked(self.guard("drive:designer", "Write", file_path=str(self.repo / "docs/readme.md"), content="x"))

    def test_implementer_and_writer_edit_but_never_touch_git(self):
        for agent in ("drive:implementer", "drive:writer"):
            with self.subTest(agent=agent):
                self.assertAllowed(self.guard(agent, "Edit", file_path=str(self.repo / "src/auth.py")))
                self.assertAllowed(self.guard(agent, "Write", file_path=str(self.repo / ".drive/packages/auth-core/report.json"), content="{}"))
                self.assertBlocked(self.guard(agent, "Edit", file_path=str(self.repo / ".drive/STATUS.md")), "only writer of .drive/ state")
                for command in ("git add src/auth.py", "git commit -m x", "git push", "git checkout main", "git switch -c x",
                                "git reset --keep HEAD", "git stash", "git rebase main", "git merge x", "git worktree add ../x",
                                "git branch -D x", "npm test && git add -A"):
                    self.assertBlocked(self.bash(agent, command), "is blocked")
                self.assertBlocked(self.bash(agent, "git restore src/auth.py"), "git restore")
                self.assertBlocked(self.bash(agent, "git restore --staged src/auth.py"))
                self.assertAllowed(self.bash(agent, "git status --porcelain && python3 -m pytest tests/test_auth.py"))
                self.assertAllowed(self.bash(agent, "echo x > src/generated.txt"))

    def test_investigator_worktrees_only_under_scratch(self):
        agent = "drive:investigator"
        wt = self.scratch / "drive-proj-hyp"
        self.assertAllowed(self.bash(agent, "git worktree add --detach {} HEAD".format(wt)))
        self.assertBlocked(self.bash(agent, "git worktree add -b drive/hyp {} HEAD".format(wt)), "detached")
        self.assertAllowed(self.bash(agent, "git worktree remove --force {}".format(wt)))
        self.assertAllowed(self.bash(agent, "git worktree prune && git worktree list"))
        self.assertAllowed(self.bash(agent, "cd {} && git bisect start HEAD HEAD~5 && git bisect run ./repro.sh".format(wt)))
        self.assertAllowed(self.bash(agent, "git branch -D drive/hyp"))
        self.assertBlocked(self.bash(agent, "git worktree add ../beside HEAD"), "only under")
        self.assertBlocked(self.bash(agent, "git commit -am fix"))
        self.assertBlocked(self.bash(agent, "git bisect start"))
        self.assertBlocked(self.bash(agent, "git branch -D main"))
        self.assertAllowed(self.guard(agent, "Write", file_path=str(self.repo / ".drive/investigations/2026-09-14-x.md"), content="x"))
        self.assertAllowed(self.guard(agent, "Write", file_path=str(wt / "probe.py"), content="x"))
        self.assertBlocked(self.guard(agent, "Write", file_path=str(self.repo / "src/auth.py"), content="x"))

    def test_ui_reviewer_scope(self):
        agent = "drive:ui-reviewer"
        self.assertAllowed(self.guard(agent, "Write", file_path=str(self.repo / ".drive/proofs/k/r1/findings.json"), content="{}"))
        self.assertAllowed(self.guard(agent, "Write", file_path=str(self.repo / ".drive/local/ui/notes.md"), content="x"))
        self.assertBlocked(self.guard(agent, "Edit", file_path=str(self.repo / "src/App.tsx")))
        self.assertAllowed(self.bash(agent, "python3 shot.py > .drive/local/ui/run.log"))
        self.assertAllowed(self.bash(agent, "python3 shot.py > .drive/proofs/k/r1/shots/home.tree.json"))
        self.assertBlocked(self.bash(agent, "python3 shot.py > src/snapshot.json"))
        self.assertBlocked(self.bash(agent, "git add .drive/proofs"))

    def test_researcher_writes_only_drive(self):
        self.assertAllowed(self.guard("drive:researcher", "Write", file_path=str(self.repo / ".drive/RESEARCH.md"), content="x"))
        self.assertBlocked(self.guard("drive:researcher", "Write", file_path=str(self.repo / "README.md"), content="x"))


class InertTests(GuardCase):
    def test_guard_is_inert_without_active_marker(self):
        (self.repo / ".drive/local/active").unlink()
        self.assertAllowed(self.bash("drive:verifier", "git commit -am x"))
        self.assertAllowed(self.guard("drive:verifier", "Edit", file_path=str(self.repo / "src/auth.py")))

    def test_guard_is_inert_for_agents_outside_the_roster(self):
        for agent in ("Explore", "general-purpose", "other-plugin:verifier", ""):
            with self.subTest(agent=agent):
                self.assertAllowed(self.bash(agent, "git commit -am x"))

    def test_guard_is_inert_in_an_unrelated_repository(self):
        other = self.new_repo("other")
        self.assertAllowed(self.bash("drive:verifier", "git commit -am x", cwd=other))

    def test_guard_follows_a_worktree_back_to_the_active_run(self):
        wt = self.scratch / "drive-proj-look"
        self.git(self.repo, "worktree", "add", "-q", "--detach", str(wt), "HEAD")
        self.assertBlocked(self.bash("drive:verifier", "git -C {} push".format(self.repo), cwd=wt))

    def test_guard_uses_project_dir_when_cwd_left_the_project(self):
        result = self.run_drive("hook-guard", stdin='{"agent_type": "drive:verifier", "tool_name": "Bash", "cwd": "%s", '
                                                  '"tool_input": {"command": "git -C %s commit -am x"}}' % (self.scratch, self.repo),
                                env={"CLAUDE_PROJECT_DIR": str(self.repo)})
        self.assertEqual(result.returncode, 2)

    def test_unparseable_input_does_not_crash(self):
        result = self.run_drive("hook-guard", stdin="not json")
        self.assertEqual(result.returncode, 0)
