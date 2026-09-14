# Positioning research · <product> · <Q-NN>

<!-- Template: skills/mission/templates/positioning.md → body of .mission/research/Q-NN.md after the question card
     (references/research.md RS-30..34, shape WEB/RSR). Fill sections IN ORDER: positioning (1–5) before messaging (6),
     sitemap (7) and copy. Positioning is not messaging; a single fill-in positioning statement is not research.
     Agents: angle lanes `mission-worker` (competitors and alternatives · category vocabulary · audience pains and jobs ·
     pricing norms · differentiators checked against the repo), each from templates/researcher.md; a skeptic lane that
     tries to refute the top claims; synthesis `mission-builder` (XL: `mission-strategist`); claim register fact-check
     `mission-critic` (templates/fact-checker.md). Never a Fable-tier page reader.
     Fact classes on every row: [SRC] registered source S-NNN · [OWN] owner-confirmed (who, date) · [HYP] hypothesis to
     validate · [INF] inference. [HYP]/[INF] are shown to the owner as such, never as findings.
     Word cap: ≤1,500 words for this note; bulky competitor evidence tables stay in .mission/lanes/<lane-id>/ and are
     linked. Outputs feed design/WEBSITE-BRIEF.md §1–4 by pointer. At Spec, § 8 rows become CLAIM-NNN requirements
     (kind content-claim) in requirements.yaml; § 8 is then replaced by a pointer so the registry is the single source. -->

## 0. Inputs

- Read: <README · docs/ · SPEC.md · CHARTER.md · owner interview notes · analytics export (if provided)> · access date <YYYY-MM-DD>
- Angle lanes: <lane-a competitors · lane-b category vocabulary · lane-c audience pains · lane-d pricing norms · lane-e differentiators vs repo> · skeptic: <lane-f>
- Owner inputs received: <audience priority · team details (consent) · customer names (permission) · metrics · roadmap> | <pending: BLOCKED-HUMAN item in STATUS>
- Sensitivity: <public-safe queries only | product name may be searched (already public)>

## 1. Competitive alternatives (what best-fit customers would do if this product did not exist)

Rule: ≤8 named alternatives + "do nothing / spreadsheet / in-house build / hire someone". Facts about a competitor come
from its own site, docs or pricing page (P1 for what it offers or charges, access-dated). No competitor weakness without
a source or a reproducible observation.

| Alt | Alternative | Who uses it | What it is good at | Where it falls short for our best-fit customers | Pricing (access-dated) | Sources | Class |
|---|---|---|---|---|---|---|---|
| ALT-1 | <do nothing / spreadsheet> | <…> | <…> | <…> | <free> | <S-NNN · owner interview> | <[SRC] · [HYP]> |
| ALT-2 | <competitor> | <…> | <…> | <…> | <plan: price, date> | <S-NNN §"Pricing"> | <[SRC]> |

## 2. Unique attributes (capabilities we have that alternatives lack)

Every attribute is checked against the repo: a path, a test or a runnable demo. No proof → it is a roadmap item, not an
attribute.

| Attr | Attribute | Proof (repo path · test ID · demo command · benchmark Q-NN/C-n) | Alternatives lacking it (source) | Class |
|---|---|---|---|---|
| ATTR-1 | <…> | <src/sync/offline.ts · @req:SYNC-004 test> | <ALT-2 per S-NNN §"Features"> | <[SRC] · [OWN]> |

## 3. Value (what each attribute enables for the customer)

| Attr | → Value (customer outcome, not a feature) | Evidence the customer cares (interview · issue · forum thread · owner data) | Class |
|---|---|---|---|
| ATTR-1 | <…> | <S-NNN "<≤25-word quote>"> | <[SRC] · [HYP]> |

## 4. Best-fit customers, audience and jobs-to-be-done

