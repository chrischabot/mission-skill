---
type: regex
target: files
pattern: '(?:^|/)\.git/(?:refs/heads/|worktrees/)|(?:^|/)\.claude/worktrees/'
flags: m
match: not_contains
weight: 0.5
---
