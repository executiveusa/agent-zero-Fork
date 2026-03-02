# 🚀 Agent Zero - Hostinger VPS Deployment Guide

## Deploy Your Own AI Agent for Almost Free (~$4-8/month)

This guide will help you deploy Agent Zero on a Hostinger VPS with minimal cost using FREE model APIs.

---

## 💰 Cost Breakdown

| Service | Cost | Notes |
|---------|------|-------|
| **Hostinger VPS** | $4-8/month | 512MB-1GB RAM, 1 vCPU |
| **Gemini CLI (Google)** | FREE | OAuth authentication, unlimited usage |
| **Antigravity (Vertex AI)** | FREE | Same as Gemini CLI |
| **Venice.ai** | FREE | Free tier with generous limits |
| **Telegram Bot** | FREE | Mobile control |
| **espeak-ng TTS** | FREE | Open source text-to-speech |
| **GitHub** | FREE | For public repositories |
| **Total** | **~$4-8/month** | Just the VPS cost! |

---

## 📋 Prerequisites

### 1. Hostinger VPS
- **Minimum specs**: 512MB RAM, 1 vCPU, 10GB storage
- **Recommended**: 1GB RAM, 1 vCPU, 20GB storage
- **OS**: Ubuntu 20.04/22.04 LTS (recommended)

