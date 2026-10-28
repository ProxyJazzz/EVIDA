# EVIDA — Database Architecture & Schema Specification

## 1. Overview & Principles

EVIDA uses **Supabase PostgreSQL** as its single source of truth for all persistent application state.

### Architectural Rules:
- **No Local Application DB in Production:** Persistent state belongs exclusively in PostgreSQL.
- **UUID Primary Keys:** All tables use `uuid_generate_v4()` for distributed key generation.
- **Auditing Timestamps:** Every table tracks `created_at` and `updated_at` (managed via triggers).
- **Row Level Security (RLS):** All tables enforce strict RLS policies ensuring tenant/user isolation.
- **Defense-in-Depth:** The FastAPI backend is the primary authority for authorization; RLS provides database-level defense-in-depth.

---

## 2. Core Entities

```text
  ┌──────────────┐          ┌──────────────┐
  │   profiles   │ 1 ──── * │   projects   │
  └──────────────┘          └──────┬───────┘
                                   │ 1
                                   │
                                   │ *
                            ┌──────┴───────┐
                            │ repositories │
                            └──────┬───────┘
                                   │ 1
                                   │
                                   │ *
                            ┌──────┴───────┐
                            │investigations│
                            └──────┬───────┘
                                   │ 1
                                   │
                                   │ *
                       ┌───────────┴──────────┐
                       │ investigation_events │
                       └──────────────────────┘
```

### 2.1 `profiles`
Links to Supabase `auth.users` to store user metadata.
- `id` (UUID, PK, references `auth.users(id) ON DELETE CASCADE`)
- `full_name` (TEXT)
- `avatar_url` (TEXT)
- `created_at` (TIMESTAMPTZ, default `now()`)
- `updated_at` (TIMESTAMPTZ, default `now()`)

### 2.2 `projects`
Organizational workspace container for software repositories.
- `id` (UUID, PK, default `uuid_generate_v4()`)
- `user_id` (UUID, FK -> `profiles(id)`)
- `name` (TEXT, NOT NULL)
- `description` (TEXT)
- `created_at` (TIMESTAMPTZ, default `now()`)
- `updated_at` (TIMESTAMPTZ, default `now()`)

### 2.3 `repositories`
Registered target code repositories for automated repair.
- `id` (UUID, PK, default `uuid_generate_v4()`)
- `project_id` (UUID, FK -> `projects(id) ON DELETE CASCADE`)
- `name` (TEXT, NOT NULL)
- `remote_url` (TEXT)
- `default_branch` (TEXT, default `'main'`)
- `created_at` (TIMESTAMPTZ, default `now()`)
- `updated_at` (TIMESTAMPTZ, default `now()`)

### 2.4 `investigations`
Tracks an autonomous repair investigation and its verification lifecycle.
- `id` (UUID, PK, default `uuid_generate_v4()`)
- `repository_id` (UUID, FK -> `repositories(id) ON DELETE CASCADE`)
- `issue_title` (TEXT, NOT NULL)
- `issue_description` (TEXT)
- `status` (TEXT, default `'CREATED'`)
  - Permitted values: `'CREATED'`, `'INGESTING'`, `'REPRODUCING'`, `'INVESTIGATING'`, `'VERIFYING'`, `'COMPLETED'`, `'FAILED'` (and compatibility states)
- `hypothesis` (JSONB)
- `regression_test_code` (TEXT)
- `candidate_patch` (TEXT)
- `verification_evidence` (JSONB)
- `created_at` (TIMESTAMPTZ, default `now()`)
- `updated_at` (TIMESTAMPTZ, default `now()`)

### 2.5 `investigation_events` (Added in Phase 1)
Immutable audit ledger capturing every lifecycle state transition and milestone.
- `id` (UUID, PK, default `uuid_generate_v4()`)
- `investigation_id` (UUID, FK -> `investigations(id) ON DELETE CASCADE`, NOT NULL)
- `event_type` (TEXT, NOT NULL)
  - Values: `'INVESTIGATION_CREATED'`, `'INVESTIGATION_STARTED'`, `'STATE_TRANSITIONED'`, `'INVESTIGATION_COMPLETED'`, `'INVESTIGATION_FAILED'`
- `from_status` (TEXT, nullable on creation)
- `to_status` (TEXT, NOT NULL)
- `metadata` (JSONB, default `'{}'::jsonb`)
- `created_at` (TIMESTAMPTZ, default `now()`, NOT NULL)

**Indexes:**
- `idx_investigation_events_investigation_created`: `(investigation_id, created_at ASC)` for fast chronological timeline querying.
- `idx_investigation_events_event_type`: `(event_type)` for event classification indexing.

---

### 2.6 `patch_verification_runs` (Added in Phase 6)
Append-only double validation execution evidence capturing patch application, regression verification, baseline test suite results, and source integrity proofs.
- `id` (UUID, PK, default `gen_random_uuid()`)
- `investigation_id` (UUID, FK -> `investigations(id) ON DELETE CASCADE`, NOT NULL)
- `patch_candidate_id` (UUID, FK -> `patch_candidates(id) ON DELETE CASCADE`, NOT NULL)
- `regression_test_id` (UUID, FK -> `investigation_regression_tests(id) ON DELETE CASCADE`, NOT NULL)
- `status` (TEXT, NOT NULL)
- `patch_sha256` (TEXT, NOT NULL)
- `repository_sha256` (TEXT, NOT NULL)
- `patch_application_status` (TEXT, NOT NULL)
- `patch_application_exit_code` (INTEGER, nullable)
- `patch_application_stdout` (TEXT, default `''`)
- `patch_application_stderr` (TEXT, default `''`)
- `regression_status` (TEXT, NOT NULL)
- `regression_exit_code` (INTEGER, nullable)
- `regression_stdout` (TEXT, default `''`)
- `regression_stderr` (TEXT, default `''`)
- `regression_duration_ms` (INTEGER, default `0`)
- `baseline_status` (TEXT, NOT NULL)
- `baseline_command` (TEXT, NOT NULL, default `'pytest'`)
- `baseline_exit_code` (INTEGER, nullable)
- `baseline_stdout` (TEXT, default `''`)
- `baseline_stderr` (TEXT, default `''`)
- `baseline_duration_ms` (INTEGER, default `0`)
- `verdict` (TEXT, NOT NULL)
- `failure_classification` (TEXT, nullable)
- `workspace_file_manifest` (JSONB, default `'{}'::jsonb`)
- `created_at` (TIMESTAMPTZ, default `now()`, NOT NULL)
- `completed_at` (TIMESTAMPTZ, default `now()`, NOT NULL)

**Indexes:**
- `idx_patch_verification_runs_investigation_created`: `(investigation_id, created_at DESC)`
- `idx_patch_verification_runs_candidate`: `(patch_candidate_id)`
- `idx_patch_verification_runs_regression`: `(regression_test_id)`

---

## 3. Row Level Security Policies

Every table has RLS enabled.
- `profiles`: Users can select and update only their own profile (`auth.uid() = id`).
- `projects`: Users can access only projects they own (`auth.uid() = user_id`).
- `repositories`: Users can access repositories belonging to their projects.
- `investigations`: Users can access investigations belonging to their repositories.
- `investigation_events`: Users can view and insert events only for investigations belonging to their repositories.
- `patch_verification_runs`: Users can view verification evidence only for investigations belonging to their projects (`investigation -> project -> auth.uid() = user_id`).
- Insecure open policies (`USING (true)`) are strictly forbidden across all tables.
