"use client";

import React from "react";
import { Navbar } from "@/components/Navbar";
import { Hero } from "@/components/Hero";
import { Features } from "@/components/Features";
import { HowItWorks } from "@/components/HowItWorks";
import { WorkspacePreview } from "@/components/WorkspacePreview";
import { FinalCTA } from "@/components/FinalCTA";
import { Footer } from "@/components/Footer";
import { LenisProvider } from "@/components/LenisProvider";

export default function HomePage() {
  return (
    <LenisProvider>
      <div className="min-h-screen flex flex-col bg-[#090d16] text-slate-100">
        {/* Navigation */}
        <Navbar />

        {/* Main Content */}
        <main className="flex-1">
          {/* Hero Section */}
          <Hero />

          {/* Feature Overview */}
          <Features />

          {/* How It Works */}
          <section id="how-it-works">
            <HowItWorks />
          </section>

          {/* Developer Workspace Preview */}
          <WorkspacePreview />

          {/* Final CTA */}
          <FinalCTA />
        </main>

        {/* Footer */}
        <Footer />
      </div>
    </LenisProvider>
  );
}
