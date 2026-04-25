import { describe, expect, it } from "vitest";
import { normalizeCommentThread } from "../../src/integrations/feishu/normalizeCommentThread";
import { resolveSheetComment } from "../../src/feedback/resolveSheetComment";
import type { StoryboardSheetRow } from "../../src/integrations/feishu/sheetSchema";

const rows: StoryboardSheetRow[] = [
  {
    project_id: "demo",
    scene_id: "scene-1",
    shot_id: "shot-1",
    shot_index: 1,
    status: "draft",
    title: "Opening",
    storyboard_text: "原始描述",
    visual_prompt: "原始 prompt",
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
  },
];

describe("resolveSheetComment", () => {
  it("maps a sheet comment to a single-shot yaml patch request", () => {
    const thread = normalizeCommentThread({
      fileToken: "sheet-token",
      comment: {
        comment_id: "comment-1",
        content: "地球发动机再大一点，喷口朝天，工业尺度更夸张。",
        create_time: "2026-04-20T12:00:00.000Z",
        anchor: {
          row: 2,
          column_key: "storyboard_text",
        },
      },
      replies: [],
    });

    const resolved = resolveSheetComment({ thread, rows });

    expect(resolved.status).toBe("ready");
    expect(resolved.row?.shot_id).toBe("shot-1");
    expect(resolved.patchRequest).toMatchObject({
      yamlPath: "storyboards/shot-1.yaml",
      field: "storyboard_text",
      value: "地球发动机再大一点，喷口朝天，工业尺度更夸张。",
    });
    expect(resolved.replyPreview).toContain("已根据你的批注更新");
  });

  it("marks multi-shot comments as needs-human-review", () => {
    const thread = normalizeCommentThread({
      fileToken: "sheet-token",
      comment: {
        comment_id: "comment-2",
        content: "把前后两个镜头都重排一下，并新增一个过渡镜头。",
        create_time: "2026-04-20T12:00:00.000Z",
        anchor: {
          row: 2,
          column_key: "storyboard_text",
        },
      },
      replies: [],
    });

    const resolved = resolveSheetComment({ thread, rows });

    expect(resolved.status).toBe("needs-human-review");
    expect(resolved.patchRequest).toBeUndefined();
    expect(resolved.replyPreview).toContain("需要人工确认");
  });
});
