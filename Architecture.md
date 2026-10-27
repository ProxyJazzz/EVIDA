# EVIDA — Canonical System Architecture

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

## 1. System Components & Responsibilities

### 1.1 Web Frontend (`apps/web`)
- **Technology:** Next.js (App Router), React, TypeScript, Tailwind CSS, Lucide Icons.
- **Responsibilities:**
  - User interface, investigation status visualization, patch diff review.
  - Client-side authentication via `@supabase/ssr` / `@supabase/supabase-js`.
  - Secure communication with the FastAPI backend.
  - Zero access to the Supabase `service_role` key; communicates with Supabase strictly using public anonymous credentials or through the backend.

### 1.2 Application Backend (`apps/api`)
- **Technology:** Python 3.12+, FastAPI, Pydantic v2, `pydantic-settings`, Uvicorn, HTTPX.
- **Responsibilities:**
  - Business domain orchestration (investigations, hypotheses, patches, verification results).
  - Authorization enforcement and tenant security.
  - AI orchestration via `AIProvider` abstractions (calling Nebius Token Factory).
  - Sandbox job dispatching and verification coordination.
  - Persistence coordination with Supabase PostgreSQL.

### 1.3 Database & Storage (`Supabase`)
- **Technology:** Supabase PostgreSQL with Row Level Security (RLS).
- **Responsibilities:**
  - Central source of persistent truth for users, projects, repositories, and investigation lifecycle.
  - Defense-in-depth security via RLS policies (`auth.uid() = user_id`).
  - Automated timestamp management and UUID primary key generation.
  - **Critical boundary:** Supabase is NOT a replacement for FastAPI; FastAPI coordinates business workflows.

### 1.4 AI Inference (`Nebius Token Factory` with NVIDIA Open Models)
- **Technology:** Nebius Token Factory OpenAI-compatible API (`https://api.tokenfactory.nebius.com/v1`).
- **Models:** Configurable NVIDIA models (e.g., `nvidia/Nemotron-3_5-Lightning`).
- **Responsibilities:**
  - Bug report triage and causal investigation.
  - Hypothesis formulation and regression test code synthesis.
  - Candidate patch generation.
  - Output is strictly treated as **untrusted proposal data** requiring deterministic verification.

### 1.5 Execution Sandbox (`sandbox/`)
- **Technology:** Isolated Docker container and Python runner harness (`sandbox/runner/runner.py`).
- **Responsibilities:**
  - Safe reproduction of failures without risking the host system.
  - Execution of test suites before and after candidate patches.
  - Enforcement of CPU, memory, and wall-clock execution limits.
  - Strict network and volume isolation: never mounts host secrets, Docker socket, or project root.

---

## 2. Trust Boundaries & Security Model

```text
[ Browser / Public Client ]  (Untrusted)
        │
        │ Bearer Token / HTTPS
        ▼
[ FastAPI Application ]     (Trusted Application Authority)
   ├── Enforces Auth & Policy
   ├── Coordinates DB Queries via Service Role
   └── Never leaks Service Role to Client
        │
   ┌────┴──────────────────────────┐
   ▼                               ▼
[ Nebius AI Provider ]     [ Execution Sandbox ]
(Untrusted Output Source)   (Isolated Execution Boundary)
* Schema Validation         * No Host Mounts
* Deterministic Rejection   * Strict Timeouts & Resource Caps
```

---

## 3. Data Flow

1. **Investigation Request:** User submits repository reference and issue description via Web UI to FastAPI backend.
2. **Persistence:** Backend writes `PENDING` investigation record to Supabase.
3. **Reproduction in Sandbox:** Sandbox runs existing test suite or repro script to confirm initial failure state.
4. **AI Reasoning:** Backend prompts Nebius Token Factory (NVIDIA model) with structured reproduction evidence to produce a causal hypothesis and regression test candidate.
5. **Verification of Regression Test:** Sandbox executes regression test against baseline code; it *must* fail (negative proof).
6. **Patch Synthesis:** Nebius generates candidate code patch.
7. **Verification of Patch:** Sandbox applies patch and executes:
   - Regression test (must now PASS).
   - Full repository test suite (must remain PASS).
8. **Evidence Bundle:** Execution outputs, diffs, timing, and exit codes are recorded in Supabase.
9. **Review UI:** User reviews the verified evidence trail and marks the fix `VERIFIED`.
