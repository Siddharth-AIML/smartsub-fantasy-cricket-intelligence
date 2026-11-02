/**
 * Human-readable label dictionary and formatting helpers for SmartSub.
 * Eliminates technical backend enum jargon for first-time fantasy cricket users.
 */

export const REAL_MATCH_STATUS_LABELS = {
  NOT_STARTED: {
    label: "Match not started",
    badgeClass: "bg-slate-800 text-slate-300 border-slate-700",
    dotClass: "bg-slate-400"
  },
  PLAYING_XI: {
    label: "In playing XI",
    badgeClass: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30 font-medium",
    dotClass: "bg-emerald-400"
  },
  IMPACT_ENTERED: {
    label: "Entered as Impact Player",
    badgeClass: "bg-purple-500/10 text-purple-300 border-purple-500/30 font-medium",
    dotClass: "bg-purple-400"
  },
  BENCH_SUBSTITUTE: {
    label: "On team bench",
    badgeClass: "bg-blue-500/10 text-blue-300 border-blue-500/30",
    dotClass: "bg-blue-400"
  },
  DID_NOT_PLAY: {
    label: "Did not play",
    badgeClass: "bg-rose-500/10 text-rose-300 border-rose-500/30 font-medium",
    dotClass: "bg-rose-400"
  }
};

export const FANTASY_SELECTION_LABELS = {
  SELECTED: {
    label: "Active in Playing XI",
    badgeClass: "bg-emerald-500/15 text-emerald-300 border-emerald-500/40 font-bold"
  },
  REPLACEMENT_CANDIDATE: {
    label: "Evaluating as backup",
    badgeClass: "bg-amber-500/15 text-amber-300 border-amber-500/40 font-bold animate-pulse"
  },
  SUBSTITUTED_OUT: {
    label: "Substituted out",
    badgeClass: "bg-rose-500/10 text-rose-300 border-rose-500/30"
  },
  NOT_SELECTED: {
    label: "On bench (reserve)",
    badgeClass: "bg-slate-800 text-slate-400 border-slate-700"
  }
};

export const MATCH_PHASE_LABELS = {
  PRE_MATCH: "Before match starts",
  TOSS_CONDUCTED: "Toss completed",
  LINEUP_CONFIRMED: "Official lineups confirmed",
  INNINGS_1: "1st Innings (CSK Bowling)",
  INNINGS_BREAK: "Innings break (Target set)",
  INNINGS_2_STARTED: "2nd Innings (CSK Batting Chase)",
  INNINGS_2: "2nd Innings (CSK Batting Chase)",
  COMPLETED: "Match completed"
};

export const PRIORITY_EXPLANATIONS = {
  1: "Priority 1 (B1) — Evaluated first if any starter does not play in the real match.",
  2: "Priority 2 (B2) — Evaluated second if B1 does not play, is unavailable, or exceeds credit limits.",
  3: "Priority 3 (B3) — Evaluated third if neither B1 nor B2 can fill the vacant spot.",
  4: "Priority 4 (B4) — Final emergency backup evaluated if B1, B2, and B3 are all unavailable."
};

export const ROLE_LABELS = {
  WK: "Wicket-Keeper",
  BAT: "Batter",
  AR: "All-Rounder",
  BOWL: "Bowler"
};

export function getRealMatchStatus(status) {
  return REAL_MATCH_STATUS_LABELS[status] || {
    label: status ? status.replace(/_/g, " ").toLowerCase() : "Unknown",
    badgeClass: "bg-slate-800 text-slate-400 border-slate-700",
    dotClass: "bg-slate-400"
  };
}

export function getFantasyStatus(status) {
  return FANTASY_SELECTION_LABELS[status] || {
    label: status ? status.replace(/_/g, " ").toLowerCase() : "Unknown",
    badgeClass: "bg-slate-800 text-slate-400 border-slate-700"
  };
}

export function getMatchPhase(phase) {
  return MATCH_PHASE_LABELS[phase] || (phase ? phase.replace(/_/g, " ") : "In Progress");
}
