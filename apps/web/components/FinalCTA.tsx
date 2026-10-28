import React from "react";
import Link from "next/link";
import { ArrowRight, Terminal } from "lucide-react";
import { AnimatedSection } from "./AnimatedSection";

export function FinalCTA() {
  return (
    <section className="relative py-24 sm:py-32">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-emerald-500/5 blur-[150px] rounded-full" />
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <AnimatedSection animation="scale-in">
          <div className="relative rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900/80 to-[#0a0f1a] p-10 sm:p-14 text-center overflow-hidden">
            {/* Subtle pattern */}
            <div
              className="absolute inset-0 opacity-[0.03] pointer-events-none"
              style={{
                backgroundImage:
                  "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.3) 1px, transparent 0)",
                backgroundSize: "24px 24px",
              }}
            />

            <div className="relative z-10">
              <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mx-auto mb-6">
                <Terminal className="w-7 h-7" />
              </div>

              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-100 mb-4">
                Ready to level up?
              </h2>
              <p className="text-base text-slate-400 max-w-lg mx-auto mb-8">
                Start practicing real coding interview challenges with AI-powered
                assistance. No setup required — jump straight into the editor.
              </p>

              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link
                  href="/challenges"
                  className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-base transition-all shadow-[0_0_30px_rgba(16,185,129,0.3)] hover:shadow-[0_0_40px_rgba(16,185,129,0.45)] active:scale-[0.98]"
                >
                  <span>Start Practicing</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
                <Link
                  href="/signup"
                  className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl border border-slate-700/60 bg-slate-900/60 text-slate-200 hover:text-white hover:bg-slate-800/60 font-medium text-base transition-all"
                >
                  Create Free Account
                </Link>
              </div>
            </div>
          </div>
        </AnimatedSection>
      </div>
    </section>
  );
}
