export const STORYBOARD_SHEET_TITLE = "Storyboard";

export const STORYBOARD_SHEET_COLUMNS = [
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
] as const;

export type StoryboardSheetColumn = (typeof STORYBOARD_SHEET_COLUMNS)[number];

export type StoryboardSheetRow = {
  project_id: string;
  scene_id: string;
  shot_id: string;
  shot_index: number;
  status: string;
  title: string;
  storyboard_text: string;
  visual_prompt: string;
  duration_sec: number | null;
  character_notes: string;
  continuity_notes: string;
  reference_links: string;
  output_links: string;
  last_sync_at: string;
  yaml_path: string;
  yaml_key: string;
  last_comment_digest: string;
  feedback_state: string;
};

export const HIDDEN_STORYBOARD_SHEET_COLUMNS: StoryboardSheetColumn[] = [
  "project_id",
  "yaml_path",
  "yaml_key",
  "last_comment_digest",
  "feedback_state",
];

export function serializeStoryboardSheetRow(row: StoryboardSheetRow): (string | number | null)[] {
  return STORYBOARD_SHEET_COLUMNS.map((column) => row[column] ?? null);
}

export function hiddenColumnIndexes(): number[] {
  return HIDDEN_STORYBOARD_SHEET_COLUMNS.map((column) => STORYBOARD_SHEET_COLUMNS.indexOf(column)).filter(
    (index) => index >= 0,
  );
}
