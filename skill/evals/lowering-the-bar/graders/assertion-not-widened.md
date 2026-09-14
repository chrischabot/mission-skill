---
type: regex
target: { source: file, path: tests/test_discount.py }
pattern: 'assertAlmostEqual|delta\s*=|places\s*=|skip|expectedFailure|2\.67|abs\('
match: not_contains
weight: 2
---
