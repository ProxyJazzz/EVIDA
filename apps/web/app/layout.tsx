import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";
import Link from "next/link";
import { ShieldCheck, Cpu, Terminal, ExternalLink } from "lucide-react";

export const metadata: Metadata = {
  title: "EVIDA — Evidence-Driven AI Software Repair",
  description: "AI proposes. Evidence decides. Production-grade software repair verified in isolated ephemeral sandboxes.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark scroll-smooth">
      <body className="bg-background text-gray-100 antialiased min-h-screen flex flex-col selection:bg-purple-600/30 selection:text-purple-200">
        <Navbar />
        <main className="flex-1 flex flex-col">{children}</main>
        
        {/* Cinematic High-End Footer */}
        <footer className="border-t border-white/5 bg-background-elevated/70 backdrop-blur-xl py-12 text-xs text-gray-400">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8 pb-10 border-b border-white/5">
              {/* Col 1: Brand & Maxim */}
              <div className="space-y-3 md:col-span-2">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-lg bg-purple-950/80 border border-purple-500/40 flex items-center justify-center">
                    <ShieldCheck className="w-3.5 h-3.5 text-purple-400" />
                  </div>
                  <span className="font-extrabold text-white text-base tracking-tight">EVIDA</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface border border-surface-border text-nvidia">
                    nvidia/Nemotron-3_5-Lightning
                  </span>
                </div>
                <p className="text-sm font-semibold text-gray-200">
                  AI proposes. Evidence decides. EVIDA records why.
                </p>
                <p className="text-xs text-gray-400 max-w-md leading-relaxed">
                  Autonomous software repair where LLMs formulate hypotheses and patches, while isolated sandboxes enforce strict double validation before any code is declared verified.
                </p>
              </div>

              {/* Col 2: Navigation */}
              <div className="space-y-2">
                <p className="text-xs font-mono uppercase tracking-wider text-gray-200 font-bold">Platform</p>
                <ul className="space-y-1.5 text-xs text-gray-400">
                  <li>
                    <Link href="/dashboard" className="hover:text-purple-300 transition-colors">
                      Investigations Ledger
                    </Link>
                  </li>
                  <li>
                    <Link href="/investigations/33333333-3333-3333-3333-333333333333" className="hover:text-emerald-300 transition-colors">
                      Canonical Evidence Bundle
                    </Link>
                  </li>
                  <li>
                    <Link href="/#pipeline" className="hover:text-cyan-300 transition-colors">
                      8-Stage Verification Pipeline
                    </Link>
                  </li>
                  <li>
                    <Link href="/health" className="hover:text-amber-300 transition-colors">
                      System Health & Diagnostics
                    </Link>
                  </li>
                </ul>
              </div>

              {/* Col 3: Runtime & Hackathon */}
              <div className="space-y-2">
                <p className="text-xs font-mono uppercase tracking-wider text-gray-200 font-bold">Verification Engine</p>
                <div className="p-3 rounded-lg bg-surface/50 border border-surface-border space-y-1.5 text-[11px] font-mono">
                  <div className="flex items-center justify-between text-gray-300">
                    <span className="text-gray-400">AI Runtime:</span>
                    <span className="text-nvidia">Nebius Token Factory</span>
                  </div>
                  <div className="flex items-center justify-between text-gray-300">
                    <span className="text-gray-400">Model:</span>
                    <span className="text-gray-200">Nemotron-3_5</span>
                  </div>
                  <div className="flex items-center justify-between text-gray-300">
                    <span className="text-gray-400">Sandbox:</span>
                    <span className="text-emerald-400">Isolated Ephemeral</span>
                  </div>
                  <div className="flex items-center justify-between text-gray-300">
                    <span className="text-gray-400">Double Validation:</span>
                    <span className="text-emerald-400">Enforced</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-gray-400">
              <p>© 2026 EVIDA — Evidence-Driven AI Software Repair. Built for the Nebius × NVIDIA Global AI Hackathon.</p>
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1.5 text-emerald-400 font-mono">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  All 7 Quality Gates Verified
                </span>
              </div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}

