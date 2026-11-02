import sys
sys.path.insert(0, r"c:\Dream11_artifact\backend")
from app.database import Base, sync_engine, SyncSessionLocal
from app.services.seed_data import seed_database
from app.services.match_simulator import MatchSimulator
from app.services.substitution_engine import SubstitutionEngine
from app.services.gemini_ai import GeminiAIService
from app.models.match import MatchEvent
from app.models.enums import RealMatchParticipation, FantasySelectionStatus, DecisionStatus

def run_verification():
    print("=== STARTING FULL END-TO-END FLOW VERIFICATION ===")
    Base.metadata.create_all(bind=sync_engine)
    db = SyncSessionLocal()
    
    # 1. Seed database
    match = seed_database(db)
    print(f"[OK] Database seeded: Match ID = {match.id}, Code = {match.match_code}")

    # 2. Reset match cleanly
    MatchSimulator.reset_match(db, match.id, "fantasy_team_demo")
    print("[OK] Match reset to pre-match state")

    # 3. Simulate Toss
    toss_res = MatchSimulator.conduct_toss(db, match.id)
    print(f"[OK] Toss simulated: Winner = {toss_res.toss_winner}, Decision = {toss_res.toss_decision}")

    # 4. Trigger Lineup Announcement (Scenario 1)
    lineup_res = MatchSimulator.announce_lineups(db, match.id, "fantasy_team_demo")
    sub1 = lineup_res["substitution_decision"]
    assert sub1 is not None, "Scenario 1 should generate a SubstitutionDecision"
    print(f"[OK] Scenario 1 Decision: Status={sub1.status.value}, Out={sub1.player_out_id}, In={sub1.player_in_id}, Reason={sub1.reason_code}")
    assert sub1.status == DecisionStatus.EXECUTED, f"Expected EXECUTED, got {sub1.status}"
    assert sub1.player_out_id == "p_csk_mustafizur", f"Expected Mustafizur out, got {sub1.player_out_id}"
    assert sub1.player_in_id == "p_csk_thakur", f"Expected Thakur in, got {sub1.player_in_id}"
    
    # Check evaluations audit
    audit = sub1.evaluations_audit
    print(f"[OK] Evaluations Audit entries: {len(audit)}")
    conway_audit = next((a for a in audit if a["player_id"] == "p_csk_conway"), None)
    thakur_audit = next((a for a in audit if a["player_id"] == "p_csk_thakur"), None)
    assert conway_audit["status"] == "SKIPPED", "Conway (B1) should be SKIPPED because DID_NOT_PLAY"
    assert thakur_audit["status"] == "ACCEPTED", "Thakur (B2) should be ACCEPTED"
    print(f"  -> Conway (B1): {conway_audit['status']} ({conway_audit['reason']})")
    print(f"  -> Thakur (B2): {thakur_audit['status']}")

    # 5. Explain Scenario 1 decision
    explanation = GeminiAIService.explain_decision(db, sub1.id)
    print(f"[OK] AI Explanation generated: Type={explanation.explanation_type}, Fallback={explanation.is_fallback}, Summary={explanation.executive_summary[:80]}...")

    # 6. Jump to 2nd Innings
    inn2_match = MatchSimulator.jump_to_second_innings(db, match.id, "fantasy_team_demo")
    print(f"[OK] Jumped to Innings 2: Status={inn2_match.status.value}, Current Innings={inn2_match.current_innings}")

    # 7. Trigger Impact Player Substitution (Scenario 2)
    impact_res = MatchSimulator.trigger_real_impact_player(
        db, match.id, "fantasy_team_demo",
        player_out_id="p_csk_thakur",
        player_in_id="p_csk_stoinis"
    )
    sub2 = impact_res["substitution_decision"]
    assert sub2 is not None, "Scenario 2 should generate a SubstitutionDecision"
    print(f"[OK] Scenario 2 Decision: Status={sub2.status.value}, Out={sub2.player_out_id}, In={sub2.player_in_id}, Reason={sub2.reason_code}")
    assert sub2.status == DecisionStatus.EXECUTED, f"Expected EXECUTED, got {sub2.status}"
    assert sub2.player_out_id == "p_csk_thakur", f"Expected Thakur out, got {sub2.player_out_id}"
    assert sub2.player_in_id == "p_csk_stoinis", f"Expected Stoinis in, got {sub2.player_in_id}"

    # 8. Replay Events
    events = db.query(MatchEvent).filter_by(match_id=match.id).order_by(MatchEvent.sequence_number.asc()).all()
    replay_snapshot = SubstitutionEngine.replay_all_events(db, "fantasy_team_demo", events)
    print(f"[OK] Event Replay: Events Replayed={len(events)}, Starters in Final Snapshot={len(replay_snapshot['selected_xi'])}")
    assert len(replay_snapshot['selected_xi']) == 11, "Expected 11 selected starters after replay"

    print("\n=== ALL VERIFICATION CHECKS PASSED PERFECTLY ===")
    db.close()

if __name__ == "__main__":
    run_verification()
