# 18 · Domain pack: websites (marketing, blog, docs) and dashboards in existing products

Researcher report for the `/drive` skill. Date: 2026-09-14. Everything marked **verified** was checked today against the cited URL or against `npm view`; **source claim** means a document says it and I did not independently test it; **opinion** is mine and argued.

## 1. Executive opinion

A website built by an agent fails in three predictable ways, and none of them is "the code was wrong." It ships copy that is not true, because the model fills gaps with plausible sentences. It looks like every other agent-built site, because the defaults are the same defaults. And it is declared finished when `dist/` exists, when the only thing that matters is what a stranger sees at the real URL on a phone. The web pack for `/drive` should therefore be organised around three ledgers and one matrix rather than around a framework choice: a claims ledger that every sentence with a number or a superlative must trace to; a design plan that every colour and typeface must derive from, reviewed against the known AI-default looks before a line of CSS is written; and a verification matrix (pages × breakpoints × colour schemes) that a separate grader scores from screenshots of the deployed preview, not of localhost.

The stack question has a clear answer for this shape: Astro 7 with content collections for marketing and blog, Starlight mounted under `/docs` in the same project, built to static HTML and served as an assets-only Cloudflare Worker. Requests to static assets are free and unlimited, preview URLs come from `wrangler versions upload`, and the custom domain is two lines of config. Next.js on Cloudflare works through OpenNext but turns a brochure site into billed Worker invocations with a bundle-size ceiling, for no benefit a static site needs. Plain HTML cannot carry a blog and a docs section without rebuilding a generator badly.

For dashboards inside an existing product the pack inverts its own design instinct: no new aesthetic, exact reuse of the product's tokens and components, and the whole verification budget spent on whether the numbers are right. A dashboard that lies about timezone or aggregation is worse than no dashboard, and it is the failure the owner's own history (dollars versus cents; a kinder-than-production shim) says to expect. The gates that matter are computable: Lighthouse CI, axe, HTML validity, link checking, and an independent recomputation of every displayed aggregate against fixtures. Run them on the preview URL, and only then call it live.

## 2. What the post says, and a critique

The source post is about self-improving agent loops and says almost nothing specific to websites. Two of its steps bear on this pack.

Step 13, "self-verification via vision," has the right structure (a maker renders, a separate verifier reads the screenshot against the goal and the design tokens) and the wrong granularity. One screenshot proves one viewport in one colour scheme. A site verified that way will break at 360 px wide, in dark mode, or with reduced motion, and the grader will have passed it. The pack needs a matrix, a rubric, and a rule that the screenshots come from the deployed preview rather than a dev server, because fonts, headers, caching and the search index all differ between the two.

Step 06, "verifier sub-agent beats self-critique," is right and matters more here than in most domains. A model that wrote a headline is a poor judge of whether the headline is true, and a model that chose a palette is a poor judge of whether the palette is a default. The claims auditor and the visual grader must be separate agents that see only the artifact and the ledger.

Where the post is wrong for this pack: it routes graders to Haiku, which the owner has already declined, and for visual judgment Haiku would be the worst choice available; taste is exactly what cheap graders lack. It also over-indexes on model judgment where a linter would do. Performance, accessibility, HTML validity, broken links, missing metadata and colourblind-safe palettes are all computable. Spend the model budget on the two things that are not computable (is this claim supported, does this look like a choice rather than a default) and spend shell commands on everything else.

The post's state-file example, with "prc is in dollars, not cents" as a verified fact, is a better dashboard lesson than anything it says about UI. The pack should make that kind of fact a required artifact (a metrics registry) rather than a hoped-for memory entry.

## 3. Verified facts

Versions are `npm view <pkg> version` on 2026-09-14 unless stated.

**Astro and Starlight**
- Astro 7.3.2 is current (published 2026-09-08). Astro 6.0 shipped 2026-03-10 requiring Node 22+ and Vite 7, with live content collections, a built-in Fonts API and a Content Security Policy API stable. https://astro.build/blog/astro-6/ , https://github.com/withastro/astro/releases
- Content collections are defined in `src/content.config.ts` with `defineCollection({ loader: glob({ pattern, base }), schema: z.object(...) })`, queried with `getCollection()`, `getEntry()`, `render()`. Zod is imported from `astro/zod` since Astro 6. https://docs.astro.build/en/guides/content-collections/
- `@astrojs/starlight` 0.42.0. The docs say plainly "Starlight is beta software." It can be added to an existing Astro project; docs live in `src/content/docs/` with file-based routing; mounting docs at a subpath means placing content in a nested directory ("the extra nested directory" is a stated current limitation). https://starlight.astro.build/manual-setup/
- Starlight search is Pagefind by default with no configuration; Algolia DocSearch via `@astrojs/starlight-docsearch`. https://starlight.astro.build/guides/site-search/
- Starlight's `<Code>` component accepts a `code` prop and the docs show importing source with Vite's `?raw` suffix (`import importedCode from '/tsconfig.json?raw'`). https://starlight.astro.build/components/code/
- Starlight theming: `customCss` array in the integration config; CSS custom properties for accent and gray scales, `--sl-content-width`, `--sl-text-*`, font variables; the full list is in `packages/starlight/src/style/props.css`. https://starlight.astro.build/guides/css-and-tailwind/
- `starlight-versions` 0.10.1: "an opinionated plugin that is still in early development. Expect frequent updates and changes." Archives the current docs as a named version on first run. https://starlight-versions.vercel.app/getting-started/
- `@astrojs/rss` 4.0.19: endpoint at `src/pages/rss.xml.js`, `site` must be set in config, items from `getCollection`. https://docs.astro.build/en/recipes/rss/
- `@astrojs/sitemap` 3.7.4: requires `site`; emits `sitemap-index.xml` and `sitemap-0.xml`; link it in `<head>` and `robots.txt`. https://docs.astro.build/en/guides/integrations-guide/sitemap/
- `@astrojs/cloudflare` 14.3.1 is only needed for on-demand rendering: "If you're using Astro as a static site builder, you don't need an adapter." https://docs.astro.build/en/guides/integrations-guide/cloudflare/
- Pagefind 1.5.2: `npx pagefind --site <dir>` writes the bundle to `<dir>/pagefind`; a 10,000-page site searches with a network payload under 300 kB. https://pagefind.app/docs/running-pagefind/ , https://pagefind.app/
- OG images: `astro-og-canvas` 0.13.1 (Canvas-based; used by the Astro docs site according to a third-party write-up) and `satori` 0.33.4 (JSX to SVG). Source claim for the "Astro docs use it" part: https://fullmetalbrackets.com/blog/how-to-dynamically-generate-og-images-with-astro

**Cloudflare**
- Pages overview carries the notice "Workers supports most Pages use cases and offers a broader feature set" and "Start new projects with Workers," linking the migration guide. https://developers.cloudflare.com/pages/
- Static assets: "Requests to static assets are free and unlimited." Worker script requests are billed. On the free tier, `run_worker_first` routes return 429 past the limit instead of falling back to assets. https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/
- Assets-only Worker config (no `main`, no `binding`): `{"name","compatibility_date","assets":{"directory":"./dist/…","not_found_handling":"single-page-application"}}`; `not_found_handling` also accepts `"404-page"`; `run_worker_first` accepts `true` or route patterns with `!` negations. `_headers` and `_redirects` "are supported natively in Workers with static assets." https://developers.cloudflare.com/workers/static-assets/migration-guides/migrate-from-pages/ , https://developers.cloudflare.com/workers/static-assets/
- `_headers` format `[url]\n  [name]: [value]`, up to 100 rules, 2,000 chars per line; applies to static responses only. https://developers.cloudflare.com/workers/static-assets/headers/
- Preview URLs: `<VERSION_PREFIX OR ALIAS>-<WORKER_NAME>.<SUBDOMAIN>.workers.dev`; created by `wrangler deploy`, `wrangler versions upload`, or `wrangler versions upload --preview-alias <alias>`; `preview_urls` defaults to the value of `workers_dev`; not available for Workers with Durable Objects; public by default, protectable with Cloudflare Access; Wrangler 4.21.0+ for aliases. https://developers.cloudflare.com/workers/configuration/previews/
- Custom domains: `[[routes]] pattern = "shop.example.com" custom_domain = true`, zone must be on Cloudflare, DNS and certificate created for you; not on a hostname that already has a CNAME. https://developers.cloudflare.com/workers/configuration/routing/custom-domains/
- Workers Builds (git integration): posts a PR comment with build status; "A preview URL will be provided for any builds which perform `wrangler versions upload`"; Worker name must match the `name` in the Wrangler config. https://developers.cloudflare.com/workers/ci-cd/builds/git-integration/github-integration/ , https://developers.cloudflare.com/workers/ci-cd/builds/
- Cloudflare Web Analytics: "does not use any client-side state, such as cookies or localStorage… We also don't 'fingerprint' individuals via their IP address, User Agent string, or any other data"; JavaScript beacon; free. https://www.cloudflare.com/web-analytics/
- `@opennextjs/cloudflare` 1.20.6 runs Next.js 14/15/16 on Workers with the Node.js runtime; Node middleware (15.2+) not yet supported; Worker size limit 3 MiB free / 10 MiB paid compressed. Next 16.3.5 is current. https://opennext.js.org/cloudflare
- Wrangler 4.131.1 current; 4.127.1 installed locally.

