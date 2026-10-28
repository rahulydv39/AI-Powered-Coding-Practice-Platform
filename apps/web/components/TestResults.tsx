"use client";

import React, { useState } from "react";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  ChevronDown,
  ChevronRight,
  ShieldAlert,
  Terminal,
} from "lucide-react";
import { CodeRunResult, TestCaseSummaryItem } from "@/lib/types";

interface TestResultsProps {
  result: CodeRunResult | null;
  isRunning: boolean;
  error?: string | null;
  testCases?: TestCaseSummaryItem[];
}

export function TestResults({
  result,
  isRunning,
  error,
  testCases = [],
}: TestResultsProps) {
  const [showStdout, setShowStdout] = useState(false);
  const [selectedCaseIndex, setSelectedCaseIndex] = useState<number | "all">("all");

  if (isRunning) {
    return (
      <div className="rounded-xl border border-slate-800 bg-[#070b12] p-8 text-center animate-pulse">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 mb-3">
          <Clock className="w-6 h-6 animate-spin" />
        </div>
        <h4 className="text-sm font-semibold text-slate-200">
          Running Tests in Isolated Sandbox...
        </h4>
        <p className="text-xs text-slate-400 mt-1">
          Spinning up an ephemeral container with strict resource limits and dropped network.
        </p>
      </div>
    );
  }

  // Network or API connection failure
  if (error) {
    return (
      <div className="rounded-xl border border-rose-900/60 bg-rose-950/20 p-5 text-rose-300">
        <div className="flex items-start gap-3">
          <XCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-sm font-semibold text-rose-200">
              Execution Request Failed
            </h4>
            <p className="text-xs text-rose-300/90 leading-relaxed font-mono">
              {error}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // No run performed yet
  if (!result) {
    return (
      <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/20 p-8 text-center space-y-2">
        <div className="w-9 h-9 rounded-lg bg-slate-800/60 border border-slate-700/50 flex items-center justify-center text-slate-400 mx-auto">
          <Terminal className="w-4 h-4" />
        </div>
        <p className="text-xs font-mono text-slate-300">
          No tests executed yet
        </p>
        <p className="text-[11px] text-slate-500 max-w-sm mx-auto">
          Click <strong className="text-slate-300">Run Tests</strong> (or press <kbd className="px-1 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono text-[10px]">⌘↵</kbd>) to evaluate your solution in the Docker sandbox.
        </p>
      </div>
    );
  }

  // Docker Sandbox is not available on host
  if (result.status === "runner_unavailable") {
    return (
      <div className="rounded-xl border border-amber-900/60 bg-amber-950/20 p-5 text-amber-200">
        <div className="flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-semibold text-amber-100">
                Docker Sandbox Prerequisite Required
              </h4>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400">
                Security Enforced
              </span>
            </div>
            <p className="text-xs text-amber-200/90 leading-relaxed">
              {result.error_message ||
                "For security, student code is never executed directly on the host machine. Ephemeral Docker containers are required to safely isolate submissions."}
            </p>
            <div className="mt-3 p-3 rounded bg-black/40 border border-amber-900/40 font-mono text-[11px] text-slate-300 space-y-1.5">
              <div className="font-semibold text-amber-300">How to enable local test execution on macOS:</div>
              <div>1. Install <span className="text-emerald-400">Docker Desktop</span> or <span className="text-emerald-400">OrbStack</span>.</div>
              <div>2. Launch the application and ensure the Docker daemon is active (<code className="text-slate-200">docker info</code>).</div>
              <div>3. Click &ldquo;Run Tests&rdquo; again. The backend will automatically detect the container runtime.</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Syntax or Runtime Crash in student code
  if (result.status === "error") {
    return (
      <div className="rounded-xl border border-rose-900/60 bg-rose-950/20 p-5 text-rose-200">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="space-y-2 flex-1">
            <h4 className="text-sm font-semibold text-rose-100">
              Code Error / Failed to Execute
            </h4>
            <div className="p-3 rounded bg-black/50 border border-rose-900/40 font-mono text-xs text-rose-300 whitespace-pre-wrap">
              {result.error_message || "Unknown error during execution."}
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              Execution duration: {result.execution_time_ms}ms
            </span>
          </div>
        </div>
      </div>
    );
  }

  // Execution Timeout
  if (result.status === "timeout") {
    return (
      <div className="rounded-xl border border-amber-900/60 bg-amber-950/20 p-5 text-amber-200">
        <div className="flex items-start gap-3">
          <Clock className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-2 flex-1">
            <h4 className="text-sm font-semibold text-amber-100">
              Execution Timed Out
            </h4>
            <p className="text-xs text-amber-300/90 leading-relaxed font-mono">
              {result.error_message || "Execution exceeded the 5.0 second time limit. Check for infinite loops or recursive recursion."}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Standard Test Run Outcome (passed or failed)
  const allPassed = result.status === "passed";

  return (
    <div className="rounded-xl border border-slate-800 bg-[#070b12] overflow-hidden shadow-lg space-y-4 p-4 sm:p-5">
      {/* Run Summary Banner */}
      <div
        className={`flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-lg border gap-3 ${
          allPassed
            ? "bg-emerald-950/30 border-emerald-800/60 text-emerald-200"
            : "bg-rose-950/30 border-rose-800/60 text-rose-200"
        }`}
      >
        <div className="flex items-center gap-3">
          {allPassed ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          ) : (
            <XCircle className="w-5 h-5 text-rose-400 shrink-0" />
          )}
          <div>
            <span className="font-semibold text-sm block">
              {allPassed
                ? "All Tests Passed! Excellent Job."
                : `${result.failed} of ${result.total} Tests Failed`}
            </span>
            <span className="text-xs opacity-80">
              {allPassed
                ? "Your implementation meets all requirements and handles edge cases."
                : "Inspect the failing test messages below to diagnose the issue."}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs self-end sm:self-center">
          <span className="px-2 py-0.5 rounded bg-black/40 border border-slate-700/60">
            {result.passed}/{result.total} Passed
          </span>
          <span className="text-slate-400">{result.execution_time_ms}ms</span>
        </div>
      </div>

      {/* Test Case Inspector */}
      <div className="space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
          <div className="flex items-center gap-1.5 overflow-x-auto text-xs font-mono py-0.5">
            <button
              type="button"
              onClick={() => setSelectedCaseIndex("all")}
              className={`cursor-pointer px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                selectedCaseIndex === "all"
                  ? "bg-slate-800 text-slate-100 border border-slate-700 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              All Cases ({result.tests.length})
            </button>
            {result.tests.map((test, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setSelectedCaseIndex(idx)}
                className={`cursor-pointer px-2.5 py-1 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 ${
                  selectedCaseIndex === idx
                    ? "bg-slate-800 text-slate-100 border border-slate-700 shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    test.passed ? "bg-emerald-400" : "bg-rose-400"
                  }`}
                />
                <span>Case {idx + 1}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Selected Individual Case View */}
        {selectedCaseIndex !== "all" && typeof selectedCaseIndex === "number" && (
          (() => {
            const test = result.tests[selectedCaseIndex];
            if (!test) return null;
            const matchingMeta = testCases.find((tc) => tc.name === test.name);

            return (
              <div className="rounded-xl border border-slate-800 bg-[#090d16] p-4 space-y-3 font-mono text-xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                  <div className="flex items-center gap-2">
                    {test.passed ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
                    )}
                    <span className="font-semibold text-slate-100 text-sm">
                      {test.name}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-[11px]">
                    <span
                      className={`px-2 py-0.5 rounded uppercase font-semibold ${
                        test.passed
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                          : "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                      }`}
                    >
                      {test.passed ? "Passed" : "Failed"}
                    </span>
                    {test.duration_ms !== null && test.duration_ms !== undefined && (
                      <span className="text-slate-500">
                        {test.duration_ms.toFixed(2)} ms
                      </span>
                    )}
                  </div>
                </div>

                {/* Real Test Case Description from metadata */}
                {matchingMeta && (
                  <div className="space-y-1">
                    <span className="text-[11px] uppercase tracking-wider text-slate-500 block">
                      Requirement Checked:
                    </span>
                    <p className="text-xs text-slate-300 font-sans leading-relaxed">
                      {matchingMeta.description}
                    </p>
                  </div>
                )}

                {/* Assertion Failure Message (if failed) */}
                {test.message ? (
                  <div className="space-y-1 pt-1">
                    <span className="text-[11px] uppercase tracking-wider text-rose-400 font-semibold block">
                      Failure Trace / Assertion Error:
                    </span>
                    <div className="p-3 rounded-lg bg-black/60 border border-rose-900/50 text-rose-300 whitespace-pre-wrap leading-relaxed text-xs">
                      {test.message}
                    </div>
                  </div>
                ) : (
                  <div className="p-3 rounded-lg bg-emerald-950/10 border border-emerald-900/30 text-emerald-300 text-xs flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>Test executed successfully and passed all assertions without errors.</span>
                  </div>
                )}
              </div>
            );
          })()
        )}

        {/* All Cases View */}
        {selectedCaseIndex === "all" && (
          <div className="space-y-2">
            {result.tests.map((test, index) => {
              const matchingMeta = testCases.find((tc) => tc.name === test.name);
              return (
                <div
                  key={index}
                  className={`p-3 rounded-lg border font-mono text-xs transition-colors ${
                    test.passed
                      ? "bg-emerald-950/10 border-emerald-900/30 text-emerald-300"
                      : "bg-rose-950/20 border-rose-900/40 text-rose-300"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      {test.passed ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                      ) : (
                        <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
                      )}
                      <span className="font-semibold text-slate-100">{test.name}</span>
                    </div>
                    <div className="flex items-center gap-2 text-[10px]">
                      {test.duration_ms !== null && test.duration_ms !== undefined && (
                        <span className="text-slate-500">{test.duration_ms.toFixed(1)}ms</span>
                      )}
                      <span
                        className={`uppercase px-1.5 py-0.5 rounded ${
                          test.passed
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                        }`}
                      >
                        {test.passed ? "Passed" : "Failed"}
                      </span>
                    </div>
                  </div>

                  {matchingMeta && (
                    <p className="mt-1 text-[11px] font-sans text-slate-400">
                      {matchingMeta.description}
                    </p>
                  )}

                  {test.message && (
                    <div className="mt-2 p-2 rounded bg-black/50 border border-rose-900/50 text-[11px] text-rose-300 whitespace-pre-wrap font-mono">
                      {test.message}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Stdout Collapsible Toggle (if available) */}
      {result.stdout && (
        <div className="pt-2 border-t border-slate-800">
          <button
            type="button"
            onClick={() => setShowStdout(!showStdout)}
            className="cursor-pointer flex items-center gap-1.5 text-xs font-mono text-slate-400 hover:text-slate-200"
          >
            {showStdout ? (
              <ChevronDown className="w-3.5 h-3.5" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5" />
            )}
            <span>Container Standard Output ({result.stdout.length} bytes)</span>
          </button>

          {showStdout && (
            <pre className="mt-2 p-3 rounded bg-black/60 border border-slate-800 text-[11px] font-mono text-slate-400 whitespace-pre-wrap max-h-40 overflow-auto">
              {result.stdout}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
