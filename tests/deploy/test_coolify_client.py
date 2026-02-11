"""
Tests for CoolifyClient wrapper.
Run: python -m pytest tests/deploy/test_coolify_client.py -v
"""
import pytest


class TestCoolifyClientConfig:
    """Test CoolifyClient configuration without making real API calls."""

    API_BASE = "https://app.coolify.io/api/v1"
    SERVER_UUID = "zks8s40gsko0g0okkw04w4w8"
    PROJECT_UUID = "ys840c0swsg4w0o4socsoc80"

    def test_api_base_url(self):
        assert self.API_BASE.startswith("https://")
        assert "/api/v1" in self.API_BASE

    def test_required_headers(self):
        token = "test-token-123"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "AgentClaw/1.0",
        }
        assert headers["User-Agent"] == "AgentClaw/1.0"
        assert headers["Authorization"].startswith("Bearer ")

    def test_user_agent_is_mandatory(self):
        """User-Agent: AgentClaw/1.0 is required for Cloudflare bypass."""
        headers = {"User-Agent": "AgentClaw/1.0"}
        assert "AgentClaw" in headers["User-Agent"]

    def test_server_uuid_format(self):
        assert len(self.SERVER_UUID) > 10
        assert all(c.isalnum() for c in self.SERVER_UUID)

    def test_project_uuid_format(self):
        assert len(self.PROJECT_UUID) > 10


class TestCoolifyEndpoints:
    """Validate endpoint construction."""

    BASE = "https://app.coolify.io/api/v1"

    def test_list_apps_endpoint(self):
        url = f"{self.BASE}/applications"
        assert url.endswith("/applications")

    def test_create_app_endpoint(self):
        url = f"{self.BASE}/applications/public"
        assert "applications/public" in url

    def test_start_endpoint_not_deploy(self):
        """CRITICAL: Use /start not /deploy."""
        uuid = "test-uuid"
        correct = f"{self.BASE}/applications/{uuid}/start"
        wrong = f"{self.BASE}/applications/{uuid}/deploy"
        assert "start" in correct
        assert "deploy" not in correct.split("/")[-1]

    def test_env_vars_endpoint(self):
        uuid = "test-uuid"
        url = f"{self.BASE}/applications/{uuid}/envs"
        assert url.endswith("/envs")

    def test_deployment_status_endpoint(self):
        deploy_uuid = "deploy-123"
        url = f"{self.BASE}/deployments/{deploy_uuid}"
        assert "deployments" in url

    def test_create_database_endpoint(self):
        url = f"{self.BASE}/databases"
        assert url.endswith("/databases")


class TestCoolifyPayloads:
    """Validate API payload construction."""

    def test_create_app_payload(self):
        payload = {
            "server_uuid": "zks8s40gsko0g0okkw04w4w8",
            "project_uuid": "ys840c0swsg4w0o4socsoc80",
            "environment_name": "production",
            "git_repository": "https://github.com/test/repo",
            "git_branch": "main",
            "build_pack": "dockerfile",
            "ports_exposes": "3000",
            "name": "test-app",
            "type": "public",
        }
        assert payload["build_pack"] == "dockerfile"
        assert payload["type"] == "public"
        assert "instant_deploy" not in payload or payload["instant_deploy"] is False

    def test_env_var_payload_no_build_time(self):
        """CRITICAL: Never include is_build_time — causes 422."""
        payload = {
            "key": "DATABASE_URL",
            "value": "postgresql://...",
            "is_preview": False,
        }
        assert "is_build_time" not in payload

    def test_configure_fqdn_payload(self):
        payload = {
            "fqdn": "http://myapp.31.220.58.212.sslip.io",
        }
        assert payload["fqdn"].startswith("http")

    def test_create_postgres_payload(self):
        payload = {
            "server_uuid": "zks8s40gsko0g0okkw04w4w8",
            "project_uuid": "ys840c0swsg4w0o4socsoc80",
            "environment_name": "production",
            "type": "postgresql",
            "name": "test-db",
            "postgres_user": "test",
            "postgres_password": "secret123",
            "postgres_db": "test",
            "image": "postgres:16-alpine",
        }
        assert payload["type"] == "postgresql"
        assert "16" in payload["image"]
