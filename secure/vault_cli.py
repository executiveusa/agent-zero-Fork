#!/usr/bin/env python3
"""
Command-Line Interface for Vault Management

Features:
- List/add/delete/rotate secrets
- View audit logs
- Backup/restore operations
- Health checks
- Search secrets

Author: Agent Zero Security Team
Version: 1.0.0
"""

import os
import sys
import getpass
import argparse
from pathlib import Path

# Add secure directory to path
sys.path.insert(0, os.path.dirname(__file__))

from secrets_vault import SecretsVault
from vault_manager import VaultManager


def print_banner():
    """Print CLI banner"""
    print("\n" + "="*60)
    print("🔐 VAULT CLI")
    print("="*60 + "\n")


def unlock_vault() -> tuple:
    """Unlock vault and return vault + manager"""
    vault = SecretsVault()
    
    if not vault.exists():
        print("❌ Vault does not exist. Run setup_vault.py first.")
        sys.exit(1)
    
    password = getpass.getpass("Enter vault master password: ")
    
    if not vault.unlock(password):
        print("❌ Invalid password")
        sys.exit(1)
    
    print("✅ Vault unlocked\n")
    
    manager = VaultManager(vault)
    return vault, manager


def cmd_list(args):
    """List secrets"""
    vault, manager = unlock_vault()
    
    secrets = vault.list_secrets()
    
    if not secrets:
        print("No secrets in vault")
        return
    
    print("📋 SECRETS:\n")
    
    for category, keys in secrets.items():
        print(f"📁 {category} ({len(keys)} secrets)")
        for key in sorted(keys):
            print(f"  • {key}")
        print()
    
    vault.lock()


def cmd_get(args):
    """Get a secret"""
    vault, manager = unlock_vault()
    
    category = args.category
    key = args.key
    
    value = vault.get_secret(category, key)
    
    if value is None:
        print(f"❌ Secret not found: {category}/{key}")
    else:
        print(f"🔑 {category}/{key}:")
        print(f"\n{value}\n")
    
    vault.lock()


def cmd_add(args):
    """Add a secret"""
    vault, manager = unlock_vault()
    
    category = args.category
    key = args.key
    
    if args.value:
        value = args.value
    else:
        value = getpass.getpass(f"Enter value for {category}/{key}: ")
    
    vault.add_secret(category, key, value)
    print(f"✅ Secret added: {category}/{key}")
    
    vault.lock()


def cmd_delete(args):
    """Delete a secret"""
    vault, manager = unlock_vault()
    
    category = args.category
    key = args.key
    
    # Confirm deletion
    confirm = input(f"Delete {category}/{key}? (yes/no): ")
    if confirm.lower() != "yes":
        print("❌ Aborted")
        return
    
    if vault.delete_secret(category, key):
        print(f"✅ Secret deleted: {category}/{key}")
    else:
        print(f"❌ Secret not found: {category}/{key}")
    
    vault.lock()


def cmd_rotate(args):
    """Rotate a secret"""
    vault, manager = unlock_vault()
    
    category = args.category
    key = args.key
    
    if args.value:
        new_value = args.value
    else:
        new_value = getpass.getpass(f"Enter new value for {category}/{key}: ")
    
    manager.rotate_secret(category, key, new_value)
    
    vault.lock()


def cmd_stats(args):
    """Show vault statistics"""
    vault, manager = unlock_vault()
    
    manager.print_stats()
    
    vault.lock()


def cmd_search(args):
    """Search secrets"""
    vault, manager = unlock_vault()
    
    query = args.query
    results = manager.search_secrets(query, case_sensitive=args.case_sensitive)
    
    if not results:
        print(f"No secrets found matching: {query}")
    else:
        print(f"🔍 Found {len(results)} secrets matching '{query}':\n")
        for result in results:
            print(f"  • {result['path']}")
    
    vault.lock()


def cmd_backup(args):
    """Create vault backup"""
    vault, manager = unlock_vault()
    
    backup_password = getpass.getpass("Enter backup password: ")
    
    backup_file = manager.backup_vault(backup_password, args.output)
    
    if backup_file:
        print(f"\n✅ Backup created: {backup_file}")
    
    vault.lock()


def cmd_restore(args):
    """Restore from backup"""
    vault, manager = unlock_vault()
    
    backup_password = getpass.getpass("Enter backup password: ")
    
    if manager.restore_vault(args.file, backup_password):
        print("\n✅ Vault restored successfully")
    
    vault.lock()


def cmd_backups(args):
    """List available backups"""
    vault, manager = unlock_vault()
    
    backups = manager.list_backups(args.directory)
    
    if not backups:
        print("No backups found")
    else:
        print(f"📦 Available backups ({len(backups)}):\n")
        for backup in backups:
            size_mb = backup['size'] / 1024 / 1024
            print(f"  • {backup['name']}")
            print(f"    Created: {backup['created']}")
            print(f"    Size: {size_mb:.2f} MB")
            print()
    
    vault.lock()


