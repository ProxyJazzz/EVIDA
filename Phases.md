# EVIDA — Multi-Phase Development Roadmap

```text
Phase 0: Project Setup & Architecture Foundation (Current)
   │
   ▼
Phase 1: EVIDA Core Backend & Investigation Lifecycle
   │
   ▼
Phase 2: Repository Ingestion & Failure Reproduction
   │
   ▼
Phase 3: AI Investigation & Hypothesis Engine (Nebius + NVIDIA)
   │
   ▼
Phase 4: Regression Test Synthesis & Deterministic Verification
   │
   ▼
Phase 5: Candidate Patch Synthesis & Double Verification
   │
   ▼
Phase 6: Web Dashboard, Evidence Visualizer & Human Review
   │
   ▼
Phase 7: End-to-End Evaluation & Hardening
```

---

## Phase Details

### Phase 0 — Project Setup & Architecture Foundation (Completed)
- Initialize monorepo (`apps/web`, `apps/api`, `packages/shared`, `sandbox`, `supabase`).
- Configure FastAPI with Pydantic v2, structured logging, health/readiness endpoints.
- Establish `AIProvider` abstraction with `NebiusAIProvider` and `MockAIProvider`.
- Configure NVIDIA open models via `NEBIUS_MODEL`.
- Build the isolated sandbox execution harness with hard timeouts.
- Set up Supabase migrations with initial tables (`profiles`, `projects`, `repositories`, `investigations`) and RLS.
- Set up Next.js frontend with visual identity and health checks.
- Establish unit, integration, and sandbox test suites.

### Phase 1 — EVIDA Core Backend & Investigation Lifecycle (Completed)
- Deterministic lifecycle state machine (`CREATED` -> `INGESTING` -> `REPRODUCING` -> `INVESTIGATING` -> `VERIFYING` -> `COMPLETED`, terminal `FAILED`).
- Strict transition validation with deterministic structured error envelopes (`INVALID_STATE_TRANSITION`, `INVESTIGATION_ALREADY_TERMINAL`, `INVESTIGATION_NOT_FOUND`).
- Idempotent investigation start endpoint (`POST /api/v1/investigations/{id}/start`).
- Investigation creation (`POST /api/v1/investigations`), retrieval (`GET /api/v1/investigations/{id}`), and listing (`GET /api/v1/investigations`).
- Append-only event timeline (`GET /api/v1/investigations/{id}/events`) with `investigation_events` Supabase schema migration and RLS.
- Transaction-consistent persistence abstraction supporting offline testing and local development.
- Comprehensive test coverage across state transitions, idempotency, event generation, and API lifecycle.

### Phase 2 — Repository Ingestion & Failure Reproduction (Completed)
- Secure ZIP repository ingestion with defense-in-depth archive validation.
- Path traversal and absolute path blocking (zero blind `extractall()`).
- Archive size, extracted size, single-file size, and file count limits in configuration.
- SHA-256 digest generation and persistence for artifact provenance.
- Deterministic repository root detection (handling nested package roots and flat roots).
- Untrusted reproduction command validation (no `shell=True`, metacharacter blocking, whitelist for `pytest`/`python`).
- Ephemeral workspace extraction and isolated execution boundary via `sandbox/runner/runner.py`.
- Objective reproduction verdict classification (`REPRODUCED`, `NOT_REPRODUCED`, `TIMEOUT`, `EXECUTION_ERROR`, `POLICY_BLOCKED`).
- Idempotent execution and append-only evidence persistence in `reproduction_runs` with Supabase migration and RLS.
- Investigation state integration: transitions from `CREATED` -> `INGESTING` -> `REPRODUCING`.
- Standard REST API endpoints:
  - `POST /api/v1/investigations/{id}/repository`
  - `GET /api/v1/investigations/{id}/repository`
  - `POST /api/v1/investigations/{id}/reproduce`
  - `GET /api/v1/investigations/{id}/reproduction`
- Minimal frontend UI displaying repository metadata, reproduction execution evidence, stdout/stderr, and lifecycle timeline.
- Comprehensive unit and integration test suite with deterministic broken and passing repo fixtures.

### Phase 3 — AI Investigation & Hypothesis Engine
- Investigation prompt templates with AST extraction and failure log summarization.
- Integration with Nebius Token Factory using NVIDIA Nemotron models.
- Structured causal hypothesis extraction with verifiable claims.

### Phase 4 — Regression Test Synthesis & Deterministic Verification
- Generation of standalone regression tests reproducing the defect.
- Sandbox execution proving the regression test fails on unpatched code (negative proof).

### Phase 5 — Candidate Patch Synthesis & Double Verification
- Synthesis of minimal unified diff patches.
- Sandbox patch application (`git apply` or diff patcher).
- Double verification: regression test passes AND full baseline test suite remains green.
- Evidence collection: logs, CPU/wall time, SHA256 of patched artifacts.

### Phase 6 — Web Dashboard, Evidence Visualizer & Human Review
- Next.js interactive timeline for investigation steps.
- Side-by-side patch diff view with test output evidence.
- Verified vs Unverified audit badge and download of cryptographic audit evidence bundle.

### Phase 7 — End-to-End Evaluation & Hardening
- SWE-bench or custom benchmark evaluation.
- Rate limiting, audit logging, and sandbox hardening.
- Production deployment configuration.
