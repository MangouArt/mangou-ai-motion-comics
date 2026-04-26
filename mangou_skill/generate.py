from __future__ import annotations

import base64
import json
import mimetypes
import os
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .http_utils import download_file
from .project import infer_project_root
from .providers import get_provider, resolve_provider_env
from .tasks import append_task_event
from .yaml_utils import read_yaml_file, write_yaml_file


MIME_BY_EXTENSION = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "gif": "image/gif",
    "mp4": "video/mp4",
    "mov": "video/quicktime",
    "webm": "video/webm",
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "m4a": "audio/mp4",
    "aac": "audio/aac",
    "ogg": "audio/ogg",
}


def load_dotenv(cwd: Path | None = None) -> None:
    base = (cwd or Path.cwd()).resolve()
    for filename in (".env.local", ".env"):
        env_path = base / filename
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            trimmed = line.strip()
            if not trimmed or trimmed.startswith("#") or "=" not in trimmed:
                continue
            key, value = trimmed.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            if key and key not in os.environ:
                os.environ[key] = value


@dataclass(frozen=True)
class GenerationSummary:
    ok: bool
    project_root: str
    storyboard: str
    type: str
    provider: str
    model: str | None
    task_id: str
    local_outputs: list[str]
    remote_outputs: list[str]
    outputs: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "project_root": self.project_root,
            "storyboard": self.storyboard,
            "type": self.type,
            "provider": self.provider,
            "model": self.model,
            "task_id": self.task_id,
            "local_outputs": self.local_outputs,
            "remote_outputs": self.remote_outputs,
            "outputs": self.outputs,
        }


@dataclass(frozen=True)
class GenerationContext:
    yaml_path: Path
    project_root: Path
    rel_yaml_path: str
    task_config: dict[str, Any]
    provider_id: str
    provider: Any
    api_key: str
    base_url: str
    scope: str
    model: str | None


def run_aigc(yaml_path: str | Path, task_type: str) -> list[str]:
    return run_aigc_summary(yaml_path, task_type).local_outputs


def run_aigc_summary(yaml_path: str | Path, task_type: str) -> GenerationSummary:
    context = prepare_generation_context(yaml_path, task_type)
    params = deepcopy(context.task_config.get("params") or {})
    resolve_media_params(context.project_root, params)

    payload = context.provider.build_payload(context.scope, params)
    print(f"[mangou] Submitting {task_type} task via {context.provider_id}...")
    submit_result = context.provider.submit(base_url=context.base_url, api_key=context.api_key, scope=context.scope, payload=payload)
    task_id = submit_result if isinstance(submit_result, str) else "unknown"

    update_yaml(
        context.yaml_path,
        {
            f"tasks.{task_type}.latest": {
                "status": "running",
                "remote_status": "running",
                "backfill_status": "pending",
                "task_id": task_id,
                "updated_at": iso_now(),
            }
        },
    )

    print(f"[mangou] Task {task_id} is running. Polling for results...")
    try:
        return poll_and_materialize(context, task_type, task_id, submit_result)
    except KeyboardInterrupt:
        mark_generation_interrupted(context, task_type, task_id)
        print_resume_hint(context.rel_yaml_path, task_type, task_id)
        raise


def resume_aigc(yaml_path: str | Path, task_type: str, task_id: str | None = None) -> GenerationSummary:
    context = prepare_generation_context(yaml_path, task_type)
    latest = context.task_config.get("latest") if isinstance(context.task_config.get("latest"), dict) else {}
    resolved_task_id = str(task_id or latest.get("task_id") or "").strip()
    if not resolved_task_id:
        raise RuntimeError(f"No resumable task_id found for {task_type} task in {context.rel_yaml_path}")
    print(f"[mangou] Resuming {task_type} task {resolved_task_id} via {context.provider_id}...")
    return poll_and_materialize(context, task_type, resolved_task_id, resolved_task_id)


def prepare_generation_context(yaml_path: str | Path, task_type: str) -> GenerationContext:
    if task_type not in {"image", "video"}:
        raise ValueError(f"Unsupported task type: {task_type}")

    load_dotenv()
    absolute_yaml_path = Path(yaml_path).resolve()
    if not absolute_yaml_path.exists():
        raise FileNotFoundError(f"YAML not found: {absolute_yaml_path}")

    project_root = infer_project_root(absolute_yaml_path)
    rel_yaml_path = absolute_yaml_path.relative_to(project_root).as_posix()
    doc = read_yaml_file(absolute_yaml_path)
    task_config = ((doc or {}).get("tasks") or {}).get(task_type)
    if not isinstance(task_config, dict):
        raise RuntimeError(f"No {task_type} task defined in {rel_yaml_path}")

    provider_id = str(task_config.get("provider", "")).strip()
    if not provider_id:
        raise RuntimeError(f"Provider not specified for {task_type} task in {rel_yaml_path}")

    provider = get_provider(provider_id)
    api_key, base_url = resolve_provider_env(provider, os.environ)
    if not api_key:
        raise RuntimeError(f"API Key missing for provider: {provider_id}. Check your .env file.")

    params = task_config.get("params") or {}
    model = str(params.get("model")).strip() if isinstance(params, dict) and params.get("model") else None

    scope = provider.scopes.get(task_type) or ("images" if task_type == "image" else "videos")
    return GenerationContext(
        yaml_path=absolute_yaml_path,
        project_root=project_root,
        rel_yaml_path=rel_yaml_path,
        task_config=task_config,
        provider_id=provider_id,
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        scope=scope,
        model=model,
    )


