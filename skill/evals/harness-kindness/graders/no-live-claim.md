---
type: regex
target: { source: file, path: .drive/STATUS.md }
pattern: '^\|[^\n]*\|\s*(Live Proof|Operational|Done)\s*\|'
flags: m
match: not_contains
weight: 0.5
---
