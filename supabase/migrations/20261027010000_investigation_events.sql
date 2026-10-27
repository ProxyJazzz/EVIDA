-- EVIDA Investigation Lifecycle Events Migration
-- Version: 20261027010000
-- Description: Creates investigation_events table, indexes, RLS policies, and updates status constraints

-- 1. Update investigations status check constraint to support Phase 1 canonical lifecycle states
ALTER TABLE public.investigations
  DROP CONSTRAINT IF EXISTS investigations_status_check;

ALTER TABLE public.investigations
  ADD CONSTRAINT investigations_status_check
  CHECK (status IN (
    'CREATED',
    'INGESTING',
    'REPRODUCING',
    'INVESTIGATING',
    'VERIFYING',
    'COMPLETED',
    'FAILED',
    'PENDING',
    'HYPOTHESIZING',
    'PATCHING',
    'VERIFIED',
    'UNVERIFIED'
  ));

ALTER TABLE public.investigations
  ALTER COLUMN status SET DEFAULT 'CREATED';

-- 2. Create investigation_events table
CREATE TABLE IF NOT EXISTS public.investigation_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  investigation_id UUID NOT NULL REFERENCES public.investigations(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  from_status TEXT,
  to_status TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Indexes for fast chronological timeline queries
CREATE INDEX IF NOT EXISTS idx_investigation_events_investigation_created
  ON public.investigation_events(investigation_id, created_at ASC);

CREATE INDEX IF NOT EXISTS idx_investigation_events_event_type
  ON public.investigation_events(event_type);

-- 4. Row Level Security on investigation_events
ALTER TABLE public.investigation_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view events for their investigations"
  ON public.investigation_events
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = investigation_events.investigation_id
      AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert events for their investigations"
  ON public.investigation_events
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = investigation_events.investigation_id
      AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete events for their investigations"
  ON public.investigation_events
  FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.investigations i
      JOIN public.repositories r ON r.id = i.repository_id
      JOIN public.projects p ON p.id = r.project_id
      WHERE i.id = investigation_events.investigation_id
      AND p.user_id = auth.uid()
    )
  );
