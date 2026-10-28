# EVIDA — Deployment, Infrastructure & Production Operations Guide

## 1. Intended Production Topology

```text
       DNS / Cloudflare CDN / TLS Termination
                 │
         ┌───────┴───────┐
         ▼               ▼
    [ Next.js App ]  [ FastAPI Backend ]
    (Vercel / Cloud) (Container / Cloud)
         │               │
         │               ├──────────────┐
         ▼               ▼              ▼
    [ Supabase ]   [ Nebius Cloud ]  [ Worker Sandboxes ]
    Managed Postgres   Token Factory  Ephemeral Subprocesses /
    Auth & Storage   NVIDIA Nemotron  Docker / gVisor
```

---

## 2. Infrastructure Components

### 2.1 Next.js Web Frontend (`apps/web`)
- **Hosting Target:** Vercel, AWS ECS, GCP Cloud Run, or Docker container.
- **Port:** 3000 (standard dev/prod).
- **Required Build-Time / Runtime Environment Variables:**
  ```env
  NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
  NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
  NEXT_PUBLIC_API_URL=https://api.yourdomain.com
  ```

### 2.2 FastAPI Backend (`apps/api`)
- **Hosting Target:** Stateless container (AWS Fargate, Google Cloud Run, Fly.io, or Kubernetes pod).
- **Port:** 8000.
- **Worker Configuration:** `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`.
- **Required Production Environment Variables:**
  ```env
  APP_ENV=production
  APP_NAME=EVIDA
  APP_VERSION=0.1.0

  API_HOST=0.0.0.0
  API_PORT=8000
  CORS_ORIGINS=["https://app.yourdomain.com", "https://yourdomain.vercel.app"]

  SUPABASE_URL=https://your-project.supabase.co
  SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

  NEBIUS_API_KEY=your-nebius-token-factory-key
  NEBIUS_BASE_URL=https://api.tokenfactory.nebius.com/v1
  NEBIUS_MODEL=nvidia/Nemotron-3_5-Lightning

  PATCH_APPLICATION_TIMEOUT_SECONDS=30.0
  REGRESSION_VERIFICATION_TIMEOUT_SECONDS=30.0
  BASELINE_VERIFICATION_TIMEOUT_SECONDS=60.0
  MAX_VERIFICATION_OUTPUT_BYTES=50000
  ```

### 2.3 Supabase Managed Platform (PostgreSQL & Storage)
- **Database Engine:** PostgreSQL 15+ with `pgcrypto` and `uuid-ossp` extensions.
- **Access Model:** All application access operates with Row Level Security (RLS) enabled.
- **Migrations:** Applied via `supabase db push` or standard SQL execution in order:
  1. `20261027000000_initial_schema.sql` (profiles, projects, repositories, investigations)
  2. `20261027010000_investigation_events.sql` (audit timeline)
  3. `20261027020000_repository_and_reproduction.sql` (archive metadata & reproduction runs)
  4. `20261027030000_investigation_hypotheses.sql` (AI root-cause hypotheses)
  5. `20261027040000_regression_tests.sql` (regression tests & verification runs)
  6. `20261027050000_patch_candidates.sql` (patch proposals & validation status)
  7. `20261027060000_patch_verification_runs.sql` (double validation execution proofs)
  8. `20261027070000_evidence_bundle.sql` (immutable append-only evidence items)

### 2.4 Isolated Execution Sandbox Fleet
- **Runner:** Ephemeral temporary directories (`tempfile.TemporaryDirectory`) with non-root UID 1000 permissions.
- **Resource Limits:** Hard execution timeouts (30s/60s), memory bounds, output clipping (50KB).
- **Security Boundary:** Disallowed shell metacharacters, whitelist executables (`pytest`, `python`), no `shell=True`, sensitive file masks (`.env*`, `*.pem`, `*.key`), and complete workspace deletion post-run.

---

## 3. Step-by-Step Production Deployment Guide

### Step 1: Clone Repository & Configure Environment
```bash
git clone https://github.com/your-org/evida.git
cd evida

# Copy example environment configuration
cp .env.example .env
```
Edit `.env` to populate your live Nebius Token Factory and Supabase credentials.

### Step 2: Database Migration
```bash
# Using Supabase CLI:
supabase link --project-ref your-project-ref
supabase db push
```

### Step 3: Backend Setup & Launch
```bash
# Set up Python virtual environment
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt || pip install -e ".[dev]"

# Start production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Step 4: Frontend Setup & Build
```bash
cd apps/web
npm install
npm run build
npm run start
```

### Step 5: System Health & Readiness Verification
Test the health probes to ensure all external dependencies are operational:
```bash
# Liveness probe:
curl -s http://localhost:8000/api/v1/health

# Readiness probe (verifies database, Nebius, and sandbox readiness):
curl -s http://localhost:8000/api/v1/health/ready
```

---

## 4. Automated Quality Gate Execution

Prior to deploying any release or submitting for review, execute the master validation script:

```bash
./scripts/final_validation.sh
```

This automatically runs:
1. All 239 backend unit and integration tests (`pytest`)
2. Python style checks (`ruff check`)
3. Python formatting checks (`ruff format --check`)
4. Python strict type safety (`mypy apps/api/app`)
5. Frontend unit tests (`vitest`)
6. Frontend linter (`next lint`)
7. Frontend production build (`next build`)