**Quality tooling**
- Lighthouse CI `@lhci/cli` 0.15.1: `lhci autorun` collects (3 runs default), asserts, uploads; assertions like `"categories:accessibility": ["error", {"minScore": 1}]`, audit thresholds like `"largest-contentful-paint": ["error", {"maxNumericValue": 2500}]`, `aggregationMethod` median/optimistic/pessimistic/median-run, `collect.staticDistDir`, `collect.url`, `settings.preset: "desktop"`, `budgetsFile` (exclusive of other assert options). https://github.com/GoogleChrome/lighthouse-ci/blob/main/docs/configuration.md , https://github.com/GoogleChrome/lighthouse-ci/blob/main/docs/getting-started.md
- Lighthouse score bands: 0-49 red, 50-89 orange, 90-100 green; performance weights LCP 25%, TBT 30%, CLS 25%, FCP 10%, SI 10%; run-to-run variability is expected. https://developer.chrome.com/docs/lighthouse/performance/performance-scoring
- Core Web Vitals thresholds at the 75th percentile: LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1; FID retired in favour of INP. https://web.dev/articles/vitals
- `@axe-core/cli` 4.13.0: `axe <url> --tags wcag2a,wcag2aa,wcag21aa --exit --save out.json`; needs a Chrome driver (`browser-driver-manager`). https://github.com/dequelabs/axe-core-npm/blob/develop/packages/cli/README.md
- `@axe-core/playwright` 4.13.0 with `@playwright/test` 1.63.0: `new AxeBuilder({ page }).withTags([...]).analyze()`; `expect(results.violations).toEqual([])`. Playwright emulation: per-project `devices[...]`, `test.use({ viewport, colorScheme })`, and `reducedMotion: 'reduce' | 'no-preference'`, `forcedColors: 'active'` as context options. https://playwright.dev/docs/accessibility-testing , https://playwright.dev/docs/emulation , https://playwright.dev/docs/api/class-browser
- `pa11y-ci` 4.1.1: `pa11y-ci --sitemap https://site/sitemap.xml` or `.pa11yci` with `urls` and `defaults`. https://github.com/pa11y/pa11y-ci
- `lychee` (Rust; `brew install lychee`): `lychee --offline --base <dir> <files>`, `--accept '200..=204,429'`, `--exclude <regex>`, `--format json`, exit 2 on broken links. https://github.com/lycheeverse/lychee
- `linkinator` 8.1.0: `npx linkinator ./dist --recurse` serves and crawls a build directory; `--skip`, `--check-fragments`, `--clean-urls`, `--format JSON`. https://github.com/JustinBeckwith/linkinator
- `html-validate` 11.15.0: `npx html-validate "dist/**/*.html"`, config `.htmlvalidate.json`, preset `html-validate:recommended`, formatters stylish/json/checkstyle. https://html-validate.org/usage/cli.html
- `vnu-jar` 26.9.7 (Nu HTML Checker): `java -jar vnu.jar [OPTIONS] FILES|DIRECTORY|URL`, `--skip-non-html`; the npm package exports the jar path. https://validator.github.io/validator/
- In this session: the Chrome DevTools MCP exposes `lighthouse_audit` (accessibility, SEO, best practices, "excludes performance"; device desktop/mobile; navigation or snapshot mode; `outputDirPath`), `emulate` (viewport string `WxHxDPR[,mobile][,touch]`, `colorScheme`, network and CPU throttling), `resize_page`, `take_screenshot` (`fullPage`, `filePath`); the Playwright MCP exposes `browser_resize` and `browser_take_screenshot` (`fullPage`, `filename`). Verified from the loaded tool schemas.

**Installed skills (read in full today)**
- `frontend-design` (`~/.agents/skills/frontend-design/SKILL.md`): two-pass process (design plan with 4-6 named hex colours, 2+ type roles, ASCII layout, one signature element; then a review against "the generic default you would produce for any similar page"); names three current AI-default looks (warm cream + serif + terracotta; near-black + acid green/vermilion; broadsheet hairlines and zero radius); requires a quality floor of responsive to mobile, visible focus, reduced motion respected; recommends screenshots for self-critique.
- `design` (bundled canvas skill): seeds `.dc.html` artboards into a published Artifact via `seed-canvas.mjs`; step 0 is "match the existing app pixel-perfectly"; has an explicit "when you cannot ask" path (commit to one direction, put 1-2 low-fi alternates beside it, state the assumption); for charts defers to `dataviz`; forbids lorem ipsum and "Welcome to our website"; bracketed placeholders like `[YOUR PRICE]` for missing facts.
- `dataviz` (bundled): form first, colour last; palette validator `node scripts/validate_palette.js "<hex,…>" --mode light|dark --surface <hex>`; non-negotiables (one axis, fixed categorical order, sequential one hue, diverging two hues + neutral midpoint, legend for ≥2 series, table-view twin, filters in one row above, hold previous render on refetch, `textContent` for untrusted labels); an anti-pattern catalogue.
- `google-dev-docs-style` (`~/Projects/google-dev-docs-skill/skill/`): golden rules (second person, imperative, present tense, sentence case, no "please", no directional language, code font rules, placeholders in UPPER_SNAKE_CASE, example.com and reserved IP ranges only) plus six reference files and a review checklist.
- `writing` (arcwell plugin 2.0.0; the `~/.claude/skills/writing` symlink is dangling since the v2 cutover and should be repointed to `~/Projects/arcwell/plugins/arcwell/skills/writing`): six relationships (source, thought, author, reader, structure, language), a Fable "story map" stage for narrative pieces only, a six-substitution revision pass, and the fidelity rule "never improve the result, invent a motive or reaction… or add a larger implication because it would make better copy."
- `imagegen` (`~/.claude/skills/imagegen/SKILL.md`; CLI at `~/.cargo/bin/imagegen`, needs `OPENAI_API_KEY`): `imagegen generate "<prompt>" -o file -s WxH -q low|medium|high -f webp -n N`; low ≈ $0.006, high ≈ $0.21 per image; edges multiples of 16, max edge 3840, ratio ≤ 3:1; exit 3 on moderation.
- `web-design-guidelines`: fetches Vercel's `command.md` and reports `file:line` findings across accessibility, focus, forms, animation, typography, touch, dark mode, i18n, hydration. Example rules verified in that file: icon-only buttons need `aria-label`; never `outline: none` without a focus replacement; honour `prefers-reduced-motion`; lists over 50 items virtualise; URL reflects state; use `Intl.DateTimeFormat`. https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md
- Diátaxis: tutorials, how-to guides, reference, explanation on two axes (practical/theoretical, acquisition/application). https://diataxis.fr/

## 4. Detailed spec

### 4.1 Stack decision

Opinion, argued. The pack should pick Astro static output unless a stated condition overrides it, and record the decision in `site/DECISIONS.md` with the condition that would flip it.

| Option | Maintainability | Performance | How well agents build with it | Verdict |
|---|---|---|---|---|
| Astro 7 + content collections + Starlight, static | Markdown/MDX content with a Zod schema; one repo; typed frontmatter is where the claims ledger hooks in | Zero client JS by default; Lighthouse performance is close to free | Mostly HTML and CSS; small API surface; few hydration foot-guns; content collections make "add a post" a file write | Default |
| Next.js 16 via OpenNext on Workers | Larger surface; app router conventions to learn; content needs MDX plugins or a CMS | Fine, but a brochure site becomes Worker invocations (billed) with a 3/10 MiB bundle ceiling | Agents are fluent, but fluency produces client components and hydration where none is needed | Only if the site is the product app or must share live components with a Next product |
| Plain HTML + CSS | Trivial until the second blog post; then hand-rolled RSS, sitemap, OG, search | Best possible | Fine for one page; agents then reinvent a generator badly | One-page landing only |
| Hugo/Eleventy/Docusaurus | Mature; Docusaurus is React-heavy for docs | Good | Templating dialects and plugin ecosystems the agent knows less well than Astro's | Not for a fresh build |

Why Astro specifically for an agent: the content model is files with schemas, so a build fails on a missing `description` or an unknown claim id; Starlight supplies search, sidebar, dark mode, i18n and a code component that can import samples from tested files; and the Astro 6+ Fonts API and CSP API cover two gates (self-hosted fonts, a real Content-Security-Policy) without third-party scripts. The cost is that Starlight is self-described beta at 0.42 and Astro moves majors yearly, so pin exact versions and upgrade only as a deliberate task, never as a side effect of `npm install`.

