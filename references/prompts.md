# Prompt 框架

## 何时阅读

- 要把用户需求转换为图片或视频生成 prompt
- 要让 prompt 与项目 YAML、资产引用和 provider 参数保持一致
- 要排查生成结果偏离当前项目约束

## 核心原则

1. Prompt 应服务当前项目，不携带 skill 内置审美偏好。
2. 风格、镜头、材质、题材和负向约束必须来自用户需求、项目 YAML、参考素材或会话上下文。
3. Prompt 只写可执行约束，不把临时经验沉淀成全局默认。
4. 连续性优先依赖引用图、资产基准图和上一镜产物；文字 prompt 只补充必要变化。

## 图片 Prompt 结构

按需组织以下信息：

- 主体：角色、物体或场景核心对象
- 状态：姿态、表情、动作或变化
- 环境：地点、时间、光线、空间关系
- 构图：镜头距离、视角、画幅、主体位置
- 风格：仅使用当前项目明确要求的风格
- 约束：需要避免的文字、水印、错位、结构错误等

示例模板：

```text
Subject: <who or what>
State: <pose/action/change>
Environment: <where, lighting, atmosphere>
Composition: <shot size, angle, framing>
Style constraints: <project-specific style only>
Negative constraints: <known failure modes only>
```

## 视频 Prompt 结构

视频 prompt 应优先说明变化过程：

- 起始状态
- 结束状态
- 摄影机运动
- 主体运动
- 不应变化的身份、空间或构图约束
- 时间分段（仅在动作复杂时使用）

示例模板：

```text
Start: <initial visual state>
Motion: <camera and subject movement>
End: <final visual state>
Continuity: keep <identity/position/style constraints>
Avoid: <project-specific failure modes>
```

## 资产引用

1. 角色、场景、道具需要稳定复用时，先生成资产基准图。
2. 后续分镜通过 `params.images`、`image_urls` 或 provider 对应媒体字段引用资产。
3. 是否需要正面、侧面、背面等多视图，由当前项目复杂度决定，不作为默认要求。

## Grid Prompt

使用 grid 母图时：

1. grid 尺寸以 `meta.grid` 为真相源。
2. prompt 可以说明每格内容，但不要让 prompt 成为 grid 尺寸的唯一依据。
3. 如果要后续切分，明确要求无字幕、无水印、无额外边框或其它当前项目不需要的装饰。
4. 如果模型把 grid 生成成普通漫画页，再临时追加更强的几何约束；这些约束只用于当前任务排障。

## 失败排查

结果偏离预期时，按顺序检查：

1. 当前 YAML 是否表达了真实需求。
2. 是否缺少必要参考图或上一镜产物。
3. provider 字段是否符合对应 `provider-*.md`。
4. prompt 是否混入了与当前项目无关的风格或负向约束。
5. 是否需要把稳定约束写入项目 YAML，而不是只写在一次性 prompt 中。
