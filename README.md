# Scanctum

Modular web application security scanner — FastAPI backend, Next.js frontend, Celery workers, PostgreSQL, Redis.

---

## Quick start (Docker)

1. **Copy env and set secrets**
   ```bash
   cp .env.example .env
   ```
   Edit `.env`: set `JWT_SECRET_KEY` to a long random string, and adjust `DATABASE_URL` / `DATABASE_URL_SYNC` if not using the default Postgres container.

2. **Run everything**
   ```bash
   docker compose up --build
   ```
   - **Frontend:** http://localhost:3000  
   - **Backend API:** http://localhost:8000  
   - **API docs:** http://localhost:8000/docs  
   - **Flower (Celery):** http://localhost:5555  

3. **Run migrations** (first time or after model changes)
   ```bash
   docker compose exec backend alembic upgrade head
   ```

---

## Running without Docker

### Prerequisites

- Python 3.11+, Node 22+, PostgreSQL 16, Redis 7

### Local Postgres (when not using Docker)

If `.env` is set to local Postgres (`localhost:5432`), create the DB and user (in `psql` or pgAdmin):

```sql
CREATE USER scanctum WITH PASSWORD 'scanctum_secret';
CREATE DATABASE scanctum OWNER scanctum;
```

Or with default postgres user: `createdb -U postgres scanctum` then create user and grant access. Redis: use `redis://localhost:6379/0` in `.env` or keep your Upstash URL.

### Backend

1. Create a venv and install:
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   pip install -e ".[dev]"
   ```

2. In project root, ensure `.env` has:
   - `DATABASE_URL` and `DATABASE_URL_SYNC` pointing at your Postgres (e.g. `localhost` instead of `postgres` if not using Docker).
   - `REDIS_URL` pointing at your Redis (e.g. `redis://localhost:6379/0`).

3. Migrations:
   ```bash
   alembic upgrade head
   ```

4. Start API and Celery (two terminals):
   ```bash
   uvicorn app.main:app --reload --port 8000
   celery -A app.tasks.celery_app worker --loglevel=info
   ```
   On **Windows**, the app uses the `solo` pool by default (prefork causes PermissionError). Optional: Flower — `celery -A app.tasks.celery_app flower --port=5555`

### Frontend

1. Install and run:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Ensure `.env` in project root has `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`.

---

## Using Neon as the database

Neon works with this stack. Use **two** URLs:

- **Async (FastAPI):** `postgresql+asyncpg://USER:PASSWORD@HOST/DB?sslmode=require`
- **Sync (Alembic, Celery):** `postgresql+psycopg2://USER:PASSWORD@HOST/DB?sslmode=require`

Set in `.env`:

- `DATABASE_URL` = Neon URL with `+asyncpg`
- `DATABASE_URL_SYNC` = same Neon URL with `+psycopg2`

If you use Neon, you can omit the `postgres` service in Docker (or run backend/frontend locally and point to Neon + a Redis instance).

---

## Stack Auth

This app uses **built-in auth**: JWT (python-jose), bcrypt, and a `users` table in PostgreSQL. There is no Stack Auth integration out of the box.

- **Neon + current auth:** Yes. Use Neon as above; auth stays as-is.
- **Stack Auth instead of built-in auth:** Not supported by default. You’d need to:
  - Use Stack Auth in the frontend for login/signup/session.
  - Change the backend to validate Stack Auth’s tokens/sessions instead of issuing its own JWTs and using the local `users` table. That would require code changes in both frontend and backend.

---

## Is the project complete?

Yes. You can run and use it:

- **Backend:** Scans, auth (login/register/me), reports, dashboard, comparisons, Celery tasks, Alembic migrations.
- **Frontend:** Next.js app calling the API.
- **Docker:** Compose for Postgres, Redis, backend, Celery worker, Flower, frontend.

For production, set strong `JWT_SECRET_KEY`, use real Postgres/Redis (or Neon + Redis), and configure CORS and `NEXT_PUBLIC_API_URL` for your domain.
