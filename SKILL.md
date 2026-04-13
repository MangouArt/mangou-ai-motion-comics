---
name: mangou-ai-motion-comics
version: 3.0.0
author: mangou-ai-studio
homepage: https://www.mangou.art
license: FSL-1.1-Apache-2.0
description: Main product repository for AI motion comic production. Includes skill docs, provider adapters, CLI/runtime, workspace template, and local setup entrypoints.
metadata:
  skill_type: local_runtime
  installation_mode: repo-native
  operator_note: "mangou.art operated by Mangou AI Studio"
tags: [ai-motion-comic, motion-comic, storyboard, image-generation, video-generation, production-pipeline, yaml, provider-runtime]
display-name: Mangou AI 漫剧导演 / Motion Comic Director
argument-hint: <project init|project stitch|storyboard generate|storyboard split|asset generate|server start> [...args]
disable-model-invocation: true
---

# Mangou AI Motion Comics

Mangou AI Motion Comics 现在是唯一对外主产品仓。

这里统一承接：
- skill 文档
- provider 执行逻辑
- CLI/runtime
- 安装与 setup 入口
- Hermes 自进化落点

## Use this skill when

- 用户要初始化 Mangou 项目或整理项目目录
- 用户要编写或修正 `asset_defs/*.yaml`、`storyboards/*.yaml`
- 用户要生成分镜图片、视频，或切分 grid 母图
- 用户要排查 provider 参数、payload、poll、回填逻辑
- 用户要更新 Mangou 的 skill 规则、CLI/runtime 行为或 provider 适配脚本

## Quick start

```text
Mangou checklist
- [ ] 先确认本技能已通过 npx skills 安装
- [ ] 需要本地运行 CLI 前，先执行 node bootstrap-runtime.mjs
- [ ] 真实项目目录只认 <workspace>/projects/
- [ ] 通过 workspace/.agents/skills/mangou-ai-motion-comics 挂载本仓时，优先在 Mango/workspace 作为 pwd 执行 CLI
- [ ] `project init` / `project stitch` 现在会优先尊重 `MANGOU_WORKSPACE_ROOT`（其次 `MANGOU_HOME + config.workspaceDir`，最后退回 `process.cwd()/projects`）
- [ ] 先读项目目录规范，再改 YAML
- [ ] 生成后只信任 tasks.jsonl 和 YAML latest 回填
- [ ] 若 provider 行为不符合文档，直接在本仓同步修文档、代码与测试
```

## Operating rules

1. 本仓是 skill、provider、CLI/runtime 的统一真相源。
2. 所有 provider 产品层修改都应在本仓完成，不回写旧的 `mangou/skill-src`。
3. 真实项目目录只保留在母仓工作区：`Mango/workspace/projects/`。
4. 生成失败时先检查 YAML 参数、provider 错误、`tasks.jsonl` 与对应测试。
5. 调优成功后，优先把经验沉淀到本仓的 `knowledge/` / `memories/`。

## Reference map

- 安装：[INSTALL.md](INSTALL.md)
- 命令：[COMMANDS.md](COMMANDS.md)
- 项目目录：[knowledge/directory.md](knowledge/directory.md)
- 资产定义：[knowledge/assets.md](knowledge/assets.md)
- 分镜规范：[knowledge/storyboards.md](knowledge/storyboards.md)
- Prompt 策略：[knowledge/prompts.md](knowledge/prompts.md)
- 任务真相源：[knowledge/tasks.md](knowledge/tasks.md)
- 工作区记忆：[memories/README.md](memories/README.md)
