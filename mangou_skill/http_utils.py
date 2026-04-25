from __future__ import annotations

import json
import ssl
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, parse, request


DEFAULT_TIMEOUT_SECONDS = 300


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: dict[str, str]
    body: bytes

    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    def json(self) -> Any:
        return json.loads(self.text())


def sleep(seconds: float) -> None:
    time.sleep(seconds)


def _build_request(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
) -> request.Request:
    return request.Request(url, data=data, headers=headers or {}, method=method)


def http_request(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> HttpResponse:
    req = _build_request(url, method=method, headers=headers, data=data)
    context = ssl.create_default_context()
    try:
        with request.urlopen(req, timeout=timeout, context=context) as response:
            return HttpResponse(
                status=response.getcode(),
                headers=dict(response.headers.items()),
                body=response.read(),
            )
    except error.HTTPError as exc:
        return HttpResponse(
            status=exc.code,
            headers=dict(exc.headers.items()),
            body=exc.read(),
        )


def fetch_with_retry(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
    max_retries: int = 3,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    retry_delay_seconds: float = 2.0,
    log_prefix: str = "[mangou]",
) -> HttpResponse:
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            return http_request(url, method=method, headers=headers, data=data, timeout=timeout)
        except Exception as exc:
            last_error = exc
            if attempt < max_retries - 1:
                print(f"{log_prefix} fetch failed (attempt {attempt + 1}/{max_retries}): {exc}")
                sleep(retry_delay_seconds * (attempt + 1))
    if last_error is None:
        raise RuntimeError("Request failed without exception")
    raise last_error


def parse_json_response(response: HttpResponse, context: str, prefix: str) -> Any:
    raw = response.text()
    try:
        return json.loads(raw)
    except Exception as exc:
        trimmed = raw.strip()
        if trimmed.startswith("{"):
            depth = 0
            in_string = False
            escaped = False
            for index, ch in enumerate(trimmed):
                if in_string:
                    if escaped:
                        escaped = False
                    elif ch == "\\":
                        escaped = True
                    elif ch == '"':
                        in_string = False
                    continue
                if ch == '"':
                    in_string = True
                    continue
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        first_object = trimmed[: index + 1]
                        try:
                            return json.loads(first_object)
                        except Exception:
                            break
        preview = raw[:400]
        raise RuntimeError(f"{prefix} Failed to parse JSON from {context}: {response.status} {preview}") from exc


def join_url(base: str, *parts: str) -> str:
    normalized_base = str(base or "").rstrip("/")
    normalized_parts = [str(part or "").strip("/") for part in parts if str(part or "").strip("/")]
    if not normalized_parts:
        return normalized_base
    return normalized_base + "/" + "/".join(normalized_parts)


def build_json_body(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def build_multipart_form_data(
    fields: dict[str, str],
    files: list[tuple[str, str, bytes, str]],
) -> tuple[str, bytes]:
    boundary = f"----MangouBoundary{uuid.uuid4().hex}"
    chunks: list[bytes] = []

    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )

    for field_name, filename, content, mime_type in files:
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                (
                    f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
                    f"Content-Type: {mime_type}\r\n\r\n"
                ).encode("utf-8"),
                content,
                b"\r\n",
            ]
        )

    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return boundary, b"".join(chunks)


def download_file(
    url: str,
    target_path: Path,
    *,
    max_attempts: int = 5,
    log_prefix: str = "[mangou]",
) -> None:
    for attempt in range(1, max_attempts + 1):
        print(f"{log_prefix} Downloading asset: {url} (attempt {attempt}/{max_attempts})")
        response = fetch_with_retry(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            },
            log_prefix=log_prefix,
        )
        if 200 <= response.status < 300:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(response.body)
            return

        should_retry = response.status == 404 and attempt < max_attempts
        if should_retry:
            delay_seconds = 5 * attempt
            print(f"{log_prefix} Remote asset not ready yet: {url} ({response.status}). Retrying in {delay_seconds}s...")
            sleep(delay_seconds)
            continue

        raise RuntimeError(f"Failed to download {url}: {response.status} {response.text()[:200]}")
