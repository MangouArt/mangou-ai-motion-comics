from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


class ScriptWrapperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skill_root = Path(__file__).resolve().parents[1]

    def test_storyboard_generate_wrapper_preserves_project_cwd(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mangou-wrapper-test-") as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            (project / "project.json").write_text('{"id":"project"}\n', encoding="utf-8")
            script = self.skill_root / "scripts" / "workflow" / "storyboard-generate.sh"

            result = subprocess.run(
                [str(script), "--path", "storyboards/missing.yaml", "--type", "image"],
                cwd=project,
                text=True,
                capture_output=True,
                check=False,
            )

            output = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(str(project / "storyboards" / "missing.yaml"), output)
            self.assertNotIn(str(self.skill_root / "storyboards" / "missing.yaml"), output)

    def test_asset_generate_wrapper_preserves_project_cwd(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mangou-wrapper-test-") as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            (project / "project.json").write_text('{"id":"project"}\n', encoding="utf-8")
            script = self.skill_root / "scripts" / "asset" / "generate.sh"

            result = subprocess.run(
                [str(script), "--path", "asset_defs/missing.yaml"],
                cwd=project,
                text=True,
                capture_output=True,
                check=False,
            )

            output = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(str(project / "asset_defs" / "missing.yaml"), output)
            self.assertNotIn(str(self.skill_root / "asset_defs" / "missing.yaml"), output)


if __name__ == "__main__":
    unittest.main()
