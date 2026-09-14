# 25 · Drafting brief for agents writing the drive skill

You are drafting part of the `/drive` skill. Read these first, in order:

1. `/Users/chabotc/Projects/drive/research/24-synthesis.md`. It is binding. Where a research
   report disagrees with it, the synthesis wins. Use its names, file grammar, agent names, phase
   names, ladder, evidence tokens, and verdict schema exactly.
2. `/Users/chabotc/Projects/drive/research/00-brief.md`, sections "Hard requirements" and
   "Owner's working preferences", plus the corrections at the top.
3. The research reports named in your task, in full where your task says so. Lift their skill
   text candidates where they fit the synthesis; adapt names to the synthesis.

## What you are writing

Files inside `/Users/chabotc/Projects/drive/skill/`. The skill runs inside Claude Code as the
main conversation (the orchestrator, on Fable) plus the subagents in synthesis section 6. Your
reader is that orchestrator or subagent at run time, mid-task, with limited context. Write for
that reader: what to do, in what order, what counts as done, what to refuse.

## How to write

- Plain language, imperative voice, full sentences. Say what a thing means; never lean on rule
  IDs, codenames, or labels the reader has to decode.
- No hype, no staccato fragments, no em-dash strings, no rhetorical questions, no flattery.
- Tables for enumerable things (shapes, traits, checks, commands). Prose for reasoning that must
  be followed. Bullets only for genuinely parallel items.
- Be prescriptive and concrete: exact file paths, exact commands, exact schemas, exact exit
  conditions. A reference file that says "consider testing appropriately" is a defect.
- Keep arguments short. One sentence of why beside a rule is enough; the research reports hold
  the long arguments and you may point to nothing outside the skill, since the research directory
  does not ship.
- Every reference file opens with one paragraph: when to read it and what it decides. Files over
  300 lines start with a short table of contents.
- Size targets: a shape file 60 to 140 lines; a topic reference 150 to 350 lines; a domain file
  up to 450 lines; an agent file 25 to 70 lines; a template as long as its structure needs.
- Never refer to the fashion or wardrobe app, Garderobe, Arcwell, or any specific owner project
  inside the skill, except where the synthesis seeds a verified lesson and needs its evidence
  line. Examples use neutral placeholders.
- Aliases only for models: `fable`, `opus`, `sonnet`. Never `haiku`. The one pinned id allowed is
  `claude-opus-4-8`, only for the cyber-classifier retry.

## Boundaries

- Write only the files your task assigns. Do not edit SKILL.md unless your task says so.
- Do not run git commands that change state in `/Users/chabotc/Projects/drive`. The coordinator
  commits.
- Do not write any code or files for any example project. Code you write is only the skill's own
  tooling when your task assigns it, and it lives under `skill/scripts/`.
- Scratch goes under `/private/tmp` and is deleted before you finish.
- If the synthesis is silent or wrong on something your file needs, decide, write the decision
  at the end of your final reply under "Synthesis gaps", and keep going.

## Final reply

At most 200 words: the files written with line counts, anything you could not do, and the
"Synthesis gaps" list. The files on disk are the deliverable.
