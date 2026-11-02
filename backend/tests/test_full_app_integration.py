import pytest
from app.database import Base, sync_engine, SyncSessionLocal
from app.services.seed_data import seed_database
from app.main import health_check
from app.routers.rules import list_rule_evidence
from app.routers.matches import list_matches, reset_match, step_simulation, trigger_impact_player, replay_match_events, get_live_state
from app.routers.fantasy_teams import get_fantasy_team
from app.routers.substitutions import get_substitution_history, get_decision_details
from app.routers.ai import get_ai_explanation
from app.schemas.api_schemas import StepRequest, TriggerImpactRequest

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=sync_engine)
    db = SyncSessionLocal()
    seed_database(db)
    db.close()

def test_full_application_lifecycle():
    # 1. Health check
    health = health_check()
    assert health["status"] == "healthy"
    assert "ILLUSTRATIVE_SIMULATION" in health["data_provenance"]

    # 2. Rule evidence register
    rules_data = list_rule_evidence()
    rules = rules_data["rules"]
    assert len(rules) >= 4
    # Verify Tier 1 vs Tier 4
    assert any(r["rule_tier"] == "TIER_1_VERIFIED" for r in rules)
    assert any(r["rule_tier"] == "TIER_4_PROPOSED_EXPERIMENTAL" for r in rules)

    # 3. Match state
    matches = list_matches()
    assert len(matches) > 0
    match_id = matches[0].id
    assert match_id == "match_csk_mi_2026"

    # 4. Fantasy team verification
    team = get_fantasy_team("fantasy_team_demo")
    assert len(team.lineup_slots) == 15
    starters = [s for s in team.lineup_slots if s.slot_type.value == "STARTER"]
    backups = [s for s in team.lineup_slots if s.slot_type.value == "BACKUP"]
    assert len(starters) == 11
    assert len(backups) == 4
    # Verify 15 unique players
    player_ids = [s.player_id for s in team.lineup_slots]
    assert len(set(player_ids)) == 15

    # 5. Reset match to pre-match
    reset_res = reset_match(match_id)
    assert reset_res["status"] == "RESET_SUCCESS"
    assert reset_res["match"].scoreboard["phase"] == "PRE_MATCH"

    # 6. Step Toss
    toss_res = step_simulation(match_id, StepRequest(step_type="TOSS"))
    assert toss_res["status"] == "TOSS_CONDUCTED"
    assert toss_res["match"].scoreboard["phase"] == "TOSS_CONDUCTED"

    # 7. Step Lineup (Scenario 1 execution)
    lineup_res = step_simulation(match_id, StepRequest(step_type="LINEUP"))
    assert lineup_res["status"] == "LINEUPS_ANNOUNCED"
    decision_id = lineup_res["substitution_decision_id"]
    assert decision_id is not None

    sub_decision = get_decision_details(decision_id)
    assert sub_decision.status.value == "EXECUTED"
    assert sub_decision.player_out_id == "p_csk_mustafizur"
    assert sub_decision.player_in_id == "p_csk_thakur"

    # 8. Check substitution history
    history = get_substitution_history("fantasy_team_demo")
    assert len(history) >= 1
    assert history[0].id == decision_id

    # 9. AI explanation for Scenario 1
    ai_exp = get_ai_explanation(decision_id)
    assert ai_exp.executive_summary is not None
    assert ai_exp.tactical_rationale is not None
    assert ai_exp.rule_compliance_audit is not None
    assert ai_exp.data_provenance == "ILLUSTRATIVE_SIMULATION"

    # 10. Jump to Innings 2
    inn2_res = step_simulation(match_id, StepRequest(step_type="INN2_JUMP"))
    assert inn2_res["status"] == "INNINGS_2_STARTED"
    assert inn2_res["match"].current_innings == 2

    # 11. Trigger Impact Player (Scenario 2 execution)
    impact_res = trigger_impact_player(
        match_id,
        TriggerImpactRequest(player_out_id="p_csk_thakur", player_in_id="p_csk_stoinis")
    )
    assert impact_res["status"] == "IMPACT_PLAYER_TRIGGERED"
    impact_sub = impact_res.get("decision")
    assert impact_sub is not None
    assert impact_sub.status.value == "EXECUTED"
    assert impact_sub.player_out_id == "p_csk_thakur"
    assert impact_sub.player_in_id == "p_csk_stoinis"

    # 12. Verify Scoring Ledger (outgoing Thakur Innings 1 points preserved and locked)
    team_updated = get_fantasy_team("fantasy_team_demo")
    ledgers = team_updated.scoring_ledgers
    thakur_ledger = next((l for l in ledgers if l.player_id == "p_csk_thakur" and l.innings == 1), None)
    assert thakur_ledger is not None
    assert thakur_ledger.is_locked is True

    # 13. Event Replay
    replay_res = replay_match_events(match_id)
    assert replay_res["status"] == "REPLAY_COMPLETE"
    assert replay_res["replayed_events_count"] >= 3
    final_snap = replay_res["final_snapshot"]
    assert len(final_snap["selected_xi"]) == 11

def test_automated_scenario_endpoints():
    from app.routers.matches import run_scenario_1_automated, run_scenario_2_automated
    match_id = "match_csk_mi_2026"
    
    # 1. Test Automated Scenario 1
    s1_res = run_scenario_1_automated(match_id)
    assert s1_res["status"] == "SCENARIO_1_COMPLETED"
    assert s1_res["substitution_decision"].player_out_id == "p_csk_mustafizur"
    assert s1_res["substitution_decision"].player_in_id == "p_csk_thakur"
    assert s1_res["ai_explanation"] is not None

    team_s1 = get_fantasy_team("fantasy_team_demo")
    selected_slots = [s for s in team_s1.lineup_slots if s.fantasy_selection_status.value == "SELECTED"]
    assert len(selected_slots) == 11
    selected_ids = [s.player_id for s in selected_slots]
    assert "p_csk_mustafizur" not in selected_ids
    assert "p_csk_thakur" in selected_ids

    # 2. Test Automated Scenario 2
    s2_res = run_scenario_2_automated(match_id)
    assert s2_res["status"] == "SCENARIO_2_COMPLETED"
    assert s2_res["substitution_decision"].player_out_id == "p_csk_thakur"
    assert s2_res["substitution_decision"].player_in_id == "p_csk_stoinis"
    assert s2_res["points_info"]["historical_locked_points"] >= 43.0

    team_s2 = get_fantasy_team("fantasy_team_demo")
    selected_slots_s2 = [s for s in team_s2.lineup_slots if s.fantasy_selection_status.value == "SELECTED"]
    assert len(selected_slots_s2) == 11
    selected_ids_s2 = [s.player_id for s in selected_slots_s2]
    assert "p_csk_thakur" not in selected_ids_s2
    assert "p_csk_stoinis" in selected_ids_s2
    # Verify Shardul Thakur's historical points are locked
    thakur_ledger = next((l for l in team_s2.scoring_ledgers if l.player_id == "p_csk_thakur" and l.innings == 1), None)
    assert thakur_ledger is not None
    assert thakur_ledger.total_fantasy_points == 43.0
    assert thakur_ledger.is_locked is True
    # Verify Stoinis's Innings 2 points
    stoinis_ledger = next((l for l in team_s2.scoring_ledgers if l.player_id == "p_csk_stoinis" and l.innings == 2), None)
    assert stoinis_ledger is not None
    assert stoinis_ledger.total_fantasy_points == 32.0
