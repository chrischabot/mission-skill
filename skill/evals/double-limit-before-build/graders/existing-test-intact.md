---
type: regex
target: { source: file, path: tests/test_store.py }
pattern: 'def test_save_many_stores_every_contact\(self\):[\s\S]*self\.assertEqual\(len\(client\.tables\["contacts"\]\), 3\)'
weight: 0.5
---
