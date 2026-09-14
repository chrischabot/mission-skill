# 20 · The deep bug hunt

Component report for the `/drive` skill. Worked shape: "find this deep annoying bug and fix it" in an existing codebase. Written 2026-09-14 against live Claude Code docs, the Fable 5 prompting guide, the Anthropic pricing page, and the owner's own bug history from the Arcwell memory files. Verified facts carry URLs; the owner's incidents are cited as "owner memory"; everything else is argued opinion.

## 1. Executive opinion

The bug-hunt shape is where the skill earns or loses trust, because it is the shape the owner will invoke most often and the one where ceremony is most visibly wasted. The skill should hold exactly three invariants and let everything else scale with the bug. The first is that no fix is written before the failure is reproduced as something that runs and fails: a test, a script, or a recorded live probe. The second is that the fix is confirmed by an agent that did not write it, and that agent reproduces the original failure on the pre-fix code before it confirms the fix. The third is that the hunt ends with the root cause stated in one sentence that explains every observation in the brief (why now, why here, why this often), and with the test harness taught the production constraint that let the bug through, so the class cannot recur silently. A one-line bug satisfies all three in ten minutes. A deep bug takes the whole runbook.

Between those invariants sits the hypothesis ledger: one row per hypothesis, with the prediction written down before the experiment runs. It is the working document, the thing a second-opinion agent reads, the thing the verifier checks the fix against, and the raw material of the post-mortem. When the ledger stalls, the skill widens scope in a fixed order: a fresh-context Opus second opinion, then parallel hypothesis workers in throwaway worktrees, then re-classification to the feature or migration shape when the bug turns out to be a design flaw.

Diagnosis belongs on Fable in the main session at high effort. Anthropic's own guide says Fable's bug-finding recall and repository-history search are noticeably better than Opus 4.8, and Fable costs twice Opus per token, not the five times the post claims. Opus at high effort takes the bounded roles: one hypothesis per worker, the second opinion, the verifier. Sonnet takes log sweeps, config diffs, stress loops, and sibling-pattern searches. There is no grader role at all: the `/goal` evaluator cannot run tools, so it can keep the loop open but cannot verify a fix. Only the tool-using verifier can.

## 2. What the post says, and a critique

The post barely mentions debugging. Its one direct statement is that Opus 4.8 should take "complex debugging" as a hard-but-bounded subtask, and its indirect contributions are the verifier-beats-self-critique point, the five-stage memory progression, the STATE.md sketch with an "Open failures" section, and the worktree advice. Taken as a debugging philosophy, here is where it lands.

It is right that the agent that wrote the code must not be the one that grades it. For bug fixes this is not a nicety but the whole game, because the failure mode of a debugging agent is not incompetence but premature closure: it stops when the symptom stops. Anthropic's harness-design post documents the mechanism in a different domain (agents "confidently praising the work" they produced) and finds that tuning a standalone evaluator to be skeptical is "far more tractable than making a generator critical of its own work" (verified, URL in section 3). The Fable prompting guide says the same in one line: "Separate, fresh-context verifier subagents tend to outperform self-critique." The post is right to make this the centrepiece. It is wrong about who the verifier should be. It proposes Haiku graders because they are cheap and have an independent context window. A bug-fix verifier must run the reproduction on the pre-fix commit, run it again on the fix, and attempt to refute the root cause with adjacent inputs. That is tool-using judgment work, not classification. The owner has already ruled Haiku out; the argument here is that even if he had not, a grader that cannot run the repro is verifying prose about a fix rather than the fix.

The five-stage progression (fail, investigate, verify, distill, consult) is the most useful thing in the post for this shape, because a bug hunt is that progression with the names changed: the brief is the documented failure, the ledger is the investigation, the failing-then-passing test is the verified fact, the general rule is the distillation, and reading STATE and LESSONS at intake is the consultation. The numbers (Fable completing the progression with verification coverage up to 73 percent against 7 to 33 percent for Opus 4.7) come from Lance Martin's X article and one task of Continual Learning Bench 1.0; the paper exists on arXiv but I did not verify the per-model figures against it, so treat them as a source claim from an Anthropic engineer rather than a verified fact.

The post's cost claim is wrong. It says Fable costs about five times Opus 4.8. The pricing page lists Fable 5.1 at $10 input and $50 output per million tokens and Opus 4.8 at $5 and $25, a factor of two, and Fable 5.1 cache hits at $0.25 per million against Opus at $0.50. A bug hunt's token volume is dominated by re-reading cached context (files, logs, the ledger), so the effective ratio is below two. This matters because the post routes "complex debugging" to Opus on cost grounds while Anthropic's guide routes bug finding to Fable on capability grounds. The capability argument wins once the cost argument is corrected.

The post's worktree advice ("maker writes in worktree A; verifier reads in worktree B") collides with the owner's rule that no branch or worktree survives a step. The docs confirm the collision: a subagent worktree "with changes stays on disk until the periodic sweep." The skill therefore uses worktrees only for experiments that end clean, and merges nothing from them; the winning patch is re-applied in the canonical checkout.

The post's "Open failures" section in STATE.md is good and should survive: a flake at "1 in 50" with a hypothesis and a repro path is exactly what the next session needs. Its "vision self-check" belongs to UI bugs. Its safety-boundary point has one real consequence here: a bug that is security-flavoured (an authorization bypass, an injection) may trip Fable's classifiers and fall back to Opus, and the skill should expect that and route those hunts to Opus explicitly rather than discover it through a silent refusal.

What the post omits entirely: reproduction before diagnosis, the ledger discipline of writing predictions before experiments, bisection, the difference between fixing the instance and fixing the class, and the harness-fidelity lesson that the owner learned the hard way. Those are the body of this report.

## 3. Verified facts

Claude Code harness, checked 2026-09-14.

