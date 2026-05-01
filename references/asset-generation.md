# 资产 YAML

## 何时阅读

- 要新建角色、场景、道具定义
- 要让分镜复用资产参考图
- 要排查 `asset generate` 的输入是否合理

## 路径

- `asset_defs/chars/`
- `asset_defs/scenes/`
- `asset_defs/props/`
- 生成产物统一写到 `assets/`

## 最小结构

- `meta.id`: 唯一 ID
- `meta.type`: `character` / `scene` / `prop`
- `meta.version`: 建议 `"1.0"`
- `content.name`: 中文名
- `content.name_en`: 英文名
- `content.description`: 基础描述
- `content.appearance`: 视觉特征
- `content.setting`: 设定补充
- `tasks.image`: 资产基准图任务

## 规则

1. 先生成资产基准图，再在分镜里引用它。
2. `asset_defs/` 只放 YAML，不放大图或二进制产物。
3. 分镜里引用资产时，同时维护：
   - `content.characters` 中的资产 ID
   - `tasks.<type>.params.images` 中的产物相对路径
4. 若 KIE `gpt-image-2-text-to-image` 连续返回 provider 侧 `500/Internal Error, Please try again later`，先不要把问题归因到项目 YAML；可在保持 `provider: kie` 不变的情况下临时切到 `params.model: nano-banana-2` 重试，尤其适合真实感角色/动物资产三视图。
5. 批量生成 5+ 个资产时，优先用 background/notify_on_complete 或外层脚本逐个调用 CLI，避免单次前台等待超时；完成后再统一做回填验证。
6. 若 provider 返回的是带 task id 的临时文件名（如 `assets/images/name-<task>-0.png` / `.jpeg`），而项目分镜引用固定基准图路径（如 `assets/images/char-name-ref.png` / `.jpeg`），必须复制到固定 `*-ref.*` 路径，并同步更新资产 YAML：`tasks.image.latest.status: completed`、`tasks.image.latest.output: <fixed-ref-path>`、`tasks.image.outputs[0].path: <fixed-ref-path>`。
7. 回填后用脚本验证每个固定文件存在、非 0 字节，并按实际格式检查文件头（PNG `\x89PNG\r\n\x1a\n`；JPEG `\xff\xd8\xff`）；再把这些 `MEDIA:/absolute/path` 返回给用户。

## 示例

```yaml
meta:
  id: "asset-001"
  type: "character"
  version: "1.0"
content:
  name: "资产名称"
  name_en: "Asset Name"
  description: "保留用户提供的资产设定。"
  appearance: "描述需要稳定复用的外观特征。"
tasks:
  image:
    provider: "<configured-image-provider>"
    params:
      model: "<provider-model>"
      prompt: "Asset reference image prompt based on current project requirements."
    latest:
      status: "completed"
      output: "assets/images/asset-001-ref.png"
```
