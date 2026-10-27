"""Tests validating Supabase migration SQL schema and security constraints."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = (
    PROJECT_ROOT / "supabase" / "migrations" / "20261027000000_initial_schema.sql"
)


def test_initial_migration_exists_and_valid():
    assert MIGRATION_PATH.exists(), "Initial migration file must exist"
    content = MIGRATION_PATH.read_text(encoding="utf-8")

    # Required tables
    assert "public.profiles" in content
    assert "public.projects" in content
    assert "public.repositories" in content
    assert "public.investigations" in content

    # Row Level Security enabled on all tables
    assert "ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;" in content
    assert "ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;" in content
    assert "ALTER TABLE public.repositories ENABLE ROW LEVEL SECURITY;" in content
    assert "ALTER TABLE public.investigations ENABLE ROW LEVEL SECURITY;" in content

    # Disallow insecure open policies
    assert "USING (true)" not in content
    assert "WITH CHECK (true)" not in content
