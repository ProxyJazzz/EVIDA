interface LogEntry {
  timestamp: string;
  source: string;
  message: string;
  level?: "info" | "success" | "warning" | "error" | "proposal";
}

interface TerminalStreamProps {
  title?: string;
  subtitle?: string;
  logs?: LogEntry[];
}

const defaultLogs: LogEntry[] = [
  {
    timestamp: "10:15:02",
    source: "INGEST",
    message: "broken_python_repo.zip ingested. SHA-256: fa4aec473a84... (4096 bytes)",
    level: "info",
  },
  {
    timestamp: "10:15:05",
    source: "REPRO",
    message: "pytest tests/test_bug.py exited with code 1 in 142ms (REPRODUCED)",
    level: "warning",
  },
  {
    timestamp: "10:15:12",
    source: "HYPOTHESIS",
    message: "AI root cause proposed: divide() in src/calculator.py multiplies (confidence 0.99)",
    level: "proposal",
  },
  {
    timestamp: "10:15:18",
    source: "REGRESSION",
    message: "Synthesized tests/test_regression.py proven against baseline (exit code 1)",
    level: "info",
  },
  {
    timestamp: "10:15:24",
    source: "PATCH",
    message: "Candidate patch structurally validated (1 hunk, 0 test mutations, 0 AST errors)",
    level: "info",
  },
  {
    timestamp: "10:15:28",
    source: "SANDBOX",
    message: "Created fresh ephemeral workspace. Applied candidate patch cleanly.",
    level: "info",
  },
  {
    timestamp: "10:15:30",
    source: "VERIFY",
    message: "Regression test execution post-patch >> PASSED (82.5ms, exit code 0)",
    level: "success",
  },
  {
    timestamp: "10:15:31",
    source: "BASELINE",
    message: "Existing test suite execution >> PASSED (91.0ms, zero regressions)",
    level: "success",
  },
  {
    timestamp: "10:15:32",
    source: "INTEGRITY",
    message: "Original repository artifact bit-for-bit unchanged. SHA-256 match confirmed.",
    level: "success",
  },
  {
    timestamp: "10:15:33",
    source: "VERDICT",
    message: "Double validation satisfied. Final Verdict: VERIFIED.",
    level: "success",
  },
];

export function TerminalStream({
  title = "PIPELINE DIAGNOSTIC STREAM",
  subtitle = "Nebius Token Factory / nvidia/Nemotron-3_5-Lightning",
  logs = defaultLogs,
}: TerminalStreamProps) {
  return (
    <div className="border border-surface-border rounded-lg bg-black/95 p-4 text-slate-300 code-font text-xs leading-relaxed overflow-hidden">
      <div className="text-slate-500 border-b border-surface-border pb-2 mb-2.5 flex flex-wrap justify-between items-center text-[11px]">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-bold text-slate-300">{title}</span>
        </div>
        <span className="text-slate-400">{subtitle}</span>
      </div>
      <div className="space-y-1 overflow-x-auto no-scrollbar font-mono text-[11px] max-h-56 overflow-y-auto">
        {logs.map((log, index) => {
          let colorClass = "text-slate-300";
          if (log.level === "success") colorClass = "text-emerald-400";
          else if (log.level === "warning") colorClass = "text-rose-400";
          else if (log.level === "proposal") colorClass = "text-purple-300";
          else if (log.level === "info") colorClass = "text-blue-300";

          return (
            <p key={index} className="truncate">
              <span className="text-slate-600">[{log.timestamp}]</span>{" "}
              <span className="font-bold text-slate-400">{log.source}:</span>{" "}
              <span className={colorClass}>{log.message}</span>
            </p>
          );
        })}
      </div>
    </div>
  );
}

