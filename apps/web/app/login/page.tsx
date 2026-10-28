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
      <div className="max-w-md w-full p-8 rounded-3xl border border-white/10 bg-surface/70 backdrop-blur-2xl shadow-glass space-y-6">
        <div className="text-center space-y-2">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-900/60 to-surface border border-purple-500/40 flex items-center justify-center mx-auto shadow-[0_0_25px_-5px_rgba(139,92,246,0.4)]">
            <ShieldCheck className="w-7 h-7 text-purple-400" />
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight text-white">Sign In to EVIDA</h1>
          <p className="text-xs text-gray-400">
            Authentication Shell (Phase 0 Foundation)
          </p>
        </div>

        {submitted ? (
          <div className="p-4 rounded-xl bg-purple-950/40 border border-purple-500/40 text-center space-y-2">
            <p className="text-sm font-semibold text-purple-300">Phase 0 Auth Shell Active</p>
            <p className="text-xs text-gray-300">
              Supabase Auth client is initialized. Live sign-in will be activated in Phase 1.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5 text-purple-400" />
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="developer@evida.local"
                className="w-full px-4 py-2.5 rounded-xl bg-background-dark/90 border border-white/10 text-sm text-white focus:outline-none focus:border-purple-500 font-mono transition-colors shadow-inner"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5 text-purple-400" />
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full px-4 py-2.5 rounded-xl bg-background-dark/90 border border-white/10 text-sm text-white focus:outline-none focus:border-purple-500 font-mono transition-colors shadow-inner"
              />
            </div>

            <button
              type="submit"
              className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white text-sm font-bold flex items-center justify-center gap-2 shadow-[0_0_25px_-5px_rgba(139,92,246,0.5)] transition-all"
            >
              <LogIn className="w-4 h-4" />
              <span>Authenticate</span>
            </button>
          </form>
        )}

        <div className="pt-4 border-t border-white/5 text-center">
          <p className="text-xs text-gray-500 font-mono">
            RLS-Enforced Multi-Tenant Isolation
          </p>
        </div>
      </div>
    </div>
  );
}
