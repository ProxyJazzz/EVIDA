import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import HomePage from "@/app/page";
import HealthPage from "@/app/health/page";

// Mock fetch globally for HealthPage
global.fetch = vi.fn().mockImplementation((url: string) => {
  if (url.includes("/api/v1/health/ready")) {
    return Promise.resolve({
      ok: true,
      json: () =>
        Promise.resolve({
          status: "ready",
          service: "evida-api",
          version: "0.1.0",
          checks: {
            database: { configured: true, provider: "supabase" },
            ai_provider: { configured: true, provider: "nebius", model: "nvidia/Nemotron-3_5-Lightning" },
            sandbox: { ready: true, runner: "isolated_process" },
          },
        }),
    });
  }
  return Promise.resolve({
    ok: true,
    json: () =>
      Promise.resolve({
        status: "ok",
        service: "evida-api",
        version: "0.1.0",
      }),
  });
});

import DashboardPage from "@/app/dashboard/page";
import InvestigationPage from "@/app/investigations/[id]/page";

describe("Frontend Foundation Tests", () => {
  it("renders the landing page with EVIDA core identity and maxim", () => {
    render(<HomePage />);
    expect(screen.getByText(/AI PROPOSES\. EVIDENCE DECIDES\./i)).toBeDefined();
    expect(screen.getByText(/Evidence-Driven/i)).toBeDefined();
  });

  it("renders the health probe page", async () => {
    render(<HealthPage />);
    expect(screen.getByText(/System Health & Readiness/i)).toBeDefined();
    expect(screen.getByText(/Frontend Web Client/i)).toBeDefined();
  });

  it("renders the dashboard page with Phase 2 investigation ledger", () => {
    render(<DashboardPage />);
    expect(screen.getByText(/Repair Investigations Dashboard/i)).toBeDefined();
    expect(screen.getByText(/broken_python_repo.zip/i)).toBeDefined();
    expect(screen.getByText(/Phase 2 Pipeline Active/i)).toBeDefined();
  });

  it("renders the Phase 3 investigation detail view with repository, reproduction evidence, and AI hypothesis", async () => {
    const Component = await InvestigationPage({ params: { id: "33333333-3333-3333-3333-333333333333" } });
    render(Component);
    expect(screen.getByText(/Investigation #33333333/i)).toBeDefined();
    expect(screen.getByText(/Repository Archive/i)).toBeDefined();
    expect(screen.getByText(/Failure Reproduction/i)).toBeDefined();
    expect(screen.getAllByText(/pytest tests\/test_bug\.py/i).length).toBeGreaterThan(0);

    // Phase 3: AI Investigation & Hypothesis Engine
    expect(screen.getByText(/AI Investigation/i)).toBeDefined();
    expect(screen.getByText(/Proposed Root Cause/i)).toBeDefined();
    expect(screen.getAllByText(/nvidia\/Nemotron-3_5-Lightning/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/99%/i)).toBeDefined();
    expect(screen.getByText(/Root Cause Candidate/i)).toBeDefined();
    expect(screen.getAllByText(/src\/calculator\.py/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Recommended Next Action/i)).toBeDefined();
    expect(screen.getByText(/Generate regression test/i)).toBeDefined();

    // Phase 4: Regression Test Generation & Deterministic Verification
    expect(screen.getAllByText(/Regression Test/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/AI PROPOSED REGRESSION TEST/i)).toBeDefined();
    expect(screen.getAllByText(/DETERMINISTIC VERIFICATION/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/REGRESSION PROVEN/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/tests\/test_regression\.py/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/ASSERTION_FAILURE/i)).toBeDefined();
    expect(screen.getAllByText(/EVIDA Invariant/i).length).toBeGreaterThan(0);

    // Phase 5: Patch Generation & Candidate Validation
    expect(screen.getAllByText(/Patch Candidate/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/AI PROPOSED PATCH/i)).toBeDefined();
    expect(screen.getAllByText(/NOT VERIFIED/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/VALIDATED/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/UNIFIED DIFF PREVIEW/i)).toBeDefined();
    expect(screen.getByText(/PATCH_VALIDATED ≠ BUG_FIXED/i)).toBeDefined();
    expect(screen.getByText(/Phase 5 Safety Guarantee/i)).toBeDefined();

    // Phase 6: Deterministic Verification & Double Validation
    expect(screen.getByText(/Phase 6 — Deterministic Verification & Double Validation/i)).toBeDefined();
    expect(screen.getByText(/Double Validation Rule Satisfied: VERIFIED/i)).toBeDefined();
    expect(screen.getByText(/Applied successfully/i)).toBeDefined();
    expect(screen.getByText(/Existing Test Suite/i)).toBeDefined();
    expect(screen.getAllByText(/The original repository artifact remained unchanged/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/EVIDA Evidence Chain: AI Proposal vs. Deterministic Evidence/i)).toBeDefined();
    expect(screen.getAllByText(/DETERMINISTIC EVIDENCE/i).length).toBeGreaterThan(0);

    // Phase 7: Evidence Bundle, Provenance & Audit System
    expect(screen.getByText(/Phase 7 — Evidence Bundle, Provenance & Audit System/i)).toBeDefined();
    expect(screen.getByText(/AUDITABLE RECORD/i)).toBeDefined();
    expect(screen.getByText(/Export Bundle \(\.json\)/i)).toBeDefined();
    expect(screen.getByText(/Evidence Bundle SHA-256:/i)).toBeDefined();
    expect(screen.getByText(/Provenance Taxonomy/i)).toBeDefined();
    expect(screen.getAllByText(/AI_PROPOSAL/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/DETERMINISTIC_EXECUTION/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/CRYPTOGRAPHIC_INTEGRITY/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Double-Validation Authoritative Confirmation Checklist/i)).toBeDefined();
    expect(screen.getByText(/100% EVIDENCE SATISFIED/i)).toBeDefined();
    expect(screen.getByText(/Evidence Chain Items/i)).toBeDefined();
  });
});
