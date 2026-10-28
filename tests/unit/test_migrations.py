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


def test_investigation_events_migration_exists_and_valid():
    events_migration = (
        PROJECT_ROOT
        / "supabase"
        / "migrations"
        / "20261027010000_investigation_events.sql"
    )
    assert events_migration.exists(), "Events migration file must exist"
    content = events_migration.read_text(encoding="utf-8")

    assert "public.investigation_events" in content
    assert (
        "ALTER TABLE public.investigation_events ENABLE ROW LEVEL SECURITY;" in content
    )
    assert "idx_investigation_events_investigation_created" in content
    assert "USING (true)" not in content
    assert "WITH CHECK (true)" not in content


def test_repository_and_reproduction_migration_exists_and_valid():
    repo_migration = (
        PROJECT_ROOT
        / "supabase"
        / "migrations"
        / "20261027020000_repository_and_reproduction.sql"
    )
    assert repo_migration.exists(), "Phase 2 repository migration file must exist"
    content = repo_migration.read_text(encoding="utf-8")

    assert "public.reproduction_runs" in content
    assert "ALTER TABLE public.reproduction_runs ENABLE ROW LEVEL SECURITY;" in content
    assert "idx_reproduction_runs_investigation_created" in content
    assert "idx_repositories_investigation_id" in content
    assert "USING (true)" not in content
    assert "WITH CHECK (true)" not in content


def test_investigation_hypotheses_migration_exists_and_valid():
    hypo_migration = (
        PROJECT_ROOT
        / "supabase"
        / "migrations"
        / "20261027030000_investigation_hypotheses.sql"
    )
    assert hypo_migration.exists(), "Phase 3 hypotheses migration file must exist"
    content = hypo_migration.read_text(encoding="utf-8")

    assert "public.investigation_hypotheses" in content
    assert (
        "ALTER TABLE public.investigation_hypotheses ENABLE ROW LEVEL SECURITY;"
        in content
    )
    assert "idx_investigation_hypotheses_investigation_created" in content
    assert "idx_investigation_hypotheses_reproduction_run_id" in content
    assert "USING (true)" not in content
    assert "WITH CHECK (true)" not in content


def test_regression_tests_migration_exists_and_valid():
    reg_migration = (
        PROJECT_ROOT / "supabase" / "migrations" / "20261027040000_regression_tests.sql"
    )
    assert reg_migration.exists(), "Phase 4 regression tests migration file must exist"
    content = reg_migration.read_text(encoding="utf-8")

    assert "public.investigation_regression_tests" in content
    assert "public.regression_verification_runs" in content
    assert (
        "ALTER TABLE public.investigation_regression_tests ENABLE ROW LEVEL SECURITY;"
        in content
    )
    assert (
        "ALTER TABLE public.regression_verification_runs ENABLE ROW LEVEL SECURITY;"
        in content
    )
    assert "idx_investigation_regression_tests_investigation_created" in content
    assert "idx_regression_verification_runs_investigation_created" in content
    assert "USING (true)" not in content
    assert "WITH CHECK (true)" not in content


def test_patch_candidates_migration_exists_and_valid():
    patch_migration = (
        PROJECT_ROOT / "supabase" / "migrations" / "20261027050000_patch_candidates.sql"
    )
    assert patch_migration.exists(), (
        "Phase 5 patch candidates migration file must exist"
    )
    content = patch_migration.read_text(encoding="utf-8")

    assert "public.patch_candidates" in content
    assert "ALTER TABLE public.patch_candidates ENABLE ROW LEVEL SECURITY;" in content
    assert "idx_patch_candidates_investigation_created" in content
    assert "idx_patch_candidates_regression_test_id" in content
    assert "USING (true)" not in content
    assert "WITH CHECK (true)" not in content


def test_patch_verification_runs_migration_exists_and_valid():
    pvr_migration = (
        PROJECT_ROOT
        / "supabase"
        / "migrations"
        / "20261027060000_patch_verification_runs.sql"
    )
    assert pvr_migration.exists(), (
        "Phase 6 patch verification runs migration file must exist"
    )
    content = pvr_migration.read_text(encoding="utf-8")

    assert "public.patch_verification_runs" in content
    assert (
        "ALTER TABLE public.patch_verification_runs ENABLE ROW LEVEL SECURITY;"
        in content
    )
    assert "idx_patch_verification_runs_investigation_created" in content
    assert "idx_patch_verification_runs_candidate_id" in content
    assert "idx_patch_verification_runs_verdict" in content
    assert "USING (true)" not in content
    assert "WITH CHECK (true)" not in content
