"use client";

import React, { useState } from "react";
import {
  BookOpen,
  Check,
  Copy,
  Sparkles,
  GitCompare,
  Lightbulb,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCcw,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { SolutionReviewData } from "../lib/types";
import { AiProviderSelector } from "./AiProviderSelector";

interface SolutionReviewPanelProps {
  review: SolutionReviewData;
  onRequestAiReview?: (provider?: string) => void;
  isAiLoading?: boolean;
  onClose?: () => void;
  selectedProvider?: string;
  onProviderChange?: (provider: string) => void;
}

export function SolutionReviewPanel({
  review,
  onRequestAiReview,
  isAiLoading = false,
  onClose,
  selectedProvider = "gemini",
  onProviderChange,
}: SolutionReviewPanelProps) {
  const [copied, setCopied] = useState(false);
  const [isDiffExpanded, setIsDiffExpanded] = useState(true);
  const [reviewProvider, setReviewProvider] = useState(selectedProvider);

  const handleProviderSelect = (p: string) => {
    setReviewProvider(p);
    if (onProviderChange) {
      onProviderChange(p);
    }
  };

  const handleCopyCode = async () => {
    try {
      await navigator.clipboard.writeText(review.reference_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback if clipboard API is blocked
    }
  };

  const isPerfect = review.score === 100;
  const isPartial = review.score !== null && review.score > 0 && review.score < 100;

  let scoreColorClass = "text-rose-400 bg-rose-950/20 border-rose-500/30";
  if (isPerfect) {
    scoreColorClass = "text-emerald-400 bg-emerald-950/20 border-emerald-500/30";
  } else if (isPartial) {
    scoreColorClass = "text-amber-400 bg-amber-950/20 border-amber-500/30";
  }

  // Diff lines formatted with color-coded syntax
  const diffLines = review.unified_diff.split("\n");

  return (
    <div className="flex flex-col rounded-xl border border-slate-800 bg-[#070b12] overflow-hidden shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3.5 bg-slate-900/90 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <BookOpen className="w-5 h-5 text-sky-400" />
          <div>
            <h3 className="font-semibold text-sm text-slate-100 flex items-center gap-2">
              Post-Submission Solution Review
              <span
                className={`text-[11px] font-mono px-2 py-0.5 rounded border ${scoreColorClass}`}
              >
                Score: {review.score !== null ? `${review.score}%` : "Unscorable"} ({review.passed_count}/{review.total_count} tests)
              </span>
            </h3>
            <p className="text-[11px] text-slate-400">
              Authoritative implementation breakdown and architectural review
            </p>
          </div>
        </div>

        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="cursor-pointer text-xs text-slate-400 hover:text-slate-200 transition-colors px-2 py-1 rounded hover:bg-slate-800"
          >
            Close Review
          </button>
        )}
      </div>

      <div className="p-5 space-y-6">
        {/* Local MVP Security Notice */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-3 text-[11px] text-slate-400 flex items-start gap-2.5">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <strong className="text-slate-300">Development Scope Notice:</strong>{" "}
            {review.security_notice}
          </p>
        </div>

        {/* Section A: Reference Implementation */}
        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="flex items-center justify-center w-5 h-5 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-400 text-xs font-mono font-bold">
                A
              </span>
              <h4 className="font-semibold text-xs uppercase tracking-wider text-slate-200">
                Authoritative Reference Implementation
              </h4>
            </div>

            <button
              type="button"
              onClick={handleCopyCode}
              className="cursor-pointer inline-flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-mono rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors border border-slate-700"
              title="Copy reference code to clipboard"
            >
              {copied ? (
                <>
                  <Check className="w-3 h-3 text-emerald-400" />
                  <span className="text-emerald-400">Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3 text-slate-400" />
                  <span>Copy Solution</span>
                </>
              )}
            </button>
          </div>

          <div className="relative rounded-lg border border-slate-800 bg-[#05080e] overflow-hidden">
            <div className="px-3.5 py-1.5 bg-slate-900/70 border-b border-slate-800/80 text-[11px] font-mono text-slate-400 flex items-center justify-between">
              <span>solution_reference.py (Python 3.12)</span>
              <span className="text-slate-500 text-[10px]">
                Your editor code remains untouched
              </span>
            </div>
            <pre className="p-4 text-xs font-mono text-emerald-300 overflow-x-auto leading-relaxed">
              <code>{review.reference_code}</code>
            </pre>
          </div>
        </div>

        {/* Section B: Key Implementation Decisions */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono font-bold">
              B
            </span>
            <h4 className="font-semibold text-xs uppercase tracking-wider text-slate-200">
              Key Implementation Decisions
            </h4>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {review.key_decisions.map((decision) => (
              <div
                key={decision.id}
                className="rounded-lg border border-slate-800/80 bg-slate-900/50 p-3.5 space-y-2"
              >
                <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400">
                  <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                  <span>{decision.title}</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {decision.explanation}
                </p>
                <div className="text-[11px] text-slate-400 bg-slate-950/70 p-2.5 rounded border border-slate-800/60 leading-relaxed">
                  <strong className="text-slate-300">Why It Matters:</strong>{" "}
                  {decision.why_it_matters}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Section C: Comparison with Submitted Code & Diff */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="flex items-center justify-center w-5 h-5 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-400 text-xs font-mono font-bold">
                C
              </span>
              <h4 className="font-semibold text-xs uppercase tracking-wider text-slate-200">
                Comparison With Your Submission
              </h4>
            </div>

            <button
              type="button"
              onClick={() => setIsDiffExpanded(!isDiffExpanded)}
              className="cursor-pointer text-xs font-mono text-slate-400 hover:text-slate-200 flex items-center gap-1"
            >
              <GitCompare className="w-3.5 h-3.5" />
              <span>{isDiffExpanded ? "Hide Line Diff" : "Show Line Diff"}</span>
              {isDiffExpanded ? (
                <ChevronUp className="w-3.5 h-3.5" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5" />
              )}
            </button>
          </div>

          {/* Semantic Comparison Summary */}
          <div className="p-3.5 rounded-lg border border-slate-800 bg-slate-900/40 space-y-2">
            <div className="flex items-center gap-2">
              {review.comparison.is_functionally_equivalent ? (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-mono bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                  <CheckCircle2 className="w-3 h-3" />
                  {review.comparison.difference_type === "identical"
                    ? "Exact Match"
                    : review.comparison.difference_type === "formatting_only"
                    ? "Formatting Difference Only"
                    : "Functionally Correct"}
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-mono bg-rose-500/10 border border-rose-500/30 text-rose-400">
                  <XCircle className="w-3 h-3" />
                  Functional Difference Detected
                </span>
              )}
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              {review.comparison.summary}
            </p>

            {/* Meaningful Differences Bullets */}
            {review.comparison.meaningful_differences.length > 0 && (
              <div className="pt-2 border-t border-slate-800 space-y-1.5">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Identified Differences:
                </span>
                <ul className="space-y-1 text-xs text-slate-300">
                  {review.comparison.meaningful_differences.map((diffItem, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-amber-400 font-bold">•</span>
                      <span>{diffItem}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Line Diff Viewer */}
          {isDiffExpanded && review.unified_diff && (
            <div className="rounded-lg border border-slate-800 bg-[#05080e] overflow-hidden font-mono text-[11px]">
              <div className="px-3 py-1.5 bg-slate-900/80 border-b border-slate-800 text-slate-400 flex items-center justify-between">
                <span>Unified Diff (- Submitted / + Reference)</span>
                <span className="text-[10px] text-slate-500">
                  {review.submission_id}
                </span>
              </div>
              <div className="p-3 overflow-x-auto leading-relaxed max-h-64 overflow-y-auto">
                {diffLines.map((line, lineIdx) => {
                  let lineStyle = "text-slate-400";
                  if (line.startsWith("+")) {
                    lineStyle = "text-emerald-300 bg-emerald-950/30";
                  } else if (line.startsWith("-")) {
                    lineStyle = "text-rose-300 bg-rose-950/30";
                  } else if (line.startsWith("@")) {
                    lineStyle = "text-sky-400 bg-sky-950/20 font-semibold";
                  }
                  return (
                    <div key={lineIdx} className={`${lineStyle} px-1.5 py-0.5`}>
                      {line || " "}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Section D: What to Learn */}
        <div className="space-y-2.5">
          <div className="flex items-center gap-2">
            <span className="flex items-center justify-center w-5 h-5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-mono font-bold">
              D
            </span>
            <h4 className="font-semibold text-xs uppercase tracking-wider text-slate-200">
              Architectural Takeaways & Concepts
            </h4>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-4 space-y-2.5">
            {review.learning_takeaways.map((takeaway, idx) => (
              <div key={idx} className="flex items-start gap-2.5 text-xs text-slate-300">
                <Lightbulb className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                <p className="leading-relaxed">{takeaway}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Section E: Optional Multi-Provider AI Review */}
        <div className="space-y-3 pt-2 border-t border-slate-800">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="flex items-center justify-center w-5 h-5 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-400 text-xs font-mono font-bold">
                E
              </span>
              <h4 className="font-semibold text-xs uppercase tracking-wider text-slate-200 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-sky-400" />
                <span>
                  AI Mentor Review{" "}
                  {review.ai_review?.provider && (
                    <span className="text-cyan-300 font-mono text-[10px] ml-1 uppercase">
                      ({review.ai_review.provider})
                    </span>
                  )}
                </span>
              </h4>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <AiProviderSelector
                selectedProvider={reviewProvider}
                onProviderChange={handleProviderSelect}
                compact
              />

              {onRequestAiReview && (
                <button
                  type="button"
                  onClick={() => onRequestAiReview(reviewProvider)}
                  disabled={isAiLoading}
                  className="cursor-pointer inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors border border-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isAiLoading ? (
                    <>
                      <Sparkles className="w-3 h-3 animate-spin text-sky-400" />
                      <span>Analyzing...</span>
                    </>
                  ) : review.ai_review?.available ? (
                    <>
                      <RotateCcw className="w-3 h-3 text-slate-400" />
                      <span>Regenerate Review</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3 h-3 text-sky-400" />
                      <span>Generate AI Review</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

          {/* AI Content / States */}
          {isAiLoading ? (
            <div className="p-6 rounded-lg border border-slate-800 bg-slate-900/30 text-center space-y-2">
              <Sparkles className="w-6 h-6 text-sky-400 animate-spin mx-auto" />
              <p className="text-xs text-slate-300 font-mono">
                {reviewProvider.toUpperCase()} is analyzing your submission against the reference solution...
              </p>
            </div>
          ) : review.ai_review?.available && review.ai_review.content ? (
            <div className="rounded-lg border border-sky-950/60 bg-sky-950/10 p-4 space-y-3">
              <div className="flex items-center justify-between text-[11px] font-mono text-sky-400 border-b border-sky-900/40 pb-2">
                <span className="flex items-center gap-2">
                  {review.ai_review.provider && (
                    <span className="px-1.5 py-0.2 rounded bg-sky-900/50 text-cyan-300 uppercase text-[10px]">
                      {review.ai_review.provider}
                    </span>
                  )}
                  <span>Model: {review.ai_review.model}</span>
                </span>
                <span className="text-slate-500">Untrusted Code Delimited</span>
              </div>
              <MarkdownRenderer content={review.ai_review.content} />
            </div>
          ) : review.ai_review?.error_message ? (
            <div className="p-4 rounded-lg border border-amber-900/60 bg-amber-950/20 text-xs text-amber-300 space-y-2">
              <div className="flex items-center gap-2 font-semibold text-amber-200">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <span>AI Review Unavailable ({reviewProvider.toUpperCase()})</span>
              </div>
              <p className="leading-relaxed font-mono text-[11px]">
                {review.ai_review.error_message}
              </p>
              {onRequestAiReview && (
                <button
                  type="button"
                  onClick={() => onRequestAiReview(reviewProvider)}
                  className="cursor-pointer inline-flex items-center gap-1.5 px-2.5 py-1 text-xs rounded bg-amber-900/50 hover:bg-amber-800/50 text-amber-200 border border-amber-700/60 transition-colors"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>Retry Review</span>
                </button>
              )}
            </div>
          ) : (
            <div className="p-4 rounded-lg border border-slate-800/80 bg-slate-900/30 text-xs text-slate-400 flex items-center justify-between">
              <span>
                Want deeper personalized guidance on architectural trade-offs? Request an AI review.
              </span>
              {onRequestAiReview && (
                <button
                  type="button"
                  onClick={() => onRequestAiReview(reviewProvider)}
                  disabled={isAiLoading}
                  className="cursor-pointer inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-sky-600 hover:bg-sky-500 text-white transition-colors"
                >
                  <Sparkles className="w-3 h-3" />
                  <span>Get AI Review</span>
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
