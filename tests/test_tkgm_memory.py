"""
Test Suite — TKGM Memory System

Tests for:
  - TemporalTag creation and decay computation
  - ByteRoverAtomic read/write
  - KnowledgeTriple creation
  - TKGMMemory insert/search operations
  - Multi-hop graph traversal
  - Domain enumeration
"""

import os
import json
import time
import tempfile
import shutil
import pytest
from datetime import datetime, timezone, timedelta


# ─── ByteRoverAtomic Tests ──────────────────────────────────

class TestByteRoverAtomic:
    """Test atomic read/write persistence."""

    def setup_method(self):
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_write_and_read(self):
        from python.helpers.tkgm_memory import ByteRoverAtomic
        path = os.path.join(self.test_dir, "test.json")
        data = {"key": "value", "number": 42}
        ByteRoverAtomic.write(path, data)
        result = ByteRoverAtomic.read(path)
        assert result == data

    def test_read_nonexistent(self):
        from python.helpers.tkgm_memory import ByteRoverAtomic
        path = os.path.join(self.test_dir, "nonexistent.json")
        result = ByteRoverAtomic.read(path)
        assert result is None

    def test_write_creates_directories(self):
        from python.helpers.tkgm_memory import ByteRoverAtomic
        path = os.path.join(self.test_dir, "sub", "dir", "test.json")
        data = {"nested": True}
        ByteRoverAtomic.write(path, data)
        assert os.path.exists(path)
        result = ByteRoverAtomic.read(path)
        assert result == data

    def test_atomic_no_partial_writes(self):
        from python.helpers.tkgm_memory import ByteRoverAtomic
        path = os.path.join(self.test_dir, "atomic.json")
        # Write initial data
        ByteRoverAtomic.write(path, {"version": 1})
        # Overwrite
        ByteRoverAtomic.write(path, {"version": 2})
        result = ByteRoverAtomic.read(path)
        assert result["version"] == 2
        # No .tmp file should remain
        assert not os.path.exists(path + ".tmp")


# ─── TemporalTag Tests ──────────────────────────────────────

class TestTemporalTag:
    """Test temporal metadata and decay scoring."""

    def test_creation(self):
        from python.helpers.tkgm_memory import TemporalTag
        tag = TemporalTag()
        assert tag.access_count == 0
        assert tag.decay_rate == 0.01
        assert tag.created_at is not None

    def test_decay_score_starts_high(self):
        from python.helpers.tkgm_memory import TemporalTag
        tag = TemporalTag()
        score = tag.compute_decay_score()
        # Just created, score should be very close to 1.0
        assert score > 0.99

    def test_decay_score_decreases_over_time(self):
        from python.helpers.tkgm_memory import TemporalTag
        # Simulate a tag created 30 days ago
        old_time = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        tag = TemporalTag(created_at=old_time, last_accessed=old_time)
        score = tag.compute_decay_score()
        # Score should be less than 1.0 after 30 days
        assert score < 1.0
        assert score > 0.0

    def test_high_decay_rate_faster_decay(self):
        from python.helpers.tkgm_memory import TemporalTag
        old_time = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        slow = TemporalTag(created_at=old_time, decay_rate=0.01)
        fast = TemporalTag(created_at=old_time, decay_rate=0.1)
        assert fast.compute_decay_score() < slow.compute_decay_score()


# ─── KnowledgeTriple Tests ───────────────────────────────────

class TestKnowledgeTriple:
    """Test knowledge graph triple operations."""

    def test_creation(self):
        from python.helpers.tkgm_memory import KnowledgeTriple
        triple = KnowledgeTriple(
            subject="Agent Zero",
            predicate="is_a",
            obj="AI Framework",
        )
        assert triple.subject == "Agent Zero"
        assert triple.predicate == "is_a"
        assert triple.obj == "AI Framework"
        assert triple.confidence == 1.0

    def test_to_dict(self):
        from python.helpers.tkgm_memory import KnowledgeTriple
        triple = KnowledgeTriple(
            subject="Python",
            predicate="used_for",
            obj="AI development",
            confidence=0.95,
        )
        d = triple.to_dict()
        assert d["subject"] == "Python"
        assert d["confidence"] == 0.95
        assert "created_at" in d


# ─── MemoryDomain Tests ─────────────────────────────────────

class TestMemoryDomain:
    """Test memory domain enumeration."""

    def test_all_domains_exist(self):
        from python.helpers.tkgm_memory import MemoryDomain
        expected = ["agent_zero", "client_projects", "agency_ops", "personal", "research", "codebase", "conversations"]
        for domain in expected:
            assert hasattr(MemoryDomain, domain.upper()), f"Missing domain: {domain}"

    def test_domain_values(self):
        from python.helpers.tkgm_memory import MemoryDomain
        assert MemoryDomain.AGENT_ZERO.value == "agent_zero"
        assert MemoryDomain.CLIENT_PROJECTS.value == "client_projects"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
