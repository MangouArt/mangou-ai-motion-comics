from __future__ import annotations

import unittest
from unittest.mock import patch

from mangou_skill.http_utils import HttpResponse
from mangou_skill.providers import AnyIntProvider, BLTAIProvider, EvolinkProvider, get_provider, resolve_provider_env


class ProviderTests(unittest.TestCase):
    def test_registry_returns_known_provider(self) -> None:
        provider = get_provider("bltai")
        self.assertEqual(provider.id, "bltai")

    def test_bltai_build_image_payload(self) -> None:
        provider = BLTAIProvider()
        payload = provider.build_payload(
            "images",
            {
                "prompt": "hero portrait",
                "model": "nano-banana",
                "image": ["https://example.com/ref.png"],
                "aspect_ratio": "16:9",
            },
        )
        self.assertEqual(payload["prompt"], "hero portrait")
        self.assertEqual(payload["image"], ["https://example.com/ref.png"])
        self.assertEqual(payload["response_format"], "url")

    def test_bltai_build_gpt_image_2_payload(self) -> None:
        provider = BLTAIProvider()
        payload = provider.build_payload(
            "images",
            {
                "prompt": "A cute mango-shaped robot assistant, no text.",
                "model": "gpt-image-2",
                "aspect_ratio": "16:9",
                "image_size": "1K",
            },
        )
        self.assertEqual(payload["model"], "gpt-image-2")
        self.assertEqual(payload["response_format"], "url")
        self.assertEqual(payload["aspect_ratio"], "16:9")
        self.assertEqual(payload["image_size"], "1K")

    def test_evolink_video_payload_keeps_media_lists(self) -> None:
        provider = EvolinkProvider()
        payload = provider.build_payload(
            "videos",
            {
                "prompt": "camera move",
                "model": "seedance-2.0-reference-to-video",
                "image_urls": ["https://example.com/a.png"],
                "video_urls": ["https://example.com/b.mp4"],
            },
        )
        self.assertEqual(payload["image_urls"], ["https://example.com/a.png"])
        self.assertEqual(payload["video_urls"], ["https://example.com/b.mp4"])

    def test_resolve_provider_env_prefers_runtime_env(self) -> None:
        provider = BLTAIProvider()
        api_key, base_url = resolve_provider_env(
            provider,
            {"BLTAI_API_KEY": "k", "BLTAI_BASE_URL": "https://api.example.com/v1/"},
        )
        self.assertEqual(api_key, "k")
        self.assertEqual(base_url, "https://api.example.com")

    def test_bltai_submit_uploads_data_url_and_tolerates_dirty_json(self) -> None:
        provider = BLTAIProvider()
        responses = [
            HttpResponse(
                status=200,
                headers={},
                body=b'{"data":{"url":"https://cdn.bltcy.ai/uploads/ref-1.png"}}\n{"error":"trailing noise"}',
            ),
            HttpResponse(
                status=200,
                headers={},
                body=b'{"id":"task-after-upload"}',
            ),
        ]

        with patch("mangou_skill.providers.fetch_with_retry", side_effect=responses) as mocked:
            task_id = provider.submit(
                base_url="https://api.bltcy.ai",
                api_key="test-key",
                scope="images",
                payload={
                    "model": "gemini-3.1-flash-image-preview",
                    "prompt": "A comic style hero",
                    "response_format": "url",
                    "image": ["data:image/png;base64,aaaa"],
                },
            )

        self.assertEqual(task_id, "task-after-upload")
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(mocked.call_args_list[1].args[0], "https://api.bltcy.ai/v1/images/generations?async=true")
        self.assertIn("https://cdn.bltcy.ai/uploads/ref-1.png", mocked.call_args_list[1].kwargs["data"].decode("utf-8"))

    def test_bltai_poll_treats_not_start_as_pending(self) -> None:
        provider = BLTAIProvider()
        responses = [
            HttpResponse(status=200, headers={}, body=b'{"status":"NOT_START"}'),
            HttpResponse(status=200, headers={}, body=b'{"status":"SUCCESS","data":[{"url":"https://example.com/out.png"}]}'),
        ]

        with patch("mangou_skill.providers.fetch_with_retry", side_effect=responses) as mocked:
            with patch("mangou_skill.providers.sleep") as sleep_mock:
                result = provider.poll(
                    base_url="https://api.bltcy.ai",
                    api_key="test-key",
                    scope="images",
                    task_id="task-image",
                )

        self.assertEqual(mocked.call_count, 2)
        sleep_mock.assert_called_once()
        self.assertEqual(provider.extract_outputs("images", result), ["https://example.com/out.png"])

    def test_anyint_submit_uploads_data_url_reference(self) -> None:
        provider = AnyIntProvider()
        responses = [
            HttpResponse(
                status=200,
                headers={},
                body=b'{"success":true,"data":{"url":"https://storage.example.com/ref.jpg"}}',
            ),
            HttpResponse(
                status=200,
                headers={},
                body=b'{"id":"task_123","task_id":"task_123","status":"queued"}',
            ),
        ]

        with patch("mangou_skill.providers.fetch_with_retry", side_effect=responses) as mocked:
            task_id = provider.submit(
                base_url="https://gateway.api.anyint.ai",
                api_key="test-key",
                scope="videos",
                payload={
                    "model": "doubao-seedance-2-0-260128",
                    "content": [
                        {"type": "text", "text": "cat"},
                        {"type": "image_url", "role": "first_frame", "image_url": {"url": "data:image/png;base64,aaaa"}},
                    ],
                    "duration": 5,
                    "ratio": "16:9",
                    "resolution": "720p",
                    "watermark": False,
                    "generate_audio": True,
                },
            )

        self.assertEqual(task_id, "task_123")
        self.assertEqual(mocked.call_args_list[1].args[0], "https://gateway.api.anyint.ai/doubao/video/generations")
        self.assertIn("https://storage.example.com/ref.jpg", mocked.call_args_list[1].kwargs["data"].decode("utf-8"))

    def test_evolink_submit_uploads_image_before_image_generation(self) -> None:
        provider = EvolinkProvider()
        responses = [
            HttpResponse(
                status=200,
                headers={},
                body=b'{"success":true,"data":{"file_url":"https://files.evolink.ai/mangou-uploads/reference.png"}}',
            ),
            HttpResponse(
                status=200,
                headers={},
                body=b'{"id":"task-image-123"}',
            ),
        ]

        with patch("mangou_skill.providers.fetch_with_retry", side_effect=responses) as mocked:
            task_id = provider.submit(
                base_url="https://api.evolink.ai",
                api_key="test-key",
                scope="images",
                payload={
                    "model": "gemini-3.1-flash-image-preview",
                    "prompt": "一只猫在草地上玩耍",
                    "size": "16:9",
                    "quality": "2K",
                    "image_urls": ["data:image/png;base64,ZmFrZQ=="],
                },
            )

        self.assertEqual(task_id, "task-image-123")
        self.assertEqual(mocked.call_args_list[1].args[0], "https://api.evolink.ai/v1/images/generations")
        self.assertIn("https://files.evolink.ai/mangou-uploads/reference.png", mocked.call_args_list[1].kwargs["data"].decode("utf-8"))

    def test_evolink_poll_and_extract_outputs(self) -> None:
        provider = EvolinkProvider()
        with patch(
            "mangou_skill.providers.fetch_with_retry",
            return_value=HttpResponse(
                status=200,
                headers={},
                body=b'{"id":"task-unified-123","status":"completed","results":[{"url":"https://example.com/image-1.png"},{"image_url":"https://example.com/image-2.png"}]}',
            ),
        ) as mocked:
            result = provider.poll(
                base_url="https://api.evolink.ai",
                api_key="test-key",
                scope="images",
                task_id="task-unified-123",
            )

        self.assertEqual(mocked.call_args.args[0], "https://api.evolink.ai/v1/tasks/task-unified-123")
        self.assertEqual(
            provider.extract_outputs("images", result),
            ["https://example.com/image-1.png", "https://example.com/image-2.png"],
        )


if __name__ == "__main__":
    unittest.main()
