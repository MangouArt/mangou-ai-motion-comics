from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def parse_yaml(content: str) -> Any:
    if not isinstance(content, str) or not content.strip():
        raise ValueError("YAML 内容为空或无效")
    data = yaml.safe_load(content)
    if data is None:
        raise ValueError("YAML 解析结果为空")
    return data


def parse_yaml_quiet(content: str) -> Any | None:
    if not isinstance(content, str) or not content.strip():
        return None
    try:
        return yaml.safe_load(content)
    except Exception:
        return None


def dump_yaml(data: Any) -> str:
    return yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        width=10_000,
    )


def read_yaml_file(path: Path) -> Any:
    return parse_yaml(path.read_text(encoding="utf-8"))


def write_yaml_file(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_yaml(data), encoding="utf-8")
