#!/bin/bash
# CineMatch AI — Automated Setup Launcher (Bash)

set -e

echo "=========================================="
echo "   CineMatch AI Automated Setup Launcher  "
echo "=========================================="

echo "[1/5] Installing backend dependencies..."
cd backend
pip install -r requirements.txt

echo "[2/5] Training ML Recommendation models..."
cd ..
python -m ml.train --skip-semantic

echo "[3/5] Installing frontend dependencies..."
cd frontend
npm install

echo "[4/5] Running frontend production build verification..."
npm run build

echo "=========================================="
echo "   [OK] CineMatch AI Setup Complete!      "
echo "=========================================="
