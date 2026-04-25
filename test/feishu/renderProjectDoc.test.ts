import { describe, expect, it } from "vitest";
import { renderProjectDoc } from "../../src/integrations/feishu/renderProjectDoc";
import type { ProjectDoc } from "../../src/integrations/feishu/projectDocSchema";

describe("renderProjectDoc", () => {
  it("renders a user-facing Feishu Doc projection without YAML paths or Sheet links", () => {
    const doc: ProjectDoc = {
      projectId: "wandering-earth-ending",
      title: "wandering-earth-ending",
      status: "reviewing",
      round: "R1",
      scriptSummary: "地球发动机关闭，群星显现。",
      globalVisualRules: ["live-action 工业科幻", "地球发动机喷口朝天"],
      shots: [
        {
          projectId: "wandering-earth-ending",
          shotId: "grid-seq2",
          index: 2,
          title: "发动机熄灭",
          status: "reviewing",
          durationSec: 5,
          storyboardText: "极地深夜，行星发动机火柱正式熄灭。",
          visualPrompt: "真实工业尺度，非漫画风。",
          yamlPath: "storyboards/grid-seq2.yaml",
          media: [{ type: "video", label: "当前视频", feishuUrl: "https://my.feishu.cn/file/demo", status: "completed" }],
        },
      ],
    };

    const markdown = renderProjectDoc(doc);

    expect(markdown).toContain("# 项目：wandering-earth-ending");
    expect(markdown).toContain("### 镜头 grid-seq2：发动机熄灭");
    expect(markdown).toContain("当前视频（completed）：https://my.feishu.cn/file/demo");
    expect(markdown).not.toContain("storyboards/grid-seq2.yaml");
    expect(markdown).not.toContain("Sheet");
  });
});
