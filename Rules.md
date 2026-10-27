# EVIDA — Architectural Rules & Coding Standards

## 1. Core Operating Principles

### 1.1 "AI Proposes. Evidence Decides."
- An AI model output is an unverified hypothesis, never system truth.
- A patch is never accepted because the model claims it works; it is accepted ONLY when a deterministic sandbox run proves that:
  1. The new regression test reproduced the failure on the original code.
  2. The patch caused the regression test to pass.
  3. The existing test suite did not regress.

### 1.2 No Local State in Production
- The application backend must be completely stateless.
- Persistent state belongs exclusively in Supabase PostgreSQL and Supabase Storage.
- Local SQLite, local filesystem storage, or in-memory caches must NEVER be used for production persistent application state.
- Worker sandbox containers use ephemeral filesystems that are discarded after execution.

---

## 2. Security Boundaries

### 2.1 Secret Handling
- Never commit `.env` or any file containing API keys or database credentials.
- The `SUPABASE_SERVICE_ROLE_KEY` is backend-only. Never import or bundle it into `apps/web`.
- The `NEBIUS_API_KEY` is backend-only.
- All secrets must be scrubbed from structured application logs.

### 2.2 Sandbox Isolation Guardrails
- The sandbox must NEVER mount the Docker socket (`/var/run/docker.sock`).
- The sandbox must NEVER mount the host root (`/`) or the project root.
- The sandbox must run under a non-root user UID/GID.
- The sandbox execution must enforce hard timeouts (default: 60s).
- Sandbox output (stdout/stderr) must be truncated to prevent memory exhaustion attacks.

### 2.3 Row Level Security (RLS)
- Supabase tables must have RLS enabled (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY;`).
- Insecure open policies (`USING (true)`) are strictly forbidden.
- RLS policies must check user identity (`auth.uid() = user_id`).
- Backend services using the service role bypass RLS, but the FastAPI application must explicitly check tenant ownership before executing queries.

---

## 3. Code Quality & Standards

### 3.1 Python Backend (`apps/api`)
- Python 3.12+ syntax and idioms.
- Strict typing with type hints across all functions and methods.
- Pydantic v2 schemas for all request/response models and external contracts.
- Ruff for linting and code formatting (`ruff check .`, `ruff format --check .`).
- No `pass` or empty `except:` blocks. Log exceptions with structured context.

### 3.2 TypeScript Frontend (`apps/web`)
- Strict TypeScript (`"strict": true` in `tsconfig.json`).
- Zero usage of `any` unless explicitly justified with a comment.
- Next.js App Router conventions with server components by default and client components marked `'use client'`.
- ESLint checks must pass without warnings or errors.

### 3.3 Error Envelopes
- All API error responses must adhere to the standard envelope:
  ```json
  {
    "error": {
      "code": "ERROR_CODE_STRING",
      "message": "Human-readable explanation.",
      "request_id": "req-uuid"
    }
  }
  ```
- Internal stack traces must never leak to clients.
