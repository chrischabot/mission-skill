# Web domain reference

Read this file when the goal includes a website (marketing, product, docs or blog) or a dashboard, report or
analytics view inside an existing web product. Part A decides how a site is researched, written, designed, built,
gated, deployed and proven; Part B decides how a dashboard is grounded in the existing product and how its numbers,
access and visuals are proven. Both parts end with what each rung of the ladder means. A site deployed to Cloudflare
also follows `references/domains/cloudflare.md`.

## Contents

Sections: 1. Activation and shapes · 2. Skills inside subagents · Part A, sites: 3. Order of work · 4. Content plan and the
claims ledger · 5. Stack decision · 6. Design direction · 7. Imagery · 8. Docs · 9. Blog · 10. Quality gates ·
11. Deploy and verify · 12. The ladder for sites · Part B, dashboards: 13. Archaeology · 14. Metrics registry ·
15. Independent-recomputation fixtures · 16. Charts · 17. States, volume and doubles · 18. Access tests ·
19. Visual verification · 20. The ladder for dashboards · Learned constraints

## 1. Activation and shapes

| Goal | Shape and traits | Read |
|---|---|---|
| A new site, landing page, docs site or blog | `publish`, traits `ui`, `prose-content`, `deploy-infra` | Part A |
| Replace an existing site | `move/migration`: the URL inventory (sitemap, crawl, inbound links, RSS, OAuth callbacks) is the consumer inventory; parity means every old URL resolves to its page or a 301 | Part A plus the migration shape |
| A site that accompanies an app | `publish` at reduced scope: landing, privacy and support pages, no blog, docs only for a public API; tokens derive from the app's design contract | Part A |
| A dashboard or analytics view in an existing product | `feature`, traits `existing-code` and `ui` confirmed; `data` and `auth` suspected until archaeology | Part B |
| Docs for a library, CLI or migrated service | `publish` or part of the owning shape | sections 8 and 10 |

On activation the orchestrator quotes the applicable Learned constraints (at most ten) under "Lessons that apply to
this task" in briefs for `drive:designer`, `drive:writer`, `drive:implementer`, `drive:ui-reviewer` and
`drive:verifier`.

## 2. Skills inside subagents

| Skill | Used by | For |
|---|---|---|
| `frontend-design` | `drive:designer` (preloaded); `drive:ui-reviewer` invokes it as its review lens | design direction, the rejected default, the tells |
| `writing` | `drive:writer`, invoked with the Skill tool under the name the brief gives (resolved at preflight; it may carry a plugin prefix) | marketing and blog prose |
| `google-dev-docs-style` | `drive:writer`, invoked with the Skill tool for every docs page, where it overrides `writing`; `drive:grader` applies its review checklist by path in the docs review | docs pages |
| `dataviz` | `drive:implementer` before the first line of chart code; `drive:ui-reviewer` for chart review | chart form, colour, palette validator |
| `web-design-guidelines` | `drive:ui-reviewer`, over `src/**` markup and styles | accessibility, focus, forms, motion, i18n findings with file and line |
| `imagegen` | `drive:implementer` in an imagery package, running the `imagegen` CLI through Bash (needs `OPENAI_API_KEY`) | illustrations, hero art, OG backgrounds |

When a skill is missing from the available-skills listing, or its CLI or key is absent, follow the inline rules in this
file for that area, record one line under STATE.md "Verified facts" (`<skill> unavailable on <date>; web.md inline
rules applied`), and tell the reviewer to grade against the same inline rules. Without `imagegen`, ship no generated
imagery: use type, CSS and SVG treatments from the design contract. Without `dataviz`, compute palette contrast with
the WCAG luminance formula instead of its validator. Never stall a run on a missing skill.

## Part A · Sites

## 3. Order of work

Follow the phase order in `references/shapes/publish.md`; this section says what each phase means for a site.

