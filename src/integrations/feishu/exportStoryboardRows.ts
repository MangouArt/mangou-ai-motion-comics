import fs from "node:fs/promises";
import path from "node:path";
import { parseYAMLQuiet } from "@core/yaml";
import type { StoryboardSheetRow } from "./sheetSchema";

type ExportStoryboardRowsOptions = {
  projectRoot: string;
  now?: string;
};

type StoryboardDoc = {
  meta?: Record<string, any>;
  content?: Record<string, any>;
  tasks?: Record<string, any>;
  refs?: Record<string, any> | any[];
};

export async function exportStoryboardRows({ projectRoot, now = new Date().toISOString() }: ExportStoryboardRowsOptions): Promise<StoryboardSheetRow[]> {
  const projectMeta = await readProjectMeta(projectRoot);
  const storyboardDir = path.join(projectRoot, "storyboards");
  const files = (await fs.readdir(storyboardDir).catch(() => []))
    .filter((file) => file.endsWith(".yaml"))
    .sort();

  const rows: StoryboardSheetRow[] = [];
  for (const file of files) {
    const relPath = path.posix.join("storyboards", file);
    const raw = await fs.readFile(path.join(projectRoot, relPath), "utf-8");
    const doc = parseYAMLQuiet(raw) as StoryboardDoc | null;
    if (!doc) continue;
    rows.push(projectStoryboardRow(projectMeta.id, relPath, doc, now));
  }

  rows.sort((a, b) => a.shot_index - b.shot_index || a.shot_id.localeCompare(b.shot_id));
  return rows;
}

function projectStoryboardRow(projectId: string, yamlPath: string, doc: StoryboardDoc, now: string): StoryboardSheetRow {
  const shotId = asString(doc.meta?.id) || path.basename(yamlPath, ".yaml");
  const sceneId = asString(doc.meta?.scene_id) || asString(doc.content?.scene_id) || deriveSceneId(shotId);
  const imageTask = doc.tasks?.image ?? {};
  const videoTask = doc.tasks?.video ?? {};
  const refs = normalizeRefs(doc.refs);

  return {
    project_id: projectId,
    scene_id: sceneId,
    shot_id: shotId,
    shot_index: asNumber(doc.content?.sequence) ?? 0,
    status: deriveStatus(doc),
    title: asString(doc.content?.title) || shotId,
    storyboard_text: asString(doc.content?.story),
    visual_prompt: asString(imageTask.params?.prompt),
    duration_sec: parseDurationSec(doc.content?.duration),
    character_notes: stringifyList(doc.content?.characters),
    continuity_notes: firstNonEmpty(refs.continuity_notes, refs.continuity, refs.notes),
    reference_links: stringifyList(refs.reference_links),
    output_links: stringifyList([imageTask.latest?.output, videoTask.latest?.output].filter(Boolean)),
    last_sync_at: now,
    yaml_path: yamlPath,
    yaml_key: `meta.id=${shotId}`,
    last_comment_digest: asString(doc.meta?.last_comment_digest),
    feedback_state: asString(doc.meta?.feedback_state) || "unprocessed",
  };
}

async function readProjectMeta(projectRoot: string): Promise<{ id: string }> {
  const projectJsonPath = path.join(projectRoot, "project.json");
  const raw = await fs.readFile(projectJsonPath, "utf-8").catch(() => "{}");
  const parsed = JSON.parse(raw) as { id?: string };
  return {
    id: parsed.id || path.basename(projectRoot),
  };
}

function deriveStatus(doc: StoryboardDoc): string {
  const videoStatus = asString(doc.tasks?.video?.latest?.status);
  if (videoStatus === "completed" || videoStatus === "success") return "done";
  const imageStatus = asString(doc.tasks?.image?.latest?.status);
  if (imageStatus === "completed" || imageStatus === "success") return "reviewing";
  return asString(doc.meta?.feedback_state) === "resolved" ? "approved" : "draft";
}

function normalizeRefs(refs: StoryboardDoc["refs"]): Record<string, any> {
  if (Array.isArray(refs)) {
    return { reference_links: refs };
  }
  if (!refs || typeof refs !== "object") return {};
  return refs;
}

function parseDurationSec(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value !== "string") return null;
  const match = value.trim().match(/(\d+(?:\.\d+)?)/);
  if (!match) return null;
  return Number(match[1]);
}

function deriveSceneId(shotId: string): string {
  const [prefix] = shotId.split("-");
  return prefix || shotId;
}

function stringifyList(value: unknown): string {
  if (Array.isArray(value)) {
    return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0).join("\n");
  }
  if (typeof value === "string") return value;
  if (value == null) return "";
  return String(value);
}

function firstNonEmpty(...values: unknown[]): string {
  for (const value of values) {
    const text = stringifyList(value).trim();
    if (text) return text;
  }
  return "";
}

function asString(value: unknown): string {
  return typeof value === "string" ? value : value == null ? "" : String(value);
}

function asNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}
