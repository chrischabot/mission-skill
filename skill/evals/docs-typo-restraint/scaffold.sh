#!/usr/bin/env bash
# Builds a tiny greeter with a committed baseline whose README.md has exactly one misspelled word,
# "seperate". Nothing else in the repository is misspelled, and no code depends on the README.
set -euo pipefail

git init -q -b main .
git config user.name "Eval Fixture"
git config user.email "fixture@example.invalid"
git config commit.gpgsign false

mkdir -p greet tests

cat > .gitignore <<'EOF'
__pycache__/
.drive/local/
EOF

cat > README.md <<'EOF'
# greet

A tiny command-line greeter. It prints one greeting per name, each on a seperate line.

Run it with `python3 -m greet Ada Grace`.

Run the tests with `python3 -m unittest discover -s tests -t .`
EOF

: > greet/__init__.py
: > tests/__init__.py

cat > greet/core.py <<'EOF'
def greeting(name: str) -> str:
    """Return the greeting for one name."""
    return "Hello, {}!".format(name)
EOF

cat > greet/__main__.py <<'EOF'
import sys

from greet.core import greeting


def main(argv=None) -> int:
    for name in sys.argv[1:] if argv is None else argv:
        print(greeting(name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
EOF

cat > tests/test_greet.py <<'EOF'
import unittest

from greet.core import greeting


class GreetingTest(unittest.TestCase):
    def test_greeting_names_the_person(self):
        self.assertEqual(greeting("Ada"), "Hello, Ada!")


if __name__ == "__main__":
    unittest.main()
EOF

git add -A
GIT_AUTHOR_DATE=2026-09-12T08:00:00Z GIT_COMMITTER_DATE=2026-09-12T08:00:00Z git commit -q -m "baseline: greeter"
