# Hermes Evolution

线上 Hermes 可以从真实协作中总结经验，但永久修改 skill 必须通过产品仓 PR 固化。

## Boundary

- 运行态记忆、单项目偏好、用户审美习惯：保留在 Hermes memory 或项目目录，不写回 skill。
- 通用流程、字段约束、provider 事实、安装/排障规则：可以写回本仓。
- 代码、runtime、provider adapter 变更：必须带测试并人工 review。
- `SKILL.md`、`references/*.md`、模板说明类变更：可以在 CI 通过后合并。

## Flow

默认主流程：直接在本地 `mangou-ai-motion-comics` skill 真相源 checkout 修改、验证、只 stage 本次相关文件并 commit，然后运行 `scripts/evolution/propose-skill-change.sh` 自动 push 分支和创建 PR。不要把新建 `/tmp` clone 当成默认提 PR 主路径；`/tmp` 干净 clone 只用于隔离验证、复现上游或本地副本缺脚本/状态太脏时兜底。

```text
线上反馈
  -> Hermes 判断是否为通用经验
  -> 记录 evolution inbox
  -> 修改本仓文件
  -> 运行 doctor/test
  -> 开 PR 到 mangou-ai-motion-comics
  -> merge 后重新部署或更新线上 skill
```

## Required environment

线上环境需要以下变量：

- `GITHUB_TOKEN`: GitHub token，只给 `MangouArt/mangou-ai-motion-comics` 开分支和 PR 的权限。
- `HERMES_EVOLUTION_REPO`: 默认 `MangouArt/mangou-ai-motion-comics`。
- `HERMES_EVOLUTION_BASE_BRANCH`: 默认 `dev`。
- `HERMES_EVOLUTION_WORKDIR`: 本地产品仓 checkout，默认当前 skill 根目录。
- `HERMES_EVOLUTION_INBOX`: evolution 反馈记录，默认 `/opt/data/evolution/inbox.jsonl`。

## Record feedback

先把线上触发事实记录下来：

```bash
./scripts/evolution/record-feedback.sh \
  --title "KIE video poll timeout should mention async task wait" \
  --source "feishu://chat/..." \
  --summary "用户多次遇到 KIE 任务未完成但 agent 当作失败。" \
  --classification provider-fact
```

## Open PR

Hermes 修改本仓文件并验证后执行：

```bash
./scripts/evolution/propose-skill-change.sh \
  --title "Clarify KIE async polling behavior" \
  --summary "Document that pending KIE video jobs should be resumed instead of retried immediately." \
  --evidence "Observed in Feishu production run 2026-05-01." \
  --validate
```

脚本会创建 `hermes/evolution-<timestamp>` 分支、提交当前 diff、推送到 GitHub，并创建 PR。

## Review rules

PR 描述必须说明：

- 线上反馈证据。
- 为什么这是通用经验。
- 修改范围。
- 验证命令。

不要把完整用户私聊、secret、provider key、个人偏好或单项目审美写入 PR。
