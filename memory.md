# EVIDA — Project Memory & Implementation Ledger
## Current Status
- **Phase:** Phase 5 — Patch Generation & Candidate Validation
- **Status:** COMPLETED & VERIFIED
- **Last Updated:** 2026-10-28

---

## Current Objective
Phase 5 patch generation and candidate validation engine is fully implemented, verified, and committed. Standing by for Phase 6 (Deterministic Patch Verification & Double Validation).

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
- [x] **REST API Endpoints:** `POST /api/v1/investigations/{id}/investigate`, `GET /api/v1/investigations/{id}/hypothesis`.
- [x] **Mock AI Provider:** Updated `MockAIProvider` to return structured Phase 3 JSON output without requiring external internet or API keys during testing.
- [x] **Frontend Integration (`apps/web/app/investigations/[id]/page.tsx`):** Renders AI Investigation card with `INVESTIGATING` status, "Proposed Root Cause" badge, model/provider tags, hypothesis text, confidence score, root cause candidate details, affected files, grounding evidence list, and recommended next action.

### Phase 4 — Regression Test Generation & Verification
- [x] **Database Migration (`supabase/migrations/20261027040000_regression_tests.sql`):** Created `investigation_regression_tests` and `regression_verification_runs` with cascading foreign keys, compound indexes `(investigation_id, created_at DESC)`, and strict RLS tenant policies.
- [x] **Structured AI Regression Contract (`RegressionTestProposal`):** Strict Pydantic v2 model validating `test_path`, `framework` (pytest), `language` (python), `description`, `test_content`, `target_symbol`, `target_file`, `expected_failure_reason`.
- [x] **Deterministic AST & Path Validator (`apps/api/app/domain/investigations/test_validator.py`):** Path traversal checks, AST parsing with `ast.parse`, disallowed module/call checks (`subprocess`, `os.system`, `socket`, `eval`, `exec`), pytest structure check, size bound (`MAX_GENERATED_TEST_BYTES`).
- [x] **Isolated Verification Workspace:** Extracts original unpatched repository archive into isolated workspace without modifying production source code.
- [x] **Deterministic Sandbox Execution & Objective Verdict Classifier (`apps/api/app/domain/investigations/verdict_classifier.py`):** Distinguishes assertion failures (`REGRESSION_PROVEN`) from execution errors (`EXECUTION_ERROR`), passing tests (`TEST_REJECTED`), timeouts (`TIMEOUT`), and policy violations (`POLICY_BLOCKED`).
- [x] **Lifecycle Transition:** Transitions `INVESTIGATING` -> `VERIFYING` upon `REGRESSION_PROVEN`. Never transitions to `COMPLETED`.
- [x] **REST API Endpoints:** `POST /api/v1/investigations/{id}/regression-test`, `GET /api/v1/investigations/{id}/regression-test`.
- [x] **Frontend Integration (`apps/web/app/investigations/[id]/page.tsx`):** Renders dual panels AI Proposed Regression Test vs Deterministic Verification evidence.

### Phase 5 — Patch Generation & Candidate Validation
- [x] **Database Migration (`supabase/migrations/20261027050000_patch_candidates.sql`):** Created `patch_candidates` table with compound indexes `(investigation_id, created_at DESC)`, `(regression_test_id)`, `(hypothesis_id)` and strict tenant RLS derived through `investigation -> project -> auth.uid()`.
- [x] **Domain Models & Pydantic Contracts (`apps/api/app/domain/patches/models.py`):** Strongly typed `PatchProposal`, `PatchCandidateStatus` (`GENERATED`, `VALIDATED`, `REJECTED`), `PatchValidationClassification`, `ChangeSummaryItem`, and `PatchCandidateRecord`.
- [x] **Bounded Configuration:** Added `MAX_GENERATED_PATCH_BYTES` (50,000), `MAX_PATCH_FILES` (5), `MAX_PATCH_HUNKS` (20), `PATCH_GENERATION_PROMPT_VERSION` (`"evida-patch-generation-v1"`).
- [x] **Deterministic Unified Diff Parser (`apps/api/app/domain/patches/patch_validator.py`):** Extracts `--- a/path` and `+++ b/path` headers, counts hunks, cross-references actual diff targets with declared `changed_files`.
- [x] **Patch Security & Safety Validator:**
  - Traversal & absolute path blocking (`..`, `/`).
  - Test suite immutability enforcement: rejects edits targeting `tests/` or regression tests (`TEST_MODIFICATION`).
  - Sensitive files shield: rejects edits targeting `.env*`, `*.pem`, `*.key`, `credentials.json`, `Dockerfile` (`SENSITIVE_FILE_MODIFICATION`).
  - Dangerous pattern inspection: blocks `subprocess`, `os.system`, `socket`, `eval`, `exec` in diff additions (`SECURITY_VIOLATION`).
  - Scope boundary check: changed files must exist in original repository and remain within confirmed hypothesis `affected_files` (`OUT_OF_SCOPE_CHANGE`).
- [x] **Source Repository Immutability:** ZERO filesystem mutation (no `git apply`, no rewriting). Original archive SHA-256 confirmed identical before and after patch generation.
- [x] **Patch Service (`apps/api/app/domain/patches/patch_service.py`):** Orchestrates preconditions (`VERIFYING`, `REPRODUCED`, hypothesis exists, regression proven), idempotency, context building, model synthesis, validation, audit events, and persistence.
- [x] **REST API Endpoints:**
  - `POST /api/v1/investigations/{id}/patch`: Generates and validates patch candidate.
  - `GET /api/v1/investigations/{id}/patch`: Retrieves latest patch candidate.
- [x] **Audit Trail Integration:** Emits `PATCH_GENERATION_STARTED`, `PATCH_GENERATED`, `PATCH_VALIDATED`, `PATCH_REJECTED`.
- [x] **Frontend UI (`apps/web/app/investigations/[id]/page.tsx`):** Renders Patch Candidate section with AI Proposal vs Deterministic Evidence, monospace highlighted unified diff, validation checklist, and prominent `NOT VERIFIED` invariant banner.
- [x] **Automated Validation:** 188 backend tests passing, 4 frontend tests passing, Ruff lint/format clean, Mypy strict clean, Next build clean, sandbox execution verified.

---

## Next Steps
- Await instruction to start **Phase 6 — Deterministic Patch Verification & Double Validation**.
- Do not begin Phase 6 until instructed.

---

## Known Issues & Notes
- Untrusted repository code never executes inside the FastAPI process; all execution occurs via the ephemeral sandbox runner.
- Live Nebius API calls require an active `NEBIUS_API_KEY`; AI models are intentionally not called in Phase 2 to maintain deterministic reproduction proofs.
