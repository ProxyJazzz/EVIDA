# EVIDA — Canonical System Architecture

```text
Next.js
   ↓
FastAPI
   ↓
Investigation Engine
   ├── Nebius / NVIDIA
   │      └── AI proposal
   │
   └── Verification Engine
          ↓
       Sandbox
          ↓
   ┌───────────────┐
   │ Patch Apply   │
   │ Regression    │
   │ Baseline      │
   └───────────────┘
          ↓
       Evidence
          ↓
     Final Verdict
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
2. **Persistence:** Backend writes `CREATED` investigation record and `INVESTIGATION_CREATED` event to Supabase.
3. **Reproduction in Sandbox:** Sandbox runs existing test suite or repro script to confirm initial failure state.
4. **AI Reasoning:** Backend prompts Nebius Token Factory (NVIDIA model) with structured reproduction evidence to produce a causal hypothesis and regression test candidate.
5. **Verification of Regression Test:** Sandbox executes regression test against baseline code; it *must* fail (negative proof).
6. **Patch Synthesis:** Nebius generates candidate code patch.
7. **Verification of Patch:** Sandbox applies patch and executes:
   - Regression test (must now PASS).
   - Full repository test suite (must remain PASS).
8. **Evidence Bundle:** Execution outputs, diffs, timing, and exit codes are recorded in Supabase.
9. **Review UI:** User reviews the verified evidence trail and marks the fix `COMPLETED` or `FAILED`.

---

## 4. Deterministic Investigation Lifecycle (Phase 1)

```text
    CREATED
       │
       ▼
   INGESTING
       │
       ▼
  REPRODUCING
       │
       ▼
 INVESTIGATING  ──► (Any Active State) ──► FAILED (Terminal)
       │
       ▼
   VERIFYING
       │
       ▼
   COMPLETED (Terminal)
```

### 4.1 State Machine Rules
- **Explicit Transitions Only:** States can only advance forward sequentially (`CREATED` -> `INGESTING` -> `REPRODUCING` -> `INVESTIGATING` -> `VERIFYING` -> `COMPLETED`).
- **Terminal Guarantees:** Once in `COMPLETED` or `FAILED`, no further transitions are allowed.
- **Idempotency:** Repeated calls to `/start` on an already active investigation safely return the current state without state resets or duplicate events.
- **Immutable Audit Events:** Every state transition automatically creates an append-only `investigation_events` entry with `from_status`, `to_status`, `event_type`, and timestamp.

---

## 5. Repository Ingestion & Failure Reproduction Pipeline (Phase 2)

```text
Repository ZIP Archive
        │
        ▼
Archive Validation & Security Gates
  ├── SHA-256 Digest Computation
  ├── Path Traversal & Absolute Path Rejection
  ├── Archive & Single-File Size Boundaries
  └── File Count & Compression Ratio Enforcement
        │
        ▼
Ephemeral Workspace Setup (Isolated Temp Directory)
  ├── Canonical Path Extraction (No extractall() blind calls)
  └── Deterministic Root Detection (Nested vs Flat layouts)
        │
        ▼