Single project, not two. Marketing and blog pages live in `src/pages/` and `src/content/{pages,blog}/`; docs live in `src/content/docs/docs/**` so they render under `/docs/…` (the nested directory is the documented way to mount Starlight at a subpath). Do not create `src/content/docs/index.md`, or it will collide with the marketing home page. Verify this at scaffold time by building and listing `dist/` before writing any content; if the routes collide, the fallback is two Astro projects behind one Worker with `run_worker_first` routing, which costs more and should be recorded as a deviation.

Server code only where a page needs it. A contact or newsletter form gets a tiny Worker handler with `"main": "src/worker.ts"` and `"run_worker_first": ["/api/*"]`, so every other request stays a free static asset. Nothing else in this pack needs the Cloudflare adapter.

### 4.2 Project layout

```
site/
  astro.config.mjs            # site: 'https://www.example.com', integrations: [starlight(...), sitemap()]
  wrangler.jsonc              # assets-only Worker (below)
  package.json                # exact-pinned versions; scripts: build, gates, preview, deploy
  public/
    _headers                  # security + cache headers
    _redirects
    robots.txt                # Sitemap: line
  src/
    content.config.ts         # pages, blog, docs, team, claims collections
    content/
      pages/*.mdx             # marketing pages; frontmatter: claims: [ids]
      blog/*.mdx              # draft: true excluded in PROD
      docs/docs/**            # Starlight content mounted at /docs
      team/*.yaml             # only supplied names/roles/photos
      claims/claims.yaml      # the claims ledger (file() loader)
    components/Claim.astro    # <Claim id="...">text</Claim> → <span data-claim="id">
    styles/tokens.css         # design tokens; light + dark
    styles/starlight.css      # maps tokens onto --sl-* variables
    pages/                    # index.astro, blog/[...slug].astro, rss.xml.js, og/[...slug].png.ts
  examples/                   # runnable code samples imported into docs via ?raw; has its own tests
  tests/
    e2e/                      # Playwright: a11y (axe), screenshots matrix, meta checks
    gates/                    # node scripts: claims-lint, placeholder-lint, meta-lint, sitemap-check
  research/
    market-map.md, positioning.md, sitemap.yaml, briefs/<page>.md
  .drive/                     # STATE.md, screenshots/, lighthouse/, gate-results/
```

### 4.3 Deployment recipe

`wrangler.jsonc` for the assets-only case:

```jsonc
{
  "name": "example-site",
  "compatibility_date": "2026-09-14",
  "assets": {
    "directory": "./dist",
    "not_found_handling": "404-page"
  },
  "workers_dev": true,
  "preview_urls": true,
  "routes": [
    { "pattern": "www.example.com", "custom_domain": true }
  ]
}
```

Use `"404-page"` for a content site so missing pages return a real 404 with `dist/404.html`; `"single-page-application"` would mask broken links behind a 200. Leave `html_handling` at its default unless Astro's `trailingSlash` setting disagrees with what the link checker reports.

`public/_headers` (static responses only):

```
/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  X-Frame-Options: DENY
/_astro/*
  Cache-Control: public, max-age=31536000, immutable
```

Set the Content-Security-Policy through Astro's CSP API (stable since 6.0) so hashes for inline scripts are generated at build; a hand-written CSP in `_headers` will break the first time Astro emits an inline script.

The release sequence, driven by the skill itself and never by waiting on Workers Builds:

```bash
npm ci
npm run build                                   # astro build → dist/ ; also runs pagefind if Starlight didn't
npm run gates:local                             # html-validate, claims-lint, placeholder-lint, meta-lint, links (offline)
npx wrangler versions upload --preview-alias drive
#   → https://drive-example-site.<subdomain>.workers.dev
npm run gates:preview -- https://drive-example-site.<subdomain>.workers.dev
#   lhci autorun (mobile + desktop), axe, pa11y-ci --sitemap, linkinator --recurse, curl -sI header check,
#   Playwright screenshot matrix → .drive/screenshots/
#   → visual grader + claims auditor run on the preview
npx wrangler versions deploy                    # promote the tested version id (verify command with --help; fallback: wrangler deploy)
curl -s https://www.example.com/ | grep -q "<meta name=\"x-build\" content=\"$(git rev-parse --short HEAD)\""
```

Promoting the uploaded version rather than re-deploying from source means the bytes that passed the gates are the bytes that went live. Stamp every page with `<meta name="x-build" content="<git sha>">` so the last line can prove the production URL serves this build and not a cached predecessor. The custom domain is created on the first `wrangler deploy` that carries the `routes` entry; the domain must already be a zone on the same Cloudflare account.

Workers Builds is optional. If the repo is connected, keep the deploy command as `npx wrangler versions upload` so PRs get preview comments, but the skill's own run must not depend on it; the owner commits to main and the skill deploys directly.

### 4.4 From research to content

The chain is research → positioning → site map → page briefs → copy, and every link carries provenance forward. Store all of it under `site/research/` so the claims auditor can follow a sentence back to a source without asking anyone.

**Market map** (`research/market-map.md`), produced with `deep-research` (or the tavily skills for narrower scans): the category as buyers name it; five to ten alternatives with what each claims on its own site (quoted, with URL and date); what each charges; who each is for; the gaps nobody claims. Every entry cites the competitor's own page. Do not paraphrase a competitor's claim into something stronger than they said.

**Positioning** (`research/positioning.md`):

```markdown
# Positioning
## Audience
Primary: <role, situation, what they are trying to do this week>. Secondary: <...>.
## Category
We are a <category buyers already search for>, for <audience>, that <one differentiating outcome>.
## Messaging pillars (3, at most 4)
1. <pillar>: <one sentence a buyer would say back to us>. Proof: claims latency-p50, uptime-2026q2.
2. ...
## Proof points
| id | statement | kind | evidence |
| latency-p50 | Median response under 40 ms | measured | bench/2026-09-10-latency.md#p50 |
## Competitor claims we must not echo
- "<quote>" (<vendor>, <URL>, <date>) : we cannot say this; we do not measure it.
## What we do not say
- No "fastest", "only", "leading", "enterprise-grade" without a measured or quoted claim.
```

**Claims ledger** (`src/content/claims/claims.yaml`, loaded as a collection so the build type-checks it):

```yaml
- id: latency-p50
  text: "Median response under 40 ms"
  kind: measured            # measured | demonstrated | quoted | descriptive | roadmap
  evidence: bench/2026-09-10-latency.md#p50
  verified: 2026-09-10
  expires: 2026-12-10
- id: soc2
  text: "SOC 2 Type II"
  kind: quoted
  evidence: compliance/soc2-letter-2026-06.pdf
  verified: 2026-06-30
- id: sso-planned
  text: "SSO is planned for Q1"
  kind: roadmap
  evidence: ROADMAP.md#sso
  verified: 2026-09-14
```

Rules the build enforces: `measured` needs a file containing the number and how it was measured; `demonstrated` needs a URL or a test name that shows the behaviour; `quoted` needs a named source and permission; `descriptive` is for things the code plainly does (checked by the auditor against the repository); `roadmap` claims may only appear on a roadmap or changelog page and must be phrased as future. An expired claim fails the build.

Copy marks claims with the `<Claim id="latency-p50">median response under 40 ms</Claim>` component, which renders a plain `<span data-claim="latency-p50">`. The claims lint then runs on `dist/`: any sentence on a marketing page that contains a number with a unit or percent, a multiplier ("3x"), or a superlative from a fixed list (fastest, only, leading, best, most, enterprise-grade, bank-grade, zero, unlimited, guaranteed, trusted by) must sit inside a `[data-claim]` element whose id exists and is verified; otherwise the gate fails and prints the sentence. Docs pages are exempt from the superlative check (they should not contain superlatives anyway) but not from the number check on landing-style docs pages.

**Site map** (`research/sitemap.yaml`): every URL, its single job, its primary call to action, which pillars it carries, and which claims it may use. Typical first cut: `/`, `/product` (or per-pillar pages), `/pricing` (only if prices are supplied; otherwise no page rather than a bracketed one), `/team`, `/blog`, `/blog/<slug>`, `/docs/…`, `/changelog`, `/privacy`, `/404`.

**Page brief** (`research/briefs/<page>.md`), written before copy:

```markdown
# / (home)
Job: a <audience> lands from a search for <category> and decides in 10 seconds whether this is for them.
Reader's question on arrival: "<question>". Answer in the hero: "<one sentence>".
Sections (in order, each with the reader's next question it answers):
1. Hero: <claim ids allowed>
2. <section>: <what it must make the reader believe>; proof: <claim ids>
Primary action: <one verb phrase>, repeated at <positions>.
Forbidden here: pricing numbers (none supplied), team photos (none supplied), roadmap claims.
Tone: <two adjectives from positioning>; register: <peer / practitioner / buyer>.
```

