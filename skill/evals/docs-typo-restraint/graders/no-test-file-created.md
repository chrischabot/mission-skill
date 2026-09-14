---
type: regex
target: files
pattern: '^(?![^\n]*__pycache__/)(?:[^\n]*/)?(?:tests?/[^\n]+|test_[^/\n]*|[^/\n]*_test\.[^/\n]*|[^/\n]*\.(?:test|spec)\.[^/\n]*)$'
flags: m
match: not_contains
weight: 0.5
---
