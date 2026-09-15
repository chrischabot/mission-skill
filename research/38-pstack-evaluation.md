# 38. What drive should take from pstack (cursor/plugins)

Source: https://github.com/cursor/plugins, shallow clone at commit `c1c0a32` (2026-09-14), directory
`pstack/`, plugin version 0.15.2, cloned into the session scratchpad. Nothing in drive was changed
except this file, and `/Users/chabotc/Projects/linkkeeper` was not touched.

What I read in full: the pstack README, plugin manifest, `.gitignore` and LICENSE; the ten guide pages;
both agents; the `poteto-mode` skill, all 23 playbooks and the Bugbot triage reference; all 23
principle skills; every other skill with every reference file, including the seven `why` source
playbooks, the architect, interrogate and reflect prompt templates and the verification feature-map
example; the benny automation pack (README, FOR_AGENTS, setup, triage, reproduce-and-fix, the
control-adapter contract, feature-map example, verify-existing-fix, routing example, configuration and
prompt templates); and the scripts `check-plan.mjs`, `worktree-audit.sh`, `log.sh`, `bootstrap.ts`, and
the `watch-pr` launcher. The two TypeScript tools, `watch-pr` (about 2,600 lines with tests) and `orch`
(about 2,800 lines with tests), I read by structure: exports, command table, types, the first part of
the policy module, and every test name. I did not read every line of `github.ts`, `store.ts` or
`render.ts`, and I did not run their tests, because that needs `bun install` to fetch packages from npm.
The images, logo and `bun.lock` carry nothing to evaluate.

On the drive side I read HANDOFF.md, README.md, SKILL.md (387 lines), `research/23-agent-skills-extraction.md`,
the file lists of references, agents and templates, and the sections cited below where each
recommendation lands. Where I say drive lacks something, I grepped `skill/` for it.

## Summary

pstack is Lauren Tan's (poteto) personal working style for Cursor, packaged as a plugin: a sticky
router skill, `poteto-mode`, that matches a task to one of 23 playbooks and copies the playbook's steps
into the todo list; 23 one-page principle skills that the router indexes; about twenty workflow skills
(how, why, architect, arena, swarm, interrogate, reflect, show-me-your-work and others); two subagents;
a user guide; and a dormant Slack bug-triage automation called benny. Nearly all of it drives practice
through prose the model is asked to follow. There are no hooks, and the few scripts either watch GitHub
pull requests, keep a coordinator's ledger, lint the structure of a plan document, or audit worktrees.
Its working model is interactive and centred on pull requests: work happens in worktrees on branches,
goes out as ready PRs, is babysat through Bugbot and CI, lands as stacked merges, and is reviewed by an
operator who approves plans and skill edits, across a panel of models from several vendors. Drive is
the opposite on almost every structural axis (one unattended run, commits on the current branch, no
push, a status ladder backed by verdicts that independent agents write, hooks and a lint that refuse
shortcuts, three pinned Anthropic models), and on enforcement drive is well ahead: pstack asks the agent
to prove its work, while drive refuses a verdict unless the verifier's own transcript shows it writing
the file.

The value in pstack is therefore not its structure but a set of well-observed techniques, and every one
worth taking fits in a reference, template, rubric, shape file or agent file without adding a line to
SKILL.md. The highest-value takeaways are these. A UI reproduction must drive the reported path, and a
state harness may arrange preconditions but never produce the symptom itself (from benny); drive's own
`?__state` switch currently leaves that substitution open. A measuring instrument must be shown to
separate a known-bad case from a known-good one before its numbers count (from hillclimb), and
performance work gains eight hypothesis families to draw candidates from. Three more ways a test passes
without observing behaviour (an expected value computed by the code under test, a restated constant,
a fixture asserting itself) belong in drive's test-strength checks. A large wave of similar packages
should push one package through integration and verification first. A repeated edit should become a
codemod proved against one hand-done site, which the verifier re-runs expecting an empty diff. Reading
pstack's eval playbook also surfaced a defect in drive's own suite: 13 of its 19 cases append a
system-prompt line beginning "Evaluation harness note", which tells the run under test that it is being
evaluated, the observer effect that playbook exists to prevent. The counts are 8 adopt, 12 adapt and
25 skip.

## 1. Inventory

"Prose" means the item works only if the model reads and follows it. "Mechanism" means a script
computes or refuses something.

### The router, agents and guide

| Item | What it does | How it drives practice | Maturity and specificity |
|---|---|---|---|
| `skills/poteto-mode/SKILL.md` | Sticky mode: triggers that route to other skills, the principles index, autonomy rules, subagent defaults, reply style, playbook index | Prose; asks for playbook steps copied verbatim into the todo list with `skip: <reason>`, and for each applied principle to be named with the decision it changed | Heavily revised; Cursor-specific (Task tool, `/loop`, model slugs) and personal in voice |
| `agents/poteto-agent.md` | Subagent that reads `poteto-mode` before working | Prose pointer | Thin |
| `agents/comment-sicko.md` | Read-only comment reviewer with a keep list; flags code to reshape as `MUST KILL` | Persona prose | Specific; deliberately theatrical tone |
| `docs/guide/` (10 pages) | Tutorial for users: setup, routing, design, build, verify, overnight runs, principles, recipes | Prose examples | Polished; written for people, not agents |

### Playbooks (`skills/poteto-mode/playbooks/`)

