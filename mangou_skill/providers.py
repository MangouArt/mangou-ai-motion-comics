from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass
from typing import Any, Protocol

from .http_utils import (
    build_json_body,
    build_multipart_form_data,
    fetch_with_retry,
    join_url,
    parse_json_response,
    sleep,
)


class Provider(Protocol):
    id: str
    env: dict[str, str]
    scopes: dict[str, str]

    def build_payload(self, scope: str, params: dict[str, Any]) -> dict[str, Any]: ...
    def submit(self, *, base_url: str, api_key: str, scope: str, payload: dict[str, Any]) -> Any: ...
    def poll(self, *, base_url: str, api_key: str, scope: str, task_id: Any, timeout_ms: int = ...) -> Any: ...
    def extract_outputs(self, scope: str, result: Any) -> list[str]: ...


def normalize_base_url(input_value: str | None, fallback: str) -> str:
    base = (input_value or fallback).strip().rstrip("/")
    if base.endswith("/v1") or base.endswith("/v2"):
        base = base[:-3]
    return base


def resolve_provider_env(provider: Provider, env: dict[str, str], provider_config: dict[str, Any] | None = None) -> tuple[str, str]:
    provider_config = provider_config or {}
    api_key = str(env.get(provider.env["apiKey"], "") or provider_config.get("apiKey", "")).strip()
    base_url = normalize_base_url(
        str(env.get(provider.env["baseUrl"], "") or provider_config.get("baseUrl", "")),
        provider.env["defaultBaseUrl"],
    )
    return api_key, base_url


def _parse_data_url(data_url: str, prefix: str) -> tuple[str, bytes]:
    if not data_url.startswith("data:") or ";base64," not in data_url:
        raise RuntimeError(f"{prefix} Invalid Data URL: expected data:<mime>;base64,<data>")
    metadata, encoded = data_url.split(",", 1)
    mime_type = metadata[5:].split(";", 1)[0]
    return mime_type, base64.b64decode(encoded)


def _upload_data_url(url: str, *, field_name: str, api_key: str | None, data_url: str, extra_fields: dict[str, str], prefix: str) -> str:
    mime_type, data = _parse_data_url(data_url, prefix)
    extension = mimetypes.guess_extension(mime_type) or ".bin"
    boundary, payload = build_multipart_form_data(
        extra_fields,
        [(field_name, f"upload{extension}", data, mime_type)],
    )
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    response = fetch_with_retry(url, method="POST", headers=headers, data=payload, log_prefix=prefix)
    result = parse_json_response(response, "file upload", prefix)
    return _extract_uploaded_url(result, response.status, prefix)


def _extract_uploaded_url(result: Any, status: int, prefix: str) -> str:
    url = (
        result.get("url")
        or result.get("data", {}).get("url")
        or result.get("file", {}).get("url")
        or result.get("data", {}).get("file", {}).get("url")
        or result.get("data", {}).get("file_url")
    )
    if not isinstance(url, str) or not url:
        raise RuntimeError(f"{prefix} File upload failed: {status} {result}")
    return url


