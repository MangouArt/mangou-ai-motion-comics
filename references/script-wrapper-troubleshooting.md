# Script wrapper troubleshooting

Use this when `scripts/workflow/*.sh` or `scripts/asset/*.sh` fails differently from `python3 -m mangou_skill.cli ...`.

## Pitfall: wrapper changes cwd to skill root

Symptom:

```text
[mangou] Error: YAML not found: <skill-root>/storyboards/<file>.yaml
```

Cause: a wrapper script `cd`'d into the skill repository before invoking Python. Relative `--path storyboards/...` then resolves against the skill root instead of the project root.

Correct wrapper pattern:

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
export PYTHONPATH="$SKILL_ROOT${PYTHONPATH:+:$PYTHONPATH}"

python3 -m mangou_skill.cli storyboard generate "$@"
```

For asset wrappers, replace `storyboard generate` with `asset generate`; for resume/split wrappers, use the matching subcommand. The wrapper must:

- preserve the caller's cwd;
- inject `SKILL_ROOT` into `PYTHONPATH`;
- not require callers to export `PYTHONPATH`;
- not `cd` into the skill root.

## Verification recipe

From a real project root:

```bash
SKILL=/opt/data/skills/mangou-ai-motion-comics
PROJECT=/opt/data/workspace/projects/<project-id>
cd "$PROJECT"
set +e
out="$($SKILL/scripts/workflow/storyboard-generate.sh --path storyboards/__missing__.yaml --type image 2>&1)"
code=$?
set -e
printf 'exit=%s\n%s\n' "$code" "$out"
[[ "$code" -ne 0 ]]
[[ "$out" == *"$PROJECT/storyboards/__missing__.yaml"* ]]
[[ "$out" != *"$SKILL/storyboards/__missing__.yaml"* ]]
```

## Regression tests

Add or preserve tests like `tests_python/test_script_wrappers.py` that execute wrappers from a temporary project root and assert errors mention the project path, not the skill path.

Before committing:

```bash
python3 -m unittest tests_python.test_script_wrappers -v
python3 -m unittest discover -s tests_python -p 'test_*.py' -v
```
