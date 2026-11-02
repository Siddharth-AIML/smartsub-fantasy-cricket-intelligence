import React from 'react';
import { Cpu, Sparkles, CheckCircle2, AlertCircle, ArrowUpRight, Split, Info } from 'lucide-react';

export default function AIExplanationCard({ explanation, liveState, isLoading }) {
  const dynamicEventAi = liveState?.latest_ai_explanation;

  if (isLoading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex items-center justify-center min-h-[200px]" data-testid="ai-explanation-card">
        <div className="flex flex-col items-center gap-2 text-slate-400">
          <div className="w-8 h-8 rounded-full border-2 border-purple-400 border-t-transparent animate-spin" />
          <span className="text-xs font-mono">Generating AI Strategic Rationale...</span>
        </div>
      </div>
    );
  }

  // If no decision explanation selected, fallback to latest match event AI explanation
  const activeExp = explanation || (dynamicEventAi ? {
    executive_summary: dynamicEventAi.headline,
    tactical_rationale: dynamicEventAi.tactical_rationale,
    rule_compliance_audit: dynamicEventAi.rule_compliance,
    is_fallback: dynamicEventAi.is_fallback ?? true,
    model_name: dynamicEventAi.model_name || "Deterministic Fallback Template",
    strategic_trade_offs: {
      pros: ["Deterministic compliance verified", "Franchise balance maintained (CSK & MI)"],
      cons: ["Illustrative match simulation data"]
    },
    counterfactual_alternatives: {}
  } : null);

  if (!activeExp) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col items-center justify-center min-h-[160px] text-center p-6" data-testid="ai-explanation-card">
        <Sparkles className="w-8 h-8 text-purple-400/50 mb-2" />
        <h4 className="text-sm font-bold text-white mb-1">AI Strategic Rationale Ready</h4>
        <p className="text-xs text-slate-400 max-w-md">
          Run <strong>Scenario 1</strong> (Confirm Lineup) or <strong>Scenario 2</strong> (Trigger Impact Sub) above to see an instant AI breakdown of the engine's substitution decisions.
        </p>
      </div>
    );
  }

  const isFallback = activeExp.is_fallback;
  const pros = activeExp.strategic_trade_offs?.pros || [];
  const cons = activeExp.strategic_trade_offs?.cons || [];
  const counterfactual = activeExp.counterfactual_alternatives || {};

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl relative overflow-hidden flex flex-col" data-testid="ai-explanation-card">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-3 mb-4 border-b border-slate-800 gap-2">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-gradient-to-tr from-purple-500/20 to-indigo-500/20 text-purple-300 border border-purple-500/30">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              AI Strategic Explanation & Analysis
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/15 text-purple-300 border border-purple-500/30">
                CSK vs MI Intelligence
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Downstream explanation of the engine's deterministic substitution decision
            </p>
          </div>
        </div>

        {/* Model Source Pill */}
        <div className="flex items-center gap-2">
          <span className={`text-[11px] font-mono px-2.5 py-1 rounded-lg border flex items-center gap-1.5 ${
            isFallback
              ? "bg-slate-800 text-slate-300 border-slate-700"
              : "bg-purple-500/10 text-purple-300 border-purple-500/30"
          }`}>
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            {isFallback ? "Deterministic Fallback Template" : activeExp.model_name}
          </span>
        </div>
      </div>

      {/* Executive Summary */}
      <div className="bg-purple-950/20 border border-purple-800/40 p-4 rounded-xl mb-4" data-testid="ai-executive-summary">
        <span className="text-[10px] font-mono uppercase tracking-wider text-purple-400 font-bold block mb-1">
          Decision Summary & Tactical Insight
        </span>
        <p className="text-sm font-semibold text-white leading-relaxed">
          {activeExp.executive_summary}
        </p>
      </div>

      {/* Tactical Rationale & Rule Compliance */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        {/* Tactical Rationale */}
        <div className="p-4 rounded-xl bg-slate-850/60 border border-slate-750" data-testid="ai-tactical-rationale">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold block mb-1.5 flex items-center gap-1">
            <ArrowUpRight className="w-3.5 h-3.5 text-purple-400" /> Tactical Cricketing Rationale
          </span>
          <p className="text-xs text-slate-300 leading-relaxed">
            {activeExp.tactical_rationale}
          </p>
        </div>

        {/* Rule Compliance Audit */}
        <div className="p-4 rounded-xl bg-slate-850/60 border border-slate-750" data-testid="ai-rule-compliance">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold block mb-1.5 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Platform & Constraint Check
          </span>
          <p className="text-xs text-slate-300 leading-relaxed">
            {activeExp.rule_compliance_audit}
          </p>
        </div>
      </div>

      {/* Strategic Trade-offs (Pros & Cons) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
        <div className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-900/40">
          <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-400 font-bold block mb-1">
            Strategic Advantages (Pros)
          </span>
          <ul className="space-y-1">
            {pros.map((pro, i) => (
              <li key={i} className="text-xs text-slate-300 flex items-start gap-1.5">
                <span className="text-emerald-400 font-bold">•</span>
                <span>{pro}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="p-3.5 rounded-xl bg-rose-950/20 border border-rose-900/40">
          <span className="text-[10px] font-mono uppercase tracking-wider text-rose-400 font-bold block mb-1">
            Trade-offs & Considerations (Cons)
          </span>
          <ul className="space-y-1">
            {cons.map((con, i) => (
              <li key={i} className="text-xs text-slate-300 flex items-start gap-1.5">
                <span className="text-rose-400 font-bold">•</span>
                <span>{con}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Counterfactual Scenario */}
      {Object.keys(counterfactual).length > 0 && (
        <div className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800 text-xs text-slate-400">
          <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold block mb-1 flex items-center gap-1">
            <Split className="w-3.5 h-3.5" /> What If Analysis
          </span>
          {Object.entries(counterfactual).map(([k, v]) => (
            <p key={k} className="leading-relaxed">
              <span className="font-semibold text-slate-300 capitalize">{k.replace(/_/g, " ")}:</span> {v}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