@dataclass(frozen=True)
class BLTAIProvider:
    id: str = "bltai"
    env: dict[str, str] = None  # type: ignore[assignment]
    scopes: dict[str, str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(self, "env", {
            "apiKey": "BLTAI_API_KEY",
            "baseUrl": "BLTAI_BASE_URL",
            "defaultBaseUrl": "https://api.bltcy.ai",
        })
        object.__setattr__(self, "scopes", {"image": "images", "video": "videos"})

    def build_payload(self, scope: str, params: dict[str, Any]) -> dict[str, Any]:
        prompt = str(params.get("prompt", "")).strip()
        if not prompt:
            raise RuntimeError("[bltai] Missing required parameter: 'prompt'")
        model = str(params.get("model", "")).strip()
        if not model:
            raise RuntimeError("[bltai] 缺失 'model' 参数。请在 YAML 的 tasks.*.params.model 中指定。")

        if scope == "images":
            if "images" in params:
                raise RuntimeError("[bltai] 图像生成请使用 'image: []'，不要使用 'images'.")
            payload: dict[str, Any] = {"prompt": prompt, "model": model, "response_format": "url"}
            if params.get("aspect_ratio"):
                payload["aspect_ratio"] = params["aspect_ratio"]
            if params.get("image_size"):
                payload["image_size"] = params["image_size"]
            if "image" in params:
                if not isinstance(params["image"], list):
                    raise RuntimeError("[bltai] 'image' 必须是数组")
                payload["image"] = [item for item in params["image"] if item]
            return payload

        if scope == "videos":
            images = params.get("images")
            if images is None:
                images = []
            if not isinstance(images, list):
                images = [images]
            payload = {
                "model": model,
                "prompt": prompt,
                "images": [item for item in images if item],
                "duration": params.get("duration", 5),
            }
            if params.get("ratio") or params.get("aspect_ratio"):
                payload["ratio"] = params.get("ratio") or params.get("aspect_ratio")
            if params.get("resolution"):
                payload["resolution"] = params["resolution"]
            return payload

        raise RuntimeError(f"[bltai] Unsupported scope: {scope}")

    def submit(self, *, base_url: str, api_key: str, scope: str, payload: dict[str, Any]) -> Any:
        final_payload = dict(payload)
        if scope == "images" and isinstance(final_payload.get("image"), list):
            uploaded: list[Any] = []
            for item in final_payload["image"]:
                if isinstance(item, str) and item.startswith("data:"):
                    uploaded.append(
                        _upload_data_url(
                            join_url(base_url, "v1", "files"),
                            field_name="file",
                            api_key=api_key,
                            data_url=item,
                            extra_fields={},
                            prefix="[bltai]",
                        )
                    )
                else:
                    uploaded.append(item)
            final_payload["image"] = uploaded

        endpoint = join_url(base_url, "v1", "images", "generations") if scope == "images" else join_url(base_url, "v2", "videos", "generations")
        if scope == "images":
            endpoint += "?async=true"

        response = fetch_with_retry(
            endpoint,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            data=build_json_body(final_payload),
            log_prefix="[bltai]",
        )
        data = parse_json_response(response, f"{scope} submit", "[bltai]")
        if not 200 <= response.status < 300:
            raise RuntimeError(f"[bltai] Submit failed: {response.status} {data}")

        if scope == "images" and isinstance(data.get("data"), list) and data["data"] and data["data"][0].get("url"):
            return {"instantData": data}

        task_id = (
            data.get("id")
            or data.get("task_id")
            or data.get("data", {}).get("id")
            or data.get("data", {}).get("task_id")
            or data.get("task", {}).get("id")
            or (data.get("data") if isinstance(data.get("data"), str) else None)
        )
        if not task_id:
            raise RuntimeError(f"[bltai] Missing task id: {data}")
        return task_id

    def poll(self, *, base_url: str, api_key: str, scope: str, task_id: Any, timeout_ms: int = 30 * 60 * 1000) -> Any:
        if isinstance(task_id, dict) and task_id.get("instantData"):
            return task_id["instantData"]
        endpoint = join_url(base_url, "v1", "images", "tasks", str(task_id)) if scope == "images" else join_url(base_url, "v2", "videos", "generations", str(task_id))
        started = time_ms()
        delay_ms = 2000
        while True:
            response = fetch_with_retry(endpoint, headers={"Authorization": f"Bearer {api_key}"}, log_prefix="[bltai]")
            if not 200 <= response.status < 300:
                raise RuntimeError(f"[bltai] Poll failed: {response.status} {response.text()[:300]}")
            data = parse_json_response(response, f"{scope} poll {task_id}", "[bltai]")
            raw_status = (
                data.get("status")
                or data.get("state")
                or data.get("task_status")
                or data.get("data", {}).get("status")
                or data.get("task", {}).get("status")
                or ""
            )
            status = str(raw_status).upper()
            if status in {"SUCCESS", "SUCCEEDED", "COMPLETED", "DONE", "FINISHED"}:
                return data
            if status in {"FAILED", "FAILURE", "ERROR", "CANCELLED", "CANCELED", "TIMEOUT", "EXPIRED"}:
                raise RuntimeError(f"[bltai] Provider task failed: {data}")
            if time_ms() - started > timeout_ms:
                raise RuntimeError("[bltai] Provider polling timeout")
            sleep(delay_ms / 1000)
            delay_ms = min(delay_ms + 2000, 15000)

    def extract_outputs(self, scope: str, result: Any) -> list[str]:
        if scope == "images":
            records = result.get("data", {}).get("data", {}).get("data")
            if records is None:
                records = result.get("data", {}).get("data") or result.get("data") or []
            if isinstance(records, dict) and isinstance(records.get("data"), list):
                records = records["data"]
            if not isinstance(records, list):
                records = []
            return [item.get("url") for item in records if isinstance(item, dict) and item.get("url")]

        data = result.get("data", result)
        video_url = (
            data.get("output")
            or data.get("video_url")
            or data.get("data", {}).get("output")
            or data.get("data", {}).get("video_url")
            or data.get("output", {}).get("url")
            or data.get("url")
        )
        if isinstance(video_url, str) and video_url:
            return [video_url]
        outputs = data.get("outputs")
        if isinstance(outputs, list):
            return [item for item in outputs if isinstance(item, str) and item]
        return []


@dataclass(frozen=True)
class AnyIntProvider:
    id: str = "anyint"
    env: dict[str, str] = None  # type: ignore[assignment]
    scopes: dict[str, str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(self, "env", {
            "apiKey": "ANYINT_API_KEY",
            "baseUrl": "ANYINT_BASE_URL",
            "defaultBaseUrl": "https://gateway.api.anyint.ai",
        })
        object.__setattr__(self, "scopes", {"image": "images", "video": "videos"})

    def build_payload(self, scope: str, params: dict[str, Any]) -> dict[str, Any]:
        if scope != "videos":
            raise RuntimeError("[anyint] 当前只支持视频生成")
        model = str(params.get("model", "")).strip()
        supported = {"doubao-seedance-2-0-260128", "doubao-seedance-2-0-fast-260128"}
        if model not in supported:
            raise RuntimeError(f"[anyint] 不支持的 model: {model or '(empty)'}")
        content = params.get("content")
        if not isinstance(content, list) or not content:
            raise RuntimeError("[anyint] content 必须是非空数组")
        duration = int(params.get("duration", 5))
        if duration < 4 or duration > 15:
            raise RuntimeError("[anyint] duration 必须在 4 到 15 秒之间")
        ratio = str(params.get("ratio", "adaptive"))
        if ratio not in {"21:9", "16:9", "4:3", "1:1", "3:4", "9:16", "adaptive"}:
            raise RuntimeError("[anyint] ratio 不合法")
        resolution = str(params.get("resolution", "720p"))
        if resolution not in {"480p", "720p"}:
            raise RuntimeError("[anyint] resolution 只接受 '480p' 或 '720p'")
        return {
            "model": model,
            "content": content,
            "duration": duration,
            "ratio": ratio,
            "resolution": resolution,
            "watermark": bool(params.get("watermark", False)),
            "generate_audio": bool(params.get("generate_audio", True)),
        }

    def submit(self, *, base_url: str, api_key: str, scope: str, payload: dict[str, Any]) -> Any:
        if scope != "videos":
            raise RuntimeError("[anyint] 当前只支持视频生成")
        final_payload = dict(payload)
        content_items: list[dict[str, Any]] = []
        for item in final_payload.get("content", []):
            next_item = dict(item)
            for field in ("image_url", "video_url", "audio_url"):
                value = next_item.get(field)
                if isinstance(value, dict) and isinstance(value.get("url"), str) and value["url"].startswith("data:"):
                    file_type = "image" if field == "image_url" else "video" if field == "video_url" else "audio"
                    next_item[field] = {
                        "url": _upload_data_url(
                            join_url(base_url, "files", "upload"),
                            field_name="file",
                            api_key=None,
                            data_url=value["url"],
                            extra_fields={"fileType": file_type, "public": "true", "folder": "seedance-references"},
                            prefix="[anyint]",
                        )
                    }
            content_items.append(next_item)
        final_payload["content"] = content_items

        response = fetch_with_retry(
            join_url(base_url, "doubao", "video", "generations"),
            method="POST",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            data=build_json_body(final_payload),
            log_prefix="[anyint]",
        )
        data = parse_json_response(response, "anyint video submit", "[anyint]")
        if not 200 <= response.status < 300:
            raise RuntimeError(f"[anyint] Submit failed: {response.status} {data}")
        task_id = data.get("task_id") or data.get("id")
        if not task_id:
            raise RuntimeError(f"[anyint] Missing task id: {data}")
        return task_id

    def poll(self, *, base_url: str, api_key: str, scope: str, task_id: Any, timeout_ms: int = 30 * 60 * 1000) -> Any:
        if scope != "videos":
            raise RuntimeError("[anyint] 当前只支持视频生成")
        started = time_ms()
        delay_ms = 2000
        while True:
            response = fetch_with_retry(join_url(base_url, "doubao", "videos", str(task_id)), headers={"Authorization": f"Bearer {api_key}"}, log_prefix="[anyint]")
            data = parse_json_response(response, "anyint video poll", "[anyint]")
            if not 200 <= response.status < 300:
                raise RuntimeError(f"[anyint] Poll failed: {response.status} {data}")
            status = str(data.get("status", "")).lower()
            if status == "completed":
                return data
            if status in {"failed", "expired", "cancelled"}:
                raise RuntimeError(f"[anyint] Provider task failed: {data}")
            if time_ms() - started > timeout_ms:
                raise RuntimeError("[anyint] Provider polling timeout")
            sleep(delay_ms / 1000)
            delay_ms = min(delay_ms * 2, 8000)

    def extract_outputs(self, scope: str, result: Any) -> list[str]:
        if scope != "videos":
            return []
        return [
            candidate
            for candidate in [result.get("metadata", {}).get("url"), result.get("data", {}).get("url"), result.get("url")]
            if isinstance(candidate, str) and candidate
        ]


@dataclass(frozen=True)
class EvolinkProvider:
    id: str = "evolink"
    env: dict[str, str] = None  # type: ignore[assignment]
    scopes: dict[str, str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(self, "env", {
            "apiKey": "EVOLINK_API_KEY",
            "baseUrl": "EVOLINK_BASE_URL",
            "defaultBaseUrl": "https://api.evolink.ai",
        })
        object.__setattr__(self, "scopes", {"image": "images", "video": "videos"})

    def build_payload(self, scope: str, params: dict[str, Any]) -> dict[str, Any]:
        model = str(params.get("model", "")).strip()
        if not model:
            raise RuntimeError("[evolink] Missing required parameter: 'model'")
        image_models = {"gemini-3.1-flash-image-preview"}
        text_video_models = {"seedance-2.0-text-to-video", "seedance-2.0-fast-text-to-video"}
        image_video_models = {"seedance-2.0-image-to-video", "seedance-2.0-fast-image-to-video"}
        reference_video_models = {"seedance-2.0-reference-to-video", "seedance-2.0-fast-reference-to-video"}
        supported = image_models | text_video_models | image_video_models | reference_video_models
        if model not in supported:
            raise RuntimeError(f"[evolink] Unsupported model: {model}")

        if scope == "images":
            if model not in image_models:
                raise RuntimeError("[evolink] 图片模型只支持 'gemini-3.1-flash-image-preview'")
            payload = {
                "model": model,
                "prompt": str(params.get("prompt", "")).strip(),
                "size": params.get("size", "auto"),
                "quality": params.get("quality", "2K"),
            }
            if not payload["prompt"]:
                raise RuntimeError("[evolink] Missing required parameter: 'prompt'")
            if params.get("image_urls"):
                payload["image_urls"] = list(params["image_urls"])
            if params.get("model_params"):
                payload["model_params"] = params["model_params"]
            if params.get("callback_url"):
                payload["callback_url"] = params["callback_url"]
            return payload

        if scope != "videos":
            raise RuntimeError(f"[evolink] Unsupported scope: {scope}")
        prompt = str(params.get("prompt", "")).strip()
        if not prompt:
            raise RuntimeError("[evolink] Missing required parameter: 'prompt'")
        payload = {
            "model": model,
            "prompt": prompt,
            "duration": int(params.get("duration", 8)),
            "quality": params.get("quality") or params.get("resolution") or "720p",
            "aspect_ratio": params.get("aspect_ratio", "16:9"),
            "generate_audio": params.get("generate_audio", True),
        }
        for field in ("image_urls", "video_urls", "audio_urls"):
            if params.get(field):
                payload[field] = list(params[field])
        if params.get("model_params"):
            payload["model_params"] = params["model_params"]
        if params.get("callback_url"):
            payload["callback_url"] = params["callback_url"]
        return payload

    def submit(self, *, base_url: str, api_key: str, scope: str, payload: dict[str, Any]) -> Any:
        final_payload = dict(payload)
        for field in ("image_urls", "video_urls", "audio_urls"):
            if isinstance(final_payload.get(field), list):
                values: list[str] = []
                for value in final_payload[field]:
                    if isinstance(value, str) and value.startswith("data:"):
                        values.append(
                            _upload_data_url(
                                "https://files-api.evolink.ai/api/v1/files/upload/stream",
                                field_name="file",
                                api_key=api_key,
                                data_url=value,
                                extra_fields={"upload_path": "mangou-uploads"},
                                prefix="[evolink]",
                            )
                        )
                    else:
                        values.append(value)
                final_payload[field] = values

        endpoint = join_url(base_url, "v1", "images", "generations") if scope == "images" else join_url(base_url, "v1", "videos", "generations")
        response = fetch_with_retry(
            endpoint,
            method="POST",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            data=build_json_body(final_payload),
            log_prefix="[evolink]",
        )
        data = parse_json_response(response, "evolink submit", "[evolink]")
        if not 200 <= response.status < 300:
            raise RuntimeError(f"[evolink] Submit failed: {response.status} {data}")
        task_id = data.get("id") or data.get("task_id")
        if not task_id:
            raise RuntimeError(f"[evolink] Missing task id in response: {data}")
        return task_id

    def poll(self, *, base_url: str, api_key: str, scope: str, task_id: Any, timeout_ms: int = 30 * 60 * 1000) -> Any:
        endpoint = join_url(base_url, "v1", "tasks", str(task_id))
        started = time_ms()
        delay_ms = 2000
        while True:
            response = fetch_with_retry(endpoint, headers={"Authorization": f"Bearer {api_key}"}, log_prefix="[evolink]")
            if not 200 <= response.status < 300:
                raise RuntimeError(f"[evolink] Poll failed: {response.status} {response.text()[:300]}")
            data = parse_json_response(response, "evolink poll", "[evolink]")
            status = str(data.get("status", "")).lower()
            if status in {"completed", "success"}:
                return data
            if status in {"failed", "error", "cancelled", "canceled"}:
                raise RuntimeError(f"[evolink] Provider task failed: {data}")
            if time_ms() - started > timeout_ms:
                raise RuntimeError("[evolink] Provider polling timeout")
            sleep(delay_ms / 1000)
            delay_ms = min(delay_ms + 2000, 15000)

    def extract_outputs(self, scope: str, result: Any) -> list[str]:
        candidates: list[Any] = []
        if scope == "images":
            for field in ("results", "data", "output", "outputs", "image_urls"):
                value = result.get(field)
                if isinstance(value, list):
                    candidates.extend(value)
            nested = result.get("result", {}).get("images")
            if isinstance(nested, list):
                candidates.extend(nested)
        elif scope == "videos":
            for field in ("results", "data", "output", "outputs", "video_urls"):
                value = result.get(field)
                if isinstance(value, list):
                    candidates.extend(value)
            nested = result.get("result", {}).get("videos")
            if isinstance(nested, list):
                candidates.extend(nested)
        else:
            return []

        outputs: list[str] = []
        for item in candidates:
            if isinstance(item, str) and item:
                outputs.append(item)
            elif isinstance(item, dict):
                value = item.get("url") or item.get("image_url") or item.get("video_url") or item.get("download_url") or item.get("output_url")
                if isinstance(value, str) and value:
                    outputs.append(value)
        return outputs


PROVIDERS: dict[str, Provider] = {
    "bltai": BLTAIProvider(),
    "anyint": AnyIntProvider(),
    "evolink": EvolinkProvider(),
}


def get_provider(provider_id: str = "bltai") -> Provider:
    provider = PROVIDERS.get(provider_id)
    if provider is None:
        supported = ", ".join(sorted(PROVIDERS.keys()))
        raise RuntimeError(f"Unsupported provider: {provider_id}. Available providers: {supported}")
    return provider


def time_ms() -> int:
    import time

    return int(time.time() * 1000)
