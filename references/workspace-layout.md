# 项目目录

## 何时阅读

- 要初始化项目
- 不确定 YAML、产物、任务日志该放哪
- 路径引用出错

## 结构

```text
<projects-root>/
  <project_id>/
    project.json
    tasks.jsonl
    storyboards/
    asset_defs/
    assets/
    output/
```

## 目录职责

- `<skill-root>/`: Mangou skill 根目录。不同 agent 会把它安装到不同位置，不要写死平台专属路径。
- `<projects-root>/<project_id>/storyboards/`: 分镜 YAML
- `<projects-root>/<project_id>/asset_defs/`: 资产 YAML
- `<projects-root>/<project_id>/assets/`: 图片和视频产物
- `<projects-root>/<project_id>/tasks.jsonl`: 任务真相源
- `<projects-root>/<project_id>/output/`: 全片导出

## 路径规则

1. 所有 YAML 和命令参数都用相对于项目根目录的路径。
2. 不要跨项目引用别的 `assets/`。
3. 不要手动删除 `tasks.jsonl`。
4. skill 根目录与项目工作区是两个不同层级，不要把真实项目放进 skill 根目录。
5. 先通过当前 agent 的技能机制定位实际 `<skill-root>`，再执行 Python runtime helper scripts。

## 运行时根目录

- `MANGOU_WORKSPACE_ROOT` 当前表示 **workspace root**。
- 真实项目目录固定在 `<workspace-root>/projects/<project-id>/`。
- 本地开发、服务器、容器或其它 agent runtime 都应显式配置自己的 workspace root。
- 如果环境变量不存在，`project init` 必须传 `--workspace <workspace-root>` 或 `--projects-root <projects-root>`；不要退回到 skill 根目录或任意 cwd。
- 执行 `project init` 后必须先确认实际落点，再继续写入资产定义或 storyboard。

## 协作工具边界

- 飞书、Slack、Discord、邮件或其它协作工具只作为输入/输出通道。
- 项目真相源仍是 `<projects-root>/<project_id>/` 下的 `project.json`、YAML、`tasks.jsonl` 和产物文件。
- 从协作工具收到的需求或素材应先落到正确项目目录，再调用 Mangou CLI；不要把聊天或文档当作项目目录或任务真相源。
