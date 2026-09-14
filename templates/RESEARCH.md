# RESEARCH · <project> · mission: <one-line goal>

<!-- Template: skills/mission/templates/RESEARCH.md → .mission/RESEARCH.md (M+; S missions spanning sessions may add it).
     Rules: references/research.md (RS-01..40). Owner: orchestrator only; researchers return drafts to
     .mission/lanes/<lane-id>/ and the orchestrator merges them here and into .mission/research/Q-NN.md.
     Reload rule: session start reads ## Index only (one line per question, ≤ ~40 words). Never load note bodies unless a
     task needs a specific Q-NN. Research IDs are Q-NN (questions) and S-NNN (sources). Never use R- ids here: R-NNN is
     a STATE rule. Claim IDs are local to a note: Q-NN/C-n.
     Statuses: open · researching · fact-check · done · partial(gaps) · conflict · stale · abandoned(<reason>)
     Triggers: T1 version-sensitive API/platform fact · T2 unfamiliar tech · T3 irreversible/expensive choice ·
               T4 hard bug prior art · T5 market/competitor/pricing/legal · T6 public-copy fact
     Evidence levels: RUN > PRIMARY > CORROBORATED > SINGLE > INFERENCE (only RUN/PRIMARY/CORROBORATED reach STATE facts)
     recheck-by: 90 days fast-moving (AI tooling, pricing, competitors, market data) · 30 days toolchain/SDK facts ·
                 competitor/third-party facts revalidated ≤7 days before any publish.
     Stale when: recheck-by passed, lockfile diff touches a dependency on the card, or a citing public claim is about to
     ship. A stale question cannot back a new decision until revalidated. -->

## Index

<!-- One line per question. Verdict ≤20 words. Evidence = top level reached for the load-bearing claims.
     Budget column shows "budget+" after a logged extension in BUDGET.md. Illustrative row is commented out:
| Q-01 | done | T1 | Max request body size on <platform> <version>? | D-003 upload design | <value> on <plan>; confirmed by RUN probe | RUN+PRIMARY | 3×15 | 2026-12-01 | <dependency>@<version> changes | research/Q-01.md |
-->

| Q | Status | Trigger | Question (≤15 words) | Decision unblocked | Verdict (≤20 words) | Evidence | Budget | recheck-by | Stale when | Note |
|---|---|---|---|---|---|---|---|---|---|---|
| Q-01 | open | <T1–T6> | <…> | <D-NNN · T-NNN · requirement ID> | <pending> | <—> | <researchers × calls> | <YYYY-MM-DD> | <trigger> | <research/Q-01.md · inline below (S)> |

## Inline questions (S, or questions answered by one lookup)

<!-- Use instead of a note file when one lookup or probe settles the question. Keep each block ≤6 lines.
- Q-NN · card: <question> · decision: <id + what changes> · done when: <criteria> · trigger: <T1–T6>
  Answer: <≤40 words> · Claims: C-1 <fact> [S-NNN §"<heading>" or "<≤25-word quote>"] <level> conf <high|medium|low>
  RUN: `<command>` → `<salient output line>` (<YYYY-MM-DD>, <env>) · Stopped because: <criteria|saturation|budget|moot>
  Gaps / negative results: <searched <queries> on <date>, found no <X> | none>
-->

## Source registry

<!-- Register once; reuse S-NNN across questions. Only the orchestrator assigns S-NNN (researchers use S-tmp-n).
     Tiers: P1 run output · dependency source/tests at pinned version · official docs/changelog/release notes at that
     version · standards · filings · vendor's own pricing page | P2 maintainer comments · official engineering blogs ·
     peer-reviewed papers | S1 independent practitioners with reproducible detail | S2 aggregators, newsletters, social
     posts, SEO listicles, AI summaries (lead-only, never sole support).
     Notes vocabulary: paywalled · truncated at fetch · snippet-only · quotes S-NNN (not independent) · owner-supplied ·
     INJECTION: <what the page tried> (tier forced to S2). -->

| S | URL | Title | Publisher | Tier | Version described | Published / updated | Accessed | Used by | Notes |
|---|---|---|---|---|---|---|---|---|---|
| S-001 | <https://…> | <…> | <vendor docs · maintainer · blog · competitor site> | <P1·P2·S1·S2> | <3.2 · unversioned> | <YYYY-MM-DD / YYYY-MM-DD> | <YYYY-MM-DD> | <Q-01/C-1> | <…> |

## Promotions to STATE

<!-- Only claims with level RUN/PRIMARY/CORROBORATED, confidence ≥ medium and (M+) fact-check CONFIRMED. The fact itself
     lives in STATE.md; this section keeps one pointer line per promotion so revalidation finds dependents.
     Pointer line:
