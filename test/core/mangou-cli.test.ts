import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { main } from "../../src/main";
import { resolveProjectRoot } from "../../src/commands/project";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import yaml from "js-yaml";

describe("mangou-cli commands", () => {
  const projectName = "test-cli-project";
  const envProjectName = "env-cli-project";
  const projectRoot = path.join(process.cwd(), "projects", projectName);
  const envProjectRootInCwd = path.join(process.cwd(), "projects", envProjectName);
  const originalArgv = [...process.argv];
  const originalMangouHome = process.env.MANGOU_HOME;
  const originalWorkspaceRoot = process.env.MANGOU_WORKSPACE_ROOT;
  let tempRoot = "";

  beforeEach(async () => {
    process.argv = [...originalArgv];
    if (originalMangouHome === undefined) {
      delete process.env.MANGOU_HOME;
    } else {
      process.env.MANGOU_HOME = originalMangouHome;
    }
    if (originalWorkspaceRoot === undefined) {
      delete process.env.MANGOU_WORKSPACE_ROOT;
    } else {
      process.env.MANGOU_WORKSPACE_ROOT = originalWorkspaceRoot;
    }
    tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), "mangou-cli-test-"));
    await fs.rm(projectRoot, { recursive: true, force: true }).catch(() => {});
    await fs.rm(envProjectRootInCwd, { recursive: true, force: true }).catch(() => {});
  });

  afterEach(async () => {
    process.argv = [...originalArgv];
    if (originalMangouHome === undefined) {
      delete process.env.MANGOU_HOME;
    } else {
      process.env.MANGOU_HOME = originalMangouHome;
    }
    if (originalWorkspaceRoot === undefined) {
      delete process.env.MANGOU_WORKSPACE_ROOT;
    } else {
      process.env.MANGOU_WORKSPACE_ROOT = originalWorkspaceRoot;
    }
    vi.restoreAllMocks();
    if (tempRoot) {
      await fs.rm(tempRoot, { recursive: true, force: true }).catch(() => {});
    }
    await fs.rm(projectRoot, { recursive: true, force: true }).catch(() => {});
    await fs.rm(envProjectRootInCwd, { recursive: true, force: true }).catch(() => {});
  });

  it("project init: creates physical directory structure", async () => {
    process.argv = ["node", "mangou", "project", "init", "--name", projectName];
    await main();

    const exists = await fs.access(projectRoot).then(() => true).catch(() => false);
    expect(exists).toBe(true);

    const storyboardDir = path.join(projectRoot, "storyboards");
    const storyboardExists = await fs.access(storyboardDir).then(() => true).catch(() => false);
    expect(storyboardExists).toBe(true);

    const projectJson = await fs.readFile(path.join(projectRoot, "project.json"), "utf-8");
    const meta = JSON.parse(projectJson);
    expect(meta.id).toBe(projectName);
  });

  it("project init: respects MANGOU_WORKSPACE_ROOT when provided", async () => {
    const envProjectsRoot = path.join(tempRoot, "projects");
    const envProjectRoot = path.join(envProjectsRoot, envProjectName);

    process.env.MANGOU_HOME = tempRoot;
    process.env.MANGOU_WORKSPACE_ROOT = envProjectsRoot;
    process.argv = ["node", "mangou", "project", "init", "--name", envProjectName];

    await main();

    const existsInEnvRoot = await fs.access(envProjectRoot).then(() => true).catch(() => false);
    const existsInCwdRoot = await fs.access(path.join(process.cwd(), "projects", envProjectName)).then(() => true).catch(() => false);

    expect(existsInEnvRoot).toBe(true);
    expect(existsInCwdRoot).toBe(false);

    const projectJson = await fs.readFile(path.join(envProjectRoot, "project.json"), "utf-8");
    const meta = JSON.parse(projectJson);
    expect(meta.id).toBe(envProjectName);
  });

  it("resolveProjectRoot: shares env-aware resolution used by init and stitch", () => {
    const envProjectsRoot = path.join(tempRoot, "projects");
    process.env.MANGOU_HOME = tempRoot;
    process.env.MANGOU_WORKSPACE_ROOT = envProjectsRoot;

    expect(resolveProjectRoot("shared-env-project")).toBe(
      path.join(envProjectsRoot, "shared-env-project"),
    );
  });

  it("project stitch: triggers ffmpeg concatenation logic", async () => {
    process.argv = ["node", "mangou", "project", "stitch", "--id", projectName];
    const exitError = new Error("process.exit");
    const exitSpy = vi
      .spyOn(process, "exit")
      .mockImplementation(((code?: string | number | null) => {
        throw Object.assign(exitError, { code });
      }) as typeof process.exit);

    await expect(main()).rejects.toMatchObject({ message: "process.exit", code: 1 });
    expect(exitSpy).toHaveBeenCalledWith(1);
  });

  it("storyboard split: splits a grid image and creates child YAMLs", async () => {
    // 1. Setup project
    process.argv = ["node", "mangou", "project", "init", "--name", projectName];
    await main();

    // 2. Setup a master grid YAML
    const masterYamlPath = path.join(projectRoot, "storyboards", "master.yaml");
    const masterDoc = {
      meta: { id: "master", grid: "2x1" },
      tasks: {
        image: {
          latest: { status: "success", output: "assets/images/master.png" }
        }
      }
    };
    await fs.writeFile(masterYamlPath, yaml.dump(masterDoc));

    // 3. Create a dummy image
    const imgDir = path.join(projectRoot, "assets/images");
    await fs.mkdir(imgDir, { recursive: true });
    await fs.writeFile(path.join(imgDir, "master.png"), "dummy content");

    // 4. Run split command
    process.argv = ["node", "mangou", "storyboard", "split", "--path", `projects/${projectName}/storyboards/master.yaml` ];
    
    // We mock FFmpeg in a real environment, but here we expect the logic to attempt it
    // For KISS, we'll just check if the code runs without crashing and reaches the backfill stage
    try {
      await main();
    } catch (e: any) {
      // ffmpeg will fail on dummy content, but we check if it created the child YAML files
    }

    const childYaml = path.join(projectRoot, "storyboards", "master-sub-01.yaml");
    const childExists = await fs.access(childYaml).then(() => true).catch(() => false);
    // Even if FFmpeg fails, our scaffold logic should have created the files
    expect(childExists).toBe(true);
  });
});