- Subagent frontmatter accepts `model: fable` alongside `sonnet`, `opus`, `haiku`, a full model ID, or `inherit`; `effort` takes `low|medium|high|xhigh|max` and "available levels depend on the model"; `isolation: worktree` gives "an isolated copy of the repository branched by default from your default branch rather than the parent session's HEAD" and "the worktree is automatically cleaned up if the subagent makes no changes"; `maxTurns` returns output "marked as partial" at the limit and the subagent can be resumed; `memory: user|project|local` gives a persistent directory whose `MEMORY.md` first 200 lines or 25 KB are loaded at start. https://code.claude.com/docs/en/sub-agents
- Model resolution order for a subagent is now: per-invocation `model` parameter, then frontmatter (`inherit` selects the main model), then `CLAUDE_CODE_SUBAGENT_MODEL`, then the main conversation's model. "Before v2.1.251, `CLAUDE_CODE_SUBAGENT_MODEL` came first." The brief states the older order; the coordinator should update it. Same URL.
- Subagents may spawn subagents "up to three layers below the main conversation"; `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` changes this. A fork inherits the whole conversation and is the wrong tool for an independent second opinion. Same URL.
- A subagent worktree "with changes stays on disk until the periodic sweep" governed by `cleanupPeriodDays`; Claude Code holds a `git worktree lock` while the agent runs; `git worktree remove --force` removes a kept one; `worktree.baseRef` is `"fresh"` (default branch from origin) or `"head"`. Non-interactive `-p` runs never clean up their worktrees. https://code.claude.com/docs/en/worktrees
- `/goal` takes a condition up to 4,000 characters, is judged after each turn by the configured small fast model (Haiku on the Claude API, overridable with `ANTHROPIC_DEFAULT_HAIKU_MODEL`) which "does not call tools, so it can only judge what Claude has already surfaced in the conversation"; verdicts are not-yet-met, met, impossible; evaluation is skipped while a subagent or background shell runs, with check-ins from 30 minutes; the loop stops with a warning if Claude answers without tool use for several turns; works with `claude -p`. https://code.claude.com/docs/en/goal
- Dynamic workflows are opt-in by the `ultracode` keyword or "use a workflow" in a human-typed prompt, or by a skill's instruction; the script API is `agent()`, `parallel()`, `pipeline()`, `phase()`, `log()`; up to 16 concurrent agents, 1,000 per run; default size guideline `medium` means fewer than 15 agents. The docs give a flaky-test workflow example: "run the suite repeatedly, record which tests fail intermittently, and stop once two rounds in a row find nothing new." https://code.claude.com/docs/en/workflows
- Best practices: "Address root causes, not symptoms" is a named strategy with the example "fix it and verify the build succeeds. address the root cause, don't suppress the error"; the debugging prompt example is "write a failing test that reproduces the issue, then fix it"; the adversarial review step says a fresh subagent "sees only the diff and the criteria you give it, not the reasoning that produced the change"; a Stop hook is overridden after 8 consecutive blocks; after two failed corrections on one issue, `/clear` and re-prompt. https://code.claude.com/docs/en/best-practices
- Common workflows, "Fix bugs efficiently": tell Claude the repro command and stack trace, the steps, and whether the error "is intermittent or consistent." https://code.claude.com/docs/en/common-workflows
- Bundled skills: `/verify` builds and runs the app "to confirm a code change does what it should, without falling back to tests or type checks" and records its recipe to `.claude/skills/verify/SKILL.md`; `/run-skill-generator` records the launch recipe; `/code-review` reviews a diff in a fresh subagent; `/debug` debugs Claude Code itself via the session debug log, not the user's code, so the bug-hunt runbook must not reach for it. SKILL.md should stay under 500 lines; after auto-compaction the first 5,000 tokens of each invoked skill are re-attached within a shared 25,000-token budget. https://code.claude.com/docs/en/skills and https://code.claude.com/docs/en/commands
- Effort levels by model: Fable 5.1, Fable 5, Opus 5, Sonnet 5, Opus 4.8, Opus 4.7 support `low..max`; `high` is the default everywhere except Opus 4.7; `max` "may show diminishing returns and is prone to overthinking"; the `sonnet` alias resolves to Sonnet 5 and `opus` to Opus 5 on the Anthropic API; `fable` resolves to Fable 5.1 unless `ANTHROPIC_DEFAULT_FABLE_MODEL` is set. No Sonnet 4.8 appears in the effort table or on the pricing page. The skill should name aliases, not versions. https://code.claude.com/docs/en/model-config
- Pricing per million tokens: Fable 5.1 $10 in / $50 out, cache hit $0.25; Opus 4.8 $5 / $25, cache hit $0.50; Sonnet 5 $2 / $10; Haiku 4.5 $1 / $5. https://platform.claude.com/docs/en/about-claude/pricing
- Fable 5 prompting guide: "Code review and debugging. Bug-finding recall (outside the cybersecurity domains the safety classifiers cover) is noticeably higher than Claude Opus 4.8, including search across codebases and repository history." "Separate, fresh-context verifier subagents tend to outperform self-critique." Effort: "Use `high` as the default for most tasks, with `xhigh` for the most capability-sensitive workloads." The guide supplies ready prompts for grounding progress claims ("audit each claim against a tool result from this session"), for autonomous operation, and the warning "A signal that pattern-matches to a known failure may have a different cause." It also warns that prompts telling the model to echo its reasoning can trigger the `reasoning_extraction` refusal and fall back to Opus. https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5
- Harness design post (Prithvi Rajasekaran, Anthropic, 24 March 2026): agents evaluating their own work "tend to respond by confidently praising the work"; a GAN-style generator/evaluator split; the evaluator drove Playwright to inspect the live page before scoring; "tuning a standalone evaluator to be skeptical turns out to be far more tractable than making a generator critical of its own work." https://www.anthropic.com/engineering/harness-design-long-running-apps
- Five-stage progression and the 73 percent figure: Lance Martin, "Designing loops with Fable 5", X article, referencing one task of Continual Learning Bench 1.0. https://x.com/RLanceMartin/article/2064397389189071163 ; the benchmark paper: https://arxiv.org/pdf/2606.05661 (existence verified, figures not cross-checked).
- `git bisect run <cmd>`: exit 0 means good, 1 to 127 except 125 means bad, 125 means skip this commit, any other code aborts; `git bisect log > file` and `git bisect replay file` recover from a mis-marked step. https://git-scm.com/docs/git-bisect
- Empirical, this machine (git 2.54.0): `git bisect run` inside a throwaway linked worktree (`git worktree add /tmp/x <bad>`, then `git -C /tmp/x bisect start <bad> <good>` and `git -C /tmp/x bisect run ...`) found the first bad commit while the main checkout had an untracked work-in-progress file and stayed on `main` throughout; `git -C /tmp/x bisect reset && git worktree remove --force /tmp/x` left one worktree and one branch. So the bisect never touches the canonical checkout and leaves nothing behind.
- Tools present in this environment for reproduction: Chrome DevTools MCP (`performance_start_trace`, `performance_stop_trace`, `performance_analyze_insight`, `take_heapsnapshot`, `lighthouse_audit`, console and network readers), Playwright MCP (`browser_snapshot` accessibility tree, screenshots, console, network), iOS Simulator MCP (`build`, `launch`, `screenshot`, `inspect` accessibility tree, `tap`, `swipe`). Verified by presence in the tool list, not exercised here.
- The installed `severe-testing` skill (`~/Projects/severe-testing/SKILL.md`) states: "Reproduce known bugs before fixing them, then keep the reproducer as a regression test," and sets the evidence bar for a bug-fix finding at 75 or 100 on its scale, with the note "a regression test that does not actually fail on the broken code is not evidence."

Owner memory, cited as lessons rather than facts: the D1 hundred-variable incident (sql.js shim permitted unlimited bound variables, 24 green validations, failed live past 100 wardrobe items); the Workflows-replay bug that "bit us twice" because closure side effects are not re-run on replay; the brief email test that "asserts the renderer, not the OutboundEmail"; the NotebookLM id-parse heuristic that "always failed while the test fake's invented shape passed"; the Codex hook outage with three stacked stale layers (cached plugin hooks, installed binary, pinned worker copy); the stale companion binary built three days before the fix it lacked; `wrangler.jsonc` naming the frozen v1 worker so a deploy targeted the wrong target; the wedged continuation "fixed" by raising `cpu_ms` (the trigger) while the honest durable fix stayed TODO; the midnight brief whose root cause was the window opening at local midnight; and the owner's own rule from the scheduler incident: "Second time is the bug. Repeating a workaround means the first diagnosis was wrong."

