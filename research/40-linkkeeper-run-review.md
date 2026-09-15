# 40 · The first complete drive run: linkkeeper

Written on 2026-09-15 by the owner session that launched and watched the run. The run built
`linkkeeper`, a self-hosted bookmarks manager, from an empty repository at
`/Users/chabotc/Projects/linkkeeper`, headless on `claude-opus-5` after a first leg on
`claude-fable-5-1` was stopped during intake at the owner's request. The owner kept the leg's
$400 hard limit and chose to stop at the run's own $360 line rather than fund a second leg. Every
observation below was checked against the run's files, commits, gate log, stream log, or subagent
transcripts; the running notes behind it are in the session scratchpad.

## Verdict

Drive did what it exists to do on the axis that matters most. It turned a one-paragraph goal into a
working product with 44 refutable claims, real tests against real HTTP, TLS and SQLite, a measured
quality floor, an independent security review, and a report that claims nothing its evidence does
not support. From a fresh clone the app starts with one command, saves and searches bookmarks, and
the full suite of 410 tests passes. Independent verification found real defects the makers' own
tests passed over: fixture checks that iterated the document under test, an SSRF bypass through IPv4
embedded in IPv6, host block-list evasion through a trailing dot, a title scan that a slow page could
hold open, and a hostile charset that turned a save into a 500. The failure-to-lesson loop worked on
two real problems, with investigations that measured their mechanism from transcripts and made
predictions the relaunch then tested. Under budget pressure the run narrowed ceremony in logged,
undoable decisions and never rounded a row up: it ended `stopped` with 6 claims at Local Proof and
38 at Partial, and the final audit passed that report.

The cost of that rigor is the main finding. The run spent $359 and about 7 hours against GOAL.md's
$130 to $270 and 3 hours, and it spent roughly three hours on planning before the first line of
code: every planning artifact used its full bound of three review rounds, and per-package mutation-led
verification then failed most units once or twice. That is why a product that works ends with no
claim above Partial outside search. The run also surfaced a dozen drive defects, almost all in the
guard and lint being too coarse for honest commands, and one that let reviewers run out of turns
before writing. They were fixed in drive during the run, each with a test that fails against the
earlier code, and are listed below. The loop's last step did not happen inside the run: the retro
named two lesson candidates and committed none, because the dedupe and auditor verification a skill
lesson needs did not fit the budget. The owner session carried both into the skill after verifying
them (`research/39-run-lessons-verification.md`).

## What the run produced

- **Product:** a Python 3.13 standard-library server, SQLite storage with full-text search, a title
  fetcher with SSRF and DNS-rebinding defences, Chrome and Firefox bookmark import and export, a JSON
  API with an OpenAPI contract, and a four-screen web UI with keyboard and screen-reader support.
- **Evidence:** 410 tests (frozen claim tests written red by a severe tester before each package),
  CONSTRAINTS.md measured after wave 0, 12 verifier verdicts with transcript-backed provenance, a
  security review (pass: F2 fixed, F1 unbounded import size open), and a final audit (go).
- **Report:** ladder 6 Local Proof and 38 Partial; three open failures, each with the test that would
  close it; every decision taken on the owner's behalf with its undo; a clean-checkout recipe that I
  ran and that passes.

## Timeline

| phase | local time | notes |
|---|---|---|
| launch and intake | 05:5x to 06:14 | Fable leg stopped and resumed on Opus 5; build M, auth suspected with concrete reasons |
| research | 06:15 to about 07:10 | probes found three things memory would have got wrong; researcher lanes ran out of turns twice |
| spec | to about 07:40 | 35 then 37 claims; three review rounds |
| design and test plan | to about 08:50 | three review rounds; 15 packages after two re-plans |
| build and verify | 09:00 to about 13:00 | contracts 3 rounds at Partial; per-wave and folded verification after $173 |
| harden, retro, report, audit | 13:00 to about 13:50 | security review pass; retro with no committed lesson; final audit go |

## Where drive worked

- **Anti-mirage under pressure.** Passing tests were never accepted as proof. Contracts closed at its
  round bound at Partial; storage-core passed a verifier round and still stayed at Partial because it
  lacked `severe:` evidence; UI rows were capped at Partial once the UI review was cut.
- **Research before design.** The ledger's probes showed that `urlopen`'s timeout is per socket
  operation (20.5 s against `timeout=3`), that FTS5 `tokenchars` with `:` and `/` breaks domain search
  while trigram gives fragment search only from three characters, and that 8 of 10 hostile search
  strings raise unless quoted. Safari's format and DNS and TLS failure handling were honestly held as
  a source claim and an assumption.
- **Threat model reaching the claims unprompted.** SSRF, CSRF, DNS rebinding, stored XSS, hostile
  imports and search input, lost writes, keyboard and screen-reader access all became claims.
- **Verification finding real defects,** listed in the verdict above, before the security review.
- **Failure to lesson.** Two repeated workarounds each triggered the second-time rule; both
  investigations named a measured mechanism and a falsifiable prediction. One found siblings of a
  defect the owner session had half-fixed, and noticed that uncommitted fix appearing mid-investigation.
