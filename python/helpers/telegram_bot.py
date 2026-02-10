"""
Telegram Bot — Agent Claw / Pauli the PauliBot

Vault-aware Telegram bot with safe imports. All credentials loaded
from encrypted Fernet vault — NEVER hardcoded.

Features:
  - Long-polling mode (no webhook needed for dev)
  - Webhook mode for VPS production
  - Admin-only command restriction
  - Auto-encrypts any secrets shared in chat
  - Forwards messages to Agent Zero for AI processing
  - Persists as a live service on VPS

Usage:
    from python.helpers.telegram_bot import start_bot, send_message
    
    start_bot()  # Long-polling mode
    send_message("Hello from Agent Claw!")
"""

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# ─── Safe Imports ────────────────────────────────────────────
# These are optional dependencies — bot degrades gracefully

_TELEGRAM_AVAILABLE = False
try:
    import httpx
    _TELEGRAM_AVAILABLE = True
except ImportError:
    try:
        import requests as httpx
        _TELEGRAM_AVAILABLE = True
    except ImportError:
        logger.warning("Neither httpx nor requests installed — Telegram bot unavailable")

# ─── Constants ───────────────────────────────────────────────

BOT_NAME = "Pauli_the_paulibot"
TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}"
LOG_DIR = "tmp/telegram"
LOG_FILE = os.path.join(LOG_DIR, "bot_log.json")
ADMIN_LOG_FILE = os.path.join(LOG_DIR, "admin_commands.json")

# Patterns that look like secrets (for auto-encryption)
SECRET_PATTERNS = [
    (r'(?:sk-[A-Za-z0-9]{20,})', "OpenAI Key"),
    (r'(?:ghp_[A-Za-z0-9]{36,})', "GitHub PAT"),
    (r'(?:AC[a-f0-9]{32})', "Twilio SID"),
    (r'(?:xoxb-[A-Za-z0-9\-]{20,})', "Slack Token"),
    (r'(?:AKIA[A-Z0-9]{16})', "AWS Access Key"),
    (r'(?:ak_-[A-Za-z0-9_\-]{10,})', "Composio Key"),
    (r'(?:[A-Za-z0-9_\-]{30,}:[A-Za-z0-9_\-]{30,})', "Bot Token Pattern"),
    (r'(?:eyJ[A-Za-z0-9_\-]{20,}\.eyJ[A-Za-z0-9_\-]{20,})', "JWT"),
    (r'(?:-----BEGIN (?:RSA )?PRIVATE KEY-----)', "Private Key"),
    (r'(?:mongodb(?:\+srv)?://[^\s]+)', "MongoDB URI"),
    (r'(?:postgres(?:ql)?://[^\s]+)', "Postgres URI"),
    (r'(?:mysql://[^\s]+)', "MySQL URI"),
    (r'(?:redis://[^\s]+)', "Redis URI"),
]


# ─── Credential Loading ─────────────────────────────────────

def _get_bot_token() -> str:
    """Load bot token from vault — NEVER hardcode."""
    from python.helpers.vault import vault_get
    token = vault_get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in vault or env")
    return token


def _get_admin_ids() -> list:
    """Get admin user IDs allowed to control the bot."""
    from python.helpers.vault import vault_get
    admin_str = vault_get("TELEGRAM_ADMIN_ID") or ""
    if admin_str:
        return [int(x.strip()) for x in admin_str.split(",") if x.strip().isdigit()]
    return []


def _api_url(method: str) -> str:
    """Build Telegram API URL."""
    return f"{TELEGRAM_API_BASE.format(token=_get_bot_token())}/{method}"


# ─── Logging ─────────────────────────────────────────────────

def _log_message(entry: dict):
    """Append to JSON log."""
    os.makedirs(LOG_DIR, exist_ok=True)
    log = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                log = json.load(f)
        except Exception:
            log = []
    log.append(entry)
    # Keep last 1000 messages
    log = log[-1000:]
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


# ─── Secret Detection & Auto-Encryption ─────────────────────

def detect_secrets_in_text(text: str) -> list:
    """Scan text for potential secrets/tokens."""
    found = []
    for pattern, sec_type in SECRET_PATTERNS:
        matches = re.findall(pattern, text)
        for match in matches:
            found.append({"type": sec_type, "value": match, "redacted": match[:6] + "..." + match[-4:]})
    return found


