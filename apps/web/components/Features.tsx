import React from "react";
import {
  Bot,
  BarChart3,
  Play,
  Lightbulb,
  History,
  Code2,
  Cpu,
} from "lucide-react";
import { AnimatedSection } from "./AnimatedSection";

const features = [
  {
    title: "Coding Interview Practice",
    description:
      "Tackle realistic debugging challenges on production-quality codebases. Fix race conditions, memory leaks, and concurrency bugs.",
    icon: Code2,
    iconColor: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/20",
  },
  {
    title: "Run Tests & Scoring",
    description:
      "Execute your code against comprehensive test suites. Get deterministic correctness scores based on how many tests pass.",
    icon: Play,
    iconColor: "text-cyan-400",
    bgColor: "bg-cyan-500/10",
    borderColor: "border-cyan-500/20",
  },
  {
    title: "AI-Powered Hints",
    description:
      "Stuck on a problem? Get progressive, contextual hints from AI assistants without spoiling the solution.",
    icon: Lightbulb,
    iconColor: "text-amber-400",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/20",
  },
  {
    title: "AI Solution Review",
    description:
      "After submission, compare your approach with a reference solution and get AI-generated feedback on improvements.",
    icon: Bot,
    iconColor: "text-purple-400",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/20",
  },
  {
    title: "Progress & History",
    description:
      "Track every submission with detailed score breakdowns, test results, and historical progression charts.",
    icon: History,
    iconColor: "text-sky-400",
    bgColor: "bg-sky-500/10",
    borderColor: "border-sky-500/20",
  },
  {
    title: "Multiple AI Providers",
    description:
      "Choose between Gemini, Claude, and OpenAI for hints and reviews. Configure your preferred AI assistant.",
    icon: Cpu,
    iconColor: "text-rose-400",
    bgColor: "bg-rose-500/10",
    borderColor: "border-rose-500/20",
  },
];

export function Features() {
  return (
    <section id="features" className="relative py-24 sm:py-32">
      {/* Section background */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-slate-950/50 to-transparent pointer-events-none" />
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/4 w-[500px] h-[400px] bg-emerald-500/3 blur-[120px] rounded-full" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <AnimatedSection animation="fade-up">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-slate-800/80 border border-slate-700/60 text-slate-300 mb-4">
              <BarChart3 className="w-3.5 h-3.5 text-emerald-400" />
              Platform Capabilities
            </span>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-slate-100">
              Everything you need to{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                level up
              </span>
            </h2>
            <p className="mt-4 text-base sm:text-lg text-slate-400">
              A complete toolkit for practicing modern coding interviews with
              real tests, AI assistance, and detailed feedback.
            </p>
          </div>
        </AnimatedSection>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <AnimatedSection
                key={feature.title}
                animation="fade-up"
                delay={index * 80}
              >
                <div className="group relative h-full rounded-2xl bg-slate-900/40 border border-slate-800/80 p-6 hover:border-slate-700/80 transition-all duration-300 hover:shadow-[0_8px_30px_rgb(0,0,0,0.3)] hover:-translate-y-0.5">
                  <div
                    className={`w-11 h-11 rounded-xl ${feature.bgColor} border ${feature.borderColor} flex items-center justify-center mb-4`}
                  >
                    <Icon className={`w-5 h-5 ${feature.iconColor}`} />
                  </div>
                  <h3 className="text-lg font-semibold text-slate-100 mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-sm text-slate-400 leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </AnimatedSection>
            );
          })}
        </div>
      </div>
    </section>
  );
}
