-- EVIDA Development Seed Data
-- Creates sample profile, project, repository, and investigation records for local testing

-- Ensure test user exists in auth.users (mocking standard supabase auth uid)
INSERT INTO auth.users (id, email)
VALUES ('00000000-0000-0000-0000-000000000001', 'dev@evida.local')
ON CONFLICT (id) DO NOTHING;

-- Seed Profile
INSERT INTO public.profiles (id, full_name, avatar_url)
VALUES (
  '00000000-0000-0000-0000-000000000001',
  'Lead Systems Engineer',
  'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100'
)
ON CONFLICT (id) DO UPDATE SET full_name = EXCLUDED.full_name;

-- Seed Project
INSERT INTO public.projects (id, user_id, name, description)
VALUES (
  '11111111-1111-1111-1111-111111111111',
  '00000000-0000-0000-0000-000000000001',
  'Core Engine Verification',
  'Core backend verification suite for automated software repair benchmarks.'
)
ON CONFLICT (id) DO NOTHING;

-- Seed Repository
INSERT INTO public.repositories (id, project_id, name, remote_url, default_branch)
VALUES (
  '22222222-2222-2222-2222-222222222222',
  '11111111-1111-1111-1111-111111111111',
  'demo-service',
  'https://github.com/evida-ai/demo-service.git',
  'main'
)
ON CONFLICT (id) DO NOTHING;

-- Seed Initial Investigation
INSERT INTO public.investigations (
  id,
  repository_id,
  issue_title,
  issue_description,
  status,
  hypothesis,
  regression_test_code,
  candidate_patch,
  verification_evidence
)
VALUES (
  '33333333-3333-3333-3333-333333333333',
  '22222222-2222-2222-2222-222222222222',
  'Fix ZeroDivisionError in calculation endpoint',
  'When input denominator is 0, endpoint raises unhandled 500 ZeroDivisionError instead of returning 400 Bad Request.',
  'CREATED',
  '{"summary": "Zero check missing in calculate() method.", "confidence": 0.95}'::jsonb,
  NULL,
  NULL,
  NULL
)
ON CONFLICT (id) DO NOTHING;

-- Seed Investigation Event
INSERT INTO public.investigation_events (
  id,
  investigation_id,
  event_type,
  from_status,
  to_status,
  metadata
)
VALUES (
  '44444444-4444-4444-4444-444444444444',
  '33333333-3333-3333-3333-333333333333',
  'INVESTIGATION_CREATED',
  NULL,
  'CREATED',
  '{"source": "seed_data"}'::jsonb
)
ON CONFLICT (id) DO NOTHING;
