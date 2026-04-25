from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASKS_FILE = "tasks.jsonl"
LOCK_FILE = "tasks.jsonl.lock"
MAX_STRING_LENGTH = 4096
STALE_LOCK_SECONDS = 10
LOCK_WAIT_SECONDS = 0.025


def _stable_stringify(value: Any) -> str:
    if isinstance(value, list):
        return "[" + ",".join(_stable_stringify(item) for item in value) + "]"
    if isinstance(value, dict):
        keys = sorted(value.keys())
        return "{" + ",".join(f"{json.dumps(key)}:{_stable_stringify(value[key])}" for key in keys) + "}"
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _sanitize_task_value(value: Any) -> Any:
    if isinstance(value, list):
        return [_sanitize_task_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_task_value(nested) for key, nested in value.items()}
    if not isinstance(value, str):
        return value

    if value.startswith("data:") and ";base64," in value:
        mime = value[5:].split(";", 1)[0]
        return f"[omitted data-url {mime}]"
    if len(value) > MAX_STRING_LENGTH:
        truncated = len(value) - MAX_STRING_LENGTH
        return f"{value[:MAX_STRING_LENGTH]}...[truncated {truncated} chars]"
    return value


def _compute_task_id(event: dict[str, Any]) -> str:
    payload = {
        "type": event.get("type"),
        "provider": event.get("provider"),
        "input": event.get("input") or {},
        "ref": event.get("ref") or "",
    }
    digest = hashlib.sha1(_stable_stringify(payload).encode("utf-8")).hexdigest()
    return f"task_{digest}"


def _normalize_event(input_event: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    event = {
        "schemaVersion": input_event.get("schemaVersion", 1),
        "id": input_event.get("id"),
        "type": input_event.get("type"),
        "status": input_event.get("status"),
        "provider": input_event.get("provider"),
        "input": _sanitize_task_value(input_event.get("input")),
        "output": _sanitize_task_value(input_event.get("output")),
        "ref": input_event.get("ref"),
        "error": _sanitize_task_value(input_event.get("error")),
        "worker": input_event.get("worker"),
        "event": input_event.get("event"),
        "createdAt": input_event.get("createdAt") or now,
        "updatedAt": now,
    }
    event["id"] = event["id"] or _compute_task_id(event)
    return event


def _ensure_tasks_file(project_root: Path) -> Path:
    project_root.mkdir(parents=True, exist_ok=True)
    tasks_path = project_root / TASKS_FILE
    tasks_path.touch(exist_ok=True)
    return tasks_path


def _is_stale_lock(lock_path: Path) -> bool:
    try:
        return time.time() - lock_path.stat().st_mtime > STALE_LOCK_SECONDS
    except FileNotFoundError:
        return False


def _acquire_lock(lock_path: Path) -> int:
    while True:
        try:
            return os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if _is_stale_lock(lock_path):
                try:
                    lock_path.unlink()
                except FileNotFoundError:
                    pass
                continue
            time.sleep(LOCK_WAIT_SECONDS)


def append_task_event(project_root: Path | str, input_event: dict[str, Any]) -> dict[str, Any]:
    root = Path(project_root)
    tasks_path = _ensure_tasks_file(root)
    lock_path = root / LOCK_FILE
    event = _normalize_event(input_event)
    fd = _acquire_lock(lock_path)
    try:
        with os.fdopen(fd, "w", encoding="utf-8"):
            with tasks_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass
    return _to_snapshot(event)


def _read_all_events(project_root: Path) -> list[dict[str, Any]]:
    tasks_path = _ensure_tasks_file(project_root)
    events: list[dict[str, Any]] = []
    for line in tasks_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _to_snapshot(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": event.get("id", ""),
        "type": event.get("type"),
        "status": event.get("status"),
        "provider": event.get("provider"),
        "input": event.get("input"),
        "output": event.get("output"),
        "ref": event.get("ref"),
        "error": event.get("error"),
        "worker": event.get("worker"),
        "event": event.get("event"),
        "createdAt": event.get("createdAt"),
        "updatedAt": event.get("updatedAt"),
    }


def list_task_events(project_root: Path | str) -> list[dict[str, Any]]:
    return _read_all_events(Path(project_root))


def list_latest_tasks(project_root: Path | str) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for event in list_task_events(project_root):
        event_id = event.get("id") or _compute_task_id(event)
        if not event_id:
            continue
        latest[event_id] = _to_snapshot({**event, "id": event_id})

    def _sort_key(item: dict[str, Any]) -> float:
        stamp = item.get("updatedAt") or item.get("createdAt") or ""
        try:
            return datetime.fromisoformat(str(stamp).replace("Z", "+00:00")).timestamp()
        except Exception:
            return 0

    return sorted(latest.values(), key=_sort_key, reverse=True)


def get_task_by_id(project_root: Path | str, task_id: str) -> dict[str, Any] | None:
    if not task_id:
        return None
    latest = None
    for event in list_task_events(project_root):
        event_id = event.get("id") or _compute_task_id(event)
        if event_id == task_id:
            latest = _to_snapshot({**event, "id": event_id})
    return latest
