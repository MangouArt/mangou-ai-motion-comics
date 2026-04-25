import type { StoryboardSheetRow } from "../integrations/feishu/sheetSchema";
import type { NormalizedCommentThread } from "../integrations/feishu/normalizeCommentThread";
import {
  describeFeedbackField,
  requiresHumanReview,
  resolveFeedbackField,
  resolveFeedbackValue,
  type FeedbackPatchField,
  type FeedbackPatchRequest,
} from "./commentIntentParser";

export type SheetPatchField = FeedbackPatchField;
export type SheetPatchRequest = FeedbackPatchRequest;

export type ResolvedSheetComment = {
  status: "ready" | "ignored" | "needs-human-review";
  row?: StoryboardSheetRow;
  patchRequest?: SheetPatchRequest;
  replyPreview: string;
};

export function resolveSheetComment(input: { thread: NormalizedCommentThread; rows: StoryboardSheetRow[] }): ResolvedSheetComment {
  const row = resolveRow(input.thread, input.rows);
  if (!row) {
    return {
      status: "ignored",
      replyPreview: "已收到批注，但当前无法稳定定位到具体镜头字段，建议补充说明或重新在目标单元格上评论。",
    };
  }

  if (requiresHumanReview(input.thread.threadText)) {
    return {
      status: "needs-human-review",
      row,
      replyPreview: "我已识别到你的修改意图，但这条反馈会影响多个镜头/整体结构，已标记为需要人工确认，暂未自动改写 YAML。",
    };
  }

  const field = resolveFeedbackField(input.thread.threadText, input.thread.columnKey);
  const value = resolveFeedbackValue(field, input.thread.body);

  return {
    status: "ready",
    row,
    patchRequest: {
      yamlPath: row.yaml_path,
      field,
      value,
      commentDigest: input.thread.body,
    },
    replyPreview: `已根据你的批注更新该镜头的${describeFeedbackField(field)}，并同步到可选分镜表。`,
  };
}

function resolveRow(thread: NormalizedCommentThread, rows: StoryboardSheetRow[]): StoryboardSheetRow | undefined {
  if (thread.rowNumber != null) {
    const index = thread.rowNumber - 2;
    if (index >= 0 && index < rows.length) return rows[index];
  }
  return rows.find((row) => row.shot_id && thread.quote.includes(row.shot_id));
}
