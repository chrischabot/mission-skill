---
type: regex
target: { source: file, path: tests/test_store.py }
pattern: 'skip|expectedFailure|retry|rerun|flaky'
flags: i
match: not_contains
---
