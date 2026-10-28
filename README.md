# EVIDA — Evidence-Driven AI Software Repair

> **AI proposes. Evidence decides.**

EVIDA is an automated, evidence-driven software repair and deterministic verification system. While contemporary AI coding assistants guess patches that look plausible, EVIDA treats all AI proposals as untrusted hypotheses. Every candidate patch must be verified deterministically in an isolated ephemeral sandbox through failure reproduction, regression test generation, double verification, and cryptographic source integrity checks.

---

## 1. Problem

AI coding agents can generate plausible-looking patches, but **a plausible patch is not proof that the software is fixed.**
- Current assistants rely on LLM self-evaluation and conversational confidence scores.
- Code that compiles often subtly fails edge cases or silently breaks existing test suites.
- Developers cannot afford to trust AI output without rigorous, automated verification.

---

## 2. Solution

EVIDA establishes a tamper-evident chain of deterministic execution evidence around every AI-generated repair:

```text
    User Bug Report
          ↓
  Reproduce Failure in Isolated Sandbox (exit code > 0)
          ↓
  AI Causal Investigation (NVIDIA Nemotron via Nebius Token Factory)
          ↓
  Synthesize Regression Test (AST & Security Validated)
          ↓
  Prove Regression Against Original Code (FAIL → PROVEN)
          ↓
  Synthesize Candidate Patch (Unified Diff Scope Validated)
          ↓
  Apply Patch in Fresh Ephemeral Workspace
          ↓
  Execute Double Validation:
    ├── Validation 1: Proven Regression Test (MUST PASS)
    ├── Validation 2: Existing Baseline Suite (MUST PASS)
    └── Cryptographic Source Integrity (SHA-256 Before == After)
          ↓
  AUTHORITATIVE VERDICT: VERIFIED or UNVERIFIED
          ↓
  EVIDA Evidence Bundle (Canonical SHA-256 Tamper-Evident Export)
```

---

## 3. Why EVIDA is Different

> **EVIDA fundamentally separates AI reasoning from software verification.**

### Traditional AI Coding Agent
```text
Prompt
  ↓
LLM
  ↓
Patch
  ↓
"Looks fixed" (Unverified Hope)
```

### EVIDA
```text
Failure
  ↓
Reproduction
  ↓
AI hypothesis (Untrusted Proposal)
  ↓
Regression proof
  ↓
AI patch (Untrusted Proposal)
  ↓
Patch validation
  ↓
Patch execution (Ephemeral Workspace)
  ↓
Regression verification
  ↓
Baseline verification
  ↓
Source integrity
  ↓
Evidence Bundle
  ↓
VERIFIED / UNVERIFIED (Authoritative Proof)
```

The difference is not merely better prompting or autonomous loops: it is the **absolute separation between AI reasoning and deterministic verification**.

- **AI Output is Never Verification:** An AI confidence score, natural language claim, or LLM self-check is classified strictly as `AI_PROPOSAL` (untrusted).
- **Evidence Decides the Verdict:** Only exit codes, subprocess logs, test results, and SHA-256 digests produced inside the sandbox are classified as `DETERMINISTIC_EXECUTION` and `CRYPTOGRAPHIC_INTEGRITY`.
- **Double Validation Invariant:** A patch is marked `VERIFIED` if and only if the proven regression passes, all existing tests continue to pass, and the original repository artifact remains cryptographically unmodified.

---

## 4. Architecture

```text
                     ┌──────────────────┐
                     │     Developer    │
                     └────────┬─────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │    Next.js UI    │
                     └────────┬─────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │    FastAPI API   │
                     └─────┬─────┬──────┘
                           │     │
              ┌────────────┘     └─────────────┐
              ▼                                ▼
      ┌───────────────┐                ┌───────────────┐
      │   Supabase    │                │ Nebius Token  │
      │ DB/Auth/RLS   │                │ Factory       │
      └───────────────┘                └───────┬───────┘
                                               │
                                               ▼
                                      ┌─────────────────┐
                                      │ NVIDIA Nemotron │
                                      └─────────────────┘

                     ┌──────────────────────────┐
                     │     EVIDA Sandbox        │
                     │ Deterministic Execution  │
                     └────────────┬─────────────┘
                                  │
                                  ▼
                     ┌──────────────────────────┐
                     │ Evidence + Verification  │
                     │ SHA-256 + Audit Trail    │
                     └──────────────────────────┘
```

---

## 5. End-to-End Workflow

Every repair follows a strict 7-phase state machine with no skips and zero human database intervention:

