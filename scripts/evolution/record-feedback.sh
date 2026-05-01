#!/usr/bin/env bash
set -euo pipefail

title=""
source=""
summary=""
classification="general"
inbox="${HERMES_EVOLUTION_INBOX:-/opt/data/evolution/inbox.jsonl}"

usage() {
  cat <<'USAGE'
Usage:
  record-feedback.sh --title <title> --summary <summary> [options]

Options:
  --source <source>                 Source pointer, for example a Feishu message URL.
  --classification <classification> general|provider-fact|workflow|docs|runtime
  --inbox <path>                    JSONL inbox path. Defaults to $HERMES_EVOLUTION_INBOX or /opt/data/evolution/inbox.jsonl.
  -h, --help                        Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --title)
      title="${2:-}"
      shift 2
      ;;
    --source)
      source="${2:-}"
      shift 2
      ;;
    --summary)
      summary="${2:-}"
      shift 2
      ;;
    --classification)
      classification="${2:-}"
      shift 2
      ;;
    --inbox)
      inbox="${2:-}"
      shift 2
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

if [[ -z "${title}" || -z "${summary}" ]]; then
  echo "[mangou-evolution] --title and --summary are required" >&2
  usage >&2
  exit 2
fi

mkdir -p "$(dirname "${inbox}")"

python3 - "$inbox" "$title" "$source" "$summary" "$classification" <<'PY'
import json
import sys
from datetime import datetime, timezone

inbox, title, source, summary, classification = sys.argv[1:]
record = {
    "created_at": datetime.now(timezone.utc).isoformat(),
    "title": title,
    "source": source,
    "summary": summary,
    "classification": classification,
}

with open(inbox, "a", encoding="utf-8") as fh:
    fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
PY

echo "[mangou-evolution] recorded feedback: ${inbox}"
