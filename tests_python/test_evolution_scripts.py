from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


class EvolutionScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skill_root = Path(__file__).resolve().parents[1]
        self.propose_script = self.skill_root / "scripts" / "evolution" / "propose-skill-change.sh"

    def test_propose_skill_change_uses_real_github_token_for_push(self) -> None:
        script = self.propose_script.read_text(encoding="utf-8")

        self.assertIn('x-access-token:', script)
        self.assertIn('"${GITHUB_TOKEN}"', script)
        self.assertIn('AUTHORIZATION: Basic ${git_push_auth}', script)
        self.assertNotIn('AUTHORIZATION: bearer ***', script)
        self.assertNotIn('AUTHORIZATION: Bearer ***', script)
        self.assertNotIn('AUTHORIZATION: Bearer ${GITHUB_TOKEN}', script)

    def test_propose_skill_change_disables_xtrace_around_authenticated_push(self) -> None:
        script = self.propose_script.read_text(encoding="utf-8")
        push_header_index = script.index('AUTHORIZATION: Basic ${git_push_auth}')
        before_push = script[:push_header_index]
        after_push = script[push_header_index:]

        self.assertIn('set +x', before_push)
        self.assertIn('push_was_traced', before_push)
        self.assertIn('set -x', after_push)

    def test_propose_skill_change_can_push_to_local_remote_before_pr_api(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mangou-evolution-test-") as tmp:
            tmp_path = Path(tmp)
            workdir = tmp_path / "workdir"
            remote = tmp_path / "remote.git"

            subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True, text=True)
            subprocess.run(
                ["git", "--git-dir", str(remote), "config", "receive.shallowUpdate", "true"],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(["git", "clone", str(self.skill_root), str(workdir)], check=True, capture_output=True, text=True)
            subprocess.run(["git", "checkout", "dev"], cwd=workdir, check=True, capture_output=True, text=True)
            (workdir / "references" / "evolution-test-marker.txt").write_text("local push simulation\n", encoding="utf-8")

            result = subprocess.run(
                [
                    str(self.propose_script),
                    "--workdir",
                    str(workdir),
                    "--branch",
                    "hermes/evolution-local-push-test",
                    "--title",
                    "test: local evolution push simulation",
                    "--summary",
                    "Validate local branch push before GitHub PR API.",
                    "--evidence",
                    "Unit test with a local bare remote.",
                ],
                env={
                    "PATH": "/usr/bin:/bin",
                    "GITHUB_TOKEN": "redacted-test-token",
                    "HERMES_EVOLUTION_REMOTE": f"file://{remote}",
                },
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("GitHub PR API failed", result.stderr)
            self.assertIn("Bad credentials", result.stderr)

            refs = subprocess.run(
                ["git", "--git-dir", str(remote), "show-ref", "refs/heads/hermes/evolution-local-push-test"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(refs.returncode, 0, result.stdout + result.stderr + refs.stderr)


if __name__ == "__main__":
    unittest.main()
