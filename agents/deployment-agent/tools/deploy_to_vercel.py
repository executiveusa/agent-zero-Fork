"""
deploy_to_vercel — Agent Zero Tool
===================================
Deploy applications to Vercel using Git integration.

This tool handles:
  1. Project creation (or find existing)
  2. Git repository linking
  3. Environment variable injection
  4. Deployment trigger & monitoring
  5. Health check validation

Simpler than Ralphy Loop: Vercel handles build/deploy automatically.

Tool args:
    repo_url:     GitHub repository URL (https://github.com/owner/repo)
    project_name: Vercel project name (defaults to repo name)
    branch:       Git branch to deploy (default: main)
    framework:    Framework preset (nextjs, vite, etc.) - auto-detected if None
    env_vars:     Dict of env vars to inject (optional)
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
from lib.vercel_client import VercelClient


class DeployToVercel(Tool):
    """Deploy an app to Vercel via Git integration."""

    def execute(
        self,
        repo_url: str,
        project_name: str | None = None,
        branch: str = "main",
        framework: str | None = None,
        env_vars: dict[str, str] | None = None,
        **kwargs,
    ) -> str:
        """Execute Vercel deployment.

        Args:
            repo_url: GitHub repository URL
            project_name: Project name (defaults to repo name)
            branch: Git branch to deploy
            framework: Framework preset (auto-detected if None)
            env_vars: Environment variables to inject

        Returns:
            Deployment summary with URL and status
        """
        # Extract project name from repo URL if not provided
        if not project_name:
            project_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")

        # Normalize project name (lowercase, alphanumeric + hyphens)
        project_name = project_name.lower().replace("_", "-")

        # Load Vercel token from vault
        token = vault_load("vercel_token")
        if not token:
            return Response.error(
                "VERCEL_TOKEN not found in vault. "
                "Store it with: vault_store('vercel_token', 'your-token')"
            )

        # Initialize client
        client = VercelClient(token=token)

        try:
            # Step 1: Create or find project
            self.log(f"🔺 Step 1: Creating/finding Vercel project '{project_name}'...")
            project = client.create_project(
                name=project_name,
                framework=framework,
            )
            project_id = project["id"]
            self.log(f"   ✅ Project ID: {project_id}")

            # Step 2: Link Git repository
            self.log(f"🔺 Step 2: Linking Git repo {repo_url}...")
            git_linked = client.configure_git(
                project_id=project_id,
                repo_url=repo_url,
                production_branch=branch,
            )
            if git_linked:
                self.log(f"   ✅ Git linked (branch: {branch})")
            else:
                self.log(
                    "   ⚠️  Git link failed - ensure Vercel GitHub App is installed"
                )

            # Step 3: Inject environment variables
            if env_vars:
                self.log(f"🔺 Step 3: Injecting {len(env_vars)} env vars...")
                results = client.set_envs(project_id, env_vars)
                success_count = sum(1 for v in results.values() if v)
                self.log(f"   ✅ Injected {success_count}/{len(env_vars)} env vars")

            # Step 4: Trigger deployment
            self.log(f"🔺 Step 4: Deploying from {branch}...")
            result = client.deploy_and_wait(
                project_name=project_name,
                git_ref=branch,
                timeout=300,
                poll_interval=10,
            )

            if result["success"]:
                url = result["url"]
                elapsed = result["elapsed"]

                # Step 5: Health check
                self.log(f"🔺 Step 5: Health check...")
                health = client.health_check(f"https://{url}")
                if health["healthy"]:
                    self.log(f"   ✅ Health check passed (status {health['status']})")
                else:
                    self.log(
                        f"   ⚠️  Health check failed: {health.get('error', 'Unknown')}"
                    )

                return Response.done(
                    f"""
✅ Deployment Complete

  Project: {project_name}
  URL: https://{url}
  Branch: {branch}
  Status: {result['state']}
  Elapsed: {elapsed}s
  Health: {'✅ Healthy' if health['healthy'] else '❌ Unhealthy'}

Next steps:
  - Visit https://{url} to see your app
  - Add custom domain via: client.add_domain('{project_id}', 'your-domain.com')
  - Monitor logs at: https://vercel.com/{project_name}
"""
                )
            else:
                error_msg = result.get("error", "Unknown error")
                return Response.error(
                    f"Deployment failed: {result['state']} - {error_msg}"
                )

        except Exception as e:
            return Response.error(f"Vercel deployment error: {e}")

    def log(self, message: str):
        """Log message to console."""
        print(message)
