from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from mangou_skill.generate import run_aigc
from mangou_skill.yaml_utils import read_yaml_file, write_yaml_file


@unittest.skipUnless(os.environ.get("MANGOU_RUN_E2E") == "1", "Set MANGOU_RUN_E2E=1 to run provider-backed e2e tests.")
class EvolinkGenerationE2ETests(unittest.TestCase):
    def setUp(self) -> None:
        if not os.environ.get("EVOLINK_API_KEY"):
            self.skipTest("EVOLINK_API_KEY is required for EvoLink e2e.")

        self.original_cwd = Path.cwd()
        self.temp_root = Path(tempfile.mkdtemp(prefix="mangou-e2e-evolink-")).resolve()
        self.project_root = self.temp_root / "projects" / "e2e-evolink"
        (self.project_root / "storyboards").mkdir(parents=True)
        (self.project_root / "assets/images").mkdir(parents=True)
        (self.project_root / "assets/videos").mkdir(parents=True)
        (self.project_root / "project.json").write_text('{"id":"e2e-evolink"}\n', encoding="utf-8")
        os.chdir(self.temp_root)

    def tearDown(self) -> None:
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_evolink_image_generation_roundtrip(self) -> None:
        yaml_path = self.project_root / "storyboards" / "shot-evolink-image.yaml"
        write_yaml_file(
            yaml_path,
            {
                "meta": {"title": "evolink image e2e"},
                "tasks": {
                    "image": {
                        "provider": "evolink",
                        "params": {
                            "model": "gemini-3.1-flash-image-preview",
                            "prompt": "quiet lakeside cabin at sunrise, soft mist, clean illustration, calm composition",
                            "size": "auto",
                            "quality": "0.5K",
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

    def test_evolink_video_generation_roundtrip_low_cost(self) -> None:
        yaml_path = self.project_root / "storyboards" / "shot-evolink-video.yaml"
        write_yaml_file(
            yaml_path,
            {
                "meta": {"title": "evolink video e2e"},
                "tasks": {
                    "video": {
                        "provider": "evolink",
                        "params": {
                            "model": "seedance-2.0-fast-text-to-video",
                            "prompt": "A paper windmill in a grassy field gently turning in a light breeze, simple daylight scene.",
                            "duration": 4,
                            "quality": "480p",
                            "aspect_ratio": "16:9",
                            "generate_audio": False,
                        },
                    }
                },
            },
        )

        outputs = run_aigc(yaml_path, "video")

        self.assertTrue(outputs, "Expected at least one local materialized video output")
        output_path = self.project_root / outputs[0]
        self.assertTrue(output_path.exists(), f"Expected generated video file: {output_path}")
        self.assertGreater(output_path.stat().st_size, 0, "Generated video file should not be empty")

        updated = read_yaml_file(yaml_path)
        latest = updated["tasks"]["video"]["latest"]
        self.assertEqual(latest["status"], "completed")
        self.assertEqual(latest["backfill_status"], "completed")
        self.assertEqual(latest["output"], outputs[0])


if __name__ == "__main__":
    unittest.main()
