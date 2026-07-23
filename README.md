# 🎬 CineMatch AI — Intelligent Hybrid Movie Recommendation Platform (MongoDB Atlas)

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)
![React](https://img.shields.io/badge/React-18-blue.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)
![TailwindCSS](https://img.shields.io/badge/Tailwind-4.0-38bdf8.svg)

> A production-ready, flagship portfolio AI movie recommendation platform powered by Machine Learning, Natural Language Processing, Sentence Transformers, FastAPI, React, TypeScript, and **MongoDB Atlas**.

---

## 🍃 MongoDB Atlas Architecture

CineMatch AI uses **MongoDB Atlas** as its primary database powered by Motor (`AsyncIOMotorClient`).

### Collections & Indexes
* `users`: `email` (unique index), `username` (unique index), hashed credentials, profiles.
* `movies`: `id` (unique index), `title` & `overview` (text index), `genres`, `popularity`, `vote_average`.
* `favorites`: compound index `(user_id, movie_id)`.
* `watchlists`: compound index `(user_id, movie_id)`.
* `ratings`: compound index `(user_id, movie_id)`.
* `reviews`: sorted by `created_at`.
* `search_history`: query logging for analytics and personalized recommendation vectors.
* `recommendation_history`: recommendation algorithm logs & similarity score tracking.

---

## 🍃 MongoDB Atlas Setup Guide (Free Tier)

1. **Create an account** on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register).
2. **Create a Free Cluster** (M0 Shared Tier).
3. **Database Access**: Create a Database User (e.g. username: `cinematch_user`, password: `your_password`).
4. **Network Access**: Add IP Address `0.0.0.0/0` (Allows access from anywhere, including Vercel and Render).
5. **Get Connection String**:
   - Click **Connect** → **Drivers** (Node.js/Python).
   - Copy the string format:
     ```env
     MONGODB_URI=mongodb+srv://cinematch_user:<password>@cluster0.xxx.mongodb.net/?retryWrites=true&w=majority
     DATABASE_NAME=cinematch_db
     ```

---

## ⚡ Quick Start

### 1. Backend & MongoDB Seeding

```powershell
cd backend

# Install dependencies (Motor & PyMongo)
pip install -r requirements.txt

# Train ML Recommendation Models
python -m ml.train --skip-semantic

# Seed MongoDB Atlas with initial movies & admin account
python -m app.db.seed

# Start FastAPI Backend
uvicorn app.main:app --reload --port 8000
```

> 📌 **Backend Server**: `http://localhost:8000`  
> 📌 **Swagger Docs**: `http://localhost:8000/api/docs`

### 2. React Frontend

```powershell
cd frontend
npm install
npm run dev
```

> 📌 **Frontend App**: `http://localhost:5173`

---

## 🔑 Default Admin Credentials

- **Email**: `admin@cinematch.ai`
- **Password**: `AdminPass123!`

---

## 🚀 Production Deployment

- **Frontend**: Deploy to **Vercel** (`frontend/vercel.json`).
- **Backend**: Deploy to **Render** (`render.yaml`). Set `MONGODB_URI` environment variable in the Render Dashboard.
- **Database**: **MongoDB Atlas** M0 Cluster.

---

## 📄 License
Licensed under the [MIT License](LICENSE).