## 4. Detailed spec

### 4.1 Intake

The skill classifies the goal as a bug hunt when the prompt describes behaviour that differs from expectation in existing code, or when a verification step of another shape fails and the failure is not explained by the change under test. Intake extracts eight fields; missing ones are looked up, not asked for, because the owner is not watching. If a field truly cannot be recovered, record "unknown" and move on; an unknown "since-when" simply removes bisection from the diagnosis menu.

The fields are symptom (what was observed, quoted or captured, and what was expected instead), frequency (always, intermittent with a rate or a count, or once), environment (production, staging, CI, local; device, OS, browser, runtime version; the deploy or build identity), since-when (first observed, last known good, what changed around then), impact (who is affected, how badly, whether a workaround exists), trigger (steps, inputs, or conditions if known), evidence attached (logs, stack traces, screenshots, request ids), and prior history (has this symptom or this area been fixed before).

Lookups, in order, each done through the system's own tools rather than by poking its database:

1. Read the repo's STATE, LESSONS, and CLAUDE.md, and the skill's own `references/bug-hunt-lessons.md`. This is the consult stage. Anything that matches becomes a hypothesis with a high prior, not a conclusion; the Fable guide's warning that a pattern-matched signal "may have a different cause" applies with full force.
2. Load the system's observability tools early (ToolSearch for the MCP verbs of the system under test, `wrangler tail`, `gh run view`, Sentry, whatever exists). The owner's scheduler incident was caused by never loading the system's own verbs; deferred tools are invisible until searched for.
3. `git log --since=<last-good> -- <area>` and `git log -S'<symbol>'` for the touched code; `gh issue list --search "<symptom words>"` and `gh pr list --search` for related work.
4. Current test status on main for the area, the names of any existing regression tests there, and every test double the area's tests rely on (fakes, shims, in-memory databases, mocked clocks). For each double, write one line answering the owner's question: where is it kinder than the real thing?
5. Deploy identity: what version is actually running where the symptom appears (worker version id, binary build date, container tag). A bug that "should already be fixed" is frequently a stale artifact.

The bug brief is at most fifteen lines and heads the hunt's working file:

```markdown
# HUNT · <slug>
Symptom:     <observed> (expected: <expected>). Evidence: <path/log line/request id>
Frequency:   <always | ~1 in N over M runs | once on <date>>
Environment: <prod|ci|local>; <runtime/device/version>; running build <id>
Since:       first seen <date/commit>; last good <date/commit>; changed then: <deploys, deps, config>
Impact:      <who/how bad>; workaround: <none | ...>
Trigger:     <steps/input/conditions | unknown>
Prior:       <STATE/LESSONS entries consulted, or "none">
Harness:     <doubles in play and where each is kinder than production>
Repro cmd:   <filled in by 4.2>
Pre-fix ref: <commit hash at intake>
```

The working file lives in the skill's run directory, not in the target repository, so the owner's repos never gain committed scratch. What gets committed is the regression test, the fix, and an entry in the repo's STATE and LESSONS if the repo keeps them.

### 4.2 Reproduce first, always

The reproduction is the gate on everything after it. The skill does not permit an edit to non-test source until the brief's "Repro cmd" line names a command that exits non-zero on the current code for the reason in the brief. That command is then turned into a test in the project's own framework, named for the bug, with a CLAIM comment stating the behavioural claim it refutes. If a framework test is impossible (the failure needs a physical device or a third-party production system), the repro is a scripted probe whose output is pasted into the ledger, and the status ladder is capped at Local Proof until a live check exists.

Deterministic bugs. Write the failing test at the lowest layer that exhibits the failure. If the symptom is only visible through the whole system, start wide (a curl, a CLI invocation, a Playwright script) and descend as diagnosis localizes the cause, ending with two tests: a narrow one that pins the root cause and runs in milliseconds, and the wide one that proves the symptom is gone. Keep both. The owner's brief-email bug is the cautionary case: a test at the renderer layer was green while the transport dropped the HTML; the test that would have caught it asserts on the outbound message, not the render.

Flaky and intermittent bugs. Measure before diagnosing. Run the failing test or scenario N times and record the rate; a shell loop is runner-agnostic:

```bash
pass=0; fail=0; for i in $(seq 1 100); do
  if <test cmd> >/dev/null 2>"$RUN/flake-$i.log"; then pass=$((pass+1)); else fail=$((fail+1)); fi
done; echo "pass=$pass fail=$fail"
```

Then amplify until the failure is reliable, because a one-in-fifty flake makes every later step fifty times slower. Amplifiers, cheapest first: fix and print the random seed on failure; run under load (`-j`, a parallel loop, CPU throttling); inject timing at suspected points (a sleep or yield before the racy read, a paused or fake clock); use the language's deterministic-schedule tooling where it exists (`go test -race -count=50`, `loom` for Rust, `tokio::test(start_paused = true)`, a shuffled test order to surface order dependence); log on failure only, with a correlation id, from a ring buffer. A flake that cannot be amplified past about one in ten is diagnosed by differential logging across many runs rather than by stepping through one. The docs' flaky-test workflow (run the suite in rounds, stop when two rounds add nothing) is the right tool when the task is "find the flakes", but for "fix this flake" a shell loop in the main session is enough.

Environment-specific bugs, especially production-only. Diff the environments along five axes before touching code: configuration (env vars, secrets present or absent, feature flags, bindings, the exact deploy target name); data shape (row counts, sizes, nulls, unicode, cardinality past a platform limit); runtime (workerd against node, D1 against sql.js, a launchd daemon against an interactive shell, a real OAuth grant against a fixture); build and artifact staleness (which copy is running: cache, installed binary, pinned worker copy, in-memory definitions in a long-lived process); and the harness itself (every double, and where it is kinder). The owner's incidents map onto all five: the wrong worker name in `wrangler.jsonc`, the hundred-variable D1 limit, launchd's TCC-denied cookie read, the three stale layers of the hook outage, and the sql.js shim. When the diff points at a constraint, reproduce it locally by teaching the local harness that constraint (enforce the limit in the shim, run `wrangler dev --remote`, use the real database engine). When it cannot be reproduced locally at all, reproduce it live but read-only: capture the exact failing input from logs and replay it against production with a probe that changes nothing. A live read-only probe is a legitimate reproduction and should be recorded as such.

UI bugs. Capture the failing state as a screenshot and as an accessibility tree (Playwright `browser_snapshot`, iOS Simulator `inspect`); assert on the tree where possible, because tree assertions survive cosmetic change and pixel assertions do not. Reduce to the smallest component and state that still shows the defect. The failing test is a Playwright or XCUITest scenario; the visual confirmation after the fix is done by a fresh agent reading the before and after screenshots against the brief, never by the agent that made the change. A Playwright trace or a screen recording is the "log" for a UI bug and should be captured at reproduction time.

Performance bugs. Write the budget first (p95 latency, memory ceiling, query count), because "slow" is not a failing test. Measure with the right profiler for the runtime (Chrome DevTools performance trace and heap snapshot through the MCP, `samply` or `cargo flamegraph`, `py-spy`, `node --cpu-prof`, Instruments on iOS, `EXPLAIN QUERY PLAN` for SQL) and turn the measurement into an assertion that fails now: a benchmark with a threshold, a test that counts queries, a trace-derived check. Benchmarks are noisy; assert relative to a baseline measured in the same run, repeat, and prefer counting (queries, allocations, bytes) to timing where a count exists.

