# 39. Verifying two lessons from a live run

Two candidates came out of a finished run's retro with no dedupe and no auditor verdict, because the
run's dollar budget had run out. This record does that work. I read the retro, the investigation into
research lanes that ran out of turns, the run's DECISIONS.md entries on folding the UI waves and
stopping verification rounds, every handoff and verdict under the run's `.drive/`, and the subagent
transcripts themselves, which I recounted with a script that counts distinct assistant message ids
(turns), `tool_use` blocks (calls), and the index of the first write to the ledger or verdict path.
Nothing in the run's repository was changed. On the skill side I read `references/lessons.md`, every
file in `references/lessons/`, the SKILL.md standing-rules block (empty), `agents/researcher.md`,
`agents/verifier.md`, `references/research.md` sections 3, 4, 7, 11 and 16, `references/verification.md`
section 2, `references/parallel.md` sections 8 to 10, `references/capabilities.md`'s brief template, and
`templates/handoff.md`, and grepped the skill for `maxTurns`, write-by, checkpoint, and claim caps.

Both candidates describe one mechanism in two roles: a worker whose deliverable is a file writes it
only after all its gathering, nothing enforces the budget its brief names, and the turn limit ends the
worker without a final message, so an overrun loses everything. In both cases the instruction that
would have prevented it was missing from the file the worker reads, so both went there rather than to
`general.md`.

## Candidate 1: write each research entry as its question closes

Verdict: **accepted, narrowed.**

What the transcripts confirm. The first lane stopped at 60 turns and 81 calls with nothing written; it
was continued and wrote its ledger at call 138 of 140. The second lane stopped at 60 turns and 84 calls
with stop reason `tool_use`, no ledger write, and no saved source. Both briefs carried three or four
questions plus probes, against a template that says one question per lane.

Counts that needed correcting. The investigation's gate log says the two relaunched lanes finished in
24 and 27 calls with first writes at calls 21 and 24. The transcripts show 28 calls in 14 turns (first
ledger Edit at call 24) and 32 calls in 25 turns (first at call 23). The conclusion still holds, since
both finished far inside 60 turns with every entry written. Two further details matter. The second
relaunched lane overran its own 25-call cap by seven calls, which shows again that a brief's budget is
not enforced. The first carried three questions, two of them with probe output already on disk, so the
evidence does not test "one or two questions per lane".

What was kept. Writing each entry and its sources when the question closes or hits its cap, a
per-question cap when a brief carries more than one question, and a lane budget at or below two thirds
of `maxTurns`. The two-thirds figure is a safety margin, not a measured threshold: the second failed
lane had a 45-call budget, three quarters of 60, and overran it to 84 calls, so the write order is the
control that matters and the budget only makes an overrun less likely.

What was dropped, and why.
- "One or two questions per lane": the brief template already says one question in one lane, and the
  failing briefs departed from it. Widening it to two has no support in the evidence.
- "Probes belong in the project's tests, not research lanes": rejected. It contradicts
  `references/research.md` section 7, where a behaviour fact about an external system is verified only
  by a probe, and the template's own `probe` lane. The measured probe cost was four-call fix cycles
  (run, read output, read script, rewrite) with no Edit tool, which `agents/researcher.md` now grants.
  Bundling probes into a documentation lane is already excluded by the one-question rule.
- The write-by-call-15 checkpoint: both relaunched lanes missed it and still finished, so it was not
  the operative part and is not adopted.

What would refute it: a lane briefed with the per-question write order that still reaches its turn
limit with no entry on disk.

Dedupe. Already said: stop at the budget and record the best answer as assumed pending refutation
(`references/research.md` section 3, `agents/researcher.md` step 7 before this change); one question per
lane and a budget in tool calls (section 11 template). Not said anywhere: when to write, or how a
budget relates to `maxTurns`. `references/parallel.md` section 10 covers continuing a partial worker
after the fact, not preventing the loss. Against `general.md`, the candidate is distinct from all six
entries. The investigation's proposed verdict, narrower than the second-workaround rule, does not
hold: that rule is about repeating a workaround, and this one is about the order of writes against a
turn limit. `rejected.md` and `retired.md` are empty.

