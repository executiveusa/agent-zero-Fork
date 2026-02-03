# Quick Reference Card
## Agent Zero + Telegram Control Bot System

---

## 🚀 Deploy in 5 Minutes

```bash
# 1. Get Telegram token from @BotFather
# 2. Get your Telegram ID from @userinfobot
# 3. Get GitHub token from github.com/settings/tokens

# 4. Configure
cp .env.example .env
nano .env
# Fill in: TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_ID, GITHUB_TOKEN

# 5. Test locally
pip3 install -r requirements-telegram-bot.txt
python3 telegram_bot.py

# 6. Deploy to Hostinger
ssh root@your_vps_ip
cd /root/agent-zero
git pull  # Get latest code
bash deployment/deploy-telegram-bot.sh
sudo systemctl start agent-zero-telegram-bot

# 7. Test in Telegram
# Send: /start
```

---

## 📱 Telegram Bot Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `/start` | Welcome & quick buttons | See available actions |
| `/help` | Show all commands | List everything |
| `/repo_status` | Repo info | Star count, forks, latest commit |
| `/repo_commits` | Recent changes | Last 5 commits |
| `/repo_prs` | Open PRs | Pending reviews |
| `/git_status` | Local changes | Uncommitted files |
| `/git_pull` | Update repo | Get latest |
| `/sync_trigger` | Trigger sync | Manual ClawBot update |
| `/sync_check` | Preview sync | What would change |
| `/agent_health` | Health status | Up? Memory? Healthy? |
| `/agent_stats` | Statistics | Messages, tools used |

---

## 🔒 Security Checklist

```
Before Pushing to Production:

☐ Copy .env.example to .env
☐ Fill TELEGRAM_BOT_TOKEN (from @BotFather)
☐ Fill TELEGRAM_ADMIN_ID (from @userinfobot)
☐ Fill GITHUB_TOKEN (from github.com/settings/tokens)
☐ chmod 600 .env (make it readable by owner only)
☐ Verify .env is in .gitignore
☐ Test locally: python3 telegram_bot.py
☐ All commands work? (/start, /help, /repo_status)
☐ No secrets in logs? (check /tmp/agent_zero_telegram_bot.log)
☐ Deploy: bash deployment/deploy-telegram-bot.sh
☐ Start service: sudo systemctl start agent-zero-telegram-bot
```

---

## 🛠️ Common Operations

### View Bot Status
```bash
systemctl status agent-zero-telegram-bot
```

### View Logs (Real-time)
```bash
journalctl -u agent-zero-telegram-bot -f
```

### View Last 50 Logs
```bash
journalctl -u agent-zero-telegram-bot -n 50
```

### Restart Bot
```bash
sudo systemctl restart agent-zero-telegram-bot
```

### Stop Bot
```bash
sudo systemctl stop agent-zero-telegram-bot
```

### Start Bot
```bash
sudo systemctl start agent-zero-telegram-bot
```

### Edit Configuration
```bash
nano /root/.env
sudo systemctl restart agent-zero-telegram-bot
```

### Enable Auto-start on Reboot
```bash
sudo systemctl enable agent-zero-telegram-bot
```

---

## 📊 Environment Variables

**Required:**
```bash
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...      # From @BotFather
TELEGRAM_ADMIN_ID=123456789               # Your Telegram ID
GITHUB_TOKEN=ghp_1234567890abcdef...      # GitHub token
```

**Recommended:**
```bash
GITHUB_OWNER=executiveusa
GITHUB_REPO=agent-zero-Fork
AGENT_ZERO_API_URL=http://127.0.0.1:8000
```

**Optional:**
```bash
TELEGRAM_AUTHORIZED_USERS=user1,user2     # Additional users
LOG_LEVEL=INFO                            # DEBUG for verbose
DEBUG=false                               # true for development
```

Full list: See `.env.example`

---

## 🚨 Troubleshooting

### Bot doesn't respond
```bash
# Check if running
systemctl is-active agent-zero-telegram-bot

# Check logs
journalctl -u agent-zero-telegram-bot -p err

# Restart
sudo systemctl restart agent-zero-telegram-bot
```

### "Unauthorized" message
```bash
# Get your ID from @userinfobot
# Update .env
TELEGRAM_ADMIN_ID="your_real_id"
# Restart
sudo systemctl restart agent-zero-telegram-bot
```

### Commands time out
```bash
# Check Agent Zero is running
curl http://127.0.0.1:8000/api/health

# Check GitHub token
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

### High memory usage
```bash
# Check memory
free -h

# Restart bot
sudo systemctl restart agent-zero-telegram-bot