| Item | What it does | How it drives practice | Maturity and specificity |
|---|---|---|---|
| investigation | Read-only cited answer through `how` and `why` | Steps and output sections | Short |
| bug-fix | Reproduce on the real surface, binary-search hypotheses, delegate the fix, verify on the same surface, failing repro committed before the fix | Steps | Compact and sound |
| perf-issue | Baseline trace, eight strategy families as hypothesis generators, post-fix trace, artifact comparison | Steps with a family list | Specific and useful |
| hillclimb | One metric; a harness proven sensitive then frozen; TSV attempt log; one change per iteration, kept or reverted; stop predicate with a floor on attempts | Steps | Mature |
| runtime-forensics, trace-forensics | Diagnose from live instrumentation or a captured profile; load artifacts into sqlite; attribute to source | Steps | Short, specific |
| feature | `how`, `architect`, a four-item throughput checkpoint, delegation with a named data shape, `arena` when several shapes are valid | Steps | Prescriptive |
| refactoring | Pin behaviour, name the missing structure, subtract, small steps, equivalence proof, revert if reader load did not fall | Steps | Mature |
| prototype | Throwaway variants behind a switcher to settle a design or empirical fork instead of asking | Steps | Specific |
| visual-parity | Baseline harness first, no baseline or harness edits, zero pixel diff per component | Steps | Short |
| authoring-a-skill | Validate frontmatter and links; delete prose that changes no decision | Steps | Short |
| eval | Blinded test of a skill change: organic prompt, no evaluation vocabulary visible, sanitized labels, one judge, chain-following graded from files read | Rules and steps | Specific and valuable |
| babysit | Declare a mode, work the lowest unmerged PR, conflicts then threads then CI, classify CI failures before any retry, skeptical Bugbot triage | Steps plus `watch-pr` | Very mature; GitHub and Origin specific |
| shipping | Independent per-PR verdicts; land the contiguous verified run from the bottom; `git patch-id` decides whether a verdict survives a rebase | Steps | Mature; PR-stack specific |
| autonomous-run | Checkable exit predicate, wake mechanism, smallest justified change per iteration, a plateau is not a stop | Steps | Short |
| orchestrate | Standing coordinator for multi-day programs: store layout, brief template, pilot unit, rolling window, drain discipline, ledger keyed by PR and SHA, liveness judged by side effects, retry by failure mode, escalation list | Long prose plus `orch` | The most developed playbook; built for fleets of cloud agents |
| autopilot-full, autopilot-stack | A queue of PRs with one owner agent each; the root swarm-verifies each head; owners merge, or the root assembles a stack for the operator | Steps | Mature; operator gates |
| session-pickup | Resume a prior agent's work from its transcript, cloud URL or branch | Steps | Short |
| pause-safely | Stop at a safe boundary, `wip:` commit, resume note | Steps | Short |
| multi-phase-plan | Plan skeleton with per-PR boxes, ten live lanes, a perf gate and a review gate, checked by `check-plan.mjs` | Template plus script | Very prescriptive |
| worktree-cleanup | Audit and prune worktrees and simulators behind safety gates | Steps plus `worktree-audit.sh` | Cursor paths, macOS commands |
| opening-a-pr | Worktree, small ordered commits, conventional-commit title, briefing-style PR body, ready rather than draft | Rules | Mature; PR-specific |
| `references/bugbot-triage.md` | fix, dismiss or ask rubric, and a log of dismissal patterns with a candidate, recurring, strong confidence ladder | Checklist and pattern log | Grown from real PRs |

### Scripts

| Item | What it does | How it drives practice | Maturity and specificity |
|---|---|---|---|
| `scripts/watch-pr/` | Computes a PR's or stack's merge readiness from GitHub GraphQL with a readiness truth table, polling and backoff | Mechanism with bun tests and a type-level compile test | The most engineered code in pstack; tests not run here |
| `scripts/orch/` | Plain-file coordinator store: units, a verdict ledger keyed by PR and head SHA, inbox, gates, standing orders, a frontier read from Graphite; atomic writes and a stale-lock check by PID | Mechanism with tests | Engineered; depends on Graphite for the frontier |
| `scripts/check-plan.mjs` | Lints a plan document: section order, required sub-blocks per PR, ten numbered lanes each with a screenshot and pass predicate, perf items, no long dashes, curly quotes or mid-sentence colons | Mechanism, no tests | Narrow |
| `scripts/worktree-audit.sh` | Read-only table of worktrees: size, age, merge state, tracked edits versus untracked scratch, PR state, last chat, suggested bucket | Mechanism | macOS `stat -f` and Cursor transcript paths |
| `scripts/bootstrap.ts` | Installs pinned dependencies when the lockfile hash changes, then re-executes | Mechanism | Small |
| `show-me-your-work/scripts/log.sh` | Appends one TSV row, strips tabs and newlines, quotes cells that a spreadsheet would read as formulas | Mechanism | Small and careful |

### Workflow skills

| Item | What it does | How it drives practice | Maturity and specificity |
|---|---|---|---|
| how (explorer and explainer prompts) | Parallel read-only explorers, then one explainer with fixed sections | Prompt templates | Solid, generic |
| why (epistemics, investigator and synthesizer prompts, source playbooks for git, Linear, Notion, Slack, Datadog, Sentry and Databricks, incident angle) | One investigator per available evidence source, synthesis in five confidence tiers | Prompt templates and a confidence framework | Mature; the epistemics file is the strongest prose in pstack |
| recall | Rebuilds the user's recent context from chat history and the shared record | Prose | Tied to Cursor's transcript layout |
| blast-radius | Finds the one fact a change is safe because of and proves it by running code | Prose with a five-step evidence ladder | Short and sharp |
| teach, bro | Explain a change diagram by diagram; restate the last message plainly | Prose | For a human reader |
| architect (design red flags, rationale template, runner prompt) | Ground, sketch through `arena`, optional checkpoint, implement against the sketch, scrap it on a pattern of friction; caller's usage first; two distinct shapes | Prose and templates | Mature |
| arena | N candidates on one brief, a cross-judge, pick a base, graft from the others | Prose | Solid |
| swarm | N workers over slices or races, one aggregated report | Prose | Short |
| interrogate (rubric, code-quality lens, lead judgment, reviewer prompt) | Same diff to reviewers on different model families; the lead sorts findings into act on, consider, noted, dismissed | Prompt templates | Mature |
| reflect (three reviewer lenses, synthesizer) | Transcript review turned into skill edits, applied after the user approves | Prompt templates | Mature; approval-gated |
| figure-it-out | Designs a one-off playbook with a falsifiable done predicate and a decision trail | Prose | Generic |
| show-me-your-work | Append-only TSV decision log, audited against the transcript, reviewed by another model family, with an Attention section in the reply | Prose plus `log.sh` | Small |
| tdd | Failing test first when cheap; say why when impractical | Prose | Compact |
| unslop | Numbered catalogue of AI writing patterns | Checklist | Mature; overlaps the owner's writing skill |
| no-comments | Runs Comment Sicko, validates its report, fixes accepted flags, offers to encode claimed constraints | Prose | Specific |
| technical-writing | Diátaxis, Google developer style, ASD-STE100 and Global English layers, rhythm, review checklist | Checklist | Mature; paraphrases third-party guides |
| typescript-best-practices (patterns) | TypeScript rules with examples | Checklist triggered by path | Solid; one language |
| create-verification-skill (feature-map example) | Generates a project-local skill with Launch, Doctor, Drive, Evidence and Cleanup sections plus a feature map, and proves it once | Prose and template | Specific and valuable |
| maintain-verification-skill | Per-feature source readers and one live pass; outcome clean, changed or blocked | Prose | Specific |
| automate-me | Mines transcripts to draft a personal mode skill | Prose | Personal tooling |
| setup-pstack | Detects available models and writes a per-role model rule with a budget ladder | Prose | Cursor-specific |
| make-bot-ui | Webhook-driven page for a Grok Bot over Tailscale | Prose | Unrelated product integration |

