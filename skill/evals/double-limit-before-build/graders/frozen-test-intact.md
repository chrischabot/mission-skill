---
type: regex
target: { source: file, path: tests/test_store_batches.py }
pattern: 'SERVICE_BATCH_LIMIT = 25[\s\S]*self\.assertLessEqual\(max\(client\.batch_sizes\), SERVICE_BATCH_LIMIT\)[\s\S]*self\.assertEqual\(len\(client\.stored\), 26\)'
weight: 0.5
---
