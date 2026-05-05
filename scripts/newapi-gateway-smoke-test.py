#!/usr/bin/env python3
"""Smoke-test Mangou NewAPI Agent Gateway without leaking tokens."""
from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_BASE = "https://mangou-newapi.zeabur.app"
TERMINAL = {"completed", "complete", "success", "succeeded", "failed", "error", "cancelled", "canceled", "timeout"}


def load_env() -> None:
    for env_file in [Path("/opt/data/.env"), Path.cwd() / ".env"]:
        if not env_file.exists():
            continue
        for line in env_file.read_text(errors="ignore").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            os.environ.setdefault(k.strip().replace("export ", ""), v.strip().strip('"').strip("'"))


def parse_json(text: str) -> Any | None:
    try:
        return json.loads(text)
    except Exception:
        return None


class Client:
    def __init__(self, base: str, token: str):
        self.base = base.rstrip("/")
        self.token = token

    def normalize_url(self, url: str) -> str:
        return re.sub(r"^http://localhost:3000", self.base, url)

    def scrub_text(self, text: str | None) -> str | None:
        if text is None:
            return None
        if self.token:
            text = text.replace(self.token, "[REDACTED_TOKEN]")
        return re.sub(r"Bearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [REDACTED]", text)

    def scrub_obj(self, obj: Any) -> Any:
        try:
            return json.loads(self.scrub_text(json.dumps(obj, ensure_ascii=False)) or "null")
        except Exception:
            return obj

    def request(self, method: str, path_or_url: str, body: Any = None, auth: bool = False, accept: str | None = None, timeout: int = 120) -> dict:
        url = path_or_url if path_or_url.startswith("http") else self.base + path_or_url
        url = self.normalize_url(url)
        headers = {}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if accept:
            headers["Accept"] = accept
        if auth:
            headers["Authorization"] = "Bearer " + self.token
        data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                text = raw[:5000].decode("utf-8", "replace")
                parsed = parse_json(text)
                return {
                    "method": method,
                    "url": url,
                    "http": resp.status,
                    "ok_http": 200 <= resp.status < 300,
                    "content_type": resp.headers.get("content-type", ""),
                    "bytes": len(raw),
                    "text": self.scrub_text(text),
                    "json": self.scrub_obj(parsed) if parsed is not None else None,
                }
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            text = raw[:5000].decode("utf-8", "replace")
            parsed = parse_json(text)
            return {
                "method": method,
                "url": url,
                "http": exc.code,
                "ok_http": False,
                "content_type": exc.headers.get("content-type", "") if exc.headers else "",
                "bytes": len(raw),
                "text": self.scrub_text(text),
                "json": self.scrub_obj(parsed) if parsed is not None else None,
            }
        except Exception as exc:
            return {"method": method, "url": url, "http": None, "ok_http": False, "error": f"{type(exc).__name__}: {exc}"}


def data(resp: dict) -> Any:
    js = resp.get("json")
    return js.get("data") if isinstance(js, dict) else None


def success(resp: dict) -> bool:
    js = resp.get("json")
    return isinstance(js, dict) and js.get("success") is True


def balance_value(resp: dict) -> int | float | None:
    d = data(resp)
    if isinstance(d, dict):
        for key in ["balance", "quota", "credits"]:
            if isinstance(d.get(key), (int, float)):
                return d[key]
    return None


def find_task_id(obj: Any) -> str | None:
    if isinstance(obj, dict):
        for key in ["task_id", "taskId", "id"]:
            if isinstance(obj.get(key), (str, int)):
                return str(obj[key])
        for value in obj.values():
            found = find_task_id(value)
            if found:
                return found
    if isinstance(obj, list):
        for value in obj:
            found = find_task_id(value)
            if found:
                return found
    return None


def status_from(obj: Any) -> str | None:
    if isinstance(obj, dict):
        d = obj.get("data")
        if isinstance(d, dict):
            return d.get("status") or d.get("state")
        return obj.get("status") or obj.get("state")
    return None


