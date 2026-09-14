# Design rubric (craft thresholds, AI-default tells, tournament protocol)

<!-- Template: skills/mission/templates/design-rubric.md. Shared with the UI maker AND the visual verifier (V-SHOULD-4).
     Rules: references/frontend-verification.md V-MUST-11..13, V-SHOULD-3..5. Edit the brief-specific lines marked
     <placeholder>; keep criteria concrete. Do not add aspirational superlatives ("museum quality", "world-class"): they
     steer makers toward convergence. -->

Mission: <name> · Class: <S|M|L|XL> · Consumer-facing: <yes|no> · Brief anchors: <2–3 reference apps/sites or
"extracted from existing product"> · Tokens: `.mission/design/tokens.md`

Scores 0–4 per criterion. Anchors are given for 4, 2 and 0; 3 and 1 sit between the neighbouring anchors. Criteria
1–10 are **craft** (gated by thresholds). Criterion 11 is **taste** (decided by tournament, never by threshold). Gate A
is binary and overrides every score.

## Gate A — accessibility floor (binary, from G1 only)

| Check | Web | iOS |
|---|---|---|
| Automated audit | zero axe WCAG A/AA violations without a written, registered suppression | zero `performAccessibilityAudit` issues without a written, registered suppression |
| Target size | interactive boxes ≥ 24×24 CSS px or WCAG 2.5.8 spacing exception | hit targets ≥ 44×44 pt |
| Text at large sizes | no clipped text or horizontal overflow at 320 px reflow on key screens | no `textClipped` / `dynamicType` issue at the largest accessibility size on key screens |
| Focus / traversal | visible keyboard focus on every focusable element | VoiceOver order matches spec region order |

Gate A fail → verdict FAIL regardless of scores.

## Craft criteria (0 / 2 / 4 anchors)

| # | Criterion | 4 — excellent | 2 — acceptable with issues | 0 — broken |
|---|---|---|---|---|
| 1 | `hierarchy` | primary action and key content identifiable at a glance on every variant; order matches spec regions | primary action findable but competes with secondary elements on some variant | primary action missing or hidden, or spec order violated |
| 2 | `layout_integrity` | no overlap, clipping, off-screen or orphaned elements across the matrix (G1 clean) | awkward wrapping or reflow on one variant, content intact | overlap, clipping or off-screen content on any key variant |
| 3 | `spacing_rhythm` | all spacing from the token scale; related items closer than unrelated | a few off-scale gaps; grouping mostly clear | arbitrary spacing; ambiguous groups; cramped or floating blocks |
| 4 | `alignment` | shared edges and baselines; G1 left-edge clusters ≤ 2 per column | occasional 1–4 px misalignments | visibly ragged edges; mixed centre/left alignment without reason |
| 5 | `typography` | type scale from tokens, ≤ 2 families, clear size/weight steps, body line length ≤ ~80ch | one or two off-scale sizes or weak step contrast | many sizes/weights, unreadable sizes, overlong lines |
| 6 | `color_contrast` | colour roles per tokens; meaning never colour-only; contrast passes in both themes | off-token colour in a non-key place; dark theme weaker but passing | contrast failures, colour-only meaning, broken dark mode |
| 7 | `system_consistency` | components match the design system / accepted references; the same thing looks and behaves the same everywhere | minor style drift from references | one-off components duplicating existing ones; inconsistent patterns |
| 8 | `microcopy` | plain user language; actions named by outcome ("Save changes"); consistent names across a flow ("Publish" → "Published"); errors say what happened and how to recover without apologising; empty states invite action | some generic labels ("Submit", "OK") or vague errors | internal jargon, misleading labels, missing error or empty text |
| 9 | `states_coverage` | every required state (empty, loading, error, overflow, permission-denied, offline) designed and captured | one required state generic or unstyled | required states missing, blank or crashing |
| 10 | `platform_conventions` | iOS: HIG navigation, system controls, Dynamic Type scaling, safe areas. Web: responsive at all breakpoints, standard link/button semantics, reduced motion respected | small deviations with no usability cost | fights the platform (custom back behaviour, fixed font sizes, safe-area overlap, div-buttons) |
| 11 | `originality` (taste, tournament only) | deliberate choices specific to the brief; no AI-default tell unless the brief asked for it | competent but template-like | unmodified library defaults / generic AI look |

