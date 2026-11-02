VITE_API_BASE_URL
const API_BASE = "https://smartsub-fantasy-cricket.vercel.app" || "http://127.0.0.1:8000/api";

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function fetchMatches() {
  const res = await fetch(`${API_BASE}/matches`);
  return res.json();
}

export async function fetchLiveState(matchId) {
  const res = await fetch(`${API_BASE}/matches/${matchId}/live-state`);
  return res.json();
}

export async function stepSimulation(matchId, stepType) {
  const res = await fetch(`${API_BASE}/matches/${matchId}/step`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ step_type: stepType })
  });
  return res.json();
}

export async function triggerImpactPlayer(matchId, playerOutId = "p_csk_thakur", playerInId = "p_csk_stoinis") {
  const res = await fetch(`${API_BASE}/matches/${matchId}/trigger-impact-player`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ player_out_id: playerOutId, player_in_id: playerInId })
  });
  return res.json();
}

export async function resetMatch(matchId) {
  const res = await fetch(`${API_BASE}/matches/${matchId}/reset`, { method: "POST" });
  return res.json();
}

export async function replayMatch(matchId) {
  const res = await fetch(`${API_BASE}/matches/${matchId}/replay`, { method: "POST" });
  return res.json();
}

export async function fetchFantasyTeam(teamId) {
  const res = await fetch(`${API_BASE}/fantasy-teams/${teamId}`);
  return res.json();
}

export async function updateBenchPriority(teamId, priorities) {
  const res = await fetch(`${API_BASE}/fantasy-teams/${teamId}/bench-priority`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ priorities })
  });
  return res.json();
}

export async function updateRuleConfig(teamId, config) {
  const res = await fetch(`${API_BASE}/fantasy-teams/${teamId}/rule-config`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config)
  });
  return res.json();
}

export async function fetchSubstitutionHistory(teamId) {
  const res = await fetch(`${API_BASE}/substitutions/history/${teamId}`);
  return res.json();
}

export async function fetchDecisionDetails(decisionId) {
  const res = await fetch(`${API_BASE}/substitutions/decision/${decisionId}`);
  return res.json();
}

export async function fetchAIExplanation(decisionId) {
  const res = await fetch(`${API_BASE}/ai/explain/${decisionId}`, { method: "POST" });
  return res.json();
}

export async function fetchRuleEvidenceRegister() {
  const res = await fetch(`${API_BASE}/rules/evidence-register`);
  return res.json();
}

export async function runScenario1Automated(matchId) {
  const res = await fetch(`${API_BASE}/matches/${matchId}/scenarios/run-scenario-1`, { method: "POST" });
  return res.json();
}

export async function runScenario2Automated(matchId) {
  const res = await fetch(`${API_BASE}/matches/${matchId}/scenarios/run-scenario-2`, { method: "POST" });
  return res.json();
}
