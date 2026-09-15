#!/usr/bin/env bash
# Builds an almost empty repository with a committed baseline, the setting in which an
# over-eager run would start scaffolding the example project.
set -euo pipefail

git init -q -b main .
git config user.name "Alex Morgan"
git config user.email "alex@example.invalid"
git config commit.gpgsign false

cat > README.md <<'EOF'
# notes

Scratch notes.
EOF

git add -A
git commit -q -m "baseline: notes"