1. `research`: `drive:researcher` builds the market map in RESEARCH.md: the category as buyers name it, five to ten
   alternatives with what each claims on its own site (quoted, URL, checked date), price, audience, and the gaps no
   one claims. Never paraphrase a competitor's claim into something stronger than it said. Research the goal asks for
   as a deliverable runs first as a `report` sub-goal.
2. `content-plan`: `drive:architect` writes positioning, the claims ledger, the site map and one brief per page
   (section 4). Nothing is scaffolded before these exist, because without briefs the scaffold fills with placeholder copy.
3. `design`: `drive:designer` writes the design contract (section 6).
4. `build`: tokens and layout first (the architect marks this package hard, so the implementer runs on `opus`), then in
   parallel one package per page template built from its brief and the design contract, the docs structure, and
   `examples/` with their tests.
5. `draft`: `drive:writer` writes copy into the content files from the briefs; a second `drive:writer` in fresh context
   runs the revision pass. Copy that breaks a layout returns to that page's package as a design-qa finding.
6. `design-qa`: `gates:local` on `dist/` (section 10) and `drive:ui-reviewer` capture and verdict on the local build.
7. `deploy`: the preview upload (section 11), then preview gates, `drive:ui-reviewer` capture and verdict, the claims
   audit and the docs smoke test, all on the preview.
8. `live-proof`, only when production is in scope: promote the tested version and prove production serves it.
9. `retro`, `report`: lessons, the final audit and REPORT.md, which names the promote command when production was out
   of scope.

STATUS rows for a site: `every-claim-on-the-site-is-supported`, `the-site-passes-its-quality-gates`,
`[ui] every-key-page-matches-the-design-contract`, and `the-getting-started-tutorial-works-for-a-new-user` when there
are docs. When production is in scope they carry live `y` and the run adds `production-serves-the-verified-build`;
otherwise they carry live `n` with the reason "production promotion not requested; the promote command is in the report".

## 4. Content plan and the claims ledger

The plan lives in `.drive/content-plan/`: `positioning.md` (primary and secondary audience in their situation; the
category buyers already search for; three messaging pillars, each a sentence a buyer would say back, with the claim ids
that prove it; competitor claims we must not echo, quoted with URL; what we do not say), `sitemap.yaml` (every URL, its
single job, primary action, pillars carried, claim ids allowed) and `briefs/<page>.md`:

```markdown
# <path>
Job: a <audience> arrives from <source> and decides in ten seconds whether this is for them.
Question on arrival: "<question>". Answer in the hero: "<one sentence>".
Sections in order, each with the next question it answers and the claim ids it may use.
Primary action: <verb phrase>, repeated at <positions>. Forbidden here: <facts not supplied, roadmap claims>.
Tone: <two adjectives from positioning>. Register: <peer | practitioner | buyer>.
```

The claims ledger is `src/content/claims/claims.yaml`, loaded as a content collection so the build type-checks it:

```yaml
- id: latency-p50
  text: "Median response under 40 ms"
  kind: measured        # measured | demonstrated | quoted | descriptive | roadmap
  evidence: bench/2026-09-10-latency.md#p50
  verified: 2026-09-10
  expires: 2026-12-10
```

The rule: every sentence on a marketing or blog page that contains a number with a unit or percent, a multiplier, a
comparative or superlative (fastest, only, leading, best, most, zero, unlimited, guaranteed, trusted by,
enterprise-grade), a compliance or security term, or a customer or partner name sits inside
`<Claim id="...">...</Claim>`, which renders `<span data-claim="id">`, and the id exists, is verified and has not
expired. The build fails otherwise. `measured` needs a file with the number and the method; `demonstrated` a URL or test
name; `quoted` a named source and permission; `descriptive` behaviour the auditor can see in the repository; `roadmap`
appears only on roadmap or changelog pages, phrased as future. A missing fact is never filled with a bracketed
placeholder or a softened claim: the writer puts `[NEEDS-EVIDENCE: <kind> · <what would prove it> · <who holds it>]`
where the sentence would go, and before any deploy each marker becomes a verified ledger claim or a removed sentence,
section, or page, as `references/shapes/publish.md` describes. The writer marks sentences with existing ids and never
adds ledger entries.

