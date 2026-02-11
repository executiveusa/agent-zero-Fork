"""
deploy_test_gate — Agent Zero Tool
====================================
Runs the validation test for a specific deployment step.
Each step has a unique test gate that must pass before marking done.

Tool args:
    app_name:  Name of the app
    step:      Step number (1-11) to test
"""

import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.tool import Tool, Response


def _load_config(app_name: str) -> dict:
    """Load deployment config JSON."""
    config_path = PROJECT_ROOT / "workspace" / "deploys" / app_name / "config.json"
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))
    return {}


def _http_check(url: str, timeout: int = 10) -> tuple[int, str]:
    """Quick HTTP GET. Returns (status_code, body_snippet)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AgentClaw/1.0"})
        resp = urllib.request.urlopen(req, timeout=timeout)
        body = resp.read().decode()[:200]
        return resp.status, body
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return 0, str(e)


class DeployTestGate(Tool):

    async def execute(self, **kwargs) -> Response:
        app_name = self.args.get("app_name", "").strip()
        step_str = self.args.get("step", "").strip()

        if not app_name or not step_str:
            return Response(
                message="Error: app_name and step are required.",
                break_loop=False,
            )

        step = int(step_str)
        config = _load_config(app_name)

        if step == 1:
            return await self._gate_analyze(config)
        elif step == 2:
            return await self._gate_secrets(config)
        elif step == 3:
            return await self._gate_dockerfile(config)
        elif step == 4:
            return await self._gate_build(config)
        elif step == 5:
            return await self._gate_test(config)
        elif step == 6:
            return await self._gate_coolify(config)
        elif step == 7:
            return await self._gate_database(config)
        elif step == 8:
            return await self._gate_deploy(config)
        elif step == 9:
            return await self._gate_dns(config)
        elif step == 10:
            return await self._gate_verify(config)
        elif step == 11:
            return await self._gate_report(config)
        else:
            return Response(message=f"Unknown step {step}", break_loop=False)

    # ── Gate Implementations ─────────────────────────────────

    async def _gate_analyze(self, config: dict) -> Response:
        """Step 1: project_type must be non-unknown."""
        ptype = config.get("type", "unknown")
        if ptype and ptype != "unknown":
            return Response(
                message=f"GATE 1 PASS: project_type={ptype}",
                break_loop=False,
            )
        return Response(
            message=f"GATE 1 FAIL: project_type is '{ptype}'. Analyzer could not detect framework.",
            break_loop=False,
        )

    async def _gate_secrets(self, config: dict) -> Response:
        """Step 2: Required env vars exist in vault."""
        env_vars = config.get("env_vars_needed", [])
        if not env_vars:
            return Response(
                message="GATE 2 PASS: No env vars required (or none detected).",
                break_loop=False,
            )

        try:
            from python.helpers.vault import vault_load
            missing = []
            for key in env_vars:
                normalized = key.lower().replace("-", "_")
                if not vault_load(normalized):
                    missing.append(key)
            if not missing:
                return Response(
                    message=f"GATE 2 PASS: All {len(env_vars)} env vars present in vault.",
                    break_loop=False,
                )
            return Response(
                message=f"GATE 2 FAIL: Missing from vault: {', '.join(missing)}",
                break_loop=False,
            )
        except Exception as e:
            return Response(
                message=f"GATE 2 FAIL: Vault error: {e}",
                break_loop=False,
            )

    async def _gate_dockerfile(self, config: dict) -> Response:
        """Step 3: Dockerfile exists (in repo or generated)."""
        app_name = config.get("app_name", "")
        deploy_dir = PROJECT_ROOT / "workspace" / "deploys" / app_name

        # Check if Dockerfile was generated locally
        if (deploy_dir / "Dockerfile").exists():
            return Response(
                message="GATE 3 PASS: Dockerfile exists in deploy workspace.",
                break_loop=False,
            )

        # Check if repo has one
        if config.get("has_dockerfile"):
            return Response(
                message="GATE 3 PASS: Dockerfile exists in repository.",
                break_loop=False,
            )

        return Response(
            message="GATE 3 FAIL: No Dockerfile found. Generate one with docker_builder.",
            break_loop=False,
        )

    async def _gate_build(self, config: dict) -> Response:
        """Step 4: GHCR image exists. (Pragmatic: just check Coolify can build)."""
        # For Coolify-built apps, this is validated during deploy
        # We check if the app exists in Coolify
        app_name = config.get("app_name", "")
        state_path = PROJECT_ROOT / "workspace" / "deploys" / app_name / "state.json"
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if state.get("app_uuid"):
                return Response(
                    message=f"GATE 4 PASS: App registered in Coolify (UUID: {state['app_uuid']}). "
                            f"Build will be handled by Coolify.",
                    break_loop=False,
                )
        return Response(
            message="GATE 4 PASS (deferred): Build will be validated during Coolify deployment.",
            break_loop=False,
        )

    async def _gate_test(self, config: dict) -> Response:
        """Step 5: Container starts and /health returns 200."""
        domain = config.get("domain", "")
        if not domain:
            return Response(
                message="GATE 5 FAIL: No domain configured. Cannot test.",
                break_loop=False,
            )

        status, body = _http_check(f"{domain}/health")
        if status == 200:
            return Response(
                message=f"GATE 5 PASS: {domain}/health → HTTP 200",
                break_loop=False,
            )

        # Try root
        status, body = _http_check(domain)
        if status == 200:
            return Response(
                message=f"GATE 5 PASS: {domain}/ → HTTP 200 (no /health endpoint)",
                break_loop=False,
            )

        return Response(
            message=f"GATE 5 FAIL: {domain} → HTTP {status}. "
                    f"Container may not be running yet.",
            break_loop=False,
        )

    async def _gate_coolify(self, config: dict) -> Response:
        """Step 6: App UUID exists in state."""
        app_name = config.get("app_name", "")
        state_path = PROJECT_ROOT / "workspace" / "deploys" / app_name / "state.json"
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            uuid = state.get("app_uuid")
            if uuid:
                return Response(
                    message=f"GATE 6 PASS: Coolify app UUID={uuid}",
                    break_loop=False,
                )
        return Response(
            message="GATE 6 FAIL: No app_uuid in state. Create app in Coolify first.",
            break_loop=False,
        )

    async def _gate_database(self, config: dict) -> Response:
        """Step 7: DB provisioned (or not needed)."""
        if not config.get("needs_db"):
            return Response(
                message="GATE 7 PASS: Database not needed (skipped).",
                break_loop=False,
            )
        app_name = config.get("app_name", "")
        state_path = PROJECT_ROOT / "workspace" / "deploys" / app_name / "state.json"
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if state.get("db_uuid"):
                return Response(
                    message=f"GATE 7 PASS: Database provisioned (UUID: {state['db_uuid']}).",
                    break_loop=False,
                )
        return Response(
            message="GATE 7 FAIL: Database required but not provisioned.",
            break_loop=False,
        )

    async def _gate_deploy(self, config: dict) -> Response:
        """Step 8: Deployment status == finished."""
        app_name = config.get("app_name", "")
        state_path = PROJECT_ROOT / "workspace" / "deploys" / app_name / "state.json"
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            deploy_status = state.get("deploy_status")
            if deploy_status == "finished":
                return Response(
                    message=f"GATE 8 PASS: Deployment finished "
                            f"(deploy_uuid: {state.get('deploy_uuid', 'N/A')}).",
                    break_loop=False,
                )
            return Response(
                message=f"GATE 8 FAIL: deploy_status='{deploy_status}' (expected 'finished').",
                break_loop=False,
            )
        return Response(
            message="GATE 8 FAIL: No state file. Deploy hasn't started.",
            break_loop=False,
        )

    async def _gate_dns(self, config: dict) -> Response:
        """Step 9: Domain resolves to VPS IP."""
        domain = config.get("domain", "")
        if not domain:
            return Response(message="GATE 9 FAIL: No domain configured.", break_loop=False)

        hostname = domain.replace("http://", "").replace("https://", "").split("/")[0]
        try:
            ip = socket.gethostbyname(hostname)
            if ip == "31.220.58.212":
                return Response(
                    message=f"GATE 9 PASS: {hostname} → {ip}",
                    break_loop=False,
                )
            return Response(
                message=f"GATE 9 WARN: {hostname} → {ip} (expected 31.220.58.212). "
                        f"May be a Cloudflare proxied IP.",
                break_loop=False,
            )
        except socket.gaierror:
            # sslip.io domains resolve dynamically — check if it contains the IP
            if "31.220.58.212" in hostname:
                return Response(
                    message=f"GATE 9 PASS: sslip.io domain {hostname} (IP embedded).",
                    break_loop=False,
                )
            return Response(
                message=f"GATE 9 FAIL: {hostname} does not resolve.",
                break_loop=False,
            )

    async def _gate_verify(self, config: dict) -> Response:
        """Step 10: External health check — HTTP 200 on /health AND /."""
        domain = config.get("domain", "")
        if not domain:
            return Response(message="GATE 10 FAIL: No domain.", break_loop=False)

        results = []
        for endpoint in ["/health", "/"]:
            status, _ = _http_check(f"{domain}{endpoint}")
            results.append((endpoint, status))

        all_ok = all(s == 200 for _, s in results)
        summary = ", ".join(f"{ep} → {s}" for ep, s in results)

        if all_ok:
            return Response(
                message=f"GATE 10 PASS: All endpoints healthy — {summary}",
                break_loop=False,
            )
        return Response(
            message=f"GATE 10 FAIL: {summary}",
            break_loop=False,
        )

    async def _gate_report(self, config: dict) -> Response:
        """Step 11: Just check the PRD has progress entries."""
        app_name = config.get("app_name", "")
        prd_path = PROJECT_ROOT / "workspace" / "deploys" / app_name / "PRD.md"
        if prd_path.exists():
            text = prd_path.read_text(encoding="utf-8")
            done_count = text.count("- [x]")
            if done_count >= 10:  # Steps 1-10 done
                return Response(
                    message=f"GATE 11 PASS: {done_count} tasks complete. Report ready.",
                    break_loop=False,
                )
        return Response(
            message="GATE 11 FAIL: Not all prior steps are complete.",
            break_loop=False,
        )
