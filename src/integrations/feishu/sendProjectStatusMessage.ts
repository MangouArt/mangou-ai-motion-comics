import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export async function sendProjectStatusMessage(options: { receiveId: string; text: string }) {
  const params = JSON.stringify({ receive_id_type: "open_id" });
  const data = JSON.stringify({
    receive_id: options.receiveId,
    msg_type: "text",
    content: JSON.stringify({ text: options.text }),
  });
  const { stdout } = await execFileAsync("lark-cli", ["im", "v1", "messages", "create", "--params", params, "--data", data], {
    maxBuffer: 1024 * 1024,
  });
  return JSON.parse(stdout);
}