`drive:verifier` audits claims on the preview with only the built pages, the ledger, positioning and the evidence
files. For each marked or unmarked sentence it returns supported, overstated, unsupported, expired or misplaced, what the
evidence actually says, and the minimal truthful rewrite. "Under 40 ms" is overstated by a p95 of 40 ms; a missing
evidence file is unsupported. Copy follows the `writing` fidelity rule: never improve a fact, invent a motive, or add an
implication because it makes better copy. Team pages use only supplied names, roles and photos; never generate a bio or
a portrait, and a team of one is a page with one person.

## 5. Stack decision

Default to Astro with content collections for marketing and blog, Starlight mounted under `/docs` in the same project,
built to static HTML and served as an assets-only Cloudflare Worker, because static asset requests are free, preview
URLs come from `wrangler versions upload`, content files carry schemas the build enforces, and Starlight supplies
search, sidebar, dark mode and a code component that imports tested files. Record the decision and the condition that
would flip it in DECISIONS.md.

| Condition | Choice |
|---|---|
| Default | Astro 7.3.2, `@astrojs/starlight` 0.42.0 (self-described beta), `@astrojs/sitemap`, `@astrojs/rss`, exact pins, upgrades only as a deliberate task |
| The site is the product application, or must share live components with a Next.js product | Next.js through `@opennextjs/cloudflare`; accept billed invocations and the 3 MiB Free / 10 MiB Paid compressed Worker limit |
| A single page with no blog or docs, now or planned | plain HTML and CSS |
| The repository already runs Hugo, Eleventy or Docusaurus well | keep it; the gates in section 10 still apply |
| A form or other server behaviour | a small Worker with `"main": "src/worker.ts"` and `"run_worker_first": ["/api/*"]`; everything else stays static |

Versions checked with `npm view` on 2026-09-14. Put marketing pages in `src/pages/` and `src/content/pages/`, posts in
`src/content/blog/`, docs in `src/content/docs/docs/**` so they render under `/docs/`, and never create
`src/content/docs/index.md`, which collides with the home page. Build and list `dist/` at scaffold time before any
content is written; if routes collide, fall back to two Astro projects behind one Worker and record the deviation. Use
`"not_found_handling": "404-page"`; single-page-application handling would mask broken links behind a 200. Set the
Content-Security-Policy through Astro's CSP API so inline script hashes are generated; put the other security headers
and `/_astro/*` immutable caching in `public/_headers`, which applies to static responses only.

## 6. Design direction

Before any CSS exists, `drive:designer` runs `frontend-design` and writes `design/DESIGN.md`, `design/tokens.json` and
`design/screens.yaml`. The direction section holds four to six named hex colours with light and dark values, a display
face and a body face, a layout concept in one sentence with an ASCII wireframe, and one signature element grounded in
the subject's own world. Then it names the generic default it would have produced for any site of this kind and shows
where the plan differs.

The plan and every primary page are checked against the templated-default tells in `references/ui-verification.md`
section 7, plus one this pack adds for sites: Inter, Roboto, Arial or Fraunces as the display face. Any tell on a
primary page is a Major finding unless the goal asked for that look.

When the goal asks for options, the designer writes two to four directions into `design/DESIGN.md`'s decision log,
chooses one by the rubric (grounding in the subject, distance from the defaults, legibility at phone width, contrast),
records the choice in DECISIONS.md, and the build proceeds on it.

