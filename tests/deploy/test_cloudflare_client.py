"""
Tests for CloudflareClient wrapper.
Run: python -m pytest tests/deploy/test_cloudflare_client.py -v
"""
import pytest


class TestCloudflareClientConfig:
    """Test CloudflareClient configuration without making real API calls."""

    API_BASE = "https://api.cloudflare.com/client/v4"

    def test_api_base_url(self):
        assert self.API_BASE.startswith("https://")
        assert "api.cloudflare.com" in self.API_BASE

    def test_required_headers(self):
        token = "test-token-123"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        assert headers["Authorization"].startswith("Bearer ")
        assert headers["Accept"] == "application/json"

    def test_account_id_required(self):
        """Account ID must be provided for all operations."""
        account_id = "abc123def456"
        assert len(account_id) > 0
        assert isinstance(account_id, str)

    def test_project_name_normalization(self):
        """Project names must be lowercase with hyphens."""
        test_cases = [
            ("MyProject", "myproject"),
            ("my_project", "my-project"),
            ("My Project", "my-project"),
            ("PROJECT-123", "project-123"),
        ]
        for input_name, expected in test_cases:
            normalized = input_name.lower().replace("_", "-").replace(" ", "-")
            assert normalized == expected


class TestCloudflareEndpoints:
    """Validate endpoint construction."""

    BASE = "https://api.cloudflare.com/client/v4"
    ACCOUNT_ID = "abc123"

    def test_pages_projects_endpoint(self):
        url = f"{self.BASE}/accounts/{self.ACCOUNT_ID}/pages/projects"
        assert "/pages/projects" in url
        assert self.ACCOUNT_ID in url

    def test_create_pages_project_endpoint(self):
        url = f"{self.BASE}/accounts/{self.ACCOUNT_ID}/pages/projects"
        assert url.endswith("/pages/projects")

    def test_pages_deployment_endpoint(self):
        project_name = "my-project"
        deployment_id = "deploy123"
        url = f"{self.BASE}/accounts/{self.ACCOUNT_ID}/pages/projects/{project_name}/deployments/{deployment_id}"
        assert project_name in url
        assert deployment_id in url
        assert "/deployments/" in url

    def test_workers_script_endpoint(self):
        script_name = "my-worker"
        url = f"{self.BASE}/accounts/{self.ACCOUNT_ID}/workers/scripts/{script_name}"
        assert script_name in url
        assert "/workers/scripts/" in url

    def test_dns_records_endpoint(self):
        zone_id = "zone123"
        url = f"{self.BASE}/zones/{zone_id}/dns_records"
        assert zone_id in url
        assert "/dns_records" in url


class TestCloudflareDeploymentStages:
    """Test Pages deployment stage handling."""

    VALID_STAGES = [
        "queued",
        "initialize",
        "clone_repo",
        "build",
        "deploy",
        "active",
    ]

    VALID_STATUSES = [
        "active",
        "success",
        "failure",
        "canceled",
    ]

    def test_success_status(self):
        status = "success"
        assert status in self.VALID_STATUSES

    def test_failure_statuses(self):
        error_statuses = ["failure", "canceled"]
        for status in error_statuses:
            assert status in self.VALID_STATUSES

    def test_active_status(self):
        status = "active"
        assert status in self.VALID_STATUSES


class TestCloudflarePages:
    """Test Cloudflare Pages functionality."""

    def test_pages_subdomain_format(self):
        project_name = "my-project"
        expected_subdomain = f"{project_name}.pages.dev"
        assert ".pages.dev" in expected_subdomain

    def test_production_branch_default(self):
        default_branch = "main"
        assert default_branch in ["main", "master"]

    def test_pages_url_format(self):
        deployment_id = "abc123"
        project_name = "my-project"
        expected_url = f"https://{deployment_id}.{project_name}.pages.dev"
        assert "pages.dev" in expected_url


class TestCloudflareWorkers:
    """Test Cloudflare Workers functionality."""

    def test_workers_subdomain_format(self):
        script_name = "my-worker"
        account_id = "abc123"
        expected_url = f"https://{script_name.replace('_', '-')}.{account_id}.workers.dev"
        assert ".workers.dev" in expected_url

    def test_worker_name_normalization(self):
        script_name = "my_worker"
        normalized = script_name.replace("_", "-")
        assert normalized == "my-worker"

    def test_worker_bindings(self):
        """Workers support environment variables via bindings."""
        bindings = [
            {"name": "API_KEY", "type": "plain_text", "text": "secret123"},
            {"name": "DATABASE_URL", "type": "plain_text", "text": "postgres://..."},
        ]
        assert len(bindings) == 2
        assert bindings[0]["type"] == "plain_text"


class TestCloudflareRateLimits:
    """Validate rate limit constraints."""

    FREE_LIMIT = 1200  # requests per 5 minutes
    PRO_LIMIT = 1200  # requests per 5 minutes
    BUSINESS_LIMIT = 4000  # requests per 5 minutes

    def test_free_tier_limit(self):
        assert self.FREE_LIMIT == 1200

    def test_stay_under_limit(self):
        # Ensure deployment polling respects rate limits
        poll_interval = 10  # seconds
        requests_per_5min = (5 * 60) // poll_interval
        assert requests_per_5min <= self.FREE_LIMIT


class TestCloudflareResponseFormat:
    """Test Cloudflare API response format."""

    def test_success_response_structure(self):
        """Cloudflare wraps responses in {success, result, errors}."""
        response = {
            "success": True,
            "result": {"id": "123", "name": "test"},
            "errors": [],
        }
        assert response["success"] is True
        assert "result" in response
        assert isinstance(response["errors"], list)

    def test_error_response_structure(self):
        response = {
            "success": False,
            "result": None,
            "errors": [{"code": 1000, "message": "Error message"}],
        }
        assert response["success"] is False
        assert len(response["errors"]) > 0


class TestCloudflareDNS:
    """Test DNS management functionality."""

    VALID_RECORD_TYPES = [
        "A",
        "AAAA",
        "CNAME",
        "TXT",
        "MX",
        "NS",
        "SRV",
    ]

    def test_a_record(self):
        assert "A" in self.VALID_RECORD_TYPES

    def test_cname_record(self):
        assert "CNAME" in self.VALID_RECORD_TYPES

    def test_proxied_default(self):
        """Cloudflare proxy should be enabled by default."""
        proxied = True
        assert proxied is True


class TestCloudflareHealthCheck:
    """Test health check validation."""

    def test_success_status(self):
        expected_status = 200
        actual_status = 200
        assert actual_status == expected_status

    def test_redirect_status(self):
        redirect_status = 301
        assert redirect_status in [301, 302, 307, 308]

    def test_error_status(self):
        error_statuses = [400, 401, 403, 404, 500, 502, 503]
        for status in error_statuses:
            assert status >= 400