Brief-specific notes per criterion (optional, concrete only): <e.g. "hierarchy: the outfit canvas outranks the item
tray on every device">

## Thresholds (G2 craft gate)

| Class | Gate A | Per-criterion floor | Mean of criteria 1–10 | Findings |
|---|---|---|---|---|
| **S / M** | pass | every criterion ≥ 2 | ≥ 3.0 | zero CONFIRMED blocker/major |
| **L / XL and any consumer-facing UI** | pass | `hierarchy`, `layout_integrity`, `color_contrast`, `states_coverage` ≥ 3; all others ≥ 2 | ≥ 3.3 | zero CONFIRMED blocker/major |

- Criteria that cannot apply (e.g. `states_coverage` on a static legal page) are marked `n/a` with a reason and excluded
  from the mean; at most 2 per screen.
- Shape switches: BUG → rubric skipped (defect-gone + nearby-regression check only); MIG admin UI → criteria 2, 7, 8 only.
- Thresholds are tunable per mission by D-entry, never lowered mid-milestone for a failing screen.

## AI-default tells checklist (criterion 11 and G2 step 7)

Report each tell that is present and not requested by the brief as a `generic-design` finding: **minor** on internal
tools, **major** on marketing sites and greenfield hero screens.

- [ ] Cream/off-white background (near #F4F1EA) + serif display type + terracotta accent
- [ ] Near-black background with a single acid/neon accent colour
- [ ] Broadsheet look: hairline rules everywhere, zero radius
- [ ] "SaaS card kit": identical rounded cards, the same soft `rgba(0,0,0,.1)` shadow, gradient washes
- [ ] ALL-CAPS eyebrow labels above every heading
- [ ] Middle-dot meta strings ("A · B · C") as decoration
- [ ] "WORD — fragment" labels
- [ ] Monospace data labels without a data context
- [ ] "→" appended to button labels
- [ ] Numbered 01 / 02 / 03 markers on non-sequential content
- [ ] Fade-and-slide-up animation on every section
- [ ] Generic stock hero (gradient blob, laptop mockup) unrelated to the product
- <brief-specific tell to avoid, e.g. "fashion app: grey placeholder silhouettes instead of real garment photos">

## Tournament protocol (taste decisions: direction, hero treatment, icon set, best iteration)

1. **Candidates:** 2–4 directions or iterations, each rendered on the **same** 2–3 key screens × the same variants
   (at least one hero screen and one dense screen). Never ≥ 3 candidates in one judging prompt.
2. **Pairs:** all pairs (≤ 6). For each pair run the judge (`mission-critic`; XL brand-defining:
   `mission-strategist-review`) **twice**, A/B order swapped, fresh context each time.
3. **Judge input:** brief, screen specs, the `hierarchy` and `originality` anchors above, AI-default tells, and two
   contact sheets labelled only "Left" and "Right" (no maker names, no iteration numbers, no scores).
4. **Judge output:** `{"winner": "left|right|tie", "reasons": ["<3 element-level reasons>"], "risks_of_winner": ["..."]}`.
5. **Aggregation:** a pair counts as a win only if both orders pick the same candidate; disagreement = tie.
6. **Winner:** most wins. A tie at the top, or a direction decision on GRN/WEB at L/XL, goes to the human batch
   (`templates/human-review.md`, item type `direction`) with the two finalists.
7. **Record** in `.mission/verification/screens/<run-id>/tournament.md`:

| Pair | Order 1 (Left/Right → winner) | Order 2 (swapped → winner) | Result | Reasons (short) |
|---|---|---|---|---|
| <C1 vs C2> | <C1/C2 → C1> | <C2/C1 → C1> | <C1 win, or tie> | <…> |

Final ranking: <C1 (3 wins), C3 (1), C2 (0)> · Promoted to accepted set: <candidate or "pending human batch"> ·
Human decision reference: <human-review/<M>/results.md item n | n/a> · D-entry: <D-NNN>
