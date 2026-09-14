# 06 — Independent verification and heavy adversarial review

Research lane report for the mission skill. Component: independent verification, maker/checker separation, adversarial
review types, findings model, review economics and convergence, loop graders.

Evidence conventions: `Lnn` = line number in the named workspace file; URLs = fetched pages (see Sources). Statements
marked "inference" are my reasoning, not something a source says.

## 1. Executive summary & strong opinions

The evidence is unusually consistent: models are bad judges of their own work, separate judges are better but still
lenient, and adversarial review only pays when a stop rule bounds it. The user's own project shows the cost of that last
point. Milestone 1 of `arcwell` went through **eighteen** adversarial rounds. Every round rejected closure. Each round
found roughly 7–19 new defects, and a steady share of them came from the previous round's fixes. Closure did not come
from convergence. It came from an owner decision to stop (`arcwell/docs/operations/m1-eighteenth-review-disposition.md`
lines 3–6, 53–57; `review-process-amendment.md` lines 3–5). The skill has to keep that rigor while adding stop rules
that fire much earlier and on purpose.

Verdicts the skill should encode:

1. **The maker never grades itself.** Every gate ("done", "passes", "ready") is flipped only by a verifier running in
   a fresh context. It gets the artifact, the acceptance criteria and the evidence, never the maker's transcript or
   reasoning. Self-review is allowed as a cheap pre-flight. It never counts as verification.
