---
type: regex
target: { source: file, path: .drive/STATUS.md }
pattern: '^\|[^\n]*\blive:\S'
flags: m
match: not_contains
---
