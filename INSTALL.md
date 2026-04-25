# INSTALL

## 推荐安装方式

```bash
npx skills add MangouArt/mangou-ai-motion-comics
```

安装完成后，在技能根目录执行：

```bash
nix develop
node bootstrap-runtime.mjs
```

这个脚本现在承担的是本地 setup 入口，而不是下载额外 zip 再合并。

本地 setup 完成后，优先通过 helper scripts 调用：

```bash
./scripts/project/init.sh --name <project-id>
./scripts/workflow/storyboard-generate.sh --path storyboards/<shot>.yaml --type image
./scripts/asset/generate.sh --path asset_defs/<asset>.yaml
```

当前 Python 主链已经接管：
- `project init`
- `project stitch`
- `storyboard generate`
- `asset generate`
- `storyboard split`
- `server start`
- 基础 CLI 入口
- 基础测试链

## 依赖要求

- Python >= 3.11
- 通过母仓根目录 `flake.nix` 进入开发环境
- Node.js（仅用于 `bootstrap-runtime.mjs`）
- `ffmpeg` 在系统 PATH 中
- 至少一套可用的 provider 环境变量

## 开发者安装

```bash
nix develop
cd mangou-ai-motion-comics
python3 -m unittest discover -s tests_python -p 'test_*.py' -v
```

## 仓库边界

- 主产品仓：`mangou-ai-motion-comics`
- Core 仓：`mangou`
- 内部母仓：`Mango`

当前只保留这一条安装路径：
- `npx skills add MangouArt/mangou-ai-motion-comics`

不要再使用任何 zip 包分发或 `mangou/skill-src/mangou` 旧链路。

## 工作区规则

- 真实项目目录只认 `<workspace>/projects/`
- 不要把 skill 根目录当成项目目录
- `test/fixtures/projects/` 只是测试夹具，不是工作区
