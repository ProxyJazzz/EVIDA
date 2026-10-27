# EVIDA — Deployment & Infrastructure Topology

## 1. Intended Production Topology

```text
       DNS / Cloudflare CDN
                │
        ┌───────┴───────┐
        ▼               ▼
   [ Next.js App ]  [ FastAPI Backend ]
   (Vercel / Kube)  (Container / Kube)
        │               │
        │               ├──────────────┐
        ▼               ▼              ▼
   [ Supabase ]   [ Nebius Cloud ]  [ Worker Sandboxes ]
   Managed Postgres   Token Factory  Ephemeral Docker/gVisor
   Auth & Storage   NVIDIA Nemotron    Execution Pool
```

---

## 2. Infrastructure Components

### 2.1 Next.js Web Frontend
- Deployed on Vercel or AWS ECS / Google Cloud Run container.
- Environment variables:
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
  - `NEXT_PUBLIC_API_URL`

### 2.2 FastAPI Backend
- Deployed as a stateless container on AWS ECS, GCP Cloud Run, or Kubernetes.
- Environment variables:
  - `APP_ENV=production`
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `NEBIUS_API_KEY`
  - `NEBIUS_BASE_URL`
  - `NEBIUS_MODEL`
- Horizontal autoscaling based on HTTP request volume and CPU utilization.

### 2.3 Supabase Managed Platform
- Hosted PostgreSQL with connection pooling (PgBouncer / Supavisor).
- Automated daily backups and point-in-time recovery.
- Row Level Security enabled for defense-in-depth data partitioning.

### 2.4 Worker / Sandbox Fleet
- Ephemeral worker nodes running hardened container runtimes (e.g., Docker with seccomp/apparmor or gVisor / Firecracker microVMs).
- Isolated VPC without access to internal management interfaces or production database instances.
