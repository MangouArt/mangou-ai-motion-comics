# AI 漫剧创作通用优先级与历史复盘方法

## 何时阅读

- 用户要求整理 Mangou / AI 漫剧创作的通用规则、优先级、验收表或 workflow。
- 用户指出 agent 只修最近一个批注、忘记前面教训，要求“完整 review 历史对话”。
- 需要把项目失败复盘抽象为跨项目规则，而不是写成某个项目的专属设定。
- 生成或审查分镜/视频前，需要按层级避免 prompt 约束平铺。

## 核心原则

不要把所有约束平铺进同一个 prompt。AI 漫剧失败通常不是“prompt 不够长”，而是约束没有层级：修了道具忘了故事，修了单图忘了跨 clip，修了局部细节忘了角色/场景资产漂移。

通用顺序：**用户意图与禁区 → 故事闭环 → 世界自洽 → 资产锁定 → 跨镜头连续 → 模型可执行尺度 → 动作节奏 → 画面细节 → 视频字段语义 → 工程回填 → 复盘沉淀**。

低层级做得再好，只要高层级失败，都不能通过。

## 先做完整历史复盘

当用户要求“通用优先级”或“完整 review 之前历史对话”时，不要只总结当前项目：

1. 用 session/history 搜索回顾近期相关会话，至少覆盖：
   - 故事重构：内容是否从素材拼贴变成目标—阻碍—推进—结果。
   - 世界规则：角色身份、物理交互、制度逻辑是否被模型改写。
   - 资产漂移：角色、场景、核心道具是否跨图/跨 clip 保持。
   - 分镜尺度：九宫格、clip、first/last frame 是否被误用。
   - 视频输入：reference / first / last 字段语义是否混淆。
   - 工程回填：YAML、tasks.jsonl、飞书文档是否一致。
   - 用户纠错：哪些错误是 agent 只修最近批注、忘记前面教训导致的。
2. 把每条教训归类到通用工作流层级，不要保留过多项目私有名词。
3. 用 DuckDuckGo / web 搜索验证外部资料：影视前期制作、AI storyboard、keyframes、reference image / character consistency、video prompting best practices。
4. 输出为“草案供审阅”。用户未确认前，不要把规则类内容直接升级为 truth-source 强规则。
5. 若用户确认，再拆成通用 reference 与 checklist 模板，并把项目私有内容留在项目文档。

## 联网验证口径

外部资料通常支持这些结论：

- 影视前期制作强调先锁剧本、故事板、角色、场景和制作计划，以减少返工。
- AI storyboard / video workflow 强调 reference images、character consistency、keyframes / start-end control。
- Luma 的 keyframe / extend 资料强调用关键帧让视频平滑过渡到目标视觉状态，并用 character / visual reference 保持一致。
- Runway Gen-3 资料强调 fidelity、consistency、motion；示例 prompt 以具体主体、动作、机位、摄影运动为核心。
- AI 视频一致性经验资料普遍强调：简单、显著、稳定的视觉锚点比复杂细节更利于跨镜头一致；一次不要同时改太多变量，否则无法定位是哪一项破坏一致性。

可用搜索方向：

```text
AI video generation reference images character consistency storyboard keyframes best practices
AI storyboard character reference consistency generated frames
filmmaking pre-production storyboard planning checklist
Luma keyframes visual reference character reference best practices
Runway Gen-3 consistency motion prompt
```

可引用链接：

- Luma Keyframes: https://lumalabs.ai/learning-hub/how-to-use-keyframes
- Luma Best Practices: https://lumalabs.ai/learning-hub/best-practices
- Runway Gen-3 Alpha: https://runwayml.com/research/introducing-gen-3-alpha
- StudioBinder Pre-production: https://www.studiobinder.com/blog/what-is-pre-production-definition/
- Boords Pre-production Guide: https://boords.com/blog/pre-production-guide

## 通用约束优先级 P0-P10

### P0 用户意图与禁区

用户明确目标、预算、禁区、风格偏好优先于一切。不要默认从图片进入视频，不要做用户未授权的昂贵生成或副作用动作。

验收问题：

