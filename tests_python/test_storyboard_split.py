from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mangou_skill.storyboard import run_split_grid
from mangou_skill.tasks import list_latest_tasks
from mangou_skill.yaml_utils import read_yaml_file, write_yaml_file


class StoryboardSplitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project_root = Path(tempfile.mkdtemp(prefix="mangou-grid-")).resolve()
        self.addCleanup(lambda: shutil.rmtree(self.project_root, ignore_errors=True))
        (self.project_root / "storyboards").mkdir(parents=True, exist_ok=True)
        (self.project_root / "assets" / "images").mkdir(parents=True, exist_ok=True)
        (self.project_root / "project.json").write_text('{"id":"demo"}\n', encoding="utf-8")

    def test_prefers_explicit_grid_index_when_backfilling_children(self) -> None:
        parent_yaml_path = self.project_root / "storyboards" / "parent.yaml"
        child_a_path = self.project_root / "storyboards" / "child-a.yaml"
        child_b_path = self.project_root / "storyboards" / "child-b.yaml"
        (self.project_root / "assets" / "images" / "parent-grid.png").write_text("dummy image", encoding="utf-8")

        write_yaml_file(
            parent_yaml_path,
            {
                "meta": {"id": "master-shot", "version": "1.0", "grid": "2x2"},
                "tasks": {"image": {"latest": {"output": "assets/images/parent-grid.png"}}},
            },
        )
        write_yaml_file(
            child_a_path,
            {"meta": {"id": "child-a", "version": "1.0", "parent": "master-shot", "grid_index": 4}, "content": {"sequence": 1}},
        )
        write_yaml_file(
            child_b_path,
            {"meta": {"id": "child-b", "version": "1.0", "parent": "master-shot", "grid_index": 2}, "content": {"sequence": 2}},
        )

        with patch("mangou_skill.storyboard._get_image_dimensions", return_value=(1024, 1024)):
            with patch("mangou_skill.storyboard._crop_image", side_effect=lambda _i, o, *_: o.write_text("cropped", encoding="utf-8")):
                run_split_grid(parent_yaml_path, project_root=self.project_root)

        child_a = read_yaml_file(child_a_path)
        child_b = read_yaml_file(child_b_path)
        tasks = list_latest_tasks(self.project_root)

        self.assertEqual(child_a["tasks"]["image"]["latest"]["output"], "assets/images/parent-grid-sub-04.png")
        self.assertEqual(child_b["tasks"]["image"]["latest"]["output"], "assets/images/parent-grid-sub-02.png")
        self.assertTrue(any(task.get("ref", {}).get("yamlPath") == "storyboards/child-a.yaml" for task in tasks))

    def test_uses_only_meta_grid_and_ignores_prompt_hints(self) -> None:
        parent_yaml_path = self.project_root / "storyboards" / "prompt-parent.yaml"
        (self.project_root / "assets" / "images" / "prompt-grid.png").write_text("dummy image", encoding="utf-8")
        write_yaml_file(
            parent_yaml_path,
            {
                "meta": {"id": "prompt-parent", "version": "1.0"},
                "tasks": {
                    "image": {
                        "params": {"prompt": "Please render this as a 3x3 storyboard grid"},
                        "latest": {"output": "assets/images/prompt-grid.png"},
                    }
                },
            },
        )

        with patch("mangou_skill.storyboard._get_image_dimensions", return_value=(1024, 1024)):
            with patch("mangou_skill.storyboard._crop_image", side_effect=lambda _i, o, *_: o.write_text("cropped", encoding="utf-8")):
                result = run_split_grid(parent_yaml_path, project_root=self.project_root)

        self.assertEqual(
            result["outputs"],
            [
                "assets/images/prompt-grid-sub-01.png",
                "assets/images/prompt-grid-sub-02.png",
                "assets/images/prompt-grid-sub-03.png",
                "assets/images/prompt-grid-sub-04.png",
            ],
        )
