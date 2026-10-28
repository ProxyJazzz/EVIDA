import Link from "next/link";
import {
  ArrowRight,
  ShieldCheck,
  Cpu,
  Terminal,
  CheckCircle2,
  FlaskConical,
  GitFork,
  FileCode,
  Bug,
  Lock,
  Layers,
  Sparkles,
  ExternalLink,
  ChevronRight,
  Code2,
  RefreshCw,
  SlidersHorizontal,
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";

export default function HomePage() {
  return (
    <div className="flex-1 flex flex-col items-center justify-start overflow-hidden">
      {/* ========================================================================= */}
      {/* 1. HERO SECTION                                                           */}
      {/* ========================================================================= */}
      <section className="relative w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 pb-20 lg:pt-20 lg:pb-28 flex flex-col items-center text-center">
        {/* Ambient Glows */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-purple-600/15 blur-[120px] rounded-full pointer-events-none -z-10" />
        <div className="absolute top-1/3 left-1/4 -translate-y-1/2 w-[300px] h-[250px] bg-cyan-500/10 blur-[100px] rounded-full pointer-events-none -z-10" />
        <div className="absolute top-1/3 right-1/4 -translate-y-1/2 w-[300px] h-[250px] bg-emerald-500/10 blur-[100px] rounded-full pointer-events-none -z-10" />

        {/* Maxim Pill Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-purple-500/30 bg-purple-950/40 backdrop-blur-xl text-xs font-mono tracking-wider text-purple-300 shadow-[0_0_20px_-3px_rgba(139,92,246,0.3)] mb-8">
          <ShieldCheck className="w-4 h-4 text-purple-400" />
          <span>CORE MAXIM: AI PROPOSES. EVIDENCE DECIDES.</span>
        </div>

        {/* Editorial Headline */}
        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white leading-[1.08] max-w-5xl">
          Evidence-Driven <br />
          <span className="bg-gradient-to-r from-purple-400 via-indigo-300 to-cyan-300 bg-clip-text text-transparent">
            AI Software Repair
          </span>
        </h1>

        {/* Subtitle */}
        <p className="mt-6 max-w-3xl text-base sm:text-xl text-gray-300 font-normal leading-relaxed">
          EVIDA investigates software failures, generates repair candidates, and deterministically
          verifies whether they actually work. No self-graded LLM assertions.
        </p>

        {/* Action CTAs */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-8">
          <Link
            href="/dashboard"
            className="group relative inline-flex items-center gap-2.5 px-8 py-4 rounded-xl bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-semibold text-sm shadow-[0_0_35px_-5px_rgba(139,92,246,0.6)] hover:shadow-[0_0_45px_-5px_rgba(139,92,246,0.8)] transition-all duration-300"
          >
            <span>Start Investigation</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
          <Link
            href="/investigations/33333333-3333-3333-3333-333333333333"
            className="inline-flex items-center gap-2 px-7 py-4 rounded-xl bg-surface/80 hover:bg-surface border border-surface-border hover:border-purple-500/40 text-gray-200 font-semibold text-sm backdrop-blur-md transition-all shadow-glass"
          >
            <Terminal className="w-4 h-4 text-emerald-400" />
            <span>Explore Evidence</span>
          </Link>
          <Link
            href="/health"
            className="inline-flex items-center gap-2 px-6 py-4 rounded-xl bg-surface/40 hover:bg-surface/70 border border-surface-border text-gray-300 font-semibold text-sm backdrop-blur-md transition-all"
          >
            <FlaskConical className="w-4 h-4 text-amber-400" />
            <span>Health Probe</span>
          </Link>
        </div>

        {/* ========================================================================= */}
        {/* HERO VISUAL: AUTONOMOUS EVIDENCE ENGINE PREVIEW CONTAINER                */}
        {/* ========================================================================= */}
        <div className="w-full mt-14 max-w-5xl rounded-2xl border border-white/10 bg-surface/70 backdrop-blur-2xl shadow-glass overflow-hidden text-left relative">
          <div className="p-4 sm:p-5 border-b border-white/10 bg-surface-card/60 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-rose-500/80" />
                <div className="w-3 h-3 rounded-full bg-amber-500/80" />
                <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
              </div>
              <span className="text-xs font-mono text-gray-400">
                evida-orchestrator — live-pipeline
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono text-gray-400">Target Model:</span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-purple-950/60 border border-purple-500/30 text-purple-300">
                nvidia/Nemotron-3_5-Lightning
              </span>
              <StatusBadge status="VERIFIED" />
            </div>
          </div>

          <div className="p-6 sm:p-8 space-y-6">
            {/* Visual Pipeline Flow Stepper */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div className="p-3.5 rounded-xl bg-background-dark/80 border border-white/5 space-y-1">
                <div className="flex items-center justify-between text-rose-400">
                  <span className="font-bold">01 REPRODUCE</span>
                  <Bug className="w-3.5 h-3.5" />
                </div>
                <p className="text-[11px] text-gray-400 font-sans">pytest exit code 1</p>
                <div className="text-[10px] text-emerald-400">✓ Isolated Sandbox</div>
              </div>

              <div className="p-3.5 rounded-xl bg-background-dark/80 border border-purple-500/20 space-y-1">
                <div className="flex items-center justify-between text-purple-400">
                  <span className="font-bold">02 HYPOTHESIS</span>
                  <Sparkles className="w-3.5 h-3.5" />
                </div>
                <p className="text-[11px] text-gray-400 font-sans">src/calculator.py</p>
                <div className="text-[10px] text-purple-300">Nemotron-3_5 (0.99)</div>
              </div>

              <div className="p-3.5 rounded-xl bg-background-dark/80 border border-blue-500/20 space-y-1">
                <div className="flex items-center justify-between text-blue-400">
                  <span className="font-bold">03 REGRESSION</span>
                  <Terminal className="w-3.5 h-3.5" />
                </div>
                <p className="text-[11px] text-gray-400 font-sans">Independent assertion</p>
                <div className="text-[10px] text-blue-300">REGRESSION_PROVEN</div>
              </div>

              <div className="p-3.5 rounded-xl bg-background-dark/80 border border-emerald-500/30 space-y-1 shadow-[0_0_15px_-3px_rgba(16,185,129,0.25)]">
                <div className="flex items-center justify-between text-emerald-400">
                  <span className="font-bold">04 DOUBLE VALIDATE</span>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                </div>
                <p className="text-[11px] text-gray-400 font-sans">Regression + Baseline</p>
                <div className="text-[10px] text-emerald-300 font-bold">100% VERIFIED</div>
              </div>
            </div>

            {/* Terminal Live Output Snapshot */}
            <div className="p-4 rounded-xl bg-background-deep border border-surface-border text-xs font-mono space-y-2">
              <div className="flex items-center justify-between text-[11px] text-gray-500 border-b border-surface-border pb-2">
                <div className="flex items-center gap-2">
                  <Terminal className="w-3.5 h-3.5 text-nvidia" />
                  <span>DETERMINISTIC VERIFICATION STAGE RUNNER</span>
                </div>
                <span className="text-gray-400">SHA-256: fa4aec473a84...</span>
              </div>
              <p className="text-purple-300">
                [AI_PROPOSAL] Proposed patch modifying src/calculator.py (1 hunk). Status: VALIDATED.
              </p>
              <p className="text-blue-300">
                [EXECUTION] Applying patch in isolated ephemeral workspace /tmp/evida_verify_x89...
              </p>
              <p className="text-emerald-400">
                [VERIFIED] pytest tests/test_regression.py &gt;&gt; PASSED (0.08s)
              </p>
              <p className="text-emerald-400">
                [VERIFIED] pytest baseline test suite &gt;&gt; PASSED (0.09s)
              </p>
              <p className="text-emerald-300 font-bold">
                [INTEGRITY] Original repository SHA-256 match confirmed. Double validation verdict: VERIFIED.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 2. STATS & SYSTEM TRUST STRIP                                             */}
      {/* ========================================================================= */}
      <section className="w-full border-y border-white/5 bg-background-dark/80 backdrop-blur-md py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center md:text-left">
            <div className="p-4 rounded-xl bg-surface/30 border border-white/5 flex flex-col md:flex-row items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-purple-950/60 border border-purple-500/30 flex items-center justify-center shrink-0">
                <ShieldCheck className="w-6 h-6 text-purple-400" />
              </div>
              <div>
                <div className="text-2xl sm:text-3xl font-extrabold text-white">239+</div>
                <p className="text-xs text-gray-400 uppercase tracking-wider font-mono">
                  Deterministic Checks
                </p>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-surface/30 border border-white/5 flex flex-col md:flex-row items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-950/60 border border-emerald-500/30 flex items-center justify-center shrink-0">
                <CheckCircle2 className="w-6 h-6 text-emerald-400" />
              </div>
              <div>
                <div className="text-2xl sm:text-3xl font-extrabold text-white">100%</div>
                <p className="text-xs text-gray-400 uppercase tracking-wider font-mono">
                  Source Integrity
                </p>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-surface/30 border border-white/5 flex flex-col md:flex-row items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-cyan-950/60 border border-cyan-500/30 flex items-center justify-center shrink-0">
                <Lock className="w-6 h-6 text-cyan-400" />
              </div>
              <div>
                <div className="text-2xl sm:text-3xl font-extrabold text-white">0</div>
                <p className="text-xs text-gray-400 uppercase tracking-wider font-mono">
                  AI Self-Graded Fixes
                </p>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-surface/30 border border-white/5 flex flex-col md:flex-row items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-amber-950/60 border border-amber-500/30 flex items-center justify-center shrink-0">
                <Layers className="w-6 h-6 text-amber-400" />
              </div>
              <div>
                <div className="text-2xl sm:text-3xl font-extrabold text-white">8-Stage</div>
                <p className="text-xs text-gray-400 uppercase tracking-wider font-mono">
                  Evidence Pipeline
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 3. INVESTIGATION PIPELINE ("WHAT EVIDA DOES")                             */}
      {/* ========================================================================= */}
      <section id="pipeline" className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-28">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-14">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-950/60 border border-purple-500/30 text-xs font-mono text-purple-300 mb-3">
              <span>INVESTIGATION PIPELINE</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              Deterministic Software Repair Architecture
            </h2>
          </div>
          <p className="text-sm text-gray-400 max-w-md">
            From repository ingestion to cryptographic bundle publication, every single transition requires objective execution evidence.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Card 1 */}
          <div className="glass-card rounded-2xl p-6 flex flex-col justify-between space-y-4">
            <div>
              <div className="w-12 h-12 rounded-xl bg-rose-950/60 border border-rose-500/30 flex items-center justify-center text-rose-400 font-bold mb-4">
                <Bug className="w-6 h-6" />
              </div>
              <span className="text-xs font-mono text-gray-500">PHASE 01 & 02</span>
              <h3 className="text-lg font-bold text-white mt-1">Failure Reproduction</h3>
              <p className="text-xs text-gray-400 mt-2 leading-relaxed">
                Source ZIP archive is ingested and executed inside an isolated sandbox. Reproduction command must confirm defect via objective non-zero exit code.
              </p>
            </div>
            <div className="pt-4 border-t border-white/5 flex items-center justify-between text-xs font-mono text-gray-400">
              <span>Status:</span>
              <span className="text-rose-400 font-semibold">REPRODUCED</span>
            </div>
          </div>

          {/* Card 2 */}
          <div className="glass-card rounded-2xl p-6 flex flex-col justify-between space-y-4">
            <div>
              <div className="w-12 h-12 rounded-xl bg-purple-950/60 border border-purple-500/30 flex items-center justify-center text-purple-400 font-bold mb-4">
                <Sparkles className="w-6 h-6" />
              </div>
              <span className="text-xs font-mono text-gray-500">PHASE 03</span>
              <h3 className="text-lg font-bold text-white mt-1">AI Causal Hypothesis</h3>
              <p className="text-xs text-gray-400 mt-2 leading-relaxed">
                NVIDIA Nemotron-3_5-Lightning analyzes reproduction stdout and code traces to propose causal hypothesis, affected files, and repair strategy.
              </p>
            </div>
            <div className="pt-4 border-t border-white/5 flex items-center justify-between text-xs font-mono text-gray-400">
              <span>Provenance:</span>
              <span className="text-purple-300 font-semibold">AI_PROPOSAL</span>
            </div>
          </div>

          {/* Card 3 */}
          <div className="glass-card rounded-2xl p-6 flex flex-col justify-between space-y-4">
            <div>
              <div className="w-12 h-12 rounded-xl bg-blue-950/60 border border-blue-500/30 flex items-center justify-center text-blue-400 font-bold mb-4">
                <Terminal className="w-6 h-6" />
              </div>
              <span className="text-xs font-mono text-gray-500">PHASE 04</span>
              <h3 className="text-lg font-bold text-white mt-1">Proven Regression Test</h3>
              <p className="text-xs text-gray-400 mt-2 leading-relaxed">
                AI synthesizes a standalone negative regression test. The sandbox executes it on unpatched baseline to deterministically prove failure before patching.
              </p>
            </div>
            <div className="pt-4 border-t border-white/5 flex items-center justify-between text-xs font-mono text-gray-400">
              <span>Verdict:</span>
              <span className="text-blue-300 font-semibold">REGRESSION_PROVEN</span>
            </div>
          </div>

          {/* Card 4 */}
          <div className="glass-card rounded-2xl p-6 flex flex-col justify-between space-y-4">
            <div>
              <div className="w-12 h-12 rounded-xl bg-emerald-950/60 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold mb-4 shadow-[0_0_20px_-3px_rgba(16,185,129,0.3)]">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <span className="text-xs font-mono text-gray-500">PHASE 05 & 06</span>
              <h3 className="text-lg font-bold text-white mt-1">Double Validation</h3>
              <p className="text-xs text-gray-400 mt-2 leading-relaxed">
                Candidate patch is applied in fresh workspace. Proven regression test must pass AND baseline test suite must remain green. Original repo untouched.
              </p>
            </div>
            <div className="pt-4 border-t border-white/5 flex items-center justify-between text-xs font-mono text-gray-400">
              <span>Final Verdict:</span>
              <span className="text-emerald-400 font-bold">VERIFIED</span>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 4. AI PROPOSES VS. EVIDENCE DECIDES CONTRAST SECTION                      */}
      {/* ========================================================================= */}
      <section id="architecture" className="w-full border-y border-white/5 bg-background-elevated/40 backdrop-blur-xl py-20 lg:py-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          <div className="text-center max-w-3xl mx-auto space-y-4">
            <span className="text-xs font-mono uppercase tracking-widest text-emerald-400 font-bold">
              Architectural Invariant
            </span>
            <h2 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
              AI Synthesis vs. Execution Proof
            </h2>
            <p className="text-sm sm:text-base text-gray-300">
              EVIDA strictly separates non-authoritative probabilistic LLM suggestions from authoritative deterministic execution proofs.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Column A: AI PROPOSES */}
            <div className="rounded-2xl border border-purple-500/30 bg-purple-950/15 p-6 sm:p-8 backdrop-blur-md space-y-6">
              <div className="flex items-center justify-between border-b border-purple-500/20 pb-4">
                <div className="flex items-center gap-2 text-purple-400 font-mono font-bold text-sm">
                  <Sparkles className="w-4 h-4" />
                  <span>AI PROPOSES (Probabilistic &amp; Untrusted)</span>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-purple-900/50 text-purple-300">
                  Non-Authoritative
                </span>
              </div>

              <div className="space-y-4 text-xs font-mono">
                <div className="p-3.5 rounded-xl bg-background/80 border border-purple-500/20 space-y-1">
                  <span className="text-purple-400 font-bold block">1. Defect Hypothesis</span>
                  <p className="text-gray-300 font-sans">
                    NVIDIA Nemotron identifies probable failure location in source code based on logs.
                  </p>
                </div>
                <div className="p-3.5 rounded-xl bg-background/80 border border-purple-500/20 space-y-1">
                  <span className="text-purple-400 font-bold block">2. Candidate Regression Test</span>
                  <p className="text-gray-300 font-sans">
                    AI synthesizes a test designed to expose the bug. (Must still be proven by sandbox).
                  </p>
                </div>
                <div className="p-3.5 rounded-xl bg-background/80 border border-purple-500/20 space-y-1">
                  <span className="text-purple-400 font-bold block">3. Unified Diff Patch</span>
                  <p className="text-gray-300 font-sans">
                    AI generates code edits. Marked <code className="text-amber-400">NOT VERIFIED</code> until sandbox execution.
                  </p>
                </div>
                <div className="p-3.5 rounded-xl bg-background/80 border border-purple-500/20 space-y-1">
                  <span className="text-purple-400 font-bold block">4. Confidence Score (e.g. 0.99)</span>
                  <p className="text-gray-300 font-sans">
                    AI confidence has <strong>zero weight</strong> in deciding whether a patch is verified.
                  </p>
                </div>
              </div>
            </div>

            {/* Column B: EVIDENCE DECIDES */}
            <div className="rounded-2xl border border-emerald-500/30 bg-emerald-950/15 p-6 sm:p-8 backdrop-blur-md space-y-6">
              <div className="flex items-center justify-between border-b border-emerald-500/20 pb-4">
                <div className="flex items-center gap-2 text-emerald-400 font-mono font-bold text-sm">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>EVIDENCE DECIDES (Deterministic &amp; Auditable)</span>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-900/50 text-emerald-300 font-bold">
                  Authoritative
                </span>
              </div>

              <div className="space-y-4 text-xs font-mono">
                <div className="p-3.5 rounded-xl bg-background/80 border border-emerald-500/20 space-y-1">
                  <span className="text-emerald-400 font-bold block">1. Sandbox Execution &amp; Exit Code</span>
                  <p className="text-gray-300 font-sans">
                    Isolated Linux subprocess execution. Exit code 0 vs non-zero determines ground truth.
                  </p>
                </div>
                <div className="p-3.5 rounded-xl bg-background/80 border border-emerald-500/20 space-y-1">
                  <span className="text-emerald-400 font-bold block">2. Double Validation Rule</span>
                  <p className="text-gray-300 font-sans">
                    Regression test passes on patched code AND existing test suite maintains 100% pass rate.
                  </p>
                </div>
                <div className="p-3.5 rounded-xl bg-background/80 border border-emerald-500/20 space-y-1">
                  <span className="text-emerald-400 font-bold block">3. SHA-256 Source Integrity</span>
                  <p className="text-gray-300 font-sans">
                    Original repository archive hash verified before and after. Zero accidental mutation.
                  </p>
                </div>
                <div className="p-3.5 rounded-xl bg-background/80 border border-emerald-500/20 space-y-1">
                  <span className="text-emerald-400 font-bold block">4. Cryptographic Evidence Bundle</span>
                  <p className="text-gray-300 font-sans">
                    Immutable append-only JSON audit record signed with SHA-256 digest for audit review.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 5. FEATURED CANONICAL INVESTIGATION PREVIEW                               */}
      {/* ========================================================================= */}
      <section className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-28">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-500/30 text-xs font-mono text-cyan-300 mb-3">
              <span>CANONICAL CASE STUDY</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              Featured Repair Investigation
            </h2>
          </div>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 text-xs font-mono text-purple-400 hover:text-purple-300"
          >
            <span>View All Investigations in Ledger</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="glass-panel rounded-3xl p-6 sm:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-6">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-surface border border-surface-border text-gray-300">
                  #INV-0001
                </span>
                <h3 className="text-xl font-bold text-white">Fix calculator division bug</h3>
              </div>
              <p className="text-xs text-gray-400">
                Target Repository: <span className="font-mono text-gray-200">broken_python_repo.zip</span> · Issue: divide(20, 4) evaluates to 80 instead of 5
              </p>
            </div>
            <div className="flex items-center gap-3">
              <StatusBadge status="VERIFIED" />
              <Link
                href="/investigations/33333333-3333-3333-3333-333333333333"
                className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold transition shadow-[0_0_15px_-3px_rgba(139,92,246,0.4)]"
              >
                Inspect Full Evidence &rarr;
              </Link>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 text-xs">
            {/* Box 1 */}
            <div className="p-4 rounded-xl bg-background-dark/80 border border-white/5 space-y-2">
              <div className="flex items-center justify-between text-gray-400 font-mono">
                <span>01 FAILURE REPRODUCED</span>
                <Bug className="w-3.5 h-3.5 text-rose-400" />
              </div>
              <pre className="p-2.5 rounded bg-black/60 text-[11px] font-mono text-rose-300 overflow-x-auto whitespace-pre">
{`FAILED tests/test_bug.py
assert divide(20, 4) == 5
assert 80 == 5
Exit code: 1 (142ms)`}
              </pre>
            </div>

            {/* Box 2 */}
            <div className="p-4 rounded-xl bg-background-dark/80 border border-white/5 space-y-2">
              <div className="flex items-center justify-between text-gray-400 font-mono">
                <span>02 VALIDATED PATCH (DIFF)</span>
                <Code2 className="w-3.5 h-3.5 text-purple-400" />
              </div>
              <pre className="p-2.5 rounded bg-black/60 text-[11px] font-mono text-gray-300 overflow-x-auto whitespace-pre">
{`--- a/src/calculator.py
+++ b/src/calculator.py
@@ -1,2 +1,2 @@
 def divide(a, b):
-    return a * b
+    return a / b`}
              </pre>
            </div>

            {/* Box 3 */}
            <div className="p-4 rounded-xl bg-background-dark/80 border border-white/5 space-y-2">
              <div className="flex items-center justify-between text-gray-400 font-mono">
                <span>03 DOUBLE VALIDATION</span>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              </div>
              <pre className="p-2.5 rounded bg-black/60 text-[11px] font-mono text-emerald-300 overflow-x-auto whitespace-pre">
{`Regression: PASSED (0.08s)
Baseline:   PASSED (0.09s)
Integrity:  MATCH (fa4aec4...)
Verdict:    VERIFIED`}
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 6. CALL TO ACTION BANNER                                                  */}
      {/* ========================================================================= */}
      <section className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-24">
        <div className="relative rounded-3xl border border-purple-500/30 bg-gradient-to-r from-purple-950/70 via-surface to-indigo-950/70 p-8 sm:p-14 backdrop-blur-2xl shadow-glass overflow-hidden text-center sm:text-left flex flex-col sm:flex-row sm:items-center justify-between gap-8">
          <div className="space-y-2 max-w-xl">
            <span className="text-xs font-mono uppercase tracking-widest text-purple-400 font-bold">
              Ready for Verification
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Bring Autonomous Software Repair to Your Repositories.
            </h2>
            <p className="text-xs sm:text-sm text-gray-300 leading-relaxed">
              Experience the certainty of deterministic patch verification backed by isolated ephemeral sandboxes and NVIDIA Nemotron intelligence.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3 shrink-0">
            <Link
              href="/dashboard"
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold text-xs shadow-[0_0_25px_-5px_rgba(139,92,246,0.6)] transition-all text-center"
            >
              Start Investigation
            </Link>
            <Link
              href="/health"
              className="w-full sm:w-auto px-5 py-3.5 rounded-xl bg-surface border border-surface-border hover:border-gray-500 text-gray-200 font-semibold text-xs transition-all text-center"
            >
              System Health
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
