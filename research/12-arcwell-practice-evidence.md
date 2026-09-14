# R12 — Practice evidence from `arcwell/` (the user's own XL project)

Lane: practice evidence. Read-only study of `arcwell/`. Citations are `path:line` inside the workspace instead of URLs.
Where a statement is my interpretation rather than a file fact, it is labelled **(inference)**.

---

## 1. Executive summary & strong opinions

The arcwell record covers a normative spec dated 2026-08-14 (`arcwell/docs/product/arcwell-spec.md:7`), eight milestones, about 20 adversarial review rounds, a simplification audit, a gap-closure plan, a cutover, the first autonomous production morning (2026-08-21) and a post-deploy verification (2026-08-22). The mission engine should reproduce the process's evidence habits. It should also fix its one structural failure: gates and reviews were aimed at a kernel that was proven only against fakes. What reached production was not the thing those reviews tested.

1. **Encode the evidence ledger, not just a checkbox list.** The user's best artifact is the milestone ledger: "An item is checked only after the gate command has been run green on a clean workspace" (`arcwell/docs/operations/milestone-ledger.md:4`). Each closure records the date, the commands, the counts and the review disposition (`milestone-ledger.md:21-28`). The skill's STATUS.md should demand this proof identity for every checked item.
2. **A requirement registry with test citations is worth its cost at L/XL scope.** It caught real lies. A citation-correspondence check "immediately exposed 29 mis-registrations" (`arcwell/docs/operations/m1-adversarial-disposition.md:21`). At S/M scope a lighter table is enough (see §6).
3. **Honest demotion is the registry's killer feature.** About 40 requirements were moved back to `planned` and "the milestone gate [went] red. That is the gate working" (`m1-adversarial-disposition.md:12-15`). "That number went DOWN because the registrations went honest" (`milestone-ledger.md:138-139`). The skill must make demotion cheap and normal, never a failure to hide.
4. **Every build needs a walking-skeleton gate before any "milestone closed".** After M7, 821 tests, 544/544 requirements and 218/218 mutants, the hub still "serves only `/health`", with "zero real provider adapters" (`arcwell/docs/operations/gap-closure-plan.md:3-18`). This contradicts the spec's own "Build vertical slices, not a broad mock surface" (`arcwell-spec.md:34`). This is the single most important lesson.
5. **Cap review→remediate loops and track convergence.** M1 ran 18 rounds. Every round found defects, and the later rounds increasingly found defects created by the previous round's fixes (`milestone-ledger.md:65-67`). The loop never converged. The owner ended it by decree (`arcwell/docs/operations/review-process-amendment.md:3-5,23-31`). The skill needs a stop rule based on novelty and severity, plus escalation, instead of "until the reviewer says close".
6. **Reviews must include the production path and the reviewer's full reference set.** A context-starved reviewer produced false findings because it "lacked the test files (not in its reference set)" (`arcwell/docs/operations/m2-m7-review-disposition.md:55-58`). Reviews of a test-only kernel never saw the production no-ops that silenced 30 sources for days (`arcwell/docs/handoff/2026-08-21-morning-remediation-handoff.md:72-91`).
7. **Keep a three-state verification vocabulary: Observed / Inferred / Unverified.** Each Unverified item carries the exact command that closes it (`arcwell/docs/handoff/2026-08-22-post-deploy-verification.md:5-13`). This is the user's own best verification-honesty format. Reuse it verbatim.
8. **Agents must never mark human or live gates PASSED.** The rule appears in three places: "No automated agent may mark a check passed" (`arcwell/tests/deployed-canary/live-acceptance.md:12`), the M3 human gate (`arcwell/docs/operations/m3-human-evaluation.md:51-52`) and the gap plan (`gap-closure-plan.md:154-155`). Encode it as a hard rule.
9. **Separate "mechanism delivered" from "outcome accepted".** The registry marks a requirement `implemented` for the mechanism and keeps the `live:` reference PENDING (`arcwell/requirements-curation.yaml:309-319`). The skill should carry both columns.
10. **Disposition every finding in a fixed vocabulary.** The vocabulary is FIXED / RESIDUAL / CONTESTED (`m2-m7-review-disposition.md:11-15`), or "ACCEPTED, NOT FIXED" with a demotion (`arcwell/docs/operations/m1-fifth-review-disposition.md:27`). Each FIXED row names the mechanism, the test and the mutation target. Keep a residual register "recorded rather than hidden" (`milestone-ledger.md:130`).
11. **Treat mutation scores as claims that can go stale.** A refactor left a mutation target matching zero sites, so "the recorded 50/50 score was not reproducible" (`m1-fifth-review-disposition.md:8-17`). The skill should require a registry `--validate` step, and should treat a survivor as an oracle weakness, "not a target to adjust" (`milestone-ledger.md:126-127`).
12. **Handoffs should be self-contained and root-caused to file:line, with a verification bar.** The 2026-08-21 handoff is a strong template: Orientation / State / prioritized Remediation plan / Recovery procedures / Note for remote agent (`morning-remediation-handoff.md:9-208`).
13. **Change the contract where it lives.** Milestone moves go through version-controlled errata and never silent edits. The spec is SHA-pinned (`arcwell/docs/product/spec.sha256:1`; `arcwell/docs/product/supplementary-requirements.md:17-21`). The skill's spec should be hash-pinned and amended through an ERRATA section.
14. **Skill-writing style to mirror:** short frontmatter with a trigger-list description, a flat rules list, explicit fallbacks, and a "Completion contract" that separates levels of completion (`arcwell/plugins/arcwell/skills/deep-research/SKILL.md:1-4,70-77`).

## 2. Claim check (practice vs post)

This lane checks the post's claims against the user's own practice, not against the web. The verdicts are about arcwell only.

