#!/usr/bin/env bash
# Builds a throwaway repository with a committed baseline: a slug helper whose
# only defect is that it strips leading hyphens but keeps trailing ones.
set -euo pipefail

git init -q -b main .
git config user.name "Eval Fixture"
git config user.email "fixture@example.invalid"
git config commit.gpgsign false

mkdir -p textutil tests

cat > .gitignore <<'EOF'
__pycache__/
.drive/local/
EOF

cat > README.md <<'EOF'
# textutil

Small text helpers.

Run the tests with `python3 -m unittest discover -s tests -t .`
EOF

: > textutil/__init__.py
: > tests/__init__.py

cat > textutil/slug.py <<'EOF'
import re


def slugify(title: str) -> str:
    """Lower-case a title and join its words with single hyphens."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower())
    return slug.lstrip("-")
EOF

cat > tests/test_slug.py <<'EOF'
import unittest

from textutil.slug import slugify


class SlugifyTest(unittest.TestCase):
    def test_joins_words_with_hyphens(self):
        self.assertEqual(slugify("Release notes 2024"), "release-notes-2024")

    def test_drops_leading_punctuation(self):
        self.assertEqual(slugify("...and then"), "and-then")


if __name__ == "__main__":
    unittest.main()
EOF

git add -A
git commit -q -m "baseline: slug helper"
