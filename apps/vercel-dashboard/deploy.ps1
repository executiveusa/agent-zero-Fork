#!/usr/bin/env pwsh
# Vercel Deployment Script for Agent Zero Dashboard

Write-Host "🚀 Agent Zero Dashboard - Vercel Deployment" -ForegroundColor Cyan
Write-Host ""

# Check if Vercel CLI is installed
if (-not (Get-Command vercel -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Vercel CLI not found. Installing..." -ForegroundColor Yellow
    npm install -g vercel
}

# Navigate to project directory
Set-Location $PSScriptRoot

# Set environment variables in Vercel
Write-Host "📝 Setting environment variables..." -ForegroundColor Yellow

# AZ_BASE_URL
$azBaseUrl = Read-Host "Enter Agent Zero Backend URL (default: http://localhost:50001)"
if ([string]::IsNullOrEmpty($azBaseUrl)) { $azBaseUrl = "http://localhost:50001" }
Write-Output $azBaseUrl | vercel env add AZ_BASE_URL production

# AZ_API_KEY
$azApiKey = Read-Host "Enter Agent Zero API Key" -AsSecureString
$azApiKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($azApiKey))
Write-Output $azApiKeyPlain | vercel env add AZ_API_KEY production

# NEXTAUTH_SECRET
Write-Host "Generating NextAuth secret..." -ForegroundColor Yellow
$nextAuthSecret = openssl rand -base64 32
Write-Output $nextAuthSecret | vercel env add NEXTAUTH_SECRET production

# HOSTINGER_API_TOKEN
$hostingerToken = "bL59Px9zyPf9JYwbCrXZRwqk82JFvaWrk8HAxqqnbd5caddb"
Write-Output $hostingerToken | vercel env add HOSTINGER_API_TOKEN production

Write-Host "✅ Environment variables set!" -ForegroundColor Green
Write-Host ""

# Deploy to production
Write-Host "🚀 Deploying to Vercel..." -ForegroundColor Cyan
vercel deploy --prod --yes

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "Visit your dashboard at the URL shown above" -ForegroundColor Cyan
