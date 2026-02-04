#!/usr/bin/env python3
"""
High-Level Vault Management Operations

Features:
- Secret rotation
- Backup/restore with encryption
- Emergency vault wipe
- Secret versioning
- Bulk import/export
- Health checks

Author: Agent Zero Security Team
Version: 1.0.0
"""

import os
import json
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import secrets
from secrets_vault import SecretsVault, SecureMemory

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    print("ERROR: cryptography not installed")
    exit(1)


class VaultManager:
    """High-level vault management"""
    
    def __init__(self, vault: SecretsVault):
        self.vault = vault
    
    def rotate_secret(self, category: str, key: str, new_value: any) -> bool:
        """Rotate a secret (keep old value in history)"""
        try:
            # Get current value
            old_value = self.vault.get_secret(category, key)
            
            if old_value is not None:
                # Save old value to history
                history_category = f"_history_{category}"
                history_key = f"{key}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                
                self.vault.add_secret(history_category, history_key, old_value, {
                    "rotated_at": datetime.utcnow().isoformat(),
                    "original_key": key
                })
            
            # Update with new value
            self.vault.add_secret(category, key, new_value, {
                "last_rotated": datetime.utcnow().isoformat()
            })
            
            print(f"✅ Secret rotated: {category}/{key}")
            return True
            
        except Exception as e:
            print(f"❌ Rotation failed: {e}")
            return False
    
    def backup_vault(self, backup_password: str, backup_dir: str = None) -> str:
        """Create encrypted backup of vault"""
        try:
            if backup_dir is None:
                backup_dir = self.vault.vault_dir / "backups"
            
            backup_dir = Path(backup_dir)
            backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"vault_backup_{timestamp}.enc"
            
            # Get all secrets
            all_secrets = self.vault.get_all_secrets()
            metadata = self.vault.get_metadata()
            
            backup_data = {
                "version": self.vault.VAULT_VERSION,
                "backed_up": datetime.utcnow().isoformat(),
                "secrets": all_secrets,
                "metadata": metadata
            }
            
            # Encrypt with separate password
            plaintext = json.dumps(backup_data, indent=2).encode()
            nonce = secrets.token_bytes(12)
            
            # Derive key from backup password
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.backends import default_backend
            
            salt = secrets.token_bytes(32)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA512(),
                length=32,
                salt=salt,
                iterations=600000,
                backend=default_backend()
            )
            key = kdf.derive(backup_password.encode())
            
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)
            
            # Save: salt + nonce + ciphertext
            backup_file.write_bytes(salt + nonce + ciphertext)
            os.chmod(backup_file, 0o600)
            
            # Wipe sensitive data
            SecureMemory.wipe(backup_password)
            SecureMemory.wipe(key)
            
            print(f"✅ Backup created: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None
    
    def restore_vault(self, backup_file: str, backup_password: str) -> bool:
        """Restore vault from encrypted backup"""
        try:
            backup_file = Path(backup_file)
            
            if not backup_file.exists():
                raise Exception(f"Backup file not found: {backup_file}")
            
            # Read encrypted backup
            encrypted_data = backup_file.read_bytes()
            
            # Extract components
            salt = encrypted_data[:32]
            nonce = encrypted_data[32:44]
            ciphertext = encrypted_data[44:]
            
            # Derive key
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.backends import default_backend
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA512(),
                length=32,
                salt=salt,
                iterations=600000,
                backend=default_backend()
            )
            key = kdf.derive(backup_password.encode())
            
            # Decrypt
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            
            backup_data = json.loads(plaintext.decode())
            
            # Restore all secrets
            restored_count = 0
            for category, secrets in backup_data.get("secrets", {}).items():
                for secret_key, secret_value in secrets.items():
                    self.vault.add_secret(category, secret_key, secret_value)
                    restored_count += 1
            
            # Wipe sensitive data
            SecureMemory.wipe(backup_password)
            SecureMemory.wipe(key)
            
            print(f"✅ Restored {restored_count} secrets from backup")
            return True
            
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False
    
    def emergency_wipe(self, confirmation: str) -> bool:
        """Permanently delete vault (requires confirmation)"""
        if confirmation != "PERMANENTLY DELETE VAULT":
            print("❌ Invalid confirmation. Vault not deleted.")
            return False
        
        try:
            # Overwrite vault files with random data before deletion
            for file_path in [self.vault.vault_file, self.vault.salt_file]:
                if file_path.exists():
                    # Overwrite with random data 3 times
                    file_size = file_path.stat().st_size
                    for _ in range(3):
                        with open(file_path, "wb") as f:
                            f.write(secrets.token_bytes(file_size))
                    # Delete
                    file_path.unlink()
            
            # Delete entire vault directory
            shutil.rmtree(self.vault.vault_dir)
            
            print("✅ Vault wiped successfully")
            return True
            
        except Exception as e:
            print(f"❌ Emergency wipe failed: {e}")
            return False
    
    def bulk_import(self, secrets_dict: Dict[str, Dict[str, any]]) -> int:
        """Import multiple secrets at once"""
        imported = 0
        
        for category, secrets in secrets_dict.items():
            for key, value in secrets.items():
                try:
                    self.vault.add_secret(category, key, value)
                    imported += 1
                except Exception as e:
                    print(f"⚠️  Failed to import {category}/{key}: {e}")
        
        print(f"✅ Imported {imported} secrets")
        return imported
    
    def export_secrets(self, output_file: str, categories: List[str] = None) -> bool:
        """Export secrets to JSON (WARNING: plaintext)"""
        try:
            if categories:
                export_data = {}
                for cat in categories:
                    export_data[cat] = self.vault.get_all_secrets(cat)
            else:
                export_data = self.vault.get_all_secrets()
            
            with open(output_file, "w") as f:
                json.dump(export_data, f, indent=2)
            
            print(f"⚠️  EXPORTED PLAINTEXT SECRETS TO: {output_file}")
            print("   Remember to delete this file after use!")
            return True
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return False
    
    def health_check(self) -> Dict:
        """Check vault health"""
        health = {
            "status": "healthy",
            "issues": [],
            "warnings": []
        }
        
        try:
            # Check if vault exists
            if not self.vault.exists():
                health["status"] = "error"
                health["issues"].append("Vault does not exist")
                return health
            
            # Check if locked
            if self.vault.is_locked():
                health["warnings"].append("Vault is locked")
            
            # Check file permissions
            for file_path in [self.vault.vault_file, self.vault.salt_file]:
                if file_path.exists():
                    mode = oct(file_path.stat().st_mode)[-3:]
                    if mode != "600":
                        health["warnings"].append(f"{file_path.name} permissions are {mode}, should be 600")
            
            # Check vault size
            vault_size = self.vault.vault_file.stat().st_size
            if vault_size > 10 * 1024 * 1024:  # 10 MB
                health["warnings"].append(f"Vault is large ({vault_size // 1024 // 1024} MB)")
            
            # Get metadata
            if not self.vault.is_locked():
                metadata = self.vault.get_metadata()
                health["secret_count"] = metadata.get("secret_count", 0)
                health["access_count"] = metadata.get("access_count", 0)
                health["last_access"] = metadata.get("last_access")
                
                # Check for old secrets needing rotation
                # (This would require storing last_modified per secret)
            
            if health["issues"]:
                health["status"] = "error"
            elif health["warnings"]:
                health["status"] = "warning"
            
        except Exception as e:
            health["status"] = "error"
            health["issues"].append(f"Health check failed: {e}")
        
        return health
    
    def list_backups(self, backup_dir: str = None) -> List[Dict]:
        """List available backups"""
        if backup_dir is None:
            backup_dir = self.vault.vault_dir / "backups"
        
        backup_dir = Path(backup_dir)
        
        if not backup_dir.exists():
            return []
        
        backups = []
        for backup_file in backup_dir.glob("vault_backup_*.enc"):
            stat = backup_file.stat()
            backups.append({
                "file": str(backup_file),
                "name": backup_file.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
            })
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x["created"], reverse=True)
        
        return backups
    
    def search_secrets(self, query: str, case_sensitive: bool = False) -> List[Dict]:
        """Search for secrets by key name"""
        results = []
        
        try:
            all_secrets = self.vault.list_secrets()
            
            if not case_sensitive:
                query = query.lower()
            
            for category, keys in all_secrets.items():
                for key in keys:
                    search_key = key if case_sensitive else key.lower()
                    if query in search_key:
                        results.append({
                            "category": category,
                            "key": key,
                            "path": f"{category}/{key}"
                        })
        
        except Exception as e:
            print(f"❌ Search failed: {e}")
        
        return results
    
    def get_audit_log(self, last_n: int = 50) -> List[Dict]:
        """Get recent audit log entries"""
        try:
            if not self.vault.audit_file.exists():
                return []
            
            entries = []
            with open(self.vault.audit_file, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entries.append(entry)
                    except:
                        pass
            
            # Return last N entries
            return entries[-last_n:]
            
        except Exception as e:
            print(f"❌ Failed to read audit log: {e}")
            return []
    
    def print_stats(self):
        """Print vault statistics"""
        try:
            if self.vault.is_locked():
                print("⚠️  Vault is locked. Unlock to see stats.")
                return
            
            metadata = self.vault.get_metadata()
            secrets = self.vault.list_secrets()
            
            print("\n" + "="*60)
            print("📊 VAULT STATISTICS")
            print("="*60)
            print(f"Version: {self.vault.VAULT_VERSION}")
            print(f"Total Secrets: {metadata.get('secret_count', 0)}")
            print(f"Access Count: {metadata.get('access_count', 0)}")
            print(f"Last Access: {metadata.get('last_access', 'Never')}")
            print(f"Last Rotation: {metadata.get('last_rotation', 'Never')}")
            print(f"\nCategories: {len(secrets)}")
            
            for category, keys in secrets.items():
                print(f"  • {category}: {len(keys)} secrets")
            
            # Health check
            health = self.health_check()
            print(f"\nHealth Status: {health['status'].upper()}")
            
            if health.get('issues'):
                print("\n⚠️  Issues:")
                for issue in health['issues']:
                    print(f"  • {issue}")
            
            if health.get('warnings'):
                print("\n⚠️  Warnings:")
                for warning in health['warnings']:
                    print(f"  • {warning}")
            
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"❌ Failed to print stats: {e}")
