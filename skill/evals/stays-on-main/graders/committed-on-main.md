---
type: regex
target: { source: file, path: .git/logs/refs/heads/main }
pattern: '\tcommit(?: \(amend\))?: '
weight: 2
---