- 用户到底要草案、分镜图、视频、流程测试，还是正式成片？
- 用户有没有说“不要生成视频 / 太贵 / 先只做图”？
- 用户要求的是 live-action、漫画、工业科幻、知识漫画、vlog、恐怖、广告，还是其他风格？
- 哪些内容是强禁区，例如宠物化、解说片化、漫画风、个人信息泄露？

一票否决：擅自进入更贵阶段；忽略用户禁区；用通用回答覆盖当前上下文。

### P1 故事闭环

先确认主角、目标、阻碍、推进、结果。视频/漫剧不能只是素材拼贴；如果内容“散”，优先重构故事链，而不是堆 prompt 细节。

验收问题：

- 主角是谁，目标是什么？
- 阻碍是什么，为什么要进入下一镜？
- 本段结束时发生了什么变化？
- 观众能否用一句话复述这一段？

一票否决：多场景堆叠但没有因果；每段都是生活片段没有推进；技术好看但故事目标不成立。

### P2 世界规则与身份逻辑

角色身份、物理交互、制度逻辑必须自洽。身份表达优先靠行为、环境、道具，不要用破坏身份的装备或捷径。

验收问题：

- 主角身份是否始终一致？
- 道具使用是否符合角色能力和物理逻辑？
- 环境制度是否支持剧情？
- 模型是否把角色误归类成另一个身份？

一票否决：角色身份被模型改写；关键行为物理不成立；道具方案破坏世界观。

### P3 资产锁定

跨镜头出现两次以上的大件先资产化：角色、场景、核心道具、风格。传参考图不等于锁定成功，必须视觉核对输出是否真正继承参考图。

资产优先级：

1. 主角/角色资产：外形、服装/身体特征、比例、身份锚点。
2. 主要场景资产：房间、走廊、街道、教室、驾驶舱、城市、基地等。
3. 核心道具资产：剧情关键物，例如卡、书、武器、信件、设备、载具。
4. 风格资产：画风、质感、色彩、摄影语法。

一票否决：主角换脸/换体型/换物种；同一场景大件在相邻 clip 里变成另一处空间；同一核心道具变形到无法识别。

### P4 跨镜头 / 跨 clip 连续性

上一镜尾帧必须能接当前镜首帧：角色位置、朝向、道具关系、空间方向、时间光线都要延续。单图通过不等于跨 clip 通过。

通用规则：

- `sequence > 1` 的镜头，prompt 开头必须声明“上一镜承接状态”。
- `c01` 先复现上一镜最后状态，再开始新动作。
- 如果动作方式要改变，必须在镜头内交代过渡。

一票否决：上一镜刚出门，下一镜无解释回到原地；同一房间结构在相邻镜头完全变化；核心道具突然换形态。

### P5 模型可执行尺度

一张九宫格只覆盖一个短 clip 的连续关键帧，不做整段剧情概览。一个视频 prompt 不要跨多个空间大跳转；视频模型需要 start / transition / end，而不是大纲。

通用规则：

- 相邻格只允许小位移、小姿态变化、小机位变化。
- 不要把多个空间和多个剧情阶段塞进同一张图。
- 单个正式分镜默认按 15s 镜头组织；探索阶段可用 8-10s 候选，但必须标清口径。

一票否决：一张九宫格里每格都换场景；一个视频 prompt 让模型跨多个空间；没有首尾状态，只有抽象剧情描述。

### P6 动作密度与节奏

动作应服务故事目标，而不是服务道具展示。8-10 秒行动段至少 2 个动作 beat + 1 个结尾钩子；12-15 秒核心冲突段至少 3 个动作 beat + 1 个反应/结果变化。同一机械动作持续约 4 秒无新信息即节奏失败。

常见处理：

- 删除重复动作，换成更直接的动作方案。
- 在动作中加入突然加速、转身、打滑恢复、道具调整、反应、障碍、方向选择、背景速度变化等微事件。
- 如果道具让主线变慢，降级道具或改成静态身份锚点。

一票否决：一段视频只有一个重复动作；动作与剧情目标相反；镜头没有新信息，只是重复移动。

### P7 画面质量与局部细节

在 P0-P6 通过后，再优化构图、清晰度、小道具、文字、质感。局部细节不能压过故事、身份、资产连续性。

通用规则：