**Copy.** Invoke the `writing` skill before drafting any marketing or blog prose, hand it the positioning document, the claims ledger and the page brief as "the source," and hold it to the fidelity rule: nothing improved, no motive or implication added. Skip the skill's Fable story-map stage for product pages and feature posts (the skill itself limits it to substantial narratives built from a dossier); use it for a founding-story or lessons-learned post. Run the skill's six-substitution revision pass as a separate step by a different agent than the drafter. The `frontend-design` skill's own writing section applies to interface copy: name things by what the reader controls, active voice, the button says what happens, an empty state is an invitation to act.

**Team page.** Names, roles and photos come only from supplied input or the repository (`AUTHORS`, git log, a supplied `team.yaml`). Never generate a bio, never generate a portrait, never fill a grid to make it look staffed. A team of one is a team page with one person on it.

### 4.5 Design process

The order is direction, tokens, layout system, imagery, implementation, verification, and the direction step happens before any CSS exists.

**Direction.** Load `frontend-design` with the Skill tool and produce `design/plan.md` following its two-pass process: a compact token system (4-6 named hex colours; a display face, a body face, optionally a utility face; a layout concept as one sentence and an ASCII wireframe; one signature element grounded in the subject's own world), then the review pass in which the agent writes down what the generic default for this kind of site would be and shows how the plan differs. Add one explicit check the skill implies but does not make mechanical: the plan must not match any of the three named default looks (cream/serif/terracotta; near-black with acid accent; broadsheet hairlines) unless the brief asked for one, and must not use Inter, Roboto, Arial or Fraunces as the display face (the `design` skill's slop list). Record the rejected default and the chosen alternative in the plan; the visual grader reads both.

**When to open a design canvas.** The `design` skill publishes an Artifact for a human to tweak. Under autonomous operation nobody is going to tweak it, and the skill's own "when you cannot ask" path says to commit to one direction and build the deliverable. So: default off. Turn it on only when the goal says mockups, options or "let me choose," or when a stakeholder other than the owner must approve a direction; then seed two to four direction artboards, pick one autonomously by rubric (subject-grounding, distance from defaults, legibility at phone width, contrast), build into `Main.dc.html`, and record the choice in `.drive/STATE.md`. Never gate the build on someone opening the canvas; that is an approval queue.

**Tokens** (`src/styles/tokens.css`): colours as CSS custom properties defined once on `:root` for light and redefined under `@media (prefers-color-scheme: dark)` and `[data-theme="dark"]`; a type scale with named steps; a spacing scale; radii; a motion token that collapses to zero under `prefers-reduced-motion: reduce`. `src/styles/starlight.css` maps the same tokens onto Starlight's variables (accent and gray scales, `--sl-font`, `--sl-content-width`) so docs and marketing read as one site; Starlight's theme toggle sets `data-theme`, so the site's toggle must use the same attribute. Fonts via the Astro Fonts API, self-hosted, with a fallback stack of similar metrics so CLS stays under 0.1 during font swap.

**Layout system.** A container width, a column grid, and the section rhythm decided once. The `frontend-design` skill warns about CSS specificity collisions between section-level and element-level selectors; enforce a single layer order (`@layer tokens, base, layout, components, utilities`) so that class fights cannot happen.

**Imagery.** Use `imagegen` for illustrations, hero art, diagrams-as-illustration and OG backgrounds; never for people, never for product screenshots (take real ones), never for logos of anyone else. Draft with `-q low -n 3 -f webp`, choose by the design plan's criteria, regenerate the winner at `-q medium` (or `high` for a hero), at a size that is a multiple of 16 and no larger than the largest rendered size times two. Every image gets meaningful `alt` text or `alt=""` if decorative, explicit `width` and `height`, and `loading="lazy"` below the fold. Budget: a site should need under a dozen generated images; record spend from `--json` in STATE. Exit code 3 (moderation) means rephrase the prompt, not retry.

**Implementation.** Sonnet builds pages from the plan and the briefs, Opus builds the tokens and layout system first. The rule that every colour and typeface must trace to `design/plan.md` is enforced by a lint that fails on any hex literal or `font-family` outside `tokens.css`.

**Vision verification.** After the preview deploy, a Playwright script (or the Playwright MCP in-session) captures the matrix:

```ts
// tests/e2e/screens.spec.ts
import { test, devices } from '@playwright/test';
const pages = ['/', '/product', '/team', '/blog', '/blog/<first-slug>', '/docs/', '/docs/getting-started/', '/404-does-not-exist'];
const views = [
  { name: 'phone',   viewport: { width: 360,  height: 780 } },
  { name: 'tablet',  viewport: { width: 768,  height: 1024 } },
  { name: 'laptop',  viewport: { width: 1280, height: 800 } },
  { name: 'wide',    viewport: { width: 1600, height: 900 } },
];
for (const v of views) for (const scheme of ['light', 'dark'] as const) {
  test.describe(`${v.name}-${scheme}`, () => {
    test.use({ viewport: v.viewport, colorScheme: scheme, reducedMotion: 'reduce' });
    for (const p of pages) test(p, async ({ page }) => {
      await page.goto(process.env.BASE_URL + p, { waitUntil: 'networkidle' });
      await page.screenshot({ path: `.drive/screenshots/${v.name}-${scheme}${p.replace(/\W+/g, '_')}.png`, fullPage: true });
    });
  });
}
```

Eight pages × four widths × two schemes is 64 screenshots; that is the point. The visual grader (section 6) receives the screenshots, `design/plan.md`, and the page briefs, and returns a structured gap list. Its rubric: does the hero state the page's job in the brief's words; does the signature element appear; are any of the three default looks present; is there text under 16 px at phone width or a horizontal scrollbar; do dark and light both derive from the tokens (no light-only images with white backgrounds); is focus visible on the first interactive element (a second screenshot after `Tab`); is anything overlapping or clipped; does the 404 page look like the site. The grader never sees the maker's transcript.

### 4.6 Docs section

**Information architecture.** Diátaxis, made concrete as four sidebar groups: Get started (tutorials: one guaranteed path from nothing to a working result, tested end to end), Guides (how-to: one task each, titled with a base-form verb), Reference (generated where possible from the source of truth: CLI `--help`, OpenAPI, TypeDoc; hand-written reference must cite the source file it describes), and Concepts (explanation: why it works this way, trade-offs, what it is not). Starlight's `sidebar` config with `autogenerate` per directory keeps the groups honest: a file in `guides/` is a how-to or it moves.

**Style.** Invoke `google-dev-docs-style` for every docs page and run its `references/review-checklist.md` as the last pass. Use `writing` for marketing and blog, `google-dev-docs-style` for docs; do not mix them. The two disagree on purpose: the docs skill wants an impersonal second-person present tense with em dashes and no humour; the writing skill protects an author's voice. Reference material is impersonal by design and the writing skill says as much.

**Code samples that are tested.** Samples live as runnable files under `examples/` with their own test command (`npm test` in that directory, or a language-appropriate runner). Docs import them rather than pasting:

```mdx
import { Code } from '@astrojs/starlight/components';
import quickstart from '../../../../examples/quickstart/index.ts?raw';

<Code code={quickstart} lang="ts" title="index.ts" />
```

The gate runs `examples/` tests on every build, so a sample that stops compiling fails the site build. For shell transcripts, the `examples/` directory holds a script that runs the documented commands against a clean temp directory and diffs the output against the documented output block (normalising timestamps and ids); the docs import the script and the captured output.

**Docs smoke test.** Before publishing, a fresh agent with no prior context follows the Get Started tutorial literally in a clean directory using only the published preview, and reports every step where it had to guess, where a command differed from the docs, or where output did not match. Each report item is a docs bug and blocks Done. This is the antidote to docs that describe intent rather than behaviour.

**Search.** Pagefind runs at build; the index does not exist under `astro dev`, so verify search on the preview URL with a Playwright test that types a known term and asserts a result link. Move to Algolia only when a site owner has a DocSearch account; never for a new project.

**Versioning.** Do not version docs until the product has a second supported major version. When that happens, `starlight-versions` is the only Starlight-native option and it is self-described early development; pin it, run it on a branch of the docs content first, and treat the first archived version as a test. Until then, a changelog page and "Added in vX.Y" asides carry the load.

**Navigation.** Every docs page has a next/previous pair (Starlight default), a "last updated" from git (Starlight `lastUpdated: true`), and an edit link if the repo is public. The docs landing at `/docs/` is a short router: the one tutorial, the three most-used guides, the reference index. No hero, no marketing.

### 4.7 Blog

Content model (`src/content.config.ts`):

