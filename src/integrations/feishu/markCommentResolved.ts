import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export async function markCommentResolved(options: { fileToken: string; commentId: string; isSolved?: boolean; fileType?: "doc" | "docx" | "sheet" | "file" | "slides" }) {
  const params = JSON.stringify({
    file_token: options.fileToken,
    comment_id: options.commentId,
    file_type: options.fileType ?? "docx",
  });
  const data = JSON.stringify({
    is_solved: options.isSolved ?? true,
  });
  const { stdout } = await execFileAsync("lark-cli", ["drive", "file.comments", "patch", "--params", params, "--data", data], {
    maxBuffer: 1024 * 1024,
  });
  return JSON.parse(stdout);
}
