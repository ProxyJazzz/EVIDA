# EVIDA — Security Architecture & Threat Model

## 1. Security Architecture Principles

EVIDA executes untrusted code and interacts with AI inference providers. The system implements strict **defense-in-depth**:

```text
Untrusted Web Client
       │ (HTTPS / Bearer Auth)
       ▼
API Gateway / FastAPI (Authorization Authority)
   ├── Input Validation (Pydantic v2)
   ├── Strict Rate Limiting
   ├── Tenant Ownership Enforcement
   └── Secret Scrubbing in Logs
       │
   ┌───┴────────────────────────────┐
   ▼                                ▼
Supabase Database           Execution Sandbox
(RLS Defense-in-Depth)       (Untrusted Execution Boundary)
* UUID tenancy checks        * Non-root user
* Service-role backend only  * Hard timeouts (60s)
* No public access to data   * No host mounts or Docker socket
                             * Ephemeral filesystem
```

---

## 2. Secrets Management & Boundaries

| Secret Name | Location | Usage | Exposure Risk | Mitigation |
| :--- | :--- | :--- | :--- | :--- |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend Only | Administrative DB persistence | Critical (Bypasses RLS) | Never expose to frontend. Never check into Git. |
| `SUPABASE_ANON_KEY` | Frontend & Backend | Public DB reads with RLS | Low | Enforce strict RLS policies. |
| `NEBIUS_API_KEY` | Backend Only | Token Factory inference | High (Cost / Quota) | Server-side only; scrubbed from logs. |
| Target Repo Secrets | Ephemeral Sandbox | Clone/install dependencies | Medium | Ephemeral container wiped post-run. |

---

## 3. Sandbox Isolation Guardrails

The execution sandbox executes arbitrary code from user repositories and AI-generated test cases:
1. **No Docker Socket Access:** The sandbox container never mounts `/var/run/docker.sock`.
2. **No Host Root Mounts:** The container cannot read or write the host file system.
3. **Non-Root Execution:** Code runs under UID 1000 (`sandboxuser`).
4. **Hard Timeout Enforcement:** Every execution is bounded by a strict wall-clock timeout (default 60s).
5. **Output Truncation:** Stderr and stdout streams are bounded to 1MB to prevent buffer exhaustion.

---

## 4. Structured Logging & Scrubbing

All log records are structured JSON. The logging pipeline includes an automatic secret scrubber regex that intercepts and replaces:
- Bearer tokens
- `eyJ...` JWT strings
- Nebius API keys
- Supabase service role keys
- Repository tokens
