import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  Cpu,
  Download,
  FileCode,
  GitPullRequest,
  Layers,
  Play,
  ShieldAlert,
  ShieldCheck,
  Terminal,
  TestTube2,
  Sparkles,
  Lock,
  AlertTriangle,
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { WorkflowNav } from "@/components/WorkflowNav";
import { ProvenanceLegend } from "@/components/ProvenanceLegend";

interface InvestigationPageProps {
  params: {
    id: string;
  };
}

export default async function InvestigationPage({ params }: InvestigationPageProps) {
  const investigationId = params.id;

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
    stdout:
      "============================= test session starts ==============================\nFAILED tests/test_bug.py::test_divide_bug - assert 20 == 5\n============================== 1 failed in 0.14s ===============================",
    stderr: "",
    verdict: "REPRODUCED",
  };

  const timelineSteps = [
    { label: "CREATED", status: "completed" },
    { label: "INGESTING", status: "completed" },
    { label: "REPRODUCING", status: "completed" },
    { label: "INVESTIGATING", status: "completed" },
    { label: "VERIFYING", status: "completed" },
    { label: "COMPLETED", status: "active" },
  ];

  const verificationRun = {
    id: "run-66666666-6666-6666-6666-666666666666",
    status: "VERIFIED",
    verdict: "VERIFIED",
    failure_classification: null,
    patch_application: {
      status: "APPLIED",
      exit_code: 0,
      stdout: "Applied 1 hunk cleanly to src/calculator.py",
      stderr: "",
      duration_ms: 12.4,
      modified_files: ["src/calculator.py"],
      created_files: [],
      deleted_files: [],
    },
    regression_execution: {
      status: "PASSED",
      command: "pytest tests/test_regression.py",
      exit_code: 0,
      stdout:
        "============================= test session starts ==============================\ntests/test_regression.py .                                               [100%]\n============================== 1 passed in 0.08s ===============================",
      stderr: "",
      duration_ms: 82.5,
    },
    baseline_execution: {
      status: "PASSED",
      command: "pytest",
      exit_code: 0,
      stdout:
        "============================= test session starts ==============================\ntests/test_bug.py .                                                      [100%]\n============================== 1 passed in 0.09s ===============================",
      stderr: "",
      duration_ms: 91.0,
    },
    repository_sha256: "fa4aec473a843aa4d3a2df0840c192a2e28526c6f5d146b0ae7b7fabaf5280a9",
    source_integrity_verified: true,
    created_at: "2026-10-28T10:15:30Z",
    completed_at: "2026-10-28T10:15:32Z",
  };

  const evidenceBundle = {
    bundle_id: "bundle-77777777-7777-7777-7777-777777777777",
    investigation_id: investigationId,
    generated_at: "2026-10-28T10:15:45Z",
    verdict: "VERIFIED",
    bundle_sha256: "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9",
    evidence_items: [
      {
        phase: 1,
        type: "INCIDENT",
        title: "Incident Bug Report",
        provenance: "SYSTEM_METADATA",
        summary: "Bug reported: divide(10, 2) evaluates to 20 instead of 5.",
        sha256: "a1b2c3d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef",
      },
      {
        phase: 2,
        type: "REPOSITORY",
        title: "Source Repository Ingested",
        provenance: "CRYPTOGRAPHIC_INTEGRITY",
        summary: "SHA-256: fa4aec473a843aa4d3a2df0840c192a2e28526c6f5d146b0ae7b7fabaf5280a9 (4096 bytes)",
        sha256: "fa4aec473a843aa4d3a2df0840c192a2e28526c6f5d146b0ae7b7fabaf5280a9",
      },
      {
        phase: 2,
        type: "REPRODUCTION",
        title: "Failure Reproduced in Sandbox",
        provenance: "DETERMINISTIC_EXECUTION",
        summary: "pytest tests/test_bug.py exited with code 1 in 142ms (REPRODUCED).",
        sha256: "b2c3d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef12",
      },
      {
        phase: 3,
        type: "HYPOTHESIS",
        title: "AI Root Cause Proposed",
        provenance: "AI_PROPOSAL",
        summary: "Divide function in src/calculator.py multiplies instead of dividing (confidence 0.99).",
        sha256: "c3d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef1234",
      },
      {
        phase: 4,
        type: "REGRESSION_TEST",
        title: "AI Regression Test Synthesized",
        provenance: "AI_PROPOSAL",
        summary: "tests/test_regression.py: asserts divide(10, 2) == 5.",
        sha256: "d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef123456",
      },
      {
        phase: 4,
        type: "REGRESSION_PROOF",
        title: "Regression Proven Against Original Code",
        provenance: "DETERMINISTIC_EXECUTION",
        summary: "pytest tests/test_regression.py exited with code 1 (REGRESSION_PROVEN).",
        sha256: "e5f678901234567890abcdef1234567890abcdef1234567890abcdef12345678",
      },
      {
        phase: 5,
        type: "PATCH_PROPOSAL",
        title: "AI Patch Candidate Proposed",
        provenance: "AI_PROPOSAL",
        summary: "Unified diff replacing multiplication with division in src/calculator.py.",
        sha256: "f678901234567890abcdef1234567890abcdef1234567890abcdef1234567890",
      },
      {
        phase: 5,
        type: "PATCH_VALIDATION",
        title: "Structural & Security Validation Passed",
        provenance: "DETERMINISTIC_EXECUTION",
        summary: "Zero AST violations, zero test mutations, strict scope checked (VALID).",
        sha256: "078901234567890abcdef1234567890abcdef1234567890abcdef1234567890ab",
      },
      {
        phase: 6,
        type: "PATCH_APPLICATION",
        title: "Patch Applied in Fresh Ephemeral Workspace",
        provenance: "DETERMINISTIC_EXECUTION",
        summary: "Applied cleanly to src/calculator.py (exit code 0).",
        sha256: "18901234567890abcdef1234567890abcdef1234567890abcdef1234567890abcd",
      },
      {
        phase: 6,
        type: "REGRESSION_VERIFICATION",
        title: "Proven Regression Test Passed Post-Patch",
        provenance: "DETERMINISTIC_EXECUTION",
        summary: "pytest tests/test_regression.py exited with code 0 (PASS).",
        sha256: "2901234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
      },
      {
        phase: 6,
        type: "BASELINE_VERIFICATION",
        title: "Baseline Test Suite Passed",
        provenance: "DETERMINISTIC_EXECUTION",
        summary: "pytest exited with code 0 (zero existing test regressions).",
        sha256: "301234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1",
      },
      {
        phase: 6,
        type: "SOURCE_INTEGRITY",
        title: "Cryptographic Source Integrity Preserved",
        provenance: "CRYPTOGRAPHIC_INTEGRITY",
        summary: "Original repository SHA-256 before == after (fa4aec473a84... matched).",
        sha256: "41234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef12",
      },
      {
        phase: 6,
        type: "FINAL_VERDICT",
        title: "Double Validation Final Verdict",
        provenance: "DETERMINISTIC_EXECUTION",
        summary: "Status: VERIFIED. Zero AI discretion. 100% deterministic execution proof.",
        sha256: "5234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef123",
      },
    ],
  };

  const hypothesis = {
    hypothesis:
      "The divide function in src/calculator.py multiplies its operands instead of dividing them.",
    confidence: 0.99,
    provider: "Nebius",
    model: "nvidia/Nemotron-3_5-Lightning",
    prompt_version: "evida-investigation-v1",
    root_cause: {
      file: "src/calculator.py",
      symbol: "divide",
      line: 2,
      description:
        "The implementation uses the multiplication operator (*) instead of the division operator (/)."
    },
    affected_files: ["src/calculator.py"],
    evidence: [
      "The reproduction test expects 5 but the function returns 20.",
      "The reproduction command 'pytest tests/test_bug.py' exited with code 1.",
      "Traceback references src/calculator.py line 2 in divide."
    ],
    recommended_next_action: "Generate regression test"
  };

  const regressionTest = {
    test_path: "tests/test_regression.py",
    framework: "pytest",
    language: "python",
    description:
      "Verifies that divide(10, 2) performs division and returns 5 rather than multiplication (20).",
    test_content:
      "from src.calculator import divide\n\ndef test_divide_regression():\n    assert divide(10, 2) == 5\n",
    target_symbol: "divide",
    target_file: "src/calculator.py",
    expected_failure_reason:
      "divide(10, 2) evaluates to 20 instead of 5, triggering assertion failure",
    generation_status: "GENERATED",
    verification_status: "REGRESSION_PROVEN",
    provider: "Nebius",
    model: "nvidia/Nemotron-3_5-Lightning",
    verification: {
      command: "pytest tests/test_regression.py",
      status: "REGRESSION_PROVEN",
      exit_code: 1,
      duration_ms: 118,
      failure_classification: "ASSERTION_FAILURE",
      stdout:
        "============================= test session starts ==============================\nFAILED tests/test_regression.py::test_divide_regression - assert 20 == 5\n============================== 1 failed in 0.12s ===============================",
      stderr: "",
    },
  };

  const patchCandidate = {
    id: "patch-55555555-5555-5555-5555-555555555555",
    status: "VALIDATED",
    verification_status: "NOT_VERIFIED",
    description:
      "Correct the divide function in src/calculator.py to perform mathematical division instead of multiplication.",
    patch_format: "unified_diff",
    patch_content:
      "--- a/src/calculator.py\n+++ b/src/calculator.py\n@@ -1,2 +1,2 @@\n def divide(a, b):\n-    return a * b\n+    return a / b",
    changed_files: ["src/calculator.py"],
    change_summary: [
      {
        file: "src/calculator.py",
        reason: "Replace incorrect multiplication operator (*) with division operator (/)."
      }
    ],
    reasoning:
      "The proven regression test and hypothesis show divide(10, 2) evaluates to 20 instead of 5 because multiplication was used instead of division.",
    provider: "Nebius",
    model: "nvidia/Nemotron-3_5-Lightning",
    prompt_version: "evida-patch-generation-v1",
    validation: {
      classification: "VALID",
      is_valid: true,
      hunk_count: 1,
      file_count: 1,
      checks: [
        { name: "Unified Diff Syntax & Line Numbers", passed: true },
        { name: "Path Traversal & Boundary Safety", passed: true },
        { name: "Test Immutability (tests/ untouched)", passed: true },
        { name: "Sensitive Files Shield (.env, keys)", passed: true },
        { name: "Scope Boundary (affected files only)", passed: true },
        { name: "Execution Safety (no subprocess/socket)", passed: true },
      ]
    }
  };

  return (
    <div className="flex-1 flex flex-col">
      {/* Workflow Navigation */}
      <WorkflowNav activeScreen="repository" investigationId={investigationId} />

      {/* Main Canvas */}
      <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Top Header & Invariant Strip */}
        <div className="tech-panel p-6 shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-surface-border pb-4">
            <div className="space-y-1">
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-1.5 text-xs font-mono text-slate-400 hover:text-white transition-colors mb-1"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Back to Investigation Ledger</span>
              </Link>
              <div className="flex items-center gap-3 flex-wrap">
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white font-mono">
                  Investigation #{investigationId.slice(0, 8)}
                </h1>
                <StatusBadge status="VERIFYING" />
                <span className="text-xs font-mono px-2.5 py-0.5 rounded bg-surface-card border border-surface-border text-slate-300">
                  Target: {repo.name}
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Fix calculator division bug: <span className="text-slate-200">divide(10, 2) returns 20 instead of 5</span>
              </p>
            </div>

            <div className="flex items-center gap-2">
              <a
                href={`/api/v1/investigations/${investigationId}/evidence/export`}
                download={`evida-evidence-${investigationId}.json`}
                className="inline-flex items-center gap-2 px-3.5 py-2 rounded bg-blue-600 hover:bg-blue-500 text-white text-xs font-mono font-semibold transition"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export Evidence (.json)</span>
              </a>
            </div>
          </div>

          <div className="mt-3 text-[11px] font-mono text-amber-400/90 flex items-center gap-2">
            <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
            <span>
              Forensic Invariant: Original source artifact is strictly immutable. All patch executions occur in isolated ephemeral sandboxes.
            </span>
          </div>
        </div>

        {/* Lifecycle Stepper (Modeled after preview.html Stepper) */}
        <div className="tech-panel p-5 space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-surface-border pb-2.5">
            <span className="font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <Clock className="w-4 h-4 text-emerald-400" />
              Investigation Lifecycle Timeline
            </span>
            <span className="text-slate-400 text-[11px]">Lifecycle Gate 6 of 6 Active</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-6 gap-2.5">
            {timelineSteps.map((step) => (
              <div
                key={step.label}
                className={`p-3 rounded border bg-surface-card flex flex-col items-center justify-center text-center space-y-1 ${
                  step.status === "active"
                    ? "border-emerald-500 bg-emerald-950/20"
                    : "border-surface-border"
                }`}
              >
                <CheckCircle2
                  className={`w-4 h-4 ${
                    step.status === "active" ? "text-emerald-400 animate-pulse" : "text-emerald-500"
                  }`}
                />
                <span className="text-[11px] font-bold text-white">{step.label}</span>
                <span className="text-[10px] text-emerald-400 font-semibold uppercase">
                  {step.status === "active" ? "Current" : "Reached"}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Global Evidence Provenance Legend */}
        <ProvenanceLegend />

        {/* Dual Side-by-Side: Repository Archive & Failure Reproduction (Modeled after preview.html Dual Dropzones) */}
        <div id="repository" className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Repository Section */}
          <div className="tech-panel p-6 flex flex-col justify-between space-y-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-surface-border pb-3">
                <div className="flex items-center gap-2">
                  <FileCode className="w-4 h-4 text-blue-400" />
                  <h2 className="text-sm font-bold text-white font-mono uppercase tracking-wider">
                    Repository Archive
                  </h2>
                </div>
                <StatusBadge status={repo.status} />
              </div>

              <div className="space-y-3 font-mono text-xs">
                <div>
                  <span className="text-slate-400 block mb-0.5">Filename:</span>
                  <span className="text-slate-100 font-semibold">{repo.name}</span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5">Archive Size:</span>
                  <span className="text-slate-100 font-semibold">
                    {(repo.size_bytes / 1024).toFixed(1)} KB ({repo.size_bytes} bytes)
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5">SHA-256 Digest:</span>
                  <span className="text-slate-300 break-all bg-background-deep p-2 rounded block border border-surface-border text-[11px]">
                    {repo.sha256}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5">Security Status:</span>
                  <span className="text-emerald-400 font-semibold flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4" />
                    Verified Safe (Zero Traversal / Bounded Size)
                  </span>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-surface-border text-[11px] font-mono text-slate-400 flex items-center justify-between">
              <span>Status: Stored Immutable Archive</span>
              <span className="text-emerald-400 font-medium">✓ Cryptographic Match</span>
            </div>
          </div>

          {/* Reproduction Section */}
          <div id="reproduction" className="tech-panel p-6 flex flex-col justify-between space-y-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-surface-border pb-3">
                <div className="flex items-center gap-2">
                  <Play className="w-4 h-4 text-rose-400" />
                  <h2 className="text-sm font-bold text-white font-mono uppercase tracking-wider">
                    Failure Reproduction
                  </h2>
                </div>
                <StatusBadge status={reproduction.verdict} />
              </div>

              <div className="space-y-3 font-mono text-xs">
                <div>
                  <span className="text-slate-400 block mb-0.5">Reproduction Command:</span>
                  <span className="text-slate-100 font-semibold bg-background-deep px-2.5 py-1 rounded border border-surface-border inline-block">
                    {reproduction.command}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div className="p-2 rounded bg-surface-card border border-surface-border">
                    <span className="text-slate-400 block mb-0.5 text-[10px]">Verdict</span>
                    <span className="text-rose-400 font-bold">{reproduction.verdict}</span>
                  </div>
                  <div className="p-2 rounded bg-surface-card border border-surface-border">
                    <span className="text-slate-400 block mb-0.5 text-[10px]">Exit Code</span>
                    <span className="text-slate-100 font-bold">{reproduction.exit_code}</span>
                  </div>
                  <div className="p-2 rounded bg-surface-card border border-surface-border">
                    <span className="text-slate-400 block mb-0.5 text-[10px]">Duration</span>
                    <span className="text-slate-100">{reproduction.duration_ms} ms</span>
                  </div>
                </div>
                <div>
                  <span className="text-slate-400 block mb-1">Execution Output (stdout):</span>
                  <pre className="bg-black/90 border border-surface-border p-3 rounded text-[11px] text-slate-300 overflow-x-auto whitespace-pre font-mono">
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

            <div className="pt-3 border-t border-surface-border text-[11px] font-mono text-slate-400 flex items-center justify-between">
              <span>Sandbox Isolation: Fresh Subprocess</span>
              <span className="text-rose-400 font-medium">Defect Proven</span>
            </div>
          </div>
        </div>

        {/* Phase 3: AI Investigation & Hypothesis Section */}
        <div id="hypothesis" className="tech-panel p-6 space-y-5 border-purple-900/60">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-surface-border pb-3">
            <div>
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
                <h2 className="text-sm font-bold text-white font-mono uppercase tracking-wider">
                  AI Investigation
                </h2>
                <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-purple-950/80 text-purple-300 border border-purple-800">
                  Proposed Root Cause
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 font-mono">
                AI proposes root-cause hypothesis. Requires deterministic verification.
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs font-mono">
              <span className="text-slate-400">Provider:</span>
              <span className="text-slate-200 bg-surface-card px-2 py-0.5 rounded border border-surface-border">
                {hypothesis.provider}
              </span>
              <span className="text-slate-400 ml-2">Model:</span>
              <span className="text-purple-300 font-bold bg-purple-950/60 px-2 py-0.5 rounded border border-purple-800">
                {hypothesis.model}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-3 p-4 rounded bg-surface-card border border-surface-border space-y-1.5 font-mono text-xs">
              <span className="text-purple-400 uppercase tracking-wider block font-bold text-[11px]">
                Hypothesis
              </span>
              <p className="text-slate-200 font-sans leading-relaxed text-xs">
                {hypothesis.hypothesis}
              </p>
            </div>
            <div className="p-4 rounded bg-surface-card border border-surface-border flex flex-col justify-center items-center text-center font-mono">
              <span className="text-slate-400 uppercase tracking-wider text-[11px] mb-0.5">Confidence</span>
              <span className="text-2xl font-bold text-purple-400">
                {(hypothesis.confidence * 100).toFixed(0)}%
              </span>
              <span className="text-[10px] text-slate-500 mt-0.5">Untrusted AI Score</span>
            </div>
          </div>

          <div className="space-y-3 font-mono text-xs">
            <span className="font-bold text-slate-300 uppercase tracking-wider block text-[11px]">
              Root Cause Candidate
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="p-2.5 rounded bg-surface-card border border-surface-border">
                <span className="text-slate-400 block mb-0.5 text-[10px]">File</span>
                <span className="text-purple-300 font-bold">{hypothesis.root_cause.file}</span>
              </div>
              <div className="p-2.5 rounded bg-surface-card border border-surface-border">
                <span className="text-slate-400 block mb-0.5 text-[10px]">Symbol</span>
                <span className="text-slate-200 font-semibold">{hypothesis.root_cause.symbol}()</span>
              </div>
              <div className="p-2.5 rounded bg-surface-card border border-surface-border">
                <span className="text-slate-400 block mb-0.5 text-[10px]">Line</span>
                <span className="text-slate-200 font-semibold">Line {hypothesis.root_cause.line}</span>
              </div>
            </div>
            <div className="p-3 rounded bg-surface-card border border-surface-border text-slate-300 text-xs">
              <span className="text-slate-400 block mb-0.5 text-[10px]">Candidate Description:</span>
              <span>{hypothesis.root_cause.description}</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
            <div className="space-y-2">
              <span className="font-bold text-slate-300 uppercase tracking-wider block text-[11px]">
                Affected Files
              </span>
              <ul className="space-y-1.5">
                {hypothesis.affected_files.map((file) => (
                  <li
                    key={file}
                    className="px-3 py-2 rounded bg-surface-card border border-surface-border text-slate-200 flex items-center gap-2"
                  >
                    <FileCode className="w-3.5 h-3.5 text-blue-400" />
                    <span>{file}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="space-y-2">
              <span className="font-bold text-slate-300 uppercase tracking-wider block text-[11px]">
                Grounding Evidence
              </span>
              <ul className="space-y-1.5">
                {hypothesis.evidence.map((ev, idx) => (
                  <li
                    key={idx}
                    className="px-3 py-2 rounded bg-surface-card border border-surface-border text-slate-300 flex items-start gap-2"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 text-purple-400 shrink-0 mt-0.5" />
                    <span>{ev}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="p-3.5 rounded bg-surface-card border border-surface-border flex flex-col sm:flex-row sm:items-center justify-between gap-3 font-mono text-xs">
            <div className="space-y-0.5">
              <span className="text-slate-400 uppercase tracking-wider block font-bold text-[10px]">
                Recommended Next Action
              </span>
              <span className="text-white font-bold">
                {hypothesis.recommended_next_action}
              </span>
            </div>
            <span className="text-slate-500 text-[11px] italic">
              Deterministic verification in Phase 4
            </span>
          </div>
        </div>

        {/* Phase 4: Regression Test Generation & Verification Section */}
        <div id="regression" className="tech-panel p-6 space-y-5 border-blue-900/60">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-surface-border pb-3">
            <div>
              <div className="flex items-center gap-2">
                <TestTube2 className="w-4 h-4 text-blue-400" />
                <h2 className="text-sm font-bold text-white font-mono uppercase tracking-wider">
                  Regression Test
                </h2>
                <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-blue-950/80 text-blue-300 border border-blue-800">
                  Phase 4 Verified
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 font-mono">
                AI proposes test against suspected defect. Deterministic execution in sandbox proves regression.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <StatusBadge status={regressionTest.verification_status} />
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Panel 1: AI Proposal (Untrusted) */}
            <div className="tech-card p-4 space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between border-b border-surface-border pb-2.5">
                <div className="flex items-center gap-1.5">
                  <Cpu className="w-4 h-4 text-purple-400" />
                  <span className="font-bold text-slate-200 uppercase tracking-wider text-[11px]">
                    AI PROPOSED REGRESSION TEST
                  </span>
                </div>
                <span className="text-[10px] uppercase px-1.5 py-0.5 rounded bg-purple-950/60 text-purple-300 border border-purple-800">
                  Untrusted Output
                </span>
              </div>

              <div className="space-y-2 text-xs">
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2 rounded bg-surface border border-surface-border">
                    <span className="text-slate-400 block text-[10px]">Test Path</span>
                    <span className="text-slate-100 font-bold">{regressionTest.test_path}</span>
                  </div>
                  <div className="p-2 rounded bg-surface border border-surface-border">
                    <span className="text-slate-400 block text-[10px]">Framework</span>
                    <span className="text-slate-100 font-semibold">{regressionTest.framework}</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2 rounded bg-surface border border-surface-border">
                    <span className="text-slate-400 block text-[10px]">Target File</span>
                    <span className="text-purple-300 font-bold">{regressionTest.target_file}</span>
                  </div>
                  <div className="p-2 rounded bg-surface border border-surface-border">
                    <span className="text-slate-400 block text-[10px]">Target Symbol</span>
                    <span className="text-slate-200 font-semibold">{regressionTest.target_symbol}()</span>
                  </div>
                </div>

                <div className="p-2 rounded bg-surface border border-surface-border">
                  <span className="text-slate-400 block text-[10px]">Expected Failure Reason</span>
                  <span className="text-rose-300 font-mono text-[11px]">{regressionTest.expected_failure_reason}</span>
                </div>

                <div>
                  <span className="text-slate-400 block mb-1 text-[10px]">Generated Test Code</span>
                  <pre className="bg-black/95 border border-surface-border p-3 rounded text-[11px] text-slate-200 overflow-x-auto whitespace-pre font-mono">
                    {regressionTest.test_content}
                  </pre>
                </div>
              </div>
            </div>

            {/* Panel 2: Deterministic Verification (Objective Evidence) */}
            <div className="tech-card p-4 space-y-3 font-mono text-xs border-emerald-900/60">
              <div className="flex items-center justify-between border-b border-surface-border pb-2.5">
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="font-bold text-slate-200 uppercase tracking-wider text-[11px]">
                    DETERMINISTIC VERIFICATION
                  </span>
                </div>
                <StatusBadge status={regressionTest.verification.status} />
              </div>

              <div className="p-3 rounded bg-emerald-950/30 border border-emerald-800/60 space-y-1">
                <span className="text-emerald-300 font-bold block text-xs">
                  {regressionTest.verification.status === "REGRESSION_PROVEN"
                    ? "REGRESSION PROVEN"
                    : regressionTest.verification.status === "TEST_REJECTED"
                    ? "TEST REJECTED"
                    : "VERIFICATION ERROR"}
                </span>
                <p className="text-slate-300 text-[11px] leading-relaxed">
                  {regressionTest.verification.status === "REGRESSION_PROVEN"
                    ? "EVIDA executed the generated regression test against the original repository and observed the expected failure."
                    : regressionTest.verification.status === "TEST_REJECTED"
                    ? "The generated test did not demonstrate the original defect."
                    : "Sandbox or setup execution failure occurred."}
                </p>
              </div>

              <div className="space-y-2">
                <div className="grid grid-cols-3 gap-2">
                  <div className="p-2 rounded bg-surface border border-surface-border">
                    <span className="text-slate-400 block text-[10px]">Classification</span>
                    <span className="text-rose-400 font-bold">{regressionTest.verification.failure_classification}</span>
                  </div>
                  <div className="p-2 rounded bg-surface border border-surface-border">
                    <span className="text-slate-400 block text-[10px]">Exit Code</span>
                    <span className="text-slate-100 font-bold">{regressionTest.verification.exit_code}</span>
                  </div>
                  <div className="p-2 rounded bg-surface border border-surface-border">
                    <span className="text-slate-400 block text-[10px]">Duration</span>
                    <span className="text-slate-100">{regressionTest.verification.duration_ms} ms</span>
                  </div>
                </div>

                <div>
                  <span className="text-slate-400 block text-[10px] mb-0.5">Verification Command</span>
                  <span className="text-slate-200 bg-surface px-2.5 py-1 rounded border border-surface-border inline-block text-[11px]">
                    {regressionTest.verification.command}
                  </span>
                </div>

                <div>
                  <span className="text-slate-400 block text-[10px] mb-1">Sandbox Execution Output (stdout)</span>
                  <pre className="bg-black/95 border border-surface-border p-3 rounded text-[11px] text-slate-300 overflow-x-auto whitespace-pre font-mono">
                    {regressionTest.verification.stdout}
                  </pre>
                </div>
              </div>

              <div className="p-2.5 rounded bg-surface border border-surface-border text-[11px] text-slate-400">
                <span className="text-amber-400 font-bold block mb-0.5">EVIDA Invariant</span>
                <span>REGRESSION_PROVEN confirms defect reproduction on the original repository. Source code has not been modified; bug is not yet fixed. Ready for Phase 5 patch generation.</span>
              </div>
            </div>
          </div>
        </div>

        {/* Phase 5: Patch Generation & Candidate Validation */}
        <div id="patch" className="tech-panel p-6 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-surface-border pb-3">
            <div className="flex items-center gap-2.5">
              <GitPullRequest className="w-4 h-4 text-blue-400" />
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-bold text-white font-mono uppercase tracking-wider">
                    Patch Candidate
                  </h2>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface-card border border-surface-border text-slate-300 font-bold">
                    PHASE 5
                  </span>
                </div>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  AI proposes repair candidate. Deterministic rules validate diff, bounds, and security.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <StatusBadge status={patchCandidate.status} />
              <StatusBadge status={patchCandidate.verification_status} />
            </div>
          </div>

          <div className="p-3.5 rounded bg-amber-950/20 border border-amber-800/60 font-mono text-xs text-amber-300 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="space-y-0.5">
              <div className="flex items-center gap-2 font-bold text-amber-400">
                <span className="px-1.5 py-0.5 rounded bg-amber-900/60 border border-amber-700 text-[10px]">
                  NOT VERIFIED
                </span>
                <span>Candidate Proposed &amp; Validated — Not Executed</span>
              </div>
              <p className="text-[11px] text-slate-300 font-sans">
                This patch was proposed and structurally validated by EVIDA. It has not yet been executed against the proven regression test. Original source code remains untouched.
              </p>
            </div>
            <div className="text-[11px] text-slate-400 sm:text-right shrink-0">
              <span className="text-slate-500">Pipeline Invariant:</span>
              <div className="text-slate-200 font-bold">PATCH_VALIDATED ≠ BUG_FIXED</div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="tech-card p-4 space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between border-b border-surface-border pb-2">
                <span className="font-bold text-purple-400 uppercase tracking-wider text-[11px]">
                  AI PROPOSED PATCH
                </span>
                <span className="text-slate-400 text-[10px]">{patchCandidate.model}</span>
              </div>

              <div className="space-y-2">
                <div>
                  <span className="text-slate-400 block text-[10px]">Description</span>
                  <p className="text-slate-200 bg-surface p-2.5 rounded border border-surface-border text-xs">
                    {patchCandidate.description}
                  </p>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Reasoning / Rationale</span>
                  <p className="text-slate-300 bg-surface p-2.5 rounded border border-surface-border text-[11px]">
                    {patchCandidate.reasoning}
                  </p>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] mb-1">Declared Changed Files</span>
                  <div className="flex flex-wrap gap-2">
                    {patchCandidate.changed_files.map((file) => (
                      <span
                        key={file}
                        className="px-2 py-0.5 rounded bg-surface border border-surface-border text-purple-300 font-mono text-[11px]"
                      >
                        {file}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="tech-card p-4 space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between border-b border-surface-border pb-2">
                <span className="font-bold text-blue-400 uppercase tracking-wider text-[11px]">
                  UNIFIED DIFF PREVIEW
                </span>
                <span className="text-slate-400 text-[10px]">
                  {patchCandidate.validation.hunk_count} hunk(s) · {patchCandidate.validation.file_count} file(s)
                </span>
              </div>

              <div className="rounded bg-black/95 border border-surface-border p-3 font-mono text-[11px] overflow-x-auto space-y-0.5">
                {patchCandidate.patch_content.split("\n").map((line, idx) => {
                  let textClass = "text-slate-400";
                  let bgClass = "bg-transparent";
                  if (line.startsWith("---") || line.startsWith("+++")) {
                    textClass = "text-blue-300 font-bold";
                    bgClass = "bg-blue-950/20";
                  } else if (line.startsWith("@@")) {
                    textClass = "text-cyan-400 font-semibold";
                    bgClass = "bg-cyan-950/20";
                  } else if (line.startsWith("+")) {
                    textClass = "text-emerald-400 font-semibold";
                    bgClass = "bg-emerald-950/30";
                  } else if (line.startsWith("-")) {
                    textClass = "text-rose-400 font-semibold";
                    bgClass = "bg-rose-950/30";
                  }
                  return (
                    <div key={idx} className={`px-2 py-0.5 rounded ${bgClass} ${textClass} whitespace-pre`}>
                      {line}
                    </div>
                  );
                })}
              </div>

              <div className="p-3 rounded bg-surface border border-surface-border space-y-2">
                <div className="flex items-center justify-between border-b border-surface-border pb-1.5">
                  <span className="text-[11px] font-bold text-slate-300 flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                    Deterministic Validation Checks
                  </span>
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800 font-bold">
                    {patchCandidate.validation.classification}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-1.5 text-[10px]">
                  {patchCandidate.validation.checks.map((check, idx) => (
                    <div key={idx} className="flex items-center gap-1.5 text-slate-300">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                      <span className="truncate">{check.name}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-2.5 rounded bg-surface border border-surface-border text-[11px] text-slate-400">
                <span className="text-amber-400 font-bold block mb-0.5">Phase 5 Safety Guarantee</span>
                <span>The candidate patch has not mutated the source workspace. Phase 6 will execute the patch and rerun the proven regression test inside an isolated sandbox.</span>
              </div>
            </div>
          </div>
        </div>

        {/* Phase 6 — Deterministic Verification & Double Validation */}
        <div id="verification" className="tech-panel p-6 space-y-5 border-emerald-900/60">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-surface-border pb-3">
            <div className="flex items-center gap-2.5">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-bold text-white font-mono uppercase tracking-wider">
                    Phase 6 — Deterministic Verification &amp; Double Validation
                  </h2>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface-card border border-surface-border text-emerald-400 font-bold">
                    PHASE 6
                  </span>
                </div>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  Isolated sandbox execution. Proven regression test + baseline suite. Zero AI discretion.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <StatusBadge status={verificationRun.status} />
            </div>
          </div>

          <div className="p-3.5 rounded bg-emerald-950/30 border border-emerald-800/60 font-mono text-xs text-emerald-300 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="space-y-0.5">
              <div className="flex items-center gap-2 font-bold text-emerald-400">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Double Validation Rule Satisfied: VERIFIED</span>
              </div>
              <p className="text-[11px] text-slate-300 font-sans leading-relaxed">
                The candidate patch was applied in an isolated workspace. The proven regression test passed after patch application. The baseline test suite also passed. The original repository artifact remained unchanged.
              </p>
            </div>
            <div className="text-[11px] text-slate-400 sm:text-right shrink-0">
              <span className="text-slate-500">Core Maxim:</span>
              <div className="text-emerald-400 font-bold">AI PROPOSES. EVIDENCE DECIDES.</div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
            <div className="tech-card p-4 space-y-2.5">
              <div className="flex items-center justify-between border-b border-surface-border pb-2">
                <span className="text-slate-400 font-bold text-[11px]">Patch Application</span>
                <span className="text-emerald-400 font-bold text-[11px] flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Applied successfully
                </span>
              </div>
              <div className="space-y-1 text-[11px]">
                <div className="flex justify-between">
                  <span className="text-slate-500">Exit Code:</span>
                  <span className="text-slate-200 font-bold">0</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Duration:</span>
                  <span className="text-slate-200">{verificationRun.patch_application.duration_ms} ms</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Modified:</span>
                  <span className="text-blue-300">src/calculator.py</span>
                </div>
              </div>
            </div>

            <div className="tech-card p-4 space-y-2.5">
              <div className="flex items-center justify-between border-b border-surface-border pb-2">
                <span className="text-slate-400 font-bold text-[11px]">Original Regression</span>
                <span className="text-emerald-400 font-bold text-[11px] flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  PASS
                </span>
              </div>
              <div className="space-y-1 text-[11px]">
                <div className="flex justify-between">
                  <span className="text-slate-500">Before Patch:</span>
                  <span className="text-rose-400 font-bold">FAIL</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">After Patch:</span>
                  <span className="text-emerald-400 font-bold">PASS</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Duration:</span>
                  <span className="text-slate-200">{verificationRun.regression_execution.duration_ms} ms</span>
                </div>
              </div>
            </div>

            <div className="tech-card p-4 space-y-2.5">
              <div className="flex items-center justify-between border-b border-surface-border pb-2">
                <span className="text-slate-400 font-bold text-[11px]">Existing Test Suite</span>
                <span className="text-emerald-400 font-bold text-[11px] flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  PASS
                </span>
              </div>
              <div className="space-y-1 text-[11px]">
                <div className="flex justify-between">
                  <span className="text-slate-500">Baseline Suite:</span>
                  <span className="text-emerald-400 font-bold">PASS</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Injected Test:</span>
                  <span className="text-slate-300">Cleanly Removed</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Duration:</span>
                  <span className="text-slate-200">{verificationRun.baseline_execution.duration_ms} ms</span>
                </div>
              </div>
            </div>
          </div>

          <div className="p-3 rounded bg-surface-card border border-surface-border font-mono text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
              <span className="text-slate-300 font-bold">Cryptographic Source Integrity:</span>
              <span className="text-emerald-400 font-bold">The original repository artifact remained unchanged.</span>
            </div>
            <div className="text-[11px] text-slate-400 flex items-center gap-2">
              <span>SHA-256:</span>
              <span className="text-slate-200 bg-surface px-2 py-0.5 rounded border border-surface-border font-mono">
                {verificationRun.repository_sha256.slice(0, 16)}... (Pre == Post)
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 font-mono text-xs">
            <div>
              <span className="text-slate-400 block mb-1 text-[11px]">Regression Test Output (Post-Patch)</span>
              <pre className="bg-black/95 border border-surface-border p-3 rounded text-[11px] text-emerald-400 overflow-x-auto whitespace-pre font-mono">
                {verificationRun.regression_execution.stdout}
              </pre>
            </div>
            <div>
              <span className="text-slate-400 block mb-1 text-[11px]">Baseline Test Suite Output</span>
              <pre className="bg-black/95 border border-surface-border p-3 rounded text-[11px] text-emerald-400 overflow-x-auto whitespace-pre font-mono">
                {verificationRun.baseline_execution.stdout}
              </pre>
            </div>
          </div>

          <div className="p-4 rounded bg-surface-card border border-surface-border space-y-2.5 font-mono">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
              EVIDA Evidence Chain: AI Proposal vs. Deterministic Evidence
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 text-[11px]">
              <div className="p-2 rounded bg-surface border border-surface-border flex items-center justify-between">
                <span className="text-slate-300">1. Bug Reproduced</span>
                <span className="px-1.5 py-0.5 rounded bg-blue-950/60 border border-blue-800 text-[10px] text-blue-300 font-bold">
                  DETERMINISTIC EVIDENCE
                </span>
              </div>
              <div className="p-2 rounded bg-surface border border-surface-border flex items-center justify-between">
                <span className="text-slate-300">2. Hypothesis Proposed</span>
                <span className="px-1.5 py-0.5 rounded bg-purple-950/60 border border-purple-800 text-[10px] text-purple-300 font-bold">
                  AI PROPOSAL
                </span>
              </div>
              <div className="p-2 rounded bg-surface border border-surface-border flex items-center justify-between">
                <span className="text-slate-300">3. Regression Proven</span>
                <span className="px-1.5 py-0.5 rounded bg-blue-950/60 border border-blue-800 text-[10px] text-blue-300 font-bold">
                  DETERMINISTIC EVIDENCE
                </span>
              </div>
              <div className="p-2 rounded bg-surface border border-surface-border flex items-center justify-between">
                <span className="text-slate-300">4. Patch Synthesized</span>
                <span className="px-1.5 py-0.5 rounded bg-purple-950/60 border border-purple-800 text-[10px] text-purple-300 font-bold">
                  AI PROPOSAL
                </span>
              </div>
              <div className="p-2 rounded bg-surface border border-surface-border flex items-center justify-between">
                <span className="text-slate-300">5. Patch Validated</span>
                <span className="px-1.5 py-0.5 rounded bg-blue-950/60 border border-blue-800 text-[10px] text-blue-300 font-bold">
                  DETERMINISTIC EVIDENCE
                </span>
              </div>
              <div className="p-2 rounded bg-surface border border-surface-border flex items-center justify-between">
                <span className="text-slate-300">6. Ephemeral Execution</span>
                <span className="px-1.5 py-0.5 rounded bg-blue-950/60 border border-blue-800 text-[10px] text-blue-300 font-bold">
                  DETERMINISTIC EVIDENCE
                </span>
              </div>
              <div className="p-2 rounded bg-surface border border-surface-border flex items-center justify-between">
                <span className="text-slate-300">7. Regression Passed</span>
                <span className="px-1.5 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-[10px] text-emerald-300 font-bold">
                  DETERMINISTIC EVIDENCE
                </span>
              </div>
              <div className="p-2 rounded bg-surface border border-surface-border flex items-center justify-between">
                <span className="text-slate-300">8. Baseline Passed</span>
                <span className="px-1.5 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-[10px] text-emerald-300 font-bold">
                  DETERMINISTIC EVIDENCE
                </span>
              </div>
              <div className="p-2 rounded bg-surface border border-surface-border flex items-center justify-between">
                <span className="text-slate-300">9. Source Unchanged</span>
                <span className="px-1.5 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-[10px] text-emerald-300 font-bold">
                  DETERMINISTIC EVIDENCE
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Phase 7: Evidence Bundle, Provenance & Audit System */}
        <div id="evidence" className="tech-panel p-6 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-surface-border pb-3">
            <div className="space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-950/80 text-purple-300 border border-purple-800">
                  PHASE 7
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-800">
                  AUDITABLE RECORD
                </span>
                <h2 className="text-sm font-bold text-white font-mono uppercase tracking-wider flex items-center gap-2">
                  <Layers className="w-4 h-4 text-purple-400" />
                  Phase 7 — Evidence Bundle, Provenance &amp; Audit System
                </h2>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Aggregated cryptographic audit chain across Phases 1–6. AI proposes; deterministic evidence decides.
              </p>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              <a
                href={`/api/v1/investigations/${investigationId}/evidence/export`}
                download={`evida-evidence-${investigationId}.json`}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-surface border border-surface-border hover:bg-surface-hover text-xs font-mono font-bold text-slate-200 transition"
              >
                <Download className="w-3.5 h-3.5 text-purple-400" />
                <span>Export Bundle (.json)</span>
              </a>
            </div>
          </div>

          <div className="p-3.5 rounded bg-surface-card border border-surface-border font-mono text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2 flex-wrap">
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
              <span className="text-slate-400 font-bold">Evidence Bundle SHA-256:</span>
              <span className="text-emerald-300 font-bold break-all bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800 text-[11px]">
                {evidenceBundle.bundle_sha256}
              </span>
            </div>
            <div className="text-[11px] text-slate-400 flex items-center gap-2 shrink-0">
              <span className="text-slate-500">Generated:</span>
              <span className="text-slate-200">{evidenceBundle.generated_at}</span>
            </div>
          </div>

          <div className="p-3.5 rounded bg-surface-card border border-surface-border space-y-2 font-mono">
            <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider block">
              Provenance Taxonomy
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 text-[10px]">
              <div className="p-2 rounded bg-purple-950/40 border border-purple-800">
                <span className="text-purple-300 font-bold block">AI_PROPOSAL</span>
                <span className="text-slate-400 text-[9px]">Untrusted suggestion</span>
              </div>
              <div className="p-2 rounded bg-blue-950/40 border border-blue-800">
                <span className="text-blue-300 font-bold block">DETERMINISTIC_EXECUTION</span>
                <span className="text-slate-400 text-[9px]">Sandboxed command output</span>
              </div>
              <div className="p-2 rounded bg-emerald-950/40 border border-emerald-800">
                <span className="text-emerald-300 font-bold block">CRYPTOGRAPHIC_INTEGRITY</span>
                <span className="text-slate-400 text-[9px]">Immutable SHA-256</span>
              </div>
              <div className="p-2 rounded bg-slate-900 border border-slate-700">
                <span className="text-slate-300 font-bold block">SYSTEM_METADATA</span>
                <span className="text-slate-400 text-[9px]">Platform timestamps &amp; IDs</span>
              </div>
              <div className="p-2 rounded bg-amber-950/40 border border-amber-800">
                <span className="text-amber-300 font-bold block">AUDIT_EVENT</span>
                <span className="text-slate-400 text-[9px]">Append-only audit record</span>
              </div>
            </div>
          </div>

          <div className="p-4 rounded bg-surface-card border border-surface-border space-y-3 font-mono">
            <div className="flex items-center justify-between border-b border-surface-border pb-2">
              <span className="text-xs font-bold text-slate-200 uppercase tracking-wider block">
                Double-Validation Authoritative Confirmation Checklist
              </span>
              <span className="text-emerald-400 font-bold text-xs flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                100% EVIDENCE SATISFIED
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 text-[11px]">
              <div className="p-2 rounded bg-surface border border-surface-border flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span className="text-slate-300">Failure Reproduced</span>
              </div>
              <div className="p-2 rounded bg-surface border border-surface-border flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span className="text-slate-300">Regression Proven</span>
              </div>
              <div className="p-2 rounded bg-surface border border-surface-border flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span className="text-slate-300">Patch Validated</span>
              </div>
              <div className="p-2 rounded bg-surface border border-surface-border flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span className="text-slate-300">Regression Passed Post-Patch</span>
              </div>
              <div className="p-2 rounded bg-surface border border-surface-border flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span className="text-slate-300">Baseline Suite Passed</span>
              </div>
              <div className="p-2 rounded bg-surface border border-surface-border flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span className="text-slate-300">Source Hash Unchanged</span>
              </div>
              <div className="p-2 rounded bg-surface border border-surface-border flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span className="text-slate-300">Isolated Sandbox Executed</span>
              </div>
              <div className="p-2 rounded bg-surface border border-surface-border flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                <span className="text-slate-300">Audit Trail Immutable</span>
              </div>
            </div>
          </div>

          <div className="space-y-3 font-mono">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
              Evidence Chain Items ({evidenceBundle.evidence_items.length})
            </span>
            <div className="space-y-2">
              {evidenceBundle.evidence_items.map((item, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded bg-surface-card border border-surface-border flex flex-col md:flex-row md:items-center justify-between gap-2 hover:bg-surface-hover transition-colors"
                >
                  <div className="flex items-start md:items-center gap-3">
                    <span className="text-xs font-bold text-slate-500 font-mono w-6">
                      #{String(idx + 1).padStart(2, "0")}
                    </span>
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-slate-200 font-bold text-xs">{item.title}</span>
                        <span className="text-[10px] text-slate-500">({item.type})</span>
                        <span
                          className={`px-1.5 py-0.5 rounded border text-[9px] font-bold ${
                            item.provenance === "AI_PROPOSAL"
                              ? "bg-purple-950/70 border-purple-800 text-purple-300"
                              : item.provenance === "DETERMINISTIC_EXECUTION"
                              ? "bg-blue-950/70 border-blue-800 text-blue-300"
                              : item.provenance === "CRYPTOGRAPHIC_INTEGRITY"
                              ? "bg-emerald-950/70 border-emerald-800 text-emerald-300"
                              : "bg-slate-900 border-slate-700 text-slate-300"
                          }`}
                        >
                          {item.provenance}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 font-sans">{item.summary}</p>
                    </div>
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono shrink-0 pl-9 md:pl-0">
                    <span className="text-slate-600 mr-1">SHA-256:</span>
                    <span className="text-slate-300 bg-surface px-1.5 py-0.5 rounded border border-surface-border">
                      {item.sha256.slice(0, 16)}...
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
