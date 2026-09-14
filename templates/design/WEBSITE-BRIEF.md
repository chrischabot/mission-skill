# Content & site brief · <site>

<!-- Template: skills/mission/templates/design/WEBSITE-BRIEF.md → .mission/design/WEBSITE-BRIEF.md. Replaces BACKEND and
     most of FRONTEND for research + marketing website missions; page templates still get SCR-NNN screen specs.
     Every claim that reaches the site binds to a source (S-NNN in RESEARCH.md: URL + access date). -->

Links: CHARTER.md · SPEC.md (domains <CLAIM, SEO, A11Y>) · RESEARCH.md · Status: draft | reviewed | approved

## 1. Research questions

| Q | Question | Finding (one line) | Sources (S-NNN) | Confidence (low/medium/high) |
|---|---|---|---|---|
| Q-01 | <who competes for this audience?> | <…> | <S-003, S-007> | <medium> |

## 2. Audiences & jobs-to-be-done

| Audience | Job-to-be-done | What they need to believe | Top task on the site |
|---|---|---|---|
| <…> | <…> | <…> | <…> |

## 3. Positioning statement

For <audience> who <need>, <product> is a <category> that <key benefit>. Unlike <alternative>, it <differentiator>
(claim IDs: <CLAIM-00N>).

## 4. Messaging hierarchy

| Level | Message | Proof point | Claim ID | Source (S-NNN) |
|---|---|---|---|---|
| Primary | <…> | <…> | <CLAIM-001> | <S-002> |
| Supporting | <…> | <…> | <CLAIM-002> | <…> |

## 5. Sitemap (≤3 levels)

```text
/ (SCR-001 Home)
├── /about (SCR-002)
├── /blog (SCR-003 index) → /blog/<slug> (SCR-004 post)
└── /docs (SCR-005 index) → /docs/<section>/<page> (SCR-006 page)
```

Synthetic tree test (labelled synthetic): for the top 5 tasks the expected path is ≤3 clicks and labels are unambiguous.

| Task | Expected path | Clicks | Ambiguous labels |
|---|---|---|---|
| <find pricing> | <Home → Pricing> | <1> | <none> |

## 6. Page inventory

| Page | Template (SCR id) | Goal | Primary CTA | Content owner | Claims (IDs) |
|---|---|---|---|---|---|
| <Home> | <SCR-001> | <…> | <…> | <…> | <CLAIM-001, CLAIM-002> |

## 7. Blog and docs

- Blog: cadence <…> · categories <…> · post template SCR-004 · author/byline rules <…>
- Docs: IA <…> · versioning <…> · search <…> · contribution flow <…>

## 8. SEO, metadata, analytics, accessibility

- Per page: title pattern, meta description, canonical URL, Open Graph image
- Public URL structure: <…> (ADR-NNN: expensive to reverse)
- Analytics events: <EVT ids + trigger>
- Accessibility: WCAG 2.2 AA; tokens from design/tokens.md

## 9. STOP conditions (add to CHARTER §10)

- Unsourced comparative or market claim.
- Personal data or photos of team members without recorded consent.
- Publishing or DNS changes without a human checkpoint.