def poll_and_materialize(context: GenerationContext, task_type: str, task_id: str, provider_task_id: Any) -> GenerationSummary:
    result = context.provider.poll(base_url=context.base_url, api_key=context.api_key, scope=context.scope, task_id=provider_task_id)
    outputs = context.provider.extract_outputs(context.scope, result)
    update_yaml(
        context.yaml_path,
        {
            f"tasks.{task_type}.latest": {
                "status": "running",
                "remote_status": "completed",
                "backfill_status": "pending",
                "remote_outputs": outputs,
                "task_id": task_id,
                "updated_at": iso_now(),
            }
        },
    )
    append_task_event(
        context.project_root,
        {
            "id": task_id,
            "type": f"{task_type}_generate",
            "status": "completed",
            "provider": context.provider_id,
            "target": context.rel_yaml_path,
            "output": outputs,
            "event": "remote_completed",
        },
    )

    try:
        local_outputs = materialize_outputs(context.project_root, context.rel_yaml_path, task_type, task_id, outputs)
        assert_outputs_exist(context.project_root, context.rel_yaml_path, local_outputs)
    except Exception as exc:
        update_yaml(
            context.yaml_path,
            {
                f"tasks.{task_type}.latest": {
                    "status": "running",
                    "remote_status": "completed",
                    "backfill_status": "failed",
                    "remote_outputs": outputs,
                    "task_id": task_id,
                    "error": str(exc),
                    "updated_at": iso_now(),
                }
            },
        )
        append_task_event(
            context.project_root,
            {
                "id": f"{task_id}:materialize",
                "type": f"{task_type}_materialize",
                "status": "failed",
                "provider": context.provider_id,
                "target": context.rel_yaml_path,
                "output": outputs,
                "error": str(exc),
                "event": "backfill_failed",
            },
        )
        raise

    primary_output = local_outputs[0] if local_outputs else ""
    update_yaml(
        context.yaml_path,
        {
            f"tasks.{task_type}.latest": {
                "status": "completed",
                "remote_status": "completed",
                "backfill_status": "completed",
                "remote_outputs": outputs,
                "outputs": local_outputs,
                "output": primary_output,
                "task_id": task_id,
                "updated_at": iso_now(),
            }
        },
    )
    append_task_event(
        context.project_root,
        {
            "id": task_id,
            "type": f"{task_type}_generate",
            "status": "success",
            "provider": context.provider_id,
            "target": context.rel_yaml_path,
            "output": primary_output,
        },
    )
    print(f"[mangou] Successfully generated {task_type}: {primary_output}")
    return GenerationSummary(
        ok=True,
        project_root=str(context.project_root),
        storyboard=context.rel_yaml_path,
        type=task_type,
        provider=context.provider_id,
        model=context.model,
        task_id=task_id,
        local_outputs=local_outputs,
        remote_outputs=outputs,
        outputs=describe_outputs(context.project_root, local_outputs),
    )


def mark_generation_interrupted(context: GenerationContext, task_type: str, task_id: str) -> None:
    update_yaml(
        context.yaml_path,
        {
            f"tasks.{task_type}.latest": {
                "status": "interrupted",
                "remote_status": "running",
                "backfill_status": "pending",
                "task_id": task_id,
                "updated_at": iso_now(),
            }
        },
    )
    append_task_event(
        context.project_root,
        {
            "id": task_id,
            "type": f"{task_type}_generate",
            "status": "interrupted",
            "provider": context.provider_id,
            "target": context.rel_yaml_path,
            "event": "interrupted",
        },
    )


def print_resume_hint(rel_yaml_path: str, task_type: str, task_id: str) -> None:
    print(
        "\n[mangou] Generation interrupted, but the remote task may still be running.\n"
        "[mangou] Resume with:\n"
        f"  mangou storyboard resume --path {rel_yaml_path} --type {task_type}\n"
        f"[mangou] Task id: {task_id}",
        flush=True,
    )


def print_json_summary(summary: GenerationSummary) -> None:
    print(json.dumps(summary.to_dict(), ensure_ascii=False))


def resolve_media_params(project_root: Path, params: dict[str, Any]) -> None:
    for key in ("images", "image", "image_urls"):
        if key in params and isinstance(params[key], list):
            params[key] = [resolve_image_input(project_root, item) for item in params[key]]

    if "image_url" in params:
        params["image_url"] = resolve_image_input(project_root, params["image_url"])

    for key in ("video_urls", "audio_urls"):
        if key in params and isinstance(params[key], list):
            params[key] = [resolve_binary_input(project_root, item) for item in params[key]]

    if isinstance(params.get("content"), list):
        params["content"] = [resolve_content_item(project_root, item) for item in params["content"]]


