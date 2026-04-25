from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from mangou_skill.runtime_api import (
    create_project_manager,
    get_project_id_from_api_path,
    get_project_ui_data,
    resolve_runtime_api_app_root,
    resolve_runtime_api_data_root,
)
from mangou_skill.yaml_utils import write_yaml_file


class RuntimeApiSupportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root = Path(tempfile.mkdtemp(prefix="mangou-server-test-")).resolve()
        self.addCleanup(lambda: shutil.rmtree(self.temp_root, ignore_errors=True))
        self.workspace_root = self.temp_root / "workspace"
        self.data_root = self.workspace_root / "projects"
        self.project_root = self.data_root / "demo-mirror"
        (self.project_root / "asset_defs").mkdir(parents=True, exist_ok=True)
        (self.project_root / "storyboards").mkdir(parents=True, exist_ok=True)
        (self.project_root / "tasks.jsonl").touch()
        (self.project_root / "project.json").write_text(
            json.dumps(
                {
                    "id": "demo-mirror",
                    "name": "Demo Mirror",
                    "createdAt": "2026-01-01T00:00:00.000Z",
                    "updatedAt": "2026-01-02T00:00:00.000Z",
                }
            ),
            encoding="utf-8",
        )

    def test_resolves_runtime_api_paths(self) -> None:
        workspace_root = self.temp_root / "custom-workspace"
        (workspace_root / "projects").mkdir(parents=True, exist_ok=True)

        self.assertEqual(resolve_runtime_api_app_root(), Path(__file__).resolve().parents[1])
        self.assertEqual(resolve_runtime_api_data_root(workspace_root), workspace_root / "projects")

    def test_projects_and_snapshots_share_same_custom_workspace_root(self) -> None:
        write_yaml_file(
            self.project_root / "asset_defs" / "duxiu.yaml",
            {
                "meta": {"id": "duxiu", "type": "character"},
                "content": {"name": "杜休", "description": "Miner"},
                "tasks": {"image": {"latest": {"status": "completed", "output": "assets/images/duxiu.png"}}},
            },
        )
        write_yaml_file(
            self.project_root / "storyboards" / "shot1.yaml",
            {
                "meta": {"id": "shot1"},
                "content": {"title": "Entry", "sequence": 1, "story": "进入矿区"},
                "tasks": {"image": {"latest": {"status": "completed", "output": "assets/images/shot1.png"}}},
                "refs": {"characters": ["duxiu"]},
            },
        )

        manager = create_project_manager(self.data_root)
        manager.init()
        projects = manager.list_projects()
        snapshot = get_project_ui_data(self.project_root, "demo-mirror")

        self.assertTrue(any(project["id"] == "demo-mirror" for project in projects))
        self.assertTrue(any(item["id"] == "shot1" and item["image_url"] == "assets/images/shot1.png" for item in snapshot["storyboards"]))
        self.assertTrue(any(item["id"] == "duxiu" and item["image_url"] == "assets/images/duxiu.png" for item in snapshot["assets"]))

    def test_accepts_flat_refs_arrays(self) -> None:
        write_yaml_file(
            self.project_root / "storyboards" / "shot2.yaml",
            {
                "meta": {"id": "shot2"},
                "content": {"title": "Flat Refs", "sequence": 2},
                "refs": ["duxiu"],
            },
        )
        snapshot = get_project_ui_data(self.project_root, "demo-mirror")
        self.assertTrue(any(item["id"] == "shot2" and item["asset_ids"] == ["duxiu"] for item in snapshot["storyboards"]))

    def test_fails_fast_when_asset_omits_meta_type(self) -> None:
        write_yaml_file(
            self.project_root / "asset_defs" / "broken.yaml",
            {"meta": {"id": "broken"}, "content": {"name": "Broken Asset"}},
        )
        with self.assertRaisesRegex(ValueError, "meta.type"):
            get_project_ui_data(self.project_root, "demo-mirror")

    def test_extracts_real_project_id_from_snapshot_path(self) -> None:
        self.assertEqual(get_project_id_from_api_path("/api/projects/demo-mirror/snapshot"), "demo-mirror")
        self.assertEqual(get_project_id_from_api_path("/api/projects/demo-mirror"), "demo-mirror")
