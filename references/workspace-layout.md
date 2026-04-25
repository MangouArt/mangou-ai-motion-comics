# 项目目录

## 何时阅读

- 要初始化项目
- 不确定 YAML、产物、任务日志该放哪
- 路径引用出错

## 结构

```text
<workspace_root>/
  <skill-root>/
  config.json
  projects.json
  projects/
    <project_id>/
      project.json
      tasks.jsonl
      storyboards/
      asset_defs/
      assets/
      output/
```

## 目录职责

- `<skill-root>/`: Mangou skill 根目录。不同 agent 会把它安装到不同位置，不要写死 `.claude`、`.agents` 或其他平台专属路径。
- `config.json`: 全局 provider 配置
- `projects/<project_id>/storyboards/`: 分镜 YAML
- `projects/<project_id>/asset_defs/`: 资产 YAML
- `projects/<project_id>/assets/`: 图片和视频产物
- `projects/<project_id>/tasks.jsonl`: 任务真相源
- `projects/<project_id>/output/`: 全片导出

## 路径规则

1. 所有 YAML 和命令参数都用相对于项目根目录的路径。
2. 不要跨项目引用别的 `assets/`。
3. 不要手动删除 `tasks.jsonl`。
4. skill 根目录与项目工作区是两个不同层级，不要把 `projects/` 放进 skill 根目录。
5. 先通过当前 agent 的技能机制定位实际 `<skill-root>`，再执行 runtime 合并或 Bun 命令。

## 运行时根目录

- `MANGOU_WORKSPACE_ROOT` 当前表示 **projects root**，不是 workspace parent。
- 本地母仓通常设置或推断为 `Mango/workspace/projects`。
- 容器化 Hermes / Feishu 环境没有本地路径 `/home/jachinshen/Sync/Mango/workspace`，应使用持久卷内路径 `/opt/data/workspace/projects`。
- 执行 `project init` 后必须先确认实际落点，再继续写入资产定义或 storyboard。
