import Link from "next/link";
import { ArrowLeft, CheckCircle2, Clock, FileCode, Play, ShieldAlert, Terminal } from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";

interface InvestigationPageProps {
  params: {
    id: string;
  };
}

export default async function InvestigationPage({ params }: InvestigationPageProps) {
  const investigationId = params.id;

  // Render minimal Phase 2 vertical slice layout with demo / fallback data
  const repo = {
    name: "broken_python_repo.zip",
    size_bytes: 4096,
    sha256: "fa4aec473a843aa4d3a2df0840c192a2e28526c6f5d146b0ae7b7fabaf5280a9",
    status: "READY",
  };

  const reproduction = {
    command: "pytest tests/test_bug.py",
    status: "REPRODUCED",
    exit_code: 1,
    duration_ms: 142,
    stdout: "============================= test session starts ==============================\nFAILED tests/test_bug.py::test_divide_bug - assert 20 == 5\n============================== 1 failed in 0.14s ===============================",
    stderr: "",
    verdict: "REPRODUCED",
  };

  const timelineSteps = [
    { label: "CREATED", status: "completed" },
    { label: "INGESTING", status: "completed" },
    { label: "REPRODUCING", status: "completed" },
    { label: "REPRODUCTION_RESULT", status: "completed" },
  ];

  return (
    <div className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Navigation & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-surface-border pb-6">
        <div className="space-y-1">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 text-xs font-mono text-gray-400 hover:text-white transition-colors mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Dashboard
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white font-mono">
              Investigation #{investigationId.slice(0, 8)}
            </h1>
            <StatusBadge status="REPRODUCING" />
          </div>
          <p className="text-sm text-gray-400">
            Fix calculator division bug: <span className="font-mono text-gray-300">divide(10, 2) returns 20 instead of 5</span>
          </p>
        </div>
      </div>

      {/* Timeline Section */}
      <div className="rounded-xl border border-surface-border bg-surface/40 p-6 space-y-4">
        <h2 className="text-sm font-mono font-semibold text-gray-200 uppercase tracking-wider flex items-center gap-2">
          <Clock className="w-4 h-4 text-emerald-400" />
          Investigation Lifecycle Timeline
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {timelineSteps.map((step) => (
            <div
              key={step.label}
              className="p-4 rounded-lg border border-surface-border bg-surface/60 flex flex-col items-center justify-center text-center space-y-2"
            >
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <span className="text-xs font-mono font-bold text-white">{step.label}</span>
              <span className="text-[10px] font-mono text-emerald-400 uppercase">Reached</span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Repository Section */}
        <div className="rounded-xl border border-surface-border bg-surface/40 p-6 space-y-5">
          <div className="flex items-center justify-between border-b border-surface-border pb-4">
            <div className="flex items-center gap-2">
              <FileCode className="w-5 h-5 text-blue-400" />
              <h2 className="text-base font-semibold text-white">Repository Archive</h2>
            </div>
            <StatusBadge status={repo.status} />
          </div>

          <div className="space-y-3 font-mono text-xs">
            <div>
              <span className="text-gray-400 block mb-0.5">Filename</span>
              <span className="text-gray-100 font-semibold">{repo.name}</span>
            </div>
            <div>
              <span className="text-gray-400 block mb-0.5">Archive Size</span>
              <span className="text-gray-100 font-semibold">{(repo.size_bytes / 1024).toFixed(1)} KB ({repo.size_bytes} bytes)</span>
            </div>
            <div>
              <span className="text-gray-400 block mb-0.5">SHA-256 Digest</span>
              <span className="text-gray-300 break-all bg-background/80 p-2 rounded block border border-surface-border">
                {repo.sha256}
              </span>
            </div>
            <div>
              <span className="text-gray-400 block mb-0.5">Security Status</span>
              <span className="text-emerald-400 font-semibold">Verified Safe (Zero Traversal / Bounded Size)</span>
            </div>
          </div>
        </div>

        {/* Reproduction Section */}
        <div className="rounded-xl border border-surface-border bg-surface/40 p-6 space-y-5">
          <div className="flex items-center justify-between border-b border-surface-border pb-4">
            <div className="flex items-center gap-2">
              <Play className="w-5 h-5 text-rose-400" />
              <h2 className="text-base font-semibold text-white">Failure Reproduction</h2>
            </div>
            <StatusBadge status={reproduction.verdict} />
          </div>

          <div className="space-y-3 font-mono text-xs">
            <div>
              <span className="text-gray-400 block mb-0.5">Reproduction Command</span>
              <span className="text-gray-100 font-semibold bg-background/80 px-2 py-1 rounded border border-surface-border inline-block">
                {reproduction.command}
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div>
                <span className="text-gray-400 block mb-0.5">Verdict</span>
                <span className="text-rose-400 font-bold">{reproduction.verdict}</span>
              </div>
              <div>
                <span className="text-gray-400 block mb-0.5">Exit Code</span>
                <span className="text-gray-100 font-bold">{reproduction.exit_code}</span>
              </div>
              <div>
                <span className="text-gray-400 block mb-0.5">Duration</span>
                <span className="text-gray-100">{reproduction.duration_ms} ms</span>
              </div>
            </div>
            <div>
              <span className="text-gray-400 block mb-1">Execution Output (stdout)</span>
              <pre className="bg-black/80 border border-surface-border p-3 rounded text-[11px] text-gray-300 overflow-x-auto whitespace-pre font-mono">
                {reproduction.stdout}
              </pre>
            </div>
            {reproduction.stderr && (
              <div>
                <span className="text-rose-400 block mb-1 flex items-center gap-1">
                  <ShieldAlert className="w-3.5 h-3.5" />
                  Execution Stderr
                </span>
                <pre className="bg-rose-950/20 border border-rose-900/40 p-3 rounded text-[11px] text-rose-300 overflow-x-auto whitespace-pre font-mono">
                  {reproduction.stderr}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
