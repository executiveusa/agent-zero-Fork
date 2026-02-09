"""
Test Suite — Export Pipeline

Tests for:
  - Knowledge export (JSON, CSV, Markdown)
  - Cost export
  - Audit export
  - Full backup
  - Export listing
"""

import os
import json
import tempfile
import shutil
import pytest


class TestExportPipeline:
    """Test export pipeline functions."""

    def test_knowledge_export_json(self):
        from python.helpers.export_pipeline import export_knowledge
        job = export_knowledge("json")
        assert job.status == "completed"
        assert job.output_path is not None
        assert job.output_path.endswith(".json")

    def test_knowledge_export_csv(self):
        from python.helpers.export_pipeline import export_knowledge
        job = export_knowledge("csv")
        assert job.status == "completed"
        assert job.output_path is not None

    def test_knowledge_export_markdown(self):
        from python.helpers.export_pipeline import export_knowledge
        job = export_knowledge("markdown")
        assert job.status == "completed"
        assert job.output_path is not None
        assert job.output_path.endswith(".md")

    def test_costs_export(self):
        from python.helpers.export_pipeline import export_costs
        job = export_costs(days=7, format="json")
        assert job.status == "completed"
        assert job.output_path is not None

    def test_audit_export(self):
        from python.helpers.export_pipeline import export_audit
        job = export_audit(days=3, format="json")
        assert job.status == "completed"

    def test_full_backup(self):
        from python.helpers.export_pipeline import export_full_backup
        job = export_full_backup()
        assert job.status == "completed"
        assert "manifest" in job.output_path

    def test_list_exports(self):
        from python.helpers.export_pipeline import list_exports, export_knowledge
        # Create at least one export
        export_knowledge("json")
        exports = list_exports()
        assert isinstance(exports, list)
        assert len(exports) >= 1
        # Check format
        for exp in exports:
            assert "filename" in exp
            assert "size_bytes" in exp

    def test_export_job_fields(self):
        from python.helpers.export_pipeline import ExportJob
        job = ExportJob(
            job_id="test_job",
            export_type="knowledge",
            format="json",
            status="pending",
            created_at="2025-01-01T00:00:00Z",
        )
        assert job.job_id == "test_job"
        assert job.error is None
        assert job.record_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
