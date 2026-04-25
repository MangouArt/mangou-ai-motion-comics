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
argument-hint: <project init|project stitch|storyboard generate|storyboard split|asset generate|runtime api> [...args]
disable-model-invocation: true
---

# Mangou AI Motion Comics

Mangou AI Motion Comics 现在按 skill-first 结构组织，是唯一对外主产品仓。

这里统一承接：
- `SKILL.md`
- `scripts/`
- `references/`
- `mangou_skill/`
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
- [ ] 需要本地运行 CLI 前，先执行 `./scripts/doctor/check-layout.sh`
- [ ] Python 主入口现在是 `python3 -m mangou_skill.cli`
- [ ] 默认测试只使用 `python3 -m unittest discover -s tests_python -p 'test_*.py' -v`
- [ ] 开发和测试统一从母仓根目录执行 `nix develop`
- [ ] 真实项目目录只认 <workspace>/projects/
- [ ] 通过 workspace/.agents/skills/mangou-ai-motion-comics 挂载本仓时，优先在 Mango/workspace 作为 pwd 执行 helper scripts
- [ ] `MANGOU_WORKSPACE_ROOT` 表示 **projects root**，不是 workspace parent；例如容器内应设为 `/opt/data/workspace/projects`
- [ ] `project init` / `project stitch` 现在会优先尊重 `MANGOU_WORKSPACE_ROOT`（其次 `MANGOU_HOME + config.workspaceDir`，最后退回 `process.cwd()/projects`）
- [ ] 执行 `storyboard generate` / `asset generate` / `storyboard split` 时，优先在包含 `project.json` 的项目根目录作为 cwd，`--path` 使用相对项目根路径
- [ ] 先读 `references/workspace-layout.md`，再改 YAML
- [ ] 生成后只信任 tasks.jsonl 和 YAML latest 回填
- [ ] 飞书协作先读 `references/lark-cli-integration.md`；lark-cli 只负责文档、群消息和素材收发，不负责改写项目真相源
- [ ] 若 provider 行为不符合文档，直接在本仓同步修 `references/`、代码与测试
```

## Operating rules

1. 本仓是 skill、references、helper scripts、provider、CLI/runtime 的统一真相源。
2. 所有 provider 产品层修改都应在本仓完成，不回写旧的 `mangou/skill-src`。
3. 真实项目目录只保留在母仓工作区：`Mango/workspace/projects/`；在容器化 Hermes 环境中使用等价持久路径 `/opt/data/workspace/projects/`。
4. 生成失败时先检查 YAML 参数、provider 错误、`tasks.jsonl` 与对应测试。
5. 调优成功后，优先把稳定规则沉淀到本仓的 `references/`、测试或模板；不要写入独立经验库目录。

## Skill structure

- `SKILL.md`: 触发条件、工作规则、references 导航
- `scripts/`: 稳定 helper scripts，给人和 agent 直接调用
- `references/`: 项目管理、YAML、provider、prompt 等长文档
- `mangou_skill/`: Python runtime 与 CLI
- `assets/templates/`: 项目、分镜、资产模板
- `workspace_template/`: 安装后工作区初始化骨架
- `tests_python/`: Python `unittest` 主测试套件

## Core workflows

1. 项目管理：先读 [references/workspace-layout.md](references/workspace-layout.md)，再使用 `scripts/project/*.sh` 初始化或拼接项目。
2. 素材生成：先读 [references/asset-generation.md](references/asset-generation.md)、[references/storyboards.md](references/storyboards.md)，再调用 `scripts/asset/` 或 `scripts/workflow/`。`storyboard generate`、`asset generate`、`storyboard split` 均走 Python 主链。
3. 任务诊断：先读 [references/yaml-state.md](references/yaml-state.md)，再检查 `tasks.jsonl`、YAML latest 和 provider 错误。
4. 飞书协作：先读 [references/lark-cli-integration.md](references/lark-cli-integration.md)，再使用 lark-cli 进行文档、群消息或附件协作。

## Reference map

- 安装：[INSTALL.md](INSTALL.md)
- 命令：[COMMANDS.md](COMMANDS.md)
- 项目目录：[references/workspace-layout.md](references/workspace-layout.md)
- 项目管理：[references/project-management.md](references/project-management.md)
- 资产定义：[references/asset-generation.md](references/asset-generation.md)
- 分镜规范：[references/storyboards.md](references/storyboards.md)
- Prompt 策略：[references/prompts.md](references/prompts.md)
- 一致性规则：[references/consistency.md](references/consistency.md)
- 任务真相源：[references/yaml-state.md](references/yaml-state.md)
- Lark CLI 协作：[references/lark-cli-integration.md](references/lark-cli-integration.md)
- Provider：`references/provider-*.md`
