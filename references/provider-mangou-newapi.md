# Mangou NewAPI Agent Gateway

Use when asked to call the hosted Mangou NewAPI Agent Skill:

- `https://mangou-newapi.zeabur.app/skills/mangou-newapi/SKILL.md`

Always download/read the remote `SKILL.md` before calling the API. The hosted contract can change independently of this repository.

## Authentication

1. If `BILLING_TOKEN` already exists, verify it before any paid task:
   ```bash
   curl -sS "$BASE/v1/agent/auth/check" \
     -H "Authorization: Bearer ${BILLING_TOKEN}"
   ```
2. If no usable token exists, request an email code:
   ```bash
   curl -sS -X POST "$BASE/v1/agents/register/email-code" \
     -H 'Content-Type: application/json' \
     --data '{"email":"USER_EMAIL"}'
   ```
3. Register with explicit agent id:
   ```bash
   curl -sS -X POST "$BASE/v1/agents/register" \
     -H 'Content-Type: application/json' \
     --data '{"email":"USER_EMAIL","verification_code":"CODE","agent_id":"mangou-agent"}'
   ```
4. Store the returned full `billing_token` as `BILLING_TOKEN`. Do not print it.

All agent API calls must include:

```http
Authorization: Bearer ${BILLING_TOKEN}
```

## Balance and demo recharge

Check balance before task submission:

```bash
curl -sS "$BASE/v1/agent/balance" \
  -H "Authorization: Bearer ${BILLING_TOKEN}"
```

If the response says quota/balance is insufficient, use the demo recharge QR flow:

```bash
curl -sS -X POST "$BASE/v1/agent/recharge-qr" \
  -H "Authorization: Bearer ${BILLING_TOKEN}" \
  -H 'Content-Type: application/json' \
  --data '{"tier":"gems_100","return_url":"https://mangou-newapi.zeabur.app"}'
```

The response should include:

- `qr_url`
- `payment_url`
- `payment_id`
- `amount`
- `currency`

Validation flow:

1. `GET qr_url` and confirm `Content-Type: image/svg+xml`.
2. `GET payment_url` to simulate the user opening/scanning the demo payment page.
3. Recheck `/v1/agent/balance` and confirm the balance increased.
4. Open the same `payment_url` again and confirm the balance does not increase a second time.

Observed 2026-05-05: demo payments are idempotent. Reopening the same `payment_url` returns paid/completed but does not double-credit the account.

## Image task: BLTAI GPT Image 2

```json
{
  "type": "image",
  "provider": "bltai",
  "model": "gpt-image-2",
  "prompt": "A mango robot checking official pricing tables, no text.",
  "params": {
    "quality": "medium",
    "image_size": "1024x1024",
    "response_format": "url"
  }
}
```

Observed 2026-05-05:

- `bltai` / `gpt-image-2` / `quality: medium` / `1024x1024` submitted successfully.
- Estimated and final quota were `15840` credits.
- Polling `/v1/agent/tasks/{task_id}` returned `status: completed` and a `result_url`.

## Video task: KIE Seedance 2.0

The requested official KIE model is:

- `doubao-seedance-2-0-fast-260128`

Minimum working payload observed 2026-05-05:

```json
{
  "type": "video",
  "provider": "kie",
  "model": "doubao-seedance-2-0-fast-260128",
  "prompt": "A mango robot flipping through a storyboard, cinematic, no text.",
  "params": {
    "duration": "5",
    "resolution": "720p",
    "quality": "720p"
  }
}
```

Pitfalls observed 2026-05-05:

- Omitting `params.quality` returned: `kie submit failed: Video quality cannot be empty`.
- Using `quality: "standard"` returned: `pricing multiplier for pricing_tier=doubao-seedance-2-0-fast-260128|with_video_input|standard is not configured`.
- Using `quality: "720p"` submitted and completed successfully.
- Estimated and final quota were `210990` credits for 720p / 5s.

## Task polling

After `POST /v1/agent/tasks`, inspect the JSON body. HTTP `200` is not enough: require `success: true` and a returned `task_id` before polling.

Poll until terminal status:

```bash
curl -sS "$BASE/v1/agent/tasks/${TASK_ID}" \
  -H "Authorization: Bearer ${BILLING_TOKEN}"
```

Terminal statuses include `completed`, `failed`, `error`, `cancelled`, and `timeout`.

## Security

- Never print or commit the full `BILLING_TOKEN`, provider keys, email verification codes, or GitHub tokens.
- Treat raw registration responses as local secret material; store them only in protected local paths if needed.
- Final reports should include HTTP status, `success`, balance, quota, task id, status, and result URL, but no secrets.
