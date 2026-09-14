# 09 · Verifying front-end layout, design quality and UX with vision

Researcher report for the `/drive` skill. Date: 2026-09-14. Scope: how the skill decides what "good UI" means before code exists, how it captures evidence from the running app (web and native iOS), which checks are cheap and deterministic, where vision is genuinely required, how an independent reviewer grades without rubber-stamping, and how the verdict flows back to the maker and into status and lessons.

Tags used below: **[verified]** means I read the live doc or ran the command today and give the URL or the output; **[local proof]** means I ran it on this Mac; **[source claim]** means a secondary source I could not confirm against a primary one; **[opinion]** is mine and argued.

---

## 1. Executive opinion

Vision review is the only check that catches "it renders, the tests pass, and it still looks wrong", and it is also the most expensive and least reliable check the skill runs. The skill should therefore treat it as the last layer over a stack of cheap deterministic checks, and it must never let the reviewer grade against its own mood. Three moves make this work.

First, write the design contract before code. For greenfield UI the skill runs the installed `frontend-design` skill's two-pass process and records the result in `DESIGN.md` (direction, palette, type scale, spacing, motion rules, state design, the one deliberate risk, and the generic default that was rejected and why), plus `design/tokens.json` for machines and `design/screens.yaml` listing every screen with its job, states, expected elements and tap budget. Verification then means comparing evidence to a document, which a second model can do repeatably. Taste review compares against the contract's own declared intent and against the skill's list of templated defaults, not against "what I would have done".

Second, capture deterministically. A drive-owned script produces the matrix (device or viewport × light/dark × default/largest text × state) into `.drive/ui/runs/<id>/` with a manifest that names the git hash and the installed bundle version, and saves the accessibility tree beside each screenshot. Objective assertions run on that evidence before any model looks at pixels: contrast from tokens, target sizes and overlaps from the tree, horizontal overflow, missing labels, console errors, axe or Lighthouse on web, `performAccessibilityAudit` on iOS. Vision is reserved for what these cannot see: hierarchy, alignment, fidelity to the contract, whether the result looks templated, and whether the flow makes sense to a new user.

Third, grade independently and structurally. A predefined `ui-reviewer` subagent on Opus at high effort captures the evidence itself, must record at least five concrete observations per screen variant and name the worst element on every screen, and returns findings in a fixed JSON shape with severity, evidence crop and suggested fix. The maker answers every finding; three rounds at most; acceptance means zero blocking or major findings, objective checks green, and every regression diff explained. "Looks fine" is not a verdict, and neither is a verdict on a build whose hash does not match HEAD.

---

## 2. What the post says, and a critique

Step 13 of the post ("Self-verification via vision") says: the maker subagent writes UI code and renders a screenshot; a verifier subagent reads it with vision and compares against the goal description, the design tokens "in the project Skill", and "the previous screenshot from STATE.md"; match means complete, mismatch means a structured diff handed back to the maker. Step 01 lists "uses vision to check outputs against goals" among the things Fable 5 unlocks, and the closing list names "no vision-verify on visual tasks" as a mistake.

Where it is right. The shape is correct and worth keeping: a maker who does not grade its own pixels, a verifier that compares against something written down, and a structured diff rather than prose back to the maker. The three reference points it names (goal, tokens, previous screenshot) are the right three, and the emphasis on an independent context for the grader matches the strongest available source: Lance Martin's public article "Designing loops with Fable 5", which states that "a verifier sub-agent tends to outperform self-critique with Fable 5, because grading is done in an independent context window" and that the grader should be given only the rubric and the artifact, not the history of how it was made **[source claim; the article states the author works at Anthropic; it is not on anthropic.com/engineering, whose index today lists no article on the subject]**.

Where it is thin. It never says what a token is or where it lives, how many viewports or appearances to capture, how to reach the empty, loading, error and offline states, how the verifier knows the screenshot came from the build under test, what "match" means, how many rounds to run, or how to stop the verifier from agreeing with itself. Every one of those gaps is where real UI verification fails, and this report is mostly about filling them.

Where it is wrong or misleading. Vision as a capability is not a Fable 5 unlock: the models overview states that all current models "support text and image input" **[verified]**. What the Fable 5.1 prompting guide actually claims is narrower and more useful: the model "has better vision capabilities out of the box" and does its best work when it "can iteratively analyze, crop, and visually verify what it sees", so give it a crop tool **[verified]**. Design tokens do not belong "in the project Skill"; a skill is procedural memory across projects, while tokens are a property of one codebase and must live beside the code where the maker reads them and the linter can check them. STATE.md does not hold a "previous screenshot"; it holds a path and a hash, and the pixels live in an evidence directory. Haiku as the grader (step 04) is wrong for UI: grading a screen is judgment work, and the owner excludes Haiku anyway. Finally, calling vision checks a "self-improvement layer" confuses verification with learning: a screenshot review makes this build better; only the distilled rule ("fixed-height rows clip at accessibility text sizes; let rows grow") makes the next build better, and that belongs to the lessons component, fed by this one.

---

## 3. Verified facts

Harness and models

1. Subagent frontmatter fields: `name`, `description`, `model` (`sonnet`, `opus`, `haiku`, `fable`, full ID, or `inherit`), `tools`, `disallowedTools`, `permissionMode`, `maxTurns`, `skills` (full content injected at startup), `memory` (`user`, `project`, `local`), `background`, `effort` (`low`…`max`), `isolation: worktree`, `mcpServers`, `hooks`, `color`, `initialPrompt`, `experimental.cacheTtl`. A `tools` list that omits Edit and Write yields an agent that "can't edit files, write files"; `disallowedTools: Write, Edit` is the inverse form. Subagents lose `Agent` at the depth limit, `AskUserQuestion`, `Workflow` and a few others regardless of the list. Results return to the parent as text; there is no documented size limit, only a warning about context consumption. **[verified]** https://code.claude.com/docs/en/sub-agents
2. Model resolution order per the same page: per-invocation `model` parameter, then the definition's frontmatter (`inherit` selects the parent's model), then `CLAUDE_CODE_SUBAGENT_MODEL`, then the main conversation's model. The brief lists the environment variable first; the docs today put it third. **[verified]** https://code.claude.com/docs/en/sub-agents and https://code.claude.com/docs/en/model-config
3. Aliases today on the Anthropic API: `opus` → Opus 5, `sonnet` → Sonnet 5, `fable` → Fable 5.1 (unless `ANTHROPIC_DEFAULT_FABLE_MODEL` is set). Effort levels `low`, `medium`, `high`, `xhigh`, `max` are supported on Fable 5.1, Fable 5, Opus 5, Sonnet 5, Opus 4.8 and Opus 4.7. `effort` in subagent frontmatter overrides the session level. **[verified]** https://code.claude.com/docs/en/model-config. Note for the coordinator: the brief speaks of Opus 4.8 and Sonnet 4.8; the docs list Opus 5 (released 2026-07-24) and Sonnet 5 (2026-06-30) as current and Opus 4.8 as legacy, and there is no Sonnet 4.8 in the table. Use the aliases, not version numbers.
4. Pricing per million tokens: Fable 5.1 $10 in / $50 out; Opus 5 $5 / $25; Sonnet 5 $2 / $10; Haiku 4.5 $1 / $5. All four take "Text and images → text". **[verified]** https://platform.claude.com/docs/en/about-claude/models/overview
5. Vision mechanics: images are read in 28×28 px patches; cost is ⌈w/28⌉ × ⌈h/28⌉ visual tokens. Claude 4.7 and later models are on the high-resolution tier (max long edge 2576 px, max 4784 visual tokens); older models downscale to 1568 px. Maximum 8000×8000 px and 10 MB per image. If a request carries more than 20 image blocks, including images from earlier turns and images inside tool results, a stricter per-image limit applies and oversized images are rejected; resizing so that neither edge exceeds 2000 px avoids it. The docs list "screenshot understanding" among the cases that benefit from the higher fidelity. Stated limitations: coordinates and localization are approximate, small images under 200 px and small text are error-prone, counting is approximate. Images placed before text perform best. **[verified]** https://platform.claude.com/docs/en/build-with-claude/vision
6. Fable 5.1 prompting guide, section "Give vision work tools to crop and zoom": on dense visual inputs the model "does its best work when it can iteratively analyze, crop, and visually verify what it sees"; "an image-cropping tool alone delivers most of the uplift". Also: tools that return base64 into context can trigger safeguard false positives; pass file paths instead. **[verified]** https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1
7. There is no official per-model vision benchmark comparison in the docs. Third-party pages quote MMMU-style numbers for various models, but they are not comparable across versions and I do not rely on them. **[verified absence]**

Web tooling

