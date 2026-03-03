# 🔐 ArchonX OS - Military-Grade Secrets Management

This directory contains military-grade encryption tools for managing secrets across the entire ArchonX OS ecosystem.

## 📋 Files

- **`secrets.template.json`** - Complete secrets template (copy & fill this)
- **`encrypt-secrets.sh`** - Encryption tool (Age/GPG/OpenSSL)
- **`decrypt-secrets.sh`** - Decryption tool
- **`load-secrets.py`** - Convert secrets.json to .env files
- **`.gitignore`** - Ensures secrets never get committed

## 🚀 Quick Start

### Step 1: Create Your Secrets File

```bash
# Copy the template
cp secrets.template.json secrets.json

# Edit with your actual secrets
nano secrets.json
```

### Step 2: Fill in Your Secrets

Open `secrets.json` and fill in all the fields. See the template for complete structure.

**Required sections:**
- `archonx_os` - Main brain configuration
- `agent_zero` - Orchestration agent
- `dashboard_agent_swarm` - Web UI
- `personaplex_voice` - Voice I/O
- `mcp_servers` - BrightData & FireCrawl
- `ai_providers` - Gemini CLI, Claude, etc.
- `server_access` - SSH credentials
- `databases` - Supabase, Redis

### Step 3: Encrypt Your Secrets

```bash
# Option 1: Age encryption (Recommended - Modern & Fast)
./encrypt-secrets.sh secrets.json
# Choose option 1

# Option 2: Triple encryption (Maximum Security)
./encrypt-secrets.sh secrets.json
# Choose option 4 (encrypts with Age + GPG + OpenSSL)
```

**Output files:**
- `secrets.json.encrypted.age` - Age encrypted
- `secrets.json.encrypted.gpg` - GPG encrypted
- `secrets.json.encrypted.enc` - OpenSSL encrypted

### Step 4: Backup Your Keys

```bash
# Age key (if you chose Age encryption)
cp .age-key.txt ~/secure-backup/age-key.txt

# GPG key (if you chose GPG encryption)
gpg --export-secret-keys archonx@executiveusa.com > ~/secure-backup/gpg-private.key

# Store these keys SECURELY and SEPARATELY from encrypted files!
```

### Step 5: Delete Unencrypted Secrets

```bash
# AFTER verifying encryption works:
rm secrets.json

# Now only encrypted files remain
```

---

## 🔓 Decrypting Secrets

When you need to use your secrets:

```bash
# Decrypt Age file
./decrypt-secrets.sh secrets.json.encrypted.age

# Decrypt GPG file
./decrypt-secrets.sh secrets.json.encrypted.gpg

# Decrypt OpenSSL file
./decrypt-secrets.sh secrets.json.encrypted.enc
```

This creates `secrets.json` - use it, then delete it when done!

---

## 🔄 Converting Secrets to .env Files

### Generate Main .env File

```bash
# Decrypt first
./decrypt-secrets.sh secrets.json.encrypted.age

# Generate .env
python3 load-secrets.py secrets.json generate-env

# This creates .env with all secrets
```

### Generate Service-Specific .env

```bash
# For Agent Zero
python3 load-secrets.py secrets.json generate-service agent_zero
# Creates .env.agent_zero

# For ArchonX OS
python3 load-secrets.py secrets.json generate-service archonx_os
# Creates .env.archonx_os

# For Dashboard
python3 load-secrets.py secrets.json generate-service dashboard_agent_swarm
# Creates .env.dashboard_agent_swarm
```

### Generate Docker Compose .env

```bash
python3 load-secrets.py secrets.json generate-docker
# Creates docker-compose.env with all container variables
```

### Export as Shell Variables

```bash
# Generate shell export commands
python3 load-secrets.py secrets.json export-shell > export-vars.sh

# Source them
source export-vars.sh
```

---

## 🛡️ Security Best Practices

### ✅ DO:

1. **Always encrypt secrets** before storing
2. **Backup encryption keys** separately from encrypted files
3. **Use strong passwords** (20+ characters, random)
4. **Delete decrypted files** after use
5. **Store keys in secure locations** (password manager, hardware key)
6. **Use different passwords** for dev/staging/production
7. **Rotate secrets regularly** (every 90 days)
8. **Use environment-specific secrets files**
   - `secrets.dev.json` - Development
   - `secrets.staging.json` - Staging
   - `secrets.prod.json` - Production

### ❌ DON'T:

1. **Never commit unencrypted secrets** to git
2. **Never share encryption keys** via email/Slack
3. **Never use weak passwords**
4. **Never store keys with encrypted files**
5. **Never leave decrypted files** on disk
6. **Never hardcode secrets** in code

---

## 🔐 Encryption Methods Comparison

