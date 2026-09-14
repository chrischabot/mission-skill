# General lessons

Rules about how to run projects, whatever the stack, each learned from a verified failure. Read
this file in full at every intake and resume above XS. Quote the rules that apply, at most ten and
verbatim, under "Lessons that apply to this task" in every worker brief; verifiers check compliance
against the same list. Entries use the template in `templates/lesson.md` and are added, merged,
proved by eval, and retired only as `references/lessons.md` describes. Cap: 60 entries or 16,000
characters.

The first six entries were seeded when the skill was created, each from a failure whose mechanism was
verified and recorded before drive existed. None has yet been re-verified by `drive:auditor` or proved
by an eval case, and their Seen counts record only the instances written down.

## Entries

### Before trusting green runs, find where each test double is kinder than the real service and close the gap
- When: a shim, emulator, in-memory store, fake, fixture, or test mode stands in for a hosted service or runtime on the path a claim depends on.
- Do: list the real service's documented hard limits and behaviours (bound parameters, payload and row sizes, rate limits, timeouts, consistency, auth expiry), record in TESTPLAN.md's kindness ledger which ones the double does not enforce, and for each give a guard in the code under test, a double that enforces it, or a check against the real runtime.
- Because: a double more permissive than production certifies broken code; every green run under it is evidence about the double, not the code.
- Check: the kindness ledger in TESTPLAN.md; `drive.py lint` refuses Live Proof unless the live `proof.json` has environment `live` or `device` and a `shim_differences` answer; the verifier handoff asks where each double is kinder; eval case `harness-kindness`.
- Verified by: seeded from a recorded failure, 2026-07-25. A SQLite shim allowed unlimited bound parameters where the hosted database stops at 100; the query passed 24 green validation runs and failed live once the data passed 100 items. The recorded remedy was to teach the harness and the code the production limit, not only to patch the query.
- Applies to: any project with a hosted backend, managed database, queue, object store, payment sandbox, or platform emulator used in tests.
- Not for: pure in-process code with no hosted counterpart, where there is no real service to be kinder than.
- Seen: 1 (2026-07-25) · Added: 2026-09-14 · Confirmed by: seeded, not yet re-verified by drive:auditor

### Drive a system through its own tools now, and never wait on a scheduler for work an action implied
- When: the goal involves a system that exposes verbs (MCP tools, a CLI, an API), or work is about to be left for a cron, queue sweep, or scheduled job to pick up.
- Do: load the system's own tools at intake (search deferred tools by the system's name) and make things happen by calling its verbs, then confirm the result through the same surface. Use direct database access only for inspection or repairs that have no verb. If no verb exists, that is a missing verb to build. Schedule only a condition with no triggering signal, such as a soak, and never report scheduled work as done.
- Because: changing a system's data behind its interface does nothing until some background process notices, which makes a scheduler look like the only way to get a result and turns a same-turn outcome into an unverified promise.
- Check: the `async-scheduled` trait gate requires the triggered run's evidence; the final audit blocks any report that describes future scheduled work as a result.
- Verified by: seeded from a recorded failure, 2026-07-24. An agent building a system's tool verbs drove the system through raw SQL, because the verbs sat unloaded in the deferred tool list; a status it wrote did nothing until a cron fired, and it twice said results would appear when the cron ran, although a verb that did the work at once already existed.
- Applies to: every shape that touches a running system, especially `operate`, `fix/incident`, and `async-scheduled` work.
- Not for: soak periods and retries of a third party that is down, where no signal exists to act on.
- Seen: 1 (2026-07-24) · Added: 2026-09-14 · Confirmed by: seeded, not yet re-verified by drive:auditor

### When the same obstacle needs a workaround a second time, stop and re-diagnose instead of repeating it
- When: a retry, sleep, wider mock, cast, skipped test, pinned version, changed flag, re-dispatch, or wait is about to be applied to an obstacle that already has a row in STATE.md's workaround ledger.
- Do: add a ledger row before every workaround; at count two apply nothing, open an investigation record, and let no work on that path continue until the record names a mechanism and a separate agent verifies it by prediction, within the investigation ceiling.
- Because: a workaround that is needed twice means the first diagnosis described a symptom, and repeating it pays for the wrong explanation again while the real mechanism stays in place.
- Check: the workaround ledger in STATE.md; `drive.py start` lists rows at count two or more; the retro requires an investigation record for each; eval case `second-time-is-the-bug`.
- Verified by: seeded from a recorded failure, 2026-07-24. After the first wait on a scheduler the diagnosis was "cron timing", nothing was fixed, and the same wait was repeated; the actual mechanism, driving the system through the wrong interface, was found only after the second occurrence.
- Applies to: all shapes and all agents, including the orchestrator's own re-dispatches.
- Not for: ordinary red-to-green iteration inside a package, where each attempt changes the code rather than working around an obstacle.
- Seen: 1 (2026-07-24) · Added: 2026-09-14 · Confirmed by: seeded, not yet re-verified by drive:auditor

