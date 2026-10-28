"use client";

import React, { useEffect, useState } from "react";
import { Check, ChevronDown } from "lucide-react";
import { getAiProviders } from "@/lib/api";
import { AiProviderInfo } from "@/lib/types";

export const LOCAL_STORAGE_PROVIDER_KEY = "ai_coding_gym_ai_provider";

interface AiProviderSelectorProps {
  selectedProvider: string;
  onProviderChange: (providerId: string) => void;
  className?: string;
  compact?: boolean;
}

export function AiProviderSelector({
  selectedProvider,
  onProviderChange,
  className = "",
  compact = false,
}: AiProviderSelectorProps) {
  const [providers, setProviders] = useState<AiProviderInfo[]>([
    {
      id: "gemini",
      name: "Google Gemini",
      model: "gemini-2.5-flash",
      configured: true,
    },
    {
      id: "claude",
      name: "Anthropic Claude",
      model: "claude-3-5-sonnet-20241022",
      configured: false,
    },
    {
      id: "openai",
      name: "OpenAI",
      model: "gpt-4o-mini",
      configured: false,
    },
  ]);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function loadProviders() {
      const res = await getAiProviders();
      if (isMounted && res.data?.providers) {
        setProviders(res.data.providers);
      }
    }
    loadProviders();
    return () => {
      isMounted = false;
    };
  }, []);

  const activeProvider =
    providers.find((p) => p.id === selectedProvider) || providers[0];

  const handleSelect = (id: string) => {
    onProviderChange(id);
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem(LOCAL_STORAGE_PROVIDER_KEY, id);
      } catch {
        // Storage restricted
      }
    }
    setIsOpen(false);
  };

  return (
    <div className={`relative inline-block text-left ${className}`}>
      <label
        htmlFor="ai-provider-button"
        className="block text-[10px] uppercase tracking-wider font-mono text-slate-400 mb-1"
      >
        AI Model Provider
      </label>

      {/* Selector Trigger Button */}
      <button
        id="ai-provider-button"
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={`Select AI Provider. Currently using ${activeProvider.name} (${activeProvider.model})`}
        className={`cursor-pointer inline-flex items-center justify-between gap-2.5 px-3 py-1.5 rounded-lg border text-xs font-mono transition-all focus:outline-none focus:ring-2 focus:ring-cyan-500/50 ${
          activeProvider.configured
            ? "bg-slate-900 border-slate-700/80 hover:border-cyan-500/50 text-slate-200"
            : "bg-slate-900 border-amber-800/60 hover:border-amber-600/80 text-amber-200"
        } ${compact ? "text-[11px] py-1 px-2.5" : ""}`}
      >
        <div className="flex items-center gap-2 truncate">
          <div
            className={`w-2 h-2 rounded-full ${
              activeProvider.configured
                ? "bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.5)]"
                : "bg-amber-400"
            }`}
          />
          <span className="font-medium text-slate-100">{activeProvider.name}</span>
          <span className="text-[10px] text-slate-400 hidden sm:inline">
            ({activeProvider.model})
          </span>
        </div>
        <ChevronDown
          className={`w-3.5 h-3.5 text-slate-400 transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Accessible Dropdown Menu */}
      {isOpen && (
        <>
          {/* Backdrop click dismiss */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
            aria-hidden="true"
          />

          <div
            role="listbox"
            tabIndex={-1}
            className="absolute left-0 mt-1.5 z-50 w-72 rounded-xl border border-slate-800 bg-[#0c1220] shadow-2xl p-1.5 space-y-1 font-mono text-xs focus:outline-none"
            onKeyDown={(e) => {
              if (e.key === "Escape") setIsOpen(false);
            }}
          >
            <div className="px-2.5 py-1.5 text-[10px] text-slate-400 border-b border-slate-800/80 flex items-center justify-between">
              <span>SELECT PROVIDER</span>
              <span className="text-slate-500">Local Preference</span>
            </div>

            {providers.map((p) => {
              const isSelected = p.id === activeProvider.id;
              return (
                <button
                  key={p.id}
                  role="option"
                  aria-selected={isSelected}
                  type="button"
                  onClick={() => handleSelect(p.id)}
                  className={`cursor-pointer w-full text-left px-3 py-2 rounded-lg flex items-start justify-between gap-2 transition-all ${
                    isSelected
                      ? "bg-cyan-950/40 border border-cyan-800/50 text-cyan-200"
                      : "hover:bg-slate-800/60 text-slate-300 border border-transparent"
                  }`}
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-1.5">
                      <span className="font-semibold text-slate-100">{p.name}</span>
                      {p.configured ? (
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                          Ready
                        </span>
                      ) : (
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400">
                          Key Needed
                        </span>
                      )}
                    </div>
                    <div className="text-[10px] text-slate-400">{p.model}</div>
                  </div>

                  {isSelected && (
                    <Check className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                  )}
                </button>
              );
            })}

            <div className="pt-1.5 border-t border-slate-800/80 px-2 text-[10px] text-slate-500 leading-relaxed">
              Keys are configured in backend <code className="text-slate-400">.env</code>. No secrets stored in browser.
            </div>
          </div>
        </>
      )}
    </div>
  );
}
