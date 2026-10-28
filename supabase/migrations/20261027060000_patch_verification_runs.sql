-- EVIDA Phase 6: Deterministic Patch Verification & Double Validation Migration
-- Version: 20261027060000
-- Description: Creates patch_verification_runs table with strict RLS and compound indexes

CREATE TABLE IF NOT EXISTS public.patch_verification_runs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  investigation_id UUID NOT NULL REFERENCES public.investigations(id) ON DELETE CASCADE,
  patch_candidate_id UUID NOT NULL REFERENCES public.patch_candidates(id) ON DELETE CASCADE,
  regression_test_id UUID NOT NULL REFERENCES public.investigation_regression_tests(id) ON DELETE CASCADE,
  status TEXT NOT NULL CHECK (status IN ('PENDING', 'PATCH_APPLIED', 'REGRESSION_RUNNING', 'REGRESSION_PASSED', 'BASELINE_RUNNING', 'VERIFIED', 'UNVERIFIED', 'FAILED')),
  patch_sha256 TEXT NOT NULL,
  repository_sha256 TEXT NOT NULL,
  patch_application_status TEXT NOT NULL,
  patch_application_exit_code INTEGER NOT NULL,
  patch_application_stdout TEXT,
  patch_application_stderr TEXT,
  regression_status TEXT NOT NULL,
  regression_exit_code INTEGER,
  regression_stdout TEXT,
  regression_stderr TEXT,
  regression_duration_ms INTEGER,
  baseline_status TEXT NOT NULL,
  baseline_command TEXT NOT NULL,
  baseline_exit_code INTEGER,
  baseline_stdout TEXT,
  baseline_stderr TEXT,
  baseline_duration_ms INTEGER,
  verdict TEXT NOT NULL CHECK (verdict IN ('VERIFIED', 'UNVERIFIED')),
  failure_classification TEXT,
  workspace_file_manifest JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Compound indexes for fast lookups and chronological queries
CREATE INDEX IF NOT EXISTS idx_patch_verification_runs_investigation_created
  ON public.patch_verification_runs(investigation_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_patch_verification_runs_candidate_id
  ON public.patch_verification_runs(patch_candidate_id);

CREATE INDEX IF NOT EXISTS idx_patch_verification_runs_verdict
  ON public.patch_verification_runs(verdict);

-- Row Level Security (RLS) enforcing strict multi-tenant isolation
ALTER TABLE public.patch_verification_runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view patch verification runs for their investigations"
  ON public.patch_verification_runs
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = patch_verification_runs.investigation_id
      AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert patch verification runs for their investigations"
  ON public.patch_verification_runs
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = patch_verification_runs.investigation_id
      AND p.user_id = auth.uid()
    )
  );
