import React from "react";
import { Server, Database, ShieldCheck, Box, Bot, CheckCircle, Clock } from "lucide-react";

export function ArchitectureSection() {
  return (
    <section id="architecture" className="py-16 sm:py-24 border-t border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100">
            System Architecture Overview
          </h2>
          <p className="mt-3 text-sm sm:text-base text-slate-400">
            Cleanly decoupled services designed for security, scalability, and deterministic scoring.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Phase 1: Implemented Foundation */}
          <div className="rounded-xl bg-slate-900/40 border border-slate-800 p-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-medium">
                Phase 1: Implemented Foundation
              </span>
              <CheckCircle className="w-4 h-4 text-emerald-400" />
            </div>

            <h3 className="text-base font-semibold text-slate-100 mb-3">
              Core Application Monorepo
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-6">
              Production-ready frontend and API layers with strict typing, configuration isolation, and automated tests.
            </p>

            <div className="space-y-3 font-mono text-xs">
              <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                <Box className="w-4 h-4 text-cyan-400 shrink-0" />
                <div>
                  <span className="text-slate-200 font-semibold block">Next.js App Router</span>
                  <span className="text-slate-400 text-[11px]">Strict TypeScript, Tailwind CSS, responsive dark UI</span>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                <Server className="w-4 h-4 text-emerald-400 shrink-0" />
                <div>
                  <span className="text-slate-200 font-semibold block">FastAPI REST Backend</span>
                  <span className="text-slate-400 text-[11px]">Pydantic v2 schemas, CORS, structured logging, health checks</span>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-950/60 border border-slate-800/80">
                <Database className="w-4 h-4 text-indigo-400 shrink-0" />
                <div>
                  <span className="text-slate-200 font-semibold block">PostgreSQL + SQLAlchemy 2.x</span>
                  <span className="text-slate-400 text-[11px]">Async connection pool & Alembic migration harness</span>
                </div>
              </div>
            </div>
          </div>

          {/* Planned Future Architecture */}
          <div className="rounded-xl bg-slate-900/20 border border-slate-800/60 border-dashed p-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-400 font-medium">
                Planned Future Phases
              </span>
              <Clock className="w-4 h-4 text-slate-500" />
            </div>

            <h3 className="text-base font-semibold text-slate-200 mb-3">
              Isolated Execution & AI Pipeline
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-6">
              Specialized services scheduled for upcoming phases to ensure sandboxed safety and deterministic evaluation.
            </p>

            <div className="space-y-3 font-mono text-xs">
              <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-950/40 border border-slate-800/60 opacity-80">
                <ShieldCheck className="w-4 h-4 text-amber-400 shrink-0" />
                <div>
                  <span className="text-slate-300 font-semibold block">Hardened Sandbox Runner (Planned)</span>
                  <span className="text-slate-500 text-[11px]">Air-gapped container execution preventing host compromise</span>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-950/40 border border-slate-800/60 opacity-80">
                <Bot className="w-4 h-4 text-cyan-400 shrink-0" />
                <div>
                  <span className="text-slate-300 font-semibold block">AI Provider Adapter (Planned)</span>
                  <span className="text-slate-500 text-[11px]">Pluggable LLM interface with permission gating & token auditing</span>
                </div>
              </div>

              <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-950/40 border border-slate-800/60 opacity-80">
                <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
                <div>
                  <span className="text-slate-300 font-semibold block">Deterministic Rubric Scorer (Planned)</span>
                  <span className="text-slate-500 text-[11px]">Automated evaluation based on test passes and prompt efficiency</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
