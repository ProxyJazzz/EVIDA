# EVIDA — Project Memory & Implementation Ledger
## Current Status
- **Phase:** Phase 8 — Production Hardening, Deployment & Hackathon Readiness
- **Status:** COMPLETED & VERIFIED
- **Last Updated:** 2026-10-28

---

## Current Objective
Phase 8 Production Hardening, Deployment & Hackathon Readiness is complete. EVIDA is fully tested across all 8 phases, hardened for public demonstration, and prepared for final GitHub and video submission.

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

### Phase 6 — Deterministic Patch Verification & Double Validation
- [x] **Database Migration (`supabase/migrations/20261027060000_patch_verification_runs.sql`):** Added `patch_verification_runs` table with compound indexes `(investigation_id, created_at DESC)`, `(patch_candidate_id)`, `(regression_test_id)`, and strict tenant RLS derived through `investigation -> project -> auth.uid()`.
- [x] **Domain Models & Pydantic Contracts (`apps/api/app/domain/verification/models.py`):** Strongly typed `PatchVerificationStatus`, `PatchVerificationVerdict` (`VERIFIED`, `UNVERIFIED`), `VerificationFailureClassification`, `PatchApplicationResult`, `VerificationTestResponse`, `PatchVerificationResponse`.
- [x] **Bounded Configuration (`apps/api/app/core/config.py`):** Centralized limits: `PATCH_APPLICATION_TIMEOUT_SECONDS` (30.0), `REGRESSION_VERIFICATION_TIMEOUT_SECONDS` (30.0), `BASELINE_VERIFICATION_TIMEOUT_SECONDS` (60.0), `MAX_VERIFICATION_OUTPUT_BYTES` (50,000), `MAX_VERIFICATION_WORKSPACE_BYTES` (50,000,000), `MAX_VERIFICATION_FILES` (1000).
- [x] **Patch Applier Engine (`apps/api/app/domain/verification/patch_applier.py`):** Pure-Python hunk engine with line-based context verification and `git apply` fallback; path traversal detection; sensitive path shield; workspace file count and total size limit enforcement; file manifest pre/post calculation; test immutability enforcement.
- [x] **Deterministic Verdict Classifier (`apps/api/app/domain/verification/verdict_classifier.py`):** Explicit deterministic taxonomy (`VERIFIED`, `PATCH_APPLICATION_FAILED`, `PATCH_APPLICATION_TIMEOUT`, `PATCH_APPLICATION_POLICY_BLOCKED`, `REGRESSION_STILL_FAILING`, `REGRESSION_EXECUTION_ERROR`, `REGRESSION_TIMEOUT`, `REGRESSION_POLICY_BLOCKED`, `BASELINE_TEST_FAILURE`, `BASELINE_EXECUTION_ERROR`, `BASELINE_TIMEOUT`, `BASELINE_POLICY_BLOCKED`, `SOURCE_INTEGRITY_VIOLATION`, `UNEXPECTED_WORKSPACE_CHANGE`).
- [x] **Double Validation Orchestrator (`apps/api/app/domain/verification/patch_verification_service.py`):**
  - All 12 preconditions checked (`INVESTIGATION_PRECONDITION_FAILED`).
  - Tenant boundary isolation enforced.
  - Validation 1: Runs proven regression test against patched code -> MUST PASS (exit 0).
  - Validation 2: Runs repository baseline test suite -> MUST PASS (exit 0).
  - Source integrity check: Cryptographic SHA-256 pre == post verification of stored repository artifact.
  - Zero AI discretion: Final verdict is 100% deterministic execution evidence.
- [x] **Lifecycle Transition:** Transitions `VERIFYING` -> `COMPLETED` exclusively upon successful double validation. Failed verification leaves status in `VERIFYING` for continued review.
- [x] **Idempotency:** Repeated calls return existing verified record without re-executing sandbox runs.
- [x] **REST API Endpoints:**
  - `POST /api/v1/investigations/{id}/verify-patch`: Executes double validation on candidate patch.
  - `GET /api/v1/investigations/{id}/verification`: Retrieves latest verification run evidence.
  - `GET /api/v1/investigations/{id}/verifications`: Retrieves list of historical verification runs.
