# EVIDA — Evidence-Driven AI Software Repair

> **AI proposes. Evidence decides.**

EVIDA is an automated, evidence-driven software repair and verification platform. While existing code assistants guess fixes that look plausible, EVIDA treats all AI proposals as untrusted hypotheses. Every candidate patch must be verified deterministically in an isolated sandbox through failure reproduction, regression test generation, and full-test-suite double verification.

---

## Architecture Overview

```text
                    ┌──────────────────────┐
                    │      Next.js         │
                    │ React + TypeScript   │
                    │   (apps/web)         │
                    └──────────┬───────────┘
                               │
                               │ HTTPS / JSON
                               ▼
                    ┌──────────────────────┐
                    │       FastAPI        │
                    │ Application Backend  │
                    │   (apps/api)         │
                    └─────┬──────┬─────────┘
                          │      │
                          │      │ HTTPS
                          ▼      ▼
                   ┌─────────┐ ┌────────────────────────┐
                   │Supabase │ │  Nebius Token Factory  │
                   │         │ │  NVIDIA Open Model     │
                   │Postgres │ │  (Nemotron-3_5, etc.)  │
                   │Auth     │ └────────────────────────┘
                   │Storage  │
                   │RLS      │
                   └────┬────┘
                        │
                        ▼
               ┌───────────────────┐
               │ Worker / Sandbox  │
               │                   │
               │ Repository        │
               │ Test execution    │
               │ Patch execution   │
               └───────────────────┘
```

---

## Monorepo Layout

```text
evida/
├── apps/
│   ├── web/               # Next.js 14+ App Router frontend
│   └── api/               # FastAPI backend with Pydantic v2 & Nebius integration
├── packages/
│   └── shared/            # Shared TypeScript contracts and JSON schemas
├── supabase/
│   ├── migrations/        # PostgreSQL schema migrations with RLS
│   └── seed.sql           # Development seed data
├── sandbox/
│   ├── Dockerfile         # Hardened non-privileged execution container
│   ├── runner/            # Isolated command runner with hard timeouts
│   └── policies/          # Resource limits & security policies
├── tests/
│   ├── unit/              # Backend unit tests (config, AI provider, health, sandbox)
│   ├── integration/       # API integration tests
│   └── fixtures/          # Test data fixtures
├── docs/                  # In-depth architectural & security documentation
├── PRD.md                 # Product requirements document
├── Architecture.md        # Canonical system architecture
├── Rules.md               # Architectural & coding rules
├── Phases.md              # Multi-phase roadmap
├── Design.md              # Visual design tokens & styling
├── memory.md              # Project status ledger
└── README.md
```

---

## Prerequisites

- **Node.js:** v18.0.0+ (Tested on v24.19+)
- **Python:** 3.12+
- **Docker:** (Optional for local containerized sandbox, standard runner works on host)
- **Supabase CLI:** (Optional for local PostgreSQL emulation)

---

## Quickstart

### 1. Clone & Configure Environment

```bash
git clone <repo-url>
cd Evida

# Copy environment template
cp .env.example .env
```

Edit `.env` to configure your API keys (e.g., `NEBIUS_API_KEY`). **Note:** The backend operates cleanly in development mode even if Supabase or Nebius keys are not yet configured.

---

### 2. Backend Setup (`apps/api`)

```bash
cd apps/api

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies in editable mode
pip install -e ".[dev]"

# Run FastAPI development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend API endpoints:
- Liveness Probe: `curl http://localhost:8000/api/v1/health`
- Readiness Probe: `curl http://localhost:8000/api/v1/health/ready`
- Create Investigation: `curl -X POST http://localhost:8000/api/v1/investigations -H 'Content-Type: application/json' -d '{"repository_id": "...", "title": "..."}'`
- Start Lifecycle: `curl -X POST http://localhost:8000/api/v1/investigations/{id}/start`
- Get Investigation: `curl http://localhost:8000/api/v1/investigations/{id}`
- Get Event Timeline: `curl http://localhost:8000/api/v1/investigations/{id}/events`
- List Investigations: `curl http://localhost:8000/api/v1/investigations`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

