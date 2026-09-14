#!/usr/bin/env bash
# probe-signals.sh — deterministic repository probe for mission classification (no model, no network).
# Writes JSON with markers that imply shapes and traits (see references/shapes-and-scope.md §2).
# Misses mean "unknown", never "absent".
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: probe-signals.sh [--repo PATH] [--out FILE]

Scans a repository (default: current directory) for classification signals and writes JSON
(default: <repo>/.mission/tmp/signals.json, or stdout with --out -).

Signals: source file counts by extension, manifests, platform markers (iOS, Android, web),
deploy/IaC config, test harness markers, CI files, migration dirs, AI SDK imports, auth and
payment SDK hits, git history depth. Heuristic only: treat misses as "unknown".
EOF
}

REPO="."
OUT=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo) REPO="${2:?--repo needs a path}"; shift 2 ;;
    --out) OUT="${2:?--out needs a file or -}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [ ! -d "${REPO}" ]; then
  echo "repo not found: ${REPO}" >&2
  exit 2
fi
REPO="$(cd "${REPO}" && pwd)"
if [ -z "${OUT}" ]; then
  mkdir -p "${REPO}/.mission/tmp"
  OUT="${REPO}/.mission/tmp/signals.json"
fi

command -v python3 >/dev/null 2>&1 || { echo "python3 is required" >&2; exit 2; }

python3 - "${REPO}" "${OUT}" <<'PY'
import json, os, re, subprocess, sys
from collections import Counter

repo, out = sys.argv[1], sys.argv[2]
SKIP_DIRS = {".git", "node_modules", "dist", "build", ".build", "target", ".wrangler", ".next", "vendor",
             "Pods", "DerivedData", ".venv", "venv", "__pycache__", ".mission", ".claude", "coverage"}
SOURCE_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".rs", ".go", ".swift", ".kt", ".kts", ".java",
              ".rb", ".php", ".cs", ".vue", ".svelte", ".sql", ".m", ".mm", ".c", ".cc", ".cpp", ".h"}
MAX_SCAN_BYTES = 200_000

ext_counts = Counter()
files = []
for root, dirs, names in os.walk(repo):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.endswith(".xcassets")]
    for n in names:
        p = os.path.join(root, n)
        rel = os.path.relpath(p, repo)
        files.append(rel)
        ext = os.path.splitext(n)[1].lower()
        if ext in SOURCE_EXT:
            ext_counts[ext] += 1

def exists_any(patterns):
    hits = []
    for rel in files:
        for pat in patterns:
            if re.search(pat, rel):
                hits.append(rel)
                break
        if len(hits) >= 5:
            break
    return hits

def grep_sources(patterns, exts=None, limit=5):
    rx = re.compile("|".join(patterns))
    hits = []
    for rel in files:
        ext = os.path.splitext(rel)[1].lower()
        if exts is not None and ext not in exts:
            continue
        if ext not in SOURCE_EXT and exts is None:
            continue
        path = os.path.join(repo, rel)
        try:
            if os.path.getsize(path) > MAX_SCAN_BYTES:
                continue
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                for i, line in enumerate(fh, 1):
                    if rx.search(line):
                        hits.append(f"{rel}:{i}")
                        break
        except OSError:
            continue
        if len(hits) >= limit:
            break
    return hits

