# Telegram Bot Deployment Guide

## 📋 Table of Contents

1. [Quick Start](#-quick-start)
2. [Setup Requirements](#-setup-requirements)
3. [Configuration](#-configuration)
4. [Installation Options](#-installation-options)
5. [Post-Deployment](#-post-deployment)
6. [Monitoring](#-monitoring)
7. [Troubleshooting](#-troubleshooting)

---

## 🚀 Quick Start

**For the impatient:**

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit with your Telegram bot token and admin ID
nano .env

# 3. Install and run
pip install -r requirements-telegram-bot.txt
python3 telegram_bot.py
```

Then send `/start` to your bot in Telegram. Done!

---

## 📦 Setup Requirements

### Prerequisites

- **Python 3.8+** (tested on 3.11)
- **pip** or **pip3**
- **Telegram Bot Token** (from @BotFather)
- **Telegram Admin ID** (from @userinfobot)
- **GitHub Token** (optional, for GitHub operations)
- **Internet connection**

### Optional (for production)

- **Hostinger VPS** (or any Linux server)
- **Docker & Docker Compose** (for containerization)
- **Systemd** (for service management)

---

## ⚙️ Configuration

### Step 1: Create Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/botfather)
2. Send `/newbot`
3. Answer the prompts:
   ```
   Alright, a new bot. How are we going to call it? Please choose a name for your bot.
   → Agent Zero Control

   Good. Now let's choose a username for your bot. It must end in `bot`.
   → agent_zero_control_bot
   ```
4. Copy the token: `123456:ABC-DEF1234ghIkl...`

### Step 2: Get Your Telegram ID

1. Message [@userinfobot](https://t.me/userinfobot)
2. It replies with your ID: `123456789`

### Step 3: Create GitHub Token (Optional)

1. Go to https://github.com/settings/tokens
2. Click "Generate new token"
3. Select scopes:
   - ✅ `repo` (all)
   - ✅ `workflow` (optional)
4. Copy the token: `ghp_1234567890abcdef...`

### Step 4: Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit your values
nano .env
```

**Minimal configuration:**
```bash
# Required
TELEGRAM_BOT_TOKEN="your_bot_token_here"
TELEGRAM_ADMIN_ID="your_user_id_here"

# For repository operations (optional)
GITHUB_TOKEN="ghp_your_token_here"
GITHUB_OWNER="executiveusa"
GITHUB_REPO="agent-zero-Fork"

# For Agent Zero monitoring
AGENT_ZERO_API_URL="http://localhost:8000"
```

**Full configuration:** See `.env.example` for all options

### Step 5: Protect Your Secrets

Ensure `.env` is never committed:

```bash
# Verify .env is in .gitignore
grep "^\.env$" .gitignore

# Set proper permissions
chmod 600 .env

# Never commit
git status  # Should not show .env
```

---

## 🖥️ Installation Options

Choose based on your environment:

### Option 1: Local Development (Quickest)

```bash
# Install dependencies
pip3 install -r requirements-telegram-bot.txt

# Load environment
export $(cat .env | xargs)

# Run bot
python3 telegram_bot.py
```

**Pros:** Simple, quick, good for testing
**Cons:** Stops when you close terminal, no auto-restart

---

### Option 2: Systemd Service (Recommended for Production)

```bash
# Run deployment script
bash deployment/deploy-telegram-bot.sh

# Edit configuration
nano /root/.env

# Start bot
sudo systemctl start agent-zero-telegram-bot

# Enable auto-start on reboot
sudo systemctl enable agent-zero-telegram-bot

# View logs
sudo journalctl -u agent-zero-telegram-bot -f
```

**Pros:** Automatic restart, persistent, production-ready
**Cons:** Requires Linux/systemd, needs sudo

---

### Option 3: Docker (Most Portable)

```bash
# Build container
docker build -f deployment/Dockerfile.telegram-bot -t agent-zero-telegram-bot .

# Create .env file (Docker will use it)
cp .env.example .env
# Edit .env

# Run container
docker run -d \
  --name agent-zero-telegram-bot \
  --env-file .env \
  -v $(pwd):/root/agent-zero \
  agent-zero-telegram-bot

# View logs
docker logs -f agent-zero-telegram-bot

# Stop
docker stop agent-zero-telegram-bot
```

Or use Docker Compose:

```bash
# Start all services
docker-compose -f deployment/docker-compose.telegram-bot.yml up -d

# View logs
docker-compose -f deployment/docker-compose.telegram-bot.yml logs -f telegram-bot

# Stop
docker-compose -f deployment/docker-compose.telegram-bot.yml down
```

**Pros:** Isolated, portable, easy to scale
**Cons:** Requires Docker, slightly more complex

---

### Option 4: Screen/Tmux (Temporary)

```bash
# Run in detached screen session
screen -S telegram-bot -d -m bash -c 'cd /root/agent-zero && python3 telegram_bot.py'

# Attach to session
screen -r telegram-bot

# Detach (Ctrl+A then D)
```

**Pros:** Easy, no installation needed
**Cons:** Stops if server reboots

---

## ✅ Post-Deployment

### Step 1: Verify Bot is Running

```bash
# Check status
systemctl status agent-zero-telegram-bot

# Or check logs
journalctl -u agent-zero-telegram-bot -n 10
```

### Step 2: Test Bot Commands

Open Telegram and send:

```
/start          # Should show welcome
/help           # Should show all commands
/repo_status    # Should show repository info
/agent_health   # Should show Agent Zero status
```

### Step 3: Set Bot Commands (Optional)

In @BotFather, set command list:

```
/start - Start the bot
/help - Show all available commands
/repo_status - Show repository status
/repo_commits - Show recent commits
/repo_prs - Show open pull requests
/git_status - Check git status
/git_pull - Pull latest changes
/sync_trigger - Trigger ClawBot sync
/sync_check - Check what would sync
/agent_health - Check Agent Zero health
/agent_stats - Show Agent Zero statistics
```

In @BotFather:
1. Select your bot
2. Send `/setcommands`
3. Paste the commands above

---

## 📊 Monitoring

### System Health

```bash
# Check if bot is running
systemctl is-active agent-zero-telegram-bot

# Get bot process info
ps aux | grep telegram_bot.py

# Check resource usage
top -p $(pgrep -f telegram_bot.py)
```

### Log Analysis

```bash
# Recent logs
journalctl -u agent-zero-telegram-bot -n 50

# Errors only
journalctl -u agent-zero-telegram-bot -p err

# Real-time logs
journalctl -u agent-zero-telegram-bot -f

# Logs from specific time
journalctl -u agent-zero-telegram-bot --since "1 hour ago"
```

### Performance Metrics

```bash
# Memory usage
free -h

# Disk usage
df -h

# Network connections
netstat -tlnp | grep python

# Check log file size
du -h /tmp/agent_zero_telegram_bot.log
```

---

## 🔧 Configuration Updates

### Change Bot Token

```bash
# 1. Get new token from @BotFather
# 2. Update .env
nano /root/.env
# Edit TELEGRAM_BOT_TOKEN=...

# 3. Restart bot
sudo systemctl restart agent-zero-telegram-bot

# 4. Verify
journalctl -u agent-zero-telegram-bot -f
```

### Change Authorized Users

```bash
# 1. Edit .env
nano /root/.env

# 2. Update:
TELEGRAM_ADMIN_ID="new_admin_id"
TELEGRAM_AUTHORIZED_USERS="user1,user2,user3"

# 3. Restart
sudo systemctl restart agent-zero-telegram-bot
```

### Enable Debug Mode

```bash
# In .env
DEBUG="true"
LOG_LEVEL="DEBUG"

# Restart
sudo systemctl restart agent-zero-telegram-bot

# Now logs will show more details
journalctl -u agent-zero-telegram-bot -f
```

---

## 🚨 Troubleshooting

### Bot Doesn't Respond

**Check if running:**
```bash
systemctl status agent-zero-telegram-bot
```

**Check logs for errors:**
```bash
journalctl -u agent-zero-telegram-bot -p err
```

**Common causes:**
- Invalid bot token → Get new from @BotFather
- Not authorized → Check TELEGRAM_ADMIN_ID
- Bot not running → Run: `sudo systemctl restart agent-zero-telegram-bot`

### "Unauthorized" Message

**Solution:**
```bash
# 1. Get your ID from @userinfobot
# 2. Update .env
TELEGRAM_ADMIN_ID="your_id_here"
# 3. Restart
sudo systemctl restart agent-zero-telegram-bot
```

### Command Returns Error

**Check Agent Zero is running:**
```bash
curl http://localhost:8000/api/health
```

**If Agent Zero not responding:**
```bash
# Restart Agent Zero
cd /root/agent-zero
docker-compose restart
```

**Check GitHub connection:**
```bash
# Verify GitHub token is valid
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

### Memory Usage High

**Restart bot:**
```bash
sudo systemctl restart agent-zero-telegram-bot
```

**Check memory:**
```bash
free -h
```

**Reduce log verbosity:**
```bash
# In .env
LOG_LEVEL="WARNING"

# Restart
sudo systemctl restart agent-zero-telegram-bot
```

### Docker Container Won't Start

**Check logs:**
```bash
docker logs agent-zero-telegram-bot
```

**Common issues:**
- Missing .env file → `cp .env.example .env`
- Invalid environment variables → Check .env syntax
- Port already in use → Change BOT_SERVER_PORT in .env

**Rebuild container:**
```bash
docker-compose -f deployment/docker-compose.telegram-bot.yml down
docker-compose -f deployment/docker-compose.telegram-bot.yml up -d --build
```

---

## 🔐 Security Checklist

Before going to production:

- [ ] `.env` file created and filled with real values
- [ ] `.env` is in `.gitignore`
- [ ] `.env` has restrictive permissions: `chmod 600 .env`
- [ ] Bot token not shared or exposed
- [ ] GitHub token has minimal required scopes
- [ ] Only authorized users in `TELEGRAM_AUTHORIZED_USERS`
- [ ] Running with minimal required permissions
- [ ] Logs don't expose sensitive information
- [ ] Regular credential rotation schedule set
- [ ] Backup of `.env` stored securely
- [ ] Firewall rules restrict API access
- [ ] Rate limiting enabled in configuration

---

## 📈 Scaling

### Multiple Instances

For high-volume usage:

```bash
# Run multiple instances with load balancer
docker-compose up -d --scale telegram-bot=3
```

### Monitoring

Use Prometheus/Grafana:

```bash
# Add to docker-compose
  prometheus:
    image: prom/prometheus
    volumes:
      - ./deployment/prometheus.yml:/etc/prometheus/prometheus.yml
```

### Database

Add persistent storage for command history:

```bash
# In .env
BOT_DATABASE_URL="postgresql://user:pass@localhost/agent_zero_bot"
```

---

## 📞 Getting Help

1. **Check logs:** `journalctl -u agent-zero-telegram-bot -f`
2. **Read docs:** `docs/TELEGRAM_BOT_GUIDE.md`
3. **File issue:** Include logs, .env structure (not values), bot version
4. **Debug:** Enable `DEBUG=true` in .env, run with verbose logging

---

## 📝 Next Steps

1. ✅ Deploy bot
2. ✅ Test all commands
3. ✅ Set up monitoring
4. ✅ Configure backups
5. ✅ Document procedures
6. ✅ Train team on bot commands

---

**Deployment Complete!** 🎉

Your Telegram control bot is now managing Agent Zero. You can:
- Monitor repository status
- Trigger ClawBot syncs
- Check Agent Zero health
- Pull updates
- All from Telegram!

For detailed command reference, see `docs/TELEGRAM_BOT_GUIDE.md`

---

**Last Updated**: February 3, 2026
**Version**: 1.0.0
