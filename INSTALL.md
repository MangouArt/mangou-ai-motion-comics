# INSTALL

## 推荐安装方式

```bash
npx skills add MangouArt/mangou-ai-motion-comics
```

安装完成后，在技能根目录执行：

```bash
node bootstrap-runtime.mjs
```

这个脚本现在承担的是本地 setup 入口，而不是下载额外 zip 再合并。

## 依赖要求

- Bun >= 1.1
- Node.js（用于执行 `bootstrap-runtime.mjs`）
- `ffmpeg` 在系统 PATH 中
- 至少一套可用的 provider 环境变量

## 开发者安装

```bash
cd mangou-ai-motion-comics
npm install
npm run typecheck
npm run test
```

## 仓库边界

- 主产品仓：`mangou-ai-motion-comics`
- Core 仓：`mangou`
- 内部母仓：`Mango`

当前只保留这一条安装路径：
- `npx skills add MangouArt/mangou-ai-motion-comics`

不要再使用任何 zip 包分发或 `mangou/skill-src/mangou` 旧链路。
