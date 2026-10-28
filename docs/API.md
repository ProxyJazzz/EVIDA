# EVIDA — API Documentation

## 1. Overview

The EVIDA Application Backend is built with **FastAPI** and exposed under the `/api/v1` prefix. All requests and responses use JSON.

Base URL: `http://localhost:8000/api/v1` (default local dev)

Interactive OpenAPI Documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 2. Standard Responses & Error Envelopes

### 2.1 Success Responses
Standard JSON payloads with strongly typed schemas.

### 2.2 Error Envelope
All error responses return HTTP 4xx or 5xx with a unified JSON body:

```json
{
  "error": {
    "code": "INVALID_STATE_TRANSITION",
    "message": "Cannot transition investigation from 'CREATED' to 'COMPLETED'.",
    "request_id": "4167831d-cb56-46b0-b616-6714138a77c7"
  }
}
```

### 2.3 Common Lifecycle Error Codes
- `INVESTIGATION_NOT_FOUND` (404): Investigation ID does not exist.
- `INVALID_STATE_TRANSITION` (409): Target state transition violates state machine rules.
- `INVESTIGATION_ALREADY_TERMINAL` (409): Investigation is in a terminal state (`COMPLETED`, `FAILED`).
- `INVALID_INVESTIGATION_REQUEST` (422): Malformed payload or missing required parameters.
- `INVESTIGATION_PERSISTENCE_ERROR` (500): Database persistence failure.

---

## 3. Endpoints

### 3.1 Health & Readiness Probes

#### Liveness Probe
`GET /api/v1/health`

Performs an immediate liveness check. Operates completely offline without requiring active Supabase or Nebius connections.

**Response (200 OK):**
```json
{
  "status": "ok",
  "service": "evida-api",
  "version": "0.1.0"
}
```

#### Readiness Probe
`GET /api/v1/health/ready`

Inspects runtime configuration and external service readiness (Supabase, Nebius AI, sandbox runner).

**Response (200 OK):**
```json
{
  "status": "ready",
  "service": "evida-api",
  "version": "0.1.0",
  "checks": {
    "database": {
      "configured": true,
      "provider": "supabase"
    },
    "ai_provider": {
      "configured": true,
      "provider": "nebius",
      "model": "nvidia/Nemotron-3_5-Lightning"
    },
    "sandbox": {
      "ready": true,
      "runner": "isolated_process"
    }
  }
}
```

---

### 3.2 Investigation Lifecycle Endpoints

#### Create Investigation
`POST /api/v1/investigations`

Creates a new repair investigation with initial status `CREATED` and emits an `INVESTIGATION_CREATED` audit event.

**Request Body:**
```json
{
  "project_id": "11111111-1111-1111-1111-111111111111",
  "repository_id": "22222222-2222-2222-2222-222222222222",
  "title": "Fix NullPointerException in token parser",
  "bug_description": "Parser throws NPE when authorization header has trailing whitespace."
}
```

**Response (201 Created):**
```json
{
  "id": "33333333-3333-3333-3333-333333333333",
  "investigation_id": "33333333-3333-3333-3333-333333333333",
  "project_id": "11111111-1111-1111-1111-111111111111",
  "repository_id": "22222222-2222-2222-2222-222222222222",
  "title": "Fix NullPointerException in token parser",
  "bug_description": "Parser throws NPE when authorization header has trailing whitespace.",
  "status": "CREATED",
  "hypothesis": null,
  "regression_test_code": null,
  "candidate_patch": null,
  "verification_evidence": null,
  "created_at": "2026-10-27T16:00:00Z",
  "updated_at": "2026-10-27T16:00:00Z"
}
```

---

#### Get Investigation
`GET /api/v1/investigations/{investigation_id}`

Retrieves an investigation record by UUID.

**Response (200 OK):**
```json
{
  "id": "33333333-3333-3333-3333-333333333333",
  "investigation_id": "33333333-3333-3333-3333-333333333333",
  "project_id": "11111111-1111-1111-1111-111111111111",
  "repository_id": "22222222-2222-2222-2222-222222222222",
  "title": "Fix NullPointerException in token parser",
  "bug_description": "Parser throws NPE when authorization header has trailing whitespace.",
  "status": "INGESTING",
  "created_at": "2026-10-27T16:00:00Z",
  "updated_at": "2026-10-27T16:01:00Z"
}
```

---

