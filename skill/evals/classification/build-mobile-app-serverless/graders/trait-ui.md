---
type: regex
target: { source: file, path: .drive/GOAL.md }
pattern: '^[ \t]*traits:[ \t]*(?:\{[^\n]*?\bconfirmed:[ \t]*\[(?:[^\]\n]*,)?[ \t]*["\x27]?ui["\x27]?[ \t]*[,\]]|\n(?:[ \t]+[a-z_]+:[^\n]*\n)*?[ \t]+confirmed:[ \t]*(?:\[(?:[^\]\n]*,)?[ \t]*["\x27]?ui["\x27]?[ \t]*[,\]]|\n(?:[ \t]+-[^\n]*\n)*?[ \t]+-[ \t]*["\x27]?ui["\x27]?[ \t]*$))'
flags: m
---