8. Playwright MCP (`npx @playwright/mcp@latest`, which is exactly how it is configured in `~/.claude.json` here): flags `--device "iPhone 15"`, `--mobile`, `--viewport-size 1280x720`, `--user-agent`, `--storage-state`, `--output-dir`, `--headless`, `--config <path>`, `--caps vision,pdf,devtools`, `--image-responses allow|omit`. The config file accepts `browser.contextOptions` (any Playwright `BrowserContextOptions`, so `colorScheme`, `reducedMotion`, `forcedColors`, `locale`) and `snapshot.boxes`. Tools include `browser_take_screenshot` (`fullPage`, `type`, `filename`, `scale: css|device`, element target), `browser_snapshot` (`boxes: true` adds `[box=x,y,w,h]` per element in CSS px), `browser_resize`, `browser_verify_element_visible`, `browser_verify_text_visible`, `browser_verify_list_visible`, `browser_verify_value`, and with `--caps=devtools` `browser_start_video`/`browser_stop_video` and tracing. `browser_run_code_unsafe` runs a function that receives the Playwright `page`, so `page.emulateMedia({ colorScheme: 'dark', reducedMotion: 'reduce' })` is reachable from the MCP. **[verified]** https://raw.githubusercontent.com/microsoft/playwright-mcp/main/README.md and the tool schemas loaded in this session.
9. Chrome DevTools MCP (configured here through `~/.local/bin/chrome-devtools-mcp-launcher`, which starts Chrome with an attach profile under `~/.cache/chrome-devtools-mcp/attach-profile` on port 9222): `emulate` takes `colorScheme dark|light|auto`, `viewport '<w>x<h>x<dpr>[,mobile][,touch][,landscape]'`, `networkConditions Offline|Slow 3G|Fast 3G|Slow 4G|Fast 4G`, `cpuThrottlingRate`, `userAgent`, `geolocation`; there is no reduced-motion or forced-colors emulation. `take_screenshot` (`fullPage`, `filePath`, element `uid`), `take_snapshot` (a11y tree with uids, `verbose`), `resize_page`, `lighthouse_audit` (accessibility, SEO, best practices, agentic browsing; "excludes performance"; `device desktop|mobile`; `mode navigation|snapshot`), `performance_start_trace`/`performance_stop_trace`, `list_console_messages`, `list_network_requests`, `evaluate_script`. **[verified]** local schemas and https://raw.githubusercontent.com/ChromeDevTools/chrome-devtools-mcp/main/docs/tool-reference.md
10. Playwright emulation API: `devices['iPhone 13']` descriptors, `viewport`, `colorScheme: 'dark'`, `page.emulateMedia({ reducedMotion: 'reduce' })`, `forcedColors`, `locale`, `timezoneId`, `offline: true`. **[verified]** https://playwright.dev/docs/emulation
11. Installed Playwright here is the Python package 1.60.0 (`~/.local/bin/playwright` is a pyenv shim; Chromium builds are cached under `~/Library/Caches/ms-playwright`). `playwright screenshot` supports `--device`, `--color-scheme light|dark`, `--full-page`, `--viewport-size "1280, 720"`, `--lang`, `--timezone`, `--wait-for-selector`, `--wait-for-timeout`, `--load-storage`, `--browser wk|ff|cr`; it has no reduced-motion flag. **[local proof]** `~/.local/bin/playwright screenshot --help`
12. A Python capture with `p.devices["iPhone 15"]`, `color_scheme="dark"`, `reduced_motion="reduce"` ran headless here and the page reported `prefers-color-scheme: dark` true and `prefers-reduced-motion: reduce` true; the full-page PNG was 2940×4932 (DPR 3). A page without a `<meta name="viewport">` laid out at 980 CSS px wide under phone emulation, which is exactly the "zoomed-out phone page" a reviewer must recognise as a bug rather than a rendering quirk. `Locator.aria_snapshot()` exists and returned a YAML tree (`- button "tiny": x`); `getBoundingClientRect` gave target sizes; `scrollWidth > innerWidth` flagged horizontal overflow. **[local proof]** scratchpad `cap.py`
13. axe with Playwright: `npm install @axe-core/playwright`; `new AxeBuilder({ page }).withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa']).analyze()`; `violations[].id` and `nodes[].target`. The docs state that "many accessibility problems can only be discovered through manual testing". **[verified]** https://playwright.dev/docs/accessibility-testing
14. Playwright visual comparison: `expect(page).toHaveScreenshot()` writes a baseline on first run, names files with browser and platform suffix, `--update-snapshots` refreshes, options `maxDiffPixels`, `maxDiffPixelRatio`, `threshold`, `animations: 'disabled'`, `caret: 'hide'`, `mask`, `fullPage`, `stylePath`; rendering varies by OS, headless mode and even power source, so baselines must be generated in the environment that checks them. **[verified]** https://playwright.dev/docs/test-snapshots
15. Lighthouse accessibility score is a weighted average of pass/fail axe-derived audits (button names, image alt, ARIA values and form labels weigh 10; colour contrast weighs 7); manual audits do not affect the score and the page lists nine manual checks that remain necessary. **[verified]** https://developer.chrome.com/docs/lighthouse/accessibility/scoring
16. WCAG 2.2: 2.5.8 Target Size (Minimum), level AA, 24×24 CSS px with spacing, equivalent, inline, user-agent and essential exceptions; 2.5.5 Target Size (Enhanced) is 44×44 at AAA. 1.4.3 Contrast (Minimum): 4.5:1 for normal text, 3:1 for large text (18 pt, or 14 pt bold; roughly 24 px / 18.5 px), with exceptions for inactive, decorative and logotype text. **[verified]** https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html and https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
17. The Vercel Web Interface Guidelines file that the installed `web-design-guidelines` skill fetches is a rule list grouped as Accessibility, Focus States, Forms, Animation, Typography, Images, Performance, Touch & Interaction, Dark Mode & Theming, Locale & i18n, with an output format of `file:line - issue` and no severity levels; the skill reads source files, not screenshots, and asks for a file pattern. **[verified]** https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md and `~/.claude/skills/web-design-guidelines/SKILL.md`
18. Nielsen's ten heuristics, by their current names: visibility of system status; match between system and the real world; user control and freedom; consistency and standards; error prevention; recognition rather than recall; flexibility and efficiency of use; aesthetic and minimalist design; help users recognize, diagnose, and recover from errors; help and documentation. **[verified]** https://www.nngroup.com/articles/ten-usability-heuristics/

Apple platform