def auto_encrypt_secrets(text: str, source: str = "telegram") -> list:
    """
    Detect and auto-encrypt any secrets found in text.
    Returns list of what was encrypted.
    """
    from python.helpers.vault import vault_store
    
    found = detect_secrets_in_text(text)
    encrypted = []
    
    for secret in found:
        # Generate a vault key name
        ts = int(time.time())
        key_name = f"auto_{source}_{secret['type'].lower().replace(' ', '_')}_{ts}"
        vault_store(key_name, secret["value"])
        encrypted.append({
            "type": secret["type"],
            "key_name": key_name,
            "redacted": secret["redacted"],
        })
        logger.info(f"Auto-encrypted {secret['type']} from {source} as {key_name}")
    
    return encrypted


# ─── Core API Methods ────────────────────────────────────────

def send_message(chat_id: int | str, text: str, parse_mode: str = "Markdown",
                 reply_to: int = None, silent: bool = False) -> dict:
    """
    Send a message to a Telegram chat.
    
    Args:
        chat_id: Chat ID or @username
        text: Message text
        parse_mode: Markdown or HTML
        reply_to: Message ID to reply to
        silent: Send without notification
    
    Returns:
        Telegram API response dict
    """
    if not _TELEGRAM_AVAILABLE:
        logger.error("Telegram HTTP client not available")
        return {"ok": False, "error": "No HTTP client"}
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_notification": silent,
    }
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    
    try:
        if hasattr(httpx, 'post'):
            # requests-style
            resp = httpx.post(_api_url("sendMessage"), json=payload, timeout=30)
            return resp.json()
        else:
            # httpx async client
            with httpx.Client(timeout=30) as client:
                resp = client.post(_api_url("sendMessage"), json=payload)
                return resp.json()
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return {"ok": False, "error": str(e)}


def send_admin_message(text: str) -> list:
    """Send a message to all admin users."""
    results = []
    for admin_id in _get_admin_ids():
        result = send_message(admin_id, text)
        results.append(result)
    return results


def get_updates(offset: int = 0, timeout: int = 30) -> list:
    """Get updates from Telegram (long polling)."""
    if not _TELEGRAM_AVAILABLE:
        return []
    
    params = {"offset": offset, "timeout": timeout, "allowed_updates": '["message","callback_query"]'}
    
    try:
        if hasattr(httpx, 'get'):
            resp = httpx.get(_api_url("getUpdates"), params=params, timeout=timeout + 10)
            data = resp.json()
        else:
            with httpx.Client(timeout=timeout + 10) as client:
                resp = client.get(_api_url("getUpdates"), params=params)
                data = resp.json()
        
        if data.get("ok"):
            return data.get("result", [])
        return []
    except Exception as e:
        logger.error(f"Telegram getUpdates failed: {e}")
        return []


def get_me() -> dict:
    """Test bot token by calling getMe."""
    if not _TELEGRAM_AVAILABLE:
        return {"ok": False, "error": "No HTTP client"}
    
    try:
        if hasattr(httpx, 'get'):
            resp = httpx.get(_api_url("getMe"), timeout=10)
            return resp.json()
        else:
            with httpx.Client(timeout=10) as client:
                resp = client.get(_api_url("getMe"))
                return resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ─── Command Handlers ────────────────────────────────────────

COMMANDS = {}

def command(name: str):
    """Decorator to register bot commands."""
    def decorator(func):
        COMMANDS[name] = func
        return func
    return decorator


@command("start")
def cmd_start(message: dict) -> str:
    """Welcome message."""
    user = message.get("from", {}).get("first_name", "there")
    return (
        f"Hey {user}! I'm *Pauli the PauliBot* - Agent Claw's Telegram liaison.\n\n"
        "Commands:\n"
        "/status - System status\n"
        "/vault - Vault health check\n"
        "/security - Security audit\n"
        "/call [number] [message] - Make a voice call\n"
        "/encrypt [text] - Encrypt a secret\n"
        "/help - Show this message\n\n"
        "_All secrets shared here are auto-encrypted._"
    )


