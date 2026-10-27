"use client";

import { useState } from "react";
import { ShieldCheck, LogIn, Key, Mail } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div className="flex-1 flex items-center justify-center px-4 py-16">
      <div className="max-w-md w-full p-8 rounded-xl border border-surface-border bg-surface/80 backdrop-blur-md space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-emerald-950/60 border border-emerald-800/60 flex items-center justify-center mx-auto">
            <ShieldCheck className="w-6 h-6 text-emerald-400" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Sign In to EVIDA</h1>
          <p className="text-xs text-gray-400">
            Authentication Shell (Phase 0 Foundation)
          </p>
        </div>

        {submitted ? (
          <div className="p-4 rounded-lg bg-emerald-950/40 border border-emerald-800/50 text-center space-y-2">
            <p className="text-sm font-semibold text-emerald-400">Phase 0 Auth Shell Active</p>
            <p className="text-xs text-gray-300">
              Supabase Auth client is initialized. Live sign-in will be activated in Phase 1.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-gray-300 flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5 text-gray-400" />
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="developer@evida.local"
                className="w-full px-3.5 py-2 rounded-lg bg-background border border-surface-border text-sm text-white focus:outline-none focus:border-emerald-500 font-mono transition-colors"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-gray-300 flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5 text-gray-400" />
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full px-3.5 py-2 rounded-lg bg-background border border-surface-border text-sm text-white focus:outline-none focus:border-emerald-500 font-mono transition-colors"
              />
            </div>

            <button
              type="submit"
              className="w-full py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold flex items-center justify-center gap-2 shadow-lg shadow-emerald-950/40 transition-colors"
            >
              <LogIn className="w-4 h-4" />
              <span>Authenticate</span>
            </button>
          </form>
        )}

        <div className="pt-4 border-t border-surface-border text-center">
          <p className="text-xs text-gray-500 font-mono">
            RLS-Enforced Multi-Tenant Isolation
          </p>
        </div>
      </div>
    </div>
  );
}
