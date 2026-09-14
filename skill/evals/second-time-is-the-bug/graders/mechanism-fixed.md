---
type: regex
target: { source: file, path: reports/fetch.py }
pattern: '/\s*1_?000(\.0+)?\b|/\s*1e3\b|\*\s*0?\.001\b|RETRY_DELAY_S(ECONDS)?\s*=\s*0?\.8\b'
weight: 2
---
