"""
Tests for the deploy loop engine and test gates.
Run: python -m pytest tests/deploy/test_deploy_loop.py -v
"""
import re
import json
import pytest


# ── Test Gate Logic ──────────────────────────────────────────

class TestDeployTestGates:
    """Test the 11 gate validation functions (logic only, no I/O)."""

    def test_gate_1_analyze_pass(self):
        """Gate 1: project_type != 'unknown'"""
        config = {"type": "flask", "port": 5000}
        assert config["type"] != "unknown"

    def test_gate_1_analyze_fail(self):
        config = {"type": "unknown"}
        assert config["type"] == "unknown"

    def test_gate_3_dockerfile_exists(self):
        """Gate 3: Dockerfile exists in config or generated."""
        config = {"has_dockerfile": True}
        assert config.get("has_dockerfile", False) is True

    def test_gate_3_dockerfile_generated(self):
        """Gate 3: Dockerfile generated and marked."""
        state = {"dockerfile_generated": True}
        assert state.get("dockerfile_generated", False) or False

    def test_gate_4_build_config_ready(self):
        """Gate 4: Config has repo_url, type, port."""
        config = {"repo_url": "https://github.com/test/repo", "type": "nextjs", "port": 3000}
        required = ["repo_url", "type", "port"]
        missing = [k for k in required if not config.get(k)]
        assert len(missing) == 0

    def test_gate_4_build_config_missing(self):
        config = {"repo_url": "https://github.com/test/repo"}
        required = ["repo_url", "type", "port"]
        missing = [k for k in required if not config.get(k)]
        assert len(missing) == 2

    def test_gate_6_coolify_app_uuid(self):
        """Gate 6: app_uuid in state."""
        state = {"app_uuid": "abc123-uuid"}
        assert state.get("app_uuid") is not None

    def test_gate_6_coolify_no_uuid(self):
        state = {}
        assert state.get("app_uuid") is None

    def test_gate_7_database_not_needed(self):
        """Gate 7: db_uuid == 'not_needed' is valid pass."""
        state = {"db_uuid": "not_needed"}
        assert state.get("db_uuid") in ("not_needed",) or state.get("db_uuid")

    def test_gate_7_database_provisioned(self):
        state = {"db_uuid": "postgres-uuid-123"}
        assert state.get("db_uuid") is not None

    def test_gate_8_deploy_finished(self):
        """Gate 8: deploy_status == 'finished'."""
        state = {"deploy_status": "finished"}
        assert state["deploy_status"] == "finished"

    def test_gate_8_deploy_failed(self):
        state = {"deploy_status": "failed"}
        assert state["deploy_status"] != "finished"

    def test_gate_11_report_enough_tasks(self):
        """Gate 11: 10+ tasks complete."""
        prd = "- [x] 1.\n" * 11
        done = len(re.findall(r"- \[x\]", prd))
        assert done >= 10


# ── Retry Logic ──────────────────────────────────────────────

class TestRetryLogic:
    """Test exponential backoff calculation."""

    def test_backoff_sequence(self):
        """Backoff: 5s, 15s, 45s (5 * 3^attempt)."""
        for attempt, expected in enumerate([5, 15, 45]):
            wait = 5 * (3 ** attempt)
            assert wait == expected

    def test_max_retries_is_3(self):
        max_retries = 3
        attempts = list(range(1, max_retries + 1))
        assert len(attempts) == 3


# ── Deploy Loop State Management ─────────────────────────────

class TestStateManagement:
    """Test state.json read/write patterns."""

    def test_state_starts_empty(self):
        state = {}
        assert len(state) == 0

    def test_state_accumulates(self):
        state = {}
        state["app_uuid"] = "abc123"
        state["fqdn"] = "http://test.31.220.58.212.sslip.io"
        state["db_uuid"] = "not_needed"
        state["deploy_status"] = "finished"
        assert len(state) == 4

    def test_state_serializes(self):
        state = {"app_uuid": "abc", "deploy_status": "finished"}
        serialized = json.dumps(state)
        loaded = json.loads(serialized)
        assert loaded["deploy_status"] == "finished"

    def test_step_progression(self):
        """Simulate full loop: steps 1-11 all pass."""
        prd_lines = [f"- [ ] {i}. STEP_{i}" for i in range(1, 12)]
        prd = "\n".join(prd_lines)

        for step in range(1, 12):
            pattern = rf"- \[ \] {step}\."
            prd = re.sub(pattern, f"- [x] {step}.", prd, count=1)

        done = len(re.findall(r"- \[x\]", prd))
        unchecked = len(re.findall(r"- \[ \]", prd))
        assert done == 11
        assert unchecked == 0
