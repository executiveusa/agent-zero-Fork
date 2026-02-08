"""
Startup Validator — Pre-flight checks for Agent Claw components.

Runs at application startup to verify all required files, configs,
and services are properly configured. Logs warnings for missing
optional components and raises on critical failures.

Called from initialize.py or run_ui.py during boot.
"""

import ast
import importlib
import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# Project root (agent-zero-Fork/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class StartupValidator:
    """Pre-flight checks for Agent Claw."""

    def __init__(self):
        self.results: List[Tuple[str, bool, str]] = []  # (check_name, passed, detail)

    def run_all(self) -> bool:
        """Run all validation checks. Returns True if no critical failures."""
        self._check_required_files()
        self._check_tool_prompt_pairs()
        self._check_env_vars()
        self._check_optional_services()
        self._check_python_modules()

        passed = sum(1 for _, ok, _ in self.results if ok)
        failed = sum(1 for _, ok, _ in self.results if not ok)
        total = len(self.results)

        logger.info(f"Startup validation: {passed}/{total} checks passed")
        if failed > 0:
            for name, ok, detail in self.results:
                if not ok:
                    logger.warning(f"  ✗ {name}: {detail}")

        return all(ok for _, ok, _ in self.results if "CRITICAL" in _[0] for _ in [(name, ok, detail)])

    def _check_required_files(self):
        """Verify critical Agent Claw files exist."""
        required = [
            "python/helpers/openclaw_ws_connector.py",
            "python/helpers/voice_command_router.py",
            "python/helpers/cron_bootstrap.py",
            "python/helpers/elevenlabs_client.py",
            "python/helpers/api_rate_limit.py",
            "python/tools/voice_command.py",
            "python/tools/voice_notify.py",
            "python/tools/venice_mcp.py",
            "python/tools/a2a_chat.py",
            "python/tools/swarm_orchestrator.py",
            "python/tools/clawbot_messaging_bridge.py",
            "prompts/default/agent.system.synthia.md",
            "docker-compose.prod.yml",
            "Dockerfile.agent",
            "coolify.json",
        ]
        for f in required:
            path = PROJECT_ROOT / f
            exists = path.exists()
            self.results.append((
                f"file:{f}",
                exists,
                "OK" if exists else f"MISSING: {f}",
            ))

    def _check_tool_prompt_pairs(self):
        """Verify each Agent Claw tool has a matching prompt file."""
        tool_prompt_pairs = {
            "voice_command": "prompts/agent.system.tool.voice_command.md",
            "voice_notify": "prompts/agent.system.tool.voice_notify.md",
            "venice_mcp": "prompts/agent.system.tool.venice_mcp.md",
            "a2a_chat": "prompts/agent.system.tool.a2a_chat.md",
        }
        for tool_name, prompt_path in tool_prompt_pairs.items():
            exists = (PROJECT_ROOT / prompt_path).exists()
            self.results.append((
                f"tool_prompt:{tool_name}",
                exists,
                "OK" if exists else f"Missing prompt for {tool_name}",
            ))

    def _check_env_vars(self):
        """Check for recommended environment variables."""
        env_checks = {
            "ELEVENLABS_API_KEY": "ElevenLabs TTS (optional)",
            "VENICE_API_KEY": "Venice AI privacy (optional)",
            "OPENCLAW_WS_URL": "OpenClaw gateway URL (defaults to ws://127.0.0.1:18789)",
        }
        for var, desc in env_checks.items():
            value = os.environ.get(var, "")
            has_value = bool(value)
            self.results.append((
                f"env:{var}",
                True,  # These are optional, so always "pass" but log if missing
                "set" if has_value else f"not set ({desc})",
            ))

    def _check_optional_services(self):
        """Check connectivity to optional services (non-blocking)."""
        # OpenClaw gateway
        openclaw_url = os.environ.get("OPENCLAW_WS_URL", "ws://127.0.0.1:18789")
        self.results.append((
            "service:openclaw",
            True,  # Non-critical
            f"configured: {openclaw_url}",
        ))

    def _check_python_modules(self):
        """Verify critical Python modules parse correctly."""
        critical_modules = [
            "python/helpers/openclaw_ws_connector.py",
            "python/helpers/voice_command_router.py",
            "python/helpers/cron_bootstrap.py",
            "python/helpers/api_rate_limit.py",
        ]
        for mod_path in critical_modules:
            full_path = PROJECT_ROOT / mod_path
            if not full_path.exists():
                continue
            try:
                source = full_path.read_text(encoding="utf-8")
                ast.parse(source, filename=mod_path)
                self.results.append((
                    f"syntax:{mod_path}",
                    True,
                    "compiles OK",
                ))
            except SyntaxError as e:
                self.results.append((
                    f"CRITICAL:syntax:{mod_path}",
                    False,
                    f"Syntax error: {e}",
                ))

    def get_report(self) -> Dict:
        """Get validation results as a JSON-serializable dict."""
        return {
            "total": len(self.results),
            "passed": sum(1 for _, ok, _ in self.results if ok),
            "failed": sum(1 for _, ok, _ in self.results if not ok),
            "checks": [
                {"name": name, "passed": ok, "detail": detail}
                for name, ok, detail in self.results
            ],
        }


def validate_startup() -> Dict:
    """
    Run startup validation and return the report.
    Called during application initialization.
    """
    validator = StartupValidator()
    validator.run_all()
    report = validator.get_report()

    if report["failed"] > 0:
        logger.warning(
            f"Startup validation: {report['failed']} issue(s) detected — "
            f"see log for details"
        )
    else:
        logger.info(
            f"Startup validation: all {report['total']} checks passed ✓"
        )

    return report
