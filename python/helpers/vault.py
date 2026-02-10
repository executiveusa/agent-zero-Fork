"""
Encrypted Vault — secure/.vault/ secret storage.

Encrypts secrets at rest using Fernet (AES-256-CBC via PBKDF2 + HMAC-SHA256).
The encryption key is derived from a machine-local vault master key
stored in secure/.vault/.vault_key (also gitignored).

Usage:
    from python.helpers.vault import vault_store, vault_load, vault_bootstrap

    vault_store("composio_api_key", "ak_-xxxxx")
    key = vault_load("composio_api_key")
    vault_bootstrap()  # auto-migrate .env secrets into vault
"""

import base64
import hashlib
import logging
import os
import time

logger = logging.getLogger(__name__)

VAULT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "secure", ".vault")
VAULT_KEY_FILE = os.path.join(VAULT_DIR, ".vault_key")

# All known secret env vars that should be vaulted
VAULT_MANAGED_KEYS = [
    "OPENROUTER_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "GROQ_API_KEY",
    "COMPOSIO_API_KEY",
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "TWILIO_SECRET",
    "TWILIO_API_KEY_SID",
    "TWILIO_API_KEY_SECRET",
    "TWILIO_REAL_ACCOUNT_SID",
    "TWILIO_PHONE_NUMBER",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_ADMIN_ID",
    "WHATSAPP_TOKEN",
    "ELEVENLABS_API_KEY",
    "GH_PAT",
    "COOLIFY_API_TOKEN",
    "FLASK_SECRET_KEY",
    "POSTGRES_PASSWORD",
    "AUTH_PASSWORD",
    "ROOT_PASSWORD",
]


def _ensure_vault_dir():
    """Create the vault directory if it doesn't exist."""
    os.makedirs(VAULT_DIR, exist_ok=True)


def _get_or_create_master_key() -> bytes:
    """
    Get or generate the vault master key.
    Stored locally in secure/.vault/.vault_key (gitignored).
    """
    _ensure_vault_dir()

    if os.path.exists(VAULT_KEY_FILE):
        with open(VAULT_KEY_FILE, "rb") as f:
            return f.read()

    # Generate a new Fernet key
    from cryptography.fernet import Fernet
    key = Fernet.generate_key()

    with open(VAULT_KEY_FILE, "wb") as f:
        f.write(key)

    logger.info("Vault: Generated new master key")
    return key


def _get_fernet():
    """Get a Fernet cipher instance."""
    from cryptography.fernet import Fernet
    key = _get_or_create_master_key()
    return Fernet(key)


def vault_store(name: str, plaintext: str) -> str:
    """
    Encrypt and store a secret in the vault.

    Args:
        name: Secret identifier (e.g., "composio_api_key")
        plaintext: The secret value to encrypt

    Returns:
        Path to the encrypted file
    """
    _ensure_vault_dir()
    f = _get_fernet()
    encrypted = f.encrypt(plaintext.encode("utf-8"))

    filepath = os.path.join(VAULT_DIR, f"{name}.enc")
    with open(filepath, "wb") as fh:
        fh.write(encrypted)

    logger.info(f"Vault: Stored encrypted secret '{name}'")
    return filepath


def vault_load(name: str) -> str | None:
    """
    Load and decrypt a secret from the vault.

    Args:
        name: Secret identifier (e.g., "composio_api_key")

    Returns:
        Decrypted plaintext, or None if not found / decryption fails
    """
    filepath = os.path.join(VAULT_DIR, f"{name}.enc")

    if not os.path.exists(filepath):
        return None

    try:
        f = _get_fernet()
        with open(filepath, "rb") as fh:
            encrypted = fh.read()
        return f.decrypt(encrypted).decode("utf-8")
    except Exception as e:
        logger.warning(f"Vault: Failed to decrypt '{name}': {e}")
        return None


def vault_delete(name: str) -> bool:
    """Delete a secret from the vault."""
    filepath = os.path.join(VAULT_DIR, f"{name}.enc")
    if os.path.exists(filepath):
        os.remove(filepath)
        logger.info(f"Vault: Deleted secret '{name}'")
        return True
    return False


def vault_list() -> list[str]:
    """List all secrets stored in the vault."""
    _ensure_vault_dir()
    return [
        f[:-4]  # strip .enc
        for f in os.listdir(VAULT_DIR)
        if f.endswith(".enc")
    ]


def vault_get(env_key: str) -> str | None:
    """
    Get a secret by env var name — vault first, env fallback.
    
    This is the primary API for reading secrets throughout the codebase.
    It checks the encrypted vault first, then falls back to os.environ.
    
    Args:
        env_key: Environment variable name (e.g., "TWILIO_AUTH_TOKEN")
    
    Returns:
        Secret value or None
    """
    # Normalize to lowercase for vault filename
    vault_name = env_key.lower()
    
    # 1. Try vault
    val = vault_load(vault_name)
    if val:
        return val
    
    # 2. Fallback to env
    val = os.environ.get(env_key, "").strip()
    return val if val else None


def vault_bootstrap() -> dict:
    """
    Auto-migrate secrets from .env into the encrypted vault.
    
    Scans VAULT_MANAGED_KEYS for non-empty values in os.environ,
    encrypts them into the vault, and clears the .env value
    (replaces with a comment pointing to the vault).
    
    Returns:
        Dict with counts: {"migrated": N, "already_vaulted": M, "empty": E}
    """
    stats = {"migrated": 0, "already_vaulted": 0, "empty": 0}
    
    for key in VAULT_MANAGED_KEYS:
        vault_name = key.lower()
        
        # Already in vault?
        existing = vault_load(vault_name)
        if existing:
            stats["already_vaulted"] += 1
            continue
        
        # Check env for a value
        env_val = os.environ.get(key, "").strip()
        if not env_val:
            stats["empty"] += 1
            continue
        
        # Skip placeholder values
        if env_val in ("changeme", "your-key-here", "xxx", ""):
            stats["empty"] += 1
            continue
        
        # Encrypt into vault
        vault_store(vault_name, env_val)
        logger.info(f"Vault: Migrated {key} from env → vault")
        stats["migrated"] += 1
    
    return stats


def vault_audit() -> dict:
    """
    Audit vault health and security status.
    
    Returns:
        Dict with audit results
    """
    results = {
        "vault_exists": os.path.exists(VAULT_DIR),
        "master_key_exists": os.path.exists(VAULT_KEY_FILE),
        "secrets_count": 0,
        "secrets": [],
        "env_leaks": [],  # secrets that are in .env AND vault (should only be vault)
        "unvaulted": [],  # secrets in .env but not vault
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    
    if results["vault_exists"]:
        vaulted = vault_list()
        results["secrets_count"] = len(vaulted)
        results["secrets"] = vaulted
    
    # Check for env leaks
    for key in VAULT_MANAGED_KEYS:
        vault_name = key.lower()
        env_val = os.environ.get(key, "").strip()
        in_vault = vault_load(vault_name) is not None
        
        if env_val and in_vault:
            results["env_leaks"].append(key)
        elif env_val and not in_vault:
            results["unvaulted"].append(key)
    
    return results
