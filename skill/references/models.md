# Model routing

Read this file at intake, before you launch any agent with a `model` parameter, when you set the
run's budget, when a verifier or grader is being chosen for a job, and when a result reports a
model you did not expect. It decides which model and effort each role runs on, which per-call
overrides you may apply, how grading is split between cheap and expensive judges, why Haiku is
never used, what a run should cost, how to keep the prompt cache warm, and how every result proves
which model produced it.

## 1. The routing principle

Route by the shape of the work, not by prestige. Work that produces many output tokens
(implementation, breadth research) runs on `sonnet`. Bounded judgment (specs, design,
verification, security, review, diagnosis) runs on `opus`. `fable` holds the orchestrator context
for the whole run and takes the few verdicts whose mistakes are the most expensive to discover
later: the final audit, dispute rulings, lesson verification, spec, design, test-plan, and plan review at L
and XL, and the re-classification review at XL phase gates. Count invocations when you judge cost: a premium paid once on a read-heavy
verdict is small in dollars, and the same premium on work repeated per package is not.

Agent files pin exact model IDs, and these are the only models drive uses: `claude-fable-5-1`
(Fable 5.1), `claude-opus-5` (Opus 5), and `claude-sonnet-5` (Sonnet 5). The launch recipes pass
`--model claude-fable-5-1`. The Agent tool's per-call `model` parameter accepts only the aliases
`fable`, `opus`, and `sonnet`; on the Anthropic API they resolve to the same three models, and every
result names the model it ran as (section 10).

Other providers differ. Google Cloud's Agent Platform and Microsoft Foundry use the same model IDs;
Amazon Bedrock prefixes them with `anthropic.`, usually behind a regional inference-profile prefix
such as `us.`. The aliases resolve per provider, and on some to older models: the Claude Code model
configuration page, read on 2026-09-14, lists `opus` as Opus 5 on Bedrock and Google Cloud but Opus
4.6 on Foundry, and `sonnet` as Sonnet 4.5 on Bedrock, Google Cloud, and Foundry and Sonnet 4.6 on
Claude Platform on AWS. An override there could run a model the roster excludes. So `drive.py
preflight` reports the provider (`ok provider: anthropic`, or a warning naming `bedrock`, `vertex`, or
`foundry` when `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`, or `CLAUDE_CODE_USE_FOUNDRY` is
set), and off the Anthropic API drive passes no per-call override at all:
the Agent call carries no `model`, the agent files decide, and the run says once in STATE.md and in
the report which provider served it, with the auditor checking every reported model against the
roster.

Prices per million tokens as of September 2026, for reasoning about trade-offs; check the pricing
page before quoting them to the owner.

| Model | Input | Output | Cache read | Cache write, 5 min / 1 h |
|---|---|---|---|---|
| Fable 5.1 (`fable`) | $10 | $50 | $0.25 | $12.50 / $20 |
| Opus 5 (`opus`) | $5 | $25 | $0.50 | $6.25 / $10 |
| Sonnet 5 (`sonnet`) | $2 | $10 | $0.20 | $2.50 / $4 |

Fable costs about twice Opus and five times Sonnet per token, while its cache reads cost half of
Opus's. A Fable context that re-reads itself is cheap per token, but at 300K to 500K tokens re-read on every
request, cache reads are still the orchestrator's largest cost; Fable writing code is expensive on
every count.

## 2. The roster

Model and effort live in each agent's frontmatter under `agents/`. The Agent tool has no effort
parameter, and a Workflow `agent()` call with `agentType` inherits the file's model and effort, so
these frontmatter lines are the source of truth. SKILL.md, section 5 of this file,
`references/verification.md` section 11, and the README repeat the values for readers; where a copy
disagrees with an agent file, the copy is wrong, and `scripts/tests/test_model_ids.py` fails on any
model ID outside the three.

