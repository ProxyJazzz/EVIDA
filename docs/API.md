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