2. **Programs judge before models do.** Tests, typecheck, lint, mutation runs, link checkers and schema validators run
   first. A model verifier reads their *output*. It does not guess at what they would say. Kamoi et al. find
   self-correction works "in tasks that can use reliable external feedback" (https://arxiv.org/abs/2406.01297).
3. **A finding without evidence is not a finding.** A finding needs `file:line` plus either a reproduction (command
   and observed output) or a written construction precise enough to turn into a test. Anything else is filed as a
   *question*, and questions cannot block.
4. **Assume broken until proven, but grade against the contract.** A verifier starts from FAIL and moves to PASS only
   when it has cited evidence for each criterion. It may not invent criteria mid-review. New concerns go into a
   separate "outside-contract" list, and the orchestrator triages that list.
5. **Change the reviewer, not just the context.** Use a different model or effort level than the maker, at least for
   blocker-capable reviews. The Claude family is one model family, so a lens panel (different prompts and evidence)
   is the diversity lever. Model-family diversity (https://arxiv.org/abs/2404.18796) is not available here.
6. **Re-review covers the fix and its blast radius, not the whole world.** Arcwell's re-reviews kept finding defects
   *introduced by the remediation* (14 in round 2, `m1-rereview-disposition.md` lines 5–7; 5 of 19 in round 16,
   `m1-sixteenth-review-disposition.md` line 8). So every fix gets a scoped re-review. A full re-review of an unchanged
   surface is waste.
7. **Hard round caps, then escalate or accept residuals.** Default cap per surface: S=1, M=2, L=3, XL=4 adversarial
   rounds. After the cap, the options are (a) record residuals with rationale, (b) escalate to a human, or (c) change
   the design. Round N+1 of the same process is not an option.
8. **Stop on severity, not on count.** A round that yields no new blocker or major that survives refutation closes
   the gate. Minors and nits are logged and never trigger another round.
9. **Consolidate review where interactions matter.** Arcwell's amendment moved heavy review to one cross-milestone
   review after the vertical product existed. That review found cross-surface defects that could not exist earlier
   (`review-process-amendment.md` lines 26–31; `m2-m7-review-disposition.md` 23 findings). The skill should gate
   milestones on automated checks and schedule adversarial review at integration points.
10. **Disposition every finding, in writing.** Allowed outcomes: FIXED (with the test that proves it), REFUTED (with
    evidence), RESIDUAL (with rationale and owner), DEFERRED (with milestone and owner), CONTESTED (escalated). Silently
    narrowing a finding counts as a defect. Arcwell's disposition docs are the model to copy
    (`m1-third-review-disposition.md` lines 47–50).
11. **Verify the verifier's instruments.** Arcwell caught stale mutation targets (round 5), "non-causal" kills (rounds
    10–17) and a reviewer that lacked the test files (M2–M7, lines 55–58). The skill must spot-check that each checker
    can fail for the reason it names.
12. **Security review goes straight to Opus 4.8.** Fable 5.1's classifiers can refuse benign security work (`category:
    "cyber"`, https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback). Plan for that route instead
    of discovering it mid-loop.
13. **Graders are rubrics with binary, evidence-bound criteria.** Use scored scales only for taste (design), and
    calibrate those with anchors. For code correctness a pass/fail list works better.
14. **Cheap verifiers are fine for checkable criteria and dangerous for judgment.** Sonnet 4.6 low can confirm
    "command X exited 0 and output contains Y". It cannot judge whether a concurrency design is sound. Downgrades are
    guarded by spot-checks from a higher tier.

## 2. Claim check

| # | Post claim (component area) | Verdict | Evidence | What the skill should do |
|---|---|---|---|---|
| C1 | "Anthropic engineer Prithvi Rajasekaran wrote a piece on the engineering blog showing models have a hard time self-critiquing their own outputs." | **Verified (paraphrase is fair).** The post, "Harness design for long-running application development" (Mar 24 2026), says agents "tend to respond by confidently praising the work—even when… the quality is obviously mediocre". It adds a nuance the post drops: separation "doesn't immediately eliminate that leniency". | https://www.anthropic.com/engineering/harness-design-long-running-apps | Separate maker and verifier, *and* tune the verifier to be skeptical (anchors, evidence rules). Separation alone is not enough. |
| C2 | "The Claude Code team confirmed this empirically with Fable 5: 'We've found that a verifier sub-agent tends to outperform self-critique with Fable 5'." | **Quote verified; attribution slightly off.** The sentence is in Lance Martin's X article "Designing loops with Fable 5" (Jun 9 2026). It continues "because grading is done in an independent context window. Outcomes in CMA handles this by spawning a grader sub-agent for you." It is presented as a small-scale experiment, not a confirmation from the Claude Code team. | https://x.com/RLanceMartin/status/2064397389189071163 | Treat it as practitioner evidence consistent with the literature, not a benchmark. The mechanism it names (independent context) is what the skill must preserve. |
| C3 | "A model evaluating its own output sees its own reasoning trail and prefers conclusions consistent with what it already wrote. A separate model… sees only the artifact and the rubric." | **Plausible and supported by adjacent research, but not stated by Anthropic in these words.** Self-preference bias is documented (https://arxiv.org/abs/2404.13076, https://arxiv.org/abs/2306.05685). Intrinsic self-correction can *degrade* reasoning (https://arxiv.org/abs/2310.01798). | papers above | Encode context isolation (the verifier gets no maker transcript). Also note that a same-family verifier still shares biases: isolation fixes anchoring, not self-preference. Hence different effort or model, and evidence rules. |
| C4 | Parameter Golf: Fable 5 with independent verifier explores larger hypothesis spaces; "Without the verifier, the same model has nothing forcing it past the first 'good enough.'" | **Partly verified, partly post-invented inference.** Martin reports ~6x more improvement than Opus 4.7, structural vs scalar experiments, and pushing through a quantization regression. The Outcomes grader "confirmed that all experimental criteria were met before allowing Claude to stop". He compares *models*, not verifier vs no-verifier. The causal claim about the verifier is the post's. | same X article | Don't cite Parameter Golf as proof that verifiers work. Cite it as proof that a rubric with *checkable process criteria* (e.g., "run 20 experiments") stops early exit. |
| C5 | /goal and Outcomes both use "an independent grader"; "the agent that wrote the code is not the agent that grades it." | **Partly verified (by sibling lane R01).** Outcomes uses a separate grader context. R01 found the /goal evaluator reads only the transcript and defaults to a small model, so it is not a trustworthy gate (`research/mission-skill/99-synthesis-notes.md` line 10). | R01 notes | Gates are flipped by the skill's own verifier sub-agent reading evidence files, or by a Stop hook running `check.sh`. /goal can serve as a loop driver, not as the verifier. |
| C6 | Dynamic Workflows "adversarial verification" pattern: "for each maker agent, spawn an independent verifier with no exposure to the maker's reasoning." | **Feature verified; the six-pattern taxonomy not verified here.** The docs say workflows "can have independent agents adversarially review each other's findings before they're reported". `/deep-research` "votes on each claim" and reports unverifiable claims as unverified "instead of counting it as refuted". | https://code.claude.com/docs/en/workflows | Copy the three-valued verdict (confirmed / refuted / unverified) into the finding model. Use workflows when available. Degrade to Agent-tool sub-agents otherwise. |
| C7 | Haiku 4.5 for grader sub-agents, "ideal for the verifier role Anthropic explicitly recommends". | **Overridden by user; claim of explicit recommendation of Haiku as verifier unverified.** Anthropic's eval guidance stresses that model graders need "calibration with human graders" (https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents). It does not endorse small models as universal verifiers. | Anthropic evals post | Use Sonnet 4.6 low for checklist graders, with higher-tier spot-checks (§5). |
| C8 | Security tooling / "some code review" on Fable 5 → expect classifier blocks; route to Opus 4.8. | **Verified in mechanism.** Refusal returns `stop_reason: "refusal"` with category `cyber`. "Benign cybersecurity work can also trigger this category." Mid-stream refusal → discard partial output. The post's "chemistry" category is not in the docs' list. | https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback | Security, pentest and exploit-construction review is assigned to Opus 4.8 up front. Partial reviewer output after a refusal is discarded, not graded. Log the fallback event. |
| C9 | "Mistakes: Self-critique instead of an independent verifier… loops stop at 'handled enough' instead of done." | **Supported.** Rajasekaran's evaluator needed tuning because it "would identify legitimate issues, then talk itself into deciding they were not a big deal" (secondary summary: https://understandingdata.com/posts/generator-evaluator-harness-design/). | as cited | Graders MUST NOT downgrade severity in their own write-up without a stated refutation. |
| C10 | (Implicit) more adversarial review = more quality. | **Contradicted by user's evidence when unbounded.** Eighteen rounds never converged on "no findings". Remediation kept introducing defects, and closure came by owner direction. | arcwell docs (§3.4) | Round caps, severity-based stopping, scoped re-review, consolidation at integration points. |

## 3. Deep findings

### 3.1 Why self-critique fails, and what actually fixes it

- **Intrinsic self-correction is unreliable.** Huang et al. (ICLR 2024) find that LLMs "struggle to self-correct their
  responses without external feedback, and at times, their performance even degrades after self-correction"
  (https://arxiv.org/abs/2310.01798). Kamoi et al.'s TACL survey goes further: "no prior work demonstrates successful
  self-correction with feedback from prompted LLMs, except for studies in tasks that are exceptionally suited for
  self-correction", while "self-correction works well in tasks that can use reliable external feedback"
  (https://arxiv.org/abs/2406.01297). For the skill, the value of verification comes mostly from *external signal*
  (executed tests, rendered screenshots, database state, fetched sources). A second opinion helps less. A verifier that
  only reads the diff and thinks is the weakest kind.
- **Judges prefer themselves.** Panickssery, Bowman & Feng show self-preference ("an LLM evaluator scores its own
  outputs higher than others' while human annotators consider them of equal quality"). The effect correlates linearly
  with the model's ability to recognize its own text (https://arxiv.org/abs/2404.13076). Zheng et al. catalogue
  position, verbosity and self-enhancement biases. They also show strong judges can still reach >80% agreement with
  humans, the same as human–human agreement (https://arxiv.org/abs/2306.05685). Two implications follow. First, context
  isolation alone does not remove self-preference, because a Sonnet verifier grading Sonnet output still recognizes the
  style. Second, judges are usable when criteria are concrete and biases are controlled (position swaps, length-blind
  criteria).
- **Separation is necessary but not sufficient.** Rajasekaran's harness post is the most practically relevant source.
  Agents grading their own work "reliably skew positive". Separating generator and evaluator "proves to be a strong
  lever", yet "the evaluator is still an LLM that is inclined to be generous towards LLM-generated outputs". The key line
  for the skill: "tuning a standalone evaluator to be skeptical turns out to be far more tractable than making a
  generator critical of its own work" (https://www.anthropic.com/engineering/harness-design-long-running-apps). He
  calibrated with "few-shot examples with detailed score breakdowns", gave the evaluator Playwright so it acted on the
  live page, and ran 5–15 iterations. He also observed that criteria *wording* steers the generator ("museum quality"),
  and that he sometimes preferred a middle iteration over the last. The skill should therefore keep the best iteration,
  not only the latest. A secondary summary reports the evaluator initially "would identify legitimate issues, then talk
  itself into deciding they were not a big deal", and that generator and evaluator negotiated "sprint contracts" of
  testable criteria before building (https://understandingdata.com/posts/generator-evaluator-harness-design/). Those
  details come from a summary, not the primary page. The fetch was truncated at 10 KB. See §9.
- **Independent context is the named mechanism.** Martin: "a verifier sub-agent tends to outperform self-critique with
  Fable 5, because grading is done in an independent context window". The Outcomes grader worked from a rubric file with
  nine *checkable* criteria (https://x.com/RLanceMartin/status/2064397389189071163). Claude Code sub-agents give exactly
  this: "Each subagent runs in its own context window with a custom system prompt, specific tool access, and independent
  permissions", and built-in Explore/Plan agents have Write/Edit denied (https://code.claude.com/docs/en/sub-agents).
- **Anthropic's grader taxonomy.** Code-based graders are "Fast, Cheap, Objective, Reproducible" but brittle.
  Model-based graders are flexible but "Non-deterministic… Requires calibration with human graders for accuracy". Human
  graders are the gold standard. The outcome is "the final state in the environment", not what the agent says ("Your
  flight has been booked" vs. a reservation existing) (https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).
  The skill's verifier should grade *outcomes and evidence*, never the maker's summary.
- **Evaluator-optimizer fits only with clear criteria.** Anthropic's patterns post: the loop works "when we have clear
  evaluation criteria, and when iterative refinement provides measurable value". Voting fits security review, "where
  several different prompts review and flag the code if they find a problem"
  (https://www.anthropic.com/engineering/building-effective-agents).

### 3.2 Panels, lenses and verification of findings

- **Panels beat a single big judge, when they are diverse.** PoLL found a panel of smaller models from *disjoint
  families* "outperforms a single large judge, exhibits less intra-model bias… while being over seven times less
  expensive" (https://arxiv.org/abs/2404.18796). This skill has only Claude models. Diversity has to come from lenses
  (different prompts, evidence and personas), effort levels and tiers, so bias reduction will be weaker than PoLL
  reports (inference).
- **Anthropic's own review product is a lens panel plus a refutation pass.** Claude Code Review: "multiple agents
  analyze the diff… Each agent looks for a different class of issue, then a verification step checks candidates against
  actual code behavior to filter out false positives. The results are deduplicated, ranked by severity". Severities are
  *Important* (fix before merge), *Nit*, *Pre-existing*. Default scope is "correctness: bugs that would break
  production, not formatting preferences or missing test coverage" (https://code.claude.com/docs/en/code-review). The
  skill should copy this shape (lenses → refute → dedupe → rank) and the *Pre-existing* category, which keeps reviews
  from blocking on inherited debt.
- **Three-valued verdicts.** `/deep-research` cross-checks, "votes on each claim", and lists claims verifiers could not
  check "as unverified instead of counting it as refuted" (https://code.claude.com/docs/en/workflows). A verifier outage
  must never read as a pass or a fail.

### 3.3 Human review economics that transfer

The SmartBear/Cisco study (https://smartbear.com/learn/code-review/best-practices-for-peer-code-review/) reports:
review 200–400 LOC over 60–90 minutes for 70–90% defect discovery; detection falls beyond 400 LOC and above 500 LOC/h;
checklists are "the most effective way… to combat the challenges of omission finding"; lightweight review takes <20% of
formal inspection time and "finds just as many bugs". LLM reviewers do not tire the same way, but long diffs dilute
attention in a context window (inference, consistent with Rajasekaran's context-coherence discussion). The transferable
rules: **chunk review units** (≈≤400 changed LOC or one coherent surface per reviewer), **use checklists for omission
classes**, and **prefer many light scoped reviews over one heavyweight ceremony**.

### 3.4 Arcwell: eighteen rounds, read as data

Source files (read-only): `arcwell/docs/operations/m1-adversarial-disposition.md`, `m1-rereview-disposition.md`,
`m1-third…eighteenth-review-disposition.md`, `review-process-amendment.md`, `m2-m7-review-disposition.md`. Counts are
the verdict summaries in each file's opening lines.

| Round | Verdict and headline counts | Pointer |
|---|---|---|
| R1 | 17 findings; "Milestone 1 must remain open"; 22 expected surviving mutation classes; ~40 requirements demoted | `m1-adversarial-disposition.md` L3–6, L12–15 |
| R2 | 2 of 17 fully closed, 12 partial, 2 not closed; **14 new defects introduced by the rework**; ~24 overstated registrations | `m1-rereview-disposition.md` L3–7 |
| R3 | 11 constructible defects + 12 blocking fixes; "third consecutive review to find real defects in a remediation" | `m1-third-review-disposition.md` L3–10 |
| R4 | 12 closure requirements; 7 new defects introduced by R3's remediation | `m1-fourth-review-disposition.md` L3–12 |
| R5 | "the fourth disposition's 'all twelve FIXED' claim is false"; 12 constructions + 13 defects; mutation target pointing at a string that "occurs zero times" | `m1-fifth-review-disposition.md` L3–14 |
| R6 | 8 directly constructible, 15 named; prior deferral judged "goalpost-moving" | `m1-sixth-review-disposition.md` L3–11 |
| R7 | 15 new + 3 outside remediation; cursor witness "rebuilt rather than patched" | `m1-seventh-review-disposition.md` L3–13 |
| R8 | 13 new; coverage made "a bijection" | `m1-eighth-review-disposition.md` L3–11 |
| R9 | 13 new; only 2 of R8's fixes closed; "a one-to-MANY relation wearing the word 'bijection'" | `m1-ninth-review-disposition.md` L3–15 |
| R10 | 7 new; mutation score overstated ("a green number standing in for a proof") | `m1-tenth-review-disposition.md` L3–12 |
| R11 | 8 new; 11 non-causal mutation targets; 18 live defects with no target; 14 overstated | `m1-eleventh-review-disposition.md` L3–7 |
| R12 | 15 new; 5 non-causal targets; ~26 overstated; a demotion judged goalpost-moving | `m1-twelfth-review-disposition.md` L3–7 |
| R13 | 15 new; ~21 live defects with no target; reviewer *proved* a removed clause redundant | `m1-thirteenth-review-disposition.md` L3–14 |
| R14 | 10 constructions + 18 defects introduced/exposed by R13; 4 non-causal; 9 overstated | `m1-fourteenth-review-disposition.md` L3–8 |
| R15 | 13 constructions (3 created by R14's fixes); 6 non-causal; 13 overstated | `m1-fifteenth-review-disposition.md` L3–10 |
| R16 | 19 constructions, **5 introduced by R15's fixes** ("now the pattern rather than the exception") | `m1-sixteenth-review-disposition.md` L3–10 |
| R17 | 17 constructions; 12 non-causal targets; 16 unproved clauses | `m1-seventeenth-review-disposition.md` L3–6 |
| R18 | "reject closure"; closed anyway "per the owner's direction"; 148/148 mutations killed | `m1-eighteenth-review-disposition.md` L3–6, L49, L53–57 |
| M2–M7 | One consolidated review: 23 findings → 15 fixed code, 2 fixed docs, 5 residual, 1 contested; focused re-review: 7 blockers, "several introduced by round one itself" | `m2-m7-review-disposition.md` L5–7, L93–97, L108–111 |

**What the data shows**

1. **No count convergence.** New-defect counts per round were 14, 11, 7, 13, 15, 15, 13, 13, 7, 8, 15, 15, 18, 13, 19,
   17 (rows above). Across 16 rounds there is no downward trend. Each disposition described the constructions as
   "narrower" and framed that as convergence (R4 L8–12). Narrower did not mean fewer. A reviewer told to find defects in
   a complex stateful substrate will always find some. **"Zero findings" is not a reachable stop condition for an
   adversarial reviewer on non-trivial systems** (inference, strongly supported by the table).
2. **Fixes are the main defect source late in the process.** Remediation-introduced defects are named explicitly in R2
   (14), R4 (7), R14 (18 introduced or exposed), R15 (3) and R16 (5 of 19), and again in the M2–M7 focused re-review.
   Big remediation batches inject new defects. Hence: small fixes, a test per fix, and re-review scoped to the changed
   surface plus its callers.
3. **Recurring defect classes mean the design is wrong, not the patch.** Key/identity delimiting appears in R2 ("6b.
   Delimiter collision in keys", `m1-rereview-disposition.md` L50), R4 ("a delimiter", L10) and R17 ("the delimiter
   identity still lost a capture", `m1-seventeenth-review-disposition.md` L10–21). Cursor/coverage witnessing appears in
   R6–R12. The skill's rule: **the same defect class in two consecutive rounds → stop patching, hold a design review of
   that mechanism.**
4. **Late rounds shift from product defects to instrument defects.** From R10 on, a large share of findings concern
   mutation targets that "cannot fail for the reason they name" and overstated registrations (R10–R17 rows). That work
   matters: it is how the team learned tests passed for wrong reasons (`m1-rereview-disposition.md` L94–97). It is also
   a signal that the product surface itself has reached diminishing returns. It should trigger an *instrument audit*
   (mutation causality, oracle strength) as a separate, bounded task, not another full round.
5. **Honesty machinery worked and should be copied.** Dispositions refused to mark a parent FIXED while a sub-finding
   stayed open (`m1-rereview-disposition.md` L36–38). They recorded residuals "not claimed closed"
   (`m1-third-review-disposition.md` L68–70), judged "goalpost-moving" deferrals (R6 L9–11), and marked findings
   CONTESTED with cited evidence (`m2-m7-review-disposition.md` L39). This is the disposition log the skill should ship.
6. **Reviewer inputs matter.** In M2–M7, two findings were wrong because "the reviewer lacked the test files (not in
   its reference set)" (`m2-m7-review-disposition.md` L55–58). The verifier's evidence bundle must include the tests and
   the gate outputs.
7. **Stopping was a governance act, and the amendment is the right shape.** The owner stopped M1 review because
   "Repeating that remediation loop before implementing any later product surface prevented progress". Consolidated
   review "lets the reviewer test cross-milestone interactions that cannot be constructed while later surfaces are
   absent", while "all automated gates continue to run at each milestone" and "the amendment changes review timing, not
   the quality bar" (`review-process-amendment.md` L18–31). The consolidated review then found cross-surface defects
   (backup omitting whole table families, finding 1; canary/obligation key mismatch contested, finding 21). That supports
   placing heavy review at integration points.
8. **Quality did compound.** Mutation kills grew from 27/27 (`m1-rereview-disposition.md` L91) to 39/39 (R3 L84), 50/50
   (R4 L62) and 148/148 (R18 L49). Integration tests went from 140 (R2 L90) to 283 (R18 L48). The process caught real
   blockers (e.g., a half-finalized revision exposure, `m1-adversarial-disposition.md` L22). The disposition calls R1 "right on every load-bearing point" (L8). My inference is that the highest-value defects
   came in the first few rounds, and later rounds found real but narrower issues at high cost. The documents record no
   token or hour costs, so marginal value cannot be measured from them.

**Derived convergence rules** (normative versions in §4 and §7.5):
- Stop when a scoped round yields **no new blocker/major that survives refutation**.
- **Cap rounds per surface** by scope and escalate afterwards. Never commission round N+1 by default.
- **Scope re-review to the remediation diff plus its blast radius.** Verify each fix against the *finding*, not the
  fix's own test (arcwell's own rule, `m1-rereview-disposition.md` L101–103).
- **Same class twice → design review.** Instrument findings → bounded instrument audit.
- **Consolidate adversarial review at integration points.** Keep automated gates per milestone.
- **Escalate reviewer tier only on disputes** (CONTESTED findings), not on every round.

## 4. Opinionated spec for the skill

Rule IDs are stable so SKILL.md and the references can cite them.

### 4.1 Verification (maker/checker)

- **V1 MUST.** A gate state (`acceptance.json` `passes`, STATUS gate PASSED, task DONE) changes only on a verifier
  verdict. The maker and the orchestrator MUST NOT flip it on their own judgment. This aligns with R01's "only verifier
  flips" (`research/mission-skill/99-synthesis-notes.md` line 6).
- **V2 MUST.** The verifier brief contains only: (a) artifact locations (paths, commit or worktree, URL), (b) the
  acceptance criteria or rubric, (c) the evidence bundle (gate command outputs, test files, screenshots, fetched sources),
  and (d) the spec excerpts the criteria cite. It MUST NOT contain the maker's transcript, reasoning, self-assessment or
  "what I changed and why" prose. A plain diff summary made by `git diff --stat` is allowed.
- **V3 MUST.** Verifiers are read-only on the artifact. Allowed: tools for reading, searching and running declared
  check commands. Disallowed: Write/Edit on source. Enforce this with the sub-agent's `tools` allow-list or a read-only
  worktree. Degrade to prose instruction plus a post-hoc `git status` clean check.
- **V4 MUST.** The verifier re-runs or directly observes evidence. It MUST NOT accept a maker's statement that "tests
  pass". When re-running is too expensive, it verifies that the log artifact exists, has a timestamp after the last
  commit, and matches the command declared in the criteria.
- **V5 MUST.** The verdict is three-valued per criterion: `PASS` (evidence cited), `FAIL` (evidence cited), `UNVERIFIED`
  (the check could not be run; reason stated). Any UNVERIFIED on a required criterion means the gate stays PENDING, never
  PASSED.
- **V6 SHOULD.** The verifier runs on a different model or effort than the maker (§5). For blocker-capable gates
  (release, security, data integrity), the verifier MUST be at least the maker's tier.
- **V7 SHOULD.** Before any build, the verifier and maker agree a **contract**: numbered, testable criteria written
  to `loops/<id>.md`. That follows Rajasekaran's sprint-contract idea (secondary source). Criteria added after the
  build are outside-contract (F6).
- **V8 MUST.** Self-review by the maker is allowed and encouraged as a pre-flight, but it is recorded as `self-check`
  and never satisfies V1.

### 4.2 Adversarial review

- **R1 MUST.** Pick review types from the trigger table (§7.3): a review type runs only when its trigger is present.
  "Review everything with every lens" is forbidden.
- **R2 MUST.** Each reviewer gets **one lens** and a bounded unit: ≈≤400 changed LOC, or one coherent surface (one
  module, one API contract, one screen flow, one document). Larger changes are split across reviewers.
- **R3 MUST.** Reviewers are told explicitly to find defects that would make the artifact fail its purpose. They are
  also told a clean report is a valid outcome and that inventing findings is a failure. This is the anti-nitpick
  counterweight.
- **R4 MUST.** Every candidate blocker/major passes a **refutation pass** before it reaches the maker: a separate
  sub-agent tries to disprove it against the actual code and tests. Only `CONFIRMED` findings block. `REFUTED` findings
  are logged with the refutation evidence. `UNVERIFIED` findings become questions for the orchestrator. This mirrors
  Claude Code Review's verification step (https://code.claude.com/docs/en/code-review).
- **R5 SHOULD.** Use a lens panel (2–4 parallel reviewers with distinct lenses) for L/XL surfaces and integration
  points. Use a single reviewer for S/M or single-lens changes.
- **R6 MUST.** Pre-existing defects outside the change are tagged `pre-existing`. They never block the current
  change. They go to the backlog with an owner.
- **R7 MUST.** Security reviews and exploit construction run on Opus 4.8 (S1–S3).

### 4.3 Findings and dispositions

- **F1 MUST.** Findings use the schema in §7.4: id, severity, lens, location (`file:line` or URL/section), claim,
  evidence (reproduction command + observed output, or a construction precise enough to become a test), expected vs
  observed, impact, and suggested fix class.
- **F2 MUST.** Severity taxonomy: `blocker` (violates a MUST, loses or corrupts data, security exposure, or the
  artifact fails its primary purpose), `major` (wrong behaviour in a supported path, or an overstated claim of
  completion), `minor` (edge case with low impact, maintainability risk), `nit` (style or naming). Plus the
  `pre-existing` flag and the `question` type.
- **F3 MUST.** Every finding gets a disposition in `reviews/<surface>-disposition.md`: `FIXED` (commit + test name that
  fails without the fix), `REFUTED` (evidence), `RESIDUAL` (rationale + owner + where recorded), `DEFERRED` (milestone
  + owner + why deferral is not goalpost-moving), `CONTESTED` (escalated to tier-up adjudicator or human).
- **F4 MUST.** A parent finding may be FIXED only when all its sub-findings are FIXED or have their own disposition
  (arcwell rule, `m1-rereview-disposition.md` L36–38).
- **F5 MUST.** A FIXED disposition is verified against the **finding** (does the original construction now fail?),
  not against the fix's own new test.
- **F6 SHOULD.** Outside-contract concerns go into a separate list the orchestrator triages. They never silently widen
  the gate.

### 4.4 Convergence and stopping

- **C1 MUST.** A surface's review closes when a round produces **no CONFIRMED blocker or major**. Minors and nits never
  trigger another round.
- **C2 MUST.** Round caps per surface: S=1, M=2, L=3, XL=4. This counts the initial round plus scoped re-reviews. At
  the cap with open CONFIRMED blockers: escalate (tier-up adjudication, then human). Otherwise record residuals and
  close.
- **C3 MUST.** Re-review scope = remediation diff + direct callers/consumers + the original findings' constructions.
  A full-surface re-review needs a stated reason (e.g., the fix exceeded 30% of the surface's LOC).
- **C4 MUST.** The same defect class CONFIRMED in two consecutive rounds → stop patching and open a design review of
  that mechanism.
- **C5 SHOULD.** From round 3 on, if more than half of CONFIRMED findings concern the checking instruments (tests that
  pass for the wrong reason, mutation targets, registry claims), switch to a bounded instrument audit task.
- **C6 SHOULD.** For multi-milestone missions, run automated gates at every milestone and adversarial panels at
  integration points (walking skeleton complete, pre-release, pre-cutover), following arcwell's amendment.
- **C7 MUST.** Escalate the reviewer tier only for CONTESTED findings or a missed-defect escape (a defect found later
  that the review should have caught).

### 4.5 Graders and classifier routing

- **G1 MUST.** Loop graders use binary criteria with an evidence field each. Scored scales (0–4) are used only for
  taste dimensions and MUST have anchors with examples.
- **G2 MUST.** Graders start from FAIL ("assume broken until proven"). A PASS without a cited artifact is invalid and
  the orchestrator treats it as UNVERIFIED.
- **G3 SHOULD.** Calibrate the grader before loop use: 3 known-good and 3 known-bad samples (or seeded defects). It
  must classify all 6 correctly, otherwise tighten the anchors.
- **G4 MUST.** The grader cannot soften a finding in its own summary. The verdict is derived mechanically from
  per-criterion results.
- **S1 MUST.** Security review, threat modelling with exploit construction, and fuzz/pentest logic are assigned to Opus
  4.8 from the start.
- **S2 MUST.** If any reviewer returns `stop_reason: "refusal"`, discard partial output, log a fallback event in STATUS,
  and re-run the review on Opus 4.8 with the same brief. Do not rephrase to evade the classifier.
- **S3 MUST.** A refusal is never interpreted as PASS or FAIL. Until the re-run completes, the criterion is UNVERIFIED.

## 5. Model & effort assignment

Tiers: Fable 5.1 (F), Opus 4.8 (O), Sonnet 4.6 (S); effort L/M/H. No Haiku. I did not verify absolute prices in this
lane. The post's figures (Fable $10/$50 per MTok, "~5× Opus") are unverified here, and R01 owns pricing and model IDs.
The reasoning below uses relative cost only. The principle: **spend on judgment, not on reading logs.** Most
verification tokens go to reading command output and code, and that is where Sonnet belongs. Reasoning about whether
a design can break is what needs Opus.

| Role | Default | Escalate to | Why this tier | Guard that protects the downgrade |
|---|---|---|---|---|
| Checklist gate verifier (did command X run, exit 0, output matches Y, file exists, criterion text satisfied by cited line) | **S-L** | S-M when criteria need reading code against spec | Mechanical and evidence-bound, high volume | **Seeded-defect canary**: ~1 in 10 verification units carries a planted failing criterion (e.g., a stale log or a doctored exit code). A miss → S-M for the rest of the mission, and log it. Also R01's agreement test: both tiers on 3 gates, downgrade only if 3/3 agree. |
| Loop grader (per iteration in a maker loop) | **S-M** | O-M for taste or complex correctness | Runs 3–8× per loop; cost multiplies | Every 5th PASS is re-graded by O-M blind. Any disagreement → O-M grades the rest of that loop. Final gate PASS is always re-checked by the gate verifier. |
| Refutation agent (try to disprove a candidate finding) | **S-H** | O-M for concurrency, data integrity, auth | Needs to run code and construct counter-examples. High effort matters more than tier for executing checks. | Refutations of *blocker* findings are sampled 1-in-3 by O-M. A false refutation found → all blocker refutations on O-M. |
| Code review lens: correctness / state / concurrency / data | **O-M** | O-H at integration points; F-M for XL cross-milestone consolidated review | Judgment about invariants and interleavings is where cheaper models miss | Missed-defect escapes (defect later found in code the lens reviewed) are logged. One escape → O-H for that lens. |
| Code review lens: test quality / oracle strength | **S-H** | O-M when mutation survivors are disputed | Mostly executing mutations and reading asserts | Mutation run output is the external oracle, so a model misread is caught by the tool |
| Spec review (ambiguity, contradictions, untestable requirements) | **O-H** | F-M for XL greenfield master specs | Spec defects are the most expensive to find late | Maker ≠ reviewer tier. Blockers go to refutation by S-H against the brief. |
| Design / architecture review | **O-H** | F-M for XL or migrations with irreversible cutover | Architecture judgment; low volume | Human sign-off for L/XL per R01 checkpoints |
| Security review | **O-H** | never Fable (classifier) | Fable 5.1 classifiers can refuse benign cyber work (https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback) | Static analysis and dependency-audit tool output are mandatory evidence. A human review queue applies for auth, crypto and payments. |
| Performance review | **S-H** reading benchmark output | O-M for algorithmic or design review | Numbers come from tools | Benchmarks rerun by the verifier (V4) |
| UX / visual review | per R05: O-M vision verifier | O-H | R05 found Sonnet-low vision unreliable (`99-synthesis-notes.md` line 27) | R05 canaries |
| Research fact-check (claims → sources) | **S-M** with web fetch | O-M for public-facing or contested claims | Fetch, read, compare; volume task | Sample 1-in-5 CONFIRMED claims with O-M; any wrong → re-check all |
| Release-readiness review | **O-M** | O-H for irreversible deploys | Aggregates gate evidence and residual register | Checklist with evidence per item; human checkpoint for deploy |
| Dedupe / rank / format findings | **S-L** | — | Pure transformation | Orchestrator spot-reads |
| CONTESTED adjudicator | **O-H** (maker was S or O-M) / **F-H** (maker was O-H and not security) | human | Tier-up only on disputes (C7) | Adjudicator must cite evidence; a new construction goes back to refutation |
| Orchestrator triage of dispositions | session orchestrator (F-M for L/XL, per R01) | — | Needs the whole picture | Disposition log is file-backed and reviewed at retro |

**Cost rules.**
1. Never put a whole-repo review on O-H. Chunk it (R2) and run lenses on the changed surface.
2. Refutation on S-H is the cheapest way to cut false positives before they cost a maker iteration.
3. A lens panel of 3×S-H plus 1×O-M refuter is cheaper than 1×F-H and covers more angles. This is an inference
   consistent with PoLL (https://arxiv.org/abs/2404.18796), though Claude-only diversity is weaker.
4. Re-review scoped to fixes (C3) typically costs a fraction of the original round. That is inference; arcwell does
   not log costs.
5. Put the cheapest guard first. Deterministic checks (tests, lint, typecheck, link checker, schema validation) always
   run before any model verifier sees the artifact. If they fail, skip the model call.

## 6. Project-shape conditionals

### 6.1 Scale by scope

| Scope | Verification | Adversarial review | Round cap (C2) | Panel | Refutation |
|---|---|---|---|---|---|
| S (one bounded change, ≤~300 LOC) | Gate verifier S-L on acceptance criteria | 1 reviewer, 1 lens chosen by trigger (usually code-correctness O-M, or S-H if trivial) | 1 | no | only if a blocker is claimed |
| M (feature, several files) | Gate verifier per task + loop grader | 1–2 lenses on the changed surface | 2 | optional | blockers + majors |
| L (multi-module feature, migration step) | Per task + milestone verifier | Lens panel at milestone integration points; spec + design review before build | 3 | yes (2–4) | all blockers/majors |
| XL (greenfield platform, service extraction) | Per task + milestone + consolidated cross-milestone | Automated gates per milestone; adversarial panel at integration points (skeleton, pre-release, pre-cutover); one consolidated review F-M/O-H | 4 per surface | yes | all, with O-M sampling |

### 6.2 Shape rules

**Greenfield multi-platform app** (e.g., Swift iOS + Cloudflare backend)
- IF the project has an API contract between platforms THEN run a *contract review* (O-H) before either side is built.
  Contract-conformance tests are the verifier's evidence for both sides.
- IF the walking skeleton is complete THEN run the first adversarial lens panel on the end-to-end path. Do not review
  isolated layers in depth before it exists (arcwell amendment rationale, `review-process-amendment.md` L26–31).
- IF the app has user data, auth or payments THEN the security lens (O-H) is mandatory at pre-release, with human
  queue items for auth and payments.
- IF there is UI THEN visual/UX verification per R05. The adversarial UX persona ("first-time user in a hurry") runs at
  pre-release.

**Deep bug hunt**
- IF the task is a bug fix THEN the verifier's first criterion is "a failing reproduction exists and fails for the
  stated reason" (R01's Reproduced gate). The verifier re-runs it before and after the fix.
- IF a root-cause claim is made THEN run a *refutation review* of the causal story (S-H/O-M): "find an observation
  this explanation does not account for". This is the highest-value review for bugs.
- Adversarial code review is scoped to the fix diff plus call sites (C3), cap 2. No lens panel unless the fix touches
  concurrency or data integrity.
- IF the same bug class recurs in two places THEN apply C4: design review of the mechanism and a lesson to STATE.md.

**Feature in an existing product**
- IF the repo has existing conventions or tests THEN the evidence bundle includes the conventions file (CLAUDE.md) and
  neighbouring tests. The reviewer checks consistency; it does not enforce its own taste.
- Pre-existing defects found → `pre-existing`, non-blocking (R6).
- IF the feature is behind a flag THEN release-readiness review checks the flag default and rollback path.
- Review cap M=2. Lenses: correctness + test quality, plus UX if UI.

**Service migration / extraction** (e.g., AI gateway → core service)
- IF behaviour must be preserved THEN the primary verifier is a *parity verifier*. Its evidence is the parity inventory
  and diffed outputs from old and new paths. Model judgement is secondary.
- Mandatory lenses: data integrity and state, failure modes and rollback (O-H), security at trust-boundary changes (O-H).
- IF there is an irreversible cutover step THEN the release-readiness review is O-H with human checkpoint. "Live gate
  pending" must never be reported as passed (arcwell, `review-process-amendment.md` L20–22).
- Consolidated adversarial review before cutover (arcwell M2–M7 pattern). Focused re-review of remediated surfaces,
  cap 2.

**Research + marketing website with blog/docs**
- IF public claims exist THEN every factual claim is fact-checked against a fetched source (S-M, O-M sampling). The
  verdict per claim is CONFIRMED / REFUTED / UNVERIFIED, and UNVERIFIED claims are removed or softened before publish
  (the /deep-research model, https://code.claude.com/docs/en/workflows).
- Design/taste review uses a calibrated rubric and a tournament (R05). No adversarial code panel beyond build, links
  and accessibility gates unless there is custom backend code.
- IF the site claims team, customer or market facts THEN a human checkpoint precedes publish.

**Other shapes that matter**
- *Security-sensitive change* (auth, crypto, permissions, secrets, CI): security lens O-H mandatory at every change,
  cap 3, refusal handling S2.
- *Data migration / schema change*: data-integrity lens with executed migration on a copy as evidence. Rollback
  rehearsed and verified.
- *Dependency / framework upgrade*: verifier relies on the full test suite plus changelog breaking-change checklist.
  Adversarial review only on code changed to adapt.
- *Research-only deliverable* (report, analysis): fact-check lens + "strongest counter-argument" persona. No code
  lenses.
- *Performance work*: verifier re-runs benchmarks with fixed seeds and hardware notes. Reviewer checks methodology
  (warm-up, variance, representative inputs).

## 7. Artifacts & templates

Directory convention (align with R01/R07's chosen root, written here as `mission/`):
`mission/reviews/<surface>-r<N>-findings.yaml`, `mission/reviews/<surface>-disposition.md`,
`mission/reviews/residuals.md`, `mission/loops/<id>.md` (contract + grader rubric), `mission/evidence/<task-id>/`
(command outputs, screenshots, fetched sources).

### 7.1 Gate verifier prompt (paste-ready)

```text
ROLE: Independent verifier. You did not build this and you have no access to how it was built.
Default stance: every criterion is FAIL until you have observed evidence that it passes.

ARTIFACT
- Repository/worktree: {path}  Commit: {sha}  (read-only: do not edit, create, or delete files in it)
- Changed files (git diff --stat): {stat}

CONTRACT (the only criteria you grade)
{numbered acceptance criteria from mission/loops/<id>.md, each with its declared check command if any}

EVIDENCE BUNDLE
- Gate outputs: {paths under mission/evidence/<task-id>/}
- Relevant tests: {paths}
- Spec excerpts cited by criteria: {paths#sections}

PROCEDURE
1. For each criterion, obtain evidence directly: re-run the declared command if it runs in under {N} minutes, else
   check that the saved output exists, was produced after commit {sha}, and was produced by the declared command.
2. Read the code or artifact at the cited locations. Do not accept summaries, commit messages, or comments as evidence.
3. If a check cannot run (tool missing, network, rate limit, permission), mark UNVERIFIED with the reason. Never guess.
4. Do not add criteria. If you notice a problem outside the contract, list it under OUTSIDE_CONTRACT with evidence.
5. Do not soften. The overall verdict is computed from the per-criterion results, not from your impression.

OUTPUT (YAML only)
verdict: PASS | FAIL | PENDING        # PASS only if every required criterion is PASS; any UNVERIFIED -> PENDING
criteria:
  - id: AC-1
    result: PASS | FAIL | UNVERIFIED
    evidence: "<command run> -> <exit code>; <quoted output line(s)>"   # or file:line quote
    note: "<one sentence; for FAIL: expected vs observed>"
outside_contract:
  - location: "<file:line>"
    observation: "<what>"
    evidence: "<command/output or quote>"
commands_run: ["<exact commands>"]
workspace_clean_after: true | false     # run `git status --porcelain` at the end
```

### 7.2 Refutation prompt (paste-ready)

```text
ROLE: Refuter. A reviewer claims the defect below. Your job is to try to DISPROVE it using the actual code, tests,
and executable checks. You succeed equally by confirming or by refuting. Being agreeable is failure.

CLAIMED FINDING
{finding YAML: id, severity, location, claim, evidence, construction}

ARTIFACT: {path}@{sha} (read-only; you may create scratch tests only under {scratch dir} and must delete them)

PROCEDURE
1. Restate the claim as a testable proposition: "If <precondition>, then <observable wrong outcome>."
2. Attempt to reproduce: write or run the smallest check that would show the outcome. Prefer executing over reading.
3. Look for guards the reviewer may have missed: validation upstream, schema constraints, triggers, types, config.
4. Decide:
   CONFIRMED  - you reproduced it, or the construction is airtight with cited file:line for every step
   REFUTED    - you found the guard or the reproduction shows correct behaviour (cite it)
   UNVERIFIED - you could neither reproduce nor refute within budget (say what would settle it)
5. If CONFIRMED, check severity against the taxonomy and state whether it should be raised or lowered, with reason.

OUTPUT (YAML only)
finding_id: F-...
verdict: CONFIRMED | REFUTED | UNVERIFIED
evidence: "<commands + output, or file:line quotes>"
severity_check: keep | raise:<level> | lower:<level>
reason: "<two sentences max>"
scratch_cleaned: true
```

### 7.3 Review types: triggers, lens blocks, personas

**Trigger table (R1).** Run a review type only when its trigger holds.

| Review type | Trigger | Unit | Default model | Mandatory evidence in bundle |
|---|---|---|---|---|
| Spec | Before build, for M+ or any spec with ≥1 MUST that has no test yet | spec doc + brief | O-H | brief, requirement list, acceptance criteria |
| Design / architecture | New component, cross-service boundary, persistence or concurrency model, migration plan | design doc + interfaces | O-H | spec excerpts, constraints, ADRs |
| Code correctness | Any non-trivial code change (≥~50 LOC or touches state/IO) | ≤400 changed LOC per reviewer | O-M | diff, tests, gate outputs |
| Test quality | New or changed tests guarding a MUST; mutation survivors; suspicious green | test files + code under test | S-H | mutation/coverage output, requirement ids |
| Security | Auth, permissions, secrets, input parsing from untrusted sources, crypto, payments, CI config, dependency adds | changed surface + trust boundary | O-H | SAST/audit output, threat notes |
| Performance | Stated perf requirement or hot path change | code + benchmark | S-H / O-M | benchmark outputs, methodology |
| UX / visual | UI change | screens/flows | per R05 | screenshots, geometry/a11y outputs |
| Research fact-check | Any deliverable with factual claims | claim list | S-M | fetched sources, URLs, access dates |
| Release readiness | Before deploy, publish, cutover, or merge to protected branch | gate register + residuals | O-M | all gate outputs, residual register, rollback plan |

**Reviewer prompt skeleton (paste-ready).** Insert exactly one LENS block.

```text
ROLE: Adversarial reviewer, lens = {LENS NAME}. You did not build this. Assume there are defects that would make this
artifact fail its purpose, and look for them. A clean report is a valid result. Invented or speculative findings
count against you; so does style commentary outside your lens.

UNIT UNDER REVIEW: {paths}@{sha} (read-only)   SIZE: {LOC changed}
PURPOSE OF THE ARTIFACT: {one paragraph from the brief}
CONTRACT / REQUIREMENTS: {criteria or spec excerpts}
EVIDENCE BUNDLE: {gate outputs, tests, tool outputs}
OUT OF SCOPE: pre-existing code not touched by this change (tag findings there as pre_existing: true, non-blocking)

{LENS BLOCK}

RULES
- Every finding needs location (file:line or doc#section) and evidence: a command with its observed output, or a
  step-by-step construction citing file:line for every step, precise enough to become a test.
- No evidence -> file it as type: question, not as a finding.
- Severity per taxonomy: blocker | major | minor | nit. Do not inflate. Report at most 5 nits in total.
- Stop after {max_findings, default 15} findings ranked by severity; state "truncated" if more exist.
OUTPUT: YAML list per mission/reviews schema (section 7.4), then `summary: {counts by severity}`.
```

**Lens blocks.**

- **SPEC.** Find: contradictions between sections; requirements with no observable acceptance test; ambiguous terms
  two engineers would build differently; missing failure and edge behaviour (empty, concurrent, offline, partial
  failure, retries); scope creep beyond the brief; unstated non-functional requirements (limits, latency, privacy).
  For each MUST, ask "how would a verifier prove this?"
- **DESIGN / ARCHITECTURE.** Find: invariants that are not enforced at a single authority; state that can diverge
  across stores; crash and retry points without idempotency; trust boundaries crossed without validation; coupling
  that blocks the stated evolution; irreversible decisions without rollback; designs whose correctness depends on
  callers behaving. Prefer constructions: "sequence A, then crash at B, then retry → outcome C violates D".
- **CODE CORRECTNESS.** Find: wrong results on supported inputs; unchecked zero-row or no-op writes treated as success;
  races and interleavings; error paths that swallow or mislabel failures; resource leaks; boundary and off-by-one
  errors; encoding and delimiter collisions; time and timezone handling; behaviour diverging from the spec's table of
  states. Run the tests that exist. Write a scratch test when a construction is cheap to execute.
- **TEST QUALITY.** Find: tests that would pass if the feature were deleted; asserts on mocks instead of outcomes;
  tests that can pass for a different reason than they name (two guards raising the same error type); missing negative
  cases for MUSTs; flaky time and ordering dependence; excess duplicate tests that add cost without a new failure mode.
  Evidence: a mutation (describe the one-line change) that survives.
- **SECURITY** (run on Opus 4.8). Find: authz checks missing or bypassable; injection (SQL, shell, template, prompt);
  secrets in code, logs or errors; SSRF and egress to private ranges; unsafe deserialization; weak crypto use; missing
  rate limits on expensive or auth endpoints; dependency advisories; CI workflows that expose secrets to untrusted PRs.
  Describe exploit preconditions and impact. Do not produce weaponized payloads beyond a minimal proof.
- **PERFORMANCE.** Find: N+1 queries, unbounded loops or allocations, missing pagination, sync IO on hot paths, cache
  invalidation errors. Check benchmark methodology (warm-up, variance, representative data). Claims need numbers from
  a run.
- **UX / VISUAL.** Use R05's verifier and rubric. Lens reviewer adds task-completion walkthrough findings only.
- **RESEARCH FACT-CHECK.** For each claim: fetch the cited source and quote the supporting sentence. Mark CONFIRMED,
  REFUTED (quote the contradiction) or UNVERIFIED (source unreachable or not supporting). Flag secondary sources used
  for primary claims, stale data (older than stated recheck date), and numbers with no source.
- **RELEASE READINESS.** For each gate in the register: is there a PASS verdict from a verifier with evidence newer
  than the release commit? Are live or environment gates honestly marked PENDING? Is every open blocker or major
  dispositioned? Is rollback documented *and rehearsed*? Are residuals accepted by an owner? Output a go/no-go table.

**Red-team personas** (optional add-on line in the LENS block, for L/XL panels):
- *Hostile input author*: "You control every external input and can call any public endpoint in any order."
- *Crash-at-the-worst-time operator*: "You can kill the process between any two statements and replay any request."
- *Skeptical auditor*: "You believe every 'implemented' claim is overstated until the test proves the exact clause."
- *First-time user in a hurry* (UX): "You skim, tap the most prominent thing, and abandon after one confusing step."
- *Maintainer in a year*: "You must change this safely without the author. What will you break?"

### 7.4 Finding schema (paste-ready YAML)

```yaml
# mission/reviews/<surface>-r<N>-findings.yaml
review:
  surface: payments-webhooks          # stable surface id
  round: 2                            # 1 = initial; >1 = scoped re-review
  scope: "remediation diff 3f2a..9c1d + callers of settle()"   # C3
  lens: code-correctness
  reviewer_model: opus-4.8/medium
  commit: 9c1d7e0
  evidence_bundle: [mission/evidence/T-041/test.txt, tests/webhooks/settle.test.ts]
findings:
  - id: F-PAY-R2-003                  # <surface>-R<round>-<seq>; never reused
    type: finding                     # finding | question
    severity: blocker                 # blocker | major | minor | nit
    pre_existing: false               # true -> never blocks this change (R6)
    lens: code-correctness
    class: zero-row-write-as-success  # short defect-class tag, used by C4 recurrence check
    location: "src/webhooks/settle.ts:88"
    claim: "settle() reports success when the conditional UPDATE matched zero rows"
    construction:                     # steps precise enough to become a test; each step cites file:line
      - "Reservation already settled (src/cost/reservations.ts:41 sets state=settled)"
      - "Replay webhook -> settle() runs UPDATE ... WHERE state='held' (settle.ts:80), changes=0"
      - "settle.ts:88 returns {ok:true} without reading changes"
    evidence: "npx vitest run tests/scratch/replay.test.ts -> 1 failed: expected ok:false, got ok:true"
    expected: "replay returns ok:false or idempotent-success with audit row unchanged"
    observed: "ok:true and a second audit row"
    impact: "double audit record; downstream reconciler counts settlement twice"
    fix_class: "check affected-row count; add replay test"
    refutation:                       # filled by the refuter (7.2)
      verdict: CONFIRMED              # CONFIRMED | REFUTED | UNVERIFIED | NOT_RUN
      by: sonnet-4.6/high
      evidence: "reproduced with the scratch test above"
    related: [F-PAY-R1-007]           # parent/sibling ids; recurrence of same class -> C4
summary: {blocker: 1, major: 0, minor: 2, nit: 1, questions: 1, truncated: false}
```

Severity taxonomy (F2), one line each for the skill:
- **blocker**: violates a MUST, loses or corrupts data, exposes security, makes the primary purpose fail, or the
  gate evidence is false.
- **major**: wrong behaviour in a supported path, a missing required negative case, or an overstated completion claim.
- **minor**: low-impact edge case, maintainability risk, or a weak but not wrong test.
- **nit**: naming, style, comments. Capped at 5 per review. Never triggers a round.

### 7.5 Disposition log template (paste-ready)

```markdown
# <surface> — review disposition (round <N>)

Source findings: `mission/reviews/<surface>-r<N>-findings.yaml` · Reviewer: <model/effort> · Commit reviewed: <sha>
Verdict as written by reviewer: <PASS | NOT CLOSED — k blockers, m majors>

Dispositions: **FIXED** (commit + test that fails without the fix, verified against the original construction) ·
**REFUTED** (evidence that the construction does not hold) · **RESIDUAL** (accepted limitation; rationale; owner;
recorded in residuals.md) · **DEFERRED** (target milestone + owner + why this is not goalpost-moving) · **CONTESTED**
(premise disputed; evidence; escalated to <adjudicator>).

| ID | Sev | Class | Finding (one line) | Disposition | Evidence / pointer |
|---|---|---|---|---|---|
| F-PAY-R2-003 | blocker | zero-row-write-as-success | settle() treats zero-row UPDATE as success | FIXED | commit a1b2c3; `tests/webhooks/settle.test.ts::replay_is_idempotent` fails on parent commit (output: mission/evidence/T-041/fix-proof.txt) |
| F-PAY-R2-004 | major | missing-idempotency-key | refund() can double-refund on client retry | REFUTED | unique index `refund_request(idempotency_key)` at `migrations/0007.sql:14`; refuter run: second insert raises constraint error (mission/evidence/T-041/refute-004.txt) |
| F-PAY-R2-005 | minor | unbounded-retry | webhook retry has no max attempts | DEFERRED | M3, owner: orchestrator; the queue adapter that enforces attempt budgets is delivered in M3 and the deferral names the test that will prove it (`queue_budget_exhausts`) |

## Sub-findings
A parent is FIXED only when every sub-finding row below has its own disposition (F4).

## Outside-contract observations (triaged)
| Observation | Triage decision (new task / backlog / dropped with reason) |

## Residuals added
- R-<n>: <limitation, stated plainly — what is NOT claimed> · owner · review-by date

## Verification after remediation
- `<gate command>` → <result line>   (one line per gate, fresh run after the last fix)

## Convergence check (C1–C5)
- CONFIRMED blockers/majors this round: <n>  → close | re-review scoped to <diff + callers>
- Round <N> of cap <cap> (scope <S|M|L|XL>)
- Recurring class from previous round? <class or none>  → design review opened: <yes/no + task id>
- Instrument-finding share: <x%>  → instrument audit: <yes/no>
- Decision: CLOSED | SCOPED RE-REVIEW | ESCALATED (<to whom>) | RESIDUALS ACCEPTED
```

### 7.6 Convergence and stop rules (paste-ready block for SKILL.md / references)

```text
REVIEW LOOP — per surface
0. Deterministic gates first (tests, typecheck, lint, build, link/schema checks). Red -> fix before any model review.
1. Round 1: run the lenses selected by the trigger table on units of <=400 changed LOC (or one coherent surface).
2. Refute every candidate blocker/major (refuter prompt). Only CONFIRMED findings count.
3. Maker fixes CONFIRMED blockers/majors in small commits; each fix adds a test that fails on the parent commit.
4. Write the disposition log. Every finding gets FIXED | REFUTED | RESIDUAL | DEFERRED | CONTESTED.
5. Decide:
   a. CONFIRMED blockers+majors this round == 0                    -> CLOSE surface.
   b. round == cap (S1 / M2 / L3 / XL4)                            -> no more rounds:
        open CONFIRMED blocker  -> ESCALATE: adjudicator one tier up; still open -> human queue (BLOCKED-HUMAN);
        only majors/minors open -> record RESIDUALS with owner, CLOSE with waiver noted in STATUS.
   c. same defect class CONFIRMED in this round and the previous  -> STOP patching; open design-review task for that
                                                                     mechanism; surface stays open until it lands.
   d. round >= 3 and >50% of CONFIRMED findings are about instruments (tests/mutations/registry claims)
                                                                   -> bounded instrument-audit task; then re-review once.
   e. otherwise                                                    -> SCOPED RE-REVIEW (round+1): remediation diff +
                                                                     direct callers + original constructions only.
6. Minors and nits never cause a round. Pre-existing findings never block.
7. CONTESTED findings go to the adjudicator (tier-up) with both sides' evidence; its verdict is final for this round.
8. A verifier/refuter refusal (stop_reason "refusal") -> discard partial output, log fallback, re-run on Opus 4.8;
   until then the criterion is UNVERIFIED (never PASS, never FAIL).

MISSION LEVEL
- Adversarial panels run at integration points (walking skeleton, pre-release, pre-cutover, milestone ends for L/XL);
  deterministic gates run at every task.
- One consolidated cross-surface review before release/cutover for L/XL, then one focused re-review of remediated
  surfaces (cap 2 for that pair).
- Missed-defect escape (defect later found in reviewed code) -> raise that lens one tier for the rest of the mission and
  add the class to the lens checklist at retro.
- Review spend guard: if review tokens for a surface exceed 2x the build tokens of that surface, pause and ask the
  orchestrator to justify another round in DECISIONS.md.
```

### 7.7 Grader rubric template (loop graders, paste-ready)

```markdown
# mission/loops/<loop-id>.md — contract and grader rubric

## Goal (one sentence, from brief)
<goal>

## Criteria (binary; each must name its evidence)
| ID | Criterion (observable) | Evidence required | Required? |
|---|---|---|---|
| AC-1 | `pnpm test tests/checkout` exits 0 | command output saved to mission/evidence/<task>/ac1.txt, newer than HEAD | yes |
| AC-2 | Replaying the same webhook twice produces exactly one settlement row | test name + assertion line; test fails on parent commit | yes |
| AC-3 | API returns 409 on idempotency-key conflict | curl transcript against local server with status line | yes |
| AC-4 | No new lint warnings | lint output diff vs base | no |

## Process criteria (prevent early exit; from the Outcomes-style rubric)
| ID | Criterion | Evidence |
|---|---|---|
| PC-1 | All required criteria were attempted in this iteration | per-criterion log lines |
| PC-2 | Previous iteration's FAIL items addressed or explicitly carried with reason | diff of verdict files |

## Taste dimensions (only if the artifact is taste-bearing; else delete this section)
Scale 0–4 with anchors; threshold per R05.
| Dimension | 0 | 2 | 4 | Anchor examples |
|---|---|---|---|---|
| hierarchy | no clear primary action | primary action findable after scanning | primary action obvious at first glance | mission/design/references/anchor-hierarchy-{0,2,4}.png |

## Grader rules
- Start every criterion at FAIL; PASS requires the named evidence, quoted or linked.
- UNVERIFIED if the evidence cannot be produced; loop verdict is then NOT_MET.
- Loop verdict = MET only if every required criterion PASS and every process criterion PASS.
- The grader lists at most 3 highest-leverage fixes for the maker; no style commentary outside criteria.
- Keep-best: record per-iteration pass counts; if the loop stops at cap, the orchestrator keeps the best iteration,
  not the latest.

## Calibration (run once before the loop, record results here)
- 3 known-good and 3 known-bad samples (or seeded defects: delete a guard, stale log, doctored exit code).
- Grader must classify 6/6. Otherwise tighten criterion wording/anchors and re-run. Record: date, model/effort, result.

## Loop bounds
- Max iterations: S3 / M5 / L8 (R01 S3); futility: same failing criterion set twice in a row -> escalate approach.
```

### 7.8 Custom agent files (Claude Code; degrade to Agent-tool briefs elsewhere)

The sub-agents doc verifies that per-agent tool restriction and model selection exist
(https://code.claude.com/docs/en/sub-agents). The exact frontmatter keys below (`tools`, `model`) follow that doc's
subagent format but were not re-read in full in this lane (fetch truncated). Pin full model IDs per R01. Effort
selection per agent is unverified here, so put the effort level into the brief and let R01 own the mechanism.

```markdown
---
name: mission-verifier
description: Independent read-only verifier. Use to grade a task or gate against its contract with cited evidence.
tools: Read, Grep, Glob, Bash
model: sonnet
---
You are the mission verifier. Follow mission/references/verification.md §7.1 exactly.
Never edit files. Bash is for running declared check commands and `git status --porcelain` only.
Output YAML only.
```

```markdown
---
name: mission-reviewer-security
description: Adversarial security reviewer for auth, secrets, input parsing, CI and dependency changes.
tools: Read, Grep, Glob, Bash
model: opus
---
Lens = SECURITY (mission/references/review-lenses.md). Minimal proofs only. Output findings YAML.
```

```markdown
---
name: mission-refuter
description: Tries to disprove a claimed defect by reproduction; returns CONFIRMED, REFUTED or UNVERIFIED.
tools: Read, Grep, Glob, Bash, Write
model: sonnet
---
Follow the refuter protocol. Write only under mission/tmp/refute/ and delete what you create before returning.
```

Caveat for the synthesizer: R01 reports that the `opus`/`sonnet` aliases may resolve to newer models than Opus 4.8 /
Sonnet 4.6 (`99-synthesis-notes.md` line 12). Use pinned IDs once confirmed.

## 8. Anti-patterns & failure modes

**Verification anti-patterns**
- *The maker's summary as evidence.* A verifier reading "all tests pass" in a handoff note and agreeing. Fix: V4,
  re-run or timestamp-check.
- *Transcript leakage.* Passing the maker's conversation or "reasoning" to the verifier "for context". It re-imports
  the anchoring the separation exists to remove. Fix: V2 brief whitelist.
- *Lenient grader drift.* The grader finds a real problem and then "talks itself into" passing it (secondary source,
  §3.1). Fix: verdict computed mechanically from per-criterion results (G4), plus calibration (G3).
- *UNVERIFIED read as PASS.* Rate limits, tool errors or refusals silently become green. Fix: V5/S3 three-valued
  verdicts.
- *Instruments that cannot fail.* Tests or mutation targets that pass for the wrong reason. Arcwell found stale
  targets whose search string "occurs zero times" (`m1-fifth-review-disposition.md` L8–14) and repeated "non-causal"
  kills. Fix: seeded-defect canaries and instrument audit (C5).
- *Evidence bundle omissions.* The reviewer lacks the tests and files false findings (`m2-m7-review-disposition.md`
  L55–58). Fix: mandatory evidence column in the trigger table.
- */goal as the gate.* R01 found the /goal evaluator reads the transcript and defaults to a small model. Fix: gates
  run through the skill's verifier or a Stop-hook check script.

**Review anti-patterns**
- *Unbounded rounds.* Arcwell M1: eighteen rounds, closure by owner direction, not by convergence (§3.4). Fix: caps
  (C2), severity stop (C1), escalation.
- *Whole-surface re-review after every fix.* It multiplies cost and finds new narrow constructions each time. Fix: C3
  scoped re-review.
- *Big-batch remediation.* Large fixes introduce new defects (14 in R2; 5 of 19 in R16). Fix: small commits, one test
  per fix, re-review scoped to the diff.
- *Patching a broken mechanism repeatedly.* Delimiter identity recurring from R2 to R17. Fix: C4 design review.
- *Nitpick spiral.* Reviewers pad reports with style issues. Makers "fix" them and another round runs. Fix: nit cap 5,
  nits never trigger rounds, lens scope limits.
- *Invented findings to look useful.* Fix: R3 ("a clean report is a valid result"), refutation pass (R4), evidence
  requirement.
- *Every lens on every change.* Security, performance and UX panels on a doc typo. Fix: trigger table (R1).
- *Goalpost-moving deferrals.* Deferring a finding "to a later milestone" when the surface already exists. Arcwell's
  reviewers called this out (`m1-sixth-review-disposition.md` L9–11). Fix: DEFERRED requires naming why the proof
  cannot exist now.
- *Quiet narrowing.* Marking a parent FIXED while sub-findings remain. Fix: F4.
- *Blocking on inherited debt.* Pre-existing bugs holding a small change hostage. Fix: R6 `pre_existing` flag.
- *Rephrasing around a classifier.* Rewording a security review to get past a Fable refusal. Fix: S2 route to Opus
  4.8, log the event.

**Cost and token traps**
- Opus-high or Fable on log-reading verification. Use S-L/S-M with canaries (§5).
- Reviewing 2,000-line diffs in one context. Chunk to ≈400 LOC (R2; SmartBear/Cisco detection drop).
- Model review before deterministic gates. Gates first; skip the model call on red.
- Panels at every task instead of integration points (C6).
- Re-running expensive suites inside every grader iteration when saved output with a valid timestamp suffices (V4).
- Taste loops without keep-best. Rajasekaran sometimes preferred a middle iteration. Without keep-best the loop pays
  for regressions.

**Process bloat**
- Disposition docs that grow to hundreds of lines per round (arcwell R14 disposition is 264 lines, per the file
  length in `m1-fourteenth-review-disposition.md`). Fix: the table format in §7.5, with detail only for CONTESTED
  and RESIDUAL items.
- Separate review documents for S tasks. For S scope, findings and dispositions live in the PR description or STATUS
  entry.

## 9. Open questions / risks for the synthesizer

1. **Round caps are judgment, not measured.** S1/M2/L3/XL4 and the "2× build tokens" spend guard come from the arcwell
   pattern and cost intuition. Arcwell records no token or hour costs, so the caps cannot be calibrated from its data.
   Recommend logging review tokens per surface in STATUS so retros can tune them.
2. **Same-family diversity.** Every verifier is Claude. PoLL's bias reduction depended on disjoint model families
   (https://arxiv.org/abs/2404.18796). Lens and effort diversity is a weaker substitute. If the harness can call a
   non-Claude model the user trusts, it could serve as an optional cross-family refuter. The user constraint currently
   rules this out, so I did not propose it as default.
3. **Read-only enforcement.** Giving verifiers `Bash` for running checks also lets them write. Real read-only needs a
   separate worktree, a permission deny-list, or a hook that rejects writes outside `mission/tmp/`. R01 owns guardrail
   settings. The post-hoc `git status --porcelain` check is a detector, not a preventer.
4. **Per-agent effort mechanism unverified.** I could not confirm whether sub-agent frontmatter accepts an effort key.
   If it doesn't, "S-L vs S-H" must be expressed through the session or brief, which may not control reasoning budget.
   R01 should settle this.
5. **Rajasekaran details from a secondary source.** The evaluator-leniency quote ("talk itself into…"), sprint
   contracts, `file:line` evidence in QA verdicts and the cost tables came from https://understandingdata.com/posts/generator-evaluator-harness-design/.
   The primary page fetch truncated at 10 KB before those sections. They are consistent with the primary's opening
   sections but unverified against the primary text.
6. **Attribution in the post.** The verifier quote is from Lance Martin's X article, not an official Claude Code team
   statement. Martin describes the experiments as "a few small scale experiments". The skill should not overclaim.
7. **Seeded-defect canaries can leak.** If makers see canary criteria, they may learn to satisfy canaries. Canaries
   must be injected into verifier evidence bundles only, never into maker briefs. Their design needs care so they are
   not trivially detectable (e.g., always a stale timestamp).
8. **Consolidated review timing risk.** Arcwell's consolidated M2–M7 review worked, but it came *after* all
   implementation. A defect in a foundational surface found that late costs more. My compromise: a contract review
   before build, per-milestone automated gates, and panels at integration points. The right balance for XL greenfield
   is unvalidated.
9. **Instrument-audit trigger (>50% at round ≥3)** is derived from arcwell rounds 10–17 qualitatively. Arcwell did not
   report per-round proportions, so the threshold is a guess.
10. **Classifier behaviour inside Claude Code** (sticky, silent fallback per R01) vs. API `stop_reason: "refusal"`.
    Refusal handling in sub-agents may surface differently from the API docs. The skill should detect "Opus 4.8
    answered where Fable was requested" from session metadata when possible.
11. **Human review economics transfer.** The SmartBear ≈400 LOC figure is for humans. The LLM equivalent chunk size is
    unmeasured. Treat 400 LOC as a starting default and tune it from missed-defect escapes.

## Sources

**Primary and secondary web sources (fetched in this lane)**
1. Prithvi Rajasekaran, "Harness design for long-running application development", Anthropic Engineering, Mar 24 2026 —
   https://www.anthropic.com/engineering/harness-design-long-running-apps (fetched; truncated at 10 KB).
2. James Phoenix, "Generator-Evaluator Harness Design" (secondary summary of 1) —
   https://understandingdata.com/posts/generator-evaluator-harness-design/
3. Lance Martin, "Designing loops with Fable 5", X article, Jun 9 2026 — https://x.com/RLanceMartin/status/2064397389189071163
4. Huang et al., "Large Language Models Cannot Self-Correct Reasoning Yet", ICLR 2024 — https://arxiv.org/abs/2310.01798
5. Kamoi et al., "When Can LLMs Actually Correct Their Own Mistakes?", TACL 2024 — https://arxiv.org/abs/2406.01297
6. Panickssery, Bowman, Feng, "LLM Evaluators Recognize and Favor Their Own Generations", 2024 —
   https://arxiv.org/abs/2404.13076
7. Zheng et al., "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena", NeurIPS 2023 — https://arxiv.org/abs/2306.05685
8. Verga et al., "Replacing Judges with Juries (PoLL)", 2024 — https://arxiv.org/abs/2404.18796
9. Anthropic, "Demystifying evals for AI agents", Jan 9 2026 — https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
10. Anthropic, "Building effective agents", Dec 19 2024 — https://www.anthropic.com/engineering/building-effective-agents
11. Claude Code docs, "Orchestrate subagents at scale with dynamic workflows" — https://code.claude.com/docs/en/workflows
12. Claude Code docs, "Code Review" — https://code.claude.com/docs/en/code-review
13. Claude Code docs, "Create custom subagents" — https://code.claude.com/docs/en/sub-agents (truncated at 10 KB)
14. Claude Platform docs, "Refusals and fallback" — https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback
15. SmartBear, "Best Practices for Code Review" (Cisco study) —
    https://smartbear.com/learn/code-review/best-practices-for-peer-code-review/
16. Search result only (not fetched): "Classifier fallback and billing for Claude Fable 5" cookbook —
    https://platform.claude.com/cookbook/fable-5-fallback-billing-guide

**Workspace evidence (read-only)**
- `arcwell/docs/operations/review-process-amendment.md` (L3–31)
- `arcwell/docs/operations/m1-adversarial-disposition.md` (L3–15, L22, L68–75)
- `arcwell/docs/operations/m1-rereview-disposition.md` (L3–7, L36–38, L50, L87–97, L101–103)
- `arcwell/docs/operations/m1-third-review-disposition.md` (L3–10, L47–50, L68–70, L84–89)
- `arcwell/docs/operations/m1-fourth…seventeenth-review-disposition.md` (verdict headers, L1–30 of each)
- `arcwell/docs/operations/m1-eighteenth-review-disposition.md` (L3–6, L45–57)
- `arcwell/docs/operations/m2-m7-review-disposition.md` (L5–7, L39, L55–58, L93–118)
- `research/mission-skill/99-synthesis-notes.md` (R01/R05/R07 decisions referenced: lines 6, 10, 12, 27)
