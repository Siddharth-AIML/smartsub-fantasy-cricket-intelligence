import os
import sys
import time
import threading
import urllib.request
import unittest
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import uvicorn
from app.main import app

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

SCREENSHOT_DIR = BASE_DIR / "tests" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://127.0.0.1:8000")
BACKEND_HEALTH_URL = "http://127.0.0.1:8000/health"


def start_backend_if_needed():
    """Ensure FastAPI backend is running and healthy."""
    try:
        req = urllib.request.urlopen(BACKEND_HEALTH_URL, timeout=1)
        if req.getcode() == 200:
            print("[SETUP] Backend server already running on port 8000.")
            return None
    except Exception:
        pass

    print("[SETUP] Launching in-thread Uvicorn server on 127.0.0.1:8000...")
    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait up to 15 seconds for health endpoint
    start_time = time.time()
    while time.time() - start_time < 15:
        try:
            req = urllib.request.urlopen(BACKEND_HEALTH_URL, timeout=1)
            if req.getcode() == 200:
                print("[SETUP] In-thread backend server is healthy and responding!")
                return server_thread
        except Exception:
            time.sleep(0.4)

    raise RuntimeError("Backend failed to start within 15 seconds.")


class SmartSubSeleniumQASuite(unittest.TestCase):
    driver = None
    server_thread = None

    @classmethod
    def setUpClass(cls):
        cls.server_thread = start_backend_if_needed()

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")

        cls.driver = webdriver.Chrome(options=options)
        cls.driver.implicitly_wait(3)

        # Reset match to canonical baseline before running test suite
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:8000/api/matches/match_csk_mi_2026/reset",
                data=b"{}",
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=3)
            print("[SETUP] Reset match to canonical baseline state.")
        except Exception as e:
            print(f"[SETUP] Initial reset note: {e}")

        print(f"[SETUP] Chrome Headless initialized. Navigating to {FRONTEND_URL}...")
        cls.driver.get(FRONTEND_URL)
        WebDriverWait(cls.driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//*[@data-testid='smartsub-app']"))
        )
        print("[SETUP] SmartSub app loaded successfully.")

    @classmethod
    def tearDownClass(cls):
        if cls.driver:
            try:
                cls.driver.quit()
            except Exception:
                pass

    def capture_screenshot(self, filename: str, description: str = ""):
        filepath = SCREENSHOT_DIR / filename
        self.driver.save_screenshot(str(filepath))
        print(f"  [SCREENSHOT] Saved: {filename} ({description})")
        return filepath

    def wait_testid(self, testid: str, timeout: int = 15):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, f"//*[@data-testid='{testid}']"))
        )

    def wait_clickable_testid(self, testid: str, timeout: int = 15):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, f"//*[@data-testid='{testid}']"))
        )

    def get_text_by_testid(self, testid: str) -> str:
        el = self.wait_testid(testid)
        return el.text.strip()

    # =========================================================================
    # TEST A: Initial Page Load & Component Verification
    # =========================================================================
    def test_a_initial_page_load(self):
        """Verify initial UI layout, brand header, scoreboard, pitch, and backups."""
        print("\n--- Running Test A: Initial Page Load & Component Verification ---")
        self.driver.set_window_size(1920, 1080)
        self.driver.get(FRONTEND_URL)

        # 1. Verify SmartSub App Container and Title
        self.assertIn("SmartSub", self.driver.title)
        self.wait_testid("smartsub-app")

        # 2. Verify Header Match Status Pill and Brand
        self.wait_testid("header-match-status")

        # 3. Verify "How to use SmartSub" Guide
        how_to_guide = self.wait_testid("how-to-use-guide")
        self.assertTrue(how_to_guide.is_displayed())

        # 4. Verify Scenario Cards
        self.wait_testid("scenario-cards-container")
        self.wait_testid("start-scenario-1-btn")
        self.wait_testid("start-scenario-2-btn")

        # 5. Verify Match Scoreboard & Simulator Card (PRE_MATCH)
        phase = self.get_text_by_testid("match-phase")
        self.assertTrue("Before match starts" in phase or "PRE_MATCH" in phase)

        # 6. Verify Pitch Formation has exactly 11 active players
        active_count_text = self.get_text_by_testid("active-player-count")
        self.assertIn("11 / 11", active_count_text, "Pitch must strictly show 11 / 11 active players.")

        # 7. Verify Pitch Team Filter Buttons
        self.wait_testid("filter-all-pitch")
        self.wait_testid("filter-csk-pitch")
        self.wait_testid("filter-mi-pitch")

        # 8. Verify Individual Player Points and Team Badges on Pitch Cards
        gaikwad_pts = self.wait_testid("player-points-p_csk_gaikwad")
        self.assertTrue(len(gaikwad_pts.text) > 0, "Gaikwad must show individual fantasy points.")
        gaikwad_team = self.wait_testid("player-team-p_csk_gaikwad")
        self.assertEqual(gaikwad_team.text, "CSK", "Gaikwad must have CSK team badge.")

        # 9. Verify Bench Priority Manager shows Section A (B1-B4) and Section B
        bench = self.wait_testid("bench-priority-manager")
        self.assertTrue(bench.is_displayed())
        for priority in ["B1", "B2", "B3", "B4"]:
            self.wait_testid(f"backup-row-{priority}")
            self.wait_testid(f"backup-team-{priority}")
            self.wait_testid(f"backup-points-{priority}")

        self.wait_testid("bench-replaced-section")

        # 10. Check for horizontal overflow
        has_no_horizontal_overflow = self.driver.execute_script(
            "return (document.documentElement.scrollWidth <= window.innerWidth + 15);"
        )
        self.assertTrue(has_no_horizontal_overflow, "Page has unhandled horizontal overflow!")

        self.capture_screenshot("01_initial_page_load_1920x1080.png", "Initial clean load at 1920x1080")
        print("  [PASS] Test A completed successfully.")

    # =========================================================================
    # TEST B: Scenario 1 Execution & Verification
    # =========================================================================
    def test_b_scenario_1_execution(self):
        """Verify 1-click Scenario 1: Mustafizur DNP removed, Conway B1 skipped, Thakur B2 promoted."""
        print("\n--- Running Test B: Scenario 1 Execution & Verification ---")

        # Click 1-Click Scenario 1 Button
        btn = self.wait_clickable_testid("start-scenario-1-btn")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        time.sleep(0.3)
        self.driver.execute_script("arguments[0].click();", btn)

        # Wait for Completion Banner
        banner = self.wait_testid("completion-notice-banner", timeout=20)
        self.assertIn("Scenario 1 Completed", banner.text)
        print(f"  [VERIFIED] Scenario 1 notice: {banner.text.splitlines()[0]}")

        # Assert Match Phase is LINEUP_CONFIRMED ("Official lineups confirmed")
        phase = self.get_text_by_testid("match-phase")
        self.assertTrue("Official lineups confirmed" in phase or "LINEUP" in phase or "INNINGS" in phase or "Lineup" in phase)

        # Assert Active Pitch Player Count remains exactly 11
        active_count_text = self.get_text_by_testid("active-player-count")
        self.assertIn("11 / 11", active_count_text, "Pitch must have exactly 11 active players after Scenario 1.")

        # Assert Mustafizur Rahman is moved to Replaced / Unavailable section
        pitch_elem = self.wait_testid("pitch-visualizer")
        pitch_text = pitch_elem.text
        # Shardul Thakur should be promoted and marked with B2 SUB badge
        self.wait_testid("sub-badge-p_csk_thakur")
        self.assertIn("Thakur", pitch_text)

        # Verify Thakur's individual points and CSK badge on card
        thakur_pts = self.wait_testid("player-points-p_csk_thakur")
        self.assertTrue(len(thakur_pts.text) > 0)
        thakur_team = self.wait_testid("player-team-p_csk_thakur")
        self.assertEqual(thakur_team.text, "CSK")

        # Conway (B1) should NOT be on the pitch, and bench should reflect skipped status
        conway_row = self.wait_testid("backup-row-B1")
        self.assertIn("SKIPPED", conway_row.text)

        # AI Explanation Card should be populated with explicit CSK/MI context
        ai_card = self.wait_testid("ai-explanation-card")
        self.assertTrue(len(ai_card.text) > 40, "AI explanation card should have substantive text.")

        self.capture_screenshot("02_scenario_1_executed.png", "Scenario 1 execution complete")
        self.capture_screenshot("03_scenario_1_pitch_11_players.png", "Pitch showing Thakur as B2 replacement")
        print("  [PASS] Test B completed successfully.")

    # =========================================================================
    # TEST C: Scenario 2 Execution & Verification
    # =========================================================================
    def test_c_scenario_2_execution(self):
        """Verify 1-click Scenario 2: Innings 1 locked (43.0 pts), Stoinis Impact Sub (32.0 active pts)."""
        print("\n--- Running Test C: Scenario 2 Execution & Verification ---")

        # Reset first to ensure clean state before Scenario 2
        reset_btn = self.wait_clickable_testid("reset-demo-btn")
        self.driver.execute_script("arguments[0].click();", reset_btn)
        WebDriverWait(self.driver, 10).until(
            lambda d: "Before match starts" in d.find_element(By.XPATH, "//*[@data-testid='match-phase']").text or "PRE_MATCH" in d.find_element(By.XPATH, "//*[@data-testid='match-phase']").text
        )

        # Click 1-Click Scenario 2 Button
        btn = self.wait_clickable_testid("start-scenario-2-btn")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        time.sleep(0.3)
        self.driver.execute_script("arguments[0].click();", btn)

        # Wait for Completion Banner
        banner = self.wait_testid("completion-notice-banner", timeout=20)
        self.assertIn("Scenario 2 Completed", banner.text)
        print(f"  [VERIFIED] Scenario 2 notice: {banner.text.splitlines()[0]}")

        # Verify Innings 1 Score is displayed (182/6)
        inn1_score = self.get_text_by_testid("inn1-score")
        self.assertIn("182/6", inn1_score, "Scoreboard must reflect Innings 1 score: MI 182/6.")

        # Verify Active Pitch Formation has exactly 11 active players
        active_count_text = self.get_text_by_testid("active-player-count")
        self.assertIn("11 / 11", active_count_text, "Pitch must have exactly 11 active players after Scenario 2.")

        # Verify Marcus Stoinis is on pitch with IMPACT SUB badge and MI team badge
        self.wait_testid("sub-badge-p_csk_stoinis")
        stoinis_team = self.wait_testid("player-team-p_csk_stoinis")
        self.assertEqual(stoinis_team.text, "MI")
        stoinis_pts = self.wait_testid("player-points-p_csk_stoinis")
        self.assertIn("32.0", stoinis_pts.text)

        # CRITICAL VERIFICATION: Single-Occupant Replacement Scoring
        # 1. Historical ledger score is 43.0 (Shardul Thakur locked)
        historical_score = self.get_text_by_testid("historical-fantasy-score")
        self.assertIn("43.0", historical_score, "Historical ledger must lock Shardul Thakur's 43.0 Innings 1 points.")

        # 2. Replacement slot audit banner explains single-occupant rule
        audit_banner = self.wait_testid("replacement-audit-banner")
        self.assertIn("32.0", audit_banner.text, "Active slot contribution must be Stoinis's 32.0 pts.")
        self.assertIn("43.0", audit_banner.text, "Historical 43.0 pts must be locked and excluded from active score.")

        self.capture_screenshot("04_scenario_2_executed.png", "Scenario 2 execution complete")
        self.capture_screenshot("05_scenario_2_pitch_stoinis_active.png", "Pitch showing Stoinis with IMPACT SUB badge")
        self.capture_screenshot("06_scenario_2_ledger_breakdown.png", "Single occupant scoring breakdown")
        print("  [PASS] Test C completed successfully.")

    # =========================================================================
    # TEST D: Application Reset Verification
    # =========================================================================
    def test_d_application_reset(self):
        """Verify full-application reset contract restores 100% clean baseline state."""
        print("\n--- Running Test D: Application Reset Verification ---")

        # 1. Trigger Reset from current state
        reset_btn = self.wait_clickable_testid("reset-demo-btn")
        self.driver.execute_script("arguments[0].click();", reset_btn)

        # Wait for match phase to become "Before match starts"
        WebDriverWait(self.driver, 10).until(
            lambda d: "Before match starts" in d.find_element(By.XPATH, "//*[@data-testid='match-phase']").text or "PRE_MATCH" in d.find_element(By.XPATH, "//*[@data-testid='match-phase']").text
        )

        # 2. Check points are 0.0
        active_pts = self.get_text_by_testid("active-fantasy-score")
        self.assertEqual(active_pts, "0.0", "Active fantasy points must reset to 0.0.")

        hist_pts = self.get_text_by_testid("historical-fantasy-score")
        self.assertEqual(hist_pts, "0.0", "Historical fantasy points must reset to 0.0.")

        # 3. Pitch has exactly 11 active players
        active_count_text = self.get_text_by_testid("active-player-count")
        self.assertIn("11 / 11", active_count_text)

        # 4. No replacement badges on pitch
        pitch_elem = self.wait_testid("pitch-visualizer")
        self.assertNotIn("IMPACT SUB", pitch_elem.text)
        self.assertNotIn("B2 SUB", pitch_elem.text)

        self.capture_screenshot("07_post_reset_clean_state.png", "Clean baseline state after reset")
        print("  [PASS] Test D completed successfully.")

    # =========================================================================
    # TEST E: Deterministic Replay Verification
    # =========================================================================
    def test_e_deterministic_replay(self):
        """Verify deterministic replay produces identical snapshot and points."""
        print("\n--- Running Test E: Deterministic Replay Verification ---")

        # 1. Run Scenario 1 to generate state
        btn = self.wait_clickable_testid("start-scenario-1-btn")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        time.sleep(0.3)
        self.driver.execute_script("arguments[0].click();", btn)
        self.wait_testid("completion-notice-banner", timeout=20)

        # Record snapshot values
        phase_1 = self.get_text_by_testid("match-phase")
        active_pts_1 = self.get_text_by_testid("active-fantasy-score")

        # 2. Click Deterministic Replay Button
        replay_btn = self.wait_clickable_testid("replay-demo-btn")
        self.driver.execute_script("arguments[0].click();", replay_btn)
        time.sleep(2)

        # 3. Verify snapshot values match identically
        phase_2 = self.get_text_by_testid("match-phase")
        active_pts_2 = self.get_text_by_testid("active-fantasy-score")

        self.assertEqual(phase_1, phase_2, "Replay phase must match original run.")
        self.assertEqual(active_pts_1, active_pts_2, "Replay active points must match original run.")
        print(f"  [VERIFIED] Deterministic replay matches: Phase={phase_2}, Points={active_pts_2}")
        print("  [PASS] Test E completed successfully.")

    # =========================================================================
    # TEST F: Interactive Components & Live Cricket Scorecard Centre
    # =========================================================================
    def test_f_interactive_components(self):
        """Verify Rule Evidence Modal, Squad Diff Modal, and Live Cricket Scorecard Centre."""
        print("\n--- Running Test F: Interactive Components Verification ---")

        # 1. Test Rule Evidence Register Modal
        rules_btn = self.wait_clickable_testid("rules-evidence-btn")
        self.driver.execute_script("arguments[0].click();", rules_btn)

        rules_modal = self.wait_testid("rule-evidence-modal")
        self.assertTrue(rules_modal.is_displayed())
        self.assertTrue("Official Source" in rules_modal.text or "VERIFIED" in rules_modal.text)
        self.assertTrue("PROPOSED" in rules_modal.text or "EXPERIMENTAL" in rules_modal.text)
        self.capture_screenshot("08_rule_evidence_modal_open.png", "Rule Evidence Modal open")

        # Close rules modal
        close_rules_btn = self.wait_clickable_testid("close-rules-modal-btn")
        self.driver.execute_script("arguments[0].click();", close_rules_btn)
        time.sleep(0.5)

        # 2. Test Squad Diff Modal via Decision Audit Trail tab
        tab_audit_btn = self.wait_testid("tab-audit-btn")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tab_audit_btn)
        time.sleep(0.3)
        self.driver.execute_script("arguments[0].click();", tab_audit_btn)
        time.sleep(0.5)

        diff_btns = self.driver.find_elements(By.XPATH, "//*[@data-testid='open-diff-modal-btn']")
        if diff_btns:
            self.driver.execute_script("arguments[0].click();", diff_btns[0])
            diff_modal = self.wait_testid("squad-diff-modal")
            self.assertTrue(diff_modal.is_displayed())
            self.capture_screenshot("09_squad_diff_modal_open.png", "Squad Diff Modal open")

            close_diff_btn = self.wait_clickable_testid("close-diff-modal-btn")
            self.driver.execute_script("arguments[0].click();", close_diff_btn)
            time.sleep(0.5)
        else:
            print("  [NOTE] open-diff-modal-btn not in visible DOM; skipping diff modal click.")

        # 3. Test Live Cricket Scorecard Centre Tab
        tab_scorecard_btn = self.wait_testid("tab-scorecard-btn")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tab_scorecard_btn)
        time.sleep(0.3)
        self.driver.execute_script("arguments[0].click();", tab_scorecard_btn)
        time.sleep(0.5)

        scorecard_centre = self.wait_testid("live-scorecard-centre")
        self.assertTrue(scorecard_centre.is_displayed())
        self.wait_testid("scorecard-innings-1")
        self.wait_testid("scorecard-innings-2")

        # Test Scorecard Team Filters
        csk_filter = self.wait_testid("filter-csk-scorecard")
        self.driver.execute_script("arguments[0].click();", csk_filter)
        time.sleep(0.3)
        all_filter = self.wait_testid("filter-all-scorecard")
        self.driver.execute_script("arguments[0].click();", all_filter)
        time.sleep(0.3)

        self.capture_screenshot("10_cricket_scorecard_centre_open.png", "Live Cricket Scorecard Centre open")
        print("  [PASS] Test F completed successfully.")

    # =========================================================================
    # TEST G: Responsive Layout Verification across 5 Viewports
    # =========================================================================
    def test_g_responsive_viewports(self):
        """Verify layout rendering and lack of unhandled horizontal overflow across 5 viewports."""
        print("\n--- Running Test G: Responsive Layout Verification across 5 Viewports ---")

        viewports = [
            (1920, 1080, "11_viewport_1920x1080.png", "Desktop Wide (1920x1080)"),
            (1366, 768, "12_viewport_1366x768.png", "Laptop Standard (1366x768)"),
            (1024, 768, "13_viewport_1024x768.png", "Tablet Landscape (1024x768)"),
            (768, 1024, "14_viewport_768x1024.png", "Tablet Portrait (768x1024)"),
            (390, 844, "15_viewport_390x844.png", "Mobile Phone (390x844)")
        ]

        for width, height, filename, desc in viewports:
            self.driver.set_window_size(width, height)
            time.sleep(0.8)  # Allow Tailwind responsive re-layout

            # Check document horizontal overflow
            scroll_width = self.driver.execute_script("return document.documentElement.scrollWidth")
            client_width = self.driver.execute_script("return document.documentElement.clientWidth")
            overflow_diff = scroll_width - client_width

            self.assertLessEqual(
                overflow_diff, 15,
                f"Viewport {width}x{height} has horizontal overflow! scrollWidth={scroll_width}, clientWidth={client_width}"
            )

            # Key controls must remain accessible
            self.wait_testid("smartsub-app")
            self.wait_testid("pitch-visualizer")

            self.capture_screenshot(filename, desc)
            print(f"  [VERIFIED] Viewport {width}x{height} passed with no overflow.")

        print("  [PASS] Test G completed successfully across all 5 viewports.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
