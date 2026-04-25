import type { ProjectDoc, ProjectDocMedia, ProjectDocShot } from "./projectDocSchema";

function escapeInline(value: string): string {
  return value.replace(/\r\n/g, "\n").trim();
}

function renderList(items: string[]): string {
  return items.length ? items.map((item) => `- ${escapeInline(item)}`).join("\n") : "- （待补充）";
}

function renderLinks(label: string, links?: string[]): string {
  if (!links?.length) return "";
  return `\n${label}：\n${renderList(links)}`;
}

function renderMedia(media?: ProjectDocMedia[]): string {
  if (!media?.length) return "";
  return media
    .map((item) => {
      const status = item.status ? `（${item.status}）` : "";
      const target = item.feishuUrl || item.path || item.feishuToken || "待同步";
      return `${item.type === "image" ? "当前图片" : "当前视频"}${status}：${target}`;
    })
    .join("\n");
}

export function renderProjectDoc(project: ProjectDoc): string {
  const usageHint =
    project.usageHint || "请直接在对应镜头文字、图片或视频附近评论。Agent 会根据评论更新工程状态与生成结果。";

  const sections = [
    `# 项目：${project.title}`,
    `项目状态：${project.status}`,
    project.round ? `当前轮次：${project.round}` : "",
    "",
    "## 交互说明",
    usageHint,
    "",
    "## 全局视觉规则",
    renderList(project.globalVisualRules),
    "",
    "## 剧本摘要",
    project.scriptSummary?.trim() || "（待补充）",
    "",
    "## 分镜列表",
    ...project.shots.flatMap(renderShotSection),
  ].filter((line) => line !== undefined);

  if (project.changelog?.length) {
    sections.push("", "## 最近变更", renderList(project.changelog));
  }

  return sections.join("\n").replace(/\n{3,}/g, "\n\n").trimEnd() + "\n";
}

function renderShotSection(shot: ProjectDocShot): string[] {
  const lines = [
    "",
    `### 镜头 ${shot.shotId}：${shot.title}`,
    "",
    `状态：${shot.status}`,
    shot.durationSec != null ? `时长：${shot.durationSec}s` : "",
    "",
    "画面目标：",
    escapeInline(shot.storyboardText) || "（待补充）",
  ];

  if (shot.visualPrompt) {
    lines.push("", "视觉方向：", escapeInline(shot.visualPrompt));
  }
  if (shot.characterNotes) {
    lines.push("", "角色说明：", escapeInline(shot.characterNotes));
  }
  if (shot.continuityNotes) {
    lines.push("", "连续性：", escapeInline(shot.continuityNotes));
  }

  const referenceBlock = renderLinks("参考素材", shot.referenceLinks);
  if (referenceBlock) lines.push(referenceBlock);
  const outputBlock = renderLinks("输出链接", shot.outputLinks);
  if (outputBlock) lines.push(outputBlock);

  const mediaBlock = renderMedia(shot.media);
  if (mediaBlock) lines.push("", mediaBlock);

  return lines.filter(Boolean);
}