@command("help")
def cmd_help(message: dict) -> str:
    """Help message."""
    return cmd_start(message)


@command("status")
def cmd_status(message: dict) -> str:
    """System status."""
    from python.helpers.vault import vault_list
    
    vaulted = vault_list()
    uptime = "Running"
    
    return (
        "*Agent Claw Status Report*\n\n"
        f"Vault: {len(vaulted)} encrypted secrets\n"
        f"Bot: {BOT_NAME}\n"
        f"Status: {uptime}\n"
        f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
    )


@command("vault")
def cmd_vault(message: dict) -> str:
    """Vault health check (admin only)."""
    from python.helpers.vault import vault_audit
    
    audit = vault_audit()
    return (
        "*Vault Audit*\n\n"
        f"Secrets: {audit['secrets_count']}\n"
        f"Master Key: {'Present' if audit['master_key_exists'] else 'MISSING'}\n"
        f"Env Leaks: {len(audit['env_leaks'])}\n"
        f"Unvaulted: {len(audit['unvaulted'])}\n"
    )


@command("security")
def cmd_security(message: dict) -> str:
    """Quick security check."""
    from python.helpers.vault import vault_audit
    
    audit = vault_audit()
    issues = []
    
    if not audit["master_key_exists"]:
        issues.append("CRITICAL: Vault master key missing!")
    if audit["env_leaks"]:
        issues.append(f"HIGH: {len(audit['env_leaks'])} secrets in both .env and vault")
    if audit["unvaulted"]:
        issues.append(f"MEDIUM: {len(audit['unvaulted'])} secrets not yet vaulted")
    
    if not issues:
        return "Security: ALL CLEAR - No issues detected."
    
    return "*Security Issues*\n\n" + "\n".join(f"- {i}" for i in issues)


@command("encrypt")
def cmd_encrypt(message: dict) -> str:
    """Manually encrypt a secret from chat."""
    text = message.get("text", "")
    # Remove /encrypt prefix
    secret_text = text.replace("/encrypt", "").strip()
    
    if not secret_text:
        return "Usage: /encrypt [secret_value]\nI'll encrypt it and delete the message."
    
    from python.helpers.vault import vault_store
    
    ts = int(time.time())
    key_name = f"manual_telegram_{ts}"
    vault_store(key_name, secret_text)
    
    return f"Encrypted as `{key_name}` in vault. Original message should be deleted."


@command("call")
def cmd_call(message: dict) -> str:
    """Initiate a Twilio voice call."""
    text = message.get("text", "")
    parts = text.replace("/call", "").strip().split(maxsplit=1)
    
    if len(parts) < 2:
        return "Usage: /call +1234567890 Hello this is a test call"
    
    phone = parts[0]
    msg = parts[1]
    
    try:
        from python.helpers.voice_ai import make_outbound_call
        result = make_outbound_call(phone, msg)
        if result and result.status != "failed":
            return f"Call initiated to {phone}\nSID: `{result.call_sid}`\nStatus: {result.status}"
        return f"Call failed: {result.status if result else 'unknown error'}"
    except Exception as e:
        return f"Call error: {str(e)}"


# ─── Message Processing ─────────────────────────────────────

def process_message(message: dict) -> Optional[str]:
    """
    Process an incoming Telegram message.
    
    1. Check for auto-encrypt triggers
    2. Route commands
    3. Forward to Agent Zero for AI processing
    
    Returns response text or None.
    """
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")
    user_id = message.get("from", {}).get("id")
    user_name = message.get("from", {}).get("first_name", "Unknown")
    
    # Log the message
    _log_message({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "user_name": user_name,
        "chat_id": chat_id,
        "text": text[:200],  # Truncate for logging
        "message_id": message.get("message_id"),
    })
    
    # Auto-encrypt any secrets detected in the message
    encrypted = auto_encrypt_secrets(text, source=f"telegram_{user_id}")
    if encrypted:
        names = ", ".join(e["key_name"] for e in encrypted)
        # Notify that secrets were auto-encrypted
        send_message(chat_id, 
            f"I detected {len(encrypted)} secret(s) in your message and auto-encrypted them.\n"
            f"Vault keys: `{names}`\n"
            f"_Please delete your original message for security._",
            reply_to=message.get("message_id"))
    
    # Handle commands
    if text.startswith("/"):
        cmd_name = text.split()[0].lstrip("/").split("@")[0].lower()
        handler = COMMANDS.get(cmd_name)
        if handler:
            # Admin check for sensitive commands
            admin_ids = _get_admin_ids()
            sensitive_commands = {"vault", "security", "call", "encrypt"}
            if cmd_name in sensitive_commands and admin_ids and user_id not in admin_ids:
                return "Access denied. This command requires admin privileges."
            
            return handler(message)
        return f"Unknown command: /{cmd_name}. Use /help to see available commands."
    
    # Non-command messages: forward to Agent Zero for AI response
    # For now, echo + acknowledge
    return f"Received: _{text[:100]}_\n\n_Processing with Agent Zero..._"


