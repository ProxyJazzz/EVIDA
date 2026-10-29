import Link from "next/link";
import {
  ShieldCheck,
  Cpu,
  Terminal,
  CheckCircle2,
  Play,
  ArrowRight,
  FolderGit2,
  Lock,
  Layers,
  Sparkles,
  ExternalLink,
  Code2,
  AlertTriangle,
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { TerminalStream } from "@/components/TerminalStream";

export default function HomePage() {
  return (
    <div className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* ========================================================================= */}
      {/* 1. HERO BANNER (Modeled after preview.html Hero Banner)                   */}
      {/* ========================================================================= */}
      <div className="tech-panel p-6 sm:p-8 relative overflow-hidden">
        <div className="max-w-4xl space-y-4">
          <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded bg-blue-950/60 text-blue-400 text-xs font-mono font-semibold border border-blue-800/80">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>CORE MAXIM: AI PROPOSES. EVIDENCE DECIDES.</span>
          </div>

          <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
            Evidence-Driven <span className="text-blue-400">AI Software Repair</span>
          </h1>

          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-sans max-w-3xl">
            Investigate failures. Prove the regression. Validate the patch. Preserve the evidence.
            EVIDA isolates defects, generates causal hypotheses via NVIDIA Nemotron, synthesizes regression
            tests, and validates patches through deterministic sandbox verification.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-surface-border text-xs text-slate-300">
            <div className="flex items-start space-x-2.5">
              <span className="text-emerald-400 font-bold text-base">✓</span>
              <div>
                <span className="font-bold text-white block">No False Pass/Fail</span>
                <span className="text-slate-400 text-[11px]">Zero self-grading. Strict double validation required.</span>
              </div>
            </div>
            <div className="flex items-start space-x-2.5">
              <span className="text-blue-400 font-bold text-base">🔍</span>
              <div>
                <span className="font-bold text-white block">Forensic Provenance</span>
                <span className="text-slate-400 text-[11px]">Every assertion cites sandboxed exit codes &amp; logs.</span>
              </div>
            </div>
            <div className="flex items-start space-x-2.5">
              <span className="text-amber-400 font-bold text-base">⚠️</span>
              <div>
                <span className="font-bold text-white block">Source Invariant</span>
                <span className="text-slate-400 text-[11px]">Original repository SHA-256 remains byte-for-byte intact.</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 2. CONFIGURATION & FAST-TRACK LAUNCHER (Modeled after preview.html)       */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 tech-panel p-6 flex flex-col justify-between space-y-5">
          <div className="border-b border-surface-border pb-3">
            <h2 className="text-sm font-bold text-white font-mono uppercase tracking-wider flex items-center gap-2">
              <FolderGit2 className="w-4 h-4 text-blue-400" />
              1. Target Repository &amp; Defect Configuration
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Specify the target archive and failure reproduction entry point for sandbox isolation.
            </p>
          </div>

          <div className="space-y-4 text-xs font-mono">
            <div>
              <label className="block font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Target Repository Artifact <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                readOnly
                value="broken_python_repo.zip (SHA-256: fa4aec473a843aa4d3a2df0840c192a2e28526c6f5d146b0ae7b7fabaf5280a9)"
                className="w-full px-3.5 py-2 bg-background-deep border border-surface-border rounded text-slate-200 outline-none cursor-default font-mono text-[11px]"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  Reproduction Command
                </label>
                <input
                  type="text"
                  readOnly
                  value="pytest tests/test_bug.py"
                  className="w-full px-3.5 py-2 bg-background-deep border border-surface-border rounded text-slate-200 outline-none cursor-default font-mono text-[11px]"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  Target Inference Model
                </label>
                <input
                  type="text"
                  readOnly
                  value="nvidia/Nemotron-3_5-Lightning"
                  className="w-full px-3.5 py-2 bg-background-deep border border-surface-border rounded text-slate-200 outline-none cursor-default font-mono text-[11px]"
                />
              </div>
            </div>

            <div className="pt-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-t border-surface-border">
              <span className="text-[11px] text-slate-400">
                Architectural Invariant: AI proposes. Sandbox executes. Evidence decides.
              </span>
              <div className="flex items-center gap-2">
                <Link
                  href="/dashboard"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-semibold shadow-xs transition flex items-center space-x-1.5"
                >
                  <span>Start Investigation</span>
                  <span>→</span>
                </Link>
                <Link
                  href="/dashboard"
                  className="px-3.5 py-2 bg-surface-card hover:bg-surface-hover border border-surface-border text-slate-200 rounded text-xs font-medium transition"
                >
                  <span>View Existing Investigations</span>
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Right Card: Canonical Benchmark Launcher */}
        <div className="tech-panel p-6 flex flex-col justify-between bg-gradient-to-b from-surface to-background-deep border-blue-900/40">
          <div className="space-y-3">
            <div className="flex items-center space-x-2 text-amber-400 text-xs font-mono font-bold uppercase tracking-wider">
              <span>⚡</span>
              <span>Instant Verification</span>
            </div>
            <h3 className="text-base font-bold text-white">Load Canonical Demo Investigation</h3>
            <p className="text-xs text-slate-300 leading-relaxed font-sans">
              Inspect an end-to-end arithmetic defect repair with all 7 phases pre-executed: isolated failure reproduction, NVIDIA Nemotron hypothesis, proven regression test, validated patch diff, and double validation proof.
            </p>
          </div>

          <div className="mt-6 pt-4 border-t border-surface-border/60">
            <Link
              href="/investigations/33333333-3333-3333-3333-333333333333"
              className="w-full py-2.5 px-4 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-bold transition shadow flex items-center justify-center space-x-2 font-mono"
            >
              <span>Inspect Investigation #33333333</span>
              <span>→</span>
            </Link>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 3. TERMINAL STREAM (Modeled after preview.html live diagnostic stream)      */}
      {/* ========================================================================= */}
      <TerminalStream />

      {/* ========================================================================= */}
      {/* 4. CANONICAL VERIFICATION WORKFLOW SUMMARY                                */}
      {/* ========================================================================= */}
      <div className="tech-panel p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-surface-border pb-3">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-emerald-400" />
            <h2 className="text-xs font-bold text-white uppercase font-mono tracking-wider">
              Canonical Verification Workflow
            </h2>
          </div>
          <StatusBadge status="VERIFIED" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
          <div className="p-4 rounded bg-background-deep border border-surface-border space-y-2">
            <div className="text-purple-400 font-bold flex items-center gap-1.5">
              <Sparkles className="w-4 h-4" />
              <span>1. AI PROPOSAL</span>
            </div>
            <p className="text-slate-400 font-sans leading-relaxed">
              Nebius Token Factory executes NVIDIA Nemotron to hypothesize root cause and synthesize negative regression tests.
            </p>
          </div>

          <div className="p-4 rounded bg-background-deep border border-surface-border space-y-2">
            <div className="text-blue-400 font-bold flex items-center gap-1.5">
              <Play className="w-4 h-4" />
              <span>2. SANDBOX RUNNER</span>
            </div>
            <p className="text-slate-400 font-sans leading-relaxed">
              Isolated execution boundary proves the regression test reproduces failure on unpatched baseline code.
            </p>
          </div>

          <div className="p-4 rounded bg-background-deep border border-surface-border space-y-2">
            <div className="text-emerald-400 font-bold flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" />
              <span>3. DETERMINISTIC PROOF</span>
            </div>
            <p className="text-slate-400 font-sans leading-relaxed">
              Candidate patch is applied: regression test must pass and existing test suite must remain green.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
