# drive: handoff

This repository holds `/drive`, a Claude Code skill that takes a high-level goal and drives it to
finished, committed work. Its default is a lean run: a Fable planner writes one implementation-ready
plan, Sonnet implementers build it, an Opus reviewer checks and corrects each change, and what every
agent learns compounds into the next plan. Rigorous mode, opt-in with `--rigorous`, runs the full
process: intake and classification, research, specification, design, test planning, parallel
implementation, independent adversarial verification, UI verification with vision, state files,
failure investigation distilled into lessons, and a final audit.

Last updated 2026-09-16 by the coordinating session, after budgets became checkpoints.

## The lean default (2026-09-15)

The owner made lean mode the default because the rigorous process spent its budget on ceremony. The
linkkeeper build cost $359 and about seven hours with three hours of planning before any code, and a
garderobe run spent about $45 in 75 minutes and produced no product code. The intended pattern was
always the token-saving one, a big model planning, a cheap model coding, and a mid-size model
reviewing, which should give output close to Fable's for roughly half the spend.

- **Flow.** `drive:planner` (Fable, high) writes an implementation-ready `.drive/PLAN.md` after
  consulting `.drive/LEARNINGS.md` and drive's lessons; `drive:implementer` (Sonnet, high) builds
  packages in parallel from it literally; `drive:reviewer` (Opus, high) reviews each change against
  the plan and fixes defects itself, returning only a fundamentally wrong package for one re-dispatch;
  a final Opus review runs the suite and writes REPORT.md. The orchestrator (Fable, medium) dispatches
  and commits. No spec, design, or test-plan files, no plan reviews, no ladder, verifiers, retro, or
  final audit.
- **Compounding.** Every agent appends Failed, Why, Verified (or guess), Rule, and Scope entries to
  `.drive/LEARNINGS.md`, whose sections follow the five-stage memory progression in the source post.
  `drive.py promote` sorts them and appends verified general rules to
  `skill/references/lessons/learned.md`, deduplicated against every lessons file and committed alone;
  lesson-check validates that file.
- **Where it lives.** SKILL.md now holds only the lean flow; the previous SKILL.md body moved intact to
  `skill/references/rigorous.md`. `drive.py` reads `mode:` from STATE.md or GOAL.md (a `.drive/` with
  GOAL.md and no mode line is rigorous), and in lean mode the lint, the Stop gate, and `end` check only
  STATE.md's status, next step, and timestamp (plus hygiene at `end`); the snapshot hook takes no tree
  snapshots. `skill/scripts/tests/test_lean_mode.py` proves lean runs are not held by rigorous gates.
- **Budgets are checkpoints (2026-09-16).** The first lean run stopped itself at a $120 hard stop
  with one of nine packages verified, so the hard stop is gone. The budget line records a target;
  when the recorded spend reaches it, and at each further multiple, the run commits and pushes what
  is reviewed, refreshes STATE.md, LEARNINGS.md, and REPORT.md with what is done and what remains,
  and continues. The only early ending is a `stop:` line the owner wrote (a dollar figure, a wall
  clock, or a date), in GOAL.md or, for a lean run, in STATE.md. `drive.py` holds a running run once
  that line is reached, refuses `Blocked on: budget:` and a report that stops on spend before then,
  and only warns on any spend or spawn figure. The lean orchestrator pushes its branch after every
  reviewed package, and STATE.md names the next package and the last pushed commit, so a run that
  loses its process resumes from the repository alone.
- **Not yet proven.** One lean run has happened and it was cut short by the old hard stop. The lean
  envelopes in `references/models.md` (small fix under $5, feature under $25, build M under $80) are
  targets to checkpoint at, not stops, and the two new eval cases (`lean-feature-plan`,
  `lean-learning-entry`) have not been scored.

## Where things stand

The skill is complete and committed under `skill/`: SKILL.md (the spine), twelve agent files with
pinned models, the references, shape files, domain packs and templates, `scripts/drive.py` with its
test suite, `hooks/hooks.json` (which registers the Stop gate, the guard and the snapshot hooks), the
plugin manifest, and the eval suite. `install.sh` links it as `~/.claude/skills/drive` and prints the
per-run launch settings. The suite passes on Python 3.13 and on the macOS system Python 3.9, and
`selfcheck`, `lesson-check` and `claude plugin validate` pass.