#### Start Investigation
`POST /api/v1/investigations/{investigation_id}/start`

Begins the investigation lifecycle by transitioning from `CREATED` to `INGESTING`.

**Idempotency & Safety:**
- If current status is `CREATED`, transitions to `INGESTING` and emits an `INVESTIGATION_STARTED` event.
- If already in `INGESTING` or subsequent active state, returns the current state safely without restarting or corrupting the lifecycle.
- If in a terminal state (`COMPLETED`, `FAILED`), returns `409 Conflict` with `INVESTIGATION_ALREADY_TERMINAL`.

**Response (200 OK):**
```json
{
  "id": "33333333-3333-3333-3333-333333333333",
  "status": "INGESTING",
  "updated_at": "2026-10-27T16:01:00Z"
}
```

---

#### Get Investigation Event Timeline
`GET /api/v1/investigations/{investigation_id}/events`

Returns the chronological audit trail of all lifecycle events for the investigation.

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "44444444-4444-4444-4444-444444444444",
      "investigation_id": "33333333-3333-3333-3333-333333333333",
      "event_type": "INVESTIGATION_CREATED",
      "from_status": null,
      "to_status": "CREATED",
      "metadata": { "user_id": "00000000-0000-0000-0000-000000000001" },
      "created_at": "2026-10-27T16:00:00Z"
    },
    {
      "id": "55555555-5555-5555-5555-555555555555",
      "investigation_id": "33333333-3333-3333-3333-333333333333",
      "event_type": "INVESTIGATION_STARTED",
      "from_status": "CREATED",
      "to_status": "INGESTING",
      "metadata": { "trigger": "api_start" },
      "created_at": "2026-10-27T16:01:00Z"
    }
  ],
  "total": 2
}
```

---

#### List Investigations
`GET /api/v1/investigations`

Lists all investigations for the authenticated user/tenant.

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "33333333-3333-3333-3333-333333333333",
      "title": "Fix NullPointerException in token parser",
      "status": "INGESTING",
      "created_at": "2026-10-27T16:00:00Z"
    }
  ],
  "total": 1
}
```

---

### 3.3 Phase 2 Repository Ingestion & Reproduction Endpoints

#### Upload Repository Archive
`POST /api/v1/investigations/{investigation_id}/repository`

Uploads and validates a ZIP repository archive. Enforces path traversal checks, file size limits, and file count limits. On success, transitions investigation state from `CREATED` to `INGESTING`.

**Request:** `multipart/form-data`
- `file`: ZIP archive payload (`.zip`)

**Response (201 Created):**
```json
{
  "id": "22222222-2222-2222-2222-222222222222",
  "investigation_id": "33333333-3333-3333-3333-333333333333",
  "name": "broken-project.zip",
  "archive_size_bytes": 1048576,
  "archive_sha256": "fa4aec473a843aa4d3a2df0840c192a2e28526c6f5d146b0ae7b7fabaf5280a9",
  "status": "READY",
  "created_at": "2026-10-27T16:05:00Z",
  "updated_at": "2026-10-27T16:05:00Z"
}
```

---

#### Get Repository Metadata
`GET /api/v1/investigations/{investigation_id}/repository`

Retrieves the archive metadata, SHA-256 digest, and validation status of the attached repository.

**Response (200 OK):**
```json
{
  "id": "22222222-2222-2222-2222-222222222222",
  "investigation_id": "33333333-3333-3333-3333-333333333333",
  "name": "broken-project.zip",
  "archive_size_bytes": 1048576,
  "archive_sha256": "fa4aec473a843aa4d3a2df0840c192a2e28526c6f5d146b0ae7b7fabaf5280a9",
  "status": "READY",
  "created_at": "2026-10-27T16:05:00Z",
  "updated_at": "2026-10-27T16:05:00Z"
}
```

---

#### Execute Failure Reproduction
`POST /api/v1/investigations/{investigation_id}/reproduce`

Extracts the validated repository archive into an ephemeral workspace, validates the reproduction command against security policy, executes it in the isolated sandbox, captures objective execution telemetry, classifies the verdict, and transitions the investigation to `REPRODUCING`.

**Request Body:**
```json
{
  "command": "pytest tests/test_bug.py"
}
```

