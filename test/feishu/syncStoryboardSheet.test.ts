import { describe, expect, it, vi } from "vitest";
import { buildStoryboardSheetSyncPlan, syncStoryboardSheet } from "../../src/integrations/feishu/syncStoryboardSheet";
import type { StoryboardSheetRow } from "../../src/integrations/feishu/sheetSchema";

const row: StoryboardSheetRow = {
  project_id: "demo",
  scene_id: "scene-1",
  shot_id: "shot-1",
  shot_index: 1,
  status: "draft",
  title: "Opening",
  storyboard_text: "开场",
  visual_prompt: "industrial sci-fi",
  duration_sec: 4,
  character_notes: "杜休",
  continuity_notes: "",
  reference_links: "",
  output_links: "",
  last_sync_at: "2026-04-20T12:00:00.000Z",
  yaml_path: "storyboards/shot-1.yaml",
  yaml_key: "meta.id=shot-1",
  last_comment_digest: "",
  feedback_state: "unprocessed",
};

describe("syncStoryboardSheet", () => {
  it("builds a replace plan with hidden system columns", () => {
    const plan = buildStoryboardSheetSyncPlan([row]);

    expect(plan.sheetTitle).toBe("Storyboard");
    expect(plan.values[0]).toEqual([
      "project_id",
      "scene_id",
      "shot_id",
      "shot_index",
      "status",
      "title",
      "storyboard_text",
      "visual_prompt",
      "duration_sec",
      "character_notes",
      "continuity_notes",
      "reference_links",
      "output_links",
      "last_sync_at",
      "yaml_path",
      "yaml_key",
      "last_comment_digest",
      "feedback_state",
    ]);
    expect(plan.values[1][2]).toBe("shot-1");
    expect(plan.hiddenColumnIndexes).toEqual(expect.arrayContaining([0, 14, 15, 16, 17]));
  });

  it("delegates replace + hide operations to the provided sheet client", async () => {
    const client = {
      ensureSheet: vi.fn(async () => ({ sheetId: "sheet-001" })),
      replaceValues: vi.fn(async () => undefined),
      hideColumns: vi.fn(async () => undefined),
    };

    const result = await syncStoryboardSheet(client, { rows: [row] });

    expect(client.ensureSheet).toHaveBeenCalledWith("Storyboard");
    expect(client.replaceValues).toHaveBeenCalledWith("sheet-001", expect.any(Array));
    expect(client.hideColumns).toHaveBeenCalledWith("sheet-001", expect.arrayContaining([0, 14, 15, 16, 17]));
    expect(result.sheetId).toBe("sheet-001");
    expect(result.rowCount).toBe(1);
  });
});
