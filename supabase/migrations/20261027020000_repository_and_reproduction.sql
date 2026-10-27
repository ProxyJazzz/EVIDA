-- EVIDA Phase 2: Repository Ingestion & Failure Reproduction Migration
-- Version: 20261027020000
-- Description: Extends repositories with archive metadata and creates reproduction_runs table with RLS

-- 1. Extend repositories table with Phase 2 ingestion fields
ALTER TABLE public.repositories
  ADD COLUMN IF NOT EXISTS investigation_id UUID REFERENCES public.investigations(id) ON DELETE CASCADE,
  ADD COLUMN IF NOT EXISTS storage_path TEXT,
  ADD COLUMN IF NOT EXISTS archive_size_bytes BIGINT,
  ADD COLUMN IF NOT EXISTS archive_sha256 TEXT,
  ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'UPLOADED'
    CHECK (status IN ('UPLOADED', 'VALIDATING', 'VALIDATED', 'EXTRACTING', 'READY', 'FAILED'));

CREATE INDEX IF NOT EXISTS idx_repositories_investigation_id
  ON public.repositories(investigation_id);

-- 2. Create reproduction_runs table for execution evidence
CREATE TABLE IF NOT EXISTS public.reproduction_runs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  investigation_id UUID NOT NULL REFERENCES public.investigations(id) ON DELETE CASCADE,
  repository_id UUID NOT NULL REFERENCES public.repositories(id) ON DELETE CASCADE,
  command TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN (
    'PENDING',
    'RUNNING',
    'REPRODUCED',
    'NOT_REPRODUCED',
    'TIMEOUT',
    'EXECUTION_ERROR',
    'POLICY_BLOCKED'
  )),
  exit_code INTEGER,
  stdout TEXT,
  stderr TEXT,
  duration_ms BIGINT,
  timed_out BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

-- 3. Indexes for fast timeline and investigation lookup
CREATE INDEX IF NOT EXISTS idx_reproduction_runs_investigation_created
  ON public.reproduction_runs(investigation_id, created_at ASC);

CREATE INDEX IF NOT EXISTS idx_reproduction_runs_repository_id
  ON public.reproduction_runs(repository_id);

CREATE INDEX IF NOT EXISTS idx_reproduction_runs_status
  ON public.reproduction_runs(status);

-- 4. Row Level Security on reproduction_runs
ALTER TABLE public.reproduction_runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view reproduction runs for their investigations"
  ON public.reproduction_runs
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = reproduction_runs.investigation_id
      AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert reproduction runs for their investigations"
  ON public.reproduction_runs
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = reproduction_runs.investigation_id
      AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update reproduction runs for their investigations"
  ON public.reproduction_runs
  FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = reproduction_runs.investigation_id
      AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete reproduction runs for their investigations"
  ON public.reproduction_runs
  FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = reproduction_runs.investigation_id
      AND p.user_id = auth.uid()
    )
  );
