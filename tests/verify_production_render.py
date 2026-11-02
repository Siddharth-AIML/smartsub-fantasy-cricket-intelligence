import urllib.request
import json
import sys

RENDER_BASE = "https://smartsub-api-r5h3.onrender.com"
print("=== TESTING PRODUCTION RENDER BACKEND ===")

# 1. Health check
with urllib.request.urlopen(f"{RENDER_BASE}/health") as r:
    data = json.loads(r.read().decode())
    print("[OK] /health ->", data.get("status"))

# 2. Reset match on Render
req = urllib.request.Request(
    f"{RENDER_BASE}/api/matches/match_csk_mi_2026/reset",
    data=b"{}",
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read().decode())
    print("[OK] /api/matches/.../reset ->", data.get("status"))

# 3. Live State
with urllib.request.urlopen(f"{RENDER_BASE}/api/matches/match_csk_mi_2026/live-state") as r:
    data = json.loads(r.read().decode())
    phase = data.get("scoreboard", {}).get("phase")
    print("[OK] /api/matches/.../live-state -> Phase:", phase)
    assert phase == "PRE_MATCH", f"Expected PRE_MATCH, got {phase}"

# 4. Fantasy Team
with urllib.request.urlopen(f"{RENDER_BASE}/api/fantasy-teams/fantasy_team_demo") as r:
    data = json.loads(r.read().decode())
    slots = data.get("lineup_slots", [])
    selected = [s for s in slots if s.get("fantasy_selection_status") == "SELECTED"]
    backups = [s for s in slots if s.get("slot_type") == "BACKUP"]
    print(f"[OK] /api/fantasy-teams/... -> Total slots: {len(slots)}, Active Playing XI: {len(selected)}/11, Backups: {len(backups)}/4")
    assert len(selected) == 11, f"Expected 11 starters, got {len(selected)}"
    assert len(backups) == 4, f"Expected 4 backups, got {len(backups)}"

# 5. Scenario 1 on Render
req = urllib.request.Request(
    f"{RENDER_BASE}/api/matches/match_csk_mi_2026/scenarios/run-scenario-1",
    data=b"{}",
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read().decode())
    print("[OK] Scenario 1 executed on Render -> Status:", data.get("status"))
    assert data.get("status") == "SCENARIO_1_COMPLETED"

# 6. Scenario 2 on Render
req = urllib.request.Request(
    f"{RENDER_BASE}/api/matches/match_csk_mi_2026/scenarios/run-scenario-2",
    data=b"{}",
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read().decode())
    print("[OK] Scenario 2 executed on Render -> Status:", data.get("status"))
    assert data.get("status") == "SCENARIO_2_COMPLETED"
    rep_audit = data.get("points_info", {}).get("replacement_slot_audit")
    if rep_audit:
        print(f"     Slot active contribution: {rep_audit.get('active_slot_contribution')} pts (Stoinis)")
        print(f"     Historical locked ledger: {rep_audit.get('replaced_player_historical_points')} pts (Thakur)")

# 7. Clean Reset back to pre-match
req = urllib.request.Request(
    f"{RENDER_BASE}/api/matches/match_csk_mi_2026/reset",
    data=b"{}",
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read().decode())
    print("[OK] Clean Reset restored on Render -> Status:", data.get("status"))

print("\n=== ALL PRODUCTION RENDER BACKEND API CHECKS PASSED PERFECTLY ===")
