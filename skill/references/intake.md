# Intake and re-classification

Read this file at intake, before the first plan line is written, and again at every phase gate and
whenever an event in section 13 happens. It decides whether the run belongs in this repository,
whether this invocation resumes, archives, or starts a run; how to read the goal and probe the tree; the shape, variant, traits, and size; the
plan GOAL.md carries; which decisions you take on the owner's behalf and the one question you may
ask; and how the classification changes when the work shows more than the goal did. Every trait has
its own section whose heading is exactly the trait's name, so read only the traits you marked.
`references/rigorous.md` section 3 is the short form of this file, and the two agree.

Contents
1. Where the run lives, resume, and paused runs
2. Parse the goal
3. Probe the tree
4. Capability preflight
5. Shape
6. Variants
7. Traits
8. Threshold discipline
9. Size
10. Derive the plan
11. GOAL.md: the restate block and the classification block
12. Decisions you take, and the one question
13. Re-classification
14. Worked classifications

## 1. Where the run lives, resume, and paused runs

`references/rigorous.md` section 2 step 0 has already settled that this repository is the run's home: the
repository that will hold the deliverable. A repository the goal names after "from" is the source of
a move and never the home, even when it is the only repository the goal names: "move our AI gateway
from the external repo into a core service of this platform" lives in the platform. A goal whose home
is another existing repository, or new work while this directory holds a different project or is not
a repository, launched a background session there and ended this one. If the probe in section 3 shows
the directory is unrelated after all, go back to that step. Then, before you parse anything:

| What you find | What it is | Do |
|---|---|---|
| `--resume` with `.drive/STATE.md` present, or `.drive/STATE.md` exists and GOAL.md's `goal:` line asks for this deliverable | a resume | Follow `references/rigorous.md` section 2, which runs `drive.py init --goal -` with GOAL.md's goal on stdin to re-create a missing `.drive/local/active` and record this session. Do not re-run intake or re-plan unless a discovery is logged. |
| `.drive/STATE.md` exists and the new goal names the same deliverable with more or different scope | a follow-up that changes the deliverable | Keep the run. Add a sub-goal through a dated re-plan (section 13). |
| `.drive/STATE.md` exists for a different goal | another run's state | Do not overwrite it and do not ask. Continue with section 2; at the plan step, `drive.py init` moves the old run to `.drive/runs/<YYYY-MM-DD>-<old slug>/`. |
| no `.drive/` | a fresh start | Continue with section 2. An XS run never creates `.drive/`. |

Run `drive.py init --size <size> --goal -` with the goal verbatim on stdin through a quoted heredoc
(`<<'GOAL'`), so quotes, `$`, and backticks in the goal cannot break the command. `--goal-file <path>`
reads the goal from a file instead, with the same safety; `--slug <slug>` names the deliverable in one
to three lowercase hyphenated words (`linkkeeper`, `invoice-csv-export`), never the goal sentence cut
short, and every run passes it, because the slug names the intake commit, the report, and any paused
run (without it, `init` derives a short noun slug from the goal); and `--root <dir>` acts on a project directory other than the current one,
a flag `start`, `lint`, `end`, `preflight`, `freeze`, `guard`, `capabilities`, `visibility`, and
`worktree-land` also take. It moves the old
run's tracked files to `.drive/runs/<date>-<slug>/` with a RESTORE.md, parks its local files under
`.drive/local/archive/<date>-<slug>/`, and appends a DECISIONS.md entry whose Undo is the restore; it
commits nothing. It also records the owner's worktrees, local branches, and uncommitted paths in
`.drive/local/baseline.json`. The hygiene checks fail only on entries created after that moment, so
the owner's own work is never the run's to commit or remove. Write one line at the top of the new STATE.md's
"Resume here" block: `Paused run: .drive/runs/<date>-<slug>/ (status <status>, phase <phase>). To
restore: follow its RESTORE.md, then invoke /drive --resume.` Commit the move, the new GOAL.md, and
that DECISIONS.md entry together in the intake commit, so GOAL.md stays the run's first commit, and
name the paused run and its restore step in the final report. The archive is a decision with an undo,
so it needs no question.

## 2. Parse the goal

Write the six slots before running any command, so that what the tree contains does not bend what
the goal says. They feed the restate block and the classification.

| Slot | Write | Example for "The invoice export drops archived invoices since the last release; fix it without touching the billing API" | Decides |
|---|---|---|---|
| deliverable | the thing the owner holds at the end | an export that includes archived invoices again | outcome line, shape |
| verb | build, add, fix, move, upgrade, research, publish, deploy, speed up | fix | shape precedence |
| named systems | repositories, services, platforms, screens, stores | invoice export, billing API | probe searches, traits |
| constraints | stack choices, "keep X", "no new dependencies", stated deadlines | the billing API stays unchanged | restate constraints, must-not-change claims |
| quality words | "deep", "urgent", "annoying", "clean", "quick", "from scratch" | none | nothing; record them only |
| exclusions | "only", "just", "don't touch" | the billing API | out-of-scope line |

Quality words set neither size nor traits. "From scratch" becomes a constraint only when the goal
says what must not be reused.

## 3. Probe the tree

Spend about thirty seconds, inline, with no subagent. The probe only has to be good enough to
classify; archaeology does the reading.

```bash
git rev-parse --show-toplevel 2>/dev/null && git log --oneline -20 && git status --porcelain | head && git worktree list
git rev-parse HEAD                                   # baseline_sha
python3 <skill dir>/scripts/drive.py visibility    # PUBLIC limits what .drive/ commits; an unknown answer counts as PUBLIC (references/state-files.md section 2)
ls -a; test -f CLAUDE.md && head -80 CLAUDE.md; ls docs 2>/dev/null | head
ls package.json Package.swift *.xcodeproj *.xcworkspace wrangler.toml wrangler.jsonc Cargo.toml pyproject.toml go.mod Makefile justfile build.gradle* 2>/dev/null
ls -d migrations db/migrate prisma drizzle supabase/migrations 2>/dev/null; ls .github/workflows 2>/dev/null
grep -rIl --exclude-dir={node_modules,.git,vendor,dist,build} -E 'jwt|oauth|session|stripe|passport|apiKey|SECRET|password' . 2>/dev/null | head -20
grep -rIl --exclude-dir={node_modules,.git,vendor,dist,build} -i '<noun from the goal>' . 2>/dev/null | head
```

**An unrelated directory.** The directory is unrelated when it is not a repository, or when the noun
search finds nothing the goal names and the README and CLAUDE.md describe a different product. Then
search the projects root (`DRIVE_PROJECTS_ROOT`, or else the directory that holds this one),
`P="${DRIVE_PROJECTS_ROOT:-$(if git rev-parse --git-dir >/dev/null 2>&1; then dirname "$(git rev-parse --show-toplevel)"; else pwd; fi)}"`, with
`ls -d "$P"/*<name>* 2>/dev/null` and `grep -il '<name>' "$P"/*/README.md 2>/dev/null`. A hit is the
run's repository when it is where the deliverable will live; no hit is the evidence for new work.
Either way, return to `references/rigorous.md` section 2 step 0, which launches a background session in the existing
repository, or creates `<projects root>/<slug>` for new work (`build`, or `publish` of a new site) and
launches there, and then ends this session. Intake never continues in an
unrelated repository and never writes `.drive/` there. When this repository is the home, record its
absolute path as `repo:`; every brief states that root and writes commands as
`cd <root> && <command>`.

