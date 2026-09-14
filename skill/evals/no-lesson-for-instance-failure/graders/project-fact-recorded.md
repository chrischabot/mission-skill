---
type: regex
target: trace
pattern: '\\?"name\\?"\s*:\s*\\?"(Edit|Write|MultiEdit)\\?"[^\n]{0,300}?\\?"file_path\\?"\s*:\s*\\?"[^"\\\n]*(STATE|LESSONS)\.md\\?"[^\n]{0,4000}?(EUR|regions\.toml)|\\?"command\\?"\s*:\s*\\?"[^\n]{0,400}?(>>?|tee(\s+-a)?)\s*[^\s"\\]*\.drive/(STATE|LESSONS)\.md[^\n]{0,4000}?(EUR|regions\.toml)'
weight: 0.5
---
