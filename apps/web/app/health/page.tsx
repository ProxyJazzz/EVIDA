"use client";

import { useEffect, useState } from "react";
import { Activity, CheckCircle2, XCircle, RefreshCw, Server, Globe } from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import type { HealthCheckResponse, ReadinessCheckResponse } from "@evida/shared/types";
import { getBackendHealth, getBackendReadiness } from "@/lib/api";

export default function HealthPage() {
  const [loading, setLoading] = useState(true);
  const [apiHealth, setApiHealth] = useState<HealthCheckResponse | null>(null);
  const [apiReadiness, setApiReadiness] = useState<ReadinessCheckResponse | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  const checkHealth = async () => {
    setLoading(true);
    setApiError(null);
    try {
      const [health, readiness] = await Promise.all([
        getBackendHealth(),
        getBackendReadiness(),
      ]);
      setApiHealth(health);
      setApiReadiness(readiness);
    } catch (err) {
      setApiError(err instanceof Error ? err.message : "Failed to connect to backend");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <div className="flex-1 max-w-4xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-12 space-y-8">
      <div className="flex items-center justify-between border-b border-surface-border pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <Activity className="w-6 h-6 text-emerald-400" />
            System Health & Readiness
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Real-time status of frontend client and FastAPI application backend.
          </p>
        </div>
        <button
          onClick={checkHealth}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-surface border border-surface-border hover:border-gray-500 text-sm font-medium text-gray-200 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Frontend Health Card */}
        <div className="p-6 rounded-xl border border-surface-border bg-surface/70 backdrop-blur-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Globe className="w-5 h-5 text-cyan-400" />
              <h2 className="font-semibold text-white">Frontend Web Client</h2>
            </div>
            <StatusBadge status="OK" />
          </div>
          <div className="space-y-2 text-xs font-mono text-gray-300">
            <div className="flex justify-between py-1 border-b border-surface-border">
              <span className="text-gray-400">Framework:</span>
              <span>Next.js 14 App Router</span>
            </div>
            <div className="flex justify-between py-1 border-b border-surface-border">
              <span className="text-gray-400">Runtime:</span>
              <span>React 18 + TypeScript Strict</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-gray-400">Supabase Client:</span>
              <span>@supabase/ssr (Anon Key)</span>
            </div>
          </div>
        </div>

        {/* Backend API Health Card */}
        <div className="p-6 rounded-xl border border-surface-border bg-surface/70 backdrop-blur-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Server className="w-5 h-5 text-emerald-400" />
              <h2 className="font-semibold text-white">FastAPI Backend API</h2>
            </div>
            {apiHealth ? (
              <StatusBadge status={apiHealth.status === "ok" ? "OK" : "ERROR"} />
            ) : apiError ? (
              <StatusBadge status="ERROR" />
            ) : (
              <StatusBadge status="INVESTIGATING" />
            )}
          </div>

          {apiError ? (
            <div className="p-3 rounded-lg bg-red-950/40 border border-red-800/50 text-xs font-mono text-red-300">
              <p className="font-semibold">Backend Unreachable:</p>
              <p className="mt-1 text-red-400">{apiError}</p>
              <p className="mt-2 text-gray-400 text-[11px]">
                Ensure FastAPI is running: `uvicorn app.main:app --port 8000`
              </p>
            </div>
          ) : apiHealth ? (
            <div className="space-y-2 text-xs font-mono text-gray-300">
              <div className="flex justify-between py-1 border-b border-surface-border">
                <span className="text-gray-400">Service:</span>
                <span>{apiHealth.service}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-surface-border">
                <span className="text-gray-400">Version:</span>
                <span>{apiHealth.version}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-gray-400">Readiness:</span>
                <span className="text-emerald-400">{apiReadiness?.status || "ready"}</span>
              </div>
            </div>
          ) : (
            <p className="text-xs text-gray-400">Probing backend health...</p>
          )}
        </div>
      </div>

      {/* External Dependencies Breakdown */}
      {apiReadiness?.checks && (
        <div className="p-6 rounded-xl border border-surface-border bg-surface/50 space-y-4">
          <h3 className="text-sm font-semibold text-gray-200">External Dependencies Configuration</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
            <div className="p-3 rounded-lg bg-background border border-surface-border">
              <p className="text-gray-400">Database</p>
              <p className="text-white font-medium mt-1">Supabase Postgres</p>
              <p className={`mt-2 ${apiReadiness.checks.database.configured ? "text-emerald-400" : "text-amber-400"}`}>
                {apiReadiness.checks.database.configured ? "● Configured" : "○ Not Configured (Dev)"}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-background border border-surface-border">
              <p className="text-gray-400">AI Provider</p>
              <p className="text-white font-medium mt-1">{apiReadiness.checks.ai_provider.provider.toUpperCase()}</p>
              <p className={`mt-2 ${apiReadiness.checks.ai_provider.configured ? "text-emerald-400" : "text-amber-400"}`}>
                {apiReadiness.checks.ai_provider.configured ? "● Configured" : "○ Mock Provider"}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-background border border-surface-border">
              <p className="text-gray-400">Sandbox</p>
              <p className="text-white font-medium mt-1">Isolated Process</p>
              <p className="mt-2 text-emerald-400">● Ready</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