| Segment | Characteristics that make them care a lot about the value | Job (situation → motivation → desired outcome) | Current alternative | Evidence | Class |
|---|---|---|---|---|---|
| SEG-1 | <…> | <when <situation>, I want to <motivation>, so I can <outcome>> | <ALT-n> | <S-NNN · owner> | <[HYP] until owner confirms> |

Audience priority for the site: <SEG-1 primary · SEG-2 secondary> (<[OWN] owner decision date | A-NN default>)

## 5. Market category (the context that makes the value obvious)

Compare ≥2 candidate categories. The category sets buyer assumptions about competitors, features, buyer and price.

| Candidate category | Assumptions it triggers (competitors, features, buyer, price) | TRUE for us | FALSE for us | Search/category vocabulary in use (S-NNN) | Verdict |
|---|---|---|---|---|---|
| <…> | <…> | <…> | <…> | <S-NNN> | <chosen · rejected: reason> |
| <…> | <…> | <…> | <…> | <S-NNN> | <…> |

Chosen category: <…> · Class: <[HYP] until owner confirms | [OWN] <who, date>> · Decision: <D-NNN>

## 6. Message hierarchy (derived from 1–5, never invented independently)

Each message needs a proof point, and each proof point needs a claim ID bound to a source or owner confirmation.
Anything else becomes `[NEEDS-EVIDENCE]` or is cut.

| Level | Message (≤12 words headline · ≤25 words otherwise) | Derived from | Proof point | Claim | Evidence (S-NNN · OWN · RUN) |
|---|---|---|---|---|---|
| Headline | <…> | <ATTR-1 → value · SEG-1 job> | <…> | <CLAIM-001> | <S-NNN · test @req:…> |
| Pillar 1 | <…> | <…> | <…> | <CLAIM-002> | <…> |
| Pillar 2 | <…> | <…> | <…> | <CLAIM-003> | <…> |
| Pillar 3 | <…> | <…> | <…> | <CLAIM-004> | <…> |
| Objection → answer | <objection from § 1 shortfalls → answer> | <ALT-n> | <…> | <CLAIM-005> | <…> |

Voice and messaging guide frozen at: <YYYY-MM-DD · commit sha> (content lanes start only after this, obligation PC-3).

## 7. Sitemap and content plan feed (→ design/WEBSITE-BRIEF.md §5–7)

| Page | Primary audience / job | Search intent (query theme from § 1 and § 4) | Key message | Proof required | Evidence status |
|---|---|---|---|---|---|
| / (home) | <SEG-1 · job> | <…> | <headline + pillars> | <CLAIM-001..004> | <draft> |
| /product or /features | <…> | <…> | <…> | <ATTR proofs> | <…> |
| /goals or /about | <…> | <brand query> | <mission, goals> | <[OWN] only> | <needs owner data> |
| /team | <…> | <brand query> | <people> | <[OWN] names, roles, photos with consent> | <BLOCKED-HUMAN until received> |
| /blog | <…> | <job-related informational queries> | <…> | <per-post S-NNN for every statistic> | <plan> |
| /docs | <developers> | <how-to queries> | <—> | <repo-derived; samples executable> | <plan> |

SEO per page: unique title and meta description · one primary intent · internal links · sitemap.xml · robots.txt ·
byline dates on posts · structured data only for true facts.

## 8. Claim register (every factual sentence that will be published)

| Claim | Page / section | Exact sentence | Class (§ 9) | Evidence (Q-NN/C-n · S-NNN · RUN test ID · OWN ref) | Fact-check verdict + date | Approved by | Revalidate by | Status |
|---|---|---|---|---|---|---|---|---|
| CLAIM-001 | <home / hero> | <"…"> | <capability> | <@req:SYNC-004 at <sha>> | <CONFIRMED <YYYY-MM-DD>> | <mission-critic> | <YYYY-MM-DD> | <ready · NEEDS-EVIDENCE · cut> |
| CLAIM-002 | <home / pillar 2> | <"…"> | <competitor comparison> | <S-NNN §"Pricing" accessed <date>> | <…> | <mission-critic + owner> | <≤7 days before publish> | <…> |

