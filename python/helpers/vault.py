"""
Encrypted Vault — secure/.vault/ secret storage.

Encrypts secrets at rest using Fernet (AES-128-CBC + HMAC-SHA256).
The encryption key is derived from a machine-local vault master key
stored in secure/.vault/.vault_key (also gitignored).

Usage:
    from python.helpers.vault import vault_store, vault_load

    vault_store("composio_api_key", "ak_-xxxxx")
    key = vault_load("composio_api_key")
"""

import base64
import hashlib
import logging
import os

logger = logging.getLogger(__name__)

VAULT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "secure", ".vault")
VAULT_KEY_FILE = os.path.join(VAULT_DIR, ".vault_key")


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
