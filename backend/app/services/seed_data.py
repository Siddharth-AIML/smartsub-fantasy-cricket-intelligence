import uuid
from sqlalchemy.orm import Session
from app.models.enums import (
    PlayerRole,
    RealMatchParticipation,
    FantasySlotType,
    FantasySelectionStatus,
    MatchStatus,
    RuleTier
)
from app.models.player import Player, InningsScoringLedger
from app.models.match import Match, MatchSquad, MatchEvent
from app.models.fantasy_team import FantasyTeam, FantasyLineupSlot, SubstitutionRulesConfig

CSK_PLAYERS_RAW = [
    # Starters & Backups
    {"id": "p_csk_gaikwad", "full_name": "Ruturaj Gaikwad", "short_name": "R. Gaikwad", "team": "CSK", "role": PlayerRole.BAT, "credits": 9.5, "is_captain": True},
    {"id": "p_csk_dube", "full_name": "Shivam Dube", "short_name": "S. Dube", "team": "CSK", "role": PlayerRole.BAT, "credits": 8.5},
    {"id": "p_csk_rahane", "full_name": "Ajinkya Rahane", "short_name": "A. Rahane", "team": "CSK", "role": PlayerRole.BAT, "credits": 8.5},
    {"id": "p_csk_dhoni", "full_name": "MS Dhoni", "short_name": "MS Dhoni", "team": "CSK", "role": PlayerRole.WK, "credits": 8.5},
    {"id": "p_csk_jadeja", "full_name": "Ravindra Jadeja", "short_name": "R. Jadeja", "team": "CSK", "role": PlayerRole.AR, "credits": 9.0, "is_vc": True},
    {"id": "p_csk_moeen", "full_name": "Moeen Ali", "short_name": "M. Ali", "team": "CSK", "role": PlayerRole.AR, "credits": 8.5},
    {"id": "p_csk_chahar", "full_name": "Deepak Chahar", "short_name": "D. Chahar", "team": "CSK", "role": PlayerRole.BOWL, "credits": 8.0},
    {"id": "p_csk_pathirana", "full_name": "Matheesha Pathirana", "short_name": "M. Pathirana", "team": "CSK", "role": PlayerRole.BOWL, "credits": 8.5},
    {"id": "p_csk_deshpande", "full_name": "Tushar Deshpande", "short_name": "T. Deshpande", "team": "CSK", "role": PlayerRole.BOWL, "credits": 7.5},
    {"id": "p_csk_theekshana", "full_name": "Maheesh Theekshana", "short_name": "M. Theekshana", "team": "CSK", "role": PlayerRole.BOWL, "credits": 8.0},
    {"id": "p_csk_mustafizur", "full_name": "Mustafizur Rahman", "short_name": "M. Rahman", "team": "MI", "role": PlayerRole.BOWL, "credits": 8.0, "is_dnp_starter": True},

    # Backups
    {"id": "p_csk_conway", "full_name": "Devon Conway", "short_name": "D. Conway", "team": "CSK", "role": PlayerRole.WK, "credits": 8.5, "priority": 1, "priority_label": "B1"},
    {"id": "p_csk_thakur", "full_name": "Shardul Thakur", "short_name": "S. Thakur", "team": "CSK", "role": PlayerRole.BOWL, "credits": 8.0, "priority": 2, "priority_label": "B2"},
    {"id": "p_csk_stoinis", "full_name": "Marcus Stoinis", "short_name": "M. Stoinis", "team": "MI", "role": PlayerRole.AR, "credits": 8.5, "priority": 3, "priority_label": "B3"},
    {"id": "p_csk_rizvi", "full_name": "Sameer Rizvi", "short_name": "S. Rizvi", "team": "CSK", "role": PlayerRole.BAT, "credits": 7.5, "priority": 4, "priority_label": "B4"},
]

