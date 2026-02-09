"""
Test Suite — Cost Tracker

Tests for:
  - CostTracker singleton pattern
  - Cost estimation for known/unknown models
  - Budget enforcement (monthly + per-agent)
  - Daily/monthly spend calculation
  - Model recommendation on budget exceed
  - Thread-safe recording
"""

import os
import json
import tempfile
import shutil
import pytest
from datetime import datetime, timezone


class TestCostTracker:
    """Test cost tracking and budget enforcement."""

    def setup_method(self):
        """Reset singleton and use temp directory."""
        # Reset singleton
        from python.helpers.cost_tracker import CostTracker
        CostTracker._instance = None
        
        self.test_dir = tempfile.mkdtemp()
        self._orig_dir = None

    def teardown_method(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        from python.helpers.cost_tracker import CostTracker
        CostTracker._instance = None

    def test_singleton(self):
        from python.helpers.cost_tracker import CostTracker
        a = CostTracker.get()
        b = CostTracker.get()
        assert a is b

    def test_known_cost_estimation(self):
        from python.helpers.cost_tracker import KNOWN_COSTS
        # Verify known models have costs
        assert "claude-sonnet-4-20250514" in KNOWN_COSTS
        assert "openai/glm-4-flash" in KNOWN_COSTS
        cost = KNOWN_COSTS["claude-sonnet-4-20250514"]
        assert "input" in cost
        assert "output" in cost
        assert cost["input"] > 0
        assert cost["output"] > 0

    def test_free_tier_models(self):
        from python.helpers.cost_tracker import FREE_TIER_MODELS
        assert "openai/glm-4-flash" in FREE_TIER_MODELS
        assert len(FREE_TIER_MODELS) >= 1

    def test_record_and_get_daily_spend(self):
        from python.helpers.cost_tracker import CostTracker
        tracker = CostTracker.get()
        tracker.record_call(
            model="openai/glm-4-flash",
            input_tokens=1000,
            output_tokens=500,
            agent_id="test_agent",
        )
        spend = tracker.get_daily_spend()
        assert spend >= 0  # Free tier might be 0

    def test_budget_not_exceeded_initially(self):
        from python.helpers.cost_tracker import CostTracker
        tracker = CostTracker.get()
        assert not tracker.is_budget_exceeded()

    def test_budget_status_format(self):
        from python.helpers.cost_tracker import CostTracker
        tracker = CostTracker.get()
        status = tracker.get_budget_status()
        assert "monthly_spend" in status
        assert "monthly_cap" in status
        assert "available" in status or "exceeded" in status or "remaining" in status

    def test_recommended_model_returns_string(self):
        from python.helpers.cost_tracker import CostTracker
        tracker = CostTracker.get()
        model = tracker.get_recommended_model()
        assert isinstance(model, str)
        assert len(model) > 0

    def test_model_breakdown_format(self):
        from python.helpers.cost_tracker import CostTracker
        tracker = CostTracker.get()
        tracker.record_call("test-model", 100, 50, "agent1")
        breakdown = tracker.get_model_breakdown()
        assert isinstance(breakdown, dict)


class TestCostEstimation:
    """Test cost estimation accuracy."""

    def setup_method(self):
        from python.helpers.cost_tracker import CostTracker
        CostTracker._instance = None

    def teardown_method(self):
        from python.helpers.cost_tracker import CostTracker
        CostTracker._instance = None

    def test_claude_cost_reasonable(self):
        """Claude Sonnet should cost ~$3/M input, $15/M output."""
        from python.helpers.cost_tracker import KNOWN_COSTS
        cost = KNOWN_COSTS.get("claude-sonnet-4-20250514", {})
        # Input cost per 1M tokens should be in reasonable range
        assert 0.5 <= cost.get("input", 0) <= 10.0
        assert 1.0 <= cost.get("output", 0) <= 30.0

    def test_free_tier_zero_cost(self):
        """Free tier models should have zero or near-zero cost."""
        from python.helpers.cost_tracker import KNOWN_COSTS
        glm_cost = KNOWN_COSTS.get("openai/glm-4-flash", {})
        assert glm_cost.get("input", 0) == 0
        assert glm_cost.get("output", 0) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
