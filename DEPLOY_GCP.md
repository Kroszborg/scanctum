# Scanctum — Google Cloud VPS Deployment Guide

Deploying Scanctum on a Google Cloud VM (single server, Docker Compose) with the domain `scanctum.kroszborg.co`.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [VM Selection](#2-vm-selection)
3. [Create the VM](#3-create-the-vm)
4. [Firewall Rules](#4-firewall-rules)
5. [DNS Setup](#5-dns-setup)
6. [Server Setup](#6-server-setup)
7. [Deploy the App](#7-deploy-the-app)
8. [Post-Deploy Checks](#8-post-deploy-checks)
9. [Performance Tuning](#9-performance-tuning)
10. [Automated Backups](#10-automated-backups)
11. [Monitoring & Logs](#11-monitoring--logs)
12. [Upgrading & Redeploying](#12-upgrading--redeploying)
13. [Feature Roadmap](#13-feature-roadmap)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Architecture Overview

```
Internet (HTTPS/443, HTTP/80)
        │
        ▼
  GCP External IP
        │
        ▼
  ┌─────────────┐
  │   Caddy     │  Auto TLS (Let's Encrypt), gzip, security headers
  └──────┬──────┘
         │
    ┌────┴──────────────────┐
    │                       │
    ▼                       ▼
┌─────────┐          ┌───────────┐
│ Next.js │          │  FastAPI  │  /api/v1/* (REST + WebSocket)
│ :3000   │          │  :8000    │
└─────────┘          └─────┬─────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌─────────┐  ┌────────┐  ┌────────┐
         │Postgres │  │ Redis  │  │Celery  │
         │  :5432  │  │ :6379  │  │Worker  │
         └─────────┘  └────────┘  └────────┘
              (all on internal Docker bridge — not exposed to internet)
```

All services run as Docker containers on the same VM and communicate on an internal Docker bridge network. Only ports 80 and 443 are exposed publicly.

---

## 2. VM Selection

### Recommended for side projects: e2-medium

| Property | Value |
|---|---|
| Machine type | `e2-medium` |
| vCPUs | 1 (shared-core, burstable) |
| RAM | 4 GB |
| Boot disk | 30 GB SSD (pd-ssd) |
| OS | Ubuntu 24.04 LTS |
| Estimated cost | ~$13–15/month |

The `docker-compose.prod.yml` in this repo is already tuned for e2-medium: 2 Uvicorn workers, 2 Celery workers, per-container memory caps, and a 2 GB swap file (required — see section 9.5). Handles light-to-moderate scan load fine.

### When to upgrade: e2-standard-2

| Property | Value |
|---|---|
| Machine type | `e2-standard-2` |
| vCPUs | 2 dedicated |
| RAM | 8 GB |
| Estimated cost | ~$49/month |

Upgrade when you start running many concurrent scans or have multiple users. Bump workers to `--workers 4` and `--concurrency=4` in `docker-compose.prod.yml`.

### OS: Ubuntu 24.04 LTS (recommended)

- Long-term support until 2029
- Excellent Docker support
- Well-documented for server use
- Select "Ubuntu 24.04 LTS Minimal" to save disk space

---

## 3. Create the VM

### Via Google Cloud Console

1. Go to **Compute Engine → VM Instances → Create Instance**
2. Fill in:
   - **Name:** `scanctum-prod`
   - **Region/Zone:** Pick closest to your users
     - US users → `us-central1-a`
     - EU users → `europe-west1-b`
     - India/Asia → `asia-south1-a`
   - **Machine type:** `e2-standard-2`
   - **Boot disk:**
     - Click **Change**
     - OS: **Ubuntu 24.04 LTS**
     - Image type: **Ubuntu 24.04 LTS Minimal** (x86/64)
     - Boot disk type: **SSD persistent disk**
     - Size: **30 GB** (enough for the app + Docker images + DB data)
   - **Firewall:** Check both **Allow HTTP traffic** and **Allow HTTPS traffic**
3. Under **Networking → Network tags:** Add tag `scanctum`
4. Click **Create**

### Via gcloud CLI

```bash
gcloud compute instances create scanctum-prod \
  --machine-type=e2-medium \
  --zone=us-central1-a \
  --image-family=ubuntu-2404-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB \
  --boot-disk-type=pd-ssd \
  --tags=http-server,https-server,scanctum \
  --metadata=enable-oslogin=TRUE
```

After creation, note the **External IP address** from the VM list.

---

## 4. Firewall Rules

GCP firewall rules must explicitly allow inbound traffic. When you check "Allow HTTP/HTTPS" during VM creation, GCP adds default `http-server` and `https-server` tags with rules for ports 80 and 443. If those weren't checked, add them now:

```bash
# Allow HTTP
gcloud compute firewall-rules create allow-http \
  --allow tcp:80 \
  --target-tags http-server \
  --description "Allow HTTP for Caddy redirect"

# Allow HTTPS
gcloud compute firewall-rules create allow-https \
  --allow tcp:443,udp:443 \
  --target-tags https-server \
  --description "Allow HTTPS + HTTP/3"
```

**Do NOT open** ports 5432 (Postgres), 6379 (Redis), 5555 (Flower), 3000 (Next.js), or 8000 (FastAPI) publicly. They are only accessible within the Docker network.

---

## 5. DNS Setup

Before Caddy can issue a TLS certificate, `scanctum.kroszborg.co` must point to the VM's external IP.

1. Get the external IP from the GCP Console (VM Instances page).
2. In your DNS provider (Cloudflare, Namecheap, etc.) for `kroszborg.co`:
   - Add an **A record**: `scanctum` → `<YOUR_VM_EXTERNAL_IP>`
   - TTL: 300 (5 minutes) for initial setup
3. Verify propagation:
   ```bash
   dig scanctum.kroszborg.co +short
   # Should return your VM's external IP
   ```

> If you use **Cloudflare**, set the proxy status to **DNS only (grey cloud)** initially so Caddy can get a TLS cert from Let's Encrypt directly. After deploy, you can optionally enable the Cloudflare proxy.

---

## 6. Server Setup

SSH into the VM:
```bash
gcloud compute ssh scanctum-prod --zone=us-central1-a
```

### 6.1 System Updates

```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y git curl ca-certificates gnupg lsb-release ufw
```

### 6.2 Install Docker

```bash
# Add Docker's GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker apt repo
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine + Compose plugin
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Run Docker without sudo
sudo usermod -aG docker $USER

# Apply group change (re-login or run:)
newgrp docker

# Verify
docker --version
docker compose version
```

### 6.3 Clone the Repository

```bash
cd /opt
sudo git clone https://github.com/YOUR_USERNAME/scanctum.git
sudo chown -R $USER:$USER /opt/scanctum
cd /opt/scanctum
```

### 6.4 Configure Environment Variables

```bash
cp .env.example .env
nano .env
```

Update these values in `.env`:

```bash
# ── Database (internal Docker service name "postgres") ─────────────────────────
DATABASE_URL=postgresql+asyncpg://scanctum:YOUR_DB_PASSWORD@postgres:5432/scanctum
DATABASE_URL_SYNC=postgresql+psycopg2://scanctum:YOUR_DB_PASSWORD@postgres:5432/scanctum

# ── Redis ─────────────────────────────────────────────────────────────────────
REDIS_URL=redis://redis:6379/0

# ── JWT — generate with: python3 -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=REPLACE_WITH_64_CHAR_RANDOM_HEX
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480

# ── CORS — only your domain ────────────────────────────────────────────────────
BACKEND_CORS_ORIGINS=["https://scanctum.kroszborg.co"]

# ── API ────────────────────────────────────────────────────────────────────────
API_V1_PREFIX=/api/v1

# ── Frontend ───────────────────────────────────────────────────────────────────
# Not used at runtime (baked at Docker build time via ARG) — but set anyway
NEXT_PUBLIC_API_URL=https://scanctum.kroszborg.co/api/v1

# ── Scanner ────────────────────────────────────────────────────────────────────
SCANNER_MAX_DEPTH_QUICK=2
SCANNER_MAX_PAGES_QUICK=20
SCANNER_MAX_DEPTH_FULL=5
SCANNER_MAX_PAGES_FULL=100
SCANNER_REQUEST_DELAY=2.0
SCANNER_CONCURRENCY=5

# ── Postgres credentials (for the postgres Docker container) ───────────────────
POSTGRES_USER=scanctum
POSTGRES_PASSWORD=YOUR_DB_PASSWORD
POSTGRES_DB=scanctum

# ── Flower basic auth ──────────────────────────────────────────────────────────
FLOWER_USER=admin
FLOWER_PASSWORD=REPLACE_WITH_STRONG_PASSWORD
```

Generate secure values:
```bash
# JWT secret
python3 -c "import secrets; print(secrets.token_hex(32))"

# DB password
openssl rand -base64 32 | tr -d '=+/' | cut -c1-32

# Flower password
openssl rand -base64 16
```

---

## 7. Deploy the App

### 7.1 Build and Start

```bash
cd /opt/scanctum

# Build all images and start in detached mode
docker compose -f docker-compose.prod.yml up -d --build
```

This will:
- Build the backend image (installs Python deps, WeasyPrint libs)
- Build the frontend image (Next.js standalone build with NEXT_PUBLIC_API_URL baked in)
- Start postgres, redis, backend (runs `alembic upgrade head` + uvicorn)
- Start celery_worker, flower, caddy
- Caddy automatically requests a TLS certificate from Let's Encrypt for `scanctum.kroszborg.co`

First build takes 3–10 minutes. Check progress:
```bash
docker compose -f docker-compose.prod.yml logs -f
```

### 7.2 Verify All Containers Are Running

```bash
docker compose -f docker-compose.prod.yml ps
```

Expected output — all services `Up` or `healthy`:
```
NAME              STATUS
scanctum-caddy    Up
scanctum-frontend Up
scanctum-backend  Up (healthy)
scanctum-celery   Up
scanctum-flower   Up
scanctum-postgres Up (healthy)
scanctum-redis    Up (healthy)
```

### 7.3 Run Database Migrations (first deploy)

Migrations run automatically via `alembic upgrade head` in the backend start command. Check they succeeded:

```bash
docker compose -f docker-compose.prod.yml logs backend | grep -i alembic
# Should show: INFO  [alembic.runtime.migration] Running upgrade ...
```

If you need to run them manually:
```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### 7.4 Test the Endpoints

```bash
# Health check
curl https://scanctum.kroszborg.co/health
# → {"status":"ok"}

# API docs (FastAPI auto-docs)
curl -I https://scanctum.kroszborg.co/api/v1/docs
# → HTTP/2 200
```

Then visit `https://scanctum.kroszborg.co` in a browser and sign up for the first account (first user becomes admin).

---

## 8. Post-Deploy Checks

### 8.1 TLS Certificate

Caddy auto-provisions a Let's Encrypt certificate. Verify:
```bash
curl -I https://scanctum.kroszborg.co
# Look for: strict-transport-security header
```

### 8.2 WebSocket Connectivity

In browser DevTools → Network → WS filter, start a scan and verify the WebSocket connects to `wss://scanctum.kroszborg.co/api/v1/ws/scans/.../progress` with status 101.

### 8.3 Celery Workers Active

```bash
docker compose -f docker-compose.prod.yml exec celery_worker \
  celery -A app.tasks.celery_app inspect active
```

Access Flower dashboard (via SSH tunnel — never expose publicly):
```bash
# From your local machine:
ssh -L 5555:localhost:5555 -N user@YOUR_VM_IP
# Then open http://localhost:5555 in your browser
```

### 8.4 Set Up UFW (Optional but Recommended)

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 443/udp
sudo ufw enable
sudo ufw status
```

---

## 9. Performance Tuning

### 9.1 Uvicorn Workers

`docker-compose.prod.yml` uses `--workers 2` which is right for e2-medium. Don't increase past 2 on 4 GB RAM — each worker forks a full Python process.

When you upgrade to e2-standard-2: change to `--workers 4`.

### 9.2 Celery Concurrency

`--concurrency=2` runs 2 parallel scan tasks. Scans are mostly I/O-bound (HTTP requests) so 2 is reasonable. Avoid going higher on 4 GB RAM as each scan worker holds crawl state in memory.

### 9.3 PostgreSQL Connection Pool

With 2 Uvicorn workers × 5 connections each = 10 DB connections max. Postgres defaults to 100 max_connections, so this is fine.

### 9.4 Redis Persistence

AOF persistence (`--appendonly yes`) is enabled so in-flight Celery task state survives Redis restarts.

### 9.5 Swap Space (required for e2-medium)

4 GB RAM is tight. Add a 2 GB swap file right after provisioning the VM — it prevents OOM kills during Docker builds and active scans:

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
# Reduce swappiness so swap is only used when really needed
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

---

## 10. Automated Backups

### 10.1 Daily PostgreSQL Backup to GCS

Install `gcloud` CLI and create a GCS bucket:
```bash
# Create bucket (one-time)
gsutil mb -l us-central1 gs://scanctum-backups-YOUR_PROJECT
```

Create `/opt/scanctum/backup.sh`:
```bash
#!/bin/bash
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="/tmp/scanctum_backup_${TIMESTAMP}.sql.gz"
BUCKET="gs://scanctum-backups-YOUR_PROJECT/postgres"

# Dump and compress
docker compose -f /opt/scanctum/docker-compose.prod.yml exec -T postgres \
  pg_dump -U scanctum scanctum | gzip > "$BACKUP_FILE"

# Upload to GCS
gsutil cp "$BACKUP_FILE" "$BUCKET/"

# Remove local copy
rm "$BACKUP_FILE"

# Keep only last 30 backups in GCS
gsutil ls "$BUCKET/" | sort | head -n -30 | xargs -r gsutil rm
```

```bash
chmod +x /opt/scanctum/backup.sh

# Schedule daily at 2am UTC
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/scanctum/backup.sh >> /var/log/scanctum-backup.log 2>&1") | crontab -
```

### 10.2 Restore from Backup

```bash
# Download from GCS
gsutil cp gs://scanctum-backups-YOUR_PROJECT/postgres/scanctum_backup_TIMESTAMP.sql.gz /tmp/

# Restore
gunzip -c /tmp/scanctum_backup_TIMESTAMP.sql.gz | \
  docker compose -f /opt/scanctum/docker-compose.prod.yml exec -T postgres \
  psql -U scanctum -d scanctum
```

---

## 11. Monitoring & Logs

### 11.1 Live Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f celery_worker
docker compose -f docker-compose.prod.yml logs -f caddy
```

### 11.2 Flower (Celery Monitor)

Access via SSH tunnel:
```bash
# From your local machine
ssh -L 5555:localhost:5555 -N YOUR_USER@YOUR_VM_IP
# Open: http://localhost:5555
# Login: admin / FLOWER_PASSWORD from .env
```

### 11.3 GCP Cloud Monitoring

Enable the Cloud Monitoring agent to get CPU, RAM, and disk metrics in GCP Console:

```bash
curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
sudo bash add-google-cloud-ops-agent-repo.sh --also-install
```

Set up an uptime check in GCP Console → Monitoring → Uptime Checks:
- Target URL: `https://scanctum.kroszborg.co/health`
- Check interval: 1 minute
- Alert policy: notify you if it fails 2+ times

### 11.4 Disk Usage

```bash
# Check disk
df -h /

# Check Docker volumes
docker system df
```

Clean up old Docker images periodically:
```bash
docker system prune -f --volumes  # WARNING: removes stopped containers and unused volumes
# Or, safer — only prune images:
docker image prune -f
```

---

## 12. Upgrading & Redeploying

```bash
cd /opt/scanctum

# Pull latest code
git pull origin main

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build

# Check migrations ran
docker compose -f docker-compose.prod.yml logs backend | tail -50
```

Zero-downtime deploy is not configured by default (the app restarts briefly). For true zero-downtime you'd need multiple backend replicas behind a load balancer — overkill for a single VM.

---

## 13. Feature Roadmap

Features worth adding to this app:

### High Value (implement soon)

| Feature | What to build |
|---|---|
| **Email notifications** | Send email on scan completion or critical vuln found. Add SMTP env vars (`SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`), use `aiosmtplib`, fire after scan task completes. |
| **Webhook / Slack alerts** | POST to a configurable URL when a scan finishes or critical severity found. One table in DB for webhook URLs per user. |
| **Celery Beat scheduled scans** | Add `celery[beat]` and a Beat scheduler container. Scans already have a schedules model — connect it to Beat so they run automatically. |
| **JSON / CSV export** | Add `GET /api/v1/scans/{id}/export?format=json|csv` alongside the existing PDF export. `csv` module is in stdlib. |

### Scanner Modules (add to `backend/app/scanner/modules/`)

| Module | What it checks |
|---|---|
| **Subdomain enumeration** | Brute-force common subdomains, check DNS, return live ones |
| **Technology fingerprinting** | Parse headers + HTML for framework/server fingerprints (like Wappalyzer) |
| **HTTP security misconfig** | TRACE method enabled, OPTIONS returning dangerous methods |
| **JavaScript secret scanner** | Crawl JS files looking for API keys, secrets, tokens in JS bundles |
| **Clickjacking test** | Check X-Frame-Options + CSP frame-ancestors |
| **SPF/DKIM/DMARC check** | DNS lookup for email security records |

### Dashboard / UI

| Feature | Where to add |
|---|---|
| **Vulnerability trend chart** | Track severity counts per scan over time, show line chart on dashboard |
| **Domain asset map** | Visual graph of crawled pages and discovered endpoints |
| **Real-time scan console** | Stream raw scan log lines over WebSocket to a terminal-style UI panel |
| **Diff view improvements** | Side-by-side diff of vulns between two scans with added/fixed/unchanged labels |

### Security & Auth

| Feature | Notes |
|---|---|
| **API key management** | Issue static API keys for CI/CD integration (GitHub Actions → run scan on deploy) |
| **MFA / TOTP** | Add TOTP 2FA for user accounts using `pyotp` |
| **Audit log** | Record who ran what scan when — important for pentesting engagements |
| **Role-based scan access** | Let admins restrict which URLs an analyst can scan |

### Infrastructure

| Feature | Notes |
|---|---|
| **GitHub Actions CI** | Auto-deploy to the VM on push to `main` via SSH deploy script |
| **Fail2ban** | Block IPs making too many failed login attempts |
| **Log aggregation** | Ship Docker logs to a central store (Loki + Grafana, or GCP Cloud Logging) |

---

## 14. Troubleshooting

### Caddy can't get TLS certificate

```bash
docker compose -f docker-compose.prod.yml logs caddy
```

Common causes:
- DNS not propagated yet — wait and retry
- Port 80 is blocked — check GCP firewall and UFW allow port 80
- Let's Encrypt rate limit — wait 1 hour and retry

Force Caddy to retry:
```bash
docker compose -f docker-compose.prod.yml restart caddy
```

### Backend health check failing

```bash
docker compose -f docker-compose.prod.yml logs backend
```

Common causes:
- `alembic upgrade head` failed — check DB credentials in `.env`
- Port 8000 not bound — check uvicorn startup line in logs
- OOM kill — increase VM size or reduce `--workers`

### Celery not processing scans

```bash
docker compose -f docker-compose.prod.yml logs celery_worker
```

Check Redis connectivity from worker:
```bash
docker compose -f docker-compose.prod.yml exec celery_worker \
  python3 -c "import redis; r=redis.from_url('redis://redis:6379/0'); print(r.ping())"
# Should print: True
```

### Frontend shows "Network Error"

1. Verify `NEXT_PUBLIC_API_URL` was set as a Docker build arg (it's baked at build time).
2. Check `BACKEND_CORS_ORIGINS` in `.env` includes exactly `https://scanctum.kroszborg.co`.
3. Rebuild after any `.env` change:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build frontend backend
   ```

### Out of disk space

```bash
df -h /

# Clean Docker layer cache (does not remove running containers or named volumes)
docker builder prune -f
docker image prune -f
```

### View container resource usage

```bash
docker stats
```

---

## Quick Reference

```bash
# Start
docker compose -f docker-compose.prod.yml up -d --build

# Stop
docker compose -f docker-compose.prod.yml down

# Restart single service
docker compose -f docker-compose.prod.yml restart backend

# View logs
docker compose -f docker-compose.prod.yml logs -f [service]

# Run alembic migration manually
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Open psql shell
docker compose -f docker-compose.prod.yml exec postgres psql -U scanctum -d scanctum

# Open Redis CLI
docker compose -f docker-compose.prod.yml exec redis redis-cli

# Check container status
docker compose -f docker-compose.prod.yml ps

# SSH tunnel to Flower
ssh -L 5555:localhost:5555 -N YOUR_USER@YOUR_VM_IP
```
