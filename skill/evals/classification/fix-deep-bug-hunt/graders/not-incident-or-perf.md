---
type: regex
target: { source: file, path: .drive/GOAL.md }
pattern: '^\s*(shape|variant):\s*["\x27]?(fix/)?(incident|perf)\b'
flags: m
match: not_contains
---
