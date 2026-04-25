import { afterEach, beforeEach, describe, expect, it } from "vitest";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { parseYAML } from "../../src/core/yaml";
import { applyFeedbackToYaml } from "../../src/storyboard/applyFeedbackToYaml";

describe("applyFeedbackToYaml", () => {
  let tempRoot = "";
  let projectRoot = "";

  beforeEach(async () => {
    tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), "mangou-feishu-yaml-"));
    projectRoot = path.join(tempRoot, "demo-project");
    await fs.mkdir(path.join(projectRoot, "storyboards"), { recursive: true });
    await fs.writeFile(
      path.join(projectRoot, "storyboards", "shot-1.yaml"),
      [
        "meta:",
        "  id: shot-1",
        "  version: '1.0'",
        "content:",
        "  sequence: 1",
        "  title: Opening",
        "  story: 原始描述",
        "  action: 推进",
        "  scene: 地下城",
        "  duration: 4s",
        "  characters:",
        "    - 杜休",
        "tasks:",
        "  image:",
        "    params:",
        "      prompt: 原始 prompt",
        "refs: {}",
        "",
      ].join("\n"),
      "utf-8",
    );
  });

  afterEach(async () => {
    if (tempRoot) {
      await fs.rm(tempRoot, { recursive: true, force: true });
    }
  });

  it("updates prompt and feedback metadata while keeping yaml valid", async () => {
    const result = await applyFeedbackToYaml({
      projectRoot,
      patchRequest: {
        yamlPath: "storyboards/shot-1.yaml",
        field: "visual_prompt",
        value: "真实工业科幻，live-action，地球发动机喷口朝天",
        commentDigest: "地球发动机再大一点，喷口朝天",
      },
    });

    const updated = parseYAML(
      await fs.readFile(path.join(projectRoot, "storyboards/shot-1.yaml"), "utf-8"),
    );

    expect(result.updatedField).toBe("visual_prompt");
    expect(updated.tasks.image.params.prompt).toBe("真实工业科幻，live-action，地球发动机喷口朝天");
    expect(updated.meta.feedback_state).toBe("resolved");
    expect(updated.meta.last_comment_digest).toBe("地球发动机再大一点，喷口朝天");
  });

  it("normalizes duration updates back into storyboard yaml duration strings", async () => {
    await applyFeedbackToYaml({
      projectRoot,
      patchRequest: {
        yamlPath: "storyboards/shot-1.yaml",
        field: "duration_sec",
        value: 6,
      },
    });

    const updated = parseYAML(
      await fs.readFile(path.join(projectRoot, "storyboards/shot-1.yaml"), "utf-8"),
    );

    expect(updated.content.duration).toBe("6s");
  });
});
