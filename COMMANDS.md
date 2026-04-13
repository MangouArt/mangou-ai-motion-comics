# COMMANDS

在本仓完成 setup 后，可使用以下命令：

```bash
# 初始化项目
bun run src/main.ts project init --name <project-id>

# 生成分镜图片
bun run src/main.ts storyboard generate --path storyboards/<shot>.yaml --type image

# 生成分镜视频
bun run src/main.ts storyboard generate --path storyboards/<shot>.yaml --type video

# 切分 grid 分镜图
bun run src/main.ts storyboard split --path storyboards/<shot>.yaml

# 生成资产
bun run src/main.ts asset generate --path asset_defs/<asset>.yaml

# 启动本地只读服务
bun run src/main.ts server start --port 3000
```

## 规则

1. 先改 YAML，再执行命令。
2. provider 行为异常时，同时检查：文档、provider adapter、测试。
3. 真实项目目录只认 `<workspace>/projects/`。
4. 不再依赖 `mangou-runtime.zip` 手工合并模型。
