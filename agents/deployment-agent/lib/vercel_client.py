"""
Vercel API Client — Production-Ready
=====================================
Vercel REST API v13 wrapper with:
  - Project creation (with framework detection)
  - Deployment via file upload or Git integration
  - Environment variable management
  - Custom domain configuration
  - Deployment logs streaming
  - Health check validation

Docs: https://vercel.com/docs/rest-api

Key Notes:
  - Token: Bearer token from https://vercel.com/account/tokens
  - Team: Optional teamId query param for team projects
  - Rate Limits: 100 req/min (free), 2000 req/min (pro)
  - Git Integration: Requires GitHub App installation
"""

import json
import time
import urllib.error
import urllib.request
from typing import Any

VERCEL_API = "https://api.vercel.com"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}


class VercelClient:
    """Wrapper around the Vercel REST API v13."""

    def __init__(self, token: str, team_id: str | None = None):
        self.token = token
        self.team_id = team_id
        self.api_url = VERCEL_API

    # ── Low-level API ────────────────────────────────────────

    def request(
        self, method: str, path: str, data: dict | None = None, version: str = "v13"
    ) -> dict:
        """Make a Vercel API request. Returns {ok, status, data/error}."""
        headers = {**HEADERS, "Authorization": f"Bearer {self.token}"}
        body = json.dumps(data).encode() if data else None

        # Add team_id to query if set
        if self.team_id and "?" not in path:
            path = f"{path}?teamId={self.team_id}"
        elif self.team_id:
            path = f"{path}&teamId={self.team_id}"

        url = f"{self.api_url}/{version}{path}"

        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            raw = resp.read().decode()
            return {
                "ok": True,
                "status": resp.status,
                "data": json.loads(raw) if raw else {},
            }
        except urllib.error.HTTPError as e:
            body_text = ""
            try:
                body_text = e.read().decode()
            except Exception:
                pass
            return {
                "ok": False,
                "status": e.code,
                "error": e.reason,
                "body": body_text,
            }
        except Exception as e:
            return {"ok": False, "status": 0, "error": str(e)}

    # ── Project Management ───────────────────────────────────

    def list_projects(self) -> list[dict]:
        """List all projects."""
        result = self.request("GET", "/projects")
        if result["ok"]:
            return result["data"].get("projects", [])
        return []

    def find_project(self, name: str) -> dict | None:
        """Find project by name (case-insensitive exact match)."""
        for project in self.list_projects():
            if project.get("name", "").lower() == name.lower():
                return project
        return None

    def create_project(
        self, name: str, framework: str | None = None, root_directory: str | None = None
    ) -> dict:
        """Create a new Vercel project.

        Args:
            name: Project name (lowercase, alphanumeric + hyphens)
            framework: nextjs, vite, create-react-app, etc. (auto-detected if None)
            root_directory: Monorepo subdirectory (optional)

        Returns:
            Project data dict with 'id', 'name', 'framework'
        """
        # Check if already exists
        existing = self.find_project(name)
        if existing:
            return existing

        payload = {"name": name}
        if framework:
            payload["framework"] = framework
        if root_directory:
            payload["rootDirectory"] = root_directory

        result = self.request("POST", "/projects", payload, version="v10")
        if result["ok"]:
            return result["data"]
        raise RuntimeError(f"Failed to create project: {result}")

    def get_project(self, project_id: str) -> dict | None:
        """Get project details."""
        result = self.request("GET", f"/projects/{project_id}", version="v10")
        return result["data"] if result["ok"] else None

    def configure_git(
        self, project_id: str, repo_url: str, production_branch: str = "main"
    ) -> bool:
        """Link project to Git repository.

        Args:
            project_id: Vercel project ID
            repo_url: GitHub repo URL (https://github.com/owner/repo)
            production_branch: Branch to auto-deploy

        Note: Requires Vercel GitHub App installed for the repo
        """
        # Extract owner/repo from URL
        parts = repo_url.rstrip("/").split("/")
        if len(parts) < 2:
            return False
        owner, repo = parts[-2], parts[-1].replace(".git", "")

        payload = {
            "gitRepository": {
                "type": "github",
                "repo": f"{owner}/{repo}",
            },
            "productionBranch": production_branch,
        }

        result = self.request("PATCH", f"/projects/{project_id}", payload, version="v10")
        return result["ok"]

    # ── Environment Variables ────────────────────────────────

    def set_env(
        self,
        project_id: str,
        key: str,
        value: str,
        target: list[str] | None = None,
    ) -> bool:
        """Set an environment variable.

        Args:
            project_id: Vercel project ID
            key: Env var name
            value: Env var value
            target: ["production", "preview", "development"] (default: all)
        """
        if target is None:
            target = ["production", "preview", "development"]

        payload = {
            "key": key,
            "value": value,
            "type": "plain",
            "target": target,
        }

        result = self.request(
            "POST", f"/projects/{project_id}/env", payload, version="v10"
        )
        return result["ok"]

    def set_envs(
        self, project_id: str, env_dict: dict[str, str], target: list[str] | None = None
    ) -> dict[str, bool]:
        """Set multiple env vars. Returns {key: success}."""
        results = {}
        for key, value in env_dict.items():
            results[key] = self.set_env(project_id, key, value, target)
        return results

    # ── Deployment ───────────────────────────────────────────

    def create_deployment(
        self, project_name: str, git_ref: str = "main", force: bool = False
    ) -> dict:
        """Trigger a deployment from linked Git repo.

        Args:
            project_name: Vercel project name
            git_ref: Git branch/tag/commit
            force: Force rebuild even if no changes

        Returns:
            {deployment_id, url, state}
        """
        payload = {
            "name": project_name,
            "gitSource": {"type": "github", "ref": git_ref},
            "target": "production",
        }
        if force:
            payload["force"] = True

        result = self.request("POST", "/deployments", payload)
        if result["ok"]:
            data = result["data"]
            return {
                "deployment_id": data.get("id"),
                "url": data.get("url"),
                "state": data.get("readyState", "QUEUED"),
            }
        raise RuntimeError(f"Deployment trigger failed: {result}")

    def get_deployment(self, deployment_id: str) -> dict | None:
        """Poll deployment status."""
        result = self.request("GET", f"/deployments/{deployment_id}")
        return result["data"] if result["ok"] else None

    def deploy_and_wait(
        self, project_name: str, git_ref: str = "main", timeout: int = 600, poll_interval: int = 10
    ) -> dict[str, Any]:
        """Trigger deployment and poll until ready/error/timeout.

        Returns:
            {success, deployment_id, url, state, elapsed}
        """
        deploy_data = self.create_deployment(project_name, git_ref)
        deployment_id = deploy_data["deployment_id"]

        start_time = time.time()
        while time.time() - start_time < timeout:
            info = self.get_deployment(deployment_id)
            if info:
                state = info.get("readyState", "UNKNOWN")
                elapsed = int(time.time() - start_time)

                if state == "READY":
                    return {
                        "success": True,
                        "deployment_id": deployment_id,
                        "url": info.get("url"),
                        "state": state,
                        "elapsed": elapsed,
                    }
                elif state in ["ERROR", "CANCELED"]:
                    return {
                        "success": False,
                        "deployment_id": deployment_id,
                        "url": info.get("url"),
                        "state": state,
                        "elapsed": elapsed,
                        "error": info.get("errorMessage", "Deployment failed"),
                    }

            time.sleep(poll_interval)

        return {
            "success": False,
            "deployment_id": deployment_id,
            "state": "TIMEOUT",
            "elapsed": timeout,
        }

    # ── Domain Management ────────────────────────────────────

    def add_domain(self, project_id: str, domain: str) -> bool:
        """Add a custom domain to project."""
        payload = {"name": domain}
        result = self.request("POST", f"/projects/{project_id}/domains", payload, version="v10")
        return result["ok"]

    def remove_domain(self, project_id: str, domain: str) -> bool:
        """Remove a domain from project."""
        result = self.request("DELETE", f"/projects/{project_id}/domains/{domain}", version="v10")
        return result["ok"]

    # ── Health Check ─────────────────────────────────────────

    def health_check(self, url: str, expected_status: int = 200) -> dict:
        """Check if deployed site is healthy.

        Args:
            url: Full URL to check (e.g., https://my-app.vercel.app)
            expected_status: Expected HTTP status code

        Returns:
            {healthy: bool, status: int, error: str|None}
        """
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AgentZero/1.0"})
            resp = urllib.request.urlopen(req, timeout=10)
            status = resp.status
            return {
                "healthy": status == expected_status,
                "status": status,
                "error": None,
            }
        except urllib.error.HTTPError as e:
            return {
                "healthy": e.code == expected_status,
                "status": e.code,
                "error": str(e),
            }
        except Exception as e:
            return {
                "healthy": False,
                "status": 0,
                "error": str(e),
            }