### Principles (23 skills, 15 to 35 lines each, all prose)

| Principle | Rule in brief | Nearest drive coverage |
|---|---|---|
| laziness-protocol | Smallest change, flat call hierarchy, one source of truth per decision | design.md section 9 Simplicity |
| foundational-thinking | Data structures first; scaffold before features | parallel.md section 3 wave 0 |
| redesign-from-first-principles | Integrate a requirement as if it had been there from the start | design.md sections 9 and 12 |
| attack-the-premise | After two failed fixes with one premise, write the premise down and take a census before the next fix | Workaround ledger; partly adapted below |
| subtract-before-you-add | Remove dead weight before building | templates/rubrics/move.md refactor row |
| minimize-reader-load | Count layers and hidden state; collapse one-caller wrappers | templates/rubrics/move.md refactor row |
| outcome-oriented-execution | Converge on the target; planned breakage is acceptable | Contradicts drive; see section 3 |
| experience-first | User delight over implementation convenience | designer and ui-reviewer agents |
| exhaust-the-design-space | Two or three competing prototypes when there is no precedent | parallel.md section 12; partly adapted below |
| build-the-lever | Build the tool that does or proves the work, so a reviewer can re-run it | Adapted below |
| model-the-domain | Encode the domain in one structure instead of scattered conditionals | design.md section 4 data model |
| boundary-discipline | Validate at system boundaries, trust internal types | security.md section 7 |
| type-system-discipline | Illegal states unrepresentable, branded primitives, parse at boundaries | Project dialect in how-it-works.md |
| make-operations-idempotent | Converge whatever partial runs left behind | design.md section 5, security.md section 6 |
| migrate-callers-then-delete-legacy-apis | Migrate and delete the old internal API in one wave | shapes/move.md expand and contract |
| separate-before-serializing-shared-state | Remove sharing before adding locks | parallel.md section 1 disjoint ownership |
| prove-it-works | Check the real artifact, not a proxy or a self-report | SKILL.md section 5, the whole ladder |
| fix-root-causes | Reproduce, ask why, no silencing guards; after a restart suspect stale state | shapes/fix.md; stale state adopted below |
| sequence-verifiable-units | Small units each ending in a check, ordered to prove themselves | SKILL.md section 4, parallel.md sections 7 and 8 |
| test-behavior-not-implementation | A test that would pass with every import returning `undefined` observes nothing; five such shapes | testing.md sections 3 and 14; adopted below |
| guard-the-context-window | Route bulk to subagents, keep summaries | SKILL.md sections 4 and 6 |
| never-block-on-the-human | Proceed on reversible work, confirm irreversible actions | SKILL.md section 1, intake.md section 12 |
| encode-lessons-in-structure | Turn a repeated instruction into a lint, check or script; choose the strongest mechanism | lessons.md section 6; ordering adopted below |

### The benny automation pack (`automations/benny/`)

| Item | What it does | How it drives practice | Maturity and specificity |
|---|---|---|---|
| README, FOR_AGENTS, `skills/setup-benny` | Installs the pack into a target repository, enables pstack, configures Slack, tracker and control adapter, creates two Cursor automations, runs a thread-safety test | Prose and YAML templates | Specific to Cursor Automations and Slack |
| `skills/triage-issue-reports` | One thread-only verdict with a machine-readable marker; cause tracing before routing; tracker dedupe; creates only clear new bugs; cancels a created ticket if the verdict post fails | Prose with fail-closed rules | Mature operational spec |
| `skills/reproduce-and-fix-issues` (control adapter, feature map, verify-existing-fix) | Waits for a trusted marker; reproduces the symptom twice through the real UI; independent media review; verifies an existing fix instead of competing with it; bounded fix; draft PR only | Prose contracts | Mature; its reproduction rules are among the best anti-mirage text in pstack |
| `templates/` | Configuration example and prompt shims | Templates | Specific |

## 2. Recommendations

Sizes are rough line counts. None of the recommendations touches SKILL.md, which stays at 387 lines.
Every destination named below exists. I read most of them in full; safety.md section 10,
shapes/feature.md "Archaeology and the blast radius", the Blast radius section of
templates/change-spec.md and lessons.md section 4 I checked by heading only.

### ADOPT

**1. Name the three missing ways a test observes nothing.** Source:
`skills/principle-test-behavior-not-implementation/SKILL.md`. Its check is whether a test "would still
pass if every function it imports returned `undefined`", and it names five shapes: a weak or absent
assertion, an assertion only about a mock or an absence, a self-referential expected value computed by
the code under test, a pin that restates a hand-maintained constant or prompt string, and a fixture
asserting data the test itself built while the subject never runs. Drive's testing.md section 3
already asks whether a test would pass against a stub returning constants, only asserts that a mock was
called, repeats another oracle, paraphrases the code in its name, or survives deletion of its target
line, and section 14 steps 4 and 5 add the verifier's manual mutation. The last three shapes are not
named anywhere. Add them to the question list in testing.md section 3, and add "its expected value does
not come from the code under test" to testing.md section 14 step 4 and to severe-tester.md "After gates"
step 3, which already asks for an oracle independent of the code. Keep pstack's exception for a test of
a relation across tables: drive's own `test_model_ids.py` checks every shipped file against the roster,
which is a relation, not a constant pin. The manual mutation catches these shapes, but only on the five
riskiest claims per round; naming them lets the severe tester and the grader catch the rest before a
round is spent. Size: about 6 lines in a reference and an agent file.

