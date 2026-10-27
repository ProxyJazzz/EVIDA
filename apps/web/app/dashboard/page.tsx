import { ShieldCheck, Plus, Terminal, Clock, FolderGit2, AlertCircle } from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";

export default function DashboardPage() {
  return (
    <div className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Dashboard Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-surface-border pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <FolderGit2 className="w-6 h-6 text-emerald-400" />
            Repair Investigations Dashboard
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Autonomous defect reproduction, causal hypothesis, and verified patches.
          </p>
        </div>
        <button
          disabled
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-surface border border-surface-border text-sm font-medium text-gray-400 cursor-not-allowed opacity-60"
        >
          <Plus className="w-4 h-4" />
          <span>New Investigation (Phase 1)</span>
        </button>
      </div>

      {/* Overview Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="p-5 rounded-xl border border-surface-border bg-surface/60">
          <p className="text-xs font-mono text-gray-400 uppercase">Active Repositories</p>
          <p className="text-2xl font-bold text-white mt-1">1</p>
        </div>
        <div className="p-5 rounded-xl border border-surface-border bg-surface/60">
          <p className="text-xs font-mono text-gray-400 uppercase">Total Investigations</p>
          <p className="text-2xl font-bold text-white mt-1">1</p>
        </div>
        <div className="p-5 rounded-xl border border-surface-border bg-surface/60">
          <p className="text-xs font-mono text-emerald-400 uppercase">Verified Fixes</p>
          <p className="text-2xl font-bold text-emerald-400 mt-1">0</p>
        </div>
        <div className="p-5 rounded-xl border border-surface-border bg-surface/60">
          <p className="text-xs font-mono text-nvidia uppercase">NVIDIA Inference Model</p>
          <p className="text-sm font-mono font-bold text-gray-200 mt-2 truncate">
            Nemotron-3_5-Lightning
          </p>
        </div>
      </div>

      {/* Investigation Queue Shell Table */}
      <div className="rounded-xl border border-surface-border bg-surface/40 overflow-hidden">
        <div className="p-4 border-b border-surface-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-mono font-semibold text-gray-200 uppercase">
              Investigation Ledger
            </h2>
          </div>
          <span className="text-xs font-mono text-gray-400">Phase 0 Schema Shell</span>
        </div>

        <div className="divide-y divide-surface-border">
          <div className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-surface/60 transition-colors">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-gray-400">#INV-0001</span>
                <h3 className="font-semibold text-white text-sm">
                  Fix ZeroDivisionError in calculation endpoint
                </h3>
              </div>
              <p className="text-xs text-gray-400">
                Target Repo: <span className="font-mono text-gray-300">evida-ai/demo-service</span>
              </p>
            </div>
            <div className="flex items-center gap-4">
              <StatusBadge status="CREATED" />
              <span className="text-xs text-gray-500 font-mono">Ready for Phase 1</span>
            </div>
          </div>
        </div>

        <div className="p-4 bg-background/50 border-t border-surface-border flex items-center gap-2 text-xs text-gray-400">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            Phase 0 Foundation Active: Repositories and investigations are configured via Supabase schema and FastAPI contracts.
          </span>
        </div>
      </div>
    </div>
  );
}
