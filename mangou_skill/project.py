from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import load_config


PROJECT_DIRS = (
    "storyboards",
    "asset_defs/chars",
    "asset_defs/scenes",
    "asset_defs/props",
    "assets/images",
    "assets/videos",
)


def resolve_workspace_root(cwd: Path | None = None) -> Path:
    env_root = os.environ.get("MANGOU_HOME")
    if env_root and env_root.strip():
        return Path(env_root.strip()).resolve()

    explicit_projects_root = os.environ.get("MANGOU_WORKSPACE_ROOT")
    if explicit_projects_root and explicit_projects_root.strip():
        return Path(explicit_projects_root.strip()).resolve().parent

    return (cwd or Path.cwd()).resolve()


def resolve_projects_root(cwd: Path | None = None) -> Path:
    explicit_projects_root = os.environ.get("MANGOU_WORKSPACE_ROOT")
    if explicit_projects_root and explicit_projects_root.strip():
        return Path(explicit_projects_root.strip()).resolve()

    workspace_root = resolve_workspace_root(cwd)
    return workspace_root / load_config(cwd).workspace_dir


def resolve_project_root(project_id: str, cwd: Path | None = None) -> Path:
    return resolve_projects_root(cwd) / project_id


def resolve_explicit_projects_root(
    cwd: Path | None = None,
    workspace: str | Path | object | None = None,
    projects_root: str | Path | object | None = None,
) -> Path:
    if projects_root:
        return Path(str(projects_root)).expanduser().resolve()
    if workspace:
        return (Path(str(workspace)).expanduser().resolve() / load_config(cwd).workspace_dir).resolve()

    explicit_projects_root = os.environ.get("MANGOU_WORKSPACE_ROOT")
    if explicit_projects_root and explicit_projects_root.strip():
        return Path(explicit_projects_root.strip()).expanduser().resolve()

    env_root = os.environ.get("MANGOU_HOME")
    if env_root and env_root.strip():
        return (Path(env_root.strip()).expanduser().resolve() / load_config(cwd).workspace_dir).resolve()

    current = (cwd or Path.cwd()).resolve()
    if (current / "project.json").exists():
        return current.parent
    if (current / "projects").is_dir() and ((current / "config.json").exists() or (current / "projects.json").exists()):
        return current / "projects"

    raise RuntimeError(
        "MANGOU_WORKSPACE_ROOT is not set and current directory is not a Mangou workspace. "
        "Set MANGOU_WORKSPACE_ROOT, run from an existing project root, or pass --workspace/--projects-root."
    )


def infer_project_root(file_path: Path | str) -> Path:
    current = Path(file_path).resolve().parent
    while True:
        if (current / "project.json").exists():
            return current
        parent = current.parent
        if parent == current:
            raise ValueError(
                f"Unable to infer project root for {file_path}. Expected an ancestor directory containing project.json."
            )
        current = parent


@dataclass(frozen=True)
class ProjectInitResult:
    project_id: str
    project_root: Path


def init_project(
    project_id: str,
    cwd: Path | None = None,
    workspace: str | Path | object | None = None,
    projects_root: str | Path | object | None = None,
) -> ProjectInitResult:
    if not project_id.strip():
        raise ValueError("Project name is required.")

    project_root = resolve_explicit_projects_root(cwd, workspace=workspace, projects_root=projects_root) / project_id
    print(f"[mangou] Initializing project: {project_id} at {project_root}")

    for rel in PROJECT_DIRS:
        (project_root / rel).mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).isoformat()
    project_meta = {
        "id": project_id,
        "name": project_id,
        "created_at": now,
    }
    (project_root / "project.json").write_text(
        json.dumps(project_meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f'[mangou] Project "{project_id}" initialized successfully.')
    return ProjectInitResult(project_id=project_id, project_root=project_root)
