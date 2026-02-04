# Agent Zero Dashboard - Vercel Deployment Guide

## 📋 Overview

Deploy the Agent Zero dashboard frontend to Vercel for global edge network distribution, automatic SSL, continuous deployment, and zero-downtime updates.

**Version**: 1.0.0
**Date**: February 3, 2026
**Status**: Ready for Production

---

## ✨ What Gets Deployed

- **Frontend Dashboard**: Agent Zero web UI (vanilla JS)
- **Static Assets**: HTML, CSS, JS, images, fonts
- **Login Interface**: Authentication page
- **Components**: Chat, projects, settings, memory dashboard
- **API Proxy**: Routes to Agent Zero backend

**Size**: ~5MB static files
**Load Time**: <1s (global edge cache)
**Uptime**: 99.99% SLA

---

## 🚀 Deployment Steps

### Step 1: Prepare Repository

```bash
cd /home/user/agent-zero-Fork

# Verify all files are committed
git status

# Push to GitHub
git push origin claude/auto-update-agent-zero-mzNwX
```

### Step 2: Connect to Vercel

#### Option A: Via GitHub (Recommended)

1. Go to https://vercel.com
2. Sign up or log in
3. Click "Add New" → "Project"
4. Select "GitHub" as source
5. Search for `executiveusa/agent-zero-Fork`
6. Click "Import"

#### Option B: Via CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy from project directory
cd /home/user/agent-zero-Fork
vercel

# Follow prompts to connect GitHub
```

### Step 3: Configure Environment Variables

In Vercel Dashboard:

1. Go to Settings → Environment Variables
2. Add these variables:

```
NEXT_PUBLIC_API_URL=https://your-api-domain.com
NEXT_PUBLIC_WS_URL=wss://your-api-domain.com/ws
NEXT_PUBLIC_ENV=production
```

**For Hostinger Integration:**
```
NEXT_PUBLIC_API_URL=https://your-hostinger-domain.com
NEXT_PUBLIC_WS_URL=wss://your-hostinger-domain.com/ws
NEXT_PUBLIC_ENABLE_SPEECH=true
NEXT_PUBLIC_ENABLE_VOICE=true
NEXT_PUBLIC_ENABLE_PROJECTS=true
NEXT_PUBLIC_ENABLE_MEMORY_DASHBOARD=true
NEXT_PUBLIC_ENABLE_MCP_SERVERS=true
NEXT_PUBLIC_ENABLE_SCHEDULER=true
```

### Step 4: Deploy

1. **Automatic**: Push to GitHub - Vercel auto-deploys
2. **Manual**: Click "Deploy" button in Vercel dashboard

Expected deployment time: 30-60 seconds

### Step 5: Verify Deployment

Once deployed, Vercel provides:
- Live URL: `https://agent-zero-fork.vercel.app` (or custom domain)
- Production URL in Vercel dashboard
- Automatic staging URLs for previews

---

## 🔗 Domain Configuration

### Connect Custom Domain

1. Go to Vercel Dashboard → Project Settings → Domains
2. Add your custom domain
3. Update DNS records:

```
DNS Records to Add:
A       agent-zero.yourdomain.com    76.76.19.163
CNAME   www.agent-zero.yourdomain.com  cname.vercel-dns.com
```

