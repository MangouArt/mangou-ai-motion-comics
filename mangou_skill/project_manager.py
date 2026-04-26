from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import load_config
from .project import resolve_workspace_and_projects_root


@dataclass
class ProjectMetadata:
    id: str
    name: str
    createdAt: str
    updatedAt: str
    coverUrl: str | None = None
    description: str = ""
    videoUrl: str | None = None


def _resolve_workspace_root() -> Path:
    return resolve_workspace_and_projects_root()[0]


def _resolve_projects_root(workspace_root: Path) -> Path:
    if os.environ.get("MANGOU_HOME"):
        return workspace_root / load_config(workspace_root).workspace_dir
    return resolve_workspace_and_projects_root()[1]


class ProjectManager:
    def __init__(self, workspace_root: str | Path | None = None, projects_root: str | Path | None = None) -> None:
        self.workspace_root = Path(workspace_root).resolve() if workspace_root else _resolve_workspace_root()
        if projects_root:
            self.projects_root = Path(projects_root).resolve()
        elif workspace_root:
            self.projects_root = self.workspace_root / load_config(self.workspace_root).workspace_dir
        else:
            self.projects_root = _resolve_projects_root(self.workspace_root)
        self.index_path = self.workspace_root / "projects.json"

    def init(self) -> None:
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.projects_root.mkdir(parents=True, exist_ok=True)
        if not self.index_path.exists():
            self._save_index({"projects": []})

    def list_projects(self) -> list[dict[str, object]]:
        indexed = self._read_index().get("projects", [])
        scanned = self._scan_projects_root()
        scanned_by_id = {project["id"]: project for project in scanned}
        merged = [scanned_by_id[project["id"]] for project in indexed if project.get("id") in scanned_by_id]
        merged_ids = {project["id"] for project in merged}
        for project in scanned:
            if project["id"] not in merged_ids:
                merged.append(project)
        merged.sort(key=lambda item: item.get("updatedAt", ""), reverse=True)
        self._save_index({"projects": merged})
        return merged

    def get_project(self, project_id: str) -> dict[str, object] | None:
        for project in self.list_projects():
            if project.get("id") == project_id:
                return project
        return None

    def _scan_projects_root(self) -> list[dict[str, object]]:
        projects: list[dict[str, object]] = []
        if not self.projects_root.exists():
            return projects

        for entry in self.projects_root.iterdir():
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            storyboards_dir = entry / "storyboards"
            if not storyboards_dir.exists():
                continue
            tasks_path = entry / "tasks.jsonl"
            tasks_path.touch(exist_ok=True)

            project_json_path = entry / "project.json"
            try:
                project_json = json.loads(project_json_path.read_text(encoding="utf-8"))
            except Exception:
                project_json = {}

            now = datetime.now(timezone.utc).isoformat()
            projects.append(
                {
                    "id": entry.name,
                    "name": project_json.get("name") or entry.name,
                    "description": project_json.get("description") or "",
                    "coverUrl": project_json.get("coverUrl"),
                    "videoUrl": project_json.get("videoUrl"),
                    "createdAt": project_json.get("createdAt") or project_json.get("created_at") or now,
                    "updatedAt": project_json.get("updatedAt") or project_json.get("updated_at") or project_json.get("createdAt") or project_json.get("created_at") or now,
                }
            )
        return projects

    def _read_index(self) -> dict[str, list[dict[str, object]]]:
        try:
            parsed = json.loads(self.index_path.read_text(encoding="utf-8"))
        except Exception:
            return {"projects": []}
        if isinstance(parsed, dict) and isinstance(parsed.get("projects"), list):
            return parsed
        return {"projects": []}

    def _save_index(self, index: dict[str, list[dict[str, object]]]) -> None:
        self.index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
