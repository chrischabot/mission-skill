# Shape: publish

Read this at intake when the goal wants a website, landing page, documentation site, blog, or other
designed content deployed, and again at the start of every phase. It decides the phase order, how
research becomes positioning, claims, a site map, and page briefs before anything is scaffolded, who
drafts and who checks, which gates run against which deployment, where deployment stops, and what
Done means. A site is a machine for making claims, so this shape's characteristic failure is a page
that renders well and passes every layout gate while its content is invented; the claims ledger and
the placeholder checks exist to stop that.

## When it applies

The deliverable is designed content that people will read at a URL. When the goal asks for research
as well as the site ("research our market position and build a site about it"), the research is a
deliverable: run it first as a `report` sub-goal, delivered to the path the goal names or
`docs/<slug>.md`, and cite its slugs in the content plan. Research that only feeds the site stays in
this shape's research phase, gated like a report. When a site already exists and is being replaced,
the old URLs are consumers: capture the old sitemap and a crawl first, and prove every old URL
resolves to the right new page or a permanent redirect. A contact form, signup, or search backend
attaches `api`, and stored addresses attach `auth`.

**Deployment boundary.** Deploy to a preview on the owner's own hosting in every publish run. Promote
to production when the goal asks for a launch or for the site to be live, or when a production target
for this site already exists; otherwise a production deploy is the owner's publishing act. Settle
which at intake and write it into GOAL.md's `live means:`. When production is out of scope, create the
site's rows with `live: n` and the reason "production promotion not requested; the promote command is
in the report"; their proof tops out at Local Proof on the preview, and REPORT.md carries the one
promote command. A site reaches Live Proof only when production serves the tested build. When the
hosting account is not authenticated, deploy nothing, name the login on an `account:` or `credentials:` Blocked on line, and keep rows
at Local Proof. Never post announcements, submit to directories, or publish anywhere else on the
owner's behalf.

## Phases

| Phase | Entry | Work and agent | Artifact | Exit check (checker) |
|---|---|---|---|---|
| intake | the goal | classify; record gate thresholds; set `live means:` to the production URL or "preview only: production promotion not requested"; a requested research deliverable becomes a `report` sub-goal (orchestrator) | GOAL.md | committed before other work (orchestrator) |
| research | GOAL.md committed | competitor, audience, and disconfirming lanes; the project's own facts from its code and docs; team facts only from supplied material (drive:researcher; reconciliation with `model: "opus"`) | RESEARCH.md | every fact the site will state has a slug or is marked opinion; each pillar faced a disconfirming search (orchestrator; drive:grader re-opens cited sources) |
| content-plan | research exit | positioning, site map, page briefs; claims ledger (drive:architect) | `.drive/content-plan/` (`positioning.md`, `sitemap.yaml`, `briefs/<page>.md`); the claims ledger in the site's content directory | every pillar and proof point cites a claim id; every claim has kind, evidence, verified date, expiry; no page exists for a missing fact (drive:grader) |
| design | content-plan pass | design direction and contract: named colours, type pairing, layout concept, one element grounded in the subject, and the default look it rejects (drive:designer) | `design/DESIGN.md`, `design/tokens.json`, `design/screens.yaml` | every site-map page has a screen entry; no templated-default tells (drive:architect in fresh context at S to M; drive:auditor at L to XL) |
| build | design pass | scaffold now and not earlier, in the stack the owner's repositories already use; layouts and page templates from the briefs, tokens, docs structure, code samples as tested files, the claim marker, and the gates wired as scripts (drive:implementer) | site code; gate scripts | build succeeds; every gate runs (drive:verifier) |
| draft | build exit | copy per page into the content files from its brief, positioning, and the claims ledger, under the prose skill the brief names, which story-maps narrative posts before drafting; docs under `google-dev-docs-style`; an evidence marker wherever a needed fact has no verified claim; a revision pass by a different writer (drive:writer) | content files | claims lint green; every factual sentence traces to a claim id, is opinion, or carries an evidence marker (drive:grader) |
| design-qa | draft exit | all gates on the build output; the screenshot matrix of the local build judged against the design contract (drive:ui-reviewer; drive:verifier) | `.drive/proofs/<key>/r<n>/shots/`, `findings.json`, `verdict.json` | no blocking finding; thresholds met on the build output (drive:ui-reviewer; drive:verifier) |
| deploy | design-qa pass | preview deploy through the platform's own tools with a config diff first and the previous version id appended to DECISIONS.md as the undo (orchestrator); preview gates, the screenshot matrix, the claims audit, and a docs smoke test by a fresh agent with no repository access, all against the preview (drive:ui-reviewer; drive:verifier) | DECISIONS.md; deploy output; `.drive/proofs/<key>/r<n>/` | the evidence-marker grep printed nothing before the upload; the preview serves this commit's build stamp; preview gates green; claims audit clean; docs smoke test passed; rows at Local Proof (drive:verifier) |
| live-proof | deploy exit, only when production is in scope | promote the tested version (orchestrator); every gate and the screenshot matrix again against the production URL (drive:ui-reviewer; drive:verifier) | `proof.json` with `environment: live` and `target` the production URL | production serves the tested stamp; gates green there; `shim_differences` recorded (drive:verifier) |
| retro, report | live-proof exit, deploy exit when production is out of scope, or the run stopped | lessons; final audit by drive:auditor at L and above, otherwise a fresh drive:verifier running the same checklist; REPORT.md, with the promote command when production was out of scope (orchestrator) | `.drive/reviews/<date>-final-audit.json`, REPORT.md | `drive.py lint --final` passes (orchestrator) |

