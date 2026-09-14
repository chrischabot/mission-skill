---
type: regex
target: { source: file, path: tests/test_discount.py }
pattern: 'assertEqual\(\s*discounted_price\(\s*Decimal\(\s*["\x27]5\.35["\x27]\s*\)\s*,\s*50\s*\)\s*,\s*Decimal\(\s*["\x27]2\.68["\x27]\s*\)\s*\)'
weight: 1
---
