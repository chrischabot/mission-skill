"""Drive uses exactly three models. Every file that ships must agree, or the docs lie about the code.

These tests fail when any shipped file names a model other than the three pinned IDs, when an agent
file pins anything else, when a launch command passes another model, when a removed retry agent is
mentioned, or when the price table drifts from the prices the cost envelopes were computed from.
"""
import re
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2]
REPO = SKILL.parent

ALLOWED_IDS = {"claude-fable-5-1", "claude-opus-5", "claude-sonnet-5"}
# The Agent tool's per-call override accepts only aliases; these are the only ones drive passes.
ALLOWED_OVERRIDE_ALIASES = {"opus", "fable"}
# Files allowed to name an older model, only to describe Claude Code's own automatic fallback or why
# Haiku is excluded. Nothing in them may select such a model.
FALLBACK_DESCRIPTION_FILES = {"references/safety.md", "references/models.md"}

ID_PATTERN = re.compile(r"\bclaude-(?:fable|opus|sonnet|haiku|mythos)-[0-9][0-9a-z-]*")
OLD_NAME_PATTERN = re.compile(r"\b(?:Opus|Sonnet|Haiku) ?[34](?:\.[0-9])?\b|\bhaiku\b", re.IGNORECASE)
EXCLUSION_STATEMENT = re.compile(r"never selected|never used|not used|is never|off Haiku|defaults to Haiku|no Haiku|HAIKU_MODEL", re.IGNORECASE)
LAUNCH_MODEL_PATTERN = re.compile(r"--model[ =]\"?([A-Za-z0-9.\-\[\]]+)")


def shipped_files():
    """Every text file a user or agent reads: the skill (minus tests and eval results) and the repo root docs."""
    files = []
    for path in SKILL.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(SKILL).as_posix()
        if rel.startswith("scripts/tests/") or "/results/" in rel or "__pycache__" in rel:
            continue
        if path.suffix in {".md", ".json", ".yaml", ".yml", ".sh", ".py", ".js", ".toml"}:
            files.append(path)
    for name in ("README.md", "install.sh", "uninstall.sh", "HANDOFF.md"):
        path = REPO / name
        if path.exists():
            files.append(path)
    return files


def rel(path):
    try:
        return path.relative_to(SKILL).as_posix()
    except ValueError:
        return path.relative_to(REPO).as_posix()


class ModelIdentityTests(unittest.TestCase):
    def test_every_agent_pins_one_of_the_three_ids(self):
        agents = sorted((SKILL / "agents").glob("*.md"))
        self.assertTrue(agents, "no agent files found")
        for agent in agents:
            text = agent.read_text()
            match = re.search(r"^model:\s*(\S+)\s*$", text, re.MULTILINE)
            self.assertIsNotNone(match, "{} has no model line".format(agent.name))
            self.assertIn(match.group(1), ALLOWED_IDS, "{} pins {}".format(agent.name, match.group(1)))

    def test_no_shipped_file_names_another_model_id(self):
        offenders = []
        for path in shipped_files():
            for number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
                for found in ID_PATTERN.findall(line):
                    if found not in ALLOWED_IDS:
                        offenders.append("{}:{}: {}".format(rel(path), number, found))
        self.assertEqual(offenders, [], "model IDs outside the three pinned ones")

    def test_older_model_names_appear_only_where_fallback_is_described(self):
        offenders = []
        for path in shipped_files():
            if rel(path) in FALLBACK_DESCRIPTION_FILES:
                continue
            if rel(path) == "HANDOFF.md":
                continue  # a work log that records what was removed and why
            for number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
                if EXCLUSION_STATEMENT.search(line):
                    continue  # says an older model is never used, or that a harness default is moved off it
                for found in OLD_NAME_PATTERN.findall(line):
                    offenders.append("{}:{}: {}".format(rel(path), number, found))
        self.assertEqual(offenders, [], "older model names outside safety.md and models.md")

    def test_fallback_files_never_select_an_older_model(self):
        for name in FALLBACK_DESCRIPTION_FILES:
            text = (SKILL / name).read_text()
            self.assertNotRegex(text, r"model:\s*(claude-opus-4|claude-sonnet-4|claude-haiku|haiku)")
            self.assertNotRegex(text, r"--model\s+(claude-opus-4|claude-sonnet-4|claude-haiku|haiku)")

    def test_launch_commands_pass_only_pinned_ids(self):
        offenders = []
        for path in shipped_files():
            for number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
                for found in LAUNCH_MODEL_PATTERN.findall(line):
                    if found.startswith("<") or found.startswith("$"):
                        continue
                    if found not in ALLOWED_IDS:
                        offenders.append("{}:{}: --model {}".format(rel(path), number, found))
        self.assertEqual(offenders, [], "launch commands with a model other than the pinned IDs")

    def test_agent_tool_overrides_use_only_the_documented_aliases(self):
        offenders = []
        pattern = re.compile(r"model: \"([a-z0-9.\-]+)\"")
        for path in shipped_files():
            if path.suffix != ".md":
                continue
            for number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
                for found in pattern.findall(line):
                    if found not in ALLOWED_OVERRIDE_ALIASES:
                        offenders.append("{}:{}: model: \"{}\"".format(rel(path), number, found))
        self.assertEqual(offenders, [], "Agent-tool overrides other than opus or fable")

    def test_removed_retry_agents_are_not_mentioned(self):
        offenders = []
        for path in shipped_files():
            for number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
                if re.search(r"-legacy\b|legacy twin", line) and "contract" not in line and ".legacy." not in line:
                    offenders.append("{}:{}".format(rel(path), number))
        self.assertEqual(offenders, [], "mentions of the removed Opus 4.8 retry agents")
        self.assertFalse(list((SKILL / "agents").glob("*-legacy.md")))

    def test_roster_tables_name_only_pinned_ids(self):
        aliases = {"sonnet", "opus", "fable", "haiku", "`sonnet`", "`opus`", "`fable`", "`haiku`"}
        for name in ("SKILL.md", "references/models.md"):
            text = (SKILL / name).read_text()
            for row in re.findall(r"^\|[^\n]*\|$", text, re.MULTILINE):
                section = text[: text.find(row)]
                section = section[section.rfind("\n## "):]
                if "| Agent | Override | When |" in section:
                    continue  # the per-call override table names aliases on purpose
                cells = {cell.strip() for cell in row.strip("|").split("|")}
                self.assertFalse(cells & aliases, "{} roster row names an alias: {}".format(name, row))

    def test_price_table_matches_the_prices_the_envelopes_assume(self):
        text = (SKILL / "references/models.md").read_text()
        expected = {
            "Fable 5.1": ("$10", "$50", "$0.25"),
            "Opus 5": ("$5", "$25", "$0.50"),
            "Sonnet 5": ("$2", "$10", "$0.20"),
        }
        for model, (price_in, price_out, cache_read) in expected.items():
            row = re.search(r"^\| {}[^|]*\| (\S+) \| (\S+) \| (\S+) \|".format(re.escape(model)), text, re.MULTILINE)
            self.assertIsNotNone(row, "price row for {} missing".format(model))
            self.assertEqual(row.groups(), (price_in, price_out, cache_read), model)
        self.assertNotRegex(text, r"^\| (?:Opus 4|Sonnet 4|Haiku)", "price table lists a model drive does not use")


if __name__ == "__main__":
    unittest.main()
