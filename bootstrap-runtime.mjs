#!/usr/bin/env node

import fs from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";
import { execFile } from "child_process";
import { promisify } from "util";

const execFileAsync = promisify(execFile);
const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const SKILL_ROOT = SCRIPT_DIR;

async function pathExists(targetPath) {
  try {
    await fs.access(targetPath);
    return true;
  } catch {
    return false;
  }
}

async function runBunInstall() {
  await execFileAsync("bun", ["install"], {
    cwd: SKILL_ROOT,
    stdio: "inherit",
  });
}

async function main() {
  const runtimeEntry = path.join(SKILL_ROOT, "src", "main.ts");
  const packageJson = path.join(SKILL_ROOT, "package.json");

  if (!(await pathExists(runtimeEntry))) {
    throw new Error("未找到 src/main.ts；当前仓库不完整，无法完成本地 setup。")
  }

  if (!(await pathExists(packageJson))) {
    throw new Error("未找到 package.json；当前仓库不完整，无法完成本地 setup。")
  }

  console.log("Mangou runtime 现已内置在主产品仓中。")
  console.log(`Skill root: ${SKILL_ROOT}`)

  if (!(await pathExists(path.join(SKILL_ROOT, "node_modules")))) {
    console.log("node_modules 缺失，开始执行 bun install...")
    await runBunInstall();
  } else {
    console.log("检测到 node_modules，跳过 bun install。")
  }

  console.log("Setup 完成。你现在可以运行：")
  console.log("  bun run src/main.ts project init --name <project-id>")
}

main().catch((error) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`Mangou setup 失败：${message}`);
  process.exit(1);
});
