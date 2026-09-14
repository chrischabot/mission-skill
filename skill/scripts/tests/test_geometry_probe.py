"""geometry-probe.js: one function expression that reports overflow, clipped text, overlap, and small targets."""
import glob
import html
import json
import os
import pwd
import re
import shutil
import subprocess

from helpers import SCRIPTS, DriveTestCase

PROBE = SCRIPTS / "geometry-probe.js"
FIXTURE = """<!doctype html>
<html><head><meta charset="utf-8"><style>
body { margin: 0; font: 16px sans-serif; }
#wide { width: 900px; height: 20px; background: #eee; }
#clip { width: 60px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
#a, #b { position: absolute; top: 100px; left: 10px; width: 80px; height: 40px; }
#b { left: 40px; }
#tiny { position: absolute; top: 200px; left: 10px; width: 12px; height: 12px; padding: 0; border: 0; }
#fine { position: absolute; top: 300px; left: 10px; width: 120px; height: 48px; }
#out { position: absolute; top: 400px; left: 0; }
</style></head><body>
<div id="wide">wide</div>
<div id="clip">This sentence is far too long for its box</div>
<button id="a">One</button><button id="b">Two</button>
<button id="tiny" aria-label="tiny"></button>
<button id="fine">Fine</button>
<pre id="out"></pre>
<script>var probe = /*PROBE*/; document.getElementById('out').textContent = JSON.stringify(probe({}));</script>
</body></html>
"""


def chrome_binary():
    """A headless browser: DRIVE_TEST_CHROME, Playwright's chrome-headless-shell, then an installed Chrome or Chromium.
    The fixtures point HOME at a scratch directory, so the real home comes from the password database."""
    home = pwd.getpwuid(os.getuid()).pw_dir
    shells = sorted(glob.glob(os.path.join(home, "Library/Caches/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell"))
                    + glob.glob(os.path.join(home, ".cache/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell")))
    for candidate in [os.environ.get("DRIVE_TEST_CHROME", "")] + shells[-1:] + [
            shutil.which("chromium") or "", shutil.which("google-chrome") or "",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]:
        if candidate and os.path.isfile(candidate):
            return candidate
    return None


class GeometryProbeTests(DriveTestCase):
    def test_the_probe_is_a_single_function_expression(self):
        text = PROBE.read_text()
        self.assertTrue(text.rstrip().endswith("})"), "no trailing semicolon, so it can be evaluated as an expression")
        if not shutil.which("node"):
            self.skipTest("node is not installed")
        script = ("const fs = require('fs'), vm = require('vm');"
                  "const f = vm.runInNewContext(fs.readFileSync(process.argv[1], 'utf8'));"
                  "process.stdout.write(typeof f)")
        result = subprocess.run(["node", "-e", script, str(PROBE)], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.stdout, "function", result.stderr)

    def test_the_probe_reports_each_defect_in_a_static_page_and_not_the_clean_button(self):
        chrome = chrome_binary()
        if not chrome:
            self.skipTest("no Chrome or Chromium binary to render the fixture")
        page = self.scratch / "fixture.html"
        page.write_text(FIXTURE.replace("/*PROBE*/", PROBE.read_text()), encoding="utf-8")
        profile = self.scratch / "chrome-profile"
        command = [chrome, "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--use-mock-keychain",
                   "--user-data-dir=" + str(profile), "--window-size=400,800", "--dump-dom", page.as_uri()]
        if not chrome.endswith("chrome-headless-shell"):
            command.insert(1, "--headless=new")
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        except subprocess.TimeoutExpired:
            self.skipTest("{} did not render the fixture within 60 seconds; set DRIVE_TEST_CHROME to a headless shell".format(chrome))
        match = re.search(r'<pre id="out">(.*?)</pre>', result.stdout, re.S)
        self.assertIsNotNone(match, result.stderr[-2000:])
        report = json.loads(html.unescape(match.group(1)))
        for check in ("h-overflow", "clipped-text", "overlap", "target-size"):
            self.assertGreaterEqual(report["counts"].get(check, 0), 1, "{} was not reported: {}".format(check, report["counts"]))
        flagged = {(f["check"], f["selector"]) for f in report["findings"]}
        self.assertIn(("clipped-text", "#clip"), flagged)
        self.assertIn(("target-size", "#tiny"), flagged)
        self.assertFalse(any(selector == "#fine" for _, selector in flagged), flagged)