## 9. Evidence standard for public claims (release gate for site, docs, blog, store listing, README, launch post)

| Class | Examples | Minimum evidence | Who may approve |
|---|---|---|---|
| Product capability | "works offline", "exports to CSV" | test or RUN demo at the release commit | `mission-critic` + test ID |
| Performance / quantitative | "2× faster", "p95 under 100 ms", "saves 5 hours a week" | RUN benchmark with published method, or owner data with method; comparisons name baseline and date | `mission-critic` + owner |
| Market / third-party statistic | "70% of teams …" | original P1 study or filing, registered with access date; the sentence keeps the source's exact scope | `mission-critic` |
| Competitor comparison | "unlike X, we …" | competitor's own P1 docs/pricing accessed ≤7 days before publish | `mission-critic` + owner |
| Customer names, logos, case studies | "used by <company>" | written permission reference [OWN] | owner only |
| Testimonials, reviews, ratings | quotes, stars | real person, real experience, permission on file [OWN]; never generated, reworded in meaning, or incentivized without disclosure | owner only |
| Team / company facts | bios, headcount, founding date, investors, awards, certifications, compliance | owner-confirmed [OWN]; certifications cite the certificate or report; photos need consent | owner only |
| Security / privacy posture | "end-to-end encrypted", "we never store …" | code reference or RUN + owner confirmation | security lens reviewer + owner |
| Pricing / availability | plans, regions, launch dates | owner-confirmed; matches billing configuration | owner |

Hard rules:
1. Zero fabrication. No invented statistics, user counts, "trusted by" numbers, testimonials, reviews, ratings, customer
   logos, press mentions, team members, bios, headshots, investors, awards or certifications: not as placeholders, not
   "for layout". The US FTC can seek civil penalties for fake reviews and testimonials; other jurisdictions have their
   own rules. Regulated claims (health, finance, legal) get a human legal review checkpoint.
2. Missing evidence ⇒ a visible marker in the copy: `[NEEDS-EVIDENCE: <class> · <what is needed> · <owner>]`. Layout
   placeholders are obviously non-real (lorem ipsum, grey boxes), never plausible names or numbers.
3. Hedges do not launder claims: "up to", "industry-leading", "trusted by thousands" need the same evidence as the
   unhedged claim, or get cut. Aspirations are phrased as goals ("we aim to …").
4. Competitor and third-party facts are revalidated ≤7 days before publish; stale ones are removed, not left in.
5. Docs facts come from the repo (code references, executable samples), never from positioning research.
6. Every blog statistic has a registered S-NNN; no "industry reports show" without a URL.

## 10. `[NEEDS-EVIDENCE]` launch gate

Publish (H-APPROVE) is blocked until all hold, each with evidence in VERIFICATION or the release checklist:

- `grep -R -n "NEEDS-EVIDENCE" <site-src> <content-dir>` → no output (exit 1).
- Every quantitative, comparative or factual sentence on the site maps to a CLAIM-NNN row with status `ready`.
- Every CLAIM-NNN has fact-check CONFIRMED (dated) or an [OWN] confirmation line (who, date); none is UNVERIFIED,
  NEEDS-VERSION-CHECK, `UNVERIFIED-OFFLINE` or flagged `FABRICATION-RISK`.
- Competitor and third-party claims accessed ≤7 days before the publish date.
- Team page content has recorded consent, or the page is not published.

## 11. Owner validation queue (batched once; autonomous mode logs defaults as A-NN)

| Item | Class now | Question for the owner | Default if unanswered | Blocks |
|---|---|---|---|---|
| <chosen category> | [HYP] | <Is "<category>" how your buyers describe this?> | <A-NN: use it on preview only> | <home headline> |
| <team details> | missing | <Names, roles, photos with consent?> | <team page BLOCKED-HUMAN> | <team page> |
| <customer names / logos> | missing | <Which customers may be named, with permission reference?> | <no names published> | <social proof section> |
