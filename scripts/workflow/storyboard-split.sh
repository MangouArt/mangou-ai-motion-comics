#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
export PYTHONPATH="$SKILL_ROOT${PYTHONPATH:+:$PYTHONPATH}"

python3 -m mangou_skill.cli storyboard split "$@"
