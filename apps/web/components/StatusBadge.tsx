import { CheckCircle2, XCircle, AlertCircle, Clock, ShieldAlert, Bug, Sparkles, Terminal, ShieldCheck } from "lucide-react";
import type { InvestigationStatus, ReproductionStatus, RepositoryStatus } from "@evida/shared/types";

interface StatusBadgeProps {
  status: InvestigationStatus | ReproductionStatus | RepositoryStatus | "OK" | "READY" | "DEGRADED" | "ERROR" | string;
  glow?: boolean;
}

export function StatusBadge({ status, glow = true }: StatusBadgeProps) {
  const normalized = status.toUpperCase();

  if (normalized === "REPRODUCED") {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-semibold bg-rose-950/70 text-rose-300 border border-rose-500/40 backdrop-blur-md ${
          glow ? "shadow-[0_0_15px_-3px_rgba(244,63,94,0.3)]" : ""
        }`}
      >
        <Bug className="w-3.5 h-3.5 text-rose-400" />
        REPRODUCED
      </span>
    );
  }

  if (normalized === "NOT_REPRODUCED") {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-semibold bg-blue-950/70 text-blue-300 border border-blue-500/40 backdrop-blur-md ${
          glow ? "shadow-[0_0_15px_-3px_rgba(59,130,246,0.3)]" : ""
        }`}
      >
        <CheckCircle2 className="w-3.5 h-3.5 text-blue-400" />
        NOT REPRODUCED
      </span>
    );
  }

  if (normalized === "REGRESSION_PROVEN") {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-500/40 backdrop-blur-md ${
          glow ? "shadow-[0_0_15px_-3px_rgba(16,185,129,0.35)]" : ""
        }`}
      >
        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
        REGRESSION PROVEN
      </span>
    );
  }

  if (normalized === "VALIDATED" || normalized === "PATCH_VALIDATED") {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-semibold bg-emerald-950/70 text-emerald-300 border border-emerald-500/40 backdrop-blur-md ${
          glow ? "shadow-[0_0_15px_-3px_rgba(16,185,129,0.3)]" : ""
        }`}
      >
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
        {normalized}
      </span>
    );
  }

  if (normalized === "NOT_VERIFIED" || normalized === "NOT VERIFIED") {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-semibold bg-amber-950/70 text-amber-300 border border-amber-500/40 backdrop-blur-md ${
          glow ? "shadow-[0_0_15px_-3px_rgba(245,158,11,0.25)]" : ""
        }`}
      >
        <Clock className="w-3.5 h-3.5 text-amber-400" />
        NOT VERIFIED
      </span>
    );
  }

  if (normalized === "TEST_REJECTED" || normalized === "PATCH_REJECTED" || normalized === "REJECTED") {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-semibold bg-rose-950/70 text-rose-300 border border-rose-500/40 backdrop-blur-md ${
          glow ? "shadow-[0_0_15px_-3px_rgba(244,63,94,0.3)]" : ""
        }`}
      >
        <XCircle className="w-3.5 h-3.5 text-rose-400" />
        {normalized}
      </span>
    );
  }

  if (normalized === "TIMEOUT" || normalized === "POLICY_BLOCKED") {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-semibold bg-amber-950/70 text-amber-300 border border-amber-500/40 backdrop-blur-md ${
          glow ? "shadow-[0_0_15px_-3px_rgba(245,158,11,0.25)]" : ""
        }`}
      >
        <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
        {normalized}
      </span>
    );
  }

  if (
    normalized === "VERIFIED" ||
    normalized === "COMPLETED" ||
    normalized === "OK" ||
    normalized === "READY"
  ) {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-500/50 backdrop-blur-md ${
          glow ? "shadow-[0_0_20px_-3px_rgba(16,185,129,0.45)]" : ""
        }`}
      >
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
        {normalized}
      </span>
    );
  }

  if (
    normalized === "UNVERIFIED" ||
    normalized === "FAILED" ||
    normalized === "ERROR" ||
    normalized === "EXECUTION_ERROR"
  ) {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-semibold bg-red-950/80 text-red-300 border border-red-500/50 backdrop-blur-md ${
          glow ? "shadow-[0_0_20px_-3px_rgba(239,68,68,0.4)]" : ""
        }`}
      >
        <XCircle className="w-3.5 h-3.5 text-red-400" />
        {normalized === "EXECUTION_ERROR" ? "VERIFICATION ERROR" : normalized}
      </span>
    );
  }

  if (
    normalized === "INGESTING" ||
    normalized === "INVESTIGATING" ||
    normalized === "REPRODUCING" ||
    normalized === "RUNNING" ||
    normalized === "VALIDATING" ||
    normalized === "EXTRACTING" ||
    normalized === "PATCHING" ||
    normalized === "VERIFYING"
  ) {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-semibold bg-indigo-950/70 text-indigo-300 border border-indigo-500/40 backdrop-blur-md ${
          glow ? "shadow-[0_0_15px_-3px_rgba(99,102,241,0.3)]" : ""
        }`}
      >
        <Clock className="w-3.5 h-3.5 animate-spin text-indigo-400" />
        {normalized}
      </span>
    );
  }

  if (normalized === "AI_PROPOSAL") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono font-semibold bg-purple-950/70 text-purple-300 border border-purple-500/40 backdrop-blur-md shadow-[0_0_15px_-3px_rgba(168,85,247,0.3)]">
        <Sparkles className="w-3 h-3 text-purple-400" />
        AI_PROPOSAL
      </span>
    );
  }

  if (normalized === "DETERMINISTIC_EXECUTION") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono font-semibold bg-blue-950/70 text-blue-300 border border-blue-500/40 backdrop-blur-md shadow-[0_0_15px_-3px_rgba(59,130,246,0.3)]">
        <Terminal className="w-3 h-3 text-blue-400" />
        DETERMINISTIC_EXECUTION
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-semibold bg-surface-card text-gray-300 border border-surface-border backdrop-blur-md">
      <AlertCircle className="w-3.5 h-3.5 text-gray-400" />
      {normalized}
    </span>
  );
}

