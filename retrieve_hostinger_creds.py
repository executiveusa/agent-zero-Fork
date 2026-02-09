#!/usr/bin/env python3
"""
Retrieve Hostinger credentials from vault
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'secure'))

from secrets_vault import SecretsVault

def main():
    try:
        # Initialize vault
        vault = SecretsVault()
        
        if not vault.exists():
            print("❌ Vault does not exist")
            return
        
        # Unlock vault with master password from environment (NEVER hardcode)
        master_password = os.getenv('VAULT_MASTER_PASSWORD', '')
        if not master_password:
            print("\u274c VAULT_MASTER_PASSWORD not set. Set it in your .env file.")
            return
        if not vault.unlock(master_password):
            print("❌ Failed to unlock vault - invalid password")
            return
        
        # List all secrets
        print("📋 Available Secret Categories:")
        categories = vault.list_secrets()
        for cat in categories:
            print(f"  - {cat}")
            for key in categories[cat]:
                print(f"    • {key}")
        
        # Try to retrieve Hostinger secrets
        print("\n🔍 Looking for Hostinger credentials...")
        
        # Check common locations
        categories_to_check = ['cloud', 'hostinger', 'deployment', 'server', 'ssh']
        
        hostinger_creds = {}
        for category in categories_to_check:
            if category in categories:
                print(f"\n📂 Category: {category}")
                for key in categories[category]:
                    value = vault.get_secret(category, key)
                    print(f"  {key}: {value}")
                    hostinger_creds[key] = value
        
        if hostinger_creds:
            print("\n✅ Found Hostinger Credentials:")
            import json
            print(json.dumps(hostinger_creds, indent=2))
        else:
            print("\n⚠️  No Hostinger credentials found in vault")
        
        # Lock vault
        vault.lock()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
