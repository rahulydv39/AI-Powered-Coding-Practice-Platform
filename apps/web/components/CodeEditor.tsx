"use client";

import React, { useRef } from "react";
import { RotateCcw, FileCode2 } from "lucide-react";

interface CodeEditorProps {
  code: string;
  onChange: (value: string) => void;
  onReset: () => void;
  onRunTests?: () => void;
  onSubmitSolution?: () => void;
  disabled?: boolean;
}

export function CodeEditor({
  code,
  onChange,
  onReset,
  onRunTests,
  onSubmitSolution,
  disabled = false,
}: CodeEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lineNumbersRef = useRef<HTMLDivElement>(null);

  const lines = code.split("\n");
  const lineCount = lines.length;

  // Keep line numbers scrolled in sync with textarea
  const handleScroll = () => {
    if (textareaRef.current && lineNumbersRef.current) {
      lineNumbersRef.current.scrollTop = textareaRef.current.scrollTop;
    }
  };

  // Keyboard navigation: Handle Tab and Run/Submit shortcuts
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Cmd/Ctrl + Enter (Run Tests) and Cmd/Ctrl + Shift + Enter (Submit Solution)
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      e.stopPropagation();
      if (disabled) return;
      if (e.shiftKey) {
        if (onSubmitSolution) onSubmitSolution();
      } else {
        if (onRunTests) onRunTests();
      }
      return;
    }

    if (e.key === "Tab") {
      e.preventDefault();
      const target = e.currentTarget;
      const start = target.selectionStart;
      const end = target.selectionEnd;

      if (e.shiftKey) {
        // Shift+Tab: Dedent if preceding 4 spaces or single tab
        const beforeCursor = code.substring(0, start);
        if (beforeCursor.endsWith("    ")) {
          const updated = code.substring(0, start - 4) + code.substring(end);
          onChange(updated);
          requestAnimationFrame(() => {
            target.selectionStart = target.selectionEnd = start - 4;
          });
        }
      } else {
        // Tab: Insert 4 spaces
        const updated = code.substring(0, start) + "    " + code.substring(end);
        onChange(updated);
        requestAnimationFrame(() => {
          target.selectionStart = target.selectionEnd = start + 4;
        });
      }
    }
  };

  return (
    <div className="flex flex-col rounded-xl border border-slate-800 bg-[#070b12] overflow-hidden shadow-lg">
      {/* Editor Header Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900/80 border-b border-slate-800 text-xs text-slate-300">
        <div className="flex items-center gap-2">
          <FileCode2 className="w-4 h-4 text-emerald-400" />
          <span className="font-mono font-medium text-slate-200">
            solution.py
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/60">
            Python 3.12
          </span>
        </div>

        <div className="flex items-center gap-3">
          <span className="font-mono text-[11px] text-slate-500 hidden sm:inline">
            {lineCount} lines • {code.length} chars
          </span>

          <button
            type="button"
            onClick={onReset}
            disabled={disabled}
            className="cursor-pointer inline-flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-mono rounded bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed border border-slate-700/50"
            title="Reset code to original starter state"
          >
            <RotateCcw className="w-3 h-3 text-slate-400" />
            <span>Reset Code</span>
          </button>
        </div>
      </div>

      {/* Editor Body with Synchronized Line Numbers */}
      <div className="relative flex flex-1 min-h-[380px] max-h-[550px] font-mono text-xs sm:text-sm">
        {/* Line Numbers Column */}
        <div
          ref={lineNumbersRef}
          aria-hidden="true"
          className="select-none py-3 px-3 bg-[#05080e] border-r border-slate-800/80 text-slate-600 text-right overflow-hidden leading-relaxed shrink-0 w-12 font-mono"
        >
          {Array.from({ length: Math.max(lineCount, 15) }).map((_, i) => (
            <div key={i}>{i + 1}</div>
          ))}
        </div>

        {/* Textarea Input */}
        <textarea
          ref={textareaRef}
          value={code}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onScroll={handleScroll}
          disabled={disabled}
          spellCheck={false}
          autoCapitalize="off"
          autoComplete="off"
          autoCorrect="off"
          aria-label="Python Solution Code Editor"
          className="flex-1 w-full p-3 bg-transparent text-slate-100 placeholder-slate-600 outline-none resize-none overflow-auto whitespace-pre leading-relaxed font-mono disabled:opacity-60"
        />
      </div>

      {/* Editor Footer / Hotkeys info */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-[#05080e] border-t border-slate-800/80 text-[11px] font-mono text-slate-500">
        <div className="flex items-center gap-2">
          <span>Tab: 4 spaces</span>
          <span className="text-slate-700 hidden sm:inline">•</span>
          <span className="hidden sm:inline">solution.py</span>
        </div>
        <div className="flex items-center gap-2 text-[10px]">
          <span className="hidden sm:inline text-slate-500">Shortcuts:</span>
          <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400">
            ⌘↵ Run
          </span>
          <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400">
            ⇧⌘↵ Submit
          </span>
        </div>
      </div>
    </div>
  );
}
