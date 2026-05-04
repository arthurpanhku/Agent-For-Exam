"""Unit tests for DocumentService._clean_base64_text."""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


@pytest.fixture
def svc(tmp_path):
    """Return a DocumentService with heavy dependencies mocked out."""
    with (
        patch("app.services.document_service.ConversationService"),
        patch("app.services.document_service.LightRAGService"),
        patch("app.services.document_service.MindMapService"),
        patch("app.services.document_service.FileManager"),
        patch("app.services.document_service.DocumentParser"),
    ):
        from app.services.document_service import DocumentService
        service = DocumentService.__new__(DocumentService)
        # minimal attribute so _clean_base64_text works
        return service


class TestCleanBase64Text:
    def test_replaces_standalone_base64(self, svc, tmp_path):
        b64 = "A" * 60  # valid base64-ish
        text = f"before {b64} after"
        out_file = tmp_path / "base64.json"
        cleaned, mapping = svc._clean_base64_text(text, out_file)
        assert b64 not in cleaned
        assert "[BASE64_1]" in cleaned
        assert "1" in mapping
        assert mapping["1"] == b64

    def test_latexit_tag_replaced(self, svc, tmp_path):
        b64_content = "Z" * 70
        text = f'<latexit sha1_base64="abc123">some {b64_content}</latexit>'
        out_file = tmp_path / "base64.json"
        cleaned, mapping = svc._clean_base64_text(text, out_file)
        assert "<latexit" not in cleaned
        assert "BASE64_" in cleaned
        assert len(mapping) >= 1

    def test_short_strings_not_replaced(self, svc, tmp_path):
        text = "word1 word2 abc123"
        out_file = tmp_path / "base64.json"
        cleaned, mapping = svc._clean_base64_text(text, out_file)
        assert cleaned == text
        assert mapping == {}

    def test_existing_map_extended(self, svc, tmp_path):
        out_file = tmp_path / "base64.json"
        out_file.write_text(json.dumps({"1": "existing"}), encoding="utf-8")
        b64 = "B" * 55
        text = f"text {b64} end"
        cleaned, mapping = svc._clean_base64_text(text, out_file)
        assert mapping.get("1") == "existing"
        assert "2" in mapping  # new entry starts at next_index = 2

    def test_output_file_written(self, svc, tmp_path):
        out_file = tmp_path / "base64.json"
        b64 = "C" * 60
        svc._clean_base64_text(f"x {b64} y", out_file)
        assert out_file.exists()
        data = json.loads(out_file.read_text())
        assert "1" in data

    def test_no_output_file_when_nothing_replaced(self, svc, tmp_path):
        out_file = tmp_path / "base64.json"
        svc._clean_base64_text("short text only", out_file)
        assert not out_file.exists()
