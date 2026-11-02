import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, JSON, ForeignKey, Enum as SQLEnum, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.enums import MatchStatus

class Match(Base):
    __tablename__ = "matches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    match_code = Column(String(50), unique=True, nullable=False, default="IPL_2026_CSK_MI")
    home_team = Column(String(50), nullable=False, default="CSK")
    away_team = Column(String(50), nullable=False, default="MI")
    venue = Column(String(100), default="Wankhede Stadium, Mumbai")
    status = Column(SQLEnum(MatchStatus), default=MatchStatus.UPCOMING)
    toss_winner = Column(String(50), nullable=True)
    toss_decision = Column(String(20), nullable=True)  # BAT or BOWL
    current_innings = Column(Integer, default=1)
    current_over = Column(Integer, default=0)
    current_ball = Column(Integer, default=0)
    scoreboard = Column(JSON, default=dict)
    data_provenance = Column(String(50), default="ILLUSTRATIVE_SIMULATION")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    squad_members = relationship("MatchSquad", back_populates="match", cascade="all, delete-orphan")
    events = relationship("MatchEvent", back_populates="match", order_by="MatchEvent.sequence_number")
    fantasy_teams = relationship("FantasyTeam", back_populates="match")


class MatchSquad(Base):
    __tablename__ = "match_squads"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    match_id = Column(String(36), ForeignKey("matches.id"), nullable=False)
    player_id = Column(String(36), ForeignKey("players.id"), nullable=False)
    team = Column(String(50), nullable=False)
    is_announced_xi = Column(Integer, default=0)  # 1 for playing XI, 0 for not
    is_impact_candidate = Column(Integer, default=0)
    is_substitute = Column(Integer, default=0)

    match = relationship("Match", back_populates="squad_members")
    player = relationship("Player")


class MatchEvent(Base):
    __tablename__ = "match_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    match_id = Column(String(36), ForeignKey("matches.id"), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    idempotency_key = Column(String(100), unique=True, nullable=False)
    event_type = Column(String(50), nullable=False)  # TOSS, LINEUP, IMPACT, BALL, WICKET, INNINGS_END
    innings = Column(Integer, default=1)
    over = Column(Integer, default=0)
    ball = Column(Integer, default=0)
    payload = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("match_id", "sequence_number", name="uq_match_sequence"),
    )

    match = relationship("Match", back_populates="events")


class ProcessedEvent(Base):
    __tablename__ = "processed_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fantasy_team_id = Column(String(36), ForeignKey("fantasy_teams.id"), nullable=False)
    event_id = Column(String(36), ForeignKey("match_events.id"), nullable=False)
    idempotency_key = Column(String(100), nullable=False)
    processed_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("fantasy_team_id", "idempotency_key", name="uq_team_idempotency"),
    )