- 主体要足够大，便于 review 和视频参考。
- 关键道具要能读出类型，但不一定要求可读文字。
- 不要出现不必要文字、字幕、水印、UI、伪文字。
- 构图、景别、光线、色彩应服务剧情信息优先级。

一票否决：明显字幕/水印/九宫格残留/分屏残留；主体小到无法判断一致性；关键道具完全不可辨导致剧情无法成立。

### P8 视频输入语义与 provider 约束

明确区分 `reference_images/reference_image_urls`、`first_frame`、`last_frame`。九宫格一般不能当 `first_frame`；视频 prompt 必须声明单一全画幅，禁止 grid / split-screen / contact sheet。

通用规则：

- `reference_images/reference_image_urls`：角色、场景、道具、风格等参考。
- `first_frame`：当前视频必须开始于该图。
- `last_frame`：当前视频需要结束于该图。
- 不要把所有图都塞进通用 `images` 让 runtime/provider 猜。
- 九宫格只作为隐藏叙事节奏参考，不得作为正式首帧/尾帧，除非用户明确要“九宫格整体动起来”。

一票否决：媒体字段语义错；提交 payload 与 YAML 不一致；视频输出继承了参考图的错误结构。

### P9 工程真相源与回填验证

项目真相源是 `project.json`、`asset_defs/*.yaml`、`storyboards/*.yaml`、`tasks.jsonl`；飞书文档是 review hub。生成后核对 provider、model、payload、remote output、本地 output、YAML latest。

通用规则：

- `tasks.jsonl` 是任务真相源，YAML `latest` 是投影缓存。
- 若用户质疑“有没有按这个生成”，必须查 `tasks.jsonl` 的 submitted payload。
- 飞书插图后要 fetch 验证图片尺寸和文档块状态。

一票否决：没有可追溯 YAML / task 记录；YAML 与实际提交 payload 不一致；产物只在聊天里，项目目录没有回填。

### P10 审查复盘与规则沉淀

把失败原因归入正确层级。单项目审美写项目文档；跨项目 workflow、provider 行为、字段语义、排障经验写本 skill 的 references / scripts / tests。

通用规则：

- 用户批注先转成验收项，再转成生成约束；不要只改当前 prompt。
- 每次汇报必须说明当前是草案、分镜图、技术预览、候选段，还是正式片段。
- 规则类内容先供审阅，确认后再写入 truth source。

一票否决：只根据最近一条批注修 prompt；失败原因没有归类；把项目私有设定误写成通用规则。

## 生成前检查表

| 层级 | 问题 |
|---|---|
| P0 | 用户目标、禁区、预算是否明确？ |
| P1 | 目标—阻碍—推进—结果是否成立？ |
| P2 | 世界规则和身份逻辑是否自洽？ |
| P3 | 角色/场景/核心道具是否已资产化？ |
| P4 | 与上一镜/下一镜的承接是否定义？ |
| P5 | 分镜尺度是否适合模型执行？ |

## 生成后验收表

| 层级 | 问题 |
|---|---|
| P3 | 资产是否真的一致？ |
| P4 | clip 间是否接得上？ |
| P6 | 动作是否有 beat 和节奏？ |
| P7 | 画面/构图/道具细节是否可 review？ |
| P8 | 视频输入/输出是否无字段误用和结构残留？ |
| P9 | YAML / tasks.jsonl / 飞书文档是否回填验证？ |
| P10 | 失败原因是否沉淀到项目或通用规则？ |

## 常见坑

- 把项目私有设定误写成通用规则。
- 只根据最近一条用户批注修 prompt，忘记早先的叙事/身份/资产层问题。
- 先修局部小物件，忽略角色、场景、核心道具的大件漂移。
- 把九宫格当视频 first frame。
- 传了参考图就声称“已锁定”，但没有视觉核对。
- 规则类内容没让用户确认就写入 truth source。

## Skill 整理建议

本文件是“通用创作优先级”的入口，不再把 P0-P10 平铺到 `SKILL.md` 主体里。`SKILL.md` 只保留一条触发导航和 Reference map；具体内容放在本文件。若后续继续增长，优先新增 checklist/template 文件，不要继续加长 `SKILL.md`。
