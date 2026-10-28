"use client";

import React from "react";
import { X, CheckCircle, Cpu } from "lucide-react";

interface PracticeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function PracticeModal({ isOpen, onClose }: PracticeModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg rounded-xl border border-slate-700 bg-[#0d1322] p-6 shadow-2xl">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="cursor-pointer absolute top-4 right-4 p-1 rounded-md text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
          aria-label="Close modal"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-slate-100">
              Phase 1 MVP Scope Notice
            </h3>
            <p className="text-xs text-slate-400 font-mono">
              AI Coding Gym — Project Foundation
            </p>
          </div>
        </div>

        {/* Modal Content */}
        <div className="text-xs sm:text-sm text-slate-300 space-y-3 leading-relaxed mb-6">
          <p>
            You are viewing the <strong className="text-emerald-400">Phase 1 Foundation</strong>.
            This milestone establishes the verified frontend UI, the FastAPI backend,
            CORS routing, structured logging, and database connection architecture.
          </p>

          <div className="rounded-lg bg-slate-900/80 border border-slate-800 p-3.5 space-y-2">
            <div className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono">
              Current Phase Deliverables:
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-300">
              <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>Next.js App Router with responsive dark developer theme</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-300">
              <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>FastAPI REST service with GET /health and /api/v1/health</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-300">
              <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>SQLAlchemy 2.x & Alembic database configuration</span>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-300">
              <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>Automated pytest suite verifying API & CORS behavior</span>
            </div>
          </div>

          <p className="text-xs text-slate-400">
            Interactive code execution, Monaco editor integration, and LLM pairing providers
            are scheduled for <strong>Phase 2</strong> in an isolated sandbox service.
          </p>
        </div>

        {/* Modal Footer / Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-end gap-3 pt-3 border-t border-slate-800">
          <button
            onClick={onClose}
            className="cursor-pointer w-full sm:w-auto px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-medium text-xs sm:text-sm transition-colors text-center"
          >
            Understood & Continue
          </button>
        </div>
      </div>
    </div>
  );
}
