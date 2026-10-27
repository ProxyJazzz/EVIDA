import { CheckCircle2, XCircle, AlertCircle, Clock, ShieldAlert, Bug } from "lucide-react";
import type { InvestigationStatus, ReproductionStatus, RepositoryStatus } from "@evida/shared/types";

interface StatusBadgeProps {
  status: InvestigationStatus | ReproductionStatus | RepositoryStatus | "OK" | "READY" | "DEGRADED" | "ERROR" | string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const normalized = status.toUpperCase();

  if (normalized === "REPRODUCED") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-semibold bg-rose-950/60 text-rose-400 border border-rose-800/60">
        <Bug className="w-3.5 h-3.5" />
        REPRODUCED
      </span>
    );
  }

  if (normalized === "NOT_REPRODUCED") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-semibold bg-blue-950/60 text-blue-400 border border-blue-800/60">
        <CheckCircle2 className="w-3.5 h-3.5" />
        NOT REPRODUCED
      </span>
    );
  }

  if (normalized === "TIMEOUT" || normalized === "POLICY_BLOCKED") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-semibold bg-amber-950/60 text-amber-400 border border-amber-800/60">
        <ShieldAlert className="w-3.5 h-3.5" />
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
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800/60">
        <CheckCircle2 className="w-3.5 h-3.5" />
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
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-semibold bg-red-950/60 text-red-400 border border-red-800/60">
        <XCircle className="w-3.5 h-3.5" />
        {normalized}
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
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-semibold bg-amber-950/60 text-amber-400 border border-amber-800/60">
        <Clock className="w-3.5 h-3.5 animate-spin" />
        {normalized}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-semibold bg-gray-900 text-gray-400 border border-gray-700">
      <AlertCircle className="w-3.5 h-3.5" />
      {normalized}
    </span>
  );
}
