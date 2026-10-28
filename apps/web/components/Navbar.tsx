"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Terminal,
  ArrowUpRight,
  User,
  LogOut,
  Menu,
  X,
  ChevronDown,
  Code2,
  Eye,
  Lightbulb,
  BookOpen,
  LayoutDashboard,
  Award,
  Sparkles,
  Cpu,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";

interface DropdownItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  description?: string;
}

interface NavDropdownProps {
  label: string;
  items: DropdownItem[];
  isOpen: boolean;
  onToggle: () => void;
  onClose: () => void;
}

function NavDropdown({ label, items, isOpen, onToggle, onClose }: NavDropdownProps) {
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && isOpen) {
        onClose();
        buttonRef.current?.focus();
      }
    }
    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
    }
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  return (
    <div
      ref={dropdownRef}
      className="relative"
      onMouseEnter={onToggle}
      onMouseLeave={onClose}
    >
      <button
        ref={buttonRef}
        type="button"
        onClick={onToggle}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onToggle();
          }
          if (e.key === "ArrowDown" && !isOpen) {
            e.preventDefault();
            onToggle();
          }
        }}
        className="cursor-pointer flex items-center gap-1 px-1 py-2 text-sm text-slate-300 hover:text-white transition-colors group"
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <span>{label}</span>
        <ChevronDown
          className={`w-3.5 h-3.5 transition-transform duration-200 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {isOpen && (
        <div
          className="absolute top-full left-1/2 -translate-x-1/2 mt-1 w-64 rounded-xl border border-slate-800 bg-[#0c1220] p-2 shadow-2xl z-50 animate-in fade-in slide-in-from-top-2 duration-200"
          role="menu"
        >
          {items.map((item) => (
            <Link
              key={item.href + item.label}
              href={item.href}
              onClick={onClose}
              role="menuitem"
              className="flex items-start gap-3 px-3 py-2.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors group"
            >
              <span className="mt-0.5 text-slate-400 group-hover:text-emerald-400 transition-colors">
                {item.icon}
              </span>
              <div>
                <div className="text-sm font-medium">{item.label}</div>
                {item.description && (
                  <div className="text-[11px] text-slate-500 mt-0.5">{item.description}</div>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, loading: authLoading, logout } = useAuth();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const [mobileExpanded, setMobileExpanded] = useState<string | null>(null);

  // Close mobile menu on route change without cascading renders
  const [prevPathname, setPrevPathname] = useState(pathname);
  if (prevPathname !== pathname) {
    setPrevPathname(pathname);
    setMobileMenuOpen(false);
    setOpenDropdown(null);
    setMobileExpanded(null);
  }

  const handleSignOut = async () => {
    setUserMenuOpen(false);
    setMobileMenuOpen(false);
    await logout();
    router.push("/");
  };

  const handleDropdownToggle = useCallback(
    (name: string) => {
      setOpenDropdown((prev) => (prev === name ? null : name));
    },
    []
  );

  const handleDropdownClose = useCallback(() => {
    setOpenDropdown(null);
  }, []);

  const practiceItems: DropdownItem[] = [
    {
      label: "Challenges Catalog",
      href: "/challenges",
      icon: <Code2 className="w-4 h-4" />,
      description: "Browse all interview challenges",
    },
    {
      label: "Challenge Preview",
      href: "/#preview",
      icon: <Eye className="w-4 h-4" />,
      description: "See what a session looks like",
    },
  ];

  const learnItems: DropdownItem[] = [
    {
      label: "How It Works",
      href: "/#how-it-works",
      icon: <Sparkles className="w-4 h-4" />,
      description: "Three-step practice flow",
    },
    {
      label: "Solution Review",
      href: "/#features",
      icon: <BookOpen className="w-4 h-4" />,
      description: "Compare with reference solutions",
    },
    {
      label: "Developer Workspace",
      href: "/#preview",
      icon: <Terminal className="w-4 h-4" />,
      description: "Integrated editor & test runner",
    },
  ];

  const aiToolsItems: DropdownItem[] = [
    {
      label: "AI Debugging Hints",
      href: "/#features",
      icon: <Lightbulb className="w-4 h-4" />,
      description: "Progressive hints without spoilers",
    },
    {
      label: "Multi-Model AI",
      href: "/#features",
      icon: <Cpu className="w-4 h-4" />,
      description: "Gemini, Claude & OpenAI support",
    },
    {
      label: "Deterministic Scoring",
      href: "/#features",
      icon: <Award className="w-4 h-4" />,
      description: "Test-backed rubric evaluation",
    },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800/60 bg-[#090d16]/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2.5 shrink-0">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Terminal className="w-4 h-4" />
          </div>
          <span className="font-semibold text-slate-100 tracking-tight text-base">
            AI Coding Gym
          </span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-5 text-sm">
          <Link
            href="/"
            className={`px-1 py-2 transition-colors ${
              pathname === "/" ? "text-white font-medium" : "text-slate-300 hover:text-white"
            }`}
          >
            Home
          </Link>

          <NavDropdown
            label="Practice"
            items={practiceItems}
            isOpen={openDropdown === "practice"}
            onToggle={() => handleDropdownToggle("practice")}
            onClose={handleDropdownClose}
          />

          <NavDropdown
            label="Learn"
            items={learnItems}
            isOpen={openDropdown === "learn"}
            onToggle={() => handleDropdownToggle("learn")}
            onClose={handleDropdownClose}
          />

          <NavDropdown
            label="AI Tools"
            items={aiToolsItems}
            isOpen={openDropdown === "ai-tools"}
            onToggle={() => handleDropdownToggle("ai-tools")}
            onClose={handleDropdownClose}
          />

          <Link
            href="/#features"
            className="px-1 py-2 text-slate-300 hover:text-white transition-colors"
          >
            Features
          </Link>

          {user && (
            <Link
              href="/progress"
              className={`px-1 py-2 flex items-center gap-1.5 transition-colors ${
                pathname === "/progress"
                  ? "text-emerald-400 font-medium"
                  : "text-slate-300 hover:text-white"
              }`}
            >
              <LayoutDashboard className="w-3.5 h-3.5" />
              <span>Dashboard</span>
            </Link>
          )}
        </nav>

        {/* Right side: Practice CTA (visually prominent) + Login/User action next to it */}
        <div className="flex items-center gap-3">
          {/* Primary CTA - Visually prominent Practice action */}
          <Link
            href="/challenges"
            className="cursor-pointer inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition-all shadow-[0_0_15px_rgba(16,185,129,0.25)] hover:shadow-[0_0_20px_rgba(16,185,129,0.4)] active:scale-[0.98]"
          >
            <span className="hidden sm:inline">Practice Now</span>
            <span className="sm:hidden">Practice</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>

          {/* Login / User menu action - next to the Practice CTA */}
          {authLoading ? (
            <div className="w-16 h-8 rounded-lg bg-slate-900/40 animate-pulse" />
          ) : user ? (
            <div className="relative hidden md:block">
              <button
                type="button"
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="cursor-pointer flex items-center gap-2 p-1.5 sm:px-3 sm:py-1.5 rounded-lg border border-slate-800 bg-slate-900/80 hover:bg-slate-800 text-sm text-slate-200 transition-colors"
                aria-label="User menu"
              >
                <div className="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-xs">
                  {user.email[0].toUpperCase()}
                </div>
                <span className="hidden lg:inline max-w-[120px] truncate text-xs">
                  {user.full_name || user.email.split("@")[0]}
                </span>
              </button>

              {userMenuOpen && (
                <div
                  onMouseLeave={() => setUserMenuOpen(false)}
                  className="absolute right-0 mt-2 w-52 rounded-xl border border-slate-800 bg-[#0c1220] p-1.5 shadow-2xl z-50 text-xs space-y-0.5"
                >
                  <div className="px-3 py-2 border-b border-slate-800/80 text-[11px] text-slate-400 truncate">
                    {user.email}
                  </div>
                  <Link
                    href="/progress"
                    onClick={() => setUserMenuOpen(false)}
                    className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
                  >
                    <Award className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Dashboard</span>
                  </Link>
                  <Link
                    href="/account"
                    onClick={() => setUserMenuOpen(false)}
                    className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
                  >
                    <User className="w-3.5 h-3.5" />
                    <span>Account Settings</span>
                  </Link>
                  <button
                    type="button"
                    onClick={handleSignOut}
                    className="cursor-pointer w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-rose-400 hover:text-rose-300 hover:bg-rose-950/20 transition-colors text-left"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>Sign Out</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <Link
              href="/login"
              className="hidden md:inline-flex px-3.5 py-1.5 rounded-lg text-sm text-slate-300 hover:text-white border border-slate-800 hover:bg-slate-800/60 transition-colors"
            >
              Log In
            </Link>
          )}

          {/* Mobile menu button */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="cursor-pointer md:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
            aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-800/60 bg-[#090d16]/98 backdrop-blur-xl">
          <div className="px-4 py-4 space-y-1">
            <Link
              href="/"
              className="block px-3 py-2.5 rounded-lg text-sm text-slate-200 hover:bg-slate-800/60"
            >
              Home
            </Link>

            {/* Practice dropdown mobile */}
            <div>
              <button
                type="button"
                onClick={() =>
                  setMobileExpanded((prev) => (prev === "practice" ? null : "practice"))
                }
                className="cursor-pointer w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm text-slate-200 hover:bg-slate-800/60"
              >
                <span>Practice</span>
                <ChevronDown
                  className={`w-4 h-4 transition-transform ${
                    mobileExpanded === "practice" ? "rotate-180" : ""
                  }`}
                />
              </button>
              {mobileExpanded === "practice" && (
                <div className="ml-4 mt-1 space-y-1">
                  {practiceItems.map((item) => (
                    <Link
                      key={item.href + item.label}
                      href={item.href}
                      className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-slate-800/40"
                    >
                      {item.icon}
                      <span>{item.label}</span>
                    </Link>
                  ))}
                </div>
              )}
            </div>

            {/* Learn dropdown mobile */}
            <div>
              <button
                type="button"
                onClick={() =>
                  setMobileExpanded((prev) => (prev === "learn" ? null : "learn"))
                }
                className="cursor-pointer w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm text-slate-200 hover:bg-slate-800/60"
              >
                <span>Learn</span>
                <ChevronDown
                  className={`w-4 h-4 transition-transform ${
                    mobileExpanded === "learn" ? "rotate-180" : ""
                  }`}
                />
              </button>
              {mobileExpanded === "learn" && (
                <div className="ml-4 mt-1 space-y-1">
                  {learnItems.map((item) => (
                    <Link
                      key={item.href + item.label}
                      href={item.href}
                      className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-slate-800/40"
                    >
                      {item.icon}
                      <span>{item.label}</span>
                    </Link>
                  ))}
                </div>
              )}
            </div>

            {/* AI Tools dropdown mobile */}
            <div>
              <button
                type="button"
                onClick={() =>
                  setMobileExpanded((prev) => (prev === "ai-tools" ? null : "ai-tools"))
                }
                className="cursor-pointer w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm text-slate-200 hover:bg-slate-800/60"
              >
                <span>AI Tools</span>
                <ChevronDown
                  className={`w-4 h-4 transition-transform ${
                    mobileExpanded === "ai-tools" ? "rotate-180" : ""
                  }`}
                />
              </button>
              {mobileExpanded === "ai-tools" && (
                <div className="ml-4 mt-1 space-y-1">
                  {aiToolsItems.map((item) => (
                    <Link
                      key={item.href + item.label}
                      href={item.href}
                      className="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-slate-800/40"
                    >
                      {item.icon}
                      <span>{item.label}</span>
                    </Link>
                  ))}
                </div>
              )}
            </div>

            <Link
              href="/#features"
              className="block px-3 py-2.5 rounded-lg text-sm text-slate-200 hover:bg-slate-800/60"
            >
              Features
            </Link>

            {user && (
              <Link
                href="/progress"
                className="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm text-emerald-400 hover:bg-slate-800/60"
              >
                <LayoutDashboard className="w-4 h-4" />
                <span>Dashboard</span>
              </Link>
            )}

            {/* Mobile auth */}
            <div className="pt-3 mt-3 border-t border-slate-800/60 space-y-2">
              {authLoading ? null : user ? (
                <>
                  <div className="px-3 py-2 text-xs text-slate-400 truncate">
                    {user.email}
                  </div>
                  <Link
                    href="/account"
                    className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-slate-800/60"
                  >
                    <User className="w-4 h-4" />
                    <span>Account</span>
                  </Link>
                  <button
                    type="button"
                    onClick={handleSignOut}
                    className="cursor-pointer w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-rose-400 hover:bg-rose-950/20"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Sign Out</span>
                  </button>
                </>
              ) : (
                <div className="flex items-center gap-2">
                  <Link
                    href="/login"
                    className="flex-1 text-center px-3 py-2.5 rounded-lg text-sm border border-slate-800 text-slate-200 hover:bg-slate-800/60"
                  >
                    Log In
                  </Link>
                  <Link
                    href="/signup"
                    className="flex-1 text-center px-3 py-2.5 rounded-lg text-sm bg-emerald-500 text-slate-950 font-medium"
                  >
                    Sign Up
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
