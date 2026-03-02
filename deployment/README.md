# Agent Zero Deployment Options

This directory contains deployment configurations for various platforms.

## Available Deployments

### 🌐 Hostinger VPS (Almost Free - Recommended)
**Cost**: ~$4-8/month (just the VPS!)

Deploy Agent Zero on a budget-friendly VPS using FREE model APIs.

**Quick Start**:
```bash
curl -o deploy.sh https://raw.githubusercontent.com/executiveusa/agent-zero-Fork/main/deployment/deploy-hostinger.sh
chmod +x deploy.sh
sudo ./deploy.sh
```

**Features**:
- ✅ Optimized for 512MB-1GB RAM VPS
- ✅ Uses FREE Gemini CLI + Antigravity OAuth
- ✅ Lightweight espeak-ng TTS
- ✅ Optional Telegram bot for mobile control
- ✅ Complete deployment automation
- ✅ Auto-start on boot

**Files**:
- `Dockerfile.hostinger` - Lightweight Dockerfile
- `docker-compose.hostinger.yml` - Optimized compose file
- `.env.hostinger.template` - Cost-optimized environment template
- `deploy-hostinger.sh` - Automated deployment script
- `systemd/agent-zero-hostinger.service` - Auto-start service

**Documentation**: See [HOSTINGER_DEPLOYMENT_GUIDE.md](../HOSTINGER_DEPLOYMENT_GUIDE.md)

---

### 📱 Telegram Bot
Control Agent Zero from your mobile device.

**Quick Start**:
```bash
cd deployment
./deploy-telegram-bot.sh
```

**Features**:
- ✅ Mobile command center
- ✅ Task creation and monitoring
- ✅ View logs remotely
- ✅ GitHub integration
- ✅ FREE (no additional cost)

**Files**:
- `Dockerfile.telegram-bot` - Telegram bot Dockerfile
- `docker-compose.telegram-bot.yml` - Telegram bot compose file
- `deploy-telegram-bot.sh` - Deployment script

---

### 🧪 Loveable.dev Testing
Browser automation testing for Loveable.dev credentials.

**Quick Start**:
```bash
cd deployment
./run_loveable_test_hostinger.sh
```

**Features**:
- ✅ Automated credential testing
- ✅ Multiple deployment options
- ✅ JSON output format
- ✅ Docker containerization

**Files**:
- `run_loveable_test_hostinger.sh` - VPS deployment script
- `deploy_loveable_test.py` - SSH automation script

**Documentation**: See [LOVEABLE_SOLUTIONS_GUIDE.md](../LOVEABLE_SOLUTIONS_GUIDE.md)

---

## Deployment Comparison

| Feature | Hostinger VPS | Local Docker | Cloud (AWS/GCP) |
|---------|---------------|--------------|-----------------|
| **Cost** | ~$4-8/month | FREE | $20-100+/month |
| **Setup Time** | 10 minutes | 5 minutes | 30+ minutes |
| **24/7 Availability** | ✅ Yes | ❌ No | ✅ Yes |
| **Mobile Access** | ✅ Yes | ⚠️ Limited | ✅ Yes |
| **Resource Limits** | 512MB-1GB RAM | Your machine | Scalable |
| **Best For** | Budget users | Development | Production |

---

## Quick Comparison: Cost Analysis

### Hostinger VPS (Recommended for budget)
- **VPS**: $4-8/month
- **Models**: FREE (Gemini CLI)
- **Total**: **$4-8/month**

### Local Development (FREE but not 24/7)
- **Hardware**: Your computer
- **Models**: FREE (Gemini CLI)
- **Total**: **$0/month** (not always running)

### AWS/GCP Cloud (Production)
- **Compute**: $30-100/month
- **Models**: FREE or paid
- **Storage**: $5-20/month
- **Total**: **$35-120+/month**

---

## Getting Started

### 1. Choose Your Deployment

For most users starting out:
- **Budget-conscious**: Hostinger VPS
- **Testing/Development**: Local Docker
- **Production/Enterprise**: Cloud deployment

### 2. Follow the Guide

Each deployment has detailed instructions:
- Hostinger: [HOSTINGER_DEPLOYMENT_GUIDE.md](../HOSTINGER_DEPLOYMENT_GUIDE.md)
- Telegram: [deploy-telegram-bot.sh](./deploy-telegram-bot.sh)
- Loveable: [LOVEABLE_SOLUTIONS_GUIDE.md](../LOVEABLE_SOLUTIONS_GUIDE.md)

### 3. Configure Environment

Copy the appropriate `.env` template:
```bash
# For Hostinger
cp .env.hostinger.template ../.env

# For local development
cp ../.env.example ../.env
```

### 4. Deploy!

Run the deployment script for your chosen platform.

---

## Support

Need help? Check these resources:
- [Main Documentation](../docs/README.md)
- [Troubleshooting](../docs/troubleshooting.md)
- [Discord Community](https://discord.gg/B8KZKNsPpj)
- [GitHub Issues](https://github.com/agent0ai/agent-zero/issues)

---

## Contributing

Have a new deployment configuration?

1. Create your deployment files in this directory
2. Add documentation
3. Update this README
4. Submit a pull request!

---

## License

See main repository for license information.
