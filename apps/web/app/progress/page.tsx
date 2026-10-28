"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowUpRight,
  Award,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  Code,
  Copy,
  FileCode,
  Filter,
  Play,
  Shield,
  Sparkles,
  TrendingUp,
  X,
  XCircle,
} from "lucide-react";
import {
  getProgressSummary,
  getSubmissionHistory,
  getSubmissionReview,
} from "@/lib/api";
import {
  ProgressSummaryData,
  SolutionReviewData,
  SubmissionHistoryItem,
  SubmissionHistoryResponse,
} from "@/lib/types";
import { SolutionReviewPanel } from "@/components/SolutionReviewPanel";
import { useAuth } from "@/lib/auth-context";

export default function ProgressPage() {
  const { user, loading: authLoading } = useAuth();
  const [summary, setSummary] = useState<ProgressSummaryData | null>(null);
  const [history, setHistory] = useState<SubmissionHistoryResponse | null>(null);
  const [page, setPage] = useState<number>(1);
  const [challengeFilter, setChallengeFilter] = useState<string>("");
  const pageSize = 15;

  const [isNavigatingPage, setIsNavigatingPage] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadingSummary = Boolean(user && !summary && !errorMsg);
  const loadingHistory = Boolean(user && ((!history && !errorMsg) || isNavigatingPage));

  // Historical Solution Review modal
  const [activeReviewId, setActiveReviewId] = useState<{
    challengeId: string;
    submissionId: string;
  } | null>(null);
  const [reviewData, setReviewData] = useState<SolutionReviewData | null>(null);
  const [loadingReview, setLoadingReview] = useState(false);
  const [loadingAiReview, setLoadingAiReview] = useState(false);
  const [reviewError, setReviewError] = useState<string | null>(null);

  // Historical Code Snapshot modal
  const [activeCodeSnapshot, setActiveCodeSnapshot] = useState<SubmissionHistoryItem | null>(null);
  const [copiedSnapshotCode, setCopiedSnapshotCode] = useState(false);

  useEffect(() => {
    let isMounted = true;
    if (authLoading || !user) return;

    async function loadData() {
      const summaryRes = await getProgressSummary();
      const historyRes = await getSubmissionHistory(page, pageSize, challengeFilter || undefined);
      if (isMounted) {
        if (summaryRes.data) {
          setSummary(summaryRes.data);
        } else if (summaryRes.error) {
          setErrorMsg(summaryRes.error);
        }
        if (historyRes.data) {
          setHistory(historyRes.data);
        } else if (historyRes.error) {
          setErrorMsg(historyRes.error);
        }
        setIsNavigatingPage(false);
      }
    }
    loadData();
    return () => {
      isMounted = false;
    };
  }, [page, challengeFilter, user, authLoading]);

  const handlePageChange = (newPage: number) => {
    setIsNavigatingPage(true);
    setPage(newPage);
  };

  const handleFilterChange = (newFilter: string) => {
    setChallengeFilter(newFilter);
    setPage(1);
    setIsNavigatingPage(true);
  };

  const handleRetry = () => {
    setErrorMsg(null);
    setSummary(null);
    setHistory(null);
    setPage(1);
  };

  const handleOpenReview = async (challengeId: string, submissionId: string) => {
    setActiveReviewId({ challengeId, submissionId });
    setLoadingReview(true);
    setReviewError(null);
    setReviewData(null);

    const res = await getSubmissionReview(challengeId, submissionId, false);
    if (res.data) {
      setReviewData(res.data);
    } else {
      setReviewError(res.error || "Failed to load solution review");
    }
    setLoadingReview(false);
  };

  const handleRequestAiReview = async (provider?: string) => {
    if (!activeReviewId || loadingAiReview) return;
    setLoadingAiReview(true);
    const res = await getSubmissionReview(
      activeReviewId.challengeId,
      activeReviewId.submissionId,
      true,
      provider
    );
    if (res.data) {
      setReviewData(res.data);
    } else if (res.error && reviewData) {
      setReviewData({
        ...reviewData,
        ai_review: {
          available: false,
          content: null,
          model: null,
          provider: provider || null,
          error_message: res.error,
        },
      });
    }
    setLoadingAiReview(false);
  };

  const handleCopySnapshot = async (codeText: string) => {
    try {
      await navigator.clipboard.writeText(codeText);
      setCopiedSnapshotCode(true);
      setTimeout(() => setCopiedSnapshotCode(false), 2000);
    } catch {
      // Ignore clipboard write failures gracefully
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#090d16] text-slate-100 font-sans">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-slate-800 bg-[#090d16]/95 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="flex items-center gap-2 text-xs font-mono text-slate-400 hover:text-slate-100 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Gym</span>
            </Link>
            <div className="h-4 w-px bg-slate-800 hidden sm:block" />
            <div className="flex items-center gap-2">
              <Award className="w-4 h-4 text-emerald-400" />
              <h1 className="font-semibold text-sm sm:text-base text-slate-100">
                Student Progress & Submission History
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/challenges/request-deduplication"
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition-colors font-mono"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Practice Challenge</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-8">
        {authLoading ? (
          <div className="py-24 text-center space-y-3">
            <div className="w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-xs font-mono text-slate-400">Loading student session...</p>
          </div>
        ) : !user ? (
          <div className="py-16 px-4 text-center space-y-4 max-w-md mx-auto rounded-2xl border border-slate-800 bg-[#0b0f19] p-8 shadow-2xl">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mx-auto">
              <Award className="w-6 h-6" />
            </div>
            <h2 className="text-xl font-bold text-slate-100">Sign in to View Your Dashboard</h2>
            <p className="text-xs text-slate-400 leading-relaxed">
              Student progress, deterministic correctness scores, and code snapshots are isolated to your authenticated account.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2 font-mono">
              <Link
                href="/login?next=/progress"
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-medium text-xs transition-colors"
              >
                Sign In
              </Link>
              <Link
                href="/signup"
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl border border-slate-700 bg-slate-900 text-slate-200 hover:bg-slate-800 text-xs transition-colors"
              >
                Create Account
              </Link>
            </div>
          </div>
        ) : (
          <>
            {/* Authenticated Student Banner */}
            <div className="rounded-xl border border-slate-800 bg-[#0c1220] p-4 text-xs text-slate-400 flex items-start justify-between gap-3 shadow-sm">
              <div className="flex items-start gap-3">
                <Shield className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <div className="font-semibold text-slate-200 flex items-center gap-2">
                    <span>Authenticated Student Dashboard</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                      Data Isolated
                    </span>
                  </div>
                  <p className="leading-relaxed">
                    Analytics reflect only formal evaluations belonging to <strong className="text-slate-200">{user.email}</strong>.
                    Your submissions, code snapshots, and review metrics are private and protected.
                  </p>
                </div>
              </div>
              <Link
                href="/account"
                className="hidden sm:inline-flex text-[11px] font-mono text-slate-400 hover:text-slate-200 border border-slate-800 bg-slate-900/60 px-2.5 py-1 rounded transition-colors"
              >
                Settings
              </Link>
            </div>

            {/* Empty State Card for New Users with 0 Submissions */}
            {summary && summary.total_submissions === 0 && (
              <div className="rounded-xl border border-dashed border-emerald-500/30 bg-emerald-500/5 p-6 sm:p-8 text-center space-y-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mx-auto">
                  <Sparkles className="w-5 h-5" />
                </div>
                <h3 className="text-base font-semibold text-slate-100">
                  Welcome to your Student Dashboard, {user.full_name || user.email.split("@")[0]}!
                </h3>
                <p className="text-xs text-slate-400 max-w-lg mx-auto leading-relaxed">
                  You haven&apos;t submitted any formal challenge solutions yet. Complete your first challenge to view your deterministic scores, test breakdowns, and historical progression timeline.
                </p>
                <div className="pt-2">
                  <Link
                    href="/challenges"
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-mono text-xs font-semibold shadow-lg transition-colors"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Browse Challenges Catalog</span>
                  </Link>
                </div>
              </div>
            )}

            {/* Error Banner */}
            {errorMsg && (
              <div className="rounded-xl border border-rose-900/60 bg-rose-950/20 p-4 text-xs text-rose-300 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <XCircle className="w-4 h-4 text-rose-400" />
                  <span>{errorMsg}</span>
                </div>
                <button
                  type="button"
                  onClick={handleRetry}
                  className="cursor-pointer px-2.5 py-1 rounded bg-rose-900/40 text-rose-200 text-xs font-mono hover:bg-rose-800/40"
                >
                  Retry
                </button>
              </div>
            )}

            {/* Section 1: Scannable Analytics KPI Cards */}
            <section aria-labelledby="analytics-heading" className="space-y-3">
              <h2
                id="analytics-heading"
                className="text-xs font-mono uppercase tracking-wider text-slate-400 flex items-center gap-2"
              >
                <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                <span>Progress Summary Overview</span>
              </h2>

              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                {/* Problems Solved / Attempted */}
                <div className="p-4 rounded-xl border border-slate-800 bg-[#0b0f19] flex flex-col justify-between">
                  <span className="text-[11px] font-mono text-slate-400">Problems Solved</span>
                  <div className="text-2xl sm:text-3xl font-extrabold text-slate-100 mt-2">
                    {loadingSummary ? "—" : `${summary?.problems_solved ?? 0} / ${summary?.distinct_challenges_attempted ?? 0}`}
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono mt-1" title="Challenges where score == 100">
                    {summary?.challenge_solve_rate !== null && summary?.challenge_solve_rate !== undefined
                      ? `${summary.challenge_solve_rate}% completion`
                      : "0% completion"}
                  </span>
                </div>

                {/* Submission Success Rate */}
                <div className="p-4 rounded-xl border border-slate-800 bg-[#0b0f19] flex flex-col justify-between">
                  <span className="text-[11px] font-mono text-slate-400">Success Rate</span>
                  <div className="text-2xl sm:text-3xl font-extrabold text-emerald-400 mt-2">
                    {loadingSummary
                      ? "—"
                      : summary?.submission_success_rate !== null && summary?.submission_success_rate !== undefined
                      ? `${summary.submission_success_rate}%`
                      : "—"}
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono mt-1" title="100% scores / scorable formal submissions">
                    {summary?.scorable_submissions ?? 0} scorable runs
                  </span>
                </div>

                {/* Average Score */}
                <div className="p-4 rounded-xl border border-slate-800 bg-[#0b0f19] flex flex-col justify-between">
                  <span className="text-[11px] font-mono text-slate-400">Average Score</span>
                  <div className="text-2xl sm:text-3xl font-extrabold text-sky-400 mt-2">
                    {loadingSummary
                      ? "—"
                      : summary?.average_score !== null && summary?.average_score !== undefined
                      ? `${summary.average_score}%`
                      : "—"}
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono mt-1">Mean of scorable runs</span>
                </div>

                {/* Best Score */}
                <div className="p-4 rounded-xl border border-slate-800 bg-[#0b0f19] flex flex-col justify-between">
                  <span className="text-[11px] font-mono text-slate-400">Best Score</span>
                  <div className="text-2xl sm:text-3xl font-extrabold text-emerald-400 mt-2">
                    {loadingSummary
                      ? "—"
                      : summary?.best_score !== null && summary?.best_score !== undefined
                      ? `${summary.best_score}%`
                      : "—"}
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono mt-1">Highest scored attempt</span>
                </div>

                {/* Most Recent Score */}
                <div className="p-4 rounded-xl border border-slate-800 bg-[#0b0f19] flex flex-col justify-between">
                  <span className="text-[11px] font-mono text-slate-400">Recent Score</span>
                  <div
                    className={`text-2xl sm:text-3xl font-extrabold mt-2 ${
                      summary?.most_recent_score === 100
                        ? "text-emerald-400"
                        : summary?.most_recent_score !== null &&
                          summary?.most_recent_score !== undefined &&
                          summary.most_recent_score > 0
                        ? "text-amber-400"
                        : "text-slate-200"
                    }`}
                  >
                    {loadingSummary
                      ? "—"
                      : summary?.most_recent_score !== null && summary?.most_recent_score !== undefined
                      ? `${summary.most_recent_score}%`
                      : "—"}
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono mt-1">Latest evaluation</span>
                </div>

                {/* Total Formal Submissions */}
                <div className="p-4 rounded-xl border border-slate-800 bg-[#0b0f19] flex flex-col justify-between">
                  <span className="text-[11px] font-mono text-slate-400">Submissions</span>
                  <div className="text-2xl sm:text-3xl font-extrabold text-slate-100 mt-2">
                    {loadingSummary ? "—" : summary?.total_submissions ?? 0}
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono mt-1">
                    {summary?.total_passed_tests ?? 0} passed / {summary?.total_failed_tests ?? 0} failed
                  </span>
                </div>
              </div>
            </section>

            {/* Section 1b: Recent Coding Activity Feed */}
            {summary?.recent_activity && summary.recent_activity.length > 0 && (
              <section aria-labelledby="activity-heading" className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3
                    id="activity-heading"
                    className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2"
                  >
                    <Clock className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Recent Activity (Last {summary.recent_activity.length} Formal Submissions)</span>
                  </h3>
                  <span className="text-[10px] font-mono text-slate-500">
                    Chronological audit log
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
                  {summary.recent_activity.map((act) => (
                    <div
                      key={act.id}
                      className="p-3.5 rounded-xl border border-slate-800 bg-[#0b0f19] flex flex-col justify-between space-y-2 hover:border-slate-700 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <Link
                          href={`/challenges/${act.challenge_id}`}
                          className="font-semibold text-xs text-slate-200 hover:text-emerald-400 transition-colors line-clamp-1"
                          title={act.challenge_title}
                        >
                          {act.challenge_title}
                        </Link>
                        <span
                          className={`text-[10px] font-mono px-1.5 py-0.5 rounded uppercase font-bold shrink-0 ${
                            act.status === "passed"
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                              : act.status === "failed"
                              ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                              : "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                          }`}
                        >
                          {act.status}
                        </span>
                      </div>

                      <div className="flex items-baseline justify-between pt-1">
                        <span className="text-xl font-bold font-mono text-slate-100">
                          {act.score !== null ? `${act.score}%` : "N/A"}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400">
                          {act.passed_count}/{act.total_count} tests
                        </span>
                      </div>

                      <div className="text-[10px] text-slate-500 font-mono border-t border-slate-800/80 pt-1.5 flex items-center justify-between">
                        <span>
                          {new Date(act.created_at).toLocaleDateString([], {
                            month: "short",
                            day: "numeric",
                          })}
                        </span>
                        <span className="truncate max-w-[80px]" title={act.id}>
                          {act.id}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Section 2: Per-Challenge Breakdown & Progress Timeline */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              {/* Per-Challenge Breakdown (5 Cols) */}
              <section
                aria-labelledby="per-challenge-heading"
                className="lg:col-span-5 rounded-xl border border-slate-800 bg-[#0b0f19] p-5 space-y-4"
              >
                <h3
                  id="per-challenge-heading"
                  className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-300 flex items-center justify-between"
                >
                  <span>Per-Challenge Breakdown</span>
                  <span className="text-slate-500 font-normal">
                    {summary?.per_challenge.length ?? 0} tracked
                  </span>
                </h3>

                {loadingSummary ? (
                  <div className="py-6 text-center text-xs font-mono text-slate-500">
                    Loading challenge breakdown...
                  </div>
                ) : summary?.per_challenge.length === 0 ? (
                  <div className="py-6 text-center text-xs font-mono text-slate-500">
                    No formal challenges attempted yet.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {summary?.per_challenge.map((c) => (
                      <div
                        key={c.challenge_id}
                        className="p-3.5 rounded-lg border border-slate-800/80 bg-slate-900/50 space-y-2.5"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-slate-200 text-xs">
                              {c.challenge_title}
                            </span>
                            {c.is_solved ? (
                              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                                <CheckCircle2 className="w-3 h-3" />
                                <span>Solved</span>
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono text-amber-400 bg-amber-500/10 border border-amber-500/30">
                                In Progress
                              </span>
                            )}
                          </div>
                          <Link
                            href={`/challenges/${c.challenge_id}`}
                            className="text-[11px] font-mono text-emerald-400 hover:text-emerald-300 inline-flex items-center gap-0.5"
                          >
                            <span>Practice</span>
                            <ArrowUpRight className="w-3 h-3" />
                          </Link>
                        </div>

                        <div className="grid grid-cols-3 gap-2 font-mono text-xs pt-1 border-t border-slate-800/80">
                          <div>
                            <div className="text-[10px] text-slate-500 uppercase">Attempts</div>
                            <div className="text-slate-200 font-semibold">{c.total_attempts}</div>
                          </div>
                          <div>
                            <div className="text-[10px] text-slate-500 uppercase">Best Score</div>
                            <div className="text-emerald-400 font-semibold">
                              {c.best_score !== null ? `${c.best_score}%` : "N/A"}
                            </div>
                          </div>
                          <div>
                            <div className="text-[10px] text-slate-500 uppercase">Latest Score</div>
                            <div className="text-slate-200 font-semibold">
                              {c.latest_score !== null ? `${c.latest_score}%` : "N/A"}
                            </div>
                          </div>
                        </div>

                        {/* Score Improvement Delta (Percentage Points) */}
                        {c.score_improvement_delta !== null && c.score_improvement_delta !== undefined && (
                          <div className="pt-2 border-t border-slate-800/80 text-[11px] font-mono flex items-center justify-between text-slate-400">
                            <span>Score change (first to latest attempt):</span>
                            <span
                              className={`font-semibold ${
                                c.score_improvement_delta > 0
                                  ? "text-emerald-400"
                                  : c.score_improvement_delta < 0
                                  ? "text-rose-400"
                                  : "text-slate-300"
                              }`}
                            >
                              {c.score_improvement_delta > 0
                                ? `+${c.score_improvement_delta}`
                                : c.score_improvement_delta}{" "}
                              percentage points
                            </span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </section>

              {/* Progress Timeline Chart (7 Cols) */}
              <section
                aria-labelledby="timeline-heading"
                className="lg:col-span-7 rounded-xl border border-slate-800 bg-[#0b0f19] p-5 space-y-4"
              >
                <div className="flex items-center justify-between">
                  <h3
                    id="timeline-heading"
                    className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-300"
                  >
                    Progress Over Time (Chronological Scores)
                  </h3>
                  <span className="text-[10px] font-mono text-slate-500">
                    {summary?.score_history.length ?? 0} data points
                  </span>
                </div>

                {loadingSummary ? (
                  <div className="h-44 flex items-center justify-center text-xs font-mono text-slate-500">
                    Loading timeline visualization...
                  </div>
                ) : !summary?.score_history || summary.score_history.length === 0 ? (
                  <div className="h-44 rounded-lg border border-dashed border-slate-800/80 flex flex-col items-center justify-center p-4 text-center space-y-1">
                    <p className="text-xs font-mono text-slate-400">
                      Not enough scorable attempts to chart progress.
                    </p>
                    <p className="text-[11px] text-slate-500">
                      Submit solutions with Docker enabled to view your score progression graph.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {/* Responsive SVG Score Chart */}
                    <div className="w-full h-44 rounded-lg bg-slate-950/60 border border-slate-800/80 p-3 flex flex-col justify-between">
                      <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
                        <span>100%</span>
                        <span>Deterministic Correctness Score</span>
                      </div>

                      <div className="relative flex-1 w-full flex items-end gap-1.5 pt-2 pb-1 overflow-x-auto">
                        {summary.score_history.map((pt) => {
                          const heightPercent = Math.max(8, pt.score);
                          const isPerfect = pt.score === 100;
                          const isPartial = pt.score > 0 && pt.score < 100;
                          return (
                            <div
                              key={pt.submission_id}
                              className="flex-1 min-w-[12px] max-w-[28px] flex flex-col items-center justify-end h-full group relative"
                            >
                              {/* Tooltip on Hover */}
                              <div className="absolute bottom-full mb-1.5 hidden group-hover:flex flex-col items-center z-20 pointer-events-none">
                                <div className="bg-slate-900 border border-slate-700 text-slate-100 text-[10px] font-mono px-2 py-1 rounded shadow-lg whitespace-nowrap">
                                  <div>Score: {pt.score}%</div>
                                  <div className="text-[9px] text-slate-400">
                                    {new Date(pt.created_at).toLocaleDateString([], {
                                      month: "short",
                                      day: "numeric",
                                    })}
                                  </div>
                                </div>
                              </div>

                              {/* Bar */}
                              <div
                                style={{ height: `${heightPercent}%` }}
                                className={`w-full rounded-t transition-all ${
                                  isPerfect
                                    ? "bg-emerald-500/80 group-hover:bg-emerald-400"
                                    : isPartial
                                    ? "bg-amber-500/80 group-hover:bg-amber-400"
                                    : "bg-rose-500/80 group-hover:bg-rose-400"
                                }`}
                              />
                            </div>
                          );
                        })}
                      </div>

                      <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 border-t border-slate-800/80 pt-1">
                        <span>Older attempts</span>
                        <span>Newest attempt</span>
                      </div>
                    </div>
                  </div>
                )}
              </section>
            </div>

            {/* Section 2b: Grounded Curriculum Concepts Evaluated */}
            <section
              aria-labelledby="curriculum-heading"
              className="rounded-xl border border-slate-800 bg-[#0b0f19] p-5 space-y-3"
            >
              <div className="flex items-center justify-between">
                <h3
                  id="curriculum-heading"
                  className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2"
                >
                  <BookOpen className="w-3.5 h-3.5 text-sky-400" />
                  <span>Curriculum Concepts Evaluated</span>
                </h3>
                <span className="text-[10px] font-mono text-slate-500">
                  Specification-grounded topics
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed font-mono">
                Technical patterns and failure boundaries evaluated by your attempted challenges. Metrics reflect verified deterministic test assertions rather than subjective estimates.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                <div className="p-3.5 rounded-lg border border-slate-800/80 bg-slate-900/40 space-y-1">
                  <div className="text-xs font-semibold text-slate-200">In-Memory State Tracking</div>
                  <p className="text-[11px] text-slate-400 font-mono leading-relaxed">
                    Set operations, O(1) membership testing, and reference mutability across request sequences.
                  </p>
                </div>
                <div className="p-3.5 rounded-lg border border-slate-800/80 bg-slate-900/40 space-y-1">
                  <div className="text-xs font-semibold text-slate-200">Idempotency & Race Handling</div>
                  <p className="text-[11px] text-slate-400 font-mono leading-relaxed">
                    First-occurrence acceptance, subsequent re-delivery rejection, and independent identifier isolation.
                  </p>
                </div>
                <div className="p-3.5 rounded-lg border border-slate-800/80 bg-slate-900/40 space-y-1">
                  <div className="text-xs font-semibold text-slate-200">Input Validation & Boundaries</div>
                  <p className="text-[11px] text-slate-400 font-mono leading-relaxed">
                    Defensive checking for empty strings, whitespace-only strings, and non-string types raising ValueError.
                  </p>
                </div>
              </div>
            </section>

            {/* Section 3: Formal Submission History Table */}
            <section aria-labelledby="history-heading" className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h2
                    id="history-heading"
                    className="text-base font-bold text-slate-100 flex items-center gap-2"
                  >
                    <span>Submission History</span>
                    <span className="text-xs font-normal text-slate-400 font-mono">
                      ({history?.total ?? 0} recorded attempts)
                    </span>
                  </h2>
                  <p className="text-xs text-slate-400">
                    Formal &quot;Submit Solution&quot; attempts are permanently recorded. Exploratory &quot;Run Tests&quot; are practice-only and not stored.
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  {/* Challenge Filter Dropdown */}
                  <div className="flex items-center gap-2">
                    <Filter className="w-3.5 h-3.5 text-slate-400" />
                    <label htmlFor="challenge-filter-select" className="sr-only">
                      Filter by Challenge
                    </label>
                    <select
                      id="challenge-filter-select"
                      value={challengeFilter}
                      onChange={(e) => handleFilterChange(e.target.value)}
                      className="cursor-pointer bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500"
                    >
                      <option value="">All Challenges</option>
                      {summary?.per_challenge.map((c) => (
                        <option key={c.challenge_id} value={c.challenge_id}>
                          {c.challenge_title}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Pagination Controls Top */}
                  {history && history.total_pages > 1 && (
                    <div className="flex items-center gap-2 font-mono text-xs">
                      <button
                        type="button"
                        onClick={() => handlePageChange(Math.max(1, page - 1))}
                        disabled={!history.has_prev || loadingHistory}
                        className="cursor-pointer inline-flex items-center gap-1 px-2.5 py-1 rounded border border-slate-800 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        <ChevronLeft className="w-3.5 h-3.5" />
                        <span>Prev</span>
                      </button>
                      <span className="text-slate-400">
                        Page {history.page} of {history.total_pages}
                      </span>
                      <button
                        type="button"
                        onClick={() => handlePageChange(Math.min(history.total_pages, page + 1))}
                        disabled={!history.has_next || loadingHistory}
                        className="cursor-pointer inline-flex items-center gap-1 px-2.5 py-1 rounded border border-slate-800 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        <span>Next</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Table Container */}
              <div className="rounded-xl border border-slate-800 bg-[#0b0f19] overflow-hidden shadow-lg">
                {loadingHistory ? (
                  <div className="py-16 text-center space-y-3">
                    <div className="w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin mx-auto" />
                    <p className="text-xs font-mono text-slate-400">
                      Loading formal submission history...
                    </p>
                  </div>
                ) : !history || history.items.length === 0 ? (
                  <div className="py-16 px-4 text-center space-y-3">
                    <FileCode className="w-10 h-10 text-slate-600 mx-auto" />
                    <h3 className="text-sm font-semibold text-slate-300">
                      No Formal Submissions Recorded Yet
                    </h3>
                    <p className="text-xs text-slate-500 max-w-md mx-auto">
                      Exploratory &quot;Run Tests&quot; are for practice. Click &quot;Submit Solution&quot;
                      in the challenge workspace to formally record your evaluation.
                    </p>
                    <div className="pt-2">
                      <Link
                        href="/challenges"
                        className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-medium text-xs transition-colors"
                      >
                        <Play className="w-3.5 h-3.5 fill-current" />
                        <span>Browse Challenges Catalog</span>
                      </Link>
                    </div>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="border-b border-slate-800 bg-slate-900/80 font-mono text-[11px] text-slate-400 uppercase tracking-wider">
                          <th className="py-3 px-4">Challenge</th>
                          <th className="py-3 px-4">Timestamp (Local Time)</th>
                          <th className="py-3 px-4">Score</th>
                          <th className="py-3 px-4">Tests Passed</th>
                          <th className="py-3 px-4">Status</th>
                          <th className="py-3 px-4 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/70 font-mono">
                        {history.items.map((item) => {
                          const isUnscorable = item.score === null || item.status === "runner_unavailable";
                          const isPerfect = item.score === 100;
                          const isPartial = item.score !== null && item.score > 0 && item.score < 100;

                          // Format timestamp in local user time
                          const localDate = new Date(item.created_at).toLocaleString([], {
                            year: "numeric",
                            month: "short",
                            day: "2-digit",
                            hour: "2-digit",
                            minute: "2-digit",
                            second: "2-digit",
                          });

                          return (
                            <tr
                              key={item.id}
                              className="hover:bg-slate-900/40 transition-colors"
                            >
                              {/* Challenge Name & ID - Link directly to Challenge */}
                              <td className="py-3.5 px-4">
                                <Link
                                  href={`/challenges/${item.challenge_id}`}
                                  className="font-semibold text-slate-200 hover:text-emerald-400 transition-colors inline-flex items-center gap-1 group"
                                  title={`Practice ${item.challenge_title}`}
                                >
                                  <span>{item.challenge_title}</span>
                                  <ArrowUpRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                                </Link>
                                <div className="text-[10px] text-slate-500 font-mono">
                                  ID: {item.id}
                                </div>
                              </td>

                              {/* Local Timestamp */}
                              <td className="py-3.5 px-4 text-slate-300">
                                <div>{localDate}</div>
                                <div className="text-[10px] text-slate-500">
                                  {item.execution_time_ms !== null
                                    ? `${item.execution_time_ms.toFixed(0)}ms runtime`
                                    : "No execution runtime"}
                                </div>
                              </td>

                              {/* Correctness Score */}
                              <td className="py-3.5 px-4">
                                {isUnscorable ? (
                                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] bg-slate-800/80 border border-slate-700/80 text-slate-400">
                                    Unscorable
                                  </span>
                                ) : (
                                  <span
                                    className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-bold border ${
                                      isPerfect
                                        ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                                        : isPartial
                                        ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
                                        : "bg-rose-500/10 border-rose-500/30 text-rose-400"
                                    }`}
                                  >
                                    {item.score}%
                                  </span>
                                )}
                              </td>

                              {/* Test Count */}
                              <td className="py-3.5 px-4">
                                <div className="flex items-center gap-2">
                                  <span className="text-emerald-400 font-semibold">
                                    {item.passed_count} passed
                                  </span>
                                  <span className="text-slate-500">/</span>
                                  <span className="text-slate-400">{item.total_count} total</span>
                                </div>
                              </td>

                              {/* Status */}
                              <td className="py-3.5 px-4">
                                <span
                                  className={`inline-block px-2 py-0.5 rounded text-[10px] uppercase font-bold border ${
                                    item.status === "passed"
                                      ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                                      : item.status === "failed"
                                      ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
                                      : item.status === "runner_unavailable"
                                      ? "bg-slate-800 border-slate-700 text-slate-400"
                                      : "bg-rose-500/10 border-rose-500/30 text-rose-400"
                                  }`}
                                >
                                  {item.status}
                                </span>
                              </td>

                              {/* Actions */}
                              <td className="py-3.5 px-4 text-right space-x-2">
                                {/* View Submitted Code Snapshot */}
                                <button
                                  type="button"
                                  onClick={() => setActiveCodeSnapshot(item)}
                                  className="cursor-pointer inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition-colors border border-slate-700/60"
                                  title="Inspect exact source code submitted for this attempt"
                                >
                                  <Code className="w-3 h-3 text-slate-400" />
                                  <span>Code</span>
                                </button>

                                {/* Open Solution Review (if eligible) */}
                                {item.is_review_available ? (
                                  <button
                                    type="button"
                                    onClick={() => handleOpenReview(item.challenge_id, item.id)}
                                    className="cursor-pointer inline-flex items-center gap-1 px-2.5 py-1 rounded bg-sky-600/90 hover:bg-sky-500 text-white text-xs font-medium transition-colors shadow-sm"
                                    title="Open reference solution review for this specific historical submission"
                                  >
                                    <BookOpen className="w-3 h-3" />
                                    <span>Review</span>
                                  </button>
                                ) : (
                                  <span
                                    className="inline-block px-2 py-1 text-[11px] text-slate-600 cursor-not-allowed"
                                    title="Review is only available for completed scorable submissions"
                                  >
                                    No Review
                                  </span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Bottom Pagination */}
                {history && history.total_pages > 1 && (
                  <div className="flex items-center justify-between p-4 border-t border-slate-800/80 bg-slate-900/40 text-xs font-mono">
                    <div className="text-slate-400">
                      Showing submissions {(history.page - 1) * history.page_size + 1} to{" "}
                      {Math.min(history.page * history.page_size, history.total)} of {history.total}
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => handlePageChange(Math.max(1, page - 1))}
                        disabled={!history.has_prev || loadingHistory}
                        className="cursor-pointer inline-flex items-center gap-1 px-3 py-1 rounded border border-slate-800 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        <ChevronLeft className="w-3.5 h-3.5" />
                        <span>Previous</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => handlePageChange(Math.min(history.total_pages, page + 1))}
                        disabled={!history.has_next || loadingHistory}
                        className="cursor-pointer inline-flex items-center gap-1 px-3 py-1 rounded border border-slate-800 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        <span>Next</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </section>
          </>
        )}
      </main>

      {/* Historical Solution Review Modal */}
      {activeReviewId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
          <div className="relative w-full max-w-4xl my-8">
            {loadingReview ? (
              <div className="p-12 rounded-xl border border-slate-800 bg-[#070b12] text-center space-y-3">
                <div className="w-8 h-8 border-2 border-sky-400 border-t-transparent rounded-full animate-spin mx-auto" />
                <p className="text-xs font-mono text-slate-400">
                  Loading authoritative solution review for {activeReviewId.submissionId}...
                </p>
              </div>
            ) : reviewError ? (
              <div className="p-6 rounded-xl border border-rose-900 bg-[#070b12] text-center space-y-3">
                <XCircle className="w-8 h-8 text-rose-400 mx-auto" />
                <p className="text-xs text-rose-300 font-mono">{reviewError}</p>
                <button
                  type="button"
                  onClick={() => setActiveReviewId(null)}
                  className="cursor-pointer px-4 py-2 rounded bg-slate-800 hover:bg-slate-700 text-xs font-mono text-slate-200"
                >
                  Close
                </button>
              </div>
            ) : reviewData ? (
              <SolutionReviewPanel
                review={reviewData}
                onRequestAiReview={handleRequestAiReview}
                isAiLoading={loadingAiReview}
                onClose={() => {
                  setActiveReviewId(null);
                  setReviewData(null);
                }}
              />
            ) : null}
          </div>
        </div>
      )}

      {/* Code Snapshot Modal with Read-Only Safety, Copy Action, and Workspace Navigation */}
      {activeCodeSnapshot && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="relative w-full max-w-3xl rounded-xl border border-slate-800 bg-[#070b12] overflow-hidden shadow-2xl flex flex-col max-h-[85vh]">
            <div className="flex items-center justify-between px-5 py-3.5 bg-slate-900 border-b border-slate-800">
              <div className="flex items-center gap-2 font-mono text-xs text-slate-200">
                <Code className="w-4 h-4 text-emerald-400" />
                <span className="font-semibold">Submitted Code Snapshot</span>
                <span className="text-slate-500">({activeCodeSnapshot.id})</span>
              </div>
              <button
                type="button"
                onClick={() => setActiveCodeSnapshot(null)}
                className="cursor-pointer text-slate-400 hover:text-slate-200 transition-colors p-1 rounded hover:bg-slate-800"
                aria-label="Close code snapshot modal"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Read-Only Safety Notice */}
            <div className="bg-slate-950 px-5 py-2.5 border-b border-slate-800/80 flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-2 text-slate-400">
                <Shield className="w-3.5 h-3.5 text-emerald-400" />
                <span>Archived Evaluation Snapshot — Read-Only</span>
              </div>
              <span className="text-[10px] text-slate-500 hidden sm:inline">
                Permanent historical record • Never overwritten
              </span>
            </div>

            <div className="p-4 flex-1 overflow-y-auto space-y-3">
              <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                <div>
                  Challenge: <strong className="text-slate-200">{activeCodeSnapshot.challenge_title}</strong> • Score:{" "}
                  {activeCodeSnapshot.score !== null ? `${activeCodeSnapshot.score}%` : "Unscorable"}
                </div>
                <button
                  type="button"
                  onClick={() => handleCopySnapshot(activeCodeSnapshot.code || "")}
                  className="cursor-pointer inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono transition-colors border border-slate-700/60"
                  title="Copy submitted source code to clipboard"
                >
                  {copiedSnapshotCode ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-emerald-400">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5 text-slate-400" />
                      <span>Copy Code</span>
                    </>
                  )}
                </button>
              </div>

              <pre className="p-4 rounded-lg bg-black border border-slate-800 text-xs font-mono text-emerald-300 overflow-x-auto leading-relaxed">
                <code>{activeCodeSnapshot.code || "# No code snapshot recorded"}</code>
              </pre>
            </div>

            <div className="px-5 py-3 bg-slate-900/80 border-t border-slate-800 flex items-center justify-between">
              <Link
                href={`/challenges/${activeCodeSnapshot.challenge_id}`}
                className="inline-flex items-center gap-1.5 text-xs font-mono text-emerald-400 hover:text-emerald-300 transition-colors"
              >
                <Play className="w-3 h-3 fill-current" />
                <span>Practice in Workspace</span>
              </Link>
              <button
                type="button"
                onClick={() => setActiveCodeSnapshot(null)}
                className="cursor-pointer px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-mono text-slate-200 transition-colors"
              >
                Close Snapshot
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
