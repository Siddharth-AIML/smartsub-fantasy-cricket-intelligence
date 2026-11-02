import React from 'react';
import { ShieldCheck, BookOpen, RotateCcw, RefreshCw, Cpu, Database, Trophy } from 'lucide-react';
import { getMatchPhase } from '../utils/formatters';

export default function Header({
  healthInfo,
  liveState,
  onOpenRulesModal,
  onResetMatch,
  onReplayMatch,
  isLoading
}) {
  const scoreboard = liveState?.scoreboard || {};
  const phase = scoreboard?.phase || "PRE_MATCH";
  const isMatchCompleted = phase === "COMPLETED" || liveState?.status === "COMPLETED";
  const activePoints = liveState?.fantasy_active_points ?? liveState?.fantasy_total_points ?? 0.0;

  return (
    <header className="border-b border-purple-900/30 bg-slate-900/90 backdrop-blur-md sticky top-0 z-40 px-4 lg:px-8 py-3.5 shadow-md">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-purple-600/30 text-white font-black text-xl">
            🏏
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                SmartSub
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-purple-500/15 text-purple-300 border border-purple-500/30">
                  AI Fantasy Intelligence
                </span>
              </h1>
              {/* Illustrative Provenance Watermark */}
              <span className="text-[10px] font-mono tracking-wider px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                [DEMO DATA: ILLUSTRATIVE SIMULATION]
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Cricket Match Simulator & Deterministic Substitution Engine • CSK vs MI
            </p>
          </div>
        </div>

        {/* Live Status and Action Controls */}
        <div className="flex items-center flex-wrap gap-2.5">
          {/* Match Status Header Pill */}
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-800 border border-slate-700 text-xs font-mono" data-testid="header-match-status">
            <span className={`w-2 h-2 rounded-full ${isMatchCompleted ? "bg-emerald-400" : "bg-purple-400 animate-pulse"}`} />
            <span className="text-slate-400">Match:</span>
            <span className="text-white font-bold">{getMatchPhase(phase)}</span>
          </div>

          {/* Final Score Pill (when completed) */}
          {isMatchCompleted && (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-xs font-mono font-bold shadow-md" data-testid="header-final-score">
              <Trophy className="w-3.5 h-3.5 text-yellow-300" />
              <span>Final: {activePoints.toFixed(1)} PTS</span>
            </div>
          )}

          <button
            onClick={onOpenRulesModal}
            data-testid="rules-evidence-btn"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-950/60 hover:bg-purple-900/80 text-purple-200 border border-purple-700/50 text-xs font-medium transition-all shadow-sm"
          >
            <BookOpen className="w-3.5 h-3.5 text-purple-400" />
            Rule Evidence Register
          </button>

          <button
            onClick={onReplayMatch}
            disabled={isLoading}
            data-testid="replay-demo-btn"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700 text-xs font-medium transition-all"
            title="Replays all match events deterministically from t=0"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            Deterministic Replay
          </button>

          <button
            onClick={onResetMatch}
            disabled={isLoading}
            data-testid="reset-demo-btn"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border border-rose-800/40 text-xs font-medium transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset Match
          </button>

          {/* System Status Pill */}
          <div className="flex items-center gap-2 pl-2 border-l border-slate-800 text-xs text-slate-400">
            <span className="flex items-center gap-1" title="Dual-Adapter: SQLite default, PostgreSQL production">
              <Database className="w-3.5 h-3.5 text-emerald-400" />
              <span className="font-mono text-[11px] text-emerald-400">SQLite/Dual</span>
            </span>
            <span className="flex items-center gap-1">
              <Cpu className="w-3.5 h-3.5 text-purple-400" />
              <span className="font-mono text-[11px] text-purple-300">
                {healthInfo?.has_gemini_api_key ? "Gemini 2.5" : "Fallback Rationale"}
              </span>
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
