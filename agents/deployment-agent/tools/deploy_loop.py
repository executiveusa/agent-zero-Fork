"""
deploy_loop — Agent Zero Tool (Ralphy Loop Engine)
====================================================
The core test-driven deployment loop. Reads the PRD, executes the next
unchecked step, runs the test gate, and marks done on pass. Retries up
to 3 times with exponential backoff on failure.

This tool does NOT break the loop — it executes one step per call and
returns control to the agent's monologue loop, which should call it again
(via the role prompt) until read_deploy_prd returns break_loop=True.

Tool args:
    app_name:  Name of the app (matches workspace/deploys/{app_name}/)
"""

import json
import secrets
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
_AGENT_ROOT = Path(__file__).resolve().parents[1]  # agents/deployment-agent/
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(_AGENT_ROOT))

from python.helpers.tool import Tool, Response

# Import lib modules (relative to agent root via sys.path)
from lib.coolify_client import CoolifyClient
from lib.analyzer import analyze_github_repo
from lib.docker_builder import generate_dockerfile
from lib.health import health_check, wait_for_healthy
from lib.secrets import (
    vault_env_audit,
    inject_secrets_to_coolify,
    get_framework_env_defaults,
)
from lib.dns import generate_sslip_domain, resolve_domain


def _load_config(app_name: str) -> dict:
    config_path = PROJECT_ROOT / "workspace" / "deploys" / app_name / "config.json"
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))
    return {}


def _load_state(app_name: str) -> dict:
    state_path = PROJECT_ROOT / "workspace" / "deploys" / app_name / "state.json"
    if state_path.exists():
        return json.loads(state_path.read_text(encoding="utf-8"))
    return {}


def _save_state(app_name: str, state: dict):
    state_path = PROJECT_ROOT / "workspace" / "deploys" / app_name / "state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _get_coolify_client() -> CoolifyClient:
    """Get a CoolifyClient with token from vault."""
    from python.helpers.vault import vault_load
    for key in ["coolify_cloud_token", "coolify_api_token", "coolify_api_token_alt"]:
        token = vault_load(key)
        if token:
            return CoolifyClient(token)
    raise RuntimeError("No Coolify API token in vault")


def _mark_step_done(app_name: str, step: int, result: str):
    """Mark a step as done in the PRD file."""
    import re
    prd_path = PROJECT_ROOT / "workspace" / "deploys" / app_name / "PRD.md"
    if not prd_path.exists():
        return

    lines = prd_path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if re.match(rf"^- \[ \] {step}\.\s+", line.strip()):
            lines[i] = line.replace("- [ ]", "- [x]", 1)
            break

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append(f"- **Step {step}** completed at {timestamp}: {result}")
    prd_path.write_text("\n".join(lines), encoding="utf-8")


def _find_next_step(app_name: str) -> int | None:
    """Find the next unchecked step number in the PRD."""
    import re
    prd_path = PROJECT_ROOT / "workspace" / "deploys" / app_name / "PRD.md"
    if not prd_path.exists():
        return None

    for line in prd_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^- \[ \] (\d+)\.", line.strip())
        if m:
            return int(m.group(1))
    return None  # All done