# Reduce log verbosity in .env
LOG_LEVEL=WARNING
```

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `telegram_bot.py` | Main bot code |
| `.env` | Secrets (NEVER commit) |
| `.env.example` | Template for .env |
| `deployment/deploy-telegram-bot.sh` | Installation script |
| `TELEGRAM_BOT_DEPLOYMENT.md` | Detailed guide |
| `docs/TELEGRAM_BOT_GUIDE.md` | Command reference |
| `/var/log/agent-zero-telegram-bot.log` | Log file |
| `/etc/systemd/system/agent-zero-telegram-bot.service` | Service config |

---

## 📈 Monitoring

### Check Bot Health
```bash
# Status
systemctl status agent-zero-telegram-bot

# Memory
ps aux | grep telegram_bot | grep -v grep

# Uptime
systemctl show agent-zero-telegram-bot -p ActiveEnterTimestamp
```

### View Metrics
```bash
# Commands processed today
journalctl -u agent-zero-telegram-bot --since today | grep -i command | wc -l

# Errors today
journalctl -u agent-zero-telegram-bot --since today -p err

# Performance check
curl http://127.0.0.1:8000/api/health
```

---

## 🔄 Daily Operations

### Morning Check
```bash
# Is bot running?
systemctl is-active agent-zero-telegram-bot

# Any overnight errors?
journalctl -u agent-zero-telegram-bot --since "8 hours ago" -p err

# Manual sync available?
/sync_check  # In Telegram
```

### Weekly Maintenance
```bash
# Review logs
journalctl -u agent-zero-telegram-bot --since "7 days ago" | less

# Check disk space
df -h

# Check memory trend
free -h

# Test all commands
# Send: /start, /help, /repo_status, etc. in Telegram
```

### Monthly Review
```bash
# Log analysis
journalctl -u agent-zero-telegram-bot --since "30 days ago" | grep error | wc -l

# Rotate old logs
journalctl --vacuum=30d

# Performance review
# Check average response times in logs

# Security review
# Verify no secrets exposed
journalctl -u agent-zero-telegram-bot | grep -i token  # Should be masked
```

---

## 🆘 Getting Help

1. **Check logs first:**
   ```bash
   journalctl -u agent-zero-telegram-bot -f
   ```

2. **Read documentation:**
   - `TELEGRAM_BOT_DEPLOYMENT.md` - Setup help
   - `docs/TELEGRAM_BOT_GUIDE.md` - Commands help
   - `IMPLEMENTATION_SUMMARY.md` - Architecture help

3. **Test bot locally:**
   ```bash
   python3 telegram_bot.py
   ```

4. **File issue with:**
   - Error message (from logs)
   - .env structure (not actual values)
   - Steps to reproduce
   - System info (OS, Python version)

---

## 📞 Key Contacts

- **Telegram Bot Support:** Check logs with `journalctl`
- **GitHub Issues:** Open issue on repo
- **Emergency:** Check `/agent_health` in Telegram

---

## ✅ Success Indicators

✅ `systemctl status` shows "active (running)"
✅ Telegram `/start` responds within 2 seconds
✅ All commands return data
✅ No error messages in logs
✅ Memory usage < 200MB
✅ Service auto-restarts on crash
✅ Service auto-starts on reboot

---

## 🎯 Implementation Timeline

| Timeline | Task | Status |
|----------|------|--------|
| Now | Review docs | 📖 Start here |
| Today | Get Telegram token | 📱 5 min |
| Today | Create .env | ⚙️ 5 min |
| Today | Test locally | 🧪 10 min |
| Tomorrow | Deploy to Hostinger | 🚀 15 min |
| Tomorrow | Test all commands | ✅ 10 min |
| Week 1 | Monitor performance | 📊 Daily 5 min |
| Week 2+ | Implement advanced features | 🔮 As needed |

---

## 💡 Pro Tips

1. **Auto-start on reboot:**
   ```bash
   sudo systemctl enable agent-zero-telegram-bot
   ```

2. **Check bot from phone:**
   Just open Telegram and send commands

3. **Share commands with team:**
   Use inline buttons: Just click buttons instead of typing

4. **Monitor remotely:**
   SSH into server and check logs anytime

5. **Backup .env:**
   ```bash
   cp /root/.env /root/backups/.env.backup
   chmod 600 /root/backups/.env.backup
   ```

6. **Rotate credentials quarterly:**
   Update tokens in .env and restart

7. **Test before deploying:**
   Always use `--dry-run` with sync

---

## 🎓 Learning Resources

- **Official Docs:** `docs/TELEGRAM_BOT_GUIDE.md`
- **Deployment Guide:** `TELEGRAM_BOT_DEPLOYMENT.md`
- **Architecture:** `IMPLEMENTATION_SUMMARY.md`
- **Sync System:** `CLAWBOT_SYNC_STRATEGY.md`
- **Integration:** `docs/CLAWBOT_INTEGRATION_GUIDE.md`

---

**Version**: 1.0
**Last Updated**: February 3, 2026
**Status**: Production Ready

---

# You're Ready! 🚀

Your system is complete and ready to deploy.
Start with the Quick Deploy section above.
Good luck! 🎉
