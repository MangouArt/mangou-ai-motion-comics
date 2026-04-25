from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from mangou_skill.generate import run_aigc
from mangou_skill.yaml_utils import read_yaml_file, write_yaml_file


@unittest.skipUnless(os.environ.get("MANGOU_RUN_E2E") == "1", "Set MANGOU_RUN_E2E=1 to run provider-backed e2e tests.")
class ImageGenerationE2ETests(unittest.TestCase):
    def setUp(self) -> None:
        if not os.environ.get("BLTAI_API_KEY"):
            self.skipTest("BLTAI_API_KEY is required for image e2e.")

        self.original_cwd = Path.cwd()
        self.temp_root = Path(tempfile.mkdtemp(prefix="mangou-e2e-image-")).resolve()
        self.project_root = self.temp_root / "projects" / "e2e-image"
        (self.project_root / "storyboards").mkdir(parents=True)
        (self.project_root / "assets/images").mkdir(parents=True)
        (self.project_root / "project.json").write_text('{"id":"e2e-image"}\n', encoding="utf-8")
        os.chdir(self.temp_root)

    def tearDown(self) -> None:
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_bltai_image_generation_roundtrip(self) -> None:
        yaml_path = self.project_root / "storyboards" / "shot-e2e.yaml"
        write_yaml_file(
            yaml_path,
            {
                "meta": {"title": "e2e image generation"},
                "tasks": {
                    "image": {
                        "provider": "bltai",
                        "params": {
                            "model": "nano-banana",
                            "prompt": "sunlit meadow with a red bicycle, gentle clouds, clean illustration, bright daytime lighting",
                            "aspect_ratio": "16:9",
                        },
                    }
                },
            },
        )

        outputs = run_aigc(yaml_path, "image")

        self.assertTrue(outputs, "Expected at least one local materialized image output")
        output_path = self.project_root / outputs[0]
        self.assertTrue(output_path.exists(), f"Expected generated image file: {output_path}")
        self.assertGreater(output_path.stat().st_size, 0, "Generated image file should not be empty")

        updated = read_yaml_file(yaml_path)
        latest = updated["tasks"]["image"]["latest"]
        self.assertEqual(latest["status"], "completed")
        self.assertEqual(latest["backfill_status"], "completed")
        self.assertEqual(latest["output"], outputs[0])


if __name__ == "__main__":
    unittest.main()
