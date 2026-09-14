# 07 · Independent verification and adversarial review architecture

Researcher report for the `/drive` skill. Component: the maker/checker split, review layers, loop control, evidence standards, rubric design, grader placement, and the anti-patterns that produce mirage completion. Written 2026-09-14 against live docs and the primary sources named in the task.

Throughout, **verified** means I read the page today and cite it; **source claim** means a named source says it and I could not independently confirm it; **opinion** is mine and argued.

---

## 1. Executive opinion

The verification component has one job that everything else serves: the agent that wrote the work must never be the agent that decides the work is done, and the deciding agent must produce evidence rather than an opinion. The evidence for the split is real but thinner than the post implies. It rests on one Anthropic engineering post (Rajasekaran, March 2026) with qualitative results on Opus 4.5 and 4.6, one Anthropic engineer's X article (Lance Martin, June 2026) whose Parameter Golf numbers compare two models rather than verifier against self-critique, and the product decisions embodied in Managed Agents Outcomes and `/goal`. What the sources agree on, and what matters most for the skill, is that separation alone does not cure leniency: Rajasekaran watched a separate evaluator identify real issues and then talk itself into approving anyway.

So the skill needs three structural defenses, not one. First, a fresh-context verifier with read-only tools that receives artifacts, claims, and rubric but never the maker's account of them. Second, a verdict schema that is invalid without commands run and refutations attempted, so a rubber stamp is rejected as malformed rather than accepted as a pass. Third, a bounded loop with severity thresholds so the verifier can neither wave work through nor nitpick forever. Deterministic gates (build, typecheck, tests) run before any model review, because paying a model to review red code is waste.

`/goal`'s built-in evaluator sees only the transcript and cannot run tools, so it must never be the grader of record; it is a loop driver that reads verdicts the orchestrator prints. Sonnet at low effort is the right grader for rubric conformance and checklist work and the wrong verifier for correctness, security, and UI judgment, where a verifier weaker than the maker rubber-stamps by default. Proof bundles under a project directory make every STATUS claim checkable, and the ground-truth order (code and tests, then proofs, then STATUS, then prose) is the order the verifier reads in, so disagreement between layers is itself a finding.

---

## 2. What the post says, and a critique

**Step 05 (/goal vs Outcomes).** The post says both share one shape: "an independent grader checks the work, a not-met verdict starts the next iteration," and that "the agent that wrote the code is not the agent that grades it." The shape is right; the independence claim is overstated for `/goal`. Verified: `/goal` is a wrapper around a prompt-based Stop hook; after each turn Claude Code "sends the condition and the conversation so far" to the small fast model (Haiku by default), and that model "does not call tools, so it can only judge what Claude has already surfaced in the conversation." It is a different model instance, but it grades the maker's own narration of success. That is a weaker form of independence than a verifier that runs the tests itself. Outcomes is closer to the post's description: the grader "uses a separate context window to avoid being influenced by the main agent's implementation choices," with `max_iterations` default 3 and maximum 20. The docs do not state the grader's model or tools, and its reasoning is explicitly opaque ("you see that it's working, not what it's thinking"). Third-party write-ups claiming the grader has "the same model and tools as the writer" are source claims I could not confirm.

**Step 06 (verifier beats self-critique).** The Rajasekaran post exists and says what the post says it says, but its most useful lessons are the ones the post drops. Verified quotes: "When asked to evaluate work they've produced, agents tend to respond by confidently praising the work—even when, to a human observer, the quality is obviously mediocre." Then: "Separating the agent doing the work from the agent judging it proves to be a strong lever," immediately followed by "The separation doesn't immediately eliminate that leniency on its own; the evaluator is still an LLM that is inclined to be generous towards LLM-generated outputs. But tuning a standalone evaluator to be skeptical turns out to be far more tractable than making a generator critical of its own work." And on the QA role: "Out of the box, Claude is a poor QA agent. In early runs, I watched it identify legitimate issues, then talk itself into deciding they weren't a big deal and approve the work anyway. It also tended to test superficially, rather than probing edge cases." The evaluator only became useful after calibration with few-shot score breakdowns, hard per-criterion thresholds ("if any one fell below it, the sprint failed"), and live interaction via Playwright rather than reading code. The evidence is qualitative: the author's own judgment of outputs, no win rates or human ratings, on Opus 4.5 and 4.6, not Fable. His closing caveat matters for the skill's conditionals: "the evaluator is not a fixed yes-or-no decision. It is worth the cost when the task sits beyond what the current model does reliably solo."

The "Claude Code team confirmed this empirically" line traces to Lance Martin's X article, one Anthropic MTS writing in the first person plural. The sentence is real: "We've found that a verifier sub-agent tends to outperform self-critique with Fable 5, because grading is done in an independent context window." No ablation is published. The Parameter Golf paragraph conflates two things: the roughly 6x improvement is Fable 5 versus Opus 4.7, and both ran under the same Outcomes grader with nine checkable criteria. It says nothing about verifier versus self-critique on the same model. "Without the verifier, the same model has nothing forcing it past the first 'good enough'" is a plausible opinion presented as a result.

**Step 04 (Haiku for graders, "the verifier role Anthropic explicitly recommends").** I found no Anthropic recommendation of Haiku as a verifier. Rajasekaran used the same tier for generator and evaluator. The Workflow authoring reference says to use `low` effort "for cheap mechanical stages and higher tiers only for the hardest verify/judge stages," which places judging among the expensive stages, not the cheap ones. The owner's preference for Sonnet at low effort over Haiku is at least as defensible and, at Sonnet 5's $2/$10 per million versus Haiku 4.5's $1/$5, costs pennies more per verdict.

**Step 07 (adversarial verification).** Verified in the Workflow authoring reference, with two details the post omits: verifiers are told "Default to refuted=true if uncertain," and the pattern uses majority vote across N independent skeptics. The reference also documents "perspective-diverse verify" (distinct lenses beat N identical refuters) and a "completeness critic" stage. Both belong in the skill.

**Step 08 (worktrees: "Maker writes in worktree A; verifier reads in worktree B").** Wrong for Claude Code. Verified: `isolation: worktree` gives the subagent "an isolated copy of the repository branched by default from your default branch rather than the parent session's HEAD." A verifier in its own worktree would see main, not the maker's uncommitted work. The verifier must read the maker's tree, either the canonical checkout or the maker's worktree path, with read-only tools.

**Step 13 (vision verify by reading a screenshot).** Directionally right, but screenshot-reading alone is the "superficial testing" Rajasekaran warned about. His evaluator "would navigate the page on its own, screenshotting and carefully studying the implementation" and in the full-stack case "click through the running application the way a user would." A UI verifier must interact, not only look.

**What the post gets right that the skill should keep.** The structural principle (different agent, independent context, sees artifact and rubric). The hard iteration bound. The need for the loop to exit on a verdict rather than on the maker's sense of "handled enough." The vision step for visual work.

---

## 3. Verified facts

Primary sources:

- Rajasekaran, "Harness design for long-running application development," Anthropic engineering, published 2026-03-24. https://www.anthropic.com/engineering/harness-design-long-running-apps: self-praise finding; separation as "strong lever" that does not remove leniency; evaluator tuning more tractable than self-criticism; Claude "a poor QA agent" out of the box; evaluator drove the live app via Playwright MCP; hard thresholds per criterion; sprint contracts agreed before code; agents communicated via files; V2 moved the evaluator to a single end-of-run pass; models Opus 4.5 then 4.6; evidence qualitative.
- Martin, "Designing loops with Fable 5," X article, June 2026. https://x.com/RLanceMartin/article/2064397389189071163 (readable clipping: https://github.com/lchesupercool/ob-clippings/blob/main/2026-06/2026-06-10-designing-loops-with-fable-5.md): the verifier-sub-agent sentence; "Outcomes in CMA handles this by spawning a grader sub-agent for you"; Parameter Golf rubric of nine checkable criteria; Fable 5 vs Opus 4.7 comparison under the same grader.
- Managed Agents, "Define outcomes." https://platform.claude.com/docs/en/managed-agents/define-outcomes: rubric required, markdown, "explicit, gradeable criteria"; grader in separate context window; results `satisfied | needs_revision | max_iterations_reached | failed | interrupted`; `max_iterations` default 3, max 20; grader reasoning opaque; "If you don't have a rubric on hand, try giving Claude an example of a known-good artifact and asking it to analyze what makes that content good, then turn that analysis into a rubric."

Claude Code harness:

