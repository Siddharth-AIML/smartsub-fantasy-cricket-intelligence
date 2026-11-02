import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, JSON, ForeignKey, Enum as SQLEnum, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.enums import FantasySlotType, FantasySelectionStatus, RuleTier

class FantasyTeam(Base):
    __tablename__ = "fantasy_teams"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    match_id = Column(String(36), ForeignKey("matches.id"), nullable=False)
    user_id = Column(String(50), default="demo_user")
    team_name = Column(String(100), default="SmartSub Tactical XI")
    captain_player_id = Column(String(36), ForeignKey("players.id"), nullable=True)
    vice_captain_player_id = Column(String(36), ForeignKey("players.id"), nullable=True)
    rule_mode = Column(SQLEnum(RuleTier), default=RuleTier.TIER_4_PROPOSED_EXPERIMENTAL)
    total_points = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    match = relationship("Match", back_populates="fantasy_teams")
    lineup_slots = relationship("FantasyLineupSlot", back_populates="fantasy_team", cascade="all, delete-orphan")
    scoring_ledgers = relationship("InningsScoringLedger", back_populates="fantasy_team", cascade="all, delete-orphan")
    decisions = relationship("SubstitutionDecision", back_populates="fantasy_team", cascade="all, delete-orphan")
    rules_config = relationship("SubstitutionRulesConfig", back_populates="fantasy_team", uselist=False, cascade="all, delete-orphan")
    captain = relationship("Player", foreign_keys=[captain_player_id])
    vice_captain = relationship("Player", foreign_keys=[vice_captain_player_id])


class FantasyLineupSlot(Base):
    __tablename__ = "fantasy_lineup_slots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fantasy_team_id = Column(String(36), ForeignKey("fantasy_teams.id"), nullable=False)
    player_id = Column(String(36), ForeignKey("players.id"), nullable=False)
    slot_type = Column(SQLEnum(FantasySlotType), nullable=False)  # STARTER or BACKUP
    priority_rank = Column(Integer, nullable=True)  # 1, 2, 3, 4 for BACKUP; None for STARTER
    priority_label = Column(String(10), nullable=True)  # B1, B2, B3, B4 for BACKUP
    fantasy_selection_status = Column(SQLEnum(FantasySelectionStatus), default=FantasySelectionStatus.NOT_SELECTED)
    entry_innings = Column(Integer, default=1)
    exit_innings = Column(Integer, nullable=True)
    substituted_in_for_player_id = Column(String(36), nullable=True)
    fantasy_points = Column(Float, default=0.0)
    active_fantasy_points = Column(Float, default=0.0)

    __table_args__ = (
        # Ensure a player cannot be placed in multiple slots of the same fantasy team
        UniqueConstraint("fantasy_team_id", "player_id", name="uq_team_player_slot"),
    )

    fantasy_team = relationship("FantasyTeam", back_populates="lineup_slots")
    player = relationship("Player", back_populates="lineup_slots")


class SubstitutionRulesConfig(Base):
    __tablename__ = "substitution_rules_config"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fantasy_team_id = Column(String(36), ForeignKey("fantasy_teams.id"), unique=True, nullable=False)
    scenario_1_enabled = Column(Boolean, default=True)
    scenario_2_enabled = Column(Boolean, default=True)
    inherit_captaincy_on_substitution = Column(Boolean, default=False)
    parameters = Column(JSON, default=dict)

    fantasy_team = relationship("FantasyTeam", back_populates="rules_config")
