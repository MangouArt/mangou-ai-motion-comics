# Mangou NewAPI Agent Gateway Smoke Test Notes

Use `scripts/newapi-gateway-smoke-test.py` to run the hosted agent gateway without leaking secrets.

The script:

1. Downloads `https://mangou-newapi.zeabur.app/skills/mangou-newapi/SKILL.md`.
2. Loads `BILLING_TOKEN` from the environment or `/opt/data/.env`.
3. Calls `/v1/agent/auth/check` and `/v1/agent/balance`.
4. If balance is below the requested threshold, calls `/v1/agent/recharge-qr`, verifies the QR SVG, opens `payment_url`, and checks idempotency by opening it twice.
5. Optionally submits the BLTAI `gpt-image-2` image task and KIE `doubao-seedance-2-0-fast-260128` video task.
6. Polls tasks until terminal status.
7. Writes a redacted JSON report.

Example:

```bash
python3 scripts/newapi-gateway-smoke-test.py \
  --submit-image \
  --submit-video \
  --min-balance 230000 \
  --out /tmp/mangou_newapi_report.json
```

Do not submit video unless the caller explicitly authorizes a real video task. The observed KIE 720p/5s quota is high (`210990` credits).

## Observed 2026-05-05 production behavior

- Auth check succeeded with `agent_id: mangou-agent`.
- `/v1/agent/balance` returned `balance`, `quota`, and `currency: credits`.
- `/v1/agent/recharge-qr` returned `qr_url` and `payment_url`.
- `GET qr_url` returned `image/svg+xml`.
- Opening `payment_url` credited the balance.
- Reopening the same `payment_url` did not credit the balance again.
- BLTAI `gpt-image-2` image task completed with final quota `15840` credits.
- KIE `doubao-seedance-2-0-fast-260128` video task required `params.quality: "720p"` and completed with final quota `210990` credits.