- [x] **Frontend Integration (`apps/web/app/investigations/[id]/page.tsx`):** Renders dedicated Phase 6 card with 3-step validation grid (Patch Application, Original Regression, Existing Test Suite), source integrity guarantee row, stdout terminals, and 9-step Evidence Chain Visualizer clearly differentiating AI PROPOSAL from DETERMINISTIC EVIDENCE.
- [x] **Automated Validation:** 224 backend tests passing (unit, integration, state machine, sandbox), 4 frontend tests passing, Ruff lint/format clean, Mypy strict clean, Next build clean, sandbox execution verified.

### Phase 7 — Evidence Bundle, Provenance & Audit System
- [x] **Core Principle Enforced:**
  - `AI_OUTPUT -> PROPOSAL` (never evidence)
  - `DETERMINISTIC_EXECUTION -> EVIDENCE`
  - `EVIDENCE -> VERDICT`
- [x] **Database Migration (`supabase/migrations/20261027070000_evidence_bundle.sql`):** Added append-only `investigation_evidence` table with compound indexes `(investigation_id, created_at DESC)`, `(investigation_id, evidence_type)`, and `(source_entity_type, source_entity_id)` with strict tenant RLS (`FOR SELECT` and `FOR INSERT` only; no `UPDATE` or `DELETE` policies, guaranteeing append-only immutability).
- [x] **Domain Models & Pydantic Contracts (`apps/api/app/domain/evidence/models.py`):**
  - Strongly typed `EvidenceProvenance` (`AI_PROPOSAL`, `DETERMINISTIC_EXECUTION`, `CRYPTOGRAPHIC_INTEGRITY`, `SYSTEM_METADATA`, `AUDIT_EVENT`).
  - Strongly typed `EvidenceType` (14 types: `INCIDENT`, `REPOSITORY`, `REPRODUCTION`, `HYPOTHESIS`, `REGRESSION_TEST`, `REGRESSION_PROOF`, `PATCH_PROPOSAL`, `PATCH_VALIDATION`, `PATCH_APPLICATION`, `REGRESSION_VERIFICATION`, `BASELINE_VERIFICATION`, `SOURCE_INTEGRITY`, `FINAL_VERDICT`, `AUDIT`).
  - `EvidenceItem`, `EvidenceBundle`, and `EvidenceHashResponse`.
  - Deterministic SHA-256 canonical JSON computation (`compute_content_sha256` and `compute_bundle_sha256`).
  - Multi-layered secret scrubbing (`scrub_secrets` and `sanitize_dict_secrets`) for bearer tokens, JWTs, API keys, and sensitive environment variables.
- [x] **Domain Service (`apps/api/app/domain/evidence/evidence_service.py`):**
  - Aggregates evidence across all 13 stages from Phases 1–6 into a coherent audit chain.
  - Zero AI calls during bundle generation (100% deterministic persistence retrieval).
  - Explicit provenance labeling: AI hypotheses, regression test proposals, and patch proposals are tagged strictly as untrusted `AI_PROPOSAL`.
  - Computes global cryptographic `bundle_sha256`.
  - Multi-tenant tenant boundary checks with `INVESTIGATION_PRECONDITION_FAILED` / 403 on tenant mismatch.
  - Audit trail integration: emits `EVIDENCE_BUNDLE_GENERATED` and `EVIDENCE_BUNDLE_EXPORTED`.
- [x] **REST API Endpoints:**
  - `GET /api/v1/investigations/{id}/evidence`: Retrieves complete structured `EvidenceBundle`.
  - `GET /api/v1/investigations/{id}/evidence/items`: Retrieves chronological list of `EvidenceItem` records.
  - `GET /api/v1/investigations/{id}/evidence/hash`: Fast hash verification endpoint returning `EvidenceHashResponse`.
  - `GET /api/v1/investigations/{id}/evidence/export`: Downloads formatted JSON file attachment (`evida-evidence-{id}.json`).
