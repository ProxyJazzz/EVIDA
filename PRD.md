# EVIDA — Product Requirements Document (PRD)

**Project Name:** EVIDA  
**Full Name:** Evidence-Driven AI Software Repair  
**Core Maxim:** *AI proposes. Evidence decides.*  
**Status:** Phase 0 — Foundation Complete  

---

## 1. Executive Summary

EVIDA is an automated software repair and verification platform designed to address the fundamental flaw in modern AI code generation: **unverified assertions masquerading as fixes**.

Current generative AI tools propose code modifications that "look right" but fail silently, introduce subtle regression bugs, or hallucinatory test passes. EVIDA treats the AI model as an **untrusted proposal engine**. Every candidate fix must be accompanied by:
1. Deterministic reproduction of the defect in an isolated execution sandbox.
2. AI investigation yielding a causal hypothesis.
3. Automatically generated regression tests that fail on baseline code.
4. Candidate patch generation.
5. Deterministic patch application and verification: the regression test must pass, existing test suites must remain green, and execution logs must provide cryptographic/reproducible evidence.
6. Structured evidence presentation for human review resulting in a verified audit record.

---

## 2. Target Users & Personas

- **Software Engineers & Maintainers:** Seeking verified, reproducible pull requests for complex bugs without spending hours reproducing edge cases.
- **Security & Quality Engineers:** Requiring proof of regression prevention and evidence that patches do not introduce new vulnerabilities.
- **Enterprise Engineering Leaders:** Demanding strict audit trails, zero reliance on blind LLM output, and isolated execution guardrails.

---

## 3. High-Level Repair Lifecycle

```text
Bug Report / Issue
       ↓
Repository Ingestion
       ↓
Failure Reproduction (Sandbox)
       ↓
AI Investigation (Nebius + NVIDIA Model)
       ↓
Causal Hypothesis
       ↓
Regression Test Generation
       ↓
Regression Test Verification (Must fail on buggy baseline)
       ↓
Candidate Patch Generation
       ↓
Patch Execution (Sandbox)
       ↓
Deterministic Verification (Regression test passes + Full test suite green)
       ↓
Evidence Collection (Deltas, logs, timing, artifact hashes)
       ↓
Human Review UI
       ↓
VERIFIED / UNVERIFIED Audit State
```

---

## 4. Phase 0 Scope & Non-Goals

### In Scope for Phase 0
- Monorepo structure separating Frontend (`apps/web`), Backend (`apps/api`), Shared contracts (`packages/shared`), Isolated Sandbox (`sandbox`), and Database migrations (`supabase`).
- Production-shaped FastAPI backend with structured configuration, logging, health probes, and error envelopes.
- Nebius Token Factory AI provider abstraction with NVIDIA open model configuration and mock provider for offline tests.
- Isolated sandbox execution harness with timeout, resource limits, and structured JSON output.
- Supabase schema migrations with Row Level Security (RLS) for tenant isolation.
- Next.js 14+ App Router frontend with visual identity, health monitoring, and authentication scaffolding.
- Comprehensive unit, integration, and sandbox test coverage.

### Out of Scope for Phase 0
- Multi-step autonomous agent execution loops (deferred to Phase 1).
- Live Git repository cloning and PR generation (Phase 2).
- Dynamic test runner synthesis for arbitrary languages (Phase 3).
- Multi-tenant enterprise SSO (Phase 4).

---

## 5. Functional Requirements

### FR-1: Health & Readiness Probes
- `GET /api/v1/health`: Returns service name, version, and status `ok` without requiring live external credentials.
- `GET /api/v1/health/ready`: Inspects external service configuration (Supabase, Nebius) and reports readiness status without crashing when optional services are unconfigured during local development.

### FR-2: AI Provider Abstraction
- Unified `AIProvider` interface supporting generation with system and user prompts.
- `NebiusAIProvider` targeting Nebius Token Factory (`https://api.tokenfactory.nebius.com/v1`) using NVIDIA open models (default `nvidia/Nemotron-3_5-Lightning`).
- `MockAIProvider` for test isolation with zero live credential dependencies.

### FR-3: Sandbox Execution Harness
- Non-privileged execution environment with strict command timeouts and resource boundaries.
- Returns structured JSON: `{ exit_code, stdout, stderr, duration_ms }`.

### FR-4: Database & Multi-Tenancy Foundation
- Supabase PostgreSQL schema with UUID keys, `created_at`, `updated_at` triggers.
- Core entities: `profiles`, `projects`, `repositories`, `investigations`.
- Row Level Security (RLS) policies enforcing user isolation.
