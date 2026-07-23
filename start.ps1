# CineMatch AI — Automated Startup & Setup Script (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   CineMatch AI Automated Setup Launcher  " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Check Python installation
Write-Host "[1/5] Checking Python environment..." -ForegroundColor Yellow
python --version

# 2. Install backend dependencies
Write-Host "[2/5] Installing backend dependencies..." -ForegroundColor Yellow
cd backend
pip install -r requirements.txt

# 3. Train ML Recommendation models
Write-Host "[3/5] Training ML Recommendation models..." -ForegroundColor Yellow
cd ..
python -m ml.train --skip-semantic

# 4. Install frontend dependencies
Write-Host "[4/5] Checking frontend dependencies..." -ForegroundColor Yellow
cd frontend
npm install

# 5. Build verification
Write-Host "[5/5] Running frontend production build verification..." -ForegroundColor Yellow
npm run build

Write-Host "==========================================" -ForegroundColor Green
Write-Host "   [OK] CineMatch AI Setup Verification Complete! " -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "To start the backend: cd backend; uvicorn app.main:app --reload --port 8000" -ForegroundColor White
Write-Host "To start the frontend: cd frontend; npm run dev" -ForegroundColor White