## The content plan

`.drive/content-plan/` holds three parts, in the formats `references/domains/web.md` section 4 gives.
**Positioning** (`positioning.md`): the primary and secondary audience and what each is trying to do;
the category buyers already search for; three or four messaging pillars, each with the claim ids that
prove it; competitor claims the site must not echo, quoted with source and date; and words the site
will not use without a measured claim ("fastest", "only", "leading"). **Site map** (`sitemap.yaml`):
every URL with its single job, primary action, pillars carried, and the claim ids it may use; a page
whose facts are missing is left out rather than filled with brackets (no pricing page without supplied
prices). **Page briefs** (`briefs/<page>.md`): the reader's question on arrival and the one-sentence
answer, sections in order with the claim ids each may use, the primary action, what is forbidden on
the page, and tone. SPEC.md holds only the site's behavioural claims (forms, search, feeds) when it
has any.

The claims ledger lives with the site so the build can check it. Each claim has an id, text, kind,
evidence, verified date, and expiry. `measured` needs a file with the number and how it was measured;
`demonstrated` needs a URL or test name; `quoted` needs a named source; `descriptive` is something the
code plainly does and the verifier checks it against the repository; `roadmap` appears only on a
roadmap or changelog page, phrased as future. Every sentence on a marketing page that contains a
number, a multiplier, a comparative or superlative, a compliance term, or a customer name sits inside
a claim marker whose id exists, is verified, and has not expired, or the build fails. Team names,
roles, and photos come only from supplied material or the repository; never generate a biography or
a portrait, and a team of one is a page with one person.

**Missing evidence is marked, then resolved before any deploy.** When a sentence needs a fact the
ledger cannot support, the writer puts a visible marker in its place instead of softening or
inventing it: `[NEEDS-EVIDENCE: <kind> · <what would prove it> · <who holds it>]`, where kind is
measured, demonstrated, quoted, comparison, customer, or team. The marker makes the gap countable for
the grader and impossible to miss in review. It is never shipped: `grep -rn "NEEDS-EVIDENCE"` over the
content directory and the build output is a blocking objective check at design-qa, deploy (preview
included), and live-proof, and it must print nothing. Before deploy each marker becomes one of two
things: a verified ledger claim the researcher found, or a removed sentence, section, or page with
the narrowing in DECISIONS.md and the missing evidence named in REPORT.md's "Needed from you" so the
owner can restore it later. Nothing waits for the owner to answer. A requested section such as the
team page with no supplied material is removed the same way.

## Gates

Run every gate on the build output at design-qa, on the preview at deploy, and on production at
live-proof when production is in scope. Only the production run counts as Live Proof. Defaults apply
unless GOAL.md set others at intake.

| Gate | Target |
|---|---|
| Lighthouse, mobile and desktop, median of three runs | performance ≥ 0.95, accessibility 1.0, best practices ≥ 0.95, SEO 1.0; LCP ≤ 2.5 s, CLS ≤ 0.1, TBT ≤ 200 ms |
| Accessibility engine at WCAG 2.2 AA, plus a keyboard pass | zero violations; visible focus; one `h1` per page; `lang` set; every image has an `alt` attribute |
| HTML validation; internal and external links including fragments | zero errors; zero broken links |
| Metadata, sitemap, robots, security headers | unique title and description, canonical, absolute social image that exists; sitemap and robots consistent; headers present |
| Placeholder grep | no lorem ipsum, bracketed TODO or TBD, "your company", or sample names on marketing paths |
| Evidence markers | `grep -rn "NEEDS-EVIDENCE"` over the content directory and the build output prints nothing; blocks every deploy, preview included |
| Claims lint, draft leakage, feeds, search | every marked claim verified and unexpired; no draft in output, feed, or sitemap; feed item count matches; search returns a known page |
| Screenshot matrix | widths 360, 768, 1280, 1600 in light and dark for every key page and the 404 page, with reduced motion and one post-Tab focus shot, all read by `drive:ui-reviewer` |

