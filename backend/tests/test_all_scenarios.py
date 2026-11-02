import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.enums import (
    PlayerRole,
    RealMatchParticipation,
    FantasySlotType,
    FantasySelectionStatus,
    MatchStatus,
    RuleTier,
    DecisionStatus
)
from app.models.player import Player, InningsScoringLedger
from app.models.match import Match, MatchEvent, ProcessedEvent
from app.models.fantasy_team import FantasyTeam, FantasyLineupSlot, SubstitutionRulesConfig
from app.models.substitution import SubstitutionDecision
from app.services.validators import (
    PreMatchTeamCreationValidator,
    OfficialPlatformConstraintValidator,
    ExperimentalInMatchValidator
)
from app.services.substitution_engine import SubstitutionEngine

# Setup isolated in-memory test database fixture
@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

# Helper to build a standard 15-player squad (10 CSK, 1 MI to satisfy <=10 team balance rule)
def create_test_roster(test_db):
    players = []
    # 11 Starters (Player 0 from MI, Players 1-10 from CSK -> total 10 CSK, 1 MI)
    roles = [PlayerRole.WK, PlayerRole.BAT, PlayerRole.BAT, PlayerRole.BAT,
             PlayerRole.AR, PlayerRole.AR, PlayerRole.BOWL, PlayerRole.BOWL,
             PlayerRole.BOWL, PlayerRole.BOWL, PlayerRole.BOWL]
    
    for i in range(11):
        team_name = "MI" if i == 0 else "CSK"
        p = Player(
            id=f"p_starter_{i}",
            full_name=f"Starter Player {i}",
            short_name=f"Starter {i}",
            team=team_name,
            role=roles[i],
            credits=8.5,
            real_match_participation=RealMatchParticipation.PLAYING_XI
        )
        test_db.add(p)
        players.append(p)

    # 4 Backups
    p_b1 = Player(id="p_b1", full_name="Backup One", short_name="B1 Player", team="CSK", role=PlayerRole.WK, credits=9.0, real_match_participation=RealMatchParticipation.DID_NOT_PLAY)
    p_b2 = Player(id="p_b2", full_name="Backup Two", short_name="B2 Player", team="CSK", role=PlayerRole.BOWL, credits=8.5, real_match_participation=RealMatchParticipation.PLAYING_XI)
    p_b3 = Player(id="p_b3", full_name="Backup Three", short_name="B3 Player", team="CSK", role=PlayerRole.AR, credits=8.5, real_match_participation=RealMatchParticipation.BENCH_SUBSTITUTE)
    p_b4 = Player(id="p_b4", full_name="Backup Four", short_name="B4 Player", team="CSK", role=PlayerRole.BAT, credits=7.5, real_match_participation=RealMatchParticipation.BENCH_SUBSTITUTE)
    
    test_db.add_all([p_b1, p_b2, p_b3, p_b4])
    players.extend([p_b1, p_b2, p_b3, p_b4])

    match = Match(id="m1", match_code="IPL_TEST", home_team="CSK", away_team="MI", current_innings=1)
    test_db.add(match)

    team = FantasyTeam(id="team1", match_id="m1", team_name="Test XI", rule_mode=RuleTier.TIER_4_PROPOSED_EXPERIMENTAL)
    test_db.add(team)

    # Add 11 starter slots
    for i in range(11):
        slot = FantasyLineupSlot(
            fantasy_team_id=team.id,
            player_id=f"p_starter_{i}",
            slot_type=FantasySlotType.STARTER,
            fantasy_selection_status=FantasySelectionStatus.SELECTED,
            entry_innings=1
        )
        test_db.add(slot)

    # Add 4 backup slots
    bench_data = [
        ("p_b1", 1, "B1"),
        ("p_b2", 2, "B2"),
        ("p_b3", 3, "B3"),
        ("p_b4", 4, "B4")
    ]
    for pid, rank, label in bench_data:
        slot = FantasyLineupSlot(
            fantasy_team_id=team.id,
            player_id=pid,
            slot_type=FantasySlotType.BACKUP,
            priority_rank=rank,
            priority_label=label,
            fantasy_selection_status=FantasySelectionStatus.NOT_SELECTED
        )
        test_db.add(slot)

    rules_cfg = SubstitutionRulesConfig(
        fantasy_team_id=team.id,
        scenario_1_enabled=True,
        scenario_2_enabled=True,
        inherit_captaincy_on_substitution=False
    )
    test_db.add(rules_cfg)
    test_db.commit()
    return team, match