Tokens: `src/styles/tokens.css` is generated from or checked against `tokens.json`. Colours are custom properties on
`:root` for light, redefined under `@media (prefers-color-scheme: dark)` and under `[data-theme="dark"]`, which is the
attribute Starlight's toggle sets. The file also holds a type scale, spacing scale, radii, and a motion token that is zero
under `prefers-reduced-motion: reduce`. `src/styles/starlight.css` maps the tokens onto Starlight's `--sl-*` variables
so docs and marketing read as one site. Fonts are self-hosted through the Astro Fonts API with a metric-similar
fallback so CLS stays under 0.1. Declare `@layer tokens, base, layout, components, utilities` once. A lint fails on any
hex literal or `font-family` outside `tokens.css`.

## 7. Imagery

An imagery package run by `drive:implementer` uses the `imagegen` CLI through Bash for illustrations, hero art,
diagram-style illustration and OG backgrounds. Never generate people, product screenshots (capture real ones), or
anyone else's logo. Draft with `-q low -n 3 -f webp`, choose by the criteria the design contract states, and regenerate the winner at `-q medium` (`high` for a hero), sized in multiples of 16 and at most
twice the largest rendered size. Save images to `design/images/` and import them from there. Every image has real `alt`
text or `alt=""` when decorative, explicit `width` and `height`, and `loading="lazy"` below the fold. A site should need
fewer than a dozen generated images; record spend in STATE.md. Exit code 3 means a moderation refusal: rephrase the
prompt, never retry it unchanged.

## 8. Docs

Organise docs in four sidebar groups with Starlight `autogenerate` per directory: Get started (one tutorial from nothing
to a working result, tested end to end), Guides (one task each, titled with a base-form verb), Reference (generated from
the source of truth where possible: OpenAPI, CLI `--help`, TypeDoc; hand-written reference cites the source file), and
Concepts (why it works this way, trade-offs, what it is not). `/docs/` is a short router to the tutorial, the three most
used guides and the reference index, with no hero. Every page has next and previous links, `lastUpdated: true`, and an
edit link when the repository is public.

The writer writes docs under `google-dev-docs-style`; the docs review by `drive:grader` applies that skill's review
checklist by path, so the maker never grades its own pages. When the skill is missing, apply its core rules inline: second person, imperative, present tense, sentence-case headings, no "please", no directional
language ("above", "below"), code font for code, placeholders in `UPPER_SNAKE_CASE`, and `example.com` or reserved
addresses in examples. Marketing and blog prose use `writing`; the two are never mixed.

Code samples are runnable files under `examples/` with their own test command, imported into pages so a sample that
stops compiling fails the build:

```mdx
import { Code } from '@astrojs/starlight/components';
import quickstart from '../../../../examples/quickstart/index.ts?raw';
<Code code={quickstart} lang="ts" title="index.ts" />
```

Shell transcripts come from a script in `examples/` that runs the documented commands in a clean temporary directory and
diffs output against the documented block, normalising timestamps and ids. Before docs count as done, `drive:verifier`
acts as a new user: given only the tutorial's preview URL and an empty directory from `mktemp -d`, it follows the
page literally without reading the repository and reports every command that failed, every output that differed, every
unstated prerequisite and every place it had to guess. Each item is a docs bug that blocks Done; the directory is deleted
afterwards. Pagefind builds the search index, which does not exist under `astro dev`, so search is verified on the
preview. Do not version docs until a second supported major version exists; until then use a changelog and "Added in"
asides.

## 9. Blog

```ts
const blog = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/blog' }),
  schema: ({ image }) => z.object({
    title: z.string().max(70), description: z.string().min(50).max(160),
    pubDate: z.coerce.date(), updatedDate: z.coerce.date().optional(),
    author: z.string(), tags: z.array(z.string()).default([]), draft: z.boolean().default(false),
    heroImage: image().optional(), heroAlt: z.string().optional(), claims: z.array(z.string()).default([]),
  }).refine(p => !p.heroImage || p.heroAlt, { message: 'heroImage needs heroAlt' }),
});
```