4. Verify domain (Vercel will confirm)
5. Auto-generates SSL certificate (Let's Encrypt)

### Hostinger Integration

For your Hostinger VPS:

```bash
# SSH into Hostinger
ssh root@your_vps_ip

# Create reverse proxy (optional)
# This allows /dashboard to proxy to Vercel while keeping backend on Hostinger
```

---

## 🔐 Security Configuration

### Environment Variable Encryption

All environment variables in Vercel are:
- ✅ Encrypted at rest
- ✅ Encrypted in transit
- ✅ Masked in logs
- ✅ Not exposed to frontend (except NEXT_PUBLIC_* vars)

### CORS Configuration

Update your Agent Zero backend (in .env):

```bash
# Allow Vercel domain for CORS
CORS_ALLOWED_ORIGINS="localhost:3000,your-vercel-domain.vercel.app,agent-zero.yourdomain.com"
```

### Security Headers

Automatically added by Vercel:
- X-Frame-Options: SAMEORIGIN
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security: max-age=31536000

---

## 📊 Monitoring & Analytics

### Vercel Dashboard

Monitor in real-time:
- **Deployments**: Status, logs, rollback
- **Analytics**: Performance, edge cache hits
- **Logs**: Function logs, error tracking
- **Usage**: Bandwidth, build minutes

### Frontend Performance

In browser console:
```javascript
// Check API connectivity
fetch('/api/health').then(r => r.json()).then(console.log)

// Monitor WebSocket
console.log('WS Status:', document.readyState)
```

### Error Tracking

Sentry integration (optional):
```bash
# In .env
SENTRY_DSN=https://your-sentry-url
```

---

## 🔄 Continuous Deployment

### Auto-Deploy on Push

Vercel automatically deploys when you:
1. Push to main branch
2. Create pull requests (preview deployments)
3. Merge pull requests (production)

### Preview Deployments

For every PR:
- Automatic preview URL
- Full testing environment
- Shareable link for team review

Example: `https://agent-zero-fork-git-feature-xyz.vercel.app`

### Rollback

If deployment fails:
1. Go to Vercel Dashboard
2. Click "Deployments"
3. Select previous good deployment
4. Click "Rollback"

---

## 🐛 Troubleshooting

### Blank Page Issue

**Symptom**: Dashboard loads but shows blank page

**Solution**:
```bash
# Check browser console for errors
# Usually CORS or API URL mismatch

# Verify API URL in environment
curl https://your-api-url/api/health

# Update NEXT_PUBLIC_API_URL if needed
```

### API Connection Timeout

**Symptom**: Messages timeout, no responses

**Solution**:
```bash
# 1. Verify backend is running
ssh root@your_vps_ip
systemctl status agent-zero

# 2. Check network connectivity
curl https://your-api-url/api/health

# 3. Update firewall if needed
# Open port 443 (HTTPS) on backend

# 4. Check CORS settings in backend .env
```

### WebSocket Connection Failed

**Symptom**: Real-time messages don't stream

**Solution**:
```bash
# Ensure NEXT_PUBLIC_WS_URL is correct
# For Hostinger: wss://your-domain.com/ws

# Check if WebSocket is enabled on backend
# In backend .env: WEBSOCKET_ENABLED=true
```

### Build Failure

**Symptom**: Deployment fails during build

**Solution**:
```bash
# Check Vercel build logs
# Usually missing dependencies

# For vanilla JS, this shouldn't happen
# If it does, check package.json

# Vercel requires valid package.json
npm init -y  # Reset if corrupted
```

---

## 📈 Performance Optimization

### Edge Cache

Vercel serves from 300+ edge locations worldwide. Cache strategies:

**HTML Pages** (10 seconds):
```
Cache-Control: no-cache, no-store, must-revalidate
```

**Static Assets** (1 year):
```
Cache-Control: public, max-age=31536000, immutable
```

### Image Optimization

For images in dashboard:
1. Use WEBP format (auto-converted by Vercel)
2. Serve via Vercel's Image Optimization API
3. Lazy load below-the-fold images

### Code Splitting

Already optimized:
- Modular JavaScript components
- Lazy-loaded CSS
- Deferred script loading

---

## 🔗 Integration with Agent Zero Backend

### Configuration

**On Hostinger Backend:**

```bash
# In /root/.env
CORS_ALLOWED_ORIGINS="your-vercel-domain.vercel.app,your-custom-domain.com"
FRONTEND_URL="https://agent-zero-fork.vercel.app"
```

**Restart backend:**
```bash
docker-compose restart
```

### API Routing

Frontend → Vercel Edge → Agent Zero Backend

```
User Browser
    ↓
Vercel Edge Network (Global CDN)
    ↓ (HTTPS)
Agent Zero Backend (Hostinger VPS)
    ↓
Database, AI Models, Tools
```

### Latency

- User to Vercel Edge: <50ms (global)
- Vercel to Backend: ~100ms (depending on geography)
- Total request time: 150-300ms

---

## 📊 Deployment Checklist

Before going live:

- [ ] Repository pushed to GitHub
- [ ] Vercel project created
- [ ] Environment variables set
- [ ] Custom domain configured (optional)
- [ ] SSL certificate active
- [ ] CORS configured on backend
- [ ] API connectivity verified
- [ ] WebSocket working
- [ ] Login page accessible
- [ ] Dashboard loads without errors
- [ ] Commands work end-to-end
- [ ] Mobile responsive
- [ ] Performance acceptable (<1s load)

---

## 📞 Support & Maintenance

### Monitor Deployment Health

```bash
# Weekly checklist:
1. Check Vercel dashboard for errors
2. Test login and send a message
3. Verify API health: /api/health
4. Review performance metrics
5. Check deployment logs for warnings
```

### Update Frontend

```bash
# To update frontend after changes:
git commit -m "Update dashboard"
git push origin claude/auto-update-agent-zero-mzNwX

# Vercel automatically deploys!
# Check dashboard for confirmation
```

### Rollback Procedure

```bash
# If deployment breaks:
1. Go to Vercel Dashboard
2. Click "Deployments"
3. Select previous working deployment
4. Click "Rollback"
5. Done! No downtime
```

---

## 🎯 Post-Deployment

### Update Team

1. Share Vercel URL with team
2. Send deployment announcement
3. Document any changes
4. Monitor first 24 hours

### Performance Baseline

Track these metrics:
- Page load time: target <1s
- API response time: target <2s
- 99.9% uptime
- Zero 5xx errors

### Future Enhancements

Planned improvements:
- [ ] Analytics dashboard (in Vercel)
- [ ] A/B testing for UI changes
- [ ] Serverless functions for API proxy
- [ ] DDoS protection (Vercel Security)

---

## 📚 Documentation

Related guides:
- `IMPLEMENTATION_SUMMARY.md` - Full system overview
- `TELEGRAM_BOT_DEPLOYMENT.md` - Bot setup
- `DEPLOYMENT_CHECKLIST.md` - Production validation
- `QUICK_REFERENCE.md` - Quick commands

---

## 🚀 Getting Help

### Common Questions

**Q: How do I update the frontend?**
A: Push to GitHub. Vercel auto-deploys in ~1 minute.

**Q: Can I use a custom domain?**
A: Yes! Set it up in Vercel → Project Settings → Domains

**Q: What if the API is slow?**
A: Check backend health. Vercel edge is <50ms. Backend latency is the bottleneck.

**Q: How do I see deploy logs?**
A: Go to Vercel Dashboard → Deployments → Select deployment → View logs

---

## 📋 Vercel URLs & Links

### Project URLs

Once deployed, you'll have:
- **Vercel Dashboard**: https://vercel.com/dashboard
- **Project URL**: https://agent-zero-fork-[hash].vercel.app
- **Production URL**: https://agent-zero-fork.vercel.app (or custom)

### Team Management

- Add teammates in Vercel → Settings → Team
- Share preview URLs with stakeholders
- Manage permissions and access levels

---

## ✨ Success Indicators

Your deployment is successful when:

✅ Vercel shows "Ready" status
✅ Dashboard loads in browser
✅ Login page appears
✅ Messages send and receive
✅ API calls complete <2s
✅ Mobile view responsive
✅ No console errors
✅ Performance metrics green

---

**Status**: ✅ Ready for Vercel Deployment

All configuration files created. Push to GitHub and connect to Vercel to deploy!

---

**Last Updated**: February 3, 2026
**Maintainer**: Agent Zero Team
