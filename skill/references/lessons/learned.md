# Learned lessons

Rules that lean runs verified and promoted on their own with `drive.py promote`, each appended with a
one-line source and committed alone. The lean planner reads this file with `general.md` before every
plan and quotes the rules that apply in PLAN.md. An entry here has not been through the rigorous
lesson loop's dedupe and audit: consolidation may merge one into `general.md`, where the full lesson
template applies, or retire it with a tombstone in `retired.md`. To undo a promotion, revert its
commit. Cap: 80 entries.

Each entry is a one-sentence rule as its heading, then Because, Verified by, Source, and Seen. When a
later run records a rule this file already holds, promotion raises that entry's Seen count instead of
adding a second one.

## Entries
