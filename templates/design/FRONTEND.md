# Frontend design · <app or site> · Platform: <SwiftUI iOS | web | …>

<!-- Template: skills/mission/templates/design/FRONTEND.md → .mission/design/FRONTEND.md (L/XL; M when screens are
     added or changed). One screen spec per new or changed screen: design/screens/SCR-<NNN>.md (templates/design/SCREEN.md).
     Written so a verifier can check it from screenshots and the view hierarchy / DOM. -->

Links: CHARTER.md · SPEC.md (domains <UX, A11Y, …>) · Tokens: design/tokens.md → <repo token source, e.g.
`design/tokens.json` (DTCG 2025.10) or the existing theme file> · Taste anchors: <2–3 reference apps/sites> · Status: <…>

## 1. Platform conventions

- Apple platforms: HIG navigation pattern (<NavigationStack | TabView>), sheets vs push, SF Symbols, Light/Dark,
  Dynamic Type up to the largest accessibility size (text enlargeable ≥200%), Accessibility Inspector audit.
- Web: WCAG 2.2 AA (incl. SC 2.5.8 target size minimum), responsive breakpoints <360 / 768 / 1280>, full keyboard
  navigation, visible focus, reduced motion.
- Deviations from platform conventions: <none | deviation + reason + ADR-NNN>

## 2. Information architecture

```text
<SCR-001 Home>
├── <SCR-002 Wardrobe> → <SCR-003 Item detail>
└── <SCR-004 Plan outfit>
```

Max depth: <3> · Primary navigation: <tab bar with 3 destinations>

Synthetic tree test (labelled synthetic; no real users):

| Top task | Expected path | Clicks/taps | Ambiguous labels found |
|---|---|---|---|
| <Plan tomorrow's outfit> | <Home → Plan outfit> | <1> | <none> |

## 3. User flows (P1 journeys)

| Flow | Journey (SPEC J*) | Steps (screen → action → screen) | Success end state | Failure branches |
|---|---|---|---|---|
| F1 | J1 | <SCR-001 → tap Plan → SCR-004 → Save → SCR-001> | <outfit visible on Home> | <save fails → inline error, draft kept> |

## 4. Screen inventory

| Screen | Name | Purpose | Entry points | Requirement IDs | Spec file | New / changed / unchanged |
|---|---|---|---|---|---|---|
| SCR-001 | <Home> | <…> | <launch> | <UX-001> | design/screens/SCR-001.md | <new> |

## 5. Design tokens (roles, not raw values)

Single source: <path>. Components reference roles only. A new token on brownfield work needs an ADR-lite D-entry.

| Group | Roles | Notes |
|---|---|---|
| Colour | <bg.primary, text.primary, accent, danger> with contrast pairs | <AA 4.5:1 body, 3:1 large text / UI> |
| Type | <title, body, caption> mapped to platform text styles | <Dynamic Type styles on iOS> |
| Spacing | <space.xs … space.xl> | |
| Radius / elevation / motion | <radius.m, motion.fast …> | reduced-motion variants |

## 6. Components

| Component | Variants | States (default, pressed, disabled, loading, error) | Tokens used | Accessibility label / trait rules |
|---|---|---|---|---|
| <OutfitCard> | <compact, large> | <…> | <…> | <"<name>, <n> items"; button trait> |

## 7. Content & copy rules

Voice: <…> · Empty-state tone: <…> · Error pattern: what happened + what to do next · No placeholder lorem in shipped screens.

## 8. Accessibility requirements (IDs)

| ID | Requirement | Threshold | Oracle |
|---|---|---|---|
| <A11Y-001> | <text scaling> | <largest AX size / 200% zoom, no truncation of primary labels> | <visual + a11y> |
| <A11Y-002> | <targets> | <iOS ≥44×44 pt (practitioner figure; verify in HIG) · web WCAG 2.5.8 ≥24×24 CSS px or spacing> | <geometry probe> |
| <A11Y-003> | <screen-reader order and labels> | <order matches region order> | <a11y> |
| <A11Y-004> | <colour-independent meaning, reduced motion> | <…> | <visual> |

## 9. Performance budgets

First render <…> · interaction latency <…> · image sizes <…> · bundle / binary size <…>

## 10. Alternatives considered (≥2 layout or navigation options)

| Option | Decisive trade-off | Verdict |
|---|---|---|
| <tab bar> | <…> | chosen |
| <single stack with menu> | <…> | rejected because <…> |
