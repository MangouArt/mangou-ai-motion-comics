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

async function runCommand(command, args) {
  return execFileAsync(command, args, {
    cwd: SKILL_ROOT,
    stdio: "pipe",
  });
}

async function main() {
  const runtimeEntry = path.join(SKILL_ROOT, "mangou_skill", "cli.py");
  const pyprojectToml = path.join(SKILL_ROOT, "pyproject.toml");

  if (!(await pathExists(runtimeEntry))) {
    throw new Error("未找到 mangou_skill/cli.py；当前仓库不完整，无法完成本地 setup。");
  }

  if (!(await pathExists(pyprojectToml))) {
    throw new Error("未找到 pyproject.toml；当前仓库不完整，无法完成本地 setup。");
  }

  console.log("Mangou runtime 现已切到 Python 主链。");
  console.log(`Skill root: ${SKILL_ROOT}`);

  const checks = [
    ["python3", ["--version"], "Python 3"],
    ["ffmpeg", ["-version"], "FFmpeg"],
  ];

  for (const [command, args, label] of checks) {
    try {
      const result = await runCommand(command, args);
      const output = `${result.stdout || ""}${result.stderr || ""}`.trim().split("\n")[0] || "(no output)";
      console.log(`${label}: ${output}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      throw new Error(`${label} 不可用，请先从母仓根目录执行 nix develop。原始错误：${message}`);
    }
  }

  console.log("Setup 完成。你现在可以运行：");
  console.log("  ./scripts/project/init.sh --name <project-id>");
  console.log("  ./scripts/workflow/storyboard-generate.sh --path storyboards/<shot>.yaml --type image");
}

main().catch((error) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`Mangou setup 失败：${message}`);
  process.exit(1);
});