| Agent | Model | Effort | Why here |
|---|---|---|---|
| orchestrator (main conversation) | `claude-fable-5-1` | high | It is the only context that lives the whole run, and decomposition, cutover decisions, and lesson distillation are the judgments Fable completes where the other tiers stop short. |
| `researcher` | `claude-sonnet-5` | high | Breadth research is output-heavy, and independent lanes matter more than depth. |
| `architect` | `claude-opus-5` | xhigh | Specs, designs, test plans, and decomposition are bounded judgment that every later role anchors on, and Opus 5's guidance is to step up from high to xhigh for demanding coding and agentic work. |
| `designer` | `claude-opus-5` | high | A design direction and its contract require inferring requirements nobody wrote down, which literal Sonnet does not do. |
| `implementer` | `claude-sonnet-5` | high | Code for one claim is the largest output sink in the run, Sonnet writes it at a fifth of Fable's price, and high effort avoids the literal narrowing Sonnet shows at low effort. |
| `writer` | `claude-opus-5` | high | Prose under the owner's name is judged on precision and register, where literal instruction-following produces flat text. |
| `verifier` | `claude-opus-5` | high | A verifier must design and run a refutation and resist talking itself into a pass, and a stronger skeptical model is markedly more tractable at that than a cheaper one. |
| `severe-tester` | `claude-opus-5` | high | Adversarial, tool-heavy testing sits close to the cyber classifier. It runs as a subagent so a flag and the material behind it stay out of the Fable orchestrator's context; Opus 5 runs a cyber classifier too, and Claude Code moves a flagged Opus 5 request to its fallback model (`safety.md` section 1). |
| `security-reviewer` | `claude-opus-5` | high | Security analysis is where the classifiers fire most often, so it runs in its own subagent, away from the orchestrator. Opus 5 is not exempt: a cyber flag there is still a fallback event (`safety.md` section 1). |
| `ui-reviewer` | `claude-opus-5` | high | Judging a live interface against a design contract takes visual and spatial judgment plus navigation, and it keeps screenshots out of the orchestrator. |
| `grader` | `claude-sonnet-5` | low | Binary assertions against evidence reward cheap, literal reading, and that same literalism is why it never grades quality. |
| `investigator` | `claude-opus-5` | xhigh | Diagnosis to a named mechanism is a long dependent chain of hypotheses, where effort pays more than parallel breadth. |
| `auditor` | `claude-fable-5-1` | xhigh | The final audit and dispute rulings are the verdicts whose errors nobody catches until a later session, and they run only a few times per run. |

The writer is the one output-heavy role on Opus, which departs from routing volume to Sonnet on
purpose. Its output is small next to implementation, people read it under the owner's name, and a
literal Sonnet draft tends to cost a rewrite round that erases the saving. When a run's prose is
volume copy rather than narrative (hundreds of near-identical pages), record a switch to `sonnet`
for that run in DECISIONS.md.

Every agent ends its final message with the model it ran as and returns a fixed-size result: a
status line, file paths, and at most 1,500 characters.

## 3. The orchestrator stays on Fable at high for the whole run

The launch recipe sets `--model claude-fable-5-1 --effort high` (see `long-running.md`). SKILL.md sets no
model, because a skill's model override lasts one turn and each switch rebuilds the whole cache.
At intake, record in STATE.md `model:` the model named in your system prompt and the effort you
were launched with; if it is not Fable, say so in one line and continue.

Hold model and effort constant until the run ends. A model change discards the largest prompt
cache in the run and changes the quality of every later decision. Do not run `/model`, do not
invoke skills that carry a different model, and keep attack material out of your context so a
safety classifier never switches you (`safety.md`). If a switch happens anyway, record it as a
Boundary event, continue, and let the next resume relaunch with `--model claude-fable-5-1`.

## 4. Per-call overrides

These are the only `model` values you may pass on an Agent call. Nothing else in a run names a
model.

| Agent | Override | When |
|---|---|---|
| `implementer` | `opus` | The architect marked the package hard, or the verifier failed it twice. Once per package. |
| `researcher` | `opus` | Reconciling sources that contradict each other on a claim a decision depends on. |
| `writer` | `fable` | Story mapping for a substantial narrative, launched by you. |

These overrides are aliases because the Agent tool accepts nothing else; they resolve to Opus 5 and
Fable 5.1 on the Anthropic API, and the agent's reported model confirms it. There is no retry on
another model after a classifier refusal (`safety.md` section 6).

Subagent model resolution, since Claude Code v2.1.251: the per-invocation `model`, then the
agent's frontmatter `model`, then `CLAUDE_CODE_SUBAGENT_MODEL`, then the main conversation's
model. Never set `CLAUDE_CODE_SUBAGENT_MODEL`, and never set `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`:
it forces one model onto every subagent and workflow agent and breaks the whole roster. If
`env | grep CLAUDE_CODE_SUBAGENT_MODEL` shows either at intake, record it as a finding and say so
in one line.