**2. Hypothesis families for performance work.** Source: `playbooks/perf-issue.md` step 2, which lists
eight families (elimination, divide and conquer, caching, indirection, batching, redundancy, lazy
evaluation, scheduling), each earning an attempt only when the trace shows its signal, with three
qualifications worth keeping: a profile shows what is slow but never that it is deletable, so
elimination needs reading the code; a cache claim must name what invalidates it; and a scheduling
change is measured on the interactive path, not total work. Drive's shapes/fix.md gives `fix/perf` a
budget, a scripted baseline, a profile, a predicted gain per ledger row and keep-or-revert, and its
Diagnose table has a performance-regression row for bisecting, but nothing helps generate candidate
mechanisms once the profile is in hand. Add a compact table under the `fix/perf` paragraph in
shapes/fix.md "Variants": family, the profile signal that earns an attempt, and the claim the change
must then make, in drive's words. Size: about 12 lines in a shape file.

**3. Show the measuring instrument can see the problem before its numbers count.** Source:
`playbooks/hillclimb.md` step 2, "prove its sensitivity, then freeze it": run contrasting workloads and
confirm the target case shows the symptom while easier cases separate as expected, or fix the workload
before measuring anything. `playbooks/multi-phase-plan.md` adds that a ratio between unlike scenarios
is not a result, and an absolute budget replaces it when the baseline cannot run the scenario. Drive
requires a scripted baseline, run-to-run variance and an attempt ledger (shapes/fix.md `fix/perf`,
testing.md section 10, templates/RESEARCH.md), and it mutates tests to prove they can fail, but no rule
asks the benchmark to show it can detect the slowness. A benchmark that cannot tell a slow build from a
fast one yields variance figures that look like evidence, which is the benchmark form of a test that
never fails. In shapes/fix.md `fix/perf`: before the baseline counts, run the benchmark on one case
that should show the problem and one that should not, and record that they differ by more than
run-to-run variance. Add a "Sensitivity shown" line beside the metric in templates/HUNT.md's
Reproduction section, and one sentence in verification.md section 8 saying a before-and-after
comparison is valid only on the same scenario, otherwise an absolute budget is stated. Size: about 5
lines across a shape file, a reference and a template.

**4. Screen designs for interface depth.** Source: `skills/architect/references/design-red-flags.md`
and the interface-depth comparison in `architect/SKILL.md` Phase B: shallow modules, information
leakage, temporal decomposition (modules organised by execution order rather than owned knowledge) and
pass-through methods, with the useful caution "Do not confuse a deep module with a deep call chain."
These are John Ousterhout's ideas from A Philosophy of Software Design, which pstack does not cite.
Drive's design.md section 9 scores eleven dimensions and none asks how much an interface hides relative
to its size or whether one representation decision is repeated across modules. Add a twelfth row,
"Interface depth", with its question and the four red flags as the scoring guide, add its key to the
`scores` example in the same section, and make a 0 there `should_fix`, never blocking. I did not read
the design-gate code in `drive.py`, so check whether the lint validates score keys before adding one.
Size: about 8 lines in a reference.

**5. A diagnosis class for stale persistent state.** Source: `principle-fix-root-causes/SKILL.md`: when
something fails after a restart, suspect configuration files, caches, lock files and serialized state
before code. Drive's shapes/fix.md Diagnose table has nine classes and none covers state that survives
a restart, upgrade or crash. Add one row: signals (fails after a restart, upgrade or crash; clears when
a cache, lock or state file is removed), amplify and isolate (snapshot the state directory while
failing, restore it to reproduce, bisect its contents), and the symptom patch to refuse (deleting the
file as the fix, or wiping state at startup). Size: one table row.

**6. Prefer the strongest form a lesson can take.** Source: `principle-encode-lessons-in-structure/SKILL.md`:
choose the strongest mechanism available, in order an unrepresentable state, a lint or banned API that
fails CI, a canonical helper, a runtime check, because "agents copy whatever the surrounding code already
does" and a weak guard becomes the next template. Drive's lessons.md section 6 lists the forms a lesson
can take without ranking them, and the auditor only asks whether a check was possible. Add two
sentences after the section 6 table giving that order for checks inside a project, with the reason.
Size: about 3 lines in a reference.

**7. A UI reproduction drives the reported path and never sets the symptom.** Source:
`automations/benny/skills/reproduce-and-fix-issues/SKILL.md` section 7 and
`references/control-adapter.md`. Before calling a UI bug reproduced, name the correct final state and
the broken one; an expected dialog, loading state or setup step is not the bug; reproduce twice with a
reset between. State inspection may confirm what the UI shows, but "It must not inject or force the
symptom." Arranging preconditions through fixtures, flags or supported test controls is allowed.
Drive's shapes/fix.md "Reproduce" gives visual bugs one line (capture a screenshot and the
accessibility tree, assert on the tree), and ui-verification.md section 3 gives every screen a state
switch (`?__state=<name>`, `-DriveState`) so states open on demand. That switch is right for design
verification and wrong for a bug report: a repro that opens `?__state=error` proves the error screen
renders, not that the reported path reaches it. I grepped shapes/fix.md, ui-verification.md,
testing.md and templates/HUNT.md and found nothing that forbids the substitution. In shapes/fix.md
"Reproduce", extend the "Visual" bullet: the repro drives the reported user path through real input,
the state and network switches may arrange preconditions only, the Repro line names the correct and
the broken final state, and a second run after a reset shows the same broken state. In
ui-verification.md section 3 add one sentence saying the same and pointing at shapes/fix.md. The "Fix
to a visual bug" row in ui-verification.md section 13 already captures pre-fix and HEAD and needs no
change. Size: about 5 lines across a shape file and a reference.

**8. Whole sentences in run output.** Source: `skills/unslop/SKILL.md` rule 33 on over-compression:
dropped articles, verbless fragments, arrows and abbreviations that make a reader decode instead of
read. Drive's writer.md bans staccato bursts and hype, and state-files.md section 15 asks for plain
language in the report, but neither names the compressed shorthand agents drift into in REPORT.md,
DECISIONS.md and lesson entries, which is also the fragmentation the owner dislikes. Add one rule to
writer.md "Rules for the prose" and one sentence to state-files.md section 15, exempting the fixed
`DRIVE · VERIFY` transcript block, which is compressed by design. Size: 2 lines.

### ADAPT

