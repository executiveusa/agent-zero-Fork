# 🎯 Master Command Reference

**Complete command list for the Secure Vault System**

---

## 📦 Setup & Initialization

### First-Time Setup
```powershell
cd C:\Users\Trevor\agent-zero-Fork\secure
python setup_vault.py
```
- Creates encrypted vault
- Imports all 70+ secrets
- Sets master password

### Install Dependencies
```powershell
python -m pip install -r requirements.txt
python C:\Users\Trevor\AppData\Local\Programs\Python\Python311\Scripts\pywin32_postinstall.py -install
```

---

## 🤖 Telegram Bot Commands

### Start the Bot
```powershell
cd C:\Users\Trevor\agent-zero-Fork\secure
python telegram_bot_secure.py
```
- Enter master password when prompted (from VAULT_MASTER_PASSWORD env var)
- Enter admin user ID (get from @userinfobot)

### Public Bot Commands (All Users)
| Command | Description |
|---------|-------------|
| `/start` | Show welcome message and your user ID |
| `/help` | Display available commands |
| `/ping` | Check bot status and vault status |

### Admin Bot Commands (Authorized Users Only)
| Command | Description | Example |
|---------|-------------|---------|
| `/list_secrets` | List all secret categories and keys | `/list_secrets` |
| `/get_secret <category> <key>` | Retrieve a specific secret value | `/get_secret llm openai_api_key` |
| `/stats` | Show vault statistics | `/stats` |
| `/health` | Check vault health status | `/health` |
| `/lock` | Lock the vault remotely | `/lock` |

---

## 💻 Vault CLI Commands

### List Operations

**List all secrets**
```powershell
python vault_cli.py list
```

**Search for secrets**
```powershell
python vault_cli.py search "openai"
python vault_cli.py search "api" --case-sensitive
```

### Secret Management

**Get a secret**
```powershell
python vault_cli.py get llm anthropic_api_key
python vault_cli.py get cloud vercel_token
python vault_cli.py get ssh coolify_ssh_private_rsa
```

**Add a new secret**
```powershell
python vault_cli.py add llm new_api_key
python vault_cli.py add llm new_api_key --value "sk-your-key-here"
```

**Delete a secret**
```powershell
python vault_cli.py delete llm old_api_key
```

**Rotate a secret**
```powershell
python vault_cli.py rotate llm openai_api_key
python vault_cli.py rotate llm openai_api_key --value "new-key-value"
```

### Backup & Restore

**Create backup**
```powershell
python vault_cli.py backup
python vault_cli.py backup --output ./my-backups
```

**List backups**
```powershell
python vault_cli.py backups
python vault_cli.py backups --directory ./my-backups
```

**Restore from backup**
```powershell
python vault_cli.py restore path/to/vault_backup_20260204_120000.enc
```

### Monitoring & Audit

**View statistics**
```powershell
python vault_cli.py stats
```

**Health check**
```powershell
python vault_cli.py health
```

**View audit logs**
```powershell
python vault_cli.py audit
python vault_cli.py audit --lines 100
```

### Export (Use with Caution)

**Export secrets to plaintext** ⚠️
```powershell
python vault_cli.py export secrets_export.json
python vault_cli.py export secrets_export.json --categories llm,cloud
```

---

## 🔑 Secret Categories

Your vault is organized into these categories:

| Category | Secrets | Examples |
|----------|---------|----------|
| **telegram** | 1 | bot_token |
| **llm** | 12 | anthropic_api_key, openai_api_key, google_api_key, glm_api_key, huggingface_token |
| **ai_services** | 4 | heygen_api, elevenlabs_api, openhands_api_1 |
| **cloud** | 12 | vercel_token, coolify_api_token, hostinger_api_token, cloudflare_api_token |
| **ssh** | 3 | coolify_ssh_private_rsa, coolify_ssh_private_ed25519, coolify_ssh_public |
| **payment** | 2 | stripe_secret_key, stripe_publishable_key |
| **supabase** | 8 | supabase_url_1, supabase_service_role_key_1, supabase_anon_key_1 |
| **integrations** | 4 | notion_api_token, github_pat, twilio_account_sid, twilio_secret |

---

## 🚀 Quick Access Patterns

### Access Anthropic API Key
```powershell
# Via CLI
python vault_cli.py get llm anthropic_api_key

# Via Telegram Bot
/get_secret llm anthropic_api_key
```

### Access OpenAI API Key
```powershell
python vault_cli.py get llm openai_api_key
```

### Access Stripe Keys
```powershell
python vault_cli.py get payment stripe_secret_key
python vault_cli.py get payment stripe_publishable_key
```

### Access GitHub PAT
```powershell
python vault_cli.py get integrations github_pat
```

### Access SSH Keys
```powershell
python vault_cli.py get ssh coolify_ssh_private_rsa
python vault_cli.py get ssh coolify_ssh_private_ed25519
```

### Access Supabase Credentials
```powershell
python vault_cli.py get supabase supabase_url_1
python vault_cli.py get supabase supabase_service_role_key_1
```

---

## 🔐 Python API Usage

### Import and Use in Python Scripts

```python
import sys
sys.path.insert(0, 'C:/Users/Trevor/agent-zero-Fork/secure')

from secrets_vault import get_vault

# Unlock vault
vault = get_vault()
vault.unlock(os.getenv("VAULT_MASTER_PASSWORD"))

# Get a secret
api_key = vault.get_secret("llm", "openai_api_key")

# Use the secret
print(f"API Key: {api_key}")

# Lock vault when done
vault.lock()
```

