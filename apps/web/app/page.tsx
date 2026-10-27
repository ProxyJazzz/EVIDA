import Link from "next/link";
import { ArrowRight, ShieldCheck, Cpu, Terminal, CheckCircle2, FlaskConical, GitFork } from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";

export default function HomePage() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 py-16">
      <div className="max-w-4xl w-full text-center space-y-8">
        {/* Core Maxim Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-surface-border bg-surface text-xs font-mono tracking-wider text-emerald-400">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>CORE MAXIM: AI PROPOSES. EVIDENCE DECIDES.</span>
        </div>

        {/* Hero Title */}
        <div className="space-y-4">
          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
            Evidence-Driven <br />
            <span className="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
              AI Software Repair
            </span>
          </h1>
          <p className="max-w-2xl mx-auto text-base sm:text-lg text-gray-400 font-normal">
            No blind LLM assertions. EVIDA isolates defects, generates causal hypotheses,
            synthesizes regression tests, and validates patches through deterministic sandbox verification.
          </p>
        </div>

        {/* CTA Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium shadow-lg shadow-emerald-950/50 transition-all"
          >
            <span>Open Dashboard</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href="/health"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-surface border border-surface-border hover:border-gray-500 text-gray-200 font-medium transition-all"
          >
            <FlaskConical className="w-4 h-4 text-amber-400" />
            <span>System Health Probe</span>
          </Link>
        </div>

        {/* Architecture Flow Card */}
        <div className="pt-12 text-left">
          <div className="rounded-xl border border-surface-border bg-surface/60 p-6 sm:p-8 backdrop-blur-sm space-y-6">
            <div className="flex items-center justify-between border-b border-surface-border pb-4">
              <div className="flex items-center gap-2">
                <Terminal className="w-5 h-5 text-nvidia" />
                <h3 className="font-mono text-sm uppercase tracking-wider text-gray-200 font-bold">
                  Canonical Verification Workflow
                </h3>
              </div>
              <StatusBadge status="VERIFIED" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
              <div className="p-4 rounded-lg bg-background/80 border border-surface-border space-y-2">
                <div className="text-nvidia font-bold flex items-center gap-1.5">
                  <Cpu className="w-4 h-4" />
                  <span>1. AI PROPOSAL</span>
                </div>
                <p className="text-gray-400 font-sans">
                  Nebius Token Factory executes NVIDIA Nemotron to hypothesize root cause and synthesize negative regression tests.
                </p>
              </div>

              <div className="p-4 rounded-lg bg-background/80 border border-surface-border space-y-2">
                <div className="text-amber-400 font-bold flex items-center gap-1.5">
                  <GitFork className="w-4 h-4" />
                  <span>2. SANDBOX RUNNER</span>
                </div>
                <p className="text-gray-400 font-sans">
                  Isolated execution boundary proves the regression test reproduces failure on unpatched baseline code.
                </p>
              </div>

              <div className="p-4 rounded-lg bg-background/80 border border-surface-border space-y-2">
                <div className="text-emerald-400 font-bold flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>3. DETERMINISTIC PROOF</span>
                </div>
                <p className="text-gray-400 font-sans">
                  Candidate patch is applied: regression test must pass and existing test suite must remain green.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