- **Decisions under a budget.** Every narrowing (per-wave verification, folded UI packages, stopping
  verification rounds) has context, the rejected option, an undo, and a `Narrows:` line.

## Where drive fell short

- **Planning cost.** Spec, design and test plan each used three review rounds; no code for about
  three hours. The later rounds did find blocking gaps (a Host rule for LAN access, frozen-test
  ownership, a fetcher that would break real HTTPS titles), so the rounds were not idle, but a size M
  build cannot afford three full rounds per artifact and per-package verification within the
  envelope drive itself quoted.
- **Cost model.** `references/models.md` section 7 put a size M build at $130 to $270; this run cost
  about $352 and stopped with most rows at Partial. The run's own spend lines were also unreliable
  (the research ledger claimed about $0.35 for a lane of about 85 tool calls).
- **Reviews left no file.** The intake classification review and all six spec and design review
  rounds returned findings only in the architect's message and a line in STATE.md or DECISIONS.md, so
  no auditor can check what they said.
- **Turn limits against write-at-the-end.** Researcher lanes (twice) and a wave verifier ran out of
  turns before writing their deliverable; server-core's third round left 9 claims unverifiable.
- **No lesson committed inside the run.** The loop reached distillation and stopped at the budget gate.
- **Smaller:** a slug cut from the goal text at 50 characters; STATE.md phase labels lagging or moving
  backwards when phases overlapped; `updated:` timestamps hours ahead of the clock; the orchestrator
  sweeping an uncommitted verdict change into a package commit; the same auditor instance reused for
  the re-audit; a frozen UI test that flaked once in 410 and went unmentioned in the report.

## Drive defects the run exposed, and what changed

Each fix was committed in `/Users/chabotc/Projects/drive` with a test that fails against the earlier
code, and pushed to `chrischabot/mission-skill`.

| defect | fix |
|---|---|
| Guard raised OSError on literals and words over 255 characters, refusing plain commands | filesystem queries on command text answer "not found" on OSError (3380bd8) |
| Orchestrator refused for inline code that mentions evidence paths, with advice pointing the wrong way | refusal now names the Edit tool for state files (3380bd8) |
| Future `updated:` in STATE.md would defeat the staleness check | lint fails a value more than 15 minutes ahead (0038108) |
| Honest in-memory SQLite and introspection probes refused | sqlite3 on `:memory:`, sysconfig, platform, importlib.util allowed (9e4188a) |
| Researcher had Write but no Edit, so lanes rewrote the shared ledger | Edit added with a no-rewrite rule (cd31dea) |
| `planned:` tokens failed every row once build began (44 false failures) | fail only at Partial or above, at `--final`, or from harden on (ee24ad7) |
| Per-round handoffs rejected; placeholders like `{scratch}` slipped past; overlapping reviewers logged false PROVENANCE REFUSED | `<unit>-r<n>.md` accepted; brace placeholders caught, superseded rounds exempt; NOTE instead of REFUSED (ee24ad7) |
| A verdict written in a shell call that later exited non-zero was refused provenance | calls that ran count; refused calls still do not (cc74c5b) |
| Wrapped-assertion rule flagged try/finally cleanup, and exception rows could name one glob, so the run loosened the rule for all tests | syntax-tree check for swallowing handlers; comma-separated exception paths (9d440db) |
| Verifiers flagged frozen tests and package reports as ownership breaches | the audit and handoff template say they are expected (06c8899) |
| An in-place `sed` script naming a frozen path was read as a write target | in-place targets skip the script (7839a33) |
| The two lesson candidates | verified, narrowed, and written where the instructions live (4b1c639) |

The final auditor's refused commands were fixed after the run closed (5836b1b): a scratch-copy
`sed -i ''`, a variable assigned a literal path earlier in the same command, `for` loops in read-only
reviews, and a `>` inside an awk string; verdicts now take an optional `model` field.

## Recommendations not yet acted on

- **Cut planning cost at size M.** Lower the review round bound for spec, design and test plan at M
  (one full round plus one scoped re-check of blocking findings), and let the wave-level verification
  the run adopted under budget be the default at M rather than per-package rounds.
- **Recompute the envelopes from this run.** Replace the build M cell with a figure grounded in the
  recorded spend, and require spend lines to come from a recorded figure or say "not measured".
- **Make every review round leave a file,** including intake classification and spec and design
  reviews, so the final audit can check them.
- **Name slugs from the deliverable,** and have the orchestrator take `updated:` from `date -u`.
- **Apply the pstack evaluation's weak-test shapes** (`research/38-pstack-evaluation.md`): the first
  contracts verdict is a live example of an expected value derived from the thing under test.

## Spend

Recorded, not estimated: the Opus 5 session's final result event gives `total_cost_usd` 355.81, and
the stopped Fable 5.1 intake leg gave 3.26, so the run cost $359.07 against GOAL.md's $130 to $270 and
the owner's $360 stop line. `drive.py end` closed the run as stopped at 13:02Z with a clean tree. The
report's own "about $330" was written before the security review and final audit finished and is
therefore low. Maker subagent starts: 36 against a budget of 40. Wall clock: about 7 hours from launch
to close, against 3.