Reproduction Command Validation
  ├── Untrusted Input Sanitization (No shell=True)
  ├── Shell Metacharacter Blocking (; & | ` $ < > { })
  └── Permitted Toolchain Whitelist (pytest, python, python3)
        │
        ▼
Isolated Sandbox Runner Execution
  ├── Process Environment Sanitization (Secrets Scrubbed)
  ├── Hard Wall-Clock Timeout Enforcement
  ├── stdout/stderr Size Truncation (Max 1MB)
  └── Exit Code & Duration Capture
        │
        ▼
Objective Reproduction Verdict Classification
  ├── Exit Code > 0  ──► REPRODUCED (Defect Reproduced)
  ├── Exit Code == 0 ──► NOT_REPRODUCED (Tests Passed)
  ├── Timed Out      ──► TIMEOUT (Exceeded Bounded Time)
  └── Sandbox Error  ──► EXECUTION_ERROR / POLICY_BLOCKED
        │
        ▼
Evidence Persistence & Audit Ledger
  ├── Append-only reproduction_runs persistence
  └── Investigation Audit Event Emitted
```

### 5.1 The Execution Boundary Invariant
Untrusted repository code **never executes inside the FastAPI process**.
1. FastAPI acts strictly as an orchestrator and policy enforcer.
2. The sandbox harness (`sandbox/runner/runner.py`) spawns subprocesses with sanitized environments, stripped of all system and cloud credentials.
3. Every execution takes place in an ephemeral directory that is destroyed immediately after evidence collection.

### 5.2 Deterministic Reproduction Semantics
A command executing with an exit code of 0 does **not** mean the bug was reproduced. In Phase 2:
- Non-zero exit code (`> 0`) from a reproduction test confirms that the failure was reproduced (`REPRODUCED`).
- Zero exit code (`== 0`) indicates that the test passed without reproducing the defect (`NOT_REPRODUCED`).
- Timeouts yield `TIMEOUT`.

### 5.3 Intentional Decoupling
AI models (Nebius / NVIDIA) are **never invoked to decide whether a bug reproduced**.
- Phase 2 establishes **what happened** through deterministic execution evidence.
- Phase 3 introduces AI to answer **why might it have happened** and propose candidate explanations.
- This decoupling prevents hallucinated reproduction verdicts and guarantees that evidence alone drives the repair pipeline.

---

## 6. AI Investigation & Hypothesis Engine Pipeline (Phase 3)

```text
REPRODUCTION EVIDENCE (Phase 2 Run: REPRODUCED)
        │
        ▼
CONTEXT BUILDER (Deterministic Heuristics)
  ├── Sensitive File Filtering (.env*, *.pem, *.key, credentials.json)
  ├── Stack Trace Extraction (File path, line number, symbol)
  ├── Prioritized File Selection (Traceback > Tests > Source)
  └── Strict Context Limits (MAX_CONTEXT_BYTES, MAX_FILE_BYTES, MAX_TREE_ENTRIES)
        │
        ▼
STRUCTURED INVESTIGATION PROMPT (evida-investigation-v1)
  ├── System Prompt: "You do not modify code. You do not claim the bug is fixed."
  └── User Prompt: Bug description, reproduction command, exit code, stdout/stderr, bounded tree, selected source/tests
        │
        ▼
NEBIUS TOKEN FACTORY (OpenAI-compatible /v1/chat/completions)
  ├── NVIDIA Open Model (nvidia/Nemotron-3_5-Lightning)
  └── Single Controlled Retry on Transient Failures
        │
        ▼
AI RESPONSE PARSER & SCHEMA VALIDATOR
  ├── Markdown Code Fence Stripping
  ├── Strict Pydantic Validation (InvestigationHypothesis)
  └── Confidence Range Enforcement (0.0 <= confidence <= 1.0)
        │
        ▼
HYPOTHESIS PERSISTENCE (investigation_hypotheses)
  ├── Raw telemetry (tokens, latency, prompt_version)
  └── Investigation Audit Event Emitted
        │
        ▼
LIFECYCLE TRANSITION
  REPRODUCING ──► INVESTIGATING
```

### 6.1 Core Invariant: AI Proposes. Evidence Decides.
1. **DETERMINISTIC SYSTEM:** "What happened?" (Exit code 1, test assertion failed, stdout/stderr captured).
2. **AI ENGINE:** "Why might it have happened?" (Proposed causal hypothesis, root cause candidate, affected files).
3. **DETERMINISTIC VERIFICATION (Phases 4-5):** "Is the proposed fix actually correct?"

Therefore:
- AI output is **never** treated as verified truth.
- The AI must NOT modify code.
- The AI must NOT generate patches (reserved for Phase 5).
- The AI must NOT declare bugs fixed.
- Terminology used: `Hypothesis`, `Confidence`, `Root cause candidate`, `Evidence`, `Affected files`, `Recommended next action`.
- Terminology forbidden: "Confirmed root cause", "Verified fix", "Bug fixed".

### 6.2 Bounded Context Guardrails
To prevent context overflow, denial of service, or secret leaks:
- `MAX_CONTEXT_FILES`: 20 files
- `MAX_CONTEXT_BYTES`: 100,000 bytes
- `MAX_FILE_BYTES`: 20,000 bytes
- `MAX_TREE_ENTRIES`: 500 entries
- `MAX_STDOUT_CONTEXT_BYTES`: 20,000 bytes
- `MAX_STDERR_CONTEXT_BYTES`: 20,000 bytes

### 6.3 Idempotency & Lifecycle Integration
- Invoking `POST /investigate` multiple times is idempotent: if a hypothesis exists for the current reproduction run, the existing record is returned without re-invoking the model.
- Lifecycle only transitions `REPRODUCING` -> `INVESTIGATING` **after** the structured hypothesis is validated and persisted.

---

## 7. Regression Test Generation & Verification Pipeline (Phase 4)

```text
PHASE 3 HYPOTHESIS & REPRODUCTION EVIDENCE
        │
        ▼
BOUNDED REGRESSION CONTEXT BUILDER
  ├── Hypothesis, root cause symbol/file, affected files
  ├── Bounded reproduction stdout/stderr
  └── Target source & existing test files
        │
        ▼
STRUCTURED REGRESSION TEST PROMPT (evida-regression-test-v1)
  ├── Model: nvidia/Nemotron-3_5-Lightning via Nebius Token Factory
  └── Strict Structured JSON (test_path, test_content, framework, etc.)
        │
        ▼
DETERMINISTIC VALIDATION (Pre-Execution Gate)
  ├── Path Safety: Inside tests/, relative path, no '..', allowed extension
  ├── AST Safety: No subprocess, socket, network, os.system, eval/exec
  ├── Structure: Valid Python syntax and pytest test functions
  └── Size Limit: Bounded by MAX_GENERATED_TEST_BYTES (20,000 bytes)
        │
        ▼
ISOLATED VERIFICATION WORKSPACE
  ├── Extract ORIGINAL unpatched repository archive
  └── Write generated regression test (NO SOURCE CODE MODIFIED)
        │
        ▼
SANDBOX RUNNER EXECUTION
  ├── Command: pytest <test_path>
  └── Hard limits: CPU, memory, PIDs, timeout (30s)
        │
        ▼
OBJECTIVE VERDICT CLASSIFIER
  ├── Assertion failure on buggy code ──► REGRESSION_PROVEN
  ├── Test passed on buggy code       ──► TEST_REJECTED
  ├── ImportError / SyntaxError / crash ──► EXECUTION_ERROR
  ├── Execution timed out              ──► TIMEOUT
  └── Security/policy violation       ──► POLICY_BLOCKED
        │
        ▼
PERSISTENCE & AUDIT TIMELINE
  ├── Table: investigation_regression_tests (Generation record)
  ├── Table: regression_verification_runs (Append-only execution evidence)
  └── Audit Events: REGRESSION_TEST_GENERATED, VERIFICATION_STARTED/COMPLETED, PROVEN/REJECTED
        │
        ▼
LIFECYCLE TRANSITION
  INVESTIGATING ──► VERIFYING (when REGRESSION_PROVEN)
```

### 7.1 Core Invariant: AI Proposes. Deterministic Evidence Decides.
1. The AI-generated test is **untrusted code** until deterministic execution proves that it triggers the defect on the original code.
2. The verification workspace contains **only** the original repository plus the generated test. **Zero source patches are applied.**
3. `REGRESSION_PROVEN` means the defect is now pinned with a deterministic test. It does **NOT** mean the bug is fixed.
4. False positives are strictly forbidden: test execution errors (`ImportError`, collection errors) must never be marked `REGRESSION_PROVEN`.

### 7.2 Safety & Sandbox Boundary
- AST validator inspects test syntax and blocks dangerous calls (`eval`, `exec`, `subprocess`, raw network sockets) before disk extraction.
- Sandbox execution runs in unprivileged boundaries with stripped credentials (`NEBIUS_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY` scrubbed).
- Output truncation prevents memory blowup while preserving failure diagnostics.

---

## 8. Patch Generation & Candidate Validation Pipeline (Phase 5)

```text
REGRESSION_PROVEN EVIDENCE (Phase 4) + HYPOTHESIS (Phase 3)
        │
        ▼
BOUNDED PATCH CONTEXT BUILDER
  ├── Original reproduction evidence & failure traceback
  ├── Hypothesis root cause candidate & affected files
  ├── Proven regression test code & failure stdout/stderr
  └── Target source files & existing unit tests
        │
        ▼
STRUCTURED PATCH PROMPT (evida-patch-generation-v1)
  ├── Model: nvidia/Nemotron-3_5-Lightning via Nebius Token Factory
  └── Strict Structured JSON (description, unified_diff, changed_files, summary, reasoning)
        │
        ▼
DETERMINISTIC PATCH VALIDATOR
  ├── Format Check: patch_format == "unified_diff"
  ├── Diff Header & Path Extraction: Parse '--- a/path' and '+++ b/path'
  ├── Path Traversal & Absolute Paths: Reject '/', '..', or out-of-tree targets
  ├── Test Immutability: Reject ANY modification targeting tests/
  ├── Sensitive Files Shield: Reject edits to .env*, credentials, pem, key, Dockerfile
  ├── Repository File Existence: Changed file must exist in original repository archive
  ├── Scope Boundary: Changed files must remain strictly within hypothesis affected_files
  ├── Safety AST/Pattern Check: Reject subprocess, socket, os.system, eval/exec
  └── Bounded Size Checks: MAX_PATCH_FILES (5), MAX_PATCH_HUNKS (20), MAX_GENERATED_PATCH_BYTES (50,000)
        │
        ▼
PERSISTENCE & AUDIT TIMELINE
  ├── Table: patch_candidates (Record validated candidate patch)
  ├── Audit Events: PATCH_GENERATION_STARTED, PATCH_GENERATED, PATCH_VALIDATED, PATCH_REJECTED
  └── Source Integrity: ZERO filesystem mutation on source code (no git apply, no file rewrite)
        │
        ▼
LIFECYCLE STATUS
  Remains VERIFYING (Awaiting Phase 6 deterministic verification)
```

---

## 9. Deterministic Patch Verification & Double Validation Pipeline (Phase 6)

```text
PATCH_VALIDATED (Phase 5 Candidate) + REGRESSION_PROVEN (Phase 4 Test)
        │
        ▼
PRECONDITION VALIDATION
  ├── Lifecycle status must be VERIFYING
  ├── Stored repository archive exists & valid
  ├── Failure reproduction status == REPRODUCED
  ├── Causal hypothesis exists
  ├── Proven regression test status == REGRESSION_PROVEN
  └── Validated patch candidate status == VALIDATED
        │
        ▼
IDEMPOTENCY CHECK
  └── Return existing VERIFIED run if matching investigation, patch SHA, & repo SHA
        │
        ▼
SOURCE INTEGRITY PRE-CHECK
  └── Record sha256_before of stored repository archive
        │
        ▼
FRESH EPHEMERAL WORKSPACE CREATION
  ├── Temporary directory (prefix: evida_patch_verify_)
  └── Extract original repository archive safely (no symlinks, bounds checked)
        │
        ▼
CONTROLLED PATCH APPLICATION
  ├── Try git apply inside ephemeral workspace
  ├── Fallback to pure-Python unified diff hunk applier if not git repo
  ├── Workspace file manifest pre vs post inspection
  └── Rejection rules:
        ├── Hunk context mismatch / rejected hunks
        ├── Test files modified (tests/ immutability violation)
        └── Unexpected files created / modified / deleted
        │
        ▼
DOUBLE VALIDATION 1: RUN PROVEN REGRESSION TEST
  ├── Inject proven regression test artifact into workspace
  ├── Execute regression test inside sandbox (pytest <regression_path>)
  └── PASS? (exit_code == 0 and not timed_out)
        ├── NO  ──► UNVERIFIED (REGRESSION_STILL_FAILING / TIMEOUT / ERROR)
        └── YES ──► Proceed to Validation 2
        │
        ▼
DOUBLE VALIDATION 2: RUN BASELINE TEST SUITE
  ├── Remove injected regression test artifact cleanly
  ├── Execute repository baseline test command (pytest)
  └── PASS? (exit_code == 0 and not timed_out)
        ├── NO  ──► UNVERIFIED (BASELINE_TEST_FAILURE / TIMEOUT / ERROR)
        └── YES ──► Proceed to Source Integrity Post-Check
        │
        ▼
SOURCE INTEGRITY POST-CHECK
  ├── Verify sha256_after of original repository artifact in storage
  └── sha256_before == sha256_after ?
        ├── NO  ──► SOURCE_INTEGRITY_VIOLATION ──► UNVERIFIED
        └── YES ──► Source Integrity Confirmed Intact
        │
        ▼
DETERMINISTIC VERDICT ASSIGNMENT
  ├── Double validation passed + integrity confirmed ──► VERIFIED
  └── Lifecycle Transition: VERIFYING ──► COMPLETED
        │
        ▼
EVIDENCE CAPTURE & AUDIT PERSISTENCE
  ├── Append-only table: patch_verification_runs
  ├── Workspace file manifest & duration telemetry
  └── Investigation Audit Events Emitted (PATCH_VERIFIED, SOURCE_INTEGRITY_CHECKED)
        │
        ▼
EPHEMERAL WORKSPACE CLEANUP
  └── Complete directory purge (no source code left behind)
```

### 9.1 The Double Validation Invariant
An AI-proposed patch is **never verified** by executing only the generated test or by trusting AI confidence. Double validation requires:
1. **Validation 1 (Defect Fix):** The exact regression test that failed before the patch must **PASS** (exit 0) after patch application.
2. **Validation 2 (Regression Protection):** The existing baseline test suite before EVIDA's repair must also **PASS** (exit 0) against the patched workspace to guarantee no existing capabilities were broken.
3. **Double Validation Rule:**
```python
if patch_application_failed:
    verdict = UNVERIFIED
elif regression_test_failed:
    verdict = UNVERIFIED
elif baseline_tests_failed:
    verdict = UNVERIFIED
elif source_integrity_violated:
    verdict = UNVERIFIED
else:
    verdict = VERIFIED
```

### 9.2 Source Repository Immutability Guarantee
The original repository artifact is **NEVER** modified:
```text
repository_sha256_before == repository_sha256_after
```
All patch application and test suite execution occurs strictly within isolated ephemeral workspaces (`tempfile.TemporaryDirectory`). If the archive's SHA-256 changes at any point during verification, `SOURCE_INTEGRITY_VIOLATION` is triggered and the run fails immediately.




