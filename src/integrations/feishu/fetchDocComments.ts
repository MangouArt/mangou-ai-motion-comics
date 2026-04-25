import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export type FeishuFileType = "doc" | "docx" | "sheet" | "file" | "slides";

export async function fetchFileComments(options: { fileToken: string; fileType: FeishuFileType; includeSolved?: boolean; pageSize?: number }) {
  const params = JSON.stringify({
    file_token: options.fileToken,
    file_type: options.fileType,
    is_solved: options.includeSolved ?? false,
    page_size: options.pageSize ?? 100,
  });
  const { stdout } = await execFileAsync("lark-cli", ["drive", "file.comments", "list", "--params", params], {
    maxBuffer: 1024 * 1024,
  });
  return JSON.parse(stdout);
}

export async function fetchDocComments(options: { fileToken: string; includeSolved?: boolean; pageSize?: number }) {
  return fetchFileComments({ ...options, fileType: "docx" });
}
