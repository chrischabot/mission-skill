#!/usr/bin/env python3
"""validate-registry.py - mechanical validator for the mission requirement registry.

Usage:
  validate-registry.py [--registry .mission/requirements.yaml] [--tests DIR ...]
                       [--root DIR] [--spec PATH] [--no-pyyaml] [--quiet]

Fails (exit 1) when:
  - the registry cannot be read or parsed
  - an entry has no id, a malformed id, or an id used twice
    (id grammar: DOMAIN-NNN where DOMAIN is 2-6 capitals/digits starting with a letter and
    NNN is 3-4 digits, e.g. API-012, REQ-001, OUT-003, A11Y-002; or BUG-<n>-<C|E|U><n>)
  - an entry lacks text, owner or status, or uses an unknown enum value
  - a non-withdrawn entry has no oracle_kind
  - status implemented/verified has no oracles; status live-only has no live checks
  - an oracle path (the part before '::') does not exist under --root
  - an implemented/verified entry's oracle file does not contain '@req:<ID>'
  - supersedes names an unknown id
  - a file under a --tests DIR cites '@req:<ID>' for an unknown, malformed or withdrawn id
  - with --spec: a bold requirement id in the spec is missing from the registry, or a
    non-withdrawn registry id is missing from the spec
Warnings (exit 0) cover softer smells, e.g. a P1 entry whose text still carries
'[NEEDS CLARIFICATION', or an implemented entry that no scanned test cites.

Exit codes: 0 pass (warnings allowed); 1 validation or parse failure; 2 usage error.

Root: oracle paths resolve against --root. Default: the parent of the registry's directory
when that directory is named '.mission', otherwise the current working directory.

Parser: PyYAML (yaml.safe_load) when importable, unless --no-pyyaml. Otherwise a built-in
parser for this YAML subset (the subset used by templates/requirements.yaml):
  - '#' comments (whole line, or after whitespace outside quotes); blank lines
  - spaces for indentation (tabs rejected)
  - block mappings 'key: value' with keys matching [A-Za-z_][A-Za-z0-9_-]*
  - block sequences '- item', including '- key: value' mapping items
  - a sequence may sit at the same indent as its parent key
  - scalars: plain, "double-quoted" (JSON escapes), 'single-quoted' ('' escapes),
    integers, true/false, null/~
  - flow sequences of scalars on one line: [a, "b", 'c'] (no nesting)
Not supported (rejected with a line number): block scalars (| >), flow mappings {},
anchors/aliases (& *), tags (!), multi-line plain or quoted scalars, plain scalars
containing ': ' (quote them), multiple documents.

No network access. Read-only: the script never writes files.
"""

import argparse
import json
import os
import re
import sys

ID_RE = re.compile(r"(?:[A-Z][A-Z0-9]{1,5}-\d{3,4}|BUG-\d{1,6}-[CEU]\d{1,2})")
CITE_RE = re.compile(r"@req:([A-Za-z0-9-]+)")
SPEC_ID_RE = re.compile(r"\*\*((?:BUG-\d{1,6}-[CEU]\d{1,2}|[A-Z][A-Z0-9]{1,5}-\d{3,4}))(?![A-Za-z0-9-])")
KEY_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_-]*):(?=\s|\Z)")
INT_RE = re.compile(r"-?\d+")

STATUSES = {"planned", "implemented", "verified", "live-only", "withdrawn"}
KINDS = {"outcome", "requirement", "nfr", "metric", "bugfix", "parity", "content-claim",
         "test-architecture"}
EARS = {"ubiquitous", "event", "state", "optional", "unwanted", "complex", "none"}
PRIORITIES = {"P1", "P2", "P3"}
ORACLE_KINDS = {"unit", "property", "contract", "integration", "scenario", "e2e", "visual",
                "a11y", "live", "human", "review"}
