from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mangou_skill.project_docs import load_feishu_doc_link, save_feishu_doc_link


class ProjectDocsTests(unittest.TestCase):
    def test_save_and_load_feishu_doc_link(self) -> None:
        with tempfile.TemporaryDirectory(prefix="mangou-doc-link-") as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            (project / "project.json").write_text('{"id":"project"}\n', encoding="utf-8")

            saved = save_feishu_doc_link(
                project,
                document_id="DOC123",
                url="https://example.feishu.cn/docx/DOC123",
                title="主文档",
            )
            loaded = load_feishu_doc_link(project)

            self.assertEqual(saved["document_id"], "DOC123")
            self.assertEqual(loaded["url"], "https://example.feishu.cn/docx/DOC123")
            self.assertTrue((project / "feishu_doc.json").exists())


if __name__ == "__main__":
    unittest.main()