19. HIG Accessibility: iOS and iPadOS controls default to 44×44 pt with a 28×28 pt minimum; about 12 pt of padding around bezelled elements and 24 pt around unbezelled ones; default text 17 pt, minimum 11 pt; give people the option to enlarge text by at least 200 percent; Accessibility Inspector uses WCAG AA values (4.5:1 up to 17 pt, 3:1 at 18 pt or bold); with Reduce Motion on, reduce zooming, scaling and peripheral motion and replace axis transitions with fades. **[verified]** https://developer.apple.com/design/human-interface-guidelines/accessibility (read through Apple's data endpoint `developer.apple.com/tutorials/data/design/human-interface-guidelines/accessibility.json`)
20. HIG Typography, Large (default) sizes: Large Title 34/41, Title 1 28/34, Title 2 22/28, Title 3 20/25, Headline 17/22 semibold, Body 17/22, Callout 16/21, Subhead 15/20, Footnote 13/18, Caption 1 12/16, Caption 2 11/13. Dynamic Type sizes: xSmall, Small, Medium, Large, xLarge, xxLarge, xxxLarge, then AX1 to AX5. **[verified]** https://developer.apple.com/design/human-interface-guidelines/typography
21. HIG Layout: "Preview your app on multiple devices, using different size classes, localizations, and text sizes… first testing versions of your experience that use the largest and the smallest layouts"; support Dynamic Type by letting horizontally adjacent views stack and rows grow "so that text isn't cropped or doesn't overlap other content"; the safe area is what hardware features and system bars do not cover. **[verified]** https://developer.apple.com/design/human-interface-guidelines/layout
22. HIG Dark Mode: "Ensure that your app looks good in both appearance modes"; test with Increase Contrast and Reduce Transparency on, separately and together; minimum 4.5:1 and "strive for a contrast ratio of 7:1" for custom colours in small text; iOS backgrounds move from base to elevated in sheets and popovers. **[verified]** https://developer.apple.com/design/human-interface-guidelines/dark-mode
23. HIG Right to Left: flip progress and navigation controls, flip icons that show reading direction or forward motion, do not flip logos, checkmarks, clocks, photos or the digits inside a number. **[verified]** https://developer.apple.com/design/human-interface-guidelines/right-to-left
24. `xcrun simctl` here (Xcode 27.0 build 27A5209h; iOS 26.4 runtimes; booted: iPhone 17 Pro and iPad Pro 11-inch (M5)): `ui <udid> appearance light|dark`; `ui <udid> content_size <extra-small … extra-extra-extra-large | accessibility-medium … accessibility-extra-extra-extra-large | increment | decrement>`; `ui <udid> increase_contrast enabled|disabled`; `io <udid> screenshot [--type=png|jpeg|…] [--mask=ignored|alpha|black] <file>`; `io <udid> recordVideo [--codec=h264|hevc] <file>` (stop with SIGINT); `status_bar <udid> override --time 9:41 --batteryLevel 100 --batteryState charged --dataNetwork wifi --wifiBars 3 --cellularBars 4 --operatorName ''` and `status_bar <udid> clear`; `launch [--terminate-running-process] <udid> <bundle> [argv…]` with environment via `SIMCTL_CHILD_*`; `appinfo <udid> <bundle>` prints `CFBundleVersion`, `CFBundleShortVersionString`, `Bundle` path and `DataContainer`. I set AX5 and dark, read them back, and restored `large` and `light`. **[local proof]**
25. `xcrun simctl io booted screenshot` with two booted devices silently chose the iPad (1668×2420) while the iPhone by UDID gave 1206×2622. Always pass the UDID. `xcrun simctl list devices booted -j | jq -r '.devices[][] | select(.state=="Booted") | "\(.name)\t\(.udid)"'` lists them (jq is installed). **[local proof]**
26. The Claude Code iOS Simulator MCP (`control` with `attach`, `launch`, `screenshot`, `inspect`, `tap`, `swipe`, `touch_path`, `text`, `button`, `open_url`; `build` with `build_status`) is configured here, and its `inspect` returns per-element type, label, value, frame in points, traits, children, omits hidden and off-screen elements, and cannot detect occlusion; a swipe starting within 4 pt of a screen edge becomes the OS edge gesture. Today every action (`attach`, `screenshot`, `inspect`) failed with "Xcode is installed but not selected. Run `sudo xcode-select -s /Applications/Xcode.app/Contents/Developer`", even though `xcode-select -p` in my shell already prints that path (two Xcodes are installed: `Xcode.app` and `Xcode-26.app`). The owner must run that command (it needs sudo); until then only `simctl` works. **[local proof]**
27. `XCUIApplication.performAccessibilityAudit` (Xcode 15, iOS 17 and later) audits the current screen "just as the Inspector does" and fails the test on any issue with no assertions; it takes an audit-type set and an issue handler that returns true to ignore an issue. **[verified]** WWDC23 session 10035 transcript, https://developer.apple.com/videos/play/wwdc2023/10035/. The seven audit types `contrast`, `dynamicType`, `elementDetection`, `hitRegion`, `sufficientElementDescription`, `textClipped`, `trait` come from secondary write-ups (createwithswift.com, polpiella.dev, augmentedcode.io); Apple's reference page did not load through the data endpoint today. **[source claim]**
28. Forcing right-to-left in the simulator: launch arguments `-AppleLanguages (ar) -AppleLocale ar_SA -AppleTextDirection YES -NSForceRightToLeftWritingDirection YES`, the same arguments XCUITest uses via `launchArguments`. **[source claim]** Apple Developer Forums thread 726456 and XcodeBuildMCP docs.
29. Point-Free `swift-snapshot-testing` renders SwiftUI/UIKit views to images with trait overrides (`preferredContentSizeCategory`, `userInterfaceStyle`); its device presets hard-code `layoutDirection: .leftToRight`, so RTL snapshots need a custom trait collection. **[source claim]** https://github.com/pointfreeco/swift-snapshot-testing and discussion #802.

Local skills and tooling