**Purchase VPS**:
1. Go to [Hostinger VPS](https://www.hostinger.com/vps-hosting)
2. Choose the cheapest plan ($4-8/month)
3. Select Ubuntu 20.04 or 22.04 as OS
4. Complete purchase and note your IP address

### 2. Google Cloud Account (for FREE models)
- Create account at: https://cloud.google.com
- Enable Vertex AI API (FREE)
- No credit card required for OAuth access

### 3. Optional Services
- **Telegram Bot** (FREE): For mobile control
- **Venice.ai API Key** (FREE): Additional free models
- **GitHub Account** (FREE): For git integration

---

## 🚀 Quick Start (Automated Installation)

### Step 1: SSH into Your VPS

```bash
ssh root@YOUR_VPS_IP
```

### Step 2: Download and Run Deployment Script

```bash
# Download the deployment script
curl -o deploy.sh https://raw.githubusercontent.com/executiveusa/agent-zero-Fork/main/deployment/deploy-hostinger.sh

# Make it executable
chmod +x deploy.sh

# Run the script
sudo ./deploy.sh
```

The script will:
- ✅ Check system resources
- ✅ Install Docker and Docker Compose
- ✅ Clone Agent Zero repository
- ✅ Setup optimized configuration
- ✅ Build Docker images
- ✅ Configure firewall
- ✅ Setup auto-start
- ✅ Start services

### Step 3: Access Your Agent

Once deployed, access your agent at:
- **Web UI**: `http://YOUR_VPS_IP:8000`
- **API**: `http://YOUR_VPS_IP:8001`

---

## 🔧 Manual Installation

If you prefer to install manually or the script fails:

### 1. Install Docker

```bash
# Update system
apt-get update && apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Start Docker
systemctl start docker
systemctl enable docker

# Verify installation
docker --version
docker compose version
```

### 2. Clone Repository

```bash
# Create deployment directory
mkdir -p /root/agent-zero
cd /root/agent-zero

# Clone repository
git clone https://github.com/executiveusa/agent-zero-Fork.git .
```

### 3. Configure Environment

```bash
# Copy Hostinger optimized .env template
cp deployment/.env.hostinger.template .env

# Edit configuration
nano .env
```

**Minimum required configuration**:
```bash
# Enable FREE models
GEMINI_CLI_ENABLED="true"
ANTIGRAVITY_ENABLED="true"

# Set default models (FREE)
DEFAULT_MODEL="gemini-2.0-flash"
PLANNING_MODEL="gemini-1.5-pro"
CODING_MODEL="gemini-2.0-flash"
```

### 4. Setup Google Cloud OAuth (for FREE models)

```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Authenticate with Google
gcloud auth login

# Set up application default credentials
gcloud auth application-default login

# Set your project (create one at cloud.google.com if needed)
gcloud config set project YOUR_PROJECT_ID

# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com
```

### 5. Build and Start

```bash
# Build Docker image
docker compose -f deployment/docker-compose.hostinger.yml build

# Start services
docker compose -f deployment/docker-compose.hostinger.yml up -d

# Check logs
docker compose -f deployment/docker-compose.hostinger.yml logs -f
```

---

## 📱 Enable Telegram Bot (Mobile Control)

### 1. Create Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Follow prompts to create your bot
4. Copy the bot token (e.g., `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Get Your Telegram User ID

1. Search for [@userinfobot](https://t.me/userinfobot)
2. Start the bot
3. Copy your user ID (e.g., `123456789`)

### 3. Configure .env

```bash
# Edit .env file
nano /root/agent-zero/.env

# Add these lines:
TELEGRAM_ENABLED="true"
TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
TELEGRAM_ADMIN_ID="YOUR_USER_ID"
```

### 4. Start with Telegram Profile

```bash
cd /root/agent-zero
docker compose -f deployment/docker-compose.hostinger.yml --profile telegram up -d
```

### 5. Test Your Bot

1. Open Telegram
2. Search for your bot by username
3. Send `/start`
4. You can now control Agent Zero from your phone!

**Available Commands**:
- `/start` - Start the bot
- `/status` - Check agent status
- `/task <description>` - Create a new task
- `/logs` - View recent logs
- `/help` - Show all commands

---

## 🌐 Setup Domain and SSL (Recommended)

### 1. Point Domain to VPS

1. Purchase domain (e.g., Hostinger, Namecheap, Cloudflare)
2. Add A record: `agent.yourdomain.com` → `YOUR_VPS_IP`
3. Wait for DNS propagation (5-30 minutes)

### 2. Install Nginx

```bash
apt-get install -y nginx certbot python3-certbot-nginx
```

### 3. Configure Nginx

```bash
# Create nginx config
cat > /etc/nginx/sites-available/agent-zero <<'EOF'
server {
    listen 80;
    server_name agent.yourdomain.com;  # Change to your domain

    client_max_body_size 100M;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/agent-zero /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and reload
nginx -t
systemctl reload nginx
```

### 4. Install SSL Certificate (FREE)

```bash
# Get Let's Encrypt certificate (FREE)
certbot --nginx -d agent.yourdomain.com

# Auto-renewal is configured automatically
```

Now access your agent at: `https://agent.yourdomain.com`

---

## 🔐 Security Best Practices

### 1. Change SSH Port

```bash
# Edit SSH config
nano /etc/ssh/sshd_config

# Change line:
# Port 22
# to:
Port 2222

# Restart SSH
systemctl restart sshd

# Update firewall
ufw allow 2222/tcp
ufw delete allow 22/tcp
```

### 2. Setup SSH Key Authentication

```bash
# On your local machine:
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key to VPS:
ssh-copy-id -p 2222 root@YOUR_VPS_IP

# Disable password authentication on VPS:
nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
systemctl restart sshd
```

### 3. Configure Firewall

```bash
# Install and configure ufw
apt-get install -y ufw

# Default policies
ufw default deny incoming
ufw default allow outgoing

# Allow services
ufw allow 2222/tcp   # SSH (custom port)
ufw allow 80/tcp     # HTTP
ufw allow 443/tcp    # HTTPS

# Enable firewall
ufw enable

# Check status
ufw status
```

### 4. Set Strong Passwords

Edit `.env` and set strong passwords for any services that require them.

### 5. Regular Updates

```bash
# Create update script
cat > /root/update-system.sh <<'EOF'
#!/bin/bash
apt-get update
apt-get upgrade -y
apt-get autoremove -y
docker system prune -af
EOF

chmod +x /root/update-system.sh

# Run weekly via cron
crontab -e
# Add line:
# 0 3 * * 0 /root/update-system.sh
```

---

## 📊 Resource Monitoring

### Check Docker Container Stats

```bash
# Real-time stats
docker stats

# Check specific container
docker stats agent-zero-hostinger
```

### Check System Resources

```bash
# Memory usage
free -h

# Disk usage
df -h

# CPU usage
top

# Or use htop (install with: apt-get install htop)
htop
```

### View Logs

```bash
cd /root/agent-zero

# All logs
docker compose -f deployment/docker-compose.hostinger.yml logs -f

# Specific service
docker compose -f deployment/docker-compose.hostinger.yml logs -f agent-zero

# Last 100 lines
docker compose -f deployment/docker-compose.hostinger.yml logs --tail=100
```

---

## 🔄 Maintenance

### Update Agent Zero

```bash
cd /root/agent-zero

# Pull latest code
git pull

# Rebuild and restart
docker compose -f deployment/docker-compose.hostinger.yml up -d --build
```

### Restart Services

```bash
cd /root/agent-zero

# Restart all
docker compose -f deployment/docker-compose.hostinger.yml restart

# Restart specific service
docker compose -f deployment/docker-compose.hostinger.yml restart agent-zero
```

### Stop Services

```bash
cd /root/agent-zero

# Stop all
docker compose -f deployment/docker-compose.hostinger.yml down

# Stop and remove volumes (CAUTION: deletes data)
docker compose -f deployment/docker-compose.hostinger.yml down -v
```

### Backup Data

```bash
# Create backup directory
mkdir -p /root/backups

# Backup volumes
docker run --rm \
  -v agent-zero_workspace:/workspace \
  -v agent-zero_memory:/memory \
  -v /root/backups:/backup \
  ubuntu tar czf /backup/agent-zero-$(date +%Y%m%d).tar.gz /workspace /memory

# Backup .env
cp /root/agent-zero/.env /root/backups/.env.$(date +%Y%m%d)
```

### Restore Backup

```bash
# Restore volumes
docker run --rm \
  -v agent-zero_workspace:/workspace \
  -v agent-zero_memory:/memory \
  -v /root/backups:/backup \
  ubuntu tar xzf /backup/agent-zero-20240101.tar.gz

# Restore .env
cp /root/backups/.env.20240101 /root/agent-zero/.env
```

---

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose -f deployment/docker-compose.hostinger.yml logs

# Check if ports are already in use
netstat -tulpn | grep -E '8000|8001'

# Check Docker daemon
systemctl status docker
```

### Out of Memory

```bash
# Check memory usage
free -h
docker stats

# Reduce MAX_WORKERS in .env
nano /root/agent-zero/.env
# Set: MAX_WORKERS="1"

# Restart
docker compose -f deployment/docker-compose.hostinger.yml restart
```

### Gemini API Not Working

```bash
# Re-authenticate with Google Cloud
gcloud auth login
gcloud auth application-default login

# Check credentials
gcloud auth list
gcloud config list

# Verify Vertex AI is enabled
gcloud services list --enabled | grep aiplatform
```

### Can't Access Web UI

```bash
# Check if container is running
docker ps

# Check firewall
ufw status
ufw allow 8000/tcp

# Check nginx (if using)
nginx -t
systemctl status nginx

# Check if port is listening
netstat -tulpn | grep 8000
```

### Disk Space Full

```bash
# Clean Docker
docker system prune -af

# Clean apt cache
apt-get clean
apt-get autoremove -y

# Find large files
du -h / | sort -rh | head -20
```

---

## 💡 Cost Optimization Tips

### 1. Use Only FREE Models

```bash
# In .env, use these settings for ZERO API costs:
DEFAULT_MODEL="gemini-2.0-flash"
PLANNING_MODEL="gemini-1.5-pro"
CODING_MODEL="gemini-2.0-flash"

# Leave these EMPTY (don't use paid APIs):
ANTHROPIC_API_KEY=""
OPENAI_API_KEY=""
```

### 2. Disable Heavy Features

```bash
# In .env:
ENABLE_BROWSER_AGENT="false"  # Saves ~200MB RAM
ENABLE_ML_AGENT="false"        # Saves ~300MB RAM
```

### 3. Limit Concurrent Tasks

```bash
# In .env:
MAX_WORKERS="1"  # For 512MB VPS
MAX_WORKERS="2"  # For 1GB VPS
```

### 4. Use Smaller VPS for Testing

Start with Hostinger's smallest VPS ($3.99/month), then upgrade if needed:
- 512MB RAM: Good for light usage, 1-2 concurrent tasks
- 1GB RAM: Better for regular usage, 2-4 concurrent tasks
- 2GB RAM: Good for heavy usage, enables browser agent

### 5. Monitor and Optimize

```bash
# Check what's using resources
docker stats
htop

# Optimize based on usage patterns
```

---

## 🎯 Upgrade Path (When You Need More)

### Level 1: Almost Free (~$4-8/month)
- ✅ Hostinger VPS (512MB-1GB)
- ✅ Gemini CLI (FREE)
- ✅ Venice.ai (FREE tier)
- ✅ espeak-ng TTS
- ❌ No browser automation
- ❌ No ML features

### Level 2: Light Usage (~$15-20/month)
- ✅ Hostinger VPS (2GB RAM)
- ✅ Gemini CLI (FREE)
- ✅ Venice.ai (FREE tier)
- ✅ Browser automation enabled
- ✅ Better TTS (Kokoro)
- ⚠️ Optional: Claude API ($10-15/month usage)

### Level 3: Heavy Usage (~$40-60/month)
- ✅ Hostinger VPS (4-8GB RAM)
- ✅ All FREE models
- ✅ Claude API ($20-30/month)
- ✅ OpenAI API ($10-20/month)
- ✅ Browser automation
- ✅ ML features enabled

### Level 4: Production (~$100+/month)
- ✅ Dedicated server or cloud VPS
- ✅ GPU for ML workloads
- ✅ All premium APIs
- ✅ High availability setup
- ✅ Auto-scaling

---

## 📚 Additional Resources

- **Agent Zero Documentation**: https://github.com/agent0ai/agent-zero/docs
- **Hostinger Support**: https://www.hostinger.com/tutorials/vps
- **Google Cloud Vertex AI**: https://cloud.google.com/vertex-ai/docs
- **Docker Documentation**: https://docs.docker.com
- **Telegram Bot API**: https://core.telegram.org/bots

---

## 🤝 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Check Agent Zero GitHub Issues: https://github.com/agent0ai/agent-zero/issues
3. Join Discord: https://discord.gg/B8KZKNsPpj
4. Check Hostinger support if VPS-related

---

## 📝 License

Agent Zero is open source. Check the main repository for license details.

---

## 🎉 You're All Set!

Congratulations! You now have your own AI agent running for almost free.

**What you've achieved**:
- ✅ Self-hosted AI agent on your own VPS
- ✅ FREE model access (Gemini, Venice.ai)
- ✅ Mobile control via Telegram
- ✅ Total cost: ~$4-8/month
- ✅ Full control and privacy

**Next steps**:
1. Explore the Web UI at `http://YOUR_VPS_IP:8000`
2. Try creating your first task
3. Set up Telegram bot for mobile access
4. Configure domain and SSL for production use
5. Customize prompts in `/app/prompts/` directory

Enjoy your almost-free AI assistant! 🚀