---

### 3. Frontend Setup (`apps/web`)

```bash
cd apps/web

# Install dependencies
npm install

# Run Next.js development server
npm run dev
```

Frontend will be accessible at `http://localhost:3000`.
- Health Status Page: `http://localhost:3000/health`
- Login Shell: `http://localhost:3000/login`
- Dashboard Shell: `http://localhost:3000/dashboard`

---

### 4. Running Tests

#### Backend Tests & Linting:
```bash
cd apps/api
source .venv/bin/activate

# Run tests with pytest
pytest ../../tests/

# Lint and format check with ruff
ruff check app/
ruff format --check app/
```

#### Frontend Tests & Linting:
```bash
cd apps/web
npm run test
npm run lint
npm run build
```

#### Sandbox Execution Test:
```bash
python3 sandbox/runner/runner.py 'python3 -c "print(\"EVIDA sandbox OK\")"'
```

---

## Phase 3 AI Investigation Workflow

Once a failure reproduction run produces verdict `REPRODUCED`:

### 1. Trigger AI Investigation
```bash
curl -X POST http://localhost:8000/api/v1/investigations/{id}/investigate \
  -H "Content-Type: application/json"
```

### 2. Retrieve Causal Hypothesis
```bash
curl http://localhost:8000/api/v1/investigations/{id}/hypothesis
```

**Example Hypothesis Response:**
```json
{
  "id": "88888888-8888-8888-8888-888888888888",
  "investigation_id": "33333333-3333-3333-3333-333333333333",
  "provider": "nebius",
  "model": "nvidia/Nemotron-3_5-Lightning",
  "prompt_version": "evida-investigation-v1",
  "hypothesis": "The divide function in src/calculator.py multiplies its operands instead of dividing them.",
  "confidence": 0.99,
  "root_cause": {
    "file": "src/calculator.py",
    "symbol": "divide",
    "line": 2,
    "description": "The implementation uses the multiplication operator (*) instead of the division operator (/)."
  },
  "affected_files": ["src/calculator.py"],
  "evidence": [
    "The reproduction test expects 5 but the function returns 20.",
    "The reproduction command 'pytest tests/test_bug.py' exited with code 1."
  ],
  "recommended_next_action": "generate_regression_test"
}
```

### 3. Execute Deterministic Double Validation (Phase 6)
```bash
curl -X POST http://localhost:8000/api/v1/investigations/{id}/verify-patch
```

**Example Verification Response:**
```json
{
  "id": "66666666-6666-6666-6666-666666666666",
  "investigation_id": "33333333-3333-3333-3333-333333333333",
  "status": "VERIFIED",
  "verdict": "VERIFIED",
  "failure_classification": null,
  "patch_application": {
    "status": "APPLIED",
    "exit_code": 0,
    "duration_ms": 12.5,
    "modified_files": ["src/calculator.py"]
  },
  "regression_execution": {
    "status": "PASSED",
    "command": "pytest tests/test_regression.py",
    "exit_code": 0,
    "duration_ms": 82.5
  },
  "baseline_execution": {
    "status": "PASSED",
    "command": "pytest",
    "exit_code": 0,
    "duration_ms": 91.0
  },
  "source_integrity_verified": true
}
```

> **The Double Validation Rule:** An AI-proposed patch is **VERIFIED** only when both the proven regression test passes and the existing baseline test suite passes inside an ephemeral sandbox, while the original repository archive remains cryptographically untouched (`sha_before == sha_after`). If any condition fails, the verdict is deterministically **UNVERIFIED**.

---

## Database Migrations (Supabase)

To apply migrations to your local or hosted Supabase project:

```bash
# Link your Supabase project (if using hosted)
supabase link --project-ref your-project-ref

# Apply pending migrations
supabase db push
```

The initial migration `20261027000000_initial_schema.sql` establishes:
- Tables: `profiles`, `projects`, `repositories`, `investigations`.
- UUID primary keys and automated `updated_at` triggers.
- Strict Row Level Security (RLS) policies enforcing tenant ownership.

---

## License

MIT © 2026 EVIDA Contributors.
