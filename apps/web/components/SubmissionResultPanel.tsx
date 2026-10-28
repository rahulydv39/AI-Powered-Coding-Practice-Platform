"use client";

import React from "react";
import {
  Award,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  ShieldAlert,
  Hash,
  Info,
  BookOpen,
} from "lucide-react";
import { SubmissionResponseData } from "../lib/types";

interface SubmissionResultPanelProps {
  submission: SubmissionResponseData;
  onDismiss?: () => void;
  onReviewSolution?: (submissionId: string) => void;
  isReviewOpen?: boolean;
}

export function SubmissionResultPanel({
  submission,
  onDismiss,
  onReviewSolution,
  isReviewOpen = false,
}: SubmissionResultPanelProps) {
  const isRunnerUnavailable =
    submission.status === "runner_unavailable" || !submission.docker_available;

  const score = submission.score;
  const isPerfect = score === 100;
  const isPartial = score !== null && score > 0 && score < 100;
  const isZero = score === 0;

  // Determine accent styling based on score status
  let scoreColorClass = "text-slate-400 border-slate-700 bg-slate-800/40";
  let scoreBadgeBg = "bg-slate-800 text-slate-300";
  let scoreText = "N/A";

  if (!isRunnerUnavailable && score !== null) {
    scoreText = `${score}%`;
    if (isPerfect) {
      scoreColorClass = "text-emerald-400 border-emerald-500/40 bg-emerald-950/20";
      scoreBadgeBg = "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
    } else if (isPartial) {
      scoreColorClass = "text-amber-400 border-amber-500/40 bg-amber-950/20";
      scoreBadgeBg = "bg-amber-500/10 text-amber-400 border-amber-500/30";
    } else if (isZero) {
      scoreColorClass = "text-rose-400 border-rose-500/40 bg-rose-950/20";
      scoreBadgeBg = "bg-rose-500/10 text-rose-400 border-rose-500/30";
    }
  }

  return (
    <div
      aria-live="polite"
      className="flex flex-col rounded-xl border border-slate-800 bg-[#070b12] overflow-hidden shadow-xl"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-900/80 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Award className="w-4 h-4 text-emerald-400" />
          <h3 className="font-semibold text-sm text-slate-200">
            Formal Submission Evaluation
          </h3>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/60">
            {submission.rubric_version}
          </span>
        </div>

        {onDismiss && (
          <button
            type="button"
            onClick={onDismiss}
            className="text-xs text-slate-400 hover:text-slate-200 transition-colors"
          >
            Dismiss
          </button>
        )}
      </div>

      {/* Main Score & Metrics Display */}
      <div className="p-4 sm:p-5 flex flex-col gap-4">
        {/* Runner Unavailable State */}
        {isRunnerUnavailable ? (
          <div className="rounded-lg border border-amber-500/40 bg-amber-950/20 p-4 text-amber-300 text-xs flex gap-3 items-start">
            <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-amber-200 mb-1">
                Sandbox Unavailable — Submission Not Evaluated
              </p>
              <p className="text-amber-300/90 leading-relaxed">
                {submission.error_message ||
                  "Docker sandbox was not detected. For safety and isolation, your code was not evaluated. No grade or penalty was recorded."}
              </p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-center">
            {/* Score Card */}
            <div
              className={`flex flex-col items-center justify-center p-4 rounded-lg border ${scoreColorClass}`}
            >
              <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 mb-1">
                Correctness Score
              </span>
              <div className="flex items-baseline gap-1">
                <span className="text-3xl sm:text-4xl font-extrabold tracking-tight">
                  {scoreText}
                </span>
                {score !== null && (
                  <span className="text-xs text-slate-500 font-mono">/ 100</span>
                )}
              </div>
              <span
                className={`mt-2 text-[10px] font-mono px-2 py-0.5 rounded border uppercase ${scoreBadgeBg}`}
              >
                {submission.status}
              </span>
            </div>

            {/* Test Summary Metrics */}
            <div className="sm:col-span-2 flex flex-col justify-between p-4 rounded-lg border border-slate-800/80 bg-slate-900/40 gap-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Deterministic Tests</span>
                <div className="flex items-center gap-3 font-mono font-medium">
                  <span className="flex items-center gap-1 text-emerald-400">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    {submission.passed} passed
                  </span>
                  <span className="flex items-center gap-1 text-rose-400">
                    <XCircle className="w-3.5 h-3.5" />
                    {submission.failed} failed
                  </span>
                  <span className="text-slate-500">
                    ({submission.total} total)
                  </span>
                </div>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-slate-800/80 rounded-full h-2 overflow-hidden flex">
                {submission.total > 0 && (
                  <>
                    <div
                      className="bg-emerald-500 transition-all duration-500"
                      style={{
                        width: `${(submission.passed / submission.total) * 100}%`,
                      }}
                    />
                    <div
                      className="bg-rose-500 transition-all duration-500"
                      style={{
                        width: `${(submission.failed / submission.total) * 100}%`,
                      }}
                    />
                  </>
                )}
              </div>

              {/* Feedback Summary */}
              <p className="text-xs text-slate-300 leading-relaxed font-mono">
                {submission.feedback_summary}
              </p>
            </div>
          </div>
        )}

        {/* Syntax / Execution Error Alert */}
        {submission.status === "error" && submission.error_message && (
          <div className="rounded-lg border border-rose-500/40 bg-rose-950/20 p-3 text-xs text-rose-300 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <div className="overflow-auto font-mono text-[11px] leading-relaxed">
              <div className="font-semibold text-rose-200 mb-1">
                Execution Error
              </div>
              <pre className="whitespace-pre-wrap">{submission.error_message}</pre>
            </div>
          </div>
        )}

        {/* Review Solution Action */}
        {submission.submission_id && !isRunnerUnavailable && onReviewSolution && (
          <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/60 border border-slate-800">
            <div className="text-xs text-slate-300 flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-sky-400" />
              <span>Understand the reference architecture and inspect line-by-line diffs:</span>
            </div>
            <button
              type="button"
              onClick={() => onReviewSolution(submission.submission_id!)}
              className="cursor-pointer inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs transition-all shadow-[0_0_12px_rgba(2,132,199,0.3)] hover:shadow-[0_0_16px_rgba(2,132,199,0.5)]"
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>{isReviewOpen ? "Hide Review" : "Review Solution"}</span>
            </button>
          </div>
        )}

        {/* Submission Meta & Mandatory Disclaimer */}
        <div className="flex flex-col gap-2 pt-2 border-t border-slate-800/80 text-[11px] text-slate-400">
          {submission.submission_id && (
            <div className="flex items-center justify-between font-mono text-slate-500">
              <span className="flex items-center gap-1.5">
                <Hash className="w-3 h-3 text-slate-500" />
                <span>ID: {submission.submission_id}</span>
                <span className="text-slate-700">•</span>
                <a
                  href="/progress"
                  className="text-emerald-400 hover:text-emerald-300 underline underline-offset-2 flex items-center gap-1"
                >
                  <Award className="w-3 h-3" />
                  <span>View in History</span>
                </a>
              </span>
              {submission.execution_time_ms !== null && (
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3 text-slate-500" />
                  {submission.execution_time_ms.toFixed(1)} ms
                </span>
              )}
            </div>
          )}

          {/* Mandatory Disclaimer */}
          <div className="flex items-start gap-1.5 text-slate-400/90 bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/60">
            <Info className="w-3.5 h-3.5 text-sky-400 shrink-0 mt-0.5" />
            <p className="leading-relaxed text-[11px]">
              {submission.score_disclaimer}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
