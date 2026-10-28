"use client";

import React, { Suspense } from "react";
import { useParams } from "next/navigation";
import { ChallengeWorkspace } from "@/components/ChallengeWorkspace";

function DynamicChallengeInner() {
  const params = useParams();
  const id =
    typeof params?.id === "string"
      ? params.id
      : Array.isArray(params?.id)
      ? params.id[0]
      : "";

  return <ChallengeWorkspace challengeId={id} />;
}

export default function DynamicChallengePage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#090d16] text-slate-100 flex items-center justify-center p-4">
          <div className="w-10 h-10 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      <DynamicChallengeInner />
    </Suspense>
  );
}