NEEDS_ORACLES = {"implemented", "verified"}
SKIP_DIRS = {".git", "node_modules", ".build", "build", "dist", "DerivedData", ".venv",
             "venv", "__pycache__", ".next", "coverage", "tmp"}
MAX_SCAN_BYTES = 2 * 1024 * 1024


class ParseError(Exception):
    pass


# ---------------------------------------------------------------- YAML subset parser

def _strip_comment(raw):
    """Remove a trailing comment that is outside quotes."""
    quote = None
    prev = " "
    escaped = False
    for idx, ch in enumerate(raw):
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\" and quote == '"':
                escaped = True
            elif ch == quote:
                quote = None
        elif ch in ("'", '"') and prev in (" ", "[", ",", ":", "-"):
            quote = ch
        elif ch == "#" and prev in (" ", "\t"):
            return raw[:idx]
        prev = ch
    return raw


def _tokenize(text):
    lines = []
    for num, raw in enumerate(text.splitlines(), 1):
        if raw.rstrip() == "...":
            break
        if raw.rstrip() == "---":
            if lines:
                raise ParseError("line %d: multiple documents are not supported" % num)
            continue
        body = _strip_comment(raw).rstrip()
        if not body.strip():
            continue
        lead = body[: len(body) - len(body.lstrip())]
        if "\t" in lead:
            raise ParseError("line %d: tab indentation is not supported" % num)
        lines.append([num, len(lead), body.strip()])
    return lines


def _is_dash(content):
    return content == "-" or content.startswith("- ")


def _split_flow(inner, num):
    items, buf, quote = [], "", None
    for ch in inner:
        if quote:
            buf += ch
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            buf += ch
        elif ch == ",":
            items.append(buf.strip())
            buf = ""
        elif ch in "[]{}":
            raise ParseError("line %d: nested flow collections are not supported" % num)
        else:
            buf += ch
    if quote:
        raise ParseError("line %d: unterminated quote in flow sequence" % num)
    if buf.strip():
        items.append(buf.strip())
    elif items:
        raise ParseError("line %d: trailing comma in flow sequence" % num)
    return items


def _scalar(token, num, allow_flow=True):
    if not token:
        raise ParseError("line %d: empty value in flow sequence" % num)
    if token.startswith("["):
        if not allow_flow or not token.endswith("]"):
            raise ParseError("line %d: unsupported or multi-line flow sequence" % num)
        return [_scalar(part, num, False) for part in _split_flow(token[1:-1], num)]
    if token.startswith('"'):
        if len(token) < 2 or not token.endswith('"'):
            raise ParseError("line %d: unterminated or multi-line double-quoted scalar" % num)
        try:
            return json.loads(token)
        except ValueError:
            raise ParseError("line %d: unsupported escape in double-quoted scalar" % num)
    if token.startswith("'"):
        if len(token) < 2 or not token.endswith("'"):
            raise ParseError("line %d: unterminated or multi-line single-quoted scalar" % num)
        return token[1:-1].replace("''", "'")
    if token[0] in "{&*!|>%@`":
        raise ParseError("line %d: unsupported YAML construct %r" % (num, token[0]))
    if ": " in token:
        raise ParseError("line %d: plain scalar contains ': ' - quote the value" % num)
    if token in ("null", "~", "Null", "NULL"):
        return None
    if token in ("true", "True", "TRUE"):
        return True
    if token in ("false", "False", "FALSE"):
        return False
    if INT_RE.fullmatch(token):
        return int(token)
    return token


def _block(lines, i, indent):
    if _is_dash(lines[i][2]):
        return _sequence(lines, i, indent)
    return _mapping(lines, i, indent)


