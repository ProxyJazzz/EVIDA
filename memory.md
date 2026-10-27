# EVIDA — Project Memory & Implementation Ledger

## Current Status
- **Phase:** Phase 4 — Regression Test Generation & Verification
- **Status:** COMPLETED & VERIFIED
- **Last Updated:** 2026-10-28

---

## Current Objective
Phase 4 regression test generation and deterministic verification engine is fully implemented and verified. Standing by for Phase 5 (Candidate Patch Synthesis & Double Verification).

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

### Phase 3 — AI Investigation & Hypothesis Engine
- [x] **Database Migration (`supabase/migrations/20261027030000_investigation_hypotheses.sql`):** Created `investigation_hypotheses` table with compound index `(investigation_id, created_at DESC)`, foreign keys with cascading delete, and RLS policies derived through investigation ownership (no open `USING (true)`).
- [x] **Context Builder (`apps/api/app/domain/investigations/context_builder.py`):** Deterministic heuristics inspecting workspace files; sensitive file filtering (`.env*`, `*.pem`, `*.key`, `credentials.json`, `service-account.json`); binary filtering; ignored directory exclusion (`.git`, `__pycache__`, `venv`, etc.); priority heuristic ordering (traceback matches > test files > package source files).
- [x] **Deterministic Stack Trace Hints:** Extracts source file paths, line numbers, and function symbols from Python tracebacks and pytest failure lines (`FAILED tests/test_bug.py::test_divide_bug`).
- [x] **Bounded Context Guardrails (`apps/api/app/core/config.py`):** Centralized limits: `MAX_CONTEXT_FILES` (20), `MAX_CONTEXT_BYTES` (100KB), `MAX_FILE_BYTES` (20KB), `MAX_TREE_ENTRIES` (500), `MAX_STDOUT_CONTEXT_BYTES` (20KB), `MAX_STDERR_CONTEXT_BYTES` (20KB).
- [x] **Structured Investigation Prompt (`apps/api/app/ai/prompts.py`):** Centralized system and user prompt templates with versioning tag `evida-investigation-v1` adhering to the core invariant: AI proposes, does NOT modify code, does NOT declare bugs fixed.
- [x] **Strict Pydantic Validation (`InvestigationHypothesis`):** Validates causal hypothesis, confidence `[0.0, 1.0]`, structured `RootCauseCandidate` (`file`, `symbol`, `line`, `description`), affected files list, grounding evidence list, and recommended next action.
- [x] **AI Investigation Service (`apps/api/app/domain/investigations/ai_service.py`):** Orchestrates precondition checks (requires `REPRODUCED`), context extraction, prompt construction, single-retry error handling for transient AI provider failures, markdown code-fence JSON extraction, schema validation, persistence, and transition `REPRODUCING` -> `INVESTIGATING`.
- [x] **REST API Endpoints:**
  - `POST /api/v1/investigations/{id}/investigate`: Starts AI investigation (idempotent, returns existing hypothesis if already generated).
  - `GET /api/v1/investigations/{id}/hypothesis`: Retrieves the latest structured causal hypothesis.
- [x] **Mock AI Provider:** Updated `MockAIProvider` to return structured Phase 3 JSON output without requiring external internet or API keys during testing.
- [x] **Frontend Integration (`apps/web/app/investigations/[id]/page.tsx`):** Renders AI Investigation card with `INVESTIGATING` status, "Proposed Root Cause" badge (never "Verified Root Cause"), model/provider tags, hypothesis text, confidence score, root cause candidate details, affected files, grounding evidence list, and recommended next action.
- [x] **Automated Validation:** 114 backend tests passing, 4 frontend tests passing, Ruff lint/formatting clean, Mypy strict type checking clean, sandbox validation passing.

