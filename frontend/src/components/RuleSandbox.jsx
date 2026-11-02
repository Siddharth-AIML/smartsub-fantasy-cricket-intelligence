import React from 'react';
import { Sliders, CheckSquare, Square, Shield, Sparkles, AlertCircle } from 'lucide-react';

export default function RuleSandbox({
  fantasyTeam,
  onUpdateRuleConfig,
  isLoading
}) {
  const ruleMode = fantasyTeam?.rule_mode || "TIER_4_PROPOSED_EXPERIMENTAL";
  const isExperimentalMode = ruleMode.includes("TIER_4");

  const toggleMode = () => {
    const nextMode = isExperimentalMode ? "TIER_1_VERIFIED" : "TIER_4_PROPOSED_EXPERIMENTAL";
    onUpdateRuleConfig({ rule_mode: nextMode });
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col">
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            Substitution Sandbox & Rule Mode
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">
              Interactive Sandbox
            </span>
          </h3>
          <p className="text-xs text-slate-400">
            Toggle between verified official platform rules and SmartSub experimental mechanics
          </p>
        </div>
      </div>

      {/* Mode Switcher Banner */}
      <div className="p-3.5 rounded-xl border mb-4 bg-slate-950/70 border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            {isExperimentalMode ? (
              <Sparkles className="w-4 h-4 text-amber-400" />
            ) : (
              <Shield className="w-4 h-4 text-emerald-400" />
            )}
            <span className="font-bold text-sm text-white">
              {isExperimentalMode
                ? "Tier 4: Proposed SmartSub Experimental Rules"
                : "Tier 1: Verified Official Dream11 Rules"}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            {isExperimentalMode
              ? "Enables Scenario 1 (B2 evaluated when B1 DNP) and Scenario 2 (2nd innings Impact sub with ledger split)."
              : "Strict compliance: Backups activate strictly at deadline for DNP starters; no in-match swaps."}
          </p>
        </div>

        <button
          onClick={toggleMode}
          disabled={isLoading}
          className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all border shrink-0 ${
            isExperimentalMode
              ? "bg-amber-500/20 text-amber-300 border-amber-500/40 hover:bg-amber-500/30"
              : "bg-emerald-500/20 text-emerald-300 border-emerald-500/40 hover:bg-emerald-500/30"
          }`}
        >
          Switch to {isExperimentalMode ? "Verified Platform Mode" : "Experimental Mode"}
        </button>
      </div>

      {/* Experimental Scenarios Configuration Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {/* Scenario 1 Card */}
        <div className={`p-3.5 rounded-xl border ${
          isExperimentalMode ? "bg-slate-850/60 border-slate-750" : "bg-slate-950/40 border-slate-800/60 opacity-60"
        }`}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-white flex items-center gap-1.5">
              Scenario 1: B2 When B1 is DNP
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              R-SUB-01
            </span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            When starter is unannounced, B1 is bypassed if real status is <code className="text-amber-400">DID_NOT_PLAY</code>, promoting B2 (<code className="text-emerald-400">PLAYING_XI</code>) if eligible.
          </p>
        </div>

        {/* Scenario 2 Card */}
        <div className={`p-3.5 rounded-xl border ${
          isExperimentalMode ? "bg-slate-850/60 border-slate-750" : "bg-slate-950/40 border-slate-800/60 opacity-60"
        }`}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-white flex items-center gap-1.5">
              Scenario 2: 2nd Innings Impact Sub
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
              R-SUB-02
            </span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Preserves outgoing player's Innings 1 points permanently in ledger. Incoming Impact Player participates exclusively in Innings 2.
          </p>
        </div>
      </div>
    </div>
  );
}