MI_PLAYERS_RAW = [
    {"id": "p_mi_rohit", "full_name": "Rohit Sharma", "short_name": "R. Sharma", "team": "MI", "role": PlayerRole.BAT, "credits": 9.5},
    {"id": "p_mi_kishan", "full_name": "Ishan Kishan", "short_name": "I. Kishan", "team": "MI", "role": PlayerRole.WK, "credits": 8.5},
    {"id": "p_mi_sky", "full_name": "Suryakumar Yadav", "short_name": "S. Yadav", "team": "MI", "role": PlayerRole.BAT, "credits": 9.5},
    {"id": "p_mi_tilak", "full_name": "Tilak Varma", "short_name": "T. Varma", "team": "MI", "role": PlayerRole.BAT, "credits": 8.5},
    {"id": "p_mi_hardik", "full_name": "Hardik Pandya", "short_name": "H. Pandya", "team": "MI", "role": PlayerRole.AR, "credits": 9.0},
    {"id": "p_mi_david", "full_name": "Tim David", "short_name": "T. David", "team": "MI", "role": PlayerRole.BAT, "credits": 8.0},
    {"id": "p_mi_bumrah", "full_name": "Jasprit Bumrah", "short_name": "J. Bumrah", "team": "MI", "role": PlayerRole.BOWL, "credits": 9.5},
    {"id": "p_mi_coetzee", "full_name": "Gerald Coetzee", "short_name": "G. Coetzee", "team": "MI", "role": PlayerRole.BOWL, "credits": 8.0},
    {"id": "p_mi_chawla", "full_name": "Piyush Chawla", "short_name": "P. Chawla", "team": "MI", "role": PlayerRole.BOWL, "credits": 7.5},
    {"id": "p_mi_thushara", "full_name": "Nuwan Thushara", "short_name": "N. Thushara", "team": "MI", "role": PlayerRole.BOWL, "credits": 7.5},
    {"id": "p_mi_madhwal", "full_name": "Akash Madhwal", "short_name": "A. Madhwal", "team": "MI", "role": PlayerRole.BOWL, "credits": 7.5},
]

FANTASY_ROSTER_RAW = [
    # 11 Starters: 10 CSK + 1 MI (Strict compliance with Dream11 Max 10 per team and 100-credit cap)
    {"id": "p_csk_gaikwad", "is_starter": True},
    {"id": "p_csk_dube", "is_starter": True},
    {"id": "p_csk_rahane", "is_starter": True},
    {"id": "p_csk_dhoni", "is_starter": True},
    {"id": "p_csk_jadeja", "is_starter": True},
    {"id": "p_csk_moeen", "is_starter": True},
    {"id": "p_csk_chahar", "is_starter": True},
    {"id": "p_csk_pathirana", "is_starter": True},
    {"id": "p_csk_deshpande", "is_starter": True},
    {"id": "p_csk_mustafizur", "is_starter": True},
    {"id": "p_mi_bumrah", "is_starter": True},

    # 4 Backups (Strictly Unique)
    {"id": "p_csk_conway", "is_starter": False, "priority": 1, "priority_label": "B1"},
    {"id": "p_csk_thakur", "is_starter": False, "priority": 2, "priority_label": "B2"},
    {"id": "p_csk_stoinis", "is_starter": False, "priority": 3, "priority_label": "B3"},
    {"id": "p_csk_rizvi", "is_starter": False, "priority": 4, "priority_label": "B4"},
]