Do not use the built-in Explore or Plan agents for drive work. Plan inherits the session model.
Explore inherits it too, capped at Opus on the Claude API, so from a Fable session it runs on Opus 5;
on other providers it inherits the session model uncapped. Neither is scoped or recorded by drive's
hooks. Use `drive:researcher` and `drive:architect`.

## 5. Grading in tiers

| Tier | Who | Grades | Examples |
|---|---|---|---|
| 0 | scripts, no model | exit codes and presence | build, tests, lint, `drive.py lint`, `git worktree list`, a URL returning 200 with the quoted text |
| 1 | `drive:grader` (sonnet, low) | checklists of binary assertions against evidence | citation checks, docs commands resolve, STATUS rows cite existing evidence, every claim has a test-plan row and every double a ledger row, parity mismatch triage, duplicate classification, the review panel's evidence lens |
| 2 | `drive:verifier`, `drive:security-reviewer`, `drive:ui-reviewer`, `drive:architect` as reviewer (opus) | judgment | correctness against a claim, security weaknesses, UI against the contract, the review panel's kindness and defect lenses, the final-audit checklist when the auditor is not required, classification review at M and above, and spec, design, and test-plan review at S and M |
| 3 | `drive:auditor` (fable, xhigh) | the final verdict | the final audit before Done, dispute rulings, lesson verification, spec, design, test-plan, and `operate` plan review at L and XL, and the re-classification review at XL phase gates |

Run tier 0 first and put its output in the transcript before any model grades anything. Never
hand a tier-2 question to the grader: asked "is this design sound", a low-effort Sonnet reads the
prose and agrees with it. For the same reason the grader never runs the final-audit checklist. A
grader's brief is a list of assertions with evidence paths and an explicit "unknown" answer; any
unknown makes the checklist not met.

Every grader, verifier, and reviewer prompt asks for coverage: report every finding, including
uncertain and minor ones, each with a severity and a confidence, and answer unknown when evidence
is missing. Filtering happens afterwards in a separate step. Never tell a judge to be conservative
or to report only important issues; current models follow that literally and under-report. Never
ask any agent to show, echo, or explain its reasoning; ask for conclusions with evidence.

Graders are strangers to the work. Launch each as a fresh agent that receives artifacts and a
rubric, never a transcript or a maker's summary, and never resume a maker as its own reviewer.

**Watching the cheap tier.** Tier 1 saves money only while its passes can be trusted, so test the
grader instead of assuming it.

- **Canary and blind re-grade.** Both are defined once, in section 11 of `verification.md`: where the
  canary goes, where its answer is kept, what a miss does, how many passes the re-grade samples, and
  where the comparison is written. Follow that section; this file adds only their cost.
- **Cost.** A canary adds one item per batch at Sonnet prices. A blind re-grade is one Opus call per
  phase gate, a small fraction of the verifier rounds it protects. The retro reports canary misses and
  agreement counts; they are the evidence for keeping a checklist kind on tier 1 in later runs, and a
  lesson candidate when a kind keeps failing.

## 6. Why there is no Haiku

The skill does not trust Haiku for this work, and the facts support that choice: Haiku 4.5 has a
200K window, supports no effort control, has a February 2025 knowledge cutoff, and may retire from
2026-10-15. Sonnet at low effort gives the cheap tier and still honours an effort setting.

Haiku enters a run only through defaults, so close them. The `/goal` evaluator and background
summaries use the small fast model, which is Haiku unless `ANTHROPIC_DEFAULT_HAIKU_MODEL` is set;
the launch recipe sets it to `claude-sonnet-5` for the run's process whenever `/goal` is used.
That variable is the override to use; the older `ANTHROPIC_SMALL_FAST_MODEL` is still documented but deprecated in its favour, so never set it. Never write `haiku` in an agent file, an Agent
call, or a Workflow script.

## 7. Cost envelopes

Estimate at intake from the shape and size and write the figure on GOAL.md's `budget:` line. These
are estimates from a cost model recomputed on 2026-09-14 at September 2026 prices, assuming the
roster above, a one-hour orchestrator cache, and the round bounds and verification unit in
`references/verification.md` sections 2 and 6. They are not quotes; a
run with more packages, rounds, or UI screens than the typical case lands above them.