| Post claim | What arcwell shows | Verdict for the skill |
|---|---|---|
| "Verifier sub-agent beats self-critique" (post §06) | Supported. Independent reviews, written to `.maestro/complex_reasoning/*.md` outside the tree, found constructible defects that the builder's own "all twelve FIXED" claim missed (`m1-fifth-review-disposition.md:3-6`). The M0 review found the ledger claiming closure early and "verification passed planned requirements" (`arcwell/docs/operations/m0-adversarial-disposition.md:10-11`). | Keep. Make it structural. |
| "Loop until done — no new findings" (post §07) | Contradicted as a stop rule. 18 M1 rounds never produced "no new findings", and fixes kept creating new findings (`milestone-ledger.md:62-67`). The owner stopped the loop (`review-process-amendment.md:3-5`). | Replace with a bounded loop plus a convergence metric plus human escalation. |
| "STATE.md: write before walking away" (post §11) | Supported in spirit. The ledger, dispositions and handoffs record state after every round (`m1-eleventh-review-disposition.md:139-154`; `morning-remediation-handoff.md:1-7`). No single STATE.md existed. State was spread across 37 files under `docs/operations/`. | Keep. Consolidate into one state file that points at detailed docs. |
| "Distill failures into general rules" (post §10/§12) | Partly supported. Dispositions often generalise ("moving code without re-checking the mutation registry silently invalidates the score", `m1-fifth-review-disposition.md:15-17`). Spec TEST-004 requires a recurrence fixture per production incident (`arcwell-spec.md:1279`). But the lessons stayed buried inside long prose docs rather than in a consultable rules file **(inference)**. | Keep. Add a dedicated LESSONS.md with short rules and backlinks. |
| "Fan-out and synthesize" (post §07) | Supported. The post-M7 audit used "31-row coverage contract, 25 bounded worker reviews, independent meta-audit" (`milestone-ledger.md:285-288`). The production audit used "an 8-agent deep audit", with each item "root-caused by a dedicated agent" (`morning-remediation-handoff.md:4-5,37-38`). | Keep. Reuse the coverage-contract idea. |
| "Vision self-check for visual work" (post §13) | Not exercised. Arcwell's quality gate for editorial output was a blinded *human* rubric, still PENDING (`m3-human-evaluation.md:3-6`). | Pair automated vision/rubric grading with a pinned human gate for taste. |

## 3. Deep findings (practice evidence)

### 3.1 Timeline and review-round finding counts

Dates come from the ledger and the handoffs. Counts are as recorded in each round's summary. Where the ledger and the disposition docs disagree, both numbers are shown.

| When | Stage / round | Recorded verdict and counts | Source |
|---|---|---|---|
| 2026-08-14 | Spec issued ("normative rebuild brief") | — | `arcwell-spec.md:3-7` |
| 08-14 | M0 adversarial review | 31 findings, plus 12 Overseer-cycle defects per the ledger (the disposition lists 9 further defects); M0 closed | `milestone-ledger.md:10,28`; `m0-adversarial-disposition.md:3,42` |
| 08-14/15 | M1 R1 | 17 findings, 22 expected-surviving mutation classes, ~40 demotions, 29 mis-registrations exposed; stays open | `m1-adversarial-disposition.md:3-15,21` |
| | R2 re-review | 2/17 fully closed, 12 partial, 2 not closed; **14 new defects introduced by the rework**; ~24 overstated registrations | `arcwell/docs/operations/m1-rereview-disposition.md:3-7` |
| | R3 | 11 constructible defects (the disposition lists 12 blocking fixes) | `milestone-ledger.md:53`; `arcwell/docs/operations/m1-third-review-disposition.md:3-5,14` |
| | R4 | 12 closure requirements + 7 new defects | `milestone-ledger.md:54` |
| | R5 | "all twelve FIXED" claim false; 12 constructions, 13 defects; stale mutation registry | `milestone-ledger.md:55`; `m1-fifth-review-disposition.md:3-17` |
| | R6 | 8 constructible, 15 named | `milestone-ledger.md:56` |
| | R7 | 15 defects + 3 outside blockers | `milestone-ledger.md:57` |
| | R8 | 13 new defects | `milestone-ledger.md:58` |
| | R9 | 13 new; 2 syntactically invalid mutants; forced demotions accepted | `milestone-ledger.md:59` |
| | R10 | 7 new + 7 unclosed; 11 live defects with no mutation target | `milestone-ledger.md:60` |
| | R11 | 8 new; 11 non-failing targets; 18 untargeted live defects; 14 overstated registrations | `m1-eleventh-review-disposition.md:3-7` |
| | R12 | 15 new; all 8 claim groups not closed; 5 non-causal targets | `milestone-ledger.md:62` |
| | R13 | 15 new; deepest was in R12's headline fix | `milestone-ledger.md:63` |
| | R14 | 10 constructions / 18 defects, "several of them created by the thirteenth round's own fixes" | `milestone-ledger.md:64` |
| | R15 | 13 constructions, 3 created by R14's fixes | `milestone-ledger.md:65` |
| | R16 | 19 constructions, 5 created by R15's fixes | `milestone-ledger.md:66` |
| | R17 | 17 constructions, "several created by the sixteenth round's own fixes" | `milestone-ledger.md:67` |
| 08-15 | R18 | still "reject closure"; accepted by owner direction; M1 CLOSED | `arcwell/docs/operations/m1-eighteenth-review-disposition.md:3-6,53-57` |
| 08-15 | Review-process amendment | M2–M7 close on automated gates; one cross-milestone review at the end | `review-process-amendment.md:3-21` |
| 08-15→16 | M2–M7 implemented | M2 CLOSED; M3 human gate pending; M4–M6 provisionally closed; M7 live gates pending | `milestone-ledger.md:218-279` |
| 08-16 | M2–M7 cross-milestone review | 23 findings → 15 fixed in code, 2 in docs, 5 residual, 1 contested | `m2-m7-review-disposition.md:3-9,95-96` |
| 08-16 | Focused re-review | 7 blockers, "several introduced by round one itself" | `m2-m7-review-disposition.md:108-111` |
| 08-16 | Simplification audit | 53 findings in 4 tiers, all implemented | `milestone-ledger.md:283-293` |
| 08-17 | Gap-closure plan | hub has no bindings, no adapters, no MCP; plugin README overclaimed | `gap-closure-plan.md:3-37` |
| 08-21 | First autonomous morning → 8-agent audit | 7 prioritized items (P0 ×2, P1a, P1b, P1, P2 ×2, P3) | `morning-remediation-handoff.md:3-5,43-182` |
| 08-22 | Post-deploy verification | 103 doctor findings; new latent defect found (no resolver path) | `post-deploy-verification.md:32-101` |

Mutation scores grew with scope: 18/18 at R1 (`m1-adversarial-disposition.md:64`), 111/111 at R11 (`m1-eleventh-review-disposition.md:148`), 148/148 at M1 acceptance (`m1-eighteenth-review-disposition.md:49`), then 159, 175, 187, 198 and 218 across M2–M7 (`milestone-ledger.md:226-277`). Test counts grew from 125 unit tests at M0 (`milestone-ledger.md:24`) to 821 tests in 79 files after the audit (`milestone-ledger.md:311-313`).