`author` must match a supplied team entry. Every listing, the RSS feed and the sitemap filter with
`getCollection('blog', p => import.meta.env.PROD ? !p.data.draft : true)`. RSS lives at `/rss.xml` through
`@astrojs/rss` with `site` set. Each post gets a 1200×630 OG image generated at build and referenced by absolute URL.
`robots.txt` points at `sitemap-index.xml`. Because the promoted version carries the same bytes as the preview, keep
previews out of search engines with `"run_worker_first": ["/robots.txt"]` and a handler that returns `Disallow: /` when
the host ends in `.workers.dev`, never with a preview-only build.

## 10. Quality gates

Run every gate as `npm run gates:local` on `dist/`, `npm run gates:preview -- <url>` against the preview, and, when
production is in scope, `npm run gates:production -- <url>`. Astro's sitemap lists production URLs, so preview gates
rewrite the host. Write each gate as a named test under `tests/gates/` or
`tests/e2e/` so STATUS can cite `test:` tokens, and give each a planted-failure test under `tests/gates/severe/`
(an unmarked superlative, a leftover evidence marker, a broken anchor, a draft post, a page without `og:image`, a stray
hex literal) that must go red;
those are the `severe:` evidence.

| Gate | Command | Target |
|---|---|---|
| Lighthouse, mobile and desktop | `npx @lhci/cli@0.15.1 autorun --config=lighthouserc.cjs` (`numberOfRuns: 3`, median; `settings.preset: "desktop"` for the second pass) | performance ≥ 0.95, accessibility 1.0, best practices ≥ 0.95, SEO 1.0; LCP ≤ 2500 ms, CLS ≤ 0.1, TBT ≤ 200 ms |
| Accessibility engine | `npx @axe-core/cli@4.13.0 <urls> --tags wcag2a,wcag2aa,wcag21aa,wcag22aa --exit --save <proof dir>/axe.json`, or `npx pa11y-ci@4.1.1 --sitemap <preview>/sitemap-0.xml --sitemap-find <prod host> --sitemap-replace <preview host>`; prefer `@axe-core/playwright` per page per scheme | zero violations |
| Accessibility proxies | Playwright: Tab through the header and assert a visible `:focus-visible` ring; `html[lang]`; one `h1` per page; every `img` has an `alt` attribute | all pass |
| HTML validity | `npx html-validate@11.15.0 "dist/**/*.html"` | zero errors |
| Internal links and fragments | `npx linkinator@8.1.0 ./dist --recurse --check-fragments` (or `lychee --offline --base dist --include-fragments "dist/**/*.html"`) | zero broken |
| External links | `npx linkinator@8.1.0 <preview> --recurse --skip '<noisy hosts>'` | zero broken; a rate-limited link is rechecked once before it counts |
| Meta and OG | `node tests/gates/meta-lint.mjs dist` | unique `<title>` ≤ 60 chars; description 50 to 160; absolute canonical; absolute `og:image` that exists; `twitter:card`; `build-hash` meta |
| Sitemap and robots | `node tests/gates/sitemap-check.mjs <url>` | every sitemap URL 200 `text/html`; every page but 404 listed; robots names the sitemap; preview robots disallows |
| Security headers | `curl -sI <url>/ <url>/docs/` | `content-security-policy`, `x-content-type-options`, `referrer-policy` present |
| Placeholders | `node tests/gates/placeholder-lint.mjs dist` (patterns below) | no match |
| Evidence markers | `grep -rn "NEEDS-EVIDENCE" src/content dist` | no output; blocks every deploy, preview included |
| Claims | `node tests/gates/claims-lint.mjs dist src/content/claims/claims.yaml` | every numeric or superlative sentence marked, every id verified and unexpired |
| Drafts, RSS, search | `drafts-check.mjs dist`; parse `<url>/rss.xml` and compare with published posts; Playwright types a known term on `/docs/` | no draft slug anywhere; item count equal and links 200; a result link appears |
| Palette (charts only) | `node <dataviz skill>/scripts/validate_palette.js "<hex,...>" --mode light` and `--mode dark --surface <hex>` | exit 0 |
| Interface guidelines | `web-design-guidelines` over `src/**/*.astro` and `src/styles/**` | no findings, or each accepted with a reason in DECISIONS.md |

