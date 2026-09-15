# Specification

Read this file before writing or reviewing a spec, a change spec, a bug brief, a migration charter,
or a report brief, and again whenever reality contradicts a spec mid-run. It decides which template
a shape uses, what goes in and what stays out, how requirements become STATUS keys and test names,
how open questions are settled without the owner, when the one question may be asked, who reviews
the spec and against what, and how a spec changes after the build has started.

## Contents

1. What the spec is for
2. Which template, by shape and size
3. Read before you decide
4. Who writes it
5. Requirements are claims
6. Keys and the trace
7. Decide and log
8. The single question
9. Constraints, omissions, and non-goals
10. Budgets, success criteria, and the cheat test
11. Conditionals by trait
12. The spec review
13. The spec gate
14. Changing the spec mid-run
15. Excuses and rebuttals
16. Red flags

## 1. What the spec is for

The spec stands in for the owner while the owner is away. Two tests decide its quality. An agent that
has read only the spec and the code must be able to decide what to do next without asking anyone. The
owner, returning hours later, must be able to see every decision made on the owner's behalf and overturn
any of them in one sentence, knowing what that costs. The executable core is the requirements; goals,
non-goals, constraints, budgets, success criteria, assumptions, risks, glossary, and changes sit
around it, and nothing else is load-bearing.

## 2. Which template, by shape and size

| Shape or variant | Template | Written to | Load-bearing section |
|---|---|---|---|
| `build` | `templates/SPEC.md` | `.drive/SPEC.md` | Requirements |
| `build` of a new library or CLI | `templates/SPEC.md`; every exported symbol or command is a requirement | `.drive/SPEC.md` | Requirements |
| `feature`, and changes to an existing library, CLI, or data pipeline | `templates/change-spec.md` | `.drive/SPEC.md` | Must not change |
| `move/refactor`, `move/upgrade` | `templates/change-spec.md` with no new-behaviour requirements | `.drive/SPEC.md` | Must not change |
| `move/migration` | `templates/MIGRATION.md` | `.drive/MIGRATION.md` | Invariants and parity |
| `fix`, `fix/incident`, `fix/perf` | `templates/HUNT.md` | `.drive/HUNT.md` | Reproduction and ledger |
| `report`, and the research half of `publish` | `templates/report-brief.md` | a `## Brief` section at the top of `.drive/RESEARCH.md`, above Status | The decision it serves |
| `publish` site | no template for the content plan (positioning, site map, page briefs), which follows `references/shapes/publish.md`; the short form of `templates/change-spec.md` for the site's behavioural claims only | `.drive/content-plan/`; `.drive/SPEC.md` for the behavioural claims | Page briefs; Requirements |
| `operate` | none; the step plan with an undo per step lives in GOAL.md | `.drive/GOAL.md` | Undo per step |

XS creates no spec; the commit body carries the claim and its evidence. At S a spec phase writes the
short form of its template (claims, their refuting scenarios, and "Must not change") in under 300
words. A `move` never specifies new behaviour; wanted new behaviour becomes a `feature` sub-goal. If
the repository already keeps specs in its own format and place, write there under the rules below
and make `.drive/SPEC.md` a one-line pointer. Length budgets: build 1,500 to 4,000 words and 15 to 40
requirements (more means the goal needs a first version and named non-goals); change spec under 800
words; migration charter 1,000 to 2,500; bug brief under fifteen lines; report brief under 300 words.

When the goal bundles capabilities that have their own users or data, could ship separately, or could
be cut without rewriting the others, `.drive/capability-map.md` (from `templates/capability-map.md`,
procedure in `references/design.md` section 3) is written before SPEC.md. SPEC.md then holds one
`## Requirements · <module>` section per module, named exactly as in the map and in build order; the
contract between two modules is specified in the provider's section.

## 3. Read before you decide

Before drafting, read GOAL.md (goal verbatim, restate block, classification, assumptions,
`not_asked`); the owner's preference files (the user-level `CLAUDE.md` when readable, the project's `CLAUDE.md` and
`.claude/rules/`, the auto memory index); the repository's README, docs index, existing specs or
requirement registries, and test layout; `.drive/how-it-works.md` when archaeology ran;
`.drive/RESEARCH.md`; and the lessons quoted in the brief. A question these already answer is not
open, and raising it is a defect. Platform constraints must land before drafting, because they become
numbers. Slower research such as a competitive scan may arrive mid-draft and enters only as non-goals,
table-stakes requirements, and glossary terms, never as a list of features to copy.

## 4. Who writes it

