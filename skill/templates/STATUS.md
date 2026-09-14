# STATUS · <project>
ladder: Missing → Scaffold → Partial → Local Proof → Live Proof → Operational → Done   (Dropped needs why:)

<!-- One row per behavioural claim. The key is the slug of the claim heading and never changes.
live is y or n, fixed when the row is created; lowering it needs a DECISIONS.md entry in the same
commit. Rows are never deleted. Only the orchestrator edits this file, and only a verifier's pass
moves a row to Local Proof or above. Evidence tokens are separated by "; ":
  test:<path>::<name>  severe:<path>::<name>  verdict:<path>  proof:<dir>  shot:<path>  live:<dir>
  ops:<url or path>  review:<path>  commit:<sha>  doc:<path>  why:<text>  planned:<path>::<name>
  sub:<sub-goal slug>, on every row when GOAL.md has sub-goals; lint --gate <phase> --sub <slug> checks only those rows
Required evidence: Scaffold commit:; Partial a test:; Local Proof test:, severe:, and a passing
verdict: (plus shot: on [ui] rows); Live Proof adds live: whose proof.json says live or device and
answers shim_differences; Operational adds ops:; Done is the Local Proof set plus review: pointing
at the final audit, live: when live is y, and doc: when user-facing behaviour changed; Dropped needs
why:. A row whose live proof can only come from a physical device carries why:device-only:<reason>:
it reaches Local Proof without a device, Live Proof only with a live: bundle whose proof.json says
device, and is never Done in a run without the owner's device. -->

| key | claim | live | status | evidence | updated |
|-----|-------|------|--------|----------|---------|
