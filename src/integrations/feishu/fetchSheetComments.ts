import { fetchFileComments } from "./fetchDocComments";

/** Optional Sheet projection helper. Feishu Doc is the default user interaction surface. */
export async function fetchSheetComments(options: { fileToken: string; includeSolved?: boolean; pageSize?: number }) {
  return fetchFileComments({ ...options, fileType: "sheet" });
}