When the goal names a system with its own tools (an MCP server, a CLI, an API), load them now: one
ToolSearch `select:` call for the server's verbs, or `<cli> --version`. Record what answered under
`probe.system_tools`. A server the session reports as failed to connect counts as missing.

**Recon commands.** Find out how this repository builds and tests itself before you write any test
or brief. Look, in this order, at checked-in wrappers and scripts (`make test`, `./gradlew`,
`package.json` scripts, `scripts/`), the CI workflow steps that gate a merge, README and
CONTRIBUTING, CLAUDE.md, and the manifest's own convention. Write three exact commands with their
flags into GOAL.md's probe: the build, one focused test, and the full suite. Quote them verbatim in
every brief. Never assume a default such as `npm test`. If the focused test takes seconds, run it
once to prove the form works; the full-suite baseline belongs to archaeology. Write `none` for a
command the project does not have. `test_command: none` means no suite: a `report` or `operate` run
keeps it, and verdicts then need no full-suite run. In a greenfield repository, wave 0's plan line
creates the commands, and replacing each `none` with the real command needs a DECISIONS.md entry
naming it (`references/shapes/build.md`, wave 0).

## 4. Capability preflight

Once the size is S or above, and always after `drive.py init` (an archive must happen before
`.drive/` gains new files, and the script creates `.drive/` when it is absent), run
`drive.py preflight` and act on it (`references/long-running.md` section 3), then run
`drive.py capabilities` and the ToolSearch probe in
`references/capabilities.md` section 1, then apply that file's fallbacks. Intake uses the result in
three places. A claim whose verification capability is missing gets its ceiling written beside it
when the row is created, with the reason. `live means` names only an environment you can reach.
The substitutions go once into STATE.md. Never install anything, ask, or stop because of a gap.

## 5. Shape

Take the first rule that fires, then run the tests beneath it.

1. **A named defect, failure, wrong output, or flaky behaviour is `fix`.**
   - *Wording test.* A typo or a wording change in docs, comments, or copy is not a `fix`. With no
     runtime behaviour to break, it stays XS under section 9's rule for such edits.
   - *False fix test.* Establish that the expected behaviour once existed: a test that asserted it,
     a commit that introduced or removed it (`git log -S '<identifier>' --oneline`,
     `git log --oneline -- <path>`), documentation or a changelog that describes it. If none
     exists, it is a `feature` phrased as a complaint. "Fix the export so it also includes archived
     invoices", where history shows archived invoices were never exported, is a feature. "The export
     dropped archived invoices after the last release", where a commit removed them, is a fix.
   - *Incident test.* An outage, or an alert firing on a failure that is getting worse, is
     `fix/incident`, because only then is mitigating before the cause is known worth an `execute`
     phase and an Operational target. A recurring intermittent defect, even one users hit today
     ("find the intermittent 500 on checkout and fix it"), is a plain `fix` with `concurrency`
     suspected. A past failure that is not live now is a plain fix.
   - *Perf test.* A complaint that is a number (slow, heavy, laggy, memory, startup) is `fix/perf`,
     even when nobody says "bug".
   - *No symptom.* When the goal names no observable symptom ("find this bug"), find the candidate
     before classifying further: open failures in earlier `.drive/` state and `.drive/runs/`, failing
     CI runs (`gh run list --status failure --limit 20`), open issues labelled as bugs, errors in the
     system's own logs read through its tools, and the project's auto memory notes. Take the
     best-evidenced failure as an assumption in the restate block and list the others under
     Discoveries. When nothing is found, stop with a report of what was searched.
2. **"From X to Y", migrate, consolidate, upgrade, refactor, simplify, or replace, with behaviour
   preserved, is `move`**, with the variant from the verb. If the goal also asks for new behaviour,
   split it: the move first, the new behaviour as a `feature` sub-goal after cutover.
3. **Prose that is delivered and not deployed as a designed site is `report`.**
4. **A site, docs site, blog, or designed content that is deployed is `publish`.**
5. **A change of state in a live system with no code change as the point is `operate`**: deploy,
   rotate, import, cut over, clean up, get a service running again when no defect is named. A
   script the steps need is a small build package inside the operate run. A broken system with a
   named defect is `fix/incident`.
6. **Existing code that hosts the deliverable makes it `feature`.** The probe, not the goal,
   confirms that the code exists.
7. **Anything else is `build`.**

*Sub-goal test.* A goal holds two shapes when its parts would be proven by different claims and
could be committed and reviewed separately. "The sync job writes rows twice; fix that, then add a
sync history page" is a `fix` followed by a `feature`. "Move the settings screen onto the new
navigation and add a dark mode toggle" is `move/refactor` followed by `feature`. "Make search fast
by moving it to a dedicated index service" is one deliverable, fast search, so it is `fix/perf`; the
move becomes a re-classification if the diagnosis demands it. Run sub-goals in dependency order:
fixes before the features that sit on the fixed path, moves before the features that depend on the
new home. They share one `.drive/`, one restate block, and one STATUS.md. GOAL.md holds
`## Classification · <sub-goal slug>` and `## Plan · <sub-goal slug>` for each, in run order. Each
sub-goal has its own commits and gates. Every STATUS row belongs to one sub-goal and carries a
`sub:<sub-goal slug>` evidence token naming it, and `drive.py lint --gate <phase> --sub <slug>` checks
only the rows carrying that token, so a report sub-goal's gate never waits on the publish rows
written beside it. The run's size is the largest across the sub-goals. A research
or report deliverable runs before the pages or features that cite it. Every shape file ends in
retro, report, final audit, `lint --final`, and `drive.py end`; with sub-goals that tail runs once,
after the last sub-goal and over all of them, because `drive.py end` switches off drive's hooks for
the whole repository. Earlier sub-goals end at their last gated phase.

## 6. Variants

A variant changes one or two steps of its shape; the shape file holds the phase order. Record
`variant: null` when none applies.

| Variant | Signals | What changes | Default target |
|---|---|---|---|
| `fix/incident` | a live system failing now | an `execute` phase runs before `archaeology` and mitigates, with its undo recorded first (`mitigate` is not a phase name); the mitigation is removed only after the real fix is live-proven; `live-proof` is mandatory | Operational |
| `fix/perf` | the symptom is a number | `reproduce` is a baseline measurement by a committed script on a named path; `diagnose` is profile-driven; `verify` re-measures with the same script; every attempt goes in HUNT.md's ledger, kept or reverted | Live Proof when deployed, else Local Proof |
| `move/migration` | crosses a repository, service, platform, or store boundary | consumer census, characterization on the old path, shadow, dual-run and compare, flip, soak, decommission; MIGRATION.md holds charter, parity, stages, and undo ledger | Operational |
| `move/refactor` | in place, one codebase | no cutover or soak; commits are the cutover; characterization is still mandatory; no pre-existing test changes | Local Proof, or Live Proof when deployed |
| `move/upgrade` | toolchain, language mode, framework, or dependency major version | characterization is the existing build, suite, and a runtime or simulator smoke on the old toolchain; research reads the migration guide and changelog; step per module where the toolchain allows | as refactor |

