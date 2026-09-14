# Specification · <mission name>

<!-- Template: skills/mission/templates/SPEC.md → .mission/SPEC.md (M+). M: ≤2 pages, flat REQ-NNN ids, sections 0, 3,
     4, 6, 9, 10. L/XL: all sections, domain ids. Bug missions use BUGFIX-SPEC.md instead of sections 3–4. -->

Charter: CHARTER.md (class <M|L|XL>) · Registry: requirements.yaml · Status: draft | reviewed | approved · Version: <n>

## 0. How to read this document

The key words MUST, MUST NOT, SHALL, SHALL NOT, SHOULD, SHOULD NOT and MAY are interpreted as in BCP 14 (RFC 2119,
RFC 8174) when, and only when, they appear in all capitals. Bold IDs are stable test anchors: never renumbered, never
reused; removed IDs stay in requirements.yaml with `status: withdrawn`. Every test MUST cite at least one ID as
`@req:<ID>`. Any independently testable behaviour found in prose MUST be split into its own ID before coding.

## 1. Outcomes (from CHARTER §6; do not diverge)

- **OUT-001.** <one sentence>. Oracle: <scenario | live>.

## 2. Glossary (every term used normatively)

| Term | Definition | Not to be confused with |
|---|---|---|
| <Outfit> | <a named set of ≥2 wardrobe items for one date> | <Look (a saved photo)> |

## 3. User journeys (prioritised; each independently testable and demonstrable)

### J1 — <title> (P1)

Why P1: <…> · Independent test: "Can be fully tested by <action> and delivers <value>."

1. Given <state>, When <action>, Then <observable outcome> → covers <UX-001, API-003>
2. Given <state>, When <failure action>, Then <observable failure handling> → covers <API-001>

### J2 — <title> (P2)

Why P2: <…> · Independent test: <…>

## 4. Requirements by domain

### 4.1 <DOMAIN> — <name> (owner: <component>)

- **<DOM>-001.** When <trigger>, the <system> SHALL <response>. · Oracle: <kind> · Priority: <P1>
- **<DOM>-002.** While <state>, the <system> SHALL <response>. · Oracle: <kind> · Priority: <P2>
- **<DOM>-003.** If <unwanted condition at a boundary>, then the <system> SHALL <response>. · Oracle: <kind> · Fixture: <name>
- **<DOM>-004.** Where <optional feature is included>, the <system> SHALL <response>. · Oracle: <kind>
- **<DOM>-005.** The <system> SHALL <always-true property>. · Oracle: <property>

[NEEDS CLARIFICATION: <question> · owner: <human | orchestrator> · default if unanswered: <x> · blocks: <ID or none>]

<!-- Oracle kinds: unit | property | contract | integration | scenario | e2e | visual | a11y | live | human | review.
     Banned without a threshold or rubric reference: fast, intuitive, robust, clean, simple, modern, seamless, scalable,
     user-friendly, large, many, etc. -->

## 5. Non-functional requirements (each with a threshold and a method)

| ID | Quality | Threshold | Load / conditions | Oracle |
|---|---|---|---|---|
| <PERF-001> | <p95 feed load> | <≤800 ms> | <1,000 items, 4G profile> | <integration + trace> |
| <PRIV-001> | <photo deletion> | <object and metadata gone before 204> | <any user> | <integration> |
| <A11Y-001> | <accessibility level> | <WCAG 2.2 AA / HIG Dynamic Type AX5> | <all P1 screens> | <a11y + visual> |

## 6. Failure modes & degradation (one row per external boundary)

| Boundary (network, provider, storage, user input, permission) | Failure | Required behaviour (ID) | Injected by (fixture) |
|---|---|---|---|
| <upload endpoint (user input)> | <file >10 MB> | <API-001> | <upload_11mb_jpeg> |
| <R2 (storage)> | <write timeout> | <API-0NN> | <r2_timeout_stub> |

## 7. Data & state (summary; details in design/BACKEND.md)

| Entity | Owner (exactly one) | Lifecycle states | Illegal transitions rejected by (ID) |
|---|---|---|---|
| <Photo> | <photos-api> | <uploading → stored → deleted> | <DATA-0NN> |

## 8. Out of scope (links to CHARTER non-goals)

- <NG1 → no requirement may add social sharing>

## 9. Acceptance

- Automated: every ID with status implemented/verified has an oracle that exists and cites it;
  `python3 .mission/bin/validate-registry.py --registry .mission/requirements.yaml --tests <dirs> --spec .mission/SPEC.md` exits 0.
- acceptance.json: every AC-NNN cites ≥1 ID; starts `passes: false`; only verifiers flip.
- Live checks: <OUT-002 → live check name>, PENDING-LIVE until actually run.
- Grader condition for an implementation slice: "<IDs> hold, proven by `<command>` exiting 0 with <evidence line>; no
  file under <frozen paths> modified; stop after <n> turns." (Gates come from verifiers and check.sh, never `/goal`.)

## 10. Change log (spec-anchored: behaviour changes update this file and requirements.yaml in the same change set)

| Version | Date | Change | IDs touched | Reason (incident / refuted A-NN / D-NNN / ADR-NNN) |
|---|---|---|---|---|
| 1 | <YYYY-MM-DD> | Initial | <all> | Intake |
