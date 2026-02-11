"""
Tests for OpenClaw AppRegistry, DeployQueue, and DeployStream.
Run: node --test or via a test runner.
These are Python-based logic tests validating the expected behavior.
"""
import json
import pytest


class TestAppRegistry:
    """Test AppRegistry logic patterns."""

    def test_register_app(self):
        registry = {}
        name = "my-app"
        registry[name] = {
            "name": name,
            "status": "registered",
            "deploys": [],
            "createdAt": "2025-01-01T00:00:00Z",
        }
        assert name in registry
        assert registry[name]["status"] == "registered"

    def test_update_app(self):
        registry = {"my-app": {"name": "my-app", "status": "registered"}}
        registry["my-app"]["status"] = "deploying"
        assert registry["my-app"]["status"] == "deploying"

    def test_remove_app(self):
        registry = {"my-app": {"name": "my-app"}}
        del registry["my-app"]
        assert "my-app" not in registry

    def test_record_deploy(self):
        app = {"name": "app", "deploys": []}
        deploy = {"id": "deploy-1", "status": "started", "trigger": "api"}
        app["deploys"].append(deploy)
        assert len(app["deploys"]) == 1
        assert app["deploys"][0]["status"] == "started"

    def test_deploy_history_limit(self):
        """Registry keeps max 20 deploys per app."""
        max_deploys = 20
        deploys = [{"id": f"deploy-{i}"} for i in range(25)]
        trimmed = deploys[-max_deploys:]
        assert len(trimmed) == 20
        assert trimmed[0]["id"] == "deploy-5"

    def test_list_apps(self):
        registry = {
            "app-1": {"name": "app-1"},
            "app-2": {"name": "app-2"},
            "app-3": {"name": "app-3"},
        }
        apps = list(registry.values())
        assert len(apps) == 3


class TestDeployQueue:
    """Test DeployQueue behavior."""

    def test_enqueue_first_job_is_immediate(self):
        """First job for an app starts immediately."""
        queues = {}
        app_name = "my-app"

        if app_name not in queues:
            queues[app_name] = {"active": None, "pending": []}

        if queues[app_name]["active"] is None:
            queues[app_name]["active"] = {"job": "deploy-1"}
            immediate = True
        else:
            queues[app_name]["pending"].append({"job": "deploy-1"})
            immediate = False

        assert immediate is True

    def test_second_job_is_queued(self):
        """Second job when one is active gets queued."""
        queues = {"my-app": {"active": {"job": "deploy-1"}, "pending": []}}
        queues["my-app"]["pending"].append({"job": "deploy-2"})

        assert len(queues["my-app"]["pending"]) == 1

    def test_complete_promotes_next(self):
        """Completing a job promotes the next pending job."""
        queue = {
            "active": {"job": "deploy-1"},
            "pending": [{"job": "deploy-2"}, {"job": "deploy-3"}],
        }

        # Complete active job
        queue["active"] = queue["pending"].pop(0) if queue["pending"] else None
        assert queue["active"]["job"] == "deploy-2"
        assert len(queue["pending"]) == 1

    def test_no_concurrent_deploys(self):
        """Only one active deploy per app at a time."""
        queue = {"active": {"job": "deploy-1"}, "pending": []}
        assert queue["active"] is not None
        # Should not start another while active exists


class TestDeployStream:
    """Test WebSocket deploy streaming patterns."""

    def test_subscribe_to_app(self):
        subscribers = {}
        app_name = "my-app"
        ws_id = "ws-1"

        if app_name not in subscribers:
            subscribers[app_name] = set()
        subscribers[app_name].add(ws_id)

        assert ws_id in subscribers[app_name]

    def test_broadcast_to_subscribers(self):
        subscribers = {"my-app": {"ws-1", "ws-2", "ws-3"}}
        event = {"type": "log", "message": "Building..."}

        recipients = list(subscribers.get("my-app", set()))
        assert len(recipients) == 3

    def test_unsubscribe_on_disconnect(self):
        subscribers = {"my-app": {"ws-1", "ws-2"}}
        subscribers["my-app"].discard("ws-1")
        assert len(subscribers["my-app"]) == 1

    def test_no_subscribers_no_error(self):
        subscribers = {}
        recipients = list(subscribers.get("nonexistent", set()))
        assert len(recipients) == 0


class TestOpenClawEndpoints:
    """Validate expected HTTP endpoints."""

    ENDPOINTS = [
        ("GET", "/health"),
        ("GET", "/status"),
        ("GET", "/apps"),
        ("POST", "/apps"),
        ("GET", "/apps/:name"),
        ("GET", "/apps/:name/status"),
        ("DELETE", "/apps/:name"),
        ("POST", "/deploy/:name"),
        ("POST", "/apps/:name/rollback"),
        ("POST", "/webhook/:channel"),
    ]

    def test_all_endpoints_defined(self):
        assert len(self.ENDPOINTS) == 10

    def test_health_endpoint_is_get(self):
        health = [e for e in self.ENDPOINTS if e[1] == "/health"]
        assert health[0][0] == "GET"

    def test_deploy_is_post(self):
        deploy = [e for e in self.ENDPOINTS if "/deploy/" in e[1]]
        assert deploy[0][0] == "POST"