def quota_from(obj: Any) -> Any:
    if isinstance(obj, dict):
        d = obj.get("data")
        if isinstance(d, dict):
            for key in ["quota", "estimated_quota", "cost", "charged_quota"]:
                if key in d:
                    return d[key]
        for key in ["quota", "estimated_quota", "cost", "charged_quota"]:
            if key in obj:
                return obj[key]
    return None


def find_urls(obj: Any) -> list[str]:
    urls: list[str] = []

    def walk(x: Any) -> None:
        if isinstance(x, str) and x.startswith("http"):
            urls.append(x)
        elif isinstance(x, dict):
            for key, value in x.items():
                if key.lower() in {"token", "billing_token", "authorization", "api_key"}:
                    continue
                walk(value)
        elif isinstance(x, list):
            for value in x:
                walk(value)

    walk(obj)
    return urls


def get_balance(client: Client, report: dict, label: str) -> int | float | None:
    resp = client.request("GET", "/v1/agent/balance", auth=True)
    if resp.get("http") == 404:
        resp = client.request("GET", "/v1/agent/credits", auth=True)
    report["steps"][label] = resp
    return balance_value(resp)


def recharge(client: Client, report: dict, amount: int | None) -> int | float | None:
    before = get_balance(client, report, "recharge_balance_before")
    payload: dict[str, Any] = {"tier": "gems_100", "return_url": client.base}
    if amount is not None:
        payload.update({"agent_id": "mangou-agent", "amount": amount})
    resp = client.request("POST", "/v1/agent/recharge-qr", body=payload, auth=True)
    d = data(resp) if isinstance(data(resp), dict) else {}
    qr_url = d.get("qr_url") if isinstance(d, dict) else None
    payment_url = d.get("payment_url") if isinstance(d, dict) else None
    qr = client.request("GET", qr_url, accept="image/svg+xml") if qr_url else {"skipped": "qr_url missing"}
    pay1 = client.request("GET", payment_url) if payment_url else {"skipped": "payment_url missing"}
    after_first = get_balance(client, report, "recharge_balance_after_first_open")
    pay2 = client.request("GET", payment_url) if payment_url else {"skipped": "payment_url missing"}
    after_second = get_balance(client, report, "recharge_balance_after_second_open")
    result = {
        "request": payload,
        "response": resp,
        "qr_get": {"http": qr.get("http"), "content_type": qr.get("content_type"), "bytes": qr.get("bytes"), "is_svg": "image/svg+xml" in (qr.get("content_type") or "")},
        "payment_first": {"http": pay1.get("http"), "content_type": pay1.get("content_type"), "text_head": (pay1.get("text") or "")[:500]},
        "payment_second": {"http": pay2.get("http"), "content_type": pay2.get("content_type"), "text_head": (pay2.get("text") or "")[:500]},
        "balance_before": before,
        "balance_after_first": after_first,
        "balance_after_second": after_second,
        "delta_first": after_first - before if isinstance(after_first, (int, float)) and isinstance(before, (int, float)) else None,
        "delta_second": after_second - after_first if isinstance(after_second, (int, float)) and isinstance(after_first, (int, float)) else None,
    }
    report["steps"].setdefault("recharges", []).append(result)
    return after_second


