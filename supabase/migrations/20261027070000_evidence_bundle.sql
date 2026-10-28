-- EVIDA Phase 7: Evidence Bundle, Provenance & Audit System Migration
-- Version: 20261027070000
-- Description: Creates investigation_evidence table with strict append-only RLS and provenance indexes

CREATE TABLE IF NOT EXISTS public.investigation_evidence (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  investigation_id UUID NOT NULL REFERENCES public.investigations(id) ON DELETE CASCADE,
  evidence_type TEXT NOT NULL,
  provenance TEXT NOT NULL,
  source_phase INTEGER NOT NULL,
  source_entity_type TEXT NOT NULL,
  source_entity_id UUID,
  title TEXT NOT NULL,
  description TEXT,
  data JSONB NOT NULL DEFAULT '{}'::jsonb,
  content_sha256 TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Query optimization indexes
CREATE INDEX IF NOT EXISTS idx_investigation_evidence_investigation_created
  ON public.investigation_evidence(investigation_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_investigation_evidence_type
  ON public.investigation_evidence(investigation_id, evidence_type);

CREATE INDEX IF NOT EXISTS idx_investigation_evidence_source_entity
  ON public.investigation_evidence(source_entity_type, source_entity_id);

-- Row Level Security (RLS) enforcing strict multi-tenant isolation
ALTER TABLE public.investigation_evidence ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view evidence for their investigations"
  ON public.investigation_evidence
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = investigation_evidence.investigation_id
      AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert evidence for their investigations"
  ON public.investigation_evidence
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = investigation_evidence.investigation_id
      AND p.user_id = auth.uid()
    )
  );

-- Note: No UPDATE or DELETE policy is defined. Records are strictly append-only.

