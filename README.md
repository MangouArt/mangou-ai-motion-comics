# Mangou AI Motion Comics

Mangou AI Motion Comics 现在是对外主产品仓，并按 skill-first 结构组织。

这里统一承接：
- `SKILL.md`
- `scripts/`
- `references/`
- `mangou_skill/`
- provider 执行逻辑
- CLI/runtime
- 安装与 setup 入口
- agent workflow 规则

本仓只维护 Python skill、provider、CLI/runtime、workspace template 和文档真相源。

## Skill 结构

```text
mangou-ai-motion-comics/
├── SKILL.md
├── scripts/
├── references/
├── mangou_skill/
├── assets/templates/
├── workspace_template/
└── tests_python/
```

说明：
- `scripts/` 是稳定 helper scripts 入口
- `references/` 是长文档，不再使用 `knowledge/`
- `mangou_skill/` 是 Python 主运行链
- `tests_python/` 是唯一默认测试套件，使用标准库 `unittest`

## 安装

推荐方式：

```bash
npx skills add MangouArt/mangou-ai-motion-comics
```

开发与本地运行统一走母仓根目录 `flake.nix`：

```bash
nix develop
```

进入壳后，先做结构检查：

```bash
./scripts/doctor/check-layout.sh
```

基础 Python 验证入口：

```bash
python3 -m unittest discover -s tests_python -p 'test_*.py' -v
```

## 仓库边界

这里修改：
- `SKILL.md`
- `INSTALL.md`
- `COMMANDS.md`
- `references/*`
- `scripts/*`
- provider adapters / registry
- `mangou_skill/*`
- `tests_python/*`
- workspace template

不要再把这些内容回写到旧链路。

## 开发

```bash
nix develop
python3 -m unittest discover -s tests_python -p 'test_*.py' -v
```

已经切到 Python 的入口：

```bash
./scripts/project/init.sh --name <project-id>
./scripts/project/stitch.sh --id <project-id>
./scripts/workflow/storyboard-generate.sh --path storyboards/<shot>.yaml --type image
./scripts/asset/generate.sh --path asset_defs/<asset>.yaml
./scripts/workflow/storyboard-split.sh --path <storyboard-yaml>
./scripts/runtime/api-start.sh --port 3000
```

## 关系说明

- `mangou-ai-motion-comics`：最终产品仓（skill / provider / runtime）
- `mangou`：core / spec / provider 无关 utilities 仓
- `Mango`：内部母仓 / workspace / orchestration
