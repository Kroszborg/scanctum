# Scanctum — Codebase Explanation

A comprehensive guide to understanding how Scanctum works, from frontend to backend, scanning to reporting.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Backend Structure](#backend-structure)
   - [FastAPI Application](#fastapi-application)
   - [Database Models](#database-models)
   - [API Endpoints](#api-endpoints)
   - [Services Layer](#services-layer)
   - [Scanner System](#scanner-system)
3. [Frontend Structure](#frontend-structure)
   - [Next.js App Router](#nextjs-app-router)
   - [Components](#components)
   - [State Management](#state-management)
4. [How Scanning Works](#how-scanning-works)
   - [Scan Lifecycle](#scan-lifecycle)
   - [Crawler](#crawler)
   - [Vulnerability Modules](#vulnerability-modules)
   - [Real-time Updates](#real-time-updates)
5. [Authentication & Authorization](#authentication--authorization)
6. [Report Generation](#report-generation)
7. [Deployment](#deployment)

---

## Architecture Overview

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────────────────────────────┐
│  Frontend (Next.js 15)              │
│  - React Server/Client Components    │
│  - WebSocket client for progress    │
│  - REST API calls via axios         │
└──────┬──────────────────────────────┘
       │ REST API + WebSocket
       ▼
┌─────────────────────────────────────┐
│  Backend (FastAPI + Uvicorn)        │
│  - REST endpoints                    │
│  - WebSocket for real-time progress  │
│  - JWT authentication               │
└──────┬───────────────┬───────────────┘
       │               │
       │ SQL           │ Redis pub/sub
       ▼               ▼
┌─────────────┐  ┌─────────────┐
│ PostgreSQL  │  │    Redis     │
│  (Database) │  │ (Queue + WS) │
└──────┬──────┘  └──────┬───────┘
       │                 │
       │                 │ Celery broker
       │                 ▼
       │         ┌───────────────┐
       │         │ Celery Worker │
       │         │ (Scan Engine) │
       └─────────┴───────────────┘
```

**Key Technologies:**
- **Backend:** FastAPI (Python), SQLAlchemy (ORM), Celery (task queue), Redis (broker/pub-sub)
- **Frontend:** Next.js 15 (React), TypeScript, Tailwind CSS
- **Database:** PostgreSQL 16
- **Task Queue:** Redis + Celery
- **Real-time:** WebSocket (FastAPI) + Redis pub/sub

---

## Backend Structure

### FastAPI Application

**Entry Point:** `backend/app/main.py`

- Creates FastAPI app with CORS middleware
- Includes API router at `/api/v1`
- Global exception handler ensures CORS headers on errors
- Health check endpoint at `/health`

**Key Middleware:**
- `RequestIDMiddleware` — adds unique request ID to logs
- `TimingMiddleware` — logs request duration
- `CORSMiddleware` — allows frontend origin, credentials, all methods/headers

### Database Models

Located in `backend/app/models/`:

1. **User** (`user.py`)
   - `id`, `email`, `password_hash`, `full_name`, `role` (admin/analyst), `is_active`
   - Relationship: `scans` (one-to-many)

2. **Scan** (`scan.py`)
   - `id`, `user_id`, `target_url`, `scan_mode` (quick/full), `status` (pending/crawling/scanning/completed/failed/cancelled)
   - `progress_percent`, `pages_found`, `pages_scanned`
   - `celery_task_id` (for cancellation), `config` (JSONB for custom headers, scope settings)
   - `started_at`, `completed_at`, `error_message`
   - Relationships: `vulnerabilities` (one-to-many), `user` (many-to-one)

3. **Vulnerability** (`result.py`)
   - `id`, `scan_id`, `module_name`, `vuln_type`, `severity` (critical/high/medium/low/info)
   - `cvss_score`, `cvss_vector`, `owasp_category`, `cwe_id`
   - `affected_url`, `affected_parameter`, `description`, `remediation`, `confidence`
   - `is_false_positive`
   - Relationships: `evidence` (one-to-many), `scan` (many-to-one)

4. **Evidence** (`result.py`)
   - `id`, `vulnerability_id`, `evidence_type`, `title`, `content`, `order_index`
   - Stores proof of vulnerability (payloads, responses, headers, etc.)

5. **ScanComparison** (`comparison.py`)
   - Compares two scans to show what changed

6. **AuditLog** (`audit.py`)
   - Tracks user actions

### API Endpoints

**Router:** `backend/app/api/v1/router.py` — includes all sub-routers

**Endpoints:**

1. **`/auth`** (`auth.py`)
   - `POST /login` — JWT login
   - `POST /signup` — public registration (first user = admin, others = analyst)
   - `POST /register` — admin-only user creation
   - `GET /me` — current user info

2. **`/scans`** (`scans.py`)
   - `POST /scans` — create scan (queues Celery task)
   - `GET /scans` — list user's scans (paginated, filterable by status)
   - `GET /scans/{id}` — get scan details
   - `GET /scans/{id}/status` — get scan status
   - `GET /scans/{id}/results` — get vulnerabilities (filterable by severity/OWASP/module)
   - `POST /scans/{id}/cancel` — cancel running scan

3. **`/vulnerabilities`** (`vulnerabilities.py`)
   - `GET /vulnerabilities` — global vulnerability DB (all scans, filterable)

4. **`/assets`** (`assets.py`)
   - `GET /assets` — list discovered assets (URLs from scans)

5. **`/reports`** (`reports.py`)
   - `GET /reports/{scan_id}?format=pdf|json` — generate/download report

6. **`/schedules`** (`schedules.py`)
   - CRUD for scheduled scans (in-memory MVP)

7. **`/dashboard`** (`dashboard.py`)
   - `GET /dashboard/stats` — scan counts, vulnerability counts by severity

8. **`/ws/scans/{scan_id}/progress`** (`ws.py`)
   - WebSocket endpoint for real-time scan progress
   - Subscribes to Redis channel `scan:{scan_id}:progress`
   - Forwards progress updates to browser

### Services Layer

**Location:** `backend/app/services/`

1. **AuthService** (`auth_service.py`)
   - `login()` — validates credentials, returns JWT
   - `register()` / `register_public()` — creates user, hashes password with bcrypt
   - JWT uses `python-jose` with HS256, expires in 480 minutes

2. **ScanService** (`scan_service.py`)
   - `create_and_dispatch()` — creates Scan record, dispatches Celery task `run_scan.delay()`
   - `list_scans()` — paginated list with filters
   - `get_scan()` — fetch scan by ID (user-scoped)
   - `cancel_scan()` — sets status to "cancelled", revokes Celery task

3. **ResultService** (`result_service.py`)
   - `get_results()` — fetches vulnerabilities for a scan with filters

4. **ReportService** (`report_service.py`)
   - `generate_json_report()` — returns structured JSON
   - `generate_pdf_report()` — renders Jinja2 template → HTML → PDF (WeasyPrint or xhtml2pdf fallback)

### Scanner System

**Location:** `backend/app/scanner/`

#### Orchestrator (`orchestrator.py`)

**`ScanOrchestrator`** — main scan coordinator:

1. **Setup** — creates HttpClient, ScopeValidator, AsyncCrawler, selects modules for scan mode
2. **Phase 1: Crawl** — discovers pages (BFS, respects depth/page limits, extracts links/forms)
3. **Phase 2: Scan** — for each page:
   - Runs passive modules (analyze HTML/headers)
   - Runs active modules (send payloads, test parameters)
   - Collects findings
4. **Phase 3: Persist** — deduplicates findings, saves to DB, publishes progress

**Progress Updates:**
- Publishes to Redis channel `scan:{scan_id}:progress` with JSON: `{status, progress, pages_found, pages_scanned}`
- Frontend WebSocket subscribes and displays updates

#### Crawler (`crawler.py`)

**`AsyncCrawler`** — BFS web crawler:

- **Link Extraction:** `<a href>`, `<link href>`, `<script/img/iframe src>`, `<area href>`, `srcset`, `data-href`, `data-src`, `<meta refresh>`, form actions
- **Seed URLs:** For quick/full scans, adds common paths (`/login`, `/admin`, `/api`, etc.) so scans always probe multiple pages
- **Deduplication:** Normalizes URLs (removes fragments, sorts query params, lowercases host)
- **Scope Control:** Only crawls same domain (or subdomains if enabled)
- **Rate Limiting:** Per-domain throttle (default 2s delay)
- **Circuit Breaker:** Stops crawling a domain after repeated failures

#### Vulnerability Modules

**Location:** `backend/app/scanner/modules/`

Each module extends `BaseModule` and implements:
- `scan_modes` — which modes include it (`["quick"]`, `["full"]`, or both)
- `is_active` — whether it sends requests (vs. passive analysis)
- `detect()` / `detect_async()` — passive analysis of HTML/headers
- `active_test()` / `active_test_async()` — sends payloads, tests parameters

**Modules:**

**Quick + Full:**
- `security_headers` — checks missing headers (CSP, HSTS, X-Frame-Options, etc.)
- `https_check` — verifies HTTPS redirect
- `tls_check` — TLS version/cipher checks
- `cors` — CORS misconfiguration
- `xss` — reflected XSS (40+ payloads, context-aware)
- `open_redirect` — open redirect vulnerabilities
- `directory_exposure` — directory listing detection
- `jwt_analysis` — JWT token security
- `robots_txt` — robots.txt analysis
- `cookie_security` — Secure/SameSite flags

**Full Only:**
- `command_injection` — OS command injection (output + time-based)
- `sqli` — SQL injection
- `ssrf` — Server-Side Request Forgery
- `path_traversal` — directory traversal
- `sensitive_files` — exposed config files (`.env`, `.git`, etc.)
- `idor` — Insecure Direct Object Reference
- `csrf` — CSRF token checks
- `crlf_injection` — CRLF injection
- `xxe` — XML External Entity
- `ssti` — Server-Side Template Injection
- `graphql` — GraphQL introspection
- `api_misconfig` — exposed API docs, debug endpoints
- `rate_limit_check` — rate limiting detection

**Module Registry** (`registry.py`):
- Auto-discovers modules via `@ModuleRegistry.register` decorator
- `get_for_mode("quick"|"full")` returns instantiated modules for that mode

#### Scoring (`scoring/`)

- **Severity** (`severity.py`) — maps CVSS scores to severity labels, OWASP Top 10 categories
- **CVSS Lite** (`cvss_lite.py`) — calculates CVSS v3.1 scores from vulnerability characteristics

---

## Frontend Structure

### Next.js App Router

**Location:** `frontend/src/app/`

**Routes:**
- `/` — redirects to `/dashboard`
- `/login` — login page (`(auth)/login/page.tsx`)
- `/signup` — signup page (`(auth)/signup/page.tsx`)
- `/dashboard` — main dashboard (`(dashboard)/page.tsx`)
- `/dashboard/scans` — scan list (`(dashboard)/scans/page.tsx`)
- `/dashboard/scans/[id]` — scan detail with progress (`(dashboard)/scans/[id]/page.tsx`)
- `/dashboard/scans/[id]/report` — report view (`(dashboard)/scans/[id]/report/page.tsx`)
- `/dashboard/vulnerabilities` — global vulnerability DB (`(dashboard)/vulnerabilities/page.tsx`)
- `/dashboard/assets` — discovered assets (`(dashboard)/assets/page.tsx`)
- `/dashboard/schedules` — scheduled scans (`(dashboard)/schedules/page.tsx`)

**Layouts:**
- `layout.tsx` — root layout (provides AuthProvider, ThemeProvider)
- `(auth)/layout.tsx` — auth pages layout
- `(dashboard)/layout.tsx` — dashboard layout (Header, Sidebar)

### Components

**Location:** `frontend/src/components/`

**Key Components:**
- `layout/header.tsx` — top bar (user email, role, theme toggle, logout)
- `layout/sidebar.tsx` — navigation sidebar
- `scan/scan-progress.tsx` — progress bar, status badge
- `scan/results-table.tsx` — vulnerabilities table (sortable, filterable)
- `report/download-button.tsx` — PDF/JSON download (uses `fetch()` to avoid XHR issues)
- `vulnerability/vulnerability-card.tsx` — vulnerability detail card
- `ui/` — reusable UI components (buttons, badges, etc.)

### State Management

**Hooks** (`frontend/src/hooks/`):

1. **`use-auth.ts`** — authentication state
   - Reads JWT from `localStorage`
   - Provides `user`, `login()`, `logout()`
   - Auto-redirects on 401

2. **`use-scans.ts`** — scan data fetching
   - `useScan(id)` — fetch single scan + results
   - `useScans()` — fetch scan list

3. **`use-scan-ws.ts`** — WebSocket for real-time progress
   - Connects to `ws://backend/ws/scans/{id}/progress`
   - Subscribes to Redis pub/sub channel
   - Falls back to polling if WebSocket unavailable
   - Calls `onProgress` callback when updates arrive

4. **`use-polling.ts`** — polling fallback for scan status

**API Client** (`frontend/src/lib/api.ts`):
- Axios instance with base URL from `NEXT_PUBLIC_API_URL`
- Request interceptor: adds `Authorization: Bearer <token>` from localStorage
- Response interceptor: handles 401 → logout + redirect to `/login`

---

## How Scanning Works

### Scan Lifecycle

1. **User creates scan** → Frontend calls `POST /scans` with `{target_url, scan_mode, config?}`
2. **Backend creates Scan record** → Status = "pending", saves to DB
3. **Backend dispatches Celery task** → `run_scan.delay(scan_id)` → task queued in Redis
4. **Celery worker picks up task** → `run_scan()` → creates `ScanOrchestrator` → calls `orchestrator.run()`
5. **Orchestrator runs async pipeline:**
   - **Crawl phase** → discovers pages, updates `pages_found`, publishes progress
   - **Scan phase** → runs modules on each page, publishes progress per page
   - **Persist phase** → saves findings to DB, sets status = "completed"
6. **Frontend receives updates** → via WebSocket (or polling fallback) → UI updates progress bar
7. **Scan completes** → Frontend fetches results → displays vulnerabilities table

### Crawler

**`AsyncCrawler`** (`crawler.py`):

- **BFS Queue:** `deque[(url, depth)]` — processes URLs level by level
- **Visited Set:** Normalized URLs to avoid duplicates
- **Link Extraction:** Parses HTML with BeautifulSoup, extracts:
  - `<a href>`, `<link href>`
  - `<script>`, `<img>`, `<iframe>`, `<source>`, `<video>`, `<audio>` `src`
  - `<area href>` (image maps)
  - `srcset` (first URL per source)
  - `data-href`, `data-src` attributes
  - `<meta http-equiv="refresh">` content URL
  - Form `action` URLs
- **Seed URLs:** Adds common paths (`/login`, `/admin`, `/api`, etc.) so scans always probe multiple pages
- **Scope Validation:** Only crawls same domain (or subdomains if `include_subdomains=true`)
- **Rate Limiting:** `PerDomainThrottle` — waits 2s between requests to same domain
- **Circuit Breaker:** Stops crawling a domain after 5 consecutive failures

### Vulnerability Modules

**Module Pattern:**

```python
@ModuleRegistry.register
class XssModule(BaseModule):
    name = "xss"
    scan_modes = ["quick", "full"]
    is_active = True  # sends requests
    
    async def detect_async(self, page: CrawledPage) -> list[Finding]:
        # Passive: analyze HTML/headers
        return []
    
    async def active_test_async(self, page: CrawledPage, http_client: HttpClient) -> list[Finding]:
        # Active: send payloads, test parameters
        findings = []
        for param in query_params:
            payload = "<script>alert(1)</script>"
            response = await http_client.get(url_with_payload)
            if payload in response.text:
                findings.append(Finding(...))
        return findings
```

**Finding Structure:**
- `module_name`, `vuln_type`, `severity`, `cvss_score`, `cvss_vector`
- `owasp_category`, `cwe_id`
- `affected_url`, `affected_parameter`
- `description`, `remediation`, `confidence`
- `evidence` — list of proof items (payloads, responses, headers)

### Real-time Updates

**Flow:**

1. **Orchestrator publishes** → `_publish_progress(scan_id, {status, progress, pages_found, pages_scanned})`
2. **Redis pub/sub** → Message published to channel `scan:{scan_id}:progress`
3. **Backend WebSocket** → `ws.py` subscribes to Redis channel, forwards to connected browser
4. **Frontend WebSocket** → `use-scan-ws.ts` receives JSON, calls `onProgress()` callback
5. **UI updates** → Progress bar, status badge, page counts update in real-time

**Fallback:** If WebSocket unavailable, frontend polls `GET /scans/{id}/status` every 3 seconds.

---

## Authentication & Authorization

**Flow:**

1. **Login** → `POST /auth/login` with `{email, password}`
2. **Backend validates** → `AuthService.login()` checks password hash (bcrypt)
3. **JWT issued** → `python-jose` creates JWT with `{"sub": user_id}`, expires in 480 minutes
4. **Frontend stores** → JWT saved to `localStorage` as `scanctum_token`
5. **API calls** → Axios interceptor adds `Authorization: Bearer <token>` header
6. **Backend validates** → `get_current_user()` dependency decodes JWT, fetches user from DB
7. **Authorization** → `require_role("admin")` checks user role

**Roles:**
- **admin** — can create users, access all features
- **analyst** — can run scans, view own results

---

## Report Generation

**Flow:**

1. **User requests report** → `GET /reports/{scan_id}?format=pdf`
2. **Backend generates** → `ReportService.generate_pdf_report()`
3. **Template rendering** → Jinja2 renders `templates/reports/report.html` with scan/vulnerability data
4. **PDF conversion:**
   - **Primary:** WeasyPrint (if GTK/system libs available) — better CSS support
   - **Fallback:** xhtml2pdf (Windows/compatibility) — simpler CSS, still works
5. **Response** → Returns PDF bytes with `Content-Type: application/pdf`, `Content-Disposition: attachment`

**Template Structure:**
- Cover page (title, target, date, risk level, CONFIDENTIAL badge)
- Executive summary (severity distribution table, OWASP Top 10 overview)
- Detailed findings (each vulnerability with description, evidence, remediation)
- Disclaimer

**Evidence Loading:** Uses `selectinload(Vulnerability.evidence)` to eager-load evidence for template.

---

## Deployment

**See `DEPLOY.md` for full details.**

**Quick Summary:**
- **Docker Compose** — local development (Postgres, Redis, backend, Celery, frontend)
- **Render Blueprint** — production deployment (`render.yaml` provisions all services)
- **Split Deployment** — backend on Render, frontend on Vercel (common setup)

**Key Files:**
- `docker-compose.yml` — local dev stack
- `render.yaml` — Render Blueprint (free tier compatible, omits Celery worker)
- `backend/Dockerfile` — Python backend image
- `frontend/Dockerfile` — Next.js frontend image (standalone build)
- `backend/entrypoint-render.sh` — rewrites `postgresql://` → `postgresql+asyncpg://` for Render

---

## Key Design Decisions

1. **Async Backend** — FastAPI uses async/await for I/O-bound operations (HTTP requests, DB queries)
2. **Celery for Scans** — Long-running scans run in background workers, not blocking API
3. **Redis Pub/Sub** — Real-time progress without polling (WebSocket forwards Redis messages)
4. **Modular Scanner** — Each vulnerability type is a separate module, easy to add new checks
5. **Dual PDF Engines** — WeasyPrint (better) + xhtml2pdf (fallback) for cross-platform compatibility
6. **Seed URLs** — Always probes common paths so scans find pages even if homepage has no links
7. **Scope Control** — Only scans same domain (configurable subdomains) to avoid scanning external sites
8. **Rate Limiting** — Per-domain throttle prevents overwhelming target servers

---

## File Structure Summary

```
scanctum/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST endpoints + WebSocket
│   │   ├── core/            # Exceptions, middleware, security
│   │   ├── db/              # Database engine, session management
│   │   ├── models/          # SQLAlchemy models (User, Scan, Vulnerability, Evidence)
│   │   ├── schemas/         # Pydantic schemas (request/response validation)
│   │   ├── scanner/         # Scanning engine
│   │   │   ├── modules/     # Vulnerability detection modules (25+ modules)
│   │   │   ├── crawler.py   # Web crawler
│   │   │   ├── orchestrator.py  # Scan coordinator
│   │   │   └── scoring/     # CVSS/severity calculation
│   │   ├── services/        # Business logic (AuthService, ScanService, ReportService)
│   │   ├── tasks/           # Celery tasks (run_scan, generate_pdf)
│   │   └── templates/reports/  # Jinja2 PDF template
│   ├── alembic/             # Database migrations
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router pages
│   │   ├── components/      # React components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── lib/             # API client, utilities
│   │   └── providers/       # AuthProvider, ThemeProvider
│   ├── Dockerfile
│   └── package.json
├── render.yaml               # Render Blueprint
├── docker-compose.yml        # Local dev stack
└── EXPLAIN.md                # This file
```

---

## Common Workflows

### Creating a Scan

1. User fills form → `POST /scans` with `{target_url: "https://example.com", scan_mode: "full"}`
2. `ScanService.create_and_dispatch()` → creates Scan record, dispatches Celery task
3. Celery worker → `run_scan()` → `ScanOrchestrator.run()`
4. Orchestrator crawls → discovers pages, extracts links/forms
5. Orchestrator scans → runs modules (passive + active tests)
6. Findings saved → vulnerabilities + evidence persisted to DB
7. Progress updates → Redis pub/sub → WebSocket → frontend updates UI

### Viewing Results

1. User navigates to `/dashboard/scans/{id}`
2. Frontend calls `GET /scans/{id}` → gets scan metadata
3. Frontend calls `GET /scans/{id}/results` → gets vulnerabilities
4. `ResultsTable` component displays findings with filters/sorting
5. User clicks vulnerability → shows detail card with evidence/remediation

### Generating PDF Report

1. User clicks "Download PDF" → `DownloadButton` component
2. Frontend uses `fetch()` → `GET /reports/{scan_id}?format=pdf` (with JWT)
3. Backend → `ReportService.generate_pdf_report()`
4. Jinja2 renders template → HTML
5. WeasyPrint/xhtml2pdf converts → PDF bytes
6. Response → browser downloads `scanctum-report-{id}.pdf`

---

This covers the core architecture and flow. For deployment details, see `DEPLOY.md`. For usage, see `README.md`.
