from __future__ import annotations

import sys
import json

from .generate import print_json_summary, resume_aigc, run_aigc_summary
from .project import init_project
from .runtime_api import resolve_runtime_api_app_root, resolve_runtime_api_data_root, start_runtime_api
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
  runtime api

Examples:
  python3 -m mangou_skill.cli project init --name my-movie
  python3 -m mangou_skill.cli project init --name my-movie --workspace ./workspace
  python3 -m mangou_skill.cli project stitch --id my-movie
  python3 -m mangou_skill.cli storyboard generate --path ./workspace/projects/demo/storyboards/shot-001.yaml --type image
  python3 -m mangou_skill.cli storyboard resume --path ./workspace/projects/demo/storyboards/shot-001.yaml --type video
  python3 -m mangou_skill.cli storyboard split --path ./workspace/projects/demo/storyboards/master.yaml
  python3 -m mangou_skill.cli runtime api --port 3000 --workspace ./workspace
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
            init_project(
                name,
                workspace=flags.get("workspace"),
                projects_root=flags.get("projectsRoot"),
            )
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
            summary = run_aigc_summary(yaml_path, task_type)
            if flags.get("json"):
                print_json_summary(summary)
            return 0

        if resource == "storyboard" and action == "resume":
            yaml_path = str(flags.get("path") or (positionals[0] if positionals else "")).strip()
            if not yaml_path:
                raise ValueError("Storyboard YAML path is required.")
            task_type = str(flags.get("type") or "image").strip()
            task_id = str(flags.get("id") or flags.get("taskId") or "").strip() or None
            summary = resume_aigc(yaml_path, task_type, task_id=task_id)
            if flags.get("json"):
                print_json_summary(summary)
            return 0

        if resource == "asset" and action == "generate":
            yaml_path = str(flags.get("path") or (positionals[0] if positionals else "")).strip()
            if not yaml_path:
                raise ValueError("Asset YAML path is required.")
            summary = run_aigc_summary(yaml_path, "image")
            if flags.get("json"):
                print_json_summary(summary)
            return 0

        if resource == "runtime" and action == "paths":
            data_root = resolve_runtime_api_data_root(str(flags.get("workspace") or flags.get("dataRoot") or "."))
            print(json.dumps({"appRoot": str(resolve_runtime_api_app_root()), "dataRoot": str(data_root)}, ensure_ascii=False))
            return 0

        if resource == "runtime" and action == "api":
            port = int(str(flags.get("port") or (positionals[0] if positionals else "3000")))
            data_root = resolve_runtime_api_data_root(str(flags.get("workspace") or flags.get("dataRoot") or "."))
            server = start_runtime_api(resolve_runtime_api_app_root(), data_root, port=port)
            print(f"[mangou] Starting runtime API on port {port}...")
            print(f"[mangou] App Root: {resolve_runtime_api_app_root()}")
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