```ts
const blog = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/blog' }),
  schema: ({ image }) => z.object({
    title: z.string().max(70),
    description: z.string().min(50).max(160),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    author: z.string(),                 // must match an entry in team/
    tags: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
    heroImage: image().optional(),
    heroAlt: z.string().optional(),
    claims: z.array(z.string()).default([]),
  }).refine(p => !p.heroImage || p.heroAlt, { message: 'heroImage needs heroAlt' }),
});
```

Drafts: `getCollection('blog', p => import.meta.env.PROD ? !p.data.draft : true)` in every place posts are listed, including RSS and the sitemap (`sitemap({ filter })`). A gate greps `dist/` for any draft slug to prove it.

RSS at `/rss.xml` via `@astrojs/rss` with full content rendered from the entry and sanitised; the gate fetches it from the preview, parses it, and asserts item count equals published post count and every `link` returns 200. OG images generated at build per post from title and author with `astro-og-canvas` (or satori), 1200×630, referenced by absolute URL; the meta gate asserts the referenced file exists in `dist/`. Sitemap and robots as in section 3, with `robots.txt` pointing at `sitemap-index.xml` and the preview deploy carrying `X-Robots-Tag: noindex` in `_headers` for the preview alias only (a second `_headers` written by the build when `PREVIEW=1`), so preview URLs never get indexed.

### 4.8 Quality gates

All gates run twice: `gates:local` on `dist/` (fast, no network) and `gates:preview` against the preview URL (the truth). Targets are opinions calibrated to a static site, where anything under 95 performance means something is wrong rather than something is hard.

| Gate | Command | Target | Notes |
|---|---|---|---|
| Lighthouse (mobile default + desktop) | `npx @lhci/cli@0.15.1 autorun --config=lighthouserc.cjs` with `collect.url` from the sitemap, `numberOfRuns: 3` | performance ≥ 0.95, accessibility = 1.0, best-practices ≥ 0.95, SEO = 1.0; LCP ≤ 2500 ms, CLS ≤ 0.1, TBT ≤ 200 ms (median) | Lab TBT is the proxy for INP; field INP comes later from analytics |
| Accessibility (engine) | `npx @axe-core/cli <urls> --tags wcag2a,wcag2aa,wcag21aa --exit --save .drive/axe.json` or `npx pa11y-ci --sitemap <preview>/sitemap-0.xml` | zero violations | Prefer the Playwright `@axe-core/playwright` test so it runs per page per scheme with a real keyboard pass |
| Accessibility (manual proxies) | Playwright: `Tab` through the header and assert `:focus-visible` box exists; assert `html[lang]`; assert one `h1` per page; assert every `img` has `alt` attribute present | all pass | Engines miss focus order and heading logic |
| HTML validity | `npx html-validate "dist/**/*.html"`; optionally `java -jar "$(node -p "require('vnu-jar')")" --skip-non-html --errors-only dist/` | zero errors | Nu checker needs Java; html-validate alone is acceptable |
| Broken links (internal, offline) | `lychee --offline --base dist --include-fragments "dist/**/*.html"` or `npx linkinator ./dist --recurse --check-fragments` | zero broken | Fragments matter for docs anchors |
| Broken links (external, preview) | `lychee --accept '200..=204,429' --exclude 'linkedin\.com' --format json --cache <preview>` | zero broken (429 tolerated) | Cache to avoid hammering |
| Meta and OG | `node tests/gates/meta-lint.mjs dist` | every page: `<title>` ≤ 60 chars and unique; `meta description` 50-160; canonical absolute; `og:title`, `og:description`, `og:image` absolute and file present; `twitter:card`; `x-build` stamp | Simple parser over `dist/**/*.html` |
| Sitemap and robots | `node tests/gates/sitemap-check.mjs <preview>` | every sitemap URL returns 200 with `text/html`; every built page except 404 is in the sitemap; `robots.txt` references the sitemap; preview carries `noindex` | |
| Security headers | `curl -sI <preview>/ \| grep -Ei 'content-security-policy\|x-content-type-options\|referrer-policy'` | all present | `_headers` only affects static responses; check a docs page too |
| Placeholder text | `! grep -rEil 'lorem ipsum\|\[(TODO\|TBD\|PLACEHOLDER\|YOUR [A-Z ]+)\]\|welcome to our website\|your company\|acme corp\|john doe\|jane doe' dist/` (docs paths may contain `example.com`; marketing paths may not) | no matches | The `design` skill's bracket placeholders are for drafts; they never ship |
| Claims | `node tests/gates/claims-lint.mjs dist src/content/claims/claims.yaml` | every numeric or superlative sentence inside `[data-claim]`, every id verified and unexpired | Section 4.4 |
| Draft leakage | `node tests/gates/drafts-check.mjs dist` | no draft slug in `dist/`, RSS or sitemap | |
| RSS | fetch `<preview>/rss.xml`, parse with `fast-xml-parser`, assert items = published posts, links 200 | pass | |
| Search | Playwright: open `/docs/`, type a term known to be on one page, assert result link | pass | Proves the Pagefind index shipped |
| Palette (charts only) | `node <dataviz>/scripts/validate_palette.js "<hex,…>" --mode light` and `--mode dark --surface <hex>` | exit 0 | Section 4.9 |
| Web Interface Guidelines | `web-design-guidelines` skill over `src/**/*.astro` and `src/styles/**` | no findings, or each accepted with a reason in STATE | Text review, cheap |

`lighthouserc.cjs`:

```js
module.exports = {
  ci: {
    collect: {
      url: JSON.parse(process.env.LH_URLS),   // from sitemap-check
      numberOfRuns: 3,
      settings: { preset: process.env.LH_PRESET === 'desktop' ? 'desktop' : undefined },
    },
    assert: {
      assertions: {
        'categories:performance':    ['error', { minScore: 0.95, aggregationMethod: 'median' }],
        'categories:accessibility':  ['error', { minScore: 1 }],
        'categories:best-practices': ['error', { minScore: 0.95 }],
        'categories:seo':            ['error', { minScore: 1 }],
        'largest-contentful-paint':  ['error', { maxNumericValue: 2500, aggregationMethod: 'median' }],
        'cumulative-layout-shift':   ['error', { maxNumericValue: 0.1 }],
        'total-blocking-time':       ['error', { maxNumericValue: 200 }],
      },
    },
    upload: { target: 'filesystem', outputDir: './.drive/lighthouse' },
  },
};
```

Analytics and privacy: Cloudflare Web Analytics beacon, which by Cloudflare's statement uses no cookies, no localStorage and no fingerprinting, so the site ships no consent banner and no third-party script other than the beacon. If a stakeholder insists on cookie-based analytics, that is a condition that adds a consent step, a cookie policy page and a gate that the analytics script does not load before consent; the pack should push back once with the cookieless option and then do it properly. Core Web Vitals in the field come from the analytics dashboard after launch; record the first week's p75 in STATE as the Operational proof.

In-session shortcuts: the Chrome DevTools MCP `lighthouse_audit` covers accessibility, SEO and best practices but not performance (its own description says so), so it is a quick check, not the gate; `emulate` with `viewport: "360x780x3,mobile,touch"` and `colorScheme: "dark"` plus `take_screenshot` covers the matrix by hand when Playwright is not set up yet.

### 4.9 Dashboards in an existing product

**Archaeology first** (`.drive/archaeology.md`, written before any code): framework and version from `package.json` and lockfile; router and layout shell; state and data layer (REST, GraphQL, tRPC, server components; the fetch wrapper everyone uses; auth headers); authorization model (roles, tenants, row-level rules, where they are enforced); the design system (tokens file, component library, an existing page closest to a dashboard; the charting library already in the bundle, if any); test setup (runner, fixtures, factories, MSW or equivalent); how existing screens handle loading, empty and error; feature flags; the database schema for the tables the dashboard will read, including the type and timezone of every timestamp column and the unit of every money column. The `design` skill's step 0 applies verbatim: lift exact values from the real component source; never round to a grid; new UI extends the vocabulary.

**Metrics registry** (`src/features/<dashboard>/metrics.ts`), the single source that both the query builder and the UI labels read:

```ts
export const metrics = {
  activeUsers: { label: 'Active users', unit: 'count', aggregate: 'distinct_count', of: 'events.user_id', bucket: 'day', timezone: 'account' },
  revenue:     { label: 'Revenue', unit: 'EUR', aggregate: 'sum', of: 'orders.amount_cents', scale: 0.01, bucket: 'day', timezone: 'account' },
  p95Latency:  { label: 'p95 latency', unit: 'ms', aggregate: 'percentile', p: 0.95, of: 'requests.duration_ms', bucket: 'hour', timezone: 'UTC' },
} as const;
```

A metric that is not in the registry cannot be rendered. The registry is where "dollars, not cents" lives as code rather than as a memory note, and a test asserts each `scale` and `unit` against a sampled row (`SELECT MIN(x), MAX(x)`), which is exactly the verification the post's state file describes.

