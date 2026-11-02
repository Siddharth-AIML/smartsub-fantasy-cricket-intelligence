import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, JSON, ForeignKey, Enum as SQLEnum, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.enums import RuleTier, DecisionStatus

class SubstitutionDecision(Base):
    __tablename__ = "substitution_decisions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fantasy_team_id = Column(String(36), ForeignKey("fantasy_teams.id"), nullable=False)
    match_event_id = Column(String(36), ForeignKey("match_events.id"), nullable=True)
    idempotency_key = Column(String(100), nullable=False)
    
    player_out_id = Column(String(36), ForeignKey("players.id"), nullable=True)
    player_in_id = Column(String(36), ForeignKey("players.id"), nullable=True)
    priority_rank_used = Column(Integer, nullable=True)  # 1, 2, 3, 4
    
    rule_id = Column(String(50), nullable=False, default="R-SUB-01")
    rule_tier = Column(SQLEnum(RuleTier), default=RuleTier.TIER_4_PROPOSED_EXPERIMENTAL)
    reason_code = Column(String(100), nullable=False)
    status = Column(SQLEnum(DecisionStatus), default=DecisionStatus.EXECUTED)
    
    evaluations_audit = Column(JSON, default=list)
    constraints_checked = Column(JSON, default=dict)
    squad_snapshot_before = Column(JSON, default=dict)
    squad_snapshot_after = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("fantasy_team_id", "idempotency_key", name="uq_decision_team_idempotency"),
    )

    fantasy_team = relationship("FantasyTeam", back_populates="decisions")
    player_out = relationship("Player", foreign_keys=[player_out_id])
    player_in = relationship("Player", foreign_keys=[player_in_id])
    ai_explanation = relationship("AIExplanation", back_populates="decision", uselist=False, cascade="all, delete-orphan")
