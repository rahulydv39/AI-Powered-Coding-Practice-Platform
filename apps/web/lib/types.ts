/**
 * Type definitions for AI Coding Gym frontend.
 */

export interface BackendHealth {
  healthy: boolean;
  version?: string;
  environment?: string;
  database?: string;
  errorMessage?: string;
}

export interface ChallengeCatalogItem {
  id: string;
  title: string;
  difficulty: "Easy" | "Medium" | "Hard" | string;
  category: string;
  tags: string[];
  estimated_minutes: number;
  short_summary: string;
}

export interface TestCaseSummaryItem {
  id: string;
  name: string;
  description: string;
}

export interface SandboxStatusInfo {
  docker_available: boolean;
  message: string;
}

export interface ChallengeDetail {
  id: string;
  title: string;
  difficulty: string;
  category?: string;
  tags?: string[];
  estimated_minutes: number;
  short_summary?: string;
  description: string;
  starter_code: string;
  test_cases: TestCaseSummaryItem[];
  sandbox_status: SandboxStatusInfo;
}

export interface TestItemOutcome {
  name: string;
  passed: boolean;
  message?: string | null;
  duration_ms?: number | null;
}

export interface CodeRunResult {
  status: "passed" | "failed" | "error" | "timeout" | "runner_unavailable";
  passed: number;
  failed: number;
  total: number;
  tests: TestItemOutcome[];
  execution_time_ms: number;
  error_message?: string | null;
  stdout?: string | null;
  docker_available: boolean;
}

export interface AiProviderInfo {
  id: "gemini" | "claude" | "openai" | string;
  name: string;
  model: string;
  configured: boolean;
}

export interface AiProvidersResponse {
  default_provider: string;
  providers: AiProviderInfo[];
}

export interface AiResponseData {
  success: boolean;
  mode: "explain" | "hint";
  content: string;
  model: string;
  provider?: string;
  hint_level?: number | null;
  error_message?: string | null;
}

export interface HintHistoryItem {
  level: number;
  content: string;
  timestamp: string;
}

export interface SubmissionResponseData {
  submission_id: string | null;
  challenge_id: string;
  status: "passed" | "failed" | "error" | "timeout" | "runner_unavailable";
  score: number | null;
  passed: number;
  failed: number;
  total: number;
  execution_time_ms: number | null;
  rubric_version: string;
  feedback_summary: string;
  score_disclaimer: string;
  docker_available: boolean;
  error_message: string | null;
  created_at: string | null;
}

export interface KeyDecisionItem {
  id: string;
  title: string;
  explanation: string;
  why_it_matters: string;
}

export interface SemanticComparisonData {
  is_exact_match: boolean;
  is_functionally_equivalent: boolean;
  difference_type:
    | "identical"
    | "formatting_only"
    | "alternative_correct"
    | "functional_bug"
    | "syntax_error";
  summary: string;
  meaningful_differences: string[];
}

export interface AiReviewSectionData {
  available: boolean;
  content: string | null;
  model: string | null;
  provider?: string | null;
  error_message: string | null;
}

export interface SolutionReviewData {
  submission_id: string;
  challenge_id: string;
  score: number | null;
  status: string;
  passed_count: number;
  failed_count: number;
  total_count: number;
  rubric_version: string;
  submitted_code: string;
  reference_code: string;
  unified_diff: string;
  comparison: SemanticComparisonData;
  key_decisions: KeyDecisionItem[];
  learning_takeaways: string[];
  ai_review: AiReviewSectionData | null;
  security_notice: string;
}

export interface SubmissionHistoryItem {
  id: string;
  challenge_id: string;
  challenge_title: string;
  created_at: string;
  score: number | null;
  passed_count: number;
  failed_count: number;
  total_count: number;
  status: string;
  execution_time_ms: number | null;
  rubric_version: string;
  is_review_available: boolean;
  code?: string | null;
}

export interface SubmissionHistoryResponse {
  items: SubmissionHistoryItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ScoreDataPoint {
  submission_id: string;
  challenge_id: string;
  score: number;
  created_at: string;
}

export interface RecentActivityItem {
  id: string;
  challenge_id: string;
  challenge_title: string;
  created_at: string;
  score: number | null;
  status: string;
  passed_count: number;
  total_count: number;
}

export interface PerChallengeProgress {
  challenge_id: string;
  challenge_title: string;
  total_attempts: number;
  scorable_attempts: number;
  best_score: number | null;
  latest_score: number | null;
  first_scorable_score?: number | null;
  score_improvement_delta?: number | null;
  is_solved?: boolean;
  latest_status: string | null;
  latest_submitted_at: string | null;
}

export interface ProgressSummaryData {
  total_submissions: number;
  scorable_submissions: number;
  distinct_challenges_attempted: number;
  problems_solved?: number;
  submission_success_rate?: number | null;
  challenge_solve_rate?: number | null;
  best_score: number | null;
  most_recent_score: number | null;
  average_score: number | null;
  total_passed_tests: number;
  total_failed_tests: number;
  per_challenge: PerChallengeProgress[];
  score_history: ScoreDataPoint[];
  recent_activity?: RecentActivityItem[];
  data_isolation_notice?: string;
}

export interface ChallengePreviewData {
  id: string;
  title: string;
  category: string;
  difficulty: "Beginner" | "Intermediate" | "Advanced";
  estimatedMinutes: number;
  description: string;
  starterCodeSnippet: string;
  sampleTestCases: Array<{
    name: string;
    expected: string;
    status: "failing" | "passing";
  }>;
  aiAssistanceMode: string;
}

export interface FeatureItem {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  iconName: "bug" | "bot" | "chart";
  bulletPoints: string[];
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
  linked_providers: string[];
}

export interface OAuthProviderItem {
  provider: string;
  configured: boolean;
  name: string;
}