**Response (200 OK):**
```json
{
  "id": "77777777-7777-7777-7777-777777777777",
  "investigation_id": "33333333-3333-3333-3333-333333333333",
  "repository_id": "22222222-2222-2222-2222-222222222222",
  "command": "pytest tests/test_bug.py",
  "status": "REPRODUCED",
  "exit_code": 1,
  "stdout": "============================= test session starts ==============================\nFAILED tests/test_bug.py::test_divide_bug - assert 20 == 5\n============================== 1 failed in 0.12s ===============================",
  "stderr": "",
  "duration_ms": 124,
  "timed_out": false,
  "created_at": "2026-10-27T16:06:00Z",
  "completed_at": "2026-10-27T16:06:01Z"
}
```

**Reproduction Verdict Semantics:**
- `REPRODUCED`: Exit code > 0 (reproduction test demonstrated failure).
- `NOT_REPRODUCED`: Exit code == 0 (test passed without defect).
- `TIMEOUT`: Execution exceeded hard wall-clock timeout.
- `EXECUTION_ERROR`: Sandbox execution setup failed.
- `POLICY_BLOCKED`: Command violated security restrictions.

---

#### Get Reproduction Result
`GET /api/v1/investigations/{investigation_id}/reproduction`

Retrieves the latest objective reproduction run execution telemetry and verdict for an investigation.

**Response (200 OK):**
Same as `POST /reproduce` response body.

---

### 3.4 AI Investigation & Hypothesis Endpoints (Phase 3)

#### Start AI Investigation
`POST /api/v1/investigations/{investigation_id}/investigate`

Executes the AI investigation pipeline for an investigation with a `REPRODUCED` failure. Binds repository context, invokes the configured NVIDIA model via Nebius Token Factory, parses and validates the structured causal hypothesis, persists it, and transitions the investigation to `INVESTIGATING`.

**Preconditions:**
- Investigation must have a completed reproduction run with status `REPRODUCED`.
- If status is `NOT_REPRODUCED`, returns `400 INVESTIGATION_PRECONDITION_FAILED`.

**Idempotency:**
- Repeating the request returns the existing hypothesis for the current reproduction run without re-invoking the model.

**Response (200 OK):**
```json
{
  "id": "88888888-8888-8888-8888-888888888888",
  "investigation_id": "33333333-3333-3333-3333-333333333333",
  "reproduction_run_id": "77777777-7777-7777-7777-777777777777",
  "provider": "nebius",
  "model": "nvidia/Nemotron-3_5-Lightning",
  "prompt_version": "evida-investigation-v1",
  "hypothesis": "The divide function in src/calculator.py multiplies its operands instead of dividing them.",
  "confidence": 0.99,
  "root_cause": {
    "file": "src/calculator.py",
    "symbol": "divide",
    "line": 2,
    "description": "The implementation uses the multiplication operator (*) instead of the division operator (/)."
  },
  "affected_files": [
    "src/calculator.py"
  ],
  "evidence": [
    "The reproduction test expects 5 but the function returns 20.",
    "The reproduction command 'pytest tests/test_bug.py' exited with code 1."
  ],
  "recommended_next_action": "generate_regression_test",
  "created_at": "2026-10-27T16:07:00Z"
}
```

---

#### Get Investigation Hypothesis
`GET /api/v1/investigations/{investigation_id}/hypothesis`

Retrieves the latest structured causal hypothesis for an investigation.

**Response (200 OK):**
Same as `POST /investigate` response body.

**Response (404 Not Found):**
```json
{
  "error": {
    "code": "HYPOTHESIS_NOT_FOUND",
    "message": "No hypothesis found for investigation '33333333-3333-3333-3333-333333333333'.",
    "request_id": "4167831d-cb56-46b0-b616-6714138a77c7"
  }
}
```

---

### 3.5 Phase 3 Error Codes
- `INVESTIGATION_PRECONDITION_FAILED` (400): Reproduction run is missing or verdict is not `REPRODUCED`.
- `AI_RESPONSE_INVALID` (502): AI provider response could not be parsed as valid JSON or extracted from markdown fences.
- `AI_RESPONSE_SCHEMA_INVALID` (502): AI response failed Pydantic schema validation.
- `AI_CONTEXT_BUILD_FAILED` (500): Failed to extract or bound repository context files.
- `AI_PROVIDER_UNAVAILABLE` (503): Nebius Token Factory connection failed or timed out.
- `HYPOTHESIS_NOT_FOUND` (404): No hypothesis recorded for the requested investigation.