## 7. Traits

A trait is anything the work touches that changes what must be proven. Record each as `confirmed`
(seen in the goal or the tree) or `suspected` (inferred). A suspected trait keeps its gate until
archaeology refutes it, because an unneeded gate costs minutes and a missed one ships broken work.
When archaeology refutes one, remove it and append a re-classification with the evidence. A trait
found later is added as confirmed at once. Stack files do much of the work: `Package.swift` or an
`.xcodeproj` confirms `native-platform` and `ui`; a `wrangler.toml` or `wrangler.jsonc` confirms
`api`, `external-systems`, and `deploy-infra` and makes `async-scheduled` and `data` suspected.
Phases below use canonical names; when the shape does not run a named phase, attach the gate to
the nearest earlier phase it does run (a `fix` has no `design`, so a `data` rollback plan belongs to
`diagnose`). Every gate applies at every size.

### ui

- **Signals.** Goal: screen, page, view, dashboard, app, email, PDF, generated report, terminal output, anything a human looks at. Probe: SwiftUI or UIKit files, React, Vue, Svelte, or HTML templates, stylesheets, email templates, TUI libraries.
- **Gate.** A design contract exists before any UI code: `drive:designer` writes it, or extracts it from the existing design system for a feature on an existing product. `drive:ui-reviewer` captures its own evidence of the rendered result and judges it against the contract, following `references/ui-verification.md`.
- **Phase.** `design` (or `content-plan` and `design` for publish) for the contract; `harden` for the review, or `design-qa` and `live-proof` in `publish`. In `fix` and `move`, the review runs at `verify` against the existing contract.
- **Artifact.** `design/DESIGN.md`, `design/tokens.json`, `design/screens.yaml`, `design/baselines/`; captures under `.drive/proofs/<key>/r<n>/shots/` with `findings.json`.
- **Exit check.** The contract's commit precedes the first UI code commit; every `[ui]` row has a `shot:` the reviewer captured and a reviewer verdict with no blocking finding.

### api