**(Inference.)** The whole of M1, 18 rounds, fits between the M1 gate run on 08-14 16:55 UTC and a 08-15 closure. So each round was an agent-driven remediate→review cycle of an hour or two, not days. The per-round cost was mostly model tokens plus disposition writing, and the returns kept diminishing: defects moved from core authorisation gaps (R1) to delimiter injectivity and expanded-year timestamps (R14–R16).

### 3.2 The requirement registry as actually used

**Three-file pipeline.** Requirement text and IDs live in the spec plus `supplementary-requirements.md`. Status and test references live in `requirements-curation.yaml`. `pnpm requirements:generate` merges them into `REQUIREMENTS.yaml`, which is marked "GENERATED FILE … Edit the sources, not this file — `pnpm verify:requirements` rejects a stale registry" (`arcwell/REQUIREMENTS.yaml:1-5`). The spec is pinned by hash (`spec.sha256:1`), so "an unreviewed spec edit fails the gate" (`m1-adversarial-disposition.md:21`).

**Entry schema as generated** (`REQUIREMENTS.yaml:6-20`):

```yaml
- id: OUT-001
  text: <verbatim normative sentence from spec>
  kind: requirement            # or `test` for named spec scenarios (e.g. REQUIREMENTS.yaml:3590)
  owner: product               # component/domain owner
  severity: high               # critical | high | ...  (derived, NOT curatable)
  milestone: 7                 # derived from reviewed mapping, NOT curatable
  status: implemented          # planned | implemented | live-only
  automated:
    - tests/scenario/m7-outcomes.test.ts::out_001_morning_brief_and_walk_audio_are_ready_before_the_deadline
  live:
    - tests/deployed-canary/live-acceptance.md::OUT-LIVE-01
  notes: <why this proof is sufficient / what is PENDING / demotion history>
```

The spec's own template also has `failure_fixtures:` (`arcwell-spec.md:1260-1274`). The generated entries sampled here do not use it. Failure fixtures ended up as test names instead **(inference from the sample)**. The registry holds 544 entries (`milestone-ledger.md:277`), and grep counts 172 `severity: critical` lines in the file.

**Rules enforced by the linter.** Every `automated` reference must resolve to an exact enabled test, *and that test must cite the requirement* it is registered to prove. Severity and milestone "are NOT curatable" (`requirements-curation.yaml:1-8`). CITE-001 says every test case must cite `@req:ID`, and `.only`/skip/todo references are rejected (`m0-adversarial-disposition.md:15-17`). `checkOracleStrength` rejects any single test serving as sole oracle for more than 5 critical requirements. `checkCitationCorrespondence` enforces reverse citation (`arcwell/packages/devtools/src/verify-requirements.ts:243,277`). The gate knows the current milestone from a one-line `MILESTONE` file (`arcwell/MILESTONE:1`; `m0-adversarial-disposition.md:11`). Strict mode rejects anything still `planned` and serves as the final gate (`arcwell/README.md:21`). CI runs both modes (`arcwell/.github/workflows/ci.yml:25-26`). "Deliberately orphaned requirement and deliberately forbidden import both fail the PRODUCTION CLIs (subprocess proofs)" (`milestone-ledger.md:27`). In other words, the gates are themselves tested.

**The `notes` field is where the honesty lives.** Demotion notes name the gap and the bar for re-registration (`requirements-curation.yaml:10-15`). They also accumulate history, for example "DEMOTED by the eleventh M1 review … Milestone 7 delivered that control plane … The enumeration is now satisfied rather than sampled" (`requirements-curation.yaml:106-125`).

**What worked.** The registry turned vague claims into countable, falsifiable ones. Reviewers could audit "overstated registrations" as a finding class (`m1-eleventh-review-disposition.md:7`; `m2-m7-review-disposition.md:11-12`).

**What it did not catch.** A requirement is `implemented` when a test against fakes passes. Nothing in the schema asks whether the mechanism is *reachable from the deployed entrypoint*. The plan says: "The ~60 domain modules are reachable only from tests" (`gap-closure-plan.md:15-17`). The spec did want production-equivalent cloud component tests (`arcwell-spec.md:1288`), yet the registry reported 544/544.

### 3.3 Milestone gate definition as used

The spec defines each milestone as **Deliver** (a noun list) plus **Exit gates** (commands and named scenario IDs). It adds a rule: "Do not begin a later milestone to hide an unmet earlier invariant" (`arcwell-spec.md:1726-1765`). The ledger then records:

- deliverables in full spec wording, each checked item carrying its proof (`milestone-ledger.md:12-19`);
- exit gates with timestamps and counts: "final green runs 2026-08-14 10:08–10:10 UTC … 543 entries, milestone-0 gate 11/11 verified" (`milestone-ledger.md:21-23`);
- "Adversarial review completed and findings addressed", pointing to the disposition doc (`milestone-ledger.md:28`);
- known limitations "recorded rather than hidden" (`milestone-ledger.md:130-211`);
- explicit non-closure language: "Milestone 1 does NOT close on this evidence alone … a green gate proves the named tests pass" (`milestone-ledger.md:213-216`).

**Status vocabulary actually used in headings:** `CLOSED <date>`; `IMPLEMENTATION COMPLETE; HUMAN GATE PENDING`; `PROVISIONALLY CLOSED; FINAL REVIEW PENDING`; `IMPLEMENTATION COMPLETE; M2–M7 REVIEW DISPOSITIONED; LIVE GATES PENDING` (`milestone-ledger.md:10,218,230,241,269`). The amended gate for M2–M7: "every named non-live exit gate is green, registry traceability is complete, critical mutation testing is green, and environment-dependent live gates have real bounded fail-closed mechanisms with their execution state recorded honestly" (`review-process-amendment.md:11-14`).

**Moving a gate.** It takes a normative erratum, never a ledger footnote: "a change to the contract has to be written down where the contract lives" (`supplementary-requirements.md:17-21`). ERRATUM-001 moves OPS-T04 to M5 because "any Milestone 1 test claiming to satisfy `OPS-T04` would be exercising a fixture" (`supplementary-requirements.md:29-34,42-43`). Reviewers policed goalpost-moving directly. Contested demotions were "built, not re-argued" (`arcwell/docs/operations/m1-fourteenth-review-disposition.md:141-146`).

