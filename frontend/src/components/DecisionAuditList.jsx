import React from 'react';
import { ArrowRight, Layers, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function DecisionAuditList({
  decisions,
  selectedDecisionId,
  onSelectDecision,
  onOpenDiffModal
}) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col">
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            Substitution Decision Audit Log
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/30">
              {decisions.length} Logged
            </span>
          </h3>
          <p className="text-xs text-slate-400">
            Immutable chronological audit record of all engine evaluations with squad before/after state diffs
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {decisions.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs italic bg-slate-950/40 rounded-xl border border-slate-800/60">
            No substitutions executed yet. Run <strong>Scenario 1</strong> or <strong>Scenario 2</strong> above to record substitution decisions.
          </div>
        ) : (
          decisions.map((dec) => {
            const isSelected = dec.id === selectedDecisionId;
            const isExecuted = dec.status === "EXECUTED";

            return (
              <div
                key={dec.id}
                onClick={() => onSelectDecision(dec.id)}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  isSelected
                    ? "bg-slate-850 border-purple-500 shadow-md ring-1 ring-purple-500/40"
                    : "bg-slate-950/60 border-slate-800 hover:border-slate-700"
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                      isExecuted
                        ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30"
                        : "bg-amber-500/10 text-amber-300 border-amber-500/30"
                    }`}>
                      {isExecuted ? "Successfully Executed" : dec.status}
                    </span>
                    <span className="text-xs font-mono text-slate-400">
                      Rule: <strong className="text-slate-200">{dec.rule_id}</strong>
                    </span>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenDiffModal(dec);
                    }}
                    data-testid="open-diff-modal-btn"
                    className="flex items-center gap-1 text-[11px] font-medium text-purple-400 hover:text-purple-300 transition-colors w-fit"
                  >
                    <Layers className="w-3.5 h-3.5" />
                    Inspect Squad State Diff
                  </button>
                </div>

                {/* Swap Details */}
                <div className="flex items-center gap-2 text-sm font-bold text-white mb-1.5">
                  <span className="text-rose-400">Out: {dec.player_out_id || "Unannounced"}</span>
                  <ArrowRight className="w-4 h-4 text-slate-500 shrink-0" />
                  <span className="text-emerald-400">In: {dec.player_in_id || "None"}</span>
                  {dec.priority_rank_used && (
                    <span className="text-[10px] font-mono font-normal px-1.5 py-0.2 rounded bg-purple-950/60 text-purple-300 border border-purple-700/50">
                      Priority Rank: B{dec.priority_rank_used}
                    </span>
                  )}
                </div>

                {/* Reason Code */}
                <div className="text-xs font-mono text-slate-400">
                  Reason: <span className="text-slate-300 font-sans">{dec.reason_code.replace(/_/g, " ")}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
