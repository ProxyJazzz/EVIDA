-- EVIDA Phase 3: AI Investigation & Hypothesis Engine Migration
-- Version: 20261027030000
-- Description: Creates investigation_hypotheses table for persisting structured AI hypotheses with strict RLS

CREATE TABLE IF NOT EXISTS public.investigation_hypotheses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  investigation_id UUID NOT NULL REFERENCES public.investigations(id) ON DELETE CASCADE,
  reproduction_run_id UUID NOT NULL REFERENCES public.reproduction_runs(id) ON DELETE CASCADE,
  model TEXT NOT NULL,
  provider TEXT NOT NULL,
  hypothesis TEXT NOT NULL,
  confidence DOUBLE PRECISION CHECK (confidence >= 0.0 AND confidence <= 1.0),
  root_cause JSONB NOT NULL DEFAULT '{}'::jsonb,
  affected_files JSONB NOT NULL DEFAULT '[]'::jsonb,
  evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
  recommended_next_action TEXT,
  raw_response JSONB,
  prompt_version TEXT NOT NULL,
  input_tokens INTEGER,
  output_tokens INTEGER,
  latency_ms BIGINT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Compound index for fast lookup of latest hypothesis per investigation
CREATE INDEX IF NOT EXISTS idx_investigation_hypotheses_investigation_created
  ON public.investigation_hypotheses(investigation_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_investigation_hypotheses_reproduction_run_id
  ON public.investigation_hypotheses(reproduction_run_id);

-- Enable Row Level Security
ALTER TABLE public.investigation_hypotheses ENABLE ROW LEVEL SECURITY;

-- RLS Policies deriving tenant ownership through investigation -> project -> user
CREATE POLICY "Users can view hypotheses for their investigations"
  ON public.investigation_hypotheses
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = investigation_hypotheses.investigation_id
      AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert hypotheses for their investigations"
  ON public.investigation_hypotheses
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = investigation_hypotheses.investigation_id
      AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete hypotheses for their investigations"
  ON public.investigation_hypotheses
  FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = investigation_hypotheses.investigation_id
      AND p.user_id = auth.uid()
    )
  );
