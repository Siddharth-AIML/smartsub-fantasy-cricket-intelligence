import React from 'react';
import { Play, FastForward, UserCheck, Flame, ArrowRight, CheckCircle2, RotateCcw, AlertCircle, ShieldCheck, Trophy, Sparkles } from 'lucide-react';
import { getMatchPhase } from '../utils/formatters';

export default function MatchSimulatorCard({
  liveState,
  onStepSimulation,
  onTriggerImpact,
  isLoading
}) {
  const scoreboard = liveState?.scoreboard || {};
  const currentInnings = liveState?.current_innings || 1;
  const inn1 = scoreboard?.innings_1 || {};
  const inn2 = scoreboard?.innings_2 || {};
  const phase = scoreboard?.phase || "PRE_MATCH";
  const matchResult = scoreboard?.match_result;

  const isMatchCompleted = phase === "COMPLETED" || liveState?.status === "COMPLETED";
  const isInningsBreak = phase === "INNINGS_BREAK";
  const isInningsEnded = isMatchCompleted || isInningsBreak || (currentInnings === 1 && (inn1.overs === "20.0" || inn1.wickets >= 10)) || (currentInnings === 2 && (inn2.overs === "20.0" || inn2.wickets >= 10 || (inn2.runs && inn2.target && inn2.runs >= inn2.target)));

  const activePoints = liveState?.fantasy_active_points ?? liveState?.fantasy_total_points ?? 0.0;
  const historicalPoints = liveState?.historical_locked_points ?? 0.0;
  const replacementAudit = liveState?.replacement_slot_audit;

  // Compute recommended next action
  const isTossNext = phase === "PRE_MATCH";
  const isLineupNext = phase === "TOSS_CONDUCTED";
  const isInnings2Next = (phase === "LINEUP_CONFIRMED" || phase === "INNINGS_1_COMPLETED" || phase === "INNINGS_1" || isInningsBreak) && currentInnings === 1;
  const isImpactNext = currentInnings === 2 && phase !== "IMPACT_PLAYER_ACTIVE" && !isMatchCompleted;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl relative overflow-hidden" data-testid="match-simulator-card">
      {/* Background Accent Gradient */}
      <div className="absolute top-0 right-0 w-80 h-40 bg-gradient-to-bl from-purple-500/10 via-transparent to-transparent pointer-events-none" />

      {/* Header Match Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-4 mb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="flex items-center -space-x-2">
            <div className="w-10 h-10 rounded-full bg-yellow-400 text-slate-950 font-black flex items-center justify-center text-xs shadow-md border-2 border-slate-900">
              CSK
            </div>
            <div className="w-10 h-10 rounded-full bg-blue-600 text-white font-black flex items-center justify-center text-xs shadow-md border-2 border-slate-900">
              MI
            </div>
          </div>
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              Chennai Super Kings vs Mumbai Indians
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/30 font-semibold">
                T20 Match Simulator (Max 20.0 Ov)
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Wankhede Stadium, Mumbai • Target: 183 Runs
            </p>
          </div>
        </div>

        {/* Phase Badge */}
        <div className="flex items-center gap-2 bg-slate-950/80 px-3 py-1.5 rounded-xl border border-slate-800 text-xs" data-testid="match-phase">
          <span className={`w-2 h-2 rounded-full ${isMatchCompleted ? "bg-emerald-400" : "bg-purple-400 animate-pulse"}`} />
          <span className="text-slate-400">Match Status:</span>
          <span className="font-mono text-purple-300 font-bold">{getMatchPhase(phase)}</span>
        </div>
      </div>

      {/* Prominent Match Completed & Final User Fantasy Score Banner */}
      {isMatchCompleted && (
        <div
          data-testid="final-user-score-banner"
          className="bg-gradient-to-r from-purple-950/90 via-indigo-950/90 to-purple-950/90 border-2 border-purple-400 p-4 rounded-2xl mb-5 shadow-2xl flex flex-col sm:flex-row items-center justify-between gap-4 text-center sm:text-left"
        >
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-yellow-400 to-amber-300 text-slate-950 flex items-center justify-center shadow-lg shadow-yellow-500/30 shrink-0">
              <Trophy className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[11px] font-mono uppercase font-bold text-yellow-300 tracking-wider flex items-center gap-1.5 justify-center sm:justify-start">
                <Sparkles className="w-3.5 h-3.5" /> Match Completed • Official Result
              </span>
              <h3 className="text-base font-black text-white" data-testid="match-result-text">
                {matchResult || "Chennai Super Kings won by 6 wickets (Target reached in 19.4 ov)"}
              </h3>
              <p className="text-xs text-slate-300">
                Single-occupant scoring applied: historical ledger preserved in database.
              </p>
            </div>
          </div>

          <div className="bg-slate-900/90 border border-purple-400/60 px-5 py-2.5 rounded-xl text-center shadow-inner shrink-0">
            <span className="text-[10px] font-mono text-purple-300 uppercase tracking-wider block font-bold">
              Final User Fantasy Score
            </span>
            <span className="text-3xl font-black text-white font-mono" data-testid="final-user-score">
              {activePoints.toFixed(1)} PTS
            </span>
          </div>
        </div>
      )}

      {/* Live Cricket Scoreboards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4" data-testid="match-scoreboard">
        {/* Innings 1 (MI Batting • CSK Bowling) */}
        <div className={`p-4 rounded-xl border transition-all ${
          currentInnings === 1 && !isMatchCompleted
            ? "bg-slate-850/90 border-blue-500/50 shadow-md shadow-blue-950/20"
            : "bg-slate-950/60 border-slate-800/80 opacity-80"
        }`}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-blue-400">1st Innings: MI Batting • CSK Bowling</span>
            {currentInnings === 1 && !isMatchCompleted && (
              <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300">
                CURRENT INNINGS
              </span>
            )}
            {(currentInnings === 2 || isMatchCompleted) && (
              <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                INNINGS COMPLETED
              </span>
            )}
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black text-white font-mono" data-testid="inn1-score">
              {inn1.runs || 0}/{inn1.wickets || 0}
            </span>
            <span className="text-xs text-slate-400 font-mono" data-testid="inn1-overs">
              ({inn1.overs || "0.0"} / 20.0 ov)
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            Shardul Thakur: 4.0 ov, 1/29, 1 maiden (43.0 pts locked) • Deepak Chahar: 1/35 • Pathirana: 2/28
          </p>
        </div>

        {/* Innings 2 (CSK Batting Chase) */}
        <div className={`p-4 rounded-xl border transition-all ${
          currentInnings === 2 && !isMatchCompleted
            ? "bg-slate-850/90 border-purple-500/50 shadow-md shadow-purple-950/20"
            : "bg-slate-950/60 border-slate-800/80 opacity-80"
        }`}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-purple-400">2nd Innings: CSK Batting Chase</span>
            {currentInnings === 2 && !isMatchCompleted && (
              <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300">
                CHASE IN PROGRESS
              </span>
            )}
            {isMatchCompleted && (
              <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
                MATCH COMPLETED
              </span>
            )}
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black text-white font-mono" data-testid="inn2-score">
              {inn2.runs || 0}/{inn2.wickets || 0}
            </span>
            <span className="text-xs text-slate-400 font-mono" data-testid="inn2-overs">
              ({inn2.overs || "0.0"} / 20.0 ov)
            </span>
            {currentInnings === 2 && !isMatchCompleted && (
              <span className="text-xs text-purple-300 ml-auto font-mono font-bold" data-testid="inn2-target-status">
                Target: {inn2.target || 183} | Need {inn2.required_runs ?? 183} runs
              </span>
            )}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            Impact Player: Marcus Stoinis (32 runs off 18 balls • 32.0 active pts)
          </p>
        </div>
      </div>

      {/* Fantasy Points Dashboard (Active vs Historical Locked) */}
      <div className="bg-slate-950/80 rounded-xl border border-slate-800 p-3.5 mb-5" data-testid="fantasy-score-dashboard">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 items-center">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-purple-600/20 text-purple-400 border border-purple-500/30">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs text-slate-400 block font-medium">Active Fantasy Team Score</span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-black text-white font-mono" data-testid="active-fantasy-score">
                  {activePoints.toFixed(1)}
                </span>
                <span className="text-xs font-mono text-emerald-400 font-semibold">Active Eligible Total</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3 sm:border-l sm:border-slate-800 sm:pl-4">
            <div className="p-2.5 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30">
              <AlertCircle className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs text-slate-400 block font-medium">Locked Historical Ledger Points</span>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-black text-amber-300 font-mono" data-testid="historical-fantasy-score">
                  {historicalPoints.toFixed(1)}
                </span>
                <span className="text-xs font-mono text-slate-400 font-semibold">Preserved in DB</span>
              </div>
            </div>
          </div>
        </div>

        {/* Replacement Slot Single-Occupant Rule Callout */}
        {replacementAudit && (
          <div className="mt-3 pt-3 border-t border-slate-800/80 text-xs text-slate-300 flex items-start gap-2" data-testid="replacement-audit-banner">
            <span className="px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 font-mono font-bold text-[10px] shrink-0">
              SINGLE-OCCUPANT SCORING
            </span>
            <p className="leading-relaxed">
              <strong className="text-purple-300">{replacementAudit.active_player_in_name}</strong> contributes <strong className="text-white">{replacementAudit.active_player_in_points.toFixed(1)} pts</strong> to the active team total. Replaced player <strong className="text-slate-300">{replacementAudit.replaced_player_out_name}</strong>'s <strong className="text-amber-300">{replacementAudit.replaced_player_historical_points.toFixed(1)} historical pts</strong> remain preserved in the locked Innings 1 ledger but are excluded from active score (they do not sum to { (replacementAudit.active_player_in_points + replacementAudit.replaced_player_historical_points).toFixed(1) } pts).
            </p>
          </div>
        )}
      </div>

      {/* Simulator Action Controls */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider font-mono">
            Interactive Step Controls
          </span>
          <span className="text-[11px] text-purple-400 font-mono">
            {isMatchCompleted ? "Match Completed — Simulation Locked" : "Pulsing Button = Recommended Step"}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
          {/* Step 1: Toss */}
          <button
            onClick={() => onStepSimulation("TOSS")}
            disabled={isLoading || phase !== "PRE_MATCH" || isMatchCompleted}
            data-testid="step-toss-btn"
            className={`flex flex-col items-center justify-center p-2.5 rounded-xl text-xs font-medium transition-all ${
              isTossNext
                ? "bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-600/30 ring-2 ring-purple-400 animate-pulse font-bold"
                : "bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700 disabled:opacity-30 disabled:pointer-events-none"
            }`}
          >
            <span className="text-base mb-1">🪙</span>
            <span>1. Conduct Toss</span>
            <span className="text-[9px] opacity-80 font-mono">MI won & bat</span>
          </button>

          {/* Step 2: Lineups */}
          <button
            onClick={() => onStepSimulation("LINEUP")}
            disabled={isLoading || (phase !== "TOSS_CONDUCTED" && phase !== "PRE_MATCH") || isMatchCompleted}
            data-testid="step-lineup-btn"
            className={`flex flex-col items-center justify-center p-2.5 rounded-xl text-xs font-medium transition-all ${
              isLineupNext
                ? "bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-600/30 ring-2 ring-purple-400 animate-pulse font-bold"
                : "bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700 disabled:opacity-30 disabled:pointer-events-none"
            }`}
          >
            <UserCheck className="w-4 h-4 mb-1 text-purple-300" />
            <span>2. Confirm Lineups</span>
            <span className="text-[9px] opacity-80 font-mono">Scenario 1 Sub</span>
          </button>

          {/* Step 3: Ball */}
          <button
            onClick={() => onStepSimulation("BALL")}
            disabled={isLoading || phase === "PRE_MATCH" || isInningsEnded || isMatchCompleted}
            data-testid="step-ball-btn"
            className="flex flex-col items-center justify-center p-2.5 rounded-xl bg-slate-800 hover:bg-slate-750 disabled:opacity-30 disabled:pointer-events-none text-slate-200 border border-slate-700 text-xs font-medium transition-all"
          >
            <Play className="w-4 h-4 mb-1 text-emerald-400" />
            <span>Simulate Ball</span>
            <span className="text-[9px] text-slate-400 font-mono">Next 1 Ball</span>
          </button>

          {/* Step 4: Over */}
          <button
            onClick={() => onStepSimulation("OVER")}
            disabled={isLoading || phase === "PRE_MATCH" || isInningsEnded || isMatchCompleted}
            data-testid="step-over-btn"
            className="flex flex-col items-center justify-center p-2.5 rounded-xl bg-slate-800 hover:bg-slate-750 disabled:opacity-30 disabled:pointer-events-none text-slate-200 border border-slate-700 text-xs font-medium transition-all"
          >
            <FastForward className="w-4 h-4 mb-1 text-emerald-400" />
            <span>Simulate Over</span>
            <span className="text-[9px] text-slate-400 font-mono">Full 6 Balls</span>
          </button>

          {/* Step 5: Jump to 2nd Innings */}
          <button
            onClick={() => onStepSimulation("INN2_JUMP")}
            disabled={isLoading || currentInnings === 2 || isMatchCompleted}
            data-testid="step-inn2-btn"
            className={`flex flex-col items-center justify-center p-2.5 rounded-xl text-xs font-medium transition-all ${
              isInnings2Next
                ? "bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-600/30 ring-2 ring-purple-400 animate-pulse font-bold"
                : "bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700 disabled:opacity-30 disabled:pointer-events-none"
            }`}
          >
            <ArrowRight className="w-4 h-4 mb-1 text-purple-300" />
            <span>Jump to Innings 2</span>
            <span className="text-[9px] opacity-80 font-mono">Lock 1st Inn (43 pts)</span>
          </button>

          {/* Step 6: Trigger Real Impact Player */}
          <button
            onClick={onTriggerImpact}
            disabled={isLoading || currentInnings !== 2 || isMatchCompleted}
            data-testid="trigger-impact-btn"
            className={`flex flex-col items-center justify-center p-2.5 rounded-xl text-xs font-medium transition-all ${
              isImpactNext
                ? "bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-lg shadow-purple-600/30 ring-2 ring-purple-400 animate-pulse font-bold"
                : "bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700 disabled:opacity-30 disabled:pointer-events-none"
            }`}
          >
            <Flame className="w-4 h-4 mb-1 text-yellow-300" />
            <span>Trigger Impact Sub</span>
            <span className="text-[9px] opacity-90 font-mono">Scenario 2 Sub</span>
          </button>
        </div>
      </div>
    </div>
  );
}
