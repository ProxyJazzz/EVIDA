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
    expect(screen.getByText(/EVIDA Invariant/i)).toBeDefined();
  });
});