30. `~/.claude/skills/frontend-design/SKILL.md` (symlink to `~/.agents/skills/frontend-design`) prescribes: ground the design in the subject; two passes (brainstorm a compact token system of 4–6 named hex colours, 2+ type roles, a layout concept with ASCII wireframes, and one signature element; then review the plan against "the generic default you would produce for any similar page" and revise); it names the three current AI-default looks (warm cream near #F4F1EA with high-contrast serif and terracotta; near-black with one acid-green or vermilion accent; broadsheet with hairline rules and zero radius); "spend your boldness in one place"; "build to a quality floor: responsive down to mobile, visible keyboard focus, reduced motion respected"; "critique your own work as you build, taking screenshots"; and a writing section (name things by what people control, active voice, "Save changes" not "Submit", errors explain and do not apologise, empty screens invite action). The marketplace copy at `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/frontend-design/…` is a slightly different revision that adds three typographic tells: accenting a single word in a headline, all-caps labels, and unnecessary labels above content. **[verified, local files]**
31. `~/.agents/skills/design-taste-frontend/SKILL.md` and `redesign-existing-projects/SKILL.md` exist but are not linked into `~/.claude/skills`, so the Skill tool cannot load them. They contain useful tell lists (purple gradients, three equal cards, pure #000, "Acme", 99.99%) alongside dogmatic bans (Inter banned, serifs banned on dashboards, centered heroes banned) that conflict with frontend-design's "the brief's words always win". **[verified, local files]**
32. The bundled `design` skill's listing describes a multi-artboard canvas of `.dc.html` artboards published as an Artifact with view-and-export (PNG/PDF) or, where saving is enabled, in-place visual editing. Its body is not on disk (it lives inside the Claude Code binary) so I could not read its instructions. **[verified listing only]**
33. `agent-browser` 0.36.0 is installed (`/opt/homebrew/bin/agent-browser`) with `open`, `snapshot -i`, `click @ref`, `screenshot --full`, `viewport <w> <h>`, `device <name>`, `record start|stop`, `har`, `get box @ref`, `is visible @ref`, `wait --load networkidle`. Its skill exists at `~/.claude/skills/agent-browser`. **[local proof]**
34. Image tooling: Python 3.13 with PIL 12.2 and numpy 2.5 work and gave the correct pixel diff (36 changed pixels, bbox (5,5,11,11)) on a synthetic pair; ImageMagick 7.1.2-30 `compare -metric AE` reported 0 on the same pair and 24 after forcing truecolor, both wrong. Do not use `compare` for regression counts. `sips -Z 2000 in.png --out out.png` resizes on the long edge. **[local proof]**
35. `~/.claude/agents/` is empty: there is no existing agent convention to match. **[local proof]**

---

## 4. Detailed spec

### 4.1 Where this component sits

The UI track runs as five steps whenever the project shape includes a screen a person will look at.

1. Design contract (during the architecture phase, before implementation): `DESIGN.md`, `design/tokens.json`, `design/screens.yaml`. Produced by the frontend-design pass for greenfield work or by "design archaeology" (extracting what exists) for work on an existing product.
2. State harness (an implementation requirement handed to the maker): every screen reachable in every declared state from a launch argument or URL parameter in debug builds, plus a build stamp readable from outside.
3. Capture (a deterministic script, run by the reviewer, never by the maker): the matrix of screenshots and accessibility trees into an evidence directory with a manifest.
4. Checks: objective assertions first, then the vision and UX review by the `ui-reviewer` subagent, producing `findings.json` and `verdict.md`.
5. Loop and record: maker answers each finding, reviewer re-verifies, three rounds at most; the verdict updates STATUS, and recurring findings become lessons.

### 4.2 The design contract

The contract exists so that a reviewer has something explicit to hold the build against. Without it, review degenerates into the reviewer's preferences, which are as arbitrary as the maker's.

`DESIGN.md` (committed, plain language, under 300 lines):

```markdown
# Design contract · <project>

## Subject, audience, job
One paragraph: what this is, who uses it, the single job of the primary screen.

## Direction
The mood in two sentences. The one deliberate aesthetic risk and why it fits the subject.
The generic default this design rejected, and what replaced it (name the look you would
have produced for any similar brief and say what changed).

## Platform base
iOS: Apple HIG is the floor; list every place the design deliberately departs from a system
component and why. Web: Web Interface Guidelines are the floor.

## Tokens (mirror of design/tokens.json, human-readable)
Palette: 4–6 named colours with hex, light and dark values, and their roles.
Type: display face, body face, utility face; the scale; weights; where each is used.
Space: base unit and steps. Radius. Elevation/borders. Motion durations and the reduced-motion rule.

## Signature element
The one memorable thing, where it appears, and what it must never be used for.

## States
How empty, loading, error, offline and long-content states look and what they say.
Loading: skeletons or spinners, and where. Empty: what the invitation to act is.
Error: what the copy pattern is (what happened, how to fix it, no apology).

## Copy voice
Register, verb style, naming rules (control names follow the flow: "Publish" → "Published").

## Not allowed
The tells this project must not exhibit (start from the frontend-design list; add project ones).

## Decision log
Dated decisions with "why" and "what would count as a violation".
```

`design/tokens.json` (committed, machine-readable; the maker's stylesheet or Swift `DesignTokens` must be generated from it or checked against it):

```json
{
  "color": {
    "light": { "bg.base": "<hex>", "bg.elevated": "<hex>", "fg.primary": "<hex>", "fg.secondary": "<hex>", "accent": "<hex>", "danger": "<hex>" },
    "dark":  { "bg.base": "<hex>", "bg.elevated": "<hex>", "fg.primary": "<hex>", "fg.secondary": "<hex>", "accent": "<hex>", "danger": "<hex>" }
  },
  "type": {
    "display": { "family": "<face>", "weights": [600] },
    "body":    { "family": "<face>", "weights": [400, 600] },
    "scale_pt": [11, 12, 13, 15, 17, 20, 22, 28, 34],
    "min_body_pt": 15
  },
  "space": { "unit": 4, "steps": [4, 8, 12, 16, 24, 32, 48] },
  "radius": { "sm": 6, "md": 12, "lg": 20 },
  "motion": { "fast_ms": 120, "base_ms": 220, "reduced_motion": "fade-only" },
  "targets": { "min_pt": 44 },
  "contrast": { "text": 4.5, "large_text": 3.0, "nontext": 3.0, "custom_small_text_goal": 7.0 }
}
```

`design/screens.yaml` (committed; the inventory the capture script and the reviewer iterate):

```yaml
build_stamp:
  web: { url: "/__build", field: "gitHash" }
  ios: { plist_key: "CFBundleVersion" }   # set to the short git hash at build time
state_harness:
  web: "?__state=<name>&__net=<online|offline|slow|fail>"
  ios: ["-DriveState", "<name>", "-DriveNetwork", "<online|offline|slow|fail>"]
screens:
  - id: outfit-builder
    tier: primary                 # primary screens get the full matrix
    job: "compose an outfit from wardrobe items"
    tap_budget: 6                 # from entry to job done, for a new user
    entry: "Tab bar → Outfits → New"
    states: [default, empty, loading, error, offline, long-text]
    must_show:
      - { role: button, label: "Add item", min_target_pt: 44 }
      - { role: heading, label: "New outfit" }
    must_not: [placeholder copy, system default font where DESIGN.md names a face]
    baseline: .drive/ui/baseline/outfit-builder/
```

How the skill uses `frontend-design` up front. For greenfield UI the orchestrator invokes the skill once, in a fresh context, with the spec's product paragraphs and the platform named, and instructs it to stop after the plan: run both passes (brainstorm the token system, layout concept and signature; then the "would I produce this for any similar brief?" review), and write the result into `DESIGN.md` and `tokens.json` with the rejected default recorded. The skill's own text asks for this review; the drive skill just makes the output durable instead of leaving it in the model's thinking. For iOS the skill's web-oriented advice (the hero as thesis) is reinterpreted: the "hero" is the first screen's primary content and the signature is more often a material, a transition or a type treatment than a landing hero; the HIG is the base and departures are logged. The skill is used again later as the review lens (section 4.6): preloaded into the reviewer so the tell list and the "one risk, everything else quiet" discipline are in its context.

The `design` canvas skill is optional and is never an approval gate. If the owner wants to look at screens before code, the skill can produce artboards from the contract as a courtesy artefact, and proceed. Mockups are never evidence; only screenshots of the running build are.

Design archaeology for existing products: read the stylesheet or token file and the most-used screens, capture five representative screens, and write a `DESIGN.md` that describes what is actually there (palette in use, faces, spacing rhythm, component vocabulary). The contract for a new feature is "consistent with this"; the reviewer grades consistency, and only proposes taste changes as Notes.

### 4.3 The state harness and build stamp

Verification of states is impossible if states cannot be reached on demand, and most "looks fine" verdicts come from only ever seeing the happy path with seeded data. The architecture component must therefore require, and the maker must implement:

- Web: `?__state=<name>` and `?__net=<mode>` handled in development builds by a small provider that swaps the data source (fixtures for empty/long-text, a delayed promise for loading, a rejecting promise for error, `navigator.onLine`-style offline handling for offline) and stripped from production bundles. `/__build` returns `{ gitHash, builtAt }`, and the page carries `<meta name="build-hash">`.
- iOS: launch arguments `-DriveState <name>` and `-DriveNetwork <mode>` read in `DEBUG` through `ProcessInfo.processInfo.arguments` (or `UserDefaults`, which iOS populates from `-key value` arguments), selecting a fixture repository and a `URLProtocol` stub for network modes. `CFBundleVersion` is set to the short git hash by the build script so `xcrun simctl appinfo <udid> <bundle>` proves which build is installed.
- Long text: a fixtures file with names and descriptions at two to three times normal length, plus a pseudo-localised variant (accented, 30 percent longer) for the long-text state.

### 4.4 Capture

Evidence layout (gitignored except where noted):

```
DESIGN.md                    committed
design/tokens.json           committed
design/screens.yaml          committed
.drive/ui/                   gitignored
  baseline/<screen>/<variant>.png      accepted reference images
  runs/<run-id>/
    manifest.json            git hash, bundle version, tool versions, matrix, timestamps
    <screen>/<variant>.png   native-resolution screenshot
    <screen>/<variant>.review.png     ≤2000 px long edge copy the reviewer reads
    <screen>/<variant>.a11y.yaml|json accessibility tree beside every screenshot
    <screen>/<variant>.crop-<n>.png   crops the reviewer made
    objective/*.json         contrast, targets, overflow, axe, lighthouse, audit results
    findings.json            reviewer output
    verdict.md               human-readable verdict, also summarised in STATUS
```

Variant naming: `<surface>.<scheme>.<text>.<dir>.<state>` such as `iphone17pro.dark.ax5.ltr.empty.png` or `w390.light.default.ltr.default.png`.

Matrix. Primary-tier screens: surfaces {phone, large phone or tablet, and for web also desktop 1440} × {light, dark} × {default text, largest accessibility text (iOS `accessibility-extra-extra-extra-large`; web 200 percent zoom or a 32 px root font)} × every declared state. Secondary-tier screens: {phone} × {light, dark} × {default} × {default, empty}. One RTL pass on the primary flow only when the spec includes localisation; otherwise skip it and record the skip in the manifest. Reduced motion is checked as an assertion rather than as screenshots: with the preference on, `document.getAnimations()` (web) should be empty or fade-only, and on iOS the screen recording of a transition should show no scale or slide.

Web capture. Prefer a drive-owned script over ad hoc MCP clicking; the script is repeatable, records the manifest and does not depend on which browser MCP happens to be connected. The Python Playwright installed here is enough:

```python
# tools/capture-web.py  (sketch; the verified pieces are devices, color_scheme,
# reduced_motion, aria_snapshot, evaluate and full_page screenshots)
import json, subprocess, sys, yaml
from playwright.sync_api import sync_playwright

base, out = sys.argv[1], sys.argv[2]
inv = yaml.safe_load(open("design/screens.yaml"))
surfaces = {"w390": dict(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True, has_touch=True),
            "w768": dict(viewport={"width": 768, "height": 1024}, device_scale_factor=2),
            "w1440": dict(viewport={"width": 1440, "height": 900}, device_scale_factor=2)}
manifest = {"git": subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip(), "shots": []}
with sync_playwright() as p:
    b = p.chromium.launch()
    for s in inv["screens"]:
        for sname, sopts in surfaces.items():
            for scheme in ("light", "dark"):
                for text in ("default", "large"):
                    for state in (s["states"] if s["tier"] == "primary" else ["default", "empty"]):
                        ctx = b.new_context(color_scheme=scheme, reduced_motion="reduce", locale="en-GB", **sopts)
                        page = ctx.new_page()
                        if text == "large": page.add_init_script("document.documentElement.style.fontSize='200%'")
                        page.goto(f"{base}{s['path']}?__state={state}")
                        page.wait_for_load_state("networkidle")
                        stamp = page.evaluate("document.querySelector('meta[name=build-hash]')?.content")
                        assert stamp == manifest["git"], f"build under test {stamp} != HEAD {manifest['git']}"
                        v = f"{sname}.{scheme}.{text}.ltr.{state}"
                        page.screenshot(path=f"{out}/{s['id']}/{v}.png", full_page=True)
                        open(f"{out}/{s['id']}/{v}.a11y.yaml", "w").write(page.locator("body").aria_snapshot())
                        manifest["shots"].append({"screen": s["id"], "variant": v, "stamp": stamp})
                        ctx.close()
    b.close()
json.dump(manifest, open(f"{out}/manifest.json", "w"), indent=2)
```

When the reviewer needs to interact (walkthroughs, hover and focus states), it uses Playwright MCP (`browser_snapshot` with boxes, `browser_take_screenshot`, `browser_run_code_unsafe` for `emulateMedia`) or `agent-browser`, and saves what it sees into the same run directory. Chrome DevTools MCP is the tool for Lighthouse, performance traces, console and network listings, and offline emulation; keep it away from anything involving Google account state, because its attach profile is a separate Chrome that has been signed into the wrong account before (owner memory).

iOS capture. The Simulator MCP is the preferred driver when it works (`launch` installs and launches, `screenshot` returns a PNG, `inspect` returns the tree in points, `tap`/`swipe`/`text` drive flows). Preflight it with one `screenshot` call; if it errors, fall back to `simctl` for capture and to XCUITest for driving flows, and say so in the manifest and the verdict. Today it errors here with the xcode-select message quoted in fact 26, so the fallback is the live path until the owner runs the sudo command.

```bash
U=$(xcrun simctl list devices booted -j | jq -r '.devices[][] | select(.state=="Booted" and .name=="iPhone 17 Pro") | .udid')
BUNDLE=com.example.app
xcrun simctl status_bar "$U" override --time 9:41 --batteryLevel 100 --batteryState charged --dataNetwork wifi --wifiBars 3 --cellularBars 4 --operatorName ''
for scheme in light dark; do
  for size in large accessibility-extra-extra-extra-large; do
    xcrun simctl ui "$U" appearance "$scheme"
    xcrun simctl ui "$U" content_size "$size"
    for state in default empty loading error offline long-text; do
      xcrun simctl launch --terminate-running-process "$U" "$BUNDLE" -DriveState "$state" -DriveScreen outfit-builder
      sleep 1.5
      v="iphone17pro.$scheme.$( [ "$size" = large ] && echo default || echo ax5 ).ltr.$state"
      xcrun simctl io "$U" screenshot --type=png ".drive/ui/runs/$RUN/outfit-builder/$v.png"
      sips -Z 2000 ".drive/ui/runs/$RUN/outfit-builder/$v.png" --out ".drive/ui/runs/$RUN/outfit-builder/$v.review.png" >/dev/null
    done
  done
done
xcrun simctl ui "$U" appearance light; xcrun simctl ui "$U" content_size large; xcrun simctl status_bar "$U" clear
xcrun simctl appinfo "$U" "$BUNDLE" | grep CFBundleVersion   # must equal git rev-parse --short HEAD
```

For RTL add `-AppleLanguages '(ar)' -AppleLocale ar_SA -AppleTextDirection YES -NSForceRightToLeftWritingDirection YES` to the launch line for one pass on the primary flow. For the iPad and a small phone, repeat with those UDIDs; if no iPhone SE-class device exists in the runtime, create one (`xcrun simctl create drive-SE "iPhone SE (3rd generation)" <runtime-id>`) or accept the smallest available and record it.

Image handling for the reviewer. Keep native-resolution originals for pixel diffs and baselines. Give the reviewer the `.review.png` copies resized to at most 2000 px on the long edge, which keeps a full simulator screenshot at roughly 2,400 visual tokens and stays inside the many-image rule regardless of how many images a review session has already read. Crop, do not shrink, when text needs to be legible: a PIL crop of a region at native resolution is the "crop tool" the Fable 5.1 guide recommends and it costs a few hundred tokens. Open images with the Read tool by path; never `cat` or base64 them through Bash.

Flows and video. Vision cannot watch a video, so a walkthrough is a screenshot after every step plus the accessibility tree at decision points. Record video (`xcrun simctl io recordVideo`, Playwright `record_video_dir`, or `agent-browser record`) only for the latency and motion checks, then extract frames at fixed offsets with PIL or `ffmpeg` if installed.

### 4.5 Objective checks that run before vision

These run on the captured evidence and produce `objective/*.json`. They are cheap, deterministic and refutable, so they carry the weight for everything they can express; vision is only asked about what remains.

| Check | How | Source of truth | Vision needed? |
|---|---|---|---|
| Build under test is HEAD | `meta[name=build-hash]` / `/__build`; `simctl appinfo` CFBundleVersion | git | No |
| Every `must_show` element present, labelled, enabled | a11y tree (`aria_snapshot`, `browser_snapshot`, MCP `inspect`) | screens.yaml | No |
| Target sizes ≥ 44 pt iOS / ≥ 24 CSS px web (flag < 44 as Major on web too when it is a primary control) | frames from tree or `getBoundingClientRect` | HIG, WCAG 2.5.8 | No |
| Frames inside the safe area; no sibling overlap; no element beyond screen bounds | frames from tree; safe-area insets from the device table or `env(safe-area-inset-*)` | HIG Layout | No |
| Horizontal overflow | `scrollWidth > clientWidth` against the configured viewport width | WIG | No |
| Text clipping and truncation | tree text ending in `…` (the MCP marks it), `scrollWidth > clientWidth` on text nodes, `textClipped` audit on iOS | HIG Dynamic Type | Partly: wrapping quality still needs eyes |
| Contrast | compute from `tokens.json` pairs with the WCAG luminance formula; on the rendered page sample fg/bg of text nodes via `getComputedStyle`; iOS `contrast` audit | WCAG 1.4.3, HIG | No, except text over images |
| Labels, roles, names, alt text, form labels | axe (`@axe-core/playwright`) or `lighthouse_audit` accessibility; iOS `sufficientElementDescription`, `trait`, `elementDetection` audits | axe rules, HIG | No |
| Focus order and visible focus | script Tab through the page recording `document.activeElement` and the focus ring's computed outline | WIG Focus States | Partly |
| Reduced motion honoured | `document.getAnimations()` under `reducedMotion: 'reduce'`; iOS: transition frames under Reduce Motion | WIG, HIG | Partly |
| Console errors, failed requests, mixed content | `list_console_messages`, `list_network_requests` | none needed | No |
| Regression against baseline | PIL/numpy pixel diff with bbox; threshold from `tokens.json` or 0.5 percent of pixels; `toHaveScreenshot` for projects that adopt snapshot tests | baseline dir | Only to explain an unexpected diff |
| Lighthouse SEO / best practices (marketing and docs) | `lighthouse_audit` mobile and desktop | Lighthouse | No |
| Tokens actually used | grep the stylesheet or Swift tokens for hex literals not in `tokens.json`; SwiftUI `.font(.system(size:))` literals where a token exists | tokens.json | No |

Regression diff, verified form:

```python
from PIL import Image, ImageChops
import numpy as np
a = Image.open(base).convert("RGB"); b = Image.open(new).convert("RGB")
if a.size != b.size: report("size changed", a.size, b.size)
d = np.asarray(ImageChops.difference(a, b)).max(axis=2)
changed = int((d > 16).sum()); ratio = changed / d.size          # tolerate antialiasing noise
bbox = Image.fromarray((d > 16).astype("uint8") * 255).getbbox()  # where it changed
```

Contrast from tokens:

```python
def lum(hexstr):
    r, g, b = (int(hexstr[i:i+2], 16) / 255 for i in (1, 3, 5))
    lin = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
def ratio(fg, bg):
    l1, l2 = sorted((lum(fg), lum(bg)), reverse=True); return (l1 + 0.05) / (l2 + 0.05)
```

Where vision is necessary. Hierarchy (does the eye land where the job is), alignment to the grid and optical alignment, spacing rhythm, fidelity to the direction in `DESIGN.md`, whether wrapped text at AX5 still reads as designed, whether the empty state is an invitation or an apology, whether the loading state matches the layout it replaces, whether an image-backed text region is legible, whether the whole thing looks templated, and whether a screen makes sense without the spec in hand. Where vision is a waste: anything in the table above.

### 4.6 The vision rubric

Severities. **Blocking**: the job cannot be completed, content is clipped or unreadable, a state is missing, the build is wrong, contrast or targets fail on a primary control, or the design contradicts the contract in a way a user would notice at once. **Major**: visibly wrong but usable (misaligned grid, wrong face or weight, wrong spacing step, truncation at AX5 that loses meaning, dark mode with light-mode assets, templated tell in a primary screen, error copy that does not say how to recover). **Minor**: polish (a 2 px misalignment, inconsistent radius, an icon a shade off, a label in the wrong case). **Note**: an observation or a taste suggestion outside the contract; never blocks.

Dimensions, each with its pass condition:

1. Contract fidelity. Every colour, face, size, spacing and radius on the screen resolves to a token; the signature element appears where the contract says and nowhere else; the declared risk is executed, not hedged. Pass: no unlisted values on primary screens.
2. Layout integrity. Nothing clipped, overlapping or outside the safe area; alignment to the spacing grid; consistent gutters; no horizontal scroll; a viewport meta present on web. Pass: objective checks green and no visual misalignment above one spacing unit.
3. States. Empty, loading, error, offline and long-text each look designed, keep the layout stable (skeletons match the final layout), and use the copy pattern. Pass: all declared states captured and designed.
4. Platform conventions. iOS: navigation bars, tab bars, sheets, back gestures, system spacing and Dynamic Type behave as the HIG describes unless DESIGN.md logs a departure. Web: semantic controls, visible focus, forms with labels above inputs and inline errors, `prefers-color-scheme` honoured with `color-scheme` set. Pass: no unlogged departure.
5. Accessibility. Contrast, target sizes, labels, focus order, reduced motion, Dynamic Type up to AX5 without loss of function. Pass: objective checks green and AX5 screens still usable end to end.
6. Taste. The templated-default test: would this exact screen come out for any similar brief? Tells to look for: the three AI looks, numbered markers where nothing is a sequence, one accented word in a headline, all-caps labels, three equal cards, purple or neon gradient accents, pure black, generic names and round numbers in sample data, "Acme"-style names, hype copy ("Elevate", "Seamless"), scattered motion. Pass: no tell on a primary screen, and the screen would be recognisable as this product with the logo removed.
7. Copy. Controls say what happens; names are consistent through the flow; errors say what happened and how to fix it; empty states invite. Pass: no vague error, no "Submit", no apology.
8. Regression. Every pixel-diff region is explained by an intended change. Pass: all diffs annotated.

Observation protocol (this is the anti-rubber-stamp mechanism). For each screen variant the reviewer must write at least five observations, each naming an element (by accessible label or tree path), a location (crop file or approximate region), what the contract or platform rule expects, and what is observed; at least one observation per screen must be the answer to "what is the worst element on this screen and why", and if the reviewer finds nothing wrong on a variant it must list the three things it checked that could have failed and did not, with the evidence it used. A variant with fewer than five observations is rejected by the orchestrator as an incomplete review, not accepted as a pass.

### 4.7 UX heuristics walkthrough

The walkthrough is a scripted task performed on the running build by the reviewer, with a screenshot and tree captured after every action, graded against Nielsen's heuristics and the tap budget in `screens.yaml`.

Protocol:

1. Take the primary job from `screens.yaml` and start from a cold launch in the default state with fixture data.
2. Act as a first-time user: read the screen, choose the most obvious control, act. Do not use knowledge of the code. Record each step as `{ step, intent, control chosen, why it looked right, screenshot, tree }`.
3. Count actions to job completion; compare with `tap_budget`. Over budget by two or more is Major.
4. Friction log: every hesitation (two plausible controls, unclear label, unexpected result) is an entry tagged with the heuristic it violates (1–10) and a severity.
5. Error recovery: submit invalid input, kill the network mid-flow (`__net=offline`, `-DriveNetwork offline`, or Chrome DevTools `emulate networkConditions Offline`), background and foreground the app, rotate. Each must leave a recoverable state with explanatory copy; data loss is Blocking.
6. Latency perception: any operation over one second without an indicator is Major; over ten seconds without progress is Blocking (the long-standing 0.1 s / 1 s / 10 s response-time thresholds from Nielsen's usability work); skeletons that do not match the layout they replace are Minor.
7. Consistency: the same action has the same name and position on every screen it appears; the back path always exists (heuristic 3).

On web the reviewer drives with Playwright MCP or `agent-browser`; on iOS with the Simulator MCP when it works. When it does not, the walkthrough is scripted as an XCUITest that taps the same path and attaches `XCUIScreen.main.screenshot()` after each step (a long-standing XCTest API I did not re-verify today), and the reviewer reads the attachments from the result bundle. The output is `walkthrough.md` in the run directory and its findings join `findings.json`.

### 4.8 The verdict and the loop

`findings.json` schema (one object per finding):

```json
{
  "id": "OB-014",
  "screen": "outfit-builder",
  "variant": "iphone17pro.dark.ax5.ltr.default",
  "element": "button 'Add item' (tree path: root/scroll/toolbar[2])",
  "category": "layout|contract|state|platform|accessibility|taste|copy|regression|ux",
  "severity": "blocking|major|minor|note",
  "expected": "DESIGN.md §Tokens: targets.min_pt 44; HIG 44x44 pt default",
  "observed": "frame 132x36 pt; label wraps to two lines at AX5 and clips the second line",
  "evidence": [".drive/ui/runs/r17/outfit-builder/iphone17pro.dark.ax5.ltr.default.review.png",
               ".drive/ui/runs/r17/outfit-builder/iphone17pro.dark.ax5.ltr.default.crop-3.png"],
  "objective_ref": "objective/targets.json#outfit-builder/ax5/Add item",
  "suggested_fix": "Give the toolbar button a minimum height of 44 pt and allow it to grow; move to ViewThatFits with an icon-only fallback at AX sizes",
  "confidence": 0.9,
  "round": 1,
  "status": "open|fixed|disputed|wont-fix"
}
```

`verdict.md` is the human summary: build hash, matrix coverage (with skipped cells named), objective results, counts by severity, the five observations per variant (collapsed), the walkthrough result against the tap budget, and the decision: `accept`, `revise`, or `stop`.

Rounds. Round one is the full review. The maker answers every finding in `findings.json` with `fixed` and the commit, or `disputed` with a reason. Round two recaptures only the affected screens plus one adjacent screen for regression, and the reviewer must point at the new crop for each `fixed` item before closing it; new findings in round two are allowed but should be rare and are a signal about round one. Round three is the last; if blocking or major findings remain, the orchestrator records the screen as Partial in STATUS, writes the open findings into the backlog file, and surfaces one question to the owner in conversation ("Accept with these two majors, or spend another round?") without waiting on an inbox. Disputed findings are adjudicated by the orchestrator (Fable) by reading the evidence and the contract, once, and its decision is logged in `DESIGN.md`'s decision log so the same argument does not recur.

Acceptance. All of: build hash matches HEAD; objective checks green or every failure explicitly waived in the contract; zero blocking and zero major findings; all regression diffs annotated; the walkthrough within the tap budget; at least five observations per primary variant recorded. Minor and Note findings go to `.drive/ui/backlog.md`, not to the gate.

Recording. STATUS uses the owner's ladder: screenshots reviewed from a local debug build against fixtures are Local Proof; the same screens against the deployed backend with real data (TestFlight build or the production URL) are Live Proof; "Done" requires Live Proof for the primary flow. The manifest path and the verdict decision are what STATE.md stores, never the images. A finding that recurs across two screens or two rounds is a candidate lesson and is handed to the lessons component in general form ("fixed-height rows clip at AX sizes; let containers grow and stack horizontally adjacent views", "phone emulation without a viewport meta renders at 980 px; add the meta before judging layout").

---

## 5. Conditionals by project shape

Greenfield iOS app with Cloudflare backend (the fashion app). Full contract via frontend-design with the HIG as the floor; departures logged. Full matrix on primary screens: iPhone 17 Pro, the smallest available iPhone, iPad Pro 11; light and dark; default and AX5; every state; one RTL pass only if the spec localises. The state harness is a hard implementation requirement and the build stamp goes into `CFBundleVersion`. Objective layer: XCUITest smoke test per screen calling `performAccessibilityAudit` with all types, plus swift-snapshot-testing images with dark and AX5 traits as the regression suite once screens stabilise. Live Proof requires the app pointed at the deployed Worker with real data, not the fixture repository, because fixtures are a harness kinder than production: the empty state you designed never appears with seeded data, and the long-text state never appears with tidy fixtures. Fashion specifics: photography dominates, so contrast of text over images and the dark-mode treatment of white-background product shots (HIG says soften them) are explicit rubric items, and the taste review weighs the signature element heavily because the category is crowded with identical grid-of-cards apps.

Deep bug hunt in an existing codebase. Skip the component unless the bug is visual or the fix touches UI. If it is visual: capture the exact repro state before and after at the reporting viewport and appearance, run the pixel diff on the fixed screen and its two neighbours, and let the reviewer confirm the fix and the absence of collateral change with a short review (two observations per variant is enough here; the rubric's minimum applies to primary screens of new work). No taste review.

Feature on an existing product (a new dashboard). Design archaeology first: extract the existing tokens and component vocabulary into `DESIGN.md`; consistency is the primary rubric and taste changes are Notes. Dashboards are used on desktop, so the surfaces are 1280, 1440 and 1920 wide plus 390 for the responsive floor; dark mode if the product has it. Load the `dataviz` skill for charts and add its rules (one system, accessible palette, legends and tooltips) to the checklist. Regression on every adjacent screen that shares navigation or layout. The walkthrough job is "find the number the dashboard exists to show" with a tap budget of two.

Migration or consolidation (moving the AI gateway into the platform). Usually no user-facing UI; if an admin UI or settings page is touched, run regression only: pixel diff and accessibility-tree diff before and after, no rubric review, no taste. If nothing visual changed, record "UI: not applicable" in STATUS rather than skipping silently.

Research plus website (market position, marketing site with blog and docs). The taste review carries the most weight here and frontend-design is mandatory up front, including the writing section, because templated copy is as much a tell as templated layout. Surfaces 390, 768, 1440 and 1920; light and dark; reduced motion; Lighthouse accessibility, SEO and best practices at mobile and desktop; a performance trace for the landing page's LCP with Chrome DevTools MCP. Docs section: code blocks scroll inside their container, sidebar and search work at 390, line length under 80 characters, headings anchor. Blog: typography and rhythm at three widths, image sizes declared, Open Graph image present. Content must be the real research content, not placeholders; a screenshot with lorem ipsum is Blocking.

Other shapes. CLI and TUI: no vision; snapshot the terminal output as text and review help and error text for the copy rules. Library or SDK: only the docs site, as above. Data pipeline and ops or incident work: not applicable; say so. Pure research report: the deliverable may be an Artifact page; a single light and dark capture at 390 and 1440 with the copy rubric is enough.

---

## 6. Model and effort assignment

Roles in this component and my recommendation:

| Role | Model | Effort | Why |
|---|---|---|---|
| Design direction (frontend-design pass, greenfield) | `opus` | `high` | Bounded creative judgment against a written brief; Fable is not needed to pick a palette, and the skill's own self-review step is the quality lever |
| Coherence and taste pass across all screens (greenfield and marketing only, once per project) | `fable` | `xhigh` | One expensive cross-screen judgment where "does this hang together as one product" is the hardest call in the track; Fable 5.1's stronger vision (per its prompting guide) is worth paying for once, not per screen |
| `ui-reviewer` per screen batch | `opus` | `high` | Judgment work with vision on 10–15 images per batch; Sonnet's image input is the same mechanism but taste and platform-convention judgment is where the tiers differ; the owner rules out Haiku |
| Objective-check triage (dedupe axe output, match pixel diffs to the maker's stated changes, classify findings into the schema) | `sonnet` | `low` | Classification over text; cheap and fast; verified that Sonnet 5 supports `low` |
| Dispute adjudication, round-three stop decision | `fable` (the orchestrator) | inherit | One decision, once, with the contract and evidence in front of it |

Evidence on vision quality differences: none official. The docs state image input for all four models and the Fable 5.1 guide claims "better vision capabilities out of the box"; I found no per-model screenshot benchmark in the docs and treat third-party MMMU numbers as not comparable. The practical difference the skill should assume is in judgment, not perception: reading "the button is clipped" is within Sonnet's reach; deciding that a screen is competent but templated, or that a departure from the HIG was a good trade, is where Opus earns its price, and Fable earns it once for the whole product.

Isolation: none. The reviewer needs the running app and the evidence directory; it must not edit code, which a tool restriction handles. Memory: `project`, with an explicit rule to use memory only to check whether a finding recurs (the owner's "second time is the bug") and never to pre-judge a screen.

Draft `~/.claude/agents/ui-reviewer.md`:

```markdown
---
name: ui-reviewer
description: Independent visual, accessibility and UX reviewer for running web and iOS builds. Captures evidence itself, grades against DESIGN.md, design/tokens.json and design/screens.yaml, and returns structured findings. Use after a UI implementation step or fix round; never to write or fix code.
model: opus
effort: high
disallowedTools: Edit, NotebookEdit, Agent
skills: frontend-design
memory: project
maxTurns: 80
color: purple
hooks:
  PreToolUse:
    - matcher: "Write"
      hooks:
        - type: command
          command: "$HOME/.claude/agents/hooks/ui-reviewer-write-guard.sh"
---

You are the independent reviewer for the user interface of this project. You did not build it, you will not fix it, and you have no stake in it passing. Your job is to find what is wrong, prove it with evidence, and say how bad it is. A review with no findings is a review that must show its work.

## Inputs you are given
- The run id and the evidence directory `.drive/ui/runs/<run-id>/` (create it if the orchestrator has not).
- `DESIGN.md`, `design/tokens.json`, `design/screens.yaml`, and the round number.
- For round 2 and later: the previous `findings.json` with the maker's `fixed`/`disputed` annotations.
- The URL of the running web build and/or the simulator UDID and bundle id.

## Procedure
1. Preflight. Confirm the build under test is HEAD: read `/__build` or `<meta name="build-hash">` on web; `xcrun simctl appinfo <udid> <bundle>` CFBundleVersion on iOS. If it does not match `git rev-parse --short HEAD`, stop and report "wrong build" as a blocking finding; do not review it. On iOS try one Simulator MCP `screenshot`; if it errors, fall back to `xcrun simctl io <udid> screenshot` and XCUITest for flows and say so in the manifest. Never use `simctl io booted` when more than one device is booted; always pass the UDID.
2. Capture. Run the capture script (`tools/capture-web.py` or `tools/capture-ios.sh`) for the screens in scope. Do not accept screenshots handed to you by the maker; capture your own. Read images with the Read tool from `.review.png` copies (long edge at most 2000 px). When text is small, crop the native PNG with PIL and read the crop; never shrink to fit.
3. Objective checks first. Run or read `objective/*.json`: build stamp, must_show elements, target sizes, overlaps and safe area, overflow, truncation, contrast from tokens, labels (axe or Lighthouse on web; performAccessibilityAudit results on iOS), console and network errors, regression diff against `.drive/ui/baseline/`. Every failure becomes a finding with `objective_ref` set. Do not re-derive these by eye.
4. Vision review. For every screen variant, write at least five observations, each with element, location, expected (cite DESIGN.md section, token, HIG or WIG rule) and observed. One of them must answer "what is the worst element on this screen, and why". If a variant has no findings, list the three things you checked that could have failed and did not, with the evidence you used. Apply the frontend-design lens for taste: would this exact screen come out for any similar brief? Name the tell if so.
5. Walkthrough. Perform the primary job from `screens.yaml` as a first-time user, screenshot after every action, count actions against `tap_budget`, log friction with the Nielsen heuristic number, test error recovery (invalid input, offline mid-flow, background/foreground), and note any wait over one second without an indicator.
6. Rounds after the first. For every finding the maker marked `fixed`, point at the new crop that proves it before closing it. Do not close on the maker's word. For `disputed` findings, restate the evidence once and leave the decision to the orchestrator.
7. Output. Write `findings.json` (schema in the drive skill's references) and `verdict.md` into the run directory, and return the verdict summary and the counts by severity as your final message. Decision is `accept` only if: build is HEAD, objective checks are green or waived in DESIGN.md, zero blocking and zero major findings, all regression diffs annotated, walkthrough within budget, and at least five observations per primary variant.

## Rules
- Never write "looks fine", "looks good", or "no issues" without the three-things-checked list.
- Never grade a mock, a design canvas, or a Storybook story as evidence of the app; only the running build counts.
- Never grade from memory of a previous round or another project; use project memory only to check whether a finding recurs, and say so when it does.
- Never review one viewport, one appearance or one text size and call the screen verified; if the matrix is incomplete, name the missing cells in the verdict and downgrade the decision to `revise`.
- Never edit source files. You may write only under `.drive/ui/`.
- Severity is about the user, not about effort to fix. A one-line fix that clips content is still blocking.
- Prefer the accessibility tree for geometry and vision for gestalt; your pixel estimates are approximate and the tree's frames are not.
```

Write guard hook, `~/.claude/agents/hooks/ui-reviewer-write-guard.sh` (follows the documented PreToolUse pattern; check the field name against the hooks reference when installing):

```bash
#!/usr/bin/env bash
input=$(cat)
path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')
case "$path" in
  */.drive/ui/*) exit 0 ;;
  *) echo "ui-reviewer may only write under .drive/ui/ (attempted: $path)" >&2; exit 2 ;;
esac
```

The reviewer keeps `Write` so it can produce `findings.json`; the hook confines it. `Agent` is disallowed so it cannot delegate the looking to a cheaper model.

---

## 7. Failure modes and anti-patterns

"Looks fine." The commonest mirage: a reviewer glances at a happy-path screenshot and approves. Prevention is structural: the five-observation minimum, the worst-element question, the three-things-checked list for clean variants, and an orchestrator that rejects a verdict whose observation count is short instead of accepting it as a pass.

Screenshots of the wrong build. The maker fixes code, the simulator still runs the previous install, the reviewer approves the old pixels. Prevention: the build stamp in the app and the manifest, checked by the reviewer before anything else; `--terminate-running-process` on launch; `simctl appinfo` on iOS.

Checking the mock instead of the app. Design canvases and Storybook stories are inputs; a verdict that cites them as evidence is invalid. The evidence path must be under the run directory and the manifest must name the build.

One viewport, light mode, default text. The matrix is declared in `screens.yaml`; a manifest missing cells makes the decision `revise` at best, and the missing cells are named in the verdict. Dark mode and AX5 are where SwiftUI and CSS defaults fail most often (light-mode assets on dark backgrounds, fixed-height rows clipping), which is why they are in the primary matrix, not an optional extra.

The wrong device by accident. `simctl io booted` picked the iPad here with two devices booted. Always resolve the UDID by name.

Shrunken screenshots. A 2622 px tall capture squeezed into a contact sheet makes 13 pt text unreadable and the reviewer guesses. Keep native originals, hand the reviewer a copy at most 2000 px on the long edge, and crop for detail.

Fixtures kinder than production. Seeded data hides the empty state, tidy fixtures hide the long-text state, a mocked network hides the error state; twenty-four green runs and a broken app is the owner's own D1 incident in a different costume. Prevention: the state harness makes every state reachable, and Live Proof requires the real backend.

The reviewer edits code. It stops being independent the moment it does. Tool restriction plus the write guard.

Rubber-stamp on round two. The maker says "fixed", the reviewer closes it. Prevention: a `fixed` item closes only when the reviewer points at the new crop.

Pixel-coordinate confidence. The docs say localisation is approximate; a reviewer asserting "the button is 3 px off" from a screenshot alone is guessing. Geometry comes from the tree; vision decides whether the composition reads right.

Base64 in tool output. Piping an image through Bash puts base64 into context, which the Fable 5.1 guide names as a false-positive trigger for safety classifiers and which costs far more tokens than a Read. Always Read by path.

Matrix explosion and cost. Three surfaces × two schemes × two text sizes × six states is 72 images per primary screen; at roughly 2,400 tokens each that is 170k input tokens per screen on Opus, about $0.85, which is affordable but adds up across a project and floods one context. Prevention: tiers in `screens.yaml`, one review session per screen batch of at most 15 images, objective checks doing the bulk of the state coverage, and vision reserved for the primary matrix.

ImageMagick as the diff oracle. It returned zero changed pixels on a pair that differed in 36. Use PIL/numpy, which gave the right answer.

The Simulator MCP silently unavailable. It fails today with an xcode-select error the reviewer cannot fix; a skill that assumes it works produces no evidence and may report the absence as a pass. Prevention: preflight with one screenshot call, fall back to `simctl`, and say so.

Verifying against the reviewer's taste. Without `DESIGN.md` the review becomes a second designer's opinion and the maker rightly disputes it. Prevention: no UI review starts without the contract; for existing products the contract is the archaeology document.

Approval queues in disguise. "Send mockups to Chris and wait" never completes. The canvas is a courtesy artefact; the pipeline proceeds; the only human touchpoint is the single round-three question, asked once, in conversation.

---

## 8. Open questions and trade-offs

The iOS Simulator MCP does not work on this Mac today. Every action returns the xcode-select error even though `xcode-select -p` is correct in a shell, so the cause may be the MCP's own environment rather than the setting. Recommendation: the owner runs `sudo xcode-select -s /Applications/Xcode.app/Contents/Developer` once and retries; the skill keeps the `simctl` fallback permanently because the same class of failure will recur after Xcode updates.

Whether to commit baselines. Playwright's convention commits snapshot images; the owner dislikes stray artefacts. Recommendation: the ad hoc evidence under `.drive/ui/` stays gitignored, and baselines are committed only when the project adopts a snapshot test suite as first-class tests (then they are fixtures, not clutter). Baselines must be regenerated in the same environment that checks them, so if CI exists, CI owns them.

RTL for a London fashion app. Probably irrelevant, and the HIG rules are subtle enough that a pass costs real review time. Recommendation: RTL only when the spec localises to an RTL language; record the skip.

Whether Fable should do any looking at all. The per-screen review on Opus is the right default for cost; the once-per-project coherence pass on Fable is my recommendation for greenfield and marketing shapes only, because it is the one moment where "does this feel like one product" is decided. If the owner finds it not worth $1–3 per project, drop it; the rubric does not depend on it.

Runtime fetch of the Vercel guidelines. The installed skill fetches the rules from GitHub each run, which is a network dependency in an autonomous pipeline. Recommendation: fetch at run time and fall back to a copy cached under the drive skill's `references/` when the fetch fails, noting the cache date in the verdict.

The two extra local design skills. `design-taste-frontend` and `redesign-existing-projects` have good tell lists and bad absolute bans. Recommendation: do not load them; lift their tell lists into the drive rubric (already done in section 4.6) and keep frontend-design as the taste authority because its "brief wins" stance is the right one.

Web AX testing without Node. The Python Playwright here cannot run `@axe-core/playwright` directly. Recommendation: use `lighthouse_audit` via Chrome DevTools MCP as the default web accessibility oracle, and add axe when the project already has a Node toolchain (most web projects do).

How strict on 24 px versus 44 pt on web. WCAG AA says 24 CSS px; the HIG says 44 pt; a web app used on phones should meet 44 for primary controls. Recommendation: 24 is the floor for any target, 44 is Major-if-missed for primary controls on mobile viewports, and `tokens.json` records the choice so the reviewer is not inventing it.

---

## 9. Skill text candidates

1. **Contract before pixels.** Before writing any UI code, write `DESIGN.md`, `design/tokens.json` and `design/screens.yaml`. Run the frontend-design skill for direction and record its plan, including the generic default it rejected and why. Every later UI verdict compares evidence to these files, never to the reviewer's preference.

2. **Screens list their jobs.** Each entry in `design/screens.yaml` names the screen's single job, its tap budget for a new user, its states (default, empty, loading, error, offline, long-text), the elements that must be present with their accessible labels, and whether it is primary or secondary. The capture matrix and the walkthrough are generated from this file.

3. **Every state must be reachable on demand.** Implement a debug-only state harness: `?__state=` and `?__net=` on web, `-DriveState` and `-DriveNetwork` launch arguments on iOS. Stamp the build with the short git hash (`/__build` and `<meta name="build-hash">` on web; `CFBundleVersion` on iOS). A screen whose states cannot be forced cannot be verified, and a screenshot whose build cannot be proven is not evidence.

4. **The reviewer captures its own evidence.** The `ui-reviewer` subagent runs the capture script itself against the running build, checks the build hash against HEAD before looking at anything, and refuses screenshots handed over by the maker. Mockups, canvases and stories are inputs, never evidence.

5. **Capture the matrix, not a screenshot.** Primary screens: phone, large phone or tablet (and desktop on web) × light and dark × default and largest accessibility text × every declared state. Secondary screens: phone × light and dark × default and empty. Save the accessibility tree beside every image. A verdict on a partial matrix names the missing cells and is at best `revise`.

6. **Objective checks run before eyes.** From the tree and the tokens, assert: must-show elements present and labelled; targets at least 44 pt on iOS and 24 CSS px on web (44 for primary mobile controls); frames inside the safe area with no sibling overlap; no horizontal overflow; no truncated text; contrast computed from tokens at 4.5:1 for text and 3:1 for large text and non-text; no console or network errors; pixel diff against the baseline with the changed region located. Use axe or Lighthouse on web and `performAccessibilityAudit` on iOS. Vision is only asked about what these cannot express.

7. **Five observations or it did not happen.** For every screen variant the reviewer records at least five concrete observations, each naming an element, a location, what the contract or platform rule expects and what is observed. One must answer "what is the worst element on this screen, and why". A clean variant must list the three things checked that could have failed and did not. The orchestrator rejects any verdict short of this as incomplete, never as a pass.

8. **Taste is checked against the templated default.** Ask of every primary screen: would this exact screen come out for any similar brief? Tells: the warm-cream serif-and-terracotta look, the near-black single-neon-accent look, the hairline broadsheet look, numbered markers where nothing is a sequence, one accented word in a headline, all-caps labels, three equal cards, purple or neon gradients, pure black, generic names and round numbers in sample data, hype verbs in copy, scattered motion. A tell on a primary screen is Major; the fix is to consult `DESIGN.md`'s signature and direction, not to add decoration.

9. **Severity is about the user.** Blocking: the job cannot be completed, content is clipped or unreadable, a declared state is missing, the build is wrong, or a primary control fails contrast or target size. Major: visibly wrong but usable. Minor: polish. Note: taste outside the contract; never blocks. Effort to fix has no bearing on severity.

10. **Walk the primary job as a stranger.** Start cold, choose the most obvious control, screenshot after every action, count actions against the tap budget, log every hesitation with the Nielsen heuristic it violates, break the flow (invalid input, offline mid-flow, background and foreground, rotate) and require a recoverable state with copy that says what happened and how to fix it. Any wait over one second without an indicator is Major; over ten seconds without progress is Blocking.

11. **Findings are data, not prose.** Return `findings.json` with screen, variant, element, category, severity, expected (citing the contract or rule), observed, evidence paths, objective reference, suggested fix, confidence, round and status. The maker answers every finding as fixed (with commit) or disputed (with reason). Closing a fixed finding requires the reviewer to point at the new crop.

12. **Three rounds, then decide.** Round one reviews everything; round two recaptures affected screens plus one neighbour; round three is the last. If blocking or major findings remain after round three, record the screen as Partial, move the findings to the backlog, and ask the owner one question in conversation. Disputes are settled once by the orchestrator against the evidence and logged in the design decision log.

13. **Local Proof is not Live Proof.** Screenshots of a debug build against fixtures are Local Proof. The primary flow against the deployed backend with real data (TestFlight or the production URL) is Live Proof, and Done requires it. Fixtures hide the empty, long-text and error states by construction.

14. **Read images by path; crop, do not shrink.** Keep native-resolution originals for diffs; give the reviewer copies at most 2000 px on the long edge; crop regions at native resolution when text is small. Never pipe image bytes through Bash. Geometry comes from the accessibility tree; vision judges composition.

15. **Name the device.** Resolve simulator UDIDs by name with `xcrun simctl list devices booted -j` and jq. `booted` with more than one device picks one arbitrarily and the evidence will be of the wrong screen size. Restore appearance, content size and status bar overrides after capture.

16. **Preflight the simulator tooling.** Try one Simulator MCP `screenshot`; if it errors, fall back to `xcrun simctl io <udid> screenshot` for capture and XCUITest for flows, and record the fallback in the manifest and verdict. Never report an unavailable tool as a passed check.

17. **Recurring findings become lessons.** A finding seen on two screens or in two rounds is written to the lessons component in general form, with the cause and the rule, so the next project's maker reads it before the reviewer has to find it again.
