from fastapi import APIRouter
from app.services.rule_evidence_register import get_rule_evidence_register

router = APIRouter(prefix="/rules", tags=["Rules Evidence"])

@router.get("/evidence-register")
def list_rule_evidence():
    return {
        "rules": get_rule_evidence_register(),
        "data_provenance": "AUTHORITATIVE_PLATFORM_DOCUMENTATION",
        "last_audit_date": "2026-11-02"
    }
