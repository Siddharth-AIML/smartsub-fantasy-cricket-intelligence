from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from app.database import SyncSessionLocal
from app.models.substitution import SubstitutionDecision
from app.models.match import MatchEvent
from app.schemas.api_schemas import SubstitutionDecisionResponse
from app.services.substitution_engine import SubstitutionEngine

router = APIRouter(prefix="/substitutions", tags=["Substitutions"])

@router.get("/history/{team_id}", response_model=list[SubstitutionDecisionResponse])
def get_substitution_history(team_id: str):
    db = SyncSessionLocal()
    try:
        decisions = db.query(SubstitutionDecision).filter_by(
            fantasy_team_id=team_id
        ).order_by(SubstitutionDecision.created_at.desc()).all()
        return decisions
    finally:
        db.close()

@router.get("/decision/{decision_id}", response_model=SubstitutionDecisionResponse)
def get_decision_details(decision_id: str):
    db = SyncSessionLocal()
    try:
        decision = db.query(SubstitutionDecision).filter_by(id=decision_id).first()
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        return decision
    finally:
        db.close()

@router.post("/evaluate/{team_id}")
def trigger_manual_evaluation(team_id: str):
    """
    Manually evaluates any unannounced players or pending in-match substitutions.
    """
    db = SyncSessionLocal()
    try:
        latest_event = db.query(MatchEvent).order_by(MatchEvent.sequence_number.desc()).first()
        if not latest_event:
            return {"status": "NO_EVENTS_FOUND"}
        decision = SubstitutionEngine.process_match_event(db, team_id, latest_event)
        return {"status": "EVALUATION_COMPLETE", "decision": decision}
    finally:
        db.close()
