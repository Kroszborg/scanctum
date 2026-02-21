# Scanctum — Production Deployment on Render

This guide walks you through deploying the full Scanctum stack to [Render](https://render.com) from scratch. Follow every step in order.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Prerequisites](#prerequisites)
3. [Repository Setup](#repository-setup)
4. [Deploy with Render Blueprint (Recommended)](#deploy-with-render-blueprint-recommended)
5. [Backend on Render + Frontend on Vercel (split)](#backend-on-render--frontend-on-vercel-split)
6. [Manual Service-by-Service Setup](#manual-service-by-service-setup)
   - [PostgreSQL Database](#1-create-postgresql-database)
   - [Redis](#2-create-redis)
   - [Backend API](#3-deploy-backend-api)
   - [Celery Worker](#4-deploy-celery-worker)
   - [Frontend](#5-deploy-frontend)
7. [Environment Variables Reference](#environment-variables-reference)
8. [Database Migrations](#database-migrations)
9. [First Login and Admin Setup](#first-login-and-admin-setup)
10. [Custom Domain and TLS](#custom-domain-and-tls)
11. [Monitoring and Logs](#monitoring-and-logs)
12. [Upgrading Plans](#upgrading-plans)
13. [Troubleshooting](#troubleshooting)

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

The included `render.yaml` provisions **free-tier** services only. Render does **not** support transforming env vars (e.g. `postgresql://` → `postgresql+asyncpg://`), so the backend uses an **entrypoint script** (`entrypoint-render.sh`) that rewrites the URLs before starting the app.

**Free plan note:** Background workers (Celery) are **not available** on Render's free plan. The Blueprint creates only: database, Redis, backend API, and frontend. Scans will **queue** but **will not run** until you add a Celery worker (paid plan) or run a worker elsewhere. See [Free tier: no worker](#free-tier-no-background-worker) and [Adding the Celery worker (paid plan)](#adding-the-celery-worker-paid-plan).

### Steps

1. Open the **[Render Dashboard](https://dashboard.render.com/)** and sign in.
2. Click **New → Blueprint** (not "New Web Service").
3. **Connect** the Git provider (e.g. GitHub) if needed, then select your **scanctum** repository.
4. **Blueprint path**: leave default `render.yaml` (repo root).
5. **Branch**: choose the branch to deploy (e.g. `main`).
6. Click **"Apply"** or **"Deploy Blueprint"**. Render will show a preview of resources:
   - `scanctum-db` — PostgreSQL 16 (free)
   - `scanctum-redis` — Redis (free)
   - `scanctum-backend` — Web Service (Docker)
   - `scanctum-frontend` — Web Service (Docker)
7. Confirm to create everything. First deploy may take several minutes (DB + Redis + two Docker builds).

### After first deploy

- **Database URLs**: The backend runs `entrypoint-render.sh`, which rewrites `postgresql://` to `postgresql+asyncpg://` and `postgresql+psycopg2://` before starting Uvicorn. No manual env edits needed.
- **CORS**: If you use a custom domain for the frontend, set `BACKEND_CORS_ORIGINS` on **scanctum-backend** to your frontend URL (e.g. `["https://your-app.example.com"]`) and save.
- **Frontend API URL**: If you use a custom domain for the backend, set `NEXT_PUBLIC_API_URL` on **scanctum-frontend** to `https://your-backend.example.com/api/v1` and redeploy.

---

## Backend on Render + Frontend on Vercel (split)

Yes — you can run the **backend** (API + Celery + Postgres + Redis) on Render and the **frontend** (Next.js) on Vercel. This is a common setup: Vercel is great for Next.js, Render for the API and workers.

### 1. Backend on Render

- Deploy **only** the backend stack on Render:
  - Either use the [Render Blueprint](#deploy-with-render-blueprint-recommended) but **delete** (or do not create) the `scanctum-frontend` service after the first deploy,  
  - Or use [Manual Service-by-Service Setup](#manual-service-by-service-setup) and create: PostgreSQL, Redis, Web Service (backend), Background Worker (Celery). Do **not** create the frontend web service.
- Note your backend URL, e.g. `https://scanctum-backend.onrender.com`.

### 2. Set CORS on the backend

On the **scanctum-backend** service in Render → **Environment**:

| Key | Value |
|-----|-------|
| `BACKEND_CORS_ORIGINS` | Your Vercel frontend URL, e.g. `["https://your-app.vercel.app"]` or `["https://scanctum.vercel.app"]` |

Add your production and preview URLs if you use Vercel preview deployments (e.g. `["https://scanctum.vercel.app","https://*.vercel.app"]` — check FastAPI/CORS support for wildcards). Save so the backend allows requests from the frontend origin.

### 3. Frontend on Vercel

1. Push your repo to GitHub and go to [vercel.com](https://vercel.com) → **Add New Project** → import the **scanctum** repo.
2. **Root Directory**: set to `frontend` (so Vercel builds only the Next.js app).
3. **Framework Preset**: Next.js (auto-detected).
4. **Environment variable** (required):

   | Name | Value |
   |------|--------|
   | `NEXT_PUBLIC_API_URL` | Your Render backend API base URL, e.g. `https://scanctum-backend.onrender.com/api/v1` |

5. Deploy. The frontend will call the Render backend for API and WebSockets (use the same host for both; e.g. `wss://...` if you add WebSocket later).

### Summary

| Part | Where | What to set |
|------|--------|-------------|
| Backend (API + Celery + DB + Redis) | Render | Deploy as in Blueprint or manual; set `BACKEND_CORS_ORIGINS` to your Vercel URL(s). |
| Frontend (Next.js) | Vercel | Root = `frontend`, set `NEXT_PUBLIC_API_URL` to `https://<your-render-backend>.onrender.com/api/v1`. |

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

## Free tier: no background worker

On Render's **free plan**, **Background Workers are not available** ("service type is not available for this plan"). The Blueprint in this repo therefore **omits** the Celery worker so the Blueprint can be applied on a free account.

- **What works on free:** API (backend), frontend, PostgreSQL, Redis. You can log in, create scans, and see the UI. Scans will stay in **pending** / queued state because no worker is running.
- **To run scans:** Add a Celery worker on a **paid plan** (see below), run a worker **for free** elsewhere (see next section), or run the worker **locally** when you need it.

### Running a Celery worker for free (Vercel? Other hosts?)

**Vercel is not an option.** Vercel runs short-lived serverless functions (with strict time limits), not long-running processes. A Celery worker must run continuously (or at least be able to poll Redis and execute tasks that can take minutes). That doesn’t fit Vercel’s model.

**Options that do work for free (or very cheap):**

| Option | Notes |
|--------|--------|
| **Run the worker on your own machine** | From the repo: `cd backend && celery -A app.tasks.celery_app worker --loglevel=info`. Set `REDIS_URL` and `DATABASE_URL_SYNC` in `.env` to the **same** values as your Render backend. This only works if Redis and Postgres are reachable from the internet. Render’s **internal** DB/Redis URLs are not; use **external** connection strings from the Render dashboard if available, or use a free [Upstash Redis](https://upstash.com) and point both Render backend and your local worker at it (and a Postgres that allows external connections). |
| **Railway** | Railway has a free tier (with monthly limits). Create a new service: deploy the **backend** Docker image, but set the start command to the Celery worker command. Use the same `REDIS_URL` and `DATABASE_URL_SYNC` as your Render backend (again, they must be publicly reachable — e.g. Upstash Redis + Render external Postgres if Render exposes it). |
| **Fly.io** | Free allowance for small VMs. Deploy a Docker image that runs only the Celery worker; configure env vars to use the same Redis and Postgres as Render. |
| **PythonAnywhere** | Free tier allows long-running processes. You can run a Celery worker there and point it at the same Redis (e.g. Upstash) and DB as your Render app. |

**Important:** Wherever the worker runs, it must use the **exact same** `REDIS_URL` (and same Redis DB) as the Render backend, and the same `DATABASE_URL_SYNC` (with `postgresql+psycopg2://`) so tasks and DB state stay in sync. If Render only gives you internal URLs, use an external Redis (e.g. Upstash free tier) and set that `REDIS_URL` on both Render backend and the external worker; then at least the queue is shared.

## Adding the Celery worker (paid plan)

Once you're on a plan that supports Background Workers (e.g. Starter):

1. In Render Dashboard → **New → Background Worker**.
2. Connect the same repo, **Root Directory**: `backend`.
3. **Build**: Docker; **Dockerfile path**: `Dockerfile`, **Docker context**: `.`
4. **Start Command**:  
   `sh -c 'export DATABASE_URL_SYNC=$(echo "$DATABASE_URL_SYNC" | sed "s|^postgresql://|postgresql+psycopg2://|"); celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2 --prefetch-multiplier=1'`
5. **Environment**: Add the same vars as the backend: `DATABASE_URL`, `DATABASE_URL_SYNC` (from scanctum-db), `REDIS_URL` (from scanctum-redis), `JWT_SECRET_KEY` (copy from scanctum-backend), `JWT_ALGORITHM` = `HS256`. Use **Secret Files** or **Environment** and paste the DB/Redis URLs; ensure `DATABASE_URL_SYNC` uses `postgresql+psycopg2://`.

After the worker is running, queued scans will execute.

---

## Upgrading Plans

Free plan limitations to be aware of:

| Resource | Free Plan Limit | Impact |
|---|---|---|
| Web Services | Spin down after 15 min idle | First request after inactivity takes ~30s |
| Background Workers | **Not available** | Scans queue but don't run; add worker on paid plan |
| PostgreSQL | 1 GB storage, no backups | Upgrade to Starter ($7/mo) for backups |
| Redis | 25 MB RAM | Upgrade to Starter ($10/mo) for persistence |

### Recommended Paid Upgrade Order

1. **Starter (or higher) for Background Worker** — required to run scans (Celery).
2. **Starter PostgreSQL ($7/mo)** — adds daily backups, point-in-time recovery
3. **Starter Web Service ($7/mo) for backend** — eliminates cold starts, adds persistent disk
4. **Starter Redis ($10/mo)** — adds persistence so in-progress scans survive restarts

---

## Troubleshooting

### "Service type is not available for this plan" (Celery / background worker)

Background workers are **not** available on Render's free plan. The Blueprint has been updated to **omit** the Celery worker so it applies on free tier. You will have API + frontend + DB + Redis; scans will queue but not run until you add a worker on a paid plan. See [Adding the Celery worker (paid plan)](#adding-the-celery-worker-paid-plan).

### Backend or frontend "Deploy failed"

- **Backend:** Ensure your repo has `backend/entrypoint-render.sh` and the backend Dockerfile copies it and runs `chmod +x entrypoint-render.sh`. The start command in the Blueprint is `./entrypoint-render.sh`. If you edited the service, set **Root Directory** to `backend`, **Dockerfile path** to `Dockerfile`, **Docker context** to `.`, **Start Command** to `./entrypoint-render.sh`.
- **Frontend:** Set **Root Directory** to `frontend`, **Dockerfile path** to `Dockerfile`, **Docker context** to `.`. If the Docker build runs out of memory on free tier, try deploying the frontend to **Vercel** instead (see [Backend on Render + Frontend on Vercel](#backend-on-render--frontend-on-vercel-split)).

### I don't see "Apply Blueprint" or the Blueprint doesn't deploy

Use **New → Blueprint** (from the Render Dashboard), not "Add Web Service" or the repo connect flow that only creates a single service. Then select your repo, leave the Blueprint path as `render.yaml`, and click **Deploy Blueprint** (or **Apply**).

### Build Fails: `WeasyPrint` or `libpango` Not Found

The backend Dockerfile installs `libpango-1.0-0` and related system libraries. If the build fails on this step, check that the base image is `python:3.11-slim` (Debian-based, not Alpine). Alpine requires different package names.

### `DATABASE_URL` / asyncpg connection errors

If you see `asyncpg: could not translate host name` or similar, the app is receiving a plain `postgresql://` URL. The backend uses `entrypoint-render.sh` to rewrite it to `postgresql+asyncpg://` before starting. Ensure the backend **Start Command** is `./entrypoint-render.sh` and the script is in the repo under `backend/`. If you set env vars manually, use `postgresql+asyncpg://` for `DATABASE_URL` and `postgresql+psycopg2://` for `DATABASE_URL_SYNC`.

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

On the **free tier** there is **no Celery worker** — scans will always stay pending until you add a worker (paid plan) or run Celery elsewhere. If you do have a worker: (1) Celery worker service is running in the Render dashboard, (2) backend and worker share the same `REDIS_URL`, (3) worker logs show task received — look for `[INFO/MainProcess] Received task: app.tasks.scan_tasks.run_scan`.

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