### 4.3 Diagnosis

The hypothesis ledger is the only required structure, and its one hard rule is that the prediction is written before the experiment runs. A hypothesis without a prediction is a hunch; a prediction written after the result is a rationalization.

```markdown
## Ledger
| # | Hypothesis | Prediction (if true, doing X shows Y) | Experiment | Result | Status |
|---|------------|----------------------------------------|------------|--------|--------|
| 1 | ...        | ...                                    | cmd/path   | output | open/confirmed/refuted/partial |
```

Start with a differential diagnosis: three to five candidates spread across layers (input and data, code logic, concurrency and timing, configuration and environment, dependency and platform behaviour, build and deploy staleness), each with a rough prior and a rough cost to test. Test the cheapest experiment that discriminates between the highest-prior candidates. One variable per experiment.

A hypothesis is confirmed only when its prediction was observed and it explains every field of the brief. The two questions that expose a half-cause are "does this explain why it started when it started?" and "does this explain why it happens here and not there?" If a confirmed hypothesis fails either question it is marked partial and becomes a contributing factor; the hunt continues. The midnight-brief incident is the model: several plausible causes existed, and only "the obligation window opens at local midnight" explained the timestamp exactly.

Bisection is available whenever the brief has a last-good reference and the repro is deterministic (or has been amplified into a script that loops and applies a rate threshold). Run it in a throwaway linked worktree so the canonical checkout is never moved:

```bash
W=$RUN/bisect; git worktree add --detach "$W" <bad>
git -C "$W" bisect start <bad> <good>
git -C "$W" bisect run sh -c 'cd "$W" && <build cmd> || exit 125; <repro cmd>'
git -C "$W" bisect log > "$RUN/bisect.log"
git -C "$W" bisect reset; git worktree remove --force "$W"; git worktree list
```

Exit 125 skips commits that do not build; the log allows replay after a mis-marked step. The same shape bisects over data (which input triggers), configuration (which variable), dependency versions (the lockfile), and deploys (which version id). Finding the commit is not finding the cause; the commit is a new high-prior hypothesis for the ledger.

Instrumentation is temporary and tagged. Every added log line or assertion carries a unique marker (`HUNT-<slug>`) so `git diff | grep HUNT-` finds all of it before the fix commit, and prefer asserting an invariant at the suspected point over printing a value. Use a real debugger when the runtime offers one. Remove everything before the fix is committed.

Read dependency and platform source instead of guessing about it. The owner's transport notes are a list of guesses that were wrong until someone read or probed the platform: the account-level email endpoint that does not exist, the gateway auth header, the D1 GLOB character classes, the OAuth provider's absolute expiry. When a hypothesis is "the platform does X", the experiment is a probe of the platform or a read of its source in `node_modules`, the cargo registry, or its docs, not a re-read of the caller.

The second opinion is a fresh-context agent, not a fork. When the ledger has three refuted rows and no open candidate, spawn the `debugger` subagent in second-opinion mode with only the brief, the ledger, and the repro command. It must produce its own ranked differential and name the single most discriminating experiment. The point is that it has not seen the transcript; the Fable guide and the harness-design post both attribute the verifier's advantage to that separation. Run it on Opus by default so that it also carries different priors from the Fable session; if it fails too, one Fable attempt at `xhigh` in a fresh subagent is the last escalation before re-classification.

Time-boxing is in attempts, not minutes, because the agent can count attempts. Three reproduction strategies without a failing command means switching from local reproduction to live capture. Three refuted hypotheses with no new candidate means the second opinion. A failed second opinion means either the parallel fan-out of section 4.8 (when several substantial hypotheses remain) or re-classification (when none do). The whole hunt is bounded by the `/goal` clause "or stop after N turns" with a written handoff into STATE's open-failures section, so a stall ends in a documented failure rather than a silent one.

Re-classification is a first-class outcome. When the confirmed cause is a design flaw (fixing it means changing an invariant, contract, or schema that many callers rely on), the hunt writes its finding, marks the bug shape complete at "root cause verified", and hands off to the feature or migration shape with the ledger as input; the small correct fix, if one exists, ships now and its limitation is recorded as a verified fact. When the "bug" turns out to be correct behaviour against a wrong expectation, the hunt reports that with the evidence and stops. The owner's wedged-continuation case shows why this matters: raising `cpu_ms` fixed the trigger, the orphaned continuation was the design flaw, and the honest fix stayed TODO because no one re-classified.

### 4.4 Fix

The fix must remove the confirmed cause, and the smallest change that does so is preferred over a larger one. When the proper fix is large, ship the smallest correct fix and re-classify the rest; never ship a symptom patch in place of a cause. A symptom patch is a retry, a sleep, a widened timeout, a swallowed exception, a null check, a default value, or a skipped test that makes the observation go away without a ledger row explaining why the cause is genuinely external and this is its correct handling. The verifier is told to look for exactly these shapes in the diff.

Fixing the class means two questions after the instance is fixed. First, where else does this pattern live: grep for siblings of the fixed construct and either fix them in the same commit or list them in the post-mortem with evidence that they are unaffected. Second, where was the harness kinder than production: teach the shim the constraint (the sql.js fake refuses more than a hundred bound variables), enforce the constraint in the code under test (the query builder chunks at a hundred), and add a test that generates the violating shape (a wardrobe of a hundred and one). The class fix is what makes the difference between a bug that recurs under a new name and a lesson. The Workflows-replay bug is the negative example: it bit twice because the first fix taught nothing to the harness; the class fix is a lint or test asserting that step results are returned, not captured.

The second-time rule is enforced at two points. At intake, if STATE or LESSONS records a fix for the same symptom or the same area, the prior fix's root cause is treated as suspect, not as settled. During the hunt, if the same workaround is about to be applied a second time (a second raise of the same limit, a second retry added to the same call), the skill stops and re-opens diagnosis, because the first diagnosis was wrong.

The Fable guide's own instruction applies verbatim to the fix commit: "A bug fix doesn't need surrounding cleanup." The diff must be explainable by the confirmed hypothesis, and anything else in it is a reason for the verifier to send it back.

### 4.5 Verification

Verification is a checklist the maker runs and a verdict the checker delivers, and both are required even for a small bug, because the checker is cheap and premature closure is the dominant failure of debugging agents.

The maker's checklist: the regression test exists, is named for the bug, carries its CLAIM, and stays in the suite; instrumentation is gone (`git diff | grep -c HUNT-` is zero); the test fails on the pre-fix code, demonstrated by stashing the fix or running the test in a throwaway worktree at the pre-fix commit and pasting the failing output into the ledger; the whole suite, lint, and typecheck pass using the project's own gates; the `severe-testing` skill has been run on the fixed area with the instruction that this is stronger verification after a bug fix (its bar for such findings is 75 or above, and it explicitly discounts a regression test that does not fail on the broken code).