---

### 3.6 Regression Test Generation & Verification Endpoints (Phase 4)

#### Generate & Verify Regression Test
`POST /api/v1/investigations/{investigation_id}/regression-test`

Synthesizes an untrusted pytest regression test targeting the Phase 3 causal hypothesis, executes deterministic AST/path safety validation, writes the test into an isolated workspace containing the **unpatched** repository, and deterministically verifies whether it fails as expected.

**Preconditions:**
- Investigation must be in `INVESTIGATING` status.
- A valid Phase 3 hypothesis must exist.
- Associated reproduction run must be `REPRODUCED`.
- Returns `400 REGRESSION_PRECONDITION_FAILED` if preconditions are unmet.

**Idempotency:**
- If a valid `REGRESSION_PROVEN` test already exists for the current hypothesis, returns the existing record without re-invoking the model.

**Response (200 OK):**
```json
{
  "id": "99999999-9999-9999-9999-999999999999",
  "investigation_id": "33333333-3333-3333-3333-333333333333",
  "hypothesis_id": "88888888-8888-8888-8888-888888888888",
  "test_path": "tests/test_regression.py",
  "framework": "pytest",
  "language": "python",
  "description": "Verifies that divide(10, 2) performs division and returns 5 rather than multiplication.",
  "test_content": "from src.calculator import divide\n\ndef test_divide_regression():\n    assert divide(10, 2) == 5\n",
  "target_symbol": "divide",
  "target_file": "src/calculator.py",
  "expected_failure_reason": "divide(10, 2) evaluates to 20 instead of 5, triggering assertion failure",
  "generation_status": "GENERATED",
  "verification_status": "REGRESSION_PROVEN",
  "verification": {
    "id": "aaaa1111-aaaa-1111-aaaa-1111aaaaaaaa",
    "command": "pytest tests/test_regression.py",
    "status": "REGRESSION_PROVEN",
    "exit_code": 1,
    "duration_ms": 118,
    "failure_classification": "ASSERTION_FAILURE",
    "stdout": "============================= test session starts ==============================\nFAILED tests/test_regression.py::test_divide_regression - assert 20 == 5\n============================== 1 failed in 0.12s ===============================",
    "stderr": "",
    "timed_out": false,
    "created_at": "2026-10-28T01:00:00Z",
    "completed_at": "2026-10-28T01:00:01Z"
  },
  "created_at": "2026-10-28T01:00:00Z",
  "verified_at": "2026-10-28T01:00:01Z"
}
```

---

#### Get Regression Test & Verification Evidence
`GET /api/v1/investigations/{investigation_id}/regression-test`

Retrieves the latest generated regression test and associated sandbox verification run.

**Response (200 OK):**
Same as `POST /regression-test` response body.

**Response (404 Not Found):**
```json
{
  "error": {
    "code": "REGRESSION_TEST_NOT_FOUND",
    "message": "No regression test found for investigation '33333333-3333-3333-3333-333333333333'.",
    "request_id": "4167831d-cb56-46b0-b616-6714138a77c7"
  }
}
```

---

### 3.7 Phase 4 Error Codes
- `REGRESSION_PRECONDITION_FAILED` (400): Missing hypothesis, invalid state, or unverified reproduction run.
- `REGRESSION_TEST_INVALID` (400): Proposed test path or content violated structural constraints.
- `REGRESSION_SECURITY_VIOLATION` (400): AI proposed test contains dangerous AST nodes (`subprocess`, `socket`, `eval`, `os.system`).
- `REGRESSION_SYNTAX_ERROR` (400): AI proposed test failed Python AST syntax compilation.
- `REGRESSION_TEST_NOT_FOUND` (404): No regression test has been generated for the investigation.

---

### 3.8 Patch Generation & Candidate Validation Endpoints (Phase 5)

#### Generate & Validate Patch Candidate
`POST /api/v1/investigations/{investigation_id}/patch`

Synthesizes a minimal unified diff candidate patch targeting the proven root cause, validates syntax, hunk bounds, path traversal, test immutability, scope boundary, and dangerous code patterns, and persists the candidate record.

**Preconditions:**
- Investigation must be in `VERIFYING` status.
- A valid Phase 3 hypothesis must exist.
- A valid Phase 4 regression test must exist with `REGRESSION_PROVEN` status.
- Associated reproduction run must be `REPRODUCED`.
- Returns `400 PATCH_PRECONDITION_FAILED` if preconditions are unmet.