class DeployLoop(Tool):

    async def execute(self, **kwargs) -> Response:
        app_name = self.args.get("app_name", "").strip()
        if not app_name:
            return Response(
                message="Error: app_name is required.",
                break_loop=False,
            )

        config = _load_config(app_name)
        if not config:
            return Response(
                message=f"No config found for '{app_name}'. Run generate_deploy_prd first.",
                break_loop=False,
            )

        step = _find_next_step(app_name)
        if step is None:
            return Response(
                message=f"ALL STEPS COMPLETE for '{app_name}'! Deployment finished.",
                break_loop=True,
            )

        state = _load_state(app_name)
        retries = state.get(f"step_{step}_retries", 0)
        max_retries = 3

        try:
            result = await self._execute_step(step, app_name, config, state)
        except Exception as e:
            result = {"success": False, "error": str(e)}

        if result.get("success"):
            _mark_step_done(app_name, step, result.get("message", "done"))
            # Clear retry counter
            state.pop(f"step_{step}_retries", None)
            _save_state(app_name, state)
            return Response(
                message=f"STEP {step} PASSED ✓ — {result.get('message', 'done')}\n"
                        f"Use deploy_loop again to continue to the next step.",
                break_loop=False,
            )
        else:
            retries += 1
            state[f"step_{step}_retries"] = retries
            _save_state(app_name, state)

            if retries >= max_retries:
                return Response(
                    message=f"STEP {step} FAILED after {max_retries} retries ✗\n"
                            f"Error: {result.get('error', 'unknown')}\n"
                            f"Manual intervention required. Check Coolify dashboard.",
                    break_loop=False,
                )

            # Exponential backoff hint
            backoff = 5 * (3 ** (retries - 1))  # 5s, 15s, 45s
            return Response(
                message=f"STEP {step} FAILED (attempt {retries}/{max_retries}) ✗\n"
                        f"Error: {result.get('error', 'unknown')}\n"
                        f"Retry in {backoff}s. Use deploy_loop again to retry.",
                break_loop=False,
            )

    # ── Step Executors ───────────────────────────────────────

    async def _execute_step(self, step: int, app_name: str, config: dict, state: dict) -> dict:
        """Execute a single pipeline step. Returns {success, message/error}."""
        if step == 1:
            return self._step_analyze(config)
        elif step == 2:
            return self._step_secrets(config, state)
        elif step == 3:
            return self._step_dockerfile(app_name, config)
        elif step == 4:
            return self._step_build(app_name, config, state)
        elif step == 5:
            return self._step_test(config, state)
        elif step == 6:
            return self._step_coolify(app_name, config, state)
        elif step == 7:
            return self._step_database(app_name, config, state)
        elif step == 8:
            return self._step_deploy(app_name, config, state)
        elif step == 9:
            return self._step_dns(config, state)
        elif step == 10:
            return self._step_verify(config)
        elif step == 11:
            return self._step_report(app_name, config, state)
        return {"success": False, "error": f"Unknown step {step}"}

    def _step_analyze(self, config: dict) -> dict:
        """Step 1: Validate project type detection."""
        ptype = config.get("type", "unknown")
        if ptype and ptype != "unknown":
            return {
                "success": True,
                "message": f"Project type: {ptype} ({config.get('language', '?')}, port {config.get('port', '?')})",
            }
        # Try re-analyzing
        analysis = analyze_github_repo(config.get("repo_url", ""))
        if analysis["type"] != "unknown":
            config["type"] = analysis["type"]
            config["port"] = analysis["port"]
            config["language"] = analysis["language"]
            config_path = PROJECT_ROOT / "workspace" / "deploys" / config.get("app_name", "") / "config.json"
            config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
            return {"success": True, "message": f"Re-analyzed: {analysis['type']}"}
        return {"success": False, "error": "Could not detect project type"}

    def _step_secrets(self, config: dict, state: dict) -> dict:
        """Step 2: Audit and import secrets."""
        env_vars = config.get("env_vars_needed", [])
        if not env_vars:
            return {"success": True, "message": "No env vars needed"}

        audit = vault_env_audit(env_vars)
        missing = [k for k, v in audit.items() if v == "missing"]
        if missing:
            return {
                "success": False,
                "error": f"Missing from vault: {', '.join(missing)}. "
                         "Import them with vault_store or vault_bootstrap_from_file.",
            }
        return {
            "success": True,
            "message": f"All {len(env_vars)} env vars present in vault",
        }

    def _step_dockerfile(self, app_name: str, config: dict) -> dict:
        """Step 3: Ensure Dockerfile exists."""
        if config.get("has_dockerfile"):
            return {"success": True, "message": "Dockerfile exists in repo"}

        # Generate one
        ptype = config.get("type", "node")
        port = config.get("port", 3000)
        dockerfile_content = generate_dockerfile(ptype, port)

        deploy_dir = PROJECT_ROOT / "workspace" / "deploys" / app_name
        deploy_dir.mkdir(parents=True, exist_ok=True)
        (deploy_dir / "Dockerfile").write_text(dockerfile_content, encoding="utf-8")

        return {
            "success": True,
            "message": f"Generated Dockerfile for {ptype} (port {port})",
        }

    def _step_build(self, app_name: str, config: dict, state: dict) -> dict:
        """Step 4: Build validation (deferred to Coolify)."""
        # For Coolify-built apps, the build happens during deploy
        # We just validate the config is ready
        if not config.get("repo_url"):
            return {"success": False, "error": "No repo_url in config"}
        return {
            "success": True,
            "message": f"Build ready: {config['repo_url']} (Coolify will build from Dockerfile)",
        }

    def _step_test(self, config: dict, state: dict) -> dict:
        """Step 5: Pre-deploy validation."""
        # Before Coolify deploy, we validate the config is sane
        checks = []
        if config.get("type", "unknown") == "unknown":
            return {"success": False, "error": "Project type is unknown"}
        checks.append(f"type={config['type']}")

        if not config.get("repo_url"):
            return {"success": False, "error": "No repo_url"}
        checks.append("repo_url=set")

        if config.get("has_dockerfile") or \
           (PROJECT_ROOT / "workspace" / "deploys" / config.get("app_name", "") / "Dockerfile").exists():
            checks.append("dockerfile=present")
        else:
            return {"success": False, "error": "No Dockerfile"}

        return {"success": True, "message": f"Pre-deploy checks passed: {', '.join(checks)}"}

    def _step_coolify(self, app_name: str, config: dict, state: dict) -> dict:
        """Step 6: Create or update Coolify application."""
        client = _get_coolify_client()
        repo_url = config.get("repo_url", "")
        branch = config.get("branch", "main")
        port = config.get("port", 3000)

        app_uuid = client.create_app(app_name, repo_url, branch, port)
        state["app_uuid"] = app_uuid

        # Configure FQDN
        domain = config.get("domain", generate_sslip_domain(app_name))
        client.configure_app(app_uuid, domain, port=port)

        # Set framework defaults
        defaults = get_framework_env_defaults(config.get("type", "node"), port)
        client.set_envs(app_uuid, defaults)

        # Inject secrets if needed
        env_vars = config.get("env_vars_needed", [])
        if env_vars:
            inject_secrets_to_coolify(client, app_uuid, env_vars)

        state["domain"] = domain
        _save_state(app_name, state)

        return {
            "success": True,
            "message": f"Coolify app created/updated: UUID={app_uuid}, domain={domain}",
        }

    def _step_database(self, app_name: str, config: dict, state: dict) -> dict:
        """Step 7: Provision PostgreSQL if needed."""
        if not config.get("needs_db"):
            return {"success": True, "message": "Database not needed (skipped)"}

        client = _get_coolify_client()
        app_uuid = state.get("app_uuid")
        if not app_uuid:
            return {"success": False, "error": "No app_uuid — run step 6 first"}

        db_name = app_name.replace("-", "_")
        db_pass = secrets.token_hex(24)
        db_uuid = client.create_postgres(app_name, db_name, db_pass, db_name)

        if db_uuid:
            # Store password in vault
            from python.helpers.vault import vault_store
            vault_store(f"{app_name}_postgres_password", db_pass)

            # Inject DATABASE_URL
            db_url = f"postgresql://{db_name}:{db_pass}@{app_name}-db:5432/{db_name}"
            client.set_env(app_uuid, "DATABASE_URL", db_url)

            state["db_uuid"] = db_uuid
            _save_state(app_name, state)
            return {"success": True, "message": f"PostgreSQL provisioned: {db_uuid}"}

        return {"success": False, "error": "Database creation failed"}

    def _step_deploy(self, app_name: str, config: dict, state: dict) -> dict:
        """Step 8: Trigger deployment and wait for completion."""
        client = _get_coolify_client()
        app_uuid = state.get("app_uuid")
        if not app_uuid:
            return {"success": False, "error": "No app_uuid — run step 6 first"}

        result = client.deploy_and_wait(app_uuid, timeout=600, poll_interval=15)
        state["deploy_uuid"] = result.get("deploy_uuid", "")
        state["deploy_status"] = result.get("status", "unknown")
        state["deploy_elapsed"] = result.get("elapsed", 0)
        _save_state(app_name, state)

        if result["success"]:
            return {
                "success": True,
                "message": f"Deployed in {result['elapsed']}s (UUID: {result['deploy_uuid']})",
            }
        return {
            "success": False,
            "error": f"Deploy {result.get('status', 'failed')}: "
                     f"{', '.join(result.get('logs', [])[:3])}",
        }

    def _step_dns(self, config: dict, state: dict) -> dict:
        """Step 9: Verify DNS resolution."""
        domain = config.get("domain", state.get("domain", ""))
        if not domain:
            return {"success": False, "error": "No domain configured"}

        hostname = domain.replace("http://", "").replace("https://", "").split("/")[0]

        # sslip.io domains contain the IP — always resolve
        if "31.220.58.212" in hostname:
            return {"success": True, "message": f"sslip.io domain: {hostname}"}

        ip = resolve_domain(domain)
        if ip:
            return {"success": True, "message": f"{hostname} → {ip}"}
        return {"success": False, "error": f"{hostname} does not resolve"}

    def _step_verify(self, config: dict) -> dict:
        """Step 10: External health check."""
        domain = config.get("domain", "")
        if not domain:
            return {"success": False, "error": "No domain"}

        result = health_check(domain, retries=5, delay=15)
        if result["healthy"]:
            return {
                "success": True,
                "message": f"Healthy! {result['endpoint']} → {result['status_code']} "
                           f"({result['response_time_ms']}ms, {result['attempts']} attempts)",
            }
        return {
            "success": False,
            "error": f"Health check failed after {result['attempts']} attempts: "
                     f"{result['errors'][-1] if result['errors'] else 'unknown'}",
        }

    def _step_report(self, app_name: str, config: dict, state: dict) -> dict:
        """Step 11: Generate deployment report."""
        report = {
            "app_name": app_name,
            "app_uuid": state.get("app_uuid"),
            "domain": config.get("domain", state.get("domain")),
            "type": config.get("type"),
            "port": config.get("port"),
            "deploy_uuid": state.get("deploy_uuid"),
            "deploy_elapsed": state.get("deploy_elapsed"),
            "db_uuid": state.get("db_uuid"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "LIVE",
        }

        # Save report
        report_path = PROJECT_ROOT / "workspace" / "deploys" / app_name / "report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        summary = (
            f"DEPLOYMENT REPORT — {app_name}\n"
            f"{'=' * 50}\n"
            f"  Status:  LIVE\n"
            f"  URL:     {report['domain']}\n"
            f"  UUID:    {report['app_uuid']}\n"
            f"  Type:    {report['type']}\n"
            f"  Port:    {report['port']}\n"
            f"  Deploy:  {report['deploy_uuid']} ({report['deploy_elapsed']}s)\n"
            f"  DB:      {report.get('db_uuid') or 'None'}\n"
            f"  Time:    {report['timestamp']}\n"
            f"{'=' * 50}"
        )

        return {"success": True, "message": summary}