def _sequence(lines, i, indent):
    items = []
    while i < len(lines):
        num, ind, content = lines[i]
        if ind < indent:
            break
        if ind > indent:
            raise ParseError("line %d: unexpected indentation" % num)
        if not _is_dash(content):
            break
        rest = content[1:].strip()
        if not rest:
            i += 1
            if i < len(lines) and lines[i][1] > indent:
                value, i = _block(lines, i, lines[i][1])
            else:
                value = None
            items.append(value)
            continue
        if KEY_RE.match(rest):
            column = indent + (len(content) - len(rest))
            lines[i] = [num, column, rest]
            value, i = _mapping(lines, i, column)
            items.append(value)
            continue
        items.append(_scalar(rest, num))
        i += 1
    return items, i


def _mapping(lines, i, indent):
    result = {}
    while i < len(lines):
        num, ind, content = lines[i]
        if ind < indent:
            break
        if ind > indent:
            raise ParseError("line %d: unexpected indentation" % num)
        if _is_dash(content):
            raise ParseError("line %d: sequence item where a mapping key was expected" % num)
        match = KEY_RE.match(content)
        if not match:
            raise ParseError("line %d: expected 'key: value'" % num)
        key = match.group(1)
        rest = content[match.end():].strip()
        if key in result:
            raise ParseError("line %d: duplicate key %r" % (num, key))
        i += 1
        if not rest:
            nxt = lines[i] if i < len(lines) else None
            if nxt and (nxt[1] > indent or (nxt[1] == indent and _is_dash(nxt[2]))):
                value, i = _block(lines, i, nxt[1])
            else:
                value = None
        else:
            value = _scalar(rest, num)
        result[key] = value
    return result, i


def parse_subset(text):
    lines = _tokenize(text)
    if not lines:
        return None
    value, i = _block(lines, 0, lines[0][1])
    if i != len(lines):
        raise ParseError("line %d: content after the top-level block" % lines[i][0])
    return value


def load_registry(path, use_pyyaml):
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    if use_pyyaml:
        try:
            import yaml  # optional dependency
        except ImportError:
            yaml = None
        if yaml is not None:
            try:
                return yaml.safe_load(text), "pyyaml"
            except yaml.YAMLError as exc:
                raise ParseError(str(exc).replace("\n", " "))
    return parse_subset(text), "subset"


# ---------------------------------------------------------------- validation

class Report:
    def __init__(self):
        self.failures = []
        self.warnings = []

    def fail(self, msg):
        self.failures.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def default_root(registry):
    parent = os.path.dirname(os.path.abspath(registry))
    if os.path.basename(parent) == ".mission":
        return os.path.dirname(parent)
    return os.getcwd()


def _check_enum(rep, rid, field, value, allowed):
    for item in _as_list(value):
        if not isinstance(item, str) or item not in allowed:
            rep.fail("%s: %s value %r not in {%s}" % (rid, field, item, ", ".join(sorted(allowed))))


def _entries(data, rep):
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("requirements"), list):
        return data["requirements"]
    rep.fail("registry: expected a top-level 'requirements:' sequence (or a bare sequence)")
    return []


