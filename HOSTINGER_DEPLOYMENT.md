# Hostinger Deployment Guide

## ✅ Status
Agent Zero is now configured for deployment to your Hostinger server via Coolify.

## 🎯 Quick Start

### Prerequisites
- Hostinger Server (with Coolify installed)
- GitHub Account with Secrets configured
- Docker Hub Account (already set up: executiveusa)

### Step 1: Add GitHub Secrets

Go to: **https://github.com/executiveusa/agent-zero-Fork/settings/secrets/actions**

Add these secrets:

```
COOLIFY_API_TOKEN = [from vault - see retrieve_hostinger_creds.py]
HOSTINGER_API_TOKEN = [from vault - see retrieve_hostinger_creds.py]
DOCKER_USER = executiveusa
DOCKER_TOKEN = [your Docker PAT from vault]
```

**To get vault credentials:**
```bash
python retrieve_hostinger_creds.py
```

### Step 2: Deploy to Hostinger via Coolify

**Option A: Automatic (Recommended)**
```bash
# Just push to main branch
git add .
git commit -m "Deploy Agent Zero"
git push origin main
```

GitHub Actions will automatically:
1. Build Docker image
2. Push to Docker Hub
3. Notify Coolify to redeploy

**Option B: Manual Coolify Deployment**
1. Visit https://app.coolify.io
2. Go to your Agent Zero deployment
3. Click "Redeploy" 
4. Coolify will pull latest image and restart

### Step 3: Configure Domain & SSL

In Coolify Dashboard:
1. Select Agent Zero deployment
2. Add your domain (e.g., `agent-zero.yourdomain.com`)
3. Enable SSL/HTTPS (auto with Let's Encrypt)
4. Configure environment variables:
   ```
   NODE_ENV=production
   NEXTAUTH_URL=https://agent-zero.yourdomain.com
   AZ_BASE_URL=http://localhost:3000
   ```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         Hostinger Server                    │
│  ┌────────────────────────────────────────┐ │
│  │         Coolify Control Plane          │ │
│  │  (Manages deployments & services)      │ │
│  └────────────────────────────────────────┘ │
│                    ↑                         │
│  ┌────────────────────────────────────────┐ │
│  │      Docker Containers                 │ │
│  │  ┌──────────────┐  ┌──────────────┐   │ │
│  │  │  Next.js     │  │  PostgreSQL  │   │ │
│  │  │  App         │  │  Database    │   │ │
│  │  │  Port 3000   │  │  Port 5432   │   │ │
│  │  └──────────────┘  └──────────────┘   │ │
│  │  ┌──────────────┐  ┌──────────────┐   │ │
│  │  │  Redis       │  │  MCP Server  │   │ │
│  │  │  Port 6379   │  │  Port 8000   │   │ │
│  │  └──────────────┘  └──────────────┘   │ │
│  └────────────────────────────────────────┘ │
│                    ↑                         │
│  ┌────────────────────────────────────────┐ │
│  │     Caddy/Nginx (Reverse Proxy)        │ │
│  │     Port 80 & 443 (HTTP/HTTPS)         │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
        ↓
   GitHub Actions
   (Automatic Deploys)
        ↓
   Docker Hub Registry
   (executiveusa/agent-zero-fork:latest)
```

## 📊 Deployment Flow

1. **Developer** pushes to `main` branch
2. **GitHub Actions** workflow triggers:
   - Builds Docker image
   - Tags with commit SHA + latest
   - Pushes to Docker Hub
3. **Coolify** detects new image:
   - Pulls latest version
   - Stops old container
   - Starts new container
   - Verifies health
4. **Caddy** (reverse proxy) routes traffic
5. **Application** running at your domain

## 🔧 Useful Commands

### Check Deployment Status
```bash
# View Coolify deployments
# https://app.coolify.io/deployments

# Monitor Docker containers on server
docker ps
docker logs agent-zero-fork-next-js

# Check database
docker exec agent-zero-fork-postgres psql -U agent_zero -c "SELECT * from migrations;"
```

### Manual Redeploy
```bash
# SSH into Hostinger server
ssh root@YOUR_SERVER_IP

# Pull latest image
docker pull executiveusa/agent-zero-fork:latest

# Restart via Docker Compose
cd /app/agent-zero-fork
docker-compose down
docker-compose up -d
```

### View Logs
```bash
# On Hostinger server
docker logs -f agent-zero-fork-next-js

# Or via Coolify dashboard
# https://app.coolify.io/monitoring
```

## 🛡️ Security Checklist

- ✅ Secrets stored in GitHub (not in code)
- ✅ Docker credentials encrypted
- ✅ HTTPS/SSL enabled via Coolify
- ✅ Database password auto-generated
- ✅ Rate limiting configured (via Caddy)
- ✅ Firewall rules (configure in Hostinger)

## 📈 Monitoring

### Coolify Dashboard
- Deployments: https://app.coolify.io/deployments
- Monitoring: https://app.coolify.io/monitoring
- Logs: https://app.coolify.io/logs

### Application Health
```bash
curl https://agent-zero.yourdomain.com/api/health
```

Should return: `{"status":"ok"}`

## 🚨 Troubleshooting

### Deployment Stuck
1. Check GitHub Actions logs
2. Verify GitHub Secrets are set correctly
3. Check Coolify dashboard for deployment errors

### Container Won't Start
```bash
docker logs agent-zero-fork-next-js
# Check for missing environment variables or port conflicts
```

### Domain Not Working
1. Verify domain DNS points to Hostinger server
2. In Coolify, wait 2-3 minutes for SSL cert generation
3. Check Caddy reverse proxy config

### Database Connection Error
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Verify connection string
docker exec agent-zero-fork-next-js env | grep DATABASE
```

## 📚 Resources

- Coolify Docs: https://coolify.io/docs
- Docker Docs: https://docs.docker.com
- Next.js Deployment: https://nextjs.org/docs/deployment
- PostgreSQL: https://www.postgresql.org/docs

## 💬 Support

Issues? Check:
1. GitHub Actions workflow logs
2. Coolify deployment logs
3. Container logs: `docker logs [container-name]`
4. Application error logs

---

**Last Updated**: 2026-02-06
**Deployment Status**: ✅ Ready
**Next Step**: Add GitHub Secrets and push to deploy
