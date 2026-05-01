from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def save_feishu_doc_link(
    project_root: str | Path,
    *,
    document_id: str,
    url: str,
    title: str = "",
    role: str = "primary",
    notes: str = "",
) -> dict[str, Any]:
    """Persist the primary Feishu/Lark document link for a Mangou project."""
    root = Path(project_root).resolve()
    if not (root / "project.json").exists():
        raise FileNotFoundError(f"project.json not found under {root}")
    if not document_id.strip() or not url.strip():
        raise ValueError("document_id and url are required")

    payload: dict[str, Any] = {
        "title": title.strip() or document_id.strip(),
        "document_id": document_id.strip(),
        "url": url.strip(),
        "role": role.strip() or "primary",
    }
    if notes.strip():
        payload["notes"] = notes.strip()

    path = root / "feishu_doc.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"path": str(path), **payload}


def load_feishu_doc_link(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).resolve()
    path = root / "feishu_doc.json"
    if not path.exists():
        raise FileNotFoundError(f"feishu_doc.json not found under {root}")
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in ("document_id", "url"):
        if not data.get(key):
            raise ValueError(f"feishu_doc.json missing required key: {key}")
    data["path"] = str(path)
    return data


def print_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))