def cmd_health(args):
    """Check vault health"""
    vault, manager = unlock_vault()
    
    health = manager.health_check()
    
    status_emoji = "✅" if health["status"] == "healthy" else "⚠️" if health["status"] == "warning" else "❌"
    
    print(f"{status_emoji} Vault Status: {health['status'].upper()}\n")
    
    if health.get('secret_count') is not None:
        print(f"Total Secrets: {health['secret_count']}")
        print(f"Access Count: {health['access_count']}")
        print(f"Last Access: {health.get('last_access', 'Never')}")
    
    if health.get('issues'):
        print("\n⚠️  Issues:")
        for issue in health['issues']:
            print(f"  • {issue}")
    
    if health.get('warnings'):
        print("\n⚠️  Warnings:")
        for warning in health['warnings']:
            print(f"  • {warning}")
    
    print()
    vault.lock()


def cmd_audit(args):
    """View audit logs"""
    vault, manager = unlock_vault()
    
    entries = manager.get_audit_log(last_n=args.lines)
    
    if not entries:
        print("No audit log entries")
    else:
        print(f"📜 Audit Log (last {len(entries)} entries):\n")
        for entry in entries:
            timestamp = entry.get('timestamp', 'Unknown')
            event = entry.get('event', 'Unknown')
            data = entry.get('data', {})
            
            print(f"[{timestamp}] {event}")
            if data:
                for key, value in data.items():
                    print(f"  {key}: {value}")
            print()
    
    vault.lock()


def cmd_export(args):
    """Export secrets (WARNING: plaintext)"""
    vault, manager = unlock_vault()
    
    print("⚠️  WARNING: This will export secrets in PLAINTEXT!")
    confirm = input("Are you sure? (yes/no): ")
    
    if confirm.lower() != "yes":
        print("❌ Aborted")
        return
    
    categories = args.categories.split(",") if args.categories else None
    
    if manager.export_secrets(args.output, categories):
        print(f"\n✅ Secrets exported to: {args.output}")
        print("⚠️  Remember to delete this file after use!")
    
    vault.lock()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Vault CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # List command
    parser_list = subparsers.add_parser("list", help="List all secrets")
    parser_list.set_defaults(func=cmd_list)
    
    # Get command
    parser_get = subparsers.add_parser("get", help="Get a secret")
    parser_get.add_argument("category", help="Secret category")
    parser_get.add_argument("key", help="Secret key")
    parser_get.set_defaults(func=cmd_get)
    
    # Add command
    parser_add = subparsers.add_parser("add", help="Add a secret")
    parser_add.add_argument("category", help="Secret category")
    parser_add.add_argument("key", help="Secret key")
    parser_add.add_argument("--value", help="Secret value (will prompt if not provided)")
    parser_add.set_defaults(func=cmd_add)
    
    # Delete command
    parser_delete = subparsers.add_parser("delete", help="Delete a secret")
    parser_delete.add_argument("category", help="Secret category")
    parser_delete.add_argument("key", help="Secret key")
    parser_delete.set_defaults(func=cmd_delete)
    
    # Rotate command
    parser_rotate = subparsers.add_parser("rotate", help="Rotate a secret")
    parser_rotate.add_argument("category", help="Secret category")
    parser_rotate.add_argument("key", help="Secret key")
    parser_rotate.add_argument("--value", help="New secret value (will prompt if not provided)")
    parser_rotate.set_defaults(func=cmd_rotate)
    
    # Stats command
    parser_stats = subparsers.add_parser("stats", help="Show vault statistics")
    parser_stats.set_defaults(func=cmd_stats)
    
    # Search command
    parser_search = subparsers.add_parser("search", help="Search secrets")
    parser_search.add_argument("query", help="Search query")
    parser_search.add_argument("--case-sensitive", action="store_true", help="Case-sensitive search")
    parser_search.set_defaults(func=cmd_search)
    
    # Backup command
    parser_backup = subparsers.add_parser("backup", help="Create vault backup")
    parser_backup.add_argument("--output", help="Backup directory")
    parser_backup.set_defaults(func=cmd_backup)
    
    # Restore command
    parser_restore = subparsers.add_parser("restore", help="Restore from backup")
    parser_restore.add_argument("file", help="Backup file path")
    parser_restore.set_defaults(func=cmd_restore)
    
    # Backups command
    parser_backups = subparsers.add_parser("backups", help="List available backups")
    parser_backups.add_argument("--directory", help="Backups directory")
    parser_backups.set_defaults(func=cmd_backups)
    
    # Health command
    parser_health = subparsers.add_parser("health", help="Check vault health")
    parser_health.set_defaults(func=cmd_health)
    
    # Audit command
    parser_audit = subparsers.add_parser("audit", help="View audit logs")
    parser_audit.add_argument("--lines", type=int, default=50, help="Number of log entries to show")
    parser_audit.set_defaults(func=cmd_audit)
    
    # Export command
    parser_export = subparsers.add_parser("export", help="Export secrets (WARNING: plaintext)")
    parser_export.add_argument("output", help="Output file")
    parser_export.add_argument("--categories", help="Comma-separated categories to export")
    parser_export.set_defaults(func=cmd_export)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    print_banner()
    
    # Execute command
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n\n👋 Aborted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
