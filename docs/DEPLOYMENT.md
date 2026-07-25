# CineMatch AI — Deployment Guide

This guide details step-by-step instructions for deploying CineMatch AI across **Vercel** (Frontend) and **Render** (Backend), backed by **MongoDB Atlas**.

---

## 1. Backend Deployment (Render)

1. Sign in to [Render](https://render.com/).
2. Create a new **Web Service** connected to repository `https://github.com/Mastermindmani88897/CINEMATCH`.
3. Configure settings:
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add Environment Variables:
   - `ENVIRONMENT` = `production`
   - `MONGODB_URI` = `mongodb+srv://<user>:<password>@cluster.mongodb.net/cinematch_db`
   - `JWT_SECRET` = `<32-byte-secret>`
   - `TMDB_API_KEY` = `<your-tmdb-api-key>`
   - `GEMINI_API_KEY` = `<your-gemini-api-key>`
   - `FRONTEND_URL` = `https://cinematch-web.vercel.app`
   - `CORS_ORIGINS` = `https://cinematch-web.vercel.app`

---

## 2. Frontend Deployment (Vercel)

1. Sign in to [Vercel](https://vercel.com/).
2. Import project from GitHub: `Mastermindmani88897/CINEMATCH`.
3. Configure Framework & Directory:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
4. Add Environment Variables:
   - `VITE_API_URL` = `https://cinematch-backend-okio.onrender.com/api`
5. Click **Deploy**. Vercel will automatically build the production bundle and deploy to global CDN.

---

## 3. Database Configuration (MongoDB Atlas)

1. Log into [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
2. Ensure Network Access IP Access List permits connections (`0.0.0.0/0` for cloud deployment).
3. Verify cluster contains collection indexes for `movies`, `users`, `ratings`, `favorites`, `watchlist`, and `reviews`.
