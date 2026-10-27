# EVIDA — Project Memory & Implementation Ledger

## Current Status
- **Phase:** Phase 2 — Repository Ingestion & Failure Reproduction
- **Status:** COMPLETED & VERIFIED
- **Last Updated:** 2026-10-27

---

## Current Objective
Phase 2 repository ingestion and failure reproduction pipeline is fully implemented and verified. Standing by for Phase 3 (AI Investigation & Hypothesis Engine).

---

## Completed

### Phase 0 — Foundation
- [x] Initialized Git repository with clean `.gitignore`, `.editorconfig`, `.env.example`, and `LICENSE` (MIT).
- [x] Authored core architecture docs: `PRD.md`, `Architecture.md`, `Rules.md`, `Phases.md`, `Design.md`, and `docs/` (`DATABASE.md`, `API.md`, `SECURITY.md`, `DEPLOYMENT.md`).
- [x] Implemented Next.js App Router frontend (`apps/web`) with visual design, `/` landing page, `/health`, `/login`, and `/dashboard`.
- [x] Implemented FastAPI backend (`apps/api`) with Pydantic v2, structured logging, credential scrubbing, standardized error envelopes, `/api/v1/health` and `/api/v1/health/ready` endpoints.
- [x] Implemented AI provider abstraction (`apps/api/app/ai/`) with `NebiusAIProvider`, `MockAIProvider`, and configurable NVIDIA open model (`NEBIUS_MODEL`).
- [x] Implemented isolated sandbox runner (`sandbox/runner/runner.py`) with hard timeouts, memory limit policies, and controlled execution.
- [x] Authored Supabase initial schema migration (`supabase/migrations/20261027000000_initial_schema.sql`) and `seed.sql` with UUID keys, updated_at triggers, and strict RLS tenant isolation.

### Phase 1 — Core Lifecycle & State Machine
- [x] **State Machine (`apps/api/app/domain/investigations/state_machine.py`):** Canonical transitions (`CREATED` -> `INGESTING` -> `REPRODUCING` -> `INVESTIGATING` -> `VERIFYING` -> `COMPLETED`, terminal `FAILED`).
- [x] **Transition Validation & Error Codes:** Deterministic error envelopes with codes `INVALID_STATE_TRANSITION`, `INVESTIGATION_ALREADY_TERMINAL`, `INVESTIGATION_NOT_FOUND`, `INVALID_INVESTIGATION_REQUEST`, `INVESTIGATION_PERSISTENCE_ERROR`.
- [x] **Idempotent Start Endpoint (`POST /api/v1/investigations/{id}/start`):** Begins lifecycle; repeated calls safely return current state without re-triggering transitions or corrupting state.
- [x] **Investigation CRUD:** Creation (`POST /api/v1/investigations`), retrieval (`GET /api/v1/investigations/{id}`), and tenant listing (`GET /api/v1/investigations`).
- [x] **Chronological Event Timeline (`GET /api/v1/investigations/{id}/events`):** Ordered event history emitted on creation and state transitions.
- [x] **Database Migration (`supabase/migrations/20261027010000_investigation_events.sql`):** Added `investigation_events` table with index `(investigation_id, created_at ASC)` and RLS policies; updated `investigations` status constraints.
- [x] **Persistence Abstraction:** Protocol-based repository with transaction-consistent in-memory storage for offline development/testing and Supabase integration.

### Phase 2 — Repository Ingestion & Failure Reproduction
- [x] **Database Migration (`supabase/migrations/20261027020000_repository_and_reproduction.sql`):** Added Phase 2 fields to `repositories` (`investigation_id`, `storage_path`, `archive_size_bytes`, `archive_sha256`, `status`) and created `reproduction_runs` table with foreign keys, compound indexes, and RLS policies (no open `USING (true)`).
- [x] **ZIP Security & Archive Validation (`apps/api/app/domain/repositories/archive_validator.py`):** Rejects path traversals (`..`), absolute paths (`/`), symlink escaping, oversized archives, file counts exceeding boundary; computes deterministic SHA-256 digest; extracts safely without blind `extractall()`.
- [x] **Deterministic Root Detection:** Detects repository root for both nested package directories and flat layouts.
- [x] **Reproduction Command Validation (`apps/api/app/domain/repositories/command_validator.py`):** Blocks shell metacharacters (`;`, `&`, `|`, `` ` ``, `$`, `(`, `)`, `<`, `>`, `{`, `}`), non-whitelisted executables (`rm`, `bash`, `curl`, `wget`), and arbitrary inline python (`-c`).
- [x] **Isolated Sandbox Execution (`apps/api/app/domain/repositories/reproduction_service.py` & `sandbox/runner/runner.py`):** Ephemeral workspace creation and teardown; secret environment scrubbing; hard timeouts (30s); output truncation; exit code and duration capture.
- [x] **Objective Reproduction Verdict Semantics:** `exit_code > 0` => `REPRODUCED`; `exit_code == 0` => `NOT_REPRODUCED`; timeout => `TIMEOUT`; sandbox error => `EXECUTION_ERROR`; disallowed command => `POLICY_BLOCKED`.
- [x] **Investigation Lifecycle Integration:** Ingestion moves `CREATED` -> `INGESTING`; reproduction start moves `INGESTING` -> `REPRODUCING`; lifecycle stops at `REPRODUCING` for Phase 2.
- [x] **Idempotency:** Repeated reproduction requests return the existing run without duplicate execution unless explicitly forced.
- [x] **REST API Endpoints:** `POST /{id}/repository`, `GET /{id}/repository`, `POST /{id}/reproduce`, `GET /{id}/reproduction`.
- [x] **Frontend Integration:** Added investigation detail view (`apps/web/app/investigations/[id]/page.tsx`) rendering repository metadata, reproduction execution evidence, stdout/stderr blocks, and lifecycle timeline.
- [x] **Automated Validation:** 96 backend tests passing, 4 frontend tests passing, Ruff lint/format clean, Mypy strict type checking clean, sandbox validation passing.

---

## Next Steps
- Await instruction to start **Phase 3 — AI Investigation & Hypothesis Engine (Nebius + NVIDIA)**.
- Do not begin Phase 3 until instructed.

---

## Known Issues & Notes
- Untrusted repository code never executes inside the FastAPI process; all execution occurs via the ephemeral sandbox runner.
- Live Nebius API calls require an active `NEBIUS_API_KEY`; AI models are intentionally not called in Phase 2 to maintain deterministic reproduction proofs.
