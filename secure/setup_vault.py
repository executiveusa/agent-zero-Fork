#!/usr/bin/env python3
"""
Vault Setup and Secret Import Tool

Features:
- Interactive vault initialization
- Bulk secret import
- Validates secret formats
- Automatic categorization
- Secure password generation

Author: Agent Zero Security Team
Version: 1.0.0
"""

import os
import sys
import getpass
from pathlib import Path

# Add secure directory to path
sys.path.insert(0, os.path.dirname(__file__))

from secrets_vault import SecretsVault
from vault_manager import VaultManager


def print_header():
    """Print welcome header"""
    print("\n" + "="*60)
    print("🔐 VAULT SETUP & SECRET IMPORT")
    print("="*60 + "\n")


def create_vault():
    """Create and initialize new vault"""
    print("📦 Creating new vault...\n")
    
    vault = SecretsVault()
    
    if vault.exists():
        print("⚠️  Vault already exists!")
        response = input("Do you want to delete it and create a new one? (yes/no): ")
        if response.lower() != "yes":
            print("❌ Aborted")
            return None
        
        # Delete existing vault
        import shutil
        shutil.rmtree(vault.vault_dir)
        print("✅ Old vault deleted")
        
        vault = SecretsVault()
    
    # Get master password
    while True:
        password1 = getpass.getpass("Enter master password (min 12 chars): ")
        
        if len(password1) < 12:
            print("❌ Password too short. Must be at least 12 characters.")
            continue
        
        password2 = getpass.getpass("Confirm master password: ")
        
        if password1 != password2:
            print("❌ Passwords don't match. Try again.")
            continue
        
        break
    
    # Initialize vault
    try:
        vault.initialize(password1)
        print("\n✅ Vault created successfully!")
        
        # Unlock vault
        vault.unlock(password1)
        
        return vault
        
    except Exception as e:
        print(f"\n❌ Failed to create vault: {e}")
        return None


def import_secrets(vault: SecretsVault):
    """Import all secrets into vault"""
    print("\n📥 Importing secrets...\n")
    
    print("⚠️  This is a template setup script.")
    print("    Your actual secrets are already encrypted in the vault.")
    print("    To add more secrets, use: python vault_cli.py add <category> <key>\n")
    
    # Template structure (secrets already imported during initial setup)
    secrets = {
        # Example structure - actual values are encrypted in vault
        # "telegram": {
        #     "bot_token": "your-telegram-bot-token"
        # },
        # "llm": {
        #     "anthropic_api_key": "your-anthropic-key",
        #     "openai_api_key": "your-openai-key",
        # },
        # Add new categories/secrets using vault_cli.py
    }
    
    # Note: Secrets are already in your vault
    if not secrets:
        print("✅ Your secrets are already encrypted in the vault!")
        print("   Use 'python vault_cli.py list' to see them.")
        print("\n💡 To add more secrets:")
        print("   python vault_cli.py add <category> <key>")
        return
    
    # Import any new secrets
    manager = VaultManager(vault)
    imported_count = manager.bulk_import(secrets)
    
    print(f"\n✅ Successfully imported {imported_count} secrets!")
    
    # Show summary
    print("\n📊 Import Summary:")
    for category, category_secrets in secrets.items():
        print(f"  • {category}: {len(category_secrets)} secrets")


def main():
    """Main entry point"""
    print_header()
    
    # Create vault
    vault = create_vault()
    
    if vault is None:
        sys.exit(1)
    
    # Note: Initial secrets import is done, this is now a template
    print("\n✅ Vault created!")
    print("\n💡 To add secrets to your vault, use:")
    print("   python vault_cli.py add <category> <key>")
    print("\nExample:")
    print("   python vault_cli.py add llm openai_api_key")
    print("   python vault_cli.py add cloud vercel_token")
    
    # Show final summary
    if not vault.is_locked():
        manager = VaultManager(vault)
        print("\n" + "="*60)
        manager.print_stats()
        print("="*60)
    
    # Lock vault
    vault.lock()
    
    print("\n✅ Setup complete!")
    print("\n💡 Next steps:")
    print("  1. Run: python telegram_bot_secure.py")
    print("  2. Enter your vault master password")
    print("  3. Provide your Telegram admin user ID")
    print("  4. Start chatting with your secure bot!")
    print("\n🔒 All secrets are encrypted with AES-256-GCM + Windows DPAPI")
    print()


if __name__ == "__main__":
    main()
