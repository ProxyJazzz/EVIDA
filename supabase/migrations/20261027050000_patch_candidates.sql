-- EVIDA Phase 5: Patch Generation & Candidate Validation Migration
-- Version: 20261027050000
-- Description: Creates patch_candidates table with strict RLS and compound indexes

CREATE TABLE IF NOT EXISTS public.patch_candidates (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  investigation_id UUID NOT NULL REFERENCES public.investigations(id) ON DELETE CASCADE,
  hypothesis_id UUID NOT NULL REFERENCES public.investigation_hypotheses(id) ON DELETE CASCADE,
  regression_test_id UUID NOT NULL REFERENCES public.investigation_regression_tests(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'GENERATED' CHECK (status IN ('GENERATED', 'VALIDATED', 'REJECTED')),
  description TEXT NOT NULL,
  patch_format TEXT NOT NULL DEFAULT 'unified_diff',
  patch_content TEXT NOT NULL,
  changed_files JSONB NOT NULL DEFAULT '[]'::jsonb,
  change_summary JSONB DEFAULT '[]'::jsonb,
  reasoning TEXT,
  validation_result TEXT,
  validation_errors JSONB DEFAULT '[]'::jsonb,
  model TEXT,
  provider TEXT,
  prompt_version TEXT NOT NULL DEFAULT 'evida-patch-generation-v1',
  raw_response JSONB,
  input_tokens INTEGER,
  output_tokens INTEGER,
  latency_ms BIGINT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  validated_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_patch_candidates_investigation_created
  ON public.patch_candidates(investigation_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_patch_candidates_regression_test_id
  ON public.patch_candidates(regression_test_id);

CREATE INDEX IF NOT EXISTS idx_patch_candidates_hypothesis_id
  ON public.patch_candidates(hypothesis_id);

ALTER TABLE public.patch_candidates ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view patch candidates for their investigations"
  ON public.patch_candidates
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = patch_candidates.investigation_id
      AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert patch candidates for their investigations"
  ON public.patch_candidates
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = patch_candidates.investigation_id
      AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update patch candidates for their investigations"
  ON public.patch_candidates
  FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = patch_candidates.investigation_id
      AND p.user_id = auth.uid()
    )
  );
