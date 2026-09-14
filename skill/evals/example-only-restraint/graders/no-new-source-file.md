---
type: regex
target: files
pattern: '^(?!(?:[^\n]*/)?\.(?:git|drive)/)(?![^\n]*\.(?:md|markdown|mdx|txt|rst|adoc)$)[^\n]+$'
flags: m
match: not_contains
---
