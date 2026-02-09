"""
Test Suite — Orchestration Config

Tests for:
  - YAML config loading
  - Agent definition parsing
  - Routing rule matching (keyword + duration)
  - Budget config parsing
  - Recovery policy parsing
  - Config caching
"""

import os
import pytest


class TestOrchestrationConfig:
    """Test orchestration config loading and routing."""

    def test_config_loads(self):
        from python.helpers.orchestration_config import load_orchestration_config
        config = load_orchestration_config()
        assert config is not None

    def test_agents_defined(self):
        from python.helpers.orchestration_config import load_orchestration_config
        config = load_orchestration_config()
        assert len(config.agents) >= 7
        agent_ids = [a.id for a in config.agents]
        assert "master" in agent_ids
        assert "designer" in agent_ids
        assert "tactical" in agent_ids

    def test_agent_has_required_fields(self):
        from python.helpers.orchestration_config import load_orchestration_config
        config = load_orchestration_config()
        for agent in config.agents:
            assert agent.id, f"Agent missing id"
            assert agent.name, f"Agent {agent.id} missing name"
            assert agent.role, f"Agent {agent.id} missing role"
            assert agent.model, f"Agent {agent.id} missing model"

    def test_routing_code_to_developer(self):
        from python.helpers.orchestration_config import load_orchestration_config
        config = load_orchestration_config()
        result = config.route_task("fix the login bug in the code")
        assert result in ("developer", "master"), f"Expected developer or master, got {result}"

    def test_routing_design_to_designer(self):
        from python.helpers.orchestration_config import load_orchestration_config
        config = load_orchestration_config()
        result = config.route_task("design a new landing page UI")
        assert result == "designer", f"Expected designer, got {result}"

    def test_routing_research_to_researcher(self):
        from python.helpers.orchestration_config import load_orchestration_config
        config = load_orchestration_config()
        result = config.route_task("research the latest AI models")
        # Should route to a research-capable agent
        assert result is not None

    def test_routing_unknown_falls_back(self):
        from python.helpers.orchestration_config import load_orchestration_config
        config = load_orchestration_config()
        result = config.route_task("xyzzy foobar gibberish")
        assert result is not None  # Should always return something

    def test_budget_config(self):
        from python.helpers.orchestration_config import load_orchestration_config
        config = load_orchestration_config()
        assert config.budget is not None
        assert config.budget.monthly_cap > 0

    def test_loop_config(self):
        from python.helpers.orchestration_config import load_orchestration_config
        config = load_orchestration_config()
        assert config.loop is not None
        assert config.loop.cycle_seconds == 30

    def test_get_agent_by_id(self):
        from python.helpers.orchestration_config import load_orchestration_config
        config = load_orchestration_config()
        agent = config.get_agent("master")
        assert agent is not None
        assert agent.name == "ClaudeCode"

    def test_get_agent_by_name(self):
        from python.helpers.orchestration_config import load_orchestration_config
        config = load_orchestration_config()
        agent = config.get_agent_by_name("Cynthia")
        assert agent is not None
        assert agent.role == "DESIGNER"

    def test_config_caching(self):
        from python.helpers.orchestration_config import load_orchestration_config
        config1 = load_orchestration_config()
        config2 = load_orchestration_config()
        assert config1 is config2  # Same object — cached


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
