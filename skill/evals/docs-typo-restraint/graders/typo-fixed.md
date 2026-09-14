---
type: regex
target: { source: file, path: README.md }
pattern: '^(?![\s\S]*seperate)(?=[\s\S]*python3 -m greet Ada Grace)(?=[\s\S]*python3 -m unittest discover -s tests -t \.)[\s\S]*It prints one greeting per name, each on a separate line\.'
weight: 2
---
