# Deployment Guide for Scanctum

This guide details how to deploy Scanctum (Frontend + Backend + Workers) to a production environment.

## Prerequisites

- **Docker** and **Docker Compose** installed on the server.
- A domain name pointing to your server's IP address (for HTTPS).

## Architecture

The production setup uses Docker Compose to orchestrate:
1.  **Frontend**: Next.js (Node.js) serving the UI.
2.  **Backend**: FastAPI (Python) API server.
3.  **Database**: PostgreSQL.
4.  **Queue**: Redis + Celery Worker (for scanning jobs).
5.  **Reverse Proxy**: Caddy (handles HTTPS automatically).

## Step 1: Configuration

1.  Copy `.env.example` to `.env` on your server:
    ```bash
    cp .env.example .env
    ```
2.  Update critical values in `.env`:
    - `SECRET_KEY`: Generate a strong random string (e.g., `openssl rand -hex 32`).
    - `POSTGRES_PASSWORD`: Set a strong database password.
    - `DOMAIN_NAME`: Set your domain (e.g., `scanctum.example.com`).

## Step 2: Production Docker Compose

Create a file named `docker-compose.prod.yml` with the following content (or use the provided file):

(See `docker-compose.prod.yml` file in repository)

## Step 3: Deployment

Run the following command to build and start the application in production mode:

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

This will:
- Build optimized Docker images for Frontend and Backend.
- Start all services (Postgres, Redis, API, Worker, Frontend, Caddy).
- Automatically provision SSL certificates for your domain via Caddy.

## Step 4: Verification

1.  Visit `https://your-domain.com`.
2.  Sign up for an account.
3.  Run a test scan.

## Troubleshooting

- **Logs**: View logs with `docker-compose -f docker-compose.prod.yml logs -f`.
- **Database Migrations**: If tables are missing, run:
    ```bash
    docker-compose -f docker-compose.prod.yml exec backend python create_tables.py
    ```
- **Worker Status**: Check Celery worker logs if scans are stuck.

## Security Notes

- Ensure port `80` and `443` are open on your firewall.
- Do NOT expose ports `5432` (Postgres) or `6379` (Redis) to the public internet. The `docker-compose.prod.yml` handles internal networking securely.