**Data-correctness tests against fixtures.** For every metric, a fixture with rows whose correct aggregate is computed independently (by hand in the test, or by a plain SQL query the test also runs), then asserted against what the dashboard's data layer returns and what the rendered component shows. The fixture set must include: rows at 23:30 and 00:30 UTC across a day boundary for an account in a non-UTC timezone (expect both in the same local day when the offset says so); the DST transition days for that timezone (a 23-hour and a 25-hour day); a week boundary under both Monday-first and Sunday-first locales; an empty bucket in the middle of the range (expect zero-fill or an explicit gap, never a line that interpolates through it); a period with a zero denominator for every ratio (expect "n/a", not Infinity or 0%); an average-of-averages trap (daily averages rolled up to a month must be weighted or recomputed from raw); late-arriving rows (the "today" bucket is marked partial); money in minor units; a metric filtered by tenant where the fixture contains another tenant's rows. The dashboard number equals the independent number, to the displayed precision, or the test fails.

**Dataviz rules that apply**, taken from the installed skill and made into checks: one axis per chart (two measures means two charts or indexing to a base); categorical hues assigned in fixed order by entity, never by rank, so filtering does not repaint survivors; a single-value metric is a stat tile, not a one-bar chart; a legend for two or more series and a table-view twin for every chart; filters in one row above everything they scope, date range first, and every chart re-rendered against the same slice; on refetch the previous render is held at reduced opacity, no skeleton flash; series and category names inserted with `textContent`; the categorical palette validated with `validate_palette.js` in both modes against the product's actual surface colours; status colours reserved for status. If the product already has a charting library, use it and its theme; if not, prefer a small dependency the archaeology can justify, and record the choice.

**States.** Every card renders and is tested in four states: loading (holds layout, no jump), empty (an invitation to act in the product's voice, per `frontend-design`'s copy guidance), error (what went wrong and how to fix it, never "Something went wrong"), and data. Playwright captures all four via fixtures or request interception; the visual grader sees them alongside an existing product screen.

**Performance with real volumes.** Seed the test database at a volume the archaeology justifies (production row counts if known, otherwise a stated estimate times ten); aggregate on the server; never ship raw rows to the browser to sum; paginate or virtualise any list over 50 items; measure the query p95 and the interaction latency of a filter change (target under 200 ms, the INP threshold) with a Playwright trace or the Chrome DevTools MCP performance trace. The shim question from the owner's D1 incident applies: if the test API returns unbounded page sizes, no latency, no auth, then it is kinder than production and certifies nothing; make the fixture layer enforce the same limits as the real one.

**Access control.** Tests, not a checklist: unauthenticated request to the page and to each data endpoint (expect redirect or 401); authenticated user without the role (expect 403 and a response body with no data fields); tenant A's session requesting tenant B's id in a parameter (expect 403 or empty, and a query-log assertion that the tenant predicate was present); the UI never receives data it hides, so no client-side filtering stands in for authorization. Run the dashboard as the least-privileged fixture user and screenshot what they see.

**Visual verification against the existing system.** Screenshot the closest existing product screen and the new dashboard at the same viewports in both themes; the grader's question is consistency, not distinctiveness: same spacing and radius tokens (read from the code, not eyeballed), same typography, same card and control anatomy, same chart chrome as any existing chart, no colours outside the product palette (computable: collect the computed styles of chart marks and compare against the token set), all four states present. The `frontend-design` instruction to take one aesthetic risk is switched off for this shape.

### 4.10 Definitions of done

Mapped to the owner's status ladder. Local-only work is never called Live Proof.

**Website.**
- Scaffold: repo builds; `dist/` exists. (Nothing is claimed.)
- Partial: pages exist with copy from briefs; some gates red.
- Local Proof: `gates:local` green on `dist/`; claims ledger complete and every claim verified; design plan reviewed against defaults; examples tests green; drafts excluded.
- Live Proof: preview URL deployed; `gates:preview` green including Lighthouse on mobile and desktop, axe, links, meta, RSS, search; 64-screenshot matrix graded by the visual grader with no open gaps; claims auditor report clean; docs smoke test passed by a fresh agent.
- Operational: production URL serves the tested version (build stamp matches); custom domain resolves with a valid certificate; analytics beacon receiving; `robots.txt` and sitemap fetched by at least one crawler or submitted; first field CWV p75 recorded when available.
- Done: all of the above agree in `.drive/STATE.md`, `site/DECISIONS.md` records the stack and any deviations, and no branch, worktree or scratch file remains.