1. **Ingest Repository Archive:** ZIP archive ingested with defense-in-depth path traversal checks; computes deterministic archive SHA-256.
2. **Reproduce Failure in Sandbox:** Executes untrusted reproduction command without `shell=True` in an ephemeral sandbox. Confirms exit code `> 0` (`REPRODUCED`).
3. **AI Root Cause Investigation:** Context builder extracts bounded repository view and failure trace; **NVIDIA Nemotron-3_5-Lightning via Nebius Token Factory** hypothesizes root cause and affected files.
4. **Regression Test Synthesis & Proof:** NVIDIA model generates standalone regression test. AST validator ensures security; sandbox proves failure against unpatched code (`REGRESSION_PROVEN`).
5. **Candidate Patch Synthesis & Validation:** NVIDIA model generates minimal unified diff. AST and scope validators confirm diff modifies only authorized files and zero test files (`STATUS: VALIDATED — NOT VERIFIED`).
6. **Deterministic Double Validation:** Pure-Python hunk engine applies patch in a fresh ephemeral workspace. Runs proven regression test (`PASS`) and baseline test suite (`PASS`), checking that original repository SHA-256 before == after (`STATUS: VERIFIED`).
7. **Evidence Bundle Generation & Export:** Aggregates all artifacts into an immutable, append-only record bound by a global SHA-256 digest (`bundle_sha256`).

---

## 6. Verification Model

An AI-proposed patch is **never verified** by executing only the generated test or by trusting AI confidence. Double validation requires:

$$\text{Verdict} = \begin{cases} \text{VERIFIED} & \text{if } P_{\text{applied}} \land R_{\text{pass}} \land B_{\text{pass}} \land S_{\text{match}} \\ \text{UNVERIFIED} & \text{otherwise} \end{cases}$$

Where:
1. $P_{\text{applied}}$: Candidate unified diff applies cleanly in fresh ephemeral workspace without unexpected modifications.
2. $R_{\text{pass}}$: Proven regression test that failed before the patch now **passes** with exit code 0.
3. $B_{\text{pass}}$: Repository baseline test suite **passes** with exit code 0 (zero existing capabilities broken).
4. $S_{\text{match}}$: Cryptographic source integrity holds ($\text{SHA-256}_{\text{before}} == \text{SHA-256}_{\text{after}}$).

If any check fails, the verdict is deterministically **`UNVERIFIED`**.

---

## 7. Evidence Bundle

Every investigation produces a cryptographically hashed, exportable **EVIDA Evidence Bundle** (`/api/v1/investigations/{id}/evidence/export`).

### Provenance Classification Taxonomy
Every evidence item carries an authoritative provenance classification:
- `AI_PROPOSAL`: Root cause hypotheses, synthesized regression tests, and candidate diffs.
- `DETERMINISTIC_EXECUTION`: Subprocess exit codes, execution durations, stdout/stderr, and test passes/fails.
- `CRYPTOGRAPHIC_INTEGRITY`: SHA-256 digests of repository archives, candidate diffs, and individual evidence items.
- `SYSTEM_METADATA`: Canonical timestamps, investigation and entity UUIDs, model IDs, and prompt versions.
- `AUDIT_EVENT`: Append-only lifecycle transition event records.

### Canonical Bundle Hash
```text
bundle_sha256 = sha256(canonical_json(sorted_scrubbed_items))
```
Any post-hoc tampering with outputs, timestamps, or verdicts mutates the bundle digest, providing a tamper-evident audit record suitable for high-assurance review.

---

## 8. Technology Stack

```text
Frontend:          Next.js 14 (App Router) + React + TypeScript + Tailwind CSS
Backend:           FastAPI + Python 3.12 + Pydantic v2
Database & Auth:   Supabase (Managed PostgreSQL 15+ with strict Row Level Security)
AI Infrastructure: Nebius Token Factory (OpenAI-compatible inference)
NVIDIA Technology: NVIDIA Open Model (nvidia/Nemotron-3_5-Lightning)
Sandbox Harness:   Isolated Ephemeral Process Sandboxes with resource & command limits
```

---

## 9. Demo

- **Demo Video Script:** [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) — 3-minute video storyboard with second-by-second timestamps.
- **Canonical Demo Fixture:** Located in `tests/fixtures/broken_python_repo.zip`.
  - **Defect:** `divide(a, b)` in `src/calculator.py` returns `a * b` instead of `a / b`.
  - **Expected:** `divide(10, 2) == 5`.
  - **Observed:** `10 * 2 == 20` (triggers assertion failure in `test_bug.py`).
  - **Verification:** Cleanly reproduced, diagnosed by NVIDIA Nemotron, regression proven, patched, double-verified, and bundled.

---

## 10. Quickstart

### 1. Clone & Configure Environment

```bash
git clone https://github.com/your-org/evida.git
cd evida

# Copy environment template
cp .env.example .env
```

Key environment variables in `.env`:
```env
APP_ENV=development
API_HOST=0.0.0.0
API_PORT=8000

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

NEBIUS_API_KEY=your-nebius-token-factory-api-key
NEBIUS_BASE_URL=https://api.tokenfactory.nebius.com/v1
NEBIUS_MODEL=nvidia/Nemotron-3_5-Lightning

NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Backend Startup (`apps/api`)

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Liveness Probe:** `curl http://localhost:8000/api/v1/health`
- **Readiness Probe:** `curl http://localhost:8000/api/v1/health/ready`
- **Interactive OpenAPI Documentation:** `http://localhost:8000/docs`

