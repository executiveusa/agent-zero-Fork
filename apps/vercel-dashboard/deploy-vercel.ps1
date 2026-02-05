# Vercel Deployment Script
# Run this script to deploy Agent Zero Dashboard to Vercel

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Agent Zero - Vercel Deployment" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Set Vercel token from environment
$env:VERCEL_TOKEN = "Fw4dKUxWtqwgar6gAZ6ncdl9"

Write-Host "✓ Vercel token configured" -ForegroundColor Green
Write-Host ""

# Navigate to dashboard directory
$dashboardPath = "C:\Users\Trevor\agent-zero-Fork\apps\vercel-dashboard"
Set-Location $dashboardPath

Write-Host "📁 Directory: $dashboardPath" -ForegroundColor Yellow
Write-Host ""

# Deploy to Vercel
Write-Host "🚀 Deploying to Vercel..." -ForegroundColor Cyan
Write-Host ""

# Use npx to run vercel without prompts
npx -y vercel@latest deploy --prod --token "$env:VERCEL_TOKEN" --yes

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Deployment Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Visit: https://agent-zero-fork.vercel.app" -ForegroundColor Yellow
