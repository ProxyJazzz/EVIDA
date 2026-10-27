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
});