The checker is a fresh subagent on Opus at high effort. It receives the brief, the ledger, the diff, the regression test name, the repro command, and the pre-fix commit hash; it does not receive the transcript. It must, in order: reproduce the original failure on the pre-fix commit in a throwaway worktree and paste the output; run the regression test and the suite on the fix and paste the output; state whether the claimed root cause explains every field of the brief, and try to refute it with at least two adjacent inputs or conditions the fix was not written for; check the class fix (siblings, harness constraint); scan the diff for symptom-patch shapes and for changes the hypothesis does not explain; and return a verdict.

```markdown
## Verifier verdict · <slug>
Pre-fix reproduction: FAILED as described | did not reproduce (details)   evidence: <cmd, output>
Post-fix regression test: PASS | FAIL                                     evidence: <cmd, output>
Suite / lint / typecheck: PASS | FAIL                                     evidence: <cmd, exit codes>
Root cause explains: symptom Y/N · frequency Y/N · environment Y/N · since-when Y/N
Refutation attempts: <input/condition → result> ×2+
Class fix present: siblings <checked/n found>; harness taught constraint <yes/no/n.a.>
Diff smells: <none | list>
Unexplained changes in diff: <none | list>
Verdict: PASS | FAIL (<one sentence>)   Ladder: Local Proof | Live Proof
```

A FAIL goes back to the maker with the verdict as the next ledger row; the maker does not argue with it in prose but answers it with an experiment.

Live proof for production bugs is not optional and is not "when the cron runs." Deploy through the system's own tools, confirm the deployed identity is the one you meant (version id, worker name, binary build), then reproduce the original failing condition against the live system with the captured input and show it passes, recording the request id or log line. If the live condition genuinely cannot be forced now (it depends on a clock boundary that has not arrived), the status is Local Proof, the pending live check is named in STATE's open failures, and the report says so in plain words. The NotebookLM id-parse fix is the model: the porting bug was fixed, then proven live the same day with a generated episode and a recorded pointer.

### 4.6 Root cause into lesson

The five stages map onto the hunt's artifacts without any extra work: the brief is the documented failure; the ledger is the investigation; the pre-fix failure plus the post-fix pass plus the one-sentence cause is the verified fact; the general rule is the distillation; and the intake read is the consultation. The skill's job is to route three different kinds of knowledge to three different homes and to keep each short.

STATE.md in the repository receives verified facts about this system, each with how it was verified: "D1 rejects more than 100 bound variables per statement; the sql.js test shim now enforces the same limit (test `severe_wardrobe_101_items`)." "launchd-spawned processes cannot read Chrome's cookie database on this Mac; interactive shells can (TCC)." If the hunt ended in a stall, STATE's open-failures section receives the symptom, the best hypothesis, the rate, and the path to the repro.