**A weakness in the gate.** Deliverables such as "X, GitHub, feed/web … adapter contracts and deterministic fixture suites" (`milestone-ledger.md:221`) were satisfiable by contracts and fakes. The closure records M2–M6 are short Delivered / Verification / Acceptance notes (`arcwell/docs/operations/m2-acceptance.md:3-44`; `arcwell/docs/operations/m5-closure.md:1-32`; `arcwell/docs/operations/m6-closure.md:1-31`). They certify only automated, non-live gates. M5's closure lists "plugin catalog reload/authorization and lifecycle-hook smoke contracts" (`m5-closure.md:13-14`). Yet two days later the gap plan found that `plugins/arcwell/` "is a README that claims Milestone 5 implementation; nothing is there" (`gap-closure-plan.md:34-35`). The plugin README was later made real (`arcwell/plugins/arcwell/README.md:5`).

### 3.4 What the first production run revealed

The first autonomous morning ran "end to end autonomously: zero Cloudflare errors, no wedged spend" (`morning-remediation-handoff.md:26-27`). The 8-agent audit still found defects of a completely different class from the ones the 20 review rounds had hunted:

- **Silent integration no-ops.** 30 sources were "hard-denied on EVERY sweep and have contributed zero evidence since cutover". The runtime passed a raw symbolic endpoint to a URL authorizer that fails closed. "It is SILENT because `recordIncident` … and `recordManifest` are production no-ops" (`morning-remediation-handoff.md:72-88`). The remote agent's summary: "The silence mattered more than the denial … an in-memory harness cannot prove persistence" (`arcwell/docs/handoff/2026-08-21-remediation-status.md:56-60`).
- **Health metrics that measured the wrong table.** Doctor read `fetch_attempt`, "which the live acquisition path never writes, so it lists ALL 271 enabled sources as 'never fetched' — noise that hides the real 30" (`morning-remediation-handoff.md:169-173`).
- **False success in orchestration.** "The `brief.audio` continuation records `completed` over a FAILED audio operation" (`morning-remediation-handoff.md:177-178`).
- **Product-quality failures.** "4/6 stories on 08-21 were 'a GitHub repo exists' non-events". The causes were evidence starvation and a persona leak that tripped gates, so that "80% of stories needed a paid retry" (`morning-remediation-handoff.md:93-111`).
- **A time-zone budget collision.** UTC-day versus owner-local-day (`morning-remediation-handoff.md:125-131`).
- **A latent defect exposed by a fix.** Once incidents became durable, "No code path resolves a `source.acquisition` incident". A doc comment "describes the condition's existence, not any caller of it" (`post-deploy-verification.md:72-93`).

Compare the M1 review subjects: incident resolution evidence, doctor blind spots and false reds, continuation completion binding (`milestone-ledger.md:55-66`). The *same concepts* were reviewed for 18 rounds at the substrate level. The production wiring that calls them was never in scope. **(Inference.)** Adversarial review is only as good as the surface it is pointed at. The skill must point reviewers at the deployed path, "who calls this in production?", and not only at the invariant-holding module.

### 3.5 Review mechanics that worked

- **External review artifacts plus in-repo dispositions.** Review reports live in `.maestro/complex_reasoning/<round>.md`. Each repo disposition starts with `Source: … Verdict: …` and a count summary (`m1-eleventh-review-disposition.md:3-7`; `m1-rereview-disposition.md:3-7`). The reviewer's text stays untouched, and the builder answers row by row.
- **Row format with proof triple.** A FIXED row names the mechanism, the proving test (`cost_005_a_settlement_statement_cannot_move…`) and the mutation target (`cost/settlement-token`) (`m1-fifth-review-disposition.md:25`). An unfixable item reads "ACCEPTED, NOT FIXED", followed by a demotion and where the proven properties moved (`m1-fifth-review-disposition.md:27`).
- **Standard section set per round.** New defects / reopened items / mutation integrity / demotions / residuals carried forward / verification after this round (`m1-eleventh-review-disposition.md:18,31,46,80,118,139`).
- **Accepting a repeated verdict instead of re-arguing.** "A second independent round rejecting the same argument is the signal this process exists to produce" (`milestone-ledger.md:59`).
- **Mutation hygiene as a review target.** Reviewers found mutants that were non-causal, equivalent, syntactically invalid, or killed only by a diagnostic difference (`milestone-ledger.md:86-128`). The rule that emerged: an invariant enforced twice cannot be targeted, so "the code keeps both checks and loses the coverage claim" (`m2-m7-review-disposition.md:48-51`).
- **Property models derived from spec tables, not implementation.** Models were built from "spec transition TABLES written as data … so a service that drifts from the spec fails even when self-consistent" (`m1-adversarial-disposition.md:46-53`).
- **Simplification audits run read-only with a byte-identical proof.** "The audit phase was required to leave the repository byte-identical — and was proven to, by recursive diff" (`milestone-ledger.md:290-293`).
- **Architecture rules as data with reasons.** Every boundary, restricted constructor and size exception in `arcwell/architecture-rules.json:1-188` cites a requirement ID or carries "reviewedBy". Review findings became lint rules, for example the 5+ trust-root lint bypasses closed round by round (`milestone-ledger.md:57,59`).

### 3.6 What was costly

- **Non-converging review loops.** From R14 onward each round reports defects "created by the previous round's own fixes" (`milestone-ledger.md:64-67`). The owner's rationale for the amendment: "Repeating that remediation loop before implementing any later product surface prevented progress on the remaining normative plan" (`review-process-amendment.md:25-28`).
- **Ledger bloat.** Single ledger bullets run to more than 2,000 characters (the view truncates `milestone-ledger.md:47` and `:63`). The residual list alone is about 80 lines (`milestone-ledger.md:130-211`). **(Inference.)** A human cannot scan this. A resuming agent must read tens of thousands of tokens to recover state.
- **Proof numbers that go stale.** A recorded mutation score was unreproducible after a refactor (`m1-fifth-review-disposition.md:8-12`). CI still says mutation testing "joins this list with the first Milestone 1 critical modules" as a comment at M7 (`ci.yml:39`), so the campaign is only validated, not run, in CI (`arcwell/package.json:20`) **(inference from the file)**.
- **Precision spent on low-value edge cases.** R10 fixed `Africa/Monrovia` (−00:44:30 until 1972) resolving thirty seconds late (`milestone-ledger.md:60`), while the delivered product had no adapters (`gap-closure-plan.md:18-22`).
- **Overclaiming docs.** Three in-tree claims were wrong and needed a "Phase 0 — Truth and hygiene" (`gap-closure-plan.md:44-57`).

