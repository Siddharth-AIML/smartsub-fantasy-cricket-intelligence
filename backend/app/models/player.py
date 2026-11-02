import uuid
from sqlalchemy import Column, String, Float, Boolean, Integer, JSON, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.enums import PlayerRole, RealMatchParticipation

class Player(Base):
    __tablename__ = "players"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(100), nullable=False)
    short_name = Column(String(50), nullable=False)
    team = Column(String(50), nullable=False)  # CSK or MI
    role = Column(SQLEnum(PlayerRole), nullable=False)  # WK, BAT, AR, BOWL
    credits = Column(Float, nullable=False, default=8.5)
    is_impact_eligible = Column(Boolean, default=True)
    real_match_participation = Column(SQLEnum(RealMatchParticipation), default=RealMatchParticipation.NOT_STARTED)
    stats = Column(JSON, default=dict)
    data_provenance = Column(String(50), default="ILLUSTRATIVE_SIMULATION")
    is_independently_verified = Column(Boolean, default=False)

    # Relationships
    lineup_slots = relationship("FantasyLineupSlot", back_populates="player")
    scoring_ledgers = relationship("InningsScoringLedger", back_populates="player")


class InningsScoringLedger(Base):
    __tablename__ = "innings_scoring_ledger"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fantasy_team_id = Column(String(36), ForeignKey("fantasy_teams.id"), nullable=False)
    player_id = Column(String(36), ForeignKey("players.id"), nullable=False)
    match_id = Column(String(36), ForeignKey("matches.id"), nullable=False)
    innings = Column(Integer, nullable=False)  # 1 or 2
    
    # Granular batting/bowling/fielding attribution
    balls_faced = Column(Integer, default=0)
    runs_scored = Column(Integer, default=0)
    fours = Column(Integer, default=0)
    sixes = Column(Integer, default=0)
    overs_bowled = Column(Float, default=0.0)
    wickets_taken = Column(Integer, default=0)
    maidens = Column(Integer, default=0)
    runs_conceded = Column(Integer, default=0)
    catches = Column(Integer, default=0)
    stumpings = Column(Integer, default=0)
    run_outs = Column(Integer, default=0)
    
    # Points
    base_fantasy_points = Column(Float, default=0.0)
    multiplier = Column(Float, default=1.0)  # 1.0, 1.5 (VC), 2.0 (C)
    total_fantasy_points = Column(Float, default=0.0)
    
    is_locked = Column(Boolean, default=False)
    idempotency_key = Column(String(100), nullable=False)

    __table_args__ = (
        UniqueConstraint("fantasy_team_id", "player_id", "innings", "idempotency_key", name="uq_fantasy_player_inn_idemp"),
    )

    player = relationship("Player", back_populates="scoring_ledgers")
    fantasy_team = relationship("FantasyTeam", back_populates="scoring_ledgers")
