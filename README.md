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
- Hermes 自进化落点

这里不再承接：
- dashboard 前端源码
- vite 构建链
- dist 静态产物

Dashboard npm 包与前端构建真相源统一留在 `mangou`。

## Skill 结构

```text
mangou-ai-motion-comics/
├── SKILL.md
├── scripts/
├── references/
├── mangou_skill/
├── assets/templates/
├── workspace_template/
├── src/
├── test/
└── tests_python/
```

说明：
- `scripts/` 是稳定 helper scripts 入口
- `references/` 是长文档，不再使用 `knowledge/`
- `mangou_skill/` 是新的 Python 主运行链
- `src/` 里仍有遗留 TS/provider 代码，仅作为迁移期参考，不再作为默认入口
- `test/fixtures/projects/` 只保留测试样例，不代表真实工作区

## 安装

推荐方式：

```bash
npx skills add MangouArt/mangou-ai-motion-comics
```

开发与本地运行统一走母仓根目录 `flake.nix`：

```bash
nix develop
```

进入壳后，如需本地依赖检查与安装：

```bash
node bootstrap-runtime.mjs
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
- `src/*`
- `test/*`
- provider adapters / registry
- workspace template

不要再把这些内容回写到 `mangou/skill-src/`。

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
./scripts/workflow/server-start.sh --port 3000
```

## 关系说明

- `mangou-ai-motion-comics`：最终产品仓（skill / provider / runtime）
- `mangou`：core / dashboard / spec 仓
- `Mango`：内部母仓 / workspace / orchestration
