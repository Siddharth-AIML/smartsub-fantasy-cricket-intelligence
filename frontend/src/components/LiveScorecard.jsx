import React, { useState } from 'react';
import { Award, Shield, User, Activity, AlertCircle, Filter } from 'lucide-react';

export default function LiveScorecard({ liveState }) {
  const [selectedTeamFilter, setSelectedTeamFilter] = useState("ALL"); // "ALL", "CSK", "MI"
  const scorecard = liveState?.scorecard || {};
  const inn1 = scorecard?.innings_1 || {};
  const inn2 = scorecard?.innings_2 || {};
  const liveMatch = scorecard?.live_match || {};
  const playerPointsMap = liveState?.player_points_map || {};

  const filterBatters = (batters, team) => {
    if (selectedTeamFilter === "ALL") return batters || [];
    return (batters || []).filter(b => (b.team || team) === selectedTeamFilter);
  };

  const filterBowlers = (bowlers, bowlingTeam) => {
    if (selectedTeamFilter === "ALL") return bowlers || [];
    return (bowlers || []).filter(b => (b.team || bowlingTeam) === selectedTeamFilter);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col" data-testid="live-scorecard-centre">
      {/* Header with Title and Team Filters */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-4 mb-4 border-b border-slate-800 gap-3">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            Match Centre & Real Cricket Scorecard
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/30">
              Official IPL Format
            </span>
          </h3>
          <p className="text-xs text-slate-400">
            Granular ball-by-ball batting and bowling scorecards with live strike rates, bowling economies & fantasy points
          </p>
        </div>

        {/* Team Filter Pills */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-950/80 border border-slate-800 text-xs font-mono">
          <span className="text-[10px] text-slate-500 uppercase px-2 font-bold flex items-center gap-1">
            <Filter className="w-3 h-3" /> Filter:
          </span>
          <button
            onClick={() => setSelectedTeamFilter("ALL")}
            data-testid="filter-all-scorecard"
            className={`px-2.5 py-1 rounded-lg font-bold transition-all ${
              selectedTeamFilter === "ALL"
                ? "bg-purple-600 text-white shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            All Players
          </button>
          <button
            onClick={() => setSelectedTeamFilter("CSK")}
            data-testid="filter-csk-scorecard"
            className={`px-2.5 py-1 rounded-lg font-bold transition-all ${
              selectedTeamFilter === "CSK"
                ? "bg-yellow-500 text-slate-950 shadow-sm"
                : "text-yellow-400 hover:text-yellow-300"
            }`}
          >
            CSK
          </button>
          <button
            onClick={() => setSelectedTeamFilter("MI")}
            data-testid="filter-mi-scorecard"
            className={`px-2.5 py-1 rounded-lg font-bold transition-all ${
              selectedTeamFilter === "MI"
                ? "bg-blue-600 text-white shadow-sm"
                : "text-blue-400 hover:text-blue-300"
            }`}
          >
            MI
          </button>
        </div>
      </div>

      {/* Live In-Play Match Mini-Bar */}
      {liveMatch && (
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 mb-5 text-xs font-mono">
          <div className="flex flex-col">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Striker *</span>
            <span className="font-bold text-white text-sm" data-testid="live-striker">
              {liveMatch.striker || "R. Sharma (MI)"}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Non-Striker</span>
            <span className="font-semibold text-slate-300 text-sm" data-testid="live-non-striker">
              {liveMatch.non_striker || "S. Yadav (MI)"}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Current Bowler</span>
            <span className="font-bold text-purple-300 text-sm" data-testid="live-bowler">
              {liveMatch.bowler || "S. Thakur (CSK)"}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Recent Deliveries</span>
            <span className="font-mono text-emerald-400 font-bold text-sm" data-testid="recent-overs-summary">
              {liveMatch.recent_deliveries || "1 • 4 • 0 • W • 2 • 1"}
            </span>
          </div>
        </div>
      )}

      {/* Innings 1 Scorecard */}
      <div className="mb-6" data-testid="scorecard-innings-1">
        <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded font-black text-xs bg-blue-600 text-white font-mono">
              MI
            </span>
            <span className="font-bold text-sm text-white">
              1st Innings: Mumbai Indians Batting
            </span>
            <span className="text-xs text-slate-400 font-mono">
              ({inn1.runs || 182}/{inn1.wickets || 6} in {inn1.overs || "20.0"} ov)
            </span>
          </div>
          <span className="text-[11px] font-mono text-slate-400">
            CRR: {inn1.overs ? ((inn1.runs || 182) / Math.max(1, parseFloat(inn1.overs))).toFixed(2) : "9.10"}
          </span>
        </div>

        {/* 1st Inn Batting Table */}
        <div className="overflow-x-auto mb-3">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="text-slate-400 border-b border-slate-800 bg-slate-850/50">
                <th className="py-2 px-3">Batter</th>
                <th className="py-2 px-3">Dismissal</th>
                <th className="py-2 px-3 text-right">R</th>
                <th className="py-2 px-3 text-right">B</th>
                <th className="py-2 px-3 text-right">4s</th>
                <th className="py-2 px-3 text-right">6s</th>
                <th className="py-2 px-3 text-right">SR</th>
                <th className="py-2 px-3 text-right text-purple-400">Pts</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-200">
              {filterBatters(inn1.batters, "MI").map((b, idx) => (
                <tr key={idx} className="hover:bg-slate-800/40">
                  <td className="py-2 px-3 font-semibold text-white flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                    {b.name}
                  </td>
                  <td className="py-2 px-3 text-slate-400 text-[11px]">{b.dismissal}</td>
                  <td className="py-2 px-3 text-right font-bold text-white">{b.runs}</td>
                  <td className="py-2 px-3 text-right text-slate-400">{b.balls}</td>
                  <td className="py-2 px-3 text-right text-slate-300">{b.fours}</td>
                  <td className="py-2 px-3 text-right text-slate-300">{b.sixes}</td>
                  <td className="py-2 px-3 text-right text-slate-400">{b.sr}</td>
                  <td className="py-2 px-3 text-right font-bold text-amber-300">{b.pts}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* 1st Inn Bowling Table (CSK Bowling) */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="text-slate-400 border-b border-slate-800 bg-slate-850/50">
                <th className="py-2 px-3">Bowler (CSK)</th>
                <th className="py-2 px-3 text-right">O</th>
                <th className="py-2 px-3 text-right">M</th>
                <th className="py-2 px-3 text-right">R</th>
                <th className="py-2 px-3 text-right">W</th>
                <th className="py-2 px-3 text-right">ECON</th>
                <th className="py-2 px-3 text-right text-purple-400">Pts</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-200">
              {filterBowlers(inn1.bowlers, "CSK").map((bw, idx) => (
                <tr key={idx} className={`hover:bg-slate-800/40 ${bw.name.includes("Thakur") ? "bg-purple-950/20 font-bold" : ""}`}>
                  <td className="py-2 px-3 font-semibold text-white flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-yellow-400" />
                    {bw.name}
                    {bw.name.includes("Thakur") && (
                      <span className="text-[9px] px-1.5 py-0.2 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                        B2 SUB
                      </span>
                    )}
                  </td>
                  <td className="py-2 px-3 text-right text-slate-300">{bw.overs}</td>
                  <td className="py-2 px-3 text-right text-slate-400">{bw.maidens}</td>
                  <td className="py-2 px-3 text-right text-slate-300">{bw.runs}</td>
                  <td className="py-2 px-3 text-right font-bold text-emerald-400">{bw.wickets}</td>
                  <td className="py-2 px-3 text-right text-slate-400">{bw.econ}</td>
                  <td className="py-2 px-3 text-right font-bold text-amber-300">{bw.pts}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Innings 2 Scorecard (CSK Chase) */}
      <div data-testid="scorecard-innings-2">
        <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded font-black text-xs bg-yellow-500 text-slate-950 font-mono">
              CSK
            </span>
            <span className="font-bold text-sm text-white">
              2nd Innings: Chennai Super Kings Chase
            </span>
            <span className="text-xs text-slate-400 font-mono">
              ({inn2.runs || 0}/{inn2.wickets || 0} in {inn2.overs || "0.0"} ov • Target: 183)
            </span>
          </div>
          <span className="text-[11px] font-mono text-purple-300 font-bold">
            Required: {inn2.required_runs ?? 183} runs
          </span>
        </div>

        {/* 2nd Inn Batting Table */}
        <div className="overflow-x-auto mb-3">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="text-slate-400 border-b border-slate-800 bg-slate-850/50">
                <th className="py-2 px-3">Batter</th>
                <th className="py-2 px-3">Dismissal</th>
                <th className="py-2 px-3 text-right">R</th>
                <th className="py-2 px-3 text-right">B</th>
                <th className="py-2 px-3 text-right">4s</th>
                <th className="py-2 px-3 text-right">6s</th>
                <th className="py-2 px-3 text-right">SR</th>
                <th className="py-2 px-3 text-right text-purple-400">Pts</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-200">
              {filterBatters(inn2.batters, "CSK").map((b, idx) => (
                <tr key={idx} className={`hover:bg-slate-800/40 ${b.name.includes("Stoinis") ? "bg-purple-950/20 font-bold" : ""}`}>
                  <td className="py-2 px-3 font-semibold text-white flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-yellow-400" />
                    {b.name}
                    {b.name.includes("Stoinis") && (
                      <span className="text-[9px] px-1.5 py-0.2 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                        IMPACT SUB
                      </span>
                    )}
                  </td>
                  <td className="py-2 px-3 text-slate-400 text-[11px]">{b.dismissal}</td>
                  <td className="py-2 px-3 text-right font-bold text-white">{b.runs}</td>
                  <td className="py-2 px-3 text-right text-slate-400">{b.balls}</td>
                  <td className="py-2 px-3 text-right text-slate-300">{b.fours}</td>
                  <td className="py-2 px-3 text-right text-slate-300">{b.sixes}</td>
                  <td className="py-2 px-3 text-right text-slate-400">{b.sr}</td>
                  <td className="py-2 px-3 text-right font-bold text-amber-300">{b.pts}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* 2nd Inn Bowling Table (MI Bowling) */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="text-slate-400 border-b border-slate-800 bg-slate-850/50">
                <th className="py-2 px-3">Bowler (MI)</th>
                <th className="py-2 px-3 text-right">O</th>
                <th className="py-2 px-3 text-right">M</th>
                <th className="py-2 px-3 text-right">R</th>
                <th className="py-2 px-3 text-right">W</th>
                <th className="py-2 px-3 text-right">ECON</th>
                <th className="py-2 px-3 text-right text-purple-400">Pts</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-200">
              {filterBowlers(inn2.bowlers, "MI").map((bw, idx) => (
                <tr key={idx} className="hover:bg-slate-800/40">
                  <td className="py-2 px-3 font-semibold text-white flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                    {bw.name}
                  </td>
                  <td className="py-2 px-3 text-right text-slate-300">{bw.overs}</td>
                  <td className="py-2 px-3 text-right text-slate-400">{bw.maidens}</td>
                  <td className="py-2 px-3 text-right text-slate-300">{bw.runs}</td>
                  <td className="py-2 px-3 text-right font-bold text-emerald-400">{bw.wickets}</td>
                  <td className="py-2 px-3 text-right text-slate-400">{bw.econ}</td>
                  <td className="py-2 px-3 text-right font-bold text-amber-300">{bw.pts}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