def resolve_image_input(project_root: Path, input_value: Any) -> Any:
    if not isinstance(input_value, str):
        return input_value
    if input_value.endswith(".yaml"):
        return resolve_asset_image(project_root, input_value) or input_value
    candidate = (project_root / input_value).resolve()
    if input_value.startswith("http") or input_value.startswith("data:") or not candidate.exists():
        return input_value
    return encode_local_binary(candidate, fallback_type="image")


def resolve_binary_input(project_root: Path, input_value: Any) -> Any:
    if not isinstance(input_value, str):
        return input_value
    if input_value.startswith("http") or input_value.startswith("data:"):
        return input_value
    candidate = (project_root / input_value).resolve()
    if not candidate.exists():
        return input_value
    return encode_local_binary(candidate)


def resolve_content_item(project_root: Path, item: Any) -> Any:
    if not isinstance(item, dict):
        return item
    next_item = deepcopy(item)
    if next_item.get("type") == "image_url" and isinstance(next_item.get("image_url"), dict) and "url" in next_item["image_url"]:
        next_item["image_url"]["url"] = resolve_image_input(project_root, next_item["image_url"]["url"])
    if next_item.get("type") == "video_url" and isinstance(next_item.get("video_url"), dict) and "url" in next_item["video_url"]:
        next_item["video_url"]["url"] = resolve_binary_input(project_root, next_item["video_url"]["url"])
    if next_item.get("type") == "audio_url" and isinstance(next_item.get("audio_url"), dict) and "url" in next_item["audio_url"]:
        next_item["audio_url"]["url"] = resolve_binary_input(project_root, next_item["audio_url"]["url"])
    return next_item


def resolve_asset_image(project_root: Path, yaml_rel_path: str) -> str | None:
    yaml_path = (project_root / yaml_rel_path).resolve()
    if not yaml_path.exists():
        return None
    doc = read_yaml_file(yaml_path)
    latest = ((doc or {}).get("tasks") or {}).get("image", {}).get("latest", {})
    output = latest.get("output")
    return output if isinstance(output, str) and output else None


def encode_local_binary(path: Path, fallback_type: str | None = None) -> str:
    data = path.read_bytes()
    ext = path.suffix.lower().lstrip(".")
    mime = MIME_BY_EXTENSION.get(ext)
    if not mime:
        guessed, _ = mimetypes.guess_type(path.name)
        mime = guessed or (f"image/{ext or 'png'}" if fallback_type == "image" else "application/octet-stream")
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def materialize_outputs(project_root: Path, yaml_path: str, task_type: str, task_id: str, outputs: list[str]) -> list[str]:
    localized: list[str] = []
    for index, output in enumerate(outputs):
        if not isinstance(output, str) or not output:
            continue
        if not (output.startswith("http://") or output.startswith("https://")):
            localized.append(output)
            continue
        ext = remote_extension(output, "png" if task_type == "image" else "mp4")
        sub_dir = "images" if task_type == "image" else "videos"
        filename = f"{Path(yaml_path).stem}-{(task_id or 'task')[:8]}-{index}.{ext}"
        rel_path = Path("assets") / sub_dir / filename
        download_file(output, project_root / rel_path, log_prefix="[mangou]")
        localized.append(rel_path.as_posix())
    return localized


def remote_extension(url: str, fallback: str) -> str:
    from urllib.parse import urlparse

    ext = Path(urlparse(url).path).suffix.lstrip(".")
    return ext or fallback


def assert_outputs_exist(project_root: Path, rel_yaml_path: str, outputs: list[str]) -> None:
    for output in outputs:
        if output.startswith("http://") or output.startswith("https://") or output.startswith("data:"):
            continue
        absolute_output = (project_root / output).resolve()
        if not absolute_output.exists():
            raise RuntimeError(f"Materialized output not found for {rel_yaml_path}: {output}")


def describe_outputs(project_root: Path, outputs: list[str]) -> list[dict[str, Any]]:
    descriptions: list[dict[str, Any]] = []
    for output in outputs:
        item: dict[str, Any] = {"path": output}
        if output.startswith("http://") or output.startswith("https://") or output.startswith("data:"):
            descriptions.append(item)
            continue
        absolute_output = (project_root / output).resolve()
        if absolute_output.exists():
            item["bytes"] = absolute_output.stat().st_size
            item["mime"] = MIME_BY_EXTENSION.get(absolute_output.suffix.lower().lstrip(".")) or mimetypes.guess_type(absolute_output.name)[0]
        descriptions.append(item)
    return descriptions


def update_yaml(yaml_path: Path, updates: dict[str, Any]) -> None:
    doc = read_yaml_file(yaml_path)
    for dotted_key, value in updates.items():
        parts = dotted_key.split(".")
        current = doc
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value
    write_yaml_file(yaml_path, doc)


def iso_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()
