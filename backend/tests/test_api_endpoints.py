import pytest
from app.main import health_check
from app.routers.rules import list_rule_evidence
from app.routers.matches import list_matches
from app.routers.fantasy_teams import get_fantasy_team

def test_health_endpoint():
    data = health_check()
    assert data["status"] == "healthy"
    assert "SmartSub" in data["app"]

def test_rules_evidence_register():
    data = list_rule_evidence()
    assert "rules" in data
    assert len(data["rules"]) >= 5
    rule_ids = [r["rule_id"] for r in data["rules"]]
    assert "R-D11-01" in rule_ids
    assert "R-SUB-01" in rule_ids
    assert "R-SUB-02" in rule_ids

def test_matches_endpoint():
    matches = list_matches()
    assert len(matches) >= 1
    assert matches[0].match_code == "IPL_2026_CSK_MI"

def test_fantasy_team_endpoint():
    team = get_fantasy_team("fantasy_team_demo")
    assert team is not None
    assert len(team.lineup_slots) == 15
    starters = [s for s in team.lineup_slots if s.slot_type == "STARTER"]
    bench = [s for s in team.lineup_slots if s.slot_type == "BACKUP"]
    assert len(starters) == 11
    assert len(bench) == 4
