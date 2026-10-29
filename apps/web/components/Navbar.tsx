"use client";

import Link from "next/link";
import { ShieldCheck, Terminal, Cpu, Activity, LogIn, FolderGit2, AlertTriangle, Layers } from "lucide-react";

export function Navbar() {
  return (
    <header className="border-b border-surface-border bg-background-deep text-slate-200">
      {/* 1. TOP BAR: Control & Runtime Telemetry Strip (Modeled after preview.html top aside) */}
      <div className="bg-black/90 text-slate-300 px-4 py-1.5 text-xs border-b border-surface-border flex flex-wrap items-center justify-between gap-2 z-50 font-mono">
        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center justify-center w-5 h-5 rounded bg-blue-600 text-white font-bold text-[10px]">
            EV
          </span>
          <span className="font-bold text-white tracking-wide">EVIDA Control Console</span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-400 text-[11px]">Autonomous Software Repair &amp; Deterministic Proof</span>
          <span className="hidden sm:inline-block px-1.5 py-0.2 rounded bg-surface border border-surface-border text-[10px] text-emerald-400 font-semibold">
            RLS ENFORCED
          </span>
        </div>

        <div className="flex items-center space-x-3 text-[11px]">
          <div className="flex items-center space-x-2">
            <span className="text-slate-400">Runtime:</span>
            <span className="text-slate-200 font-semibold">nvidia/Nemotron-3_5-Lightning</span>
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
          </div>
          <span className="text-slate-600 hidden sm:inline">|</span>
          <div className="hidden sm:flex items-center space-x-2 text-[10px] text-slate-400">
            <span>API <span className="text-emerald-400">●</span></span>
            <span>SANDBOX <span className="text-emerald-400">●</span></span>
            <span>DB <span className="text-emerald-400">●</span></span>
          </div>
        </div>
      </div>

      {/* 2. PERSISTENT INVARIANT WARNING STRIP (Modeled after preview.html banner) */}
      <aside
        className="bg-amber-500/10 text-amber-300 px-4 py-1.5 text-xs font-mono font-semibold tracking-wider uppercase text-center border-b border-amber-500/30 shadow-xs flex items-center justify-center space-x-2 select-none"
        role="alert"
      >
        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
        <span>EVIDA Invariant: AI Output is a Proposal. Deterministic Sandbox Execution is the Sole Authority.</span>
      </aside>

      {/* 3. MAIN APP HEADER */}
      <div className="bg-surface/90 border-b border-surface-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="flex items-center space-x-3">
              <Link href="/" className="flex items-center space-x-3 group">
                <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white shadow-sm group-hover:bg-blue-500 transition-colors">
                  <ShieldCheck className="w-5 h-5 text-white" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-base tracking-tight text-white group-hover:text-blue-400 transition-colors">
                      EVIDA
                    </span>
                    <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-surface-card text-slate-300 border border-surface-border">
                      Evidence Engine v1.0
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 truncate max-w-xs sm:max-w-md font-mono">
                    Evidence-Driven AI Software Repair · Nebius × NVIDIA
                  </p>
                </div>
              </Link>
            </div>

            <div className="flex items-center space-x-2 sm:space-x-3 self-start sm:self-auto text-xs font-mono">
              <Link
                href="/dashboard"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-surface-card border border-surface-border text-slate-200 hover:text-white hover:bg-surface-hover transition-colors"
              >
                <FolderGit2 className="w-3.5 h-3.5 text-blue-400" />
                <span>Dashboard</span>
              </Link>
              <Link
                href="/investigations/33333333-3333-3333-3333-333333333333"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-surface-card border border-surface-border text-slate-200 hover:text-white hover:bg-surface-hover transition-colors"
              >
                <Terminal className="w-3.5 h-3.5 text-emerald-400" />
                <span>Evidence Console</span>
              </Link>
              <Link
                href="/health"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-surface-card border border-surface-border text-slate-200 hover:text-white hover:bg-surface-hover transition-colors"
              >
                <Activity className="w-3.5 h-3.5 text-amber-400" />
                <span>Health</span>
              </Link>
              <Link
                href="/login"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white font-semibold transition-colors"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Sign In</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
