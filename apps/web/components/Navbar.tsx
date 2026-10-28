"use client";

import { useState } from "react";
import Link from "next/link";
import { ShieldCheck, LayoutDashboard, Activity, LogIn, Menu, X, Terminal, Cpu, ArrowUpRight } from "lucide-react";

export function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/5 bg-background/70 backdrop-blur-xl transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 py-3.5 flex items-center justify-between">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-3.5 group">
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-purple-900/60 via-surface to-background border border-purple-500/30 flex items-center justify-center shadow-[0_0_20px_-3px_rgba(139,92,246,0.35)] group-hover:border-purple-400/60 transition-all">
            <ShieldCheck className="w-5 h-5 text-purple-400 group-hover:text-purple-300 transition-colors" />
            <div className="absolute inset-0 rounded-xl bg-purple-500/10 blur-sm opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-xl tracking-tight text-white group-hover:text-purple-200 transition-colors">
                EVIDA
              </span>
              <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-nvidia/10 border border-nvidia/30 text-nvidia">
                <span className="w-1.5 h-1.5 rounded-full bg-nvidia animate-ping" />
                NVIDIA Nemotron
              </span>
            </div>
            <span className="text-[11px] text-gray-400 tracking-wide hidden md:block">
              Evidence-Driven AI Software Repair
            </span>
          </div>
        </Link>

        {/* Center Navigation Links */}
        <nav className="hidden md:flex items-center gap-1 text-sm font-medium">
          <Link
            href="/dashboard"
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-white/5 transition-all"
          >
            <LayoutDashboard className="w-4 h-4 text-purple-400" />
            <span>Investigations</span>
          </Link>
          <Link
            href="/investigations/33333333-3333-3333-3333-333333333333"
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-white/5 transition-all"
          >
            <Terminal className="w-4 h-4 text-emerald-400" />
            <span>Evidence</span>
          </Link>
          <Link
            href="/#architecture"
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-white/5 transition-all"
          >
            <Cpu className="w-4 h-4 text-cyan-400" />
            <span>Architecture</span>
          </Link>
          <Link
            href="/health"
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-white/5 transition-all"
          >
            <Activity className="w-4 h-4 text-amber-400" />
            <span>Health</span>
          </Link>
        </nav>

        {/* Action Controls */}
        <div className="hidden sm:flex items-center gap-3">
          <Link
            href="/login"
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold text-gray-300 hover:text-white hover:bg-white/5 transition-colors"
          >
            <LogIn className="w-4 h-4" />
            <span>Sign In</span>
          </Link>
          <Link
            href="/dashboard"
            className="relative group inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-bold shadow-[0_0_20px_-3px_rgba(139,92,246,0.5)] transition-all"
          >
            <span>New Investigation</span>
            <ArrowUpRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
          </Link>
        </div>

        {/* Mobile Menu Toggle */}
        <div className="flex md:hidden items-center gap-2">
          <Link
            href="/dashboard"
            className="px-3 py-1.5 rounded-lg bg-purple-600 text-white text-xs font-semibold"
          >
            Dashboard
          </Link>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 focus:outline-none"
            aria-label="Toggle mobile menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-white/10 bg-background/95 backdrop-blur-2xl px-4 py-4 space-y-2">
          <Link
            href="/dashboard"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-200 hover:bg-white/5"
          >
            <LayoutDashboard className="w-4 h-4 text-purple-400" />
            <span>Investigations</span>
          </Link>
          <Link
            href="/investigations/33333333-3333-3333-3333-333333333333"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-200 hover:bg-white/5"
          >
            <Terminal className="w-4 h-4 text-emerald-400" />
            <span>Evidence</span>
          </Link>
          <Link
            href="/#architecture"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-200 hover:bg-white/5"
          >
            <Cpu className="w-4 h-4 text-cyan-400" />
            <span>Architecture</span>
          </Link>
          <Link
            href="/health"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-200 hover:bg-white/5"
          >
            <Activity className="w-4 h-4 text-amber-400" />
            <span>Health</span>
          </Link>
          <div className="pt-2 border-t border-white/5 flex items-center justify-between">
            <Link
              href="/login"
              onClick={() => setMobileMenuOpen(false)}
              className="text-xs text-gray-400 hover:text-white"
            >
              Sign In
            </Link>
            <Link
              href="/dashboard"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3.5 py-1.5 rounded-lg bg-purple-600 text-white text-xs font-semibold"
            >
              New Investigation
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}

