"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Play,
  RotateCcw,
  Clock,
  ShieldAlert,
  ShieldCheck,
  AlertCircle,
  Award,
  LogIn,
  Send,
  X,
  Terminal,
  Sparkles,
  BookOpen,
  Lock,
  Tag,
  CheckCircle2,
  Code2,
} from "lucide-react";
import { CodeEditor } from "@/components/CodeEditor";
import { TestResults } from "@/components/TestResults";
import { SubmissionResultPanel } from "@/components/SubmissionResultPanel";
import { SolutionReviewPanel } from "@/components/SolutionReviewPanel";
import { AiAssistantPanel } from "@/components/AiAssistantPanel";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { useAuth } from "@/lib/auth-context";
import {
  getChallenge,
  getSubmissionReview,
  runChallengeCode,
  submitChallengeCode,
} from "@/lib/api";
import {
  ChallengeDetail,
  CodeRunResult,
  SolutionReviewData,
  SubmissionResponseData,
} from "@/lib/types";

type ConsoleTab = "tests" | "submission" | "ai" | "review";
type MobileSegment = "problem" | "code" | "console";

interface ChallengeWorkspaceProps {
  challengeId: string;
}

export function ChallengeWorkspace({ challengeId }: ChallengeWorkspaceProps) {
  const { user } = useAuth();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showResetModal, setShowResetModal] = useState(false);
  const [challenge, setChallenge] = useState<ChallengeDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Workbench navigation
  const [activeConsoleTab, setActiveConsoleTab] = useState<ConsoleTab>("tests");
  const [mobileSegment, setMobileSegment] = useState<MobileSegment>("code");

  // Code & Execution states
  const [code, setCode] = useState<string>("");
  const [isRunning, setIsRunning] = useState(false);
  const [runResult, setRunResult] = useState<CodeRunResult | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  // Submission states
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionResult, setSubmissionResult] = useState<SubmissionResponseData | null>(null);
  const [submissionError, setSubmissionError] = useState<string | null>(null);

  // Solution Review state
  const [reviewData, setReviewData] = useState<SolutionReviewData | null>(null);
  const [isReviewLoading, setIsReviewLoading] = useState(false);
  const [isAiReviewLoading, setIsAiReviewLoading] = useState(false);
  const [reviewError, setReviewError] = useState<string | null>(null);

  // Load challenge metadata on mount or when challengeId changes
  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      setLoading(true);
      const res = await getChallenge(challengeId);
      if (isMounted) {
        if (res.data) {
          setChallenge(res.data);
          setCode(res.data.starter_code);
          setLoadError(null);
        } else {
          setLoadError(res.error || "Failed to load challenge metadata");
        }
        setLoading(false);
      }
    }
    loadData();
    return () => {
      isMounted = false;
    };
  }, [challengeId]);

  const handleResetClick = () => {
    if (!challenge) return;
    if (code.trim() !== challenge.starter_code.trim()) {
      setShowResetModal(true);
    } else {
      handleResetCode();
    }
  };

  const handleResetCode = () => {
    if (challenge) {
      setCode(challenge.starter_code);
      setRunResult(null);
      setRunError(null);
      setSubmissionResult(null);
      setSubmissionError(null);
      setReviewData(null);
      setReviewError(null);
      setActiveConsoleTab("tests");
    }
  };

  const handleRunTests = async () => {
    if (!code.trim() || isRunning || isSubmitting) return;

    if (!user) {
      setShowAuthModal(true);
      return;
    }

    setIsRunning(true);
    setRunError(null);
    setActiveConsoleTab("tests");
    setMobileSegment("console");

    const response = await runChallengeCode(challengeId, code);

    if (response.data) {
      setRunResult(response.data);
    } else {
      if (
        response.error?.toLowerCase().includes("authentication") ||
        response.error?.toLowerCase().includes("not authenticated") ||
        response.error?.toLowerCase().includes("log in")
      ) {
        setShowAuthModal(true);
      }
      setRunError(response.error || "Failed to communicate with test runner");
    }

    setIsRunning(false);
  };

  const handleSubmitSolution = async () => {
    if (!code.trim() || isRunning || isSubmitting) return;

    if (!user) {
      setShowAuthModal(true);
      return;
    }

    setIsSubmitting(true);
    setSubmissionError(null);
    setReviewData(null);
    setReviewError(null);
    setActiveConsoleTab("submission");
    setMobileSegment("console");

    const response = await submitChallengeCode(challengeId, code);

    if (response.data) {
      setSubmissionResult(response.data);
    } else {
      if (
        response.error?.toLowerCase().includes("authentication") ||
        response.error?.toLowerCase().includes("not authenticated") ||
        response.error?.toLowerCase().includes("log in")
      ) {
        setShowAuthModal(true);
      }
      setSubmissionError(response.error || "Failed to submit solution for scoring");
    }

    setIsSubmitting(false);
  };

  const handleOpenReviewTab = async (submissionId?: string) => {
    const targetId = submissionId || submissionResult?.submission_id;
    setActiveConsoleTab("review");
    setMobileSegment("console");

    if (targetId && (!reviewData || reviewData.submission_id !== targetId)) {
      setIsReviewLoading(true);
      setReviewError(null);

      const response = await getSubmissionReview(challengeId, targetId, false);

      if (response.data) {
        setReviewData(response.data);
      } else {
        setReviewError(response.error || "Failed to retrieve solution review.");
      }

      setIsReviewLoading(false);
    }
  };

  const handleRequestAiReview = async (provider?: string) => {
    if (!submissionResult?.submission_id || isAiReviewLoading) return;

    setIsAiReviewLoading(true);
    const response = await getSubmissionReview(
      challengeId,
      submissionResult.submission_id,
      true,
      provider
    );

    if (response.data) {
      setReviewData(response.data);
    } else if (response.error && reviewData) {
      setReviewData({
        ...reviewData,
        ai_review: {
          available: false,
          content: null,
          model: null,
          error_message: response.error,
        },
      });
    }

    setIsAiReviewLoading(false);
  };

  // Global Keyboard Shortcuts (Cmd/Ctrl + Enter to Run, Cmd/Ctrl + Shift + Enter to Submit)
  const handleRunTestsRef = useRef(handleRunTests);
  const handleSubmitSolutionRef = useRef(handleSubmitSolution);

  useEffect(() => {
    handleRunTestsRef.current = handleRunTests;
    handleSubmitSolutionRef.current = handleSubmitSolution;
  });

  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        const active = document.activeElement;
        const tagName = active?.tagName.toLowerCase();
        if (tagName === "input" || tagName === "select") {
          return;
        }
        if (
          tagName === "textarea" &&
          active?.getAttribute("aria-label") !== "Python Solution Code Editor"
        ) {
          return;
        }
        e.preventDefault();
        if (e.shiftKey) {
          handleSubmitSolutionRef.current();
        } else {
          handleRunTestsRef.current();
        }
      }
    };

    window.addEventListener("keydown", handleGlobalKeyDown);
    return () => window.removeEventListener("keydown", handleGlobalKeyDown);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#090d16] text-slate-100 flex items-center justify-center p-4">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm font-mono text-slate-400">Loading challenge workspace...</p>
        </div>
      </div>
    );
  }

  if (loadError || !challenge) {
    return (
      <div className="min-h-screen bg-[#090d16] text-slate-100 flex items-center justify-center p-4">
        <div className="max-w-md w-full rounded-xl border border-rose-900/60 bg-rose-950/20 p-6 text-center space-y-4">
          <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
          <h2 className="text-lg font-semibold text-rose-100">Unable to Load Challenge</h2>
          <p className="text-xs text-rose-300 font-mono leading-relaxed">
            {loadError || "FastAPI backend appears unreachable. Verify backend is running on port 8000."}
          </p>
          <div className="pt-2 flex items-center justify-center gap-3">
            <Link
              href="/challenges"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Browse Catalog</span>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const isDockerActive = challenge.sandbox_status.docker_available;
  const isBusy = isRunning || isSubmitting;

  const difficultyColors =
    challenge.difficulty === "Easy"
      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
      : challenge.difficulty === "Medium"
      ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
      : "bg-rose-500/10 border-rose-500/30 text-rose-400";

  return (
    <div className="min-h-screen flex flex-col bg-[#090d16] text-slate-100">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 border-b border-slate-800 bg-[#090d16]/95 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/challenges"
              className="flex items-center gap-2 text-xs font-mono text-slate-400 hover:text-slate-100 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Challenges Catalog</span>
            </Link>
            <div className="h-4 w-px bg-slate-800 hidden sm:block" />
            <div className="flex items-center gap-2">
              <span className="font-semibold text-sm text-slate-200">
                {challenge.title}
              </span>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${difficultyColors}`}>
                {challenge.difficulty}
              </span>
            </div>
          </div>

          {/* Right Header Controls: Progress Link & Sandbox Indicator */}
          <div className="flex items-center gap-2.5">
            {user ? (
              <Link
                href="/progress"
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono border border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
                title="View student progress analytics and submission history"
              >
                <Award className="w-3.5 h-3.5 text-emerald-400" />
                <span className="hidden sm:inline">Progress & History</span>
              </Link>
            ) : (
              <Link
                href={`/login?next=/challenges/${challengeId}`}
                className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold transition-colors"
              >
                <LogIn className="w-3 h-3" />
                <span>Sign In to Practice</span>
              </Link>
            )}

            <div
              title={challenge.sandbox_status.message}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono border bg-slate-900 border-slate-800"
            >
              {isDockerActive ? (
                <>
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-emerald-400 hidden sm:inline">Sandbox Active</span>
                </>
              ) : (
                <>
                  <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                  <span className="text-amber-400 hidden sm:inline">Docker Required</span>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {/* Mobile / Tablet Segment Switcher (< 1024px) */}
        <div className="lg:hidden flex items-center p-1 rounded-xl bg-slate-900 border border-slate-800 mb-4 font-mono text-xs">
          <button
            type="button"
            onClick={() => setMobileSegment("problem")}
            className={`cursor-pointer flex-1 py-2 text-center rounded-lg transition-colors ${
              mobileSegment === "problem"
                ? "bg-slate-800 text-slate-100 font-semibold shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Problem
          </button>
          <button
            type="button"
            onClick={() => setMobileSegment("code")}
            className={`cursor-pointer flex-1 py-2 text-center rounded-lg transition-colors ${
              mobileSegment === "code"
                ? "bg-slate-800 text-slate-100 font-semibold shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {user ? "Code Editor" : "Practice Gate"}
          </button>
          {user && (
            <button
              type="button"
              onClick={() => setMobileSegment("console")}
              className={`cursor-pointer flex-1 py-2 text-center rounded-lg transition-colors flex items-center justify-center gap-1.5 ${
                mobileSegment === "console"
                  ? "bg-slate-800 text-slate-100 font-semibold shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <span>Results & AI</span>
              {runResult && (
                <span
                  className={`w-2 h-2 rounded-full ${
                    runResult.status === "passed" ? "bg-emerald-400" : "bg-rose-400"
                  }`}
                />
              )}
            </button>
          )}
        </div>

        {/* 2-Column Responsive Workspace */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Problem Statement & Requirements */}
          <div
            className={`lg:col-span-5 space-y-6 ${
              mobileSegment === "problem" ? "block" : "hidden lg:block"
            }`}
          >
            <div className="rounded-xl border border-slate-800 bg-[#0b0f19] p-5 sm:p-6 space-y-5 shadow-lg">
              <div>
                <div className="flex flex-wrap items-center gap-2 text-xs font-mono text-slate-400 mb-2">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{challenge.estimated_minutes} min</span>
                  </span>
                  <span>•</span>
                  <span>Python 3.12</span>
                  {challenge.category && (
                    <>
                      <span>•</span>
                      <span className="text-emerald-400 font-medium">{challenge.category}</span>
                    </>
                  )}
                </div>
                <h1 className="text-xl font-bold text-slate-100">
                  {challenge.title}
                </h1>
                {challenge.tags && challenge.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2.5">
                    {challenge.tags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono bg-slate-900 border border-slate-800 text-slate-400"
                      >
                        <Tag className="w-2.5 h-2.5 text-slate-500" />
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Problem Statement Content */}
              <div className="border-t border-slate-800 pt-4">
                <MarkdownRenderer content={challenge.description} />
              </div>

              {/* Public Test Case Checklist */}
              <div className="border-t border-slate-800 pt-4 space-y-2.5">
                <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono">
                  Deterministic Test Suite ({challenge.test_cases.length} Cases)
                </h3>
                <div className="space-y-2">
                  {challenge.test_cases.map((tc) => (
                    <div
                      key={tc.id}
                      className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80 text-xs"
                    >
                      <span className="font-semibold text-slate-200 block font-mono text-[11px]">
                        {tc.name}
                      </span>
                      <span className="text-slate-400 text-[11px] leading-relaxed">
                        {tc.description}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Code Editor & Workbench OR Authentication Gate */}
          <div
            className={`lg:col-span-7 space-y-4 ${
              mobileSegment !== "problem" ? "block" : "hidden lg:block"
            }`}
          >
            {!user ? (
              /* Public / Unauthenticated Visitor Experience: Authentication Gate */
              <div className="space-y-5">
                <div className="rounded-2xl border border-slate-800 bg-[#0b0f19] p-6 sm:p-8 shadow-2xl space-y-6">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                      <Lock className="w-6 h-6" />
                    </div>
                    <div>
                      <h2 className="text-lg font-bold text-slate-100">
                        Ready to practice this challenge?
                      </h2>
                      <p className="text-xs text-slate-400 font-mono mt-0.5">
                        Interactive practice requires an authenticated student account.
                      </p>
                    </div>
                  </div>

                  <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                    Sign in to access our browser-based Python workspace, test your code against
                    isolated Docker containers, query AI interview coaches powered by Gemini, Claude,
                    and OpenAI, and earn verified correctness scores.
                  </p>

                  {/* Feature Highlights */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                    <div className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-900/70 border border-slate-800/80 text-xs">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      <div>
                        <strong className="text-slate-200 block font-medium">Docker Sandbox Execution</strong>
                        <span className="text-slate-400 text-[11px]">Run code safely against hidden test harnesses.</span>
                      </div>
                    </div>
                    <div className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-900/70 border border-slate-800/80 text-xs">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      <div>
                        <strong className="text-slate-200 block font-medium">Multi-Provider AI Coach</strong>
                        <span className="text-slate-400 text-[11px]">Context-aware progressive hints & explanations.</span>
                      </div>
                    </div>
                    <div className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-900/70 border border-slate-800/80 text-xs">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      <div>
                        <strong className="text-slate-200 block font-medium">Deterministic Scoring</strong>
                        <span className="text-slate-400 text-[11px]">Objective test-based rubric saved to profile.</span>
                      </div>
                    </div>
                    <div className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-900/70 border border-slate-800/80 text-xs">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      <div>
                        <strong className="text-slate-200 block font-medium">Architectural Reviews</strong>
                        <span className="text-slate-400 text-[11px]">Post-submission diff against reference solutions.</span>
                      </div>
                    </div>
                  </div>

                  {/* Primary Call to Action */}
                  <div className="pt-3 flex flex-col sm:flex-row items-center gap-3">
                    <Link
                      href={`/login?next=/challenges/${challengeId}`}
                      className="w-full sm:w-auto flex-1 inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm shadow-[0_0_20px_rgba(16,185,129,0.3)] transition-all"
                    >
                      <Play className="w-4 h-4 fill-current" />
                      <span>Start Practicing Now</span>
                    </Link>
                    <Link
                      href={`/signup?next=/challenges/${challengeId}`}
                      className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs font-mono transition-colors"
                    >
                      <span>Create Account</span>
                    </Link>
                  </div>
                </div>

                {/* Starter Code Preview (Read-Only) */}
                <div className="rounded-xl border border-slate-800 bg-[#070b12] overflow-hidden">
                  <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900/90 border-b border-slate-800 font-mono text-xs text-slate-400">
                    <div className="flex items-center gap-2">
                      <Code2 className="w-3.5 h-3.5 text-sky-400" />
                      <span>Starter Code Preview</span>
                    </div>
                    <span className="text-[10px] text-slate-500">Read-Only</span>
                  </div>
                  <pre className="p-4 text-xs font-mono text-slate-300 overflow-x-auto leading-relaxed">
                    <code>{challenge.starter_code}</code>
                  </pre>
                </div>
              </div>
            ) : (
              /* Authenticated Student Experience: Full Interactive Workspace */
              <>
                {/* Python Code Editor */}
                <div className={mobileSegment === "console" ? "hidden lg:block" : "block"}>
                  <CodeEditor
                    code={code}
                    onChange={setCode}
                    onReset={handleResetClick}
                    onRunTests={handleRunTests}
                    onSubmitSolution={handleSubmitSolution}
                    disabled={isBusy}
                  />
                </div>

                {/* Action Bar: Run Tests & Submit Solution */}
                <div className="flex flex-col gap-2.5 p-3.5 rounded-xl border border-slate-800 bg-[#0b0f19]">
                  <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
                    <div className="text-xs text-slate-400 font-mono flex items-center gap-2">
                      <span>Runner:</span>
                      <span className="text-slate-200 font-medium">
                        {isDockerActive ? "Isolated Docker Sandbox" : "Docker (Not Detected)"}
                      </span>
                    </div>

                    <div className="flex items-center gap-2.5 w-full sm:w-auto justify-end">
                      {/* Run Tests (Exploratory Attempt) */}
                      <button
                        type="button"
                        onClick={handleRunTests}
                        disabled={isBusy || !code.trim()}
                        className="cursor-pointer flex-1 sm:flex-none inline-flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs sm:text-sm transition-colors border border-slate-700/70 disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Run tests to check your progress (exploratory attempt, ⌘↵)"
                      >
                        <Play className={`w-3.5 h-3.5 ${isRunning ? "animate-spin text-sky-400" : "text-sky-400"}`} />
                        <span>{isRunning ? "Running..." : "Run Tests"}</span>
                        <span className="hidden md:inline text-[10px] text-slate-400 font-mono ml-0.5">⌘↵</span>
                      </button>

                      {/* Submit Solution (Formal Submission & Scoring) */}
                      <button
                        type="button"
                        onClick={handleSubmitSolution}
                        disabled={isBusy || !code.trim()}
                        className="cursor-pointer flex-1 sm:flex-none inline-flex items-center justify-center gap-1.5 px-5 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs sm:text-sm transition-all shadow-[0_0_15px_rgba(16,185,129,0.25)] hover:shadow-[0_0_20px_rgba(16,185,129,0.4)] disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Submit your code for formal grading and score recording (⇧⌘↵)"
                      >
                        <Send className={`w-3.5 h-3.5 ${isSubmitting ? "animate-spin" : ""}`} />
                        <span>{isSubmitting ? "Submitting..." : "Submit Solution"}</span>
                        <span className="hidden md:inline text-[10px] text-emerald-950/80 font-mono ml-0.5 font-bold">⇧⌘↵</span>
                      </button>
                    </div>
                  </div>

                  {/* Concise Helper Text clarifying Run Tests vs Submit Solution */}
                  <div className="pt-2 border-t border-slate-800/80 flex flex-col sm:flex-row items-start sm:items-center justify-between text-[11px] font-mono text-slate-400 gap-1.5 sm:gap-4">
                    <div className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-sky-400 shrink-0" />
                      <span><strong>Run Tests (⌘↵)</strong>: Exploratory check against test suite; no score impact.</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
                      <span><strong>Submit Solution (⇧⌘↵)</strong>: Deterministic rubric grading saved to profile.</span>
                    </div>
                  </div>
                </div>

                {/* Unified Workbench Console Pane */}
                <div
                  className={`rounded-xl border border-slate-800 bg-[#070b12] overflow-hidden shadow-xl ${
                    mobileSegment === "code" ? "hidden lg:block" : "block"
                  }`}
                >
                  {/* Tab Navigation Header */}
                  <div className="flex items-center justify-between px-2.5 py-1.5 bg-slate-900/90 border-b border-slate-800 overflow-x-auto">
                    <div className="flex items-center gap-1.5" role="tablist" aria-label="Workbench Console Tabs">
                      {/* Tab 1: Test Results */}
                      <button
                        type="button"
                        role="tab"
                        aria-selected={activeConsoleTab === "tests"}
                        onClick={() => setActiveConsoleTab("tests")}
                        className={`cursor-pointer flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono transition-colors ${
                          activeConsoleTab === "tests"
                            ? "bg-slate-800 text-slate-100 font-semibold border border-slate-700/60 shadow-sm"
                            : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
                        }`}
                      >
                        <Terminal className="w-3.5 h-3.5 text-sky-400" />
                        <span>Test Results</span>
                        {runResult && (
                          <span
                            className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-medium ${
                              runResult.status === "passed"
                                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                                : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                            }`}
                          >
                            {runResult.passed}/{runResult.total}
                          </span>
                        )}
                      </button>

                      {/* Tab 2: Submission Outcome */}
                      <button
                        type="button"
                        role="tab"
                        aria-selected={activeConsoleTab === "submission"}
                        onClick={() => setActiveConsoleTab("submission")}
                        className={`cursor-pointer flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono transition-colors ${
                          activeConsoleTab === "submission"
                            ? "bg-slate-800 text-slate-100 font-semibold border border-slate-700/60 shadow-sm"
                            : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
                        }`}
                      >
                        <Award className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Submission</span>
                        {submissionResult?.score !== undefined && submissionResult.score !== null && (
                          <span
                            className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-medium ${
                              submissionResult.score === 100
                                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                                : submissionResult.score > 0
                                ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                                : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                            }`}
                          >
                            {submissionResult.score}%
                          </span>
                        )}
                      </button>

                      {/* Tab 3: AI Interview Coach */}
                      <button
                        type="button"
                        role="tab"
                        aria-selected={activeConsoleTab === "ai"}
                        onClick={() => setActiveConsoleTab("ai")}
                        className={`cursor-pointer flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono transition-colors ${
                          activeConsoleTab === "ai"
                            ? "bg-slate-800 text-slate-100 font-semibold border border-slate-700/60 shadow-sm"
                            : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
                        }`}
                      >
                        <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                        <span>AI Coach</span>
                      </button>

                      {/* Tab 4: Solution Review */}
                      <button
                        type="button"
                        role="tab"
                        aria-selected={activeConsoleTab === "review"}
                        onClick={() => {
                          setActiveConsoleTab("review");
                          if (submissionResult?.submission_id && !reviewData && !isReviewLoading) {
                            handleOpenReviewTab(submissionResult.submission_id);
                          }
                        }}
                        className={`cursor-pointer flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono transition-colors ${
                          activeConsoleTab === "review"
                            ? "bg-slate-800 text-slate-100 font-semibold border border-slate-700/60 shadow-sm"
                            : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
                        }`}
                      >
                        <BookOpen className="w-3.5 h-3.5 text-sky-400" />
                        <span>Solution Review</span>
                        {!submissionResult?.submission_id && (
                          <Lock className="w-3 h-3 text-slate-500" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Tab Contents */}
                  <div className="p-4 sm:p-5">
                    {activeConsoleTab === "tests" && (
                      <TestResults
                        result={runResult}
                        isRunning={isRunning}
                        error={runError}
                        testCases={challenge.test_cases}
                      />
                    )}

                    {activeConsoleTab === "submission" && (
                      <div className="space-y-4">
                        {submissionError && (
                          <div className="rounded-xl border border-rose-900/60 bg-rose-950/20 p-4 text-xs text-rose-300 flex items-start gap-2.5">
                            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                            <div>
                              <div className="font-semibold text-rose-200 mb-0.5">Submission Error</div>
                              <p className="font-mono">{submissionError}</p>
                            </div>
                          </div>
                        )}

                        {submissionResult ? (
                          <SubmissionResultPanel
                            submission={submissionResult}
                            onDismiss={() => {
                              setSubmissionResult(null);
                              setReviewData(null);
                            }}
                            onReviewSolution={handleOpenReviewTab}
                            isReviewOpen={false}
                          />
                        ) : (
                          <div className="p-8 rounded-xl border border-slate-800/80 bg-slate-900/30 text-center space-y-4">
                            <div className="w-12 h-12 rounded-2xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-slate-400 mx-auto">
                              <Award className="w-6 h-6 text-emerald-400" />
                            </div>
                            <div className="max-w-md mx-auto space-y-1.5">
                              <h4 className="font-semibold text-sm text-slate-200">
                                No Formal Submission Yet
                              </h4>
                              <p className="text-xs text-slate-400 leading-relaxed font-mono">
                                Click &quot;Run Tests&quot; (⌘↵) to experiment without recording a score. When ready, click &quot;Submit Solution&quot; (⇧⌘↵) to record your score to your student profile and unlock the solution review.
                              </p>
                            </div>
                            <div className="pt-2">
                              <button
                                type="button"
                                onClick={handleSubmitSolution}
                                disabled={isBusy || !code.trim()}
                                className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs font-mono transition-colors disabled:opacity-50"
                              >
                                <Send className="w-3.5 h-3.5" />
                                <span>Submit Solution Now</span>
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {activeConsoleTab === "ai" && (
                      <AiAssistantPanel
                        challengeId={challengeId}
                        code={code}
                      />
                    )}

                    {activeConsoleTab === "review" && (
                      <div>
                        {!submissionResult?.submission_id ? (
                          <div className="p-8 rounded-xl border border-slate-800/80 bg-slate-900/30 text-center space-y-4">
                            <div className="w-12 h-12 rounded-2xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-slate-400 mx-auto">
                              <Lock className="w-6 h-6 text-slate-400" />
                            </div>
                            <div className="max-w-md mx-auto space-y-1.5">
                              <h4 className="font-semibold text-sm text-slate-200">
                                Solution Review is Locked
                              </h4>
                              <p className="text-xs text-slate-400 leading-relaxed font-mono">
                                To protect your learning experience and simulate real technical interviews, the authoritative reference implementation and code diff unlock after your first formal submission.
                              </p>
                            </div>
                            <div className="pt-2">
                              <button
                                type="button"
                                onClick={handleSubmitSolution}
                                disabled={isBusy || !code.trim()}
                                className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs font-mono transition-colors disabled:opacity-50"
                              >
                                <Send className="w-3.5 h-3.5" />
                                <span>Submit Solution to Unlock</span>
                              </button>
                            </div>
                          </div>
                        ) : isReviewLoading ? (
                          <div className="p-8 rounded-xl border border-slate-800 bg-[#070b12] text-center space-y-3">
                            <div className="w-8 h-8 border-2 border-sky-400 border-t-transparent rounded-full animate-spin mx-auto" />
                            <p className="text-xs font-mono text-slate-400">
                              Loading authoritative reference review and code diff...
                            </p>
                          </div>
                        ) : reviewError ? (
                          <div className="rounded-xl border border-rose-900/60 bg-rose-950/20 p-4 text-xs text-rose-300 flex items-start gap-2.5">
                            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                            <div className="space-y-1">
                              <div className="font-semibold text-rose-200">Unable to Load Solution Review</div>
                              <p className="font-mono">{reviewError}</p>
                              <button
                                type="button"
                                onClick={() => handleOpenReviewTab(submissionResult.submission_id!)}
                                className="cursor-pointer mt-2 inline-flex items-center gap-1.5 px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono transition-colors"
                              >
                                <RotateCcw className="w-3 h-3" />
                                <span>Retry Review</span>
                              </button>
                            </div>
                          </div>
                        ) : reviewData ? (
                          <SolutionReviewPanel
                            review={reviewData}
                            onRequestAiReview={handleRequestAiReview}
                            isAiLoading={isAiReviewLoading}
                            onClose={() => setActiveConsoleTab("submission")}
                          />
                        ) : (
                          <div className="p-8 rounded-xl border border-slate-800/80 bg-slate-900/30 text-center space-y-4">
                            <div className="w-12 h-12 rounded-2xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 mx-auto">
                              <BookOpen className="w-6 h-6 text-sky-400" />
                            </div>
                            <div className="max-w-md mx-auto space-y-1.5">
                              <h4 className="font-semibold text-sm text-slate-200">
                                Review Solution & Compare Implementation
                              </h4>
                              <p className="text-xs text-slate-400 leading-relaxed font-mono">
                                Inspect the production reference solution, architectural breakdown, and line-by-line diff against your submission.
                              </p>
                            </div>
                            <div className="pt-2">
                              <button
                                type="button"
                                onClick={() => handleOpenReviewTab(submissionResult.submission_id!)}
                                className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs font-mono transition-colors shadow-[0_0_12px_rgba(2,132,199,0.3)]"
                              >
                                <BookOpen className="w-3.5 h-3.5" />
                                <span>Load Reference Solution</span>
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </main>

      {/* Reset Code Confirmation Modal */}
      {showResetModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="relative w-full max-w-md rounded-2xl border border-slate-800 bg-[#0b0f19] p-6 shadow-2xl space-y-5">
            <div className="flex items-start justify-between">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                <RotateCcw className="w-5 h-5" />
              </div>
              <button
                type="button"
                onClick={() => setShowResetModal(false)}
                className="cursor-pointer text-slate-400 hover:text-slate-200 transition-colors p-1 rounded-lg hover:bg-slate-800"
                aria-label="Close modal"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2">
              <h3 className="text-lg font-bold text-slate-100">Reset to Starter Code?</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                This will revert your code back to the original starter template. All unsubmitted edits will be permanently lost.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-end gap-3 pt-2 font-mono text-xs">
              <button
                type="button"
                onClick={() => setShowResetModal(false)}
                className="cursor-pointer w-full sm:w-auto px-4 py-2.5 rounded-xl border border-slate-800 bg-slate-900/60 text-slate-400 hover:text-slate-200 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => {
                  handleResetCode();
                  setShowResetModal(false);
                }}
                className="cursor-pointer w-full sm:w-auto inline-flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Reset Code</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sign In Required Modal */}
      {showAuthModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="relative w-full max-w-md rounded-2xl border border-slate-800 bg-[#0b0f19] p-6 shadow-2xl space-y-5">
            <div className="flex items-start justify-between">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <LogIn className="w-5 h-5" />
              </div>
              <button
                type="button"
                onClick={() => setShowAuthModal(false)}
                className="cursor-pointer text-slate-400 hover:text-slate-200 transition-colors p-1 rounded-lg hover:bg-slate-800"
                aria-label="Close modal"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2">
              <h3 className="text-lg font-bold text-slate-100">Sign in to Practice</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Running tests, submitting solutions for grading, and accessing AI interview coaching require an active student session. Sign in or create an account to start practicing.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-end gap-3 pt-2 font-mono text-xs">
              <button
                type="button"
                onClick={() => setShowAuthModal(false)}
                className="cursor-pointer w-full sm:w-auto px-4 py-2.5 rounded-xl border border-slate-800 bg-slate-900/60 text-slate-400 hover:text-slate-200 transition-colors"
              >
                Cancel
              </button>
              <Link
                href={`/login?next=/challenges/${challengeId}`}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold transition-colors"
              >
                <span>Sign In / Sign Up</span>
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
