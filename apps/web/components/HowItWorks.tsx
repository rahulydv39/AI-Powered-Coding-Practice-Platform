import React from "react";
import { FileSearch, Code2, TrendingUp } from "lucide-react";
import { AnimatedSection } from "./AnimatedSection";

const steps = [
  {
    number: "01",
    title: "Choose a Challenge",
    description:
      "Pick a coding challenge from our collection of real-world debugging and refactoring problems.",
    icon: FileSearch,
    color: "text-emerald-400",
    borderColor: "border-emerald-500/30",
    bgColor: "bg-emerald-500/10",
    glowColor: "shadow-emerald-500/10",
  },
  {
    number: "02",
    title: "Write & Run Tests",
    description:
      "Write your solution in the editor, run it against comprehensive test suites, and iterate until tests pass.",
    icon: Code2,
    color: "text-cyan-400",
    borderColor: "border-cyan-500/30",
    bgColor: "bg-cyan-500/10",
    glowColor: "shadow-cyan-500/10",
  },
  {
    number: "03",
    title: "Review & Improve",
    description:
      "Get your deterministic score, review AI-generated feedback, compare with reference solutions, and learn.",
    icon: TrendingUp,
    color: "text-purple-400",
    borderColor: "border-purple-500/30",
    bgColor: "bg-purple-500/10",
    glowColor: "shadow-purple-500/10",
  },
];

export function HowItWorks() {
  return (
    <section className="relative py-24 sm:py-32">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-slate-800 to-transparent" />
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <AnimatedSection animation="fade-up">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-100">
              How it works
            </h2>
            <p className="mt-4 text-base text-slate-400">
              Three simple steps to start improving your coding interview skills.
            </p>
          </div>
        </AnimatedSection>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
          {/* Connecting line (desktop only) */}
          <div className="hidden md:block absolute top-16 left-[16.67%] right-[16.67%] h-px bg-gradient-to-r from-emerald-500/30 via-cyan-500/30 to-purple-500/30" />

          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <AnimatedSection
                key={step.number}
                animation="fade-up"
                delay={index * 150}
              >
                <div className="relative text-center">
                  {/* Step icon */}
                  <div className="relative inline-flex mb-6">
                    <div
                      className={`w-16 h-16 rounded-2xl ${step.bgColor} border ${step.borderColor} flex items-center justify-center shadow-lg ${step.glowColor}`}
                    >
                      <Icon className={`w-7 h-7 ${step.color}`} />
                    </div>
                    <div
                      className={`absolute -top-2 -right-2 w-7 h-7 rounded-full bg-[#090d16] border-2 ${step.borderColor} flex items-center justify-center text-[11px] font-bold ${step.color} font-mono`}
                    >
                      {step.number}
                    </div>
                  </div>

                  <h3 className="text-xl font-semibold text-slate-100 mb-3">
                    {step.title}
                  </h3>
                  <p className="text-sm text-slate-400 leading-relaxed max-w-xs mx-auto">
                    {step.description}
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
