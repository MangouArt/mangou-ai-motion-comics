# Mangou AI Motion Comics

Mangou AI Motion Comics 现在是对外主产品仓。

这里统一承接：
- skill 文档
- provider 执行逻辑
- CLI/runtime
- 安装与 setup 入口
- Hermes 自进化落点

## 安装

推荐方式：

```bash
npx skills add MangouArt/mangou-ai-motion-comics
```

安装后，如需本地依赖检查与安装：

```bash
node bootstrap-runtime.mjs
```

## 仓库边界

这里修改：
- `SKILL.md`
- `INSTALL.md`
- `COMMANDS.md`
- `knowledge/*`
- `src/*`
- `test/*`
- provider adapters / registry
- workspace template

不要再把这些内容回写到 `mangou/skill-src/`。

## 开发

```bash
npm install
npm run typecheck
npm run test
npm run build
```

## 关系说明

- `mangou-ai-motion-comics`：最终产品仓
- `mangou`：core / dashboard / spec 仓
- `Mango`：内部母仓 / workspace / orchestration