def seed_database(db: Session):
    # Check if match already exists
    existing_match = db.query(Match).filter_by(match_code="IPL_2026_CSK_MI").first()
    if existing_match:
        return existing_match

    # 1. Create Players
    player_objects = {}
    for p_data in CSK_PLAYERS_RAW + MI_PLAYERS_RAW:
        player = Player(
            id=p_data["id"],
            full_name=p_data["full_name"],
            short_name=p_data["short_name"],
            team=p_data["team"],
            role=p_data["role"],
            credits=p_data["credits"],
            is_impact_eligible=True,
            real_match_participation=RealMatchParticipation.NOT_STARTED,
            stats={"runs": 0, "wickets": 0, "overs": 0.0, "maidens": 0, "catches": 0},
            data_provenance="ILLUSTRATIVE_SIMULATION",
            is_independently_verified=False
        )
        db.add(player)
        player_objects[p_data["id"]] = player
    db.flush()

    # 2. Create Match
    match = Match(
        id="match_csk_mi_2026",
        match_code="IPL_2026_CSK_MI",
        home_team="CSK",
        away_team="MI",
        venue="Wankhede Stadium, Mumbai",
        status=MatchStatus.UPCOMING,
        toss_winner=None,
        toss_decision=None,
        current_innings=1,
        current_over=0,
        current_ball=0,
        scoreboard={
            "innings_1": {"batting_team": "MI", "runs": 0, "wickets": 0, "overs": 0.0, "extras": 0},
            "innings_2": {"batting_team": "CSK", "runs": 0, "wickets": 0, "overs": 0.0, "target": 183, "required_runs": 183},
            "current_batsmen": [],
            "current_bowler": None,
            "phase": "PRE_MATCH"
        },
        data_provenance="ILLUSTRATIVE_SIMULATION"
    )
    db.add(match)
    db.flush()

    # 3. Create Match Squads
    for p_id in [p["id"] for p in CSK_PLAYERS_RAW]:
        is_sub = 1 if p_id in ["p_csk_conway", "p_csk_thakur", "p_csk_stoinis", "p_csk_rizvi"] else 0
        squad_entry = MatchSquad(
            match_id=match.id,
            player_id=p_id,
            team="CSK",
            is_announced_xi=0,
            is_impact_candidate=1 if is_sub else 0,
            is_substitute=is_sub
        )
        db.add(squad_entry)

    for p_id in [p["id"] for p in MI_PLAYERS_RAW]:
        squad_entry = MatchSquad(
            match_id=match.id,
            player_id=p_id,
            team="MI",
            is_announced_xi=0,
            is_impact_candidate=1,
            is_substitute=0
        )
        db.add(squad_entry)
    db.flush()

    # 4. Create Fantasy Team (11 Starters + 4 Backups)
    fantasy_team = FantasyTeam(
        id="fantasy_team_demo",
        match_id=match.id,
        user_id="demo_user",
        team_name="SmartSub Tactical XI",
        captain_player_id="p_csk_gaikwad",
        vice_captain_player_id="p_csk_jadeja",
        rule_mode=RuleTier.TIER_4_PROPOSED_EXPERIMENTAL,
        total_points=0.0
    )
    db.add(fantasy_team)
    db.flush()

    # Add Slots
    for p_slot in FANTASY_ROSTER_RAW:
        is_starter = p_slot["is_starter"]
        slot = FantasyLineupSlot(
            fantasy_team_id=fantasy_team.id,
            player_id=p_slot["id"],
            slot_type=FantasySlotType.STARTER if is_starter else FantasySlotType.BACKUP,
            priority_rank=p_slot.get("priority", None),
            priority_label=p_slot.get("priority_label", None),
            fantasy_selection_status=FantasySelectionStatus.SELECTED if is_starter else FantasySelectionStatus.NOT_SELECTED,
            entry_innings=1 if is_starter else None,
            exit_innings=None
        )
        db.add(slot)

    # Add Rules Config
    rules_cfg = SubstitutionRulesConfig(
        fantasy_team_id=fantasy_team.id,
        scenario_1_enabled=True,
        scenario_2_enabled=True,
        inherit_captaincy_on_substitution=False,
        parameters={
            "scenario_1_description": "Evaluate B2 when B1 is DNP",
            "scenario_2_description": "2nd Innings Impact player swap with immutable ledger"
        }
    )
    db.add(rules_cfg)

    # Initial Pre-Match Event
    init_event = MatchEvent(
        match_id=match.id,
        sequence_number=1,
        idempotency_key="EVT_CSK_MI_INIT_001",
        event_type="MATCH_INITIALIZED",
        innings=1,
        over=0,
        ball=0,
        payload={"message": "Match initialized in pre-match state"}
    )
    db.add(init_event)

    db.commit()
    return match
