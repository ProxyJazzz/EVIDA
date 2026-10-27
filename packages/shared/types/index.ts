/**
 * EVIDA Shared Core Contracts and Type Definitions
 */

export type ServiceStatus = "ok" | "degraded" | "error";

export interface HealthCheckResponse {
  status: ServiceStatus;
  service: string;
  version: string;
}

export interface ReadinessCheckResponse {
  status: "ready" | "not_ready";
  service: string;
  version: string;
  checks: {
    database: {
      configured: boolean;
      provider: string;
    };
    ai_provider: {
      configured: boolean;
      provider: string;
      model: string;
    };
    sandbox: {
      ready: boolean;
      runner: string;
    };
  };
}

export type InvestigationStatus =
  | "PENDING"
  | "REPRODUCING"
  | "INVESTIGATING"
  | "HYPOTHESIZING"
  | "PATCHING"
  | "VERIFYING"
  | "VERIFIED"
  | "UNVERIFIED"
  | "FAILED";

export interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface AIResponse {
  content: string;
  model: string;
  provider: string;
  usage?: TokenUsage;
  finish_reason?: string;
  duration_ms: number;
}

export interface ExecutionResult {
  exit_code: number;
  stdout: string;
  stderr: string;
  duration_ms: number;
  timed_out: boolean;
  command: string;
}

export interface InvestigationHypothesis {
  summary: string;
  root_cause: string;
  affected_files: string[];
  confidence: number;
  reproduction_strategy: string;
}

export interface VerificationEvidence {
  reproduction_run: ExecutionResult;
  regression_test_run: ExecutionResult;
  post_patch_test_run: ExecutionResult;
  verified: boolean;
  timestamp: string;
}

export interface Investigation {
  id: string;
  repository_id: string;
  issue_title: string;
  issue_description?: string;
  status: InvestigationStatus;
  hypothesis?: InvestigationHypothesis;
  regression_test_code?: string;
  candidate_patch?: string;
  verification_evidence?: VerificationEvidence;
  created_at: string;
  updated_at: string;
}

export interface APIErrorResponse {
  error: {
    code: string;
    message: string;
    request_id?: string;
    details?: unknown;
  };
}
