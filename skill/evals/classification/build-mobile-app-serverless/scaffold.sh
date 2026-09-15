#!/usr/bin/env bash
# Builds an almost empty repository with a committed baseline, so intake sees a
# greenfield project with version control already in place.
set -euo pipefail

git init -q -b main .
git config user.name "Alex Morgan"
git config user.email "alex@example.invalid"
git config commit.gpgsign false

cat > .gitignore <<'EOF'
.drive/local/
EOF

cat > README.md <<'EOF'
# plant-care

Nothing here yet.
EOF

git add -A
git commit -q -m "baseline: empty project"