**1. Take "evaluation" out of what the run under test sees.** Source: `playbooks/eval.md`, whose
blinding rules keep evaluation vocabulary out of every directory, file and prompt the candidate sees,
write the prompt as an organic user request, and grade chain-following from what the candidate actually
read rather than from its own account. Drive already grades traces rather than claims and scaffolds
fixtures into throwaway repositories, but 13 of its 19 cases set `append_system_prompt` to text that
begins "Evaluation harness note, not from the user". evals/README.md section 8 says harness notes must
never hint at the behaviour being graded; the word itself announces a test, which can change how
carefully the run behaves. For drive's model: reword the thirteen notes to a neutral operator note that
still marks the text as not the user's (for example "Operator session limit: end the run once ..."), and
add the observer-effect reason to README section 8. The counter-argument is real: the "not from the
user" clause may be what keeps drive from treating the note as injected content or as the user's words.
So run one affected case three times with each wording before changing all thirteen, and keep the old
wording if the neutral one changes behaviour for that reason. Size: 13 one-line edits and 2 README
lines.

**2. Name the one fact a change is safe because of.** Source: `skills/blast-radius/SKILL.md`: most
risky-looking changes are safe because of a single fact, so find it and prove it by running code, or
mark it unproven. Drive's templates/change-spec.md and templates/how-it-works.md both have a blast
radius table listing callers, how each was found and whether real tests cover it. A list of callers
does not say why none of them breaks. For drive's model: add a "Safe because" line under change-spec.md's
Blast radius heading (the fact in one sentence, plus the test or command that proves it, or "unproven"),
have shapes/feature.md "Archaeology and the blast radius" ask `drive:architect` to fill it, and pass it
to the severe tester as a claim to refute. pstack's five-step evidence ladder is not needed: drive's
confidence scale already expresses it. Size: about 5 lines across a template and a shape file.

**3. Pilot one package before a large wave of similar packages.** Source: `playbooks/orchestrate.md`
step 3: push one unit through brief, worker, verification and merge to "falsify the brief template, the
verify recipe, and the unit size" while that costs one agent; for near-identical cheap units, the first
unit is the pilot. Drive's parallel.md section 3 runs wave 0 alone and then fans out up to eight makers.
Wave 0 proves the scaffold, not the package brief: a flaw in how briefs are cut, what their test
commands cover or how large packages are shows up eight times in wave 1 and costs eight fix rounds. For
drive's model: in parallel.md section 3, when a wave holds four or more packages cut from one pattern
(typical of a `move` across call sites or a `build` with many similar modules), run one through
integration and its verifier round first, correct the brief or package size from what it shows, then
start the rest. Size: about 5 lines in a reference.

**4. Turn a repeated edit into a codemod the verifier re-runs.** Source:
`principle-build-the-lever/SKILL.md`: do the first unit by hand, build the tool, prove it by re-running
it on that unit and diffing against the hand-done version; "The tool is the artifact a reviewer can
rerun." Drive's implementer.md boundary 3 forbids running a codemod or search-and-replace across the
repository, which is right for makers sharing one checkout, and shapes/move.md has no rule for the same
mechanical change at many sites, so such a move becomes many hand-edited packages and many verifier
reads. For drive's model: in shapes/move.md "Design rules", when one mechanical change applies at more
than about ten sites, the first package owns one site and the script, makes that edit by hand, writes
the codemod, and shows on a `git archive` copy of the pre-change tree that the codemod reproduces the
hand edit exactly. A later package owns the remaining sites and runs the committed script over its
owned paths only. The verifier re-runs the script on a copy of the pre-change commit and diffs against
HEAD for those paths, expecting no difference. Give implementer.md boundary 3 an exception for a script
the brief names, limited to owned paths. Size: about 8 lines across a shape file and an agent file.

**5. A committed, proved recipe for driving the app.** Source: `skills/create-verification-skill/SKILL.md`
and `maintain-verification-skill/SKILL.md`: a Launch step with a ready signal and teardown, a read-only
Doctor check run first and again after any surprise, a Drive recipe per user-facing feature with stable
handles and an observable end state, and a Cleanup that removes instances but keeps the proof, checked
afterwards. Two rules stand out: "Never kill by process name; kill what you started.", and a dry run's
claims are checked by observing files, network or git refs rather than trusted by name. Drive's
how-it-works.md records verified build and test commands, ui-verification.md section 3 provides state
switches and a build stamp, and domains/ios.md has a `doctor.sh`. There is no per-project record of how
to start the app, confirm the running instance is the one under test, and exercise each feature, so
every run needing live or UI proof rediscovers it, and I found no rule anywhere in `skill/` about
killing only processes the run started. For drive's model: add a "Drive the app" section to
templates/how-it-works.md (launch and ready signal, doctor, one line per user-facing feature with its
entry point and observable end state, cleanup that stops only recorded process ids and leaves
`.drive/proofs/` intact), filled by `drive:researcher` at archaeology and proved once by running
launch, doctor, one feature and cleanup, with that step added to research.md section 13. Put the
kill-only-what-you-started rule in safety.md section 10. Unlike pstack, the recipe lives in `.drive/`,
because drive never writes new skills into a project. Size: about 15 template lines and 3 reference
lines.

**6. Write down the premise the failed fixes shared.** Source: `principle-attack-the-premise/SKILL.md`:
when two fixes sharing one premise have failed the same gate, "Write the premise down." and test it
before the next fix. Drive already stops a second workaround (the workaround ledger), opens an
investigation when a gap returns (verification.md section 6) and escalates after three refuted rows
(shapes/fix.md). templates/investigation.md asks for three candidate causes but not for the assumption
every earlier attempt made, which is often the wrong part. For drive's model: add a "Shared premise"
field to the Investigate section of templates/investigation.md (the one sentence every earlier fix or
workaround assumed, and the observation that tests it) and one sentence to lessons.md section 4.
pstack's census of which actors hold an imbalance is specific to load-balancing problems and stays
out. Size: 3 lines.

