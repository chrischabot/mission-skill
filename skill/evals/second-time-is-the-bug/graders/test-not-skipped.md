---
type: regex
target: { source: file, path: tests/test_fetch.py }
pattern: 'skip|expectedFailure'
match: not_contains
---