- [x] **Frontend UI (`apps/web/app/investigations/[id]/page.tsx`):**
  - Renders dedicated Phase 7 card with "Export Bundle (.json)" download button.
  - Evidence Bundle SHA-256 cryptographic badge bar.
  - Provenance Taxonomy Legend (`AI_PROPOSAL`, `DETERMINISTIC_EXECUTION`, `CRYPTOGRAPHIC_INTEGRITY`, `SYSTEM_METADATA`, `AUDIT_EVENT`).
  - Double-Validation Authoritative Confirmation Checklist confirming all 8 verification conditions.
  - Evidence chain timeline listing all 11+ aggregated evidence items with distinct provenance badges, summaries, and SHA-256 hashes.
- [x] **Automated Validation:** 235 backend tests passing, 4 frontend tests passing, Ruff lint/format clean, Mypy strict clean, Next build clean.

### Phase 8 — Production Hardening, Deployment & Hackathon Readiness
- [x] **Repository Secrets & Machine Path Scrubbing:** Verified 0 secrets, tokens, or personal paths (`/Users/sandygen/...`) exist across codebase and documentation.
- [x] **Production Authentication & Authorization:**
  - Enforced authentication token requirements when `APP_ENV=production` (rejecting anonymous requests with 401 `UNAUTHORIZED`).
  - Added strict tenant boundary validation across all investigation, repository, reproduction, AI, patch, verification, and evidence endpoints (`INVESTIGATION_PERMISSION_DENIED` 403).
- [x] **Production AI Provider Guardrails:**
  - Added explicit check prohibiting silent fallback to `MockAIProvider` when `APP_ENV=production`.
  - Configured structured `AIProviderError` with `AI_SERVICE_UNAVAILABLE` on provider downtime, preventing unverified investigations from being marked verified.
- [x] **Production CORS & Configuration:**
  - Added configurable `CORS_ORIGINS` to `Settings`.
  - Restricted CORS to explicit origins in production while retaining developer ergonomics in development.
- [x] **Failure Path UX Polish:**
  - Added high-contrast `UNVERIFIED` failure banner in the Web UI explicitly communicating: *"The proposed patch was not verified because deterministic regression validation failed."*
  - Visually links failure classification reasons (e.g. `REGRESSION_STILL_FAILING`).
- [x] **Full E2E Regression & Acceptance Suite (`tests/integration/test_e2e_workflow.py`):**
  - Canonical happy path test from fresh investigation to `COMPLETED` and evidence bundle export.
  - Negative failure test proving flawed patch results in `UNVERIFIED` verdict and state remains `VERIFYING`.
  - Multi-tenant boundary isolation test across all endpoints.
  - Production anonymous rejection test.
- [x] **Master Quality Gate Script (`scripts/final_validation.sh`):**
  - Executable script verifying all 7 quality gates (pytest, ruff check, ruff format check, mypy, vitest, next lint, next build).
- [x] **Hackathon Compliance Documentation (`docs/HACKATHON_COMPLIANCE.md`):**
  - Full architectural alignment with Nebius Token Factory, NVIDIA Nemotron open model, and submission category.
- [x] **3-Minute Demo Script (`docs/DEMO_SCRIPT.md`):**
  - Second-by-second storyboard and voiceover script illustrating the problem, reproduction, AI proposal, deterministic verification, and evidence bundle.
- [x] **Deployment & Operations Guide (`docs/DEPLOYMENT.md`):**
  - Complete, reproducible deployment instructions for Next.js, FastAPI, Supabase, and isolated sandboxes without machine-specific paths.
- [x] **Product README Rewrite (`README.md`):**
  - Complete hackathon presentation highlighting the core maxim, problem, solution, architecture, and verification proof.

---

## Next Steps
- Final submission for Nebius x NVIDIA Global AI Hackathon.
- Record demo video following `docs/DEMO_SCRIPT.md`.

---

## Known Issues & Notes
- Untrusted repository code never executes inside the FastAPI process; all execution occurs via the ephemeral sandbox runner.
- Live Nebius API calls require an active `NEBIUS_API_KEY`; AI models are intentionally not called in Phase 2, Phase 6, or Phase 7 to maintain deterministic execution proofs and audit integrity.
