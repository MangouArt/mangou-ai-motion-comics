from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class NewAPIAgentDocsTests(unittest.TestCase):
    def test_provider_doc_records_recharge_and_official_pricing_models(self) -> None:
        text = (ROOT / "references" / "provider-mangou-newapi.md").read_text(encoding="utf-8")
        for required in [
            "/v1/agent/recharge-qr",
            "/v1/agent/balance",
            "qr_url",
            "payment_url",
            "bltai",
            "gpt-image-2",
            "doubao-seedance-2-0-fast-260128",
            '"quality": "720p"',
            "15840",
            "210990",
        ]:
            self.assertIn(required, text)

    def test_smoke_script_keeps_video_quality_required_by_newapi(self) -> None:
        text = (ROOT / "scripts" / "newapi-gateway-smoke-test.py").read_text(encoding="utf-8")
        self.assertIn('"model": "doubao-seedance-2-0-fast-260128"', text)
        self.assertIn('"quality": "720p"', text)
        self.assertIn('"model": "gpt-image-2"', text)
        self.assertIn("[REDACTED_TOKEN]", text)


if __name__ == "__main__":
    unittest.main()