- **Signals.** Goal: endpoint, route, RPC, webhook, contract, integration for another client. Probe: server frameworks, route directories, OpenAPI or schema files, Worker or function configuration. A route that only renders a page for a browser is `ui`; `api` is confirmed when the change adds or alters a request and response that code consumes (JSON, RPC, a webhook, a fetch from the page's own script), and suspected when the design might add one.
- **Gate.** Contract tests on request, response, and error shapes. Live Proof needs a request against the deployed endpoint with its response captured.
- **Phase.** `design` pins the contract (wave 0 when parallel); `test-plan` plans the contract tests; `verify` runs them; `live-proof` makes the request.
- **Artifact.** The contract in DESIGN.md or a schema file in the repository; contract tests; `.drive/proofs/<key>/r<n>/live.md` with request and response.
- **Exit check.** Contract tests appear as `test:` tokens on the api rows; each api row with `live` y has a `live:` bundle whose `proof.json` target is the deployed URL, not localhost.

### auth

- **Signals.** Goal: login, session, token, key, secret, permission, role, billing, card, payment, personal data. Probe: auth libraries, `.env*`, key management, payment SDKs, the probe's secret grep, fields holding names, addresses, or health data.
- **Gate.** `drive:security-reviewer` (which invokes `security-review` itself) and `drive:severe-tester`, both on Opus, never in your context, even at XS. Secrets are named for the owner to set, never invented, committed, logged, or screenshotted. At M and above the threat model in `references/security.md` comes first.
- **Phase.** `design` for the threat model; `verify` for severe tests on every auth claim; `harden` for the review (at XS, before the commit).
- **Artifact.** `.drive/reviews/<date>-security-<slug>.md`; `severe:` tests on the trust boundaries. At XS the reviewer writes no file; its findings return in its final message, and the commit body quotes its verdict line and each finding's disposition.
- **Exit check.** The review exists for the range `<baseline_sha>...HEAD`, every finding has a disposition, every auth row carries a `severe:` token, and no attack material appears in your transcript.

### data

- **Signals.** Goal: table, schema, migration, backfill, import, store, retention, a new thing saved. Probe: `migrations/`, `db/migrate`, `prisma`, `drizzle`, ORM configuration, database bindings, a new write path in the touched code.
- **Gate.** A verified backup and a rollback rehearsed on a copy before any destructive step; schema changes use expand and contract; writes are idempotent; every test double on the path has a row in TESTPLAN.md's kindness ledger saying where it is kinder than production (bound-parameter limits, row and object sizes, timeouts, transaction semantics), with a guard, a live check, or a recorded accepted risk.
- **Phase.** `design` for the rollback plan; `test-plan` for the kindness ledger; before the `build` package that runs a destructive step for the backup and rehearsal; `verify` for the limit checks.
- **Artifact.** Rollback plan in DESIGN.md (MIGRATION.md's undo ledger in a move); kindness ledger in TESTPLAN.md; restore and rollback rehearsal in `.drive/proofs/<key>/r<n>/commands.log`.
- **Exit check.** A restore from backup and a rehearsed rollback appear in `commands.log` with timestamps before the destructive step's commit; no ledger row lacks a guard, a live check, or an accepted risk.

### existing-code

- **Signals.** Probe only: the repository has source for the touched area, or the goal names modules, screens, or services the probe finds. The goal alone never confirms it.
- **Gate.** An archaeology note and a recorded baseline of the full suite at `baseline_sha` before any change, plus the list of consumers of the code you will touch. A baseline that is already red is recorded as red; the failing tests become a discovery and are never quietly repaired or skipped.
- **Phase.** `archaeology`.
- **Artifact.** `.drive/how-it-works.md` (at most 150 lines, with the drift table) at M and above; at S, "Verified facts" lines in STATE.md. The baseline result goes in "Verified facts" with command, commit, and pass and fail counts.
- **Exit check.** The note names the three recon commands, the conventions of the touched area, and its consumers; the baseline line exists with a commit equal to `baseline_sha`.

### multi-repo

- **Signals.** Goal names two or more repositories, or a consumer in another repository. Probe: sibling repositories beside this one that import the touched package, vendored copies, workspace packages with separate owners.
- **Gate.** An ownership map (each repository, its role, which is the source of truth) and a change order; the cross-repository contract is pinned (a version, a schema file, a hash) before either side moves. The run lives in the repository that holds the deliverable, the destination of a move, where its session started. Every repository in the map goes under GOAL.md's `probe.repos` as an absolute path and into `additionalDirectories` in the launch settings (`references/long-running.md` section 2): a session nobody watches needs that grant to write outside its working directory, and drive's guard accepts writes only in the repositories `probe.repos` lists. A session launched without them relaunches from files with them before its first write to another repository, in the relaunch order of `references/long-running.md` section 3: set `status: blocked` with a "launch preflight" Blocked on line quoting the relaunch command, run it, and end the turn. Record each other repository's `git status --porcelain`, `git worktree list`, and branch list under "Verified facts" at intake, which is its hygiene baseline. Every command against another repository names it by absolute path (`git -C <absolute path> ...`, `cd <absolute path> && ...`).
- **Phase.** `archaeology` or `inventory` for the map; `decompose` for the order; the pin is a wave 0 item.
- **Artifact.** Ownership map and change order in DESIGN.md, or in MIGRATION.md for a move.
- **Exit check.** Every repository touched by a commit appears in the map with its order; the pin is committed before the first consumer change; the final git audit runs in every repository in the map.

### external-systems

- **Signals.** Goal names a hosting platform, app store, payment processor, identity provider, model provider, or third-party API. Probe: their SDKs, configuration files, webhook handlers.
- **Gate.** For each system record sandbox versus live, the secrets the owner must set (named, never invented), quotas and cost, and proof of egress from where the code runs rather than from this machine.
- **Phase.** `design` for the record; `live-proof` for egress and the live call.
- **Artifact.** An external systems table in DESIGN.md (system, sandbox or live, owner-set secrets, quota, egress check); the live call in a `live:` bundle.
- **Exit check.** A call made from the deployed runtime appears in `live.md` for every system on a `live` y row; every missing secret is named on a `credentials:` Blocked on line or recorded as set.

### async-scheduled

- **Signals.** Goal: cron, schedule, nightly, queue, workflow, retry, backoff, webhook, alarm, "every morning". Probe: cron triggers, queue consumers, workflow classes, alarms, launchd plists, scheduled CI jobs.
- **Gate.** Trigger the work now through the system's own tools, never "at the next tick"; writes are idempotent; a replay or backfill path exists; the trigger is observable.
- **Phase.** `design` for idempotency and replay; `build`; `live-proof` for the triggered run.
- **Artifact.** The trigger command and observed effect in `live.md`; a `severe:` test that runs the job twice and finds one effect.
- **Exit check.** Evidence from this session shows the trigger fired and its effect was read back; nothing scheduled is reported as done.

### concurrency

- **Signals.** Goal: race, sometimes, intermittent, parallel, lock, ordering. Probe: shared mutable state, actors, durable objects, transactions across requests, strict concurrency modes, worker pools.
- **Gate.** Severe tests on ordering and interleaving that run the operations many times in varied orders and assert invariants.
- **Phase.** `test-plan`; `verify`.
- **Artifact.** Stress or property tests named after the concurrency claims.
- **Exit check.** Each concurrency claim has a `severe:` test, and the verifier showed it failing when the synchronisation is removed in a scratch copy.

### native-platform

- **Signals.** Goal: iOS, iPadOS, macOS, watchOS, Android, native app. Probe: `Package.swift`, `*.xcodeproj`, `*.xcworkspace`, Gradle files, entitlements.
- **Gate.** The simulator loop: build, launch, screenshot, read the accessibility tree. Claims only a physical device can prove (camera, push delivery, real purchases, health sensors) carry `why:device-only:<reason>`, reach Local Proof without a device and Live Proof only with an `environment: device` bundle, and are never Done in a run without the owner's device; claims blocked on the owner's developer team stay at Partial. Headless runs use `xcodebuild test` with XCUITest and `xcrun simctl io <udid> screenshot`. Read `references/domains/ios.md`.
- **Phase.** wave 0 of `build` for a building scheme; `verify` and `live-proof`.
- **Artifact.** Screenshots and accessibility inspections under `.drive/proofs/<key>/r<n>/`; `proof.json` `target` naming the backend the simulator talked to.
- **Exit check.** Build and launch succeeded in this session and `drive:ui-reviewer` read a screenshot and the accessibility tree; every device-only claim carries its `why:device-only:` reason in STATUS.md.

### prose-content

- **Signals.** Goal: blog, docs, copy, README, announcement, about or team page, report prose. Probe: content directories, markdown collections, docs sites.
- **Gate.** `drive:writer` drafts with the prose skill resolved at preflight; every factual sentence traces to a research ledger row or is labelled opinion; `drive:grader` checks the trace.
- **Phase.** `research` for the ledger; `draft` or `build`; `verify`.
- **Artifact.** RESEARCH.md; for publish, positioning, site map, and page briefs in `.drive/content-plan/`; the grader's claim-to-source table under `.drive/proofs/<key>/r<n>/`.
- **Exit check.** The grader's table maps every factual sentence to a ledger row or an opinion label, and a search for placeholder text (lorem ipsum, TBD, sample posts, invented biographies) finds nothing.

### public-api

- **Signals.** Goal: library, SDK, package, consumers, semver, exported functions. Probe: a package manifest with exports, a registry publish configuration, generated API docs.
- **Gate.** An API review, a semver decision, a deprecation path for anything removed, and examples that run as tests. Drive never publishes to a registry on the owner's behalf; the report gives the publish command.
- **Phase.** `design` for the review; `verify` for the examples; `docs`.
- **Artifact.** `.drive/reviews/<date>-api-<slug>.md`; the semver decision in DECISIONS.md; example tests.
- **Exit check.** The examples run in the full-suite command and pass; the semver decision exists before `docs`.

### cli

- **Signals.** Goal: command, flag, tool you run, script for the terminal. Probe: `bin` entries, argument parsers, a `main` that reads argv.
- **Gate.** Golden output tests, exit-code assertions, a `--help` review, and hostile arguments (empty, unicode, very long, paths with spaces, missing files).
- **Phase.** `test-plan`; `verify`.
- **Artifact.** Golden files beside the tests.
- **Exit check.** Goldens exist for every documented command, and the verifier showed a changed output failing them.

### perf

- **Signals.** Goal: faster, slow, latency, memory, startup, bundle size, snappy. Probe: existing benchmarks, performance budgets, profiling scripts.
- **Gate.** A baseline measured by a committed script, a profile, a re-measurement with the same script under the same conditions, and the benchmark kept with a budget. Keep a change only when it beats run-to-run variance with every test green; a neutral result is reverted. Never report a number you did not measure.
- **Phase.** `reproduce` (or `archaeology`) for the baseline; `diagnose` for the profile; `verify` for the re-measurement.
- **Artifact.** The benchmark script; before and after numbers with commits and variance; the attempt ledger in HUNT.md (`fix/perf`) or RESEARCH.md.
- **Exit check.** Both numbers come from the same script at named commits, and the benchmark runs as a test with its budget.

### research-needed

- **Signals.** Goal: figure out, compare, which is best, market, competitors, a technology new to the repository. Probe: no prior art in the tree, platform limits the design will depend on.
- **Gate.** A research ledger before any design decision depends on the answer, each row dated and classed as verified fact, source claim, inference, or unresolved conflict, following `references/research.md`.
- **Phase.** `research`.
- **Artifact.** `.drive/RESEARCH.md`.
- **Exit check.** Every decision in DESIGN.md or the content plan cites a ledger row or is marked as an assumption, and `drive:grader` re-opened each load-bearing citation.

### deploy-infra

- **Signals.** Goal: deploy, release, environment, DNS, domain, infrastructure, configuration. Probe: platform configuration files, IaC directories, deploy scripts, CI deploy jobs.
- **Gate.** A deploy plan with an undo for each step, a configuration diff saved before apply, and a live smoke check after, read back independently of the deploy command.
- **Phase.** `design` (or `plan` in operate) for the plan; `deploy`, `execute`, or `live-proof` for apply and smoke.
- **Artifact.** The plan in DESIGN.md or GOAL.md's step plan; the config diff and smoke in the `live:` bundle.
- **Exit check.** Each step's undo is committed before the step runs; the smoke result is an observed response, never the deploy command's exit code; for a site, production serves the tested build, and a preview deployment is Local Proof.

### ai-llm

- **Signals.** Goal: prompt, model, agent, embeddings, generated suggestions, classification by a model. Probe: model SDKs, prompt files, API keys for model providers.
- **Gate.** An eval set with expected behaviours, handling for non-determinism (repeats and pass thresholds), a cost budget, and prompts versioned in files; graders are never the maker.
- **Phase.** `test-plan` for the eval set; `verify` for the run.
- **Artifact.** The eval set in the repository; eval results with repeat counts under `.drive/proofs/<key>/r<n>/`.
- **Exit check.** The eval ran with its numbers and repeat count recorded, and every prompt that shipped is a versioned file.

### large-surface

- **Signals.** The same change across about twenty files or more, counted by the probe (`grep -rl '<pattern>' <src> | wc -l`), never guessed.
- **Gate.** Fan out in waves of at most eight makers, verified per wave at M and per package at L and XL (`references/verification.md` section 2), following `references/parallel.md`.
- **Phase.** `decompose`; `build`.
- **Artifact.** `.drive/packages/<id>/brief.md` and `report.json`.
- **Exit check.** Every package's claims have a passing verdict, and `git worktree list` prints one line after each wave.

### generated-code

- **Signals.** Probe: files with "generated" or "do not edit" headers, `*.pb.go`, `*_pb2.py`, `*.generated.*`, codegen configuration, vendored directories.
- **Gate.** Never hand-edit; change the source or generator and regenerate.
- **Phase.** `build`.
- **Artifact.** The regeneration command in STATE.md "Verified facts".
- **Exit check.** The verifier re-runs the generator on the committed source and `git status --porcelain` shows no change.

## 8. Threshold discipline

Marking too many traits adds gates that find nothing: every run marked `auth` and `data`, three
reviews per package, and a budget spent on checks with no findings. Apply these thresholds.

- `auth` attaches when the diff touches identity, money, or personal-data code or configuration, or
  the claims themselves are about them. Showing a user's display name on a page is not `auth`.
- `data` attaches on schema or migration changes and new write paths, not on a read of an existing
  table. The kindness question still applies when a read is tested against a double.
- `concurrency` attaches when shared mutable state or interleaved I/O exists on the path, not
  because the language has threads.
- `ui` attaches to anything a human looks at, including email and terminal output, and never to an
  internal data structure that happens to be named "view".
- `large-surface` needs the count, and `research-needed` needs a decision that depends on the
  answer; unfamiliarity alone sets neither.
- Every suspected trait names the probe line that raised it. A suspicion with no line is not
  recorded.
- The number of traits never sets size, and a trait never adds a phase from another shape.

## 9. Size

Size is the largest size any single structural trigger demands. Risk never sets it; traits carry
risk at every size. Write the trigger that set it in `size_set_by`, because re-classification checks
against that fact.

| Trigger | XS | S | M | L | XL |
|---|---|---|---|---|---|
| Components touched | one function or file | one module | several modules in one app or service | two surfaces or two repositories | three or more surfaces or repositories |
| Unknowns after the probe | none; cause or change known | at most one, answered by reading code | two or three, answered by archaeology or a spike | a design unknown | the problem itself is open |
| UI surface | none | a change to one existing screen | new screens in an existing app | a new client | a new product across clients |
| Honest duration | minutes | under two hours | about a day | one to three days | several days |
| New files | none or one | a few | a directory | a package or app | a repository or several |

**Borderline.** When two adjacent sizes are both defensible, take the smaller and rely on
re-classification, except for `move` and `operate`, where take the larger, because an under-called
size there skips the cutover plan or the undo record. A two-line change to a session-token check is
XS with `auth`, and the security review still runs. A rename across sixty files with no logic change
is M by component count, with `large-surface`. A one-module refactor that could be S or M is M.

| Size | Files created | Agents and verification | Final review | Live proof | Starting budget |
|---|---|---|---|---|---|
| XS | none; the commit body records claim and evidence | none except trait gates; one refutation test seen red then green, except for an edit with no runtime behaviour (docs, comments, copy, a typo), whose evidence is the diff plus whatever check applies (a render, link check, spell check, or the build), named in the commit body, with no failing test first; the project's checks; the run becomes S when a second non-test source file changes, a workaround is needed, or the test cannot be made to fail first | none | only when a trait gate demands it | minutes |
| S | GOAL.md, STATE.md, STATUS.md with one to three rows, plus the shape's ledger (HUNT.md for fix, RESEARCH.md with a `## Brief` section for report), a SPEC.md under 300 words for a feature or build, and TESTPLAN.md with its kindness ledger once a test double is on a claim's path | one independent verifier; a severe test per claim by `drive:severe-tester`, which Local Proof requires (for a fix, on an adjacent input); planning reviews at one full round plus at most one scoped re-check of its blocking findings, the spec folded into one combined review of design and test plan | `drive:auditor` for build, move, every `fix/incident`, or a feature with five or more claims; otherwise a fresh `drive:verifier` with the checklist in `references/definition-of-done.md` section 6; never the grader | for `live` y rows when a deploy target exists; otherwise the target and reason are written | 15 turns, 8 subagents, 30 minutes |
| M | everything the shape and traits call for: SPEC.md or the shape's spec file, TESTPLAN.md, DECISIONS.md, CONSTRAINTS.md from measured values (at archaeology, or after wave 0 for a greenfield build) | a fresh `drive:architect` review of the classification before the intake commit; a spec review, then one combined review of design and test plan, each one full round plus at most one scoped re-check; a verifier per wave, and per package for a package carrying an auth, money, or data-loss claim; conformance grader; a severe test per claim, with severe review scaled to the diff | as S | required when a deploy target exists | 40 turns, 40 subagents, 3 hours |
| L | adds RESEARCH.md, DESIGN.md, LESSONS.md | adds research lanes, separate spec, design, and test strategy reviews by `drive:auditor` of up to three full rounds each, a verifier per package, and for build a walking skeleton proven live at the end of wave 0 | `drive:auditor`, for every shape | a requirement for every `live` y row | 100 turns, 90 subagents, 12 hours |
| XL | as L | adds phase gates with a re-classification review by `drive:auditor`, workflow fan-out for bulk, and per-phase bounds | as L | required per surface | 250 turns, 200 subagents, several days |

Budgets are starting targets in turns, subagents, and wall clock; the dollar target comes from
`references/models.md`. A target is a checkpoint, not a stop. The lint counts only maker spawns
against the subagent figure (`drive:implementer`, `drive:writer`, `drive:designer`, `drive:architect`,
`drive:researcher`), so the reviews a size requires (verifiers, graders, the UI, severe, and security
reviews, and the final audit) never push a run past it, and past the figure it warns and names the
checkpoint work rather than failing. Only a `stop:` line the owner wrote in GOAL.md ends a run early.

## 10. Derive the plan

1. Read `references/shapes/<shape>.md`. Take its phase order and its thinning for this size.
2. Delete the phases the shape and size skip. For each phase you keep, name its artifact and the
   later phase, gate, or package that reads it. Delete any phase whose artifact nothing reads.
3. Insert each confirmed and suspected trait's gate at its phase from section 7, inside that
   phase's exit check, or as its own plan line when it has its own artifact.
4. For `build`, and for a `feature` that bundles capabilities with their own users or data, put a
   capability map before `spec`; its build order becomes the wave order. Put first the package that
   rests on an assumption that must be true.
5. Name the checker for every line. You check intake, archaeology, research completeness,
   decompose, and docs. An agent that did not do the work checks spec, design, build, verify,
   integrate, live-proof, harden, and the final audit.
6. Write `live means` in one line: the deployed host, the device or simulator and what it talks to,
   or the clean environment a CLI installs into; for prose, `out of scope: <reason>`. Create the
   STATUS rows you already know with their `live` value (at S, all of them; at M and above the spec
   adds the rest, and each row's `live` is fixed when it is created). Write any target below the
   shape's default beside its claim now, with the reason.
7. Write the budget line, and the `stop:` line with what the owner's goal names, otherwise `none`.
8. At M and above, spawn a fresh `drive:architect` in review mode with the goal verbatim, the probe
   output, and the draft GOAL.md, asking whether shape, variant, size trigger, and traits follow from
   this file. It writes `.drive/reviews/<date>-intake-review-r1.md` from `templates/review.md`, with
   `verdict:` and `round: 1/1` first (`references/verification.md` section 6). Apply its blocking
   findings before the commit, because every later phase inherits the classification.
9. Commit before any other work, once the review has returned and no agent is running, which is the
   one moment staging the whole directory is safe; every later commit stages paths by name
   (`references/state-files.md` section 10):
   `git add .drive .gitignore && git commit -m "drive(intake): <goal slug>"`. The lint and the final
   audit find this commit with `git log --grep '^drive(intake): <goal slug>$' --format=%h -1`, never
   by the first commit that added GOAL.md.

Plan lines use one grammar:
`- [ ] <phase> · artifact: <path> · exit: <checkable condition> · checker: <orchestrator | any roster agent name>`.
A roster name may carry the `drive:` prefix or omit it. An `operate` step names itself in words
between the phase and `artifact:`, as `references/shapes/operate.md` shows:
`- [ ] execute · rotate the api key · artifact: .drive/proofs/api-key-rotated/r1/commands.log · exit: command completed with output saved · checker: orchestrator`.
An exit that cannot be checked by a command or a file ("design is good") is a defect in the plan.

## 11. GOAL.md: the restate block and the classification block

The restate block comes right after the header. Each line is quoted from the goal or begins with
`assumption:`; out of scope is never blank, because an unstated boundary is where the owner and the
run most often disagree. Filled example:

````markdown
# GOAL · invoice-csv-export
goal: "Add CSV export to the invoices list in the admin app. Finance needs it before quarter close. Keep the existing PDF export as it is."
live means: the staging deployment named in deploy/staging.toml, exercised from a browser against its real database
budget: 40 turns · 40 subagents · 3 h · usd per references/models.md
stop: none

## Restate
- outcome: "CSV export to the invoices list in the admin app"
- user: "Finance"
- why now: "before quarter close"
- success: assumption: a finance user downloads a CSV of the currently filtered invoices, and it opens in a spreadsheet with the same totals the list shows
- constraints: "Keep the existing PDF export as it is"; assumption: no new runtime dependency
- out of scope: assumption: scheduled or emailed exports, other lists, import

## Classification
```yaml
shape: feature
variant: null
size: M
size_set_by: "several modules: list screen, export endpoint, CSV serializer; two unknowns (large result sets, column set)"
traits: { confirmed: [existing-code, ui, api], suspected: [auth] }
suspected_because: { auth: "invoices carry customer names and addresses; export access control may be new code" }
probe:
  repo: /path/to/admin-app
  stacks: [typescript, react, node]
  build_command: "npm run build"
  focused_test_command: "npx vitest run src/invoices/list.test.ts"
  test_command: "npm run test:ci"
  baseline_sha: "3c9d2e1"
  recent_history: "20 commits; the last 4 touch src/invoices/*"
  claude_md: present
  system_tools: none
assumptions:
  - text: "The export streams from the existing invoice query; no new table."
    overturned_by: "the query cannot page, or finance needs fields the query does not return"
not_asked:
  - question: "Which columns?"
    default: "the columns the list shows, plus invoice id and currency"
classified_at: 2026-09-14T09:12Z
reclassifications: []
```

## Plan
- [ ] intake · artifact: .drive/GOAL.md · exit: a fresh architect's classification review in .drive/reviews/2026-09-14-intake-review-r1.md has no blocking finding; committed as drive(intake) · checker: orchestrator
- [ ] archaeology · artifact: .drive/how-it-works.md · exit: baseline of npm run test:ci at 3c9d2e1 recorded; export consumers listed; auth suspicion confirmed or refuted · checker: orchestrator
- [ ] spec · artifact: .drive/SPEC.md · exit: every claim refutable and in STATUS.md with live fixed; PDF export listed under must not change; the spec review, one round and at most one scoped re-check, leaves no open blocking finding · checker: architect
- [ ] design · artifact: design/ extended; .drive/DESIGN.md contract for the export endpoint · exit: reviewed together with the test plan below, one round and at most one scoped re-check, with no open blocking finding · checker: architect
- [ ] test-plan · artifact: .drive/TESTPLAN.md · exit: one refutation test per claim at an honest layer; kindness ledger covers the test database; the combined review wrote this file's own test-plan review file · checker: architect
- [ ] build · artifact: code and tests · exit: gates green; each wave's verdict passes, with the export access check verified alone if auth is confirmed · checker: verifier
- [ ] verify · artifact: .drive/proofs/wave-1/r<n>/verdict.json · exit: every row at Local Proof; [ui] rows have shot: from ui-reviewer · checker: verifier
- [ ] live-proof · artifact: live.md per live y row · exit: a CSV downloaded from staging matches the list totals · checker: verifier
- [ ] harden · artifact: .drive/reviews/ · exit: severe tests and, if auth confirmed, security review with dispositions · checker: security-reviewer
- [ ] docs · artifact: docs/admin/invoices.md · exit: export described where finance looks · checker: orchestrator
- [ ] retro · artifact: .drive/reviews/<date>-retro.md · exit: investigations closed; lessons committed or none with the reason · checker: orchestrator
- [ ] report · artifact: .drive/REPORT.md · exit: final review go; lint --final passes · checker: verifier

## Re-plans
````

`decompose` and `integrate` are absent from that plan because a feature with three or fewer
packages folds them into `build`; the plan says so by leaving them out, and the shape file is the
authority for that thinning. At S the probe keeps the same fields and the plan has four to six lines.

## 12. Decisions you take, and the one question

Decide, record, and continue. Every decision the goal does not settle is yours, sorted into three
tiers.

| Tier | Includes | Do |
|---|---|---|
| Always | anything `git revert` undoes with no effect outside the repository: running the project's checks, following its conventions, validating input at boundaries, creating files, restarting local services, committing on the current branch in small steps | act; log it in DECISIONS.md only when it chose between real alternatives |
| Allowed once the undo is written in DECISIONS.md | schema changes (with the `data` gate), new dependencies, development or runtime, configuration or CI changes, deletions with zero-reference evidence (dynamic lookups, configuration, and other repositories searched), deploys to environments with a rollback, archiving another run's state | write the entry with its exact undo, commit it with the change or before it, then act |
| Never | committing a secret, hand-editing vendored or generated code, removing or weakening a failing test, entering credentials or payment details, creating accounts, accepting legal terms, creating a branch or tag or pushing in any worktree, force-pushing, `git reset --hard` or to another commit, `git update-ref HEAD`, `git stash` (beyond `list` and `show`), `git clean` (beyond a dry run), or `git commit --amend` in the shared checkout, opening pull requests, commenting, posting, or publishing on the owner's behalf, messaging real users, destroying data without a verified backup | refuse; if the goal needs it, it is a stop condition: finish everything else, name the exact step the owner takes, and record it on the Blocked on line with its stop-condition token (`credentials:`, `payment:`, `legal:`, `account:`, or `destructive:`) |

A DECISIONS.md entry uses the grammar in `references/state-files.md` section 8: Context, Decision,
Rejected, Undo with its reversal cost, Evidence, and Narrows. Entries are never deleted; an assumption
later confirmed or overturned gets a new entry naming the one it settles.

**The single-question test.** Ask only when all of these hold:

1. Two readings of the goal lead to different deliverables.
2. Proceeding on the wrong one would destroy work or waste more than an hour that cannot be
   redirected.
3. No default is defensible from the goal, CLAUDE.md, the owner's preferences, or research.
4. The step it gates has no possible undo; anything with an undo is decided and logged instead.

Never ask what CLAUDE.md or the preferences already answer, what has an industry default (session
length, error tone, retention defaults), what research can settle, or what a later phase owns. Write
the question as plain text at the end of a turn that has already delivered all progress that does
not depend on it: `One decision needs you: <question>. I have taken <default> because <reason>; to
change it, say "<sentence>". Until then, <what continues>.` Record it on a `destructive:` Blocked on line in STATE.md
(or `credentials:`, `payment:`, `legal:`, or `account:` when that is what the gated step needs), and in
`not_asked` if you chose not to ask. Apply the default at once when the choice is reversible;
block only for irreversible, destructive, credential, payment, or legal steps. Never ask a second
question; a second is a defect of intake and is logged as one.

Worked tests. "Which charting library?" fails test 4: it is reversible and the existing library is a
defensible default. "Drop the old column after the migration?" fails test 4: expand and contract
keeps the column, and the contract step waits with its undo. "One user per account or shared
workspaces?" for a new app that stores user data passes tests 1 to 3 and still fails test 4 early,
because the data model is cheap to change before build; take single-user, record its reversal cost
rising after the first migration, and continue. "Delete the production bucket of the service being
decommissioned?" passes all four when the goal implies decommissioning and no backup can be
verified; it becomes the question, and every other step finishes first.

## 13. Re-classification

**At every phase gate**, before the next phase starts, answer three questions: does the shape still
describe the work; has a trait been confirmed, refuted, or newly found; has any structural trigger
passed the size's ceiling. When all three are no, write `reclassification check: none` in the gate
commit body. Otherwise apply the events table. At XL, a fresh `drive:auditor` reviews those three
answers against the evidence before the next phase starts.

**On events**, immediately, wherever you are:

| Event | Change | Also do |
|---|---|---|
| A fix needs an interface change or touches more than one module | `fix` becomes `move/refactor`, or a `feature` sub-goal if behaviour changes; size up one | the reproducer becomes the first characterization test; characterize the callers |
| A feature needs a schema or store change | add `data` confirmed | rollback plan and kindness ledger before build continues |
| A cron, queue, workflow, alarm, or webhook is on the touched path | add `async-scheduled`, and `external-systems` when it calls out | plan the trigger-now evidence and idempotency before the code |
| An auth, secret, payment, or personal-data file enters the diff | add `auth` confirmed, even at XS | schedule `drive:security-reviewer` and `drive:severe-tester` |
| A workaround is about to be used a second time | stop; the diagnosis was wrong | open an investigation; change nothing until it names a mechanism |
| The component or repository count passes the size's ceiling | size up one | add the new size's ceremony to the remaining phases only |
| Research overturns a recorded assumption | update the assumption with its evidence | re-derive the plan from the affected phase forward |
| Archaeology refutes a suspected trait | remove it | remove its gate lines with the evidence |
| Reproduction shows a known one-line cause | size down to XS or S | keep the reproducer as the regression test |
| The owner's follow-up changes the deliverable | a new sub-goal, classified from section 2 | earlier sub-goals keep their plans and targets |
| The goal's thing already exists, or the honest answer is "do not build this" | none | stop with a report that shows the evidence and the nearest useful goal |

**Protocol.** Let running makers finish their current package and start no new one. Write the
discovery in STATE.md with its evidence path. Append to `reclassifications` and add a dated line to
`## Re-plans` naming the phases re-derived. Re-derive from the current phase forward; never restart
a completed phase and never discard evidence (a reproducer stays a test, a ledger stays a ledger).
Targets carry forward; a change that lowers one or removes a phase needs a DECISIONS.md entry in the
same commit. A re-plan may extend the budget by at most half, once per run, logged. A third re-plan
that changes the shape or the goal ends the run with a report; size changes, added packages, and a
`diagnose` ledger that moves do not count.

```yaml
reclassifications:
  - at: 2026-09-14T11:40Z
    gate: diagnose
    from: "fix / S"
    to: "move/refactor / M"
    because: "the retry wrapper fires twice under backoff; a cause-level fix changes three callers"
    evidence: ".drive/HUNT.md#retry-wrapper-double-fire"
    added: [characterization tests on the three callers, blast-radius review]
    kept: [reproducer, now the first characterization test]
    decision: null
```

## 14. Worked classifications

**A native mobile app with a serverless backend, described in a few paragraphs.** Shape `build`,
size XL, set by three surfaces (the client, the backend, storage) and an open problem. Confirmed:
`ui`, `native-platform`, `api`, `external-systems`, `data`, `auth` (accounts), `deploy-infra`,
`research-needed`. Suspected: `ai-llm` if the paragraphs describe generated content,
`async-scheduled` for background processing, `prose-content` for store copy. The plan runs research
lanes on platform limits and comparable products, a capability map, a spec with refutable claims, a
design with the client and backend contract pinned before either side, a design contract, a test
plan with a kindness ledger for every local stand-in, wave 0 ending in a walking skeleton (one
request from the app in the simulator to the deployed backend and back), parallel waves with
verifiers, integrate, full live proof on both surfaces, harden with security review, docs, retro,
and the auditor's final audit. Claims only a physical device can prove, such as push delivery, carry
`why:device-only:`, so without the owner's device the run ends `stopped` with those rows explained.
Recorded assumptions: single-user accounts, no payments in the first
version. Not asked: the minimum OS version, defaulting to the current release minus one. Watch for
payments (widens `auth`, adds a payment processor) and generated content (confirms `ai-llm` and puts
an eval set before the waves).

**"Find this deep annoying bug and fix it," in an existing codebase.** Shape `fix`, size M at intake,
set by an unknown cause (two or three unknowns in one service). "Deep" and "annoying" set nothing.
The goal names no symptom, so intake first searches for the bug the owner means: open failures in
earlier `.drive/` state, failing CI runs, open bug issues, the system's own logs, and auto memory
notes. It takes the best-evidenced failure as an assumption in the restate block, and when nothing is
found it stops with a report of what was searched. Confirmed: `existing-code`; other traits come from
the failing path once found. The plan is narrow archaeology of the failing path and its history,
reproduce (a failing test, or a loop that shows the failure rate when intermittent), diagnose through
`drive:investigator` with a hypothesis ledger, fix at the cause, verify with the reproducer red in a
`git archive` copy of the pre-fix commit and green after, a blast-radius check, and retro. Not asked:
how to reproduce it; if reproduction fails within budget, that is the finding, and the run ends
`stopped`. Watch for a design cause (to `move/refactor`), a one-line cause (down to S), and a second
workaround (stop and investigate).

**"Add a new dashboard to the existing product."** Shape `feature`, size M, set by several modules (a
route, a query, screens) and two unknowns (the charting approach and who may see it). Confirmed:
`existing-code`, `ui`. Suspected: `api`, confirmed when the page fetches its data from a new endpoint rather than rendering it on the server; `data`, refuted when there is no schema change and tests
run on the real engine; `auth`, confirmed if the dashboard needs new role checks. The plan is
archaeology with a green baseline, a change spec, a design delta that reuses the component library,
a test plan, build with a verifier per wave (a package carrying new role checks verified alone), UI review at desktop and phone widths, live proof on
staging when it exists, scaled harden, and a docs delta. Recorded assumptions: reads existing
metrics and needs no ingestion; visibility matches the existing admin pages. Watch for a new
aggregation table (confirms `data`) and a new role (confirms `auth`).

**"Move a model gateway from a separate project into a core service of the platform."** Shape
`move/migration`, size L, set by two repositories and a design unknown (where it lives and how
consumers switch). The run lives in the platform repository, which holds the deliverable, even
though the goal names the gateway's repository; that one follows "from" and is never the home. Both
repositories go under `probe.repos` and into `additionalDirectories`, because the run still writes
to the old gateway (identity logging during the dual run, then decommission), and commands against it
name it by absolute path. Confirmed: `existing-code`, `multi-repo`, `api`, `auth` (provider keys and caller
credentials), `external-systems`, `deploy-infra`. Suspected: `async-scheduled` (retries, usage
rollups), `data` (usage logs), `concurrency` (rate limits). The plan is archaeology of both
repositories, an inventory with a consumer census and ownership map, characterization tests
recorded against the current gateway, a cutover design with an undo per stage, steps per adapter
with a verifier each, dual-run and comparison, flip by configuration, live proof from the platform's
runtime, a soak with a scheduled check that decides and acts, decommission, and a runbook. No new
behaviour enters the move; the wish list becomes a `feature` sub-goal after cutover. Not asked: the
home service, defaulting to the platform's existing outbound-integration module. Watch for a third
repository (to XL) and usage data needing a schema (confirms `data`).

**"Research our market position and build a website about the project, goals, and team, with blog
and documentation sections."** Shape `publish`, size L, set by two surfaces (a research deliverable
and a multi-section site) and a design unknown. Confirmed: `research-needed`, `prose-content`, `ui`,
`deploy-infra`. Suspected: `external-systems` (hosting, analytics); `api` and `auth` only if a form
collects addresses. The market research is a deliverable in its own right: it runs first as a
`report` sub-goal, and the content plan cites its ledger; the retro, report, and final audit run
once, after the publish sub-goal. The publish plan is a content plan, a
design direction, build, drafting per page by `drive:writer` with every claim traced, design QA at
360, 768, 1280, and 1600 px and in dark mode with Lighthouse and accessibility thresholds written at
intake, and a preview deploy with an undo. Production is in scope only when the goal asks for a
launch or a production target already exists; otherwise the rows are created with `live` n and the
promote command goes in the report. Recorded assumptions: static hosting, markdown blog, no CMS. Watch for a signup form, which
attaches `api` and personal-data `auth`.

**Edge case: "make the app faster."** Shape `fix/perf`, size M, set by an unknown metric and path.
Traits: `existing-code`, `perf`, and the app's own (`ui`, `native-platform` for a mobile app). Do not
ask which path. Measure the obvious user-facing paths with a repeatable script, pick the worst
against a reasonable budget, record the choice as an assumption, then baseline, profile, keep or
revert each attempt, and keep the benchmark. Watch for an architectural cause across the codebase
(to `move/refactor` at L) and a single hot spot (down to S).

**Edge case: "upgrade to the next major version of the language toolchain."** Shape `move/upgrade`,
size M, or L when the probe counts twenty or more affected modules, which also confirms
`large-surface`. Confirmed: `existing-code`, `research-needed` (the migration guide and behaviour
changes), and `concurrency` when the new version changes concurrency checking; `ui` and
`native-platform` for regression when the app has them. Characterize with the existing build, suite,
and a runtime smoke before touching anything, then change module by module and compare the same
smoke. No refactor beyond what the compiler demands; cleanups become a later `move/refactor`.

**Edge case: "write a market research report only."** Shape `report`, size S for a narrow question
or M for a market map. Traits: `research-needed`, `prose-content`. `live means: out of scope:
prose deliverable`. At S the run writes GOAL.md, STATE.md, STATUS.md, and RESEARCH.md with its `## Brief`
section at the top. The plan decomposes the question,
runs source lanes into the ledger with a cross-check lane for contradictions, has an adversarial
reader on Opus try to refute the central claims, drafts under the prose skill, and delivers a file.
Unverified claims are listed as unverified, never dropped.
