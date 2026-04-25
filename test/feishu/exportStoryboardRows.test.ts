import { afterEach, beforeEach, describe, expect, it } from "vitest";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import yaml from "js-yaml";
import { exportStoryboardRows } from "../../src/integrations/feishu/exportStoryboardRows";

describe("exportStoryboardRows", () => {
  let tempRoot = "";
  let projectRoot = "";

  beforeEach(async () => {
    tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), "mangou-feishu-export-"));
    projectRoot = path.join(tempRoot, "feishu-demo");
    await fs.mkdir(path.join(projectRoot, "storyboards"), { recursive: true });
    await fs.writeFile(
      path.join(projectRoot, "project.json"),
      JSON.stringify({ id: "feishu-demo", name: "Feishu Demo" }, null, 2),
      "utf-8",
    );

    await fs.writeFile(
      path.join(projectRoot, "storyboards", "shot-b.yaml"),
      yaml.dump({
        meta: { id: "shot-b", scene_id: "scene-2" },
        content: {
          sequence: 2,
          title: "Second Shot",
          story: "后续镜头",
          action: "推进",
          scene: "控制室",
          duration: "6s",
          characters: ["杜休"],
        },
        tasks: {
          image: {
            params: { prompt: "industrial sci-fi, live-action" },
            latest: { status: "completed", output: "assets/images/shot-b.png" },
          },
          video: {
            latest: { status: "completed", output: "assets/videos/shot-b.mp4" },
          },
        },
        refs: {
          continuity_notes: "承接上一个镜头的爆炸余波",
          reference_links: ["https://example.com/ref-1.png", "https://example.com/ref-2.png"],
        },
      }),
      "utf-8",
    );

    await fs.writeFile(
      path.join(projectRoot, "storyboards", "shot-a.yaml"),
      yaml.dump({
        meta: { id: "shot-a", scene_id: "scene-1" },
        content: {
          sequence: 1,
          title: "First Shot",
          story: "开场镜头",
          action: "俯冲",
          scene: "冰原",
          duration: "4s",
          characters: [],
        },
      }),
      "utf-8",
    );
  });

  afterEach(async () => {
    if (tempRoot) {
      await fs.rm(tempRoot, { recursive: true, force: true });
    }
  });

  it("projects storyboard yaml files into sheet rows with stable mapping fields", async () => {
    const rows = await exportStoryboardRows({
      projectRoot,
      now: "2026-04-20T12:00:00.000Z",
    });

    expect(rows).toHaveLength(2);
    expect(rows.map((row) => row.shot_id)).toEqual(["shot-a", "shot-b"]);

    expect(rows[1]).toMatchObject({
      project_id: "feishu-demo",
      scene_id: "scene-2",
      shot_id: "shot-b",
      shot_index: 2,
      status: "done",
      title: "Second Shot",
      storyboard_text: "后续镜头",
      visual_prompt: "industrial sci-fi, live-action",
      duration_sec: 6,
      character_notes: "杜休",
      continuity_notes: "承接上一个镜头的爆炸余波",
      yaml_path: "storyboards/shot-b.yaml",
      yaml_key: "meta.id=shot-b",
      last_sync_at: "2026-04-20T12:00:00.000Z",
      feedback_state: "unprocessed",
    });

    expect(rows[1].reference_links).toContain("https://example.com/ref-1.png");
    expect(rows[1].output_links).toContain("assets/images/shot-b.png");
    expect(rows[1].output_links).toContain("assets/videos/shot-b.mp4");
  });
});
