import pytest
from app.database import Base, sync_engine, SyncSessionLocal
from app.models.enums import MatchStatus, FantasySelectionStatus
from app.models.match import Match
from app.models.fantasy_team import FantasyTeam, FantasyLineupSlot
from app.services.seed_data import seed_database
from app.services.match_simulator import MatchSimulator

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=sync_engine)
    db = SyncSessionLocal()
    seed_database(db)
    yield db
    db.close()

def test_t20_overs_notation_and_progression(test_db):
    match_id = "match_csk_mi_2026"
    team_id = "fantasy_team_demo"
    MatchSimulator.reset_match(test_db, match_id, team_id)
    MatchSimulator.conduct_toss(test_db, match_id)
    MatchSimulator.announce_lineups(test_db, match_id, team_id)

    match = test_db.query(Match).filter_by(id=match_id).first()
    assert match.status == MatchStatus.INNINGS_1

    # Simulate 6 balls (1 over)
    for ball_idx in range(1, 7):
        res = MatchSimulator.step_ball(test_db, match_id, team_id)
        if ball_idx < 6:
            assert res["overs_formatted"] == f"0.{ball_idx}"
        else:
            assert res["overs_formatted"] == "1.0"

    assert match.current_over == 1
    assert match.current_ball == 0

def test_t20_overs_cannot_exceed_twenty(test_db):
    match_id = "match_csk_mi_2026"
    team_id = "fantasy_team_demo"
    MatchSimulator.reset_match(test_db, match_id, team_id)
    MatchSimulator.conduct_toss(test_db, match_id)
    MatchSimulator.announce_lineups(test_db, match_id, team_id)

    match = test_db.query(Match).filter_by(id=match_id).first()

    # Fast forward to 19 overs and 5 balls
    match.current_over = 19
    match.current_ball = 5
    match.scoreboard["innings_1"]["overs"] = "19.5"
    test_db.commit()

    # Simulate 120th ball (over 20.0 completion)
    res = MatchSimulator.step_ball(test_db, match_id, team_id)
    assert res["overs_formatted"] == "20.0"
    assert match.scoreboard["phase"] == "INNINGS_BREAK"

    # Attempting another ball should be rejected
    res_rejected = MatchSimulator.step_ball(test_db, match_id, team_id)
    assert "error" in res_rejected
    assert "already ended" in res_rejected["error"] or "not in an active innings" in res_rejected["error"]

def test_single_occupant_scoring_in_scenario_2(test_db):
    match_id = "match_csk_mi_2026"
    team_id = "fantasy_team_demo"
    
    res = MatchSimulator.execute_scenario_2_automation(test_db, match_id, team_id)
    assert res["status"] == "SCENARIO_2_COMPLETED"

    pts_info = res["points_info"]
    # Check replacement slot audit
    rep_audit = pts_info["replacement_slot_audit"]
    assert rep_audit is not None
    assert rep_audit["active_player_in_id"] == "p_csk_stoinis"
    assert rep_audit["replaced_player_out_id"] == "p_csk_thakur"
    assert rep_audit["replaced_player_historical_points"] == 43.0
    assert rep_audit["active_player_in_points"] == 32.0
    assert rep_audit["active_slot_contribution"] == 32.0  # NOT 75.0!

    # Active fantasy points strictly excludes historical locked points
    assert pts_info["historical_locked_points"] >= 43.0
    
    # Check that Thakur is SUBSTITUTED_OUT and Stoinis is SELECTED
    thakur_slot = test_db.query(FantasyLineupSlot).filter_by(fantasy_team_id=team_id, player_id="p_csk_thakur").first()
    stoinis_slot = test_db.query(FantasyLineupSlot).filter_by(fantasy_team_id=team_id, player_id="p_csk_stoinis").first()
    assert thakur_slot.fantasy_selection_status == FantasySelectionStatus.SUBSTITUTED_OUT
    assert stoinis_slot.fantasy_selection_status == FantasySelectionStatus.SELECTED
