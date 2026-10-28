"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Code2,
  Play,
  Bot,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Sparkles,
  Info,
  Terminal,
} from "lucide-react";

interface ChallengePreviewProps {
  onLaunchAssessment?: () => void;
}

export function ChallengePreview({ onLaunchAssessment }: ChallengePreviewProps = {}) {
  void onLaunchAssessment;
  const [activeTab, setActiveTab] = useState<"code" | "tests" | "ai">("code");

  return (
    <section id="preview" className="py-16 sm:py-24 border-t border-slate-800/80 bg-slate-950/40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 mb-2">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Interactive Preview (Placeholder Data)</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100">
              Sample Interview Round
            </h2>
            <p className="mt-1 text-sm text-slate-400">
              Explore the structure of a real AI-assisted debugging and refactoring session.
            </p>
          </div>

          {/* Placeholder Banner Notice */}
          <div className="flex items-center gap-2 text-xs font-mono text-amber-300/90 bg-amber-500/10 border border-amber-500/20 px-3 py-1.5 rounded-lg">
            <Info className="w-4 h-4 shrink-0 text-amber-400" />
            <span>Phase 1 Scope: Read-only preview. Live execution sandbox coming in Phase 2.</span>
          </div>
        </div>

        {/* Challenge Card Workspace */}
        <div className="rounded-xl border border-slate-800 bg-[#0b0f19] overflow-hidden shadow-2xl">
          {/* Challenge Meta Bar */}
          <div className="p-4 sm:p-6 border-b border-slate-800 bg-slate-900/60 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-rose-500/10 border border-rose-500/30 text-rose-300">
                  Bug Investigation
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 text-slate-300">
                  TypeScript / Node.js
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-amber-500/10 text-amber-300">
                  Medium Difficulty
                </span>
                <div className="flex items-center gap-1 text-[11px] text-slate-400 font-mono ml-2">
                  <Clock className="w-3.5 h-3.5" />
                  <span>35 Minutes</span>
                </div>
              </div>
              <h3 className="text-lg sm:text-xl font-semibold text-slate-100">
                Fix In-Flight Request Deduplication Race Condition
              </h3>
            </div>

            {/* Launch Assessment Action */}
            <div className="flex items-center gap-3">
              <Link
                href="/challenges/request-deduplication"
                className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-medium text-xs sm:text-sm transition-all shadow-[0_0_15px_rgba(16,185,129,0.2)]"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Open Python Challenge</span>
              </Link>
            </div>
          </div>

          {/* Description Snippet */}
          <div className="px-4 py-3 sm:px-6 bg-slate-900/20 border-b border-slate-800 text-xs sm:text-sm text-slate-300 leading-relaxed">
            <span className="font-semibold text-slate-200">Scenario:</span> The
            production cache layer deduplicates identical concurrent HTTP requests.
            Under burst traffic, simultaneous requests for un-cached keys trigger
            duplicate database queries due to non-atomic promise memoization.
            Your task: diagnose the race condition, write a regression test, and
            safely coordinate with the AI pairing partner to refactor.
          </div>

          {/* Interactive Preview Tabs */}
          <div className="flex items-center border-b border-slate-800 bg-[#080c14] px-4">
            <button
              onClick={() => setActiveTab("code")}
              className={`cursor-pointer flex items-center gap-2 px-4 py-3 text-xs font-mono border-b-2 transition-colors ${
                activeTab === "code"
                  ? "border-emerald-400 text-emerald-400 bg-slate-900/40"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <Code2 className="w-4 h-4" />
              <span>deduplicator.ts</span>
            </button>
            <button
              onClick={() => setActiveTab("tests")}
              className={`cursor-pointer flex items-center gap-2 px-4 py-3 text-xs font-mono border-b-2 transition-colors ${
                activeTab === "tests"
                  ? "border-emerald-400 text-emerald-400 bg-slate-900/40"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <Terminal className="w-4 h-4" />
              <span>deduplicator.test.ts (2 Failing)</span>
            </button>
            <button
              onClick={() => setActiveTab("ai")}
              className={`cursor-pointer flex items-center gap-2 px-4 py-3 text-xs font-mono border-b-2 transition-colors ${
                activeTab === "ai"
                  ? "border-emerald-400 text-emerald-400 bg-slate-900/40"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <Bot className="w-4 h-4 text-cyan-400" />
              <span>AI Copilot Log</span>
            </button>
          </div>

          {/* Tab Content Display */}
          <div className="p-4 sm:p-6 font-mono text-xs text-slate-300 bg-[#070b12] overflow-x-auto min-h-[260px]">
            {activeTab === "code" && (
              <pre className="text-slate-300 leading-relaxed">
{`import { fetchFromDatabase } from "./db";

// Map storing in-flight promises to deduplicate queries
const pendingPromises = new Map<string, Promise<unknown>>();

export async function fetchWithDeduplication<T>(key: string): Promise<T> {
  const existing = pendingPromises.get(key);
  if (existing) {
    return existing as Promise<T>;
  }

  // BUG: Race condition! In concurrent Node event loop ticks, multiple callers
  // evaluate existing === undefined before the promise is stored below.
  const task = fetchFromDatabase<T>(key).finally(() => {
    pendingPromises.delete(key);
  });

  pendingPromises.set(key, task);
  return task;
}`}
              </pre>
            )}

            {activeTab === "tests" && (
              <div className="space-y-3">
                <div className="p-3 rounded bg-rose-950/30 border border-rose-900/40 text-rose-300 flex items-start gap-3">
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold block">
                      FAIL: test_concurrent_burst_triggers_single_query
                    </span>
                    <span className="text-rose-300/80 text-[11px]">
                      Expected fetchFromDatabase to be called exactly 1 time, but received 4 calls during 100 concurrent iterations.
                    </span>
                  </div>
                </div>

                <div className="p-3 rounded bg-emerald-950/20 border border-emerald-900/40 text-emerald-300 flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold block">
                      PASS: test_sequential_requests_evict_after_resolution
                    </span>
                    <span className="text-emerald-300/80 text-[11px]">
                      Cache promise cleanly deleted from map upon resolution.
                    </span>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "ai" && (
              <div className="space-y-3">
                <div className="p-3 rounded bg-slate-900/70 border border-slate-800 text-slate-300">
                  <div className="flex items-center gap-2 text-cyan-400 font-semibold mb-1">
                    <Bot className="w-4 h-4" />
                    <span>AI Assistant (Pairing Mode: Guided Critique)</span>
                  </div>
                  <p className="text-slate-400 text-[11px] leading-relaxed">
                    &ldquo;Notice where <code className="text-emerald-400">pendingPromises.set(key, task)</code> is invoked relative to any microtask checkpoints. If <code className="text-emerald-400">fetchFromDatabase</code> triggers an initial synchronous setup before the promise reference is registered, other concurrent calls in the same tick will miss the cache hit.&rdquo;
                  </p>
                </div>

                <div className="text-[11px] text-slate-500 italic">
                  Candidate prompt history and AI token usage will be recorded for scoring in Phase 2.
                </div>
              </div>
            )}
          </div>

          {/* Footer inside Challenge card */}
          <div className="px-4 py-3 bg-slate-900/40 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span>Standard round duration: 35 minutes</span>
            <span className="font-mono text-[11px] text-emerald-400">
              Deterministic scoring ready
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
