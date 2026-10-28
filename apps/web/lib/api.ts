/**
 * Client-side API utilities for backend communication.
 */

import {
  AiProvidersResponse,
  AiResponseData,
  BackendHealth,
  ChallengeCatalogItem,
  ChallengeDetail,
  CodeRunResult,
  OAuthProviderItem,
  ProgressSummaryData,
  SolutionReviewData,
  SubmissionHistoryItem,
  SubmissionHistoryResponse,
  SubmissionResponseData,
  UserProfile,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Fetch health status from FastAPI backend.
 * Provides a graceful error fallback if the backend service is offline.
 */
export async function getBackendHealth(): Promise<BackendHealth> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3500);

    const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      signal: controller.signal,
      cache: "no-store",
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return {
        healthy: false,
        errorMessage: `HTTP ${response.status}: ${response.statusText}`,
      };
    }

    const data = await response.json();
    return {
      healthy: data.status === "healthy",
      version: data.version,
      environment: data.environment,
      database: data.database,
    };
  } catch (err: unknown) {
    const message =
      err instanceof Error
        ? err.name === "AbortError"
          ? "Request timed out"
          : err.message
        : "Failed to connect to backend service";

    return {
      healthy: false,
      errorMessage: message,
    };
  }
}

/**
 * Retrieve public catalog of available coding challenges.
 */
export async function getChallengeCatalog(): Promise<{
  data?: ChallengeCatalogItem[];
  error?: string;
}> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${API_BASE_URL}/api/v1/challenges`, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      signal: controller.signal,
      cache: "no-store",
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return {
        error: `Failed to load challenges catalog (HTTP ${response.status})`,
      };
    }

    const data: ChallengeCatalogItem[] = await response.json();
    return { data };
  } catch (err: unknown) {
    const message =
      err instanceof Error ? err.message : "Failed to load challenges catalog";
    return { error: message };
  }
}

/**
 * Retrieve challenge metadata and starter code.
 */
export async function getChallenge(
  challengeId: string
): Promise<{ data?: ChallengeDetail; error?: string }> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${API_BASE_URL}/api/v1/challenges/${challengeId}`, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      signal: controller.signal,
      cache: "no-store",
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return {
        error: `Failed to load challenge (HTTP ${response.status}: ${response.statusText})`,
      };
    }

    const data: ChallengeDetail = await response.json();
    return { data };
  } catch (err: unknown) {
    const message =
      err instanceof Error
        ? err.name === "AbortError"
          ? "Challenge request timed out"
          : err.message
        : "Unable to connect to API server";
    return { error: message };
  }
}

/**
 * Submit candidate code to isolated runner for test execution.
 */
export async function runChallengeCode(
  challengeId: string,
  code: string
): Promise<{ data?: CodeRunResult; error?: string }> {
  try {
    const controller = new AbortController();
    // Allow up to 10s for container creation and execution
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    const response = await fetch(
      `${API_BASE_URL}/api/v1/challenges/${challengeId}/run`,
      {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-Gym-CSRF": "1",
        },
        body: JSON.stringify({ code }),
        signal: controller.signal,
      }
    );

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorJson = await response.json().catch(() => null);
      const detail =
        errorJson?.error?.message ||
        errorJson?.detail ||
        `HTTP ${response.status}: ${response.statusText}`;
      return { error: detail };
    }

    const data: CodeRunResult = await response.json();
    return { data };
  } catch (err: unknown) {
    const message =
      err instanceof Error
        ? err.name === "AbortError"
          ? "Code execution request timed out after 10s"
          : err.message
        : "Failed to connect to execution server";
    return { error: message };
  }
}

/**
 * Submit candidate code for final evaluation and deterministic scoring.
 */
