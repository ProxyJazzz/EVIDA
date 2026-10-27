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

---

## 5. Phase 2 ZIP Ingestion & Reproduction Security Model

### 5.1 Archive Verification Boundary
Uploaded repository archives represent untrusted binary input. The system enforces strict security gates prior to any disk extraction:
1. **No Blind `extractall()`:** Standard Python `extractall()` is strictly forbidden due to Zip Slip vulnerabilities.
2. **Path Traversal Defense:** All archive entry names are analyzed. Any entry containing `../`, `..\\`, or relative navigation escaping the destination root is immediately rejected with `400 INVALID_ARCHIVE`.
3. **Absolute Path Blocking:** Any entry starting with `/` or drive specifications (e.g. `C:\`) is immediately rejected.
4. **Symlink Containment:** Symlinks that point outside the ephemeral extraction directory are blocked.
5. **Resource Boundaries:**
   - Maximum archive size: `MAX_ARCHIVE_SIZE_MB` (default 50 MB)
   - Maximum uncompressed size: `MAX_EXTRACTED_SIZE_MB` (default 200 MB)
   - Maximum file count: `MAX_FILE_COUNT` (default 5,000 files)
   - Maximum single-file size: `MAX_SINGLE_FILE_SIZE_MB` (default 20 MB)
6. **Integrity Digest:** SHA-256 digest is computed on the raw archive bytes and persisted to guarantee artifact provenance.

### 5.2 Ephemeral Workspace Lifecycle
Extraction and reproduction execute inside temporary ephemeral workspaces created via `tempfile.TemporaryDirectory`.
- The workspace directory is created with restrictive permissions.
- Repository root is detected deterministically (supporting nested directory packages or flat roots).
- The directory and all extracted files are wiped from the host immediately upon execution completion.

### 5.3 Untrusted Reproduction Command Execution
1. **Never `shell=True`:** Reproduction commands are parsed into structured argument vectors (`shlex.split`) and passed directly as argument lists to `subprocess.Popen`.
2. **Disallowed Shell Metacharacters:** Shell control operators (`;`, `&`, `|`, `` ` ``, `$`, `(`, `)`, `<`, `>`, `{`, `}`, `\n`) are strictly blocked before subprocess execution.
3. **Executable Whitelist:** Only approved testing harnesses (`pytest`, `python`, `python3`) are permitted. System administration tools (`rm`, `bash`, `curl`, `wget`, `sudo`) are blocked with `EXECUTION_POLICY_BLOCKED`.
4. **No Inline Python Execution:** Arbitrary code execution via `python -c` is forbidden.
5. **Argument Traversal Protection:** Arguments containing `..` path traversals are blocked.
6. **Environment Scrubbing:** Processes inherit a sanitized environment with `EVIDA_SANDBOX=1` and all cloud secrets scrubbed.

---

## 6. Phase 3 AI Context Security & Prompt Isolation

### 6.1 Sensitive File Exclusion
Untrusted repositories may contain local configuration files, development keys, or accidental secrets. The context builder strictly enforces exclusion patterns before files can be read or transmitted to external AI providers:
- Environment and secret files: `.env`, `.env.*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`
- Cloud & authentication credentials: `credentials.json`, `service-account.json`, `service_account.json`, `id_rsa`, `id_ed25519`
- Binary and media files: executable binaries, images, archives, compiled bytecode
- Build and cache directories: `.git/`, `.venv/`, `venv/`, `__pycache__/`, `node_modules/`, `dist/`, `build/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`

### 6.2 Bounded Transmission & Resource Limits
To defend against prompt injection and unbounded context denial of service:
- Maximum files in prompt: 20 files
- Maximum combined context: 100,000 bytes
- Maximum individual file content: 20,000 bytes
- Maximum repository tree entries: 500 lines
- Maximum stdout context: 20,000 bytes
- Maximum stderr context: 20,000 bytes

### 6.3 Credential Protection
The `NEBIUS_API_KEY` and other platform credentials:
- Are never included in system or user prompt templates.
- Are scrubbed from outgoing error payloads and application logs.
- Never surface in raw or parsed model responses returned to API clients.

