"""
DNS Manager — sslip.io auto-domains + Cloudflare custom domains
================================================================
"""

import json
import urllib.error
import urllib.request
from typing import Any

VPS_IP = "31.220.58.212"


def generate_sslip_domain(app_name: str, ip: str = VPS_IP) -> str:
    """Generate an sslip.io auto-domain for the app."""
    # Sanitize app name
    name = app_name.lower().replace("_", "-").replace(" ", "-")
    return f"http://{name}.{ip}.sslip.io"


def create_cloudflare_record(
    zone_id: str,
    api_token: str,
    name: str,
    ip: str = VPS_IP,
    record_type: str = "A",
    proxied: bool = True,
) -> dict[str, Any]:
    """Create a DNS A record via Cloudflare API.

    Args:
        zone_id: Cloudflare zone ID
        api_token: Cloudflare API token
        name: Subdomain name (e.g. "myapp" → myapp.example.com)
        ip: Target IP address
        record_type: DNS record type (default: A)
        proxied: Enable Cloudflare proxy (default: True)

    Returns:
        {"ok": True, "record_id": "..."} or {"ok": False, "error": "..."}
    """
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "type": record_type,
        "name": name,
        "content": ip,
        "ttl": 1,  # Auto TTL
        "proxied": proxied,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )

    try:
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read().decode())
        if data.get("success"):
            return {"ok": True, "record_id": data["result"]["id"]}
        return {"ok": False, "error": str(data.get("errors", []))}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def resolve_domain(domain: str) -> str | None:
    """Quick DNS resolution check using a public resolver."""
    import socket
    try:
        # Strip protocol
        hostname = domain.replace("http://", "").replace("https://", "").split("/")[0]
        ip = socket.gethostbyname(hostname)
        return ip
    except socket.gaierror:
        return None
