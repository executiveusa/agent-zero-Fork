"""
Coolify Cloud API Client — Battle-Tested
==========================================
All known gotchas baked in:
  - User-Agent: AgentClaw/1.0 (required for Cloudflare bypass)
  - Use /start not /deploy (returns 404)
  - Never include is_build_time in env var calls (causes 422)
  - Always bind to 0.0.0.0, never localhost
"""

import json
import time
import urllib.error
import urllib.request
from typing import Any

COOLIFY_API = "https://app.coolify.io/api/v1"
SERVER_UUID = "zks8s40gsko0g0okkw04w4w8"
PROJECT_UUID = "ys840c0swsg4w0o4socsoc80"
VPS_IP = "31.220.58.212"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "AgentClaw/1.0",
}


class CoolifyClient:
    """Wrapper around the Coolify Cloud REST API."""

    def __init__(self, token: str, api_url: str = COOLIFY_API):
        self.token = token
        self.api_url = api_url

    # ── Low-level API ────────────────────────────────────────

    def request(self, method: str, path: str, data: dict | None = None) -> dict:
        """Make a Coolify API request. Returns {ok, status, data/error}."""
        headers = {**HEADERS, "Authorization": f"Bearer {self.token}"}
        body = json.dumps(data).encode() if data else None
        url = f"{self.api_url}{path}"

        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            raw = resp.read().decode()
            return {"ok": True, "status": resp.status, "data": json.loads(raw) if raw else {}}
        except urllib.error.HTTPError as e:
            body_text = ""
            try:
                body_text = e.read().decode()
            except Exception:
                pass
            return {"ok": False, "status": e.code, "error": e.reason, "body": body_text}
        except Exception as e:
            return {"ok": False, "status": 0, "error": str(e)}

    # ── Application CRUD ─────────────────────────────────────

    def list_apps(self) -> list[dict]:
        """List all applications."""
        result = self.request("GET", "/applications")
        return result["data"] if result["ok"] else []

    def find_app(self, name: str) -> str | None:
        """Find app UUID by name (case-insensitive partial match)."""
        for app in self.list_apps():
            if name.lower() in app.get("name", "").lower():
                return app["uuid"]
        return None

    def create_app(
        self,
        name: str,
        repo_url: str,
        branch: str = "main",
        port: int = 3000,
        dockerfile: str = "/Dockerfile",
    ) -> str:
        """Create a new app or return existing UUID."""
        existing = self.find_app(name)
        if existing:
            return existing

        payload = {
            "server_uuid": SERVER_UUID,
            "project_uuid": PROJECT_UUID,
            "environment_name": "production",
            "git_repository": repo_url,
            "git_branch": branch,
            "build_pack": "dockerfile",
            "ports_exposes": str(port),
            "name": name,
            "dockerfile_location": dockerfile,
            "instant_deploy": False,
            "type": "public",
        }
        result = self.request("POST", "/applications/public", payload)
        if result["ok"]:
            return result["data"]["uuid"]
        raise RuntimeError(f"Failed to create app: {result}")

    def configure_app(
        self,
        app_uuid: str,
        fqdn: str,
        health_path: str = "/health",
        port: int = 3000,
    ) -> bool:
        """Set FQDN and health check config."""
        payload = {
            "fqdn": fqdn,
            "health_check_enabled": True,
            "health_check_path": health_path,
            "health_check_port": str(port),
            "health_check_interval": 30,
            "health_check_timeout": 10,
            "health_check_retries": 3,
            "health_check_start_period": 60,
        }
        result = self.request("PATCH", f"/applications/{app_uuid}", payload)
        return result["ok"]

    def get_app(self, app_uuid: str) -> dict | None:
        """Get application details."""
        result = self.request("GET", f"/applications/{app_uuid}")
        return result["data"] if result["ok"] else None

    # ── Environment Variables ────────────────────────────────

    def set_env(self, app_uuid: str, key: str, value: str) -> bool:
        """Set an env var. NOTE: Never include is_build_time (422 error)."""
        result = self.request("POST", f"/applications/{app_uuid}/envs", {
            "key": key,
            "value": value,
            "is_preview": False,
        })
        return result["ok"]

    def set_envs(self, app_uuid: str, env_dict: dict[str, str]) -> dict[str, bool]:
        """Set multiple env vars. Returns {key: success}."""
        results = {}
        for key, value in env_dict.items():
            results[key] = self.set_env(app_uuid, key, value)
        return results

    # ── Deployment ───────────────────────────────────────────

    def start(self, app_uuid: str) -> dict:
        """Trigger deployment. Use /start NOT /deploy (404)."""
        result = self.request("POST", f"/applications/{app_uuid}/start", {})
        if result["ok"]:
            return result["data"]
        raise RuntimeError(f"Deploy trigger failed: {result}")

    def restart(self, app_uuid: str) -> dict:
        """Restart (rollback to last build)."""
        result = self.request("POST", f"/applications/{app_uuid}/restart", {})
        if result["ok"]:
            return result["data"]
        raise RuntimeError(f"Restart failed: {result}")

    def get_deployment(self, deploy_uuid: str) -> dict | None:
        """Poll deployment status."""
        result = self.request("GET", f"/deployments/{deploy_uuid}")
        return result["data"] if result["ok"] else None

    def deploy_and_wait(
        self, app_uuid: str, timeout: int = 600, poll_interval: int = 15
    ) -> dict[str, Any]:
        """Start deployment and poll until finished/failed."""
        deploy_data = self.start(app_uuid)
        deploy_uuid = deploy_data.get("deployment_uuid")
        if not deploy_uuid:
            return {"success": False, "error": "No deployment UUID returned"}

        start_time = time.time()
        while time.time() - start_time < timeout:
            info = self.get_deployment(deploy_uuid)
            if info:
                status = info.get("status", "unknown")
                elapsed = int(time.time() - start_time)
                if status == "finished":
                    return {
                        "success": True,
                        "deploy_uuid": deploy_uuid,
                        "elapsed": elapsed,
                        "status": "finished",
                    }
                if status == "failed":
                    logs = []
                    try:
                        entries = json.loads(info.get("logs", "[]"))
                        logs = [e.get("output", "")[:200] for e in entries[-5:]]
                    except Exception:
                        pass
                    return {
                        "success": False,
                        "deploy_uuid": deploy_uuid,
                        "elapsed": elapsed,
                        "status": "failed",
                        "logs": logs,
                    }
            time.sleep(poll_interval)

        return {
            "success": False,
            "deploy_uuid": deploy_uuid,
            "elapsed": timeout,
            "status": "timeout",
        }

    # ── Database ─────────────────────────────────────────────

    def create_postgres(
        self, app_name: str, db_user: str, db_pass: str, db_name: str
    ) -> str | None:
        """Provision a Postgres 16 database. Returns UUID or None."""
        payload = {
            "server_uuid": SERVER_UUID,
            "project_uuid": PROJECT_UUID,
            "environment_name": "production",
            "type": "postgresql",
            "name": f"{app_name}-db",
            "postgres_user": db_user,
            "postgres_password": db_pass,
            "postgres_db": db_name,
            "image": "postgres:16-alpine",
        }
        result = self.request("POST", "/databases", payload)
        if result["ok"]:
            return result["data"].get("uuid")
        return None