export async function submitChallengeCode(
  challengeId: string,
  code: string
): Promise<{ data?: SubmissionResponseData; error?: string }> {
  try {
    const controller = new AbortController();
    // Allow up to 15s for execution, scoring, and DB persistence
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    const response = await fetch(
      `${API_BASE_URL}/api/v1/challenges/${challengeId}/submit`,
      {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-Gym-CSRF": "1",
        },
        body: JSON.stringify({ code }),
        signal: controller.signal,
      }
    );

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorJson = await response.json().catch(() => null);
      const detail =
        errorJson?.error?.message ||
        errorJson?.detail ||
        `HTTP ${response.status}: ${response.statusText}`;
      return { error: detail };
    }

    const data: SubmissionResponseData = await response.json();
    return { data };
  } catch (err: unknown) {
    const message =
      err instanceof Error
        ? err.name === "AbortError"
          ? "Submission evaluation request timed out after 15s"
          : err.message
        : "Failed to connect to submission server";
    return { error: message };
  }
}

/**
 * Retrieve supported AI providers and active defaults.
 */
export async function getAiProviders(): Promise<{
  data?: AiProvidersResponse;
  error?: string;
}> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 4000);

    const response = await fetch(`${API_BASE_URL}/api/v1/challenges/ai/providers`, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      signal: controller.signal,
      cache: "no-store",
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return {
        error: `Failed to load AI providers (HTTP ${response.status})`,
      };
    }

    const data: AiProvidersResponse = await response.json();
    return { data };
  } catch (err: unknown) {
    const message =
      err instanceof Error ? err.message : "Failed to load AI providers";
    return { error: message };
  }
}

/**
 * Request AI explanation for current code with selected provider.
 */
export async function explainCode(
  challengeId: string,
  code: string,
  question?: string,
  provider?: string
): Promise<{ data?: AiResponseData; error?: string }> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 20000);

    const response = await fetch(
      `${API_BASE_URL}/api/v1/challenges/${challengeId}/ai/explain`,
      {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-Gym-CSRF": "1",
        },
        body: JSON.stringify({ code, question, provider }),
        signal: controller.signal,
      }
    );

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorJson = await response.json().catch(() => null);
      const detail =
        errorJson?.error?.message ||
        errorJson?.detail ||
        `HTTP ${response.status}: ${response.statusText}`;
      return { error: detail };
    }

    const data: AiResponseData = await response.json();
    return { data };
  } catch (err: unknown) {
    const message =
      err instanceof Error
        ? err.name === "AbortError"
          ? "AI assistant request timed out after 20s"
          : err.message
        : "Failed to connect to AI assistant service";
    return { error: message };
  }
}

/**
 * Request progressive debugging hint from AI with selected provider.
 */
export async function getHint(
  challengeId: string,
  code: string,
  hintLevel: number = 1,
  question?: string,
  provider?: string
): Promise<{ data?: AiResponseData; error?: string }> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 20000);

    const response = await fetch(
      `${API_BASE_URL}/api/v1/challenges/${challengeId}/ai/hint`,
      {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-Gym-CSRF": "1",
        },
        body: JSON.stringify({
          code,
          hint_level: hintLevel,
          question,
          provider,
        }),
        signal: controller.signal,
      }
    );

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorJson = await response.json().catch(() => null);
      const detail =
        errorJson?.error?.message ||
        errorJson?.detail ||
        `HTTP ${response.status}: ${response.statusText}`;
      return { error: detail };
    }

    const data: AiResponseData = await response.json();
    return { data };
  } catch (err: unknown) {
    const message =
      err instanceof Error
        ? err.name === "AbortError"
          ? "AI assistant request timed out after 20s"
          : err.message
        : "Failed to connect to AI assistant service";
    return { error: message };
  }
}

/**
 * Retrieve post-submission solution review comparing submitted code against the reference solution.
 */