def validate_entries(entries, root, rep):
    """Return {id: status} for well-formed ids."""
    known = {}
    first_seen = {}
    for pos, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            rep.fail("entry %d: not a mapping" % pos)
            continue
        rid = entry.get("id")
        if not isinstance(rid, str) or not rid:
            rep.fail("entry %d: missing id" % pos)
            continue
        if not ID_RE.fullmatch(rid):
            rep.fail("entry %d: malformed id %r (expected DOMAIN-NNN, OUT-NNN, REQ-NNN or BUG-<n>-<C|E|U><n>)"
                     % (pos, rid))
            continue
        if rid in first_seen:
            rep.fail("%s: duplicate id (entries %d and %d)" % (rid, first_seen[rid], pos))
            continue
        first_seen[rid] = pos
        status = entry.get("status")
        known[rid] = status if isinstance(status, str) else None
        for field in ("text", "owner", "status"):
            if entry.get(field) in (None, ""):
                rep.fail("%s: missing required field '%s'" % (rid, field))
        if status is not None:
            _check_enum(rep, rid, "status", status, STATUSES)
        if entry.get("kind") is not None:
            _check_enum(rep, rid, "kind", entry.get("kind"), KINDS)
        if entry.get("ears") is not None:
            _check_enum(rep, rid, "ears", entry.get("ears"), EARS)
        if entry.get("priority") is not None:
            _check_enum(rep, rid, "priority", entry.get("priority"), PRIORITIES)
        kinds = _as_list(entry.get("oracle_kind"))
        if status != "withdrawn" and not kinds:
            rep.fail("%s: no oracle_kind (every requirement names how it will be proven)" % rid)
        _check_enum(rep, rid, "oracle_kind", kinds, ORACLE_KINDS)
        oracles = _as_list(entry.get("oracles"))
        if status in NEEDS_ORACLES and not oracles:
            rep.fail("%s: status %s but no oracles" % (rid, status))
        if status == "live-only" and not _as_list(entry.get("live")):
            rep.fail("%s: status live-only but no live checks" % rid)
        for ref in oracles:
            _check_oracle(rep, rid, status, ref, root)
        text = entry.get("text") if isinstance(entry.get("text"), str) else ""
        if "[NEEDS CLARIFICATION" in text and entry.get("priority") == "P1" and status != "withdrawn":
            rep.warn("%s: P1 requirement still carries [NEEDS CLARIFICATION] (blocks spec review)" % rid)
    for entry in entries:
        if isinstance(entry, dict) and entry.get("supersedes") is not None:
            for target in _as_list(entry.get("supersedes")):
                if not isinstance(target, str) or target not in known:
                    rep.fail("%s: supersedes unknown id %r" % (entry.get("id"), target))
    return known


def _check_oracle(rep, rid, status, ref, root):
    if not isinstance(ref, str) or not ref.strip():
        rep.fail("%s: oracle reference is not a non-empty string: %r" % (rid, ref))
        return
    path, _, name = ref.partition("::")
    full = os.path.join(root, path.strip())
    if not os.path.isfile(full):
        rep.fail("%s: oracle path does not exist: %s (root %s)" % (rid, path.strip(), root))
        return
    if status not in NEEDS_ORACLES:
        return
    try:
        with open(full, "r", encoding="utf-8", errors="replace") as handle:
            body = handle.read(MAX_SCAN_BYTES)
    except OSError as exc:
        rep.fail("%s: cannot read oracle %s: %s" % (rid, path.strip(), exc))
        return
    if not re.search(r"@req:" + re.escape(rid) + r"(?![A-Za-z0-9-])", body):
        rep.fail("%s: oracle %s does not cite @req:%s (citation must be bidirectional)"
                 % (rid, path.strip(), rid))
    elif name.strip() and name.strip() not in body:
        rep.warn("%s: test name %r not found verbatim in %s" % (rid, name.strip(), path.strip()))


def scan_tests(dirs, known, rep):
    """Return the set of ids cited by files under dirs."""
    cited = set()
    for base in dirs:
        if not os.path.isdir(base):
            rep.fail("--tests %s: not a directory" % base)
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for filename in sorted(filenames):
                path = os.path.join(dirpath, filename)
                try:
                    if os.path.getsize(path) > MAX_SCAN_BYTES:
                        continue
                    with open(path, "rb") as handle:
                        raw = handle.read()
                except OSError:
                    continue
                if b"\0" in raw or b"@req:" not in raw:
                    continue
                text = raw.decode("utf-8", errors="replace")
                for lineno, line in enumerate(text.splitlines(), 1):
                    for match in CITE_RE.finditer(line):
                        cid = match.group(1).rstrip("-")
                        where = "%s:%d" % (path, lineno)
                        if not ID_RE.fullmatch(cid):
                            rep.fail("%s: malformed citation @req:%s" % (where, cid))
                        elif cid not in known:
                            rep.fail("%s: cites unknown id @req:%s" % (where, cid))
                        elif known[cid] == "withdrawn":
                            rep.fail("%s: cites withdrawn id @req:%s (cite the superseding id)"
                                     % (where, cid))
                        else:
                            cited.add(cid)
    return cited


