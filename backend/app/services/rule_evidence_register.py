from typing import List, Dict, Any

RULE_EVIDENCE_REGISTER: List[Dict[str, Any]] = [
    {
        "rule_id": "R-D11-01",
        "title": "4-Backup System & Priority Ordering",
        "description": "Users can designate up to 4 backup players (B1-B4). Backups replace unannounced or non-playing starters in strict priority order (B1 > B2 > B3 > B4) at match start deadline, provided platform composition constraints are satisfied.",
        "source_url": "https://get.dream11.help/hc/en-in/articles/360046522331-What-is-the-Backup-feature-and-how-does-it-work-",
        "source_excerpt": "You can select up to 4 Backup players in order of priority (B1, B2, B3, B4)... Backups will replace unannounced/non-playing players in your starting 11 in priority order (B1 > B2 > B3 > B4)... only if the replacement adheres to the fantasy cricket team creation rules.",
        "verification_date": "2024-03-20",
        "applicable_contest": "Dream11 T20 / IPL / International Contests",
        "status": "VERIFIED",
        "rule_tier": "TIER_1_VERIFIED"
    },
    {
        "rule_id": "R-D11-02",
        "title": "Deadline-Only Evaluation Trigger",
        "description": "Backup evaluations activate strictly at the official match start deadline once Playing XIs are confirmed. No substitutions or bench replacements occur dynamically during live match play.",
        "source_url": "https://get.dream11.help/hc/en-in/articles/360046522331-What-is-the-Backup-feature-and-how-does-it-work-",
        "source_excerpt": "Backups will be activated ONLY at match start/deadline once the official lineups are confirmed. No substitutions occur during the match.",
        "verification_date": "2024-03-20",
        "applicable_contest": "All Official Dream11 Contests",
        "status": "VERIFIED",
        "rule_tier": "TIER_1_VERIFIED"
    },
    {
        "rule_id": "R-D11-03",
        "title": "Squad Composition & Credit Constraints",
        "description": "Every active 11-player lineup must consist of 1-8 Wicket Keepers, 1-8 Batters, 1-8 All-Rounders, 1-8 Bowlers, max 10 players from a single real franchise, and total credits <= 100.0.",
        "source_url": "https://www.dream11.com/games/fantasy-cricket/how-to-play",
        "source_excerpt": "11 players: 1-8 Wicket-Keepers, 1-8 Batters, 1-8 All-Rounders, 1-8 Bowlers, max 10 players from one team, 100 credit limit.",
        "verification_date": "2024-04-01",
        "applicable_contest": "Dream11 Cricket Contests",
        "status": "VERIFIED",
        "rule_tier": "TIER_1_VERIFIED"
    },
    {
        "rule_id": "R-D11-04",
        "title": "Captain/Vice-Captain Multiplier Invariance",
        "description": "If a designated Captain or Vice-Captain is unannounced (DNP) and replaced by an eligible backup, the replacement player scores standard (1x) points. Multipliers are not inherited by the incoming backup.",
        "source_url": "https://get.dream11.help/hc/en-in/articles/360046522331-What-is-the-Backup-feature-and-how-does-it-work-",
        "source_excerpt": "If your Captain/Vice-Captain does not play, your backup will replace them as a normal player (1x points). The 2x/1.5x multiplier is NOT transferred.",
        "verification_date": "2024-03-20",
        "applicable_contest": "All Official Dream11 Contests",
        "status": "VERIFIED",
        "rule_tier": "TIER_1_VERIFIED"
    },
    {
        "rule_id": "R-IPL-01",
        "title": "Real-World BCCI IPL Impact Player Regulation",
        "description": "Real-world cricket regulation allowing each team to name 5 substitutes at the toss and introduce 1 Impact Player at innings breaks, over completion, or fall of wicket.",
        "source_url": "https://www.iplt20.com",
        "source_excerpt": "Each team will name 5 substitutes at the toss along with the playing XI... One Impact Player can be used per match by each team at the start of an innings, over completion, or fall of wicket.",
        "verification_date": "2024-03-15",
        "applicable_contest": "BCCI IPL 2023-2025 Match Playing Conditions (Clause 1.2)",
        "status": "VERIFIED (CRICKET ONLY)",
        "rule_tier": "TIER_2_SECONDARY"
    },
    {
        "rule_id": "R-SUB-01",
        "title": "Scenario 1: B2 Evaluated When B1 Does Not Participate",
        "description": "When an unannounced fantasy starter is DNP and Backup 1 (B1) also does not participate in the real match (DID_NOT_PLAY), SmartSub bypasses B1 with an audit log and evaluates Backup 2 (B2, who is in the real Playing XI) against platform composition constraints.",
        "source_url": "https://smartsub.internal/rules/r-sub-01",
        "source_excerpt": "Engine evaluates B2 as the replacement for unannounced starter when B1 has real-world status DID_NOT_PLAY, maintaining platform credit and role invariants.",
        "verification_date": "2026-11-02",
        "applicable_contest": "SmartSub Tactical Simulation Sandbox",
        "status": "PROPOSED / EXPERIMENTAL",
        "rule_tier": "TIER_4_PROPOSED_EXPERIMENTAL"
    },
    {
        "rule_id": "R-SUB-02",
        "title": "Scenario 2: Dynamic 2nd Innings Impact Player & Ledger Split",
        "description": "Allows substituting an active player (P_B2) who participated in Innings 1 with an incoming Impact Player (P_B1) for Innings 2. Permanently locks P_B2's 1st-innings points in an immutable ledger while P_B1 earns points exclusively in Innings 2.",
        "source_url": "https://smartsub.internal/rules/r-sub-02",
        "source_excerpt": "Innings-specific participation and scoring ledger: Outgoing player retains 100% of Phase 1 fantasy points, incoming player accumulates Phase 2 points, team score sums both ledger entries.",
        "verification_date": "2026-11-02",
        "applicable_contest": "SmartSub Tactical Simulation Sandbox",
        "status": "PROPOSED / EXPERIMENTAL",
        "rule_tier": "TIER_4_PROPOSED_EXPERIMENTAL"
    }
]

def get_rule_evidence_register() -> List[Dict[str, Any]]:
    return RULE_EVIDENCE_REGISTER

def get_rule_by_id(rule_id: str) -> Dict[str, Any]:
    for rule in RULE_EVIDENCE_REGISTER:
        if rule["rule_id"] == rule_id:
            return rule
    return None
