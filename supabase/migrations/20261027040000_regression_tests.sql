-- EVIDA Phase 4: Regression Test Generation & Verification Migration
-- Version: 20261027040000
-- Description: Creates investigation_regression_tests and regression_verification_runs tables with strict RLS

CREATE TABLE IF NOT EXISTS public.investigation_regression_tests (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  investigation_id UUID NOT NULL REFERENCES public.investigations(id) ON DELETE CASCADE,
  hypothesis_id UUID NOT NULL REFERENCES public.investigation_hypotheses(id) ON DELETE CASCADE,
  test_path TEXT NOT NULL,
  test_content TEXT NOT NULL,
  framework TEXT NOT NULL DEFAULT 'pytest',
  language TEXT NOT NULL DEFAULT 'python',
  description TEXT NOT NULL,
  target_symbol TEXT,
  target_file TEXT,
  expected_failure_reason TEXT,
  status TEXT NOT NULL DEFAULT 'GENERATED',
  verification_status TEXT DEFAULT 'PENDING',
  verification_run_id UUID,
  model TEXT,
  provider TEXT,
  prompt_version TEXT NOT NULL DEFAULT 'evida-regression-test-v1',
  raw_response JSONB,
  input_tokens INTEGER,
  output_tokens INTEGER,
  latency_ms BIGINT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  verified_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_investigation_regression_tests_investigation_created
  ON public.investigation_regression_tests(investigation_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_investigation_regression_tests_hypothesis_id
  ON public.investigation_regression_tests(hypothesis_id);

ALTER TABLE public.investigation_regression_tests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view regression tests for their investigations"
  ON public.investigation_regression_tests
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = investigation_regression_tests.investigation_id
      AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert regression tests for their investigations"
  ON public.investigation_regression_tests
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = investigation_regression_tests.investigation_id
      AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update regression tests for their investigations"
  ON public.investigation_regression_tests
  FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = investigation_regression_tests.investigation_id
      AND p.user_id = auth.uid()
    )
  );

-- Verification Runs Table for deterministic test execution audit
CREATE TABLE IF NOT EXISTS public.regression_verification_runs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  investigation_id UUID NOT NULL REFERENCES public.investigations(id) ON DELETE CASCADE,
  regression_test_id UUID NOT NULL REFERENCES public.investigation_regression_tests(id) ON DELETE CASCADE,
  command TEXT NOT NULL,
  status TEXT NOT NULL,
  exit_code INTEGER,
  stdout TEXT,
  stderr TEXT,
  duration_ms INTEGER,
  timed_out BOOLEAN NOT NULL DEFAULT false,
  failure_classification TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_regression_verification_runs_investigation_created
  ON public.regression_verification_runs(investigation_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_regression_verification_runs_test_id
  ON public.regression_verification_runs(regression_test_id);

ALTER TABLE public.regression_verification_runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view verification runs for their investigations"
  ON public.regression_verification_runs
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = regression_verification_runs.investigation_id
      AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert verification runs for their investigations"
  ON public.regression_verification_runs
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = regression_verification_runs.investigation_id
      AND p.user_id = auth.uid()
    )
  );