### 3.7 Handoffs and verification honesty

The handoffs are the most transferable artifacts. They were written so that "A remote agent … may pick this up while the owner's local network is down. Everything needed to continue is here" (`morning-remediation-handoff.md:5-7`). They come as a *triad*:

1. a **plan handoff** with root causes at exact file:line "as of this commit" (`morning-remediation-handoff.md:37-41`);
2. a **status companion** to the plan handoff, "which remains the authoritative statement of the defects". It has a Landed table (Item | PR | What changed), a "Not done — owner action required" section, and a closing "Note on verification honesty" that says: "None of it is backed by production behavior" (`remediation-status.md:3-22,121-127,216-221`);
3. a **post-deploy verification** that classifies every expectation as Observed / Inferred / Unverified. It explains why a flat metric is *not* evidence of failure, and names new must-fix defects without silently doing them ("outside this turn's scope") (`post-deploy-verification.md:5-13,59-101`).

The runbook and drills use the same evidence discipline. The runbook table is `# | Step | Evidence | Rollback`, with "No step is marked done without its named evidence" (`arcwell/docs/operations/cutover-runbook.md:3-8`). The drills table is `# | Failure class | Automated proof | Live drill (injected fault) | Status` (`arcwell/docs/operations/incident-drills.md:9`).

## 4. Opinionated spec for the skill (rules derived from practice)

**Evidence and status**

- **MUST** check a STATUS item only with its proof identity attached: the command, the date/commit, and the counts or output line (`milestone-ledger.md:4,21-28`).
- **MUST** use distinct completion levels: *implemented (mechanism)*, *verified offline*, *deployed*, *observed live*, *accepted by human*. Never collapse them (`deep-research/SKILL.md:75-77`; `requirements-curation.yaml:315-319`).
- **MUST** tag every verification claim in handoffs and final reports as Observed / Inferred / Unverified. Each Unverified item carries the exact closing command (`post-deploy-verification.md:5-13`).
- **MUST NOT** let any agent mark a live, human or owner gate PASSED. Agents record mechanism state and PENDING only (`live-acceptance.md:8-12`; `m3-human-evaluation.md:51-52`).
- **MUST** make demotion first-class. Any reviewer or agent may move an item back to planned with a note naming the gap and the re-registration bar. A red gate after demotion is reported as "the gate working" (`requirements-curation.yaml:10-15`; `m1-adversarial-disposition.md:12-15`).

**Requirements and spec (scope L/XL)**

- **MUST** give every normative requirement a stable ID. It is referenced by at least one test or a named live check, and CI/verifier rejects orphans, unknown IDs and stale generated registries (`arcwell/README.md:21`; `arcwell-spec.md:1276-1279`).
- **MUST** use reverse citation: a test counts as proof only if it cites the ID it proves. **SHOULD** reject a single test as sole oracle for more than N critical requirements (`verify-requirements.ts:243,277`).
- **MUST** hash-pin the spec. Changes go through an errata section with a rationale, and are "written down where the contract lives" (`spec.sha256:1`; `supplementary-requirements.md:17-21`).
- **SHOULD** test the gates themselves with deliberately broken inputs through the production verifier CLI (`milestone-ledger.md:27`).

**Milestones and integration**

- **MUST** include a *walking-skeleton / reachability* gate in the first build milestone for any deployable system. The real entrypoint is deployed (or run in a production-equivalent runtime) and calls at least one real domain path with bindings. Every later milestone adds "reachable from the entrypoint" as a registry column (`gap-closure-plan.md:9-37`; `arcwell-spec.md:34`).
- **MUST** reject a module as `implemented` if its only callers are tests. Wiring no-ops (`recordIncident` as a no-op) are blocker findings (`morning-remediation-handoff.md:86-88`).
- **MUST** name deliverables and exit gates per milestone as commands plus scenario IDs, and use explicit heading states (CLOSED / PROVISIONALLY CLOSED / IMPLEMENTATION COMPLETE; X PENDING) (`milestone-ledger.md:10,230,241`).
- **SHOULD** give every health or doctor metric an oracle that runs against the *live write path*, not a table only tests write (`morning-remediation-handoff.md:169-173`).

**Reviews**

- **MUST** give reviewers the full reference set: spec, registry, the tests for the reviewed surface, and the production call graph or entrypoint (`m2-m7-review-disposition.md:55-58`).
- **MUST** disposition every finding as FIXED (mechanism + test + mutation/regression) / RESIDUAL (rationale, register entry) / CONTESTED (cited evidence) / ACCEPTED-NOT-FIXED (demotion) (`m2-m7-review-disposition.md:11-15`; `m1-fifth-review-disposition.md:25-27`).
- **MUST** cap review→remediate rounds per gate (default 3 at L, 5 at XL). After the cap, escalate to the human with a convergence summary: new-finding count per round, the share caused by the previous round's fixes, and the highest severity. Do not loop silently (`review-process-amendment.md:23-28`; `milestone-ledger.md:64-67`).
- **SHOULD** always run a *focused re-review of the remediated surface* after a large remediation, because "a large remediation introduces defects while closing them" (`milestone-ledger.md:215-216`; `m2-m7-review-disposition.md:108-111`).
- **SHOULD** accept a verdict rejected twice by independent reviewers instead of re-arguing it (`milestone-ledger.md:59`).
- **MAY** run read-only audits (simplification, security) with a byte-identical proof, and keep their artifacts outside the tree (`milestone-ledger.md:285-293`).

**Test quality**

- **MUST** treat a mutation survivor as an oracle weakness, and validate the mutation registry after refactors (`milestone-ledger.md:86-87,126-127`; `m1-fifth-review-disposition.md:15-17`).
- **SHOULD** derive property/model tests from spec tables, not from implementation (`m1-adversarial-disposition.md:46-53`).
- **MUST** have every production incident add a minimal recurrence fixture before closure (`arcwell-spec.md:1279`).
- **MUST** keep deterministic fakes in CI and bounded, fail-closed live canaries out of CI. Each canary has a spend bound and a cleanup proof (`arcwell/README.md:40`; `live-acceptance.md:14-20`).

**Stop conditions**

- **MUST** carry a STOP list: escalate rather than improvise. The user's list includes "a test can pass without observing the user-relevant outcome it claims to validate" and "a milestone would require production credentials or real spend in normal CI" (`arcwell-spec.md:2063-2076`).

