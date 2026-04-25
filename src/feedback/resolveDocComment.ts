import type { NormalizedCommentThread } from "../integrations/feishu/normalizeCommentThread";
import type { ProjectDocShot } from "../integrations/feishu/projectDocSchema";
import {
  describeFeedbackField,
  requiresHumanReview,
  resolveFeedbackField,
  resolveFeedbackValue,
  type FeedbackPatchRequest,
} from "./commentIntentParser";

export type ResolvedDocComment = {
  status: "ready" | "ignored" | "needs-human-review";
  shot?: ProjectDocShot;
  patchRequest?: FeedbackPatchRequest;
  replyPreview: string;
};

export function resolveDocComment(input: { thread: NormalizedCommentThread; shots: ProjectDocShot[] }): ResolvedDocComment {
  const shot = resolveShot(input.thread, input.shots);
  if (!shot) {
    return {
      status: "ignored",
      replyPreview: "已收到批注，但当前无法稳定定位到具体镜头字段，建议补充说明或重新在目标镜头段落上评论。",
    };
  }

  if (requiresHumanReview(input.thread.threadText)) {
    return {
      status: "needs-human-review",
      shot,
      replyPreview: "我已识别到你的修改意图，但这条反馈会影响多个镜头/整体结构，已标记为需要人工确认，暂未自动改写 YAML。",
    };
  }

  if (!shot.yamlPath) {
    return {
      status: "needs-human-review",
      shot,
      replyPreview: "已定位到镜头，但当前缺少内部工程映射，已标记为需要人工确认，暂未自动改写 YAML。",
    };
  }

  const explicitField = resolveDocFieldFromQuote(input.thread.quote || input.thread.blockId || "");
  const field = resolveFeedbackField(input.thread.threadText, explicitField);
  const value = resolveFeedbackValue(field, input.thread.body);

  return {
    status: "ready",
    shot,
    patchRequest: {
      yamlPath: shot.yamlPath,
      field,
      value,
      commentDigest: input.thread.body,
    },
    replyPreview: `已根据你的批注更新该镜头的${describeFeedbackField(field)}，并同步到项目文档。`,
  };
}

function resolveShot(thread: NormalizedCommentThread, shots: ProjectDocShot[]): ProjectDocShot | undefined {
  const context = [thread.quote, thread.blockId, thread.body, thread.threadText].filter(Boolean).join("\n");
  return shots.find((shot) => {
    const escaped = shot.shotId.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    return new RegExp(`(?:镜头\\s*)?${escaped}(?:\\b|：|:|\n|$)`).test(context);
  });
}

function resolveDocFieldFromQuote(quote: string): string | null {
  if (/视觉方向|视觉|prompt/i.test(quote)) return "visual_prompt";
  if (/时长|duration/i.test(quote)) return "duration_sec";
  if (/连续性|承接/i.test(quote)) return "continuity_notes";
  if (/参考素材|参考图|素材/i.test(quote)) return "reference_links";
  if (/画面目标|分镜|描述/i.test(quote)) return "storyboard_text";
  return null;
}
