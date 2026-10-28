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

### Phase 3 — AI Investigation & Hypothesis Engine (Completed)
- Deterministic repository context builder selecting relevant source and test files.
- Bounded file trees, file byte limits, and output clipping (`MAX_CONTEXT_BYTES = 100000`, `MAX_FILE_BYTES = 20000`).
- Deterministic Python stack trace parsing extracting file paths, lines, and function symbols to prioritize context.
- Defense-in-depth sensitive file exclusion (`.env*`, `*.pem`, `*.key`, `credentials.json`, `service-account.json`, binary files).
- Centralized prompt templates (`apps/api/app/ai/prompts.py`) versioned as `evida-investigation-v1`.
- Integration with Nebius Token Factory using NVIDIA open models (`nvidia/Nemotron-3_5-Lightning`).
- Structured `InvestigationHypothesis` contract with Pydantic validation (hypothesis, confidence `[0.0, 1.0]`, `RootCauseCandidate`, affected files, grounding evidence, recommended next action).
- Resilience handling: markdown code fence parsing, single controlled retry on transient errors, typed domain errors (`INVESTIGATION_PRECONDITION_FAILED`, `AI_RESPONSE_INVALID`, `HYPOTHESIS_NOT_FOUND`).
- Supabase schema migration (`investigation_hypotheses`) with cascading FKs, compound indexes, and RLS policies derived from investigation ownership.
- Lifecycle transition: `REPRODUCING` -> `INVESTIGATING` (only transitions upon successful hypothesis creation and persistence).
- Standard REST API endpoints:
  - `POST /api/v1/investigations/{id}/investigate`
  - `GET /api/v1/investigations/{id}/hypothesis`
- Minimal frontend UI rendering AI hypothesis, unverified confidence score, proposed root cause details, affected files, grounding evidence, and next action.

### Phase 4 — Regression Test Generation & Verification (Completed)
- Standalone regression test generation from Phase 3 hypotheses via Nebius Token Factory and NVIDIA models.
- Versioned prompt template (`REGRESSION_TEST_PROMPT_VERSION = "evida-regression-test-v1"`).
- Strict Pydantic v2 structured output validation (`RegressionTestProposal`).
- Deterministic AST and path validator (`apps/api/app/domain/investigations/test_validator.py`):
  - Traversal, absolute path, and extension validation (must be relative path within `tests/test_*.py`).
  - AST inspection blocking dangerous execution (`subprocess`, `os.system`, `socket`, `requests`, `eval`, `exec`, write mode open).
  - Validation of Python syntax and requirement of at least one valid pytest test structure.
- Bounded test size enforcement (`MAX_GENERATED_TEST_BYTES = 20,000`).
- Isolated verification workspace extraction with original unpatched repository (zero source code modification).
- Deterministic sandbox test execution via `sandbox/runner/runner.py`.
- Objective verdict classification distinguishing test assertion failures (`REGRESSION_PROVEN`) from execution errors (`EXECUTION_ERROR`, `ImportError`, syntax error, collection failure), passing tests (`TEST_REJECTED`), timeouts (`TIMEOUT`), and policy violations (`POLICY_BLOCKED`).
- Supabase migration (`20261027040000_regression_tests.sql`) creating `investigation_regression_tests` and append-only `regression_verification_runs` with RLS.
- Audit timeline integration with events (`REGRESSION_TEST_GENERATED`, `REGRESSION_TEST_VERIFICATION_STARTED`, `REGRESSION_TEST_VERIFICATION_COMPLETED`, `REGRESSION_TEST_PROVEN`, `REGRESSION_TEST_REJECTED`).
- Lifecycle state transition: `INVESTIGATING` -> `VERIFYING` upon proven regression.
- Standard REST API endpoints:
  - `POST /api/v1/investigations/{id}/regression-test`
  - `GET /api/v1/investigations/{id}/regression-test`
- Frontend visualization clearly separating AI PROPOSAL from DETERMINISTIC VERIFICATION with explicit invariant notice (`REGRESSION_PROVEN ≠ BUG_FIXED`).
- Comprehensive unit and end-to-end integration test suite with deterministic mocks.

