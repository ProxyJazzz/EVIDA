import Link from "next/link";
import {
  ShieldCheck,
  Plus,
  Terminal,
  FolderGit2,
  AlertCircle,
  Search,
  Sparkles,
  ArrowRight,
  Filter,
  CheckCircle2,
  Bug,
  FileCode,
  Lock,
  Layers,
  Clock,
  ExternalLink,
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";

export default function DashboardPage() {
  return (
    <div className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* ========================================================================= */}
      {/* 1. DASHBOARD HEADER & CONTROLS                                            */}
      {/* ========================================================================= */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/5 pb-8">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-purple-400 mb-1">
            <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
            <span>SYSTEM CONSOLE — REPAIR LEDGER</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
            <FolderGit2 className="w-7 h-7 text-purple-400" />
            Repair Investigations Dashboard
          </h1>
          <p className="text-sm text-gray-400 mt-1 max-w-2xl leading-relaxed">
            Autonomous defect reproduction, causal hypothesis formulation, regression proof, and double-validated patches.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/investigations/33333333-3333-3333-3333-333333333333"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-surface border border-surface-border hover:border-purple-500/40 text-xs font-semibold text-gray-200 transition-all shadow-glass"
          >
            <Terminal className="w-4 h-4 text-emerald-400" />
            <span>Open Canonical Demo</span>
          </Link>
          <button
            disabled
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-purple-900/30 border border-purple-500/20 text-xs font-semibold text-purple-300/60 cursor-not-allowed"
          >
            <Plus className="w-4 h-4" />
            <span>New Investigation (Phase 1)</span>
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 2. STATS OVERVIEW CARDS (Inspired by reference glass card styling)        */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="glass-card rounded-2xl p-5 border border-white/10 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-purple-950/60 border border-purple-500/30 flex items-center justify-center shrink-0">
            <FolderGit2 className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <p className="text-xs font-mono text-gray-400 uppercase tracking-wider">Active Repositories</p>
            <p className="text-2xl font-extrabold text-white mt-0.5">1</p>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-white/10 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-blue-950/60 border border-blue-500/30 flex items-center justify-center shrink-0">
            <Layers className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <p className="text-xs font-mono text-gray-400 uppercase tracking-wider">Total Investigations</p>
            <p className="text-2xl font-extrabold text-white mt-0.5">1</p>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-white/10 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-950/60 border border-emerald-500/30 flex items-center justify-center shrink-0 shadow-[0_0_20px_-3px_rgba(16,185,129,0.3)]">
            <CheckCircle2 className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <p className="text-xs font-mono text-emerald-400 uppercase tracking-wider">Verified Fixes</p>
            <p className="text-2xl font-extrabold text-emerald-400 mt-0.5">1</p>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-white/10 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-nvidia/10 border border-nvidia/30 flex items-center justify-center shrink-0">
            <Sparkles className="w-6 h-6 text-nvidia" />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-mono text-nvidia uppercase tracking-wider">NVIDIA Inference Model</p>
            <p className="text-xs font-mono font-bold text-gray-200 mt-1 truncate">
              Nemotron-3_5-Lightning
            </p>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 3. GLOSSY PILL SEARCH & FILTER BAR (Inspired by reference search bar)     */}
      {/* ========================================================================= */}
      <div className="relative rounded-2xl border border-white/10 bg-surface/70 backdrop-blur-xl p-3 shadow-glass flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-3 w-full sm:w-auto flex-1 px-3">
          <Search className="w-5 h-5 text-gray-400 shrink-0" />
          <input
            type="text"
            readOnly
            value="broken_python_repo.zip"
            placeholder="Search investigations, repositories, or SHA-256 digests..."
            className="w-full bg-transparent text-sm text-gray-200 font-mono outline-none placeholder:text-gray-500 cursor-default"
          />
        </div>
        <div className="flex items-center gap-2 w-full sm:w-auto shrink-0 border-t sm:border-t-0 sm:border-l border-white/10 pt-2 sm:pt-0 sm:pl-3">
          <span className="text-xs font-mono px-3 py-1.5 rounded-xl bg-background-dark border border-white/10 text-gray-300 flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-purple-400" />
            <span>Status: All Verified</span>
          </span>
          <span className="text-xs font-mono px-3 py-1.5 rounded-xl bg-purple-950/60 border border-purple-500/30 text-purple-300">
            2026.10
          </span>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 4. INVESTIGATION LEDGER                                                    */}
      {/* ========================================================================= */}
      <div className="rounded-2xl border border-white/10 bg-surface/50 backdrop-blur-xl shadow-glass overflow-hidden">
        <div className="p-5 border-b border-white/5 bg-surface-card/60 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Terminal className="w-4 h-4 text-purple-400" />
            <h2 className="text-sm font-mono font-bold text-gray-200 uppercase tracking-wider">
              Investigation Ledger
            </h2>
          </div>
          <span className="text-xs font-mono text-gray-400">
            Active Multi-Tenant Scope
          </span>
        </div>

        <div className="divide-y divide-white/5">
          {/* Main Canonical Investigation Card */}
          <Link
            href="/investigations/33333333-3333-3333-3333-333333333333"
            className="p-6 flex flex-col lg:flex-row lg:items-center justify-between gap-6 hover:bg-surface/80 transition-all duration-300 group block"
          >
            <div className="space-y-2">
              <div className="flex items-center gap-2.5 flex-wrap">
                <span className="font-mono text-xs px-2.5 py-0.5 rounded-lg bg-surface border border-surface-border text-gray-300">
                  #INV-0001
                </span>
                <span className="font-mono text-xs text-purple-400">
                  ID: 33333333-3333-3333-3333-333333333333
                </span>
                <span className="text-xs text-gray-500">·</span>
                <span className="text-xs text-gray-400">2 min ago</span>
              </div>
              <h3 className="text-base font-bold text-white group-hover:text-purple-300 transition-colors">
                Fix calculator division bug
              </h3>
              <p className="text-xs text-gray-400 leading-relaxed max-w-2xl">
                Defect reported in arithmetic division: <code className="text-gray-300">divide(20, 4)</code> evaluates to <code className="text-rose-400">80</code> instead of expected <code className="text-emerald-400">5</code>.
              </p>
              <div className="flex items-center gap-4 text-xs font-mono text-gray-400 pt-1">
                <span>
                  Target Repo: <span className="text-gray-200 font-semibold">broken_python_repo.zip</span>
                </span>
                <span>•</span>
                <span>SHA-256: fa4aec473a84...</span>
                <span>•</span>
                <span className="text-purple-300">12 Evidence Items</span>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 shrink-0">
              <div className="flex flex-col sm:items-end gap-1.5">
                <StatusBadge status="VERIFIED" />
                <span className="text-[11px] font-mono text-emerald-400">
                  Double Validation Passed
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-purple-400 font-mono group-hover:text-purple-300 transition-colors">
                  View Phase 2 Evidence &rarr;
                </span>
              </div>
            </div>
          </Link>
        </div>

        {/* Phase 2 Pipeline Invariant Banner */}
        <div className="p-4 bg-background-dark/80 border-t border-white/5 flex items-center gap-3 text-xs text-gray-300 font-mono">
          <AlertCircle className="w-4 h-4 text-purple-400 shrink-0" />
          <span>
            Phase 2 Pipeline Active: Repository ZIP ingestion, isolated sandbox reproduction, and objective failure evidence persisted.
          </span>
        </div>
      </div>
    </div>
  );
}
