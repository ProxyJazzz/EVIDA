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
    { label: "INVESTIGATING", status: "active" },
  ];

  const hypothesis = {
    hypothesis: "The divide function in src/calculator.py multiplies its operands instead of dividing them.",
    confidence: 0.99,
    provider: "Nebius",
    model: "nvidia/Nemotron-3_5-Lightning",
    prompt_version: "evida-investigation-v1",
    root_cause: {
      file: "src/calculator.py",
      symbol: "divide",
      line: 2,
      description: "The implementation uses the multiplication operator (*) instead of the division operator (/)."
    },
    affected_files: ["src/calculator.py"],
    evidence: [
      "The reproduction test expects 5 but the function returns 20.",
      "The reproduction command 'pytest tests/test_bug.py' exited with code 1.",
      "Traceback references src/calculator.py line 2 in divide."
    ],
    recommended_next_action: "Generate regression test"
  };

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
            <StatusBadge status="INVESTIGATING" />
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
              className={`p-4 rounded-lg border bg-surface/60 flex flex-col items-center justify-center text-center space-y-2 ${
                step.status === "active" ? "border-amber-500/50 bg-amber-950/20" : "border-surface-border"
              }`}
            >
              {step.status === "active" ? (
                <Clock className="w-5 h-5 text-amber-400 animate-spin" />
              ) : (
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              )}
              <span className="text-xs font-mono font-bold text-white">{step.label}</span>
              <span className={`text-[10px] font-mono uppercase ${step.status === "active" ? "text-amber-400" : "text-emerald-400"}`}>
                {step.status === "active" ? "Current" : "Reached"}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Phase 3: AI Investigation & Hypothesis Section */}
      <div className="rounded-xl border border-amber-500/30 bg-surface/50 p-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-surface-border pb-4">
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                AI Investigation
              </h2>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-amber-950/80 text-amber-300 border border-amber-700/60">
                Proposed Root Cause
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-1">
              AI proposes. Evidence decides. Deterministic verification remains the authority.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-gray-400">Provider:</span>
            <span className="text-white font-semibold bg-surface-border/60 px-2 py-0.5 rounded">{hypothesis.provider}</span>
            <span className="text-gray-400 ml-2">Model:</span>
            <span className="text-amber-300 font-semibold bg-amber-950/60 px-2 py-0.5 rounded border border-amber-800/40">{hypothesis.model}</span>
          </div>
        </div>

        {/* Primary Hypothesis & Confidence Banner */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="md:col-span-3 p-4 rounded-lg bg-background/70 border border-surface-border space-y-2">
            <span className="text-xs font-mono text-gray-400 uppercase tracking-wider block">Hypothesis</span>
            <p className="text-sm text-gray-100 font-medium leading-relaxed">
              {hypothesis.hypothesis}
            </p>
          </div>
          <div className="p-4 rounded-lg bg-background/70 border border-surface-border flex flex-col justify-center items-center text-center">
            <span className="text-xs font-mono text-gray-400 uppercase tracking-wider mb-1">Confidence</span>
            <span className="text-2xl font-mono font-bold text-amber-400">
              {(hypothesis.confidence * 100).toFixed(0)}%
            </span>
            <span className="text-[10px] font-mono text-gray-500 mt-0.5">Untrusted AI Score</span>
          </div>
        </div>

        {/* Root Cause Candidate Details */}
        <div className="space-y-3">
          <h3 className="text-xs font-mono font-semibold text-gray-300 uppercase tracking-wider">
            Root Cause Candidate
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
            <div className="p-3 rounded-lg bg-background/50 border border-surface-border">
              <span className="text-gray-400 block mb-1">File</span>
              <span className="text-amber-300 font-semibold">{hypothesis.root_cause.file}</span>
            </div>
            <div className="p-3 rounded-lg bg-background/50 border border-surface-border">
              <span className="text-gray-400 block mb-1">Symbol</span>
              <span className="text-gray-200 font-semibold">{hypothesis.root_cause.symbol}()</span>
            </div>
            <div className="p-3 rounded-lg bg-background/50 border border-surface-border">
              <span className="text-gray-400 block mb-1">Line</span>
              <span className="text-gray-200 font-semibold">Line {hypothesis.root_cause.line}</span>
            </div>
          </div>
          <div className="p-3 rounded-lg bg-background/50 border border-surface-border font-mono text-xs">
            <span className="text-gray-400 block mb-1">Candidate Description</span>
            <span className="text-gray-300">{hypothesis.root_cause.description}</span>
          </div>
        </div>

        {/* Affected Files & Evidence Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <h3 className="text-xs font-mono font-semibold text-gray-300 uppercase tracking-wider">
              Affected Files
            </h3>
            <ul className="space-y-1.5 font-mono text-xs">
              {hypothesis.affected_files.map((file) => (
                <li key={file} className="px-3 py-2 rounded bg-background/60 border border-surface-border text-gray-200 flex items-center gap-2">
                  <FileCode className="w-3.5 h-3.5 text-blue-400" />
                  {file}
                </li>
              ))}
            </ul>
          </div>
          <div className="space-y-2">
            <h3 className="text-xs font-mono font-semibold text-gray-300 uppercase tracking-wider">
              Grounding Evidence
            </h3>
            <ul className="space-y-1.5 font-mono text-xs">
              {hypothesis.evidence.map((ev, idx) => (
                <li key={idx} className="px-3 py-2 rounded bg-background/60 border border-surface-border text-gray-300 flex items-start gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                  <span>{ev}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Recommended Next Action */}
        <div className="p-4 rounded-lg bg-emerald-950/20 border border-emerald-900/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-0.5">
            <span className="text-xs font-mono text-emerald-400 uppercase tracking-wider block font-semibold">
              Recommended Next Action
            </span>
            <span className="text-sm font-semibold text-white">
              {hypothesis.recommended_next_action}
            </span>
          </div>
          <span className="text-xs font-mono text-gray-400 italic">
            Deterministic verification in Phase 4
          </span>
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
