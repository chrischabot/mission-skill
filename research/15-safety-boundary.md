# The Fable safety boundary and the fallback design

*Component report for the `/drive` skill. Post step 14. Author model: Fable 5.1. Date: 2026-09-14.*

## 1. Executive opinion

The single most consequential fact for `/drive` is one the source post gets wrong: **on the API and in headless (`-p`) Claude Code, the fallback to Opus is not automatic.** Automatic model switching is a Claude *apps* behaviour (Claude.ai, the desktop app, and interactive Claude Code). In a non-interactive run — which is exactly how a self-driving skill executes — a flagged request simply ends the turn with a refusal. There is nothing to catch it. A `/drive` design that assumes "Anthropic falls back for me" will, on the first security-review or adversarial-test step that trips the classifier, stall silently and look for all the world like a bug in the code it was testing.

So the component's job is not to *react* to blocks. It is to *route around* them before they happen. Fable 5.1's classifiers fire hardest on precisely the roles this skill leans on most: security review, adversarial testing with real attack payloads, auth and crypto code, pentest-shaped end-to-end tests, and dependency-CVE triage. Every one of those is "hard-but-bounded" work the brief already assigns to Opus. The recommendation writes itself: **pin the security and severe-testing roles to Opus by default, as predefined subagents, not on-block.** Keep the Fable orchestrator away from raw attack strings so it never trips its own classifier and gets stuck on a sticky switch. Treat an actual block as a logged event with a defined next step, never as a mystery.

The rest of the report verifies the boundary against Anthropic's own documents, defines a decision procedure that never confuses a classifier decline with a real error, gives draft subagent definitions, and lists the model-independent boundaries the skill must honour regardless of any of this (credentials, destructive operations, systems you don't own, data retention on cloud runs).

## 2. What the post says, and a critique

Step 14 of the post reads: *"Fable 5 ships with classifiers that decline in cybersecurity vulnerability research, biology, chemistry, and model distillation; Anthropic falls back to Opus 4.8 automatically. Architect for the fallback... A loop that silently fails on a classifier block looks identical to a loop that fails on a real error until you debug it. Treat the boundary as a known fallback, not a failure mode."*

The **spirit is correct and valuable**: architect for the boundary, and the "silent block looks like a real error" observation is the single best sentence in the post. But three specifics are wrong or imprecise, and the errors matter for a headless skill.

- **"Falls back to Opus 4.8 automatically"** is false for the two surfaces `/drive` runs in. On the API, fallback is opt-in (you configure it). In headless Claude Code, a flag ends the turn with a refusal; it does not switch. Automatic switching is real, but only in interactive/consumer surfaces. Building on "automatic" is the core mistake to avoid.
- **"Falls back to Opus 4.8"** for everything is wrong even where switching *is* automatic. Cybersecurity flags route to Opus 4.8; **biology flags route to Opus 5**, not 4.8. Opus 5 itself has no biology fallback, so biology work hard-refuses there.
- **"chemistry, and model distillation"** as named categories is imprecise. The API surface exposes five categories: `cyber`, `bio`, `frontier_llm`, `reasoning_extraction`, and `general_harms` (plus `null`). Chemistry is folded into `bio`. "Distillation" splits into two different things: `reasoning_extraction` (asking the model to reproduce its own chain of thought) and `frontier_llm` (helping build a competing model). Those two have **no fallback model at all** — the refusal simply stands. That distinction is load-bearing: some blocks are recoverable by re-routing, and some are not.

The post is directionally right and specifically unreliable — which is the norm for a Twitter roadmap and the reason the brief insists on verification.

## 3. Verified facts (with URLs)

**Classifier domains and how a decline is surfaced.** Claude Fable 5.1, Fable 5, and Opus 5 include safety classifiers that can decline a request. A decline is a **successful HTTP 200** with `stop_reason: "refusal"` and a `stop_details` object naming the category. The documented `stop_details.category` values and meanings ([Refusals and fallback](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback), [Stop reasons and fallback](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)):