def submit_and_poll(client: Client, payload: dict, max_wait: int) -> dict:
    submit = client.request("POST", "/v1/agent/tasks", body=payload, auth=True, timeout=180)
    task_id = find_task_id(submit.get("json"))
    result = {"request": payload, "submit": submit, "task_id": task_id, "polls": [], "final_status": None, "result_url": None, "quota": quota_from(submit.get("json"))}
    if not task_id:
        return result
    start = time.time()
    delay = 5
    while time.time() - start < max_wait:
        time.sleep(delay)
        poll = client.request("GET", f"/v1/agent/tasks/{task_id}", auth=True, timeout=180)
        st = status_from(poll.get("json"))
        urls = find_urls(poll.get("json"))
        quota = quota_from(poll.get("json"))
        if urls:
            result["result_url"] = urls[0]
        if quota is not None:
            result["quota"] = quota
        result["polls"].append({"http": poll.get("http"), "status": st, "quota": quota, "urls": urls, "json": poll.get("json"), "text_head": (poll.get("text") or "")[:500]})
        if str(st).lower() in TERMINAL:
            result["final_status"] = st
            break
        delay = min(30, delay + 5)
    if result["final_status"] is None:
        result["final_status"] = "poll_timeout"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=os.environ.get("MANGOU_NEWAPI_BASE", DEFAULT_BASE))
    parser.add_argument("--out", default=os.environ.get("MANGOU_NEWAPI_TEST_RESULT", "/tmp/mangou_newapi_gateway_result.json"))
    parser.add_argument("--min-balance", type=int, default=0)
    parser.add_argument("--recharge-amount", type=int, default=None)
    parser.add_argument("--submit-image", action="store_true")
    parser.add_argument("--submit-video", action="store_true")
    parser.add_argument("--image-wait", type=int, default=900)
    parser.add_argument("--video-wait", type=int, default=1500)
    args = parser.parse_args()

    load_env()
    token = os.environ.get("BILLING_TOKEN", "")
    client = Client(args.base, token)
    report: dict[str, Any] = {"base": client.base, "token_present": bool(token), "token_length": len(token) if token else 0, "steps": {}}

    skill = client.request("GET", "/skills/mangou-newapi/SKILL.md")
    skill_text = skill.get("text") or ""
    report["steps"]["skill"] = {"http": skill.get("http"), "content_type": skill.get("content_type"), "bytes": skill.get("bytes"), "contains": {s: s in skill_text for s in ["/v1/agent/recharge-qr", "/v1/agent/balance", "qr_url", "payment_url"]}}
    report["steps"]["auth_check"] = client.request("GET", "/v1/agent/auth/check", auth=True)
    balance = get_balance(client, report, "balance_initial")

    if args.min_balance and (not isinstance(balance, (int, float)) or balance < args.min_balance):
        balance = recharge(client, report, args.recharge_amount or args.min_balance)

    if args.submit_image:
        image_payload = {
            "type": "image",
            "provider": "bltai",
            "model": "gpt-image-2",
            "prompt": "A mango robot checking official pricing tables, no text.",
            "params": {"quality": "medium", "image_size": "1024x1024", "response_format": "url"},
        }
        report["steps"]["image_task"] = submit_and_poll(client, image_payload, args.image_wait)
        get_balance(client, report, "balance_after_image")

    if args.submit_video:
        video_payload = {
            "type": "video",
            "provider": "kie",
            "model": "doubao-seedance-2-0-fast-260128",
            "prompt": "A mango robot flipping through a storyboard, cinematic, no text.",
            "params": {"duration": "5", "resolution": "720p", "quality": "720p"},
        }
        report["steps"]["video_task"] = submit_and_poll(client, video_payload, args.video_wait)
        get_balance(client, report, "balance_after_video")

    report["summary"] = {
        "auth_http": report["steps"]["auth_check"].get("http"),
        "auth_success": success(report["steps"]["auth_check"]),
        "balance_initial": balance_value(report["steps"].get("balance_initial", {})),
        "image_task_id": report["steps"].get("image_task", {}).get("task_id"),
        "image_status": report["steps"].get("image_task", {}).get("final_status"),
        "image_result_url": report["steps"].get("image_task", {}).get("result_url"),
        "image_quota": report["steps"].get("image_task", {}).get("quota"),
        "video_task_id": report["steps"].get("video_task", {}).get("task_id"),
        "video_status": report["steps"].get("video_task", {}).get("final_status"),
        "video_result_url": report["steps"].get("video_task", {}).get("result_url"),
        "video_quota": report["steps"].get("video_task", {}).get("quota"),
    }

    out = Path(args.out)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({"saved": str(out), "summary": report["summary"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