## 5. Model & effort assignment (practice-derived, short)

The arcwell docs do not record model identities. Reviews are "Overseer" cycles and `.maestro/complex_reasoning/*` reports (`m0-adversarial-disposition.md:3,42`). The mapping below is therefore **inference** from the task shapes observed:

| Role observed in arcwell | Assign | Guard |
|---|---|---|
| Adversarial constructive reviewer (constructs defects against invariants) | Opus 4.8 high; Fable 5.1 only for the cross-milestone review | Findings must be *constructible* (a repro or test), or they are marked CONTESTED |
| Remediation builder per finding | Sonnet 4.6 medium for mechanical fixes; Opus 4.8 for protocol/state-machine redesign | Focused re-review of the remediated surface |
| Disposition/ledger writer | Sonnet 4.6 low | Verifier script checks that every finding ID has a disposition row |
| Fan-out audit workers (the 25 bounded reviews; the 8-agent production audit) | Sonnet 4.6 medium, one subsystem each | Opus/Fable meta-audit reconciles and drops unsupported claims (`milestone-ledger.md:286-287`) |
| Convergence judge (continue vs. escalate) | Fable 5.1 orchestrator | Hard round cap; human escalation |
| Registry/citation linting | Script, not a model | CI |

## 6. Project-shape conditionals

- **IF greenfield multi-platform app (arcwell-like) THEN** use the full stack: hash-pinned spec, ID registry, milestone ledger, per-milestone review with a round cap, a live register, and incident drills. **AND** make M1 a walking skeleton that deploys the real entrypoint with bindings and one real adapter per external provider class, *before* deep invariant hardening. Arcwell's order was contracts → kernel → all domains → "gap closure" → deploy (`gap-closure-plan.md:39-40,65-69`). The skill should put deploy near the start instead.
- **IF task has a human-taste product (editorial, UI, audio) THEN** pin a blinded rubric gate with fixtures, dimensions, thresholds and an evidence list, recorded PENDING until a human runs it (`m3-human-evaluation.md:8-49`). Automated rubric/vision checks are pre-filters, not acceptance.
- **IF deep bug hunt THEN** use the 8-agent audit shape: one agent per symptom, root cause at file:line, a regression test "fails against the old query" (`remediation-status.md:31-33`), and the three-state post-deploy verification. Skip the registry. Add the TEST-004 recurrence fixture.
- **IF feature in an existing product THEN** reuse the existing verification bar as the gate ("each item passed the full repository bar before merge", `remediation-status.md:8-10`), and add a reachability check from the real entrypoint. Register new IDs only through errata/curation, "never by editing the spec silently" (`gap-closure-plan.md:58-63`).
- **IF service migration/extraction THEN** copy the cutover runbook: Evidence + Rollback per step, shadow mode, and a *suppression fence* so "at no point do both systems own the same external side effect" (`cutover-runbook.md:18`). Treat the legacy code as "reference, not vendor" (`gap-closure-plan.md:295-297`).
- **IF research + marketing website THEN** borrow the research completion contract (executive answer, evidence, contradictions, links, levels of completion) (`deep-research/SKILL.md:70-77`), plus a human editorial gate. Heavy registries are overkill.
- **IF operational/unattended system THEN** require a live register with Spend bound / Cleanup / Status per canary (`live-acceptance.md:14-20`), an incident-drill table (`incident-drills.md:9-21`), and "every red names its repair verb" (`ops-control/SKILL.md:15-17`).

**Scale by scope**

| Scope | Registry | Review | Ledger | Live/human gates |
|---|---|---|---|---|
| S (bug, small change) | none; a checklist in STATUS | 1 independent verifier pass | STATUS entry with proof identity | Observed/Inferred/Unverified in the final report |
| M (feature) | a requirements table in the spec, with test names | 1 review + focused re-review | milestone section per feature | PENDING list |
| L (subsystem/migration) | YAML registry + citation check | ≤3 rounds per gate, then escalate | ledger + disposition docs | live register + rollback runbook |
| XL (arcwell) | generated registry, hash-pinned spec, strict mode | per-milestone ≤5 rounds + one cross-milestone review + focused re-review | ledger, residual register, errata | live register, drills, blinded human gate |

## 7. Artifacts & templates (reuse the user's structures)

**7.1 Milestone ledger entry** (from `milestone-ledger.md:10-31`):

```markdown
## Milestone N — <name> — <CLOSED YYYY-MM-DD | PROVISIONALLY CLOSED; <X> PENDING | IMPLEMENTATION COMPLETE; <gate> PENDING>

Deliverables (spec wording):
- [x] <deliverable> — <what proves it>
Exit gates (final green runs <date time UTC>, commit <sha>):
- [x] `<command>` — <counts/output line>
- [x] Reachable from production entrypoint: <route/binding + observed probe>
- [x] Adversarial review completed — <n> findings dispositioned in <path>
- [ ] <live/human gate> — PENDING (no agent may mark passed)
Known limitations carried forward (recorded rather than hidden):
- <limitation> — <why> — <milestone/ID where it lands>
```

**7.2 Registry entry**: see §3.2. Add `reachable_from:` (entrypoint path or route) as the skill's one addition.

**7.3 Review disposition doc** (from `m1-eleventh-review-disposition.md:1-18,139-154`; `m2-m7-review-disposition.md:1-17,93-102`):

```markdown
# <Milestone/scope> — <ordinal> review disposition
Source: `<review artifact path>`. Verdict: **<verbatim verdict>** — <counts by class>.
Severity classes: constructible defect / overstated registration / residual.
Dispositions: FIXED / RESIDUAL / CONTESTED / ACCEPTED-NOT-FIXED.
## 1. Findings
| # | Finding | Disposition (mechanism · proving test · mutation/regression target) |
## 2. Reopened items from previous round
## 3. Mutation / oracle integrity
## 4. Demotions (ID · to milestone · why · re-registration bar)
## 5. Residuals carried forward
## 6. Verification after this round (every command + counts)
## Verdict / convergence: new findings <n>, caused by previous fixes <k>, max severity <s>, round <r>/<cap>
```

**7.4 Live acceptance register entry** (from `live-acceptance.md:14-20`):

```markdown
## <LIVE-ID> — <name> (`<command>`)
- Requirement: <ID> — <clause>
- Mechanism: <path> — <bounds/scope>
- Spend bound: <calls/bytes/cost per run>
- Cleanup: <cleanup mode + read-back>
- Status: PENDING — requires <bindings> | PASSED <date> — evidence <link>  (human only)
```

