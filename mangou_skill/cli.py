from __future__ import annotations

import sys
import json

from .generate import run_aigc
from .project import init_project
from .server import resolve_server_app_root, resolve_server_data_root, start_http_server
from .stitch import stitch_project
from .storyboard import run_split_grid


def parse_cli_args(argv: list[str]) -> tuple[str, str, list[str], dict[str, object]]:
    flags: dict[str, object] = {}
    raw_positionals: list[str] = []
    i = 0
    while i < len(argv):
        token = argv[i]
        if token.startswith("--"):
            key = _to_camel_case(token[2:])
            if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
                flags[key] = True
            else:
                flags[key] = argv[i + 1]
                i += 1
        else:
            raw_positionals.append(token)
        i += 1

    resource = raw_positionals[0] if raw_positionals else ""
    action = raw_positionals[1] if len(raw_positionals) > 1 else ""
    positionals = raw_positionals[2:]
    return resource, action, positionals, flags


def _to_camel_case(name: str) -> str:
    parts = name.split("-")
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def show_help() -> None:
    print(
        """
Mangou CLI - Python Runtime

Usage:
  mangou <resource> <action> [options]

Resources:
  project
  storyboard
  asset
  server

Examples:
  python3 -m mangou_skill.cli project init --name my-movie
  python3 -m mangou_skill.cli project stitch --id my-movie
  python3 -m mangou_skill.cli storyboard generate --path ./workspace/projects/demo/storyboards/shot-001.yaml --type image
  python3 -m mangou_skill.cli storyboard split --path ./workspace/projects/demo/storyboards/master.yaml
""".strip()
    )


def main(argv: list[str] | None = None) -> int:
    resource, action, positionals, flags = parse_cli_args(argv or sys.argv[1:])

    try:
        if resource in {"", "help"}:
            show_help()
            return 0

        if resource == "project" and action == "init":
            name = str(flags.get("name") or (positionals[0] if positionals else "")).strip()
            if not name:
                raise ValueError("Project name is required. Use --name [name] or positional arg.")
            init_project(name)
            return 0

        if resource == "project" and action == "stitch":
            project_id = str(flags.get("id") or (positionals[0] if positionals else "")).strip()
            if not project_id:
                raise ValueError("Project ID is required. Use --id [id] or positional arg.")
            output_name = str(flags.get("outputName") or flags.get("output") or "output.mp4")
            stitch_project(project_id, output_name=output_name)
            return 0

        if resource == "storyboard" and action == "split":
            yaml_path = str(flags.get("path") or (positionals[0] if positionals else "")).strip()
            if not yaml_path:
                raise ValueError("Parent storyboard YAML path is required.")
            run_split_grid(yaml_path, project_root=flags.get("projectRoot"))
            return 0

        if resource == "storyboard" and action == "generate":
            yaml_path = str(flags.get("path") or (positionals[0] if positionals else "")).strip()
            if not yaml_path:
                raise ValueError("Storyboard YAML path is required.")
            task_type = str(flags.get("type") or "image").strip()
            run_aigc(yaml_path, task_type)
            return 0

        if resource == "asset" and action == "generate":
            yaml_path = str(flags.get("path") or (positionals[0] if positionals else "")).strip()
            if not yaml_path:
                raise ValueError("Asset YAML path is required.")
            run_aigc(yaml_path, "image")
            return 0

        if resource == "server" and action == "paths":
            data_root = resolve_server_data_root(str(flags.get("workspace") or flags.get("dataRoot") or "."))
            print(json.dumps({"appRoot": str(resolve_server_app_root()), "dataRoot": str(data_root)}, ensure_ascii=False))
            return 0

        if resource == "server" and action == "start":
            port = int(str(flags.get("port") or (positionals[0] if positionals else "3000")))
            data_root = resolve_server_data_root(str(flags.get("workspace") or flags.get("dataRoot") or "."))
            server = start_http_server(resolve_server_app_root(), data_root, port=port)
            print(f"[mangou] Starting readonly mirror server on port {port}...")
            print(f"[mangou] App Root: {resolve_server_app_root()}")
            print(f"[mangou] Data Root: {data_root}")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                server.shutdown()
            return 0

        raise ValueError(f'Unsupported command: "{resource} {action}".')
    except Exception as exc:
        print(f"[mangou] Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