**Idempotency:**
- If a valid `VALIDATED` patch candidate already exists for the current proven regression test, returns the existing record without re-invoking the model.

**Response (200 OK):**
```json
{
  "id": "55555555-5555-5555-5555-555555555555",
  "investigation_id": "33333333-3333-3333-3333-333333333333",
  "hypothesis_id": "88888888-8888-8888-8888-888888888888",
  "regression_test_id": "99999999-9999-9999-9999-999999999999",
  "status": "VALIDATED",
  "description": "Correct the divide function to perform mathematical division rather than multiplication.",
  "patch_format": "unified_diff",
  "patch_content": "--- a/src/calculator.py\n+++ b/src/calculator.py\n@@ -1,2 +1,2 @@\n def divide(a, b):\n-    return a * b\n+    return a / b\n",
  "changed_files": [
    "src/calculator.py"
  ],
  "change_summary": [
    {
      "file": "src/calculator.py",
      "reason": "Replace incorrect multiplication operator (*) with division operator (/)."
    }
  ],
  "reasoning": "The proven regression test and hypothesis show divide(10, 2) evaluates to 20 instead of 5 because multiplication was used instead of division.",
  "verification_status": "NOT_VERIFIED",
  "model": "nvidia/Nemotron-3_5-Lightning",
  "provider": "nebius",
  "prompt_version": "evida-patch-generation-v1",
  "created_at": "2026-10-28T02:00:00Z"
}
```

---

#### Get Latest Patch Candidate
`GET /api/v1/investigations/{investigation_id}/patch`

Retrieves the latest persisted patch candidate record for the investigation.

**Response (200 OK):**
Same as `POST /patch` response body.

**Response (404 Not Found):**
```json
{
  "error": {
    "code": "PATCH_CANDIDATE_NOT_FOUND",
    "message": "No patch candidate found for investigation '33333333-3333-3333-3333-333333333333'.",
    "request_id": "4167831d-cb56-46b0-b616-6714138a77c7"
  }
}
```

---

### 3.9 Phase 5 Error Codes
- `PATCH_PRECONDITION_FAILED` (400): Missing hypothesis, missing proven regression test, or invalid lifecycle state.
- `INVALID_FORMAT` (400): Format is not unified diff or diff header is missing/corrupted.
- `MALFORMED_DIFF` (400): Diff contains mismatched declared files, malformed hunk lines, or invalid hunk count.
- `PATH_VIOLATION` (400): Path traversal (`..`) or absolute path detected in diff target.
- `TEST_MODIFICATION` (400): Patch attempted to modify files under `tests/` or the regression test.
- `SENSITIVE_FILE_MODIFICATION` (400): Patch attempted to modify `.env`, credentials, private keys, or Dockerfile.
- `OUT_OF_SCOPE_CHANGE` (400): Patch modified files outside the hypothesis-confirmed `affected_files`.
- `PATCH_TOO_LARGE` (400): Patch exceeds file limits (`MAX_PATCH_FILES`), hunk limits (`MAX_PATCH_HUNKS`), or byte limit (`MAX_GENERATED_PATCH_BYTES`).
- `FILE_NOT_FOUND` (400): Patch targets a file that does not exist in the original repository archive.
- `SECURITY_VIOLATION` (400): Patch introduces dangerous code patterns (`subprocess`, `socket`, `eval`, `os.system`).
- `PATCH_CANDIDATE_NOT_FOUND` (404): No patch candidate exists for the investigation.
- `AI_RESPONSE_SCHEMA_INVALID` (502): AI provider response failed Pydantic schema validation.
- `AI_RESPONSE_INVALID` (502): AI provider returned unparseable non-JSON text.
- `AI_PROVIDER_UNAVAILABLE` (503): Nebius AI API timeout or connectivity failure.

---

### 3.10 Phase 6 Deterministic Double Validation Endpoints

#### Execute Deterministic Double Validation
`POST /api/v1/investigations/{investigation_id}/verify-patch`

Executes deterministic double validation on the latest candidate patch inside an isolated ephemeral workspace. Reruns the proven regression test (Validation 1) and the repository baseline test suite (Validation 2). Verifies cryptographic source repository immutability.

