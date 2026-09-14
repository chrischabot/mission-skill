# SCR-<NNN> · <Screen name>

<!-- Template: skills/mission/templates/design/SCREEN.md → .mission/design/screens/SCR-<NNN>.md. Every assertion is
     binding and checkable from a screenshot plus the view hierarchy / DOM. No prose adjectives ("clean", "modern")
     without a token or a rubric item. -->

Purpose: <one sentence> · Requirement IDs: <UX-0NN, A11Y-0NN> · Flows: <F1 step 2>
Reference: <taste anchor or wireframe path> · Viewports: <iPhone large (e.g. 393×852 pt), iPhone small (e.g. 375×667 pt) |
web 360 / 768 / 1280 px> (illustrative sizes; confirm against the device list in CHARTER constraints)

## Regions (top → bottom; layout assertions are binding)

| Region | Contents | Layout assertions |
|---|---|---|
| R1 Nav bar | <title "<text>", trailing action "Add"> | <title uses type.title; trailing action hit area ≥44×44 pt> |
| R2 Content | <grid of OutfitCard> | <2 columns at ≥375 pt; gutters = space.m; cards equal width ±1 pt> |
| R3 Primary action | <button "Create outfit"> | <bottom-most interactive element; full width within safe-area insets minus space.l; exactly one primary action on screen> |

## State matrix (each state gets a screenshot in verification)

| State | Trigger | What renders | Assertions |
|---|---|---|---|
| populated | <≥1 item> | <R2 grid> | <no truncation at default text size> |
| empty | <0 items> | <illustration + "No outfits yet" + R3> | <R3 visible without scrolling on the smallest viewport> |
| loading | <first fetch >300 ms> | <≤6 skeleton cards> | <no layout shift >1 card height when content arrives> |
| error | <fetch fails> | <inline message + "Retry"> | <message states cause + action; Retry is first focusable element> |
| partial / offline | <cached data, no network> | <banner "Offline — showing saved outfits"> | <banner does not cover R3> |
| permission denied | <photos permission off> | <explanation + "Open Settings"> | <no dead-end; action reachable> |
| largest text | <Dynamic Type AX5 / 200% zoom> | <single column> | <primary labels not truncated; no overlap> |
| dark mode | <system dark> | <same layout> | <token contrast pairs meet AA> |

<!-- SwiftUI screens MUST include light, dark and largest-text rows. Delete rows that genuinely cannot occur and say why. -->

## Interactions

| Element | Gesture / input | Result | Feedback |
|---|---|---|---|
| <OutfitCard> | <tap> | <push SCR-00N> | <highlight ≤ motion.fast> |
| <R3> | <tap while saving> | <ignored> | <button shows progress; not double-submittable> |

## Accessibility

Screen-reader order: <R1 title → R1 action → R2 cards (label "<name>, <n> items") → R3> · Traits: <…> ·
Reduced-motion variant: <…> · Colour-independent meaning: <…>

## Verification hooks (for references/frontend-verification.md)

- Screenshot names: `SCR-<NNN>-<state>-<viewport>.png` under `.mission/verification/screens/<run-id>/`
- Machine checks: target sizes, truncation, overlap, safe-area, token usage, region order
- Vision rubric items: one primary action; hierarchy matches region order; matches reference within <stated tolerance>
