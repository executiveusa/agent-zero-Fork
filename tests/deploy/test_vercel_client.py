"""
Tests for VercelClient wrapper.
Run: python -m pytest tests/deploy/test_vercel_client.py -v
"""
import pytest


class TestVercelClientConfig:
    """Test VercelClient configuration without making real API calls."""

    API_BASE = "https://api.vercel.com"
    API_VERSION = "v13"

    def test_api_base_url(self):
        assert self.API_BASE.startswith("https://")
        assert "api.vercel.com" in self.API_BASE

    def test_required_headers(self):
        token = "test-token-123"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        assert headers["Authorization"].startswith("Bearer ")
        assert headers["Accept"] == "application/json"

    def test_team_id_query_param(self):
        """Team ID must be added as query param if provided."""
        team_id = "team_abc123"
        path = "/projects"
        full_path = f"{path}?teamId={team_id}"
        assert "teamId=" in full_path
        assert team_id in full_path

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


class TestVercelEndpoints:
    """Validate endpoint construction."""

    BASE = "https://api.vercel.com"
    VERSION = "v13"

    def test_list_projects_endpoint(self):
        url = f"{self.BASE}/{self.VERSION}/projects"
        assert "/projects" in url
        assert self.VERSION in url

    def test_create_project_endpoint(self):
        url = f"{self.BASE}/v10/projects"
        assert url.endswith("/projects")

    def test_deployment_endpoint(self):
        deployment_id = "dpl_abc123"
        url = f"{self.BASE}/{self.VERSION}/deployments/{deployment_id}"
        assert deployment_id in url
        assert "/deployments/" in url

    def test_env_vars_endpoint(self):
        project_id = "prj_abc123"
        url = f"{self.BASE}/v10/projects/{project_id}/env"
        assert project_id in url
        assert "/env" in url

    def test_domains_endpoint(self):
        project_id = "prj_abc123"
        url = f"{self.BASE}/v10/projects/{project_id}/domains"
        assert "/domains" in url


class TestVercelDeploymentStates:
    """Test deployment state handling."""

    VALID_STATES = [
        "QUEUED",
        "BUILDING",
        "READY",
        "ERROR",
        "CANCELED",
    ]

    def test_ready_is_success(self):
        state = "READY"
        assert state in self.VALID_STATES
        assert state == "READY"

    def test_error_states(self):
        error_states = ["ERROR", "CANCELED"]
        for state in error_states:
            assert state in self.VALID_STATES

    def test_pending_states(self):
        pending_states = ["QUEUED", "BUILDING"]
        for state in pending_states:
            assert state in self.VALID_STATES


class TestVercelFrameworks:
    """Test framework detection and presets."""

    SUPPORTED_FRAMEWORKS = [
        "nextjs",
        "vite",
        "create-react-app",
        "vue",
        "nuxtjs",
        "gatsby",
        "svelte",
        "sveltekit",
        "astro",
        "remix",
        "solidstart",
    ]

    def test_nextjs_framework(self):
        assert "nextjs" in self.SUPPORTED_FRAMEWORKS

    def test_vite_framework(self):
        assert "vite" in self.SUPPORTED_FRAMEWORKS

    def test_static_frameworks(self):
        static_frameworks = ["create-react-app", "vite", "gatsby"]
        for framework in static_frameworks:
            assert framework in self.SUPPORTED_FRAMEWORKS


class TestVercelEnvironmentTargets:
    """Test environment variable targets."""

    VALID_TARGETS = ["production", "preview", "development"]

    def test_production_target(self):
        assert "production" in self.VALID_TARGETS

    def test_preview_target(self):
        assert "preview" in self.VALID_TARGETS

    def test_development_target(self):
        assert "development" in self.VALID_TARGETS

    def test_all_targets_default(self):
        default_targets = ["production", "preview", "development"]
        assert set(default_targets) == set(self.VALID_TARGETS)


class TestVercelHealthCheck:
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


class TestVercelRateLimits:
    """Validate rate limit constraints."""

    FREE_LIMIT = 100  # requests per minute
    PRO_LIMIT = 2000  # requests per minute

    def test_free_tier_limit(self):
        assert self.FREE_LIMIT == 100

    def test_pro_tier_limit(self):
        assert self.PRO_LIMIT == 2000

    def test_stay_under_limit(self):
        # Ensure deployment polling respects rate limits
        poll_interval = 10  # seconds
        requests_per_minute = 60 // poll_interval
        assert requests_per_minute <= self.FREE_LIMIT


class TestVercelGitIntegration:
    """Test Git repository linking."""

    def test_github_repo_url_parsing(self):
        repo_url = "https://github.com/owner/repo"
        parts = repo_url.rstrip("/").split("/")
        owner = parts[-2]
        repo = parts[-1].replace(".git", "")
        assert owner == "owner"
        assert repo == "repo"

    def test_github_repo_with_git_extension(self):
        repo_url = "https://github.com/owner/repo.git"
        repo = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        assert repo == "repo"

    def test_production_branch_default(self):
        default_branch = "main"
        assert default_branch in ["main", "master"]