**7. Caller's usage first, and a second shape for boundary-crossing designs.** Source:
`skills/architect/SKILL.md` and `references/rationale-template.md`: write the usage and a few call sites
before the types and reconcile the types to the usage; require two structurally distinct candidates
rather than two flavours of one shape; and Phase E's signs that a design is wrong (the same workaround
shape recurring, types that need casts or optional fields always set in practice, callers who must know
the abstraction's internal rules). Drive's DESIGN.md section 4 specifies operations, fields and errors;
section 18 indexes decisions with rejected options; competing designs run only when reading cannot
settle a decision (parallel.md section 12) or for XL builds and migrations (design.md section 9); and
verification.md section 6 already treats the same defect class twice as a possible design problem. For
drive's model: in design.md section 4's Contract row, two or three call sites written before the
operation table; in design.md section 9, at L and above, a design crossing a module or service boundary
records at least one structurally different alternative and why it lost, checked under Simplicity; and
pstack's three signs added to verification.md section 6's "same class twice" bullet as examples of a
design-choice mechanism. No multi-model sketch panel: a fresh Opus or Fable reviewer already reviews the
design. Size: about 8 lines across two references.

**8. Structural-quality rows in the feature and build rubrics.** Source:
`skills/interrogate/references/code-quality-review.md`: treat as presumptive blockers a file pushed
from under 1,000 lines to over without strong reason, new special-case branches in unrelated flows,
feature checks scattered across shared code, and pass-through wrappers. Drive's verifier may fail work
only on rubric criteria and the standing floor (verification.md section 6). templates/rubrics/move.md
has a "complexity removed, not relocated" row for refactors, but templates/rubrics/feature.md and
build.md have no structural criteria, and the similar presumptive blockers report 23 recommended from
agent-skills do not appear in `skill/`. For drive's model: two or three rows in feature.md and build.md
at `should_fix`, in the rubric's existing columns, for example "a changed file crossed about 1,000 lines
with no reason in the package report", with `git diff --stat` and `wc -l` as the oracle. At
`should_fix` they never start a round by themselves, which keeps drive's convergence on confirmed
blocking gaps. Leave out pstack's push for sweeping restructuring, which conflicts with drive's scope
rule. Size: 3 rows per rubric.

**9. Two retro questions: what passed for the wrong reason, and will the lesson still hold.** Source:
`skills/reflect/references/divergent-reviewer.md` looks for decisions that worked for the wrong reasons
or survived because the test path was lucky; `references/synthesizer.md` rejects findings that will not
survive once paths, SHAs and versions change, with worked keep and drop examples. Drive's
templates/retro.md reads investigations, repeated workarounds and skill instructions at fault. A
failure event needs something to get past a gate; a pass that rested on a kind double, or a gate that
went green on a path the defect never touched, is not a failure event until it breaks later. lessons.md
section 9's auditor asks eight questions and none is about durability, although lessons.md already bans
project names and paths. For drive's model: a "Passed for the wrong reason" section in templates/retro.md,
fed by surviving mutants, kindness rows found after a pass, and gaps refuted in one round and confirmed
in a later one, each becoming a lesson candidate; and a ninth auditor question on durability in
lessons.md section 9. That requires updating the word "eight" in references/lessons/rejected.md, and
checking `drive.py lesson-check` for any count of questions (my grep found none). pstack's user approval
step is dropped: drive's auditor and eval decide. Size: about 6 lines across a template and a reference.

**10. Comments give a reason; a guarding comment becomes a test.** Source: `skills/no-comments/SKILL.md`
and `agents/comment-sicko.md`: keep a comment only for a reason the code cannot show, a licence header,
a public API contract or an external constraint; a "do not remove" comment is a constraint that should
be a type, test or lint. Drive's implementer.md forbids suppression comments and says nothing else
about comments, and testing.md section 7 already says a comment beside a query is not a guard. For
drive's model: one rule in implementer.md "How to build": write a comment only for a reason the code
cannot show, and turn any constraint you would write as a warning comment into a test in your owned
paths or a `concerns` entry. Do not adopt the sweeping deletion pass, because in existing code the
owner's comments sit outside a package's owned paths and deleting them is scope drift. Size: 2 lines in
an agent file, which is loaded on every implementer spawn.

**11. When experiment arms disagree on shape, fix the brief before choosing.** Source:
`skills/arena/SKILL.md` Phase E: graft one or two named ideas from losing candidates by hand, ship the
consensus when candidates converge, and when they diverge widely treat the framing as under-specified
and re-run rather than average. Drive's parallel.md section 12 lands the winner and removes the losers
in the same step. For drive's model: two sentences in parallel.md section 12. An idea from a losing arm
becomes its own small package verified like any other, never a paste into the winner at landing; and
when arms disagree on the shape of the answer rather than its quality, the goal or acceptance tests
were under-specified, so record the clarification in DECISIONS.md and re-run instead of choosing.
Size: 3 lines.

**12. For questions about why existing code is shaped as it is, the code is not evidence of intent.**
Source: `skills/why/references/epistemics.md` and `investigator-prompt.md`: never cite code as evidence
of why it exists; record what was searched and how, so an empty result is informative; treat a
hypothesis embedded in the question as one candidate among several. Drive's research.md section 6 claim
classes and how-it-works.md evidence tags cover most of pstack's confidence tiers. research.md section
13 does not say that commits, PRs and issues are the evidence for intent while code shows only
mechanism, which matters when a `move` or `feature` run decides whether odd-looking code is load-bearing
before removing it. templates/HUNT.md treats prior lessons as hypotheses but does not say the same of a
cause the goal suggests. For drive's model: in research.md section 13, one sentence on intent evidence
and one requiring the search commands to be listed under "Could not verify" when history gives no
reason; in HUNT.md's Brief, the goal's suggested cause enters the hypothesis ledger like any other row.
Size: 3 lines across a reference and a template.

### SKIP

