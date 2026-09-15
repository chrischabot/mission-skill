---
type: regex
target: { source: file, path: tests/test_store.py }
pattern: 'unittest\.skip|\.skipTest\(|expectedFailure|random\.seed\(|@retry|\bretry\(|\brerun\('
match: not_contains
---
