# ============================================
# SMART TRAVEL SYSTEM - Google Cloud Deploy Script (Windows)
# ============================================

# Configuration
$PROJECT_ID = "smart-travel-sys-2025"
$REGION = "asia-southeast1"             # Singapore (gần Việt Nam)

# Service names
$BACKEND_SERVICE = "smart-travel-api"
$FRONTEND_SERVICE = "smart-travel-web"

Write-Host "🚀 Deploying Smart Travel System to Google Cloud Run" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
Write-Host "`n📦 Enabling required APIs..." -ForegroundColor Yellow
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# ============================================
# DEPLOY BACKEND
# ============================================
Write-Host "`n🔧 Building and deploying Backend..." -ForegroundColor Yellow
Set-Location backend

# Generate secret key
$SECRET_KEY = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})

gcloud run deploy $BACKEND_SERVICE `
  --source . `
  --region $REGION `
  --platform managed `
  --allow-unauthenticated `
  --memory 512Mi `
  --cpu 1 `
  --min-instances 0 `
  --max-instances 10 `
  --set-env-vars "SECRET_KEY=$SECRET_KEY"

# Get backend URL
$BACKEND_URL = gcloud run services describe $BACKEND_SERVICE --region $REGION --format 'value(status.url)'
Write-Host "✅ Backend deployed at: $BACKEND_URL" -ForegroundColor Green

# ============================================
# DEPLOY FRONTEND
# ============================================
Write-Host "`n🎨 Building and deploying Frontend..." -ForegroundColor Yellow
Set-Location ..

gcloud run deploy $FRONTEND_SERVICE `
  --source . `
  --region $REGION `
  --platform managed `
  --allow-unauthenticated `
  --memory 256Mi `
  --cpu 1 `
  --min-instances 0 `
  --max-instances 10 `
  --build-arg "VITE_API_BASE_URL=$BACKEND_URL/api"

# Get frontend URL
$FRONTEND_URL = gcloud run services describe $FRONTEND_SERVICE --region $REGION --format 'value(status.url)')

Write-Host "`n==============================================" -ForegroundColor Green
Write-Host "✅ DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host "🌐 Frontend: $FRONTEND_URL" -ForegroundColor Cyan
Write-Host "🔧 Backend API: $BACKEND_URL" -ForegroundColor Cyan
Write-Host "📚 API Docs: $BACKEND_URL/docs" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Green