The placeholder lint fails, case-insensitively, on "lorem ipsum", "welcome to our website", "your company", "acme
corp", "john doe", "jane doe", and bracketed `[TODO]`, `[TBD]`, `[PLACEHOLDER]` or `[YOUR ...]`; `example.com` is
allowed only under `/docs/`. Lab TBT stands in for INP. Analytics is the Cloudflare Web Analytics beacon, which sets no
cookies and does no fingerprinting, so the site ships no consent banner; if a stakeholder requires cookie-based
analytics, push back once, then add a consent step, a cookie policy page, and a test that the script does not load
before consent.

## 11. Deploy and verify

Every page carries `<meta name="build-hash" content="<short sha>">`. The run deploys directly; it never waits for Workers
Builds, and if the repository is connected its deploy command is `npx wrangler versions upload`.

```bash
npm ci && npm run build && npm run gates:local
SHA=$(git rev-parse --short HEAD)
npx wrangler versions upload --preview-alias drive-<slug> --message "$SHA" --tag "$SHA"    # note NEW version id
PREVIEW=https://drive-<slug>-<worker>.<subdomain>.workers.dev
npm run gates:preview -- "$PREVIEW"
# drive:ui-reviewer captures and judges; drive:verifier audits claims and runs the docs smoke test; all on $PREVIEW
# live-proof, only when production is in scope (references/shapes/publish.md); otherwise the next line is the report's promote command
npx wrangler versions deploy "$NEW@100%" --yes
curl -fsS https://<domain>/ | grep -q "<meta name=\"build-hash\" content=\"$SHA\">"
npm run gates:production -- https://<domain>     # links, meta, headers, sitemap, robots, search
```

Promoting the uploaded version means the bytes that passed the gates are the bytes that go live. The custom domain comes
from `routes: [{ "pattern": "www.example.com", "custom_domain": true }]` on a zone in the same account.

`drive:ui-reviewer` captures its own evidence into `.drive/proofs/<key>/r<n>/shots/`, checking the build hash before
looking at anything. The matrix is every key page plus the 404 page, at widths 360, 768, 1280 and 1600, in light and
dark, with reduced motion on, plus a post-Tab screenshot for focus and a 200% text-size pass at 360 for primary pages.
Objective checks run first (build hash, horizontal overflow, text under 16 px at phone width, contrast from tokens,
target sizes, console errors) and vision judges only what they cannot: hierarchy, fidelity to the direction, the tells,
whether dark mode looks designed, whether the 404 looks like the site. The reviewer records observations at the counts
`references/ui-verification.md` section 7 sets, returns `findings.json`, and the loop runs at most three rounds. During page
iteration a reduced matrix (360 dark, 1280 light) is enough; the full matrix runs at `design-qa` and after any CSS change.

## 12. The ladder for sites

| Rung | Means here |
|---|---|
| Scaffold | the project builds and `dist/` exists; nothing is claimed |
| Partial | pages exist with copy from briefs; some gates red |
| Local Proof | `gates:local` and the planted-failure tests green on `dist/`; ledger complete with every claim verified; design contract reviewed against the defaults; `examples/` tests green; drafts excluded; a `drive:ui-reviewer` verdict on local screenshots; a passing verifier verdict |
| Live Proof | preview gates green; full matrix graded with no blocking or major findings; claims audit clean; docs smoke test passed; then production serves the same build hash and `gates:production` is green. The `live:` bundle's `proof.json` has `environment: "live"` and `target` set to the production URL. Preview-only results stay at Local Proof; when production is out of scope the rows carry live `n` and the report names the promote command. |
| Operational | the custom domain answers with a valid certificate; the analytics beacon records a page view; the sitemap is submitted or fetched. Field Core Web Vitals are recorded in STATE.md by whichever later session finds them and never hold Done. |