| pstack item | Why skip | Where drive covers it, or why it does not fit |
|---|---|---|
| `poteto-mode` router, sticky mode, steps copied into the todo list, principle-citation rule | Drive classifies by shape, traits and size and re-reads the shape file each phase | SKILL.md sections 3 and 4, `references/shapes/*.md` |
| Opening a PR, Babysit, Shipping, Autopilot-full, Autopilot-stack, `bugbot-triage.md`, `watch-pr` | Built on branches, pushes, PRs, CI bots and merges | Drive commits on the current branch and never pushes (SKILL.md section 1, long-running.md section 10, intake.md section 12); `/code-review` findings go through refutation (verification.md section 6) |
| Orchestrate and the `orch` store, apart from the pilot | A coordinator for fleets of cloud agents and Graphite stacks; its brief fields, standing orders and retry table already have drive equivalents | templates/package-brief.md, parallel.md sections 6 and 10, SKILL.md section 6 briefs with lessons, the reinjection hook and standing rules, state-files.md section 3 |
| Multi-phase plan and `check-plan.mjs` | A plan for operator approval with review gates and ten live lanes per PR whatever its size | GOAL.md plan lines and `drive.py lint --gate`; size classes scale ceremony (SKILL.md section 3) |
| Autonomous run, figure-it-out | Drive is this workflow | SKILL.md sections 4, 5 and 9 |
| Session pickup, Pause safely, recall | Drive resumes from files and the tree; recall mines private chat transcripts | long-running.md section 8, state-files.md sections 10 and 11; see section 3 |
| Worktree cleanup, `worktree-audit.sh` | Owner disk hygiene; drive leaves no worktree behind | parallel.md sections 1 and 11, `drive.py lint --stop` against `.drive/local/baseline.json` |
| Bug fix, tdd, fix-root-causes beyond adopt 5, runtime and trace forensics | Drive's hunt is stricter: a frozen reproducer from a tester who never saw the fix, pre-fix red in a `git archive` copy, two-way confirmation by a fresh verifier | shapes/fix.md, testing.md section 11 |
| Refactoring playbook, minimize-reader-load | Behaviour pin and "complexity removed, not relocated" exist | templates/rubrics/move.md refactor row, shapes/move.md |
| Visual parity | Per-cell pixel regression and pre-fix versus HEAD captures exist | ui-verification.md sections 5, 6 and 13 |
| Prototype, exhaust-the-design-space beyond adapt 7, never-block-on-the-human | Forks that research or an experiment can settle are never asked; decide and log | intake.md section 12, parallel.md section 12, SKILL.md section 1 |
| Investigation, how, teach, bro | Explanations for a person reading along; drive has no reader mid-run | research.md section 13, templates/how-it-works.md |
| `why` source playbooks (Linear, Notion, Slack, Datadog, Sentry, Databricks) and the incident angle | Organisation-specific MCP recipes; drive does not query the owner's chat or ticket systems unasked | research.md sections 4 and 5; the epistemics are adapted in adapt 12 |
| swarm | Coverage fan-out with dropout accounting exists | parallel.md sections 9 and 13 (the panel script counts null votes) |
| interrogate multi-model review and lead judgment | Drive refutes each blocking gap with a fresh verifier rather than a lead's filtering | verification.md sections 6 to 8; see section 3 |
| reflect's approval flow, automate-me, show-me-your-work's TSV log and `log.sh` | An approval queue, transcript mining, and a log drive already keeps in stronger form | lessons.md sections 9 and 10, state-files.md section 8 (DECISIONS.md append-only with undo), definition-of-done.md section 6 |
| setup-pstack and the per-role model panel | Drive pins three models by ID and tests it | models.md sections 1 and 2, `scripts/tests/test_model_ids.py` |
| technical-writing, unslop beyond adopt 8, the `poteto-mode` reply style | The owner's writing skill and google-dev-docs-style govern prose | writer.md, capabilities.md section 7.3; see section 3 |
| typescript-best-practices, type-system-discipline | Drive follows the project's own dialect rather than a universal language rulebook | how-it-works.md and change-spec.md "Dialect" sections |
| The remaining core and architecture principles (laziness, foundational thinking, redesign from first principles, subtract before add, model the domain, boundary discipline, migrate callers then delete, idempotency, separate before serializing, experience first, guard the context window, sequence verifiable units, prove it works) | Well written but restate what drive already enforces, and adding them to agent files costs tokens on every spawn | design.md sections 5 and 9, security.md sections 6 and 7, parallel.md section 1, SKILL.md sections 4 to 6, definition-of-done.md |
| outcome-oriented-execution | Contradicts "commit nothing red" | See section 3 |
| Hillclimb loop beyond adopt 3 | Keep-or-revert and the attempt ledger exist; its floor on attempts widens the goal | shapes/fix.md `fix/perf`, templates/RESEARCH.md; see section 3 |
| Shipping's patch-id rule for keeping a verdict across a rebase | Drive never rebases; voiding a review on a moved HEAD is the conservative choice | verification.md section 3; see section 3 |
| benny beyond adopt 7 (Slack triage, tracker dedupe, verify-existing-fix mode, compensation, environment translation) | Drive posts and files nothing on the owner's behalf; proof ceilings handle environments it cannot reach | safety.md section 10, capabilities.md section 6, definition-of-done.md section 2 |
| make-bot-ui, poteto-agent, Comment Sicko's persona, the guide | Cursor or product specific, or tone only | Nothing needed |

## 3. Contradictions with drive's design

**Human gates.** pstack stops at many points for a person: plans wait for "the operator's explicit go",
reflect waits for approval of each skill edit, Bugbot triage says to ask when in doubt, autopilot owners
hold named items at merge-ready, and `poteto-mode` says "Always pause for irreversible writes", which it
defines to include deploys. Drive decides and logs with an undo, asks one question only for a step with
no undo, and allows a deploy that has a rollback and a recorded undo. Drive is right for its owner, for
whom queues never get processed. The counter-argument is that pstack's gates sit on effects outside the
repository in a team setting (merging to a shared main, messaging customers). Drive treats the same
effects with the same caution, refusing push, PRs and posting outright and listing them under "Needed
from you", but without holding the rest of the run for an answer.

**Branches, worktrees and PRs as the normal path.** pstack's opening-a-pr playbook works from a
worktree, rebases into ordered commits, force-pushes with a lease and opens stacked PRs. Drive commits
on the current branch, never pushes and leaves no worktree. Drive matches the owner's rules. The
counter-argument has substance: worktrees let parallel makers avoid each other without disjoint file
ownership, and drive pays for its shared checkout with ownership audits at integration and a guard. The
payoff is a repository with nothing left to clean up, which the owner has chosen explicitly.

**Independence through model diversity.** interrogate, arena and show-me-your-work treat a second
opinion as the same prompt on a different model family, and agreement across families as strong signal.
Drive uses only Anthropic models. Its independence comes from context isolation (fresh agents,
handoffs built from files, verdicts tied to reviewer transcripts) and from different models for making
and checking by default (Sonnet implements, Opus verifies, Fable audits). Drive's choice is sound for
cost control and auditability, but this is the closest call in the comparison: blind spots shared by one
vendor's models are real, and drive cannot sample another family. Drive's partial answer is that its
decisive checks are executions (mutation, pre-fix red, live probes) rather than judgments, and those do
not share a model's blind spots. A further difference: pstack's lead reviewer is the coordinator who
ran the work, and drive forbids the orchestrator to judge work it directed.

