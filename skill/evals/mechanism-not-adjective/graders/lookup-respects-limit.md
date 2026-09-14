---
type: regex
target: { source: file, path: inventory/store.py }
pattern: 'MAX_HOST_PARAMETERS|\b999\b|chunk|batch|range\([^)]*,\s*len\(|json_each|carray|temp(orary)?\s+table'
flags: i
---
