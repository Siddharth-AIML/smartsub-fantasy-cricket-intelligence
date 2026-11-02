from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from app.database import SyncSessionLocal
from app.schemas.api_schemas import AIExplanationResponse
from app.services.gemini_ai import GeminiAIService

router = APIRouter(prefix="/api/ai", tags=["AI Intelligence"])

@router.post("/explain/{decision_id}", response_model=AIExplanationResponse)
def get_ai_explanation(decision_id: str):
    db = SyncSessionLocal()
    try:
        explanation = GeminiAIService.explain_decision(db, decision_id)
        return explanation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate explanation: {e}")
    finally:
        db.close()
