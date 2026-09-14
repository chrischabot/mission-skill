"""install.sh and uninstall.sh against a fake `claude`, in a throwaway HOME."""
import os
import subprocess

from helpers import DriveTestCase, SKILL

REPO = SKILL.parent
FAKE_CLAUDE = """#!/bin/sh
echo "$*" >> "$FAKE_CLAUDE_LOG"
if [ "$1 $2" = "plugin enable" ]; then
  exit "${FAKE_ENABLE_EXIT:-0}"
fi
if [ "$1 $2" = "plugin list" ]; then
  printf 'Installed plugins:\\n\\n'
  if [ "${FAKE_PLUGIN_LISTED:-1}" = "1" ]; then
    printf '  \\342\\235\\257 drive@skills-dir\\n    Version: 0.1.0\\n    Scope: user\\n    Status: %s\\n' "$FAKE_PLUGIN_STATUS"
  fi
fi
exit 0
"""


class InstallTests(DriveTestCase):
    def setUp(self):
        super().setUp()
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        claude = self.bin / "claude"
        claude.write_text(FAKE_CLAUDE)
        claude.chmod(0o755)
        self.log = self.tmp / "claude.log"

    def script(self, name, *args, status="✔ enabled", extra=None):
        env = dict(os.environ)
        env.update({"PATH": "{}:{}".format(self.bin, os.environ.get("PATH", "")), "FAKE_CLAUDE_LOG": str(self.log),
                    "FAKE_PLUGIN_STATUS": status, "DRIVE_INSTALL_SKIP_TESTS": "1", "HOME": str(self.home)})
        env.update(extra or {})
        return subprocess.run(["bash", str(REPO / name), *args], capture_output=True, text=True, env=env, timeout=120)

    def test_install_accepts_the_skills_directory_loaded_status_and_prints_the_settings(self):
        result = self.script("install.sh", status="✔ loaded")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Enabled drive@skills-dir", result.stdout)
        self.assertIn("DRIVE_SETTINGS='{", result.stdout)

    def test_install_prints_enabled_only_when_the_enable_command_succeeds(self):
        result = self.script("install.sh", status="✔ loaded", extra={"FAKE_ENABLE_EXIT": "1"})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("Enabled drive@skills-dir", result.stdout)
        self.assertIn("did not succeed", result.stderr)

    def test_install_fails_when_the_plugin_is_not_listed(self):
        result = self.script("install.sh", status="✔ loaded", extra={"FAKE_PLUGIN_LISTED": "0"})
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("not listed", result.stderr)
        self.assertNotIn("DRIVE_SETTINGS=", result.stdout)

    def calls(self):
        return self.log.read_text() if self.log.exists() else ""

    def test_install_enables_the_plugin_and_writes_no_settings_file(self):
        result = self.script("install.sh")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("plugin enable drive@skills-dir", self.calls())
        self.assertTrue((self.home / ".claude/skills/drive").is_symlink())
        self.assertFalse((self.home / ".claude/settings.json").exists(), "install.sh must never write a settings file")
        self.assertIn('"worktree":{"bgIsolation":"none"}', result.stdout)
        self.assertIn("--permission-mode auto", result.stdout)
        self.assertNotIn("CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0", result.stdout)
        self.assertNotIn("ANTHROPIC_DEFAULT_HAIKU_MODEL", result.stdout)

    def test_install_fails_when_the_plugin_stays_disabled(self):
        result = self.script("install.sh", status="✘ disabled")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("does not show drive@skills-dir as enabled", result.stderr)

    def test_apply_settings_is_refused_and_changes_nothing(self):
        result = self.script("install.sh", "--apply-settings")
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.home / ".claude/settings.json").exists())

    def test_uninstall_removes_the_link_without_disabling_by_name(self):
        self.assertEqual(self.script("install.sh").returncode, 0)
        result = self.script("uninstall.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.home / ".claude/skills/drive").exists())
        self.assertNotIn("plugin disable", self.calls())
        self.assertEqual(self.script("install.sh").returncode, 0)
        self.assertTrue((self.home / ".claude/skills/drive").is_symlink())