| `category` | Meaning | Fallback? |
|---|---|---|
| `"cyber"` | Could enable cyber harm (malware, exploit dev). Benign security work can also trigger it. | Yes → Opus 4.8 |
| `"bio"` | Could enable biological harm. Beneficial life-sciences work can also trigger it. (Chemistry lives here.) | From Fable → Opus 5; on Opus 5, none |
| `"frontier_llm"` | Could assist a competing model's development (restricted by Anthropic's commercial terms). Benign ML work can also trigger it. | None — refusal stands |
| `"reasoning_extraction"` | Asks the model to reproduce its internal reasoning in the output. | None — refusal stands |
| `"general_harms"` | A usage-policy area outside the four named categories. | None — refusal stands |
| `null` | The refusal maps to no named category. `null` is a permanent, normal value, not a placeholder. | — |

`explanation` is a human-readable string that "is not stable, so display it rather than parse it," and both `category` and `explanation` can be `null` on a genuine refusal. **Branch on `stop_reason`, never on `stop_details`.**

**Is the fallback automatic? It depends on the surface.**

- *API:* not automatic. "API customers must opt into and configure fallbacks. Until fallbacks are configured, the model will return a 200 response with a stop reason" ([support: why Claude switched models](https://support.claude.com/en/articles/15363606-why-claude-switched-models-in-your-conversation-with-fable-5-or-fable-5-1)). Three opt-in mechanisms exist: the server-side `fallbacks` parameter (beta `server-side-fallback-2026-07-01` for `"default"` mode; Claude API and Claude Platform on AWS only), SDK client-side middleware (`BetaRefusalFallbackMiddleware`, for Bedrock/Vertex/Foundry), or a hand-rolled retry with fallback credit. Permitted server-side targets for Fable 5.1 are `claude-opus-4-8` and `claude-opus-5` ([Refusals and fallback](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback)).
- *Claude Code (interactive):* automatic by default and **sticky**. "When a classifier flags a request and the flagged category has a fallback model, Claude Code re-runs the request on that model and shows a notice in the transcript... After a fallback, the session continues on the fallback model. To return to your original model, run `/model`." Routing: "Fable 5.1 and Fable 5: biology-flagged requests re-run on Opus 5, and cybersecurity-flagged requests re-run on Opus 4.8. Opus 5: cybersecurity-flagged requests re-run on Opus 4.8. Biology-flagged requests end with a refusal instead." Category-based routing needs Claude Code v2.1.219+ ([Model configuration → Automatic model fallback](https://code.claude.com/docs/en/model-config)).
- *Claude Code (headless `-p`) — the case that matters for `/drive`:* "In non-interactive mode and SDK integrations that can't show the prompt, a flagged request ends the turn with a refusal instead" ([Model configuration](https://code.claude.com/docs/en/model-config)). This is the crux. **A `claude -p` driven `/drive` run does not auto-switch. It refuses.**

**What a block looks like inside Claude Code.** The Agent SDK emits system messages with subtype `model_refusal_fallback` (and `model_refusal_no_fallback` when no fallback exists). The transcript event has the shape `{"type":"system","subtype":"model_refusal_fallback","direction":"retry","originalModel":"claude-fable-5[1m]","level":"warning","trigger":"refusal","content":"..."}` (GitHub issue [#67009](https://github.com/anthropics/claude-code/issues/67009)). The interactive notice text is: *"Fable 5's safety measures flagged this message for cybersecurity or biology topics. They may flag safe, normal content as well... Switched to Opus 4.8. Send feedback with /feedback or learn more: https://support.claude.com/en/articles/15363606"* (issues [#67246](https://github.com/anthropics/claude-code/issues/67246), [#67305](https://github.com/anthropics/claude-code/issues/67305)). On the raw API path the Claude Code error line is *"API Error: <model>'s safeguards flagged this message..."* pointing at the Cyber Verification Program ([Error reference](https://code.claude.com/docs/en/errors.md)).

**First-request and context-only triggers.** "Fallback can trigger on the first request of a session, before you send anything unusual, because the first request carries workspace context such as your CLAUDE.md content and git status. A repository that contains security or biology material can trip the classifier on that context alone." `claude --safe-mode` disables CLAUDE.md, skills, MCP servers, and hooks to test whether a customization is the trigger; git status and directory names are still included ([Model configuration](https://code.claude.com/docs/en/model-config)). This is why an Arcwell-style repo full of security notes can flag Fable on turn one.

**What is actually blocked vs allowed (system card).** The [Claude Fable 5.1 & Mythos 5.1 System Card](https://www-cdn.anthropic.com/0339e6a7c5c7b87f5c07798616dc32c215d14235/Claude%20Fable%205.1%20&%20Claude%20Mythos%205.1%20System%20Card.pdf) (Sept 1, 2026), §3.4: "Fable 5.1 will allow vulnerability discovery in **source code** at all access levels, including general availability, while continuing to block vulnerability discovery in **compiled binaries**." §3.4.3 states the revised safeguards "reduce false positives on cybersecurity work that falls in our benign use tier: the classifier now triggers less often on defensive tasks like secure coding, patching already identified vulnerabilities, incident response, containment, and defensive configuration management." Fable 5.1 still triggers more than Opus 5 and Sonnet 5, because Anthropic deliberately chose a "wider safety margin" given Fable 5.1's higher cyber capability. The launch post claims "more than 95% of Fable sessions involve no fallback at all" ([Introducing Claude Fable 5 and Mythos 5](https://www.anthropic.com/news/claude-fable-5-mythos-5)) — but the tail is heavy for security workloads: one defensive-CTI operator measured 2,746 of 3,427 assistant messages served by Opus 4.8 after fallbacks in a single day (issue [#67305](https://github.com/anthropics/claude-code/issues/67305)).

**Data retention.** Fable 5.1 and Mythos 5.1 require 30-day data retention, are Covered Models, and are "not available under zero data retention (ZDR) arrangements unless expressly authorized by Anthropic." On the API a request from a ZDR org returns `400 invalid_request_error` ([Fable 5.1 migration guide](https://platform.claude.com/docs/en/models/fable-5-1/migration-guide)). The retained data is used only for safety monitoring, not training, and is deleted after 30 days ([Introducing Claude Fable 5](https://www.anthropic.com/news/claude-fable-5-mythos-5)). Consumer, Team, and Enterprise chat plans are unaffected; the constraint bites ZDR-configured API/Console/Bedrock/Vertex/Foundry orgs ([support: data retention](https://support.claude.com/en/articles/15425996)).

## 4. Detailed spec: what the skill should instruct

### 4.1 Route the risky roles to Opus up front

The skill declares two predefined Opus-pinned subagents (frontmatter in §6) and, in SKILL.md, an unconditional rule: **all security-review and severe/adversarial-testing work runs on the `security-reviewer` and `severe-tester` subagents, which are pinned to Opus. The Fable orchestrator never puts raw exploit strings, attack payloads, malware samples, or offensive pentest instructions into its own turn.** Rationale, in order of weight:

1. In headless mode a Fable classifier flag ends the turn — there is no automatic rescue, so the work must already be on a model that will do it.
2. If the Fable *orchestrator* trips its own classifier interactively, the switch to Opus is sticky for the rest of the session; the whole run silently degrades to Opus and loses the model you chose it for. Keeping attack material out of the orchestrator's turns prevents that.
3. Opus has a lower false-positive rate than Fable and is the designated fallback target regardless — so you pay no capability penalty by routing there deliberately.
4. This exactly matches the owner's routing policy (Opus for hard-but-bounded) and needs no special-casing.

Source-code security review, auth/crypto implementation, prompt-injection hardening, and dependency-CVE triage are *allowed* at GA on both Fable and Opus, but they sit close enough to the boundary to flag intermittently. Running them on Opus makes the flag rare and, when it happens, recoverable rather than terminal.

### 4.2 Detection: distinguish a block from a real error

The orchestrator sees subagent outcomes as Agent-tool results and sees its own transcript. The decision procedure (put this verbatim in a `references/safety-boundary.md`):

```
When a step returns without the expected result, classify before retrying:

1. stop_reason == "refusal"  (API/SDK)           → CLASSIFIER OR MODEL DECLINE.
     Read stop_details.category.
       cyber            → re-dispatch to Opus (security-reviewer / severe-tester).
       bio              → re-dispatch to Opus 5; if Opus 5 also declines, STOP and surface.
       reasoning_extraction / frontier_llm / general_harms / null
                        → NO fallback exists. STOP and surface. Do not re-route.
2. Transcript shows a "model_refusal_fallback" / "model_refusal_no_fallback"
   system event, or an "API Error: <model>'s safeguards flagged this message"
   line, or the "Switched to Opus" notice
                                                  → CLASSIFIER BLOCK. Same routing as (1).
3. "Agent terminated early due to an API error: <detail>"
                                                  → read <detail>:
       429 / 529 / 5xx      → REAL, retryable. Back off and retry (harness already does).
       400 invalid_request  → REAL, non-retryable. Likely ZDR/param. Fix config, don't loop.
       401 / 403            → REAL, auth/policy. Stop; this is not a classifier block.
4. HTTP 4xx/5xx with no refusal      → REAL API error. Handle per error code.
5. Model wrote a plain-prose "I can't help with that" with stop_reason == "end_turn"
                                                  → ordinary decline (rare). Rephrase once;
                                                    do not treat as a code bug.

NEVER: treat any of the above as evidence of a bug in the code under test until
the block/error is ruled out. A classifier decline is a statement about the
request, not about the code.
```

The load-bearing rule for the owner's "second time is the bug" discipline: **a repeated identical refusal is not a flaky test — it is the same classifier decision.** The Usage-Policy check evaluates the whole conversation and persists across `--continue`/`--resume`, so re-running the same transcript re-triggers it every time. Looping is futile; the fix is to change model or change the request, once.

### 4.3 Logging to STATE.md

Every block gets one line in STATE.md so the run is auditable and the next session resumes instead of re-deriving. Add a dedicated section:

```
## Safety-boundary events            # classifier declines and re-routes
- 2026-09-14 11:02Z · step: severe-testing/sql-injection · category: cyber
  · action: re-dispatched to severe-tester (Opus 5) · result: completed
- 2026-09-14 11:40Z · step: research/pathogen-dataset-loader · category: bio
  · action: Opus 5 also declined (no fallback) · SURFACED to user · run paused
```

The distillation loop (post step 12) should promote a recurring block into a *rule*, not just a note — e.g. "Binary-diffing tasks flag `cyber` on Fable and Opus alike; scope security review to source only, or ask the owner about the Cyber Verification Program."

### 4.4 The retry-on-Opus rule (orchestrator)

Because the risky roles are already Opus-pinned (§4.1), the common case never reaches a retry. The retry rule covers the residual case where a non-security step trips a flag (a research step touching a biology dataset, say):

1. Detect per §4.2. If category has a fallback and the failing unit of work is delegable, **re-dispatch that unit to a fresh Opus-pinned subagent** with the same task text (fresh context avoids carrying a poisoned transcript). Log to STATE.md.
2. Retry at most **once** per unit on the fallback model. A second identical decline means the request itself is out of bounds — stop.
3. Never retry the same prompt on the same model. Never wrap the retry in a `/goal` loop (the loop will re-trigger forever on the persisted transcript).

### 4.5 Surface to the user — once, directly

Per the owner's "no approval queues, surface one choice directly" rule: surface only when **both** Fable and Opus decline, or when the category has no fallback. The message states the plain-language reason, the category, what was tried, and the one decision:

> The security review of `crypto/keywrap.rs` was declined by the safety classifier as cybersecurity-adjacent, on both Fable and Opus 5. I can (a) skip this file's deep review and note it in STATE.md, or (b) you can run this step yourself, or apply for the Cyber Verification Program for uninterrupted access. Which?

No inbox, no queue, no "it will run later." One question, in conversation, then the run continues or pauses cleanly.

## 5. Conditionals by project shape

- **Greenfield app (fashion/outfit iOS + Cloudflare):** high relevance. Auth, session tokens, and any payment integration are `cyber`-adjacent; run their review on `security-reviewer`. The iOS/Swift and CF Worker code itself is ordinary and stays on Fable/Sonnet. Severe testing of the API (authz bypass, injection) runs on `severe-tester`. No biology exposure.
- **Deep bug hunt:** low relevance unless the bug is in auth/crypto/parsing of untrusted input. If it is, the *investigation* (reading the vulnerable code, writing a refuting test) belongs on `security-reviewer`/`severe-tester`. A plain logic bug never touches the boundary.
- **Feature on existing product (dashboard):** low-to-medium. Only the auth/RBAC and any query-building paths matter; route those, leave the rest.
- **Migration/consolidation (AI gateway into core service):** medium-high and easy to under-estimate. Gateway/failover/circuit-breaker code reads as security-adjacent to the classifier — issue [#67246](https://github.com/anthropics/claude-code/issues/67246) is exactly this: a Bedrock provider-failover design tripped the flag on vocabulary like "outage," "failover," "circuit breaker." Expect first-request flags from the repo context; run with `--safe-mode` once to confirm whether CLAUDE.md is the trigger, and route the security review to Opus.
- **Research + website:** medium if the research topic is biology, chemistry, cybersecurity, or frontier-AI. The `deep-research` step can flag `bio`/`frontier_llm`; those have **no fallback**, so the skill must be ready to surface, not silently drop sources. The website build itself is boundary-free.
- **Pure research report:** as above — topic-dependent; the only shape where `bio`/`frontier_llm`/`reasoning_extraction` (no-fallback categories) are the likely ones.
- **Refactor/simplification, CLI tool, library/SDK, data pipeline:** boundary-free unless they contain crypto or parse untrusted input. Skip the security roles unless the intake classifier detects those elements. Do not impose the ceremony where it doesn't pay.
- **Ops/incident:** medium — incident response and containment are explicitly in the *benign* tier the system card says Fable 5.1 blocks less often, but "less often" is not "never." Route the forensic/exploit-analysis parts to Opus.

Conditional the skill needs: **if the task or repo involves cybersecurity, auth/crypto, exploit/pentest, biology/chemistry, or frontier-model training, then (a) pin the relevant roles to Opus, (b) run one `--safe-mode` probe to see if repo context is a standing trigger, and (c) pre-write the STATE.md safety-boundary section.** Otherwise skip all of it.

## 6. Model and effort assignment, with draft subagent definitions

Both roles are hard-but-bounded → **Opus**, at **high** effort (raise to `xhigh` for the final adversarial pass on security-critical code). They read and write within the repo, run tests, and are the natural home for attack payloads. They should be **predefined subagents** in `~/.claude/agents/` (shipped with the skill's plugin, or installed alongside it), so their Opus pin and system prompt are stable and not re-derived each run. Draft frontmatter and system prompts:

```markdown
---
name: security-reviewer
description: Reviews code for real security defects — authn/authz, injection,
  secrets handling, crypto misuse, SSRF, deserialization, prompt-injection in
  LLM apps, and dependency CVEs. Runs on Opus so classifier flags are rare and,
  when they happen, recoverable. Use for any auth/crypto/untrusted-input path.
model: opus
effort: high
tools: Read, Grep, Glob, Bash, WebFetch
memory: project
---
You review source code for genuine, exploitable security defects. Work from the
source: name each finding's concrete attack path, the file and line, and a
minimal fix. Prefer proof over assertion — where you can, write or describe a
test that demonstrates the defect. You review only code in this repository and
systems the user owns; you never exercise an exploit against a live third party.
You do not enter credentials, keys, or payment data anywhere. Vulnerability
discovery in this project's own source is in scope; reverse-engineering compiled
third-party binaries is not — say so and stop if asked. Report findings ranked
by severity with the behavioural claim each one refutes. If a task is declined by
a safety classifier, say which category and stop; do not loop.
```

```markdown
---
name: severe-tester
description: Adversarial, security-focused testing — abuse cases, fuzzing,
  property-based tests, authz-bypass and injection e2e tests, failure-mode and
  stress tests that try to REFUTE the implementation's claims. Runs on Opus.
  Use after any implementation or bug fix that touches untrusted input, auth, or
  crypto, or when the user asks for severe/adversarial/red-team testing.
model: opus
effort: high
tools: Read, Grep, Glob, Bash, Edit, Write
memory: project
isolation: worktree
---
You are the independent verifier, not the maker. You did not write this code and
you owe its conclusions nothing. For every behavioural claim, write at least one
test that tries to break it: malformed input, boundary values, concurrent access,
injection and authz-bypass payloads against THIS system only, resource
exhaustion, and the failure modes the maker did not consider. Ask of every test
harness: where is it kinder than production? A shim that accepts what the real
system rejects certifies broken code. Run destructive test operations only
against disposable local state, and record how to undo anything you change.
Report each test, the claim it targets, and pass/fail with evidence. If a
classifier declines a task, name the category and stop; never re-run the same
blocked prompt.
```

Notes: the `severe-tester` runs in a worktree so its adversarial edits and disposable test state never touch the canonical checkout, and — per the owner's rule — the skill merges-and-deletes that worktree in the same step, never as an epilogue. Both inherit `memory: project` so their findings and any boundary events land in the shared STATE.md. The orchestrator stays on **Fable 5.1** and dispatches to these two via the Agent tool; it never inlines attack material into its own context.

## 7. Failure modes and anti-patterns

- **Silent failure on a block (the headline risk).** In headless mode a flag ends the turn; if the orchestrator treats an empty/short result as "step done," it produces mirage completion — a green run over work that never happened. Prevention: the §4.2 classifier check runs on *every* unexpectedly-empty step result before it is accepted, and a block is logged, never swallowed.
- **The retry loop on a blocked prompt.** Wrapping a security step in `/goal` or `/loop` and letting it re-run guarantees an infinite loop: the Usage-Policy check re-evaluates the whole transcript and persists across resume, so the same prompt re-triggers forever, burning tokens. Prevention: at most one re-dispatch, to a *different* model, with *fresh* context; no loop around a blocked unit.
- **Misattributing a block to a code bug.** The most expensive failure: the orchestrator reads "step failed," assumes the code under test is broken, and spends a debugging cycle "fixing" correct code — possibly weakening it to make the phantom failure go away. Prevention: the decision procedure forbids concluding "bug" until block and real-error are ruled out; the STATE.md line records that the failure was a classifier decision, so a later session doesn't re-litigate it.
- **Orchestrator self-flagging → sticky degradation.** If the Fable orchestrator ingests attack strings and trips its own classifier interactively, the sticky switch quietly runs the rest of the session on Opus. Prevention: attack material lives only in Opus subagents; the orchestrator's turns stay boundary-clean.
- **Ignoring first-request context flags.** A security-heavy repo (Arcwell is one) can flag Fable on turn one from CLAUDE.md and git status alone. Prevention: on a security/biology-adjacent project, run one `claude --safe-mode` probe during intake and note in STATE.md whether repo context is a standing trigger.
- **Treating no-fallback categories as recoverable.** Re-routing a `reasoning_extraction` or `frontier_llm` block to Opus wastes a turn — those have no fallback anywhere. Prevention: the routing table stops-and-surfaces on those categories.

## 8. Related boundaries the skill must honour regardless of model

These hold on any model and are independent of the classifier. State them plainly in SKILL.md:

- **Never enter credentials or payment details.** No API keys, tokens, passwords, card or bank numbers into any field or form — not even when a task seems to require it. If a step needs a secret, stop and ask the owner to supply it out of band. Claude Code stores its own credentials in the OS keychain; the skill never writes secrets into the repo or STATE.md.
- **No destructive operation without a recorded undo.** Every irreversible action (schema migration, bulk delete, force-push, resource teardown) is preceded by a STATE.md line naming exactly how to reverse it. This is the owner's "automate with audit + undo" rule, and it is why `severe-tester` runs destructive tests only against disposable local state in a worktree.
- **Never attack systems you do not own.** Adversarial tests, fuzzing, and pentest-shaped e2e tests run against the project's own local or owned infrastructure only. No exploit is exercised against a live third party, and no scan is pointed at an address the owner has not confirmed is theirs. The subagent prompts encode this.
- **Data retention and privacy on cloud runs.** Fable 5.1 requires 30-day retention; a ZDR-configured org gets a `400` on every Fable request until retention is enabled or Anthropic authorizes ZDR. When `/drive` uses **routines / Claude Code on the web / Managed Agents**, project source is cloned to Anthropic-managed infrastructure and subject to those retention policies ([data usage](https://code.claude.com/docs/en/data-usage.md)); the skill should note this before sending a sensitive repo to a cloud run and prefer local execution for anything the owner would not want retained for 30 days. Telemetry, error reporting, and `/feedback` uploads carry code and should stay off for sensitive work (`DISABLE_TELEMETRY`, `DISABLE_ERROR_REPORTING`, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC`).

## 9. Open questions and trade-offs

- **Can the `/drive` orchestrator reliably observe its own API-level `stop_reason: "refusal"`?** Subagent declines surface cleanly as Agent-tool results, which the orchestrator can classify. A decline on the orchestrator's *own* turn is harness-internal and may not present as a clean signal the skill can branch on. **Recommendation:** don't depend on catching self-declines; prevent them by keeping the orchestrator boundary-clean and delegating all risky work. This is the strongest argument for pin-by-default over rescue-on-block.
- **Pin-by-default vs. run-on-Fable-then-fallback.** Fallback preserves Fable's edge on the rare security task Fable would handle, but costs a wasted turn, risks sticky degradation, and dies silently in headless mode. **Recommendation:** pin by default. The capability loss is marginal (Opus is strong and is the fallback target anyway); the reliability gain in a headless, autonomous skill is large. Revisit only if Anthropic ships headless auto-fallback with a signal the skill can read.
- **Cyber Verification Program.** For an owner who does substantive security work, CVP access (or a trusted-access program for Fable-class capability) would remove most of this friction. That is an account-level action the owner must take; the skill can only surface the suggestion. **Recommendation:** when the safety-boundary section of STATE.md accumulates repeated `cyber` blocks on legitimate work, distil a one-time note recommending CVP, and stop re-flagging it each run.
- **`switchModelsOnFlag` in interactive `/drive` sessions.** When the owner runs `/drive` interactively rather than headless, leaving auto-switch on means a Fable orchestrator can go sticky-Opus mid-run. **Recommendation:** the skill documents `switchModelsOnFlag: false` as the preferred setting for `/drive` work, so a flag pauses with a choice rather than silently rewriting the session's model — but does not change the setting itself (that is the owner's config).

## 10. Skill text candidates (lift into SKILL.md or references/safety-boundary.md)

1. *The fallback to Opus is not automatic here.* On the API and in headless Claude Code, a safety-classifier flag ends the turn with a refusal — nothing switches models for you. Automatic switching is a Claude-app behaviour, not something a self-driving skill can rely on. Route around the boundary before it bites; don't wait to be rescued.

2. *Pin the risky roles to Opus from the start.* Security review and severe/adversarial testing run on the `security-reviewer` and `severe-tester` subagents, which are pinned to Opus. The Fable orchestrator never puts raw exploit strings or attack payloads into its own turn, so it never trips its own classifier and gets stuck on a sticky switch.

3. *A block is a statement about the request, not about the code.* When a step returns empty or short, classify it before you touch the code: a `stop_reason: "refusal"`, a `model_refusal_fallback` event, or a "safeguards flagged this message" line is a classifier decision. Never spend a debugging cycle "fixing" correct code to make a phantom failure disappear.

4. *Read the category; it tells you whether re-routing helps.* `cyber` falls back to Opus 4.8, `bio` from Fable to Opus 5. But `reasoning_extraction`, `frontier_llm`, and `general_harms` have no fallback anywhere — re-routing them wastes a turn. Stop and surface those.

5. *Retry once, on a different model, with fresh context.* Never re-run a blocked prompt on the same model, and never wrap it in `/goal` or `/loop`. The usage check reads the whole transcript and persists across resume, so a loop re-triggers forever. One re-dispatch to Opus with a clean context, then stop.

6. *Log every boundary event to STATE.md.* One line: timestamp, step, category, action taken, result. A recurring block becomes a distilled rule, so the next run consults it instead of re-hitting it.

7. *Surface once, directly, only when both models decline.* No inbox, no queue. State the plain-language reason and the single choice — skip and note it, or the owner runs it themselves — then continue or pause cleanly.

8. *Source is in scope; third-party binaries are not.* Vulnerability discovery in this project's own source code is allowed at general availability. Reverse-engineering compiled third-party binaries is blocked by design — don't try to route around it.

9. *A security-heavy repo can flag on turn one.* CLAUDE.md content and git status travel with the first request and can trip the classifier before you ask anything. On a security- or biology-adjacent project, run one `claude --safe-mode` probe during intake to see whether the repo context itself is the trigger, and record the answer.

10. *Model-independent boundaries hold regardless of the classifier.* Never enter credentials or payment data. No destructive operation without a recorded undo. Attack only systems the owner owns, from disposable local state. And before sending a sensitive repo to a cloud run, remember Fable requires 30-day retention — prefer local execution for anything you would not keep for a month.