| Method | Security | Speed | Use Case |
|--------|----------|-------|----------|
| **Age** | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ | Recommended for most users |
| **GPG** | ⭐⭐⭐⭐⭐ | ⚡⚡ | Industry standard, widely supported |
| **OpenSSL** | ⭐⭐⭐⭐ | ⚡⚡⚡ | Password-based, portable |
| **Triple** | ⭐⭐⭐⭐⭐ | ⚡ | Maximum security (all three) |

### Age (Recommended)
- **Pros**: Modern, fast, simple, secure
- **Cons**: Less widely deployed than GPG
- **Best for**: Personal use, small teams

### GPG
- **Pros**: Industry standard, widely supported
- **Cons**: Complex, slower
- **Best for**: Enterprise, compliance requirements

### OpenSSL
- **Pros**: Portable, password-based
- **Cons**: Need to remember password
- **Best for**: Quick encryption, no key management

---

## 📦 Complete Workflow Example

### Initial Setup (One Time)

```bash
# 1. Create secrets file
cp secrets.template.json secrets.json

# 2. Fill in all your secrets
nano secrets.json

# 3. Encrypt with Age (recommended)
./encrypt-secrets.sh secrets.json
# Choose option 1 (Age)

# 4. Backup your Age key
cp .age-key.txt ~/Dropbox/secure-backups/archonx-age-key.txt

# 5. Delete unencrypted file
rm secrets.json

# 6. Commit encrypted file to git
git add secrets.json.encrypted.age
git add .gitignore
git commit -m "chore: add encrypted secrets"
```

### Daily Use

```bash
# When deploying or running services:

# 1. Decrypt
./decrypt-secrets.sh secrets.json.encrypted.age

# 2. Generate .env for your service
python3 load-secrets.py secrets.json generate-service agent_zero

# 3. Use the .env file
cp .env.agent_zero /path/to/agent-zero/.env

# 4. Clean up
rm secrets.json .env.agent_zero
```

### On Production Server

```bash
# 1. Copy encrypted file and key to server
scp secrets.json.encrypted.age user@server:/root/archonx/
scp .age-key.txt user@server:/root/.secrets/

# 2. SSH into server
ssh user@server

# 3. Decrypt and generate env
cd /root/archonx
./decrypt-secrets.sh secrets.json.encrypted.age
python3 load-secrets.py secrets.json generate-env

# 4. Move .env to project
mv .env /root/agent-zero/

# 5. Clean up decrypted file
rm secrets.json

# 6. Secure the key
chmod 600 /root/.secrets/.age-key.txt
```

---

## 🔄 Rotating Secrets

When you need to change secrets (recommended every 90 days):

```bash
# 1. Decrypt current secrets
./decrypt-secrets.sh secrets.json.encrypted.age

# 2. Update secrets
nano secrets.json

# 3. Re-encrypt
./encrypt-secrets.sh secrets.json

# 4. Delete decrypted
rm secrets.json

# 5. Update all services
# ... redeploy with new secrets
```

---

## 🆘 Emergency Recovery

### Lost Age Key

If you lose your Age key but have the encrypted file:
- **Result**: ❌ Unrecoverable (Age uses strong encryption)
- **Prevention**: Always backup keys to multiple secure locations

### Lost GPG Key

If you lose your GPG key:
- **Result**: ❌ Unrecoverable
- **Prevention**: Export and backup GPG private key

### Forgot OpenSSL Password

If you forget your OpenSSL password:
- **Result**: ❌ Unrecoverable
- **Prevention**: Store password in password manager

### Secrets File Compromised

If your encrypted file is exposed:
1. **Immediately** rotate all secrets
2. Revoke all API keys
3. Change all passwords
4. Review access logs
5. Create new encrypted file with new secrets

---

## 🔧 Troubleshooting

### "Age not installed"

```bash
# Ubuntu/Debian
apt-get install age

# macOS
brew install age

# Manual install
curl -LO https://github.com/FiloSottile/age/releases/latest/download/age-linux-amd64.tar.gz
tar xzf age-linux-amd64.tar.gz
mv age/age /usr/local/bin/
```

### "GPG key not found"

```bash
# List existing keys
gpg --list-keys

# Generate new key
gpg --gen-key
```

### "Permission denied"

```bash
# Make scripts executable
chmod +x encrypt-secrets.sh decrypt-secrets.sh
chmod +x load-secrets.py
```

### "Module not found" (Python)

```bash
# No external dependencies - uses only stdlib
# If issues, ensure Python 3.6+
python3 --version
```

---

## 📚 Additional Resources

- **Age**: https://github.com/FiloSottile/age
- **GPG**: https://gnupg.org/documentation/
- **OpenSSL**: https://www.openssl.org/docs/
- **Secrets Management Best Practices**: https://www.owasp.org/index.php/Secrets_Management_Cheat_Sheet

---

## 🤝 Support

Need help with secrets management?

1. Check this README
2. Review error messages
3. Check ArchonX OS documentation
4. Contact: archonx@executiveusa.com

---

## 📝 License

Part of ArchonX OS ecosystem. See main repository for license.
