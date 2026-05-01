#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

repo="${HERMES_EVOLUTION_REPO:-MangouArt/mangou-ai-motion-comics}"
base_branch="${HERMES_EVOLUTION_BASE_BRANCH:-dev}"
workdir="${HERMES_EVOLUTION_WORKDIR:-${SKILL_ROOT}}"
remote_url="${HERMES_EVOLUTION_REMOTE:-https://github.com/${repo}.git}"
branch=""
title=""
summary=""
evidence=""
validate=0
dry_run=0

usage() {
  cat <<'USAGE'
Usage:
  propose-skill-change.sh --title <title> --summary <summary> --evidence <evidence> [options]

Options:
  --repo <owner/name>          GitHub repository. Defaults to $HERMES_EVOLUTION_REPO or MangouArt/mangou-ai-motion-comics.
  --base <branch>             PR base branch. Defaults to $HERMES_EVOLUTION_BASE_BRANCH or dev.
  --workdir <path>            Product repo checkout. Defaults to current skill root.
  --branch <name>             Branch name. Defaults to hermes/evolution-<timestamp>.
  --validate                  Run layout check and Python unittest before committing.
  --dry-run                   Validate and print the PR body without commit/push/API calls.
  -h, --help                  Show this help.

Required environment for non-dry-run:
  GITHUB_TOKEN                Token with permission to push branches and create PRs on the target repo.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo="${2:-}"
      remote_url="https://github.com/${repo}.git"
      shift 2
      ;;
    --base)
      base_branch="${2:-}"
      shift 2
      ;;
    --workdir)
      workdir="${2:-}"
      shift 2
      ;;
    --branch)
      branch="${2:-}"
      shift 2
      ;;
    --title)
      title="${2:-}"
      shift 2
      ;;
    --summary)
      summary="${2:-}"
      shift 2
      ;;
    --evidence)
      evidence="${2:-}"
      shift 2
      ;;
    --validate)
      validate=1
      shift
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[mangou-evolution] unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "${title}" || -z "${summary}" || -z "${evidence}" ]]; then
  echo "[mangou-evolution] --title, --summary, and --evidence are required" >&2
  usage >&2
  exit 2
fi

cd "${workdir}"

if [[ ! -f "SKILL.md" || ! -d "references" || ! -d "scripts" ]]; then
  echo "[mangou-evolution] workdir is not a mangou-ai-motion-comics skill root: ${workdir}" >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "[mangou-evolution] workdir is not a git checkout: ${workdir}" >&2
  exit 1
fi

if [[ "${validate}" -eq 1 ]]; then
  ./scripts/doctor/check-layout.sh
  python3 -m unittest discover -s tests_python -p 'test_*.py' -v
fi

if [[ -z "$(git status --porcelain)" ]]; then
  echo "[mangou-evolution] no local changes to propose" >&2
  exit 1
fi

changed_files="$(git status --short)"
validation_text="Not run"
if [[ "${validate}" -eq 1 ]]; then
  validation_text="./scripts/doctor/check-layout.sh
python3 -m unittest discover -s tests_python -p 'test_*.py' -v"
fi

body_file="$(mktemp)"
cat >"${body_file}" <<EOF
## Summary

${summary}

## Evidence

${evidence}

## Boundary check

- This proposal should only include general workflow, docs, template, provider fact, CLI, or runtime changes.
- It must not include user secrets, private chat transcripts, single-project preferences, or project-local assets.

## Changed files

\`\`\`text
${changed_files}
\`\`\`

## Validation

\`\`\`text
${validation_text}
\`\`\`
EOF

if [[ "${dry_run}" -eq 1 ]]; then
  echo "[mangou-evolution] dry run PR body:"
  cat "${body_file}"
  rm -f "${body_file}"
  exit 0
fi

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "[mangou-evolution] GITHUB_TOKEN is required for push and PR creation" >&2
  rm -f "${body_file}"
  exit 2
fi

if [[ -z "${branch}" ]]; then
  branch="hermes/evolution-$(date -u +%Y%m%d%H%M%S)"
fi

current_branch="$(git branch --show-current || true)"
if [[ -z "${current_branch}" ]]; then
  echo "[mangou-evolution] detached HEAD is not supported" >&2
  rm -f "${body_file}"
  exit 1
fi

git switch -c "${branch}"
git add SKILL.md COMMANDS.md INSTALL.md README.md references scripts assets workspace_template mangou_skill tests_python 2>/dev/null || true

if git diff --cached --quiet; then
  echo "[mangou-evolution] no allowed files were staged" >&2
  git switch "${current_branch}"
  rm -f "${body_file}"
  exit 1
fi

git -c user.name="${HERMES_GIT_AUTHOR_NAME:-Hermes Evolution}" \
  -c user.email="${HERMES_GIT_AUTHOR_EMAIL:-hermes-evolution@users.noreply.github.com}" \
  commit -m "${title}"

git -c "http.https://github.com/.extraheader=AUTHORIZATION: bearer ${GITHUB_TOKEN}" \
  push "${remote_url}" "HEAD:refs/heads/${branch}"

api_response="$(mktemp)"
if ! python3 - "$repo" "$base_branch" "$branch" "$title" "$body_file" "$GITHUB_TOKEN" >"${api_response}" <<'PY'
import json
import sys
import urllib.error
import urllib.request

repo, base, head, title, body_path, token = sys.argv[1:]
payload = json.dumps({
    "title": title,
    "head": head,
    "base": base,
    "body": open(body_path, encoding="utf-8").read(),
    "maintainer_can_modify": True,
}).encode("utf-8")

request = urllib.request.Request(
    f"https://api.github.com/repos/{repo}/pulls",
    data=payload,
    headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "mangou-hermes-evolution",
        "X-GitHub-Api-Version": "2022-11-28",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(request, timeout=30) as response:
        sys.stdout.write(response.read().decode("utf-8"))
        sys.exit(0)
except urllib.error.HTTPError as exc:
    sys.stdout.write(exc.read().decode("utf-8"))
    sys.exit(exc.code)
PY
then
  echo "[mangou-evolution] GitHub PR API failed" >&2
  cat "${api_response}" >&2
  rm -f "${body_file}" "${api_response}"
  exit 1
fi

python3 - "${api_response}" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
print(f"[mangou-evolution] opened PR: {data.get('html_url')}")
PY

rm -f "${body_file}" "${api_response}"
