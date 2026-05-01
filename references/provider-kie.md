# KIE Provider

## 何时使用

- 默认资产图、分镜图、分镜视频生成。
- 用户明确要求 `kie`、`gpt-image-2` 或 `bytedance/seedance-2-fast`。

## 默认模型

- 图片默认：`gpt-image-2-text-to-image`
- 图片可用备选：`nano-banana-2`（当 `gpt-image-2-text-to-image` 在 KIE 返回短时 500/Internal Error，或用户强调真实感资产图时，可切换到该模型重试）
- 视频：`bytedance/seedance-2-fast`

## YAML 规则

1. `provider` 写在 task 层，不写进 `params`。
2. 资产图和分镜图未被项目或用户覆盖时，默认使用 `tasks.image.provider: kie` 与 `tasks.image.params.model: gpt-image-2-text-to-image`；若 provider 侧连续返回 `500/Internal Error`，或当前任务更需要真实感资产三视图，可保持 `provider: kie` 不变并切换到 `params.model: nano-banana-2` 重试。
3. 分镜视频未被项目或用户覆盖时，统一使用 `tasks.video.provider: kie`、`tasks.video.params.model: bytedance/seedance-2-fast`、`tasks.video.params.duration: 15s` 与 `tasks.video.params.resolution: 480p`。
4. 参考图字段与首尾帧字段必须显式区分；不要把所有图片都塞进通用 `params.images` 让运行时按数量猜测。
5. 本地图片路径必须使用相对项目根目录的路径；远程 URL 可直接写 URL。
6. KIE `nano-banana-2` 的 image-to-image / reference-image 分镜图若用本地相对路径触发 provider 侧 `500 Server exception`，不要立刻判定 prompt 或 YAML 语义有误；优先改用上一轮已成功产物的远程 `latest.remote_output` / `tasks.jsonl.remote_outputs` URL 作为 `image_urls` 重试。
7. 飞书文档插入图片时，`lark-cli docs +media-insert --file` 要求文件路径是当前工作目录内的相对路径；先 `cd <project-root>`，再传 `assets/images/...`，不要直接传绝对路径。

## 执行前检查

1. 先确认当前安装的 runtime 真的注册了 `kie` provider。
2. 再确认凭证已进入当前进程环境或可被 `load_dotenv()` 读取。
3. 若 `asset generate` 报 `Unsupported provider: kie`，先修/更新 provider registry，不要改项目 YAML 到其他 provider。
4. 若报 `API Key missing for provider: kie`，这是环境凭证问题；不要尝试用通用 `image_generate` 作为等价替代，除非已确认其后端凭证可用且用户同意偏离 Mangou provider 主链。
5. Seedance 15s 视频任务可能超过一次终端命令超时时间；如果命令超时但 YAML `tasks.video.latest.status` 是 `running` 且有 `task_id`，不要重提新任务，先用 `python3 -m mangou_skill.cli storyboard resume --path <yaml> --type video --json` 轮询并回填。

## 分镜视频参数映射与审计

KIE Seedance 视频生成的 YAML 真相源与 provider payload 不是逐字同形，但必须语义一致：

- YAML 中保持 `tasks.video.params.duration: 15s`；提交给 KIE 时规范化为数字秒数 `15`。
- YAML 中保持 `tasks.video.params.resolution: 480p`；提交 payload 中仍应为 `480p`。
- YAML 中保持 `tasks.video.params.model: bytedance/seedance-2-fast`；提交 payload 中不得变成旧模型名或 provider 示例模型。
- 参考图应优先使用显式参考图字段（如 `reference_image_urls` / `reference_images`，按当前 runtime 支持为准），首尾帧使用 `first_frame` / `last_frame` 等首尾帧字段；不要让运行时只按图片数量猜测语义。
- 兼容旧 YAML 时，通用 `images` 会被解析为 KIE 可接受的远程 `reference_image_urls`；本地相对路径必须先解析/上传为远程 URL，不能把本地路径原样提交给 KIE。
- 每次排查“是不是按 YAML 生成”时，必须检查 `tasks.jsonl` 的 `event: "submitted"`，核对 `input.yaml_params`、`input.resolved_params`、`input.submitted_payload`。
- 若 submitted payload 出现旧错误值（如 `duration: 4`、`model: seedance-2.0-fast-image-to-video`、`generate_audio: false`），立即停止生成，先修 runtime/provider 参数链路并补测试。