## Part B · Dashboards in an existing product

## 13. Archaeology

Before any code, `drive:researcher` extends `.drive/how-it-works.md` with: framework and version from the lockfile;
router and layout shell; the data layer and the fetch wrapper everyone uses; the authorization model (roles, tenants,
where each check is enforced); the test stack (runner, fixtures, factories, request mocking); how existing screens show
loading, empty and error; feature flags; the charting library already in the bundle; and, for every table the dashboard
reads, the type and timezone of every timestamp column and the unit of every money column, each checked with
`SELECT MIN(col), MAX(col)` on a read-only replica or export; and the build identifier the product already exposes (a
version endpoint, a deploy id header, a hashed asset name), recorded in `design/screens.yaml`. Add a build stamp only
when none exists, with a DECISIONS.md entry naming it verification infrastructure and its undo. `drive:designer`
extracts the existing design system into `design/DESIGN.md` and `design/tokens.json`, lifting exact values from
component source and naming the closest existing screen as the exemplar; when the product already has a token source,
`tokens.json` cites that file for every value and a check compares the two, so the copy cannot drift. New UI extends
that vocabulary; the aesthetic-risk instruction in `frontend-design` is off.

## 14. Metrics registry

One module, `src/features/<dashboard>/metrics.ts` or the product's equivalent, is read by both the query builder and the
labels, so a metric that is not in the registry cannot render:

```ts
export const metrics = {
  activeUsers: {
    label: 'Active users', source: 'events.user_id', aggregate: 'distinct_count', where: "kind = 'session_start'",
    unit: 'count', timezone: 'account', bucket: 'day', window: '30d', refresh: '15m',
    empty: 'zero', partial: 'mark', fixture: 'tests/fixtures/metrics/active-users.sql',
  },
  revenue: {
    label: 'Revenue', source: 'orders.amount_cents', aggregate: 'sum', where: "status = 'paid'",
    unit: 'EUR', scale: 0.01, timezone: 'account', bucket: 'day', window: '30d', refresh: '1h',
    empty: 'zero', partial: 'mark', fixture: 'tests/fixtures/metrics/revenue.sql',
  },
  p95Latency: {
    label: 'p95 latency', source: 'requests.duration_ms', aggregate: 'percentile', p: 0.95,
    unit: 'ms', timezone: 'UTC', bucket: 'hour', window: '7d', refresh: '5m',
    empty: 'gap', partial: 'mark', fixture: 'tests/fixtures/metrics/p95-latency.sql',
  },
} as const;
```

Every entry carries the fields SPEC.md's definition block names (`references/spec.md` section 11): source, formula
(`aggregate` and `where`), unit and scale, time zone, bucket and window, refresh cadence, what an empty bucket shows, how
a partial current bucket is marked, and the oracle fixture section 15 writes. A type makes every field required, so a
metric added without a definition does not compile. A test asserts each `unit` and `scale` against a sampled row. When the product already documents its metrics, the same
definitions, in the registry's words, go there; a new definitions page the goal did not ask for is a discovery.

## 15. Independent-recomputation fixtures

For every metric, `drive:severe-tester` writes fixtures whose correct value is computed independently, by hand in the
test or by a plain SQL query the test also runs, and asserts it against both the data layer's result and the rendered
text read from the DOM or accessibility tree, to the displayed precision. Its brief is "make this number wrong".

| Fixture | Expected |
|---|---|
| rows at 23:30 and 00:30 UTC for an account in a non-UTC timezone | both fall in the local day the offset dictates |
| the account timezone's DST transition days | a 23-hour and a 25-hour day, with complete daily totals |
| a week boundary under Monday-first and Sunday-first locales | each week equals the independent sum |
| an empty bucket in the middle of the range | zero-filled or an explicit gap; no line interpolated through it |
| a zero denominator for every ratio | "n/a", never Infinity, NaN or 0% |
| daily averages rolled up to a month | recomputed from raw rows or weighted; the naive average of averages is shown to differ |
| late-arriving rows in the current bucket | the current bucket is marked partial |
| money stored in minor units | major units with the currency, using the registry's scale |
| another tenant's rows in the same tables | excluded, and the query log shows the tenant predicate |