### 3. Frontend Startup (`apps/web`)

```bash
cd apps/web
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.
- **Dashboard:** `http://localhost:3000/dashboard`
- **Investigation View:** `http://localhost:3000/investigations/33333333-3333-3333-3333-333333333333`

### 4. Automated Master Quality Gate

Verify the complete system with a single command:

```bash
./scripts/final_validation.sh
```

Runs all 7 quality gates:
1. Backend unit and integration test suite (239 tests passing via `pytest`)
2. Python linting (`ruff check`)
3. Python formatting (`ruff format --check`)
4. Static type safety (`mypy apps/api/app`)
5. Frontend unit tests (`vitest`)
6. Frontend linter (`next lint`)
7. Frontend production build (`next build`)

---

## 11. Security Model

> **EVIDA treats generated AI artifacts as untrusted input.**

- **Execution Boundary:** Repository code and generated tests are executed exclusively inside constrained ephemeral sandboxes (`tempfile.TemporaryDirectory`).
- **No Command Injection:** Untrusted commands are validated and parsed into vector arguments; `shell=True` is strictly forbidden. Disallowed metacharacters (`;`, `&`, `|`, `` ` ``, `$`, `>`, `<`) and blocked executables (`rm`, `sudo`, `curl`, `wget`, `bash`) trigger immediate policy violations.
- **Path Traversal Shield:** Ingestion rejects Zip Slip attempts (`..`, `/`, symlink breakouts).
- **Test Immutability:** AI patches targeting `tests/` or regression test suites are rejected with `TEST_MODIFICATION`.
- **Sensitive Path Masking:** Exclusion patterns block reads or edits to `.env*`, `*.pem`, `*.key`, `credentials.json`, `Dockerfile`.
- **Tenant Isolation:** Enforced through FastAPI authorization and Supabase Row Level Security (RLS) across all 8 tables. No open `USING (true)` policies exist.
- **Append-Only Evidence:** `investigation_evidence` table has only `SELECT` and `INSERT` policies; no `UPDATE` or `DELETE` policies exist.

---

## 12. Hackathon Compliance

- **Hackathon:** Nebius x NVIDIA Global AI Hackathon
- **Primary Category:** Autonomous Software Engineering & Developer Tools
- **One-Line Description:**
  > **AI proposes software repairs. EVIDA deterministically verifies whether they actually work.**
- **Short Description:**
  > EVIDA is an evidence-driven AI software repair system. It uses NVIDIA Nemotron through Nebius Token Factory to investigate software failures and propose regression tests and patches, then independently executes and verifies those changes in a sandbox. A repair is marked VERIFIED only when the regression passes, the baseline suite passes, and source integrity is preserved. Every investigation produces a cryptographically hashed evidence bundle.
- **Compliance Documentation:** Detailed breakdown in [`docs/HACKATHON_COMPLIANCE.md`](docs/HACKATHON_COMPLIANCE.md).

---

## 13. Repository Structure

```text
evida/
├── apps/
│   ├── web/               # Next.js 14 App Router frontend with evidence timeline UI
│   └── api/               # FastAPI backend with domain state machine & Nebius integration
├── packages/
│   └── shared/            # Shared TypeScript contracts and domain models
├── supabase/
│   ├── migrations/        # 8 PostgreSQL migrations with strict RLS tenant isolation
│   └── seed.sql           # Development seed data
├── sandbox/
│   ├── Dockerfile         # Hardened non-privileged execution container
│   ├── runner/            # Isolated command runner with hard timeouts & secret scrubbing
│   └── policies/          # Resource limits & security policies
├── scripts/
│   └── final_validation.sh # Master quality gate execution script
├── tests/
│   ├── unit/              # Unit tests (models, validators, classifiers, state machine)
│   ├── integration/       # API integration & full end-to-end regression tests
│   └── fixtures/          # Deterministic test repositories (broken calculator, etc.)
├── docs/
│   ├── HACKATHON_COMPLIANCE.md # Nebius x NVIDIA compliance documentation
│   ├── DEMO_SCRIPT.md          # 3-minute video/live demonstration script
│   ├── DEPLOYMENT.md           # Production deployment & operations guide
│   ├── API.md                  # Comprehensive OpenAPI / REST endpoints documentation
│   ├── DATABASE.md             # Supabase PostgreSQL schema & RLS policies
│   └── SECURITY.md             # Threat model, sandbox boundaries & scrubbing rules
├── memory.md              # Project status ledger across all 8 phases
└── README.md
```

---

## 14. License

MIT © 2026 EVIDA Contributors.
