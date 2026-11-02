from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict

class PlayerSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    full_name: str
    short_name: str
    team: str
    role: str
    credits: float
    is_impact_eligible: bool
    real_match_participation: str
    stats: Dict[str, Any] = {}
    data_provenance: str = "ILLUSTRATIVE_SIMULATION"

class LineupSlotSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    player_id: str
    slot_type: str
    priority_rank: Optional[int] = None
    priority_label: Optional[str] = None
    fantasy_selection_status: str
    entry_innings: Optional[int] = None
    exit_innings: Optional[int] = None
    substituted_in_for_player_id: Optional[str] = None
    fantasy_points: float = 0.0
    active_fantasy_points: float = 0.0
    player: PlayerSchema

class InningsLedgerSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    player_id: str
    innings: int
    runs_scored: int = 0
    balls_faced: int = 0
    fours: int = 0
    sixes: int = 0
    overs_bowled: float = 0.0
    wickets_taken: int = 0
    maidens: int = 0
    catches: int = 0
    base_fantasy_points: float = 0.0
    multiplier: float = 1.0
    total_fantasy_points: float = 0.0
    is_locked: bool = False

class FantasyTeamSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    match_id: str
    team_name: str
    captain_player_id: Optional[str] = None
    vice_captain_player_id: Optional[str] = None
    rule_mode: str
    total_points: float = 0.0
    lineup_slots: List[LineupSlotSchema] = []
    scoring_ledgers: List[InningsLedgerSchema] = []

class MatchSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    match_code: str
    home_team: str
    away_team: str
    venue: str
    status: str
    toss_winner: Optional[str] = None
    toss_decision: Optional[str] = None
    current_innings: int
    current_over: int
    current_ball: int
    scoreboard: Dict[str, Any] = {}
    data_provenance: str = "ILLUSTRATIVE_SIMULATION"

class StepRequest(BaseModel):
    step_type: str = "BALL"

class TriggerImpactRequest(BaseModel):
    player_out_id: str = "p_csk_thakur"
    player_in_id: str = "p_csk_stoinis"

class BenchPriorityUpdateItem(BaseModel):
    player_id: str
    priority_rank: int
    priority_label: str

class BenchPriorityUpdateRequest(BaseModel):
    priorities: List[BenchPriorityUpdateItem]

class RuleConfigUpdateRequest(BaseModel):
    scenario_1_enabled: Optional[bool] = None
    scenario_2_enabled: Optional[bool] = None
    inherit_captaincy_on_substitution: Optional[bool] = None
    rule_mode: Optional[str] = None

class SubstitutionDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    fantasy_team_id: str
    match_event_id: Optional[str] = None
    idempotency_key: str
    player_out_id: Optional[str] = None
    player_in_id: Optional[str] = None
    priority_rank_used: Optional[int] = None
    rule_id: str
    rule_tier: str
    reason_code: str
    status: str
    evaluations_audit: List[Dict[str, Any]] = []
    constraints_checked: Dict[str, Any] = {}
    squad_snapshot_before: Dict[str, Any] = {}
    squad_snapshot_after: Dict[str, Any] = {}

class AIExplanationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    decision_id: str
    explanation_type: str
    model_name: str
    is_fallback: bool
    executive_summary: str
    tactical_rationale: str
    rule_compliance_audit: str
    strategic_trade_offs: Dict[str, Any] = {}
    counterfactual_alternatives: Dict[str, Any] = {}
    data_provenance: str = "ILLUSTRATIVE_SIMULATION"
