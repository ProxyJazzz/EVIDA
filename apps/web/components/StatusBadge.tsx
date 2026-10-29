import { CheckCircle2, XCircle, AlertCircle, Clock, ShieldAlert, Bug, Sparkles, Terminal, ShieldCheck, Lock, FileCode } from "lucide-react";
import type { InvestigationStatus, ReproductionStatus, RepositoryStatus } from "@evida/shared/types";

interface StatusBadgeProps {
  status: InvestigationStatus | ReproductionStatus | RepositoryStatus | "OK" | "READY" | "DEGRADED" | "ERROR" | string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const normalized = status.toUpperCase();

  if (normalized === "REPRODUCED") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-bold bg-rose-950/80 text-rose-300 border border-rose-800/80">
        <Bug className="w-3.5 h-3.5 text-rose-400" />
        REPRODUCED
      </span>
    );
  }

  if (normalized === "NOT_REPRODUCED") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-bold bg-blue-950/80 text-blue-300 border border-blue-800/80">
        <CheckCircle2 className="w-3.5 h-3.5 text-blue-400" />
        NOT REPRODUCED
      </span>
    );
  }

  if (normalized === "REGRESSION_PROVEN") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-800/80">
        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
        REGRESSION PROVEN
      </span>
    );
  }

  if (normalized === "VALIDATED" || normalized === "PATCH_VALIDATED") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-800/80">
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
        {normalized}
      </span>
    );
  }

  if (normalized === "NOT_VERIFIED" || normalized === "NOT VERIFIED") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-bold bg-amber-950/80 text-amber-300 border border-amber-800/80">
        <Clock className="w-3.5 h-3.5 text-amber-400" />
        NOT VERIFIED
      </span>
    );
  }

  if (normalized === "TEST_REJECTED" || normalized === "PATCH_REJECTED" || normalized === "REJECTED") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-bold bg-rose-950/80 text-rose-300 border border-rose-800/80">
        <XCircle className="w-3.5 h-3.5 text-rose-400" />
        {normalized}
      </span>
    );
  }

  if (normalized === "TIMEOUT" || normalized === "POLICY_BLOCKED") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-bold bg-amber-950/80 text-amber-300 border border-amber-800/80">
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
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-700">
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
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-bold bg-red-950/80 text-red-300 border border-red-800/80">
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
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-bold bg-blue-950/80 text-blue-300 border border-blue-800/80">
        <Clock className="w-3.5 h-3.5 animate-spin text-blue-400" />
        {normalized}
      </span>
    );
  }

  if (normalized === "AI_PROPOSAL") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-purple-950/70 text-purple-300 border border-purple-800">
        <Sparkles className="w-3 h-3 text-purple-400" />
        AI_PROPOSAL
      </span>
    );
  }

  if (normalized === "DETERMINISTIC_EXECUTION") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-blue-950/70 text-blue-300 border border-blue-800">
        <Terminal className="w-3 h-3 text-blue-400" />
        DETERMINISTIC_EXECUTION
      </span>
    );
  }

  if (normalized === "CRYPTOGRAPHIC_INTEGRITY") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-emerald-950/70 text-emerald-300 border border-emerald-800">
        <Lock className="w-3 h-3 text-emerald-400" />
        CRYPTOGRAPHIC_INTEGRITY
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-semibold bg-surface-card text-gray-300 border border-surface-border">
      <AlertCircle className="w-3.5 h-3.5 text-gray-400" />
      {normalized}
    </span>
  );
}
