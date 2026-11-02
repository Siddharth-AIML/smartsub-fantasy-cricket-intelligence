import React from 'react';
import { X, ArrowRight, ShieldCheck, CheckCircle2, XCircle } from 'lucide-react';

export default function SquadDiffModal({ decision, onClose }) {
  if (!decision) return null;

  const beforeXI = decision.squad_snapshot_before?.selected_xi || [];
  const afterXI = decision.squad_snapshot_after?.selected_xi || [];
  const audits = decision.evaluations_audit || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn" data-testid="squad-diff-modal">
      <div className="bg-slate-900 border border-slate-800 w-full max-w-4xl max-h-[90vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              Squad State Diff & Constraint Verification
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                {decision.rule_id}
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Before and after squad roster state with complete constraint audit logs
            </p>
          </div>
          <button
            onClick={onClose}
            data-testid="close-diff-modal-btn"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-5">
          {/* Evaluations Audit Trace (Shows B1 bypass in Scenario 1) */}
          {audits.length > 0 && (
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono mb-2">
                Sequential Bench Evaluation Audit Trace
              </h4>
              <div className="space-y-2">
                {audits.map((a, i) => (
                  <div
                    key={i}
                    className={`p-3 rounded-xl border text-xs font-mono flex items-center justify-between ${
                      a.status === "ACCEPTED"
                        ? "bg-emerald-950/20 border-emerald-800/40 text-emerald-300"
                        : a.status === "SKIPPED"
                        ? "bg-amber-950/20 border-amber-800/40 text-amber-300"
                        : "bg-rose-950/20 border-rose-800/40 text-rose-300"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-bold px-1.5 py-0.5 rounded bg-slate-800 text-white">
                        {a.priority_label || `B${a.priority_rank}`}
                      </span>
                      <span>{a.short_name || a.player_id}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold">{a.status}</span>
                      <span className="text-[11px] opacity-80">({a.reason || a.details?.error || "Platform valid"})</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Before & After Squad Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Before Squad */}
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-800 text-xs font-bold text-slate-400">
                <span>Active 11 Before Substitution</span>
                <span className="font-mono text-slate-500">{beforeXI.length} Players</span>
              </div>
              <div className="space-y-1.5 font-mono text-xs">
                {beforeXI.map((p, i) => {
                  const isOut = p.player_id === decision.player_out_id;
                  return (
                    <div
                      key={i}
                      className={`p-2 rounded-lg flex items-center justify-between ${
                        isOut ? "bg-rose-950/40 text-rose-300 border border-rose-800/60 font-bold" : "text-slate-300"
                      }`}
                    >
                      <span>{p.short_name} ({p.role})</span>
                      <span className="text-slate-400">{p.credits} Cr</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* After Squad */}
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-800 text-xs font-bold text-slate-400">
                <span>Active 11 After Substitution</span>
                <span className="font-mono text-slate-500">{afterXI.length} Players</span>
              </div>
              <div className="space-y-1.5 font-mono text-xs">
                {afterXI.map((p, i) => {
                  const isIn = p.player_id === decision.player_in_id;
                  return (
                    <div
                      key={i}
                      className={`p-2 rounded-lg flex items-center justify-between ${
                        isIn ? "bg-emerald-950/40 text-emerald-300 border border-emerald-800/60 font-bold" : "text-slate-300"
                      }`}
                    >
                      <span>{p.short_name} ({p.role})</span>
                      <span className="text-slate-400">{p.credits} Cr</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-900/90 text-right">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition-colors"
          >
            Close Diff
          </button>
        </div>
      </div>
    </div>
  );
}
