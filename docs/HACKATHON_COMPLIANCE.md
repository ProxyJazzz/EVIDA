# EVIDA — Nebius x NVIDIA Hackathon Compliance & Architecture Alignment

## 1. Hackathon Details & Submission Metadata

- **Hackathon:** Nebius x NVIDIA Global AI Hackathon
- **Project Name:** EVIDA — Evidence-Driven AI Software Repair
- **Core Maxim:** *AI proposes. Evidence decides.*
- **Primary Category:** Autonomous Software Engineering & Developer Tools
- **Submission Repository:** Public GitHub Repository
- **License:** Open Source (MIT)

---

## 2. Infrastructure & Model Compliance

| Requirement | Implementation in EVIDA | Verification & Location |
| :--- | :--- | :--- |
| **AI Inference Infrastructure** | **Nebius Token Factory** OpenAI-compatible API (`https://api.tokenfactory.nebius.com/v1`) | Configured in `app.core.config.Settings.NEBIUS_BASE_URL` and implemented in `apps/api/app/ai/client.py:NebiusAIProvider`. |
| **NVIDIA Technology** | **NVIDIA Open Model: `nvidia/Nemotron-3_5-Lightning`** | Default model in `Settings.NEBIUS_MODEL`. Attributed across all investigation prompts and visible in the Web UI. |
| **Autonomous Workflow** | End-to-end failure reproduction, root-cause investigation, regression test synthesis, patch generation, double verification, and evidence aggregation. | Orchestrated through FastAPI backend and isolated ephemeral sandboxes (`sandbox/runner/runner.py`). |
| **Non-Fabrication & Determinism** | Clear separation between AI proposal and deterministic execution proof. | AI responses are strictly classified as `AI_PROPOSAL`. Verdicts are 100% computed from exit codes, SHA-256 digests, and sandboxed test executions. |
| **Auditable Evidence** | Immutable, cryptographically hashed evidence bundle with full provenance tracking. | Implemented in Phase 7 (`apps/api/app/domain/evidence/`). Canonical SHA-256 bundle export. |

---

## 3. The Core Architectural Distinction

EVIDA enforces a fundamental architectural boundary:

```text
┌─────────────────────────────────┐
│       NEBIUS TOKEN FACTORY      │
│     NVIDIA Nemotron-3_5 Model   │
└────────────────┬────────────────┘
                 │
                 │ Synthesizes Untrusted Hypotheses,
                 │ Regression Tests & Patch Candidates
                 ▼
          [ AI_PROPOSAL ]
                 │
                 │ Subjected to Ephemeral Execution
                 ▼
┌─────────────────────────────────┐
│     EVIDA ISOLATED SANDBOX      │
│      Deterministic Engine       │
└────────────────┬────────────────┘
                 │
                 │ Evaluates Exit Codes, Diffs & Hashes
                 ▼
      [ DETERMINISTIC EVIDENCE ]
                 │
                 │ Decides Authoritative Verdict
                 ▼
    VERIFIED or UNVERIFIED
```

### What the NVIDIA Model Does:
- **Triage & Causal Diagnosis:** Inspects sandboxed failure traces and bounded workspace context to hypothesize the root cause defect.
- **Regression Test Synthesis:** Formulates isolated, standalone regression test suites targeting the suspected defect.
- **Candidate Patch Generation:** Produces clean, minimal unified diffs resolving the defect without mutating test suites or sensitive paths.

### What EVIDA's Deterministic Harness Does:
- **Zero AI Discretion for Verdicts:** An AI confidence score, natural-language explanation, or LLM self-evaluation is **never** accepted as verification.
- **Double Validation Execution:** Executes the proven regression test and the entire baseline test suite in isolated ephemeral workspaces (`tempfile.TemporaryDirectory`).
- **Cryptographic Source Integrity:** Compares SHA-256 digests of the original repository before and after patch application to guarantee zero filesystem mutation.
- **Tamper-Evident Evidence Bundle:** Compiles all observations into an append-only, SHA-256 hashed audit bundle exported as structured JSON.

---

## 4. Environment Variables Checklist

For production deployment and judges reproducing the environment:

```env
APP_ENV=production
APP_NAME=EVIDA
APP_VERSION=0.1.0

API_HOST=0.0.0.0
API_PORT=8000

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

NEBIUS_API_KEY=your-nebius-token-factory-key
NEBIUS_BASE_URL=https://api.tokenfactory.nebius.com/v1
NEBIUS_MODEL=nvidia/Nemotron-3_5-Lightning

NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=https://api.evida.dev
```

---

## 5. Hackathon Submission Criteria Self-Audit

- [x] **Functionality:** 100% complete working software repair and verification loop across 7 phases.
- [x] **Infrastructure Compliance:** Real Nebius Token Factory client targeting NVIDIA open models with structured JSON extraction, timeout bounds, and graceful error handling.
- [x] **Security & Tenant Isolation:** Complete RLS on all 8 PostgreSQL migration tables, zero open `USING (true)`, non-root isolated sandbox execution, command argument parsing without `shell=True`, path traversal protection, and secret scrubbing.
- [x] **Testing & Verification:** 239 backend unit and integration tests passing, 4 frontend vitest tests passing, 0 Ruff lint/format errors, strict Mypy clean on all 50 source files, and clean Next.js 14 production build.
- [x] **Open Source Integrity:** Free of proprietary secrets, personal developer machine paths, and artificial dependencies.

