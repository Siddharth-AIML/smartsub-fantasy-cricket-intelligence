import React, { useState } from 'react';
import { ChevronDown, ChevronUp, BookOpen, Layers, Sliders, Table, Sparkles, Shield, Activity } from 'lucide-react';
import InningsLedgerCard from './InningsLedgerCard';
import DecisionAuditList from './DecisionAuditList';
import RuleSandbox from './RuleSandbox';
import LiveScorecard from './LiveScorecard';

export default function CollapsibleSections({
  fantasyTeam,
  liveState,
  decisions,
  selectedDecisionId,
  onSelectDecision,
  onOpenDiffModal,
  onOpenRulesModal,
  onUpdateRuleConfig,
  isLoading
}) {
  const [activeTab, setActiveTab] = useState("scorecard"); // default to "scorecard" or "ledger"

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col" data-testid="collapsible-sections">
      {/* Section Header with Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-5 border-b border-slate-800 gap-3">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            Detailed Analytics & Verification Records
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              Advanced Inspection
            </span>
          </h3>
          <p className="text-xs text-slate-400">
            Expand below to audit granular ball scoring ledgers, squad diff snapshots, and rule evidence
          </p>
        </div>

        {/* Tab Buttons */}
        <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-950/80 border border-slate-800 text-xs font-mono overflow-x-auto">
          <button
            onClick={() => setActiveTab("scorecard")}
            data-testid="tab-scorecard-btn"
            className={`px-3 py-1.5 rounded-lg font-bold flex items-center gap-1.5 transition-all ${
              activeTab === "scorecard"
                ? "bg-purple-600 text-white shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Activity className="w-3.5 h-3.5 text-blue-400" />
            Live Cricket Scorecard
          </button>

          <button
            onClick={() => setActiveTab("ledger")}
            data-testid="tab-ledger-btn"
            className={`px-3 py-1.5 rounded-lg font-bold flex items-center gap-1.5 transition-all ${
              activeTab === "ledger"
                ? "bg-purple-600 text-white shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Table className="w-3.5 h-3.5" />
            Innings Scoring Ledger
          </button>

          <button
            onClick={() => setActiveTab("audit")}
            data-testid="tab-audit-btn"
            className={`px-3 py-1.5 rounded-lg font-bold flex items-center gap-1.5 transition-all ${
              activeTab === "audit"
                ? "bg-purple-600 text-white shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            Decision Audit Trail ({decisions.length})
          </button>

          <button
            onClick={() => setActiveTab("sandbox")}
            data-testid="tab-sandbox-btn"
            className={`px-3 py-1.5 rounded-lg font-bold flex items-center gap-1.5 transition-all ${
              activeTab === "sandbox"
                ? "bg-purple-600 text-white shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            Rule Mode Sandbox
          </button>
        </div>
      </div>

      {/* Tab Panels */}
      <div>
        {activeTab === "scorecard" && (
          <div className="animate-fadeIn">
            <LiveScorecard liveState={liveState} />
          </div>
        )}

        {activeTab === "ledger" && (
          <div className="animate-fadeIn">
            <InningsLedgerCard fantasyTeam={fantasyTeam} liveState={liveState} />
          </div>
        )}

        {activeTab === "audit" && (
          <div className="animate-fadeIn">
            <DecisionAuditList
              decisions={decisions}
              selectedDecisionId={selectedDecisionId}
              onSelectDecision={onSelectDecision}
              onOpenDiffModal={onOpenDiffModal}
            />
          </div>
        )}

        {activeTab === "sandbox" && (
          <div className="animate-fadeIn">
            <RuleSandbox
              fantasyTeam={fantasyTeam}
              onUpdateRuleConfig={onUpdateRuleConfig}
              isLoading={isLoading}
            />
          </div>
        )}
      </div>
    </div>
  );
}
