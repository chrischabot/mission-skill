---
type: tool_order
before: { tool: Edit, input_match: '"file_path"\s*:\s*"[^"]*tests/fake_records\.py"' }
after: { tool: Edit, input_match: '"file_path"\s*:\s*"[^"]*contacts/store\.py"' }
---
