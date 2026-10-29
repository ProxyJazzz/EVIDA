import Link from "next/link";
import {
  FolderGit2,
  Terminal,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Play,
  Clock,
  Sparkles,
  ArrowRight,
  Filter,
  Search,
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { WorkflowNav } from "@/components/WorkflowNav";

export default function DashboardPage() {
  return (
    <div className="flex-1 flex flex-col">
      {/* Workflow Navigation */}
      <WorkflowNav activeScreen="dashboard" />

      {/* Main Canvas */}
      <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Dashboard Header */}
        <div className="tech-panel p-6 shadow-xs">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 border-b border-surface-border pb-4">
            <div>
              <div className="flex items-center space-x-2 text-xs font-mono text-blue-400">
                <span className="font-bold uppercase tracking-wider">Autonomous Defect Ledger</span>
                <span className="text-slate-600">·</span>
                <span className="text-slate-400">Scope: Multi-Tenant Isolated</span>
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-white mt-1 flex items-center gap-2">
                <FolderGit2 className="w-6 h-6 text-blue-400" />
                Repair Investigations Dashboard
              </h1>
              <p className="text-xs text-slate-400 mt-0.5 font-mono">
                Isolated defect reproduction, causal hypothesis, regression tests, and double-verified patches.
              </p>
            </div>

            <div className="text-left lg:text-right font-mono text-xs">
              <span className="inline-flex items-center px-2.5 py-1 rounded bg-surface-card text-slate-300 border border-surface-border">
                1 Investigation Active · Zero AI Self-Graded Fixes
              </span>
              <p className="text-[11px] text-slate-500 mt-1">
                Deterministic proof required for all state promotions
              </p>
            </div>
          </div>

          {/* Metric Cards (Modeled after preview.html 5-Status Distinct Category Chips) */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 text-xs font-mono">
            <div className="p-3.5 rounded bg-surface-card border border-surface-border">
              <span className="text-slate-400 block mb-1 uppercase tracking-wider text-[11px]">Active Repositories</span>
              <div className="text-2xl font-bold text-white">1</div>
              <p className="text-[11px] text-slate-400 mt-0.5">Python Workspace ZIP</p>
            </div>

            <div className="p-3.5 rounded bg-surface-card border border-surface-border">
              <span className="text-slate-400 block mb-1 uppercase tracking-wider text-[11px]">Total Investigations</span>
              <div className="text-2xl font-bold text-blue-400">1</div>
              <p className="text-[11px] text-slate-400 mt-0.5">INV-0001 (Active)</p>
            </div>

            <div className="p-3.5 rounded bg-surface-card border border-surface-border">
              <span className="text-slate-400 block mb-1 uppercase tracking-wider text-[11px]">Verified Fixes</span>
              <div className="text-2xl font-bold text-emerald-400">1</div>
              <p className="text-[11px] text-emerald-500/80 mt-0.5">Double validated (100%)</p>
            </div>

            <div className="p-3.5 rounded bg-surface-card border border-surface-border">
              <span className="text-slate-400 block mb-1 uppercase tracking-wider text-[11px]">NVIDIA Inference</span>
              <div className="text-sm font-bold text-slate-200 truncate mt-1">Nemotron-3_5</div>
              <p className="text-[11px] text-purple-400 mt-0.5">Nebius Token Factory</p>
            </div>
          </div>
        </div>

        {/* Prioritized Action Banner (Modeled after preview.html Prioritized Action List) */}
        <div className="tech-panel p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-surface-border pb-2.5">
            <div className="flex items-center space-x-2">
              <span className="text-amber-400 font-bold">⚡</span>
              <h2 className="text-xs font-mono font-bold text-white uppercase tracking-wide">
                Investigation Priority Action (Immediate Defect Impact)
              </h2>
            </div>
            <span className="text-xs font-mono text-slate-400">Deterministic proof ready</span>
          </div>

          <div className="p-3.5 rounded bg-surface-card border border-surface-border flex flex-col md:flex-row md:items-center md:justify-between gap-3 text-xs font-mono">
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider text-white bg-blue-600">
                  Active Run
                </span>
                <span className="font-bold text-white">#INV-0001</span>
                <span className="text-slate-600">·</span>
                <span className="text-slate-300">Arithmetic Division Regression in Calculator</span>
              </div>
              <p className="text-slate-400 mt-1 leading-relaxed font-sans text-xs">
                Candidate patch validated. Fresh ephemeral workspace double-validated against proven regression test and baseline suite.
              </p>
            </div>
            <div className="flex items-center space-x-3 shrink-0">
              <span className="text-emerald-400 font-bold text-xs">VERIFIED</span>
              <Link
                href="/investigations/33333333-3333-3333-3333-333333333333"
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-semibold"
              >
                Inspect Evidence →
              </Link>
            </div>
          </div>
        </div>

        {/* Scannable Investigations Table (Modeled after preview.html Scannable Findings Table) */}
        <div className="tech-panel overflow-hidden">
          <div className="p-3.5 border-b border-surface-border bg-surface-card/60 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 text-xs font-mono">
            <div className="flex items-center space-x-3">
              <span className="font-bold text-slate-300">Investigation Ledger:</span>
              <span className="px-2 py-0.5 bg-surface rounded border border-surface-border text-slate-300">
                All Active Repositories
              </span>
            </div>
            <span className="text-slate-400 text-[11px]">Click row to open forensic evidence workstation</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs font-mono">
              <thead>
                <tr className="border-b border-surface-border bg-surface-card/40 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  <th className="py-3 px-4">Investigation ID</th>
                  <th className="py-3 px-4">Target Repository</th>
                  <th className="py-3 px-4">Failure Description</th>
                  <th className="py-3 px-4">Current Lifecycle</th>
                  <th className="py-3 px-4">Double Validation</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border">
                <tr className="hover:bg-surface-hover/60 transition cursor-pointer">
                  <td className="py-3.5 px-4 font-bold text-white">
                    <Link href="/investigations/33333333-3333-3333-3333-333333333333" className="hover:underline">
                      #INV-0001
                    </Link>
                  </td>
                  <td className="py-3.5 px-4 font-semibold text-slate-200">
                    broken_python_repo.zip
                  </td>
                  <td className="py-3.5 px-4 text-slate-300 font-sans">
                    divide(10, 2) evaluates to 20 instead of 5
                  </td>
                  <td className="py-3.5 px-4">
                    <StatusBadge status="REPRODUCING" />
                  </td>
                  <td className="py-3.5 px-4">
                    <StatusBadge status="VERIFIED" />
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <Link
                      href="/investigations/33333333-3333-3333-3333-333333333333"
                      className="text-blue-400 hover:text-blue-300 font-bold"
                    >
                      Inspect →
                    </Link>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Phase 2 Pipeline Invariant Banner */}
          <div className="p-3.5 bg-background-deep border-t border-surface-border flex items-center gap-2.5 text-xs text-slate-300 font-mono">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>
              Phase 2 Pipeline Active: Repository ZIP ingestion, isolated sandbox reproduction, and objective failure evidence persisted.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
