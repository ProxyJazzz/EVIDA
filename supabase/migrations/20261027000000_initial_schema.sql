-- EVIDA Initial Database Migration
-- Version: 20261027000000
-- Description: Establishes profiles, projects, repositories, and investigations with RLS

-- 1. Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Timestamp trigger function
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3. Profiles table
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own profile"
  ON public.profiles
  FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
  ON public.profiles
  FOR UPDATE
  USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
  ON public.profiles
  FOR INSERT
  WITH CHECK (auth.uid() = id);

-- 4. Projects table
CREATE TABLE IF NOT EXISTS public.projects (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_projects_user_id ON public.projects(user_id);

CREATE TRIGGER update_projects_updated_at
  BEFORE UPDATE ON public.projects
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();

ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own projects"
  ON public.projects
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own projects"
  ON public.projects
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own projects"
  ON public.projects
  FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own projects"
  ON public.projects
  FOR DELETE
  USING (auth.uid() = user_id);

-- 5. Repositories table
CREATE TABLE IF NOT EXISTS public.repositories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  remote_url TEXT,
  default_branch TEXT NOT NULL DEFAULT 'main',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_repositories_project_id ON public.repositories(project_id);

CREATE TRIGGER update_repositories_updated_at
  BEFORE UPDATE ON public.repositories
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();

ALTER TABLE public.repositories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view repositories in their projects"
  ON public.repositories
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.projects p
      WHERE p.id = repositories.project_id
      AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert repositories in their projects"
  ON public.repositories
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.projects p
      WHERE p.id = repositories.project_id
      AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update repositories in their projects"
  ON public.repositories
  FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.projects p
      WHERE p.id = repositories.project_id
      AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete repositories in their projects"
  ON public.repositories
  FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.projects p
      WHERE p.id = repositories.project_id
      AND p.user_id = auth.uid()
    )
  );

-- 6. Investigations table
CREATE TABLE IF NOT EXISTS public.investigations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  repository_id UUID NOT NULL REFERENCES public.repositories(id) ON DELETE CASCADE,
  issue_title TEXT NOT NULL,
  issue_description TEXT,
  status TEXT NOT NULL DEFAULT 'PENDING'
    CHECK (status IN (
      'PENDING',
      'REPRODUCING',
      'INVESTIGATING',
      'HYPOTHESIZING',
      'PATCHING',
      'VERIFYING',
      'VERIFIED',
      'UNVERIFIED',
      'FAILED'
    )),
  hypothesis JSONB,
  regression_test_code TEXT,
  candidate_patch TEXT,
  verification_evidence JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_investigations_repository_id ON public.investigations(repository_id);
CREATE INDEX IF NOT EXISTS idx_investigations_status ON public.investigations(status);

CREATE TRIGGER update_investigations_updated_at
  BEFORE UPDATE ON public.investigations
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();

ALTER TABLE public.investigations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view investigations in their repositories"
  ON public.investigations
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.repositories r
      JOIN public.projects p ON p.id = r.project_id
      WHERE r.id = investigations.repository_id
      AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert investigations in their repositories"
  ON public.investigations
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.repositories r
      JOIN public.projects p ON p.id = r.project_id
      WHERE r.id = investigations.repository_id
      AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update investigations in their repositories"
  ON public.investigations
  FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.repositories r
      JOIN public.projects p ON p.id = r.project_id
      WHERE r.id = investigations.repository_id
      AND p.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete investigations in their repositories"
  ON public.investigations
  FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.repositories r
      JOIN public.projects p ON p.id = r.project_id
      WHERE r.id = investigations.repository_id
      AND p.user_id = auth.uid()
    )
  );