**7.5 Handoff (plan)** (from `morning-remediation-handoff.md:1-208`):

```markdown
# <System> — handoff & plan (<date>)
<one paragraph: why written, who may pick up, "everything needed is here">
## Orientation   (repo/branch/commit · deployed resources · schedules · what a remote agent CANNOT do)
## State after <date> (what works — verified how)
## Remediation plan (priority order, with exact fixes)
Verification bar: `<commands>` · Deploy: `<command>`
### P0 — <title> (<deadline if any>)
Symptom · Root cause (file:line as of <sha>) · Fix · Verify with <test> · Evidence query
## Recovery procedures (operational)
## Note for a remote agent (what is doable, start order)
```

**7.6 Status companion + post-deploy verification** (from `remediation-status.md:1-22,121-127,216-221`; `post-deploy-verification.md:1-13,203-222`): a `Landed | PR | What changed` table; "Not done — owner action required" with exact commands; "Note on verification honesty"; then a verification doc whose sections are **Observed**, **Inferred** and **Unverified (with closing command and expected output)**, followed by Repository state and Still owner-only.

**7.7 Runbook and drills tables**: `| # | Step | Evidence | Rollback |` plus standing rules (`cutover-runbook.md:8-31`); `| # | Failure class | Automated proof | Live drill (injected fault) | Status |` (`incident-drills.md:9`).

**7.8 Human evaluation gate**: Status / pinned protocol (reviewers, blinding) / fixtures / rubric 0–4 per dimension / acceptance threshold / evidence to record (`m3-human-evaluation.md:1-52`).

**7.9 Skill-file style**: frontmatter `name` plus a `description` that starts with "Use for/Use when …" and a trigger list; an H1; "Rules:" bullets; a fallback section; a "Completion contract" (`deep-research/SKILL.md:1-6,57-77`; `ops-control/SKILL.md:1-8`). Tool names are bound to a live catalog and not frozen (`arcwell/plugins/arcwell/README.md:9`).

## 8. Anti-patterns & failure modes observed

1. **Green kernel, dark product.** Every gate was green and 544/544 requirements verified, yet the deploy was "a 0.37 KiB bundle with **no bindings**" (`gap-closure-plan.md:15-17`). Its cause: milestones whose deliverables fakes could satisfy, plus a registry with no reachability dimension.
2. **Review fatigue and non-convergence.** Rounds 14–17 mostly reviewed the previous round's fixes (`milestone-ledger.md:64-67`). The loop ended by owner fiat while the verdict was still "reject closure" (`m1-eighteenth-review-disposition.md:3-6`). **(Inference.)** Without a cap, a reviewer paid to find defects always finds some, and the builder always adds surface area.
3. **Wrong review surface.** The substrate was hardened against constructed attacks while production wiring had no-op recorders and a doctor reading an unused table (`morning-remediation-handoff.md:86-88,169-173`).
4. **Claiming what was not built or run.** "Ledger showed M0 not closed" and "Verification passed planned requirements" were M0 findings (`m0-adversarial-disposition.md:10-11`). "The fourth round's 'all twelve FIXED' claim is false" (`m1-fifth-review-disposition.md:3-4`). The plugin README claimed an implementation that did not exist (`gap-closure-plan.md:34-35`). A doc comment claimed a resolver that nobody called (`post-deploy-verification.md:82-85`). The countermeasure that worked was independent review plus "no agent may mark passed" (`live-acceptance.md:12`).
5. **Stale proof numbers.** A score recorded against a refactored tree was not reproducible (`m1-fifth-review-disposition.md:8-12`). A CI promise remained a comment (`ci.yml:39`).
6. **Inflated mutation scores.** Mutants killed by a diagnostic difference, SQL bind arity, syntax errors, or an equivalent change (`milestone-ledger.md:88-96`).
7. **Goalpost-moving by demotion.** Reviewers flagged demotions as "goalpost-moving" or "retreat" (`milestone-ledger.md:62,67`). Demotion is honest only with a normative erratum and a re-registration bar.
8. **Context-starved reviewers.** A reviewer "lacked the test files (not in its reference set)" and filed false findings (`m2-m7-review-disposition.md:55-58`).
9. **Unscannable state docs.** Ledger bullets over 2,000 characters and an 80-line residual list (`milestone-ledger.md:47,130-211`). The skill should keep STATUS terse and link out.
10. **Silent failure paths.** "The silence mattered more than the denial" (`remediation-status.md:56`). A health projection that shows 25 of 103 findings hides the rest (`post-deploy-verification.md:41-42`).
11. **False success states.** A continuation recorded `completed` over a failed operation (`morning-remediation-handoff.md:177-178`). This is the ops analogue of "declaring a queued action complete", which the spec forbids (`arcwell-spec.md:38`).
12. **Cost trap: paid retries caused by prompt design.** A persona leak drove "80% of stories [to need] a paid retry" (`morning-remediation-handoff.md:105-108`).

### 8.1 Encode this / avoid this — recommendations for the mission engine