**Dashboard.**
- Local Proof: metrics registry complete with sampled unit checks; data-correctness fixtures (timezone, DST, week, empty, zero-denominator, average-of-averages, partial bucket, tenant) green; four states rendered; access-control tests green; palette validated; existing tests still green.
- Live Proof: deployed to the product's staging or preview environment (whatever the product already has); verified with a real account of each role; performance measured at seeded volume; screenshots graded against an existing screen.
- Operational: behind the product's feature flag or released; first real-data numbers spot-checked against an independent query on production data (read-only) and recorded.
- Done: STATE, tests, code and docs (a short page in the product's docs describing each metric's definition, in the registry's words) all agree.

### 4.11 State files for this pack

`.drive/STATE.md` gains a section:

```markdown
## Web pack
Stack: astro 7.3.2, starlight 0.42.0, wrangler 4.131.1 (pinned). Decision: site/DECISIONS.md#stack.
Preview: https://drive-example-site.<sub>.workers.dev  (version 0a1b…)  Production: https://www.example.com (x-build 3f9c2e1)
Gates (preview, 2026-09-14 11:02Z): lighthouse m/d 98/100 · 100/100 · 96/100 · 100/100; axe 0; links 0/412; meta ok; rss 7/7; search ok
Claims: 14 verified, 0 expired, 0 unmarked sentences. Auditor: .drive/gate-results/claims-2026-09-14.md
Visual: 64/64 screenshots, 0 open gaps. Grader: .drive/gate-results/visual-2026-09-14.md
Docs smoke: passed (agent docs-smoke-tester, 2026-09-14). Open docs bugs: none.
Imagery: 9 images, $0.87.
Next: none. Status: Live Proof → Operational pending first field CWV.
```

## 5. Conditionals by project shape

**Greenfield app (fashion iOS app, Cloudflare backend).** The website is not the product and should not compete with it for budget. Ship a reduced pack: one landing page, a privacy policy page and a support page (App Store Connect requires a privacy policy URL and a support URL for submission; source claim from Apple's submission requirements, verify at the time), no blog, docs only if there is a public API. Design direction is shared with the app: the design plan for the site derives from the app's tokens, not the other way round. All gates still run; the matrix shrinks to three pages.

**Deep bug hunt.** Pack skipped unless the bug is in a website or dashboard, in which case only the relevant sub-section applies (usually the data-correctness fixtures for a dashboard bug, or the screenshot matrix for a layout bug).

**Feature on existing product ("add this dashboard").** Section 4.9 in full. Sections 4.4 through 4.8 do not apply except the palette validator and the four-state rule. The design direction step is replaced by archaeology. If the product has public docs, add a page describing the dashboard's metrics in the registry's words; that page follows 4.6's style rules.

**Migration / consolidation (AI gateway into core platform).** No marketing work. Docs only: a reference page for the new service generated from its contract (OpenAPI or the route table), a migration guide (how-to) for internal callers, an architecture decision record (explanation). Tested code samples for the new call pattern. Run the docs smoke test on the migration guide with a fresh agent. The gateway's own admin or observability screens count as dashboards and get the data-correctness fixtures, especially if they show cost or latency aggregates across timezones.

**Research + website (the worked shape).** Everything in section 4. Order: market map and positioning first (deep-research), then claims ledger, then site map and briefs, then design plan, then scaffold and tokens, then docs IA and examples, then copy, then build, then gates, then preview deploy, then grading, then production. Do not scaffold before positioning exists; a scaffold invites filler.

**Library or SDK.** Docs-heavy variant: reference generated from source (TypeDoc, rustdoc, or the language's equivalent) is mandatory, tutorials tested as `examples/`, a versioning decision recorded (defer until a second supported major), a minimal marketing home that is mostly the tutorial's first result. Blog optional; changelog mandatory and generated from releases.

**CLI tool.** Same as library with the shell-transcript pattern from 4.6: documented commands run in a clean directory and their output diffed against the docs at build.

**Pure research report, ops or incident, refactor.** Pack skipped. If an incident postmortem is to be published as a blog post, the `writing` skill's story-map stage applies and the claims ledger applies to any number in it.

**Data pipeline.** No site; but any monitoring view it exposes is a dashboard and gets the timezone and aggregation fixtures. Pipelines are where "the dashboard lies" is most common because bucket boundaries and late data are the pipeline's whole problem.

## 6. Model and effort assignment

| Role | Model / effort | Tools | Isolation | Notes |
|---|---|---|---|---|
| Market map and competitor claims | `deep-research` skill as it routes (Fable orchestrates in that skill) | web | none | Output is quoted, cited, dated |
| Positioning and messaging pillars | opus / high | Read, Write | none | Judgment about audience and category; one agent, not a fan-out |
| Page briefs | opus / medium | Read, Write | none | Short documents, but they set every downstream constraint |
| Copy drafting | opus / high with `writing` skill preloaded | Read, Write | none | Prose quality is the deliverable; Sonnet drafts read templated |
| Copy revision (six substitutions) | opus / medium, a different agent than the drafter | Read, Write | none | Fresh context on purpose |
| Design plan and defaults review | opus / high with `frontend-design` preloaded | Read, Write | none | Taste; the one place the pack spends on boldness |
| Tokens and layout system | opus / medium | Read, Write, Edit, Bash | none | Structural CSS that everything derives from |
| Page implementation (fan-out) | sonnet / medium | Read, Write, Edit, Bash | none (single repo, disjoint files) | Given plan, tokens and a brief per page; one agent per page |
| Docs writing (how-to, reference) | sonnet / medium with `google-dev-docs-style` preloaded | Read, Write, Bash | none | Mechanical style with a checklist |
| Docs explanation pieces | opus / medium with `google-dev-docs-style` | Read, Write | none | Requires understanding the system |
| Code samples and their tests | sonnet / medium | Read, Write, Bash | none | Must run, not look right |
| Gate running | orchestrator's own Bash, not an agent | Bash | none | Scripts, deterministic; summarise from JSON output |
| Claims auditor | sonnet / medium, predefined agent, read-only | Read, Grep, Glob, Bash, WebFetch | none | Judgment on "does the evidence support the sentence"; low effort misses hedged overclaims |
| Visual grader | opus / medium, predefined agent, read-only | Read, Glob, Bash | none | Taste plus the rubric; Sonnet accepts defaults it should reject |
| Docs smoke tester | sonnet / medium, predefined agent, fresh context | Bash, Read, WebFetch | clean temp dir (not a worktree) | Must know nothing but the docs |
| Dashboard archaeology | opus / high | Read, Grep, Glob, Bash | none | Wrong archaeology poisons everything after |
| Metrics registry and correctness fixtures | opus / high, then `severe-testing` skill for the adversarial pass | Read, Write, Edit, Bash | none | The owner's highest-value bug class |
| Dashboard implementation | sonnet / medium | Read, Write, Edit, Bash | none | Given registry, tokens, exemplar screen |
| Access-control tests | opus / medium via `severe-testing` | Read, Write, Bash | none | Adversarial by nature |

Predefined subagents for `~/.claude/agents/` (three; everything else is an inline `Agent` call with a model parameter).

```markdown
---
name: web-claims-auditor
description: Read-only auditor that checks every claim on a built website against the claims ledger and its evidence files. Use after copy is written and again on the deployed preview, before any deploy to production. Reports unsupported, overstated, expired and unmarked claims.
model: sonnet
effort: medium
tools: Read, Grep, Glob, Bash, WebFetch
disallowedTools: Write, Edit
---
You audit a website's claims. You receive: the path to the built site (dist/ or a preview URL), the claims ledger (claims.yaml), the positioning document, and the evidence directory. You did not write the copy and you must not repair it.

For every page: extract each sentence that contains a number with a unit or percent, a multiplier, a comparative or superlative, a compliance or security term, a customer or partner name, or a statement about what the product does. For each, find the claim id it is marked with. If unmarked, report it. If marked, open the evidence and decide whether the evidence supports the sentence as written, at the strength written. "Under 40 ms" is not supported by a p95 of 40 ms; "trusted by teams at X" is not supported by one user at X; "SOC 2" is not supported by "in progress". Roadmap claims must appear only on roadmap or changelog pages and be phrased as future. Check the verified date against expiry.

Report as a table: page, sentence, claim id or UNMARKED, verdict (supported / overstated / unsupported / expired / misplaced), what the evidence actually says, and the minimal truthful rewrite if one exists. Then a one-line summary count. Do not soften verdicts. Do not invent evidence. If the evidence file is missing, the verdict is unsupported.
```

```markdown
---
name: web-visual-grader
description: Grades screenshots of a deployed site or dashboard against the design plan (or, for dashboards, against an existing product screen) and returns a structured gap list. Never sees the maker's reasoning. Use after the screenshot matrix is captured from the preview URL.
model: opus
effort: medium
tools: Read, Glob, Bash
disallowedTools: Write, Edit
---
You grade visual work from screenshots alone. You receive a directory of screenshots named <viewport>-<scheme><path>.png, the design plan (design/plan.md) or, for a dashboard, a directory of screenshots of an existing product screen, and the page briefs. Read every screenshot; do not sample.

For a website, for each screenshot answer: Does the hero say the page's job in the brief's words? Is the plan's signature element present and legible? Does anything match the known default looks (cream background with serif display and terracotta accent; near-black with a single acid-green or vermilion accent; broadsheet hairlines with zero radius) or use Inter, Roboto, Arial or Fraunces as display? At phone width, is any text visibly under 16 px, is there a horizontal scrollbar, is anything clipped or overlapping? Do light and dark both look designed (no light-only images on dark, no unreadable contrast)? Is the focus ring visible in the post-Tab screenshot? Does the 404 page look like the site? Are there placeholder-looking images (stock-photo humans, generic abstract gradients)?

For a dashboard, the question is consistency with the existing screen: same spacing, radii, type sizes, control heights, card anatomy, chart chrome; no colour that does not appear in the existing screen; all four states (loading, empty, error, data) present and in the product's voice; one axis per chart; a legend where there are two or more series; filters in one row above.

Output: a list of gaps, each with screenshot filename, what is wrong, why it fails the plan or the exemplar, and a concrete instruction to the maker. Then "PASS" only if the list is empty. You are not asked to be kind and you are not asked to redesign.
```

```markdown
---
name: docs-smoke-tester
description: Follows a published tutorial or how-to literally in a clean directory using only the published docs, and reports every step where it had to guess, where a command or output differed, or where a prerequisite was missing. Use before calling a docs section done.
model: sonnet
effort: medium
tools: Bash, Read, WebFetch
disallowedTools: Write, Edit
memory: none
---
You are a new user. You receive one URL (the tutorial on the preview site) and an empty working directory. You may read only the published docs at that site; you may not read the repository, the source code, or any notes. Follow the page from top to bottom, running each command exactly as written. After each step, compare what happened to what the docs said would happen.

Report every discrepancy: a command that failed, output that differed materially, a step that assumed something not stated earlier (an installed tool, an environment variable, an account), a link that did not resolve, a term used before it was defined, a place where you had to choose between two readings. Quote the docs text and paste the actual output. End with: completed the tutorial YES/NO, and the count of discrepancies. Do not fix anything. Do not consult outside sources to get unstuck; getting stuck is the finding.
```

## 7. Failure modes and anti-patterns

**Lorem ipsum and its cousins shipped.** Bracketed placeholders, "Welcome to our website", "Your Company", "John Doe", stock team grids, a pricing page with `[YOUR PRICE]`. Cause: scaffolding before positioning; the model fills structure with filler. Prevention: no scaffold until briefs exist; the placeholder grep in `gates:local`; a page with a missing fact is removed from the site map rather than bracketed.

**Claims invented or inflated.** "Fastest", "trusted by thousands", "enterprise-grade security", a latency number nobody measured, a competitor's claim echoed as our own. Cause: marketing copy has a genre and the model reproduces the genre. Prevention: the claims ledger, the `<Claim>` marker, the claims lint, and an auditor who did not write the copy. The auditor's verdict "overstated" is the common one; "under 40 ms" from a p95 of 40 ms is the typical shape.

**Single-breakpoint, single-scheme verification.** One desktop screenshot in light mode, declared beautiful. Prevention: the 64-screenshot matrix is the minimum; the grader must read all of them; the skill counts files before grading.

**Screenshots of localhost.** Fonts, headers, caching, CSP and the search index differ on the edge. Prevention: the matrix and the gates run against the preview URL; local runs are a fast pre-check only.

**Search that works in dev and not in production, or the reverse.** Pagefind has no index under `astro dev`; a site built without the Pagefind step has a search box that returns nothing. Prevention: the Playwright search test on the preview.

**Docs that describe intent, not behaviour.** Written from the design doc before the code settled, or from the code as the author imagined it. Prevention: samples imported from tested files; shell transcripts captured by running; the docs smoke tester with no access to the repository.

**Dashboards that lie.** Day buckets in UTC labelled as local days; weeks starting on the wrong day; averages of averages; cents shown as dollars; the partial "today" bucket drawn as a cliff; a line interpolated through an empty bucket; a ratio dividing by zero; a dual-axis chart inventing a correlation. Prevention: the metrics registry, the fixture list in 4.9, one axis per chart, and a `severe-testing` pass whose brief is "make this number wrong".

**Kinder-than-production shims.** A mock API with unbounded pages, no latency, no auth, no tenant predicate. Prevention: ask of every test double where it is kinder than the real thing and make it match; run performance at seeded volume; run access tests against the real authorization layer.

**Mirage completion.** "Deployed" because `wrangler deploy` printed a URL; "gates green" because they ran on `dist/`; "Live Proof" without a production check. Prevention: the build stamp check on the production URL; the ladder's rule that Live Proof requires the preview gates and Operational requires the production stamp; STATE lines that quote gate output rather than summarise it.

**Design defaults presented as choices.** The cream/serif/terracotta site, the near-black acid-green site, Inter everywhere. Prevention: the plan must name the default it rejected; the grader checks for the three looks by name.

**Generated people.** A hero with AI-rendered humans, or worse, a generated "team". Prevention: `imagegen` never for people; team page only from supplied data; grader flags stock-looking humans.

**Consent theatre.** A cookie banner on a site that sets no cookies, or GA loaded before consent behind a banner. Prevention: cookieless analytics by default; if cookies are required, a test that the script does not load before consent.

**Version churn.** Starlight is beta and Astro moves majors yearly; an unpinned install breaks the build in six months. Prevention: exact pins; upgrades as a deliberate task with the full gate run.

**The dangling `writing` symlink.** `~/.claude/skills/writing` points at a path removed in the v2 cutover; the plugin copy at `~/.claude/plugins/cache/arcwell-local/arcwell/2.0.0/skills/writing/SKILL.md` is what actually loads as `arcwell:writing`. Repoint the symlink to `~/Projects/arcwell/plugins/arcwell/skills/writing` so the canonical checkout is what loads.

## 8. Open questions and trade-offs

**One Astro project or two.** The nested-directory mount for Starlight is documented as a limitation rather than a feature, and a future Starlight may change it. One project keeps tokens, deploy and gates in one place, which is worth the awkward path. Recommendation: one project; verify the route table at scaffold; record the fallback.

**Whether to open the design canvas at all.** It exists to let a human tweak, and this owner will not be watching. Recommendation: off by default; on only when the goal asks for options or a third party must approve. The design plan document is the artifact.

**Lighthouse performance threshold.** 0.9 is the green band; a static Astro site should score 98-100, so 0.9 hides regressions. Recommendation: error at 0.95 on median of three runs, and record the raw numbers so drift is visible.

**Next.js when the marketing site must share components with a Next product.** Sharing tokens is cheap and sharing components is expensive; the marketing site rarely needs the product's components. Recommendation: still Astro; share `tokens.css` as a package if both repos need it.

**Docs versioning timing.** Versioning early costs maintenance and the only Starlight option is early-development. Recommendation: defer until a second supported major exists; use changelog and "added in" asides.

**Analytics consent.** Legal positions differ by jurisdiction and lawyer. Recommendation: cookieless Cloudflare Web Analytics and no banner, with the reasoning recorded; escalate as one question only if a stakeholder requires cookie-based tooling.

**Workers Builds versus direct wrangler.** Builds gives PR previews with no effort but is a scheduler the skill would wait on. Recommendation: the skill deploys directly; Builds may be connected for humans' PRs with `wrangler versions upload` as its command.

**HTML validity: html-validate alone or also the Nu checker.** The Nu checker needs Java and is the reference implementation; html-validate is stricter in some places and configurable. Recommendation: html-validate in the gate; Nu checker once at Live Proof if Java is present.

**Screenshot count.** 64 is heavy per iteration. Recommendation: the full matrix at Live Proof and on any CSS change; a reduced matrix (phone dark, laptop light) during page iteration.

## 9. Skill text candidates

For `references/web.md` unless marked for SKILL.md.

1. (SKILL.md, shape router) If the goal includes a website, landing page, docs site or blog, load `references/web.md`. If it includes a dashboard, report or analytics view inside an existing product, load the dashboard section of `references/web.md` and skip the design-direction step in favour of archaeology.

2. Do not scaffold a site before the positioning document, the claims ledger and a brief for every page exist. A scaffold without briefs invites filler, and filler ships.

3. Every sentence on a marketing page that contains a number, a multiplier, a comparative, a superlative, a compliance term or a customer name must be wrapped in a claim marker whose id exists in the claims ledger, is verified and has not expired. The build fails otherwise. A missing fact means the sentence is removed, not bracketed.

4. Choose Astro with content collections for marketing and blog and Starlight mounted under `/docs` in the same project, built to static HTML and deployed as an assets-only Cloudflare Worker. Pin exact versions. Use Next.js only when the site is the product application; use plain HTML only for a single page. Record the decision and the condition that would change it.

5. Deploy in this order: build, local gates on `dist/`, `wrangler versions upload --preview-alias drive`, full gates against the preview URL, screenshot matrix and graders against the preview URL, promote the tested version, then prove the production URL serves this build by reading the build stamp in its HTML. Never wait for a hosted build pipeline to do this for you.

6. Before writing CSS, load `frontend-design` and write a design plan: four to six named colours, a display and a body face, a layout concept, one signature element grounded in the subject. Then write down the default you would have produced for any site of this kind and show where the plan differs. Reject the three known default looks and the overused display faces unless the brief asked for them.

7. Open a design canvas only when the goal asks for mockups or options, or when someone other than the owner must approve a direction. Otherwise the design plan is the artifact and the site is the deliverable. Never wait for anyone to open the canvas.

8. Verification means screenshots of the deployed preview at four widths (360, 768, 1280, 1600) in light and dark, for every key page plus the 404 page, with reduced motion on and a post-Tab shot for focus. A separate grader reads all of them against the design plan and returns gaps. One screenshot proves one viewport.

9. Generate illustrations with `imagegen` at low quality in threes, choose by the plan, regenerate the winner at medium or high, as WebP, sized to at most twice its rendered size. Never generate people, product screenshots or anyone else's logo. Every image has real alt text or `alt=""`, explicit dimensions, and lazy loading below the fold.

10. Write marketing and blog prose under the `writing` skill, with the positioning document, the ledger and the page brief as the source; do not improve the facts. Write docs under `google-dev-docs-style` and run its review checklist. Do not mix the two; reference material is impersonal on purpose.

11. Docs follow four groups: a tested tutorial, task how-tos titled with a verb, reference generated from the source of truth where possible, and explanation. Code samples are files under `examples/` with their own tests, imported into pages; a sample that stops compiling fails the site build. Before calling docs done, a fresh agent with no repository access follows the tutorial on the preview site and reports every place it had to guess.

12. Quality gates and targets, run against the preview URL: Lighthouse performance ≥ 0.95 (median of three), accessibility 1.0, best practices ≥ 0.95, SEO 1.0, LCP ≤ 2.5 s, CLS ≤ 0.1, TBT ≤ 200 ms; zero axe violations at WCAG 2.1 AA; zero HTML validation errors; zero broken links including fragments; every page with a unique title, description, canonical and absolute OG image that exists; sitemap and robots consistent; security headers present; no placeholder text; no draft leakage; RSS parses with the right item count; search returns a known page. Use cookieless analytics and ship no consent banner unless cookies are genuinely required.

13. For a dashboard in an existing product, first write the archaeology: framework, data layer, authorization model, design tokens and the closest existing screen, timestamp column timezones and money column units. Then a metrics registry that both the queries and the labels read from. Nothing renders that is not in the registry.

14. Every dashboard metric gets fixtures whose correct value is computed independently: rows across a UTC day boundary in a non-UTC account, DST transition days, week boundaries under two locales, an empty bucket, a zero denominator, an average-of-averages trap, a partial current bucket, minor-unit money, and another tenant's rows. The displayed number equals the independent number to the displayed precision, or the work is not done.

15. Charts obey the dataviz rules: one axis; categorical colour fixed to the entity, never to rank; a stat tile for a single value; a legend for two or more series and a table twin for every chart; filters in one row above everything they scope; hold the previous render on refetch; validate the palette with the script in both modes against the product's real surface colours.

16. A dashboard is verified against the product's existing screens, not against a new aesthetic. Same tokens, same anatomy, same chart chrome, all four states present, no colour outside the palette. Access is proven by tests: unauthenticated, wrong role, and cross-tenant requests to the page and to every endpoint, with no data in refused responses. Performance is measured at seeded production-like volume, and every test double is checked for where it is kinder than production.

17. (SKILL.md, status ladder note) A site is Local Proof when gates are green on `dist/`, Live Proof when gates, screenshots and the graders are green on the preview URL, Operational when the production URL carries the tested build stamp on the custom domain with analytics receiving. Never call local gates Live Proof.