- F-NNN ← Q-NN/C-n · CONFIRMED <YYYY-MM-DD> · recheck-by <YYYY-MM-DD>

     STATE.md → ## Verified facts line (the orchestrator writes it there; memory-lint requires Evidence, Level, verified):
- F-NNN · <fact, one sentence, with version/plan it applies to> · conf: <medium|high> · verified <YYYY-MM-DD> · recheck-by <YYYY-MM-DD>
  Evidence: Q-NN/C-n [S-NNN §"<heading>"] <RUN|PRIMARY|CORROBORATED>, fact-check CONFIRMED <YYYY-MM-DD> (RUN: `<command>` → `<salient line>`)
  Level: <local-run|ci|staging|production for RUN · doc-source for PRIMARY/CORROBORATED> · Scope: <version, plan, region> · Supersedes: <H-NNN|F-NNN|—>

     UNVERIFIED, NEEDS-VERSION-CHECK, SINGLE, INFERENCE or UNVERIFIED-OFFLINE claims go to STATE ## Hypotheses (H-NNN
     with a Check:) or ASSUMPTIONS.md (A-NN with reversal cost), never to Verified facts.

     Decision citation (D-entry Context/Options, ADR Context):
     Research basis: Q-NN (matrix/note) · load-bearing Q-NN/C-n CONFIRMED <date> [S-NNN] · accepted assumptions A-NN -->

## Revalidation log

<!-- Milestone close, lockfile change, recheck-by passed, and ≤7 days before publish.
- <YYYY-MM-DD> · Q-NN · trigger <milestone M<n> | lockfile <dep>@<old>→<new> | recheck-by | pre-publish> · result <unchanged | changed: <what> → D-NNN/F-NNN updated | stale, blocked decision <id>>
-->

## Note skeleton

<!-- Copy the block below into .mission/research/Q-NN.md (M+). ≤1,500 words including tables; raw extracts go to
     .mission/tmp/, lane drafts stay in .mission/lanes/<lane-id>/. T3 decisions use templates/option-matrix.md as the
     body after the card; positioning questions use templates/positioning.md.

# Q-NN · <short title>

## Question card
- Opened: <YYYY-MM-DD> · Owner: <orchestrator | agent roster name> · Trigger: <T1–T6> · Class budget: <S|M|L|XL>
- Question: <one precise question>
- Decision it unblocks: <D-NNN | T-NNN | requirement ID> — what changes with the answer: <…>
- Scope / time window / versions: <e.g. "<platform> docs as of today; <package>@<version> from <lockfile>">
- Done criteria: <e.g. "limit value with a PRIMARY quote at the pinned version + a RUN probe on dev">
- Counter-question(s): <e.g. "does the limit differ on the paid plan or with streaming?">
- Sub-questions (M+): SQ1 <…> (source family <…>, lane <id>) · SQ2 <…> (…) · SQ3 <…>
- Budget: <researchers × tool calls> · Stop: criteria · saturation (2 rounds nothing new) · budget · moot
- Sensitivity: <public-safe queries only | internal names allowed (why)>
- Route: <inline | mission-scout | researchers from templates/researcher.md | /deep-research>

## Answer
<≤100 words at the decision's precision.>
Status: <done | partial | conflict | abandoned(<reason>)> · Stopped because: <criteria | saturation | budget | moot>

## Claims
| C | Claim (one fact) | Applies to (version/plan/date) | Sources + location | Level | Conf | Fact-check | Load-bearing |
|---|---|---|---|---|---|---|---|
| C-1 | <…> | <v3.2.x> | [S-NNN §"<heading>"] [S-NNN "<≤25-word quote>"] | <RUN · PRIMARY · CORROBORATED · SINGLE · INFERENCE> | <high · medium · low> | <CONFIRMED · REFUTED · UNVERIFIED · NEEDS-VERSION-CHECK · —> | <yes · no> |

## RUN evidence
- C-n: `<command>` → `<salient output line>` (<YYYY-MM-DD>, <env>; log: .mission/logs/<path>)

## Conflicts
- C-n: S-NNN says <…> vs S-NNN says <…>; checked version/plan/config: <…>; resolution: <newer at-version P1 | RUN result | CONFLICT escalated to <agent/human>>

## Gaps and negative results
- Searched <queries / sites> on <YYYY-MM-DD>; found no evidence of <…> (coverage: <…>).

## Rejected claims (audit only; never promote or publish)
- C-n REFUTED by S-NNN: <…>

## Promotions and citations
- STATE F-NNN ← C-n · D-NNN / ADR-NNN cites Q-NN · CLAIM-NNN ← C-n · A-NN ← C-n (UNVERIFIED)

## Staleness triggers
- <dependency@version> · <90-day topic: yes|no> · <cited by public claim: yes|no> · recheck-by <YYYY-MM-DD>
-->
