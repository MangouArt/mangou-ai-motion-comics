# Lark CLI 协作流程

## 何时阅读

- Hermes 通过飞书群或私聊接收 Mangou 任务
- 需要把飞书文档、图片、视频或文件转成项目输入
- 需要把生成结果回传到飞书文档或群消息
- 需要排查飞书权限、文档分享或附件下载问题

## 职责边界

- `lark-cli` 负责飞书协作层：收发消息、读取或创建文档、上传下载附件、查询联系人或群聊。
- Mangou CLI 负责项目层：初始化项目、维护 YAML、调用 provider、写入 `tasks.jsonl`、生成资产和视频。
- 飞书文档可以承载需求、脚本、评审意见和结果链接，但不能替代项目目录里的 YAML 和 `tasks.jsonl`。
- 文档权限不足时，不要假设项目失败；应先确认 lark-cli 当前身份、应用 scopes、文档 token 和目标 chat/member 权限。

## 推荐流程

1. 从飞书消息或文档提取需求、参考素材和项目 ID。
2. 确认 `MANGOU_WORKSPACE_ROOT` 指向 projects root，例如 `/opt/data/workspace/projects`；如果 Hermes tool 环境读不到该变量，但当前在 Zeabur `/opt/data` 持久卷中运行，使用 `/opt/data/workspace/projects` 作为显式 fallback。
3. 如果项目不存在，执行 `./scripts/project/init.sh --name <project-id>`。
4. 把需求整理为 `asset_defs/*.yaml` 或 `storyboards/*.yaml`，所有路径都相对项目根目录。
5. 调用 `./scripts/asset/generate.sh`、`./scripts/workflow/storyboard-generate.sh`、`./scripts/workflow/storyboard-split.sh` 或 `./scripts/project/stitch.sh`。
6. 读取 `tasks.jsonl` 和 YAML `latest` 字段确认结果。
7. 用 lark-cli 把摘要、产物路径、下载链接或文档更新回传给用户。

## 容器环境

- Hermes 容器内不要使用本地开发机路径，例如 `/home/jachinshen/Sync/Mango/workspace`。
- 线上持久项目目录应使用 `/opt/data/workspace/projects`。
- skill 根目录、lark-cli 配置目录和项目目录是不同概念；不要把任何一个复制成另一个。

## 权限排查

1. 先确认 lark-cli 当前使用的是 bot 还是 user 身份。
2. 权限错误要记录 API 动作和缺失 scope，例如文档成员授权可能需要 `docs:permission.member:create`。
3. 如果无法主动给群或成员授权，可以先发送文档链接、导出内容或把结果直接发到群里，但要说明文档权限仍需补齐。
4. 不要在日志、飞书消息或文档中回显 access token、app secret、refresh token 或 provider API key。

## 输出规范

- 回传给飞书的结果应包含项目 ID、执行命令、关键产物路径和失败原因。
- 产物路径优先使用项目相对路径，例如 `assets/images/shot-001.png`。
- 需要人工继续处理时，明确下一步是补权限、补素材、改 YAML 还是重跑 provider。