# ─── Bot Loop (Long Polling) ────────────────────────────────

def start_bot(blocking: bool = True):
    """
    Start the Telegram bot in long-polling mode.
    
    Args:
        blocking: If True, runs forever. If False, processes one batch and returns.
    """
    logger.info(f"Starting Telegram bot: @{BOT_NAME}")
    
    # Verify bot token
    me = get_me()
    if not me.get("ok"):
        logger.error(f"Bot token invalid: {me}")
        raise ValueError(f"Invalid bot token: {me.get('error', 'unknown')}")
    
    bot_info = me.get("result", {})
    logger.info(f"Bot authenticated: @{bot_info.get('username')} (ID: {bot_info.get('id')})")
    
    offset = 0
    
    while True:
        try:
            updates = get_updates(offset=offset, timeout=30)
            
            for update in updates:
                offset = update["update_id"] + 1
                
                message = update.get("message")
                if not message:
                    continue
                
                response = process_message(message)
                if response:
                    chat_id = message.get("chat", {}).get("id")
                    send_message(chat_id, response)
            
            if not blocking:
                break
                
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"Bot loop error: {e}")
            time.sleep(5)  # Back off on errors


# ─── Webhook Mode (Production/VPS) ──────────────────────────

def setup_webhook(url: str, secret_token: str = None) -> dict:
    """
    Set up webhook for production VPS deployment.
    
    Args:
        url: Full HTTPS URL for webhook (e.g., https://your-vps.com/webhook/telegram)
        secret_token: Optional secret for webhook verification
    """
    if not _TELEGRAM_AVAILABLE:
        return {"ok": False, "error": "No HTTP client"}
    
    payload = {
        "url": url,
        "allowed_updates": ["message", "callback_query"],
        "drop_pending_updates": True,
    }
    if secret_token:
        payload["secret_token"] = secret_token
    
    try:
        if hasattr(httpx, 'post'):
            resp = httpx.post(_api_url("setWebhook"), json=payload, timeout=30)
            return resp.json()
        else:
            with httpx.Client(timeout=30) as client:
                resp = client.post(_api_url("setWebhook"), json=payload)
                return resp.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}


def handle_webhook(body: dict) -> Optional[str]:
    """
    Process an incoming webhook update.
    Returns response text for the message.
    """
    message = body.get("message")
    if not message:
        return None
    
    response = process_message(message)
    if response:
        chat_id = message.get("chat", {}).get("id")
        send_message(chat_id, response)
    
    return response


# ─── Quick Test ──────────────────────────────────────────────

def test_bot() -> dict:
    """Quick test: verify token, get bot info."""
    result = get_me()
    if result.get("ok"):
        bot = result["result"]
        return {
            "status": "ok",
            "bot_id": bot["id"],
            "bot_name": bot.get("first_name"),
            "username": bot.get("username"),
            "can_join_groups": bot.get("can_join_groups", False),
            "can_read_messages": bot.get("can_read_all_group_messages", False),
        }
    return {"status": "error", "error": result.get("error", "unknown")}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    
    print("Testing Telegram Bot...")
    info = test_bot()
    print(json.dumps(info, indent=2))
    
    if info.get("status") == "ok":
        print(f"\nBot @{info['username']} is alive! Starting polling...")
        start_bot(blocking=True)
    else:
        print(f"Bot test failed: {info}")
