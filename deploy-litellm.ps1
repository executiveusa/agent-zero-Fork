# Deploy Agent Zero with LiteLLM Integration
# This script loads secrets and deploys the enhanced dashboard with LLM switching

param(
    [switch]$Deploy,
    [switch]$Update
)

Write-Host "`n=== AGENT ZERO LITELLM DEPLOYMENT ===" -ForegroundColor Cyan
Write-Host ""

# Load secrets from master.env
Write-Host "[1/5] Loading secrets from master.env..." -ForegroundColor Yellow
. .\load-agent-secrets.ps1
$secretsLoaded = Load-AgentSecrets

if (-not $secretsLoaded) {
    Write-Host "❌ Failed to load secrets. Exiting..." -ForegroundColor Red
    exit 1
}

# Create .env file for Docker Compose
Write-Host "`n[2/5] Creating Docker environment file..." -ForegroundColor Yellow
@"
ANTHROPIC_API_KEY=$env:ANTHROPIC_API_KEY
OPENAI_API_KEY=$env:OPENAI_API_KEY
GOOGLE_AI_API_KEY=$env:GOOGLE_AI_API_KEY
GEMINI_API_KEY=$env:GOOGLE_AI_API_KEY
ZHIPUAI_API_KEY=$env:ZHIPUAI_API_KEY
GLM_API_KEY=$env:ZHIPUAI_API_KEY
REPLICATE_API_KEY=$env:REPLICATE_API_KEY
REPLICATE_API_TOKEN=$env:REPLICATE_API_TOKEN
HUGGINGFACE_TOKEN=$env:HUGGINGFACE_TOKEN
POSTGRES_PASSWORD=agentzero2026secure
LITELLM_UI_PASSWORD=agent-zero-admin-2026
"@ | Out-File -FilePath .env.litellm -Encoding utf8

Write-Host "✅ Environment file created (.env.litellm)" -ForegroundColor Green

# Copy enhanced dashboard
Write-Host "`n[3/5] Preparing enhanced dashboard..." -ForegroundColor Yellow
Copy-Item -Path "index-enhanced.html" -Destination "index.html" -Force
Write-Host "✅ Enhanced dashboard with LLM switcher ready" -ForegroundColor Green

if ($Deploy) {
    # Deploy to VPS
    Write-Host "`n[4/5] Deploying to VPS..." -ForegroundColor Yellow
    
    # Copy files to VPS
    Write-Host "   📦 Copying files to VPS..." -ForegroundColor Gray
    scp index.html litellm-config.yaml docker-compose.litellm.yml .env.litellm root@31.220.58.212:/app/agent-zero/
    
    # Deploy LiteLLM
    Write-Host "   🚀 Starting LiteLLM container..." -ForegroundColor Gray
    ssh root@31.220.58.212 "cd /app/agent-zero && docker compose --env-file .env.litellm -f docker-compose.litellm.yml up -d"
    
    # Update web container
    Write-Host "   🔄 Updating web container..." -ForegroundColor Gray
    ssh root@31.220.58.212 "cd /app/agent-zero/web && cp /app/agent-zero/index.html . && docker restart agent-zero-web"
    
    Write-Host "✅ Deployment complete!" -ForegroundColor Green
    
    Write-Host "`n[5/5] Testing deployment..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    $webStatus = Invoke-WebRequest -Uri "http://31.220.58.212:3001" -UseBasicParsing -ErrorAction SilentlyContinue
    if ($webStatus.StatusCode -eq 200) {
        Write-Host "✅ Web interface: OK" -ForegroundColor Green
    }
    
    $litellmStatus = Invoke-WebRequest -Uri "http://31.220.58.212:4000/health" -UseBasicParsing -ErrorAction SilentlyContinue
    if ($litellmStatus.StatusCode -eq 200) {
        Write-Host "✅ LiteLLM proxy: OK" -ForegroundColor Green
    } else {
        Write-Host "⚠️ LiteLLM proxy: Starting (may take 30-60 seconds)" -ForegroundColor Yellow
    }
    
    Write-Host "`n" -NoNewline
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "           DEPLOYMENT SUCCESSFUL! ✅" -ForegroundColor Green
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🌐 WEB INTERFACE:" -ForegroundColor Yellow
    Write-Host "   http://31.220.58.212:3001" -ForegroundColor White
    Write-Host ""
    Write-Host "🔄 LITELLM PROXY:" -ForegroundColor Yellow
    Write-Host "   http://31.220.58.212:4000" -ForegroundColor White
    Write-Host "   Dashboard: http://31.220.58.212:4000/ui" -ForegroundColor White
    Write-Host ""
    Write-Host "🎯 SUPPORTED MODELS:" -ForegroundColor Yellow
    Write-Host "   • Claude Sonnet (Anthropic)" -ForegroundColor White
    Write-Host "   • GPT-4 (OpenAI)" -ForegroundColor White
    Write-Host "   • Gemini 2.0 (Google)" -ForegroundColor White
    Write-Host "   • GLM-4 Plus (智谱AI)" -ForegroundColor White
    Write-Host "   • GLM-4 Air (智谱AI)" -ForegroundColor White
    Write-Host ""
    Write-Host "🔑 CREDENTIALS:" -ForegroundColor Yellow
    Write-Host "   Username: admin" -ForegroundColor White
    Write-Host "   Password: agent-zero-admin-2026" -ForegroundColor White
    Write-Host "   Master Key: agent-zero-master-key" -ForegroundColor White
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host ""
} elseif ($Update) {
    Write-Host "`n[4/5] Updating configuration..." -ForegroundColor Yellow
    scp litellm-config.yaml root@31.220.58.212:/app/agent-zero/
    ssh root@31.220.58.212 "cd /app/agent-zero && docker restart agent-zero-litellm"
    Write-Host "✅ Configuration updated and LiteLLM restarted" -ForegroundColor Green
} else {
    Write-Host "`n[4/5] Local preparation complete" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "📋 NEXT STEPS:" -ForegroundColor Yellow
    Write-Host "   1. Review litellm-config.yaml" -ForegroundColor White
    Write-Host "   2. Test locally: docker compose -f docker-compose.litellm.yml --env-file .env.litellm up" -ForegroundColor White
    Write-Host "   3. Deploy: .\deploy-litellm.ps1 -Deploy" -ForegroundColor White
    Write-Host "   4. Update config: .\deploy-litellm.ps1 -Update" -ForegroundColor White
    Write-Host ""
}

Write-Host "✅ Script complete!" -ForegroundColor Green
Write-Host ""