`drive:architect` writes SPEC.md and MIGRATION.md. You write HUNT.md's brief at intake and the report
brief; `drive:investigator` fills HUNT.md's ledger. Open the architect's brief with the reason ("I'm
working on <goal> for the owner, who is not watching. The spec you write is what every later agent
reads instead of asking the owner. With that in mind: ...") and give it the repository root as an absolute path,
the goal verbatim, shape and traits, the paths in section 3, the template, this file, the output
path, and any command it may run written as `cd <root> && <command>`. Every other brief this file
describes, including the reviewer's, states the root and writes commands the same way. Ask for the file, the requirement
headings, the assumptions made, and at most one candidate question with its default. Never ask it to
explain its reasoning; the assumptions log records decisions, which is what the owner needs.

## 5. Requirements are claims

Each requirement is a `###` heading of three to eight words, unique in the document, phrased as a
claim that could be false: "Deleting the account removes every photo", "An expired token is
rejected". A claim is already the statement a test will try to refute. Under each heading write:

- One paragraph of intent: what the user or caller gets and why it matters.
- Two to five scenarios, each with a bold title of at most ten words, unique in the document, and
  Given, When, Then lines. Then describes observable output, never internal state. More than five
  scenarios means two requirements.
- A line `What would prove this wrong` followed by at least one scenario that a plausible wrong
  implementation would fail. Restating the happy path in the negative does not count; if you cannot
  name the wrong implementation it catches, write a better scenario.
- `Failure behaviour:` whenever the requirement depends on a network, a permission, a quota, another
  service, or partial success: what the user sees and what the system does.

Invariants are claims too: the entries under "Must not change" in a change spec and "Invariants" in a
migration charter. Each has a claim heading, a guard (a test that exists today or a characterization
test captured from the current code), and at least one regression scenario under "What would prove
this wrong"; it gets a STATUS row like any requirement. Write triggers and responses in plain
sentences, never capitalised "WHEN ... SHALL" form. Refer to requirements by their words; numbered
requirement or criterion codes never appear anywhere in a spec.

## 6. Keys and the trace

The key is the slug of the heading: lowercase, every run of non-alphanumeric characters replaced by
one hyphen, leading and trailing hyphens removed. "An expired token is rejected" becomes
`an-expired-token-is-rejected`, used in STATUS.md, `.drive/proofs/<key>/`, handoffs, and package
briefs. Prose uses the words; paths and tools use the key.

At the spec gate, seed STATUS.md with one row per claim heading: the key, the heading words as the
claim, status Missing, and `live` fixed now: `y` when the claim crosses a network boundary, touches a
real datastore or deployed service, or concerns a device a person will hold; otherwise `n`. Prefix
`[ui]` when a person looks at the result. Lowering `live` later needs a DECISIONS.md entry in the same
commit.

Tests carry the same words. The suite or `describe` name is the heading verbatim and each test name
is a scenario title verbatim; the refuting scenario's test belongs to the severe tester and is
recorded as `severe:<path>::<name>`. Where a framework needs an identifier, use the key with
underscores (`test_an_expired_token_is_rejected`). The trace slugifies suite names and identifiers; a
suite matching no heading or `Formerly:` line is a finding, except under a `supporting/` directory. A
reworded heading keeps its old words on a line `Formerly: "<old words>"` beneath it, and its STATUS key
never changes, because proofs and tests point at it.

## 7. Decide and log

When the goal leaves something open, decide it, taking care in this order: scope, security and
privacy, user experience, technical detail. Some actions are always fine (following the project's
conventions, running its checks); some are allowed once their undo is written (schema shape, new
dependencies, configuration, deletions with evidence of zero use); some are never done (committing a
secret, weakening a failing test). Only a step with no possible undo can become the single question.
Every decision made on the owner's behalf goes in the spec's Assumptions section:

```markdown
### We assume <the decision, as a plain claim>
Because: <the one or two facts or preferences that drove it>.
Instead we could have: <the strongest alternative>.
To overturn: say "<the sentence the owner would type>". Before <milestone> this costs <cost>; after it costs <cost>, because <reason>.
Status: assumed <YYYY-MM-DD>
```

Status is `assumed <date>`, `asked, unanswered <date>`, `confirmed <date>`, or `overturned <date>, see
Changes`. Never delete an entry, because the old assumption explains code written before the change. A
build spec with fewer than eight assumptions is hiding decisions inside requirements; a requirement not
derivable from the goal, the owner's preferences, or a verified constraint is an assumption. Decisions
taken later in the run (design choices, narrowed targets, dispute rulings) go to DECISIONS.md with
their undo, and the report lists both.

## 8. The single question

`AskUserQuestion` is disallowed in drive, and subagents never ask anyone. The run asks the owner at
most one question in total, so if intake already asked, the spec phase asks nothing. A spec decision
may become that question only when all of these hold:

1. The two readings lead to different deliverables, and building on the wrong one would destroy work
   or waste more than an hour that cannot be redirected.
2. No undo is possible short of discarding the work built on it: one user or many, a data model that
   will hold user data, a public API, money, legal or privacy posture, product identity.
3. No default is defensible from the goal, the owner's files, the repository, or the research, and
   the decision is not owned by design or settled by an industry default.

Ask after the spec review, with the spec already drafted around the default, as plain text at the end
of a turn that has delivered every piece of progress that does not depend on the answer:

```
One decision needs you: <the question in one sentence>.
Default I am taking now: <the default>. Changing it later costs <cost>.
To choose otherwise, reply "<the sentence>".
```

Set the assumption to `asked, unanswered <date>`, record the question and default on a `destructive:` Blocked on line
in STATE.md (the token names the stop condition the gated step meets), and apply the default immediately if it is reversible. Block only a step that is
irreversible, destructive, or needs credentials, payment, or legal acceptance, and keep working on the
rest. When an answer arrives, mark `confirmed` or `overturned`; if overturned, run section 14.

## 9. Constraints, omissions, and non-goals

Constraints come from three sources, kept apart: the owner, the platform, and policy or law. Each
states what it forbids or requires, never how to comply. A platform limit carries its number and unit,
URL, checked date, and research slug ("at most 100 bound parameters per query, checked <date>,
research: <slug>"). A constraint with no ledger entry is labelled "decision, not fact" and has an
assumption. Where the test environment does not enforce a production limit, say so and require a test
against the real semantics; TESTPLAN.md's kindness ledger carries the guard. These are external limits;
`.drive/CONSTRAINTS.md`, the measured quality floor, is a different file.

Leave out technology choices beyond what the owner or existing code fixes (the spec says "photos
survive reinstalling the app"; design picks the store), task lists and estimates, personas and
background, mockups and copy, competitive narrative, and any future-work section. Something worth
mentioning and not worth building now is a non-goal: a thing that could reasonably be a goal and is
deliberately not, with a reason clause ("No public profiles, because sharing one item by link covers
the stated need"). "The system should not crash" is not a non-goal.

## 10. Budgets, success criteria, and the cheat test

State non-functional requirements as numbers with the environment they are measured in: first
response or cold start, p95 on the hot paths, monthly cost at a stated usage, offline behaviour,
retention and deletion, an accessibility floor, an internationalisation posture, and what must be
visible when it breaks. Turn every vague word into a target: "faster" becomes a p95 on a named path
and device; "simple" becomes a count of steps to the main job.

Success criteria number three to seven, each measurable by an agent, containing a number or count, and
naming the requirements it evidences. "It feels polished" is not a criterion; "a new account reaches
its first result in under ninety seconds, measured in the simulator by the UI reviewer" is. Then try to
cheat: for each criterion and requirement, describe an implementation that passes every scenario and
still fails the user. If you find one in under a minute, tighten the scenario or add a refuting one.
This is a drafting technique for better scenarios, not a completion check: the reviewer repeats the
cheat test independently (section 12), and only its result counts.

## 11. Conditionals by trait

| Trait or signal | The spec must add |
|---|---|
| `ui` | an accessibility floor with numbers, and a success criterion the UI reviewer can check from a capture |
| stores anything a user made | retention, deletion (verifiable by a listing that returns nothing), and export |
| `auth`, money, health | abuse cases next to each use case; the single question becomes more likely |
| `external-systems`, `data` | blocking platform research before drafting; per external system, where the test double is kinder |
| `async-scheduled` | the trigger that starts the work now, idempotency, and replay as failure behaviour |
| `api`, `public-api` | request, response, and error shapes as requirements; every exported symbol has a scenario |
| `cli` | command grammar, exit codes, and machine-readable output as requirements |
| `ai-llm` | eval set size and pass threshold, a cost ceiling, behaviour on refusal or malformed output |
| `perf` | the baseline measurement and the target, measured the same way |
| a displayed metric (dashboard, report view, analytics card) | one claim heading per metric, with the definition block below and its oracle fixture |
| existing spec or registry in the repo | its format and location; the trace also runs against existing tests |

A number on a screen is a claim that can be wrong in ways no screenshot shows, so every displayed
metric gets this block under its heading, and the severe tester's fixture is written from it before
the query is:

```markdown
### Daily active accounts counts each account once per local day
Source: <table or event, and the column counted>
Formula: <in words and as the query shape, such as count distinct account_id where kind = login>
Unit: <count, currency with scale, percent, milliseconds>
Time zone: <the zone that decides which day a row belongs to, and where it is read from>
Window: <bucket size and range, such as one day over the last 30 days>
Refresh: <how often the number updates, and what the screen shows while it is stale>
Empty: <what a bucket with no rows shows: zero, a gap, or n/a>
Partial: <how the current, incomplete bucket is marked>
Oracle fixture: <fixture path> · expected <the values, computed by hand or by an independent query>
```

The refuting scenarios come from the definition: a row at 23:30 UTC for an account in a non-UTC
zone, a zero denominator, an average of averages, late rows in the current bucket.

## 12. The spec review

A fresh agent that did not write the spec reviews it. At S and M, spawn a new `drive:architect`, never
the authoring instance. At L and XL, spawn `drive:auditor` for every shape. HUNT.md gets no spec review (the verifier checks it at `verify`); you check the report
brief at the research gate. Give the reviewer the spec path, the goal verbatim, the owner's preference
files, the research ledger, the template, and this file, never the author's summary or reasoning. Tell
it to report every finding with severity and confidence; you filter afterwards. Never tell a reviewer
to be conservative or to report only important issues.

| Check | Finding when |
|---|---|
| Structure | a heading is not a falsifiable claim; a requirement with fewer than two scenarios; an invariant with no guard; no refuting scenario; duplicate headings or scenario titles; an assumption missing a line; a non-goal without a reason; a platform limit without a URL; a numbered identifier anywhere |
| Completeness | a noun or verb in the goal maps to no requirement and no non-goal; a job has no requirement; an external dependency has no failure behaviour |
| Testability | a Then cannot be observed by an agent; a success criterion has no number |
| Refutation | a refuting scenario would pass against a plausible wrong implementation (the reviewer names it) |
| Contradictions | requirements against non-goals, constraints, assumptions; criteria against the budget |
| Hidden scope | "also", "etc.", "any", "all", "and more"; a requirement that implies an unstated system |
| Failure semantics | offline, partial failure, retry and idempotency, data loss, denial, quota, first-run empty states |
| Non-functional coverage | performance, cost, privacy and retention, security, offline, accessibility, internationalisation, observability |
| Cheat test | an implementation passes every scenario and still fails the user |
| Owner conformance | an approval queue or human review step in any flow; a scheduler where a trigger exists; codes or jargon in prose |
| Kinder doubles | an external system with no statement of where its test stand-in is kinder and no real-semantics test |
| Assumption honesty | an assumption stated as a requirement; an implausible reversal cost; one so costly it should have been the question |

Every round, a scoped re-check included, writes `.drive/reviews/<YYYY-MM-DD>-spec-review-r<n>.md` from
`templates/review.md`, opening with `verdict: ready` or `verdict: not ready` and `round: <n>/<bound>`,
and adds this table after its findings:

```markdown
## Cheat attempts
| requirement | implementation that passes and fails the user | caught by |
```

Reconcile each finding in order, stopping at the first that fits: the template or rubric was unclear
(fix the wording); the finding is valid (change the spec); it is valid but costs more to fix than to
accept (record it in Risks with the reason); it is wrong given context the reviewer lacked (add that
context to the spec). A dispute over a blocking finding goes once to `drive:auditor` with
`.drive/reviews/<date>-dispute-<key>.md`; it rules `defect`, `not_a_defect`, or `rubric_ambiguous`,
and you write the DECISIONS.md entry from the ruling. When the auditor was the reviewer, you decide
and log it with its reversal cost.

Rounds follow size, as `references/verification.md` section 6 sets them, and every round and re-check writes `.drive/reviews/<date>-spec-review-r<n>.md` from `templates/review.md`. At S and M the spec gets one
full round and at most one scoped re-check, and at S that round is the combined review of spec, design,
and test plan. The re-check is a fresh instance of the same agent type given the previous round's file,
the spec's diff since that round, and the sections each blocking finding names; it answers each of those
findings `closed` or `open` with evidence and raises a new blocking finding only where the revision
introduced it. At L and XL `drive:auditor` runs up to three full rounds, each a fresh instance given the
diff since the previous round and that round's file. Afterwards, unresolved `should_fix` and `note`
findings go into Risks in the reviewer's words. A finding still `blocking` at the bound becomes a
proposed decision record holding both positions, logged with its reversal cost, a Risks entry, and a
line in STATE.md's Open failures, and the work proceeds on the reviewer's position; if it passes every
test in section 8, it becomes the single question instead. Never run a round past the bound; needing
one means the goal was ambiguous, which is what the question is for.

## 13. The spec gate

The gate passes when all of these hold; commit them together with a message naming the phase and the
claim count:

1. `drive.py lint --gate spec` exits 0, run from the skill directory as SKILL.md writes it.
2. The latest review file opens with `verdict: ready`, or the last round its size allows closed under
   section 12's rules.
3. STATUS.md has exactly one row per claim heading (requirements and invariants), keyed by its slug,
   at Missing, with `live` set and `[ui]` marked.
4. Guidance comments from the template are gone, the version line is filled, and Changes exists.
5. Any question asked is recorded in STATE.md and its assumption carries `asked, unanswered`.

Then tell the owner one line: the spec phase passed, how many claims it names, and the review path.

## 14. Changing the spec mid-run

When a maker, verifier, or experiment shows the spec is wrong, incomplete, or contradicted by the real
system, never code around it and never quietly edit the spec to match the code. Makers report it under
`concerns`; you decide.

1. Record the discovery and its evidence path in STATE.md, and run the re-classification check.
2. Edit one or two requirements yourself; brief `drive:architect` for more. A reworded heading gets its
   `Formerly:` line.
3. Append to Changes: `- <YYYY-MM-DD> · <heading words affected> · <what changed and why> ·
   invalidates: <keys demoted, tests to re-run> · decision: <DECISIONS.md entry or none>`.
4. In STATUS.md, every row whose requirement text changed and whose status is above Partial drops to
   Partial, with its claim words and date updated and its evidence tokens kept; the next verdict is a
   new round under `.drive/proofs/<key>/`. A removed requirement's row becomes Dropped with `why:`.
   Rows are never deleted.
5. Narrowing a target (Dropped, `live` from y to n, a loosened criterion) needs a DECISIONS.md entry in
   the same commit. A frozen rubric under `.drive/rubrics/` changes only between units, logged in
   DECISIONS.md. A test assertion is never widened except through this protocol.
6. Have a fresh reviewer of the original type review the diff and the Changes entry, one round.
7. Commit the spec, STATUS.md, and DECISIONS.md together as `spec: change <heading words>`.

No row climbs again until its tests re-ran against the changed text and a verifier confirmed it. The
final audit compares Changes dates with verdict dates; a verdict older than the text it certifies is a
mirage.

## 15. Excuses and rebuttals

| Excuse | Why it fails |
|---|---|
| "The goal is clear; a spec is ceremony." | The verifier needs a fixed point other than the maker's summary, and the tests need something to be written from. |
| "Asking is safer than guessing." | The owner is not watching; a blocked question blocks the run. Decide, log the reversal cost, keep going. |
| "This requirement is obvious; it needs no refuting scenario." | Obvious claims are the ones a wrong implementation passes unnoticed. |
| "We'll pick the numbers later." | A budget chosen after the build is chosen to match the build. |
| "The limit is well known; no URL needed." | Remembered limits are where stale knowledge certifies broken code. |
| "Naming the stack in the spec saves design a step." | Every design improvement then becomes a spec change, reviewed with the wrong rubric. |
| "Competitors all have it, so it's a requirement." | Research enters as non-goals and table stakes; the budget is fixed, so every addition displaces something. |
| "The code is right, so update the spec to match." | That erases the record of what was asked; run section 14 so the change is visible and the rows re-verify. |
| "The reviewer only found nitpicks; no need to reconcile them." | Findings are filtered by reconciliation, not by skipping the step. |
| "The review keeps finding things; one more round." | The bound is one round and a scoped re-check at S and M, and three rounds at L and XL; what remains goes to Risks or becomes the question. |

## 16. Red flags

- A build spec with fewer than eight assumptions, or an assumption with no reversal cost.
- A refuting scenario that restates the happy path, or a requirement with none.
- A numbered identifier, "TBD", "etc.", or "and more" anywhere in the spec.
- A success criterion or budget with no number.
- A question raised whose answer sits in CLAUDE.md, the repository, or the research ledger.
- A technology named that neither the owner nor the existing code fixed.
- A review with no findings table and no cheat attempts, or a verdict of "looks good".
- A third review round, or a second question to the owner.
- A spec change with no Changes entry, or a row above Partial whose requirement text is newer than its
  verdict.
- A STATUS row whose claim words differ from its heading with no `Formerly:` line.
