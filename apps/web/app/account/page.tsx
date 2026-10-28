"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  CheckCircle2,
  ExternalLink,
  Info,
  LogOut,
  Mail,
  Shield,
} from "lucide-react";
import { GithubIcon } from "@/components/icons";
import { useAuth } from "@/lib/auth-context";
import { getLeetCodeStatus } from "@/lib/api";

export default function AccountPage() {
  const router = useRouter();
  const { user, loading, logout } = useAuth();
  const [isSigningOut, setIsSigningOut] = useState(false);
  const [leetCodeInfo, setLeetCodeInfo] = useState<{
    supports_oauth_sign_in: boolean;
    message: string;
  } | null>(null);

  useEffect(() => {
    if (!loading && !user && !isSigningOut) {
      router.push("/login?next=/account");
    }
  }, [user, loading, router, isSigningOut]);

  useEffect(() => {
    async function loadLeetCode() {
      const info = await getLeetCodeStatus();
      setLeetCodeInfo(info);
    }
    loadLeetCode();
  }, []);

  const handleSignOut = async () => {
    setIsSigningOut(true);
    await logout();
    router.push("/");
  };

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#090d16] text-slate-400 font-mono text-xs">
        Loading account profile...
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#090d16] text-slate-100 font-sans">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-[#090d16]/90 sticky top-0 z-40 backdrop-blur-md">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link
            href="/"
            className="flex items-center gap-2 text-xs font-mono text-slate-400 hover:text-slate-100 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Gym</span>
          </Link>
          <div className="flex items-center gap-3">
            <Link
              href="/progress"
              className="text-xs font-mono text-emerald-400 hover:text-emerald-300 transition-colors"
            >
              My Progress &rarr;
            </Link>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-4xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Student Profile & Settings</h1>
          <p className="text-xs text-slate-400 mt-1">
            Manage your credentials, external connected accounts, and platform security.
          </p>
        </div>

        {/* Profile Card */}
        <section aria-labelledby="profile-heading" className="rounded-xl border border-slate-800 bg-[#0b0f19] p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold font-mono text-lg">
                {user.email[0].toUpperCase()}
              </div>
              <div>
                <h2 id="profile-heading" className="text-base font-semibold text-slate-100">
                  {user.full_name || "Engineering Candidate"}
                </h2>
                <div className="text-xs text-slate-400 font-mono flex items-center gap-1.5 mt-0.5">
                  <Mail className="w-3.5 h-3.5" />
                  <span>{user.email}</span>
                </div>
              </div>
            </div>

            <button
              onClick={handleSignOut}
              className="cursor-pointer inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-rose-900/40 bg-rose-950/20 text-rose-300 hover:bg-rose-900/30 text-xs font-mono transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out</span>
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
            <div className="p-3.5 rounded-lg border border-slate-800/80 bg-slate-900/40">
              <span className="text-[10px] text-slate-500 uppercase block">Account ID</span>
              <span className="text-slate-200 mt-1 block truncate">{user.id}</span>
            </div>
            <div className="p-3.5 rounded-lg border border-slate-800/80 bg-slate-900/40">
              <span className="text-[10px] text-slate-500 uppercase block">Member Since</span>
              <span className="text-slate-200 mt-1 block">
                {new Date(user.created_at).toLocaleDateString([], {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </span>
            </div>
          </div>
        </section>

        {/* Linked External Identities */}
        <section aria-labelledby="external-accounts-heading" className="rounded-xl border border-slate-800 bg-[#0b0f19] p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 id="external-accounts-heading" className="text-sm font-semibold text-slate-100">
                Connected Social Identities
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Sign in with verified external accounts linked to this profile.
              </p>
            </div>
            <Shield className="w-4 h-4 text-emerald-400" />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
            {/* Google */}
            <div className="p-3.5 rounded-lg border border-slate-800 bg-slate-900/40 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
                  <path
                    fill="#EA4335"
                    d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.7 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.3 9 5 12 5z"
                  />
                  <path
                    fill="#4285F4"
                    d="M23.5 12.3c0-.8-.1-1.7-.2-2.3H12v4.6h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.9z"
                  />
                </svg>
                <span className="text-xs text-slate-200">Google</span>
              </div>
              {user.linked_providers.includes("google") ? (
                <span className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>Linked</span>
                </span>
              ) : (
                <span className="text-[11px] font-mono text-slate-500">Not linked</span>
              )}
            </div>

            {/* GitHub */}
            <div className="p-3.5 rounded-lg border border-slate-800 bg-slate-900/40 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <GithubIcon className="w-4 h-4 text-slate-300 shrink-0" />
                <span className="text-xs text-slate-200">GitHub</span>
              </div>
              {user.linked_providers.includes("github") ? (
                <span className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>Linked</span>
                </span>
              ) : (
                <span className="text-[11px] font-mono text-slate-500">Not linked</span>
              )}
            </div>

            {/* Apple */}
            <div className="p-3.5 rounded-lg border border-slate-800 bg-slate-900/40 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <svg className="w-4 h-4 fill-current text-slate-300 shrink-0" viewBox="0 0 24 24">
                  <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 6.38c.62-.75 1.04-1.8 0.93-2.85-.9.04-1.98.6-2.61 1.34-.56.64-1.05 1.71-.92 2.74 1 .08 2.01-.51 2.6-1.23z" />
                </svg>
                <span className="text-xs text-slate-200">Apple</span>
              </div>
              {user.linked_providers.includes("apple") ? (
                <span className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>Linked</span>
                </span>
              ) : (
                <span className="text-[11px] font-mono text-slate-500">Not linked</span>
              )}
            </div>
          </div>
        </section>

        {/* LeetCode External Profile Section */}
        <section aria-labelledby="leetcode-heading" className="rounded-xl border border-slate-800 bg-[#0b0f19] p-6 space-y-3">
          <div className="flex items-center justify-between">
            <h2 id="leetcode-heading" className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <span>External Profile: LeetCode</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-400 border border-slate-700">
                Informational
              </span>
            </h2>
            <ExternalLink className="w-4 h-4 text-slate-500" />
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-4 text-xs text-slate-400 space-y-2">
            <div className="flex items-start gap-2.5 text-slate-300">
              <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
              <p className="leading-relaxed">
                {leetCodeInfo?.message ||
                  "LeetCode does not provide an official public third-party OAuth/OIDC authorization service. Profile linking is supported strictly as a public profile reference and cannot be used for authentication."}
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
