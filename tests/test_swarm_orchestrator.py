"""
Test Suite — Swarm Orchestrator

Tests for:
  - Swarm creation and task management
  - SwarmTask lifecycle (pending → running → completed/failed)
  - Decomposition strategy detection
  - Progress tracking
  - Swarm serialization (to_dict / from_dict)
  - Registry loading from disk
"""

import os
import json
import tempfile
import shutil
import pytest
from datetime import datetime, timezone


class TestSwarmTask:
    """Test SwarmTask data model."""

    def test_creation(self):
        from python.tools.swarm_orchestrator import SwarmTask
        task = SwarmTask("t1", "Test task", agent_profile="developer")
        assert task.task_id == "t1"
        assert task.status == "pending"
        assert task.agent_profile == "developer"

    def test_to_dict(self):
        from python.tools.swarm_orchestrator import SwarmTask
        task = SwarmTask("t1", "Test task", model="gpt-4")
        d = task.to_dict()
        assert d["task_id"] == "t1"
        assert d["status"] == "pending"
        assert d["model"] == "gpt-4"

    def test_from_dict(self):
        from python.tools.swarm_orchestrator import SwarmTask
        data = {
            "task_id": "t2",
            "description": "Another task",
            "agent_profile": "researcher",
            "status": "completed",
            "result": "Done",
        }
        task = SwarmTask.from_dict(data)
        assert task.task_id == "t2"
        assert task.status == "completed"
        assert task.agent_profile == "researcher"

    def test_default_max_seconds(self):
        from python.tools.swarm_orchestrator import SwarmTask
        task = SwarmTask("t1", "Test")
        assert task.max_seconds == 300

    def test_retry_tracking(self):
        from python.tools.swarm_orchestrator import SwarmTask
        task = SwarmTask("t1", "Test")
        assert task.retries == 0
        assert task.max_retries == 2


class TestSwarm:
    """Test Swarm management."""

    def test_creation(self):
        from python.tools.swarm_orchestrator import Swarm
        swarm = Swarm("sw1", "Test Swarm", "Do something")
        assert swarm.swarm_id == "sw1"
        assert swarm.status == "created"
        assert len(swarm.tasks) == 0

    def test_add_task(self):
        from python.tools.swarm_orchestrator import Swarm
        swarm = Swarm("sw1", "Test", "Objective")
        task = swarm.add_task("Sub-task 1", agent_profile="developer")
        assert len(swarm.tasks) == 1
        assert task.task_id == "sw1_t0"
        assert task.agent_profile == "developer"

    def test_progress_tracking(self):
        from python.tools.swarm_orchestrator import Swarm
        swarm = Swarm("sw1", "Test", "Objective")
        swarm.add_task("Task 1")
        swarm.add_task("Task 2")
        swarm.add_task("Task 3")

        progress = swarm.progress
        assert progress["total"] == 3
        assert progress["pending"] == 3
        assert progress["percent"] == 0

        # Simulate completion
        swarm.tasks[0].status = "completed"
        swarm.tasks[1].status = "running"
        progress = swarm.progress
        assert progress["completed"] == 1
        assert progress["running"] == 1
        assert progress["pending"] == 1

    def test_to_dict_and_from_dict(self):
        from python.tools.swarm_orchestrator import Swarm
        swarm = Swarm("sw1", "Test Swarm", "Big objective")
        swarm.add_task("Task A", agent_profile="developer")
        swarm.add_task("Task B", agent_profile="researcher")
        swarm.status = "running"

        d = swarm.to_dict(include_results=True)
        assert d["swarm_id"] == "sw1"
        assert d["task_count"] == 2
        assert len(d["tasks"]) == 2

        # Reconstruct
        restored = Swarm.from_dict(d)
        assert restored.swarm_id == "sw1"
        assert len(restored.tasks) == 2
        assert restored.status == "running"

    def test_check_completion(self):
        from python.tools.swarm_orchestrator import Swarm
        swarm = Swarm("sw1", "Test", "Objective")
        swarm.add_task("Task 1")
        swarm.add_task("Task 2")

        swarm.tasks[0].status = "completed"
        swarm.tasks[1].status = "completed"
        swarm.check_completion()
        assert swarm.status == "completed"

    def test_check_completion_with_failures(self):
        from python.tools.swarm_orchestrator import Swarm
        swarm = Swarm("sw1", "Test", "Objective")
        swarm.add_task("Task 1")
        swarm.add_task("Task 2")

        swarm.tasks[0].status = "failed"
        swarm.tasks[1].status = "failed"
        swarm.check_completion()
        assert swarm.status == "failed"


class TestDecompositionStrategies:
    """Test strategy detection."""

    def test_code_review_detection(self):
        from python.tools.swarm_orchestrator import detect_strategy
        assert detect_strategy("review the authentication code") == "code_review"
        assert detect_strategy("security audit of the API") == "code_review"

    def test_project_finish_detection(self):
        from python.tools.swarm_orchestrator import detect_strategy
        assert detect_strategy("finish all remaining features") == "project_finish"
        assert detect_strategy("complete the MVP") == "project_finish"

    def test_research_detection(self):
        from python.tools.swarm_orchestrator import detect_strategy
        assert detect_strategy("research competitor pricing") == "research"
        assert detect_strategy("investigate the memory leak") == "research"

    def test_design_detection(self):
        from python.tools.swarm_orchestrator import detect_strategy
        assert detect_strategy("design the checkout UI") == "design"

    def test_deployment_detection(self):
        from python.tools.swarm_orchestrator import detect_strategy
        assert detect_strategy("deploy to production") == "deployment"

    def test_agency_detection(self):
        from python.tools.swarm_orchestrator import detect_strategy
        assert detect_strategy("find new agency leads") == "agency"
        assert detect_strategy("marketing campaign for clients") == "agency"

    def test_general_fallback(self):
        from python.tools.swarm_orchestrator import detect_strategy
        assert detect_strategy("random unclassifiable task") == "general"

    def test_all_strategies_have_tasks(self):
        from python.tools.swarm_orchestrator import DECOMPOSITION_STRATEGIES
        for name, tasks in DECOMPOSITION_STRATEGIES.items():
            assert len(tasks) > 0, f"Strategy '{name}' has no tasks"
            for task in tasks:
                assert "desc" in task, f"Task in '{name}' missing 'desc'"
                assert "profile" in task, f"Task in '{name}' missing 'profile'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
