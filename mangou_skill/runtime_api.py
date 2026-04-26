from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .project_manager import ProjectManager
from .yaml_utils import read_yaml_file


ASSET_TYPES = {"character", "scene", "prop"}
STORYBOARD_REF_KEYS = ("characters", "scenes", "props", "assets")


def resolve_runtime_api_app_root() -> Path:
    return Path(__file__).resolve().parent.parent


def resolve_runtime_api_data_root(input_root: str | Path | None = None) -> Path:
    data_root = Path(input_root or Path.cwd()).resolve()
    projects_path = data_root / "projects"
    if projects_path.is_dir():
        data_root = projects_path
    if not data_root.is_dir():
        raise ValueError(f'Data root "{data_root}" is not a directory.')
    return data_root


def get_project_id_from_api_path(pathname: str) -> str | None:
    parts = [part for part in pathname.split("/") if part]
    return parts[2] if len(parts) > 2 else None


def normalize_storyboard_refs(refs: Any) -> list[str]:
    if isinstance(refs, list):
        return [value for value in refs if isinstance(value, str) and value]
    if not isinstance(refs, dict):
        return []
    values: list[str] = []
    seen: set[str] = set()
    for key in STORYBOARD_REF_KEYS:
        bucket = refs.get(key)
        if not isinstance(bucket, list):
            continue
        for item in bucket:
            if isinstance(item, str) and item and item not in seen:
                seen.add(item)
                values.append(item)
    return values


def collect_yaml_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.yaml") if path.is_file())


def get_project_ui_data(project_root: str | Path, project_id: str) -> dict[str, list[dict[str, Any]]]:
    root = Path(project_root).resolve()
    assets: list[dict[str, Any]] = []
    storyboards: list[dict[str, Any]] = []

    for asset_path in collect_yaml_files(root / "asset_defs"):
        doc = read_yaml_file(asset_path)
        asset_type = doc.get("meta", {}).get("type")
        if asset_type not in ASSET_TYPES:
            rel_path = asset_path.relative_to(root).as_posix()
            raise ValueError(f"Invalid asset type in {rel_path}. Expected meta.type to be one of: character, scene, prop.")
        assets.append(
            {
                "id": doc.get("meta", {}).get("id") or asset_path.stem,
                "project_id": project_id,
                "type": asset_type,
                "name": doc.get("content", {}).get("name") or asset_path.name,
                "description": doc.get("content", {}).get("description"),
                "status": doc.get("tasks", {}).get("image", {}).get("latest", {}).get("status") or "pending",
                "image_url": doc.get("tasks", {}).get("image", {}).get("latest", {}).get("output"),
                "version": doc.get("meta", {}).get("version") or "1.0",
                "metadata": doc.get("meta", {}),
                "created_at": "",
            }
        )

    for storyboard_path in sorted((root / "storyboards").glob("*.yaml")) if (root / "storyboards").exists() else []:
        doc = read_yaml_file(storyboard_path)
        image_latest = doc.get("tasks", {}).get("image", {}).get("latest", {})
        video_latest = doc.get("tasks", {}).get("video", {}).get("latest", {})
        storyboards.append(
            {
                "id": doc.get("meta", {}).get("id") or storyboard_path.stem,
                "project_id": project_id,
                "sequence_number": doc.get("content", {}).get("sequence") or 0,
                "title": doc.get("content", {}).get("title") or storyboard_path.name,
                "description": doc.get("content", {}).get("story"),
                "prompt": doc.get("tasks", {}).get("image", {}).get("params", {}).get("prompt"),
                "image_url": image_latest.get("output"),
                "video_url": video_latest.get("output"),
                "status": "completed"
                if video_latest.get("status") == "completed" or image_latest.get("status") == "completed"
                else "pending",
                "asset_ids": normalize_storyboard_refs(doc.get("refs")),
                "grid": doc.get("meta", {}).get("grid"),
                "parentId": doc.get("meta", {}).get("parent"),
                "tasks": doc.get("tasks", {}),
                "metadata": doc.get("meta", {}),
                "created_at": "",
            }
        )

    storyboards.sort(key=lambda item: item["sequence_number"])
    return {"assets": assets, "storyboards": storyboards}


def create_project_manager(data_root: str | Path) -> ProjectManager:
    root = Path(data_root).resolve()
    return ProjectManager(workspace_root=root.parent, projects_root=root)


def get_content_type_by_path(file_path: str) -> str:
    ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
    if ext in {"yaml", "yml"}:
        return "text/yaml; charset=utf-8"
    if ext == "json":
        return "application/json; charset=utf-8"
    if ext == "txt":
        return "text/plain; charset=utf-8"
    if ext == "md":
        return "text/markdown; charset=utf-8"
    if ext == "png":
        return "image/png"
    if ext in {"jpg", "jpeg"}:
        return "image/jpeg"
    if ext == "gif":
        return "image/gif"
    if ext == "webp":
        return "image/webp"
    if ext == "mp4":
        return "video/mp4"
    guessed, _ = mimetypes.guess_type(file_path)
    return guessed or "application/octet-stream"