## 16. Charts

`drive:implementer` invokes `dataviz` before writing chart code; without it these rules stand alone. Use one axis per
chart; two measures become two charts or an index to a base. Assign categorical colours in a fixed order by entity,
never by rank, so filtering does not repaint survivors. Show a single value as a stat tile, not a one-bar chart. Give
every chart with two or more series a legend, and every chart a table-view twin. Put filters in one row above
everything they scope, date range first, and re-render every chart against the same slice. On refetch hold the
previous render at reduced opacity instead of flashing a skeleton. Insert series and category names with `textContent`.
Validate the categorical palette in both modes against the product's real surface colours, and reserve status colours
for status. Use the product's existing charting library and theme; add a new dependency only when archaeology found
none, and record why in DECISIONS.md.

## 17. States, volume and doubles

Every card is built and captured in four states: loading (holds the layout without a jump), empty (an invitation to act
in the product's voice), error (what went wrong and how to fix it, never "Something went wrong"), and data. Seed the
test database at production row counts when known, otherwise a stated estimate times ten; aggregate on the server,
never sum raw rows in the browser; virtualise or paginate lists over 50 items. Measure the query p95 and the latency of
a filter change (target under 200 ms) with a Playwright trace or the Chrome DevTools performance trace. Ask of every
test double where it is kinder than production (unbounded pages, no latency, no auth, no tenant predicate) and make it
enforce the real limit, recording each row in TESTPLAN.md's kindness ledger.

## 18. Access tests

`drive:severe-tester` writes these against the real authorization layer, and `drive:security-reviewer` reviews them
because the `auth` trait applies:

| Request | Expected |
|---|---|
| unauthenticated, to the page and to each data endpoint | redirect or 401 |
| authenticated without the role | 403 with no data fields in the body |
| tenant A's session asking for tenant B's id in a parameter | 403 or empty, and the query log shows the tenant predicate |
| the least-privileged fixture user loading the dashboard | sees only permitted data; screenshot saved as evidence |

The UI never receives data it hides; client-side filtering never stands in for authorization.

## 19. Visual verification

`drive:ui-reviewer` captures the exemplar screen and the dashboard at the same viewports in both themes, in all four
states, and grades consistency rather than distinctiveness: the same spacing and radius tokens read from code, the same
typography, card and control anatomy and chart chrome as existing charts, and no colour outside the product palette,
checked by comparing the computed styles of chart marks against the token set. The objective checks, observation counts
and three-round limit from section 11 apply.

## 20. The ladder for dashboards

| Rung | Means here |
|---|---|
| Local Proof | registry complete with sampled unit checks; every fixture in section 15 green; four states captured; access tests green; palette validated; the product's existing suite still green; `drive:ui-reviewer` verdict against the exemplar; a passing verifier verdict |
| Live Proof | deployed to the environment GOAL.md's `live means:` names; verified as each role, using test accounts the environment already has, reached through variables the owner has set (checked with `test -n "${NAME+x}"`, never printed), or fixture users the product's own seed command creates outside production, and with neither the per-role checks stay at Local Proof with the variable names under Blocked on; each card's number matches an independent read-only query on live data; filter latency measured at real volume; screenshots graded against the exemplar; `proof.json` has `environment: "live"` |
| Operational | released to its audience behind the product's flag or generally; error logs clean over the release traffic; metric definitions current wherever the product documents them |
| Done | Local Proof evidence, `review:` from the final audit, the `live:` bundle, and `doc:` pointing at where the product documents the dashboard's metrics |

The lesson loop appends entries below using the lesson template (`templates/lesson.md`), capped at 40 entries.

## Learned constraints
