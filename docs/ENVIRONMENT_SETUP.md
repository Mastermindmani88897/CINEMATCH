# CineMatch AI — Environment Variables Setup & Audit Guide

| Variable Name | Component | Required in Prod | Default (Dev) | Production Value | Description |
|---------------|-----------|------------------|---------------|------------------|-------------|
| `ENVIRONMENT` | Backend | Yes | `development` | `production` | App execution environment |
| `BACKEND_HOST` | Backend | No | `0.0.0.0` | `0.0.0.0` | Bind IP address for FastAPI |
| `BACKEND_PORT` | Backend | No | `8000` | `$PORT` (Render) | Server listening port |
| `MONGODB_URI` | Backend | Yes | None | `mongodb+srv://...` | MongoDB Atlas cluster connection URI |
| `DATABASE_NAME` | Backend | No | `cinematch_db` | `cinematch_db` | Main database name |
| `JWT_SECRET` | Backend | Yes | None | `<32-byte-secret>` | Secret key for signing JWT tokens |
| `TMDB_API_KEY` | Backend | Yes | None | `<tmdb-api-key>` | The Movie Database (TMDB) API Key |
| `GEMINI_API_KEY` | Backend | Yes | None | `<gemini-api-key>` | Google Gemini AI API key |
| `FRONTEND_URL` | Backend | Yes | `http://localhost:5173` | `https://cinematch-web.vercel.app` | Frontend production origin for CORS |
| `CORS_ORIGINS` | Backend | Yes | `http://localhost:5173` | `https://cinematch-web.vercel.app` | Comma-separated allowed origins |
| `VITE_API_URL` | Frontend | Yes | `http://localhost:8000/api` | `https://cinematch-backend-okio.onrender.com/api` | Base API URL for frontend HTTP client |

---

## Local Development vs Production

- **Local Development**:
  - Frontend runs on `http://localhost:5173`.
  - Backend runs on `http://localhost:8000`.
- **Production Environment**:
  - Frontend hosted on Vercel (`https://cinematch-web.vercel.app`).
  - Backend hosted on Render (`https://cinematch-backend-okio.onrender.com`).
  - Database hosted on MongoDB Atlas.