Drive uses exactly three models, pinned by full ID: `claude-fable-5-1` for the orchestrator and the
final audit, `claude-opus-5` for design, verification, security, UI review and investigation, and
`claude-sonnet-5` for research, implementation and low-effort grading. No other model is selected;
`skill/scripts/tests/test_model_ids.py` fails if any shipped file says otherwise or if the price
table drifts.

Two reviews on 2026-09-14 (`research/34-adversarial-review.md` and `research/37-fix-review.md`) and
their fixes are described in `research/35-code-fixes-for-docs.md`. On 2026-09-15 three further things
happened:

- **The eval suite was scored for the first time.** Running `claude plugin eval` with `HOME` pointed
  at an empty directory avoids the sandbox's refusal when `~/.docker` holds symbolic links
  (`skill/evals/README.md` section 2). One pass over the 19 cases cost $81 and scored 11 at 1.0; the
  traces showed mostly grader defects, which were fixed and confirmed by re-running the affected
  cases. No three-run gating run has been done.
- **Drive ran a complete project.** It built `linkkeeper`, a self-hosted bookmarks manager, from an
  empty repository at `/Users/chabotc/Projects/linkkeeper`. The run cost $359 against the owner's
  $360 stop line, ended `stopped` with 6 claims at Local Proof and 38 at Partial, and its final audit
  passed. The product runs from a fresh clone and its 410 tests pass. `research/40-linkkeeper-run-review.md`
  is the full review: what worked, what cost too much, and the dozen drive defects the run exposed,
  each fixed in drive with a test that fails against the earlier code.
- **The run's lessons were carried into the skill.** The retro named two candidates it could not
  afford to verify; they were verified against the run's transcripts, narrowed, and written where the
  missing instructions live (`research/39-run-lessons-verification.md`). The `build` cost envelopes in
  `references/models.md` section 7 were rescaled from the run's recorded spend.

## What is not yet proven

- **Planning cost at size M.** The linkkeeper run spent about three hours planning. S and M now get one
  full review round plus one scoped re-check, a combined design and test-plan review, and wave-level
  verification at M; every review round leaves a file that lint checks. No run has yet measured the saving.
- **The cost envelopes rest on one run.** Only the `build` row was rescaled; the other rows are still
  modelled.
- **No gating eval run.** The suite has single-run scores only; `skill/evals/README.md` section 3 has
  the two-arm, three-run procedure.
- **UI verification with vision has not run end to end.** The linkkeeper run cut its UI review to fit
  the budget, so no `drive:ui-reviewer` capture exists yet.
- **Unverified harness facts** are listed at the end of report 34: whether a background session has
  the iOS Simulator and Browser pane tools, whether `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` in the
  `--settings` env block takes effect, and whether a subagent can invoke the bundled
  `security-review` skill. The headless linkkeeper run found the bundled security-review, simplify,
  code-review and workflow-authoring skills unavailable and substituted drive's own agents.

## Where to read

- `research/00-brief.md`: the original brief, with corrections at the top. The iOS app with a
  Cloudflare backend was only ever an example of the kind of goal drive receives; no code for it
  exists or should be written.
- `research/01` to `23`: component research. `research/23-agent-skills-extraction.md` covers what
  was reused from addyosmani/agent-skills (MIT; see THIRD_PARTY_NOTICES.md).
- `research/24-synthesis.md`: the binding design record, with amendments in sections 15 to 21.
  Section 21 is the threat model: the guard makes honest mistakes fail loudly, and transcript-backed
  provenance makes tampering evident afterwards; deliberate shell obfuscation is out of scope.
- `research/25` to `32`: the drafting brief and successive review rounds.
- `research/30-compare-mission-vs-drive.md`: comparison with the earlier `mission` skill.
- `research/33` to `37`: the model and cost audit, the whole-project review, the behaviour changes it
  produced, the completion checklist (done), and the review of the fixes.
- `research/38-pstack-evaluation.md`: what drive could take from cursor/plugins pstack (applied on 2026-09-15, with its MIT notice).
- `research/39-run-lessons-verification.md` and `research/40-linkkeeper-run-review.md`: the first
  complete run and the lessons carried from it.

## Checks to run after any change

```bash
python3 -m unittest discover -s skill/scripts/tests
```

```bash
python3 skill/scripts/drive.py selfcheck
```

```bash
python3 skill/scripts/drive.py lesson-check
```

```bash
claude plugin validate skill
```

The suite takes about four minutes and must also pass on the macOS system Python (3.9).
