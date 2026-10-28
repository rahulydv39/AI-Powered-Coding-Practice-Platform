"use client";

import React, { useState } from "react";
import {
  Sparkles,
  AlertCircle,
  RotateCcw,
  Bot,
  ChevronDown,
  ChevronUp,
  Lightbulb,
} from "lucide-react";
import { explainCode, getHint } from "@/lib/api";
import { HintHistoryItem } from "@/lib/types";
import { MarkdownRenderer } from "./MarkdownRenderer";
import {
  AiProviderSelector,
  LOCAL_STORAGE_PROVIDER_KEY,
} from "./AiProviderSelector";

interface AiAssistantPanelProps {
  challengeId: string;
  code: string;
}

export function AiAssistantPanel({ challengeId, code }: AiAssistantPanelProps) {
  const [activeTab, setActiveTab] = useState<"explain" | "hint">("explain");

  // Multi-Provider state (lazy initialize from localStorage if available)
  const [selectedProvider, setSelectedProvider] = useState<string>(() => {
    if (typeof window !== "undefined") {
      try {
        return localStorage.getItem(LOCAL_STORAGE_PROVIDER_KEY) || "gemini";
      } catch {
        return "gemini";
      }
    }
    return "gemini";
  });

  // Loading & Error States
  const [loadingExplain, setLoadingExplain] = useState(false);
  const [loadingHint, setLoadingHint] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Content States
  const [explanation, setExplanation] = useState<string | null>(null);
  const [explanationModel, setExplanationModel] = useState<string | null>(null);
  const [explanationProvider, setExplanationProvider] = useState<string | null>(null);

  // Progressive Hint States
  const [hintHistory, setHintHistory] = useState<HintHistoryItem[]>([]);
  const [hintModel, setHintModel] = useState<string | null>(null);
  const [hintProvider, setHintProvider] = useState<string | null>(null);

  // Optional Student Question
  const [showQuestionInput, setShowQuestionInput] = useState(false);
  const [question, setQuestion] = useState("");

  const handleExplain = async () => {
    if (loadingExplain || loadingHint || !code.trim()) return;

    setLoadingExplain(true);
    setErrorMsg(null);
    setActiveTab("explain");

    const result = await explainCode(
      challengeId,
      code,
      question.trim() || undefined,
      selectedProvider
    );

    if (result.data && result.data.success) {
      setExplanation(result.data.content);
      setExplanationModel(result.data.model);
      setExplanationProvider(result.data.provider || selectedProvider);
    } else {
      setErrorMsg(result.error || "Failed to generate code explanation.");
    }

    setLoadingExplain(false);
  };

  const handleGetHint = async () => {
    if (loadingExplain || loadingHint || !code.trim()) return;

    setLoadingHint(true);
    setErrorMsg(null);
    setActiveTab("hint");

    const nextLevel = hintHistory.length + 1;
    const result = await getHint(
      challengeId,
      code,
      nextLevel,
      question.trim() || undefined,
      selectedProvider
    );

    if (result.data && result.data.success) {
      const newHintItem: HintHistoryItem = {
        level: nextLevel,
        content: result.data.content,
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };
      setHintHistory((prev) => [...prev, newHintItem]);
      setHintModel(result.data.model);
      setHintProvider(result.data.provider || selectedProvider);
    } else {
      setErrorMsg(result.error || "Failed to generate hint.");
    }

    setLoadingHint(false);
  };

  const handleResetHints = () => {
    setHintHistory([]);
    setHintModel(null);
    setErrorMsg(null);
  };

  const isAnyLoading = loadingExplain || loadingHint;

  return (
    <div className="rounded-xl border border-slate-800 bg-[#0a0f1c] overflow-hidden shadow-lg flex flex-col">
      {/* Panel Header */}
      <div className="px-4 py-3 bg-slate-900/90 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-xs text-slate-100">
                AI Interview Coach
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
                Multi-Provider
              </span>
            </div>
            <p className="text-[10px] text-slate-400 hidden sm:block">
              Code isolated in sandbox • Progressive hints • Independent from deterministic grading
            </p>
          </div>
        </div>

        {/* Right side controls: Model Selector & Actions */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Multi-Provider Selector */}
          <AiProviderSelector
            selectedProvider={selectedProvider}
            onProviderChange={(p) => {
              setSelectedProvider(p);
              setErrorMsg(null);
            }}
            compact
          />

          {/* Action Buttons */}
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={handleExplain}
              disabled={isAnyLoading || !code.trim()}
              className={`cursor-pointer inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === "explain" && explanation
                  ? "bg-emerald-500/20 border border-emerald-500/40 text-emerald-300"
                  : "bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/60"
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              <Sparkles
                className={`w-3.5 h-3.5 ${
                  loadingExplain ? "animate-spin text-emerald-400" : "text-emerald-400"
                }`}
              />
              <span>{loadingExplain ? "Analyzing..." : "Explain Code"}</span>
            </button>

            <button
              type="button"
              onClick={handleGetHint}
              disabled={isAnyLoading || !code.trim() || hintHistory.length >= 3}
              className={`cursor-pointer inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === "hint" && hintHistory.length > 0
                  ? "bg-cyan-500/20 border border-cyan-500/40 text-cyan-300"
                  : "bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/60"
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              <Lightbulb
                className={`w-3.5 h-3.5 ${
                  loadingHint ? "animate-spin text-cyan-400" : "text-cyan-400"
                }`}
              />
              <span>
                {loadingHint
                  ? "Thinking..."
                  : hintHistory.length === 0
                  ? "Get Hint"
                  : hintHistory.length >= 3
                  ? "All 3 Hints Viewed"
                  : `Next Hint (${hintHistory.length + 1}/3)`}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Optional Student Question Bar (Collapsible) */}
      <div className="px-4 py-2 bg-slate-950/40 border-b border-slate-800/80">
        <button
          type="button"
          onClick={() => setShowQuestionInput(!showQuestionInput)}
          className="cursor-pointer flex items-center gap-1.5 text-[11px] font-mono text-slate-400 hover:text-slate-200"
        >
          {showQuestionInput ? (
            <ChevronUp className="w-3.5 h-3.5" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5" />
          )}
          <span>Ask a specific question about your code (optional)</span>
        </button>

        {showQuestionInput && (
          <div className="mt-2 flex gap-2">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. Why is seen_ids.add() important here?"
              maxLength={500}
              className="flex-1 px-3 py-1.5 text-xs bg-slate-900 border border-slate-800 rounded-md text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
            />
            {question && (
              <button
                type="button"
                onClick={() => setQuestion("")}
                className="text-[11px] text-slate-500 hover:text-slate-300 px-1 font-mono"
              >
                Clear
              </button>
            )}
          </div>
        )}
      </div>

      {/* Content Area */}
      <div className="p-4 sm:p-5 flex-1 min-h-[160px] max-h-[460px] overflow-y-auto space-y-4">
        {/* Error Notification Alert */}
        {errorMsg && (
          <div className="p-3.5 rounded-lg border border-rose-900/50 bg-rose-950/20 text-rose-300 text-xs">
            <div className="flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <span className="font-semibold block text-rose-200">
                  Assistant Request Failed ({selectedProvider.toUpperCase()})
                </span>
                <p className="text-[11px] font-mono text-rose-300/90 leading-relaxed">
                  {errorMsg}
                </p>
                <div className="mt-2 p-2 rounded bg-black/40 border border-rose-900/30 font-mono text-[10px] text-slate-300 flex items-center justify-between gap-2">
                  <span>
                    Need to switch provider? Choose another from the selector above, or configure{" "}
                    <code className="text-cyan-400">
                      {selectedProvider === "claude"
                        ? "ANTHROPIC_API_KEY"
                        : selectedProvider === "openai"
                        ? "OPENAI_API_KEY"
                        : "GEMINI_API_KEY"}
                    </code>{" "}
                    in <code className="text-slate-200">apps/api/.env</code>.
                  </span>
                  {selectedProvider !== "gemini" && (
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedProvider("gemini");
                        setErrorMsg(null);
                      }}
                      className="cursor-pointer shrink-0 px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 text-[10px] border border-cyan-800/60"
                    >
                      Switch to Gemini
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Loading Indicator */}
        {isAnyLoading && (
          <div className="py-8 text-center space-y-2 animate-pulse">
            <div className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Bot className="w-4 h-4 animate-bounce" />
            </div>
            <p className="text-xs font-mono text-slate-400">
              {loadingExplain
                ? `Analyzing Python code structure with ${selectedProvider.toUpperCase()}...`
                : `Generating progressive Hint ${hintHistory.length + 1} with ${selectedProvider.toUpperCase()}...`}
            </p>
          </div>
        )}

        {/* Empty State when no action taken yet */}
        {!isAnyLoading && !explanation && hintHistory.length === 0 && !errorMsg && (
          <div className="py-6 text-center space-y-2 text-slate-500">
            <Bot className="w-8 h-8 mx-auto text-slate-600 stroke-[1.5]" />
            <p className="text-xs font-mono">
              Ready to assist with your solution.
            </p>
            <p className="text-[11px] text-slate-500 max-w-sm mx-auto">
              Click <strong className="text-slate-400">Explain Code</strong> to understand your logic, or <strong className="text-slate-400">Get Hint</strong> for progressive debugging clues without spoiling the answer.
            </p>
          </div>
        )}

        {/* Explain Mode Content Display */}
        {activeTab === "explain" && explanation && !loadingExplain && (
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800 text-xs">
              <span className="font-semibold text-slate-200 flex items-center gap-1.5 font-mono text-[11px]">
                <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                Code Explanation
              </span>
              <div className="flex items-center gap-2 font-mono text-[10px] text-slate-400">
                {explanationProvider && (
                  <span className="px-1.5 py-0.5 rounded bg-cyan-950/50 border border-cyan-800/40 text-cyan-300 uppercase">
                    {explanationProvider}
                  </span>
                )}
                {explanationModel && (
                  <span className="text-slate-500">Model: {explanationModel}</span>
                )}
              </div>
            </div>

            <MarkdownRenderer content={explanation} />
          </div>
        )}

        {/* Hint Mode Progressive Content Display */}
        {activeTab === "hint" && hintHistory.length > 0 && !loadingHint && (
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800 text-xs">
              <span className="font-semibold text-slate-200 flex items-center gap-1.5 font-mono text-[11px]">
                <Lightbulb className="w-3.5 h-3.5 text-cyan-400" />
                Progressive Hints ({hintHistory.length} of 3)
              </span>
              <div className="flex items-center gap-3">
                {hintProvider && (
                  <span className="px-1.5 py-0.5 rounded bg-cyan-950/50 border border-cyan-800/40 text-cyan-300 font-mono text-[10px] uppercase">
                    {hintProvider}{hintModel ? ` • ${hintModel}` : ""}
                  </span>
                )}
                <button
                  type="button"
                  onClick={handleResetHints}
                  className="cursor-pointer text-[10px] font-mono text-slate-400 hover:text-slate-200 flex items-center gap-1"
                  title="Clear hint history and restart at Hint 1"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>Reset Hints</span>
                </button>
              </div>
            </div>

            {/* Stacked Hint History (Older hints stay visible) */}
            <div className="space-y-3">
              {hintHistory.map((item) => (
                <div
                  key={item.level}
                  className="p-3.5 rounded-lg border border-cyan-900/30 bg-cyan-950/10 space-y-2"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono font-semibold text-cyan-400 text-[11px]">
                      Hint Level {item.level}
                      {item.level === 1 && " — Conceptual Direction"}
                      {item.level === 2 && " — State Tracking Condition"}
                      {item.level === 3 && " — Concrete Debugging Clue"}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500">
                      {item.timestamp}
                    </span>
                  </div>

                  <MarkdownRenderer content={item.content} />
                </div>
              ))}
            </div>

            {/* Next hint button inside panel */}
            {hintHistory.length < 3 && (
              <div className="pt-2 text-center">
                <button
                  type="button"
                  onClick={handleGetHint}
                  disabled={isAnyLoading}
                  className="cursor-pointer inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-950/60 hover:bg-cyan-900/60 border border-cyan-800/60 text-cyan-300 text-xs font-mono transition-colors"
                >
                  <Lightbulb className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Request Hint {hintHistory.length + 1} (More Specific)</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Safety Notice Footer */}
      <div className="px-4 py-2 bg-slate-950 border-t border-slate-800/80 text-[10px] font-mono text-slate-500 flex items-center justify-between">
        <span className="truncate">
          AI generated. Scoring and test results remain 100% deterministic.
        </span>
        <span className="text-slate-600 hidden sm:inline shrink-0 ml-2">
          Safety Delimited
        </span>
      </div>
    </div>
  );
}
