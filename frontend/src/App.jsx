import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import HowToUseGuide from './components/HowToUseGuide';
import ScenarioCards from './components/ScenarioCards';
import ProgressIndicator from './components/ProgressIndicator';
import MatchSimulatorCard from './components/MatchSimulatorCard';
import PitchVisualizer from './components/PitchVisualizer';
import BenchPriorityManager from './components/BenchPriorityManager';
import AIExplanationCard from './components/AIExplanationCard';
import CollapsibleSections from './components/CollapsibleSections';
import RuleEvidenceModal from './components/RuleEvidenceModal';
import SquadDiffModal from './components/SquadDiffModal';

import {
  fetchHealth,
  fetchMatches,
  fetchLiveState,
  stepSimulation,
  triggerImpactPlayer,
  resetMatch,
  replayMatch,
  fetchFantasyTeam,
  updateBenchPriority,
  updateRuleConfig,
  fetchSubstitutionHistory,
  fetchAIExplanation,
  fetchRuleEvidenceRegister,
  runScenario1Automated,
  runScenario2Automated
} from './services/api';

export default function App() {
  const [matchId, setMatchId] = useState("match_csk_mi_2026");
  const [teamId, setTeamId] = useState("fantasy_team_demo");
  
  const [healthInfo, setHealthInfo] = useState(null);
  const [liveState, setLiveState] = useState(null);
  const [fantasyTeam, setFantasyTeam] = useState(null);
  const [decisions, setDecisions] = useState([]);
  const [selectedDecisionId, setSelectedDecisionId] = useState(null);
  const [aiExplanation, setAiExplanation] = useState(null);
  const [rulesData, setRulesData] = useState(null);
  
  const [completionNotice, setCompletionNotice] = useState(null);
  const [isRulesModalOpen, setIsRulesModalOpen] = useState(false);
  const [diffModalDecision, setDiffModalDecision] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isAiLoading, setIsAiLoading] = useState(false);

  // Initial Data Load
  useEffect(() => {
    loadAllData();
  }, [matchId, teamId]);

  const loadAllData = async () => {
    setIsLoading(true);
    try {
      const [h, ls, ft, decs, r] = await Promise.all([
        fetchHealth().catch(err => { console.warn("fetchHealth:", err); return null; }),
        fetchLiveState(matchId).catch(err => { console.warn("fetchLiveState:", err); return null; }),
        fetchFantasyTeam(teamId).catch(err => { console.warn("fetchFantasyTeam:", err); return null; }),
        fetchSubstitutionHistory(teamId).catch(err => { console.warn("fetchSubstitutionHistory:", err); return []; }),
        fetchRuleEvidenceRegister().catch(err => { console.warn("fetchRuleEvidenceRegister:", err); return null; })
      ]);

      if (h) setHealthInfo(h);
      if (ls && (ls.scoreboard || ls.status)) setLiveState(ls);
      if (ft && ft.id && Array.isArray(ft.lineup_slots)) setFantasyTeam(ft);
      if (Array.isArray(decs)) setDecisions(decs);
      if (r) setRulesData(r);

      // Auto-select latest decision if available
      if (decs && decs.length > 0) {
        setSelectedDecisionId(decs[0].id);
        loadAiExplanation(decs[0].id);
      }
    } catch (err) {
      console.error("Failed to load initial data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadAiExplanation = async (decisionId) => {
    setIsAiLoading(true);
    try {
      const exp = await fetchAIExplanation(decisionId);
      setAiExplanation(exp);
    } catch (err) {
      console.error("Failed to load AI explanation:", err);
    } finally {
      setIsAiLoading(false);
    }
  };

  const handleSelectDecision = (decisionId) => {
    setSelectedDecisionId(decisionId);
    loadAiExplanation(decisionId);
  };

  const handleStepSimulation = async (stepType) => {
    setIsLoading(true);
    setCompletionNotice(null);
    try {
      await stepSimulation(matchId, stepType);
      await loadAllData();
    } catch (err) {
      console.error("Simulation step failed:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTriggerImpact = async () => {
    setIsLoading(true);
    try {
      await triggerImpactPlayer(matchId, "p_csk_thakur", "p_csk_stoinis");
      await loadAllData();
      setCompletionNotice({
        scenario: 2,
        title: "Scenario 2: Impact Player Substituted",
        details: "Marcus Stoinis (32.0 active pts) replaces Shardul Thakur. Thakur's 43.0 historical pts remain locked in Innings 1 ledger."
      });
    } catch (err) {
      console.error("Impact player trigger failed:", err);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 1-Click Automated Scenario 1 Demonstration
   * Executes atomic backend flow: Reset -> Toss -> Official Lineups -> Mustafizur DNP -> Conway B1 Skipped -> Thakur B2 Selected.
   */
  const handleRunScenario1 = async () => {
    setIsLoading(true);
    setCompletionNotice(null);
    try {
      const res = await runScenario1Automated(matchId);
      await loadAllData();
      setCompletionNotice({
        scenario: 1,
        title: "Scenario 1 Completed Successfully",
        details: "Starter Mustafizur Rahman (DNP) removed. Backup 1 Devon Conway (DNP) skipped. Backup 2 Shardul Thakur selected into active Playing XI."
      });
    } catch (err) {
      console.error("Scenario 1 execution failed:", err);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 1-Click Automated Scenario 2 Demonstration
   * Executes atomic backend flow: Scenario 1 -> Innings 1 Sim (Thakur 43 pts locked) -> Jump Innings 2 -> Stoinis Impact Sub -> Innings 2 Chase (Stoinis 32 pts) -> Single-occupant active score.
   */
  const handleRunScenario2 = async () => {
    setIsLoading(true);
    setCompletionNotice(null);
    try {
      const res = await runScenario2Automated(matchId);
      await loadAllData();
      setCompletionNotice({
        scenario: 2,
        title: "Scenario 2 Completed Successfully",
        details: "Marcus Stoinis entered as Impact Player for Shardul Thakur. Thakur's 43.0 pts locked in historical ledger; Stoinis contributes 32.0 active pts (single-occupant scoring rule)."
      });
    } catch (err) {
      console.error("Scenario 2 execution failed:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetMatch = async () => {
    setIsLoading(true);
    setCompletionNotice(null);
    try {
      await resetMatch(matchId);
      setAiExplanation(null);
      setSelectedDecisionId(null);
      await loadAllData();
    } catch (err) {
      console.error("Reset failed:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReplayMatch = async () => {
    setIsLoading(true);
    try {
      await replayMatch(matchId);
      await loadAllData();
    } catch (err) {
      console.error("Replay failed:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdatePriorities = async (priorities) => {
    setIsLoading(true);
    try {
      await updateBenchPriority(teamId, priorities);
      const ft = await fetchFantasyTeam(teamId);
      setFantasyTeam(ft);
    } catch (err) {
      console.error("Failed to update priorities:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateRuleConfig = async (config) => {
    setIsLoading(true);
    try {
      await updateRuleConfig(teamId, config);
      const ft = await fetchFantasyTeam(teamId);
      setFantasyTeam(ft);
    } catch (err) {
      console.error("Failed to update rule config:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-['Outfit',sans-serif]" data-testid="smartsub-app">
      {/* Global Header */}
      <Header
        healthInfo={healthInfo}
        liveState={liveState}
        onOpenRulesModal={() => setIsRulesModalOpen(true)}
        onResetMatch={handleResetMatch}
        onReplayMatch={handleReplayMatch}
        isLoading={isLoading}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 lg:p-8 space-y-6">
        {/* Completion Toast Banner */}
        {completionNotice && (
          <div
            data-testid="completion-notice-banner"
            className="p-4 rounded-2xl bg-gradient-to-r from-emerald-950/80 via-slate-900 to-emerald-950/80 border border-emerald-500/50 shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 animate-fadeIn"
          >
            <div>
              <h4 className="text-sm font-bold text-white flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                {completionNotice.title}
              </h4>
              <p className="text-xs text-slate-300 mt-0.5">{completionNotice.details}</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={completionNotice.scenario === 1 ? handleRunScenario1 : handleRunScenario2}
                className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md transition-colors"
                data-testid="notice-run-again-btn"
              >
                Run Again
              </button>
              <button
                onClick={handleResetMatch}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs transition-colors"
                data-testid="notice-reset-btn"
              >
                Reset Demo
              </button>
            </div>
          </div>
        )}

        {/* Step 1: How to use SmartSub Guide Banner */}
        <HowToUseGuide
          onSelectScenario1={handleRunScenario1}
          onSelectScenario2={handleRunScenario2}
        />

        {/* Step 2: Clearly Separated Scenario Cards with 1-Click Guided Actions */}
        <ScenarioCards
          onRunScenario1={handleRunScenario1}
          onRunScenario2={handleRunScenario2}
          decisions={decisions}
          liveState={liveState}
          isLoading={isLoading}
        />

        {/* 4-Step Progress Indicator */}
        <ProgressIndicator
          liveState={liveState}
          decisions={decisions}
        />

        {/* Match Simulator Center */}
        <MatchSimulatorCard
          liveState={liveState}
          onStepSimulation={handleStepSimulation}
          onTriggerImpact={handleTriggerImpact}
          isLoading={isLoading}
        />

        {/* Playing XI Pitch & B1–B4 Bench Manager */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-7">
            <PitchVisualizer fantasyTeam={fantasyTeam} liveState={liveState} />
          </div>
          <div className="lg:col-span-5 flex flex-col gap-6">
            <BenchPriorityManager
              fantasyTeam={fantasyTeam}
              liveState={liveState}
              onUpdatePriorities={handleUpdatePriorities}
              isLoading={isLoading}
            />
          </div>
        </div>

        {/* AI Strategic Explanation Card (Directly visible) */}
        <AIExplanationCard
          explanation={aiExplanation}
          liveState={liveState}
          isLoading={isAiLoading}
        />

        {/* Collapsible Advanced Analytics (Scoring Ledger, Decision History, Rule Sandbox) */}
        <CollapsibleSections
          fantasyTeam={fantasyTeam}
          liveState={liveState}
          decisions={decisions}
          selectedDecisionId={selectedDecisionId}
          onSelectDecision={handleSelectDecision}
          onOpenDiffModal={(dec) => setDiffModalDecision(dec)}
          onOpenRulesModal={() => setIsRulesModalOpen(true)}
          onUpdateRuleConfig={handleUpdateRuleConfig}
          isLoading={isLoading}
        />
      </main>

      {/* Rule Evidence Register Modal */}
      <RuleEvidenceModal
        isOpen={isRulesModalOpen}
        onClose={() => setIsRulesModalOpen(false)}
        rulesData={rulesData}
      />

      {/* Squad Diff Inspection Modal */}
      <SquadDiffModal
        decision={diffModalDecision}
        onClose={() => setDiffModalDecision(null)}
      />

      {/* Footer */}
      <footer className="border-t border-purple-900/30 bg-slate-900/40 py-4 px-6 text-center text-xs text-slate-500 font-mono">
        SmartSub • Fantasy Cricket Substitution Intelligence • Single-Occupant Experimental Scoring • Google Gemini API
      </footer>
    </div>
  );
}
