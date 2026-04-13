import fs from "node:fs/promises";
import path from "node:path";
import { configStore } from "@core/config-store";
import { stitch as runStitch } from "../../stitch";

function resolveWorkspaceRoot(): string {
  const envRoot = process.env.MANGOU_HOME;
  if (envRoot && envRoot.trim()) {
    return path.resolve(envRoot.trim());
  }

  const explicitProjectsRoot = process.env.MANGOU_WORKSPACE_ROOT;
  if (explicitProjectsRoot && explicitProjectsRoot.trim()) {
    return path.dirname(path.resolve(explicitProjectsRoot.trim()));
  }

  return process.cwd();
}

function resolveProjectsRoot(workspaceRoot: string): string {
  const explicitProjectsRoot = process.env.MANGOU_WORKSPACE_ROOT;
  if (explicitProjectsRoot && explicitProjectsRoot.trim()) {
    return path.resolve(explicitProjectsRoot.trim());
  }

  return path.resolve(workspaceRoot, configStore.get("workspaceDir"));
}

export function resolveProjectRoot(projectId: string): string {
  const workspaceRoot = resolveWorkspaceRoot();
  const projectsRoot = resolveProjectsRoot(workspaceRoot);
  return path.join(projectsRoot, projectId);
}

/**
 * Initialize a new project directory structure.
 */
export async function init(positionals: string[], flags: any) {
  const name = flags.name || positionals[0];
  if (!name) throw new Error("Project name is required. Use --name [name] or positional arg.");

  const projectRoot = resolveProjectRoot(name);
  console.log(`[mangou] Initializing project: ${name} at ${projectRoot}`);

  const dirs = [
    "storyboards",
    "asset_defs/chars",
    "asset_defs/scenes",
    "asset_defs/props",
    "assets/images",
    "assets/videos"
  ];

  for (const dir of dirs) {
    await fs.mkdir(path.join(projectRoot, dir), { recursive: true });
  }

  // Create project.json
  const projectMeta = {
    id: name,
    name: name,
    created_at: new Date().toISOString()
  };
  await fs.writeFile(path.join(projectRoot, "project.json"), JSON.stringify(projectMeta, null, 2));

  console.log(`[mangou] Project "${name}" initialized successfully.`);
}

/**
 * Stitch all storyboard videos into a final movie.
 */
export async function stitch(positionals: string[], flags: any) {
  const projectId = flags.id || positionals[0];
  if (!projectId) throw new Error("Project ID is required.");

  const projectRoot = resolveProjectRoot(projectId);
  await runStitch(projectRoot);
}
