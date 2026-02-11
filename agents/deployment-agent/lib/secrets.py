"""
Secrets Manager — Vault integration for deployment
===================================================
Wraps vault_store/vault_load with deploy-specific logic:
  - Bulk import from .env files
  - Inject secrets into Coolify apps
  - Audit which secrets are present/missing
"""

import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.vault import vault_load, vault_store, vault_list


def vault_env_audit(required_keys: list[str]) -> dict[str, str]:
    """Check which required keys are in the vault.

    Returns:
        {key: "present"|"missing"} for each required key
    """
    existing = set(vault_list())
    result = {}
    for key in required_keys:
        normalized = key.lower().replace("-", "_")
        result[key] = "present" if normalized in existing else "missing"
    return result


def vault_import_env_file(env_path: str) -> dict[str, int]:
    """Import all secrets from a .env file into the vault.

    Returns:
        {"imported": N, "skipped": N, "errors": N}
    """
    stats = {"imported": 0, "skipped": 0, "errors": 0}
    p = Path(env_path)
    if not p.exists():
        return stats

    for line in p.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if not key or not value:
            stats["skipped"] += 1
            continue

        normalized = key.lower().replace("-", "_")
        try:
            existing = vault_load(normalized)
            if existing:
                stats["skipped"] += 1
            else:
                vault_store(normalized, value)
                stats["imported"] += 1
        except Exception:
            stats["errors"] += 1

    return stats


def inject_secrets_to_coolify(
    coolify_client,
    app_uuid: str,
    keys: list[str],
) -> dict[str, bool]:
    """Load secrets from vault and inject them into a Coolify app.

    Args:
        coolify_client: CoolifyClient instance
        app_uuid: Application UUID
        keys: List of env var keys to inject

    Returns:
        {key: success} for each key
    """
    results = {}
    for key in keys:
        normalized = key.lower().replace("-", "_")
        value = vault_load(normalized)
        if value:
            ok = coolify_client.set_env(app_uuid, key, value)
            results[key] = ok
        else:
            results[key] = False
    return results


def get_framework_env_defaults(project_type: str, port: int) -> dict[str, str]:
    """Get default env vars that should always be set for a given framework.

    These are non-secret config values that prevent common deployment failures.
    """
    defaults = {"PORT": str(port)}

    if project_type in ("flask", "python"):
        defaults["FLASK_HOST"] = "0.0.0.0"
        defaults["WEB_UI_HOST"] = "0.0.0.0"
        defaults["PYTHONUNBUFFERED"] = "1"
    elif project_type in ("django",):
        defaults["DJANGO_ALLOWED_HOSTS"] = "*"
        defaults["PYTHONUNBUFFERED"] = "1"
    elif project_type in ("fastapi",):
        defaults["HOST"] = "0.0.0.0"
        defaults["PYTHONUNBUFFERED"] = "1"
    elif project_type in ("nextjs", "nuxt", "node", "express"):
        defaults["HOST"] = "0.0.0.0"
        defaults["NODE_ENV"] = "production"
    elif project_type == "static":
        pass  # nginx handles everything

    return defaults
