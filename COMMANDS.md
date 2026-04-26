# COMMANDS

在母仓根目录先执行 `nix develop`，再进入本仓使用以下命令：

```bash
# 初始化项目
./scripts/project/init.sh --name <project-id> --workspace <workspace-root>

# 拼接项目输出
./scripts/project/stitch.sh --id <project-id>

# 生成分镜图片
./scripts/workflow/storyboard-generate.sh --path storyboards/<shot>.yaml --type image

# 生成分镜视频
./scripts/workflow/storyboard-generate.sh --path storyboards/<shot>.yaml --type video

# 恢复已提交但被中断的分镜任务
./scripts/workflow/storyboard-resume.sh --path storyboards/<shot>.yaml --type video

# 生成后输出机器可读 summary
./scripts/workflow/storyboard-generate.sh --path storyboards/<shot>.yaml --type image --json

# 切分 grid 分镜图
./scripts/workflow/storyboard-split.sh --path storyboards/<shot>.yaml

# 生成资产
./scripts/asset/generate.sh --path asset_defs/<asset>.yaml

# 启动本地 runtime API
./scripts/runtime/api-start.sh --port 3000

# 检查 skill 结构
./scripts/doctor/check-layout.sh

# 运行 Python 测试
python3 -m unittest discover -s tests_python -p 'test_*.py' -v
```

## 规则

1. 先读 `references/`，再改 YAML，再执行命令。
2. provider 行为异常时，同时检查：`references/`、provider adapter、测试。
3. 真实项目目录只认 `<workspace>/projects/`。
4. 安装与升级只走 `npx skills add MangouArt/mangou-ai-motion-comics` 主流程，不再使用任何 zip 包分发。
5. `project init`、`project stitch`、`storyboard split`、`runtime api` 均走 Python 主链。
6. `storyboard generate`、`storyboard resume`、`asset generate` 也走 Python provider 主链；默认开发验证不依赖旧 TS 测试链。
7. 飞书文档、群消息和附件协作走 `lark-cli`；项目文件、任务日志和生成产物仍以 `<workspace>/projects/<project-id>/` 为真相源。
8. `MANGOU_WORKSPACE_ROOT` 未设置时，`project init` 必须显式传 `--workspace` 或 `--projects-root`，不要在任意 cwd 下隐式创建 `./projects`。