export async function getSubmissionReview(
  challengeId: string,
  submissionId: string,
  includeAi: boolean = false,
  provider?: string
): Promise<{ data?: SolutionReviewData; error?: string }> {
  try {
    const controller = new AbortController();
    // Allow up to 25s if AI review is requested
    const timeoutId = setTimeout(() => controller.abort(), includeAi ? 25000 : 8000);

    const url = new URL(
      `${API_BASE_URL}/api/v1/challenges/${challengeId}/submissions/${submissionId}/review`
    );
    url.searchParams.set("include_ai", String(includeAi));
    if (provider) {
      url.searchParams.set("provider", provider);
    }

    const response = await fetch(url.toString(), {
      method: "GET",
      credentials: "include",
      headers: {
        Accept: "application/json",
      },
      signal: controller.signal,
      cache: "no-store",
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorJson = await response.json().catch(() => null);
      const detail =
        errorJson?.error?.message ||
        errorJson?.detail ||
        `HTTP ${response.status}: ${response.statusText}`;
      return { error: detail };
    }

    const data: SolutionReviewData = await response.json();
    return { data };
  } catch (err: unknown) {
    const message =
      err instanceof Error
        ? err.name === "AbortError"
          ? "Solution review request timed out"
          : err.message
        : "Failed to connect to review server";
    return { error: message };
  }
}

/**
 * Fetch aggregated student progress metrics based on real formal submissions.
 */
export async function getProgressSummary(): Promise<{
  data?: ProgressSummaryData;
  error?: string;
}> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 6000);

    const response = await fetch(`${API_BASE_URL}/api/v1/progress/summary`, {
      method: "GET",
      credentials: "include",
      headers: {
        Accept: "application/json",
      },
      signal: controller.signal,
      cache: "no-store",
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorJson = await response.json().catch(() => null);
      const detail =
        errorJson?.error?.message ||
        errorJson?.detail ||
        `HTTP ${response.status}: ${response.statusText}`;
      return { error: detail };
    }

    const data: ProgressSummaryData = await response.json();
    return { data };
  } catch (err: unknown) {
    const message =
      err instanceof Error
        ? err.name === "AbortError"
          ? "Progress request timed out"
          : err.message
        : "Failed to connect to progress service";
    return { error: message };
  }
}

/**
 * Fetch paginated formal submission history.
 */
export async function getSubmissionHistory(
  page: number = 1,
  pageSize: number = 20,
  challengeId?: string
): Promise<{
  data?: SubmissionHistoryResponse;
  error?: string;
}> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);

    const url = new URL(`${API_BASE_URL}/api/v1/progress/history`);
    url.searchParams.set("page", String(page));
    url.searchParams.set("page_size", String(pageSize));
    if (challengeId) {
      url.searchParams.set("challenge_id", challengeId);
    }

    const response = await fetch(url.toString(), {
      method: "GET",
      credentials: "include",
      headers: {
        Accept: "application/json",
      },
      signal: controller.signal,
      cache: "no-store",
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorJson = await response.json().catch(() => null);
      const detail =
        errorJson?.error?.message ||
        errorJson?.detail ||
        `HTTP ${response.status}: ${response.statusText}`;
      return { error: detail };
    }

    const data: SubmissionHistoryResponse = await response.json();
    return { data };
  } catch (err: unknown) {
    const message =
      err instanceof Error
        ? err.name === "AbortError"
          ? "History request timed out"
          : err.message
        : "Failed to connect to history service";
    return { error: message };
  }
}

/**
 * Fetch snapshot of a historical formal submission.
 */
export async function getHistoricalSubmission(
  submissionId: string
): Promise<{
  data?: SubmissionHistoryItem;
  error?: string;
}> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(
      `${API_BASE_URL}/api/v1/progress/submissions/${submissionId}`,
      {
        method: "GET",
        credentials: "include",
        headers: {
          Accept: "application/json",
        },
        signal: controller.signal,
        cache: "no-store",
      }
    );

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorJson = await response.json().catch(() => null);
      const detail =
        errorJson?.error?.message ||
        errorJson?.detail ||
        `HTTP ${response.status}: ${response.statusText}`;
      return { error: detail };
    }

    const data: SubmissionHistoryItem = await response.json();
    return { data };
  } catch (err: unknown) {
    const message =
      err instanceof Error ? err.message : "Failed to load submission snapshot";
    return { error: message };
  }
}

// =============================================================================
// Authentication & User Account API
// =============================================================================

/**
 * Fetch profile of currently authenticated user.
 */
export async function getCurrentUser(): Promise<{
  data?: UserProfile;
  error?: string;
  unauthorized?: boolean;
}> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
      method: "GET",
      credentials: "include",
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    });

    if (response.status === 401) {
      return { unauthorized: true };
    }

    if (!response.ok) {
      const err = await response.json().catch(() => null);
      return { error: err?.error?.message || err?.detail || "Authentication error" };
    }

    const data: UserProfile = await response.json();
    return { data };
  } catch (err: unknown) {
    return { error: err instanceof Error ? err.message : "Failed to verify session" };
  }
}

