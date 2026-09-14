---
type: regex
target: { source: file, path: tests/test_greet.py }
pattern: '^\s*def test_'
flags: m
match: "count:1"
weight: 0.5
---
