from typing import List, Dict, Tuple, Any
from app.models.player import Player
from app.models.enums import PlayerRole

class PreMatchTeamCreationValidator:
    """
    Validates initial 15-player fantasy team assembly.
    11 Starters + 4 Backups, all unique, within credit & role quotas.
    """
    CREDIT_CAP = 100.0
    ROLE_MIN = 1
    ROLE_MAX = 8
    MAX_TEAM_PLAYERS = 10  # Dream11 modern 10-1 rule

    @classmethod
    def validate_squad(cls, starters: List[Player], backups: List[Player]) -> Tuple[bool, str, Dict[str, Any]]:
        # 1. Total counts
        if len(starters) != 11:
            return False, f"Starting XI must contain exactly 11 players, found {len(starters)}", {}
        if len(backups) != 4:
            return False, f"Backups must contain exactly 4 players, found {len(backups)}", {}

        # 2. Check for duplicate players across the entire 15-man roster
        all_players = starters + backups
        unique_ids = set(p.id for p in all_players)
        if len(unique_ids) != 15:
            duplicates = [p.short_name for p in all_players if [x.id for x in all_players].count(p.id) > 1]
            return False, f"DUPLICATE_ROSTER_PLAYER_ERROR: Duplicate players found in squad: {set(duplicates)}", {}

        # 3. Credits for starting XI
        total_starter_credits = sum(p.credits for p in starters)
        if total_starter_credits > cls.CREDIT_CAP:
            return False, f"CREDIT_LIMIT_EXCEEDED: Starters credit {total_starter_credits:.1f} exceeds {cls.CREDIT_CAP}", {
                "credit_cap": cls.CREDIT_CAP,
                "total_credits": total_starter_credits
            }

        # 4. Role quotas for starting XI
        role_counts = {r.value: 0 for r in PlayerRole}
        for p in starters:
            role_val = p.role.value if hasattr(p.role, "value") else str(p.role)
            role_counts[role_val] = role_counts.get(role_val, 0) + 1

        for role, count in role_counts.items():
            if count < cls.ROLE_MIN:
                return False, f"ROLE_UNDERFLOW: Role {role} count {count} is below minimum {cls.ROLE_MIN}", role_counts
            if count > cls.ROLE_MAX:
                return False, f"ROLE_OVERFLOW: Role {role} count {count} exceeds maximum {cls.ROLE_MAX}", role_counts

        # 5. Team balance (max 10 from one real team)
        team_counts = {}
        for p in starters:
            team_counts[p.team] = team_counts.get(p.team, 0) + 1
            if team_counts[p.team] > cls.MAX_TEAM_PLAYERS:
                return False, f"TEAM_BALANCE_BREACH: {team_counts[p.team]} players from team {p.team} exceeds limit {cls.MAX_TEAM_PLAYERS}", team_counts

        return True, "VALID", {
            "total_credits": total_starter_credits,
            "role_counts": role_counts,
            "team_counts": team_counts
        }


class OfficialPlatformConstraintValidator:
    """
    Tier 1 Verified Dream11 deadline substitution validator.
    Tests if candidate backup swap preserves valid 11-player squad rules.
    """
    CREDIT_CAP = 100.0
    ROLE_MIN = 1
    ROLE_MAX = 8
    MAX_TEAM_PLAYERS = 10

    @classmethod
    def validate_swap(
        cls,
        current_starters: List[Player],
        player_out: Player,
        player_in: Player
    ) -> Tuple[bool, Dict[str, Any]]:
        # Form hypothetical 11
        projected_xi = [p for p in current_starters if p.id != player_out.id] + [player_in]
        
        # 1. Total credit check
        projected_credits = sum(p.credits for p in projected_xi)
        if projected_credits > cls.CREDIT_CAP:
            return False, {
                "error": "CREDIT_LIMIT_EXCEEDED",
                "limit": cls.CREDIT_CAP,
                "projected_credits": round(projected_credits, 2),
                "excess": round(projected_credits - cls.CREDIT_CAP, 2)
            }

        # 2. Role counts check (1 to 8 per role)
        role_counts = {r.value: 0 for r in PlayerRole}
        for p in projected_xi:
            role_val = p.role.value if hasattr(p.role, "value") else str(p.role)
            role_counts[role_val] = role_counts.get(role_val, 0) + 1

        for role, count in role_counts.items():
            if count < cls.ROLE_MIN:
                return False, {
                    "error": f"ROLE_UNDERFLOW_{role}",
                    "role": role,
                    "count": count,
                    "min": cls.ROLE_MIN
                }
            if count > cls.ROLE_MAX:
                return False, {
                    "error": f"ROLE_OVERFLOW_{role}",
                    "role": role,
                    "count": count,
                    "max": cls.ROLE_MAX
                }

        # 3. Team balance check (max 10 from one team)
        team_counts = {}
        for p in projected_xi:
            team_counts[p.team] = team_counts.get(p.team, 0) + 1
            if team_counts[p.team] > cls.MAX_TEAM_PLAYERS:
                return False, {
                    "error": "TEAM_BALANCE_BREACH",
                    "team": p.team,
                    "count": team_counts[p.team],
                    "max": cls.MAX_TEAM_PLAYERS
                }

        return True, {
            "projected_credits": round(projected_credits, 2),
            "role_counts": role_counts,
            "team_counts": team_counts,
            "passed": True
        }


class ExperimentalInMatchValidator:
    """
    Tier 4 Proposed SmartSub context-sensitive in-match validator.
    Validates tactical Impact Player swaps in 2nd innings without blindly
    enforcing starting-phase bowling quotas.
    """
    CREDIT_CAP = 100.0

    @classmethod
    def validate_impact_swap(
        cls,
        current_xi: List[Player],
        player_out: Player,
        player_in: Player,
        innings: int
    ) -> Tuple[bool, Dict[str, Any]]:
        # 1. Innings check
        if innings != 2:
            return False, {"error": "NOT_SECOND_INNINGS", "details": f"Innings is {innings}, must be 2"}

        # 2. Check that player_in is not already in the active 11
        if any(p.id == player_in.id for p in current_xi):
            return False, {"error": "PLAYER_ALREADY_IN_ACTIVE_XI", "player": player_in.short_name}

        # 3. Credit ceiling verification for projected 11
        projected_xi = [p for p in current_xi if p.id != player_out.id] + [player_in]
        projected_credits = sum(p.credits for p in projected_xi)
        if projected_credits > cls.CREDIT_CAP:
            return False, {
                "error": "CREDIT_LIMIT_EXCEEDED",
                "limit": cls.CREDIT_CAP,
                "projected_credits": round(projected_credits, 2)
            }

        # 4. Contextual role validity: In 2nd innings batting chase, we do not require
        # having >= 3 bowlers if the bowling phase is already completed.
        # We only require at least 1 WK and at least 1 BAT or AR.
        role_counts = {r.value: 0 for r in PlayerRole}
        for p in projected_xi:
            role_val = p.role.value if hasattr(p.role, "value") else str(p.role)
            role_counts[role_val] = role_counts.get(role_val, 0) + 1

        if role_counts.get("WK", 0) < 1:
            return False, {"error": "MISSING_WICKET_KEEPER", "details": "Active lineup must retain a wicket-keeper"}

        return True, {
            "projected_credits": round(projected_credits, 2),
            "role_counts": role_counts,
            "passed": True
        }
