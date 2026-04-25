from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from .project import resolve_project_root
from .tasks import list_latest_tasks
from .yaml_utils import parse_yaml_quiet


DEFAULT_IMAGE_SEGMENT_DURATION_SECONDS = 4.0


def infer_project_id_from_cwd(cwd: Path | None = None) -> str | None:
    current = (cwd or Path.cwd()).resolve()
    parts = current.parts
    try:
        index = parts.index("projects")
    except ValueError:
        return None
    if index + 1 >= len(parts):
        return None
    return parts[index + 1]


def infer_project_root_from_cwd(cwd: Path | None = None) -> Path | None:
    project_id = infer_project_id_from_cwd(cwd)
    if not project_id:
        return None
    current = (cwd or Path.cwd()).resolve()
    parts = current.parts
    index = parts.index("projects")
    return Path(*parts[: index + 2])


def _extract_output_path(output: Any) -> str:
    if isinstance(output, str):
        candidate = output
    elif isinstance(output, dict):
        candidate = output.get("files", [""])[0] or output.get("urls", [""])[0] or output.get("output") or ""
    else:
        candidate = ""
    if not isinstance(candidate, str) or not candidate or candidate.startswith("http"):
        return ""
    return candidate


def _is_successful_status(status: str) -> bool:
    return status in {"success", "completed"}


def _parse_duration_seconds(value: Any) -> float:
    if isinstance(value, (int, float)) and value > 0:
        return float(value)
    if isinstance(value, str):
        raw = value.strip().lower().removesuffix("s").strip()
        try:
            parsed = float(raw)
            if parsed > 0:
                return parsed
        except ValueError:
            pass
    return DEFAULT_IMAGE_SEGMENT_DURATION_SECONDS


def _read_storyboard_doc(file_path: Path) -> dict[str, Any] | None:
    return parse_yaml_quiet(file_path.read_text(encoding="utf-8"))


def _find_latest_output(tasks: list[dict[str, Any]], yaml_path: str, task_type: str) -> str:
    for item in tasks:
        if item.get("ref", {}).get("yamlPath") == yaml_path and item.get("type") == task_type and _is_successful_status(str(item.get("status") or "")):
            return _extract_output_path(item.get("output"))
    return ""


def _create_image_segment(project_root: Path, output_dir: Path, image_path: str, duration_seconds: float, index: int) -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required for project stitch")
    segment_path = output_dir / f".stitch-segment-{index + 1:03d}.mp4"
    proc = subprocess.run(
        [
            ffmpeg,
            "-loop",
            "1",
            "-i",
            str((project_root / image_path).resolve()),
            "-t",
            str(duration_seconds),
            "-vf",
            "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-y",
            str(segment_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg image segment failed: {proc.stderr}")
    return segment_path


def _collect_storyboard_segments(project_root: Path, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    storyboards_dir = project_root / "storyboards"
    if not storyboards_dir.exists():
        raise FileNotFoundError("Failed to read storyboards directory: storyboards does not exist")

    docs_with_meta: list[tuple[Path, float]] = []
    for file_path in storyboards_dir.glob("*.yaml"):
        if not file_path.name.startswith("s") or "grid" in file_path.name or "test" in file_path.name:
            continue
        doc = _read_storyboard_doc(file_path) or {}
        sequence = doc.get("content", {}).get("sequence")
        docs_with_meta.append((file_path, float(sequence) if isinstance(sequence, (int, float)) else float("inf")))

    docs_with_meta.sort(key=lambda item: (item[1], item[0].name))

    segments: list[dict[str, Any]] = []
    for file_path, _ in docs_with_meta:
        yaml_path = f"storyboards/{file_path.name}"
        doc = _read_storyboard_doc(file_path) or {}
        video_path = _find_latest_output(tasks, yaml_path, "video")
        if video_path:
            segments.append({"mode": "video", "path": video_path, "yamlPath": yaml_path})
            continue

        image_path = _find_latest_output(tasks, yaml_path, "image") or _extract_output_path(doc.get("tasks", {}).get("image", {}).get("latest", {}).get("output"))
        if not image_path:
            continue
        segments.append(
            {
                "mode": "image",
                "path": image_path,
                "yamlPath": yaml_path,
                "durationSeconds": _parse_duration_seconds(doc.get("content", {}).get("duration")),
            }
        )
    return segments


def stitch_project(project_id: str, output_name: str = "output.mp4", cwd: Path | None = None) -> Path:
    project_root = resolve_project_root(project_id, cwd)
    return stitch(project_root, output_name=output_name)


def stitch(project_root: Path | str, output_name: str = "output.mp4") -> Path:
    root = Path(project_root).resolve()
    tasks = list_latest_tasks(root)
    segments = _collect_storyboard_segments(root, tasks)
    if not segments:
        raise RuntimeError("No completed video tasks found for the storyboards in this project.")

    output_dir = root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_name

    materialized_segments: list[Path] = []
    try:
        for index, segment in enumerate(segments):
            if segment["mode"] == "video":
                materialized_segments.append((root / segment["path"]).resolve())
            else:
                materialized_segments.append(
                    _create_image_segment(
                        root,
                        output_dir,
                        segment["path"],
                        float(segment["durationSeconds"]),
                        index,
                    )
                )

        list_path = output_dir / "concat_list.txt"
        list_path.write_text(
            "\n".join(f"file '{segment}'" for segment in materialized_segments),
            encoding="utf-8",
        )

        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("ffmpeg is required for project stitch")
        proc = subprocess.run(
            [
                ffmpeg,
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_path),
                "-c",
                "copy",
                "-y",
                str(output_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg concat failed: {proc.stderr}")
        return output_path
    finally:
        for segment_path in materialized_segments:
            if segment_path.name.startswith(".stitch-segment-"):
                segment_path.unlink(missing_ok=True)
        (output_dir / "concat_list.txt").unlink(missing_ok=True)
