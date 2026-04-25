export type ProjectDocStatus = "draft" | "reviewing" | "approved" | "rendering" | "done" | "blocked";

export type ProjectDocMedia = {
  type: "image" | "video";
  label: string;
  path?: string;
  feishuToken?: string;
  feishuUrl?: string;
  status?: string;
};

export type ProjectDocShot = {
  projectId: string;
  shotId: string;
  sceneId?: string;
  index: number;
  title: string;
  status: ProjectDocStatus;
  durationSec?: number;
  storyboardText: string;
  visualPrompt?: string;
  characterNotes?: string;
  continuityNotes?: string;
  referenceLinks?: string[];
  outputLinks?: string[];
  media?: ProjectDocMedia[];
  /** Internal mapping back to YAML. Do not render into user-facing Doc body. */
  yamlPath?: string;
  /** Internal mapping back to YAML. Do not render into user-facing Doc body. */
  yamlKey?: string;
};

export type ProjectDoc = {
  projectId: string;
  title: string;
  status: ProjectDocStatus;
  round?: string;
  scriptSummary?: string;
  globalVisualRules: string[];
  usageHint?: string;
  shots: ProjectDocShot[];
  changelog?: string[];
};
