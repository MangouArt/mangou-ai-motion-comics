from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mangou_skill.generate import resolve_media_params, run_aigc
from mangou_skill.yaml_utils import read_yaml_file, write_yaml_file


class GenerateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_cwd = Path.cwd()
        self.temp_root = Path(tempfile.mkdtemp(prefix="mangou-generate-test-")).resolve()
        self.project_root = self.temp_root / "projects" / "demo"
        (self.project_root / "storyboards").mkdir(parents=True)
        (self.project_root / "assets/images").mkdir(parents=True)
        (self.project_root / "assets/videos").mkdir(parents=True)
        (self.project_root / "project.json").write_text('{"id":"demo"}\n', encoding="utf-8")
        os.chdir(self.temp_root)
        self.addCleanup(self._cleanup)

    def _cleanup(self) -> None:
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_root, ignore_errors=True)
        os.environ.pop("BLTAI_API_KEY", None)

    def test_resolve_media_params_expands_local_image(self) -> None:
        image_path = self.project_root / "assets/images/ref.png"
        image_path.write_bytes(b"png")
        params = {"image": ["assets/images/ref.png"]}
        resolve_media_params(self.project_root, params)
        self.assertTrue(params["image"][0].startswith("data:image/png;base64,"))

    def test_run_aigc_updates_yaml_and_task_log(self) -> None:
        yaml_path = self.project_root / "storyboards" / "shot-001.yaml"
        write_yaml_file(
            yaml_path,
            {
                "tasks": {
                    "image": {
                        "provider": "bltai",
                        "params": {"prompt": "hero portrait", "model": "nano-banana"},
                    }
                }
            },
        )
        os.environ["BLTAI_API_KEY"] = "test-key"

        class FakeProvider:
            id = "bltai"
            env = {"apiKey": "BLTAI_API_KEY", "baseUrl": "BLTAI_BASE_URL", "defaultBaseUrl": "https://api.bltcy.ai"}
            scopes = {"image": "images", "video": "videos"}

            def build_payload(self, scope: str, params: dict[str, object]) -> dict[str, object]:
                self.last_payload = dict(params)
                return dict(params)

            def submit(self, **_: object) -> str:
                return "task-123"

            def poll(self, **_: object) -> dict[str, object]:
                return {"data": [{"url": "https://example.com/result.png"}]}

            def extract_outputs(self, scope: str, result: dict[str, object]) -> list[str]:
                return ["https://example.com/result.png"]

        with patch("mangou_skill.generate.get_provider", return_value=FakeProvider()):
            with patch("mangou_skill.generate.download_file", side_effect=lambda _u, p, **_k: Path(p).write_bytes(b"png")):
                outputs = run_aigc(yaml_path, "image")

        self.assertEqual(len(outputs), 1)
        self.assertTrue(outputs[0].startswith("assets/images/shot-001-task-123-0"))
        updated = read_yaml_file(yaml_path)
        latest = updated["tasks"]["image"]["latest"]
        self.assertEqual(latest["status"], "completed")
        self.assertEqual(latest["task_id"], "task-123")
        self.assertEqual(latest["output"], outputs[0])
        tasks_log = (self.project_root / "tasks.jsonl").read_text(encoding="utf-8")
        self.assertIn('"type": "image_generate"', tasks_log)


if __name__ == "__main__":
    unittest.main()