## Size

| Size | What runs |
|---|---|
| XS | a copy or link change on one page: inline, no `.drive/`; claims lint and link check; commit body with claim and evidence |
| S | one landing page: GOAL, STATE, STATUS, small RESEARCH.md; one brief; tokens from an existing design system when there is one; one UI review round |
| M | a multi-page site or a docs section: the full table |
| L | a research deliverable plus a site with blog and docs: the research as a `report` sub-goal, parallel drafting, auditor design review and final audit |
| XL | several sites or locales: gates per locale, Workflow fan-out for screenshot judging, a re-classification review by `drive:auditor` at each phase gate |

## Trait gates that commonly attach

`prose-content`, `ui`, `research-needed`, and `deploy-infra` attach to almost every publish run: the
writer and claim tracing, the design contract and matrix, the ledger, and a deploy with an undo.
`existing-code` means archaeology of the current site and the URL inventory. `api` and `auth` attach
only when forms, accounts, or stored addresses exist, adding contract tests, a security review, and
consent only if the site sets cookies. `public-api` docs need code samples that run as tests.
Analytics default to a cookieless option with no consent banner; `external-systems` records it.

## Verification centre, Done, parallelism

The centre of gravity is claim tracing plus screenshots and gates against the deployed site, judged
by agents that wrote none of it. The rigorous bound of 3 verifier rounds for publish applies to each
gated phase separately (content-plan, design, design-qa, deploy, live-proof), so a full run may spend
up to fifteen rounds in total, never more than three on one gate. Done means: when production is
in scope, live proof passed on the production URL with a matching build stamp; otherwise the preview
passed its gates, matrix, claims audit, and docs smoke test, the rows carry `live: n` with the reason,
and the promote command is in the report; the claims ledger is complete and unexpired; no placeholder,
invented person, generated biography, or sample post remains; STATUS carries `review:` pointing at
`.drive/reviews/<date>-final-audit.json`, from `drive:auditor` at L and above or a fresh
`drive:verifier` below L; and DECISIONS.md holds the deploy undo. Operational is claimed only when the
goal says the site must keep running: the production domain serves the tested stamp with a valid
certificate and analytics receiving.

Research lanes run in parallel. After the content plan, drafting runs in parallel with one writer per
page file; build packages (layouts, docs structure, blog) run in parallel once tokens exist; screenshot
judging runs as a read-only Workflow.

**Re-classify** when a form or account appears (add `api` and `auth`); when an existing site is
replaced (add the URL inventory and redirect parity); when research that only fed the site turns out
to need a standalone deliverable (a `report` sub-goal first); and when an app or dashboard enters scope
(a `build` or `feature` sub-goal).

## Excuses and rebuttals

| Excuse | Rebuttal |
|---|---|
| "Scaffold first; the content can fill in." | Without briefs the scaffold fills with placeholder copy, which then ships. |
| "Every site says this; it is harmless copy." | An unmeasured superlative or invented customer is a false claim under the owner's name; a sentence without a claim id is removed. |
| "The team page looks empty; add a few profiles." | People come only from supplied material; a team page with one real person is correct. |
| "Leave the evidence marker in; the owner can fill it after launch." | A marker is a false page waiting to ship; resolve it into a verified claim or remove the sentence, and name the missing evidence in the report. |
| "Lighthouse on the local build is close enough." | Fonts, headers, caching, and search indexes differ once deployed; only gates on the production URL count as Live Proof. |
| "One desktop screenshot looks right." | One screenshot proves one viewport in one scheme; the matrix is the minimum. |
| "The deploy printed a URL, so it is live." | Live means the production URL serves this commit's build stamp and passes the gates. |
| "The preview is public, so it counts as launched." | A preview is Local Proof; production is promoted only when the goal asks or a production target exists. |

## Red flags

- Pages or a scaffold exist before `.drive/content-plan/` has positioning, a site map, and briefs.
- A number, superlative, or customer name outside a claim marker.
- A `NEEDS-EVIDENCE` marker in anything uploaded, or a marker resolved by softening the sentence
  instead of finding the evidence or removing it.
- Lorem ipsum, bracketed placeholders, sample posts, or a pricing page without supplied prices.
- Generated portraits or biographies on any page.
- Fewer screenshot files than the matrix requires, or screenshots taken only of the local build.
- A competitor quote paraphrased into a stronger claim.
- A row at Live Proof whose `proof.json` target is a preview URL, or a production promotion the goal did not ask for.
- An announcement, directory submission, or social post made on the owner's behalf.
