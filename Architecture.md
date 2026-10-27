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