Where it went. `skill/agents/researcher.md` gains step 7, write as you go (the old step 7 becomes step
8). `skill/references/research.md` section 11 gains a per-question cap and a write-order line in the
brief template, and a short paragraph after it on the two-thirds budget and why the write order matters.

## Candidate 2: cap verifier handoffs and name a budget with a write-by point

Verdict: **accepted, narrowed**: the budget, the write-by point and one verdict per handoff are
kept; eight claims is only a starting size.

What the transcripts confirm. The combined wave 1 verifier had no budget line and one handoff covering
two verdicts: 13 wave 1 claims and a re-judgement of server-core's 11. It stopped at turn 80, call 92,
with neither verdict written, and wrote both only after the orchestrator sent a message, at calls 93
and 94. Three later handoffs named a tool-call budget and a write-by call. The search round 2 handoff
(6 claims, 45 calls) wrote at call 32. The wave 2 API handoff (8 claims, 60 calls, write by 50) wrote at
call 39. The titles, files and server-core round 3 handoff (60 calls, write by 50) wrote both verdicts
starting exactly at call 50, and 9 of the 11 server-core claims came back `unverifiable` with the
recorded reason "no independent refutation within budget".

Counts that needed correcting. The retro says later handoffs capped at eight claims did not run out.
The round 3 handoff listed 7 claims but also told the verifier to re-judge the eleven server-core claims
from another handoff, 18 claims across two verdicts. It did not run out because of its write-by point,
not because of a claim cap, and its nine unverifiable claims are the cost of the excess. In the other
direction, the server-core round 1 verifier had 11 claims and no budget, and wrote its verdict at call
62, turn 48. Eight is therefore not a threshold the run measured. What the run does show is that the
two handoffs covering two verdicts (24 and 18 claims) were the ones that failed or came back thin, and
that a named write-by point turned an overrun into unverifiable rows instead of a lost round.

A conflict the change had to resolve. The handoff contract (`references/verification.md` section 2 and
the comment in `templates/handoff.md`) forbade giving the verifier any opinion of "remaining budget". A
tool-call budget read that way would be banned. The change distinguishes the run's remaining budget,
still excluded, from the verifier's own tool limit, which is a fact about the agent. The write-by
instruction pushes unfinished claims to `unverifiable`, never to `holds`, so it cannot make a verdict
more lenient.

What would refute it: a verifier given a budget line and write-by call that still ends with no
verdict, or a verdict whose `holds` rate rises when a budget is named.

Dedupe. `agents/verifier.md` says how to write the verdict (its own Bash call, a heredoc, full path) but
not when. `references/verification.md` section 2 had no budget field. `templates/handoff.md` had no budget
line. `references/capabilities.md` gives other workers a `Budget: <turns or tool calls>` line, but not
the verifier handoff. `references/parallel.md` section 10 handles the partial worker afterwards. Against
`general.md` it is distinct from all six entries, and it names the same mechanism as candidate 1. A single
general lesson covering both (write a file deliverable before the turn limit, Seen 2) would be a fair
consolidation target later, but it would need the grader, the auditor, and an eval case, and the
instruction fixes below remove the need for now.

Where it went. `skill/templates/handoff.md` gains a `budget:` line and the corrected comment, including
"one verdict per handoff". `skill/references/verification.md` section 2 gains a `budget` row and the
corrected exclusion sentence. `skill/agents/verifier.md`'s Verdict section now says to write by the
handoff's write-by call, or by call 50 when none is named, and to rewrite the verdict as claims are
settled. `skill/scripts/tests/test_templates.py` fills the new line in its handoff fixture so the
placeholder lint stays satisfied.

## Not done

No `lesson-commit`: neither candidate went to `general.md`, so there is nothing for it to commit, and
nothing was committed. `skill/scripts/drive.py` is unchanged; an enforcing control, such as a hook
counting a worker's calls since its last write under `.drive/`, would be the one change proposal the
investigation names. One stale line was noticed in the run itself: its STATE.md rule says not to tell a
researcher to use Edit, which `agents/researcher.md` now grants. It was left alone because that
repository is read-only here.
