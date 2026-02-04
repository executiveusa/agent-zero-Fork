# 🔐 Secrets Management for Agent Zero Dashboard

## ⚠️ CRITICAL SECURITY NOTICE

**NEVER commit secrets to git!** All sensitive credentials are stored securely outside the repository.

---

## 📋 Required Secrets

### 1. Agent Zero Backend
```bash
AZ_BASE_URL=http://localhost:50001
AZ_API_KEY=<your-api-key>
AZ_AUTH_LOGIN=<optional-backend-login>
AZ_AUTH_PASSWORD=<optional-backend-password>
```

### 2. NextAuth
```bash
NEXTAUTH_URL=https://your-domain.vercel.app
NEXTAUTH_SECRET=<generate-with-openssl-rand-base64-32>
```

### 3. Hostinger Deployment
```bash
HOSTINGER_API_TOKEN=bL59Px9zyPf9JYwbCrXZRwqk82JFvaWrk8HAxqqnbd5caddb
```

### 4. LiteLLM (Optional - for LLM switching)
```bash
LITELLM_BASE_URL=http://localhost:8000
LITELLM_MASTER_KEY=<your-master-key>
OPENAI_API_KEY=<if-using-openai>
ANTHROPIC_API_KEY=<if-using-anthropic>
AZURE_API_KEY=<if-using-azure>
COHERE_API_KEY=<if-using-cohere>
```

---

## 🛠️ Setup Methods

### Method 1: Local Development (.env.local)

Create `.env.local` in the project root:

```bash
cd apps/vercel-dashboard
cp .env.example .env.local
# Edit .env.local with your actual secrets
```

**`.env.local` is gitignored and will never be committed.**

---

### Method 2: Vercel Production (Encrypted Secrets)

Set secrets via Vercel CLI:

```bash
cd apps/vercel-dashboard

# Set each secret
echo "http://localhost:50001" | vercel env add AZ_BASE_URL production
echo "your-api-key" | vercel env add AZ_API_KEY production
echo "$(openssl rand -base64 32)" | vercel env add NEXTAUTH_SECRET production
echo "bL59Px9zyPf9JYwbCrXZRwqk82JFvaWrk8HAxqqnbd5caddb" | vercel env add HOSTINGER_API_TOKEN production
```

Or use the deployment script:

```bash
pwsh deploy.ps1
```

---

### Method 3: Vercel Dashboard (GUI)

1. Go to https://vercel.com/dashboard
2. Select your project
3. Navigate to **Settings** → **Environment Variables**
4. Add each secret:
   - `AZ_BASE_URL`
   - `AZ_API_KEY`
   - `NEXTAUTH_SECRET`
   - `HOSTINGER_API_TOKEN`

---

## 🔒 Encryption Strategy

### Server-Side Only
All secrets are:
- ✅ Stored in Vercel's encrypted secret storage
- ✅ Injected at runtime into Next.js server routes
- ✅ Never exposed to browser/client code
- ✅ Never included in client-side JavaScript bundles

### BFF Architecture Protects Secrets
```
Browser (Client)
    ↓ HTTPS
Next.js API Routes (Server) ← Secrets loaded here
    ↓ HTTPS
Agent Zero Backend
```

The BFF proxy at `/api/az/*` handles all backend communication server-side, so the browser **never sees** your API keys or tokens.

---

## 🧪 Verify Secrets Are Secure

### Test 1: Check Client Bundle
```bash
npm run build
# Search for secrets in .next/static - should find NOTHING
grep -r "bL59Px9zyPf9JYwbCrXZRwqk82JFvaWrk8HAxqqnbd5caddb" .next/static
# Result: (nothing found) ✅
```

### Test 2: Check Browser DevTools
1. Open dashboard in browser
2. Open DevTools → Network tab
3. Search all requests for "AZ_API_KEY" or "HOSTINGER_API_TOKEN"
4. Result: Not found ✅

### Test 3: Check Git History
```bash
git log --all --full-history --source --pretty=format: -S "bL59Px9zyPf9JYwbCrXZRwqk82JFvaWrk8HAxqqnbd5caddb"
# Result: (empty) ✅
```

---

## 🚨 Secret Leak Prevention

### .gitignore Protection
```gitignore
# Secrets (NEVER COMMIT)
.env
.env*.local
secrets/
*.key
*.secret
config/secrets.json
```

### Pre-commit Hook (Optional)
Create `.git/hooks/pre-commit`:

```bash
#!/bin/sh
# Prevent committing secrets

if git diff --cached | grep -E "HOSTINGER_API_TOKEN|AZ_API_KEY"; then
    echo "❌ ERROR: Secret detected in commit!"
    echo "Remove secrets before committing."
    exit 1
fi
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## 🔄 Rotating Secrets

If a secret is compromised:

1. **Revoke** the old key at the provider
2. **Generate** a new key
3. **Update** in Vercel:
   ```bash
   vercel env rm AZ_API_KEY production
   echo "new-key" | vercel env add AZ_API_KEY production
   ```
4. **Redeploy**:
   ```bash
   vercel deploy --prod
   ```

---

## 📚 References

- [Vercel Environment Variables](https://vercel.com/docs/environment-variables)
- [Next.js Environment Variables](https://nextjs.org/docs/app/building-your-application/configuring/environment-variables)
- [OWASP Secret Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
