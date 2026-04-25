import { HIDDEN_STORYBOARD_SHEET_COLUMNS, STORYBOARD_SHEET_COLUMNS, STORYBOARD_SHEET_TITLE, hiddenColumnIndexes, serializeStoryboardSheetRow, type StoryboardSheetRow } from "./sheetSchema";

export type StoryboardSheetClient = {
  ensureSheet: (title: string) => Promise<{ sheetId: string }>;
  replaceValues: (sheetId: string, values: (string | number | null)[][]) => Promise<void>;
  hideColumns: (sheetId: string, columnIndexes: number[]) => Promise<void>;
};

export type StoryboardSheetSyncPlan = {
  sheetTitle: string;
  hiddenColumns: readonly string[];
  hiddenColumnIndexes: number[];
  values: (string | number | null)[][];
};

export function buildStoryboardSheetSyncPlan(rows: StoryboardSheetRow[]): StoryboardSheetSyncPlan {
  return {
    sheetTitle: STORYBOARD_SHEET_TITLE,
    hiddenColumns: HIDDEN_STORYBOARD_SHEET_COLUMNS,
    hiddenColumnIndexes: hiddenColumnIndexes(),
    values: [STORYBOARD_SHEET_COLUMNS as unknown as string[], ...rows.map(serializeStoryboardSheetRow)],
  };
}

export async function syncStoryboardSheet(client: StoryboardSheetClient, options: { rows: StoryboardSheetRow[] }) {
  const plan = buildStoryboardSheetSyncPlan(options.rows);
  const { sheetId } = await client.ensureSheet(plan.sheetTitle);
  await client.replaceValues(sheetId, plan.values);
  await client.hideColumns(sheetId, plan.hiddenColumnIndexes);
  return {
    sheetId,
    rowCount: options.rows.length,
    hiddenColumnCount: plan.hiddenColumnIndexes.length,
  };
}