def check_spec(spec, known, rep):
    try:
        with open(spec, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        rep.fail("--spec %s: %s" % (spec, exc))
        return
    in_spec = set(SPEC_ID_RE.findall(text))
    for rid in sorted(in_spec - set(known)):
        rep.fail("%s: in spec %s but not in registry" % (rid, spec))
    for rid in sorted(set(known) - in_spec):
        if known[rid] != "withdrawn":
            rep.fail("%s: in registry but not in spec %s (withdraw it or add it to the spec)" % (rid, spec))


# ---------------------------------------------------------------- main

def build_parser():
    parser = argparse.ArgumentParser(
        prog="validate-registry.py",
        description=(__doc__ or "").split("\n", 1)[-1],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: validate-registry.py --registry .mission/requirements.yaml "
               "--tests tests --tests ios/AppTests --spec .mission/SPEC.md",
    )
    parser.add_argument("--registry", default=".mission/requirements.yaml",
                        help="registry file (default: .mission/requirements.yaml)")
    parser.add_argument("--tests", action="append", default=[], metavar="DIR",
                        help="directory to scan for @req:<ID> citations (repeatable)")
    parser.add_argument("--root", default=None,
                        help="directory oracle paths resolve against (default: parent of .mission/, "
                             "else the current directory)")
    parser.add_argument("--spec", default=None,
                        help="optional SPEC.md; bold ids must match non-withdrawn registry ids")
    parser.add_argument("--no-pyyaml", action="store_true",
                        help="force the built-in YAML subset parser even if PyYAML is installed")
    parser.add_argument("--quiet", action="store_true", help="print only failures and the result line")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    rep = Report()
    print("validate-registry: %s" % args.registry)
    if not os.path.isfile(args.registry):
        print("FAIL registry not found: %s" % args.registry)
        print("result: FAIL (1 failure, 0 warnings)")
        return 1
    try:
        data, parser_name = load_registry(args.registry, not args.no_pyyaml)
    except (ParseError, UnicodeDecodeError, OSError) as exc:
        print("FAIL cannot parse registry: %s" % exc)
        print("result: FAIL (1 failure, 0 warnings)")
        return 1
    root = os.path.abspath(args.root) if args.root else default_root(args.registry)
    entries = _entries(data, rep)
    known = validate_entries(entries, root, rep)
    counts = {}
    for status in known.values():
        counts[status] = counts.get(status, 0) + 1
    summary = ", ".join("%s %d" % (k, counts[k]) for k in sorted(counts, key=str))
    if not args.quiet:
        print("parser: %s | root: %s" % (parser_name, root))
        print("requirements: %d (%s)" % (len(known), summary or "none"))
    if args.tests:
        cited = scan_tests(args.tests, known, rep)
        for rid in sorted(known):
            if known[rid] in NEEDS_ORACLES and rid not in cited:
                rep.warn("%s: status %s but no scanned test cites @req:%s" % (rid, known[rid], rid))
        if not args.quiet:
            active = [r for r in known if known[r] != "withdrawn"]
            print("citations: %d of %d active ids cited under %s"
                  % (len(cited), len(active), ", ".join(args.tests)))
    if args.spec:
        check_spec(args.spec, known, rep)
    for msg in rep.failures:
        print("FAIL " + msg)
    if not args.quiet:
        for msg in rep.warnings:
            print("WARN " + msg)
    verdict = "FAIL" if rep.failures else "PASS"
    print("result: %s (%d failure%s, %d warning%s)" % (
        verdict, len(rep.failures), "" if len(rep.failures) == 1 else "s",
        len(rep.warnings), "" if len(rep.warnings) == 1 else "s"))
    return 1 if rep.failures else 0


if __name__ == "__main__":
    sys.exit(main())
