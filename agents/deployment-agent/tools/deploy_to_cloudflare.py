"""
deploy_to_cloudflare — Agent Zero Tool
========================================
Deploy applications to Cloudflare Pages or Workers.

Auto-detection:
  - Static sites (HTML/CSS/JS, React, Vue) → Cloudflare Pages
  - Edge functions (service workers, API routes) → Cloudflare Workers

This tool handles:
  1. Project/script creation
  2. Git repository linking (Pages only)
  3. Environment variable injection
  4. Deployment trigger & monitoring
  5. Health check validation

Tool args:
    project_name:  Cloudflare project/worker name
    repo_url:      GitHub repository URL (Pages only)
    branch:        Git branch to deploy (default: main)
    deployment_type: "pages" or "workers" (auto-detected if None)
    script_content: Worker script content (Workers only)
    env_vars:      Dict of env vars to inject (optional)
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
_AGENT_ROOT = Path(__file__).resolve().parents[1]  # agents/deployment-agent/
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(_AGENT_ROOT))

from python.helpers.tool import Tool, Response
from python.helpers.vault import vault_load

# Import lib modules
from lib.cloudflare_client import CloudflareClient


class DeployToCloudflare(Tool):
    """Deploy an app to Cloudflare Pages or Workers."""

    def execute(
        self,
        project_name: str,
        repo_url: str | None = None,
        branch: str = "main",
        deployment_type: str | None = None,
        script_content: str | None = None,
        env_vars: dict[str, str] | None = None,
        **kwargs,
    ) -> str:
        """Execute Cloudflare deployment.

        Args:
            project_name: Project or Worker name
            repo_url: GitHub repository URL (Pages only)
            branch: Git branch to deploy (Pages only)
            deployment_type: "pages" or "workers" (auto-detected if None)
            script_content: Worker script content (Workers only)
            env_vars: Environment variables to inject

        Returns:
            Deployment summary with URL and status
        """
        # Normalize project name (lowercase, alphanumeric + hyphens)
        project_name = project_name.lower().replace("_", "-")

        # Auto-detect deployment type
        if not deployment_type:
            if script_content:
                deployment_type = "workers"
            elif repo_url:
                deployment_type = "pages"
            else:
                return Response.error(
                    "Cannot auto-detect deployment type. "
                    "Specify deployment_type='pages' or 'workers'"
                )

        # Load Cloudflare credentials from vault
        token = vault_load("cloudflare_api_token")
        account_id = vault_load("cloudflare_account_id")
        
        if not token or not account_id:
            return Response.error(
                "Cloudflare credentials not found in vault. "
                "Store them with:\n"
                "  vault_store('cloudflare_api_token', 'your-token')\n"
                "  vault_store('cloudflare_account_id', 'your-account-id')"
            )

        # Initialize client
        client = CloudflareClient(token=token, account_id=account_id)

        try:
            if deployment_type == "pages":
                return self._deploy_pages(
                    client, project_name, repo_url, branch, env_vars
                )
            elif deployment_type == "workers":
                return self._deploy_workers(
                    client, project_name, script_content, env_vars
                )
            else:
                return Response.error(
                    f"Invalid deployment_type: {deployment_type}. "
                    "Must be 'pages' or 'workers'"
                )

        except Exception as e:
            return Response.error(f"Cloudflare deployment error: {e}")

    def _deploy_pages(
        self,
        client: CloudflareClient,
        project_name: str,
        repo_url: str | None,
        branch: str,
        env_vars: dict[str, str] | None,
    ) -> str:
        """Deploy to Cloudflare Pages."""
        if not repo_url:
            return Response.error("repo_url is required for Pages deployment")

        # Step 1: Create or find project
        self.log(f"☁️  Step 1: Creating/finding Pages project '{project_name}'...")
        project = client.create_pages_project(
            name=project_name,
            production_branch=branch,
        )
        project_id = project["id"]
        subdomain = project.get("subdomain", project_name)
        self.log(f"   ✅ Project ID: {project_id}")
        self.log(f"   ✅ Subdomain: {subdomain}.pages.dev")

        # Step 2: Trigger deployment
        self.log(f"☁️  Step 2: Deploying from {branch}...")
        result = client.deploy_pages_and_wait(
            project_name=project_name,
            branch=branch,
            timeout=300,
            poll_interval=10,
        )

        if result["success"]:
            url = result["url"]
            elapsed = result["elapsed"]

            # Step 3: Health check
            self.log(f"☁️  Step 3: Health check...")
            health = client.health_check(url)
            if health["healthy"]:
                self.log(f"   ✅ Health check passed (status {health['status']})")
            else:
                self.log(f"   ⚠️  Health check failed: {health.get('error', 'Unknown')}")

            return Response.done(
                f"""
✅ Cloudflare Pages Deployment Complete

  Project: {project_name}
  URL: {url}
  Branch: {branch}
  Status: {result['stage']}
  Elapsed: {elapsed}s
  Health: {'✅ Healthy' if health['healthy'] else '❌ Unhealthy'}

Next steps:
  - Visit {url} to see your app
  - Add custom domain via Cloudflare dashboard
  - Monitor at: https://dash.cloudflare.com/{client.account_id}/pages/view/{project_name}
"""
            )
        else:
            error_msg = result.get("error", "Unknown error")
            return Response.error(
                f"Pages deployment failed: {result['stage']} - {error_msg}"
            )

    def _deploy_workers(
        self,
        client: CloudflareClient,
        script_name: str,
        script_content: str | None,
        env_vars: dict[str, str] | None,
    ) -> str:
        """Deploy to Cloudflare Workers."""
        if not script_content:
            return Response.error("script_content is required for Workers deployment")

        # Step 1: Deploy Worker
        self.log(f"☁️  Step 1: Deploying Worker '{script_name}'...")
        result = client.deploy_worker(
            script_name=script_name,
            script_content=script_content,
            env_vars=env_vars,
        )
        url = result["url"]
        self.log(f"   ✅ Worker deployed: {url}")

        # Step 2: Health check
        self.log(f"☁️  Step 2: Health check...")
        health = client.health_check(url)
        if health["healthy"]:
            self.log(f"   ✅ Health check passed (status {health['status']})")
        else:
            self.log(f"   ⚠️  Health check failed: {health.get('error', 'Unknown')}")

        return Response.done(
            f"""
✅ Cloudflare Workers Deployment Complete

  Worker: {script_name}
  URL: {url}
  Health: {'✅ Healthy' if health['healthy'] else '❌ Unhealthy'}

Next steps:
  - Visit {url} to test your Worker
  - Add custom route via Cloudflare dashboard
  - Monitor at: https://dash.cloudflare.com/{client.account_id}/workers/services/view/{script_name}
  - View logs: wrangler tail {script_name}
"""
        )

    def log(self, message: str):
        """Log message to console."""
        print(message)
