# Agent Zero Telegram Control Bot

## 📱 Overview

The **Telegram Control Bot** is a secure command interface for managing Agent Zero and the ClawBot synchronization system directly from Telegram. Control your repository, monitor Agent Zero's health, and trigger syncs without leaving Telegram.

**Key Features:**
- 🔐 Secure admin authentication
- 📦 Repository management (status, commits, PRs, git operations)
- 🔄 ClawBot sync control (manual trigger, status checks)
- 🤖 Agent Zero monitoring (health, statistics)
- 📊 Real-time status updates
- 🚨 Error notifications
- 🎯 Inline button interface

---

## 🚀 Quick Start

### 1. Create Telegram Bot

1. Open Telegram and chat with [@BotFather](https://t.me/botfather)
2. Send `/newbot`
3. Follow the prompts:
   - Bot name: `Agent Zero Control` (or your preference)
   - Bot username: `agent_zero_control_bot` (must be unique)
4. Copy the **token** (looks like `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

Save this token for later!

### 2. Get Your Telegram ID

1. Chat with [@userinfobot](https://t.me/userinfobot)
2. It will show your user ID
3. Save this ID

### 3. Setup Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and fill in:
```bash
# Telegram
TELEGRAM_BOT_TOKEN="your_bot_token_here"
TELEGRAM_ADMIN_ID="your_user_id_here"

# GitHub
GITHUB_TOKEN="ghp_your_github_token_here"
GITHUB_OWNER="executiveusa"
GITHUB_REPO="agent-zero-Fork"

# Agent Zero
AGENT_ZERO_API_URL="http://localhost:8000"

# Server (if on Hostinger)
HOSTINGER_DEPLOY_PATH="/root/agent-zero"
```

### 4. Install Dependencies

```bash
pip install -r requirements-telegram-bot.txt
```

### 5. Run the Bot

**Development (polling mode):**
```bash
python3 telegram_bot.py
```

**Production (systemd):**
```bash
sudo bash deployment/deploy-telegram-bot.sh
sudo systemctl start agent-zero-telegram-bot
sudo systemctl enable agent-zero-telegram-bot  # Auto-start
```

**Docker:**
```bash
docker-compose -f deployment/docker-compose.telegram-bot.yml up -d
```

---

## 📋 Commands Reference

### Repository Commands

#### `/repo_status`
Shows repository information:
- URL and owner
- Star and fork counts
- Latest commit hash
- Default branch

**Example:**
```
/repo_status
```

**Response:**
```
✅ Repository Status

Repository: agent-zero-Fork
Owner: executiveusa
URL: https://github.com/executiveusa/agent-zero-Fork
Stars: 1250
Watchers: 450
Forks: 180
Default Branch: main
Latest Commit: `ab12cd3`
```

---

#### `/repo_commits`
Shows the last 5 commits on the main branch:
- Commit hash (short)
- Message
- Author
- Date

**Example:**
```
/repo_commits
```

---

#### `/repo_prs`
Lists all open pull requests:
- PR number and title
- Author
- Creation date

**Example:**
```
/repo_prs
```

---

#### `/git_status`
Shows local repository git status (on server):
- Number of modified files
- List of changes
- Uncommitted changes

**Example:**
```
/git_status
```

---

#### `/git_pull`
Pulls the latest changes from the remote branch:
- Updates all files
- Resolves updates
- Shows pull summary

⚠️ **Warning**: This modifies local files. Use with caution.

**Example:**
```
/git_pull
```

---

### Sync Commands

#### `/sync_trigger`
Triggers the GitHub Actions workflow for ClawBot synchronization:
- Creates a new sync branch
- Pulls latest ClawBot updates
- Creates PR for review
- Validates integration

**Example:**
```
/sync_trigger
```

**Response:**
```
✅ Sync Workflow Triggered

ClawBot sync workflow triggered on main branch

The workflow will run and create a PR if updates are found.
Check GitHub Actions for progress.
```

---

#### `/sync_check`
Performs a dry-run sync check (no changes made):
- Shows what would be synced
- Identifies potential conflicts
- Estimates merge impact

**Example:**
```
/sync_check
```

---

### Agent Zero Commands

#### `/agent_health`
Shows Agent Zero health status:
- Status (healthy/unhealthy)
- Uptime
- Version
- Active chats
- Memory usage

**Example:**
```
/agent_health
```

**Response:**
```
✅ Agent Zero Health

Status: ✅ Healthy
Uptime: 3600 seconds
Version: 0.9.7
Active Chats: 12
Memory Usage: 1245 MB
```

---

#### `/agent_stats`
Shows Agent Zero statistics:
- Total messages processed
- Total chats
- Total tools used
- Average response time

**Example:**
```
/agent_stats
```

---

### Help Commands

#### `/help`
Shows all available commands with descriptions

#### `/start`
Shows welcome message and quick access buttons

---

## 🔒 Security

### Authentication

The bot uses **Telegram user ID** for authentication:

1. Only users in the authorized list can use commands
2. Admin ID has full access
3. Additional users via `TELEGRAM_AUTHORIZED_USERS` env var
4. Unauthorized access is logged and denied

### Secret Management

**Secrets are never exposed:**
- Environment variables loaded from `.env`
- `.env` file in `.gitignore` (never committed)
- Secrets masked in logs
- GitHub token never shown in responses
- All credentials kept in environment

### Best Practices

1. ✅ **DO:**
   - Keep `.env` file safe and secure
   - Use strong GitHub tokens with minimal scopes
   - Limit authorized users list
   - Review commands before executing
   - Monitor logs for suspicious activity

2. ❌ **DON'T:**
   - Commit `.env` to git
   - Share bot token publicly
   - Give bot access to multiple admins unnecessarily
   - Run dangerous commands without review
   - Store credentials in code

### Credential Rotation

Rotate credentials regularly:

```bash
# 1. Generate new token in @BotFather
# 2. Get new GitHub token at https://github.com/settings/tokens
# 3. Update .env file
# 4. Restart bot
sudo systemctl restart agent-zero-telegram-bot
```

---

## 🐛 Troubleshooting

### Bot doesn't respond to commands

**Solution:**
1. Check bot is running: `systemctl status agent-zero-telegram-bot`
2. Check logs: `journalctl -u agent-zero-telegram-bot -f`
3. Verify bot token: `echo $TELEGRAM_BOT_TOKEN`
4. Verify you're authorized: Check TELEGRAM_ADMIN_ID in .env

### "Unauthorized" message

**Solution:**
1. Get your Telegram ID from [@userinfobot](https://t.me/userinfobot)
2. Update TELEGRAM_ADMIN_ID in .env
3. Restart bot

### API connection errors

**Solution:**
1. Verify Agent Zero is running: `curl http://localhost:8000/api/health`
2. Check AGENT_ZERO_API_URL in .env
3. Check firewall allows connection
4. Check Agent Zero logs

### GitHub token errors

**Solution:**
1. Generate new token at https://github.com/settings/tokens
2. Token needs `repo` scope
3. Update GITHUB_TOKEN in .env
4. Restart bot

### Sync workflow not found

**Solution:**
1. Ensure `.github/workflows/sync-clawbot-updates.yml` exists
2. Push the file to the branch
3. Try `/sync_trigger` again

---

## 📊 Monitoring

### Logs

View bot logs:

```bash
# Systemd logs
journalctl -u agent-zero-telegram-bot -f

# File logs
tail -f /tmp/agent_zero_telegram_bot.log

# Docker logs
docker logs agent-zero-telegram-bot -f
```

### Health Checks

The bot includes periodic health checks:

```bash
# Check bot response
curl http://localhost:8001/health

# Check Agent Zero
curl http://localhost:8000/api/health
```

### Metrics to Track

- Command success rate
- Average response time
- Sync frequency
- Unauthorized access attempts
- API error rates

---

## 🔧 Advanced Configuration

### Multiple Authorized Users

```bash
# In .env
TELEGRAM_AUTHORIZED_USERS="123456789,987654321,555555555"
```

### Custom API Endpoint

```bash
# For remote server
AGENT_ZERO_API_URL="https://agent-zero.example.com:8000"
```

### Webhook Mode (Production)

Instead of polling, use webhook (faster):

```bash
# In .env
TELEGRAM_WEBHOOK_URL="https://your-domain.com/telegram/webhook"
```

Requires:
- Valid domain (HTTPS)
- Open port 443
- Certificate setup

### Slack Notifications

Get sync notifications in Slack:

```bash
# In .env
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

---

## 🚀 Deployment

### Local Development

```bash
python3 telegram_bot.py
```

### Hostinger VPS (Systemd)

```bash
sudo bash deployment/deploy-telegram-bot.sh
sudo systemctl start agent-zero-telegram-bot
sudo systemctl enable agent-zero-telegram-bot
```

### Docker (Any Server)

```bash
docker-compose -f deployment/docker-compose.telegram-bot.yml up -d
```

### Kubernetes (Enterprise)

```bash
kubectl apply -f deployment/k8s/telegram-bot-deployment.yaml
```

---

## 📈 Usage Examples

### Morning Routine

```
/agent_health      # Check if Agent Zero is running
/repo_commits      # See what changed overnight
/sync_check        # Check if sync needed
```

### After Deploy

```
/repo_status       # Confirm latest version
/git_pull          # Update local copy
/agent_health      # Verify Agent Zero healthy
```

### Regular Maintenance

```
/sync_trigger      # Trigger ClawBot sync
/agent_stats       # Review usage stats
```

---

## 🤝 Contributing

To add new commands:

1. Add handler function in `TelegramBotHandlers` class
2. Register in `create_app()` function
3. Add to `/help` command documentation
4. Test thoroughly

Example:

```python
async def handle_custom_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /custom_command"""
    response = CommandResponse(
        success=True,
        title="Custom Command",
        message="Command output here"
    )
    await update.message.reply_text(
        response.to_string(),
        parse_mode="Markdown"
    )
```

---

## 📞 Support

For issues:

1. Check logs: `journalctl -u agent-zero-telegram-bot -f`
2. Review this guide
3. Check `.env` configuration
4. Verify network connectivity
5. File GitHub issue with logs

---

## 📝 License

Same as Agent Zero (check main project LICENSE)

---

**Last Updated**: February 3, 2026
**Version**: 1.0.0
**Maintainer**: Agent Zero Team
