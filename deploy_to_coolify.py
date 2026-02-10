#!/usr/bin/env python3
"""
Agent Claw — One-Click Coolify Cloud Deploy Script
===================================================
Deploys the full Agent Claw stack to your Hostinger VPS via Coolify Cloud API.

Usage:
    python deploy_to_coolify.py                           # uses vault token
    python deploy_to_coolify.py --token YOUR_NEW_TOKEN    # use fresh token
    python deploy_to_coolify.py --status                  # check deployment status

Prerequisites:
    1. Coolify Cloud account at https://app.coolify.io
    2. Valid Coolify API token (generate at app.coolify.io > Security > API Tokens)
    3. Server connected to Coolify Cloud (healthy-heron @ 31.220.58.212)
    4. GitHub repo accessible: executiveusa/agent-zero-Fork

Note: This targets Coolify CLOUD (app.coolify.io), not self-hosted Coolify.
      Cloud manages your server remotely through its control plane.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse

# ── Config ───────────────────────────────────────────────────
COOLIFY_URL = "https://app.coolify.io/api/v1"   # Coolify Cloud
SERVER_UUID = "zks8s40gsko0g0okkw04w4w8"         # healthy-heron via Cloud
APP_UUID_EXISTING = "h0skw08c4o80k8s08wws4g04"   # created app
GITHUB_REPO = "https://github.com/executiveusa/agent-zero-Fork"
GIT_BRANCH = "main"
APP_NAME = "agent-claw"
APP_FQDN = "http://agent-claw.31.220.58.212.sslip.io"
EXPOSED_PORTS = "5000"
BUILD_PACK = "dockerfile"
DOCKERFILE_LOCATION = "/Dockerfile.agent"

# Env vars to inject into the Coolify deployment (non-secret defaults)
DEFAULT_ENV = {
    "WEB_UI_PORT": "5000",
    "WEB_UI_HOST": "0.0.0.0",
    "DOCKER_MODE": "true",
    "PYTHONUNBUFFERED": "1",
    "POSTGRES_DB": "agentclaw",
    "POSTGRES_USER": "agentclaw",
    "A0_PERSISTENT_RUNTIME_ID": "0a4b48acbaf8f850066237c6bc1bc66a",
    "DEFAULT_USER_TIMEZONE": "America/Mexico_City",
    "DEFAULT_USER_UTC_OFFSET_MINUTES": "-360",
}

# Secrets to pull from vault and inject
VAULT_SECRETS = [
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "VENICE_API_KEY",
    "ELEVENLABS_API_KEY",
    "COMPOSIO_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_PHONE_NUMBER",
    "GH_PAT",
    "NOTION_API_TOKEN",
    "STRIPE_SECRET_KEY",
]


def get_token():
    """Get Coolify API token from args or vault."""
    # Check command line
    if "--token" in sys.argv:
        idx = sys.argv.index("--token")
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]

    # Check environment
    if os.getenv("COOLIFY_API_TOKEN"):
        return os.getenv("COOLIFY_API_TOKEN")

    # Try vault
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from python.helpers.vault import vault_load
        for key in ["coolify_api_token", "coolify_api_token_alt", "coolify_api_token_alt2"]:
            val = vault_load(key)
            if val:
                return val
    except Exception:
        pass

    print("ERROR: No Coolify API token found.")
    print("Generate one at: https://app.coolify.io/security/api-tokens")
    print("Then run: python deploy_to_coolify.py --token YOUR_TOKEN")
    sys.exit(1)


def coolify_request(method, path, token, data=None):
    """Make a Coolify API request."""
    url = f"{COOLIFY_URL}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "AgentClaw/1.0 (deploy-script)",  # Required for Cloudflare
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        raw = resp.read().decode()
        return {"status": resp.status, "data": json.loads(raw) if raw else {}}
    except urllib.error.HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode()
        except Exception:
            pass
        return {"status": e.code, "error": e.reason, "body": body_text}
    except Exception as e:
        return {"status": 0, "error": str(e)}


def check_auth(token):
    """Verify the token works."""
    result = coolify_request("GET", "/teams", token)
    if result["status"] == 200:
        print("[OK] Coolify API authenticated")
        return True
    else:
        print(f"[FAIL] Auth check failed: {result}")
        return False


def find_or_create_project(token):
    """Find the Agent Claw project or create it."""
    result = coolify_request("GET", "/projects", token)
    if result["status"] != 200:
        print(f"[FAIL] Could not list projects: {result}")
        sys.exit(1)

    # Look for existing project
    for proj in result["data"]:
        if "agent" in proj.get("name", "").lower() or "claw" in proj.get("name", "").lower():
            print(f"[OK] Found existing project: {proj['name']} ({proj['uuid']})")
            return proj["uuid"], proj.get("environments", [{}])[0].get("name", "production")

    # Create new project
    print("[INFO] Creating Agent Claw project...")
    create_result = coolify_request("POST", "/projects", token, {
        "name": "Agent Claw",
        "description": "Autonomous AI Agency - $100M by 2030"
    })
    if create_result["status"] in (200, 201):
        uuid = create_result["data"].get("uuid")
        print(f"[OK] Created project: {uuid}")
        return uuid, "production"
    else:
        print(f"[FAIL] Could not create project: {create_result}")
        # Fallback to first project
        if result["data"]:
            proj = result["data"][0]
            print(f"[FALLBACK] Using project: {proj['name']} ({proj['uuid']})")
            return proj["uuid"], proj.get("environments", [{}])[0].get("name", "production")
        sys.exit(1)


def find_existing_app(token):
    """Check if agent-claw app already exists."""
    result = coolify_request("GET", "/applications", token)
    if result["status"] != 200:
        return None

    for app in result["data"]:
        name = app.get("name", "").lower()
        if "agent-claw" in name or "agent-zero" in name:
            print(f"[OK] Found existing app: {app['name']} ({app['uuid']}) - Status: {app.get('status')}")
            return app["uuid"]
    return None


def create_app(token, project_uuid, env_name):
    """Create the Agent Claw application in Coolify."""
    payload = {
        "server_uuid": SERVER_UUID,
        "project_uuid": project_uuid,
        "environment_name": env_name,
        "git_repository": GITHUB_REPO,
        "git_branch": GIT_BRANCH,
        "build_pack": BUILD_PACK,
        "ports_exposes": EXPOSED_PORTS,
        "name": APP_NAME,
        "description": "Agent Claw - Autonomous AI Agency (Python Flask + SYNTHIA Dashboard)",
        "dockerfile_location": DOCKERFILE_LOCATION,
        "instant_deploy": False,
        "type": "public",
    }
    result = coolify_request("POST", "/applications/public", token, payload)
    if result["status"] in (200, 201):
        uuid = result["data"].get("uuid")
        print(f"[OK] Created application: {uuid}")
        return uuid
    else:
        print(f"[FAIL] Could not create app: {result}")
        sys.exit(1)


def configure_app(token, app_uuid):
    """Set domain, health check, and other settings."""
    config = {
        "name": APP_NAME,
        "fqdn": APP_FQDN,
        "health_check_enabled": True,
        "health_check_path": "/health",
        "health_check_port": "5000",
        "health_check_interval": 30,
        "health_check_timeout": 10,
        "health_check_retries": 3,
        "health_check_start_period": 60,
    }
    result = coolify_request("PATCH", f"/applications/{app_uuid}", token, config)
    if result["status"] == 200:
        print(f"[OK] Configured app: FQDN={APP_FQDN}")
    else:
        print(f"[WARN] Config update: {result}")


def set_env_vars(token, app_uuid):
    """Set environment variables from defaults and vault."""
    # Set default (non-secret) env vars
    for key, value in DEFAULT_ENV.items():
        result = coolify_request("POST", f"/applications/{app_uuid}/envs", token, {
            "key": key,
            "value": value,
            "is_preview": False,
        })
        status = "OK" if result["status"] in (200, 201) else "SKIP"
        print(f"  [{status}] {key}")

    # Set secrets from vault
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from python.helpers.vault import vault_load
        for key in VAULT_SECRETS:
            val = vault_load(key.lower())
            if val:
                result = coolify_request("POST", f"/applications/{app_uuid}/envs", token, {
                    "key": key,
                    "value": val,
                    "is_preview": False,
                })
                status = "OK" if result["status"] in (200, 201) else "SKIP"
                print(f"  [{status}] {key} (from vault)")
            else:
                print(f"  [SKIP] {key} (not in vault)")
    except Exception as e:
        print(f"  [WARN] Could not load vault: {e}")
        print("  Set secrets manually in Coolify dashboard")


def deploy_app(token, app_uuid):
    """Trigger deployment via /start endpoint (Coolify Cloud)."""
    # Coolify Cloud uses /start, not /deploy
    result = coolify_request("POST", f"/applications/{app_uuid}/start", token, {})
    if result["status"] in (200, 201):
        deployment_uuid = result.get("data", {}).get("deployment_uuid")
        print(f"[OK] Deployment triggered: {deployment_uuid}")
        return deployment_uuid
    else:
        print(f"[FAIL] Deploy failed: {result}")
        # Fallback to /deploy endpoint
        result2 = coolify_request("POST", f"/applications/{app_uuid}/deploy", token, {"force": True})
        if result2["status"] in (200, 201):
            deployment_uuid = result2.get("data", {}).get("deployment_uuid")
            print(f"[OK] Deploy triggered via fallback: {deployment_uuid}")
            return deployment_uuid
        print(f"[FAIL] Fallback also failed: {result2}")
        return None


def wait_for_deployment(token, app_uuid, timeout=300):
    """Wait for deployment to complete."""
    print(f"\n[INFO] Waiting for deployment (timeout: {timeout}s)...")
    start = time.time()
    while time.time() - start < timeout:
        result = coolify_request("GET", f"/applications/{app_uuid}", token)
        if result["status"] == 200:
            status = result["data"].get("status", "unknown")
            print(f"  Status: {status} ({int(time.time() - start)}s)")
            if "running" in status.lower():
                return True
            if "error" in status.lower() or "exited" in status.lower():
                print(f"[FAIL] Deployment failed with status: {status}")
                return False
        time.sleep(15)
    print("[WARN] Deployment timed out")
    return False


def health_check():
    """Test the live app."""
    print(f"\n[INFO] Health checking {APP_FQDN}...")
    for attempt in range(5):
        try:
            req = urllib.request.Request(f"{APP_FQDN}/health", method="GET")
            resp = urllib.request.urlopen(req, timeout=10)
            data = resp.read().decode()
            print(f"[OK] Health check passed (HTTP {resp.status})")
            print(f"  Response: {data[:200]}")
            return True
        except Exception as e:
            print(f"  Attempt {attempt + 1}/5: {str(e)[:60]}")
            time.sleep(10)
    print("[FAIL] Health check failed after 5 attempts")
    return False


def check_status(token):
    """Check current deployment status."""
    app_uuid = find_existing_app(token)
    if not app_uuid:
        print("[INFO] No agent-claw app found in Coolify")
        return

    result = coolify_request("GET", f"/applications/{app_uuid}", token)
    if result["status"] == 200:
        app = result["data"]
        print(f"\nApp: {app.get('name')}")
        print(f"UUID: {app.get('uuid')}")
        print(f"Status: {app.get('status')}")
        print(f"FQDN: {app.get('fqdn')}")
        print(f"Branch: {app.get('git_branch')}")
        print(f"Build Pack: {app.get('build_pack')}")


def main():
    print("=" * 60)
    print("Agent Claw - Coolify Deployment")
    print(f"Target: {COOLIFY_URL} (Coolify Cloud)")
    print(f"Server: healthy-heron @ 31.220.58.212 (UUID: {SERVER_UUID})")
    print(f"App: {APP_NAME} -> {APP_FQDN}")
    print("=" * 60)

    token = get_token()

    # Status check mode
    if "--status" in sys.argv:
        if check_auth(token):
            check_status(token)
        return

    # Auth check
    if not check_auth(token):
        print("\nToken expired. Generate a new one at:")
        print(f"  https://app.coolify.io/security/api-tokens")
        print("\nThen run:")
        print(f"  python deploy_to_coolify.py --token YOUR_NEW_TOKEN")
        sys.exit(1)

    # Check for existing app
    app_uuid = find_existing_app(token)

    if not app_uuid:
        # Check for pre-created app UUID
        if APP_UUID_EXISTING:
            app_uuid = APP_UUID_EXISTING
            print(f"[OK] Using pre-created app: {app_uuid}")
        else:
            # Create project and app
            project_uuid, env_name = find_or_create_project(token)
            app_uuid = create_app(token, project_uuid, env_name)

    # Configure
    print("\n--- Configuration ---")
    configure_app(token, app_uuid)

    # Environment variables
    print("\n--- Environment Variables ---")
    set_env_vars(token, app_uuid)

    # Deploy
    print("\n--- Deploying ---")
    deployment_uuid = deploy_app(token, app_uuid)

    if deployment_uuid:
        success = wait_for_deployment(token, app_uuid, timeout=300)
        if success:
            health_check()
            print(f"\n{'=' * 60}")
            print(f"DEPLOYMENT COMPLETE")
            print(f"Dashboard: {APP_FQDN}")
            print(f"Coolify:   https://app.coolify.io")
            print(f"{'=' * 60}")
        else:
            print(f"\nCheck logs at: https://app.coolify.io")
    else:
        print("\nDeployment not triggered. Check Coolify dashboard at https://app.coolify.io")


if __name__ == "__main__":
    main()