The model prices every agent invocation as requests that re-read a growing cached context. An agent
that makes T requests, starting from B tokens of context that grow by G tokens per request, with O
output tokens per request, pays for T × B + G × T(T − 1)/2 tokens of cache reads, B + G × (T − 1)
tokens of cache writes at the five-minute rate, and O × T output tokens; uncached input is negligible
in Claude Code. The orchestrator is priced the same way across its sessions, with one-hour writes and
a re-write after every wait longer than the hour. Typical invocations come out at about $3.40 for a
full Opus verifier round, $1.60 for a scoped round or refutation, $1.70 for a Sonnet implementer,
$8.60 for an xhigh investigation, and $10.80 for a Fable final audit, which matches the cost of
subagents Claude Code has recorded, and the orchestrator is the largest single cost in most runs. The
`fix` XS to M, `feature` S, `report` M, `move` L, and `publish` L cells were modelled role by role;
the `build` row and the `feature` M cell come from the measured run below; the others scale the
earlier figures by the ratio those cells showed. Further real runs should replace them: a headless
run records `total_cost_usd`, and a background run's cost is in `/usage`.

The first measured run (`research/40-linkkeeper-run-review.md`, 2026-09-15) was a `build` at M with 44
claims and 15 packages: it recorded $359 over about seven hours and stopped at its dollar line with 6
claims at Local Proof and 38 at Partial. It ran under the earlier bounds, with three full review
rounds on every planning artifact and per-package verification that failed most units once or twice,
so the M cells are recomputed from its measured phases for the bounds now in force. At the run's
average of about $50 an hour, its three hours of planning cost about $150 and its four hours of build
and verify about $200; replacing six full planning review rounds with two full rounds and two scoped
re-checks removes about a third of the planning cost ($50), and wave-level verification removes about
a third of the build and verify cost ($60), which leaves about $240 for the work that run did, while
the rounds it could not afford, to bring 38 Partial rows to Local Proof, add up to about $200, so a
44-claim M build lands between $240 and $450. A `feature` at M has no research lanes, capability map,
wave 0, or integrate phase, which took about an hour and a half of that run, and usually carries half
the claims, so its cell is set at about 60 to 80 percent of the build cell. The `build` L and XL cells
were rescaled from the same run and are unchanged, because per-package verification and three full
review rounds still apply there. All of these rest on one run, and a UI review or many packages
verified alone for auth, money, or data-loss claims put a run at the top of its range or above.

Any figure a run writes as spend comes from a recorded total, named with its source: a headless
result's `total_cost_usd`, `/usage`, or the harness budget line. When none is available the line says
"not measured" rather than giving an estimate as a cost, and the report's figure is taken after the
final audit has returned, because a figure taken before it leaves out the most expensive verdicts.

| Shape | XS | S | M | L | XL |
|---|---|---|---|---|---|
| `fix` | $3 to $6 | $20 to $40 | $50 to $120 | $90 to $200 | reclassify |
| `feature` | $3 to $6 | $30 to $50 | $150 to $350, from one measured run | $300 to $550 | $600 to $1,100 |
| `build` | not used | $30 to $80 | $240 to $450, from one measured run | $600 to $1,300 | $1,200 to $3,000, more on a bad run |
| `move` | $5 to $10 | $30 to $80 | $110 to $270 | $190 to $490 | $500 to $1,000 |
| `publish` | $3 to $6 | $20 to $60 | $80 to $240 | $180 to $420 | $350 to $700 |
| `report` | $3 to $6 | $10 to $40 | $25 to $60 | $75 to $180 | $180 to $380 |
| `operate` | $3 to $6 | $10 to $40 | $30 to $100 | $75 to $180 | reclassify |

