# 任务真相源

## 何时阅读

- 生成结果和 YAML 回填对不上
- 想判断任务是否真的成功
- 想排查重复提交、失败原因、split 回填

## 核心事实

1. `projects/<id>/tasks.jsonl` 是唯一真相源。
2. 它是 append-only；同一任务多条记录时，最后一条代表当前状态。
3. 写入器会等待锁释放，但不会替你拦截重复 `pending`。

## 关键字段

- `schemaVersion`
- `id`
- `kind`
- `provider`
- `status`
- `input`
- `output.files`
- `ref.yamlPath`
- `ref.taskType`
- `error.message`

## 回填规则

1. 任务完成后，脚本会把最新状态和产物路径投影到 YAML 的 `tasks.<type>.latest`。
2. 回填失败不影响 `tasks.jsonl` 的可靠性。
3. `storyboard split` 成功后也会补写 `image/success` 事件。
4. 长任务被中断时，YAML `latest.task_id` 是恢复轮询入口；使用 `storyboard resume --path <yaml> --type <image|video>`，不要重新提交 provider 任务。
5. 自动化或 agent 调用生成命令时优先加 `--json`，以机器可读 summary 为准，不解析人类日志最后一行。

## latest 状态

- `running`: 远程任务已提交，仍在等待 provider 结果。
- `interrupted`: 本地命令被中断，但远程任务可能仍在运行，可用 `storyboard resume` 恢复。
- `completed`: 远程任务完成，且本地产物已回填到 `assets/`。
- `remote_status`: provider 侧状态投影，例如 `running`、`completed`。
- `backfill_status`: 本地下载和 YAML 回填状态，例如 `pending`、`completed`、`failed`。

## 诊断顺序

1. 看 `tasks.jsonl` 末尾记录
2. 看 YAML `tasks.<type>.latest`
3. 看 `error.message`
4. 如果有 `task_id` 且远程任务可能未结束，先执行 `storyboard resume`
5. 再决定修参数、修 prompt，还是重跑
