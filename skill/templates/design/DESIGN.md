# <Product name> · design contract
Updated: <YYYY-MM-DD> · mode: <new direction | extracted from the existing system> · platforms: <web | ios | web, ios> · tokens: `design/tokens.json` · screens: `design/screens.yaml`

<!-- Written by drive:designer. Rules: references/ui-verification.md section 2. Every later UI
verdict compares evidence with this file, never with a reviewer's preference, so write only what a
reviewer can check. Plain language, under 300 lines. For an extracted contract, describe what ships
and cite the file and line each value comes from; the contract for new work is consistency with it.
Delete every guidance comment before the design gate. -->

## Subject, audience, job
<!-- One paragraph: what this is, who uses it and in what situation, and the single job of the
primary screen. Name the subject concretely; its own materials and vocabulary are where the direction
comes from. -->

## Direction
<!-- Two sentences on the mood. Then the one deliberate aesthetic risk and why it fits this subject.
For an extracted contract, describe the existing direction and write "Risk: none; consistency with
the existing system." -->

Risk: <the one deliberate choice> because <why it fits the subject>.

Rejected generic default: <the look you would have produced for any similar brief, named concretely:
palette, type pairing, layout pattern>. Replaced by: <what this contract chose instead, per axis>.
<!-- Required for a new direction; the design gate fails without it. Where the brief itself asks for
a look that is commonly a default, quote the brief here and say so. -->

## Platform base
<!-- iOS: the Human Interface Guidelines are the floor. Web: the Web Interface Guidelines and WCAG
2.2 AA are the floor. List every deliberate departure; an unlisted departure is a finding. -->

| Departure | Where | Why | What would count as a violation |
|---|---|---|---|
| <system component or convention replaced> | <screens> | <reason> | <observable condition> |

## Tokens
<!-- Human-readable mirror of design/tokens.json. The JSON is the source; if they disagree, the JSON
wins and this section is corrected in the same commit. -->

Palette (four to six named colours):

| Name | Role | Light | Dark | Used for | Contrast pair and ratio |
|---|---|---|---|---|---|
| <name> | <token role, e.g. fg.primary> | <#RRGGBB> | <#RRGGBB> | <where it appears> | <on bg.base: n.n:1> |

Type:

| Role | Face and fallback | Weights | Used for |
|---|---|---|---|
| display | <face>, <fallback stack> | <weights> | <where; with restraint> |
| body | <face>, <fallback stack> | <weights> | <running text, controls> |
| utility | <face or none> | <weights> | <captions, data> |

Scale: <step names with size and line height, in px or pt; on iOS the text style each maps to>.
Minimum body size: <n>.
Space: base unit <n>; steps <list>. Radii: <names and values>. Borders and elevation: <rules>.
Motion: durations <fast, base, slow>; easing <curve>; with reduced motion: <fade-only | none>.
Targets: <minimum sizes, at or above the floors in tokens.json>.

## Signature element
<!-- The one memorable thing. Everything around it stays quiet. -->
- What: <the element>
- Where it appears: <screens and positions>
- Never used for: <places it must not appear>

## States
<!-- Every screen in screens.yaml declares its states; this section says how each kind looks and
what it says. -->

| State | How it looks | What it says (copy pattern) |
|---|---|---|
| empty | <layout; the invitation to act> | <e.g. "No entries yet. Create your first entry."> |
| loading | <skeleton matching the final layout, or indicator, and where> | <none, or a short status> |
| error | <placement; layout stays stable> | <what happened, then how to fix it; no apology> |
| offline | <what remains usable; how it is shown> | <what works offline and what does not> |
| long-text | <how text wraps, truncates, or stacks at the largest size> | <none> |
| <platform extra: permission-denied, partial> | <how it looks> | <what it says> |

## Copy voice
- Register: <plain, conversational, sentence case; tuned to the audience>.
- Controls name the action: "<Save changes>", never "Submit". An action keeps its name through the flow ("<Publish>" produces "<Published>").
- Names follow what people control and recognise, never how the system is built.
- Errors: <pattern>. Empty screens: <pattern>.
- Words this product does not use: <list>.

## Not allowed
<!-- Start from the templated-default tells in references/ui-verification.md section 7 and add
project-specific ones. The reviewer treats each as a finding on sight. -->
- <tell or project-specific pattern>

## Decision log
<!-- Append-only, newest last. Includes waivers of objective checks and contract changes from dispute
rulings (with the DECISIONS.md entry). When the goal asks for options, record the two to four directions
considered here with how each scored on grounding in the subject, distance from the defaults, legibility
at phone width, and contrast, then the one chosen. -->

| Date | Decision | Why | What would count as a violation | Undo |
|---|---|---|---|---|
| <YYYY-MM-DD> | <decision> | <reason> | <observable condition> | <how to reverse it> |
