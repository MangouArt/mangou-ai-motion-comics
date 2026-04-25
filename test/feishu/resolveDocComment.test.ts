import { describe, expect, it } from "vitest";
import { normalizeCommentThread } from "../../src/integrations/feishu/normalizeCommentThread";
import { resolveDocComment } from "../../src/feedback/resolveDocComment";
import type { ProjectDocShot } from "../../src/integrations/feishu/projectDocSchema";

const shots: ProjectDocShot[] = [
  {
    projectId: "demo",
    shotId: "grid-seq2",
    index: 2,
    title: "发动机熄灭",
    status: "reviewing",
    durationSec: 5,
    storyboardText: "极地深夜，行星发动机火柱正式熄灭。",
    yamlPath: "storyboards/grid-seq2.yaml",
  },
];

describe("resolveDocComment", () => {
  it("maps a doc section comment to a single-shot yaml patch request", () => {
    const thread = normalizeCommentThread({
      fileToken: "doc-token",
      comment: {
        comment_id: "comment-1",
        content: "地球发动机再大一点，喷口朝天，工业尺度更夸张。",
        quote: "### 镜头 grid-seq2：发动机熄灭\n视觉方向：真实工业科幻",
      },
      replies: [],
    });

    const resolved = resolveDocComment({ thread, shots });

    expect(resolved.status).toBe("ready");
    expect(resolved.shot?.shotId).toBe("grid-seq2");
    expect(resolved.patchRequest).toMatchObject({
      yamlPath: "storyboards/grid-seq2.yaml",
      field: "visual_prompt",
      value: "地球发动机再大一点，喷口朝天，工业尺度更夸张。",
    });
    expect(resolved.replyPreview).toContain("项目文档");
  });

  it("requires human review for multi-shot doc feedback", () => {
    const thread = normalizeCommentThread({
      fileToken: "doc-token",
      comment: {
        comment_id: "comment-2",
        content: "把前后两个镜头都重排一下，并新增一个过渡镜头。",
        quote: "### 镜头 grid-seq2：发动机熄灭",
      },
      replies: [],
    });

    const resolved = resolveDocComment({ thread, shots });

    expect(resolved.status).toBe("needs-human-review");
    expect(resolved.patchRequest).toBeUndefined();
  });
});
