# Option matrix · <decision topic> · <Q-NN> → <D-NNN> / <ADR-NNN>

<!-- Template: skills/mission/templates/option-matrix.md → body of .mission/research/Q-NN.md after the question card
     (references/research.md RS-26..29). Use for T3 decisions (irreversible or expensive: datastore, auth provider,
     hosting platform, sync model, public API style, build vs adopt, new core dependency).
     Order is mandatory: 1 Frozen (commit it: record the sha) → 2 Spikes → 3 Scoring by two independent scorers → 4
     Adjudication → 5 Recommendation → 6 Research basis pasted into the D-entry and ADR Context.
     Changing section 1 after scoring starts needs a D-entry (Kind: spec-change) and fresh scoring.
     Scale: S → three-line note (options, pick, why) in RESEARCH.md inline block, no matrix. M → matrix-lite: 3 options,
     ≤5 criteria, one scorer + one reviewer (`mission-critic` if the choice backs an ADR). L/XL → full matrix, two
     scorers, spikes. Scorers: A `mission-builder`, B `mission-worker-high`; neither sees the other's scores or the
     orchestrator's preference until both submit. Keep the file ≤1,500 words: spike logs go to .mission/logs/<Q-NN>/. -->

## 1. Frozen before scoring

Frozen at: <YYYY-MM-DD> · commit <short sha> · by <orchestrator>

- Problem statement: <what must be decided and why now; requirement IDs affected: <API-003, PERF-002>>
- Constraints from spec/charter: <budget, platform, licence, data residency, team skills>
- Options (include the status quo when one exists):
  - O1 <keep current / do nothing / keep external>
  - O2 <…>
  - O3 <…>

Must-have gates (pass/fail; a failed gate removes the option before scoring):

| G | Gate | Evidence required |
|---|---|---|
| G1 | <runs on <platform/runtime> at <version>> | <PRIMARY docs quote or RUN> |
| G2 | <licence compatible with <licence>> | <P1 licence file at the pinned version> |
| G3 | <data residency <region> / compliance <…>> | <PRIMARY vendor docs, access-dated> |

Criteria (weights sum to 100; anchors fixed now):

| K | Criterion | Weight | How measured (evidence required) | 1 = | 3 = | 5 = |
|---|---|---|---|---|---|---|
| K1 | <latency p50 under workload W> | <25> | <RUN benchmark per plan below> | <above 200 ms> | <about 80 ms> | <below 20 ms> |
| K2 | <operational burden> | <20> | <PRIMARY docs + spike notes> | <self-hosted cluster> | <managed, some config> | <managed, zero-config> |
| K3 | <cost at projected volume <…>> | <20> | <vendor pricing page, access-dated> | <…> | <…> | <…> |
| K4 | <maintenance health> | <15> | <release cadence and open-issue trend from repo tags, access-dated> | <no release 12 months> | <quarterly> | <monthly, maintainers active> |
| K5 | <team familiarity / ecosystem fit> | <20> | <repo evidence: existing usage, CONTEXT.md> | <new to the codebase> | <used elsewhere> | <already in use here> |
| | **Total** | **100** | | | | |

Benchmark plan (required if any criterion is performance; written before any run):
- Workload: <…> · Dataset: <size, shape, source> · Metric: <p50/p95 latency, throughput, memory>
- Warm-up: <…> · Repetitions: <≥5> · Report: median and spread (<IQR | min–max>)
- Environment: <hardware, region, instance type> · Versions: <each option at <version>>
- Decision threshold: <e.g. "O2 must beat O1 p95 by ≥20% or K1 scores equal">
- Vendor benchmarks are P2 claims about the vendor's workload, never scores for K-criteria.

## 2. Spikes (riskiest unknown per front-running option)

| SP | Option | Riskiest unknown (question) | Timebox (S ≤1 h · M ≤half day · L/XL ≤2 days) | Branch / worktree | Expected if viable | Result (RUN: command → salient line) | Code discarded |
|---|---|---|---|---|---|---|---|
| SP-1 | <O2> | <can it stream responses through <platform>?> | <4 h> | <claude/<mission>/spike-<slug>> | <first byte <…> ms> | <`<command>` → `<line>`> | <yes> |
| SP-2 | <O3> | <…> | <…> | <…> | <…> | <…> | <yes> |

Spike code is never merged; adopting an option re-enters as FEA/GRN work with tests.

## 3. Scoring

Scorer A (<agent · model ID>) · submitted <YYYY-MM-DD HH:MM>:

| Option | Gates | K1 | K2 | K3 | K4 | K5 | Weighted (Σ weight × score / 5) | Evidence refs |
|---|---|---|---|---|---|---|---|---|
| O1 | <pass> | <3> | <5> | <4> | <5> | <5> | <…> | <Q-NN/C-2 · SP-1> |
| O2 | <pass> | <…> | <…> | <…> | <…> | <…> | <…> | <…> |
| O3 | <fail G2> | — | — | — | — | — | — | <S-NNN> |

Scorer B (<agent · model ID>) · submitted <YYYY-MM-DD HH:MM>:

| Option | Gates | K1 | K2 | K3 | K4 | K5 | Weighted | Evidence refs |
|---|---|---|---|---|---|---|---|---|
| O1 | <…> | <…> | <…> | <…> | <…> | <…> | <…> | <…> |
| O2 | <…> | <…> | <…> | <…> | <…> | <…> | <…> | <…> |

Every score cites evidence (claim ID, S-NNN, spike, repo path). A score without evidence counts as 1 for that criterion.

## 4. Disagreements and adjudication

Trigger: any gate disagreement, or |A − B| > 1 on any criterion.

| Option · K | A | B | A rationale | B rationale | Adjudicated score | By (orchestrator high effort · `mission-strategist`) | Evidence that decided it |
|---|---|---|---|---|---|---|---|
| <O2 · K2> | <2> | <4> | <…> | <…> | <3> | <…> | <SP-1 result> |

## 5. Recommendation

- Chosen: <option>, because <top 2 reasons with evidence refs>.
- Rejected: <O-n: decisive reason + evidence> · <O-n: …>
- Sensitivity: the result flips if <weight K-n changes by <…> | assumption A-NN is false | cost grows past <…>>.
- Evidence that would reverse this decision: <measurable trigger, e.g. "p95 >150 ms at 2× projected volume">.
- Accepted UNVERIFIED claims (as assumptions): <Q-NN/C-n → A-NN, why acceptable> | none
- Open risks: <…>

## 6. Research basis (paste into the D-entry Context and the ADR Context)

```text
Research basis: <Q-NN> option matrix (frozen <short sha>, scorers <A agent> + <B agent>, adjudicated <K list | none>)
· spikes <SP-1: result one line> · <SP-2: …>
· load-bearing claims: <Q-NN/C-1 CONFIRMED <YYYY-MM-DD> [S-NNN]> · <Q-NN/C-3 RUN <YYYY-MM-DD>>
· rejected options: <O-n: reason> · accepted assumptions: <A-NN> | none
· reverse if: <trigger> · recheck-by <YYYY-MM-DD> (<pricing/vendor facts: 90 days · toolchain: 30 days>)
```

Links: D-<NNN> (DECISIONS.md) · design/adr/ADR-<NNN>.md · RESEARCH.md index line <Q-NN> status `done`.
