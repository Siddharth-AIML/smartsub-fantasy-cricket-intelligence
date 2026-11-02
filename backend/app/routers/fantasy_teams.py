from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import SyncSessionLocal
from app.models.fantasy_team import FantasyTeam, FantasyLineupSlot, SubstitutionRulesConfig
from app.schemas.api_schemas import (
    FantasyTeamSchema,
    BenchPriorityUpdateRequest,
    RuleConfigUpdateRequest
)
from app.services.match_simulator import MatchSimulator

router = APIRouter(prefix="/fantasy-teams", tags=["Fantasy Teams"])

@router.get("/{team_id}", response_model=FantasyTeamSchema)
def get_fantasy_team(team_id: str):
    db = SyncSessionLocal()
    try:
        MatchSimulator.recompute_active_points(db, team_id)
        team = db.query(FantasyTeam).options(
            joinedload(FantasyTeam.lineup_slots).joinedload(FantasyLineupSlot.player),
            joinedload(FantasyTeam.scoring_ledgers)
        ).filter_by(id=team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Fantasy team not found")
        return team
    finally:
        db.close()

@router.put("/{team_id}/bench-priority")
def update_bench_priority(team_id: str, req: BenchPriorityUpdateRequest):
    db = SyncSessionLocal()
    try:
        team = db.query(FantasyTeam).filter_by(id=team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Fantasy team not found")

        for item in req.priorities:
            slot = db.query(FantasyLineupSlot).filter_by(
                fantasy_team_id=team_id,
                player_id=item.player_id
            ).first()
            if slot:
                slot.priority_rank = item.priority_rank
                slot.priority_label = item.priority_label
        db.commit()
        return {"status": "PRIORITIES_UPDATED"}
    finally:
        db.close()

@router.put("/{team_id}/rule-config")
def update_rule_config(team_id: str, req: RuleConfigUpdateRequest):
    db = SyncSessionLocal()
    try:
        cfg = db.query(SubstitutionRulesConfig).filter_by(fantasy_team_id=team_id).first()
        if not cfg:
            cfg = SubstitutionRulesConfig(fantasy_team_id=team_id)
            db.add(cfg)

        if req.scenario_1_enabled is not None:
            cfg.scenario_1_enabled = req.scenario_1_enabled
        if req.scenario_2_enabled is not None:
            cfg.scenario_2_enabled = req.scenario_2_enabled
        if req.inherit_captaincy_on_substitution is not None:
            cfg.inherit_captaincy_on_substitution = req.inherit_captaincy_on_substitution

        if req.rule_mode:
            team = db.query(FantasyTeam).filter_by(id=team_id).first()
            if team:
                team.rule_mode = req.rule_mode

        db.commit()
        return {"status": "RULES_CONFIG_UPDATED"}
    finally:
        db.close()
