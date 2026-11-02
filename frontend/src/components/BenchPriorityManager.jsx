import React from 'react';
import { ArrowUp, ArrowDown, Info, HelpCircle, CheckCircle, ArrowRightCircle, AlertTriangle, ShieldCheck } from 'lucide-react';
import { getRealMatchStatus, getFantasyStatus, PRIORITY_EXPLANATIONS } from '../utils/formatters';

export default function BenchPriorityManager({
  fantasyTeam,
  liveState,
  onUpdatePriorities,
  isLoading
}) {
  const slots = fantasyTeam?.lineup_slots || [];
  const playerPointsMap = liveState?.player_points_map || {};

  const isSelected = (status) => {
    if (!status) return false;
    const s = typeof status === "object" ? (status.value || status.name || "") : String(status);
    return s.toUpperCase() === "SELECTED";
  };

  const isSubstitutedOut = (status) => {
    if (!status) return false;
    const s = typeof status === "object" ? (status.value || status.name || "") : String(status);
    return s.toUpperCase() === "SUBSTITUTED_OUT";
  };

  const benchSlots = slots
    .filter(s => s.slot_type === "BACKUP" || (s.priority_rank != null && s.slot_type !== "STARTER"))
    .sort((a, b) => (a.priority_rank || 0) - (b.priority_rank || 0));

  // Replaced / Substituted players
  const substitutedSlots = slots.filter(s => isSubstitutedOut(s.fantasy_selection_status));

  const handleMove = (index, direction) => {
    const targetIndex = index + direction;
    if (targetIndex < 0 || targetIndex >= benchSlots.length) return;

    const newSlots = [...benchSlots];
    const temp = newSlots[index];
    newSlots[index] = newSlots[targetIndex];
    newSlots[targetIndex] = temp;

    // Reassign ranks 1 to 4
    const payload = newSlots.map((s, idx) => ({
      player_id: s.player.id,
      priority_rank: idx + 1,
      priority_label: `B${idx + 1}`
    }));

    onUpdatePriorities(payload);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col" data-testid="bench-priority-manager">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            B1–B4 Bench & Squad Priority Manager
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/30">
              Deterministic Priority Order
            </span>
          </h3>
          <p className="text-xs text-slate-400">
            Sequential backup evaluation: B1 evaluated first, then B2, then B3, then B4.
          </p>
        </div>
      </div>

      {/* Priority Helper Callout */}
      <div className="bg-purple-950/25 p-3 rounded-xl border border-purple-800/40 mb-4 text-xs text-slate-300 flex items-start gap-2.5">
        <Info className="w-4 h-4 mt-0.5 text-purple-400 shrink-0" />
        <div>
          <span className="font-semibold text-white">How Priority Works:</span> When an unannounced starter does not play, SmartSub checks <strong className="text-purple-300">B1</strong>. If B1 also does not play (as in Scenario 1), the engine skips B1 with an audit log and evaluates <strong className="text-purple-300">B2</strong>.
        </div>
      </div>

      {/* SECTION A: Active Backup Queue (B1–B4) */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-mono uppercase font-bold text-purple-300 tracking-wider flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-purple-400" />
            Section A: Active Backup Queue (B1–B4)
          </span>
          <span className="text-[11px] font-mono text-slate-400">
            {benchSlots.length} Allocated Backups
          </span>
        </div>

        <div className="space-y-2.5">
          {benchSlots.map((slot, index) => {
            const p = slot.player;
            const rank = index + 1;
            const isSelected = slot.fantasy_selection_status === "SELECTED";
            const isSubstitutedOut = slot.fantasy_selection_status === "SUBSTITUTED_OUT";
            const matchStatus = getRealMatchStatus(p.real_match_participation);
            const fantasyStatus = getFantasyStatus(slot.fantasy_selection_status);
            const tooltip = PRIORITY_EXPLANATIONS[rank];

            // Points
            const ptsInfo = playerPointsMap[p.id];
            const activePts = ptsInfo?.active_points ?? slot.active_fantasy_points ?? 0.0;
            const totalEarnedPts = ptsInfo?.total_points ?? slot.fantasy_points ?? 0.0;

            let queueBadge = null;
            if (isSelected) {
              queueBadge = (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/40 font-bold flex items-center gap-1">
                  <CheckCircle className="w-3 h-3 text-purple-400" />
                  ACTIVE IN PLAYING XI
                </span>
              );
            } else if (p.real_match_participation === "DID_NOT_PLAY") {
              queueBadge = (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950/60 text-rose-400 border border-rose-800">
                  SKIPPED (DID NOT PLAY)
                </span>
              );
            }

            return (
              <div
                key={slot.id}
                data-testid={`backup-row-B${rank}`}
                className={`p-3.5 rounded-xl border flex items-center justify-between transition-all group ${
                  isSelected
                    ? "bg-purple-950/50 border-purple-500 shadow-md ring-1 ring-purple-500/40"
                    : isSubstitutedOut
                    ? "bg-slate-950/80 border-slate-800 opacity-80"
                    : p.real_match_participation === "DID_NOT_PLAY"
                    ? "bg-slate-950/60 border-slate-800/80 opacity-75"
                    : "bg-slate-850/80 border-slate-750 hover:border-purple-500/40"
                }`}
              >
                <div className="flex items-center gap-3">
                  {/* Priority Label Badge with Tooltip */}
                  <div
                    data-testid={`priority-badge-B${rank}`}
                    className={`w-9 h-9 rounded-xl font-mono font-black text-sm flex items-center justify-center border shadow-sm cursor-help relative shrink-0 ${
                      isSelected
                        ? "bg-purple-600 text-white border-purple-400"
                        : "bg-slate-850 text-slate-200 border-slate-700"
                    }`}
                    title={tooltip}
                  >
                    B{rank}
                  </div>

                  {/* Player Details */}
                  <div>
                    <div className="flex items-center gap-2">
                      {/* Team Badge */}
                      <span
                        data-testid={`backup-team-B${rank}`}
                        className={`px-1.5 py-0.2 rounded font-black text-[9px] shadow-sm ${
                          p.team === "CSK" ? "bg-yellow-400 text-slate-950" : "bg-blue-600 text-white"
                        }`}
                      >
                        {p.team}
                      </span>
                      <span className="font-bold text-sm text-white" data-testid={`backup-name-B${rank}`}>
                        {p.full_name}
                      </span>
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                        {p.role} • {p.credits} Cr
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 mt-1">
                      <span className={`text-[10px] font-mono px-2 py-0.2 rounded border inline-flex items-center gap-1 ${matchStatus.badgeClass}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${matchStatus.dotClass}`} />
                        {matchStatus.label}
                      </span>

                      {queueBadge || (
                        <span className={`text-[10px] font-mono px-2 py-0.2 rounded border ${fantasyStatus.badgeClass}`}>
                          {fantasyStatus.label}
                        </span>
                      )}

                      {/* Individual Fantasy Points */}
                      <span
                        data-testid={`backup-points-B${rank}`}
                        className="text-[10px] font-mono font-bold text-amber-300 bg-amber-500/10 px-1.5 py-0.2 rounded border border-amber-500/30"
                      >
                        {isSelected ? `${activePts.toFixed(1)} pts (Active)` : `${totalEarnedPts.toFixed(1)} pts`}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Reorder Buttons */}
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleMove(index, -1)}
                    disabled={index === 0 || isLoading || isSelected}
                    data-testid={`priority-up-B${rank}`}
                    className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 disabled:opacity-20 disabled:pointer-events-none transition-colors"
                    title="Move Priority Up"
                  >
                    <ArrowUp className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => handleMove(index, 1)}
                    disabled={index === benchSlots.length - 1 || isLoading || isSelected}
                    data-testid={`priority-down-B${rank}`}
                    className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 disabled:opacity-20 disabled:pointer-events-none transition-colors"
                    title="Move Priority Down"
                  >
                    <ArrowDown className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* SECTION B: Replaced / Unavailable Players */}
      <div className="pt-4 border-t border-slate-800" data-testid="bench-replaced-section">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-mono uppercase font-bold text-rose-400 tracking-wider flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
            Section B: Replaced / Unavailable Players ({substitutedSlots.length})
          </span>
          <span className="text-[10px] font-mono text-slate-400">
            Historical Ledger Maintained
          </span>
        </div>

        {substitutedSlots.length === 0 ? (
          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80 text-xs text-slate-400 text-center">
            No players currently substituted out. When Scenario 1 or 2 is run, outgoing players appear here.
          </div>
        ) : (
          <div className="space-y-2">
            {substitutedSlots.map(s => {
              const p = s.player;
              const isThakur = p.id === "p_csk_thakur";
              const isMustafizur = p.id === "p_csk_mustafizur";
              const ptsInfo = playerPointsMap[p.id];
              const histPts = ptsInfo?.historical_points ?? s.fantasy_points ?? (isThakur ? 43.0 : 0.0);

              return (
                <div
                  key={s.id}
                  data-testid={`bench-replaced-${p.id}`}
                  className="p-3 rounded-xl bg-slate-950/90 border border-slate-800 flex items-center justify-between"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="w-2 h-2 rounded-full bg-rose-400 shrink-0" />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={`px-1.5 py-0.2 rounded font-black text-[9px] ${
                          p.team === "CSK" ? "bg-yellow-400 text-slate-950" : "bg-blue-600 text-white"
                        }`}>
                          {p.team}
                        </span>
                        <span className="font-bold text-xs text-white">
                          {p.full_name}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400">
                          {p.role} • {p.credits} Cr
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        {isMustafizur && "Did not play in announced XI • Replaced by Shardul Thakur (CSK, B2)"}
                        {isThakur && "Substituted out for Innings 2 • 43.0 pts locked in Innings 1 • Replaced by M. Stoinis (MI)"}
                        {!isMustafizur && !isThakur && `Substituted out in Innings ${s.exit_innings || 1}`}
                      </p>
                    </div>
                  </div>

                  <div className="text-right shrink-0">
                    <span
                      data-testid={`bench-replaced-pts-${p.id}`}
                      className="text-xs font-mono font-bold text-amber-300 block"
                    >
                      {histPts.toFixed(1)} pts locked
                    </span>
                    <span className="text-[9px] font-mono text-slate-500">
                      (0.0 pts active)
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