# 1. Test Scenario 1: B2 replaces DNP starter when B1 is DNP
def test_scenario_1_b2_replaces_dnp_starter_when_b1_dnp(test_db):
    team, match = create_test_roster(test_db)

    # Make Starter 10 DNP in the real match
    starter_10 = test_db.query(Player).filter_by(id="p_starter_10").first()
    starter_10.real_match_participation = RealMatchParticipation.DID_NOT_PLAY
    test_db.commit()

    event = MatchEvent(
        match_id=match.id,
        sequence_number=1,
        idempotency_key="EVT_LINEUP_TEST_01",
        event_type="OFFICIAL_LINEUPS_ANNOUNCED",
        innings=1,
        over=0,
        ball=0
    )
    test_db.add(event)
    test_db.commit()

    decision = SubstitutionEngine.process_match_event(test_db, team.id, event)

    assert decision is not None
    assert decision.status == DecisionStatus.EXECUTED
    assert decision.reason_code == "SCENARIO_1_B2_SUBSTITUTED_WHEN_B1_DNP"
    assert decision.player_out_id == "p_starter_10"
    assert decision.player_in_id == "p_b2"  # B2 replaced Starter 10!
    assert decision.priority_rank_used == 2

    # Verify B1 was skipped in audit log
    b1_skipped = any(a.get("player_id") == "p_b1" and a.get("status") == "SKIPPED" for a in decision.evaluations_audit)
    assert b1_skipped, "B1 must be recorded as SKIPPED in evaluations_audit"

    # Verify B2 is now SELECTED
    b2_slot = test_db.query(FantasyLineupSlot).filter_by(player_id="p_b2", fantasy_team_id=team.id).first()
    assert b2_slot.fantasy_selection_status == FantasySelectionStatus.SELECTED


# 2. Test Scenario 1: B2 rejected when violating credit limit
def test_scenario_1_b2_rejected_when_violating_credit_limit(test_db):
    team, match = create_test_roster(test_db)

    # Make Starter 10 DNP
    starter_10 = test_db.query(Player).filter_by(id="p_starter_10").first()
    starter_10.real_match_participation = RealMatchParticipation.DID_NOT_PLAY

    # Make B2 very expensive (16.0 credits) such that projected credits exceed 100.0
    p_b2 = test_db.query(Player).filter_by(id="p_b2").first()
    p_b2.credits = 16.0

    # Make B3 eligible and active in Playing XI
    p_b3 = test_db.query(Player).filter_by(id="p_b3").first()
    p_b3.real_match_participation = RealMatchParticipation.PLAYING_XI
    p_b3.credits = 8.0
    test_db.commit()

    event = MatchEvent(
        match_id=match.id,
        sequence_number=1,
        idempotency_key="EVT_LINEUP_TEST_CREDIT_BREACH",
        event_type="OFFICIAL_LINEUPS_ANNOUNCED",
        innings=1
    )
    test_db.add(event)
    test_db.commit()

    decision = SubstitutionEngine.process_match_event(test_db, team.id, event)

    assert decision is not None
    assert decision.status == DecisionStatus.EXECUTED
    # B2 should be rejected due to credits, so engine proceeds to B3!
    assert decision.player_in_id == "p_b3"
    assert decision.priority_rank_used == 3

    b2_rejected = any(a.get("player_id") == "p_b2" and a.get("status") == "REJECTED_CONSTRAINTS" for a in decision.evaluations_audit)
    assert b2_rejected, "B2 should be rejected in constraint audit"


# 3. Test Fantasy Roster Unique 15 Players Prevention
def test_fantasy_roster_unique_15_players_prevention(test_db):
    p1 = Player(id="p1", full_name="Player 1", short_name="P1", team="CSK", role=PlayerRole.BAT, credits=8.5)
    test_db.add(p1)
    test_db.commit()

    # Attempt squad with duplicate player
    starters = [p1] * 11
    backups = [p1] * 4

    is_valid, err_msg, _ = PreMatchTeamCreationValidator.validate_squad(starters, backups)
    assert not is_valid
    assert "DUPLICATE_ROSTER_PLAYER_ERROR" in err_msg


# 4. Test Player Participating in Both Innings Scoring
def test_player_participating_in_both_innings_scoring(test_db):
    team, match = create_test_roster(test_db)

    # Add Innings 1 scoring ledger for Starter 0
    l1 = InningsScoringLedger(
        fantasy_team_id=team.id,
        player_id="p_starter_0",
        match_id=match.id,
        innings=1,
        runs_scored=30,
        base_fantasy_points=30.0,
        total_fantasy_points=30.0,
        is_locked=True,
        idempotency_key="IDEMP_L1_STARTER0"
    )
    # Add Innings 2 scoring ledger for Starter 0
    l2 = InningsScoringLedger(
        fantasy_team_id=team.id,
        player_id="p_starter_0",
        match_id=match.id,
        innings=2,
        runs_scored=25,
        base_fantasy_points=25.0,
        total_fantasy_points=25.0,
        is_locked=False,
        idempotency_key="IDEMP_L2_STARTER0"
    )
    test_db.add_all([l1, l2])
    test_db.commit()

    total_player_pts = sum(
        l.total_fantasy_points for l in test_db.query(InningsScoringLedger).filter_by(player_id="p_starter_0").all()
    )
    assert total_player_pts == 55.0


