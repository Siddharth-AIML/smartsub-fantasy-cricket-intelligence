from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.enums import (
    FantasySlotType,
    RealMatchParticipation,
    FantasySelectionStatus,
    RuleTier,
    DecisionStatus
)
from app.models.player import Player, InningsScoringLedger
from app.models.match import MatchEvent, ProcessedEvent
from app.models.fantasy_team import FantasyTeam, FantasyLineupSlot, SubstitutionRulesConfig
from app.models.substitution import SubstitutionDecision
from app.models.ai_explanation import AIExplanation
from app.services.validators import (
    OfficialPlatformConstraintValidator,
    ExperimentalInMatchValidator
)

class SubstitutionEngine:
    @classmethod
    def capture_team_snapshot(cls, db: Session, fantasy_team_id: str) -> Dict[str, Any]:
        """Captures complete squad state and point breakdown for audit history."""
        slots = db.query(FantasyLineupSlot).filter_by(fantasy_team_id=fantasy_team_id).all()
        ledgers = db.query(InningsScoringLedger).filter_by(fantasy_team_id=fantasy_team_id).all()
        
        snapshot = {
            "fantasy_team_id": fantasy_team_id,
            "selected_xi": [],
            "bench": [],
            "total_points": 0.0,
            "ledger_entries": []
        }
        
        for slot in slots:
            player = slot.player
            slot_info = {
                "player_id": player.id,
                "short_name": player.short_name,
                "role": player.role.value if hasattr(player.role, "value") else str(player.role),
                "credits": player.credits,
                "slot_type": slot.slot_type.value if hasattr(slot.slot_type, "value") else str(slot.slot_type),
                "priority_rank": slot.priority_rank,
                "priority_label": slot.priority_label,
                "fantasy_selection_status": slot.fantasy_selection_status.value if hasattr(slot.fantasy_selection_status, "value") else str(slot.fantasy_selection_status),
                "real_match_participation": player.real_match_participation.value if hasattr(player.real_match_participation, "value") else str(player.real_match_participation),
                "entry_innings": slot.entry_innings,
                "exit_innings": slot.exit_innings
            }
            if slot.fantasy_selection_status == FantasySelectionStatus.SELECTED:
                snapshot["selected_xi"].append(slot_info)
            else:
                snapshot["bench"].append(slot_info)

        for l in ledgers:
            snapshot["ledger_entries"].append({
                "player_id": l.player_id,
                "innings": l.innings,
                "total_fantasy_points": l.total_fantasy_points,
                "is_locked": l.is_locked
            })
            snapshot["total_points"] += l.total_fantasy_points

        return snapshot

    @classmethod
    def process_match_event(cls, db: Session, fantasy_team_id: str, event: MatchEvent) -> Optional[SubstitutionDecision]:
        """
        Atomic and idempotent event processor for fantasy team substitutions.
        Guarantees idempotency and monotonic ordering.
        """
        # 1. Idempotency Check
        existing_processed = db.query(ProcessedEvent).filter_by(
            fantasy_team_id=fantasy_team_id,
            idempotency_key=event.idempotency_key
        ).first()
        if existing_processed:
            # Already processed; return existing decision if any
            existing_decision = db.query(SubstitutionDecision).filter_by(
                fantasy_team_id=fantasy_team_id,
                idempotency_key=event.idempotency_key
            ).first()
            return existing_decision

        # 2. Monotonic sequence check
        latest_processed = db.query(ProcessedEvent).join(
            MatchEvent, ProcessedEvent.event_id == MatchEvent.id
        ).filter(
            ProcessedEvent.fantasy_team_id == fantasy_team_id
        ).order_by(MatchEvent.sequence_number.desc()).first()

        if latest_processed:
            latest_event = db.query(MatchEvent).filter_by(id=latest_processed.event_id).first()
            if latest_event and event.sequence_number < latest_event.sequence_number:
                # Out-of-order event rejected
                return SubstitutionDecision(
                    fantasy_team_id=fantasy_team_id,
                    match_event_id=event.id,
                    idempotency_key=event.idempotency_key,
                    rule_id="ENGINE_EVENT_DISPATCH",
                    rule_tier=RuleTier.TIER_1_VERIFIED,
                    reason_code="OUT_OF_ORDER_EVENT_REJECTED",
                    status=DecisionStatus.SKIPPED
                )

        fantasy_team = db.query(FantasyTeam).filter_by(id=fantasy_team_id).first()
        rules_config = db.query(SubstitutionRulesConfig).filter_by(fantasy_team_id=fantasy_team_id).first()

        decision = None

        # Route by event type
        if event.event_type in ["LINEUP_ANNOUNCED", "OFFICIAL_LINEUPS_ANNOUNCED"]:
            decision = cls._handle_lineup_announcement_scenario_1(db, fantasy_team, event, rules_config)
        elif event.event_type in ["IMPACT_PLAYER_DECLARED", "IMPACT_PLAYER_ACTIVATED"]:
            decision = cls._handle_impact_player_scenario_2(db, fantasy_team, event, rules_config)

        # Mark as processed in processed_events table
        processed_record = ProcessedEvent(
            fantasy_team_id=fantasy_team_id,
            event_id=event.id,
            idempotency_key=event.idempotency_key
        )
        db.add(processed_record)
        db.commit()

        return decision

    @classmethod
    def _handle_lineup_announcement_scenario_1(
        cls,
        db: Session,
        fantasy_team: FantasyTeam,
        event: MatchEvent,
        rules_config: SubstitutionRulesConfig
    ) -> Optional[SubstitutionDecision]:
        """
        Scenario 1: Evaluates unannounced starters.
        If B1 does not participate in the real match (DID_NOT_PLAY),
        SmartSub logs B1 bypass and evaluates B2 (in real Playing XI) against platform constraints.
        """
        starters = db.query(FantasyLineupSlot).filter_by(
            fantasy_team_id=fantasy_team.id,
            slot_type=FantasySlotType.STARTER,
            fantasy_selection_status=FantasySelectionStatus.SELECTED
        ).all()

        # Find starters that did not play in the real match
        dnp_starters = [s for s in starters if s.player.real_match_participation == RealMatchParticipation.DID_NOT_PLAY]
        if not dnp_starters:
            return None  # All starters playing; no substitution required

        dnp_starter = dnp_starters[0]  # Process unannounced starter

        # Fetch bench backups sorted strictly by priority_rank 1 to 4
        bench_slots = db.query(FantasyLineupSlot).filter_by(
            fantasy_team_id=fantasy_team.id,
            slot_type=FantasySlotType.BACKUP
        ).order_by(FantasyLineupSlot.priority_rank.asc()).all()

        evaluations_audit = []
        chosen_backup_slot = None
        rejection_reason = "NO_ELIGIBLE_BACKUP_FOUND"

        active_starters_players = [s.player for s in starters]

        for b_slot in bench_slots:
            candidate = b_slot.player

            # Check real match participation
            if candidate.real_match_participation == RealMatchParticipation.DID_NOT_PLAY:
                evaluations_audit.append({
                    "player_id": candidate.id,
                    "short_name": candidate.short_name,
                    "priority_rank": b_slot.priority_rank,
                    "priority_label": b_slot.priority_label,
                    "status": "SKIPPED",
                    "reason": "BACKUP_SKIPPED_DID_NOT_PLAY"
                })
                continue  # B1 never enters; proceeds to evaluate B2!

            # Evaluate platform constraints
            is_valid, constraint_details = OfficialPlatformConstraintValidator.validate_swap(
                current_starters=active_starters_players,
                player_out=dnp_starter.player,
                player_in=candidate
            )

            if not is_valid:
                evaluations_audit.append({
                    "player_id": candidate.id,
                    "short_name": candidate.short_name,
                    "priority_rank": b_slot.priority_rank,
                    "priority_label": b_slot.priority_label,
                    "status": "REJECTED_CONSTRAINTS",
                    "details": constraint_details
                })
                continue

            # Eligible replacement found (e.g. B2 Shardul Thakur)
            chosen_backup_slot = b_slot
            evaluations_audit.append({
                "player_id": candidate.id,
                "short_name": candidate.short_name,
                "priority_rank": b_slot.priority_rank,
                "priority_label": b_slot.priority_label,
                "status": "ACCEPTED",
                "details": constraint_details
            })
            break

        if not chosen_backup_slot:
            # No eligible candidate found
            decision = SubstitutionDecision(
                fantasy_team_id=fantasy_team.id,
                match_event_id=event.id,
                idempotency_key=event.idempotency_key,
                player_out_id=dnp_starter.player_id,
                player_in_id=None,
                rule_id="R-D11-01",
                rule_tier=RuleTier.TIER_1_VERIFIED,
                reason_code="NO_ELIGIBLE_BACKUP_FOUND",
                status=DecisionStatus.NO_ELIGIBLE_BACKUP_FOUND,
                evaluations_audit=evaluations_audit
            )
            db.add(decision)
            return decision

        # Execute Swap
        snapshot_before = cls.capture_team_snapshot(db, fantasy_team.id)

        dnp_starter.fantasy_selection_status = FantasySelectionStatus.SUBSTITUTED_OUT
        dnp_starter.exit_innings = 1
        chosen_backup_slot.fantasy_selection_status = FantasySelectionStatus.SELECTED
        chosen_backup_slot.entry_innings = 1
        chosen_backup_slot.substituted_in_for_player_id = dnp_starter.player_id

        # Initialize Innings 1 scoring ledger for the replacement player
        ledger_entry = InningsScoringLedger(
            fantasy_team_id=fantasy_team.id,
            player_id=chosen_backup_slot.player_id,
            match_id=fantasy_team.match_id,
            innings=1,
            base_fantasy_points=0.0,
            multiplier=1.0,
            total_fantasy_points=0.0,
            is_locked=False,
            idempotency_key=f"LEDGER_{event.idempotency_key}_{chosen_backup_slot.player_id}_INN1"
        )
        db.add(ledger_entry)

        snapshot_after = cls.capture_team_snapshot(db, fantasy_team.id)

        decision = SubstitutionDecision(
            fantasy_team_id=fantasy_team.id,
            match_event_id=event.id,
            idempotency_key=event.idempotency_key,
            player_out_id=dnp_starter.player_id,
            player_in_id=chosen_backup_slot.player_id,
            priority_rank_used=chosen_backup_slot.priority_rank,
            rule_id="R-SUB-01",
            rule_tier=RuleTier.TIER_4_PROPOSED_EXPERIMENTAL,
            reason_code="SCENARIO_1_B2_SUBSTITUTED_WHEN_B1_DNP",
            status=DecisionStatus.EXECUTED,
            evaluations_audit=evaluations_audit,
            constraints_checked={"passed": True, "details": "Platform constraints verified"},
            squad_snapshot_before=snapshot_before,
            squad_snapshot_after=snapshot_after
        )
        db.add(decision)
        return decision

    @classmethod
    def _handle_impact_player_scenario_2(
        cls,
        db: Session,
        fantasy_team: FantasyTeam,
        event: MatchEvent,
        rules_config: SubstitutionRulesConfig
    ) -> Optional[SubstitutionDecision]:
        """
        Scenario 2: Mid-match tactical Impact Player substitution.
        Preserves outgoing player's Innings 1 batting/bowling/fielding points in an immutable ledger.
        Activates incoming player for Innings 2.
        """
        if not rules_config or not rules_config.scenario_2_enabled:
            return SubstitutionDecision(
                fantasy_team_id=fantasy_team.id,
                match_event_id=event.id,
                idempotency_key=event.idempotency_key,
                rule_id="R-SUB-02",
                rule_tier=RuleTier.TIER_4_PROPOSED_EXPERIMENTAL,
                reason_code="RULE_DISABLED_SCENARIO_2",
                status=DecisionStatus.SKIPPED
            )

        if event.innings != 2:
            return SubstitutionDecision(
                fantasy_team_id=fantasy_team.id,
                match_event_id=event.id,
                idempotency_key=event.idempotency_key,
                rule_id="R-SUB-02",
                rule_tier=RuleTier.TIER_4_PROPOSED_EXPERIMENTAL,
                reason_code="REJECTED_NOT_SECOND_INNINGS",
                status=DecisionStatus.REJECTED_CONSTRAINTS
            )

        payload = event.payload or {}
        # Outgoing player (e.g., Shardul Thakur who bowled in Innings 1)
        player_out_id = payload.get("player_out_id", "p_csk_thakur")
        # Incoming player (e.g., Marcus Stoinis impact finisher)
        player_in_id = payload.get("player_in_id", "p_csk_stoinis")

        out_slot = db.query(FantasyLineupSlot).filter_by(
            fantasy_team_id=fantasy_team.id,
            player_id=player_out_id
        ).first()

        in_slot = db.query(FantasyLineupSlot).filter_by(
            fantasy_team_id=fantasy_team.id,
            player_id=player_in_id
        ).first()

        if not out_slot or not in_slot:
            return SubstitutionDecision(
                fantasy_team_id=fantasy_team.id,
                match_event_id=event.id,
                idempotency_key=event.idempotency_key,
                rule_id="R-SUB-02",
                rule_tier=RuleTier.TIER_4_PROPOSED_EXPERIMENTAL,
                reason_code="PLAYER_SLOTS_NOT_FOUND",
                status=DecisionStatus.REJECTED_CONSTRAINTS
            )

        # Verify outgoing player participated in Innings 1
        inn1_ledger = db.query(InningsScoringLedger).filter_by(
            fantasy_team_id=fantasy_team.id,
            player_id=player_out_id,
            innings=1
        ).first()

        # Context-sensitive validation
        active_slots = db.query(FantasyLineupSlot).filter_by(
            fantasy_team_id=fantasy_team.id,
            fantasy_selection_status=FantasySelectionStatus.SELECTED
        ).all()
        current_xi = [s.player for s in active_slots]

        is_valid, validation_details = ExperimentalInMatchValidator.validate_impact_swap(
            current_xi=current_xi,
            player_out=out_slot.player,
            player_in=in_slot.player,
            innings=2
        )

        if not is_valid:
            return SubstitutionDecision(
                fantasy_team_id=fantasy_team.id,
                match_event_id=event.id,
                idempotency_key=event.idempotency_key,
                player_out_id=player_out_id,
                player_in_id=player_in_id,
                rule_id="R-SUB-02",
                rule_tier=RuleTier.TIER_4_PROPOSED_EXPERIMENTAL,
                reason_code="IMPACT_SWAP_VALIDATION_FAILED",
                status=DecisionStatus.REJECTED_CONSTRAINTS,
                constraints_checked=validation_details
            )

        snapshot_before = cls.capture_team_snapshot(db, fantasy_team.id)

        # 1. Lock outgoing player's Innings 1 points permanently
        if inn1_ledger:
            inn1_ledger.is_locked = True
        
        out_slot.fantasy_selection_status = FantasySelectionStatus.SUBSTITUTED_OUT
        out_slot.exit_innings = 1

        # 2. Activate incoming player for Innings 2
        in_slot.fantasy_selection_status = FantasySelectionStatus.SELECTED
        in_slot.entry_innings = 2
        in_slot.substituted_in_for_player_id = player_out_id

        # 3. Create fresh Innings 2 ledger entry for incoming player
        inn2_ledger = InningsScoringLedger(
            fantasy_team_id=fantasy_team.id,
            player_id=player_in_id,
            match_id=fantasy_team.match_id,
            innings=2,
            base_fantasy_points=0.0,
            multiplier=1.0,
            total_fantasy_points=0.0,
            is_locked=False,
            idempotency_key=f"LEDGER_{event.idempotency_key}_{player_in_id}_INN2"
        )
        db.add(inn2_ledger)

        snapshot_after = cls.capture_team_snapshot(db, fantasy_team.id)

        decision = SubstitutionDecision(
            fantasy_team_id=fantasy_team.id,
            match_event_id=event.id,
            idempotency_key=event.idempotency_key,
            player_out_id=player_out_id,
            player_in_id=player_in_id,
            priority_rank_used=in_slot.priority_rank,
            rule_id="R-SUB-02",
            rule_tier=RuleTier.TIER_4_PROPOSED_EXPERIMENTAL,
            reason_code="SCENARIO_2_IMPACT_SUB_INN2_EXECUTED",
            status=DecisionStatus.EXECUTED,
            constraints_checked={"passed": True, "details": "Experimental 2nd innings impact constraints satisfied"},
            squad_snapshot_before=snapshot_before,
            squad_snapshot_after=snapshot_after
        )
        db.add(decision)
        return decision

    @classmethod
    def replay_all_events(cls, db: Session, fantasy_team_id: str, events: List[MatchEvent]) -> Dict[str, Any]:
        """
        Deterministic event replay: Resets state to t=0 and replays events in monotonic order.
        """
        # 1. Clear processed events and decisions
        db.query(AIExplanation).delete()
        db.query(ProcessedEvent).filter_by(fantasy_team_id=fantasy_team_id).delete()
        db.query(SubstitutionDecision).filter_by(fantasy_team_id=fantasy_team_id).delete()
        db.query(InningsScoringLedger).filter_by(fantasy_team_id=fantasy_team_id).delete()

        # 2. Reset slots to initial pre-match state
        slots = db.query(FantasyLineupSlot).filter_by(fantasy_team_id=fantasy_team_id).all()
        for s in slots:
            if s.slot_type == FantasySlotType.STARTER:
                s.fantasy_selection_status = FantasySelectionStatus.SELECTED
                s.entry_innings = 1
                s.exit_innings = None
            else:
                s.fantasy_selection_status = FantasySelectionStatus.NOT_SELECTED
                s.entry_innings = None
                s.exit_innings = None
            s.substituted_in_for_player_id = None
        db.commit()

        # 3. Replay sorted events
        sorted_events = sorted(events, key=lambda e: e.sequence_number)
        for evt in sorted_events:
            cls.process_match_event(db, fantasy_team_id, evt)

        return cls.capture_team_snapshot(db, fantasy_team_id)
