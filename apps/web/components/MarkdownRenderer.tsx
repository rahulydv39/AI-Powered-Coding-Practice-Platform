"use client";

import React from "react";

interface MarkdownRendererProps {
  content: string;
}

/**
 * Safe, zero-dependency Markdown renderer using native React elements.
 *
 * SECURITY:
 * Never uses `dangerouslySetInnerHTML`. All strings are rendered as standard
 * React text nodes, preventing XSS and HTML injection vulnerabilities.
 */
export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  if (!content) return null;

  // Split content into code blocks vs standard text blocks
  const sections = content.split(/(```[\s\S]*?```)/g);

  return (
    <div className="space-y-3 text-xs sm:text-sm text-slate-300 leading-relaxed font-sans">
      {sections.map((section, secIdx) => {
        // Code Block
        if (section.startsWith("```") && section.endsWith("```")) {
          const firstLineEnd = section.indexOf("\n");
          const lang = section.slice(3, firstLineEnd).trim();
          const codeBody = section.slice(firstLineEnd + 1, -3);

          return (
            <div
              key={secIdx}
              className="my-2.5 rounded-lg border border-slate-800 bg-[#05080e] overflow-hidden font-mono"
            >
              {lang && (
                <div className="px-3 py-1 bg-slate-900/80 border-b border-slate-800 text-[10px] uppercase tracking-wider text-slate-400">
                  {lang}
                </div>
              )}
              <pre className="p-3 text-[11px] sm:text-xs text-slate-200 overflow-x-auto leading-relaxed">
                <code>{codeBody}</code>
              </pre>
            </div>
          );
        }

        // Standard text: process lines (headings, lists, paragraphs)
        const lines = section.split("\n");
        return (
          <React.Fragment key={secIdx}>
            {lines.map((line, lineIdx) => {
              const trimmed = line.trim();

              // Empty line
              if (!trimmed) {
                return null;
              }

              // H1 Heading
              if (trimmed.startsWith("# ")) {
                return (
                  <h3
                    key={lineIdx}
                    className="text-base font-bold text-slate-100 mt-3 mb-1 text-emerald-400"
                  >
                    {renderInline(trimmed.slice(2))}
                  </h3>
                );
              }

              // H2 Heading
              if (trimmed.startsWith("## ")) {
                return (
                  <h4
                    key={lineIdx}
                    className="text-sm font-semibold text-slate-100 mt-2.5 mb-1 text-emerald-300"
                  >
                    {renderInline(trimmed.slice(3))}
                  </h4>
                );
              }

              // H3 Heading
              if (trimmed.startsWith("### ")) {
                return (
                  <h5
                    key={lineIdx}
                    className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono mt-2 mb-1 text-cyan-300"
                  >
                    {renderInline(trimmed.slice(4))}
                  </h5>
                );
              }

              // H4 Heading
              if (trimmed.startsWith("#### ")) {
                return (
                  <h6
                    key={lineIdx}
                    className="text-xs font-semibold text-slate-300 font-mono mt-2.5 mb-1 text-sky-400"
                  >
                    {renderInline(trimmed.slice(5))}
                  </h6>
                );
              }

              // Bullet list item (- or *)
              if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
                return (
                  <div
                    key={lineIdx}
                    className="flex items-start gap-2 ml-2 my-1 text-slate-300"
                  >
                    <span className="text-emerald-400 mt-0.5">•</span>
                    <span>{renderInline(trimmed.slice(2))}</span>
                  </div>
                );
              }

              // Numbered list item
              const numMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
              if (numMatch) {
                return (
                  <div
                    key={lineIdx}
                    className="flex items-start gap-2 ml-2 my-1 text-slate-300"
                  >
                    <span className="font-mono text-emerald-400 font-semibold shrink-0">
                      {numMatch[1]}.
                    </span>
                    <span>{renderInline(numMatch[2])}</span>
                  </div>
                );
              }

              // Standard Paragraph
              return (
                <p key={lineIdx} className="my-1.5 text-slate-300">
                  {renderInline(line)}
                </p>
              );
            })}
          </React.Fragment>
        );
      })}
    </div>
  );
}

/**
 * Render inline tokens: `code`, **bold**, *italic* safely as React nodes.
 */
function renderInline(text: string): React.ReactNode {
  // Regex splitting on code `...`, bold **...**, and italic *...*
  const tokens = text.split(/(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g);

  return tokens.map((token, idx) => {
    // Inline code
    if (token.startsWith("`") && token.endsWith("`") && token.length > 2) {
      return (
        <code
          key={idx}
          className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-[11px] font-mono text-emerald-300 mx-0.5"
        >
          {token.slice(1, -1)}
        </code>
      );
    }

    // Bold
    if (token.startsWith("**") && token.endsWith("**") && token.length > 4) {
      return (
        <strong key={idx} className="font-semibold text-slate-100">
          {token.slice(2, -2)}
        </strong>
      );
    }

    // Italic
    if (token.startsWith("*") && token.endsWith("*") && token.length > 2) {
      return (
        <em key={idx} className="italic text-slate-200">
          {token.slice(1, -1)}
        </em>
      );
    }

    // Plain text
    return token;
  });
}
