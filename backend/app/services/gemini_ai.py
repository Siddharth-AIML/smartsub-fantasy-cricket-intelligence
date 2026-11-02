import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.models.substitution import SubstitutionDecision
from app.models.ai_explanation import AIExplanation
from app.models.player import Player, InningsScoringLedger

logger = logging.getLogger("smartsub.ai")

class GeminiAIService:
    @classmethod
    def explain_decision(cls, db: Session, decision_id: str) -> AIExplanation:
        """
        Explains a deterministic substitution decision.
        If GEMINI_API_KEY is configured, calls Google Gemini API.
        Otherwise, uses the deterministic fallback template with explicit metadata tags.
        """
        # Check if already explained
        existing = db.query(AIExplanation).filter_by(decision_id=decision_id).first()
        if existing:
            return existing

        decision = db.query(SubstitutionDecision).filter_by(id=decision_id).first()
        if not decision:
            raise ValueError(f"Decision {decision_id} not found")

        # Try Gemini Live if key is available
        if settings.GEMINI_API_KEY:
            try:
                explanation = cls._generate_gemini_live_explanation(db, decision)
                if explanation:
                    db.add(explanation)
                    db.commit()
                    return explanation
            except Exception as e:
                logger.warning(f"Gemini API call failed, falling back to deterministic template: {e}")

        # Deterministic Fallback Generator
        explanation = cls._generate_deterministic_fallback(db, decision)
        db.add(explanation)
        db.commit()
        return explanation

    @classmethod
    def _generate_gemini_live_explanation(cls, db: Session, decision: SubstitutionDecision) -> Optional[AIExplanation]:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)

        p_out = decision.player_out
        p_in = decision.player_in

        prompt = f"""
You are the SmartSub Tactical Fantasy Cricket Analyst.
Analyze the following deterministic substitution decision executed by the SmartSub engine.

Context:
- Decision ID: {decision.id}
- Rule Applied: {decision.rule_id} ({decision.rule_tier.value})
- Reason Code: {decision.reason_code}
- Status: {decision.status.value}
- Outgoing Player: {p_out.full_name if p_out else 'N/A'} (Role: {p_out.role.value if p_out else 'N/A'}, Team: {p_out.team if p_out else 'N/A'}, Credits: {p_out.credits if p_out else 'N/A'})
- Incoming Player: {p_in.full_name if p_in else 'N/A'} (Role: {p_in.role.value if p_in else 'N/A'}, Team: {p_in.team if p_in else 'N/A'}, Credits: {p_in.credits if p_in else 'N/A'}, Priority: {decision.priority_rank_used})
- Evaluations Audit: {json.dumps(decision.evaluations_audit)}
- Constraints Checked: {json.dumps(decision.constraints_checked)}

CRITICAL INSTRUCTIONS:
1. Explain the deterministic decision. DO NOT invent platform rules or claim unverified Dream11 in-match behaviors.
2. DO NOT output arbitrary or hallucinated confidence scores.
3. Provide crisp cricketing and fantasy points rationale.
4. Output strict JSON matching the schema below:

{{
  "executive_summary": "1-2 sentence executive summary of the swap",
  "tactical_rationale": "Detailed cricketing rationale",
  "rule_compliance_audit": "Detailed explanation of rule validation (credits, quotas, verified vs experimental)",
  "strategic_trade_offs": {{
    "pros": ["Pro 1", "Pro 2"],
    "cons": ["Con 1"],
    "net_point_impact": "Expected or observed point delta"
  }},
  "counterfactual_alternatives": {{
    "alternative_option": "What would have occurred had this rule not triggered"
  }}
}}
"""
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        parsed = json.loads(response.text)

        return AIExplanation(
            decision_id=decision.id,
            explanation_type="GEMINI_LIVE",
            model_name=settings.GEMINI_MODEL,
            is_fallback=False,
            executive_summary=parsed.get("executive_summary", ""),
            tactical_rationale=parsed.get("tactical_rationale", ""),
            rule_compliance_audit=parsed.get("rule_compliance_audit", ""),
            strategic_trade_offs=parsed.get("strategic_trade_offs", {}),
            counterfactual_alternatives=parsed.get("counterfactual_alternatives", {}),
            data_provenance="ILLUSTRATIVE_SIMULATION"
        )

    @classmethod
    def _generate_deterministic_fallback(cls, db: Session, decision: SubstitutionDecision) -> AIExplanation:
        """
        Synthesizes structured, zero-hallucination deterministic template explanations.
        Tagged with is_fallback: True.
        """
        p_out = decision.player_out
        p_in = decision.player_in

        if decision.reason_code == "SCENARIO_1_B2_SUBSTITUTED_WHEN_B1_DNP":
            p_out_name = p_out.short_name if p_out else "Unannounced Starter"
            p_in_name = p_in.short_name if p_in else "Eligible Backup"
            summary = f"[SIMULATED RATIONALE] Replaced unannounced starter {p_out_name} with Priority 2 backup {p_in_name} after Priority 1 was bypassed."
            rationale = (
                f"Starter {p_out_name} was omitted from the confirmed real-world matchday squad (DID_NOT_PLAY). "
                f"Priority 1 backup Devon Conway (B1) was also unannounced (DID_NOT_PLAY) and bypassed per engine rules. "
                f"Priority 2 backup {p_in_name} was confirmed in the real Playing XI and satisfied all platform squad composition constraints."
            )
            audit = (
                f"Evaluated under Tier 4 Proposed Rule R-SUB-01. Confirmed {p_in_name}'s credit cost ({p_in.credits if p_in else 8.5} Cr) "
                f"complies with the 100-credit roster ceiling and preserves the 1-8 role quotas."
            )
            trade_offs = {
                "pros": [
                    f"Restores active 11-player scoring coverage with confirmed starter {p_in_name}.",
                    "Bypasses non-participating Priority 1 asset to prevent dead bench slot."
                ],
                "cons": [
                    "Consumes Priority 2 bench asset; remaining bench depth reduced."
                ],
                "net_point_impact": "Prevents 0.0 point forfeit from unannounced starter."
            }
            counterfactual = {
                "if_b1_forced": "Would have substituted a non-playing player with another non-playing player, yielding 0 fantasy points.",
                "if_b2_ineligible": "Engine would have proceeded down to evaluate Priority 3 (B3)."
            }

        elif decision.reason_code == "SCENARIO_2_IMPACT_SUB_INN2_EXECUTED":
            p_out_name = p_out.short_name if p_out else "Shardul Thakur"
            p_in_name = p_in.short_name if p_in else "Marcus Stoinis"
            
            # Fetch locked Innings 1 points from ledger
            inn1_ledger = db.query(InningsScoringLedger).filter_by(
                fantasy_team_id=decision.fantasy_team_id,
                player_id=decision.player_out_id,
                innings=1
            ).first()
            pts_locked = inn1_ledger.total_fantasy_points if inn1_ledger else 0.0

            summary = f"[SIMULATED RATIONALE] Substituted {p_out_name} with Impact Player {p_in_name} for 2nd Innings run chase."
            rationale = (
                f"{p_out_name} completed his bowling spell during Innings 1, securing {pts_locked:.1f} historical fantasy points. "
                f"Under SmartSub Tier 4 Proposed Rule R-SUB-02 (Single-Occupant Replacement Model), {p_out_name}'s Innings 1 points are permanently preserved in the locked ledger. "
                f"{p_in_name} replaces him as the active fantasy asset for Innings 2. Under this experimental rule, only {p_in_name}'s points count toward the active team score ({p_in_name}'s points replace {p_out_name}'s rather than summing together)."
            )
            audit = (
                f"Evaluated under Tier 4 Proposed Rule R-SUB-02 (Experimental). Enforces immutable ledger lock for Innings 1. "
                f"Applies SmartSub single-occupant scoring: active slot contribution reflects {p_in_name} only, preventing dual-point accumulation."
            )
            trade_offs = {
                "pros": [
                    f"Preserves {pts_locked:.1f} bowling points from {p_out_name} in historical audit ledger.",
                    f"Activates {p_in_name}'s death-overs batting capacity for Phase 2 scoring."
                ],
                "cons": [
                    f"Excludes {p_out_name}'s 1st innings points from active team total under single-occupant experimental rule."
                ],
                "net_point_impact": f"Replacement slot contribution is {p_in_name}'s active points (not summed with {p_out_name}'s {pts_locked:.1f} pts)."
            }
            counterfactual = {
                "without_impact_substitution": f"{p_out_name} would have remained in the active XI with negligible batting contribution as a lower-order bowler."
            }
        else:
            summary = f"[SIMULATED RATIONALE] Decision executed under rule {decision.rule_id}."
            rationale = f"Decision reason code: {decision.reason_code}."
            audit = f"Rule tier: {decision.rule_tier.value}."
            trade_offs = {"pros": [], "cons": [], "net_point_impact": "Neutral"}
            counterfactual = {}

        return AIExplanation(
            decision_id=decision.id,
            explanation_type="DETERMINISTIC_FALLBACK",
            model_name="fallback-template-v2",
            is_fallback=True,
            executive_summary=summary,
            tactical_rationale=rationale,
            rule_compliance_audit=audit,
            strategic_trade_offs=trade_offs,
            counterfactual_alternatives=counterfactual,
            data_provenance="ILLUSTRATIVE_SIMULATION"
        )