markers = {
    "manifests": exists_any([r"(^|/)package\.json$", r"(^|/)Cargo\.toml$", r"(^|/)pyproject\.toml$",
                             r"(^|/)requirements\.txt$", r"(^|/)go\.mod$", r"(^|/)Package\.swift$",
                             r"(^|/)Gemfile$", r"(^|/)pom\.xml$", r"(^|/)build\.gradle(\.kts)?$"]),
    "ios": exists_any([r"\.xcodeproj/", r"\.xcworkspace/", r"(^|/)Package\.swift$", r"(^|/)Info\.plist$"]),
    "android": exists_any([r"(^|/)AndroidManifest\.xml$", r"(^|/)build\.gradle(\.kts)?$"]),
    "web_frontend": exists_any([r"\.(tsx|jsx|vue|svelte)$", r"(^|/)index\.html$", r"(^|/)(astro|next|vite|nuxt|svelte)\.config\."]),
    "deploy_config": exists_any([r"(^|/)wrangler\.(toml|jsonc?)$", r"(^|/)Dockerfile$", r"(^|/)vercel\.json$",
                                 r"(^|/)netlify\.toml$", r"(^|/)fly\.toml$", r"\.tf$", r"(^|/)serverless\.ya?ml$",
                                 r"(^|/)app\.yaml$", r"(^|/)k8s/", r"(^|/)helm/"]),
    "ci": exists_any([r"^\.github/workflows/", r"^\.gitlab-ci\.yml$", r"^\.circleci/", r"(^|/)Jenkinsfile$"]),
    "tests": exists_any([r"(^|/)(tests?|__tests__|spec|e2e|UITests|Tests)/", r"\.(test|spec)\.[jt]sx?$",
                         r"_test\.(go|py)$", r"(^|/)test_[^/]+\.py$", r"(^|/)(vitest|jest|playwright)\.config\."]),
    "database_migrations": exists_any([r"(^|/)migrations?/", r"(^|/)schema\.prisma$", r"(^|/)drizzle\.config\.",
                                       r"\.sql$"]),
    "docs_site": exists_any([r"(^|/)docs/", r"(^|/)mkdocs\.ya?ml$", r"(^|/)docusaurus\.config\.", r"(^|/)(content|posts|blog)/"]),
}
android_gradle = []
for rel in markers["android"]:
    if rel.endswith((".gradle", ".gradle.kts")):
        try:
            with open(os.path.join(repo, rel), encoding="utf-8", errors="ignore") as fh:
                if "com.android.application" in fh.read():
                    android_gradle.append(rel)
        except OSError:
            pass
    else:
        android_gradle.append(rel)
markers["android"] = android_gradle

greps = {
    "ai_sdk": grep_sources([r"@anthropic-ai/sdk", r"\banthropic\b", r"\bopenai\b", r"@ai-sdk/", r"env\.AI\b", r"workers-ai"]),
    "auth": grep_sources([r"jsonwebtoken", r"\bjose\b", r"passport", r"next-auth", r"better-auth", r"lucia", r"\bJWT\b",
                          r"Set-Cookie", r"AuthenticationServices", r"ASAuthorization", r"oauth"]),
    "payments": grep_sources([r"\bstripe\b", r"RevenueCat", r"StoreKit", r"paddle", r"braintree", r"adyen"]),
    "pii_fields": grep_sources([r"\bemail\b", r"phone_?number", r"date_?of_?birth", r"\baddress\b", r"upload", r"avatar", r"photo"]),
    "concurrency": grep_sources([r"DurableObject", r"\bMutex\b", r"\bsemaphore\b", r"advisory_lock", r"\bqueue\b", r"tokio::spawn",
                                 r"DispatchQueue", r"\bactor\b"]),
}

def git(*args):
    try:
        return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return ""

commit_count = git("rev-list", "--count", "HEAD")
source_files = sum(ext_counts.values())
signals = {
    "repo": repo,
    "source_files": source_files,
    "source_files_by_ext": dict(ext_counts.most_common()),
    "git_commits": int(commit_count) if commit_count.isdigit() else None,
    "markers": markers,
    "grep_hits": greps,
    "implied": {
        "near_empty_repo": source_files < 20 and not markers["deploy_config"],
        "existing_codebase": source_files >= 20,
        "has_ios": bool(markers["ios"]) and any(r.endswith((".xcodeproj", "Package.swift")) or ".xcodeproj/" in r for r in markers["ios"]),
        "has_android": bool(markers["android"]),
        "has_web_frontend": bool(markers["web_frontend"]),
        "deploy_to_production": "unknown" if markers["deploy_config"] else "unknown-no-config",
        "has_database": bool(markers["database_migrations"]),
        "no_test_harness": not markers["tests"],
        "has_ai_llm_features": bool(greps["ai_sdk"]),
        "touches_auth": bool(greps["auth"]),
        "touches_payments": bool(greps["payments"]),
        "touches_pii": "probe" if greps["pii_fields"] else "unknown",
        "infra_or_ci_present": bool(markers["ci"] or markers["deploy_config"]),
    },
    "note": "Heuristic markers. Absence of a marker means unknown, not absent. Confirm present traits with file:line evidence.",
}
data = json.dumps(signals, indent=2)
if out == "-":
    print(data)
else:
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(data + "\n")
    print(f"wrote {out}")
PY
