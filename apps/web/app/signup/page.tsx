"use client";

import React, { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  AlertCircle,
  ArrowRight,
  Eye,
  EyeOff,
  Lock,
  Mail,
  Terminal,
  User,
} from "lucide-react";
import { GithubIcon } from "@/components/icons";
import { useAuth } from "@/lib/auth-context";
import { getOAuthProviders } from "@/lib/api";
import { OAuthProviderItem } from "@/lib/types";

function getSafeNextUrl(raw: string | null): string {
  if (!raw) return "/";
  if (raw.startsWith("/") && !raw.startsWith("//") && !raw.includes("\\")) {
    return raw;
  }
  return "/";
}

function SignupForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextUrl = getSafeNextUrl(searchParams.get("next"));
  const { user, register } = useAuth();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [providers, setProviders] = useState<OAuthProviderItem[]>([]);
  const [providerNotice, setProviderNotice] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      router.push(nextUrl);
    }
  }, [user, nextUrl, router]);

  useEffect(() => {
    async function loadProviders() {
      const res = await getOAuthProviders();
      if (res.data) {
        setProviders(res.data);
      }
    }
    loadProviders();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!email.trim() || !password) {
      setErrorMessage("Please enter your email and password.");
      return;
    }

    if (password.length < 8) {
      setErrorMessage("Password must be at least 8 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage("Passwords do not match.");
      return;
    }

    setLoading(true);
    const result = await register({
      email: email.trim(),
      password,
      full_name: fullName.trim() || undefined,
    });

    if (result.success) {
      router.push(nextUrl);
    } else {
      setErrorMessage(result.error || "Failed to create account.");
      setLoading(false);
    }
  };

  const handleOAuthClick = (providerKey: string, providerName: string) => {
    setProviderNotice(null);
    const prov = providers.find((p) => p.provider === providerKey);
    if (!prov || !prov.configured) {
      setProviderNotice(
        `${providerName} sign-in is not configured on this server yet. Set ${providerKey.toUpperCase()}_CLIENT_ID in your environment.`
      );
      return;
    }

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const nextQuery = nextUrl && nextUrl !== "/" ? `?next=${encodeURIComponent(nextUrl)}` : "";
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination -- External backend OAuth redirect
    window.location.assign(`${apiUrl}/api/v1/auth/${providerKey}/authorize${nextQuery}`);
  };

  return (
    <div className="w-full max-w-md mx-auto space-y-6">
      {/* Brand Header */}
      <div className="text-center space-y-2">
        <Link href="/" className="inline-flex items-center gap-2 mb-2">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Terminal className="w-5 h-5" />
          </div>
          <span className="text-xl font-bold tracking-tight text-slate-100 font-mono">
            AI Coding Gym
          </span>
        </Link>
        <h1 className="text-2xl font-bold text-slate-100">Create Account</h1>
        <p className="text-xs text-slate-400">
          Join the developer gym and start tracking your real interview progress.
        </p>
      </div>

      {/* Main Card */}
      <div className="rounded-2xl border border-slate-800 bg-[#0b0f19] p-6 sm:p-8 shadow-2xl space-y-6">
        {/* Error Banner */}
        {errorMessage && (
          <div className="rounded-lg border border-rose-900/60 bg-rose-950/30 p-3.5 text-xs text-rose-300 flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <div className="leading-relaxed">{errorMessage}</div>
          </div>
        )}

        {/* OAuth Notice Banner */}
        {providerNotice && (
          <div className="rounded-lg border border-amber-900/60 bg-amber-950/30 p-3.5 text-xs text-amber-300 flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div className="leading-relaxed">{providerNotice}</div>
          </div>
        )}

        {/* Social Sign-In Buttons */}
        <div className="space-y-2.5">
          <button
            type="button"
            onClick={() => handleOAuthClick("google", "Google")}
            className="cursor-pointer w-full flex items-center justify-center gap-3 px-4 py-2.5 rounded-xl border border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 text-xs font-medium text-slate-200 transition-colors"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24">
              <path
                fill="#EA4335"
                d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.7 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.3 9 5 12 5z"
              />
              <path
                fill="#4285F4"
                d="M23.5 12.3c0-.8-.1-1.7-.2-2.3H12v4.6h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.9z"
              />
              <path
                fill="#FBBC05"
                d="M5.6 14.8c-.2-.7-.4-1.5-.4-2.8s.2-2.1.4-2.8L1.9 6.3C.7 8.7 0 10.3 0 12s.7 3.3 1.9 5.7l3.7-2.9z"
              />
              <path
                fill="#34A853"
                d="M12 23c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2.3-6.4-5.2L1.9 16C3.7 19.7 7.5 23 12 23z"
              />
            </svg>
            <span>Continue with Google</span>
          </button>

          <button
            type="button"
            onClick={() => handleOAuthClick("github", "GitHub")}
            className="cursor-pointer w-full flex items-center justify-center gap-3 px-4 py-2.5 rounded-xl border border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 text-xs font-medium text-slate-200 transition-colors"
          >
            <GithubIcon className="w-4 h-4" />
            <span>Continue with GitHub</span>
          </button>

          <button
            type="button"
            onClick={() => handleOAuthClick("apple", "Apple")}
            className="cursor-pointer w-full flex items-center justify-center gap-3 px-4 py-2.5 rounded-xl border border-slate-800 bg-slate-900/60 hover:bg-slate-800/80 text-xs font-medium text-slate-200 transition-colors"
          >
            <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
              <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 6.38c.62-.75 1.04-1.8 0.93-2.85-.9.04-1.98.6-2.61 1.34-.56.64-1.05 1.71-.92 2.74 1 .08 2.01-.51 2.6-1.23z" />
            </svg>
            <span>Continue with Apple</span>
          </button>
        </div>

        {/* Divider */}
        <div className="relative flex items-center justify-center">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-800" />
          </div>
          <span className="relative bg-[#0b0f19] px-3 text-[11px] font-mono uppercase tracking-wider text-slate-500">
            Or create with email
          </span>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label
              htmlFor="fullName"
              className="block text-xs font-mono font-medium text-slate-300"
            >
              Full Name (Optional)
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                id="fullName"
                type="text"
                autoComplete="name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Ada Lovelace"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-800 bg-slate-900/60 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 font-mono transition-colors"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="signupEmail"
              className="block text-xs font-mono font-medium text-slate-300"
            >
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                id="signupEmail"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="developer@example.com"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-800 bg-slate-900/60 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 font-mono transition-colors"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="signupPassword"
              className="block text-xs font-mono font-medium text-slate-300"
            >
              Password (Min 8 Characters)
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                id="signupPassword"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-slate-800 bg-slate-900/60 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 font-mono transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="cursor-pointer absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="confirmPassword"
              className="block text-xs font-mono font-medium text-slate-300"
            >
              Confirm Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                id="confirmPassword"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-slate-800 bg-slate-900/60 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 font-mono transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="cursor-pointer w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-medium text-xs sm:text-sm transition-all shadow-[0_0_15px_rgba(16,185,129,0.25)] hover:shadow-[0_0_20px_rgba(16,185,129,0.4)] disabled:opacity-50 disabled:cursor-not-allowed mt-2 font-mono"
          >
            {loading ? (
              <span>Creating Account...</span>
            ) : (
              <>
                <span>Complete Registration</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>
      </div>

      {/* Footer Navigation Link */}
      <div className="text-center text-xs text-slate-400">
        Already have an account?{" "}
        <Link
          href="/login"
          className="text-emerald-400 hover:text-emerald-300 font-medium font-mono transition-colors underline-offset-4 hover:underline"
        >
          Sign In
        </Link>
      </div>
    </div>
  );
}

export default function SignupPage() {
  return (
    <div className="min-h-screen flex flex-col justify-center items-center p-4 bg-[#090d16] text-slate-100">
      <Suspense fallback={<div className="text-xs font-mono text-slate-400">Loading sign up...</div>}>
        <SignupForm />
      </Suspense>
    </div>
  );
}
