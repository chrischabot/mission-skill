---
type: tool_used
tool: Bash
input_match: 'git\s+(?:-[cC]\s+\S+\s+|--?[a-z][a-z-]*(?:=\S+)?\s+)*commit(?![\w-])[\s\S]*?Claim:[\s\S]*?Evidence:|Claim:[\s\S]*?Evidence:[\s\S]*?git\s+(?:-[cC]\s+\S+\s+|--?[a-z][a-z-]*(?:=\S+)?\s+)*commit(?![\w-])\s[^\n]*?(-F|--file)'
min: 1
---
