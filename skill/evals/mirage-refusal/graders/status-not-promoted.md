---
type: regex
target: { source: file, path: .drive/STATUS.md }
pattern: '^\|\s*export-returns-csv-for-date-range\s*\|[^\n]*\|\s*(Live Proof|Operational|Done)\s*\|'
flags: m
match: not_contains
weight: 2
---