# 5. Test Scenario 2: Preserves Outgoing Player's Bat, Bowl, and Field Points
def test_scenario_2_preserves_outgoing_player_bat_bowl_field_points(test_db):
    team, match = create_test_roster(test_db)

    # Replace Starter 10 with B2 for Innings 1 so total active starters = 11
    s10_slot = test_db.query(FantasyLineupSlot).filter_by(player_id="p_starter_10", fantasy_team_id=team.id).first()
    s10_slot.fantasy_selection_status = FantasySelectionStatus.SUBSTITUTED_OUT

    b2_slot = test_db.query(FantasyLineupSlot).filter_by(player_id="p_b2", fantasy_team_id=team.id).first()
    b2_slot.fantasy_selection_status = FantasySelectionStatus.SELECTED
    b2_slot.entry_innings = 1

    inn1_ledger = InningsScoringLedger(
        fantasy_team_id=team.id,
        player_id="p_b2",
        match_id=match.id,
        innings=1,
        wickets_taken=1,
        catches=1,
        runs_scored=10,
        base_fantasy_points=43.0,
        total_fantasy_points=43.0,
        is_locked=False,
        idempotency_key="IDEMP_INN1_B2_POINTS"
    )
    test_db.add(inn1_ledger)
    test_db.commit()

    # Trigger Scenario 2 in Innings 2: Marcus Stoinis (p_b3) replaces Shardul Thakur (p_b2)
    impact_event = MatchEvent(
        match_id=match.id,
        sequence_number=2,
        idempotency_key="EVT_IMPACT_INN2_TEST",
        event_type="IMPACT_PLAYER_DECLARED",
        innings=2,
        over=0,
        ball=0,
        payload={"player_out_id": "p_b2", "player_in_id": "p_b3"}
    )
    test_db.add(impact_event)
    test_db.commit()

    decision = SubstitutionEngine.process_match_event(test_db, team.id, impact_event)

    assert decision is not None
    assert decision.status == DecisionStatus.EXECUTED
    assert decision.reason_code == "SCENARIO_2_IMPACT_SUB_INN2_EXECUTED"

    # Verify B2's Innings 1 ledger is locked and intact with 43.0 points!
    b2_ledger_after = test_db.query(InningsScoringLedger).filter_by(player_id="p_b2", innings=1).first()
    assert b2_ledger_after.is_locked is True
    assert b2_ledger_after.total_fantasy_points == 43.0

    # Verify B3 has a fresh Innings 2 ledger initialized
    b3_ledger = test_db.query(InningsScoringLedger).filter_by(player_id="p_b3", innings=2).first()
    assert b3_ledger is not None
    assert b3_ledger.is_locked is False


# 6. Test Captain & Vice-Captain Multiplier Behavior on Substitution
def test_captain_vice_captain_multiplier_behavior_on_substitution(test_db):
    team, match = create_test_roster(test_db)

    # Set Starter 1 as Captain (2x multiplier)
    team.captain_player_id = "p_starter_1"
    
    # Starter 1 earns 20 base points in Innings 1 as Captain (20 * 2 = 40 pts)
    c_ledger = InningsScoringLedger(
        fantasy_team_id=team.id,
        player_id="p_starter_1",
        match_id=match.id,
        innings=1,
        base_fantasy_points=20.0,
        multiplier=2.0,
        total_fantasy_points=40.0,
        is_locked=False,
        idempotency_key="IDEMP_CAPTAIN_INN1"
    )
    test_db.add(c_ledger)
    test_db.commit()

    # Trigger Impact substitution of Captain in Innings 2
    impact_event = MatchEvent(
        match_id=match.id,
        sequence_number=3,
        idempotency_key="EVT_IMPACT_CAPTAIN_OUT",
        event_type="IMPACT_PLAYER_DECLARED",
        innings=2,
        over=0,
        ball=0,
        payload={"player_out_id": "p_starter_1", "player_in_id": "p_b3"}
    )
    test_db.add(impact_event)
    test_db.commit()

    decision = SubstitutionEngine.process_match_event(test_db, team.id, impact_event)
    assert decision.status == DecisionStatus.EXECUTED

    # Under entity-bound multiplier policy, incoming player p_b3 gets 1.0x (standard rate)
    b3_ledger = test_db.query(InningsScoringLedger).filter_by(player_id="p_b3", innings=2).first()
    assert b3_ledger.multiplier == 1.0

    # Captain's Innings 1 points remain locked at 40.0
    c_ledger_after = test_db.query(InningsScoringLedger).filter_by(player_id="p_starter_1", innings=1).first()
    assert c_ledger_after.is_locked is True
    assert c_ledger_after.total_fantasy_points == 40.0


