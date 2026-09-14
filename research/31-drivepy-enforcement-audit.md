# 31 · Audit of drive.py enforcement (commit ae0fa44)

Independent audit run by a helper of the mission-versus-drive comparison. Citations are line numbers in
`skill/scripts/drive.py` at commit `ae0fa44`; uncommitted fixes were in progress in the working tree while it ran.

## Bugs, false negatives, false positives (the actionable list)

1. Committed STATUS row deletions are invisible to `lint --final`, because the intake baseline has no STATUS.md
   (1136–1147). A deleted Done row passes once committed.
2. A row may sit above its latest verdict's `rung_supported`; lint only requires the verdict to support Local Proof or
   higher (939–941). Mutation of this check survived all tests.
3. Any DECISIONS.md change excuses any narrowing (a `live` y→n flip, a new Dropped row, a removed phase); it downgrades
   to a warning (1169–1172). The decision entry must name the narrowed row or phase.
4. `status: blocked` bypasses the Stop gate unchecked; `blocked`, `stalled`, `aborted` always allow (2758).
5. Read-only guards evaporate for projects under /tmp or /private/tmp (3237, 3376): `echo x > src/calc.py` and
   `git commit` were allowed for a verifier there.
6. hook-guard evasions allowed for read-only roles: `python3 -c "open('src/calc.py','w')"`, `node -e writeFileSync`,
   `bash -c "$C"`, `tar -C src`, `ruby -i`, `make install`.
7. Implementers and the main thread are effectively unguarded: `git -c alias.ci=commit ci`, `git symbolic-ref HEAD
   refs/heads/other`, `git branch newb`, `echo >> ~/.zshrc`, `rm -rf ~/Projects/other` allowed for an implementer;
   `git checkout -b feature && git worktree add ../wt` allowed on the main thread; implementer or general-purpose Edit
   of a test file allowed. Only the thirteen drive role names are guarded (3510); no package-ownership check and no
   Bash path check for implementers (2898–2901, 3252–3254, 3318).
8. `guard` at the default `--base HEAD` loses everything already committed (SKILL.md runs it that way); it misses
   `from unittest import skip` / bare `@skip(...)`, `self.assertTrue(True)` replacements, early `return` in tests,
   `git mv` of a test out of discovery, `conftest.py collect_ignore`, pyproject `-k not ...`, and `fail_under = 0`.
   Nothing calls `guard` automatically.
9. Snapshots ignore untracked files (3541): a verifier creating `src/new_module.py` passed. Concurrent tracked edits by
   another agent are blamed on the reviewer. A block never voids a verdict (lint does not read `.drive/local/ro` or
   `gate.log`).
10. The floor guard flags banned markers in documentation (CONTRIBUTING.md mentioning `eslint-disable`,
    `raise NotImplementedError`) and a test calling `r.skip(1)`: false positives.
11. Placeholders longer than 80 characters pass lint (regex at 77); fresh `init` output leaves `live means: <...>`
    unflagged.
12. `--final` runs the `registry:` command with a 600-second limit (2212) under a 60-second Stop hook timeout; a
    timed-out hook renders no decision, so the stop goes through.
13. Stall detection resets whenever STATE.md changes (2794); rewriting `updated:` before each stop keeps the counter at
    1, so only Claude Code's cap ends the loop. The hooks page states the cap is 8 consecutive blocks and does not
    mention `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`, which install.sh sets to 30: verify that variable exists before relying
    on it. `stop_hook_active` is ignored.
14. The `CLAUDE_PROJECT_DIR` fallback (2665) lets a stale marker in the session's project block a Stop fired from an
    unrelated XS repository.
15. `worktree-land` never checks that the main checkout is on its expected branch; requires git 2.31+ for
    `--path-format=absolute` (220) without a version check; `/private/tmp` hard-coded (249) and shown to agents.
16. Prose requirements not enforced: `doc:` on Done rows; a captured `live.md` or artifact hashes for live proofs;
    `produced_by` and screenshots are free text. `Ctx.intake_commit` (742–746) is dead and silently replaced at 1329.

## Mutation results (24 copies of the committed file, full suite each)

Killed: need_live, skip, removed-assertion, snapshot, stall, interpreter-git, localhost, stale-time, branch and worktree
hygiene, full-suite, deploy, land allowlist, both final-audit checks, redirect, background subagent, harness kindness,
environment. Survived (no test catches their removal): `verdict_rung_supported` (939), `history_vs_intake` (1136),
`verdict_confidence` (928), `intake_order` (1317), and, on later copies, `operational_ops` (1108) and
`live_commit_exists` (981).

## Untested paths

Every evasion in items 6 to 8; an unguarded orchestrator or implementer; projects under a tmp root; the `blocked`
escape; the `CLAUDE_PROJECT_DIR` fallback; untracked files in snapshots; the merge-conflict path of worktree-land; hook
timeouts.
