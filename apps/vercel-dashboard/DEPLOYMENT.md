# Deployment Scripts

## Set Vercel Environment Variables

Run these commands to set encrypted secrets in Vercel:

```bash
cd apps/vercel-dashboard

# Set Agent Zero Backend URL
vercel env add AZ_BASE_URL production
# Enter: http://localhost:50001 (or your backend URL)

# Set Agent Zero API Key
vercel env add AZ_API_KEY production
# Enter: your-api-key

# Set NextAuth Secret
vercel env add NEXTAUTH_SECRET production
# Enter: $(openssl rand -base64 32)

# Set Hostinger Token
vercel env add HOSTINGER_API_TOKEN production
# Enter: bL59Px9zyPf9JYwbCrXZRwqk82JFvaWrk8HAxqqnbd5caddb
```

## Deploy to Vercel

```bash
vercel deploy --prod
```

## Deploy to Hostinger

```bash
# Build production bundle
npm run build

# Upload to Hostinger via FTP/SSH
# Or use Hostinger API with the token
```

## Environment Variable Security

**NEVER commit .env.local to git!**

All secrets are:
- Stored in .env.local (local dev only)
- Set as Vercel secrets (@ references in vercel.json)
- Injected at runtime server-side only
- Never exposed to browser/client code
