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
  | "CREATED"
  | "INGESTING"
  | "REPRODUCING"
  | "INVESTIGATING"
  | "VERIFYING"
  | "COMPLETED"
  | "FAILED"
  | "PENDING"
  | "HYPOTHESIZING"
  | "PATCHING"
  | "VERIFIED"
  | "UNVERIFIED";

export type InvestigationEventType =
  | "INVESTIGATION_CREATED"
  | "INVESTIGATION_STARTED"
  | "STATE_TRANSITIONED"
  | "INVESTIGATION_COMPLETED"
  | "INVESTIGATION_FAILED"
  | "INVESTIGATION_HYPOTHESIS_RECORDED"
  | "REGRESSION_TEST_GENERATED"
  | "REGRESSION_TEST_VERIFICATION_STARTED"
  | "REGRESSION_TEST_VERIFICATION_COMPLETED"
  | "REGRESSION_TEST_REJECTED"
  | "REGRESSION_TEST_PROVEN";

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

export interface RootCauseCandidate {
  file: string;
  symbol?: string | null;
  line?: number | null;
  description: string;
}

export interface InvestigationHypothesis {
  hypothesis: string;
  confidence: number;
  root_cause: RootCauseCandidate | string;
  affected_files: string[];
  evidence?: string[];
  recommended_next_action?: string;
  summary?: string;
  reproduction_strategy?: string;
}

export interface InvestigationHypothesisResponse {
  id: string;
  investigation_id: string;
  reproduction_run_id: string;
  model: string;
  provider: string;
  prompt_version: string;
  hypothesis: string;
  confidence: number;
  root_cause: RootCauseCandidate;
  affected_files: string[];
  evidence: string[];
  recommended_next_action: string;
  input_tokens?: number | null;
  output_tokens?: number | null;
  latency_ms?: number | null;
  created_at: string;
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
  investigation_id?: string;
  project_id?: string | null;
  repository_id: string;
  title: string;
  bug_description?: string | null;
  issue_title?: string;
  issue_description?: string | null;
  status: InvestigationStatus;
  hypothesis?: InvestigationHypothesis;
  regression_test_code?: string;
  candidate_patch?: string;
  verification_evidence?: VerificationEvidence;
  created_at: string;
  updated_at: string;
}

export interface InvestigationCreateRequest {
  project_id?: string | null;
  repository_id: string;
  title: string;
  bug_description?: string | null;
}

export interface InvestigationEvent {
  id: string;
  investigation_id: string;
  event_type: InvestigationEventType | string;
  from_status: InvestigationStatus | null;
  to_status: InvestigationStatus;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface InvestigationEventsResponse {
  items: InvestigationEvent[];
  total: number;
}

export interface APIErrorResponse {
  error: {
    code: string;
    message: string;
    request_id?: string;
    details?: unknown;
  };
}

export type RepositoryStatus =
  | "UPLOADED"
  | "VALIDATING"
  | "VALIDATED"
  | "EXTRACTING"
  | "READY"
  | "FAILED";

export type ReproductionStatus =
  | "PENDING"
  | "RUNNING"
  | "REPRODUCED"
  | "NOT_REPRODUCED"
  | "TIMEOUT"
  | "EXECUTION_ERROR"
  | "POLICY_BLOCKED";

export interface RepositoryMetadata {
  id: string;
  investigation_id?: string | null;
  name: string;
  archive_size_bytes: number;
  archive_sha256: string;
  status: RepositoryStatus;
  created_at: string;
  updated_at: string;
}

export interface ReproductionRun {
  id: string;
  investigation_id: string;
  repository_id: string;
  command: string;
  status: ReproductionStatus;
  exit_code?: number | null;
  stdout: string;
  stderr: string;
  duration_ms?: number | null;
  timed_out: boolean;
  created_at: string;
  completed_at?: string | null;
}

export interface ReproductionRequest {
  command: string;
}

export type RegressionTestGenerationStatus = "GENERATED" | "REJECTED";

export type RegressionVerificationStatus =
  | "PENDING"
  | "REGRESSION_PROVEN"
  | "TEST_REJECTED"
  | "TIMEOUT"
  | "EXECUTION_ERROR"
  | "POLICY_BLOCKED";

export type RegressionFailureClassification =
  | "ASSERTION_FAILURE"
  | "TEST_EXECUTION_ERROR"
  | "PASSING"
  | "TIMEOUT"
  | "POLICY_BLOCKED";

export interface RegressionTestProposal {
  test_path: string;
  framework: string;
  language: string;
  description: string;
  test_content: string;
  target_symbol: string;
  target_file: string;
  expected_failure_reason: string;
}

export interface RegressionVerificationResponse {
  id: string;
  command: string;
  status: RegressionVerificationStatus;
  exit_code?: number | null;
  duration_ms?: number | null;
  failure_classification?: RegressionFailureClassification | null;
  stdout: string;
  stderr: string;
  timed_out: boolean;
  created_at: string;
  completed_at?: string | null;
}

export interface RegressionTestResponse {
  id: string;
  investigation_id: string;
  hypothesis_id: string;
  test_path: string;
  framework: string;
  language: string;
  description: string;
  test_content: string;
  target_symbol?: string | null;
  target_file?: string | null;
  expected_failure_reason?: string | null;
  generation_status: RegressionTestGenerationStatus;
  verification_status?: RegressionVerificationStatus | null;
  model?: string | null;
  provider?: string | null;
  prompt_version: string;
  verification?: RegressionVerificationResponse | null;
  created_at: string;
  verified_at?: string | null;
}


