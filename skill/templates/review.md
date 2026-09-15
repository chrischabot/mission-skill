# REVIEW · <phase> · round <n>
verdict: <ready | not ready>
round: <n>/<bound>
artifact: <path of the reviewed file> at <short sha>
reviewer: drive:<agent> · model: <model it ran as>

<!-- One file per review round, written by the reviewing agent before its final message:
.drive/reviews/<YYYY-MM-DD>-<phase>-review-r<n>.md, with the sub-goal slug after the phase when the
round reviews one sub-goal. The verdict and round lines stay in the first lines, because
`drive.py lint --gate <phase>` reads them there. Report every finding with its severity and
confidence; the orchestrator filters afterwards. -->

## Blocking
- <where> · <what is wrong> · <proposed fix> · confidence <25|50|75|100>, or none

## Should fix
- <where> · <what is wrong> · <proposed fix> · confidence <25|50|75|100>, or none

## Notes
- <anything else the author or the auditor should know>, or none
