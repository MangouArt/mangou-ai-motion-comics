import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export async function replyToComment(options: { fileToken: string; commentId: string; text: string; fileType?: "doc" | "docx" | "sheet" | "file" | "slides" }) {
  const params = JSON.stringify({
    file_token: options.fileToken,
    comment_id: options.commentId,
    file_type: options.fileType ?? "docx",
  });
  const data = JSON.stringify({
    content: {
      elements: [
        {
          type: "text_run",
          text_run: { text: options.text },
        },
      ],
    },
  });
  const { stdout } = await execFileAsync("lark-cli", [
    "drive",
    "file.comment.replys",
    "create",
    "--params",
    params,
    "--data",
    data,
  ], { maxBuffer: 1024 * 1024 });
  return JSON.parse(stdout);
}
