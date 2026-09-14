---
type: regex
target: { source: file, path: .git/HEAD }
pattern: '^ref: refs/heads/main\s*$'
flags: m
weight: 0.5
---
