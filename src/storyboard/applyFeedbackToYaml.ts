import fs from "node:fs/promises";
import path from "node:path";
import { parseYAML, stringifyYAML } from "@core/yaml";
import type { FeedbackPatchRequest } from "../feedback/commentIntentParser";

type ApplyFeedbackOptions = {
  projectRoot: string;
  patchRequest: FeedbackPatchRequest;
};

export async function applyFeedbackToYaml({ projectRoot, patchRequest }: ApplyFeedbackOptions) {
  const absolutePath = path.join(projectRoot, patchRequest.yamlPath);
  const raw = await fs.readFile(absolutePath, "utf-8");
  const doc = parseYAML(raw) as Record<string, any>;

  doc.meta = doc.meta ?? {};
  doc.content = doc.content ?? {};
  doc.tasks = doc.tasks ?? {};
  doc.refs = doc.refs ?? {};

  switch (patchRequest.field) {
    case "storyboard_text":
      doc.content.story = String(patchRequest.value);
      break;
    case "visual_prompt":
      doc.tasks.image = doc.tasks.image ?? {};
      doc.tasks.image.params = doc.tasks.image.params ?? {};
      doc.tasks.image.params.prompt = String(patchRequest.value);
      break;
    case "duration_sec":
      doc.content.duration = `${patchRequest.value}s`;
      break;
    case "continuity_notes":
      doc.refs.continuity_notes = String(patchRequest.value);
      break;
    case "reference_links":
      doc.refs.reference_links = String(patchRequest.value)
        .split(/\n+/)
        .map((item) => item.trim())
        .filter(Boolean);
      break;
    default:
      throw new Error(`Unsupported patch field: ${(patchRequest as any).field}`);
  }

  doc.meta.feedback_state = "resolved";
  if (patchRequest.commentDigest) {
    doc.meta.last_comment_digest = patchRequest.commentDigest;
  }

  if (!doc.meta?.id || !doc.content) {
    throw new Error(`Updated YAML is missing required base fields: ${patchRequest.yamlPath}`);
  }

  await fs.writeFile(absolutePath, stringifyYAML(doc), "utf-8");
  return {
    yamlPath: patchRequest.yamlPath,
    updatedField: patchRequest.field,
  };
}
