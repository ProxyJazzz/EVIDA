# EVIDA — Database Architecture & Schema Specification

## 1. Overview & Principles

EVIDA uses **Supabase PostgreSQL** as its single source of truth for all persistent application state.

### Architectural Rules:
- **No Local Application DB:** SQLite or in-memory application databases are strictly prohibited in production.
- **UUID Primary Keys:** All tables use `uuid_generate_v4()` for distributed key generation.
- **Auditing Timestamps:** Every table tracks `created_at` and `updated_at` (managed via triggers).
- **Row Level Security (RLS):** All tables enforce strict RLS policies ensuring tenant/user isolation.
- **Defense-in-Depth:** The FastAPI backend is the primary authority for authorization; RLS provides database-level defense-in-depth.

---

## 2. Core Entities (Phase 0 Migration)

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
                            └──────────────┘
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
- `status` (TEXT, default `'PENDING'`)
  - Permitted values: `'PENDING'`, `'REPRODUCING'`, `'INVESTIGATING'`, `'PATCHING'`, `'VERIFYING'`, `'VERIFIED'`, `'UNVERIFIED'`, `'FAILED'`
- `hypothesis` (JSONB)
- `regression_test_code` (TEXT)
- `candidate_patch` (TEXT)
- `verification_evidence` (JSONB)
- `created_at` (TIMESTAMPTZ, default `now()`)
- `updated_at` (TIMESTAMPTZ, default `now()`)

---

## 3. Row Level Security Policies

Every table has RLS enabled.
- `profiles`: Users can select and update only their own profile (`auth.uid() = id`).
- `projects`: Users can access only projects they own (`auth.uid() = user_id`).
- `repositories`: Users can access repositories belonging to their projects.
- `investigations`: Users can access investigations belonging to their repositories.
- Open policies such as `USING (true)` are prohibited.
