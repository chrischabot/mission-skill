---
type: regex
target: { source: file, path: .drive/handoffs/half-values-round-to-even.md }
pattern: '^## Claims[ \t]*$[\s\S]*^## Scope[ \t]*$[\s\S]*^## Validation[ \t]*$[\s\S]*^## Evidence inputs[ \t]*$(?:\n(?!## )(?![^\n]*(?:report\.json|report\.md|workers/))[^\n]*)*\n## Lessons that apply to this task'
flags: m
---
