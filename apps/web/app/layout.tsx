import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import Link from "next/link";
import { ShieldCheck, Scale, Cpu, Terminal, ExternalLink } from "lucide-react";

export const metadata: Metadata = {
  title: "EVIDA — Evidence-Driven AI Software Repair",
  description:
    "AI proposes. Evidence decides. Production-grade autonomous software repair verified in isolated ephemeral sandboxes.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark scroll-smooth">
      <body className="bg-background text-slate-100 antialiased min-h-screen flex flex-col font-sans selection:bg-blue-600/30 selection:text-blue-200">
        <Navbar />
        <main className="flex-1 flex flex-col bg-background">{children}</main>

        {/* DISCLAIMER & TECHNICAL TELEMETRY FOOTER (Modeled after preview.html footer) */}
        <footer className="border-t border-surface-border bg-surface text-slate-400 py-6 text-xs font-mono">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-4">
            <div className="flex flex-col sm:flex-row items-start space-y-2 sm:space-y-0 sm:space-x-3 text-xs leading-relaxed">
              <div className="p-1 rounded bg-surface-card text-slate-300 mt-0.5 shrink-0 border border-surface-border">
                <Scale className="w-4 h-4 text-slate-400" />
              </div>
              <div>
                <span className="font-bold text-slate-200 block mb-0.5">
                  Statutory Epistemic Disclaimer — Proof vs. Proposal:
                </span>
                <p className="italic text-slate-400 font-sans text-xs">
                  &ldquo;This platform distinguishes probabilistic model suggestions from deterministic execution truth. AI-generated hypotheses and candidate patches are non-authoritative proposals. Verification is achieved solely when candidate patches apply cleanly, proven regressions pass, and existing test suites remain green inside isolated ephemeral sandboxes without repository mutation.&rdquo;
                </p>
                <p className="text-[11px] text-slate-500 mt-2 font-mono">
                  EVIDA Autonomous Software Repair Platform · Nebius Token Factory × NVIDIA Nemotron · SHA-256 Append-Only Audit Trail
                </p>
              </div>
            </div>

            <div className="pt-4 border-t border-surface-border/60 flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] text-slate-500">
              <div className="flex items-center space-x-4">
                <span>© 2026 EVIDA Platform</span>
                <span>·</span>
                <Link href="/dashboard" className="text-slate-400 hover:text-white">
                  Ledger
                </Link>
                <span>·</span>
                <Link
                  href="/investigations/33333333-3333-3333-3333-333333333333"
                  className="text-slate-400 hover:text-white"
                >
                  Evidence Console
                </Link>
                <span>·</span>
                <Link href="/health" className="text-slate-400 hover:text-white">
                  System Health
                </Link>
              </div>
              <div className="flex items-center gap-2 text-emerald-400 font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                <span>Deterministic Verification Invariants Active</span>
              </div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
