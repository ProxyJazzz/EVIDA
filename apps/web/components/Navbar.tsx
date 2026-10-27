import Link from "next/link";
import { ShieldCheck, Terminal, Activity, LogIn, LayoutDashboard } from "lucide-react";

export function Navbar() {
  return (
    <header className="border-b border-surface-border bg-background/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-lg bg-surface flex items-center justify-center border border-surface-border group-hover:border-emerald-500/50 transition-colors">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-lg tracking-wider text-white flex items-center gap-2">
              EVIDA
              <span className="text-[10px] font-mono font-medium px-1.5 py-0.5 rounded bg-surface border border-surface-border text-nvidia">
                NVIDIA AI
              </span>
            </span>
            <span className="text-[11px] text-gray-400 -mt-1 hidden sm:inline">
              Evidence-Driven AI Software Repair
            </span>
          </div>
        </Link>

        <nav className="flex items-center gap-1 sm:gap-4 text-sm font-medium">
          <Link
            href="/health"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-gray-300 hover:text-white hover:bg-surface transition-colors"
          >
            <Activity className="w-4 h-4 text-amber-400" />
            <span>Health</span>
          </Link>
          <Link
            href="/dashboard"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-gray-300 hover:text-white hover:bg-surface transition-colors"
          >
            <LayoutDashboard className="w-4 h-4 text-blue-400" />
            <span>Dashboard</span>
          </Link>
          <Link
            href="/login"
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-md bg-surface border border-surface-border hover:border-gray-500 text-white transition-colors"
          >
            <LogIn className="w-4 h-4" />
            <span>Sign In</span>
          </Link>
        </nav>
      </div>
    </header>
  );
}
