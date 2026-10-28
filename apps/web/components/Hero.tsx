"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";
import { AnimatedSection } from "./AnimatedSection";

export function Hero() {
  return (
    <section className="relative pt-20 pb-24 sm:pt-28 sm:pb-32 lg:pt-36 lg:pb-40 overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[500px] bg-emerald-500/5 blur-[150px] rounded-full" />
        <div className="absolute top-1/4 right-1/4 w-[400px] h-[300px] bg-cyan-500/3 blur-[120px] rounded-full" />
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-slate-800 to-transparent" />
      </div>

      {/* Grid overlay */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center">
          {/* Category Pill */}
          <AnimatedSection animation="fade-in" delay={0}>
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-medium bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 mb-8">
              <Sparkles className="w-3.5 h-3.5" />
              <span>AI-Powered Coding Interview Practice</span>
            </div>
          </AnimatedSection>

          {/* Headline */}
          <AnimatedSection animation="fade-up" delay={100}>
            <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight text-slate-100 max-w-5xl mx-auto leading-[1.1]">
              Train Your Mind.{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
                Master the Code.
              </span>
            </h1>
          </AnimatedSection>

          {/* Supporting text */}
          <AnimatedSection animation="fade-up" delay={200}>
            <p className="mt-6 text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
              Practice coding interviews, run real tests, get AI-powered hints,
              and understand your mistakes — all in one focused workspace.
            </p>
          </AnimatedSection>

          {/* CTA Buttons */}
          <AnimatedSection animation="fade-up" delay={300}>
            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/challenges"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-base transition-all shadow-[0_0_30px_rgba(16,185,129,0.3)] hover:shadow-[0_0_40px_rgba(16,185,129,0.45)] active:scale-[0.98]"
              >
                <span>Start Practicing</span>
                <ArrowRight className="w-4 h-4" />
              </Link>

              <Link
                href="/#features"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl bg-slate-900/80 hover:bg-slate-800/80 border border-slate-700/60 text-slate-200 hover:text-white font-medium text-base transition-all"
              >
                <span>Explore Features</span>
              </Link>
            </div>
          </AnimatedSection>

          {/* Code editor preview mockup */}
          <AnimatedSection animation="scale-in" delay={500}>
            <div className="mt-16 max-w-4xl mx-auto">
              <div className="rounded-xl border border-slate-800 bg-[#0a0f1a] shadow-2xl shadow-black/40 overflow-hidden">
                {/* Editor title bar */}
                <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900/80 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1.5">
                      <div className="w-3 h-3 rounded-full bg-rose-500/80" />
                      <div className="w-3 h-3 rounded-full bg-amber-500/80" />
                      <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
                    </div>
                    <span className="ml-3 text-xs text-slate-400 font-mono">
                      deduplicator.ts — AI Coding Gym
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-[11px] text-slate-500 font-mono">
                    <span className="text-emerald-400">● Tests: 12/14 passing</span>
                    <span>TypeScript</span>
                  </div>
                </div>
                {/* Code content */}
                <div className="p-5 font-mono text-[13px] leading-relaxed text-slate-300 overflow-x-auto">
                  <div className="space-y-0.5">
                    <div>
                      <span className="text-slate-500 select-none mr-4 inline-block w-6 text-right">1</span>
                      <span className="text-purple-400">import</span>{" "}
                      <span className="text-slate-200">{"{ fetchFromDatabase }"}</span>{" "}
                      <span className="text-purple-400">from</span>{" "}
                      <span className="text-emerald-300">&quot;./db&quot;</span>
                      <span className="text-slate-400">;</span>
                    </div>
                    <div>
                      <span className="text-slate-500 select-none mr-4 inline-block w-6 text-right">2</span>
                    </div>
                    <div>
                      <span className="text-slate-500 select-none mr-4 inline-block w-6 text-right">3</span>
                      <span className="text-slate-500">{"// Map storing in-flight promises"}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 select-none mr-4 inline-block w-6 text-right">4</span>
                      <span className="text-purple-400">const</span>{" "}
                      <span className="text-cyan-300">pendingPromises</span>{" "}
                      <span className="text-slate-400">=</span>{" "}
                      <span className="text-purple-400">new</span>{" "}
                      <span className="text-amber-300">Map</span>
                      <span className="text-slate-400">{"<"}</span>
                      <span className="text-amber-300">string</span>
                      <span className="text-slate-400">{", "}</span>
                      <span className="text-amber-300">Promise</span>
                      <span className="text-slate-400">{"<"}</span>
                      <span className="text-amber-300">unknown</span>
                      <span className="text-slate-400">{">>"}()</span>
                      <span className="text-slate-400">;</span>
                    </div>
                    <div>
                      <span className="text-slate-500 select-none mr-4 inline-block w-6 text-right">5</span>
                    </div>
                    <div>
                      <span className="text-slate-500 select-none mr-4 inline-block w-6 text-right">6</span>
                      <span className="text-purple-400">export async function</span>{" "}
                      <span className="text-sky-300">fetchWithDedup</span>
                      <span className="text-slate-400">{"<"}</span>
                      <span className="text-amber-300">T</span>
                      <span className="text-slate-400">{">"}</span>
                      <span className="text-slate-400">(</span>
                      <span className="text-orange-300">key</span>
                      <span className="text-slate-400">:</span>{" "}
                      <span className="text-amber-300">string</span>
                      <span className="text-slate-400">)</span>{" "}
                      <span className="text-slate-400">{"{"}</span>
                    </div>
                    <div className="bg-rose-500/5 border-l-2 border-rose-500/60 pl-1">
                      <span className="text-slate-500 select-none mr-4 inline-block w-6 text-right">7</span>
                      {"  "}
                      <span className="text-slate-500">{"// ⚠️ BUG: Race condition here"}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 select-none mr-4 inline-block w-6 text-right">8</span>
                      {"  "}
                      <span className="text-purple-400">const</span>{" "}
                      <span className="text-cyan-300">existing</span>{" "}
                      <span className="text-slate-400">=</span>{" "}
                      <span className="text-cyan-300">pendingPromises</span>
                      <span className="text-slate-400">.</span>
                      <span className="text-sky-300">get</span>
                      <span className="text-slate-400">(</span>
                      <span className="text-orange-300">key</span>
                      <span className="text-slate-400">);</span>
                    </div>
                    <div>
                      <span className="text-slate-500 select-none mr-4 inline-block w-6 text-right">9</span>
                      {"  "}
                      <span className="text-purple-400">if</span>{" "}
                      <span className="text-slate-400">(</span>
                      <span className="text-cyan-300">existing</span>
                      <span className="text-slate-400">)</span>{" "}
                      <span className="text-purple-400">return</span>{" "}
                      <span className="text-cyan-300">existing</span>
                      <span className="text-slate-400">;</span>
                    </div>
                  </div>
                </div>
                {/* Bottom bar */}
                <div className="flex items-center justify-between px-4 py-2 bg-slate-900/60 border-t border-slate-800 text-[11px] font-mono text-slate-500">
                  <div className="flex items-center gap-3">
                    <span className="text-emerald-400">AI Hint Available</span>
                    <span>Ln 7, Col 4</span>
                  </div>
                  <span>Product Preview</span>
                </div>
              </div>
            </div>
          </AnimatedSection>
        </div>
      </div>
    </section>
  );
}
