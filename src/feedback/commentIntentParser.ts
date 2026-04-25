export type FeedbackPatchField = "storyboard_text" | "visual_prompt" | "duration_sec" | "continuity_notes" | "reference_links";

export type FeedbackPatchRequest = {
  yamlPath: string;
  field: FeedbackPatchField;
  value: string | number;
  commentDigest?: string;
};

export function requiresHumanReview(text: string): boolean {
  return /(多个镜头|前后两个镜头|重排|插入|新增.*镜头|整体结构|删除.*镜头)/.test(text);
}

export function resolveFeedbackField(text: string, explicitField?: string | null): FeedbackPatchField {
  if (explicitField === "visual_prompt") return "visual_prompt";
  if (explicitField === "duration_sec") return "duration_sec";
  if (explicitField === "continuity_notes") return "continuity_notes";
  if (explicitField === "reference_links") return "reference_links";
  if (/时长|秒|duration/i.test(text)) return "duration_sec";
  if (/承接|连续|continuity/i.test(text)) return "continuity_notes";
  if (/参考图|reference|素材/i.test(text)) return "reference_links";
  if (/prompt|视觉|画面风格|质感|镜头语言/i.test(text)) return "visual_prompt";
  return "storyboard_text";
}

export function resolveFeedbackValue(field: FeedbackPatchField, body: string): string | number {
  if (field === "duration_sec") {
    const match = body.match(/(\d+(?:\.\d+)?)/);
    return match ? Number(match[1]) : 4;
  }
  return body.trim();
}

export function describeFeedbackField(field: FeedbackPatchField): string {
  switch (field) {
    case "visual_prompt":
      return "视觉 prompt";
    case "duration_sec":
      return "时长";
    case "continuity_notes":
      return "承接说明";
    case "reference_links":
      return "参考链接";
    default:
      return "分镜描述";
  }
}
