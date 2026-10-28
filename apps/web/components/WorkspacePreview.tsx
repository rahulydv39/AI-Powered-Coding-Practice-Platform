"use client";

import React, { useState } from "react";
import {
  Code2,
  Terminal,
  Bot,
  CheckCircle2,
  AlertTriangle,
  Play,
} from "lucide-react";
import Link from "next/link";
import { AnimatedSection } from "./AnimatedSection";

export function WorkspacePreview() {
  const [activeTab, setActiveTab] = useState<"code" | "tests" | "ai">("code");

  return (
    <section id="preview" className="relative py-24 sm:py-32">
      <div className="absolute inset-0 bg-slate-950/40 pointer-events-none" />
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-slate-800 to-transparent" />
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-slate-800 to-transparent" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <AnimatedSection animation="fade-up">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-100">
              The developer workspace
            </h2>
            <p className="mt-4 text-base text-slate-400">
              A focused coding environment with integrated tests and AI
              assistance — preview of the actual practice experience.
            </p>
          </div>
        </AnimatedSection>

        <AnimatedSection animation="fade-up" delay={200}>
          <div className="rounded-2xl border border-slate-800 bg-[#0a0f1a] overflow-hidden shadow-2xl shadow-black/40">
            {/* Challenge header */}
            <div className="p-4 sm:p-5 border-b border-slate-800 bg-slate-900/60 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex flex-wrap items-center gap-2 mb-1.5">
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-rose-500/10 border border-rose-500/30 text-rose-300">
                    Bug Investigation
                  </span>
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 text-slate-300">
                    TypeScript
                  </span>
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-amber-500/10 text-amber-300">
                    Medium
                  </span>
                </div>
                <h3 className="text-base sm:text-lg font-semibold text-slate-100">
                  Fix Request Deduplication Race Condition
                </h3>
              </div>
              <Link
                href="/challenges/request-deduplication"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-medium text-sm transition-all shrink-0"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Try This Challenge</span>
              </Link>
            </div>

            {/* Tab navigation */}
            <div className="flex items-center border-b border-slate-800 bg-[#080c14] px-4 overflow-x-auto">
              <button
                type="button"
                onClick={() => setActiveTab("code")}
                className={`cursor-pointer flex items-center gap-2 px-4 py-3 text-xs font-mono border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === "code"
                    ? "border-emerald-400 text-emerald-400 bg-slate-900/40"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                <Code2 className="w-4 h-4" />
                <span>deduplicator.ts</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("tests")}
                className={`cursor-pointer flex items-center gap-2 px-4 py-3 text-xs font-mono border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === "tests"
                    ? "border-emerald-400 text-emerald-400 bg-slate-900/40"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                <Terminal className="w-4 h-4" />
                <span>Test Results</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("ai")}
                className={`cursor-pointer flex items-center gap-2 px-4 py-3 text-xs font-mono border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === "ai"
                    ? "border-cyan-400 text-cyan-400 bg-slate-900/40"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                <Bot className="w-4 h-4" />
                <span>AI Assistant</span>
              </button>
            </div>

            {/* Tab content */}
            <div className="p-5 sm:p-6 font-mono text-sm text-slate-300 bg-[#070b12] overflow-x-auto min-h-[240px]">
              {activeTab === "code" && (
                <pre className="text-slate-300 leading-relaxed text-[13px]">
{`import { fetchFromDatabase } from "./db";

const pendingPromises = new Map<string, Promise<unknown>>();

export async function fetchWithDeduplication<T>(
  key: string
): Promise<T> {
  const existing = pendingPromises.get(key);
  if (existing) {
    return existing as Promise<T>;
  }

  // BUG: Race condition — concurrent callers bypass
  // the check before the promise is stored below.
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
                  <div className="p-3 rounded-lg bg-rose-950/20 border border-rose-900/40 text-rose-300 flex items-start gap-3">
                    <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold block text-xs">
                        FAIL: test_concurrent_burst_triggers_single_query
                      </span>
                      <span className="text-rose-300/80 text-[11px]">
                        Expected fetchFromDatabase called 1 time, but got 4 calls
                        during 100 concurrent iterations.
                      </span>
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-900/40 text-emerald-300 flex items-start gap-3">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold block text-xs">
                        PASS: test_sequential_requests_evict_after_resolution
                      </span>
                      <span className="text-emerald-300/80 text-[11px]">
                        Cache promise cleanly deleted from map upon resolution.
                      </span>
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-900/40 text-emerald-300 flex items-start gap-3">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold block text-xs">
                        PASS: test_different_keys_not_deduplicated
                      </span>
                      <span className="text-emerald-300/80 text-[11px]">
                        Separate keys correctly trigger independent database calls.
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "ai" && (
                <div className="space-y-3">
                  <div className="p-4 rounded-lg bg-slate-900/70 border border-slate-800 text-slate-300">
                    <div className="flex items-center gap-2 text-cyan-400 font-semibold mb-2 text-xs">
                      <Bot className="w-4 h-4" />
                      <span>AI Assistant — Hint Level 1</span>
                    </div>
                    <p className="text-slate-400 text-[13px] leading-relaxed">
                      &ldquo;Consider where{" "}
                      <code className="text-emerald-400 bg-emerald-500/10 px-1 rounded">
                        pendingPromises.set(key, task)
                      </code>{" "}
                      is called relative to any microtask checkpoint. If
                      concurrent callers in the same event loop tick evaluate
                      the map lookup before the promise is stored, they will
                      each create a new database query.&rdquo;
                    </p>
                  </div>
                  <div className="text-[11px] text-slate-500 italic px-1">
                    AI hints are progressive — request higher levels for more
                    specific guidance.
                  </div>
                </div>
              )}
            </div>

            {/* Bottom status bar */}
            <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900/50 border-t border-slate-800 text-[11px] font-mono text-slate-500">
              <div className="flex items-center gap-3">
                <span className="text-amber-400">1 test failing</span>
                <span>35 min estimated</span>
              </div>
              <span className="text-slate-600">Preview of actual workspace</span>
            </div>
          </div>
        </AnimatedSection>
      </div>
    </section>
  );
}
