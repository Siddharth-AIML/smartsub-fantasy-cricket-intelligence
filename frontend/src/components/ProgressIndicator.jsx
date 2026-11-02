import React from 'react';
import { Check, CircleDot, Circle } from 'lucide-react';

export default function ProgressIndicator({ liveState, decisions }) {
  const phase = liveState?.scoreboard?.phase || "PRE_MATCH";
  const hasSubstitutions = decisions && decisions.length > 0;
  const currentInnings = liveState?.current_innings || 1;

  // Determine stage (1 to 4)
  let currentStep = 1;
  if (phase === "TOSS_CONDUCTED") {
    currentStep = 1;
  } else if (phase === "LINEUP_CONFIRMED" || phase === "INNINGS_1") {
    currentStep = hasSubstitutions ? 3 : 2;
  } else if (phase === "INNINGS_2_STARTED" || phase === "INNINGS_2") {
    currentStep = 4;
  }

  const steps = [
    {
      num: 1,
      title: "Match Setup",
      desc: "Toss & Pitch formation",
      isCompleted: currentStep > 1 || phase !== "PRE_MATCH",
      isCurrent: currentStep === 1
    },
    {
      num: 2,
      title: "Lineup Announced",
      desc: "Official 11 & DNP detection",
      isCompleted: currentStep > 2 || phase === "LINEUP_CONFIRMED" || phase === "INNINGS_1" || currentInnings === 2,
      isCurrent: currentStep === 2
    },
    {
      num: 3,
      title: "Substitution Evaluated",
      desc: "Deterministic rules applied",
      isCompleted: hasSubstitutions,
      isCurrent: currentStep === 3
    },
    {
      num: 4,
      title: "Results & Scoring",
      desc: "Split ledger & points impact",
      isCompleted: currentInnings === 2,
      isCurrent: currentStep === 4
    }
  ];

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 shadow-md" data-testid="progress-indicator">
      <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-bold mb-3 flex items-center justify-between">
        <span>Simulation Progress Tracker</span>
        <span className="text-purple-400">Step {currentStep} of 4</span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {steps.map((s) => {
          const isDone = s.isCompleted;
          const isCurrent = s.isCurrent;

          return (
            <div
              key={s.num}
              data-testid={`progress-step-${s.num}`}
              className={`p-3 rounded-xl border flex items-center gap-3 transition-all ${
                isCurrent
                  ? "bg-purple-950/30 border-purple-500/50 ring-1 ring-purple-500/30"
                  : isDone
                  ? "bg-emerald-950/15 border-emerald-800/40"
                  : "bg-slate-950/50 border-slate-800 opacity-60"
              }`}
            >
              <div className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs shrink-0 ${
                isDone
                  ? "bg-emerald-500 text-slate-950"
                  : isCurrent
                  ? "bg-purple-500 text-white animate-pulse"
                  : "bg-slate-800 text-slate-400 border border-slate-700"
              }`}>
                {isDone ? <Check className="w-4 h-4 stroke-[3]" /> : s.num}
              </div>

              <div className="min-w-0">
                <p className={`text-xs font-bold truncate ${isCurrent ? "text-purple-300" : isDone ? "text-white" : "text-slate-400"}`}>
                  {s.title}
                </p>
                <p className="text-[10px] text-slate-400 truncate">
                  {s.desc}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
