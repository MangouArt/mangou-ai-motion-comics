#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

required_paths=(
  "SKILL.md"
  "scripts/project/init.sh"
  "scripts/asset/generate.sh"
  "scripts/runtime/api-start.sh"
  "scripts/workflow/storyboard-generate.sh"
  "references/workspace-layout.md"
  "references/lark-cli-integration.md"
  "references/asset-generation.md"
  "workspace_template/config.json"
)

for rel in "${required_paths[@]}"; do
  if [[ ! -e "${SKILL_ROOT}/${rel}" ]]; then
    echo "[mangou-layout] missing: ${rel}" >&2
    exit 1
  fi
done

echo "[mangou-layout] skill-first layout looks healthy"