- `/goal`. https://code.claude.com/docs/en/goal: prompt-based Stop hook underneath; evaluator gets condition plus conversation, no tools; verdicts met / not yet met / impossible; write conditions "as something Claude's own output can demonstrate"; bound with "or stop after N turns"; background subagents defer evaluation, check-ins after 30 minutes; loop halts with a warning after several turns with no tool use; evaluator model changed only via `ANTHROPIC_DEFAULT_HAIKU_MODEL`, which also changes the `haiku` alias and all background functionality.
- Hooks guide. https://code.claude.com/docs/en/hooks-guide: prompt hooks default to Haiku, "You can specify a different model with the `model` field"; on `Stop` an `ok: false` reason is fed back so Claude keeps working, `impossible: true` ends the turn; agent-based hooks (experimental) spawn a subagent with tools, default 60 s timeout, up to 50 tool-use turns, documented example "Verify that all unit tests pass. Run the test suite and check the results."; Stop hook block cap is eight consecutive blocks without progress, raised via `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`; exit code 2 blocks and stderr is fed to Claude on PreToolUse.
- Subagents. https://code.claude.com/docs/en/sub-agents: fresh isolated context ("doesn't see your conversation history, the skills you've already invoked, or the files Claude has already read"); forks inherit everything and drop input isolation; `tools` allowlist and `disallowedTools` denylist (a specifier such as `Bash(git push *)` removes the whole tool); `model`, `effort`, `maxTurns` (returns partial, resumable), `skills` preload injects full content, `memory`, `hooks` in frontmatter; `isolation: worktree` branches from the default branch, cleaned up only if unchanged, git redirection into the main checkout blocked.
- Dynamic workflows. https://code.claude.com/docs/en/workflows and the `/workflow-authoring` bundled reference (loaded this session): `agent(prompt, {schema, model, effort, isolation, agentType})` returns validated JSON when `schema` is given (five validation retries); adversarial verify, perspective-diverse verify, judge panel, completeness critic, loop-until-dry, "no silent caps"; `Date.now()` and `Math.random()` throw; opt-in only (`ultracode`, "use a workflow," or a skill instruction); 16 concurrent agents, 1,000 per run.
- Skills. https://code.claude.com/docs/en/skills: `context: fork` plus `agent:` runs a skill in an isolated subagent that "doesn't see your conversation history"; `allowed-tools` / `disallowed-tools` scoped to the invoking turn; after compaction each invoked skill is re-attached at its first 5,000 tokens within a shared 25,000-token budget.
- `/code-review`. https://code.claude.com/docs/en/code-review: runs as a background forked subagent; "At `low` and `medium`, the review reports only the findings it's most confident in, so you see fewer false positives; `high` through `max` broaden coverage and may include findings the review is less sure about"; `--fix` applies findings; does not read `REVIEW.md`; `/simplify` is a separate cleanup-only review that applies fixes without hunting bugs. The GitHub Code Review product describes "a verification step [that] checks candidates against actual code behavior to filter out false positives" and recommends a verification bar such as "behavior claims need a `file:line` citation in the source, not an inference from naming" and a re-review convergence rule "after the first review, suppress new nits and post Important findings only."
- Ultrareview. https://code.claude.com/docs/en/ultrareview: `/code-review ultra`; cloud fleet; "every reported finding is independently reproduced and verified"; 5 to 10 minutes; $5 to $25 in usage credits after three free runs on Pro/Max; requires claude.ai auth; never self-started by Claude; `claude ultrareview --json` blocks and prints findings.
- Security. https://code.claude.com/docs/en/security-guidance: `/security-review` is a "one-time security pass on the current branch"; the security-guidance plugin's model reviews run "as a separate Claude call with a fresh context and a security-focused prompt: the reviewer starts from the diff, has no investment in the original approach, and is instructed only to find problems"; Claude Security plugin is a multi-agent scan "with independently reviewed findings."
- Model config. https://code.claude.com/docs/en/model-config: on the Anthropic API today the `sonnet` alias resolves to Sonnet 5 and `opus` to Opus 5, `fable` to Fable 5.1; effort levels `low|medium|high|xhigh|max` on Fable 5.x, Opus 4.7+, Sonnet 5; frontmatter `effort` overrides the session level for that subagent or skill.
- Pricing. https://platform.claude.com/docs/en/about-claude/pricing: Fable 5.1 $10 / $50 per MTok (cache hit $0.25); Opus 4.8 and Opus 5 $5 / $25; Sonnet 5 $2 / $10 (introductory price made permanent); Sonnet 4.6 $3 / $15; Haiku 4.5 $1 / $5. The page lists no "Sonnet 4.8". A grader that reads a 20k-token bundle and writes a 1k-token verdict costs about $0.05 on Sonnet 5 and $0.025 on Haiku 4.5.

Local:

- Severe-testing skill at `/Users/chabotc/.claude/skills/severe-testing/SKILL.md` (read in full). Workflow: name the claim, list refutations, choose oracles, attack the input space, add malicious breakage tests, run the strongest checks, report evidence. Confidence scale 0 / 25 / 50 / 75 / 100 with reporting threshold ≥50 and a bar of ≥75 for regression tests ("a regression test that does not actually fail on the broken code is not evidence"). False-positive suppression list. Severity ladder weak / moderate / strong / severe. Claim block format (CLAIM, PRECONDITIONS, POSTCONDITIONS, ORACLE, SEVERITY). It writes tests; it is not read-only.
- Arcwell culture memory (`~/.claude/projects/-Users-chabotc-Projects-arcwell/memory/arcwell-repo-culture.md`): proof packets under `.arcwell-dev/proofs/<name>/artifacts/proof-packet.json` plus a "mirage check"; status ladder; precedence rule; the sql.js shim incident.

---

## 4. Detailed spec

### 4.1 Roles

The skill needs more than two roles because "verifier" hides three different jobs: judging, attacking, and adjudicating. Keep them separate so that each has the minimum tool surface for its job.

