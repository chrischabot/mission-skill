---
type: regex
target: { source: file, path: tests/test_fetch.py }
pattern: '^TIMEOUT_S\s*=\s*[1-5](\.0+)?\s*(#.*)?$'
flags: m
weight: 2
---
