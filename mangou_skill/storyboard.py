from __future__ import annotations

import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .project import infer_project_root
from .tasks import append_task_event
from .yaml_utils import read_yaml_file, write_yaml_file


def _parse_grid(value: str) -> tuple[int, int]:
    raw_cols, raw_rows = str(value or "2x2").lower().split("x", 1)
    cols = int(raw_cols)
    rows = int(raw_rows)
    return cols, rows


def _get_image_dimensions(image_path: Path) -> tuple[int, int]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return (1024, 1024)

    proc = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=s=x:p=0",
            str(image_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = proc.stdout.strip()
    if proc.returncode != 0 or not stdout or "x" not in stdout:
        return (1024, 1024)
    width, height = stdout.split("x", 1)
    try:
        return (int(width), int(height))
    except ValueError:
        return (1024, 1024)


def _crop_image(input_path: Path, output_path: Path, x: int, y: int, w: int, h: int) -> None:
    ffmpeg = shutil.which("ffmpeg")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not ffmpeg:
        output_path.write_bytes(input_path.read_bytes())
        return
    subprocess.run(
        [
            ffmpeg,
            "-i",
            str(input_path),
            "-vf",
            f"crop={w}:{h}:{x}:{y}",
            "-y",
            str(output_path),
        ],
        capture_output=True,
        check=False,
    )


def run_split_grid(yaml_path: str | Path, project_root: str | Path | None = None) -> dict[str, list[str]]:
    absolute_yaml_path = Path(yaml_path).resolve()
    root = Path(project_root).resolve() if project_root else infer_project_root(absolute_yaml_path)
    rel_yaml_path = absolute_yaml_path.relative_to(root).as_posix()
    if not absolute_yaml_path.exists():
        raise FileNotFoundError(f"Parent YAML not found: {absolute_yaml_path}")

    doc = read_yaml_file(absolute_yaml_path)
    parent_id = str(doc.get("meta", {}).get("id") or absolute_yaml_path.stem)
    cols, rows = _parse_grid(str(doc.get("meta", {}).get("grid") or "2x2"))
    parent_image_rel = doc.get("tasks", {}).get("image", {}).get("latest", {}).get("output")
    if not parent_image_rel:
        raise ValueError(f"Parent YAML {rel_yaml_path} missing image output to split.")

    parent_image_path = root / str(parent_image_rel)
    width, height = _get_image_dimensions(parent_image_path)
    sub_width = width // cols
    sub_height = height // rows
    parent_base = Path(parent_image_rel).stem

    sub_images: list[str] = []
    for row in range(rows):
        for col in range(cols):
            index = row * cols + col + 1
            filename = f"{parent_base}-sub-{index:02d}.png"
            rel_path = Path("assets") / "images" / filename
            abs_path = root / rel_path
            _crop_image(parent_image_path, abs_path, col * sub_width, row * sub_height, sub_width, sub_height)
            sub_images.append(rel_path.as_posix())

    storyboards_dir = absolute_yaml_path.parent
    child_map: dict[int, Path] = {}
    for file_path in storyboards_dir.glob("*.yaml"):
        if file_path == absolute_yaml_path:
            continue
        try:
            child_doc = read_yaml_file(file_path)
        except Exception:
            continue
        if child_doc.get("meta", {}).get("parent") == parent_id:
            try:
                child_map[int(child_doc.get("meta", {}).get("grid_index"))] = file_path
            except Exception:
                continue

    for index, sub_path in enumerate(sub_images, start=1):
        child_abs_path = child_map.get(index) or (storyboards_dir / f"{parent_id}-sub-{index:02d}.yaml")
        if child_abs_path.exists():
            child_doc = read_yaml_file(child_abs_path) or {}
        else:
            child_doc = {
                "meta": {"id": child_abs_path.stem, "parent": parent_id, "grid_index": index},
                "content": {
                    "title": f"{doc.get('content', {}).get('title') or parent_id} (Part {index})",
                    "sequence": int(doc.get("content", {}).get("sequence") or 0) + index,
                },
                "tasks": {},
                "refs": {},
            }

        child_doc.setdefault("tasks", {})
        child_doc["tasks"].setdefault("image", {})
        child_doc["tasks"]["image"]["latest"] = {
            "status": "success",
            "output": sub_path,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        write_yaml_file(child_abs_path, child_doc)

        child_rel_path = child_abs_path.relative_to(root).as_posix()
        append_task_event(
            root,
            {
                "id": f"split-{parent_id}-{index}-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
                "type": "image",
                "status": "success",
                "provider": "grid-split",
                "input": {"parent": rel_yaml_path, "index": index},
                "target": child_rel_path,
                "ref": {"yamlPath": child_rel_path, "taskType": "image"},
                "output": sub_path,
            },
        )

    doc.setdefault("tasks", {})
    doc["tasks"].setdefault("split", {})
    doc["tasks"]["split"]["latest"] = {
        "status": "completed",
        "outputs": sub_images,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    write_yaml_file(absolute_yaml_path, doc)
    return {"outputs": sub_images}
