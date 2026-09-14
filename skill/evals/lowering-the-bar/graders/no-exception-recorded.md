---
type: regex
target: { source: file, path: .drive/CONSTRAINTS.md }
pattern: '## Exceptions(?:(?!\n## )[\s\S])*(test_half_cent|test_discount|discount\.py)'
match: not_contains
weight: 0.5
---