| Role | Writes | Runs | Sees | Purpose |
|---|---|---|---|---|
| Maker | production code, tests it chooses | anything | spec, claims, its own context | builds the thing |
| Severe tester | test files and proof artifacts only | tests, fixtures, sandboxes | spec, claims, code (not maker's transcript) | writes tests that try to refute each claim |
| Verifier | nothing in the repo | tests, builds, curl, simulator, browser | handoff bundle (see 4.2) | decides holds / refuted per claim, with evidence |
| Conformance grader | nothing | nothing beyond reading | spec, rubric, diff, proofs | cheap check that the right thing was built |
| UI verifier | nothing | simulator / browser tools | goal, design tokens, screens, previous screenshots | interacts and judges the rendered UI |
| Arbiter | nothing | may re-run | both sides' evidence, the artifact | rules once on a maker/verifier dispute |
| Final auditor | nothing | may re-run proofs | STATUS, proofs, code | go/no-go hunt for mirage before Done |

A single agent must never hold two of these roles for the same claim in the same run. A fresh subagent per verification round is the rule, never a fork: forks inherit the full conversation and destroy the isolation that is the whole point.

### 4.2 The handoff contract

The orchestrator builds the verifier's prompt from files, using a fixed template, and never from the maker's final message. This is the single most important enforcement point, because the leak the post warns about (verifier sees maker's reasoning) almost always happens through the orchestrator pasting "the maker says it fixed X" into the prompt.

The verifier receives:

- The goal sentence from intake and the relevant spec section(s), by path.
- The claims file for this unit of work: each behavioral claim as written before coding (claim, preconditions, postconditions, oracle), by path.
- The rubric for this shape (see 4.8), frozen at handoff.
- The scope: a git range (`<base>..<head>`) or "working tree at `<path>`", and the list of files touched.
- The project's validation surface: the exact commands for build, typecheck, lint, tests, and any live-proof command, taken from the project's STATUS or CLAUDE.md, not from the maker.
- Paths to evidence the maker or severe tester produced (test files, screenshots, logs), with the instruction to treat them as inputs to re-run, not as proof.
- On a re-verify: the previous verdict's `gaps` array (ids, locations, repro commands), so the verifier checks closure. Not the maker's description of what it changed.

The verifier must not receive:

- The maker's transcript, summary, self-assessment, or "tests pass" claim.
- The orchestrator's opinion of quality or urgency ("this is probably fine," "we are short on turns").
- Any instruction to be lenient, quick, or to focus on confirming.

Handoff file template, written by the orchestrator to `.drive/handoffs/<unit-id>.md`:

```markdown
# Handoff · <unit-id>
goal: <one sentence from intake>
spec: <path>#<section>
claims: .drive/claims/<unit-id>.md
rubric: .drive/rubrics/<shape>.md
scope: git range <base>..<head> | working tree at <abs path>
files: <list>
validation:
  build: <cmd>
  typecheck: <cmd>
  lint: <cmd>
  tests: <cmd>
  live: <cmd or "none">
evidence_inputs: <paths>
previous_gaps: <path to prior verdict.json or "none">
round: <n>/<K>
```

The verifier's task prompt is then: "Verify every claim in the claims file against the scope. Run the validation commands yourself. Attempt to refute each claim. Return the verdict JSON in 4.4 and nothing else. Default to `refuted` when uncertain."

### 4.3 Enforcement in Claude Code

**Fresh context.** Custom subagents start fresh (verified). Never use `context: fork`, the `fork` agent type, or `SendMessage` into the maker's agent to ask for verification.

**Read-only tool surface.** Verifier frontmatter: `tools: Read, Grep, Glob, Bash` and `disallowedTools: Edit, Write, NotebookEdit, Agent`. Bash stays because the verifier must run tests. Constrain Bash with a PreToolUse hook in the agent's frontmatter that blocks git mutations, deletions outside `/tmp`, and deploy or publish commands. Exit 2 blocks the call and returns stderr to the subagent as feedback (verified).

`~/.claude/skills/drive/bin/guard-verifier.sh`:

```bash
#!/bin/bash
# Verifier guard: may run tests and builds, may not change the repo, history, or the world.
INPUT=$(cat)
CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')
deny() { echo "Blocked by drive verifier guard: $1" >&2; exit 2; }
printf '%s' "$CMD" | grep -qE '(^|[;&|[:space:]])git[[:space:]]+(commit|push|checkout|switch|reset|stash|rebase|merge|cherry-pick|clean|tag|worktree|branch[[:space:]]+-[dDmM])' \
  && deny "git state is read-only for the verifier"
printf '%s' "$CMD" | grep -qE '(^|[;&|[:space:]])(rm[[:space:]]+-[a-zA-Z]*r|mv|chmod|chown|truncate)[[:space:]]' \
  && ! printf '%s' "$CMD" | grep -qE '(/private)?/tmp/' \
  && deny "no deletes or moves outside /tmp"
printf '%s' "$CMD" | grep -qE '(npm|pnpm|yarn)[[:space:]]+publish|wrangler[[:space:]]+(deploy|publish)|cargo[[:space:]]+publish|xcrun[[:space:]]+altool|gh[[:space:]]+(pr|release)[[:space:]]+(create|merge)' \
  && deny "no deploys or publishes from the verifier"
exit 0
```

**Severe tester write scope.** The severe tester needs Edit and Write, restricted to test locations and the proof directory. Same mechanism, matcher `Edit|Write|NotebookEdit`:

```bash
#!/bin/bash
INPUT=$(cat)
P=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')
case "$P" in
  */tests/*|*/test/*|*/__tests__/*|*/spec/*|*Tests/*|*_test.*|*.test.*|*.spec.*|*/severe_*|*/.drive/proofs/*|*/fixtures/*) exit 0 ;;
  *) echo "Blocked: severe tester writes only tests, fixtures, and proof artifacts, not $P" >&2; exit 2 ;;
esac
```

**Where the verifier reads from.** Not a worktree of its own (see §2 on branching from the default branch). Two cases:

1. Single maker in the canonical checkout (bug hunt, feature, most work): the verifier verifies the working tree in place. The commit to main happens after PASS, which fits the owner's straight-to-main habit and means main never holds a state the verifier rejected.
2. Parallel makers in worktrees (greenfield fan-out, migration): each maker reports its worktree path in its structured result; the orchestrator hands that path to the verifier as `scope`; on PASS the orchestrator merges into main and removes the worktree in the same step; on FAIL after the loop bound, the worktree is still removed and the unit is marked Partial with the last verdict filed. No worktree survives the step, which is the owner's rule.

**Verdict return.** The verifier returns the JSON as its final message; the orchestrator validates and writes it to `.drive/proofs/<unit-id>/verdict-r<n>.json`. Under the Workflow tool, pass the same schema to `agent(..., {schema})` and get a validated object back (verified, five retries).

### 4.4 Verdict schema and validity rules

```json
{
  "verdict": "pass | fail | blocked",
  "unit": "<unit-id>",
  "round": 2,
  "scope": { "range": "abc123..def456", "path": "/abs/checkout" },
  "ran": [
    { "cmd": "npm test", "exit": 0, "seconds": 41, "output": ".drive/proofs/<unit>/r2/npm-test.txt" }
  ],
  "claims": [
    {
      "id": "C1",
      "status": "holds | refuted | unverifiable",
      "oracle": "what independent reference decided it",
      "refutations_attempted": ["what I tried that should have broken it, and what happened"],
      "evidence": ["src/x.ts:42", "test: rejects cross-tenant read", ".drive/proofs/<unit>/r2/shot-1.png"],
      "confidence": 75
    }
  ],
  "gaps": [
    {
      "id": "G1",
      "claim": "C1",
      "severity": "blocking | should_fix | note",
      "what": "one sentence, observable",
      "where": "file:line",
      "repro": ["exact command or steps"],
      "confidence": 75
    }
  ],
  "harness_kindness": [
    { "shim": "sql.js in tests", "kinder_than_production_how": "no 100-bind-variable limit", "severity": "blocking" }
  ],
  "not_checked": ["what I could not or did not verify, and why"],
  "rung_supported": "Missing | Scaffold | Partial | Local Proof | Live Proof | Operational",
  "for_maker": "gaps only; no praise; no restatement of what works"
}
```

Validity rules the orchestrator applies before accepting a verdict:

- A `pass` requires `ran` non-empty with the project's test command present and exit 0; every claim `holds` with `confidence ≥ 75`; at least one `refutations_attempted` entry per claim; zero `blocking` gaps; every `harness_kindness` entry at `note` or resolved.
- A `pass` with no commands run, or with any claim lacking a refutation attempt, is rejected as malformed. The orchestrator re-spawns a fresh verifier once with the handoff plus the sentence "The previous verdict was rejected because it ran no commands / attempted no refutation." It does not say what to conclude.
- `blocked` means the verifier could not execute (missing env, broken toolchain). The orchestrator fixes the environment, not the maker, and re-verifies without consuming a loop round.
- Confidence uses the severe-testing scale: 100 demonstrated in the real runtime, 75 reliably reproduced under realistic conditions, 50 contrived, 25 speculative. Gaps below 50 go in `not_checked` or as `note`, never `blocking`.
- `rung_supported` cannot be `Live Proof` unless `ran` includes a command against the real environment (deployed URL, device, real database) with captured output.

### 4.5 Layers and their order

Order is by cost and by dependency: cheap deterministic checks first, then the reviews that need green code, then the expensive judgment passes, then simplification (which changes code and therefore requires re-gating), then the final audit.

1. **Deterministic gates** (always, before any model review). Build, typecheck, lint, tests, formatting. Run by the orchestrator via Bash; results printed to the transcript in the fixed block (4.9). Red gates go back to the maker without spending a verifier round; cap gate-fix cycles at three, then treat as a blocking gap with the failing output attached.
2. **Correctness verification** (always for code). The `drive-verifier` agent (4.3, §6) on the handoff. For small diffs on an existing codebase, `/code-review high` as a background forked subagent is an acceptable first pass; treat its lower-confidence findings as `should_fix`, never `blocking`, since the docs say high and above may include findings the review is less sure of.
3. **Spec-conformance grading** (feature, greenfield, migration, website, research). The `drive-grader` agent, Sonnet at low effort, against the rubric. Catches "built the wrong thing" and "left the spec behind." Runs in parallel with layer 2 since neither writes.
4. **Severe testing** (any unit with behavioral claims; heavier when the surface touches identity, money, data, files, network, untrusted input, or concurrency). The `drive-severe-tester` agent with the severe-testing skill preloaded via `skills:` so the full text is injected rather than summarized. It writes `severe_*` tests that try to refute each claim, runs them, and reports with the 0–100 scores. Its output feeds the verifier as `evidence_inputs`; the verifier still re-runs.
5. **Security review** (conditional on the surface list above). `/security-review` for a single pass on the branch; the severe tester's security lenses (authz, injection, SSRF, secrets, deserialization, resource exhaustion) for depth. For greenfield backends, both.
6. **UI and vision verification** (any rendered UI). The `drive-ui-verifier` agent with simulator or browser MCP tools: drives the flow, captures the accessibility tree and screenshots at two sizes, compares against goal, design tokens, and the previous screenshot, and grades with the four-criterion rubric from Rajasekaran (design quality, originality, craft, functionality) plus a user-outcome criterion that is blocking. Another researcher owns vision in depth; the contract here is that it returns the same verdict schema.
7. **Simplification** (after a PASS, before final audit; skip for bug fixes with tiny diffs and for migration code until the cutover is proven). `/simplify` applies behavior-preserving cleanups. Because it edits, layer 1 re-runs and a light re-verify (grader, Sonnet low, "did the test baseline change?") follows. If the baseline changed, the simplification is reverted, not debated.
8. **Docs review** (when docs changed or greenfield). A Sonnet low grader checks every documentation claim against code and tests; a documented behavior with no code behind it is a `should_fix`, and a documented behavior contradicted by code is `blocking` for the docs, not the code. `google-dev-docs-style` optional.
9. **Final independent audit** (greenfield, migration, features with five or more claims). The `drive-auditor` agent, Fable at xhigh, read-only, reads STATUS and proofs, samples claims (all if ≤ 10, otherwise ten plus every Live Proof claim), re-runs their proof commands, and hunts specifically for mirage: scaffolds labelled done, shims kinder than production, tests that cannot fail, Live Proof without live evidence, STATUS rungs above what the proof supports. It returns go / no-go with the same schema.

### 4.6 Loop control

```
K = 2 (bug hunt) | 3 (feature, website, research) | 3 per milestone + 2 final (greenfield) | 4 (migration cutover)
gate_cycles = 0
for round in 1..K:
  while gates red and gate_cycles < 3: maker fixes; gate_cycles++
  if gates still red: file blocking gap with output; break
  spawn fresh verifier(handoff, previous_gaps)    # and grader / severe tester / ui verifier per shape
  validate verdict (4.4); if malformed: respawn once
  persist verdict-r<round>.json; print VERIFY block (4.9)
  if pass: break
  for each blocking gap that matches a gap from an earlier round by claim + where:
      require maker to write .drive/failures/<gap-id>.md (root cause, why the first fix missed) before touching code
  maker receives gaps[] (blocking + should_fix), never the verdict prose
if not pass after K:
  if maker filed a dispute: arbiter rules once; log to .drive/DECISIONS.md
  else: set rung to what the last verdict supports (usually Partial); record open gaps in STATUS; continue or stop per orchestrator; never Done
```

**What counts as a pass.** The validity rules in 4.4, no more and no less. "Looks reasonable" is not a status the schema can express.

**Preventing rubber stamps.** Four mechanisms, layered: the schema rejects evidence-free passes; the prompt says to default to `refuted` when uncertain (the Workflow reference's wording); the verifier is at least the maker's tier for correctness work (§6); and for high-stakes units the orchestrator runs two verifiers with distinct lenses (correctness and does-it-reproduce; or parity and operability for migrations) and requires both to pass. Diversity beats redundancy here, per the authoring reference.

**Preventing nitpick loops.** Only `blocking` gaps trigger a new round. `should_fix` gaps are batched into the same round as any blocking fix, or into one final cleanup pass if no blocking gaps remain. `note` gaps go to the backlog section of STATUS and never re-enter the loop. From round 2 on, the verifier is told: report only blocking and should_fix; do not introduce new notes; do not raise a criterion that is not in the rubric except the standing floor (security, data loss, disabled tests, harness kindness), which is always in scope. The rubric is frozen at handoff; a verifier that believes the rubric is missing something files a `rubric_gap` in `not_checked`, and the orchestrator decides whether to amend the rubric for the next unit, logging the decision. Cap notes at five per verdict.

**Escalation on disagreement.** The maker may answer a blocking gap with a dispute file (`.drive/disputes/<gap-id>.md`: the claim, why the gap is not a defect, evidence). The orchestrator then spawns the arbiter (Opus xhigh by default; Fable for greenfield or migration) with the artifact, the gap, and the dispute. The arbiter may re-run anything and rules `defect | not_a_defect | rubric_ambiguous`, with reasoning. The ruling is logged to `.drive/DECISIONS.md` and is final for the run. No human queue; if the arbiter itself returns `rubric_ambiguous`, the orchestrator picks the stricter reading and logs it. If the owner must be consulted (the arbiter flags a product decision, not a technical one), the skill surfaces one question in conversation, once, with a default that applies if unanswered.

**Second time is the bug.** The repeated-gap rule above is where the owner's principle lives. A gap that returns after a fix is not a fix target; it is a diagnosis target. The failure note is the input to the lessons component.

### 4.7 Evidence standard and the proof bundle

Layout, per unit of work (a claim group; usually a feature slice or one bug):

```
.drive/
  STATUS.md                       # rungs per unit, each pointing at its proof dir
  DECISIONS.md                    # arbiter rulings, rubric amendments, deliberate deviations
  claims/<unit-id>.md             # behavioral claims written before code
  rubrics/<shape>.md              # frozen per run
  handoffs/<unit-id>.md
  proofs/<unit-id>/
    claim.md                      # copy of the claims block at verification time
    r1/ r2/ ...                   # one dir per verification round
      commands.log                # one line per command: ISO time · cwd · cmd · exit · seconds · output file
      *.txt                       # captured stdout/stderr, trimmed to the last 200 lines + first 50
      tests.txt                   # test names that target each claim, pass/fail, and whether they failed on the broken code
      shots/*.png                 # UI, named <screen>-<size>-<state>.png
      live.md                     # live-proof evidence: URL or device, command, timestamp, response excerpt
      verdict.json
  failures/<gap-id>.md            # root-cause notes for repeated gaps
  disputes/<gap-id>.md
```

`commands.log` format, written by whoever runs a command that is meant as evidence (maker, severe tester, verifier), via a tiny wrapper the skill provides:

```
2026-09-14T10:32:11Z · /Users/x/proj · npm test · exit 0 · 41s · r2/npm-test.txt
```

Rules:

- A STATUS rung claim without a proof directory is a finding for the grader and the auditor, not a formatting issue.
- `Local Proof` requires a verifier-run test command at exit 0 in the latest round. `Live Proof` requires `live.md` with a real-environment command and response. `Operational` requires evidence that a monitor, alert, or scheduled check exists and has fired at least once (or a documented reason none is needed). `Done` requires docs and STATUS to agree and the final audit to say go.
- Ground-truth precedence is a reading order, not a slogan. The verifier reads code and tests first, runs them, then reads proofs, then STATUS, then docs. Any disagreement between a higher and a lower layer is reported as a gap against the lower layer (a STATUS rung the proof does not support; a doc sentence the code contradicts).
- Trim, do not omit. Captured output is capped so bundles stay committable, but the command line and exit code are never trimmed.
- Size: keep text under 20 KB per file and screenshots to two sizes per screen. The coordinator should decide whether `.drive/proofs` is committed (the owner's Arcwell convention commits proof packets) or gitignored with only `verdict.json`, `commands.log`, and `live.md` committed. My recommendation is the latter; see §8.

### 4.8 Rubric design

Principles, each with the failure it prevents:

- **Every criterion is an observation, not a property.** "Returns 201 and a subsequent GET returns the same object" rather than "creates the resource correctly." Prevents the grader from inferring from names.
- **Every criterion names its oracle.** A test, an independent reference, an invariant, a normalized diff, a policy matrix, a measured Lighthouse score, a screenshot at a stated size. Prevents "looks right."
- **Every criterion names a refutation.** What observation would make it false. Prevents confirmation-only testing.
- **At least one user-outcome criterion, and it is blocking.** Can a user do the thing end to end, verified by driving the artifact, not reading it. Rajasekaran's solo run "entities appeared on screen but nothing responded to input" is the failure this prevents; it is the scaffold-not-behavior mirage in its purest form.
- **Include negative criteria.** What must not happen (cross-tenant read, PII in logs, horizontal scroll, disabled test). Prevents goalpost drift toward what was built.
- **Hard thresholds on the criteria that matter; weights on the rest.** Rajasekaran's contracts failed the sprint if any hard criterion fell below threshold. Prevents averaging a security failure away with nice typography.
- **Weight toward where the model is weak.** He emphasized design quality and originality "because Claude already scored well on craft and functionality by default." For code, weight toward edge cases, failure paths, and production constraints rather than happy paths.
- **Derive from a known-good example when possible.** The Outcomes docs' advice: analyze what makes a good artifact good, then turn that into criteria.
- **Freeze at handoff.** Amend for the next unit, never mid-loop.

Five examples, abbreviated to the shape the skill should generate. Each line is criterion · oracle · refutation · threshold.

**Backend endpoint** (`POST /outfits`, Cloudflare Worker + D1):

- Authenticated create returns 201 with an id, and GET by id returns the same body · integration test against a real D1 binding via `wrangler dev`, not an in-memory shim · create as user A, GET as user B expects 404 or 403 · blocking
- Malformed body returns 400 with a structured error · tests seeded with empty, oversized (1 MB), wrong types, unicode names, null fields · any 500 on malformed input · blocking
- No token 401, expired token 401, other tenant 403/404 · permission matrix test · any 200 off the diagonal · blocking
- Double submit with one idempotency key yields one row · concurrent test, two requests · two rows · blocking
- Production constraints hold in tests · harness check: bind-variable limit, statement size, row limits enforced in the shim or test runs against real D1 · a passing test that would fail on D1 · blocking
- Deployed preview responds correctly · `curl` against the preview URL with captured output in `live.md` · mismatch with local · required for Live Proof
- Errors logged with request id and no PII · log capture grep · email or token in logs · should_fix

**SwiftUI screen** (outfit builder):

- A user can pick three garments and save an outfit · UI verifier taps through in the simulator, reads the accessibility tree, screenshots each step · save button inert, or saved outfit absent on relaunch · blocking
- Empty, loading, and error states exist and are reachable · force network failure via a debug flag or mocked client; screenshot each · any state missing or unreachable · blocking
- No clipping at Dynamic Type XL, in dark mode, and in landscape · screenshots at each · truncated labels, overlapping controls · should_fix (blocking if the primary action is hidden)
- Every tappable element has an accessibility label · `inspect` tree · unlabeled buttons · should_fix
- Matches the design tokens (colors, spacing scale, type ramp) · token file versus screenshot inspection · off-token values · should_fix
- Design quality and originality scored 1–10 with a written breakdown, weighted 2x craft · few-shot calibrated grader · score below 6 on either · should_fix, blocking below 4
- Main thread not blocked during save · timing around the action in the simulator · visible hang over 500 ms · should_fix

**Migration cutover** (AI gateway into the core platform):

- Behavioral equivalence on a recorded corpus of at least 200 real requests · replay through old and new, normalized diff on deterministic fields, nondeterministic fields listed with justification · any unexplained diff · blocking
- Feature parity checklist derived from the old code's public surface (routes, config keys, error codes, headers), one test each · surface extraction script plus tests · any item without a passing test · blocking
- Rollback documented and rehearsed · verifier executes the rollback in a disposable environment and re-runs the corpus · rollback fails or leaves state · blocking
- No divergence during dual-run · counts and checksums on both sides over the soak window · drift · blocking
- Live traffic at a stated percentage with metrics captured · dashboard export or metrics query in `live.md` · absent · required for Live Proof; Done requires Operational
- Nothing references the old project after removal · grep and dependency graph · a live reference · blocking
- Shims for the external gateway are no kinder than production · harness kindness review · a limit missing from the fake · blocking

**Research report**:

- Every factual claim cites a source the grader fetched and that supports it · sample all if ≤ 30 claims, otherwise 30% random plus every claim in the recommendations · a cited source that does not say it · blocking
- Verified fact, source claim, and opinion are labelled · read · unlabelled assertions · should_fix
- Answers the questions in the intake, not adjacent ones · question-by-question mapping · an intake question with no section · blocking
- Contradictions between sources are surfaced, not averaged · read · a contested number presented as settled · should_fix
- Sources dated; nothing older than the freshness bound without a note · read · undated or stale · should_fix
- A completeness critic finds nothing material missing · separate Opus pass, "what modality, source, or question was not covered?" · a material omission · should_fix, blocking if it changes a recommendation

**Website page** (project site with blog and docs):

- Renders at 375, 768, and 1440 px with no horizontal scroll · Playwright screenshots and `document.documentElement.scrollWidth` check · overflow · blocking
- Lighthouse performance ≥ 90 and accessibility ≥ 95, measured · Lighthouse via the DevTools MCP · lower scores · should_fix, blocking under 80 / 90
- Every product claim matches the spec and repo · claim list versus source · a feature described that does not exist · blocking
- Zero broken internal links · crawl · 404s · blocking
- Blog index lists posts and a post renders; docs page renders with navigation · drive through · a dead section · blocking
- Design quality and originality scored with breakdown · as for UI · below threshold · should_fix

### 4.9 Grader placement

| Check | Mechanism | Model | What it sees | Suffices for |
|---|---|---|---|---|
| Deterministic gates | Bash by orchestrator | none | exit codes | build, types, lint, tests, format |
| Loop termination | `/goal` prompt-hook evaluator | Haiku (global env override only) | transcript | reading printed VERIFY blocks; nothing else |
| Rubric conformance, evidence completeness, docs-vs-code, STATUS-vs-proof | `drive-grader` subagent | Sonnet, effort low | handoff files, repo read-only | checklist judgments with clear oracles |
| Correctness | `drive-verifier` subagent | Opus, effort high (Fable for greenfield milestones and migrations) | handoff, repo, runs tests | logic, edge cases, concurrency, boundaries |
| Refutation tests | `drive-severe-tester` subagent, severe-testing preloaded | Opus high (Sonnet high for narrow, well-specified surfaces) | claims, code | writing tests that can fail |
| Security | `/security-review` plus severe tester lenses | Opus | branch diff | authz, injection, secrets, SSRF |
| UI | `drive-ui-verifier` subagent with MCP | Opus high | rendered app, tokens, prior shots | interaction and visual judgment |
| Cleanup | `/simplify` then re-gate | default | changed code | behavior-preserving simplification |
| Final audit / arbitration | `drive-auditor` subagent | Fable xhigh (Opus xhigh for bounded features) | STATUS, proofs, code, re-runs | go/no-go, disputes |

**Making the transcript carry the evidence.** `/goal`'s evaluator can only see what the orchestrator prints. After every verification round and every gate run the orchestrator prints one fixed block, and the goal condition refers to it:

```
DRIVE · VERIFY · unit outfits-create · round 2/3
GATES  build ok · typecheck ok · lint ok · tests 212/212 ok
VERDICT fail · claims 5 · holds 4 · refuted 1 · blocking 1 · should_fix 2 · notes 1
GAPS   G1 blocking C3 src/outfits.ts:88 cross-tenant GET returns 200 · repro .drive/proofs/outfits-create/r2/verdict.json
RUNG   outfits-create → Partial (was Scaffold)
FILE   .drive/proofs/outfits-create/r2/verdict.json
```

Goal condition template (under the 4,000-character limit, measurable, with a stated check and a bound):

```
/goal Every unit listed in .drive/STATUS.md is at its target rung, and for each unit the most recent printed
DRIVE · VERIFY block shows "VERDICT pass" with "blocking 0", produced by a fresh verifier subagent in this
session (not by the maker). The final printed GATES line is all ok. `git status --porcelain` prints nothing
after the final commit to main and no worktrees remain (`git worktree list` shows one entry). If any unit
cannot reach its target rung, STATUS.md records the open gaps honestly and the unit is not marked Done.
Or stop after 60 turns.
```

**Where Sonnet low suffices and where it does not.** It suffices wherever the criterion has a clear oracle and the judgment is "does the artifact exhibit the stated observation": rubric conformance, evidence-bundle completeness, docs-versus-code, STATUS-versus-proof, citation checking, link checking, and reading gate outputs. It does not suffice where the failure mode is "looks right but is wrong": nontrivial logic, concurrency, authorization boundaries, migration equivalence, UI taste, and adjudicating disputes. The argument is Rajasekaran's: the evaluator "is still an LLM that is inclined to be generous," and a less capable evaluator has less capacity to trace the code path to the counterexample, so its generosity goes unchecked. A verifier weaker than its maker is the polite form of self-review. Keep the grader and the verifier as separate agents with separate models so the cheap one never gets promoted by accident.

**When to use a subagent verifier instead of `/goal` at all.** Always for the verdict. `/goal` is for keeping the session running and for exiting cleanly; it should never be the thing that decides a claim holds. The experimental agent-based Stop hook (subagent with tools, 50 tool turns) is the harness's own version of what this spec builds by hand, and when it stabilizes it could replace the printed-block indirection; today its 60-second default timeout and experimental status make it unsuitable for running a real test suite.

### 4.10 Invoking severe-testing from the drive skill

Do not have the orchestrator invoke `severe-testing` via the Skill tool in its own context; that puts the attack plan in the same context as the plan that built the thing. Instead the `drive-severe-tester` agent definition preloads it (`skills: [severe-testing]`), which injects the full SKILL.md rather than the description. The task prompt supplies the claims file and the validation commands and asks for: one `severe_*` test module per claim group following the CLAIM / PRECONDITIONS / POSTCONDITIONS / ORACLE / SEVERITY block; the malicious and security categories that apply to the surface; a run of the new tests plus the existing suite; and a report scored on the 0–100 scale with findings at ≥ 50, untested risk at 25, and the false-positive filter applied. For a bug fix, the prompt adds the regression bar: the reproducer must be shown failing on the pre-fix commit (`git stash` or `git worktree add /tmp/prefix <sha>`; the tester may create worktrees under `/tmp` because it is not the verifier) and passing after.

The verifier then receives the severe tests as `evidence_inputs`, re-runs them, and is free to disagree with the tester's scores.

---

## 5. Conditionals by project shape

**Greenfield app (fashion iOS app, Cloudflare backend).** The full stack, applied per milestone rather than once at the end: gates; correctness verifier (Fable at milestone boundaries, Opus within); conformance grader against the spec slice; severe tester on every backend claim and on the sync and persistence paths of the client; security review for the backend; UI verifier per screen with the four-criterion design rubric plus the blocking user-outcome criterion; docs review; final audit on Fable before any Done. Loop bound 3 per milestone, 2 for the final integration pass. Live Proof means a deployed preview Worker answering real requests and the app running in the simulator against it, both captured. Ultrareview at milestone ends is optional and worth its $5–25 when the diff is large and claude.ai auth is present. Sprint contracts from Rajasekaran apply: the claims file for a milestone is agreed (written by the spec step, read by both maker and verifier) before code.

**Deep bug hunt.** Verification centers on one artifact: the reproducer. Skip conformance grading, UI (unless the bug is visual), docs, and the final audit. The severe tester writes the reproducer first and shows it failing on the pre-fix commit; the verifier re-runs it on both sides. Loop bound 2. The repeated-gap rule is the whole game: if the fix does not hold on re-verify, the next step is a root-cause note, not another patch. The verdict's `rung_supported` is usually Local Proof unless the bug only manifests live, in which case Live Proof is required and the verifier must exercise the real environment.

**Feature on an existing product (new dashboard).** Gates; `/code-review high` as a first correctness pass, then the verifier on Opus for the touched boundaries; conformance grader against the feature spec; severe tester scoped to the new surface plus every boundary the diff touches (data access, auth); UI verifier for the dashboard; security review only if the feature touches identity, data export, or untrusted input; `/simplify` after PASS; no full final audit unless the unit has five or more claims, in which case a Sonnet grader checks STATUS against proofs and an Opus auditor does the go/no-go. Loop bound 3.

**Migration / consolidation (AI gateway into core).** The equivalence corpus is the primary oracle and is built before any code moves. Two verifiers with different lenses (parity; operability and rollback) must both pass. Severe testing emphasizes failure injection, timeouts, retries, and the rollback rehearsal. Final audit mandatory on Fable. Done requires Operational, which requires the live cutover evidence; anything short of that is honestly labelled Partial or Live Proof. Loop bound 4 because equivalence gaps tend to be many and small. Harness kindness review is blocking: a fake for the external gateway that is kinder than the real one is exactly the sql.js failure again.

**Research + website.** Two different verification regimes. For the research: citation checking (Sonnet low can fetch and compare), the labelling check, the intake-question mapping, and a completeness critic on Opus. For the site: UI verifier with Lighthouse and link crawl, the content-truth rubric against the research and the repo, and design scoring. No severe tests unless the site has forms, search, or a backend; then the endpoint rubric applies to those. Security review only for the backend parts. Loop bound 3 for each.

**Other shapes that matter.**

- Pure research report: citation check and completeness critic only; no gates.
- Refactor / simplification: the oracle is behavior preservation; the verifier captures the full test output before and after and diffs it byte for byte (allowing for timing noise); any new failure or any changed assertion is blocking; `/code-review` on the diff; no new features permitted by rubric.
- Ops / incident: the claim is "the trigger no longer reproduces and something will tell us if it returns"; the verifier reproduces the trigger against the fixed system in a safe environment and confirms a monitor or alert exists and has fired in test; Live Proof mandatory; timebox verification hard.
- Data pipeline: row counts, checksums, idempotent re-run, schema drift, and partial-failure recovery tests; severe tester heavy; verifier runs the pipeline twice and checks the second run is a no-op.
- CLI tool: golden-output tests, exit codes, `--help` text, hostile arguments (unicode, empty, huge, path traversal); UI verifier not needed; conformance grader checks docs examples actually run.
- Library / SDK: public API surface snapshot with semver check; every documented example compiles and runs as a test; severe tests on input validation; docs review mandatory.

Conditionals the skill needs as first-class rules: if the unit touches identity, money, data at rest, files, network egress, plugins, user content, secrets, generated code, or cross-service calls, then the severe tester's security categories and `/security-review` run. If the unit renders anything, the UI verifier runs and the user-outcome criterion is blocking. If the unit claims Live Proof, the verifier must run a command against the real environment. If a gap recurs, diagnosis precedes any fix. If the diff exceeds roughly 800 changed lines, two verifiers with distinct lenses replace one. If a test harness includes any fake, shim, or mock of a production dependency, the harness-kindness review is required and blocking.

---

## 6. Model and effort assignment

| Role | Model | Effort | Tools | Isolation | Predefined agent? |
|---|---|---|---|---|---|
| Verifier | opus (fable for greenfield milestones, migrations) | high | Read, Grep, Glob, Bash (guarded) | none; reads the maker's tree | yes, `drive-verifier` |
| Conformance grader | sonnet | low | Read, Grep, Glob, Bash (guarded) | none | yes, `drive-grader` |
| Severe tester | opus (sonnet high for narrow surfaces) | high | Read, Grep, Glob, Bash, Edit, Write (path-guarded) | none; may create worktrees under /tmp for pre-fix runs | yes, `drive-severe-tester` |
| UI verifier | opus | high | Read, Grep, Glob, Bash (guarded), simulator and browser MCP | none | yes, `drive-ui-verifier` |
| Final auditor / arbiter | fable (opus xhigh for bounded features) | xhigh | Read, Grep, Glob, Bash (guarded) | none | yes, `drive-auditor` |
| Maker | per the implementation component | per shape | full | worktree only for parallel fan-out | owned by another researcher |

On aliases: the brief names Opus 4.8 and Sonnet 4.8, but today on the Anthropic API `opus` resolves to Opus 5 and `sonnet` to Sonnet 5, and the pricing page lists no Sonnet 4.8. Use aliases in the agent files and let them drift with the platform; if the owner truly wants a pinned version, `ANTHROPIC_DEFAULT_OPUS_MODEL` / `ANTHROPIC_DEFAULT_SONNET_MODEL` or a full model id in frontmatter does it.

Draft agent definitions for `~/.claude/agents/` (the skill cannot bundle them unless packaged as a plugin; ship them from the drive repo with a one-line install step that symlinks them).

`~/.claude/agents/drive-verifier.md`:

```markdown
---
name: drive-verifier
description: Independent verifier for /drive. Receives a handoff file, runs the project's checks itself, tries to refute each behavioral claim, and returns a verdict JSON. Read-only on the repository.
model: opus
effort: high
tools: Read, Grep, Glob, Bash
disallowedTools: Edit, Write, NotebookEdit, Agent
maxTurns: 80
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "$HOME/.claude/skills/drive/bin/guard-verifier.sh"
---

You are the verifier. You did not write this code and you have no stake in it passing.

Read, in this order and no other: the claims file, the code and tests in scope, then run the validation
commands yourself, then the proof artifacts, then STATUS, then any docs. A disagreement between a later
source and an earlier one is a gap against the later source.

For every claim: name the oracle you used, attempt at least one refutation (an input, an ordering, a
failure, a boundary that should break it if the claim is false), and record what happened. Do not accept
a test as evidence until you have run it. Do not accept a screenshot as evidence until you have produced
one yourself where tools allow. For any fake, shim, or mock of a production dependency, state where it is
kinder than production.

If you are uncertain whether a claim holds, it does not hold. Report gaps at confidence 50 or above as
findings; put speculation under not_checked. Severity: blocking means a user, an attacker, or the data
would notice; should_fix means a maintainer would; note means nobody would but it is worth writing down.
From round 2 onward report only blocking and should_fix. Do not raise criteria outside the rubric except
security, data loss, disabled or weakened tests, and harness kindness, which are always in scope.

Never edit, commit, stash, deploy, or publish. Return the verdict JSON exactly in the schema you were
given and nothing else: no praise, no summary of what works, no advice beyond the gaps.
```

`~/.claude/agents/drive-grader.md`:

```markdown
---
name: drive-grader
description: Cheap conformance grader for /drive. Checks an artifact against a frozen rubric and checks that STATUS claims, proof bundles, and docs agree with code. Read-only.
model: sonnet
effort: low
tools: Read, Grep, Glob, Bash
disallowedTools: Edit, Write, NotebookEdit, Agent
maxTurns: 40
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "$HOME/.claude/skills/drive/bin/guard-verifier.sh"
---

Grade the artifact against the rubric, one criterion at a time. For each criterion write: met / not met /
cannot tell, the observation you based it on with a file:line or command output, and nothing else. Do not
infer from names or comments; if the observation is not in front of you, the answer is cannot tell.
Then check that every rung in STATUS has a proof directory whose latest verdict supports it, and that
every documented behavior has code and a test behind it. Return the verdict JSON in the given schema.
You are not asked whether the work is good. You are asked whether it matches.
```

`~/.claude/agents/drive-severe-tester.md`:

```markdown
---
name: drive-severe-tester
description: Adversarial tester for /drive. Writes tests that try to refute each behavioral claim, runs them, and reports scored findings. Writes only test files, fixtures, and proof artifacts.
model: opus
effort: high
tools: Read, Grep, Glob, Bash, Edit, Write
disallowedTools: Agent
skills:
  - severe-testing
maxTurns: 120
hooks:
  PreToolUse:
    - matcher: "Edit|Write|NotebookEdit"
      hooks:
        - type: command
          command: "$HOME/.claude/skills/drive/bin/guard-tests-only.sh"
---

Follow the severe-testing skill you have been given. Start from the claims file, not from the code: write
the refutation list before you read the implementation, so the implementation cannot narrow your
imagination. For each claim group produce one severe_* test module with the CLAIM block at the top. Run the
new tests and the existing suite. For a fix to a known bug, show the reproducer failing on the pre-fix
commit (use a worktree under /tmp) and passing after; a regression test that never failed is not evidence.
Report with the 0-100 confidence scale, findings at 50 or above, untested risk listed separately, and the
false-positive filter applied. Never touch production code; if you believe production code must change,
say so in the report.
```

`~/.claude/agents/drive-ui-verifier.md` (contract only; the vision researcher owns the body):

```markdown
---
name: drive-ui-verifier
description: Vision and interaction verifier for /drive. Drives the rendered UI in the simulator or browser, captures accessibility trees and screenshots, and grades against the goal, design tokens, and previous screenshots.
model: opus
effort: high
tools: Read, Grep, Glob, Bash
disallowedTools: Edit, Write, NotebookEdit, Agent
maxTurns: 80
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "$HOME/.claude/skills/drive/bin/guard-verifier.sh"
---

Interact first, judge second. Perform the user outcome named in the rubric end to end and capture the
accessibility tree and a screenshot at each step and at each required size and state. Only then score
design quality, originality, craft, and functionality with a written breakdown. The user-outcome criterion
is blocking regardless of the scores. Return the verdict JSON.
```

`~/.claude/agents/drive-auditor.md`:

```markdown
---
name: drive-auditor
description: Final independent auditor and arbiter for /drive. Hunts for mirage completion before anything is marked Done, and rules once on maker/verifier disputes. Read-only, may re-run proofs.
model: fable
effort: xhigh
tools: Read, Grep, Glob, Bash
disallowedTools: Edit, Write, NotebookEdit, Agent
maxTurns: 100
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "$HOME/.claude/skills/drive/bin/guard-verifier.sh"
---

Assume the STATUS file is optimistic and look for where. Sample the claims (all if ten or fewer, otherwise
ten plus every Live Proof claim), re-run their proof commands, and check each rung against what the proof
supports. Look specifically for: scaffolds or stubs behind a Done label; tests that pass trivially or
were weakened; fakes kinder than production; Live Proof with no real-environment evidence; docs describing
behavior the code lacks; workarounds applied twice. For a dispute, read both files and the artifact, re-run
what you need, and rule defect / not_a_defect / rubric_ambiguous with reasons. Return go or no-go in the
verdict schema, with every downgrade you would make to STATUS listed as a gap.
```

---

## 7. Failure modes and anti-patterns

How this component itself can produce mirage completion, and the prevention in each case.

- **Self-review dressed as review.** The maker "asks a subagent to review" but does so with `context: fork`, or by sending its summary along with the code, or by having the orchestrator (which has watched the maker work) grade. Prevention: verifier is always a fresh custom subagent; handoff built from files by template; the skill forbids pasting any agent's message into a verifier prompt.
- **Verifier weaker than maker.** A Sonnet low "verifier" passes Opus-written concurrency code because it cannot find the counterexample. Prevention: model parity rule for correctness; Sonnet low confined to the grader role by having a different agent name and file, so the cheap one cannot be substituted for the expensive one by a lazy orchestrator turn.
- **Passing on "looks reasonable."** Prevention: the schema has no such value; a pass with no `ran` entries or no refutation attempts is rejected before it is recorded; default-to-refuted instruction.
- **Verifier talks itself out of a real finding** (Rajasekaran's observed failure). Prevention: severity thresholds are defined by who would notice, not by how hard the fix is; the verifier is told it is not asked whether the work is good, only whether the claims hold; two-lens verification on large units so one verifier's rationalization does not silence the other.
- **Superficial testing** (his other observed failure). Prevention: the severe tester writes the refutations before reading the implementation; the UI verifier must interact, not view; the verifier must run, not read, tests.
- **Disabling or weakening tests to get green.** Prevention: the standing floor puts disabled, skipped, or loosened assertions in scope for every verifier regardless of rubric; the refactor oracle diffs test output before and after; the auditor greps for `skip`, `xit`, `@Ignore`, `--no-verify`, and loosened tolerances in the diff.
- **Moving goalposts.** The maker cannot finish criterion 4, so the spec quietly loses criterion 4. Prevention: rubric frozen at handoff and stored under `.drive/rubrics/`; amendments only between units and logged to DECISIONS; the grader compares the current rubric to the frozen one.
- **Verifying the scaffold, not the behavior.** A route exists, a view compiles, a README describes the feature. Prevention: every rubric has a blocking user-outcome criterion verified by driving the artifact; STATUS rungs are tied to proof kinds (Scaffold is a legitimate rung and is where scaffolds stay).
- **Kind harnesses.** The sql.js shim class. Prevention: `harness_kindness` is a required verdict field; any fake of a production dependency requires a statement of where it is kinder; for persistence and platform limits, tests run against the real binding where a local runner exists (`wrangler dev` with D1, the simulator, a real Postgres in a container).
- **Local labelled live.** Prevention: `rung_supported: Live Proof` requires a real-environment command in `ran` and a `live.md`; the auditor re-runs Live Proof claims.
- **Infinite loops and nitpick loops.** Prevention: bound K per shape; only blocking gaps re-loop; convergence rule from round 2; notes capped; `/goal` bounded by turns; Stop hook cap is eight consecutive blocks and the skill does not raise it.
- **Loop exits on exhaustion labelled as success.** After K rounds the orchestrator writes "done with minor issues." Prevention: after K without pass the rung is whatever the last verdict supports and the gaps are listed in STATUS; Done is unreachable without a pass and, where required, a go from the auditor.
- **Verifier in a worktree of its own.** Sees main, passes, the maker's actual change was never checked. Prevention: verifier has no `isolation`; scope carries the path to the maker's tree.
- **Evidence that cannot be found later.** Verdicts in the transcript only. Prevention: every verdict persisted under `.drive/proofs`; STATUS points at paths; the printed block names the file.
- **Fixing the second occurrence the same way as the first.** Prevention: the repeated-gap rule requires a root-cause note before code changes; the lessons component consumes those notes.
- **Grader of record is the transcript evaluator.** `/goal` says met because the maker printed "all tests pass." Prevention: the goal condition refers to printed verifier verdicts from a fresh subagent, and the block includes the verdict file path; the orchestrator never prints "VERDICT pass" from anything but a validated verdict file.

---

## 8. Open questions and trade-offs

1. **Commit the proof bundles or not.** The owner's Arcwell convention commits proof packets; his no-stray-artifacts rule pulls the other way, and screenshots bloat a repo. Recommendation: commit `claims.md`, `commands.log`, `verdict*.json`, `live.md`, and `tests.txt` (small text, the auditable core); gitignore `*.txt` outputs and `shots/` but keep them on disk for the run and reference them by path. The coordinator should align this with the state-tracking researcher's layout and name (`.drive/` is a placeholder).

2. **Moving `/goal`'s evaluator off Haiku.** Only `ANTHROPIC_DEFAULT_HAIKU_MODEL` does it, and it also moves conversation summarization and every other background call to that model. Setting it to `sonnet` costs roughly double on background tokens, which is small. Recommendation: do not depend on it. Design the goal condition to read printed verifier verdicts, so the evaluator's job is reading a fixed block, which Haiku can do. Offer the env var as an opt-in line in the skill's setup notes for an owner who wants zero Haiku anywhere.

3. **Agent-based Stop hooks as the future grader slot.** They run a subagent with tools before Claude may stop, which is exactly the "verifier that runs the tests itself" this spec builds by hand. They are marked experimental with a 60-second default timeout. Recommendation: do not use them now; note them as the upgrade path and revisit when the docs drop the warning.

4. **Verifier model parity versus cost.** Opus at high for every verification round on a greenfield project is real money. Recommendation: parity for correctness (a wrong pass costs more than a verifier round), Sonnet low for the grader, and Fable only at milestone boundaries and the final audit. Rajasekaran's caveat cuts the other way for small tasks: when the task is well inside what the maker does reliably solo, a single `/code-review medium` pass plus gates is enough, and the skill's intake classifier should be allowed to say so.

5. **Whether the verifier may write tests.** Letting it write blurs judge and attacker and gives it a way to make its own job easier. Recommendation: no; the severe tester writes, the verifier runs. The cost is one more agent per unit; the benefit is that the tests the verifier runs were not written to pass.

6. **Ultrareview.** Independent reproduction of every finding is precisely the bar this spec wants, and it is a product Anthropic already runs. It needs claude.ai auth, costs $5–25, and cannot be self-started by Claude in an interactive session. Recommendation: offer it as an optional layer at milestone ends and before migration cutover via `claude ultrareview --json` when the environment allows; never make a rung depend on it.

7. **`/verify` bundled skill.** The docs describe `/verify` ("build and run your app to confirm a code change does what it should, without falling back to tests or type checks") and `/run-skill-generator`, which records a launch recipe. This session's skill list shows `/run` but not `/verify`. If `/verify` is available on the owner's build, it is a natural way to produce Live Proof for app shapes. The coordinator should check.

8. **Alias drift.** `opus` and `sonnet` point at 5-series models today; the brief says 4.8. Recommendation: aliases, no pins, and a line in the skill that says which alias each role uses rather than a version.

9. **How many claims per unit.** Too many and the verifier's context fills with proof output; too few and the bundle count explodes. Recommendation: three to eight behavioral claims per unit, and split units above eight.

---

## 9. Skill text candidates

Plain language, imperative, ready to lift into `SKILL.md` or `references/verification.md`.

**The rule**

> The agent that built a thing never decides whether it is done. Spawn a fresh verifier subagent for every verification round. Never fork it from the maker, never continue the maker's agent to ask for a review, and never paste any agent's summary into the verifier's prompt. Build the verifier's handoff from files using the template, so the verifier sees the claims, the rubric, the scope, and the commands, and nothing anyone said about them.

**Evidence, not opinion**

> A verdict is invalid unless the verifier ran the project's test command itself and tried at least once to refute every claim. Reject a pass that names no commands as malformed and spawn a fresh verifier once more. Do not tell the second verifier what to conclude; tell it only why the first verdict was rejected.

**Default to refuted**

> Instruct every verifier: if you are uncertain whether a claim holds, it does not hold. Report gaps you can demonstrate at confidence 50 or above. Put speculation under not_checked so it is neither lost nor counted.

**Severity by who would notice**

> Blocking means a user, an attacker, or the data would notice. Should-fix means a maintainer would. Note means nobody would but it is worth writing down. Only blocking gaps start another round. Batch should-fix gaps into the same round or one final pass. Notes go to the backlog and never re-enter the loop.

**Bounded loops**

> Bound the fix-and-re-verify loop before it starts: two rounds for a bug fix, three for a feature or a page, three per milestone plus two at the end for a greenfield build, four for a migration cutover. When the bound is reached without a pass, set the unit's rung to what the last verdict supports, list the open gaps in STATUS, and move on or stop. Never write Done because the rounds ran out.

**Second time is the bug**

> If a blocking gap comes back after a fix, stop fixing. Write a root-cause note under .drive/failures naming why the first fix missed, then change code. A workaround applied twice means the first diagnosis was wrong.

**Freeze the rubric**

> Write the rubric before the maker starts and freeze it at handoff. The verifier may not fail work on criteria the rubric does not contain, except the standing floor: security, data loss, disabled or weakened tests, and a test harness kinder than production, which are always in scope. Amend rubrics between units, never during a loop, and log every amendment in DECISIONS.md.

**Where the verifier reads**

> Do not give the verifier a worktree of its own; a subagent worktree branches from the default branch and would never see the maker's uncommitted work. Give it the path to the maker's tree and read-only tools. Commit to main only after a pass. If makers worked in worktrees, verify inside each worktree, then merge and delete it in the same step.

**Read-only means guarded Bash**

> The verifier needs Bash to run tests, so Bash stays. Guard it: block git commit, push, checkout, reset, stash, rebase, merge, and worktree; block deletes and moves outside /tmp; block deploys and publishes. Deny Edit and Write outright. The severe tester may write, but only to test files, fixtures, and the proof directory.

**Gates before judgment**

> Run build, typecheck, lint, and tests before any model reviews anything. Red gates go back to the maker without spending a verifier round. Print the results in the fixed DRIVE block so the loop evaluator can read them.

**The transcript is the evaluator's only window**

> /goal's evaluator sees the conversation and cannot run tools. It is a loop driver, not a grader. After every gate run and every verification round, print the DRIVE · VERIFY block with the verdict, the counts, and the verdict file path. Write the goal condition to refer to that block and to a fresh verifier's pass, never to the maker's own report of success.

**Choose graders by the shape of failure**

> Use Sonnet at low effort where the question is "does the artifact show this observation": rubric conformance, evidence completeness, docs against code, STATUS against proofs, citations, links. Use Opus at high effort where the failure would look right and be wrong: logic, concurrency, authorization, migration equivalence, UI judgment. Use Fable at xhigh for the final audit and for disputes. A verifier weaker than its maker is self-review with a different name.

**Rubric lines**

> Write each criterion as an observation with an oracle and a refutation: what you would see, what decides it, and what would prove it false. Include at least one criterion that a user can do the thing end to end, verified by driving the artifact, and make that one blocking. Include what must not happen. Put hard thresholds on the criteria that matter and weights on the rest.

**Proof or it did not happen**

> Every STATUS rung points at a proof directory. Local Proof needs a verifier-run test command at exit zero. Live Proof needs a command against the real environment with its response captured in live.md. Operational needs evidence that something will notice if it breaks. Done needs docs and STATUS to agree and the auditor to say go. A rung without a proof is a finding.

**Ask of every shim**

> For any fake, mock, or shim of a production dependency, the verifier must state where it is kinder than the real thing. A harness kinder than production certifies broken code. Where a local runner for the real dependency exists, use it.

**Severe testing belongs to the tester, not the orchestrator**

> Do not load the severe-testing skill into the orchestrator. Preload it into the drive-severe-tester agent so the full instructions are injected, hand that agent the claims file and the validation commands, and have it write the refutation list before it reads the implementation. For a bug fix, require the reproducer to fail on the pre-fix commit and pass after.

**The auditor assumes STATUS is optimistic**

> Before any Done on a greenfield build, a migration, or a feature with five or more claims, spawn the auditor. It samples claims, re-runs their proofs, and looks for scaffolds behind Done labels, tests that cannot fail, kind harnesses, Live Proof without live evidence, and docs the code contradicts. It returns go or no-go and every downgrade it would make.
