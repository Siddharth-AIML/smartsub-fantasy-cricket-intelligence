import React from 'react';
import { PlayCircle, CheckCircle2, ArrowRight, Sparkles, Flame, UserX, UserCheck, Shield } from 'lucide-react';

export default function ScenarioCards({
  onRunScenario1,
  onRunScenario2,
  decisions = [],
  liveState,
  isLoading
}) {
  const hasScenario1Executed = decisions.some(d => d.reason_code === "SCENARIO_1_B2_SUBSTITUTED_WHEN_B1_DNP");
  const hasScenario2Executed = decisions.some(d => d.reason_code === "SCENARIO_2_IMPACT_SUB_INN2_EXECUTED");

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-5" data-testid="scenario-cards-container">
      {/* Scenario 1 Card */}
      <div
        data-testid="scenario-card-1"
        className={`rounded-2xl border p-5 flex flex-col justify-between transition-all relative overflow-hidden ${
          hasScenario1Executed
            ? "bg-slate-900/90 border-emerald-500/50 shadow-lg shadow-emerald-950/20"
            : "bg-slate-900 border-purple-500/30 hover:border-purple-400/50 shadow-lg shadow-purple-950/10"
        }`}
      >
        <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/5 rounded-full blur-2xl pointer-events-none" />

        <div>
          <div className="flex items-center justify-between gap-2 mb-2.5">
            <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
              SCENARIO 1 • BENCH REPLACEMENT
            </span>
            {hasScenario1Executed ? (
              <span
                data-testid="scenario-1-status"
                className="text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded-full flex items-center gap-1"
              >
                <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Shardul Thakur Active (B2)
              </span>
            ) : (
              <span
                data-testid="scenario-1-status"
                className="text-[11px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700"
              >
                Ready to Start
              </span>
            )}
          </div>

          <h3 className="text-base font-bold text-white mb-1.5 flex items-center gap-2">
            Non-Playing Starter & Backup Replacement
          </h3>

          <p className="text-xs text-slate-300 leading-relaxed mb-4">
            Your starter <strong className="text-rose-300">Mustafizur Rahman</strong> is omitted from the announced XI (DNP). SmartSub checks <strong className="text-amber-300">Backup 1 (Devon Conway)</strong>, detects he also does not play, skips B1 with an audit record, and promotes <strong className="text-emerald-300">Backup 2 (Shardul Thakur)</strong> into your Playing XI!
          </p>

          {/* Micro Visual Flow */}
          <div className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 mb-4 text-[11px] font-mono flex items-center justify-between text-slate-300">
            <div className="flex items-center gap-1.5 text-rose-300">
              <UserX className="w-3.5 h-3.5" />
              <span>Mustafizur (DNP)</span>
            </div>
            <ArrowRight className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <div className="text-amber-300">
              <span>Conway (B1: Skipped)</span>
            </div>
            <ArrowRight className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <div className="flex items-center gap-1.5 text-emerald-300 font-bold">
              <UserCheck className="w-3.5 h-3.5" />
              <span>Thakur (B2: Active XI)</span>
            </div>
          </div>
        </div>

        <button
          onClick={onRunScenario1}
          disabled={isLoading}
          data-testid="start-scenario-1-btn"
          className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold text-xs flex items-center justify-center gap-2 transition-all shadow-md shadow-purple-600/20 disabled:opacity-50"
        >
          <PlayCircle className="w-4 h-4 text-purple-200" />
          {hasScenario1Executed ? "Run Scenario 1 Again" : "Start Demo: Scenario 1 (Auto-Step)"}
        </button>
      </div>

      {/* Scenario 2 Card */}
      <div
        data-testid="scenario-card-2"
        className={`rounded-2xl border p-5 flex flex-col justify-between transition-all relative overflow-hidden ${
          hasScenario2Executed
            ? "bg-slate-900/90 border-emerald-500/50 shadow-lg shadow-emerald-950/20"
            : "bg-slate-900 border-indigo-500/30 hover:border-indigo-400/50 shadow-lg shadow-indigo-950/10"
        }`}
      >
        <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-full blur-2xl pointer-events-none" />

        <div>
          <div className="flex items-center justify-between gap-2 mb-2.5">
            <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              SCENARIO 2 • IMPACT PLAYER & SCORING
            </span>
            {hasScenario2Executed ? (
              <span
                data-testid="scenario-2-status"
                className="text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded-full flex items-center gap-1"
              >
                <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Stoinis Active (32 pts) | Thakur (43 pts Locked)
              </span>
            ) : (
              <span
                data-testid="scenario-2-status"
                className="text-[11px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700"
              >
                Ready to Start
              </span>
            )}
          </div>

          <h3 className="text-base font-bold text-white mb-1.5 flex items-center gap-2">
            Impact Player Replacement & Innings Scoring
          </h3>

          <p className="text-xs text-slate-300 leading-relaxed mb-4">
            <strong className="text-emerald-300">Shardul Thakur</strong> bowls 4 overs in Innings 1 and locks in <strong className="text-amber-300">43.0 historical points</strong>. In Innings 2, <strong className="text-purple-300">Marcus Stoinis (B3)</strong> enters as CSK's Impact Player. Under SmartSub's single-occupant experimental rule, Thakur's 43 historical pts are preserved in the locked ledger but excluded from active score, while Stoinis's 32 pts count for the slot!
          </p>

          {/* Micro Visual Flow */}
          <div className="p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 mb-4 text-[11px] font-mono flex items-center justify-between text-slate-300">
            <div className="text-emerald-300">
              <span>Thakur (1st Inn: 43 pts)</span>
            </div>
            <ArrowRight className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <div className="text-amber-300 font-semibold">
              <span>🔒 Ledger Locked</span>
            </div>
            <ArrowRight className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <div className="flex items-center gap-1.5 text-purple-300 font-bold">
              <Flame className="w-3.5 h-3.5 text-amber-400" />
              <span>Stoinis (32 pts Active)</span>
            </div>
          </div>
        </div>

        <button
          onClick={onRunScenario2}
          disabled={isLoading}
          data-testid="start-scenario-2-btn"
          className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-xs flex items-center justify-center gap-2 transition-all shadow-md shadow-indigo-600/20 disabled:opacity-50"
        >
          <PlayCircle className="w-4 h-4 text-indigo-200" />
          {hasScenario2Executed ? "Run Scenario 2 Again" : "Start Demo: Scenario 2 (Full Auto-Run)"}
        </button>
      </div>
    </div>
  );
}
