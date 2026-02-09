# ⚡ Quick Command Cheatsheet

## 🔐 Master Password
```
Set via VAULT_MASTER_PASSWORD environment variable
```

## 🚀 Most Used Commands

### Start Bot
```powershell
cd C:\Users\Trevor\agent-zero-Fork\secure
python telegram_bot_secure.py
```

### Get Any Secret
```powershell
python vault_cli.py get llm openai_api_key
python vault_cli.py get cloud vercel_token
python vault_cli.py get payment stripe_secret_key
python vault_cli.py get ssh coolify_ssh_private_rsa
```

### List Everything
```powershell
python vault_cli.py list
```

### Search
```powershell
python vault_cli.py search "openai"
```

### Add Secret
```powershell
python vault_cli.py add category key_name
```

### Backup
```powershell
python vault_cli.py backup
```

### Health Check
```powershell
python vault_cli.py health
```

### View Logs
```powershell
python vault_cli.py audit --lines 20
```

---

## 📱 Telegram Bot (In Chat)

```
/start          - Show welcome
/list_secrets   - List all (admin)
/get_secret llm openai_api_key - Get secret (admin)
/stats          - Show stats (admin)
/health         - Health check (admin)
/lock           - Lock vault (admin)
```

---

## 🎯 Secret Categories

- **telegram** - Bot token
- **llm** - AI API keys (Anthropic, OpenAI, Google, etc.)
- **ai_services** - HeyGen, ElevenLabs, OpenHands
- **cloud** - Vercel, Coolify, Hostinger, Cloudflare
- **ssh** - Private keys (RSA, Ed25519)
- **payment** - Stripe keys
- **supabase** - Database credentials (2 projects)
- **integrations** - Notion, GitHub, Twilio

---

## 🔥 Emergency

**Lock vault:**
```powershell
# In Telegram
/lock

# Or kill bot process
Get-Process python | Where-Object {$_.CommandLine -like '*telegram*'} | Stop-Process
```

**Restore from backup:**
```powershell
python vault_cli.py restore backups/vault_backup_YYYYMMDD_HHMMSS.enc
```

---

See [COMMAND_REFERENCE.md](COMMAND_REFERENCE.md) for complete documentation.
