import random
from typing import Dict, Any, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.models.enums import MatchStatus, RealMatchParticipation, FantasySlotType, FantasySelectionStatus, DecisionStatus, RuleTier
from app.models.match import Match, MatchEvent, ProcessedEvent
from app.models.player import Player, InningsScoringLedger
from app.models.fantasy_team import FantasyTeam, FantasyLineupSlot
from app.models.substitution import SubstitutionDecision
from app.models.ai_explanation import AIExplanation
from app.services.substitution_engine import SubstitutionEngine
from app.services.gemini_ai import GeminiAIService

class MatchSimulator:

    @classmethod
    def _next_sequence_number(cls, db: Session, match_id: str) -> int:
        max_seq = db.query(func.max(MatchEvent.sequence_number)).filter_by(match_id=match_id).scalar()
        return (max_seq or 0) + 1

    @classmethod
    def recompute_active_points(cls, db: Session, fantasy_team_id: str) -> Dict[str, Any]:
        """
        Calculates active fantasy points strictly honoring the SmartSub single-occupant experimental rule.
        - Historical event record: All ledgers are preserved in the database.
        - Active fantasy points: Only currently SELECTED players' eligible innings count.
          If a player was substituted OUT (e.g. Shardul Thakur replaced by Stoinis),
          their historical points (43.0) remain locked in the ledger but are EXCLUDED from the active total.
          The incoming player's contribution (e.g. Stoinis 32.0) counts instead.
          Replacement slot active contribution = 32.0, NOT 75.0.
        - Also calculates individual player points map and writes fantasy_points directly to lineup slots.
        """
        team = db.query(FantasyTeam).filter_by(id=fantasy_team_id).first()
        if not team:
            return {"active_total_points": 0.0, "historical_locked_points": 0.0, "player_points_map": {}}

        all_slots = db.query(FantasyLineupSlot).filter_by(fantasy_team_id=fantasy_team_id).all()
        selected_slots = [s for s in all_slots if s.fantasy_selection_status == FantasySelectionStatus.SELECTED]
        active_slot_map = {s.player_id: s for s in selected_slots}

        all_ledgers = db.query(InningsScoringLedger).filter_by(fantasy_team_id=fantasy_team_id).all()

        active_points = 0.0
        historical_locked_points = 0.0
        player_points_map = {}

        for slot in all_slots:
            p_ledgers = [l for l in all_ledgers if l.player_id == slot.player_id]
            total_earned = sum(l.total_fantasy_points for l in p_ledgers)

            if slot.fantasy_selection_status == FantasySelectionStatus.SELECTED:
                eligible = [l for l in p_ledgers if not (slot.entry_innings and l.innings < slot.entry_innings)]
                act_pts = sum(l.total_fantasy_points for l in eligible)
                hist_pts = total_earned - act_pts
            else:
                act_pts = 0.0
                hist_pts = total_earned

            slot.fantasy_points = round(total_earned, 1)
            slot.active_fantasy_points = round(act_pts, 1)

            player_points_map[slot.player_id] = {
                "player_id": slot.player_id,
                "full_name": slot.player.full_name if slot.player else "",
                "short_name": slot.player.short_name if slot.player else "",
                "team": slot.player.team if slot.player else "CSK",
                "role": slot.player.role.value if slot.player else "BOWL",
                "total_points": round(total_earned, 1),
                "active_points": round(act_pts, 1),
                "historical_points": round(hist_pts, 1),
                "is_selected": slot.fantasy_selection_status == FantasySelectionStatus.SELECTED
            }

        for l in all_ledgers:
            slot = active_slot_map.get(l.player_id)
            if slot is not None:
                if slot.entry_innings and l.innings < slot.entry_innings:
                    historical_locked_points += l.total_fantasy_points
                else:
                    active_points += l.total_fantasy_points
            else:
                # Only count historical points for players who actually belonged to the fantasy team (e.g. substituted out players)
                team_slot = next((s for s in all_slots if s.player_id == l.player_id), None)
                if team_slot is not None:
                    historical_locked_points += l.total_fantasy_points

        team.total_points = round(active_points, 1)
        db.commit()

        # Audit information for replacement slot
        replaced_slot = db.query(FantasyLineupSlot).filter_by(
            fantasy_team_id=fantasy_team_id,
            fantasy_selection_status=FantasySelectionStatus.SELECTED
        ).filter(FantasyLineupSlot.substituted_in_for_player_id.isnot(None)).first()

        replacement_audit = None
        if replaced_slot:
            in_player = replaced_slot.player
            out_player = db.query(Player).filter_by(id=replaced_slot.substituted_in_for_player_id).first()
            in_ledger = db.query(InningsScoringLedger).filter_by(
                fantasy_team_id=fantasy_team_id,
                player_id=in_player.id,
                innings=replaced_slot.entry_innings or 2
            ).first()
            out_ledger = db.query(InningsScoringLedger).filter_by(
                fantasy_team_id=fantasy_team_id,
                player_id=out_player.id if out_player else "",
                innings=1
            ).first()

            replacement_audit = {
                "active_player_in_id": in_player.id,
                "active_player_in_name": in_player.short_name,
                "active_player_in_team": in_player.team,
                "active_player_in_points": in_ledger.total_fantasy_points if in_ledger else 0.0,
                "replaced_player_out_id": out_player.id if out_player else None,
                "replaced_player_out_name": out_player.short_name if out_player else None,
                "replaced_player_out_team": out_player.team if out_player else "CSK",
                "replaced_player_historical_points": out_ledger.total_fantasy_points if out_ledger else 0.0,
                "active_slot_contribution": in_ledger.total_fantasy_points if in_ledger else 0.0,
                "rule_type": "EXPERIMENTAL_SINGLE_OCCUPANT_REPLACEMENT",
                "explanation": f"Under SmartSub experimental single-occupant scoring, {in_player.short_name} ({in_player.team}) contributes {in_ledger.total_fantasy_points if in_ledger else 0.0:.1f} active pts. {out_player.short_name if out_player else 'Previous player'} ({out_player.team if out_player else 'CSK'}) 1st innings points ({out_ledger.total_fantasy_points if out_ledger else 0.0:.1f}) are preserved in the locked ledger but excluded from the active team total."
            }

        return {
            "active_total_points": round(active_points, 1),
            "historical_locked_points": round(historical_locked_points, 1),
            "player_points_map": player_points_map,
            "replacement_slot_audit": replacement_audit
        }

    @classmethod
    def build_canonical_scorecard(cls, match: Match, db: Session) -> Dict[str, Any]:
        """
        Builds the comprehensive cricket match centre scorecard with granular batting and bowling stats,
        strike rates, economy rates, dismissal details, and franchise team identifications (CSK vs MI).
        """
        innings_1_batting = [
            {"player_id": "p_mi_rohit", "name": "Rohit Sharma", "team": "MI", "dismissal": "c Dhoni b Chahar", "runs": 38, "balls": 24, "fours": 4, "sixes": 2, "strike_rate": 158.33, "is_out": True},
            {"player_id": "p_mi_kishan", "name": "Ishan Kishan", "team": "MI", "dismissal": "c & b Jadeja", "runs": 28, "balls": 19, "fours": 3, "sixes": 1, "strike_rate": 147.37, "is_out": True},
            {"player_id": "p_mi_sky", "name": "Suryakumar Yadav", "team": "MI", "dismissal": "c Gaikwad b Pathirana", "runs": 45, "balls": 27, "fours": 5, "sixes": 2, "strike_rate": 166.67, "is_out": True},
            {"player_id": "p_mi_tilak", "name": "Tilak Varma", "team": "MI", "dismissal": "c Rahane b Thakur", "runs": 31, "balls": 22, "fours": 2, "sixes": 1, "strike_rate": 140.91, "is_out": True},
            {"player_id": "p_mi_hardik", "name": "Hardik Pandya", "team": "MI", "dismissal": "b Pathirana", "runs": 18, "balls": 13, "fours": 1, "sixes": 1, "strike_rate": 138.46, "is_out": True},
            {"player_id": "p_mi_david", "name": "Tim David", "team": "MI", "dismissal": "not out", "runs": 14, "balls": 10, "fours": 1, "sixes": 1, "strike_rate": 140.00, "is_out": False},
            {"player_id": "p_mi_coetzee", "name": "Gerald Coetzee", "team": "MI", "dismissal": "not out", "runs": 4, "balls": 5, "fours": 0, "sixes": 0, "strike_rate": 80.00, "is_out": False},
        ]

        innings_1_bowling = [
            {"player_id": "p_csk_chahar", "name": "Deepak Chahar", "team": "CSK", "overs": 4.0, "maidens": 0, "runs_conceded": 35, "wickets": 1, "economy": 8.75},
            {"player_id": "p_csk_deshpande", "name": "Tushar Deshpande", "team": "CSK", "overs": 4.0, "maidens": 0, "runs_conceded": 38, "wickets": 0, "economy": 9.50},
            {"player_id": "p_csk_thakur", "name": "Shardul Thakur", "team": "CSK", "overs": 4.0, "maidens": 1, "runs_conceded": 29, "wickets": 1, "economy": 7.25, "fantasy_highlight": "43.0 pts locked"},
            {"player_id": "p_csk_jadeja", "name": "Ravindra Jadeja", "team": "CSK", "overs": 4.0, "maidens": 0, "runs_conceded": 25, "wickets": 1, "economy": 6.25, "fantasy_highlight": "37.5 pts (VC 1.5x)"},
            {"player_id": "p_csk_pathirana", "name": "Matheesha Pathirana", "team": "CSK", "overs": 4.0, "maidens": 0, "runs_conceded": 28, "wickets": 2, "economy": 7.00, "fantasy_highlight": "50.0 pts"},
        ]

        innings_2_batting = [
            {"player_id": "p_csk_gaikwad", "name": "Ruturaj Gaikwad (C)", "team": "CSK", "dismissal": "c Kishan b Bumrah", "runs": 42, "balls": 28, "fours": 5, "sixes": 1, "strike_rate": 150.00, "is_out": True},
            {"player_id": "p_csk_rahane", "name": "Ajinkya Rahane", "team": "CSK", "dismissal": "b Coetzee", "runs": 26, "balls": 20, "fours": 3, "sixes": 0, "strike_rate": 130.00, "is_out": True},
            {"player_id": "p_csk_dube", "name": "Shivam Dube", "team": "CSK", "dismissal": "not out", "runs": 36, "balls": 22, "fours": 2, "sixes": 3, "strike_rate": 163.64, "is_out": False, "is_non_striker": True},
            {"player_id": "p_csk_moeen", "name": "Moeen Ali", "team": "CSK", "dismissal": "c David b Chawla", "runs": 9, "balls": 8, "fours": 1, "sixes": 0, "strike_rate": 112.50, "is_out": True},
            {"player_id": "p_csk_stoinis", "name": "Marcus Stoinis (Impact)", "team": "MI", "dismissal": "not out", "runs": 32, "balls": 18, "fours": 3, "sixes": 2, "strike_rate": 177.78, "is_out": False, "is_striker": True, "fantasy_highlight": "32.0 active pts"},
        ]

        innings_2_bowling = [
            {"player_id": "p_mi_bumrah", "name": "Jasprit Bumrah", "team": "MI", "overs": 3.2, "maidens": 0, "runs_conceded": 24, "wickets": 1, "economy": 7.20, "is_current_bowler": True},
            {"player_id": "p_mi_coetzee", "name": "Gerald Coetzee", "team": "MI", "overs": 3.0, "maidens": 0, "runs_conceded": 32, "wickets": 1, "economy": 10.67},
            {"player_id": "p_mi_chawla", "name": "Piyush Chawla", "team": "MI", "overs": 4.0, "maidens": 0, "runs_conceded": 36, "wickets": 1, "economy": 9.00},
            {"player_id": "p_mi_hardik", "name": "Hardik Pandya", "team": "MI", "overs": 3.0, "maidens": 0, "runs_conceded": 28, "wickets": 0, "economy": 9.33},
            {"player_id": "p_mi_madhwal", "name": "Akash Madhwal", "team": "MI", "overs": 3.0, "maidens": 0, "runs_conceded": 25, "wickets": 0, "economy": 8.33},
        ]

        return {
            "innings_1_batting": innings_1_batting,
            "innings_1_bowling": innings_1_bowling,
            "innings_2_batting": innings_2_batting,
            "innings_2_bowling": innings_2_bowling,
            "current_striker": {"name": "Marcus Stoinis", "team": "MI", "runs": 32, "balls": 18, "is_impact": True},
            "current_non_striker": {"name": "Shivam Dube", "team": "CSK", "runs": 36, "balls": 22},
            "current_bowler": {"name": "Jasprit Bumrah", "team": "MI", "overs": "3.2", "figures": "1/24"},
            "last_ball_event": "4 runs • Marcus Stoinis drives Jasprit Bumrah over extra cover",
            "last_over_summary": "1 4 0 2 6 1 • 14 runs (Over 16: Bumrah to Stoinis & Dube)"
        }

    @classmethod
    def set_match_ai_explanation(cls, match: Match, event_type: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Dynamically updates the latest AI strategic explanation responding to the actual backend match event.
        Guarantees realistic natural language, team identification, and fantasy points attribution.
        """
        details = details or {}
        time_tag = details.get("time_tag", "Live Simulation")

        explanations = {
            "PRE_MATCH": {
                "event_label": "PRE_MATCH_INITIALIZED",
                "timestamp": "Pre-Match",
                "headline": "Match Initialized — CSK vs MI at Wankhede Stadium",
                "summary": "T20 Match simulation ready. Fantasy team loaded with 11 starters and 4 prioritized backups (B1-B4). Awaiting official toss and lineup announcement.",
                "tactical_context": "Backups will only be evaluated at the official match start deadline once real Playing XIs are confirmed.",
                "fantasy_impact": "Active fantasy score is 0.0 pts. Multipliers: Ruturaj Gaikwad (C, 2x), Ravindra Jadeja (VC, 1.5x)."
            },
            "TOSS": {
                "event_label": "TOSS_COMPLETED",
                "timestamp": "Toss • 19:00 IST",
                "headline": "Mumbai Indians Win Toss and Elect to Bat First",
                "summary": "Hardik Pandya (MI) won the toss and elected to bat first against Chennai Super Kings at Wankhede Stadium, Mumbai.",
                "tactical_context": "Both teams will announce their Playing XIs and 5 official substitutes shortly.",
                "fantasy_impact": "Pre-match lineup configurations remain pending official confirmation."
            },
            "LINEUP": {
                "event_label": "LINEUP_ANNOUNCEMENT_SCENARIO_1",
                "timestamp": "Lineup Deadline • 19:15 IST",
                "headline": "Starter Mustafizur Rahman (MI) Absent — B2 Shardul Thakur (CSK) Selected",
                "summary": "Mustafizur Rahman (MI) is absent from the announced Playing XI. SmartSub checked Backup 1 Devon Conway (CSK), who also did not play (DID_NOT_PLAY), skipped B1 with an audit log, and promoted Backup 2 Shardul Thakur (CSK) into the active Playing XI.",
                "tactical_context": "Shardul Thakur satisfies all credit (8.0 Cr) and bowling role quotas. Mustafizur Rahman is moved to unavailable squad assets.",
                "fantasy_impact": "Shardul Thakur active in Playing XI (0.0 pts). Mustafizur Rahman excluded from active scoring."
            },
            "BALL": {
                "event_label": "BALL_SIMULATED",
                "timestamp": f"Over {match.current_over}.{match.current_ball}",
                "headline": details.get("headline", "Ball Delivered in Match Play"),
                "summary": details.get("summary", "Ball simulated. The match score, individual player batting and bowling statistics, and fantasy points have been recalculated."),
                "tactical_context": "Real-time ledger updates attribute performance points immediately.",
                "fantasy_impact": details.get("impact", "Player points updated dynamically from match event.")
            },
            "OVER": {
                "event_label": "OVER_COMPLETED",
                "timestamp": f"Over {match.current_over}.0 Completed",
                "headline": f"Over {match.current_over} Complete",
                "summary": "The over is complete. Scoreboard, individual batting statistics, bowling figures, and fantasy point totals have been recalculated.",
                "tactical_context": "Bowler changes and strike rotations applied per standard cricket playing conditions.",
                "fantasy_impact": "Active team fantasy score updated from all participating player contributions."
            },
            "INNINGS_1": {
                "event_label": "INNINGS_1_COMPLETED",
                "timestamp": "Innings Break",
                "headline": "Mumbai Indians Finished at 182/6 (20.0 ov) — Target: 183 Runs",
                "summary": "Mumbai Indians finished their 20.0 overs at 182/6. Shardul Thakur (CSK) bowled 4.0 overs, claiming 1/29 with 1 maiden over, locking in 43.0 illustrative fantasy points.",
                "tactical_context": "CSK requires 183 runs to win at a required run rate of 9.15 RPO.",
                "fantasy_impact": "Shardul Thakur's 43.0 points permanently locked in the Innings 1 ledger."
            },
            "IMPACT_PLAYER": {
                "event_label": "IMPACT_PLAYER_SCENARIO_2",
                "timestamp": "2nd Innings Chase",
                "headline": "Marcus Stoinis (MI) Enters as Impact Player for Shardul Thakur (CSK)",
                "summary": "Marcus Stoinis (MI) has entered as an Impact Player. Under the experimental SmartSub single-occupant replacement rule, he replaces Shardul Thakur (CSK) in the active fantasy slot. Shardul's 43.0 historical points remain locked in the ledger, while Stoinis's 32.0 runs/points count towards the active fantasy total.",
                "tactical_context": "Single-Occupant Rule: Active slot contribution is strictly 32.0 pts (NOT 75.0 pts). Thakur is moved to the replaced players panel.",
                "fantasy_impact": "Active fantasy score includes Marcus Stoinis (32.0 pts) and excludes Shardul Thakur (43.0 historical pts)."
            },
            "MATCH_COMPLETED": {
                "event_label": "MATCH_COMPLETED",
                "timestamp": "Match Concluded",
                "headline": details.get("headline", "Match Concluded — Target Reached"),
                "summary": details.get("summary", "Chennai Super Kings reached the target. Marcus Stoinis (32 off 18) and Shivam Dube (36* off 22) anchored the chase."),
                "tactical_context": "The innings ended under official T20 playing conditions.",
                "fantasy_impact": f"Final User Fantasy Score: {details.get('final_score', '182.5')} points."
            }
        }

        explanation_data = explanations.get(event_type, explanations["PRE_MATCH"])
        explanation_data["is_fallback"] = True
        match.scoreboard["latest_ai_explanation"] = explanation_data
        flag_modified(match, "scoreboard")

    @classmethod
    def conduct_toss(cls, db: Session, match_id: str) -> Match:
        match = db.query(Match).filter_by(id=match_id).first()
        match.toss_winner = "MI"
        match.toss_decision = "BAT"
        match.status = MatchStatus.TOSS_COMPLETED
        match.scoreboard["phase"] = "TOSS_CONDUCTED"
        cls.set_match_ai_explanation(match, "TOSS")
        flag_modified(match, "scoreboard")

        event = MatchEvent(
            match_id=match.id,
            sequence_number=cls._next_sequence_number(db, match.id),
            idempotency_key=f"EVT_{match.id}_TOSS_001",
            event_type="TOSS_CONDUCTED",
            innings=1,
            over=0,
            ball=0,
            payload={"toss_winner": "MI", "toss_decision": "BAT"}
        )
        db.add(event)
        db.commit()
        return match

    @classmethod
    def announce_lineups(cls, db: Session, match_id: str, fantasy_team_id: str) -> Dict[str, Any]:
        """
        Reveals real-world match participation and triggers Scenario 1 evaluation:
        - Starter Mustafizur Rahman (MI) is DID_NOT_PLAY
        - Backup 1 Devon Conway (CSK) is DID_NOT_PLAY (skipped)
        - Backup 2 Shardul Thakur (CSK) is PLAYING_XI (evaluated and selected into Playing XI)
        """
        match = db.query(Match).filter_by(id=match_id).first()
        
        # 1. Update CSK players' real-world participation
        csk_lineups = {
            "p_csk_gaikwad": RealMatchParticipation.PLAYING_XI,
            "p_csk_dube": RealMatchParticipation.PLAYING_XI,
            "p_csk_rahane": RealMatchParticipation.PLAYING_XI,
            "p_csk_dhoni": RealMatchParticipation.PLAYING_XI,
            "p_csk_jadeja": RealMatchParticipation.PLAYING_XI,
            "p_csk_moeen": RealMatchParticipation.PLAYING_XI,
            "p_csk_chahar": RealMatchParticipation.PLAYING_XI,
            "p_csk_pathirana": RealMatchParticipation.PLAYING_XI,
            "p_csk_deshpande": RealMatchParticipation.PLAYING_XI,
            "p_csk_theekshana": RealMatchParticipation.PLAYING_XI,
            "p_csk_mustafizur": RealMatchParticipation.DID_NOT_PLAY,  # Starter DNP (MI)
            "p_csk_conway": RealMatchParticipation.DID_NOT_PLAY,      # B1 DNP (CSK)
            "p_csk_thakur": RealMatchParticipation.PLAYING_XI,        # B2 Playing XI (CSK)
            "p_csk_stoinis": RealMatchParticipation.BENCH_SUBSTITUTE, # B3 Impact candidate (MI)
            "p_csk_rizvi": RealMatchParticipation.BENCH_SUBSTITUTE    # B4 Reserve (CSK)
        }

        for p_id, status in csk_lineups.items():
            p = db.query(Player).filter_by(id=p_id).first()
            if p:
                p.real_match_participation = status

        # 2. Update MI players as PLAYING_XI
        mi_players = db.query(Player).filter_by(team="MI").all()
        for p in mi_players:
            if p.id != "p_csk_mustafizur" and p.id != "p_csk_stoinis":
                p.real_match_participation = RealMatchParticipation.PLAYING_XI

        match.status = MatchStatus.INNINGS_1
        match.scoreboard["phase"] = "LINEUP_CONFIRMED"
        match.scoreboard["current_batsmen"] = ["Rohit Sharma (MI)", "Ishan Kishan (MI)"]
        match.scoreboard["current_bowler"] = "Deepak Chahar (CSK)"
        cls.set_match_ai_explanation(match, "LINEUP")
        flag_modified(match, "scoreboard")

        # 3. Create Lineup Event
        event = MatchEvent(
            match_id=match.id,
            sequence_number=cls._next_sequence_number(db, match.id),
            idempotency_key=f"EVT_{match.id}_LINEUP_001",
            event_type="OFFICIAL_LINEUPS_ANNOUNCED",
            innings=1,
            over=0,
            ball=0,
            payload={
                "unannounced_starters": ["p_csk_mustafizur"],
                "b1_status": "DID_NOT_PLAY",
                "b2_status": "PLAYING_XI",
                "message": "Official Playing XIs announced. Mustafizur Rahman (MI) and Devon Conway (CSK) did not play. Shardul Thakur (CSK) evaluated."
            }
        )
        db.add(event)
        db.commit()

        # 4. Trigger substitution engine for fantasy team
        decision = SubstitutionEngine.process_match_event(db, fantasy_team_id, event)
        cls.recompute_active_points(db, fantasy_team_id)

        return {
            "match": match,
            "event": event,
            "substitution_decision": decision
        }

    @classmethod
    def populate_innings_1_deterministic_scores(cls, db: Session, match_id: str, fantasy_team_id: str) -> None:
        """
        Simulates deterministic 1st-innings cricket events:
        MI bats, CSK bowls.
        - Shardul Thakur (CSK): 4.0 overs, 1 maiden, 29 runs conceded, 1 wicket (Tilak Varma).
          Fantasy points: 25 (wicket) + 12 (maiden) + 6 (economy) = 43.0 pts.
        - Deepak Chahar (CSK): 1 wicket = 25.0 pts.
        - Matheesha Pathirana (CSK): 2 wickets = 50.0 pts.
        - Ravindra Jadeja (CSK, VC 1.5x): 1 wicket = 37.5 pts (25.0 * 1.5).
        - MS Dhoni (CSK): 1 catch = 8.0 pts.
        - MI completed score: 182/6 (20.0 overs).
        """
        match = db.query(Match).filter_by(id=match_id).first()
        match.scoreboard["innings_1"] = {
            "batting_team": "MI",
            "runs": 182,
            "wickets": 6,
            "overs": "20.0",
            "extras": 8
        }
        match.scoreboard["phase"] = "INNINGS_1_COMPLETED"
        match.current_over = 20
        match.current_ball = 0
        cls.set_match_ai_explanation(match, "INNINGS_1")
        flag_modified(match, "scoreboard")

        scores = [
            ("p_csk_thakur", 1, 0, 0, 4.0, 1, 1, 29, 0, 43.0, 1.0, 43.0),
            ("p_csk_chahar", 0, 0, 0, 4.0, 1, 0, 35, 0, 25.0, 1.0, 25.0),
            ("p_csk_pathirana", 0, 0, 0, 4.0, 2, 0, 28, 0, 50.0, 1.0, 50.0),
            ("p_csk_jadeja", 0, 0, 0, 4.0, 1, 0, 22, 0, 25.0, 1.5, 37.5),
            ("p_csk_dhoni", 0, 0, 0, 0.0, 0, 0, 0, 1, 8.0, 1.0, 8.0),
        ]

        for p_id, runs, f4, f6, overs, wkt, maid, runs_conc, ct, base, mult, total in scores:
            ledger = db.query(InningsScoringLedger).filter_by(
                fantasy_team_id=fantasy_team_id,
                player_id=p_id,
                innings=1
            ).first()
            if not ledger:
                ledger = InningsScoringLedger(
                    fantasy_team_id=fantasy_team_id,
                    player_id=p_id,
                    match_id=match_id,
                    innings=1,
                    idempotency_key=f"LEDGER_{match_id}_{p_id}_INN1"
                )
                db.add(ledger)
            ledger.runs_scored = runs
            ledger.fours = f4
            ledger.sixes = f6
            ledger.overs_bowled = overs
            ledger.wickets_taken = wkt
            ledger.maidens = maid
            ledger.runs_conceded = runs_conc
            ledger.catches = ct
            ledger.base_fantasy_points = base
            ledger.multiplier = mult
            ledger.total_fantasy_points = total
            ledger.is_locked = True

        db.commit()
        cls.recompute_active_points(db, fantasy_team_id)

    @classmethod
    def jump_to_second_innings(cls, db: Session, match_id: str, fantasy_team_id: str) -> Match:
        """
        Completes Innings 1 (MI: 182/6 in 20.0 overs) and starts Innings 2 (CSK chase).
        Ensures Shardul Thakur's Innings 1 points (43.0 pts) are locked and preserved.
        """
        match = db.query(Match).filter_by(id=match_id).first()
        match.current_innings = 2
        match.current_over = 0
        match.current_ball = 0
        match.status = MatchStatus.INNINGS_2

        cls.populate_innings_1_deterministic_scores(db, match_id, fantasy_team_id)

        match.scoreboard["innings_2"] = {
            "batting_team": "CSK",
            "runs": 0,
            "wickets": 0,
            "overs": "0.0",
            "target": 183,
            "required_runs": 183
        }
        match.scoreboard["phase"] = "INNINGS_2_STARTED"
        match.scoreboard["current_batsmen"] = ["Ruturaj Gaikwad (CSK)", "Ajinkya Rahane (CSK)"]
        match.scoreboard["current_bowler"] = "Jasprit Bumrah (MI)"
        cls.set_match_ai_explanation(match, "INNINGS_1")
        flag_modified(match, "scoreboard")

        event = MatchEvent(
            match_id=match.id,
            sequence_number=cls._next_sequence_number(db, match.id),
            idempotency_key=f"EVT_{match.id}_INN2_START_001",
            event_type="INNINGS_2_STARTED",
            innings=2,
            over=0,
            ball=0,
            payload={"target": 183, "chasing_team": "CSK"}
        )
        db.add(event)
        db.commit()
        cls.recompute_active_points(db, fantasy_team_id)
        return match

    @classmethod
    def trigger_real_impact_player(
        cls,
        db: Session,
        match_id: str,
        fantasy_team_id: str,
        player_out_id: str = "p_csk_thakur",
        player_in_id: str = "p_csk_stoinis"
    ) -> Dict[str, Any]:
        """
        Dispatches IMPACT_PLAYER_DECLARED event in Innings 2.
        Replaces Shardul Thakur (CSK) with Marcus Stoinis (MI) in active fantasy Playing XI.
        Locks Thakur's 1st-innings points in historical ledger and excludes them from active total.
        """
        match = db.query(Match).filter_by(id=match_id).first()
        
        p_in = db.query(Player).filter_by(id=player_in_id).first()
        if p_in:
            p_in.real_match_participation = RealMatchParticipation.IMPACT_ENTERED

        p_out = db.query(Player).filter_by(id=player_out_id).first()
        if p_out:
            p_out.real_match_participation = RealMatchParticipation.BENCH_SUBSTITUTE

        event = MatchEvent(
            match_id=match.id,
            sequence_number=cls._next_sequence_number(db, match.id),
            idempotency_key=f"EVT_{match.id}_IMPACT_{player_in_id}_001",
            event_type="IMPACT_PLAYER_DECLARED",
            innings=2,
            over=match.current_over,
            ball=match.current_ball,
            payload={
                "player_out_id": player_out_id,
                "player_in_id": player_in_id,
                "reason": "CSK introduces Marcus Stoinis (MI) as 2nd innings Impact Player finisher for Shardul Thakur (CSK)"
            }
        )
        db.add(event)
        db.commit()

        # Evaluate substitution
        decision = SubstitutionEngine.process_match_event(db, fantasy_team_id, event)

        # Simulate Stoinis 2nd innings batting performance
        cls.populate_innings_2_deterministic_scores(db, match_id, fantasy_team_id)

        # Update scoreboard batsmen and latest explanation
        match.scoreboard["current_batsmen"] = ["Marcus Stoinis (Impact)", "Shivam Dube (CSK)"]
        match.scoreboard["phase"] = "IMPACT_PLAYER_ACTIVE"
        cls.set_match_ai_explanation(match, "IMPACT_PLAYER")
        flag_modified(match, "scoreboard")
        db.commit()

        return {
            "match": match,
            "event": event,
            "substitution_decision": decision
        }

    @classmethod
    def populate_innings_2_deterministic_scores(cls, db: Session, match_id: str, fantasy_team_id: str) -> None:
        """
        Simulates deterministic 2nd-innings cricket events:
        Marcus Stoinis (MI) bats at #5 in the chase, scoring 32 runs off 18 balls (3 fours, 2 sixes).
        Generates 32.0 fantasy points.
        CSK scoreboard: 145/4 in 16.2 overs, chasing 183.
        """
        match = db.query(Match).filter_by(id=match_id).first()
        match.scoreboard["innings_2"] = {
            "batting_team": "CSK",
            "runs": 145,
            "wickets": 4,
            "overs": "16.2",
            "target": 183,
            "required_runs": 38
        }
        match.current_over = 16
        match.current_ball = 2

        # Stoinis Innings 2 ledger
        ledger = db.query(InningsScoringLedger).filter_by(
            fantasy_team_id=fantasy_team_id,
            player_id="p_csk_stoinis",
            innings=2
        ).first()
        if not ledger:
            ledger = InningsScoringLedger(
                fantasy_team_id=fantasy_team_id,
                player_id="p_csk_stoinis",
                match_id=match_id,
                innings=2,
                idempotency_key=f"LEDGER_{match_id}_p_csk_stoinis_INN2"
            )
            db.add(ledger)
        ledger.runs_scored = 32
        ledger.balls_faced = 18
        ledger.fours = 3
        ledger.sixes = 2
        ledger.base_fantasy_points = 32.0
        ledger.multiplier = 1.0
        ledger.total_fantasy_points = 32.0
        ledger.is_locked = False

        # Additional CSK chase scores
        csk_scores = [
            ("p_csk_gaikwad", 42, 5, 1, 0.0, 0, 0, 0, 0, 52.0, 2.0, 104.0),  # Captain 2x
            ("p_csk_dube", 36, 2, 3, 0.0, 0, 0, 0, 0, 48.0, 1.0, 48.0),
            ("p_csk_rahane", 26, 3, 0, 0.0, 0, 0, 0, 0, 32.0, 1.0, 32.0),
        ]
        for p_id, r, f4, f6, ov, w, m, rc, ct, base, mult, tot in csk_scores:
            l = db.query(InningsScoringLedger).filter_by(
                fantasy_team_id=fantasy_team_id,
                player_id=p_id,
                innings=2
            ).first()
            if not l:
                l = InningsScoringLedger(
                    fantasy_team_id=fantasy_team_id,
                    player_id=p_id,
                    match_id=match_id,
                    innings=2,
                    idempotency_key=f"LEDGER_{match_id}_{p_id}_INN2"
                )
                db.add(l)
            l.runs_scored = r
            l.fours = f4
            l.sixes = f6
            l.base_fantasy_points = base
            l.multiplier = mult
            l.total_fantasy_points = tot

        flag_modified(match, "scoreboard")
        db.commit()
        cls.recompute_active_points(db, fantasy_team_id)

    @classmethod
    def step_ball(cls, db: Session, match_id: str, fantasy_team_id: str) -> Dict[str, Any]:
        """
        Simulates 1 legal delivery in the cricket match.
        STRICT T20 OVERS LIMIT ENFORCED:
        - Max 20 legal overs (120 legal deliveries).
        - Cricket notation: 0.1, 0.2 ... 19.5, 20.0. Never 19.6, 20.1, or 20.2!
        - Innings 1 ends when: 20 legal overs complete OR 10 wickets fallen.
        - Innings 2 ends when: 20 legal overs complete OR 10 wickets fallen OR target reached.
        - When innings ends, further simulation is disabled and reason is explained.
        """
        match = db.query(Match).filter_by(id=match_id).first()
        if match.status not in [MatchStatus.INNINGS_1, MatchStatus.INNINGS_2]:
            return {"error": "Match is not in an active innings. Complete or reset the match to proceed."}

        innings_key = f"innings_{match.current_innings}"
        sc = match.scoreboard.get(innings_key, {})

        # Check if already at 20 overs or all out
        current_overs_val = match.current_over
        if current_overs_val >= 20 or sc.get("wickets", 0) >= 10:
            return {"error": "Innings has already ended (20 overs reached or team all out)."}

        # Advance delivery
        match.current_ball += 1
        if match.current_ball >= 6:
            match.current_over += 1
            match.current_ball = 0

        # Format overs strictly in cricket notation
        if match.current_ball == 0 and match.current_over > 0:
            overs_str = f"{match.current_over}.0"
        else:
            overs_str = f"{match.current_over}.{match.current_ball}"
        sc["overs"] = overs_str

        # Delivery outcome
        outcomes = [0, 1, 1, 2, 4, 6, "W"]
        ball_outcome = random.choice(outcomes)

        runs_scored = 0
        wicket_fallen = False

        if ball_outcome == "W":
            wicket_fallen = True
            sc["wickets"] = sc.get("wickets", 0) + 1
        else:
            runs_scored = ball_outcome
            sc["runs"] = sc.get("runs", 0) + runs_scored

        # Check innings-ending conditions
        target = sc.get("target", 183)
        if match.current_innings == 1:
            if match.current_over >= 20 or sc["wickets"] >= 10:
                match.scoreboard["phase"] = "INNINGS_BREAK"
                match.scoreboard["innings_2"]["target"] = sc["runs"] + 1
                match.scoreboard["innings_2"]["required_runs"] = sc["runs"] + 1
                cls.set_match_ai_explanation(match, "INNINGS_1")
        elif match.current_innings == 2:
            sc["required_runs"] = max(0, target - sc.get("runs", 0))
            if sc["runs"] >= target:
                match.scoreboard["phase"] = "COMPLETED"
                match.status = MatchStatus.COMPLETED
                res_msg = f"Chennai Super Kings won by {10 - sc['wickets']} wickets (Target reached in {overs_str} ov)"
                match.scoreboard["match_result"] = res_msg
                cls.set_match_ai_explanation(match, "MATCH_COMPLETED", {"headline": "CSK Won the Match!", "summary": res_msg})
            elif match.current_over >= 20 or sc["wickets"] >= 10:
                match.scoreboard["phase"] = "COMPLETED"
                match.status = MatchStatus.COMPLETED
                res_msg = f"Mumbai Indians won by {target - 1 - sc['runs']} runs (Defended target in 20.0 ov)"
                match.scoreboard["match_result"] = res_msg
                cls.set_match_ai_explanation(match, "MATCH_COMPLETED", {"headline": "MI Won the Match!", "summary": res_msg})

        match.scoreboard[innings_key] = sc

        # Fantasy points attribution for active replacements
        if match.current_innings == 1:
            thakur_slot = db.query(FantasyLineupSlot).filter_by(
                fantasy_team_id=fantasy_team_id,
                player_id="p_csk_thakur",
                fantasy_selection_status=FantasySelectionStatus.SELECTED
            ).first()
            if thakur_slot and wicket_fallen:
                ledger = db.query(InningsScoringLedger).filter_by(
                    fantasy_team_id=fantasy_team_id,
                    player_id="p_csk_thakur",
                    innings=1
                ).first()
                if ledger:
                    ledger.wickets_taken += 1
                    ledger.base_fantasy_points += 25.0
                    ledger.total_fantasy_points = ledger.base_fantasy_points * ledger.multiplier
        elif match.current_innings == 2:
            stoinis_slot = db.query(FantasyLineupSlot).filter_by(
                fantasy_team_id=fantasy_team_id,
                player_id="p_csk_stoinis",
                fantasy_selection_status=FantasySelectionStatus.SELECTED
            ).first()
            if stoinis_slot and runs_scored > 0:
                ledger = db.query(InningsScoringLedger).filter_by(
                    fantasy_team_id=fantasy_team_id,
                    player_id="p_csk_stoinis",
                    innings=2
                ).first()
                if ledger:
                    ledger.runs_scored += runs_scored
                    ledger.base_fantasy_points += float(runs_scored)
                    if runs_scored == 4:
                        ledger.fours += 1
                        ledger.base_fantasy_points += 1.0
                    elif runs_scored == 6:
                        ledger.sixes += 1
                        ledger.base_fantasy_points += 2.0
                    ledger.total_fantasy_points = ledger.base_fantasy_points * ledger.multiplier

        flag_modified(match, "scoreboard")
        db.commit()
        pts_info = cls.recompute_active_points(db, fantasy_team_id)

        return {
            "over": match.current_over,
            "ball": match.current_ball,
            "overs_formatted": overs_str,
            "outcome": ball_outcome,
            "scoreboard": match.scoreboard,
            "fantasy_team_total_points": pts_info["active_total_points"]
        }

    @classmethod
    def execute_scenario_1_automation(cls, db: Session, match_id: str, fantasy_team_id: str) -> Dict[str, Any]:
        """
        Complete end-to-end automated execution of Scenario 1:
        1. Clean reset to pre-match initial state
        2. Conduct toss (MI wins, bats)
        3. Announce official lineups (Mustafizur DNP, Conway B1 skipped DNP, Thakur B2 evaluated & substituted)
        4. Generate AI explainability report
        """
        cls.reset_match(db, match_id, fantasy_team_id)
        match_after_toss = cls.conduct_toss(db, match_id)
        lineup_result = cls.announce_lineups(db, match_id, fantasy_team_id)
        sub_decision = lineup_result["substitution_decision"]

        explanation = None
        if sub_decision:
            explanation = GeminiAIService.explain_decision(db, sub_decision.id)

        pts_info = cls.recompute_active_points(db, fantasy_team_id)
        match = db.query(Match).filter_by(id=match_id).first()

        return {
            "scenario": 1,
            "status": "SCENARIO_1_COMPLETED",
            "match": match,
            "substitution_decision": sub_decision,
            "ai_explanation": explanation,
            "points_info": pts_info,
            "message": "Scenario 1 automated successfully: Mustafizur Rahman (MI, DNP) replaced by Shardul Thakur (CSK, B2) after Devon Conway (CSK, B1) skipped."
        }

    @classmethod
    def execute_scenario_2_automation(cls, db: Session, match_id: str, fantasy_team_id: str) -> Dict[str, Any]:
        """
        Complete end-to-end automated execution of Scenario 2:
        Can be run independently from ANY state!
        1. Runs clean reset + Scenario 1 setup (Mustafizur -> Shardul Thakur)
        2. Simulates Innings 1 (MI 182/6 in 20.0 overs; Shardul Thakur bowls 4 ov, 1 wkt, locks 43.0 pts)
        3. Starts Innings 2 (CSK chase target 183)
        4. Triggers Impact Player substitution (Marcus Stoinis replaces Shardul Thakur)
        5. Simulates Innings 2 chase (Stoinis scores 32 runs off 18 balls)
        6. Computes active fantasy points: Stoinis contributes 32.0 active pts; Thakur's 43.0 historical pts remain locked in ledger.
        7. Sets dynamic AI explanation and final summary.
        """
        cls.execute_scenario_1_automation(db, match_id, fantasy_team_id)
        cls.jump_to_second_innings(db, match_id, fantasy_team_id)
        impact_result = cls.trigger_real_impact_player(
            db=db,
            match_id=match_id,
            fantasy_team_id=fantasy_team_id,
            player_out_id="p_csk_thakur",
            player_in_id="p_csk_stoinis"
        )
        sub_decision = impact_result["substitution_decision"]

        explanation = None
        if sub_decision:
            explanation = GeminiAIService.explain_decision(db, sub_decision.id)

        pts_info = cls.recompute_active_points(db, fantasy_team_id)
        match = db.query(Match).filter_by(id=match_id).first()

        return {
            "scenario": 2,
            "status": "SCENARIO_2_COMPLETED",
            "match": match,
            "substitution_decision": sub_decision,
            "ai_explanation": explanation,
            "points_info": pts_info,
            "message": "Scenario 2 automated successfully: Marcus Stoinis (MI) introduced as 2nd innings Impact Player for Shardul Thakur (CSK). Thakur's 43.0 1st innings points locked in historical ledger and excluded from active score; Stoinis's 32.0 points active."
        }

    @classmethod
    def reset_match(cls, db: Session, match_id: str, fantasy_team_id: str) -> Match:
        """
        Full application restoration contract.
        Guarantees exact return to pristine pre-match state:
        - Match status -> UPCOMING, current_innings -> 1, overs -> 0.0, runs -> 0, wickets -> 0, toss -> None
        - Scoreboard -> pre-match state
        - Clears all AI explanations, substitution decisions, processed events, scoring ledgers
        - Resets all player participation to NOT_STARTED and stats to zero
        - Restores fantasy lineup slots: 11 Starters (SELECTED, entry_innings=1), 4 Backups (NOT_SELECTED)
        - Restores original B1-B4 backup priorities
        - Resets fantasy team total_points -> 0.0
        """
        match = db.query(Match).filter_by(id=match_id).first()
        if not match:
            return None

        match.status = MatchStatus.UPCOMING
        match.toss_winner = None
        match.toss_decision = None
        match.current_innings = 1
        match.current_over = 0
        match.current_ball = 0
        match.scoreboard = {
            "innings_1": {"batting_team": "MI", "runs": 0, "wickets": 0, "overs": "0.0", "extras": 0},
            "innings_2": {"batting_team": "CSK", "runs": 0, "wickets": 0, "overs": "0.0", "target": 183, "required_runs": 183},
            "current_batsmen": [],
            "current_bowler": None,
            "phase": "PRE_MATCH"
        }

        # Clear dependent tables in reverse foreign key dependency order
        db.query(AIExplanation).delete()
        db.query(SubstitutionDecision).filter_by(fantasy_team_id=fantasy_team_id).delete()
        db.query(ProcessedEvent).filter_by(fantasy_team_id=fantasy_team_id).delete()
        db.query(MatchEvent).filter(MatchEvent.match_id == match.id).delete()
        db.query(InningsScoringLedger).filter_by(fantasy_team_id=fantasy_team_id).delete()

        # Re-create canonical initial match event
        init_event = MatchEvent(
            match_id=match.id,
            sequence_number=1,
            idempotency_key=f"EVT_{match.id}_INIT_001",
            event_type="MATCH_INITIALIZED",
            innings=1,
            over=0,
            ball=0,
            payload={"message": "Match initialized in pre-match state"}
        )
        db.add(init_event)

        # Reset all player participation and stats
        players = db.query(Player).all()
        for p in players:
            p.real_match_participation = RealMatchParticipation.NOT_STARTED
            p.stats = {"runs": 0, "wickets": 0, "overs": 0.0, "maidens": 0, "catches": 0}

        # Canonical backup priorities mapping
        backup_priorities = {
            "p_csk_conway": (1, "B1"),
            "p_csk_thakur": (2, "B2"),
            "p_csk_stoinis": (3, "B3"),
            "p_csk_rizvi": (4, "B4")
        }

        # Reset fantasy lineup slots
        slots = db.query(FantasyLineupSlot).filter_by(fantasy_team_id=fantasy_team_id).all()
        for s in slots:
            s.fantasy_points = 0.0
            s.active_fantasy_points = 0.0
            if s.slot_type == FantasySlotType.STARTER:
                s.fantasy_selection_status = FantasySelectionStatus.SELECTED
                s.entry_innings = 1
                s.exit_innings = None
                s.priority_rank = None
                s.priority_label = None
            else:
                s.fantasy_selection_status = FantasySelectionStatus.NOT_SELECTED
                s.entry_innings = None
                s.exit_innings = None
                if s.player_id in backup_priorities:
                    rank, label = backup_priorities[s.player_id]
                    s.priority_rank = rank
                    s.priority_label = label
            s.substituted_in_for_player_id = None

        team = db.query(FantasyTeam).filter_by(id=fantasy_team_id).first()
        if team:
            team.total_points = 0.0

        cls.set_match_ai_explanation(match, "PRE_MATCH")
        flag_modified(match, "scoreboard")
        db.commit()
        return match
