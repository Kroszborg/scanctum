# Scanctum — Production Deployment on Render

This guide walks you through deploying the full Scanctum stack to [Render](https://render.com) from scratch. Follow every step in order.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Prerequisites](#prerequisites)
3. [Repository Setup](#repository-setup)
4. [Deploy with Render Blueprint (Recommended)](#deploy-with-render-blueprint-recommended)
5. [Manual Service-by-Service Setup](#manual-service-by-service-setup)
   - [PostgreSQL Database](#1-create-postgresql-database)
   - [Redis](#2-create-redis)
   - [Backend API](#3-deploy-backend-api)
   - [Celery Worker](#4-deploy-celery-worker)
   - [Frontend](#5-deploy-frontend)
6. [Environment Variables Reference](#environment-variables-reference)
7. [Database Migrations](#database-migrations)
8. [First Login and Admin Setup](#first-login-and-admin-setup)
9. [Custom Domain and TLS](#custom-domain-and-tls)
10. [Monitoring and Logs](#monitoring-and-logs)
11. [Upgrading Plans](#upgrading-plans)
12. [Troubleshooting](#troubleshooting)

---

## Architecture

```
Browser
  │ HTTPS
  ▼
Render Web Service: scanctum-frontend (Next.js)
  │ HTTPS REST + WebSocket
  ▼
Render Web Service: scanctum-backend (FastAPI + Uvicorn)
  │                    │
  │ SQL (asyncpg)     │ Redis pub/sub + Celery broker
  ▼                    ▼
Render PostgreSQL    Render Redis
  ▲                    ▲
  │ SQL (psycopg2)     │ Celery
  └────────────────────┘
Render Worker: scanctum-celery (Celery worker)
```

All four services run in the **same Render region** so they communicate over Render's internal network without egress charges.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Render account | — | [render.com](https://render.com) — free tier works |
| GitHub account | — | Repo must be on GitHub (or GitLab) |
| Git | ≥ 2.30 | Push the repo before deploying |
| Python (local) | 3.11+ | Optional — only needed to run tests locally |
| Node.js (local) | 22+ | Optional — only needed for local frontend dev |

---

## Repository Setup

Render pulls directly from your Git repository. Before deploying, make sure the repo is pushed to GitHub:

```bash
git remote add origin https://github.com/YOUR_USERNAME/scanctum.git
git push -u origin main
```

> **Important:** Do **not** commit your `.env` file. It is already in `.gitignore`. Render manages secrets through environment variables (see below).

---

## Deploy with Render Blueprint (Recommended)

The included `render.yaml` Blueprint provisions all services, databases, and environment variables in one click.

### Steps

1. Go to **[dashboard.render.com/select-repo](https://dashboard.render.com/select-repo)**
2. Connect your GitHub account if you haven't already
3. Select your **scanctum** repository
4. Click **"Apply Blueprint"**
5. Render will preview all resources it will create:
   - `scanctum-db` — PostgreSQL 16 (free)
   - `scanctum-redis` — Redis (free)
   - `scanctum-backend` — Web Service (free)
   - `scanctum-celery` — Background Worker (free)
   - `scanctum-frontend` — Web Service (free)
6. Click **"Apply"** to start the build

### Post-Blueprint Required Edits

After the Blueprint deploys, you **must** update two environment variables manually because Render's Blueprint `transform` field is informational (the actual connection strings use `postgresql://` by default):

**On `scanctum-backend` service → Environment:**

| Key | Value |
|---|---|
| `DATABASE_URL` | Replace `postgresql://` with `postgresql+asyncpg://` in the auto-filled value |
| `DATABASE_URL_SYNC` | Replace `postgresql://` with `postgresql+psycopg2://` in the auto-filled value |
| `BACKEND_CORS_ORIGINS` | Set to `["https://scanctum-frontend.onrender.com"]` (or your custom domain) |

**On `scanctum-celery` worker → Environment:**

| Key | Value |
|---|---|
| `DATABASE_URL_SYNC` | Replace `postgresql://` with `postgresql+psycopg2://` |

Then click **"Save Changes"** on each service and Render will redeploy automatically.

---

## Manual Service-by-Service Setup

Use this if you prefer not to use the Blueprint, or if you need fine-grained control.

### 1. Create PostgreSQL Database

1. Dashboard → **New → PostgreSQL**
2. **Name:** `scanctum-db`
3. **Database:** `scanctum`
4. **User:** `scanctum`
5. **PostgreSQL Version:** `16`
6. **Region:** `Oregon` (or your preferred region — keep it consistent)
7. **Plan:** Free (25 GB, shared)
8. Click **"Create Database"**

After creation, copy the **Internal Database URL** from the database info page. It looks like:
```
postgresql://scanctum:GENERATED_PASSWORD@dpg-XXXX-a.oregon-postgres.render.com/scanctum
```

You will need two modified versions of this URL:
```bash
# Async (for FastAPI / asyncpg)
DATABASE_URL=postgresql+asyncpg://scanctum:PASSWORD@HOST/scanctum

# Sync (for Celery / psycopg2 / Alembic)
DATABASE_URL_SYNC=postgresql+psycopg2://scanctum:PASSWORD@HOST/scanctum
```

---

### 2. Create Redis

1. Dashboard → **New → Redis**
2. **Name:** `scanctum-redis`
3. **Region:** Same as your other services
4. **Max Memory Policy:** `allkeys-lru`
5. **Plan:** Free (25 MB)
6. **IP Allow List:** Leave empty (internal Render access only)
7. Click **"Create Redis"**

After creation, copy the **Internal Redis URL** (starts with `redis://`). If you upgrade to a paid plan with TLS, the URL starts with `rediss://`.

---

### 3. Deploy Backend API

1. Dashboard → **New → Web Service**
2. Connect your repository
3. **Name:** `scanctum-backend`
4. **Region:** Same as database
5. **Branch:** `main`
6. **Runtime:** `Docker`
7. **Dockerfile Path:** `./backend/Dockerfile`
8. **Docker Build Context:** `./backend`
9. **Start Command:**
   ```
   sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2"
   ```
10. **Health Check Path:** `/health`
11. **Plan:** Free (or Starter for persistent instances)

**Environment Variables** (add all of these):

```
DATABASE_URL              = postgresql+asyncpg://... (internal URL from step 1)
DATABASE_URL_SYNC         = postgresql+psycopg2://... (internal URL from step 1)
REDIS_URL                 = redis://... (internal URL from step 2)
JWT_SECRET_KEY            = (generate: python -c "import secrets; print(secrets.token_hex(32))")
JWT_ALGORITHM             = HS256
JWT_EXPIRE_MINUTES        = 480
BACKEND_CORS_ORIGINS      = ["https://scanctum-frontend.onrender.com"]
API_V1_PREFIX             = /api/v1
SCANNER_MAX_DEPTH_QUICK   = 2
SCANNER_MAX_PAGES_QUICK   = 20
SCANNER_MAX_DEPTH_FULL    = 5
SCANNER_MAX_PAGES_FULL    = 100
SCANNER_REQUEST_DELAY     = 2.0
SCANNER_CONCURRENCY       = 3
```

12. Click **"Create Web Service"**

> The start command runs `alembic upgrade head` on every deploy, which applies any new migrations automatically before traffic is served.

---

### 4. Deploy Celery Worker

1. Dashboard → **New → Background Worker**
2. Connect the same repository
3. **Name:** `scanctum-celery`
4. **Region:** Same region
5. **Runtime:** `Docker`
6. **Dockerfile Path:** `./backend/Dockerfile`
7. **Docker Build Context:** `./backend`
8. **Start Command:**
   ```
   celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2 --prefetch-multiplier=1
   ```
9. **Plan:** Free

**Environment Variables:**

```
DATABASE_URL              = postgresql+asyncpg://... (same as backend)
DATABASE_URL_SYNC         = postgresql+psycopg2://... (same as backend)
REDIS_URL                 = redis://... (same as backend)
JWT_SECRET_KEY            = (same value as backend — must match)
JWT_ALGORITHM             = HS256
```

10. Click **"Create Background Worker"**

---

### 5. Deploy Frontend

1. Dashboard → **New → Web Service**
2. Connect your repository
3. **Name:** `scanctum-frontend`
4. **Region:** Same region
5. **Runtime:** `Docker`
6. **Dockerfile Path:** `./frontend/Dockerfile`
7. **Docker Build Context:** `./frontend`
8. **Plan:** Free

**Environment Variables:**

```
NEXT_PUBLIC_API_URL = https://scanctum-backend.onrender.com/api/v1
```

> Replace `scanctum-backend.onrender.com` with your actual backend URL from step 3. This variable is baked into the Next.js build — changing it requires a redeploy.

9. Click **"Create Web Service"**

---

## Environment Variables Reference

Complete reference for all environment variables used across services.

| Variable | Used By | Required | Description |
|---|---|---|---|
| `DATABASE_URL` | backend, celery | ✅ | Async PostgreSQL URL (`postgresql+asyncpg://`) |
| `DATABASE_URL_SYNC` | celery, alembic | ✅ | Sync PostgreSQL URL (`postgresql+psycopg2://`) |
| `REDIS_URL` | backend, celery | ✅ | Redis URL. Use `rediss://` for TLS. |
| `JWT_SECRET_KEY` | backend, celery | ✅ | 64+ char random secret. Must be identical on both. |
| `JWT_ALGORITHM` | backend, celery | ✅ | `HS256` |
| `JWT_EXPIRE_MINUTES` | backend | — | Default `480` (8 hours) |
| `BACKEND_CORS_ORIGINS` | backend | ✅ | JSON array of allowed frontend origins |
| `API_V1_PREFIX` | backend | — | Default `/api/v1` |
| `NEXT_PUBLIC_API_URL` | frontend | ✅ | Full public URL of backend API (baked at build time) |
| `SCANNER_MAX_DEPTH_QUICK` | celery | — | Default `2` |
| `SCANNER_MAX_PAGES_QUICK` | celery | — | Default `20` |
| `SCANNER_MAX_DEPTH_FULL` | celery | — | Default `5` |
| `SCANNER_MAX_PAGES_FULL` | celery | — | Default `100` |
| `SCANNER_REQUEST_DELAY` | celery | — | Min seconds between requests per domain. **Must be ≥ 2.0** |
| `SCANNER_CONCURRENCY` | celery | — | Parallel HTTP requests during crawl. Default `5`, use `3` on free plan. |

### Generating a Secure JWT Secret

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output (64 hex characters) and set it as `JWT_SECRET_KEY` on **both** the backend and celery services. They must be identical or JWT validation will fail.

---

## Database Migrations

Migrations run automatically via `alembic upgrade head` in the backend start command.

### Running Migrations Manually

If you need to run migrations manually (e.g., after a failed deploy):

1. Go to the **scanctum-backend** service in Render dashboard
2. Click **"Shell"** tab (available on paid plans)
3. Run:
   ```bash
   alembic upgrade head
   ```

**Alternative — use a one-off job via Render:** Create a temporary web service with the same Docker image and start command `alembic upgrade head`, let it run and exit, then delete it.

### Creating a New Migration (Local)

When you add or change SQLAlchemy models, generate a migration locally:

```bash
cd backend

# Activate virtual environment
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Point to your database (use your Render external DB URL)
export DATABASE_URL_SYNC="postgresql+psycopg2://..."

# Auto-generate migration
alembic revision --autogenerate -m "describe_your_change"

# Review the generated file in alembic/versions/
# Then commit and push — it will be applied on next deploy
```

---

## First Login and Admin Setup

The first user to register via the `/signup` endpoint (or the UI signup page) automatically becomes an **admin**. All subsequent users become **analysts**.

### Steps

1. Navigate to `https://scanctum-frontend.onrender.com`
2. Click **"Sign Up"**
3. Enter your email, name, and password
4. You are now the admin — subsequent users you create via `/auth/register` can have any role

### Creating Additional Users (Admin Only)

```bash
curl -X POST https://scanctum-backend.onrender.com/api/v1/auth/register \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email":"analyst@yourorg.com","password":"SecurePass123!","full_name":"Jane Analyst","role":"analyst"}'
```

---

## Custom Domain and TLS

Render provides free TLS on all `.onrender.com` subdomains. To use your own domain:

### Backend Custom Domain

1. **scanctum-backend** → **Settings** → **Custom Domains**
2. Add your domain (e.g., `api.scanctum.yourcompany.com`)
3. Add the CNAME record shown to your DNS provider
4. Wait for DNS propagation (up to 48 hours)
5. Update `BACKEND_CORS_ORIGINS` on the backend to include your frontend domain
6. Update `NEXT_PUBLIC_API_URL` on the frontend to your new backend URL
7. Trigger a manual redeploy of the frontend

### Frontend Custom Domain

1. **scanctum-frontend** → **Settings** → **Custom Domains**
2. Add your domain (e.g., `scanctum.yourcompany.com`)
3. Add the CNAME record to DNS

### TLS Certificate

Render auto-provisions Let's Encrypt certificates for all custom domains. No action required.

---

## Monitoring and Logs

### Render Built-in Logs

- Each service has a **Logs** tab in the dashboard showing real-time stdout/stderr
- Logs are retained for 7 days on free plans, 30 days on paid plans

### Celery Task Monitoring (Flower)

Flower is not deployed by default on Render (it requires an open port and increases costs). To enable it temporarily:

1. SSH into the celery worker or create a separate web service:
   ```
   Start Command: celery -A app.tasks.celery_app flower --port=$PORT
   ```
2. Add the same env vars as the celery worker service

### Key Log Locations

| Service | What to Look For |
|---|---|
| `scanctum-backend` | FastAPI startup, request logs, unhandled exceptions |
| `scanctum-celery` | Scan task start/completion, module errors, Redis pub/sub failures |
| `scanctum-frontend` | Next.js build output, runtime errors |
| `scanctum-db` | Query errors (accessible via Render PostgreSQL dashboard) |

### Health Check

The backend exposes a health endpoint:

```bash
curl https://scanctum-backend.onrender.com/health
# → {"status": "ok"}
```

Render pings this endpoint every 30 seconds. If it fails 3 times consecutively, Render marks the service as unhealthy and restarts it.

---

## Upgrading Plans

Free plan limitations to be aware of:

| Resource | Free Plan Limit | Impact |
|---|---|---|
| Web Services | Spin down after 15 min idle | First request after inactivity takes ~30s |
| Background Workers | 750 hrs/month | Celery worker stays up continuously |
| PostgreSQL | 1 GB storage, no backups | Upgrade to Starter ($7/mo) for backups |
| Redis | 25 MB RAM | Upgrade to Starter ($10/mo) for persistence |

### Recommended Paid Upgrade Order

1. **Starter PostgreSQL ($7/mo)** — adds daily backups, point-in-time recovery
2. **Starter Web Service ($7/mo) for backend** — eliminates cold starts, adds persistent disk
3. **Starter Redis ($10/mo)** — adds persistence so in-progress scans survive restarts
4. **Standard PostgreSQL ($20/mo)** — for multiple users with concurrent scans

---

## Troubleshooting

### Build Fails: `WeasyPrint` or `libpango` Not Found

The backend Dockerfile installs `libpango-1.0-0` and related system libraries. If the build fails on this step, check that the base image is `python:3.11-slim` (Debian-based, not Alpine). Alpine requires different package names.

### `DATABASE_URL asyncpg` Connection Errors

Render's managed PostgreSQL uses `postgresql://` URLs. You must manually replace with `postgresql+asyncpg://` for the async driver. This is the most common setup mistake.

```
Error: asyncpg: could not translate host name "..."
```

Verify `DATABASE_URL` starts with `postgresql+asyncpg://`.

### Celery Tasks Never Execute

1. Verify `REDIS_URL` is identical on both backend and celery worker
2. Check that the celery worker service is **running** (not spun down — workers don't spin down on free plans)
3. Check celery worker logs for connection errors
4. Verify the worker can reach the database: check `DATABASE_URL_SYNC` uses `psycopg2`

### WebSocket Connections Fail

Render's free tier web services support WebSockets. However:
- The backend service must **not** be spun down (free services sleep after 15 min idle)
- Upgrade to Starter plan to prevent spin-down and ensure stable WS connections
- Check CORS — `BACKEND_CORS_ORIGINS` must include the frontend URL exactly

### Alembic Migration Fails on Deploy

The start command `alembic upgrade head` runs before Uvicorn starts. If the migration fails, the service will not start.

Common causes:
1. **`DATABASE_URL_SYNC` is wrong** — check it uses `psycopg2` driver not `asyncpg`
2. **Database not yet ready** — on first deploy, the database may still be initializing. Trigger a manual redeploy from the dashboard after the database shows "Available"
3. **Migration conflict** — check the alembic versions directory for conflicting heads: `alembic heads`

To debug: temporarily change the start command to `sleep 3600` to SSH in and run migrations manually.

### Frontend Shows "Network Error" / Can't Reach API

1. Verify `NEXT_PUBLIC_API_URL` is set to your backend's public URL
2. This variable is **baked into the Next.js build** — changing it requires a full redeploy of the frontend
3. Check browser network tab for the actual request URL being made
4. Verify CORS is configured: `BACKEND_CORS_ORIGINS` on the backend must include the frontend URL

### Scan Stuck on "Pending"

The Celery worker did not pick up the task. Check:
1. Celery worker service is running (check Render dashboard status)
2. Both backend and worker share the same `REDIS_URL`
3. Worker logs show task received — look for `[INFO/MainProcess] Received task: app.tasks.scan_tasks.run_scan`

---

## Local Development

See the main `README.md` for local development with Docker Compose:

```bash
cp .env.example .env
# Fill in .env values (or leave defaults for local postgres/redis)
docker compose up --build
```

Services available locally:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Flower (Celery monitor): http://localhost:5555

---

## Security Checklist Before Going Live

- [ ] `JWT_SECRET_KEY` is a random 64+ character string (not the default)
- [ ] `BACKEND_CORS_ORIGINS` lists only your specific frontend domain
- [ ] `.env` is in `.gitignore` and was never committed
- [ ] First admin account uses a strong password
- [ ] PostgreSQL and Redis are only accessible via internal Render network (not publicly exposed)
- [ ] `SCANNER_REQUEST_DELAY` is ≥ 2.0 seconds (prevents accidental DoS)
- [ ] Render free services upgraded to paid for production (prevents cold starts / data loss)
