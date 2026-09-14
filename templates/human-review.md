# Human review batch · <mission name> · milestone <M> · batch <YYYY-MM-DD>

<!-- Template: skills/mission/templates/human-review.md → .mission/verification/human-review/<M>/protocol.md (+ form.md,
     contact-sheets/, mapping.json, results.md in the same folder). Rules: references/frontend-verification.md
     V-MUST-18, V-MAY-1, V-MAY-2, Procedure P10–P11. Sections 1–3 are prepared by agents; section 4 is filled by the
     human only; sections 5–6 are completed after the session. Placeholders in <angle brackets>. -->

Goal: spend 20–40 minutes of human time per milestone only on what models judge poorly (taste, conceptual clarity,
brand fit, real-user feel) and return a machine-readable decision.

**No agent may mark the human gate passed.** The STATUS.md gate line changes from `PENDING` only after `results.md`
records the human's own decision, with the reviewer's name and date.

## 1. Batch contents (only these item types; nothing else)

| # | Type | Source | Rule |
|---|---|---|---|
| 1 | `direction` | tournament ties or top-2 finalists (`templates/design-rubric.md` §Tournament) | pairwise; owner decides |
| 2 | `loop-bound` | screens that hit the iteration bound (5, hero 8) with their open findings | best iteration only |
| 3 | `disagreement` | verifier vs verifier (e.g. regression screener vs `mission-reviewer` re-check), CONTESTED visual findings | show both verdicts' evidence, not their prose |
| 4 | `calibration` | 3–5 random screens the pipeline PASSED | measures agent leniency |
| 5 | `flow` | top 1–3 flows: step strip + friction-log summary + "Needs a human?" answers from `templates/walkthrough.md` | |

Session cap: ≤ 25 items and ≤ 90 seconds per item. More items → split into sessions or cut the calibration sample;
never lengthen a session.

## 2. Preparation (agent: `mission-checker` + scripts)

- [ ] One contact sheet per item in `contact-sheets/item-<nn>.png` (or `.html`): relevant variants side by side at a
      readable scale; captions `SCR-NNN / state / device-or-viewport / theme / text size`; **no model scores, verdicts
      or maker names visible** (avoid anchoring).
- [ ] Pairwise items: randomise Left/Right per item; write the mapping to `mapping.json`
      (`{"item-01": {"left": "C2", "right": "C1"}}`) and do not link it from `form.md`. The reviewer does not open it.
- [ ] Pre-fill `form.md` from section 4 with one block per item, in randomised item order.
- [ ] Flow items: step strip of ≤ 8 screenshots with one-line captions from the friction log.
- [ ] Add one line to STATUS `## Human queue`: `- [ ] UI review batch <M> (<n> items, ~<minutes> min, folder
      .mission/verification/human-review/<M>/) · default taken: gate stays PENDING · blocks: <T-ids or "none"> · since <YYYY-MM-DD>`.
- [ ] Continue other work. Do not block unrelated tasks while the batch is pending.

## 3. Session rules (for the human; paste at the top of form.md)

- Reviewers: **M** owner alone (optional batch) · **L/XL** owner + one independent reviewer · **XL pre-launch** one
  real-user session in addition.
- Rate independently; no discussion before both forms are submitted.
- Timebox: about 90 seconds per item. Gut reaction is the data; do not open the app unless an item asks you to.
- Asynchronous is fine: open the folder when convenient.
- Mark anything you would never ship with Q3 = no, even on non-calibration items.

## 4. Review form (one block per item; human only)

```markdown
## Item <nn> · type: <direction | loop-bound | disagreement | calibration | flow>
Contact sheet: <contact-sheets/item-nn.png>
Reviewer: <name> · Date: <YYYY-MM-DD>

Q1 (pairwise items): Left preferred / Right preferred / tie — reason (one line): <…>
Q2 (all items), rate 0–4 each:
  - hierarchy: <0-4>
  - clarity of primary action: <0-4>
  - visual quality / brand fit: <0-4>
  - states and copy: <0-4>
Q3 (calibration and loop-bound items): Would you ship this screen as is? yes / no — if no, the single biggest issue: <…>
Q4 (flow items): Where would a real user hesitate? step <nn> — <one line>
Free text (optional, ≤ 3 lines): <…>
```

Scale for Q2: 4 ready to ship · 3 small polish issues · 2 noticeable problems · 1 serious problems · 0 broken.

## 5. Acceptance thresholds (defaults; tighten per mission by D-entry, never loosen mid-milestone)

| Decision | Threshold |
|---|---|
| Direction | chosen by the owner; independent-reviewer disagreement is recorded under STATUS `## Risks`, not a veto |
| Milestone visual gate | mean Q2 ≥ 3.0 across items (L/XL ≥ 3.3) · no item rated 0–1 on "clarity of primary action" · calibration "would ship" ≥ 80% |
| Calibration below 80% | recalibrate the verifier (human reasons → few-shot examples in `templates/visual-verifier.md` copy) before the next milestone; re-run G2 on this milestone's PASSED screens |
| Flows | any Q4 hesitation reported by both reviewers (L/XL) or by the owner (M) becomes a `major` finding `FND-ux-<flow-id>-NN` |
| Loop-bound items | Q3 yes → accept best iteration with its open findings as RESIDUAL (D-entry); Q3 no → re-plan the screen (design change, not iteration n+1) |

## 6. After the session (agent; results.md)

1. Unseal `mapping.json`; compute per-item results and aggregates; write `results.md`:

| Item | Type | Q1 (revealed) | Q2 mean | Q3 | Q4 | Reasons (verbatim) | Human decision |
|---|---|---|---|---|---|---|---|
| <01> | <direction> | <C1 preferred (was Left)> | <3.5> | <—> | <—> | <"calmer, the tray reads first"> | <owner: C1> |

   Gate decision line (copied verbatim from the human, never inferred): `<ACCEPTED | REJECTED | ACCEPTED-WITH-CHANGES:
   <list>> — <reviewer name>, <YYYY-MM-DD>`
2. Only if the human decision is ACCEPTED (or ACCEPTED-WITH-CHANGES after the changes are verified by G1–G2): promote the
   accepted variants and manifests to `.mission/verification/accepted/SCR-NNN/`; record goldens now (V-MUST-10) and
   update the frozen manifest.
3. Update the STATUS gate line from the recorded decision; remove the Human queue line; add a D-entry for any direction
   choice or accepted residual.
4. Human reasons that contradict agent verdicts become (a) few-shot calibration examples for the verifier brief and
   (b) `L-NNN` candidates in `LESSONS-INBOX.md` (e.g. "verifier under-weights empty-state copy").
5. If no human has responded: leave the gate `PENDING`; list it under STATUS `## Risks` and in HANDOFF.md. Never
   convert PENDING to PASSED on timeout.
