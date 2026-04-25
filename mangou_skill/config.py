from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    workspace_dir: str = "projects"


def resolve_config_path(cwd: Path | None = None) -> Path:
    base = Path(os.environ.get("MANGOU_HOME") or cwd or Path.cwd()).resolve()
    return base / "config.json"


def load_config(cwd: Path | None = None) -> AppConfig:
    config_path = resolve_config_path(cwd)
    if not config_path.exists():
        return AppConfig()

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return AppConfig()

    workspace_dir = data.get("workspaceDir") or "projects"
    return AppConfig(workspace_dir=str(workspace_dir))
