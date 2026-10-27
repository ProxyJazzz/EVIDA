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
    "code": "CONFIGURATION_ERROR",
    "message": "Required service configuration is missing.",
    "request_id": "4167831d-cb56-46b0-b616-6714138a77c7"
  }
}
```

---

## 3. Endpoints (Phase 0)

### 3.1 Health Probe
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

### 3.2 Readiness Probe
`GET /api/v1/health/ready`

Inspects runtime configuration and external service readiness (Supabase, Nebius AI). Does not crash during local development if optional services are unconfigured.

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

### 3.3 Investigations Placeholder (Foundation)
`GET /api/v1/investigations`

Lists current repair investigations for the authenticated tenant.

**Response (200 OK):**
```json
{
  "items": [],
  "total": 0
}
```