**Preconditions:**
1. Investigation status must be `VERIFYING`.
2. Valid stored repository archive exists.
3. Reproduction status is `REPRODUCED`.
4. Causal hypothesis exists.
5. Proven regression test exists with status `REGRESSION_PROVEN`.
6. Validated candidate patch exists with status `VALIDATED`.

**Response (200 OK — Verified):**
```json
{
  "id": "66666666-6666-6666-6666-666666666666",
  "investigation_id": "33333333-3333-3333-3333-333333333333",
  "patch_candidate_id": "55555555-5555-5555-5555-555555555555",
  "regression_test_id": "99999999-9999-9999-9999-999999999999",
  "status": "VERIFIED",
  "verdict": "VERIFIED",
  "failure_classification": null,
  "patch_sha256": "3cb15bf6476e313ff83a2fc9aa30023069b2bebead8772a1548e6788db3d0407",
  "repository_sha256": "fa4aec473a843aa4d3a2df0840c192a2e28526c6f5d146b0ae7b7fabaf5280a9",
  "patch_application": {
    "status": "APPLIED",
    "exit_code": 0,
    "stdout": "Applied cleanly to src/calculator.py",
    "stderr": "",
    "duration_ms": 12.5,
    "modified_files": ["src/calculator.py"],
    "created_files": [],
    "deleted_files": []
  },
  "regression_execution": {
    "status": "PASSED",
    "command": "pytest tests/test_regression.py",
    "exit_code": 0,
    "stdout": "1 passed in 0.08s",
    "stderr": "",
    "duration_ms": 82.5
  },
  "baseline_execution": {
    "status": "PASSED",
    "command": "pytest",
    "exit_code": 0,
    "stdout": "1 passed in 0.09s",
    "stderr": "",
    "duration_ms": 91.0
  },
  "workspace_file_manifest": {
    "src/calculator.py": "a6b7...",
    "pyproject.toml": "682c..."
  },
  "source_integrity_verified": true,
  "created_at": "2026-10-28T10:15:30Z",
  "completed_at": "2026-10-28T10:15:32Z"
}
```

---

#### Get Latest Verification Evidence
`GET /api/v1/investigations/{investigation_id}/verification`

Retrieves the latest execution verification run for the investigation.

**Response (200 OK):**
Same structure as `POST /verify-patch`.

**Response (404 Not Found):**
```json
{
  "error": {
    "code": "VERIFICATION_RUN_NOT_FOUND",
    "message": "No verification evidence found for investigation '33333333-3333-3333-3333-333333333333'.",
    "request_id": "4167831d-cb56-46b0-b616-6714138a77c7"
  }
}
```

---

#### List All Verification Runs
`GET /api/v1/investigations/{investigation_id}/verifications`

Retrieves historical verification run records in descending chronological order.

**Response (200 OK):**
```json
[
  {
    "id": "66666666-6666-6666-6666-666666666666",
    "investigation_id": "33333333-3333-3333-3333-333333333333",
    "status": "VERIFIED",
    "verdict": "VERIFIED",
    "failure_classification": null,
    "source_integrity_verified": true,
    "created_at": "2026-10-28T10:15:30Z",
    "completed_at": "2026-10-28T10:15:32Z"
  }
]
```

---

### 3.11 Phase 6 Error Codes
- `INVESTIGATION_PRECONDITION_FAILED` (400): Missing required Phase 5 artifacts or investigation is not in status `VERIFYING`.
- `VERIFICATION_RUN_NOT_FOUND` (404): No verification run recorded for the investigation.
- `PATCH_APPLICATION_FAILED`: Candidate patch failed to apply to the extracted workspace cleanly.
- `REGRESSION_STILL_FAILING`: Candidate patch applied but the proven regression test continues to fail.
- `REGRESSION_EXECUTION_ERROR`: Error executing regression test inside the sandbox.
- `REGRESSION_TIMEOUT`: Regression test execution exceeded timeout threshold.
- `BASELINE_TEST_FAILURE`: Proven regression test passed, but repository baseline test suite failed.
- `BASELINE_EXECUTION_ERROR`: Error executing baseline test suite inside the sandbox.
- `BASELINE_TIMEOUT`: Baseline test suite execution exceeded timeout threshold.
- `SOURCE_INTEGRITY_VIOLATION`: The stored repository archive SHA-256 changed during verification.
- `UNEXPECTED_WORKSPACE_CHANGE`: Patch application modified files outside the declared scope or modified test directories.




