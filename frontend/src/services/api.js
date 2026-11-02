// SmartSub API Client Service
// Robust base URL normalization supporting Vercel, Render, and Localhost

const RAW_URL = (import.meta.env.VITE_API_BASE_URL || "").trim().replace(/\/+$/, "");

// Normalize API root (for /health) and API base (for /api endpoints)
export const API_ROOT = RAW_URL.replace(/\/api$/, "");
export const API_BASE = RAW_URL
  ? (RAW_URL.endsWith("/api") ? RAW_URL : `${RAW_URL}/api`)
  : "/api";

async function request(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const errorText = await res.text().catch(() => "");
    throw new Error(`API ${options.method || 'GET'} ${url} returned ${res.status}: ${errorText || res.statusText}`);
  }
  return res.json();
}

export async function fetchHealth() {
  // Support both /health at root and /api/health as fallback
  const primaryUrl = `${API_ROOT || API_BASE}/health`;
  try {
    return await request(primaryUrl);
  } catch (err) {
    return await request(`${API_BASE}/health`);
  }
}

export async function fetchMatches() {
  return request(`${API_BASE}/matches`);
}

export async function fetchLiveState(matchId) {
  return request(`${API_BASE}/matches/${matchId}/live-state`);
}

export async function stepSimulation(matchId, stepType) {
  return request(`${API_BASE}/matches/${matchId}/step`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ step_type: stepType })
  });
}

export async function triggerImpactPlayer(matchId, playerOutId = "p_csk_thakur", playerInId = "p_csk_stoinis") {
  return request(`${API_BASE}/matches/${matchId}/trigger-impact-player`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ player_out_id: playerOutId, player_in_id: playerInId })
  });
}

export async function resetMatch(matchId) {
  return request(`${API_BASE}/matches/${matchId}/reset`, { method: "POST" });
}

export async function replayMatch(matchId) {
  return request(`${API_BASE}/matches/${matchId}/replay`, { method: "POST" });
}

export async function fetchFantasyTeam(teamId) {
  return request(`${API_BASE}/fantasy-teams/${teamId}`);
}

export async function updateBenchPriority(teamId, priorities) {
  return request(`${API_BASE}/fantasy-teams/${teamId}/bench-priority`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ priorities })
  });
}

export async function updateRuleConfig(teamId, config) {
  return request(`${API_BASE}/fantasy-teams/${teamId}/rule-config`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config)
  });
}

export async function fetchSubstitutionHistory(teamId) {
  return request(`${API_BASE}/substitutions/history/${teamId}`);
}

export async function fetchDecisionDetails(decisionId) {
  return request(`${API_BASE}/substitutions/decision/${decisionId}`);
}

export async function fetchAIExplanation(decisionId) {
  return request(`${API_BASE}/ai/explain/${decisionId}`, { method: "POST" });
}

export async function fetchRuleEvidenceRegister() {
  return request(`${API_BASE}/rules/evidence-register`);
}

export async function runScenario1Automated(matchId) {
  return request(`${API_BASE}/matches/${matchId}/scenarios/run-scenario-1`, { method: "POST" });
}

export async function runScenario2Automated(matchId) {
  return request(`${API_BASE}/matches/${matchId}/scenarios/run-scenario-2`, { method: "POST" });
}
