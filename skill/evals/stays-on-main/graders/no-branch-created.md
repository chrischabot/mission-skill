---
type: tool_used
tool: Bash
input_match: '(?:"command"\s*:\s*"|[;&|(]\s*|\\n\s*|\$\(\s*)(?:sudo\s+)?git\s+(?:-C\s+\S+\s+)?(?:checkout\s+(?:-b|-B|--orphan)\b|switch\s+(?:-c|-C|--create|--orphan)\b|branch\s+(?:(?:-f|--force|-t|--track|--no-track|-c|-C|--copy)\s+)*(?!-)(?:\\?["\x27])?[A-Za-z0-9_./-]|worktree\s+add\b)'
min: 0
max: 0
weight: 2
---