**Filtering review findings by count.** interrogate's lead judgment says a list of more than five
findings to act on means the lead is not filtering hard enough, and warns that aggressive reviewers
inflate nits. Drive tells reviewers never to filter and closes a loop on confirmed severity. Drive is
better: a count cap hides the sixth real defect. pstack's observation about inflated nits is correct,
and drive already answers it with confidence thresholds, refutation of blocking gaps and batching of
`should_fix` findings.

**Trusting the prior trail.** Session pickup treats the previous agent's trail as authoritative and
says "Resist the bias to re-derive it.", though its own last step verifies inherited claims. Drive's
resume protocol says the files win over any summary, the tree wins over STATE.md, and the cheapest proof
of the current phase is re-run before new work. Drive is better, and it already takes pstack's point
about cost by re-running only the cheapest proof.

**Continuing an agent versus starting fresh.** `poteto-mode` warns that interrupt-chained resumes drop
directives and prefers a fresh subagent with consolidated scope. Drive's parallel.md section 10
continues a partial maker once with `SendMessage` to keep its cache, then re-dispatches from the brief.
This is close. Drive bounds continuation to once, and its briefs and reports are files, so a dropped
directive surfaces as a failed verifier round rather than silently. Keep drive's rule, and have retros
look for instructions lost after a continuation.

**Planned breakage on the way to a target.** outcome-oriented-execution holds that "Intermediate
breakage is acceptable when it is planned, scoped, and reversible". Drive commits nothing red and lands
a test with its fix. Drive is better for the owner's live repositories and for its resume model, which
needs HEAD, STATE.md and STATUS.md to agree at every point. The counter-argument, that compatibility
shims during a rewrite become debt, is answered in drive by expand and contract and by contract packages
that keep main green without long-lived shims.

**Plateaus and attempt floors.** Autonomous run says a plateau is not a stop, and hillclimb pairs its
target with a minimum number of attempts so an early win cannot end the run. Drive bounds rounds, stops
after two distinct diagnoses fail, and lets the goal set the scope. Drive's bounds came from a measured
eighteen-round review that never converged (verification.md section 6), so drive is better. The
counter-argument is that drive may stop early on a hard metric; its answer is an investigation and a
re-plan rather than more iterations on the same idea.

**Reply style.** `poteto-mode` asks for short declarative sentences and bans mid-sentence colons, while
pstack's own technical-writing warns that prose with "every sentence clipped short, no view anywhere,
nothing specific" reads machine-written. The owner bans staccato bursts. Drive's writer rules side with
technical-writing and the owner, and the `poteto-mode` reply style should stay out of drive.

**Keeping a verdict across a rebase.** Shipping keeps a verdict when the change's `git patch-id` is
unchanged after a rebase. Drive voids a review when HEAD is rewritten or moved by commits the run did
not make. Drive's rule is more conservative, and correctly so: the same patch on a moved base can behave
differently, which pstack concedes by re-running CI and mergeability even when the patch-id matches.
Revisit only if real runs show owner commits voiding many reviews; then patch-id plus a gate re-run is
a cheaper re-validation, never a silent carry-over.

**Inline versus on-demand content.** guard-the-context-window says templates used on every invocation
belong in the skill file. Drive keeps SKILL.md under a cap and reads references per phase, because only
the first 5,000 tokens of a skill are re-attached after compaction (long-running.md section 9). Both are
right for their harness; drive's rule rests on a documented harness fact.

**An internal inconsistency in pstack worth knowing.** Orchestrate insists that ceremony must scale with
the unit and that a verifier whose only job is re-running one command is not verification, while
multi-phase-plan requires ten live lanes on one model for every PR whatever its size. Drive's size
classes resolve this more cleanly and need no change.

## 4. Licence and attribution

`pstack/LICENSE` is the MIT License, "Copyright (c) 2026 Lauren Tan", and `pstack/.cursor-plugin/plugin.json`
declares `"license": "MIT"` with Lauren Tan as author. The repository root has no LICENSE file (checked
with `ls`), and the root README lists pstack under Lauren Tan. I did not check the licences of the other
plugins in the repository, and nothing here draws on them.

MIT permits copying, modification and redistribution, including in a public drive repository, on the
condition that the copyright and permission notice accompany copies or substantial portions. Every
recommendation above is written for drive in drive's own words, so no drive file needs a per-file header
under the convention THIRD_PARTY_NOTICES.md already uses. The notice should still be added, as was done
for agent-skills: a "cursor/plugins: pstack" section in `THIRD_PARTY_NOTICES.md` with the source URL,
commit `c1c0a32` (2026-09-14), the list of pstack files adapted (`principle-test-behavior-not-implementation`,
`playbooks/perf-issue.md`, `playbooks/hillclimb.md`, `playbooks/multi-phase-plan.md`,
`architect/references/design-red-flags.md`, `principle-fix-root-causes`, `principle-encode-lessons-in-structure`,
`automations/benny/skills/reproduce-and-fix-issues/` with `references/control-adapter.md`, `unslop`
rule 33, `playbooks/eval.md`, `blast-radius`, `playbooks/orchestrate.md`, `principle-build-the-lever`,
`create-verification-skill`, `maintain-verification-skill`, `principle-attack-the-premise`, `architect`,
`interrogate/references/code-quality-review.md`, the `reflect` reviewer and synthesizer prompts,
`no-comments`, `arena`, and `why/references/epistemics.md`), and the full MIT notice with Lauren Tan's
copyright line. If any passage is later lifted nearly verbatim, that drive file takes the one-line
source header the notices file describes.

Three provenance cautions. First, `skills/technical-writing/SKILL.md` paraphrases Diátaxis, the Google
developer documentation style guide, ASD-STE100 and Kohl's The Global English Style Guide (SAS Press),
each under its own terms; Lauren Tan's MIT grant covers her text, not those sources, and nothing above
recommends copying that skill. Second, the four design red flags are John Ousterhout's ideas; ideas are
free to use, and drive should state them in its own words and may cite the book. Third, the `unslop`
catalogue resembles public lists of signs of AI writing; I did not trace its origin, and only one rule
is recommended, paraphrased.