LESSONS (in the repo if it keeps one, otherwise the owner's memory) receives the general rule, phrased without this repo's names: "A test harness kinder than production certifies broken code; ask of every shim where it is kinder." "A workaround applied twice means the first diagnosis was wrong." "When a symptom appears after a rename or deploy, enumerate every copy of the artifact that could be running and check each."

The skill's own `references/bug-hunt-lessons.md` receives procedural lessons about how to hunt, and only those that would change the next hunt: "bisect in a throwaway worktree so the checkout is never moved", "for production-only symptoms diff the deploy target identity before diffing code", "a flake under about one in ten is diagnosed by differential logging, not stepping." An addition requires the verifier's agreement that it is general and not already present, and the file is pruned when it passes about eighty lines, because a long lessons file is the over-specified CLAUDE.md the docs warn about.

The post-mortem is the last section of the working file and is at most twelve lines:

```markdown
## Post-mortem
Symptom:        <one line>
Root cause:     <one sentence that explains symptom, frequency, environment, since-when>
Why not caught: <the harness gap or missing constraint>
Fix:            instance <commit>; class <shim/lint/test added, siblings checked>
Evidence:       pre-fix fail <cmd/output ref>; post-fix pass; suite green; verifier PASS; live <request id | pending: reason>
Lesson:         <one general rule → LESSONS>  Facts → STATE: <n>  Skill lesson: <none | one line>
Ladder:         Local Proof | Live Proof | Operational
```

### 4.7 The working file

One file, `HUNT.md`, in the skill's run directory, with sections appended in order: brief, repro, ledger, fix, verification, post-mortem. Five separate files would be ceremony for a bug. The file is the handoff if the hunt stalls, the input to the second opinion and the verifier, and the source of the STATE and LESSONS entries. Nothing in it is committed to the target repo.

### 4.8 Parallel hypothesis testing

Fan out when, and only when, the ledger holds two or more open hypotheses whose discriminating experiments are each substantial (they need instrumentation or a candidate patch, not a one-line probe) and independent (different layers or files), or when the reproduction is expensive and several instrumentations can run concurrently against it. Do not fan out for hypotheses whose test takes a minute; run it. Do not fan out for hypotheses that depend on each other's results.

Each worker is the `debugger` subagent in hypothesis mode, launched with the Agent tool, `run_in_background: true`, and `isolation: "worktree"`, and given exactly one hypothesis, its prediction, the repro command, the brief, and the paths it may touch. Because subagent worktrees branch from the default branch on the remote, a worker will not see an uncommitted regression test; the prompt therefore carries the test's content and path so the worker recreates it. The worker must leave its worktree clean (it reverts every change, including the recreated test, before returning), because a worktree with changes survives the agent, and the owner's rule is that nothing survives the step. It returns evidence and, if confirmed, a proposed minimal patch as text; it never merges.

The judge is the main session. It accepts a confirmation only when the returned evidence shows the predicted observation and the hypothesis explains the whole brief; two confirmations mean two contributing causes and one more discriminating experiment; no confirmation means the refutations go into the ledger and the escalation ladder continues. After the fan-out, `git worktree list` must show one entry and `git branch --list 'worktree-*'` must be empty; anything else is removed with `git worktree remove --force` and `git branch -D` before the next step.

The Workflow tool is not needed for this. It is the right tool when the hypotheses number more than five or the sweep is codebase-wide (the docs' flaky-test sweep), and a skill may instruct it, but for the bug shape the Agent tool with two to four workers is smaller and leaves the judge in the main session where the ledger is.

## 5. Conditionals by project shape

Greenfield app (the fashion iOS app). The bug hunt appears as the failure-investigation sub-loop whenever an adversarial or vision verification step fails and the change under test does not explain it. Intake is internal: the failing verification is the brief, and "since-when" and bisection do not apply because there is no history worth bisecting; the differential is drawn against the spec instead. UI bugs dominate and use the iOS Simulator accessibility tree and screenshots, with a fresh agent doing the visual comparison. Verified facts about the platform (Cloudflare limits, Swift concurrency behaviour) go to STATE from the first hunt onward, which is how the greenfield project's STATE fills with facts rather than guesses.

Deep bug hunt (this shape). The runbook is the entire plan. No specification or architecture phase, one working file, `/goal` set to the completion condition in section 9, and the escalation ladder as the only branching. Sub-conditionals: intermittent means amplify before diagnosing; production-only means the five-axis environment diff comes before any code hypothesis and live proof is mandatory; UI means tree-plus-screenshot repro and a fresh visual checker; performance means a budget and a profile before a hypothesis; a security-flavoured symptom (authorization, injection, secrets) means routing the hunt's diagnosis and workers to Opus explicitly, because Fable's classifiers may refuse and the fallback would otherwise be silent; a design-flaw cause means re-classification.

Feature on an existing product (the dashboard). Bugs found while implementing follow the runbook without the intake lookups, since the context is already loaded. A pre-existing bug discovered in adjacent code is recorded in STATE's open failures with a repro path and is not fixed inline unless it blocks the feature; scope discipline matters more than opportunism here. The second-time rule applies across the feature's own fixes: two workarounds in the same area during one feature is a diagnosis failure, not bad luck.

Migration or consolidation (the AI gateway move). Almost every bug is a behaviour difference between old and new, so the reproduction is a differential test that runs the same input through both and diffs the output, and the class fix is usually a parity suite rather than a single regression test. Bisection runs over the migration's own commits. The harness-fidelity risk is at its highest here because a migration creates new shims by definition; the intake's "where is it kinder" line should be answered for every double the new code introduces, and live proof means the new path serving real traffic with the old path's result as the oracle.

Research plus website. Bugs are build, link, layout, and content defects. Reproduction is a Playwright snapshot, a Lighthouse run, or a link checker; the ledger collapses to one row for a one-line CSS fix, but the regression check stays (the link checker or visual snapshot in the build), and the visual confirmation is still done by a fresh agent reading the screenshot.

Ops and incident. The runbook gains a prelude: stop the bleeding with a reversible mitigation recorded with its undo, then hunt the cause with the incident's own telemetry as the evidence. Live proof is the only proof that counts, and the post-mortem's "why not caught" line becomes the alerting or health-check change. The owner's mornings are this shape: the doctor and product commitments that now page a missed morning were the class fix.

Data pipeline. Reproduction is a captured input slice replayed through the stage in isolation; hypotheses lean toward ordering, idempotency, replay, and partial failure; the class fix is often a replay or determinism test (the Workflows lesson). CLI tool. The repro is a shell script with the exact invocation and expected output, kept as a golden test. Library or SDK. The repro is a consumer-side test added to the public suite, and the post-mortem names the changelog entry.

## 6. Model and effort assignment

Diagnosis in the main session: Fable, `high` effort, escalating to `xhigh` when the ledger has three refuted rows. The reasons are the guide's statement that Fable's bug-finding recall and repository-history search exceed Opus 4.8's, the corrected cost ratio (two times, less on cached context), and the fact that Fable is already the orchestrator for every other shape, so nothing new is spawned for a bug. `max` is not a default; the docs say it is prone to overthinking, and a debugging session that overthinks writes rationalizations instead of experiments.

Hypothesis workers and the second opinion: the predefined `debugger` subagent on Opus at `high`. The work is hard but bounded (one hypothesis, one experiment, one verdict), the different model gives the second opinion genuinely different priors, and Opus is the documented fallback if a security-flavoured hypothesis trips a classifier. The last escalation before re-classification is a one-off Fable `xhigh` fresh-context run of the same prompt.

The verifier: Opus at `high`, fresh context, tools included. Not Sonnet, because refuting a root cause with adjacent inputs is judgment work; not the main session, for the structural reason the post and the docs agree on. The verifier prompt is given in section 9 and could be folded into the general adversarial-verification agent another report specifies, with the bug-specific steps (pre-fix reproduction first) kept intact.

Sonnet, `medium` or `high`: log sweeps that summarize thousands of lines into candidate anomalies; the five-axis environment diff (list bindings, variables, versions on each side); running the stress loop and reporting the rate; grepping for siblings of a fixed construct; inserting tagged instrumentation under exact instructions. Sonnet at `low` as a classifier has no role in this shape; the only classification the hunt needs (does this diff contain a symptom patch) is a judgment the Opus verifier already makes with the diff in front of it. Haiku appears nowhere except as the `/goal` evaluator that Claude Code supplies, and the skill treats that evaluator as a loop-holder, never as a verifier.

Isolation. Workers that edit files run with `isolation: worktree` and must end clean; the verifier reproduces the pre-fix failure in a worktree it creates and removes itself. Nothing is merged from any worktree. The debugger does not use the `memory` field: the procedural lessons belong in the skill's references file where they are reviewed and pruned, and a `.claude/agent-memory/` directory would be new files in the owner's repos.

Draft `~/.claude/agents/debugger.md`:

```markdown
---
name: debugger
description: Tests one named hypothesis about a bug in an isolated checkout, or gives a fresh second opinion on a stalled hunt. Give it the bug brief, the repro command, and either one hypothesis with its prediction or the ledger so far. Returns evidence and a proposed patch as text; never edits the main checkout.
model: opus
effort: high
tools: Read, Grep, Glob, Bash, Edit, Write, WebFetch
isolation: worktree
maxTurns: 40
color: orange
---

You are testing a hypothesis about a bug, or giving a second opinion on a hunt that has stalled. You work in an isolated copy of the repository and you leave it exactly as you found it.

You will receive a bug brief, a reproduction command, and one of two things: a single hypothesis with its prediction, or a hypothesis ledger of what has already been tried. You will not receive the conversation that produced them; that is deliberate.

Hypothesis mode. First run the reproduction command and confirm the failure happens here; if it does not, stop and report exactly what you observed and how this environment differs from the brief. If the prompt includes a regression test's content and path, write it first. Then run the one experiment that tests the prediction you were given, changing one thing at a time. Any instrumentation you add carries the marker HUNT-<slug>. Report confirmed only if you observed the predicted result; report partial if the prediction held but the hypothesis does not explain the brief's frequency, environment, or since-when; otherwise report refuted, with what you saw instead. If confirmed, propose the smallest patch that removes the cause, as a diff in your report, not as an edit you keep.

Second-opinion mode. Read the brief and the ledger, then write your own ranked list of three to five candidate causes across different layers (data, logic, timing, configuration, platform, stale artifacts), noting which the ledger has already refuted. Name the single experiment that best discriminates between your top candidates, and run it if it fits in this checkout.

Before you finish: revert every change you made, including any test you wrote and all HUNT- markers, so the checkout is clean (git status shows nothing). Audit each claim in your report against a tool result from this session; if something is not verified, say so. Do not fix the bug in place, do not tidy surrounding code, and do not refactor.

Report in this shape: Reproduction here (yes/no, output). Hypothesis. Prediction. Experiment (commands). Observed (output). Verdict (confirmed / partial / refuted / inconclusive) with one sentence. Proposed patch (diff or none). Checkout clean (git status output).
```

## 7. Failure modes and anti-patterns

Fixing without reproducing. The skill gates edits to non-test source on the "Repro cmd" line being a command that fails now. Prevention is structural: the ledger has no row to attach a fix to until the reproduction exists.

Changing many things at once. One variable per experiment in the ledger, and a fix diff that must be explainable by the confirmed hypothesis; the verifier lists unexplained changes and fails the verdict on them.

Deleting or loosening the failing test. The verifier diffs test files and requires a ledger row for any removed or weakened assertion. Skipped tests and `.only`/`.skip`/`#[ignore]` additions are diff smells.

Declaring fixed when the symptom stopped. Completion requires the pre-fix failure, the post-fix pass, and a cause that explains all four brief fields. A symptom that stopped without a cause is status Partial and goes to open failures, in those words.

Skipping the lesson. The post-mortem is in the `/goal` completion condition, so the loop does not close without it.

Mirage completion specific to this shape, with the prevention the skill applies: green tests on a harness kinder than production (the D1 incident; prevented by the intake harness line and the class-fix question); a test asserting the wrong layer (the renderer, not the outbound message; prevented by the wide-plus-narrow test rule); a fake whose shape was invented rather than captured (the id-parse heuristic; prevented by requiring fixtures to be captured from the real system when a platform response is involved); a fix that never ran where the symptom lives (the stale companion binary; prevented by the deploy-identity check in live proof); a deploy to the wrong target (the frozen v1 worker; same check); and fixing the trigger instead of the wedge (the `cpu_ms` raise; prevented by the "does this explain everything" test and by re-classification).

Model-behaviour failures documented in the Fable guide and mitigated with its own prompts: fabricated status reports (the "audit each claim against a tool result" instruction goes into every worker and verifier prompt); ending a turn on a promise ("I'll now run the suite" without running it; the autonomous-operation reminder); unrequested tidying at high effort (the "a bug fix doesn't need surrounding cleanup" line); and acting on a pattern match ("a signal that pattern-matches to a known failure may have a different cause"), which is the specific danger of the consult stage: a LESSONS entry is a high-prior hypothesis, never a shortcut past the experiment.

Harness-specific traps. The `/goal` evaluator only sees the transcript, so the maker must surface test output and the verifier's verdict in the conversation, not only in files. Subagent worktrees with changes are kept until a periodic sweep; the skill checks `git worktree list` after every fan-out. Prompts that tell an agent to "explain your reasoning" or "show your thinking" can trip Fable's reasoning-extraction refusal; the ledger asks for predictions and observations, which are work products, not reasoning transcripts. `/debug` is Claude Code's self-diagnosis skill and is never the right tool for the user's bug.

## 8. Open questions and trade-offs

Where the working file lives. In the skill's run directory (recommended) it never pollutes the owner's repo but is invisible to a future session that opens the repo cold; in the repo it is visible but is exactly the stray artifact he does not want. Recommendation: run directory, with the durable content (facts, open failures, lessons) written into the repo's STATE and LESSONS, which are already committed files.

Committing the failing test before the fix. The owner commits straight to main, so a red test commit would break main between two commits. Recommendation: one commit containing test and fix, with the pre-fix failure preserved as evidence in the ledger and reproduced by the verifier at the recorded pre-fix hash. The cost is that `git bisect` in the far future cannot see the test alone; that is acceptable.

Second opinion on Opus or Fable. Opus gives model diversity and costs half; Fable has the higher recall. Recommendation: Opus first, Fable `xhigh` as the last step before re-classification; measure over ten hunts which one actually breaks stalls and adjust.

Whether the verifier should be this shape's own agent or the general adversarial verifier. Recommendation: one general verifier agent with a bug-specific preamble, because the owner's culture already has one severe-review role and two would drift apart. The bug preamble must keep "reproduce the pre-fix failure first" as step one.

Agent memory versus the references file for procedural lessons. Recommendation: references file, reviewed by the verifier, pruned at eighty lines. Revisit if the owner adopts agent memory elsewhere.

Agent tool versus Workflow tool for fan-out. Recommendation: Agent tool for two to four workers; Workflow tool only when the skill is explicitly sweeping a codebase for a class of bug.

How far to scale down. The invariants (failing repro first, independent verifier after, one-sentence cause, post-mortem) cost perhaps five minutes on a trivial bug; everything else is skipped when the ledger has one confirmed row. If in practice the verifier is pure overhead on trivial fixes, the threshold for skipping it should be a single-file, single-line diff with a narrow regression test, and nothing looser.

## 9. Skill text candidates

Passage 1, the runbook for SKILL.md's bug-hunt section (58 lines):

```markdown
## Shape: bug hunt

Hold three invariants; let everything else scale with the bug.
1. No fix before a reproduction that runs and fails.
2. No completion without a fresh-context verifier that reproduced the pre-fix failure.
3. No completion without a one-sentence cause that explains symptom, frequency, environment, and since-when, plus the harness taught the constraint that let it through.

Intake. Extract symptom, frequency, environment, since-when, impact, trigger, evidence, prior history. Look up, do not ask: STATE, LESSONS, references/bug-hunt-lessons.md (matches are hypotheses, not conclusions); load the system's own tools; git log for the area; related issues; current tests and every test double, with one line each on where it is kinder than production; the identity of the build actually running. Write the brief at the top of HUNT.md in the run directory. Record the pre-fix commit hash.

Reproduce. Produce a command that exits non-zero for the brief's reason, then a test in the project's framework named for the bug with a CLAIM comment. Deterministic: lowest layer that shows it; keep a wide test too when the symptom is only visible end to end. Intermittent: measure the rate over 100 runs, then amplify (seed, load, timing injection, deterministic schedulers) until reliable; under one in ten, use differential logging. Production-only: diff configuration, data shape, runtime, artifact staleness, and harness before code; teach the local harness the constraint or reproduce live read-only with a captured input. UI: screenshot plus accessibility tree, assert on the tree. Performance: write the budget, profile, assert a count or threshold that fails now. If no test is possible, a scripted probe with pasted output is the repro and the ladder caps at Local Proof.

Diagnose. Keep a ledger: hypothesis, prediction written before the experiment, experiment, result, status. Start with three to five candidates across layers (data, logic, timing, config, platform, stale artifact). One variable per experiment. Confirmed means the prediction was observed and the hypothesis explains every brief field; otherwise partial. Bisect in a throwaway worktree with `git bisect run` and exit 125 for unbuildable commits, then remove the worktree in the same step. Tag instrumentation HUNT-<slug>; remove it before committing. Probe or read the platform instead of guessing about it. After three refuted rows: second opinion from the debugger agent with brief, ledger, and repro only. After that: parallel workers if substantial independent hypotheses remain, else re-classify (design flaw → feature or migration shape; wrong expectation → report and stop). Bound the hunt with the /goal turn clause.

Fix. Remove the cause with the smallest change that does; ship the small correct fix and re-classify the rest if the proper fix is large. No retry, sleep, timeout, swallow, null check, default, or skip without a ledger row proving the cause is external. Fix the class: grep for siblings; teach the shim the production constraint; enforce it in the code under test; add the test that generates the violating shape. If STATE records a prior fix here, or you are about to apply the same workaround twice, stop and re-diagnose. No surrounding cleanup.

Verify. Regression test stays. `git diff | grep HUNT-` is empty. Demonstrate the test fails at the pre-fix hash. Run the project's full gates. Run the severe-testing skill on the fixed area as post-fix verification. Spawn the verifier (Opus, fresh context) with brief, ledger, diff, test name, repro, pre-fix hash; it reproduces the pre-fix failure first, confirms the fix, tries two adjacent inputs, checks siblings and harness, scans for symptom-patch shapes, returns the verdict template. FAIL becomes the next ledger row. Production bug: deploy through the system's tools, confirm the deployed identity, reproduce the original condition live, record the request id. Never "when the cron runs"; if the condition cannot be forced, status is Local Proof and the pending check is named.

Close. Post-mortem in HUNT.md (twelve lines). Verified facts → STATE. General rule → LESSONS. Procedural lesson → references/bug-hunt-lessons.md only if it changes the next hunt and the verifier agrees. One commit on main with test and fix. `git worktree list` shows one entry. Surface test output and verdict in the conversation for the /goal evaluator.
```

Passage 2, the `/goal` condition to set at the start of a bug hunt:

```text
/goal The bug in HUNT.md is closed: a regression test named for it exists and passes; the ledger shows it failing at the recorded pre-fix commit; the project's full test, lint, and typecheck gates pass; a fresh-context verifier returned PASS with its verdict pasted in the conversation; the post-mortem states a one-sentence cause explaining symptom, frequency, environment, and since-when; STATE and LESSONS are updated; git worktree list shows one entry; and for a production bug the live reproduction passed with a recorded id, or the report says Local Proof and names the pending check. Or stop after 60 turns and write the open-failure handoff into STATE.
```

Passage 3, the brief template (section 4.1 block).

Passage 4, the reproduction gate:

```markdown
Do not edit non-test source until HUNT.md's "Repro cmd" names a command that exits non-zero now, for the reason in the brief. Turn it into a test in the project's framework, named for the bug, with a CLAIM comment stating what the code claims and what this test refutes. If a framework test is impossible, a scripted probe with its output pasted into the ledger is the repro, and the status ladder caps at Local Proof until a live check exists.
```

Passage 5, the flake protocol:

```markdown
For an intermittent failure, measure before you diagnose: run it 100 times and record pass and fail counts. Then amplify until it fails reliably, cheapest first: fix and print the random seed; run under load or in parallel; inject a sleep, yield, or paused clock at the suspected point; use the language's deterministic scheduler tooling; shuffle test order to expose order dependence. Log on failure only, with a correlation id. If you cannot get past about one failure in ten, diagnose by differential logging across many runs, not by stepping through one.
```

Passage 6, the production-only protocol:

```markdown
When the bug appears only in one environment, diff the environments before you touch code, on five axes: configuration (variables, secrets present or absent, flags, bindings, the exact deploy target name); data shape (counts, sizes, nulls, unicode, cardinality past a platform limit); runtime (the real engine against the local substitute, a daemon against a shell); artifact staleness (which copy is actually running: cache, installed binary, pinned copy, in-memory definitions); and the harness (every double, and where it is kinder than the real thing). Teach the local harness the constraint you find, or reproduce live and read-only with a captured input.
```

Passage 7, the ledger rule:

```markdown
The ledger has one hard rule: write the prediction before you run the experiment. A row is hypothesis, prediction ("if true, doing X shows Y"), experiment, result, status. Change one thing per experiment. Mark confirmed only when the prediction was observed and the hypothesis also explains why the bug started when it started and why it happens here and not there; otherwise mark partial and keep going. A bisected commit is a new hypothesis, not a cause.
```

Passage 8, the bisect recipe (section 4.3 block, with the sentence "the checkout you are working in never moves; the worktree is removed in the same step").

Passage 9, the fix rules:

```markdown
The fix removes the confirmed cause with the smallest change that does so. A retry, sleep, widened timeout, swallowed error, null check, default value, or skipped test is a symptom patch unless a ledger row proves the cause is genuinely external and this is its correct handling. After the instance: grep for siblings and fix or clear them; teach the test shim the production constraint; enforce the constraint in the code under test; add the test that generates the violating shape. A bug fix does not need surrounding cleanup. If STATE records an earlier fix for this symptom or area, treat its cause as suspect. If you are about to apply the same workaround a second time, stop: the first diagnosis was wrong.
```

Passage 10, the verifier preamble (to fold into the general verifier agent):

```markdown
You are verifying a bug fix you did not write. You have the brief, the ledger, the diff, the regression test name, the repro command, and the pre-fix commit hash. Do these in order and paste the output of each: create a throwaway worktree at the pre-fix hash and reproduce the original failure there, then remove the worktree; run the regression test and the full gates on the fix; say whether the stated cause explains symptom, frequency, environment, and since-when; try at least two adjacent inputs or conditions the fix was not written for; check that siblings were handled and that the harness now enforces the production constraint; list any retry, sleep, timeout, swallow, null check, default, skip, or loosened assertion in the diff, and any change the cause does not explain. Return the verdict template. Audit every claim against a tool result from this session. You are not asked to praise the fix; you are asked to break it.
```

Passage 11, the verdict template (section 4.5 block).

Passage 12, the parallel fan-out rule:

```markdown
Fan out only when two or more open hypotheses each need a substantial, independent experiment. Launch one debugger worker per hypothesis with the Agent tool in the background and `isolation: worktree`, giving each the brief, one hypothesis with its prediction, the repro command, and the regression test's path and content (the worktree branches from the default branch and will not have your uncommitted test). Workers return evidence and a proposed patch as text and leave their worktree clean. You judge: a confirmation needs the predicted observation and a hypothesis that explains the whole brief. Afterwards `git worktree list` shows one entry and `git branch --list 'worktree-*'` is empty; remove anything else before continuing.
```

Passage 13, the post-mortem template (section 4.6 block).

Passage 14, routing knowledge:

```markdown
Three homes, kept short. STATE (in the repo): verified facts about this system with how they were verified, and open failures with rate, best hypothesis, and repro path. LESSONS: the general rule without this repo's names. references/bug-hunt-lessons.md (in this skill): a procedural lesson only if it changes how the next hunt is run and the verifier agrees it is new; prune past eighty lines. A consulted rule is a hypothesis with a high prior; it still gets an experiment.
```

Passage 15, the anti-pattern list for the skill's known-failure-modes section:

```markdown
Known ways a bug hunt lies to you: fixing before reproducing; changing several things in one experiment; deleting or loosening the failing test; calling it fixed because the symptom stopped; skipping the post-mortem; trusting a green suite whose fakes are kinder than production; asserting on the wrong layer (the renderer, not the message that was sent); fixtures with invented shapes instead of captured ones; a fix that never reached the artifact actually running; a deploy to the wrong target; fixing the trigger instead of the wedge; reaching for /debug (it debugs Claude Code, not your code); and reporting that the live check will happen when the schedule fires.
```

Passage 16, the debugger agent file (section 6 block, shipped to `~/.claude/agents/debugger.md`).

Passage 17, conditionals in one paragraph for the classifier:

```markdown
If the failure is intermittent, amplify before diagnosing. If it appears in one environment only, diff the five axes before code and require live proof. If it is visual, reproduce with screenshot plus accessibility tree and have a fresh agent do the visual comparison. If it is performance, write the budget and profile first. If it smells of security (authorization, injection, secrets), run diagnosis and workers on Opus explicitly. If the cause is a design flaw, ship the small correct fix and re-classify the rest. If the expectation was wrong, report with evidence and stop. If the shape is a migration, the repro is a differential test against the old system and the class fix is a parity suite. If the shape is an incident, mitigate with an undo first, then hunt.
```

The `references/bug-hunt.md` candidate is passages 3 through 15 in that order, with section 4.2 through 4.6 of this report as the connecting prose where the coordinator wants explanation rather than instruction.
