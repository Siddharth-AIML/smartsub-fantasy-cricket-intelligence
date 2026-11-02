import React from 'react';
import { X, ExternalLink, CheckCircle2, AlertTriangle, ShieldCheck, FileText } from 'lucide-react';

export default function RuleEvidenceModal({ isOpen, onClose, rulesData }) {
  if (!isOpen) return null;

  const rules = rulesData?.rules || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn" data-testid="rule-evidence-modal">
      <div className="bg-slate-900 border border-slate-750 w-full max-w-4xl max-h-[90vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-slate-800">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Rule Evidence Register & Trust Matrix</h2>
              <p className="text-xs text-slate-400">
                Authoritative citations distinguishing verified platform rules from SmartSub proposed experimental rules
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            data-testid="close-rules-modal-btn"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content list */}
        <div className="p-6 overflow-y-auto space-y-4">
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-3.5 text-xs text-amber-300 flex items-start gap-3">
            <AlertTriangle className="w-4 h-4 mt-0.5 text-amber-400 shrink-0" />
            <div>
              <span className="font-semibold">Platform Rule Fidelity Notice:</span> In official Dream11 rules, backups activate strictly once at match deadline to replace unannounced players (DNP). Dynamic in-match Impact Player restorations and mutual exclusion constraints are strictly classified under <span className="font-semibold text-white">Tier 4: Proposed SmartSub Experimental Rules</span>.
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {rules.map((rule) => {
              const isVerified = rule.status.includes("VERIFIED");
              return (
                <div
                  key={rule.rule_id}
                  className={`p-4 rounded-xl border transition-all ${
                    isVerified
                      ? "bg-slate-900/60 border-slate-800 hover:border-slate-700"
                      : "bg-amber-950/20 border-amber-800/40 hover:border-amber-700/60"
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {rule.rule_id}
                      </span>
                      <h3 className="font-semibold text-sm text-white">{rule.title}</h3>
                    </div>
                    <span
                      className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full inline-flex items-center gap-1.5 w-fit ${
                        isVerified
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                          : "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                      }`}
                    >
                      {isVerified ? (
                        <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      ) : (
                        <AlertTriangle className="w-3 h-3 text-amber-400" />
                      )}
                      {rule.status}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 mb-3 leading-relaxed">
                    {rule.description}
                  </p>

                  <div className="bg-slate-950/70 p-3 rounded-lg border border-slate-800/80 mb-3">
                    <div className="text-[10px] uppercase font-mono tracking-wider text-slate-500 mb-1 flex items-center gap-1">
                      <FileText className="w-3 h-3" /> Exact Supporting Source Excerpt
                    </div>
                    <p className="text-xs italic text-slate-400 font-serif leading-relaxed">
                      "{rule.source_excerpt}"
                    </p>
                  </div>

                  <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/60 gap-2">
                    <div>
                      <span className="text-slate-500">Applicable: </span>
                      {rule.applicable_contest}
                    </div>
                    <div className="flex items-center gap-3">
                      <span>Verified: {rule.verification_date}</span>
                      {rule.source_url && rule.source_url.startsWith("http") && (
                        <a
                          href={rule.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1 underline"
                        >
                          Official Source <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-900/90 text-right">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition-colors"
          >
            Close Register
          </button>
        </div>
      </div>
    </div>
  );
}