/**
 * Authenticate with email and password.
 */
export async function loginUser(payload: {
  email: string;
  password: string;
}): Promise<{ data?: UserProfile; error?: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-Gym-CSRF": "1",
      },
      body: JSON.stringify(payload),
    });

    const body = await response.json().catch(() => null);

    if (!response.ok) {
      const errorMsg =
        body?.error?.message ||
        body?.detail ||
        "Invalid email or password.";
      return { error: errorMsg };
    }

    return { data: body as UserProfile };
  } catch (err: unknown) {
    return { error: err instanceof Error ? err.message : "Failed to sign in" };
  }
}

/**
 * Register a new student account.
 */
export async function registerUser(payload: {
  email: string;
  password: string;
  full_name?: string;
}): Promise<{ data?: UserProfile; error?: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-Gym-CSRF": "1",
      },
      body: JSON.stringify(payload),
    });

    const body = await response.json().catch(() => null);

    if (!response.ok) {
      const errorMsg =
        body?.error?.message ||
        body?.detail ||
        "Registration failed. Please check your details.";
      return { error: errorMsg };
    }

    return { data: body as UserProfile };
  } catch (err: unknown) {
    return { error: err instanceof Error ? err.message : "Failed to register" };
  }
}

/**
 * Sign out of current session.
 */
export async function logoutUser(): Promise<{ success: boolean; error?: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-Gym-CSRF": "1",
      },
    });

    if (!response.ok) {
      return { success: false, error: "Logout failed" };
    }

    return { success: true };
  } catch (err: unknown) {
    return { success: false, error: err instanceof Error ? err.message : "Failed to sign out" };
  }
}

/**
 * Request password recovery instructions.
 */
export async function requestPasswordReset(
  email: string
): Promise<{ success: boolean; message: string; error?: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/forgot-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-Gym-CSRF": "1",
      },
      body: JSON.stringify({ email }),
    });

    const body = await response.json().catch(() => null);
    if (!response.ok) {
      return {
        success: false,
        message: body?.error?.message || "Failed to process request.",
        error: body?.error?.message,
      };
    }

    return {
      success: true,
      message: body?.message || "If an account matches that email address, instructions have been sent.",
    };
  } catch (err: unknown) {
    return {
      success: false,
      message: err instanceof Error ? err.message : "Failed to request password reset",
    };
  }
}

/**
 * Complete password reset using token.
 */
export async function resetPassword(
  token: string,
  newPassword: string
): Promise<{ success: boolean; message: string; error?: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/reset-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-Gym-CSRF": "1",
      },
      body: JSON.stringify({ token, new_password: newPassword }),
    });

    const body = await response.json().catch(() => null);
    if (!response.ok) {
      return {
        success: false,
        message: body?.error?.message || "Password reset failed.",
        error: body?.error?.message,
      };
    }

    return {
      success: true,
      message: body?.message || "Password successfully reset. Please sign in.",
    };
  } catch (err: unknown) {
    return {
      success: false,
      message: err instanceof Error ? err.message : "Password reset failed",
    };
  }
}

/**
 * Get available OAuth providers and configuration status.
 */
export async function getOAuthProviders(): Promise<{
  data?: OAuthProviderItem[];
  error?: string;
}> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/providers`, {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });

    if (!response.ok) {
      return { error: "Failed to load OAuth providers" };
    }

    const data: OAuthProviderItem[] = await response.json();
    return { data };
  } catch (err: unknown) {
    return { error: err instanceof Error ? err.message : "Failed to load providers" };
  }
}

/**
 * Get LeetCode status and official limitation explanation.
 */
export async function getLeetCodeStatus(): Promise<{
  supports_oauth_sign_in: boolean;
  message: string;
}> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/leetcode/status`, {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });

    if (!response.ok) {
      return {
        supports_oauth_sign_in: false,
        message: "LeetCode does not provide an official public third-party OAuth 2.0 service.",
      };
    }

    return await response.json();
  } catch {
    return {
      supports_oauth_sign_in: false,
      message: "LeetCode does not provide an official public third-party OAuth 2.0 service.",
    };
  }
}
