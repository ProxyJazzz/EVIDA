import { Sparkles, Terminal, Lock, FileCode, Clock } from "lucide-react";

export function ProvenanceLegend() {
  return (
    <div className="tech-panel p-4 space-y-3 font-mono text-xs">
      <div className="flex items-center justify-between border-b border-surface-border pb-2">
        <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
          Evidence Classification Standard
        </span>
        <span className="text-[10px] text-slate-400">EVIDA Audit Standard v1.0</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5 text-[11px]">
        <div className="p-2.5 rounded bg-purple-950/40 border border-purple-800/80">
          <div className="flex items-center gap-1.5 text-purple-300 font-bold mb-1">
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            <span>AI_PROPOSAL</span>
          </div>
          <p className="text-slate-400 text-[10px] leading-relaxed">
            Untrusted AI suggestion. Zero authority until deterministically proven.
          </p>
        </div>

        <div className="p-2.5 rounded bg-blue-950/40 border border-blue-800/80">
          <div className="flex items-center gap-1.5 text-blue-300 font-bold mb-1">
            <Terminal className="w-3.5 h-3.5 text-blue-400" />
            <span>DETERMINISTIC_EXECUTION</span>
          </div>
          <p className="text-slate-400 text-[10px] leading-relaxed">
            Sandboxed process exit code, stdout, and stderr execution proofs.
          </p>
        </div>

        <div className="p-2.5 rounded bg-emerald-950/40 border border-emerald-800/80">
          <div className="flex items-center gap-1.5 text-emerald-300 font-bold mb-1">
            <Lock className="w-3.5 h-3.5 text-emerald-400" />
            <span>CRYPTOGRAPHIC_INTEGRITY</span>
          </div>
          <p className="text-slate-400 text-[10px] leading-relaxed">
            Immutable SHA-256 digests and bit-for-bit repository preservation.
          </p>
        </div>

        <div className="p-2.5 rounded bg-slate-900 border border-slate-700/80">
          <div className="flex items-center gap-1.5 text-slate-300 font-bold mb-1">
            <FileCode className="w-3.5 h-3.5 text-slate-400" />
            <span>SYSTEM_METADATA</span>
          </div>
          <p className="text-slate-400 text-[10px] leading-relaxed">
            Platform timestamps, investigation UUIDs, and tenant isolation identities.
          </p>
        </div>

        <div className="p-2.5 rounded bg-amber-950/40 border border-amber-800/80">
          <div className="flex items-center gap-1.5 text-amber-300 font-bold mb-1">
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            <span>AUDIT_EVENT</span>
          </div>
          <p className="text-slate-400 text-[10px] leading-relaxed">
            Immutable append-only lifecycle transitions persisted to Postgres.
          </p>
        </div>
      </div>
    </div>
  );
}
