from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SyncSessionLocal
from app.models.match import Match, MatchEvent
from app.models.fantasy_team import FantasyTeam
from app.schemas.api_schemas import MatchSchema, StepRequest, TriggerImpactRequest
from app.services.match_simulator import MatchSimulator
from app.services.substitution_engine import SubstitutionEngine

router = APIRouter(prefix="/api/matches", tags=["Matches"])

@router.get("", response_model=list[MatchSchema])
def list_matches():
    db = SyncSessionLocal()
    try:
        matches = db.query(Match).all()
        return matches
    finally:
        db.close()

@router.get("/{match_id}/live-state")
def get_live_state(match_id: str):
    db = SyncSessionLocal()
    try:
        match = db.query(Match).filter_by(id=match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        team = db.query(FantasyTeam).filter_by(match_id=match_id).first()
        team_id = team.id if team else "fantasy_team_demo"

        pts_info = MatchSimulator.recompute_active_points(db, team_id)
        scorecard_data = MatchSimulator.build_canonical_scorecard(match, db)

        return {
            "match": match,
            "scoreboard": match.scoreboard,
            "scorecard": scorecard_data,
            "status": match.status.value,
            "current_innings": match.current_innings,
            "current_over": match.current_over,
            "current_ball": match.current_ball,
            "fantasy_team_id": team_id,
            "fantasy_total_points": pts_info["active_total_points"],
            "fantasy_active_points": pts_info["active_total_points"],
            "historical_locked_points": pts_info["historical_locked_points"],
            "player_points_map": pts_info.get("player_points_map", {}),
            "replacement_slot_audit": pts_info["replacement_slot_audit"],
            "latest_ai_explanation": match.scoreboard.get("latest_ai_explanation"),
            "data_provenance": "ILLUSTRATIVE_SIMULATION",
            "is_independently_verified": False
        }
    finally:
        db.close()

@router.post("/{match_id}/step")
def step_simulation(match_id: str, req: StepRequest):
    db = SyncSessionLocal()
    try:
        team = db.query(FantasyTeam).filter_by(match_id=match_id).first()
        team_id = team.id if team else "fantasy_team_demo"

        if req.step_type == "TOSS":
            match = MatchSimulator.conduct_toss(db, match_id)
            return {"status": "TOSS_CONDUCTED", "match": match}
        elif req.step_type == "LINEUP":
            res = MatchSimulator.announce_lineups(db, match_id, team_id)
            return {
                "status": "LINEUPS_ANNOUNCED",
                "substitution_decision_id": res["substitution_decision"].id if res.get("substitution_decision") else None,
                "message": "Lineups announced. Scenario 1 evaluated."
            }
        elif req.step_type == "INN2_JUMP":
            match = MatchSimulator.jump_to_second_innings(db, match_id, team_id)
            return {"status": "INNINGS_2_STARTED", "match": match}
        elif req.step_type == "OVER":
            last_res = {}
            for _ in range(6):
                last_res = MatchSimulator.step_ball(db, match_id, team_id)
            return {"status": "OVER_SIMULATED", "details": last_res}
        else:  # BALL
            res = MatchSimulator.step_ball(db, match_id, team_id)
            return {"status": "BALL_SIMULATED", "details": res}
    finally:
        db.close()

@router.post("/{match_id}/trigger-impact-player")
def trigger_impact_player(match_id: str, req: TriggerImpactRequest):
    db = SyncSessionLocal()
    try:
        team = db.query(FantasyTeam).filter_by(match_id=match_id).first()
        team_id = team.id if team else "fantasy_team_demo"

        res = MatchSimulator.trigger_real_impact_player(
            db=db,
            match_id=match_id,
            fantasy_team_id=team_id,
            player_out_id=req.player_out_id,
            player_in_id=req.player_in_id
        )
        return {
            "status": "IMPACT_PLAYER_TRIGGERED",
            "decision": res.get("substitution_decision")
        }
    finally:
        db.close()

@router.post("/{match_id}/scenarios/run-scenario-1")
def run_scenario_1_automated(match_id: str):
    """
    Executes full automated Scenario 1 demonstration:
    Reset -> Toss -> Lineups announced -> Mustafizur DNP -> Conway B1 skipped -> Thakur B2 substituted.
    """
    db = SyncSessionLocal()
    try:
        team = db.query(FantasyTeam).filter_by(match_id=match_id).first()
        team_id = team.id if team else "fantasy_team_demo"
        result = MatchSimulator.execute_scenario_1_automation(db, match_id, team_id)
        return result
    finally:
        db.close()

@router.post("/{match_id}/scenarios/run-scenario-2")
def run_scenario_2_automated(match_id: str):
    """
    Executes full automated Scenario 2 demonstration:
    Scenario 1 -> Innings 1 simulated (MI 182/6; Thakur locks 43.0 pts) -> Jump to Innings 2 ->
    Stoinis Impact Player enters -> Innings 2 chase simulated (Stoinis 32.0 pts) ->
    Single-occupant scoring applied (Active = 32.0, Historical = 43.0).
    """
    db = SyncSessionLocal()
    try:
        team = db.query(FantasyTeam).filter_by(match_id=match_id).first()
        team_id = team.id if team else "fantasy_team_demo"
        result = MatchSimulator.execute_scenario_2_automation(db, match_id, team_id)
        return result
    finally:
        db.close()

@router.post("/{match_id}/reset")
def reset_match(match_id: str):
    db = SyncSessionLocal()
    try:
        team = db.query(FantasyTeam).filter_by(match_id=match_id).first()
        team_id = team.id if team else "fantasy_team_demo"
        match = MatchSimulator.reset_match(db, match_id, team_id)
        return {"status": "RESET_SUCCESS", "match": match}
    finally:
        db.close()

@router.post("/{match_id}/replay")
def replay_match_events(match_id: str):
    db = SyncSessionLocal()
    try:
        team = db.query(FantasyTeam).filter_by(match_id=match_id).first()
        team_id = team.id if team else "fantasy_team_demo"

        events = db.query(MatchEvent).filter_by(match_id=match_id).order_by(MatchEvent.sequence_number.asc()).all()
        snapshot = SubstitutionEngine.replay_all_events(db, team_id, events)
        return {
            "status": "REPLAY_COMPLETE",
            "replayed_events_count": len(events),
            "final_snapshot": snapshot
        }
    finally:
        db.close()
