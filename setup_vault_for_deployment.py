#!/usr/bin/env python3
"""
Setup vault for GitHub and Vercel deployment tokens
Run this script to securely store your deployment tokens
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from secure.secrets_vault import SecretsVault

def setup_vault():
    """Initialize vault and add deployment tokens"""
    
    print("=" * 60)
    print("VAULT SETUP FOR DEPLOYMENT")
    print("=" * 60)
    
    # Create vault instance
    vault = SecretsVault('./secure/.vault')
    
    # Check if vault already exists
    if vault.exists():
        print("\nVault already exists. Checking if locked...")
        # Try to unlock with default password
        password = 'Sheraljean2026'
        if vault.unlock(password):
            print("Vault unlocked with default password")
        else:
            print("\nVault exists but couldn't unlock with default password")
            print("Please enter your existing master password:")
            password = input("> ")
            if not vault.unlock(password):
                print("ERROR: Could not unlock vault. Exiting.")
                sys.exit(1)
    else:
        print("\nCreating new vault...")
        print("\nEnter a new master password for your vault:")
        print("(This password will be used to unlock the vault)")
        password1 = input("Password: ")
        password2 = input("Confirm Password: ")
        
        if password1 != password2:
            print("ERROR: Passwords don't match")
            sys.exit(1)
        
        if len(password1) < 8:
            print("ERROR: Password must be at least 8 characters")
            sys.exit(1)
        
        # Initialize new vault
        vault.initialize(password1)
        print("\nVault created successfully!")
    
    print("\n" + "-" * 60)
    print("ADD DEPLOYMENT TOKENS")
    print("-" * 60)
    
    # Get tokens from user
    print("\nPlease enter your deployment tokens:")
    print("(These will be stored securely in your vault)")
    
    github_token = input("\nGitHub Personal Access Token: ").strip()
    vercel_token = input("Vercel Access Token: ").strip()
    
    # Store tokens
    if github_token:
        vault.add_secret('deployment', 'github_token', github_token)
        print("\n[OK] GitHub token stored securely")
    else:
        print("\n[SKIP] GitHub token not provided")
    
    if vercel_token:
        vault.add_secret('deployment', 'vercel_token', vercel_token)
        print("[OK] Vercel token stored securely")
    else:
        print("[SKIP] Vercel token not provided")
    
    # Lock the vault
    vault.lock()
    
    print("\n" + "=" * 60)
    print("VAULT SETUP COMPLETE")
    print("=" * 60)
    print("\nYour tokens are now securely stored in:")
    print("  agent-zero-Fork/secure/.vault/")
    print("\nIMPORTANT: Remember your master password!")
    print("  Password: Sheraljean2026 (or your custom password)")
    
    print("\n" + "-" * 60)
    print("DEPLOYMENT INSTRUCTIONS")
    print("-" * 60)
    print("\nTo deploy, run:")
    print("  1. Set environment variables:")
    print("     set GITHUB_TOKEN=<your github token>")
    print("     set VERCEL_TOKEN=<your vercel token>")
    print("")
    print("  2. Deploy to Vercel:")
    print("     cd spy-scape-mustang-maXx")
    print("     npx vercel --prod")
    print("")
    print("Or manually push to GitHub and connect to Vercel")

if __name__ == '__main__':
    setup_vault()
