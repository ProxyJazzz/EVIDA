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

---

## 7. Phase 4 AI Regression Test Security & AST Safety Model

### 7.1 Untrusted Code Invariant
Code synthesized by AI models (Nebius / NVIDIA) is inherently untrusted. A model may inadvertently or adversarially output malicious Python statements, shell invocations, network probes, or filesystem destruction calls. EVIDA treats all AI-generated tests as untrusted code.

### 7.2 Deterministic AST Safety Inspection
Before any generated test code is written to disk or executed in the sandbox, it must pass through an AST validator (`apps/api/app/domain/investigations/test_validator.py`):
1. **Compilation Check:** The test code is parsed using Python's standard `ast.parse()`. Any syntax error or invalid construct immediately triggers `400 REGRESSION_SYNTAX_ERROR`.
2. **Prohibited Module Imports:** Imports of dangerous libraries are blocked via AST node inspection:
   - Process control: `subprocess`, `multiprocessing`, `pty`, `commands`
   - Networking & HTTP: `socket`, `requests`, `urllib`, `urllib3`, `http.client`, `httpx`, `aiohttp`, `paramiko`, `fabric`
   - System internals: `ctypes`
3. **Prohibited Function Calls:**
   - Dynamic evaluation: `eval()`, `exec()`, `compile()`, `__import__()`
   - Command execution: `os.system()`, `os.popen()`, `os.kill()`
   - Filesystem destruction: `shutil.rmtree()`, `shutil.move()`, `os.remove()`, `os.unlink()`, `os.rmdir()`, `os.chmod()`, `os.chown()`
   - Arbitrary write opens: `open(..., 'w')` / `open(..., 'wb')` / `open(..., 'a')`
4. **Required Structure:** The test must contain at least one valid pytest test function (`def test_*`) or test class (`class Test*`). Empty or vacuous files are rejected.

### 7.3 Path Traversal Defense
The test path specified by the model is strictly sanitized:
- Must be a relative POSIX path.
- Must not begin with `/` or contain drive letters.
- Must not contain `..` parent directory traversal tokens.
- Must reside within the `tests/` directory and match `test_*.py` or `*_test.py`.

### 7.4 Bounded Test Size
Generated test content is capped at `MAX_GENERATED_TEST_BYTES` (20,000 bytes) to prevent resource exhaustion.

### 7.5 Workspace Isolation & Non-Destructive Execution
- The verification workspace extracts the **original unpatched repository**.
- Zero modifications are made to production source files.
- The test runs exclusively inside the ephemeral sandbox runner with stripped environment variables (`NEBIUS_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY` scrubbed).
- Hard timeouts (30s) and memory caps prevent infinite loop denial-of-service.

---

## 8. Phase 5 Patch Generation & Candidate Validation Security

### 8.1 The "Untrusted Patch" Maxim
Patches synthesized by AI models are strictly untrusted candidates. A proposed patch may attempt to weaken tests, inject backdoors, modify security infrastructure, overwrite configuration or secrets, or execute path traversal attacks. EVIDA treats patch candidates as untrusted data until deterministic validation accepts them and Phase 6 executes verification.

### 8.2 Deterministic Unified Diff Parsing
Before persistence, the unified diff is deterministically parsed by `patch_validator.py`:
- Diff headers `--- a/<path>` and `+++ b/<path>` are extracted and canonicalized.
- Declared `changed_files` in the model's structured payload must match the actual files modified in the diff. Any mismatch triggers `MALFORMED_DIFF`.
- Hunk counts (`@@ -l,s +l,s @@`) are counted and bounded by `MAX_PATCH_HUNKS` (20).

### 8.3 Path Traversal & Boundary Safety
Every target path in the patch is validated:
- Must be a relative path (cannot start with `/` or contain drive letters).
- Must not contain `..` or traverse outside the repository directory.
- Must target an existing file present in the original repository archive (`FILE_NOT_FOUND` if targeting nonexistent files).

### 8.4 Test Suite Immutability (Anti-Cheating Policy)
A classic failure mode of automated code synthesis is weakening or deleting tests so that broken code appears to pass.
- **Rule:** Any patch candidate that modifies, deletes, or adds files under `tests/` or modifies the proven regression test is immediately rejected with `TEST_MODIFICATION`.
- Phase 5 enforces that repair patches modify production source files only.

### 8.5 Sensitive Files Shield
Patches targeting any sensitive system files are rejected with `SENSITIVE_FILE_MODIFICATION`:
- Environment files: `.env`, `.env.local`, `.env.production`
- Secrets and keys: `*.pem`, `*.key`, `*.pfx`, `id_rsa`, `id_ed25519`
- Cloud credentials: `credentials.json`, `service-account*.json`
- Security and infrastructure files: `Dockerfile`, `docker-compose*.yml`, `.github/workflows/`

### 8.6 Dangerous Code Pattern Inspection
Added lines in the diff (lines starting with `+`) are analyzed for dangerous calls:
- Process spawning: `subprocess`, `os.system`, `os.popen`, `pty`, `multiprocessing`
- Network calls: `socket`, `requests`, `urllib`, `http.client`, `httpx`, `aiohttp`
- Dynamic execution: `eval(`, `exec(`
Any violation immediately triggers `SECURITY_VIOLATION`.

### 8.7 Bounded Scope & Sizing Limits
- Number of modified files is bounded by `MAX_PATCH_FILES` (5).
- Number of hunks is bounded by `MAX_PATCH_HUNKS` (20).
- Total patch bytes is bounded by `MAX_GENERATED_PATCH_BYTES` (50,000 bytes).
- Patches modifying files outside the hypothesis-confirmed `affected_files` are rejected with `OUT_OF_SCOPE_CHANGE`.

### 8.8 Architectural Immutability: No Patch Application
Phase 5 **never applies or executes** candidate patches:
- Zero calls to `git apply`, `patch`, or filesystem file writers on the source repository.
- The original repository archive and workspace remain cryptographically identical (proven by SHA-256 snapshots before and after patch generation).
- Execution is strictly quarantined until Phase 6 in an ephemeral, unprivileged sandbox.


