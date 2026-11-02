import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class AIExplanation(Base):
    __tablename__ = "ai_explanations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    decision_id = Column(String(36), ForeignKey("substitution_decisions.id"), unique=True, nullable=False)
    explanation_type = Column(String(50), nullable=False, default="DETERMINISTIC_FALLBACK")  # GEMINI_LIVE or DETERMINISTIC_FALLBACK
    model_name = Column(String(50), default="fallback-template-v2")
    is_fallback = Column(Boolean, default=True)
    
    executive_summary = Column(Text, nullable=False)
    tactical_rationale = Column(Text, nullable=False)
    rule_compliance_audit = Column(Text, nullable=False)
    strategic_trade_offs = Column(JSON, default=dict)
    counterfactual_alternatives = Column(JSON, default=dict)
    data_provenance = Column(String(50), default="ILLUSTRATIVE_SIMULATION")
    created_at = Column(DateTime, default=datetime.utcnow)

    decision = relationship("SubstitutionDecision", back_populates="ai_explanation")