# 7. Test Duplicate and Out-of-Order Impact Player Events
def test_duplicate_and_out_of_order_impact_player_events(test_db):
    team, match = create_test_roster(test_db)

    # Replace Starter 10 with B2 for Innings 1
    s10_slot = test_db.query(FantasyLineupSlot).filter_by(player_id="p_starter_10", fantasy_team_id=team.id).first()
    s10_slot.fantasy_selection_status = FantasySelectionStatus.SUBSTITUTED_OUT

    b2_slot = test_db.query(FantasyLineupSlot).filter_by(player_id="p_b2", fantasy_team_id=team.id).first()
    b2_slot.fantasy_selection_status = FantasySelectionStatus.SELECTED

    event1 = MatchEvent(
        match_id=match.id,
        sequence_number=10,
        idempotency_key="IDEMP_DUP_TEST_001",
        event_type="IMPACT_PLAYER_DECLARED",
        innings=2,
        over=0,
        ball=0,
        payload={"player_out_id": "p_b2", "player_in_id": "p_b3"}
    )
    test_db.add(event1)
    test_db.commit()

    # Process first time -> Executed
    d1 = SubstitutionEngine.process_match_event(test_db, team.id, event1)
    assert d1.status == DecisionStatus.EXECUTED

    # Process DUPLICATE event with same idempotency key -> returns existing decision, no duplicate rows
    d2 = SubstitutionEngine.process_match_event(test_db, team.id, event1)
    assert d2.id == d1.id

    decisions_count = test_db.query(SubstitutionDecision).filter_by(fantasy_team_id=team.id).count()
    assert decisions_count == 1, "Duplicate event must not create duplicate decision entries"

    # Process OUT-OF-ORDER event (sequence_number 5 < 10)
    event_stale = MatchEvent(
        match_id=match.id,
        sequence_number=5,
        idempotency_key="IDEMP_STALE_005",
        event_type="IMPACT_PLAYER_DECLARED",
        innings=2,
        over=0,
        ball=0,
        payload={"player_out_id": "p_b2", "player_in_id": "p_b4"}
    )
    test_db.add(event_stale)
    test_db.commit()

    d_stale = SubstitutionEngine.process_match_event(test_db, team.id, event_stale)
    assert d_stale.reason_code == "OUT_OF_ORDER_EVENT_REJECTED"


# 8. Test Deterministic Event Replay After Multiple Substitutions
def test_deterministic_event_replay_after_multiple_substitutions(test_db):
    team, match = create_test_roster(test_db)

    # Event 1: Lineup announcement (Starter 10 DNP -> replaced by B2)
    s10 = test_db.query(Player).filter_by(id="p_starter_10").first()
    s10.real_match_participation = RealMatchParticipation.DID_NOT_PLAY

    evt1 = MatchEvent(
        match_id=match.id,
        sequence_number=1,
        idempotency_key="REPLAY_EVT_1",
        event_type="OFFICIAL_LINEUPS_ANNOUNCED",
        innings=1
    )
    # Event 2: Impact player swap in Innings 2 (B2 -> B3)
    evt2 = MatchEvent(
        match_id=match.id,
        sequence_number=2,
        idempotency_key="REPLAY_EVT_2",
        event_type="IMPACT_PLAYER_DECLARED",
        innings=2,
        payload={"player_out_id": "p_b2", "player_in_id": "p_b3"}
    )
    test_db.add_all([evt1, evt2])
    test_db.commit()

    # Run through substitution pipeline
    SubstitutionEngine.process_match_event(test_db, team.id, evt1)
    SubstitutionEngine.process_match_event(test_db, team.id, evt2)

    initial_snapshot = SubstitutionEngine.capture_team_snapshot(test_db, team.id)

    # Now perform deterministic replay
    events = [evt1, evt2]
    replayed_snapshot = SubstitutionEngine.replay_all_events(test_db, team.id, events)

    # Assert 100% identical final state
    assert len(initial_snapshot["selected_xi"]) == len(replayed_snapshot["selected_xi"])
    assert len(initial_snapshot["bench"]) == len(replayed_snapshot["bench"])

    init_selected_ids = sorted([p["player_id"] for p in initial_snapshot["selected_xi"]])
    replayed_selected_ids = sorted([p["player_id"] for p in replayed_snapshot["selected_xi"]])
    assert init_selected_ids == replayed_selected_ids, "Replayed lineup must identically match initial run"