### Phase 5 — Patch Generation & Candidate Validation (Completed)
- Synthesis of minimal unified diff patches using proven regression evidence, hypothesis, and bounded context.
- Versioned patch generation prompt (`PATCH_GENERATION_PROMPT_VERSION = "evida-patch-generation-v1"`).
- Strongly typed Pydantic v2 `PatchProposal` model (description, patch_format, patch_content, changed_files, change_summary, reasoning).
- Deterministic unified diff parser (`parse_unified_diff_files_and_hunks`).
- Path traversal and boundary validator rejecting `/`, `..`, and out-of-tree targets.
- Test suite immutability enforcement: AI is strictly prohibited from modifying `tests/` or the regression test.
- Sensitive files shield: rejects changes targeting `.env`, credentials, private keys, or infrastructure.
- Scope boundary check: changed files must exist in repository and remain within hypothesis `affected_files`.
- Safety pattern scanner blocking `subprocess`, `os.system`, `socket`, `eval`, `exec`.
- Strict sizing limits (`MAX_PATCH_FILES = 5`, `MAX_PATCH_HUNKS = 20`, `MAX_GENERATED_PATCH_BYTES = 50,000`).
- Database migration `20261027050000_patch_candidates.sql` with RLS.
- Audit timeline integration (`PATCH_GENERATION_STARTED`, `PATCH_GENERATED`, `PATCH_VALIDATED`, `PATCH_REJECTED`).
- Source repository immutability: zero filesystem mutation (no `git apply`, no rewriting).
- Standard REST API endpoints:
  - `POST /api/v1/investigations/{id}/patch`
  - `GET /api/v1/investigations/{id}/patch`
- Frontend UI displaying AI Proposal vs Deterministic Evidence, unified diff preview, and prominent `NOT VERIFIED` badge.
- Comprehensive unit, parser, scope, safety, and API integration test suite.

### Phase 6 — Deterministic Patch Verification & Double Validation (Completed)
- Deterministic patch application in fresh ephemeral sandbox workspaces (`tempfile.TemporaryDirectory`).
- Pure-Python unified diff hunk engine with context checking and `git apply` fallback.
- Workspace file manifest pre/post analysis enforcing that only declared files were modified.
- Strict test immutability: automatic rejection if any test files were modified or deleted.
- Double Validation Rule:
  1. **Validation 1 (Defect Fix):** Proven regression test executed against patched code -> MUST PASS (exit code 0).
  2. **Validation 2 (Regression Protection):** Existing baseline test suite executed against patched code -> MUST PASS (exit code 0).
- Source repository immutability guarantee: `repository_sha256_before == repository_sha256_after`.
- Deterministic failure classification taxonomy (`REGRESSION_STILL_FAILING`, `BASELINE_TEST_FAILURE`, `PATCH_APPLICATION_FAILED`, `SOURCE_INTEGRITY_VIOLATION`, `UNEXPECTED_WORKSPACE_CHANGE`, `REGRESSION_TIMEOUT`, `BASELINE_TIMEOUT`).
- Zero AI discretion: Final verdict (`VERIFIED` or `UNVERIFIED`) is exclusively determined by execution evidence.
- Idempotency: Repeated verification calls return existing verified records without duplicate sandbox executions.
- Supabase schema migration `20261027060000_patch_verification_runs.sql` with compound indexes and tenant RLS.
- Audit event timeline integration (`PATCH_VERIFICATION_STARTED`, `PATCH_APPLICATION_STARTED`, `PATCH_APPLICATION_COMPLETED`, `REGRESSION_VERIFICATION_PASSED`, `BASELINE_VERIFICATION_STARTED`, `BASELINE_VERIFICATION_PASSED`, `SOURCE_INTEGRITY_CHECKED`, `PATCH_VERIFIED`, `PATCH_UNVERIFIED`).
- Lifecycle state machine transition: `VERIFYING` -> `COMPLETED` upon conclusive verification proof.
- Standard REST API endpoints:
  - `POST /api/v1/investigations/{id}/verify-patch`
  - `GET /api/v1/investigations/{id}/verification`
  - `GET /api/v1/investigations/{id}/verifications`
- Frontend UI with dedicated Phase 6 card, 3-step validation grid, execution output inspection, and full 9-step Evidence Chain Visualizer clearly separating AI PROPOSAL from DETERMINISTIC EVIDENCE.
- Comprehensive unit and integration test suite covering happy paths, negative paths (regression still failing, baseline failing, timeout), source integrity, and precondition enforcement.

### Phase 7 — End-to-End Evaluation & Hardening
- SWE-bench or custom benchmark evaluation.
- Rate limiting, audit logging, and sandbox hardening.
- Production deployment configuration.
