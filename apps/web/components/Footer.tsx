"use client";

import React, { useSyncExternalStore } from "react";
import Link from "next/link";
import { Terminal } from "lucide-react";

const emptySubscribe = () => () => {};
const getYearSnapshot = () => new Date().getFullYear();
const getYearServerSnapshot = () => 2026;

export function Footer() {
  const currentYear = useSyncExternalStore(
    emptySubscribe,
    getYearSnapshot,
    getYearServerSnapshot
  );

  const productLinks = [
    { label: "Challenges Catalog", href: "/challenges" },
    { label: "Features", href: "/#features" },
    { label: "How It Works", href: "/#how-it-works" },
    { label: "Challenge Preview", href: "/#preview" },
  ];

  const practiceLinks = [
    { label: "Start Practicing", href: "/challenges" },
    { label: "AI Hints", href: "/#features" },
    { label: "Solution Review", href: "/#features" },
  ];

  const accountLinks = [
    { label: "Dashboard", href: "/progress" },
    { label: "Account Settings", href: "/account" },
    { label: "Log In", href: "/login" },
    { label: "Sign Up", href: "/signup" },
  ];

  return (
    <footer className="w-full border-t border-slate-800/60 bg-[#060a12]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Main footer grid */}
        <div className="py-12 sm:py-16 grid grid-cols-2 md:grid-cols-4 gap-8 lg:gap-12">
          {/* Brand column */}
          <div className="col-span-2 md:col-span-1">
            <Link href="/" className="inline-flex items-center gap-2.5 mb-4">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                <Terminal className="w-4 h-4" />
              </div>
              <span className="font-semibold text-slate-100 text-sm">
                AI Coding Gym
              </span>
            </Link>
            <p className="text-xs text-slate-400 leading-relaxed max-w-xs">
              Practice coding interviews with AI-powered hints, real test
              execution, and deterministic scoring. Built with Next.js, FastAPI,
              and PostgreSQL.
            </p>
          </div>

          {/* Product links */}
          <div>
            <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider mb-4">
              Product
            </h3>
            <ul className="space-y-2.5">
              {productLinks.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-slate-400 hover:text-slate-200 transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Practice links */}
          <div>
            <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider mb-4">
              Practice
            </h3>
            <ul className="space-y-2.5">
              {practiceLinks.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-slate-400 hover:text-slate-200 transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Account links */}
          <div>
            <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider mb-4">
              Account
            </h3>
            <ul className="space-y-2.5">
              {accountLinks.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-slate-400 hover:text-slate-200 transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="py-6 border-t border-slate-800/60 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
          <span>© {currentYear} AI Coding Gym. All rights reserved.</span>
          <span className="font-mono">
            Built with Next.js, FastAPI & PostgreSQL
          </span>
        </div>
      </div>
    </footer>
  );
}
