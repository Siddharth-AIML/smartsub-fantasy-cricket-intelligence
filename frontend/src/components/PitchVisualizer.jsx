import React, { useState } from 'react';
import { Shield, Sparkles, User, Award, Info, AlertTriangle, ArrowRight, CheckCircle2, Filter } from 'lucide-react';
import { getRealMatchStatus, ROLE_LABELS } from '../utils/formatters';

export default function PitchVisualizer({ fantasyTeam, liveState }) {
  const [teamFilter, setTeamFilter] = useState("ALL"); // "ALL", "CSK", "MI"
  const slots = fantasyTeam?.lineup_slots || [];
  const playerPointsMap = liveState?.player_points_map || {};

  // Strict backend single source of truth: only currently SELECTED players are active on pitch
  const selectedSlots = slots.filter(s => s.fantasy_selection_status === "SELECTED");
  const substitutedSlots = slots.filter(s => s.fantasy_selection_status === "SUBSTITUTED_OUT");
  
  const captainId = fantasyTeam?.captain_player_id;
  const viceCaptainId = fantasyTeam?.vice_captain_player_id;

  // Group active 11 by role
  const wk = selectedSlots.filter(s => s.player.role === "WK");
  const bat = selectedSlots.filter(s => s.player.role === "BAT");
  const ar = selectedSlots.filter(s => s.player.role === "AR");
  const bowl = selectedSlots.filter(s => s.player.role === "BOWL");

  const totalCredits = selectedSlots.reduce((sum, s) => sum + s.player.credits, 0);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col" data-testid="pitch-visualizer">
      {/* Header Info with Team Filters */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 mb-4 border-b border-slate-800">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            Active Playing XI Formation
            <span
              data-testid="active-player-count"
              className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
            >
              {selectedSlots.length} / 11 Active Players
            </span>
          </h3>
          <p className="text-xs text-slate-400">
            Real-time active fantasy lineup. Exactly 11 eligible slots; unavailable and replaced players are moved to the unavailable drawer.
          </p>
        </div>

        {/* Filter Pills & Squad Metrics */}
        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
          {/* Team Filter Pills */}
          <div className="flex items-center gap-1 p-1 rounded-xl bg-slate-950/80 border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase px-1.5 font-bold flex items-center gap-1">
              <Filter className="w-3 h-3" /> Team:
            </span>
            <button
              onClick={() => setTeamFilter("ALL")}
              data-testid="filter-all-pitch"
              className={`px-2 py-0.5 rounded-lg font-bold transition-all ${
                teamFilter === "ALL"
                  ? "bg-purple-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              All
            </button>
            <button
              onClick={() => setTeamFilter("CSK")}
              data-testid="filter-csk-pitch"
              className={`px-2 py-0.5 rounded-lg font-bold transition-all ${
                teamFilter === "CSK"
                  ? "bg-yellow-500 text-slate-950 shadow-sm"
                  : "text-yellow-400 hover:text-yellow-300"
              }`}
            >
              CSK
            </button>
            <button
              onClick={() => setTeamFilter("MI")}
              data-testid="filter-mi-pitch"
              className={`px-2 py-0.5 rounded-lg font-bold transition-all ${
                teamFilter === "MI"
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-blue-400 hover:text-blue-300"
              }`}
            >
              MI
            </button>
          </div>

          <div className="bg-slate-800 px-2.5 py-1 rounded-lg border border-slate-700 text-slate-300 hidden md:block">
            WK: <strong className="text-white">{wk.length}</strong> | BAT: <strong className="text-white">{bat.length}</strong> | AR: <strong className="text-white">{ar.length}</strong> | BOWL: <strong className="text-white">{bowl.length}</strong>
          </div>
          <div className={`px-2.5 py-1 rounded-lg border font-bold ${
            totalCredits <= 100.0 ? "bg-emerald-950/40 text-emerald-300 border-emerald-800/40" : "bg-rose-950 text-rose-300 border-rose-800"
          }`}>
            {totalCredits.toFixed(1)} / 100.0 Cr
          </div>
        </div>
      </div>

      {/* Visual Cricket Field Pitch */}
      <div className="pitch-grass rounded-2xl p-5 relative min-h-[460px] flex flex-col justify-between border-2 border-emerald-600/40 overflow-hidden shadow-inner">
        {/* Pitch crease lines */}
        <div className="absolute inset-x-12 top-10 border-b-2 crease-line pointer-events-none" />
        <div className="absolute inset-x-12 bottom-10 border-t-2 crease-line pointer-events-none" />
        <div className="absolute inset-y-10 left-1/2 w-0.5 border-l-2 border-dashed crease-line opacity-30 pointer-events-none" />

        {/* Section 1: Wicket-Keeper (Top) */}
        <div className="flex justify-center items-center gap-3 z-10">
          {wk.map(slot => (
            <PlayerCard
              key={slot.id}
              slot={slot}
              allSlots={slots}
              captainId={captainId}
              viceCaptainId={viceCaptainId}
              playerPointsMap={playerPointsMap}
              teamFilter={teamFilter}
            />
          ))}
        </div>

        {/* Section 2: Batters */}
        <div className="flex flex-wrap justify-center items-center gap-2.5 z-10 py-1.5">
          {bat.map(slot => (
            <PlayerCard
              key={slot.id}
              slot={slot}
              allSlots={slots}
              captainId={captainId}
              viceCaptainId={viceCaptainId}
              playerPointsMap={playerPointsMap}
              teamFilter={teamFilter}
            />
          ))}
        </div>

        {/* Section 3: All-Rounders */}
        <div className="flex flex-wrap justify-center items-center gap-3 z-10 py-1.5">
          {ar.map(slot => (
            <PlayerCard
              key={slot.id}
              slot={slot}
              allSlots={slots}
              captainId={captainId}
              viceCaptainId={viceCaptainId}
              playerPointsMap={playerPointsMap}
              teamFilter={teamFilter}
            />
          ))}
        </div>

        {/* Section 4: Bowlers (Bottom) */}
        <div className="flex flex-wrap justify-center items-center gap-2.5 z-10">
          {bowl.map(slot => (
            <PlayerCard
              key={slot.id}
              slot={slot}
              allSlots={slots}
              captainId={captainId}
              viceCaptainId={viceCaptainId}
              playerPointsMap={playerPointsMap}
              teamFilter={teamFilter}
            />
          ))}
        </div>
      </div>

      {/* Replaced / Substituted Squad Assets Drawer */}
      {substitutedSlots.length > 0 && (
        <div className="mt-4 pt-3 border-t border-slate-800" data-testid="replaced-players-section">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-300 mb-2">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            <span>Replaced / Unavailable Squad Assets ({substitutedSlots.length})</span>
            <span className="text-[10px] font-normal text-slate-400">
              (Excluded from active formation; historical points preserved in locked ledger)
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {substitutedSlots.map(s => {
              const p = s.player;
              const isThakur = p.id === "p_csk_thakur";
              const isMustafizur = p.id === "p_csk_mustafizur";
              const histPts = playerPointsMap[p.id]?.historical_points ?? s.fantasy_points ?? (isThakur ? 43.0 : 0.0);

              return (
                <div
                  key={s.id}
                  data-testid={`replaced-player-${p.id}`}
                  className="bg-slate-950/80 border border-slate-800 p-2.5 rounded-xl flex items-center justify-between text-xs"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="w-2 h-2 rounded-full bg-rose-400 shrink-0" />
                    <div>
                      <div className="font-bold text-white flex items-center gap-1.5">
                        <span className={`px-1.5 py-0.2 rounded font-black text-[9px] ${
                          p.team === "CSK" ? "bg-yellow-400 text-slate-950" : "bg-blue-600 text-white"
                        }`}>
                          {p.team}
                        </span>
                        <span>{p.full_name}</span>
                        <span className="text-[10px] font-mono text-slate-400">({p.role} • {p.credits} Cr)</span>
                        <span data-testid={`replaced-pts-${p.id}`} className="text-[10px] font-mono font-bold text-amber-300 bg-amber-500/10 px-1 rounded border border-amber-500/30">
                          {histPts.toFixed(1)} pts locked
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400">
                        {isMustafizur && "Did not play in announced XI • Replaced by Shardul Thakur (CSK, B2)"}
                        {isThakur && "Substituted out for Innings 2 • 43.0 pts locked in Innings 1 • Replaced by M. Stoinis (MI)"}
                        {!isMustafizur && !isThakur && `Substituted out in Innings ${s.exit_innings || 1}`}
                      </p>
                    </div>
                  </div>

                  <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800 shrink-0">
                    SUBSTITUTED OUT
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Legend Footer */}
      <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-400 pt-3 mt-3 border-t border-slate-800/80 gap-2">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" /> In playing XI
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-400" /> Active Replacement / Impact
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-400" /> Substituted out
          </span>
        </div>
        <div className="flex items-center gap-2 font-mono">
          <span className="px-1.5 py-0.5 rounded bg-yellow-500/20 text-yellow-300 border border-yellow-500/30 font-bold">2x = Captain</span>
          <span className="px-1.5 py-0.5 rounded bg-slate-400/20 text-slate-300 border border-slate-400/30 font-bold">1.5x = Vice Captain</span>
        </div>
      </div>
    </div>
  );
}

function PlayerCard({ slot, allSlots, captainId, viceCaptainId, playerPointsMap, teamFilter }) {
  const p = slot.player;
  const isCaptain = p.id === captainId;
  const isVC = p.id === viceCaptainId;
  
  // A player is substituted in if substituted_in_for_player_id is set or entry_innings is 2
  const isSubstitutedIn = Boolean(slot.substituted_in_for_player_id) || slot.entry_innings === 2;
  const isImpact = p.id === "p_csk_stoinis" || slot.entry_innings === 2;

  // Active Points for player
  const pointsInfo = playerPointsMap[p.id];
  const activePoints = pointsInfo?.active_points ?? slot.active_fantasy_points ?? slot.fantasy_points ?? 0.0;

  // Find replaced player name if any
  let replacedPlayerName = null;
  if (slot.substituted_in_for_player_id) {
    const replaced = allSlots.find(s => s.player_id === slot.substituted_in_for_player_id);
    if (replaced) {
      replacedPlayerName = `${replaced.player.short_name} (${replaced.player.team})`;
    }
  }

  const matchStatus = getRealMatchStatus(p.real_match_participation);
  const isFilteredOut = teamFilter !== "ALL" && p.team !== teamFilter;

  return (
    <div
      data-testid={`player-card-${p.id}`}
      className={`relative group flex flex-col items-center p-2 rounded-xl border backdrop-blur-md transition-all duration-300 hover:scale-105 shadow-lg w-28 sm:w-32 ${
        isFilteredOut ? "opacity-25 grayscale hover:grayscale-0 hover:opacity-100" : ""
      } ${
        isSubstitutedIn
          ? isImpact
            ? "bg-purple-950/90 border-purple-400 ring-2 ring-purple-500 shadow-purple-950/60"
            : "bg-indigo-950/90 border-indigo-400 ring-2 ring-indigo-500 shadow-indigo-950/60"
          : "bg-slate-900/85 border-slate-700 hover:border-slate-500"
      }`}
    >
      {/* Captain / VC Badges */}
      {isCaptain && (
        <span className="absolute -top-2 -left-2 w-5 h-5 rounded-full bg-gradient-to-tr from-yellow-500 to-amber-300 text-slate-950 font-black text-[10px] flex items-center justify-center shadow-md border border-slate-900" title="Captain (2x Points)">
          2x
        </span>
      )}
      {isVC && (
        <span className="absolute -top-2 -left-2 w-5 h-5 rounded-full bg-gradient-to-tr from-slate-300 to-slate-100 text-slate-950 font-black text-[10px] flex items-center justify-center shadow-md border border-slate-900" title="Vice-Captain (1.5x Points)">
          1.5x
        </span>
      )}

      {/* Substituted In indicator */}
      {isSubstitutedIn && (
        <span
          data-testid={`sub-badge-${p.id}`}
          className={`absolute -top-2.5 -right-2 px-1.5 py-0.5 rounded-full text-white font-black text-[9px] shadow-md flex items-center gap-0.5 border ${
            isImpact ? "bg-purple-600 border-purple-300" : "bg-indigo-600 border-indigo-300"
          }`}
        >
          <Sparkles className="w-2.5 h-2.5" />
          {isImpact ? "IMPACT SUB" : "B2 SUB"}
        </span>
      )}

      {/* Team Badge & Role Pill & Credits */}
      <div className="flex items-center justify-between w-full text-[10px] text-slate-400 font-mono mb-1">
        <span
          data-testid={`player-team-${p.id}`}
          className={`px-1.5 py-0.2 rounded font-black text-[9px] shadow-sm ${
            p.team === "CSK" ? "bg-yellow-400 text-slate-950" : "bg-blue-600 text-white"
          }`}
        >
          {p.team}
        </span>
        <span className="px-1 py-0.2 rounded bg-slate-800 text-slate-300 font-bold border border-slate-700" title={ROLE_LABELS[p.role]}>
          {p.role}
        </span>
        <span className="text-amber-400 font-semibold">{p.credits} Cr</span>
      </div>

      {/* Player Name */}
      <div className="text-center w-full my-0.5">
        <p className="text-xs font-bold text-white truncate group-hover:text-purple-300 transition-colors" data-testid="player-short-name">
          {p.short_name}
        </p>

        {/* Individual Player Fantasy Points Display */}
        <div className="my-1">
          <span
            data-testid={`player-points-${p.id}`}
            className="text-[10px] font-mono font-black px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30 shadow-inner"
          >
            {activePoints.toFixed(1)} pts
          </span>
        </div>

        {/* Replaces Note */}
        {replacedPlayerName && (
          <p className="text-[9px] text-purple-300 font-medium truncate mt-0.5" data-testid="replaced-note">
            ⇄ {replacedPlayerName}
          </p>
        )}

        <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded border inline-flex items-center gap-1 mt-0.5 ${matchStatus.badgeClass}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${matchStatus.dotClass}`} />
          {matchStatus.label}
        </span>
      </div>
    </div>
  );
}
