#!/usr/bin/env python3
"""
Add Docker credentials to the encrypted vault
Run this once to securely store Docker Cloud credentials
"""

import sys
sys.path.insert(0, './secure')

from secrets_vault import SecretsVault
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Initialize vault
vault = SecretsVault(vault_dir='./secure/.vault')

# Master password (same as before)
master_password = 'Sheraljean2026'

# Unlock the vault
print("🔓 Unlocking vault...")
if not vault.unlock(master_password):
    print("❌ Failed to unlock vault. Check the password.")
    sys.exit(1)

print("✅ Vault unlocked successfully")
print("")

# Get Docker credentials from environment variables
docker_username = os.getenv('DOCKER_USERNAME', 'executiveusa')
docker_token = os.getenv('DOCKER_TOKEN')

if not docker_token:
    print("❌ DOCKER_TOKEN not found in .env file")
    print("   Please set DOCKER_TOKEN in your .env file")
    print("   Get your token from: https://hub.docker.com/settings/security")
    sys.exit(1)

# Add Docker credentials
print("📝 Adding Docker credentials to vault...")
vault.add_secret(
    category='docker',
    key='username',
    value=docker_username,
    metadata={'service': 'docker-cloud', 'added_at': 'Feb 6 2026'}
)
print(f"✅ Added Docker username: {docker_username}")

vault.add_secret(
    category='docker',
    key='token',
    value=docker_token,
    metadata={'service': 'docker-cloud', 'type': 'PAT', 'added_at': 'Feb 6 2026'}
)
print("✅ Added Docker PAT (Personal Access Token - from .env)")

# Try to retrieve and verify
print("")
print("🔍 Verifying stored credentials...")
stored_user = vault.get_secret('docker', 'username')
stored_token = vault.get_secret('docker', 'token')

if stored_user == docker_username:
    print(f"✅ Docker username verified: {stored_user}")
else:
    print("❌ Docker username verification failed")

if stored_token == docker_token:
    print("✅ Docker token verified (securely stored in vault)")
else:
    print("❌ Docker token verification failed")

# List all categories
print("")
print("📋 Vault contents summary:")
all_secrets = vault.list_secrets()
for category, keys in all_secrets.items():
    print(f"  • {category}: {len(keys)} secret(s)")

# Lock the vault
vault.lock()
print("")
print("🔒 Vault locked successfully")
print("")
print("✨ Docker credentials are now securely encrypted in the vault!")
print("   Location: ./secure/.vault/secrets.vault")
print("   Protected by: AES-256-GCM + Windows DPAPI + PBKDF2")
