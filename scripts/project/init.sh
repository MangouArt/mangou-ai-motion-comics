#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

cd "${SKILL_ROOT}"
exec python3 -m mangou_skill.cli project init "$@"
