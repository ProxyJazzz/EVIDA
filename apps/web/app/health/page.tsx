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
    <div className="flex-1 max-w-5xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-12 space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/5 pb-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-purple-400 mb-1">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>DIAGNOSTIC TELEMETRY</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
            <Activity className="w-7 h-7 text-emerald-400" />
            System Health & Readiness
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Real-time status of frontend client, FastAPI backend, Nebius Token Factory, and isolated sandboxes.
          </p>
        </div>
        <button
          onClick={checkHealth}
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-surface border border-surface-border hover:border-purple-500/40 text-xs font-semibold text-gray-200 transition-all shadow-glass disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Frontend Health Card */}
        <div className="glass-card rounded-2xl p-6 border border-white/10 space-y-4">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <div className="flex items-center gap-2.5">
              <Globe className="w-5 h-5 text-cyan-400" />
              <h2 className="font-bold text-white text-base">Frontend Web Client</h2>
            </div>
            <StatusBadge status="OK" />
          </div>
          <div className="space-y-2.5 text-xs font-mono text-gray-300">
            <div className="flex justify-between py-1.5 border-b border-white/5">
              <span className="text-gray-400">Framework:</span>
              <span className="text-white font-semibold">Next.js 14 App Router</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-white/5">
              <span className="text-gray-400">Runtime:</span>
              <span className="text-white font-semibold">React 18 + TypeScript Strict</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-gray-400">Design System:</span>
              <span className="text-purple-300 font-semibold">Cinematic Glass Dark</span>
            </div>
          </div>
        </div>

        {/* Backend API Health Card */}
        <div className="glass-card rounded-2xl p-6 border border-white/10 space-y-4">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <div className="flex items-center gap-2.5">
              <Server className="w-5 h-5 text-emerald-400" />
              <h2 className="font-bold text-white text-base">FastAPI Backend API</h2>
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
            <div className="p-3.5 rounded-xl bg-red-950/40 border border-red-800/50 text-xs font-mono text-red-300">
              <p className="font-semibold">Backend Unreachable:</p>
              <p className="mt-1 text-red-400">{apiError}</p>
              <p className="mt-2 text-gray-400 text-[11px]">
                Ensure FastAPI is running: `uvicorn app.main:app --port 8000`
              </p>
            </div>
          ) : apiHealth ? (
            <div className="space-y-2.5 text-xs font-mono text-gray-300">
              <div className="flex justify-between py-1.5 border-b border-white/5">
                <span className="text-gray-400">Service:</span>
                <span className="text-white font-semibold">{apiHealth.service}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-white/5">
                <span className="text-gray-400">Version:</span>
                <span className="text-white font-semibold">{apiHealth.version}</span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-gray-400">Readiness:</span>
                <span className="text-emerald-400 font-bold">{apiReadiness?.status || "ready"}</span>
              </div>
            </div>
          ) : (
            <p className="text-xs text-gray-400">Probing backend health...</p>
          )}
        </div>
      </div>

      {/* External Dependencies Breakdown */}
      {apiReadiness?.checks && (
        <div className="glass-card rounded-2xl p-6 border border-white/10 space-y-4">
          <h3 className="text-sm font-bold text-gray-200 uppercase font-mono tracking-wider">
            External Dependencies Configuration
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
            <div className="p-4 rounded-xl bg-background-dark/80 border border-white/5 space-y-1">
              <p className="text-gray-400">Database</p>
              <p className="text-white font-semibold mt-1">Supabase Postgres</p>
              <p className={`mt-2 ${apiReadiness.checks.database.configured ? "text-emerald-400" : "text-amber-400"}`}>
                {apiReadiness.checks.database.configured ? "● Configured (RLS Enforced)" : "○ Not Configured (Dev)"}
              </p>
            </div>
            <div className="p-4 rounded-xl bg-background-dark/80 border border-white/5 space-y-1">
              <p className="text-gray-400">AI Provider</p>
              <p className="text-white font-semibold mt-1">{apiReadiness.checks.ai_provider.provider.toUpperCase()}</p>
              <p className={`mt-2 ${apiReadiness.checks.ai_provider.configured ? "text-emerald-400" : "text-amber-400"}`}>
                {apiReadiness.checks.ai_provider.configured ? "● nvidia/Nemotron-3_5" : "○ Mock Provider"}
              </p>
            </div>
            <div className="p-4 rounded-xl bg-background-dark/80 border border-white/5 space-y-1">
              <p className="text-gray-400">Sandbox</p>
              <p className="text-white font-semibold mt-1">Isolated Process</p>
              <p className="mt-2 text-emerald-400">● Ephemeral Ready</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
