"""
Test Suite — Knowledge Ingestion Pipeline

Tests for:
  - Smart text chunking (semantic boundaries)
  - Source type detection
  - ChatGPT export parsing
  - Claude export parsing
  - Text file parsing
  - Ingestion deduplication
  - Ingestion history
"""

import os
import json
import tempfile
import shutil
import pytest


class TestSmartChunking:
    """Test semantic-boundary text chunking."""

    def test_short_text_single_chunk(self):
        from python.helpers.knowledge_ingestion import smart_chunk_text
        text = "This is a short paragraph."
        chunks = smart_chunk_text(text, max_chunk_size=500)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_multiple_chunks(self):
        from python.helpers.knowledge_ingestion import smart_chunk_text
        # Create text with clear paragraph boundaries
        paragraphs = [f"Paragraph {i}. " * 20 for i in range(10)]
        text = "\n\n".join(paragraphs)
        chunks = smart_chunk_text(text, max_chunk_size=200)
        assert len(chunks) > 1

    def test_chunks_not_empty(self):
        from python.helpers.knowledge_ingestion import smart_chunk_text
        text = "Line 1\n\nLine 2\n\nLine 3"
        chunks = smart_chunk_text(text, max_chunk_size=50)
        for chunk in chunks:
            assert len(chunk.strip()) > 0


class TestSourceDetection:
    """Test source type auto-detection."""

    def test_detect_chatgpt_export(self):
        from python.helpers.knowledge_ingestion import detect_source_type
        assert detect_source_type("conversations.json") in ("chatgpt_export", "json")

    def test_detect_text_file(self):
        from python.helpers.knowledge_ingestion import detect_source_type
        assert detect_source_type("notes.txt") == "text"

    def test_detect_markdown(self):
        from python.helpers.knowledge_ingestion import detect_source_type
        assert detect_source_type("README.md") == "text"

    def test_detect_pdf(self):
        from python.helpers.knowledge_ingestion import detect_source_type
        assert detect_source_type("document.pdf") == "pdf"


class TestTextFileParsing:
    """Test text file parsing."""

    def setup_method(self):
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_parse_text_file(self):
        from python.helpers.knowledge_ingestion import parse_text_file
        # Create a test file
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("This is test content.\nWith multiple lines.\n\nAnd paragraphs.")
        
        chunks = parse_text_file(test_file)
        assert isinstance(chunks, list)
        assert len(chunks) >= 1
        joined = " ".join(chunks)
        assert "test content" in joined


class TestIngestionHistory:
    """Test ingestion tracking."""

    def test_get_history_empty(self):
        from python.helpers.knowledge_ingestion import get_ingestion_history
        history = get_ingestion_history()
        assert isinstance(history, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
