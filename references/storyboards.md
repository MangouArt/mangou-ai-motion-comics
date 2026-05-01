# 分镜 YAML

## Contents

- 最小结构
- 字段要求
- 规则
- 示例

## 最小结构

每个 `storyboards/*.yaml` 只表示一个镜头，根字段通常是：

- `meta`
- `content`
- `tasks`
- `refs`（可选）

## 字段要求

### `meta`

- `id`: 必填，通常与文件名一致
- `version`: 必填，建议 `"1.0"`
- `grid`: 可选。存在时表示母图
- `parent`: 可选。存在时表示子镜

### `content`

- `sequence`: 必填，镜头顺序
- `title`: 必填
- `story`: 必填，保留原剧情
- `action`: 必填，画面动作
- `scene`: 必填，场景说明
- `duration`: 必填，如 `"4s"`
- `characters`: 可选，角色 ID 列表

### `tasks.<type>`

- `provider`: 必填。脚本不会自动推断；按当前环境、用户要求和 provider 文档选择。
- `params.model`
- `params.prompt`
- `params.images`
- `latest`: 运行后回填

## 规则

1. 真相源是 `tasks.jsonl`，`latest` 只是投影缓存。
2. `params.images` 必须是相对项目根目录的路径。
3. 连续镜头优先引用上一镜产物来保持一致性。
4. 做 vlog / 口播 / 生活记录类分镜图时，图片 prompt 需要显式写出第一视角、手机/运动相机、手持晃动、自拍构图、拍摄设备入画、自然生活光、随拍感等 vlog 语法；否则模型容易生成电影感宠物写真，而不是 vlog 分镜。
5. 若用户要求“4 个分镜图即可”“每个分镜图内部九宫格”“详细描述镜头移动”，按 [vlog-grid-storyboards.md](vlog-grid-storyboards.md) 生成少量 3x3 contact sheet 母图；不要继续输出一长串单张镜头。
6. 母图和子镜的关系统一用 `meta.parent`、`meta.grid`、`meta.grid_index` 表达。
7. `storyboard split` 不从 prompt 猜 grid 尺寸，只认 `meta.grid` 或 `--grid`。
8. `storyboard split` 成功后也会写 `tasks.jsonl`，不要把它当例外。
9. `stitch` 优先用视频；没视频时会按 `content.duration` 用静图补预览段。
10. `tasks.image.provider` 和 `tasks.video.provider` 都必须显式写出；skill 仅提供推荐，不做脚本默认。

## 示例

```yaml
meta:
  id: "shot-001"
  version: "1.0"
content:
  sequence: 1
  title: "镜头标题"
  story: "保留用户提供的原始剧情或需求。"
  action: "描述当前镜头中可执行的主体动作。"
  scene: "描述当前镜头所在的场景和空间关系。"
  duration: "4s"
tasks:
  image:
    provider: "<configured-image-provider>"
    params:
      model: "<provider-model>"
      prompt: "Subject, action, scene, composition, and project-specific constraints."
      aspect_ratio: "16:9"
    latest:
      status: "completed"
      output: "assets/images/shot-001.png"
```
