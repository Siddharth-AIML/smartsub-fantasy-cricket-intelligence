import React from 'react';
import { Lock, Unlock, TrendingUp, Info, AlertCircle, ShieldCheck } from 'lucide-react';

export default function InningsLedgerCard({ fantasyTeam, liveState }) {
  const ledgers = fantasyTeam?.scoring_ledgers || [];
  const slots = fantasyTeam?.lineup_slots || [];

  const activePoints = liveState?.fantasy_active_points ?? fantasyTeam?.total_points ?? 0.0;
  const historicalPoints = liveState?.historical_locked_points ?? 0.0;
  const replacementAudit = liveState?.replacement_slot_audit;

  // Group ledgers by player
  const playerLedgers = {};
  for (const l of ledgers) {
    if (!playerLedgers[l.player_id]) {
      const slot = slots.find(s => s.player_id === l.player_id);
      playerLedgers[l.player_id] = {
        player_id: l.player_id,
        player: slot?.player || { short_name: l.player_id, role: "N/A" },
        slot: slot,
        innings1: null,
        innings2: null,
        totalPoints: 0
      };
    }
    if (l.innings === 1) playerLedgers[l.player_id].innings1 = l;
    if (l.innings === 2) playerLedgers[l.player_id].innings2 = l;
    playerLedgers[l.player_id].totalPoints += l.total_fantasy_points;
  }

  const entries = Object.values(playerLedgers);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col" data-testid="innings-ledger-card">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-3 mb-4 border-b border-slate-800 gap-2">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            Innings Participation & Scoring Ledger
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/30">
              Immutable Split-Ledger
            </span>
          </h3>
          <p className="text-xs text-slate-400">
            Immutable cricket event record. Distinguishes active fantasy points from preserved historical points under single-occupant rules.
          </p>
        </div>

        <div className="flex items-center gap-4 text-right">
          <div>
            <span className="text-[11px] text-slate-400 font-mono block">Historical Locked:</span>
            <span className="text-base font-black text-amber-300 font-mono" data-testid="ledger-historical-total">
              {historicalPoints.toFixed(1)} pts
            </span>
          </div>
          <div className="pl-3 border-l border-slate-800">
            <span className="text-[11px] text-slate-400 font-mono block">Active Total:</span>
            <span className="text-xl font-black text-purple-400 font-mono" data-testid="ledger-active-total">
              {activePoints.toFixed(1)} pts
            </span>
          </div>
        </div>
      </div>

      {/* Educational Note Explaining Single-Occupant Rule */}
      <div className="bg-purple-950/20 border border-purple-800/40 p-3 rounded-xl mb-4 text-xs text-slate-300 flex items-start gap-2.5">
        <Info className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
        <div>
          <strong className="text-white">SmartSub Single-Occupant Rule:</strong> Once Marcus Stoinis replaces Shardul Thakur in Innings 2, Shardul's <strong className="text-amber-300">43.0 historical points</strong> remain permanently preserved in this locked ledger (<Lock className="w-3 h-3 text-amber-400 inline" />), but are excluded from active team points. Stoinis's <strong className="text-purple-300">32.0 active points</strong> count for the slot. Active slot contribution is <strong>32.0, not 75.0</strong>!
        </div>
      </div>

      {/* Ledger Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono" data-testid="innings-ledger-table">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider bg-slate-950/60">
              <th className="py-2.5 px-3">Player</th>
              <th className="py-2.5 px-3">Role</th>
              <th className="py-2.5 px-3 text-center">Innings 1 (MI Bat / CSK Bowl)</th>
              <th className="py-2.5 px-3 text-center">Innings 2 (CSK Chase)</th>
              <th className="py-2.5 px-3 text-right">Active Fantasy Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {entries.length === 0 ? (
              <tr>
                <td colSpan="5" className="py-6 text-center text-slate-500 italic">
                  No scoring events simulated yet. Click "Start Scenario 1" or "Start Scenario 2" to populate the ledger.
                </td>
              </tr>
            ) : (
              entries.map((item, idx) => {
                const inn1 = item.innings1;
                const inn2 = item.innings2;
                const isSelected = item.slot?.fantasy_selection_status === "SELECTED";
                const isSubstitutedOut = item.slot?.fantasy_selection_status === "SUBSTITUTED_OUT";

                return (
                  <tr
                    key={idx}
                    data-testid={`ledger-row-${item.player_id}`}
                    className="hover:bg-slate-850/50 transition-colors"
                  >
                    {/* Player */}
                    <td className="py-2.5 px-3 font-bold text-white">
                      {item.player.short_name}
                    </td>

                    {/* Role */}
                    <td className="py-2.5 px-3 text-slate-400">
                      <span className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px]">
                        {item.player.role}
                      </span>
                    </td>

                    {/* Innings 1 Column */}
                    <td className="py-2.5 px-3 text-center">
                      {inn1 ? (
                        <div className="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-slate-850 border border-slate-700">
                          {inn1.is_locked ? (
                            <Lock className="w-3 h-3 text-amber-400" title="Locked Historical Record" />
                          ) : (
                            <Unlock className="w-3 h-3 text-emerald-400" title="Active Scoring" />
                          )}
                          <span className="font-bold text-white">{inn1.total_fantasy_points.toFixed(1)}</span>
                          <span className="text-[10px] text-slate-400">pts</span>
                          {inn1.wickets_taken > 0 && (
                            <span className="text-[9px] text-emerald-400">({inn1.wickets_taken} wkt)</span>
                          )}
                          {inn1.maidens > 0 && (
                            <span className="text-[9px] text-blue-400">({inn1.maidens} mdn)</span>
                          )}
                        </div>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>

                    {/* Innings 2 Column */}
                    <td className="py-2.5 px-3 text-center">
                      {inn2 ? (
                        <div className="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-slate-850 border border-purple-500/40">
                          {inn2.is_locked ? (
                            <Lock className="w-3 h-3 text-amber-400" title="Locked" />
                          ) : (
                            <Unlock className="w-3 h-3 text-purple-400" title="Active 2nd Innings" />
                          )}
                          <span className="font-bold text-purple-300">{inn2.total_fantasy_points.toFixed(1)}</span>
                          <span className="text-[10px] text-slate-400">pts</span>
                          {inn2.runs_scored > 0 && (
                            <span className="text-[9px] text-purple-300">({inn2.runs_scored} runs)</span>
                          )}
                        </div>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>

                    {/* Active Fantasy Status */}
                    <td className="py-2.5 px-3 text-right">
                      {isSubstitutedOut ? (
                        <span className="px-2 py-0.5 rounded bg-amber-950/50 text-amber-300 border border-amber-800 text-[10px] font-bold">
                          HISTORICAL (0.0 active)
                        </span>
                      ) : isSelected ? (
                        <span className="px-2 py-0.5 rounded bg-emerald-950/50 text-emerald-300 border border-emerald-800 text-[10px] font-bold">
                          ACTIVE ({item.totalPoints.toFixed(1)} pts)
                        </span>
                      ) : (
                        <span className="text-slate-500 text-[10px]">
                          ON BENCH
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