### Phase 4 — Regression Test Generation & Verification
- [x] **Database Migration (`supabase/migrations/20261027040000_regression_tests.sql`):** Created `investigation_regression_tests` and `regression_verification_runs` with cascading foreign keys, compound indexes `(investigation_id, created_at DESC)`, and strict RLS tenant policies derived from project/investigation ownership.
- [x] **Structured AI Regression Contract (`RegressionTestProposal`):** Strict Pydantic v2 model validating `test_path`, `framework` (pytest), `language` (python), `description`, `test_content`, `target_symbol`, `target_file`, `expected_failure_reason`.
- [x] **Deterministic AST & Path Validator (`apps/api/app/domain/investigations/test_validator.py`):**
  - Path traversal checks: must be relative, inside `tests/test_*.py`, no `..`, no leading `/`.
  - Python AST parsing with `ast.parse`.
  - Disallowed module and attribute checks: blocks `subprocess`, `os.system`, `os.popen`, `socket`, `requests`, `urllib`, `eval`, `exec`, `__import__`, `shutil.rmtree`, write-mode `open`.
  - Structural validation: verifies presence of at least one test function (`test_*`).
  - Size boundary: capped at `MAX_GENERATED_TEST_BYTES` (20,000 bytes).
- [x] **Isolated Verification Workspace:**
  - Extracts original unpatched repository archive into an isolated temporary workspace.
  - Injects the generated regression test file without applying any patch or source code changes.
  - Zero modification to production source files: validates negative reproduction proof.
- [x] **Deterministic Sandbox Execution & Objective Verdict Classifier (`apps/api/app/domain/investigations/verdict_classifier.py`):**
  - Distinguishes test assertion failures (`REGRESSION_PROVEN`, `ASSERTION_FAILURE`) from test execution errors (`EXECUTION_ERROR`, `TEST_EXECUTION_ERROR` due to `ImportError`, syntax error, collection failure).
  - Classifies passing tests against buggy repo as `TEST_REJECTED` (`PASSING`).
  - Classifies timeouts as `TIMEOUT` (never proven).
  - Classifies policy violations as `POLICY_BLOCKED`.
- [x] **Append-Only Evidence Persistence & Audit Trail:**
  - Persists generated tests and append-only verification runs.
  - Emits audit timeline events: `REGRESSION_TEST_GENERATED`, `REGRESSION_TEST_VERIFICATION_STARTED`, `REGRESSION_TEST_VERIFICATION_COMPLETED`, `REGRESSION_TEST_PROVEN`, `REGRESSION_TEST_REJECTED`.
- [x] **Lifecycle Transition:**
  - Transitions investigation `INVESTIGATING` -> `VERIFYING` only upon `REGRESSION_PROVEN`.
  - Never transitions to `COMPLETED` (Phase 4 establishes defect capture, not bug repair).
- [x] **REST API Endpoints:**
  - `POST /api/v1/investigations/{id}/regression-test`: Generates and verifies regression test (idempotent for existing proven tests).
  - `GET /api/v1/investigations/{id}/regression-test`: Retrieves regression test and latest verification run evidence.
- [x] **Frontend Integration (`apps/web/app/investigations/[id]/page.tsx`):**
  - Displays dual panels: "AI PROPOSED REGRESSION TEST" (untrusted proposal) vs "DETERMINISTIC VERIFICATION" (objective sandbox evidence).
  - Shows verdict badge `REGRESSION PROVEN` / `TEST REJECTED` / `VERIFICATION ERROR`.
  - Explicit invariant warning: "REGRESSION_PROVEN ≠ BUG_FIXED. Ready for Phase 5 patch generation."
- [x] **Automated Validation:** 159 backend tests passing, 4 frontend tests passing, Ruff clean, Mypy strict clean, Next build clean, sandbox execution verified.

---

## Next Steps
- Await instruction to start **Phase 5 — Candidate Patch Synthesis & Double Verification**.
- Do not begin Phase 5 until instructed.

---

## Known Issues & Notes
- Untrusted repository code never executes inside the FastAPI process; all execution occurs via the ephemeral sandbox runner.
- Live Nebius API calls require an active `NEBIUS_API_KEY`; AI models are intentionally not called in Phase 2 to maintain deterministic reproduction proofs.