def get_cache_control_by_content_type(content_type: str) -> str:
    lower = content_type.lower()
    if lower.startswith("text/") or "json" in lower or "yaml" in lower or "markdown" in lower:
        return "no-store"
    return "public, max-age=31536000, immutable"


STATUS_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>Mangou Motion Comics Runtime</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { background: #09090b; color: #fafafa; font-family: sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 1rem; box-sizing: border-box; }
    .card { background: #18181b; border: 1px solid #27272a; padding: 2.5rem; border-radius: 0.75rem; text-align: left; max-width: 560px; width: 100%; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4); }
    h1 { color: #f4f4f5; margin-bottom: 1rem; font-size: 1.5rem; letter-spacing: -0.025em; }
    p, li { color: #a1a1aa; line-height: 1.6; font-size: 0.95rem; }
    code { background: #27272a; padding: 0.2rem 0.45rem; border-radius: 0.375rem; color: #e4e4e7; font-family: monospace; font-size: 0.9em; }
    .status { display: inline-flex; align-items: center; background: rgba(34, 197, 94, 0.1); color: #4ade80; padding: 0.35rem 0.75rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 500; margin-bottom: 1.25rem; }
    .dot { width: 8px; height: 8px; background: currentColor; border-radius: 50%; margin-right: 0.5rem; }
    a { color: #3b82f6; text-decoration: none; }
    a:hover { text-decoration: underline; }
    ul { padding-left: 1.25rem; }
  </style>
</head>
<body>
  <div class="card">
    <div class="status"><span class="dot"></span>Runtime Active</div>
    <h1>Mangou Motion Comics Runtime</h1>
    <p>这个仓库承接 skill、provider、CLI 和 Python runtime API。项目数据以 workspace projects 目录为真相源。</p>
    <ul>
      <li>项目 API：<a href="/api/projects"><code>/api/projects</code></a></li>
      <li>运行入口：<code>./scripts/runtime/api-start.sh</code></li>
      <li>数据目录：<code>MANGOU_WORKSPACE_ROOT</code> 指向 workspace root，项目位于其 <code>projects/</code> 子目录</li>
    </ul>
  </div>
</body>
</html>
"""


def start_runtime_api(app_root: str | Path, data_root: str | Path, port: int = 3000) -> ThreadingHTTPServer:
    app_root_path = Path(app_root).resolve()
    data_root_path = Path(data_root).resolve()
    project_manager = create_project_manager(data_root_path)
    project_manager.init()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            pathname = parsed.path
            query = parse_qs(parsed.query)

            if pathname == "/api/projects":
                return self._send_json(HTTPStatus.OK, {"success": True, "projects": project_manager.list_projects()})

            if pathname == "/api/meta":
                return self._send_json(
                    HTTPStatus.OK,
                    {"success": True, "data": {"appRoot": str(app_root_path), "dataRoot": str(data_root_path)}},
                )

            if pathname.startswith("/api/projects/"):
                project_id = get_project_id_from_api_path(pathname)
                if not project_id:
                    return self._send_json(HTTPStatus.BAD_REQUEST, {"success": False, "error": "Missing project id"})
                try:
                    if pathname.endswith("/snapshot"):
                        payload = get_project_ui_data(data_root_path / project_id, project_id)
                        return self._send_json(HTTPStatus.OK, {"success": True, **payload})
                    project = project_manager.get_project(project_id)
                    if not project:
                        return self._send_json(HTTPStatus.NOT_FOUND, {"success": False, "error": "Project not found"})
                    payload = get_project_ui_data(data_root_path / project_id, project_id)
                    return self._send_json(HTTPStatus.OK, {"success": True, "project": project, **payload, "keyframes": [], "videos": []})
                except Exception as exc:
                    return self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"success": False, "error": str(exc)})

            if pathname == "/api/vfs":
                project_id = (query.get("projectId") or [None])[0]
                rel_path = (query.get("path") or [None])[0]
                if not project_id or not rel_path:
                    return self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Missing params"})
                target = (data_root_path / project_id / rel_path).resolve()
                if not target.exists() or not str(target).startswith(str((data_root_path / project_id).resolve())):
                    return self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
                content_type = get_content_type_by_path(rel_path)
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", content_type)
                self.send_header("Cache-Control", get_cache_control_by_content_type(content_type))
                self.end_headers()
                self.wfile.write(target.read_bytes())
                return

            if pathname in {"", "/"}:
                body = STATUS_HTML.encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            self._send_json(HTTPStatus.NOT_FOUND, {"success": False, "error": "Not found"})

        def log_message(self, format: str, *args: object) -> None:
            return

        def _send_json(self, status: HTTPStatus, data: dict[str, Any]) -> None:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    return server
