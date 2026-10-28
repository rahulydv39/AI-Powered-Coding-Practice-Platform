"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Clock,
  Compass,
  Layers,
  Play,
  Search,
  Tag,
  Terminal,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { useAuth } from "@/lib/auth-context";
import { getChallengeCatalog } from "@/lib/api";
import { ChallengeCatalogItem } from "@/lib/types";

type DifficultyFilter = "All" | "Easy" | "Medium" | "Hard";

export default function ChallengesCatalogPage() {
  const { user } = useAuth();
  const [challenges, setChallenges] = useState<ChallengeCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDifficulty, setSelectedDifficulty] = useState<DifficultyFilter>("All");

  useEffect(() => {
    let isMounted = true;
    async function loadCatalog() {
      setLoading(true);
      const res = await getChallengeCatalog();
      if (isMounted) {
        if (res.data) {
          setChallenges(res.data);
          setError(null);
        } else {
          setError(res.error || "Failed to load challenges catalog.");
        }
        setLoading(false);
      }
    }
    loadCatalog();
    return () => {
      isMounted = false;
    };
  }, []);

  const filteredChallenges = challenges.filter((c) => {
    // Difficulty filter
    if (selectedDifficulty !== "All" && c.difficulty.toLowerCase() !== selectedDifficulty.toLowerCase()) {
      return false;
    }

    // Search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      const matchTitle = c.title.toLowerCase().includes(q);
      const matchSummary = c.short_summary.toLowerCase().includes(q);
      const matchCategory = c.category.toLowerCase().includes(q);
      const matchTags = c.tags?.some((t) => t.toLowerCase().includes(q));
      return matchTitle || matchSummary || matchCategory || matchTags;
    }

    return true;
  });

  return (
    <div className="min-h-screen flex flex-col bg-[#070b12] text-slate-100">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-14 space-y-10">
        {/* Catalog Hero Banner */}
        <div className="relative rounded-3xl border border-slate-800 bg-gradient-to-b from-[#0b1120] to-[#070b12] p-8 sm:p-12 overflow-hidden shadow-2xl">
          <div className="absolute top-0 right-0 -mr-16 -mt-16 w-80 h-80 rounded-full bg-emerald-500/10 blur-3xl pointer-events-none" />
          <div className="absolute bottom-0 left-1/3 -mb-16 w-60 h-60 rounded-full bg-sky-500/10 blur-3xl pointer-events-none" />

          <div className="relative z-10 max-w-3xl space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 font-mono text-xs">
              <Terminal className="w-3.5 h-3.5" />
              <span>Standard Interview Gym Catalog</span>
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-slate-100">
              Backend & Systems <br className="hidden sm:inline" />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-sky-300 to-indigo-400">
                Coding Interview Challenges
              </span>
            </h1>
            <p className="text-sm sm:text-base text-slate-300 leading-relaxed max-w-2xl">
              Sharpen your engineering instincts with production-grade distributed systems, caching,
              rate limiting, and reliability patterns. Every problem includes isolated Docker test execution,
              deterministic scoring, and multi-provider AI coaching.
            </p>
          </div>
        </div>

        {/* Filter and Search Bar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 p-2 rounded-2xl border border-slate-800 bg-[#0b0f19]">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search challenges by keyword, tag, or concept..."
              className="w-full pl-10 pr-4 py-2 text-xs font-mono bg-slate-900/60 rounded-xl border border-slate-800 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500/60 transition-colors"
            />
          </div>

          {/* Difficulty Filter Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto p-1 bg-slate-900/80 rounded-xl border border-slate-800 font-mono text-xs">
            {(["All", "Easy", "Medium", "Hard"] as DifficultyFilter[]).map((diff) => (
              <button
                key={diff}
                type="button"
                onClick={() => setSelectedDifficulty(diff)}
                className={`cursor-pointer px-3 py-1.5 rounded-lg transition-colors ${
                  selectedDifficulty === diff
                    ? "bg-slate-800 text-slate-100 font-semibold shadow-sm border border-slate-700/60"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
                }`}
              >
                {diff}
              </button>
            ))}
          </div>
        </div>

        {/* Catalog Content Area */}
        {loading ? (
          <div className="py-20 text-center space-y-3">
            <div className="w-10 h-10 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-xs font-mono text-slate-400">Loading interview practice catalog...</p>
          </div>
        ) : error ? (
          <div className="rounded-2xl border border-rose-900/60 bg-rose-950/20 p-8 text-center space-y-4 max-w-md mx-auto">
            <Layers className="w-10 h-10 text-rose-400 mx-auto" />
            <h3 className="text-base font-semibold text-rose-100">Unable to Load Catalog</h3>
            <p className="text-xs text-rose-300 font-mono leading-relaxed">{error}</p>
          </div>
        ) : filteredChallenges.length === 0 ? (
          <div className="py-16 text-center space-y-3 rounded-2xl border border-slate-800/80 bg-[#0b0f19] p-8">
            <Compass className="w-10 h-10 text-slate-500 mx-auto" />
            <h3 className="text-base font-semibold text-slate-200">No challenges matched your query</h3>
            <p className="text-xs text-slate-400 font-mono">
              Try adjusting your search keywords or resetting difficulty filters.
            </p>
            <button
              type="button"
              onClick={() => {
                setSearchQuery("");
                setSelectedDifficulty("All");
              }}
              className="cursor-pointer mt-2 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono transition-colors"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
            {filteredChallenges.map((challenge) => {
              const diffColor =
                challenge.difficulty === "Easy"
                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                  : challenge.difficulty === "Medium"
                  ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
                  : "bg-rose-500/10 border-rose-500/30 text-rose-400";

              const practiceTarget = user
                ? `/challenges/${challenge.id}`
                : `/login?next=/challenges/${challenge.id}`;

              return (
                <div
                  key={challenge.id}
                  className="group rounded-2xl border border-slate-800 bg-[#0b0f19] hover:border-slate-700 p-6 flex flex-col justify-between transition-all duration-200 shadow-xl hover:shadow-2xl"
                >
                  <div className="space-y-4">
                    {/* Header Tags & Metadata */}
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className={`px-2.5 py-0.5 rounded text-[11px] font-mono border ${diffColor}`}>
                          {challenge.difficulty}
                        </span>
                        <span className="text-[11px] font-mono text-slate-400 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded">
                          {challenge.category}
                        </span>
                      </div>
                      <div className="flex items-center gap-1 text-[11px] font-mono text-slate-400">
                        <Clock className="w-3.5 h-3.5 text-slate-500" />
                        <span>{challenge.estimated_minutes}m</span>
                      </div>
                    </div>

                    {/* Problem Title & Summary */}
                    <div>
                      <Link
                        href={`/challenges/${challenge.id}`}
                        className="text-lg font-bold text-slate-100 group-hover:text-emerald-400 transition-colors"
                      >
                        {challenge.title}
                      </Link>
                      <p className="text-xs sm:text-sm text-slate-300 mt-2 leading-relaxed">
                        {challenge.short_summary}
                      </p>
                    </div>

                    {/* Tags */}
                    {challenge.tags && challenge.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {challenge.tags.map((tag) => (
                          <span
                            key={tag}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono bg-slate-900/80 border border-slate-800/80 text-slate-400"
                          >
                            <Tag className="w-2.5 h-2.5 text-slate-500" />
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Action Bar */}
                  <div className="pt-6 border-t border-slate-800/80 mt-6 flex items-center justify-between gap-3">
                    <Link
                      href={`/challenges/${challenge.id}`}
                      className="text-xs font-mono text-slate-400 hover:text-slate-200 transition-colors"
                    >
                      View Details
                    </Link>

                    <Link
                      href={practiceTarget}
                      className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs font-mono transition-all shadow-[0_0_12px_rgba(16,185,129,0.2)] hover:shadow-[0_0_18px_rgba(16,185,129,0.35)]"
                    >
                      <Play className="w-3 h-3 fill-current" />
                      <span>Start Practicing</span>
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
