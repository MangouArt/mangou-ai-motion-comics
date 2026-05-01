# Vlog 九宫格分镜与 Seedance 预览

## 适用场景

用户要“vlog 分镜图”“供 review 的分镜图”“每张图内部九宫格”“详细描述镜头移动”时，不要默认输出很多单张镜头。优先做少量母图，每张母图内部是 3x3 contact sheet。

## 推荐产物形态

- 默认数量：若用户未指定，可先给 4 张九宫格母图；若用户明确说“4 个分镜图即可”，严格只做 4 张。
- 每张母图：16:9 横版，内部清晰 3x3 九宫格，黑色细分隔线。
- 每格：同一角色、同一段 vlog 的连续镜头；要写清镜头运动（推、拉、摇、移、跟拍、低机位、过肩、主观机位、手持抖动）。
- Vlog 语法：第一视角、手机/运动相机、手持随拍、拍摄设备入画、自然生活光、轻微不稳定构图。否则模型容易生成电影感宠物写真或单张生活照。
- 动物/宠物第一视角 vlog：必须明确“相机固定在角色自己的胸前/项圈/背带上”“狗眼/动物眼高度”“鼻尖、耳朵、前爪可在画面边缘入画”“广角运动相机畸变和轻微晃动”；同时显式禁止“人在拍狗/第三人称宠物写真/外部电影机位”。
- 不要在图里生成可读文字、字幕、水印；若剧情需要手机/闹钟/屏幕，只写“不可读”。

## Prompt 骨架

```text
@image1:角色参考 = 角色身份锚点，保持同一只/同一人：[外观锚点]。

生成一张 16:9 横版真实感 VLOG 分镜图，画面内部必须是清晰的 3x3 九宫格，共九个小画面，黑色细分隔线，像导演分镜 contact sheet。每个小画面都是同一角色在同一段 vlog 里的连续镜头，手机/运动相机随拍感，真实生活光线，live-action vlog，纪录片质感，不要漫画、不要插画、不要字幕、不要可读文字、不要水印。

主题：《标题》一句话剧情。
九宫格镜头运动：
1/9 ...
2/9 ...
...
9/9 ...

视觉要求：九格必须明显分格，镜头角度和运动方向有变化；保持角色外观一致；画面像真实 vlog 截帧组合，不要单张电影剧照。
```

## 从九宫格母图生成视频预览

- 若用户要“看看视频效果”，九宫格母图应作为 `reference_images` / `reference_image_urls` 参考图输入，不要作为 `first_frame` 首帧输入；九宫格是分镜参考板，不是正式视频第一帧。
- 使用 `bytedance/seedance-2-fast` 生成 `15s`、`480p` 预览时，视频 YAML 必须显式写参考图字段，并避免 `first_frame`，除非用户明确要求做“九宫格整体动起来”的实验。
- 关键不是否定九宫格 reference image，而是视频 prompt 必须把语义说清楚：九宫格只是 storyboard/contact-sheet reference，用来理解 9 个连续 beats 的动作、构图和节奏；最终视频必须是单一连续 vlog 画面，不能显示九宫格、分隔线、panel border、split-screen 或 contact sheet。
- 推荐 prompt 句式：`Use the attached 3x3 storyboard contact sheet only as visual reference for nine sequential vlog beats. It is not a first frame and must never appear on screen. Generate one continuous full-frame live-action vlog shot; no grid, no panel borders, no split-screen, no contact sheet.`
- 只有当强 prompt 后仍稳定出现九宫格/分隔线，或用户明确要求正式无格连续视频时，才把母图切成 9 张单格 panel 作为 fallback reference；不要把“必须拆格”当成默认第一步。
- 预期效果是“按九宫格参考板理解镜头顺序的连续 vlog 预览”，不是把九宫格母图整体/分格直接动画化。最终汇报要提醒用户：如果要正式成片，下一步应把每格或每个 beat 拆成真实单镜头视频。

## Review 检查

生成后至少抽样/逐张检查：

- 是否真的是清晰 3x3，而不是单张剧照。
- 主角外观是否稳定。
- 是否有 vlog 感：自拍/手持/低机位/拍摄设备/随拍生活光。
- 镜头运动是否能从九格顺序读出来。
- 视频是否只是九宫格预览；不要误称为最终正式 vlog 成片。
