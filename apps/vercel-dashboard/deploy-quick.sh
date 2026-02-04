#!/bin/bash
# Quick Vercel Deploy (assumes env vars already set)

cd "$(dirname "$0")"

echo "🚀 Deploying Agent Zero Dashboard to Vercel..."

# Build check
npm run build || {
    echo "❌ Build failed"
    exit 1
}

# Deploy
vercel deploy --prod --yes

echo "✅ Deployed!"
