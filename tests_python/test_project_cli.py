from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from mangou_skill.cli import main
from mangou_skill.project import resolve_project_root


class MangouCliProjectInitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_cwd = Path.cwd()
        self.temp_root = Path(tempfile.mkdtemp(prefix="mangou-py-test-")).resolve()
        self.addCleanup(self._cleanup)

        os.environ.pop("MANGOU_HOME", None)
        os.environ.pop("MANGOU_WORKSPACE_ROOT", None)
        os.chdir(self.temp_root)

    def _cleanup(self) -> None:
        os.chdir(self.original_cwd)
        os.environ.pop("MANGOU_HOME", None)
        os.environ.pop("MANGOU_WORKSPACE_ROOT", None)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_project_init_creates_directory_structure(self) -> None:
        exit_code = main(["project", "init", "--name", "py-cli-project"])
        self.assertEqual(exit_code, 0)

        project_root = self.temp_root / "projects" / "py-cli-project"
        self.assertTrue(project_root.exists())
        self.assertTrue((project_root / "storyboards").exists())
        self.assertTrue((project_root / "asset_defs/chars").exists())
        self.assertTrue((project_root / "assets/images").exists())

        project_json = json.loads((project_root / "project.json").read_text(encoding="utf-8"))
        self.assertEqual(project_json["id"], "py-cli-project")

    def test_project_init_respects_mangou_workspace_root(self) -> None:
        env_projects_root = self.temp_root / "runtime-home" / "projects"
        os.environ["MANGOU_HOME"] = str(self.temp_root / "runtime-home")
        os.environ["MANGOU_WORKSPACE_ROOT"] = str(env_projects_root)

        exit_code = main(["project", "init", "--name", "env-py-project"])
        self.assertEqual(exit_code, 0)

        self.assertTrue((env_projects_root / "env-py-project").exists())
        self.assertFalse((self.temp_root / "projects" / "env-py-project").exists())

    def test_resolve_project_root_shares_env_aware_resolution(self) -> None:
        env_projects_root = self.temp_root / "shared-home" / "projects"
        os.environ["MANGOU_HOME"] = str(self.temp_root / "shared-home")
        os.environ["MANGOU_WORKSPACE_ROOT"] = str(env_projects_root)

        self.assertEqual(
            resolve_project_root("shared-env-project"),
            env_projects_root / "shared-env-project",
        )

    def test_runtime_paths_cli_uses_runtime_api_naming(self) -> None:
        workspace_root = self.temp_root / "workspace"
        (workspace_root / "projects").mkdir(parents=True)

        exit_code = main(["runtime", "paths", "--workspace", str(workspace_root)])

        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