### Use with Environment Variables Alternative

```python
from secrets_vault import get_vault
import os

vault = get_vault()
vault.unlock(os.getenv("VAULT_MASTER_PASSWORD"))

# Load all LLM secrets as env vars (temporary)
secrets = vault.get_all_secrets("llm")
for key, value in secrets.items():
    os.environ[key.upper()] = value

# Now use like normal env vars
import openai
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Lock vault
vault.lock()
```

---

## 🛠️ Maintenance Commands

### Check Vault Status
```powershell
python vault_cli.py health
```

### View Access History
```powershell
python vault_cli.py audit --lines 50
```

### Create Daily Backup
```powershell
python vault_cli.py backup --output ./backups
```

### Rotate All OpenAI Keys
```powershell
python vault_cli.py rotate llm openai_api_key --value "new-key-1"
python vault_cli.py rotate llm openai_api_key_alt --value "new-key-2"
```

### Find All API Keys
```powershell
python vault_cli.py search "api_key"
```

---

## 🚨 Emergency Commands

### Emergency Vault Lock (via Telegram)
```
/lock
```

### View Failed Access Attempts
```powershell
python vault_cli.py audit --lines 100 | Select-String "FAILED"
```

### Create Emergency Backup
```powershell
python vault_cli.py backup --output ./emergency-backup
```

### Restore Corrupted Vault
```powershell
python vault_cli.py restore ./backups/vault_backup_YYYYMMDD_HHMMSS.enc
```

---

## 📝 Common Workflows

### Daily Development Workflow
```powershell
# 1. Get API key for today's work
python vault_cli.py get llm openai_api_key

# 2. Check vault health
python vault_cli.py health

# 3. View recent access
python vault_cli.py audit --lines 10
```

### Secret Rotation Workflow
```powershell
# 1. Generate new API key from provider
# 2. Rotate in vault
python vault_cli.py rotate llm openai_api_key --value "new-key"

# 3. Backup after rotation
python vault_cli.py backup

# 4. Verify rotation
python vault_cli.py audit --lines 5
```

### Adding New Service Integration
```powershell
# 1. Add new secrets
python vault_cli.py add integrations new_service_api_key
python vault_cli.py add integrations new_service_secret

# 2. Verify added
python vault_cli.py list

# 3. Backup
python vault_cli.py backup
```

### Weekly Security Check
```powershell
# 1. Health check
python vault_cli.py health

# 2. View stats
python vault_cli.py stats

# 3. Review audit log
python vault_cli.py audit --lines 100

# 4. Create backup
python vault_cli.py backup
```

---

## 🎓 Advanced Usage

### Batch Add Secrets from File
```python
import sys
sys.path.insert(0, 'C:/Users/Trevor/agent-zero-Fork/secure')
from secrets_vault import get_vault
from vault_manager import VaultManager

vault = get_vault()
vault.unlock(os.getenv("VAULT_MASTER_PASSWORD"))
manager = VaultManager(vault)

# Import from dict
new_secrets = {
    "new_category": {
        "key1": "value1",
        "key2": "value2"
    }
}

manager.bulk_import(new_secrets)
vault.lock()
```

### Automated Backup Script
```powershell
# backup-vault.ps1
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
cd C:\Users\Trevor\agent-zero-Fork\secure
python vault_cli.py backup --output ".\backups\auto_backup_$timestamp"
```

### Secret Expiry Checker
```python
from datetime import datetime, timedelta
from secrets_vault import get_vault

vault = get_vault()
vault.unlock(os.getenv("VAULT_MASTER_PASSWORD"))

# Get audit log and check last rotation
# Implement custom expiry logic
# Alert if secrets haven't been rotated in 90 days
```

---

## 🔒 Security Best Practices

### DO:
✅ Always lock vault after use  
✅ Create backups before major changes  
✅ Review audit logs regularly  
✅ Rotate secrets every 90 days  
✅ Use CLI for scripting, bot for manual access  

### DON'T:
❌ Share master password  
❌ Export secrets to plaintext unnecessarily  
❌ Store backups in same location as vault  
❌ Disable rate limiting  
❌ Grant admin access without verification  

---

## 📞 Quick Help

| Need to... | Command |
|------------|---------|
| Get master password reminder | Use VAULT_MASTER_PASSWORD env var |
| Find a secret | `python vault_cli.py search "keyword"` |
| Add new API key | `python vault_cli.py add category key_name` |
| Check if vault is healthy | `python vault_cli.py health` |
| See what changed | `python vault_cli.py audit --lines 20` |
| Create backup | `python vault_cli.py backup` |
| Start bot | `python telegram_bot_secure.py` |
| Get Telegram user ID | Message [@userinfobot](https://t.me/userinfobot) |

---

## 🏆 All Commands At-A-Glance

```powershell
# Setup
python setup_vault.py

# Bot
python telegram_bot_secure.py

# CLI - Listing
python vault_cli.py list
python vault_cli.py search <query>
python vault_cli.py stats

# CLI - Secrets
python vault_cli.py get <category> <key>
python vault_cli.py add <category> <key>
python vault_cli.py delete <category> <key>
python vault_cli.py rotate <category> <key>

# CLI - Backup
python vault_cli.py backup
python vault_cli.py backups
python vault_cli.py restore <file>

# CLI - Monitoring
python vault_cli.py health
python vault_cli.py audit

# CLI - Export (Dangerous)
python vault_cli.py export <file>
```

---

**Built with ❤️ by Agent Zero Security Team**

🔒 **Your secrets are safe. Command with confidence.**
