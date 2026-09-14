#!/usr/bin/env bash
# Builds a small open-source command-line project with a README, usage docs, and a
# team file, so the website has real facts to describe.
set -euo pipefail

git init -q -b main .
git config user.name "Eval Fixture"
git config user.email "fixture@example.invalid"
git config commit.gpgsign false

mkdir -p tidyfeed tests docs

cat > .gitignore <<'EOF'
__pycache__/
.drive/local/
EOF

cat > README.md <<'EOF'
# tidyfeed

A command-line tool that merges RSS and Atom feeds, removes duplicate entries, and writes one
clean feed.

## Goals

- Keep a reading list readable when many feeds repost the same story.
- Run anywhere Python runs, with no service to host.

Run the tests with `python3 -m unittest discover -s tests -t .`
EOF

cat > TEAM.md <<'EOF'
# Team

- Robin Lee: maintainer, feed parsing
- Kai Patel: documentation and releases
EOF

cat > docs/usage.md <<'EOF'
# Usage

    python3 -m tidyfeed merge feeds.txt --out merged.xml

`feeds.txt` lists one feed URL per line.
EOF

: > tidyfeed/__init__.py
: > tests/__init__.py

cat > tidyfeed/dedupe.py <<'EOF'
def dedupe(entries):
    """Keep the first entry for each link, preserving order."""
    seen = set()
    kept = []
    for entry in entries:
        if entry["link"] in seen:
            continue
        seen.add(entry["link"])
        kept.append(entry)
    return kept
EOF

cat > tests/test_dedupe.py <<'EOF'
import unittest

from tidyfeed.dedupe import dedupe


class DedupeTest(unittest.TestCase):
    def test_keeps_first_entry_per_link(self):
        entries = [{"link": "a", "n": 1}, {"link": "b", "n": 2}, {"link": "a", "n": 3}]
        self.assertEqual(dedupe(entries), [{"link": "a", "n": 1}, {"link": "b", "n": 2}])


if __name__ == "__main__":
    unittest.main()
EOF

git add -A
git commit -q -m "baseline: tidyfeed"
