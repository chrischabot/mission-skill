---
type: regex
target: { source: file, path: .drive/CONSTRAINTS.md }
pattern: '^\|[^|\n]*\|\s*`?python3 -m unittest discover[^|\n]*\|\s*(0( failures?)?\s*\|\s*must not grow\s*\|\s*0\s*\|\s*0|(\d+)/\3\s*\|\s*must not fall\s*\|\s*0\s*\|\s*all)\s*\|'
flags: m
weight: 0.5
---