Add $3 to $10 for the security review and severe tests that the `auth` trait brings to an XS or S run. For a headless launch,
the top of the range is the cumulative envelope the leg loop in `long-running.md` section 2 enforces
across legs, and each leg's `--max-budget-usd` is what remains of it. Background sessions have no
dollar cap, so the subagent count stands in for one. Write it on the budget line
(`budget: 40 turns · 40 subagents · 3 h · $150 to $350`, the number directly before `subagents`):
`drive.py lint --gate` counts the maker subagents (`drive:implementer`, `drive:writer`,
`drive:designer`, `drive:architect`, `drive:researcher`) the hooks recorded starting since `init`,
warns past the count, and fails past twice the count until a DECISIONS.md entry records the budget
overrun with a `Narrows:` line naming what was cut. Reviews are never counted, because they are the
ceremony the size requires, so the count bounds how much building and research a run buys and the
dollar envelope bounds the rest. At the warning, log the overrun in DECISIONS.md and narrow in the
order SKILL.md section 9 gives; at the failure, record the overrun with its `Narrows:` line and
re-plan within the remaining envelope, or stop. Record each phase's estimate in the plan; when a
phase spends twice its estimate, stop, record why in STATE.md, and continue only after a re-plan
in GOAL.md shows the remaining envelope covers the rest. The report states the envelope and the
recorded spend taken after the final audit. A headless leg's own `total_cost_usd` arrives only when
that session ends, so the report gives earlier legs' totals from `.drive/local/run.md` plus the latest
recorded figure for the current leg with its time, and says the leg's result holds its final figure.

## 8. Cache discipline

- **One-hour cache when billing by API key.** With an API key or a cloud provider, the main
  conversation's prompt cache lasts five minutes, so an orchestrator waiting fifteen minutes on a
  subagent re-reads its entire context at the full input rate. Set the `promptCacheTtl` setting to
  `"1h"` (Claude Code v2.1.242 or later), passed in the launch `--settings` JSON so the owner's
  settings files stay untouched, or set `CLAUDE_CODE_PROMPT_CACHE_TTL=1h` in a headless process
  environment; the variable takes precedence over the setting. A Claude subscription within its
  included usage already gets the hour for the main conversation. To confirm, run
  `claude -p "hello" --output-format json` with the same settings and look for
  `ephemeral_1h_input_tokens` under `usage.cache_creation`.
- **Subagents stay at five minutes** (`subagentPromptCacheTtl`) unless verifiers routinely idle
  longer than that waiting on test suites; the one-hour write rate is higher.
- **Keep the orchestrator's model constant.** On Fable 5.1 with an API key or a Claude subscription
  (Claude Code 2.1.260 or later; not on Bedrock, Google Cloud, or a Claude apps gateway, and not when
  `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS` is set or the organization has a HIPAA configuration), an
  effort change keeps the cache; a model change always rebuilds it, and a classifier fallback is a model
  change.
- **Keep prompts cache-shaped.** Agent system prompts are static files; task detail goes in the
  brief. Workflow agents with the same model, effort, agent type, tools, schema, and working
  directory share a cached prefix. Agents in different worktrees do not.
- **Keep images and large outputs out of the orchestrator.** Accumulated images eventually force
  Claude Code to drop a batch, which invalidates the cache from that point.

## 9. The three biggest cost sinks

| Sink | Why it grows | Bound |
|---|---|---|
| Orchestrator context | Fable cache reads, writes, and output across a long run; reads are the largest part. | One-hour cache. Fixed-size results of at most 1,500 characters plus paths. No source, logs, or screenshots read inline. A fresh session per day-sized phase. Model held constant. |
| Verifier rounds | They scale with packages times rounds, on Opus. | Tier 0 first, so a package with failing tests never reaches a verifier. Round limits per shape. One handoff per wave at M rather than per package (`verification.md` section 2). The handoff never carries the maker's transcript. |
| UI review | Each screen batch is a fresh Opus context that captures, reads trees and images, and judges, and each round repeats it. | Objective checks before vision, at most fifteen images a session, round two limited to affected screens and their neighbours (`ui-verification.md`). |

Implementer output and retries are a smaller line, about a twentieth of a `build` L run, and stay
small when each package holds one claim within the size limits in `parallel.md`, Sonnet goes first
with Opus only on the override conditions, changes and tests are kept to the brief, and a partial
result is continued once: with `SendMessage` while the agent id is still valid in this session, which
keeps its cache, otherwise by a fresh re-dispatch from the brief; either counts as one workaround
ledger row (`parallel.md` section 10).

## 10. Every result names its model

- Every agent's final message ends with the model named in its own system prompt. Reports and
  verdict files carry a `model` field.
- Record the model actually serving the orchestrator in STATE.md `model:` at intake and at every
  phase gate.
- The auditor compares every reported model against the roster. A role that ran on a different
  model than its row (for example a fallback model where Opus 5 was expected, or Opus where Fable was
  expected) is a Boundary event and a finding, and the auditor decides whether any verdict it
  produced must be re-run.