| # | Encode / Avoid | Recommendation | Evidence |
|---|---|---|---|
| R1 | Encode | Add a walking-skeleton gate to the first build milestone: deploy the real entrypoint with real bindings and one real adapter; add a `reachable_from` column to requirements | `gap-closure-plan.md:9-37`; `arcwell-spec.md:34` |
| R2 | Encode | Check STATUS items only with proof identity (command + commit/date + counts) | `milestone-ledger.md:4,21-28` |
| R3 | Encode | Report verification as Observed / Inferred / Unverified, with the closing command for each Unverified item | `post-deploy-verification.md:5-13` |
| R4 | Encode | Hard rule: agents never mark live, human or owner gates PASSED; they record PENDING plus a mechanism | `live-acceptance.md:12`; `m3-human-evaluation.md:51-52` |
| R5 | Encode | Use a fixed disposition vocabulary (FIXED with test+mutation / RESIDUAL / CONTESTED / ACCEPTED-NOT-FIXED+demotion) and a residual register | `m2-m7-review-disposition.md:11-15`; `m1-fifth-review-disposition.md:25-27` |
| R6 | Encode | Cap review→remediate rounds (L: 3, XL: 5). Log convergence per round (new findings, fix-induced findings, max severity), then escalate to the human | `review-process-amendment.md:23-28`; `milestone-ledger.md:64-67` |
| R7 | Encode | After any large remediation, run a focused re-review of only the remediated surface | `m2-m7-review-disposition.md:108-111`; `milestone-ledger.md:215-216` |
| R8 | Encode | Give reviewers the full reference set, including tests and the production call path. Require constructible findings | `m2-m7-review-disposition.md:55-58`; `post-deploy-verification.md:72-81` |
| R9 | Encode | Hash-pin the spec; change gates only through errata; make demotion cheap, with a re-registration bar | `spec.sha256:1`; `supplementary-requirements.md:17-21`; `requirements-curation.yaml:10-15` |
| R10 | Encode | Require reverse test citation (a test must cite the ID it proves), an oracle-strength limit, and gates that are themselves tested with deliberately broken inputs | `verify-requirements.ts:243,277`; `milestone-ledger.md:27` |
| R11 | Encode | Use the handoff triad (plan with file:line root causes → status companion with "Not done" section and honesty note → post-deploy verification) | `docs/handoff/*` (§3.7) |
| R12 | Encode | Every production incident gets a recurrence fixture, and every doctor/health metric is tested against the live write path | `arcwell-spec.md:1279`; `morning-remediation-handoff.md:169-173` |
| R13 | Avoid | Don't let reviews spend rounds on exotic invariants while nothing is deployed. Order work deploy → integrate → harden | `milestone-ledger.md:60`; `gap-closure-plan.md:18-22` |
| R14 | Avoid | Don't record scores or commitments that CI does not re-derive (mutation `--validate`, CI comments promising a gate) | `m1-fifth-review-disposition.md:8-17`; `ci.yml:39` |
| R15 | Avoid | Don't grow state docs by accretion. Keep STATUS terse, link out to disposition docs, and keep LESSONS as short rules | `milestone-ledger.md:47,130-211` |

## 9. Open questions / risks for the synthesizer

- **How much of arcwell's heaviness should be the default?** The brief says the user sees this heavy process as how they *should* work (`research/mission-skill/00-brief.md:7-10,55-62`). Yet they directed a stop after 18 rounds (`review-process-amendment.md:3-5`). I assumed they want the evidence discipline without the loop cost. Scope defaults (§6) encode that assumption.
- **Round-cap numbers (3/5) are my judgement**, not derived from data. A better stop rule might watch the share of findings induced by previous fixes. Arcwell shows this rising from R14 onward, but earlier rounds do not report the split, so no threshold can be calibrated from it.
- **Model identities for arcwell's reviewers are unknown** (`.maestro` reports are outside the workspace). §5 is inference.
- **Registry tooling cost.** Arcwell built a custom generator/linter (`arcwell/package.json:17-19`; `packages/devtools`). The skill should ship a minimal portable verifier script, or describe the checks so that per-project tooling can be written. The synthesizer must decide.
- **Human gates block completion.** Arcwell's M3 human gate and live gates were still PENDING at the latest ledger state (`milestone-ledger.md:239,279`). The skill needs a "done with pending human gates" terminal state that is not reported as success.
- **Risk of over-applying mutation testing.** It found real oracle weaknesses (`m1-adversarial-disposition.md:60-64`), but it also consumed round-by-round hygiene effort (`milestone-ledger.md:86-128`). Suggested: critical modules only, at L/XL scope.
- **Evidence gaps in this lane.** Seven of 18 M1 disposition docs were sampled directly: the 1st, 2nd, 3rd, 5th, 11th, 14th and 18th. The other rounds' counts come from the ledger summaries. The `.maestro` review reports and the `audit/` directory were not available in the workspace.

## Sources (arcwell files studied; all read-only)

Specification and registry
- `arcwell/docs/product/arcwell-spec.md` — §0 (lines 13-38), §19 (1252-1301), §22 (1726-1785), §26 incl. STOP conditions (2030-2079)
- `arcwell/docs/product/spec.sha256` — spec hash pin
- `arcwell/docs/product/supplementary-requirements.md` — errata ERRATUM-001/002 (15-64)
- `arcwell/REQUIREMENTS.yaml` — generated registry header and entries (1-90, 180-229, kind: test from 3590)
- `arcwell/requirements-curation.yaml` — curation rules, demotion notes, live refs (1-80, 98-127, 305-344)
- `arcwell/packages/devtools/package.json`; `arcwell/packages/devtools/src/verify-requirements.ts` (checkOracleStrength :243, checkCitationCorrespondence :277)
- `arcwell/MILESTONE`; `arcwell/README.md`; `arcwell/package.json`; `arcwell/.github/workflows/ci.yml`; `arcwell/architecture-rules.json`

Milestones, reviews, acceptance
- `arcwell/docs/operations/milestone-ledger.md` (whole file, 321 lines)
- `arcwell/docs/operations/review-process-amendment.md`
- `arcwell/docs/operations/gap-closure-plan.md` (whole file)
- `arcwell/docs/operations/m0-adversarial-disposition.md`
- `arcwell/docs/operations/m1-adversarial-disposition.md`
- `arcwell/docs/operations/m1-rereview-disposition.md` (1-25)
- `arcwell/docs/operations/m1-third-review-disposition.md` (1-20)
- `arcwell/docs/operations/m1-fifth-review-disposition.md` (1-60)
- `arcwell/docs/operations/m1-eleventh-review-disposition.md` (1-40, 139-155)
- `arcwell/docs/operations/m1-fourteenth-review-disposition.md` (141-170)
- `arcwell/docs/operations/m1-eighteenth-review-disposition.md` (whole)
- headings of all `m1-*-review-disposition.md` (grep)
- `arcwell/docs/operations/m2-m7-review-disposition.md` (1-20, 43-122, 147-168)
- `arcwell/docs/operations/m2-acceptance.md`; `m3-human-evaluation.md`; `m5-closure.md`; `m6-closure.md`
- `arcwell/tests/deployed-canary/live-acceptance.md`
- `arcwell/docs/operations/incident-drills.md` (table); `arcwell/docs/operations/cutover-runbook.md`

Handoffs and plugin
- `arcwell/docs/handoff/2026-08-21-morning-remediation-handoff.md`
- `arcwell/docs/handoff/2026-08-21-remediation-status.md`
- `arcwell/docs/handoff/2026-08-22-post-deploy-verification.md`
- `arcwell/plugins/arcwell/README.md`
- `arcwell/plugins/arcwell/skills/deep-research/SKILL.md`; `arcwell/plugins/arcwell/skills/ops-control/SKILL.md`

Short path forms in the body (e.g. `milestone-ledger.md:4`) refer to the full paths above.
