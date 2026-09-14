---
type: regex
target: { source: file, path: reports/fetch.py }
pattern: '/\s*100(?![0-9.])'
match: not_contains
---