### Remove every worktree a step creates in that same step, and never create a branch
- When: parallel isolation seems to need a worktree or branch (an experiment arm, a bisect, a hypothesis arm), or a large change tempts a feature branch "for safety".
- Do: commit straight to the current branch in small steps, and never push. Create worktrees only for arms whose losers are discarded, bisects, and hypothesis arms, always detached (`git worktree add --detach`, never `-b`) under a scratch directory such as `/tmp`, from HEAD; land a winner with `drive.py worktree-land <worktree path> <sha>`, which cherry-picks the arm's commits onto the current branch and removes the worktree, and remove losers before the step ends. Never give an editing subagent `isolation: worktree`.
- Because: a branch or worktree left for later is work nobody tracks; it goes unmerged, gets lost, or conflicts, and a report of "done" on a branch describes work the main line does not have.
- Check: the guard refuses every role and the main thread `git push` and, in every worktree of the repository, any command that creates a branch; it refuses `git worktree add` without `--detach` or outside a scratch directory; `drive.py lint --stop` fails on any linked worktree or local branch that the baseline recorded at init does not list; the orphan audit runs after every wave; eval case `stays-on-main`.
- Verified by: seeded from two recorded failures, 2026-07-10 and 2026-07-24. One session left two worktrees and five branches behind; another committed a feature to a branch and reported it done while the main line did not contain it.
- Applies to: every run in a repository the owner commits to directly.
- Not for: a repository whose own documented rules require feature branches; follow those, and still leave nothing behind that the step created.
- Seen: 2 (2026-07-10, 2026-07-24) · Added: 2026-09-14 · Confirmed by: seeded, not yet re-verified by drive:auditor

### Never build a queue for a person to review; automate the decision and record its audit trail and undo
- When: a design, a run step, or a fix would hold items, decisions, or lessons pending someone's approval, including "confirm once" steps, labelled sets a person must fill, or review inboxes.
- Do: take the reversible decision now, record it with provenance and an exact undo (DECISIONS.md for runs, a digest line the owner may ignore), and continue. Only a step with no possible undo and no defensible default becomes the single question, asked once in plain text while every independent piece of work continues.
- Because: an approval queue waits on attention that does not come, so work gated on it never completes and the queue grows until it is discarded.
- Check: none mechanical: whether a design waits on a person is judged at spec and design review and in the final audit, and the run's own flow has no queue to create.
- Verified by: seeded from a recorded failure, 2026-07-08. A review queue held items for approval and dead-lettered more than two thousand of them, none of which was ever reviewed.
- Applies to: every shape; product designs as well as drive's own procedure.
- Not for: irreversible, destructive, credential, payment, or legal steps, which block as the single question rather than proceed.
- Seen: 1 (2026-07-08) · Added: 2026-09-14 · Confirmed by: seeded, not yet re-verified by drive:auditor

### Treat any output a person will see as unverified until an agent that did not build it has looked at the rendered result
- When: a claim covers something a person reads or sees: an email, a web page, a native screen, a PDF, a notification, a report file, or terminal output.
- Do: capture the output as delivered, at the boundary where it leaves the system (the message handed to the mail transport, the page as served, the screen on the simulator), assert on that in a test, and have `drive:ui-reviewer` capture and judge it before the row reaches Local Proof.
- Because: tests of an internal renderer pass while the delivery step drops or alters what was rendered, and nobody notices until a person opens the result.
- Check: the `ui` trait covers email and terminal output and gates on `drive:ui-reviewer` capturing its own evidence; `drive.py lint` requires `shot:` evidence for `[ui]` rows at Local Proof.
- Verified by: seeded from a recorded failure, 2026-08-20. A renderer produced HTML and plain text, the sending step passed on only the text, and the test asserted the renderer's output rather than the outbound message, so a text-only email shipped with green tests. Passing the HTML and adding a transport-level test fixed it, and the next delivery was checked against the bytes actually sent.
- Applies to: every claim tagged `[ui]`, every `publish` run, and any feature that sends messages or writes documents for people.
- Not for: machine-to-machine payloads with a schema test at the boundary, which no person reads.
- Seen: 1 (2026-08-20) · Added: 2026-09-14 · Confirmed by: seeded, not yet re-verified by drive:auditor
