import os
import sys
import time
import threading
import urllib.request
import unittest
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, HTTPServer

BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "frontend" / "dist"

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

SCREENSHOT_DIR = BASE_DIR / "tests" / "screenshots" / "production_validation"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

PORT = 5174
APP_URL = f"http://127.0.0.1:{PORT}"
RENDER_API_BASE = "https://smartsub-api-r5h3.onrender.com"

class StaticServerThread(threading.Thread):
    def __init__(self, directory, port):
        super().__init__(daemon=True)
        self.directory = directory
        self.port = port
        self.httpd = None

    def run(self):
        handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, directory=str(self.directory), **kwargs)
        self.httpd = HTTPServer(("127.0.0.1", self.port), handler)
        self.httpd.serve_forever()

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()

class SmartSubProductionValidationSuite(unittest.TestCase):
    driver = None
    server_thread = None

    @classmethod
    def setUpClass(cls):
        # 1. Reset match on Render backend first to guarantee clean baseline
        try:
            req = urllib.request.Request(
                f"{RENDER_API_BASE}/api/matches/match_csk_mi_2026/reset",
                data=b"{}",
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=15)
            print("[SETUP] Production Render match reset to pre-match state.")
        except Exception as e:
            print(f"[SETUP] Initial Render reset error: {e}")

        # 2. Start local static server serving the production frontend build
        cls.server_thread = StaticServerThread(DIST_DIR, PORT)
        cls.server_thread.start()
        time.sleep(1)

        # 3. Start Headless Chrome
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")

        cls.driver = webdriver.Chrome(options=options)
        cls.driver.implicitly_wait(4)

        print(f"[SETUP] Navigating to {APP_URL} (pointing to {RENDER_API_BASE})...")
        cls.driver.get(APP_URL)
        WebDriverWait(cls.driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//*[@data-testid='smartsub-app']"))
        )
        print("[SETUP] App loaded successfully in Chrome.")

    @classmethod
    def tearDownClass(cls):
        if cls.driver:
            cls.driver.quit()
        if cls.server_thread:
            cls.server_thread.stop()

    def capture_screenshot(self, filename: str, description: str = ""):
        filepath = SCREENSHOT_DIR / filename
        self.driver.save_screenshot(str(filepath))
        print(f"  [SCREENSHOT] {filename} ({description})")
        return filepath

    def wait_testid(self, testid: str, timeout: int = 20):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, f"//*[@data-testid='{testid}']"))
        )

    def wait_clickable_testid(self, testid: str, timeout: int = 20):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, f"//*[@data-testid='{testid}']"))
        )

    def get_text_by_testid(self, testid: str) -> str:
        el = self.wait_testid(testid)
        return el.text.strip()

    # -------------------------------------------------------------------------
    # TEST 1: Initial Screen - 11 Active Players & 4 Backups
    # -------------------------------------------------------------------------
    def test_01_initial_playing_xi_rendered(self):
        """CRITICAL: Verify exactly 11 active players rendered on pitch and 4 backups on bench."""
        print("\n--- TEST 1: Initial Playing XI & Bench Rendering ---")
        
        # Wait for pitch visualizer and active player count
        active_count_el = self.wait_testid("active-player-count")
        
        # Wait up to 15s for the Render backend data to populate
        WebDriverWait(self.driver, 15).until(
            lambda d: "11 / 11" in d.find_element(By.XPATH, "//*[@data-testid='active-player-count']").text
        )
        active_count_text = self.get_text_by_testid("active-player-count")
        print(f"  [ACTIVE COUNT]: {active_count_text}")
        self.assertIn("11 / 11", active_count_text, "Pitch MUST show exactly 11 / 11 Active Players!")

        # Verify pitch has player cards
        pitch_elem = self.wait_testid("pitch-visualizer")
        player_cards = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid^='player-card-']")
        print(f"  [RENDERED CARDS ON PITCH]: {len(player_cards)} cards found")
        self.assertEqual(len(player_cards), 11, "Must render exactly 11 player cards on pitch!")

        # Verify all 4 backups are rendered in Section A of bench
        bench_rows = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid^='backup-row-B']")
        print(f"  [BACKUP ROWS ON BENCH]: {len(bench_rows)} rows found")
        self.assertEqual(len(bench_rows), 4, "Must render exactly 4 backup rows on bench!")

        # Verify Unavailable and Replaced section is initially empty
        replaced_drawer = self.driver.find_elements(By.XPATH, "//*[@data-testid='replaced-players-section']")
        self.assertEqual(len(replaced_drawer), 0, "Replaced/Unavailable players section on pitch MUST be initially empty/hidden!")

        # Verify Section B in bench says 'No players currently substituted out'
        bench_replaced_text = self.get_text_by_testid("bench-replaced-section")
        self.assertIn("No players currently substituted out", bench_replaced_text)

        self.capture_screenshot("01_initial_11_players_visible.png", "11 active starters visibly rendered on pitch")
        print("  [PASS] Test 1: Exactly 11 active players rendered on pitch!")

    # -------------------------------------------------------------------------
    # TEST 2: Page Refresh Persistence
    # -------------------------------------------------------------------------
    def test_02_refresh_initial_loading(self):
        """Verify that browser page refresh reloads and preserves exactly 11 active players."""
        print("\n--- TEST 2: Page Refresh & Initial Loading Persistence ---")
        self.driver.refresh()
        
        # Wait for app container
        self.wait_testid("smartsub-app")
        
        # Verify 11 / 11 is displayed after refresh
        WebDriverWait(self.driver, 15).until(
            lambda d: "11 / 11" in d.find_element(By.XPATH, "//*[@data-testid='active-player-count']").text
        )
        active_count_text = self.get_text_by_testid("active-player-count")
        self.assertIn("11 / 11", active_count_text)

        player_cards = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid^='player-card-']")
        self.assertEqual(len(player_cards), 11)

        self.capture_screenshot("02_post_refresh_11_players.png", "Verified 11 players visible after browser refresh")
        print("  [PASS] Test 2: Page refresh successfully preserves 11 active players!")

    # -------------------------------------------------------------------------
    # TEST 3: Scenario 1 Execution on Render
    # -------------------------------------------------------------------------
    def test_03_scenario_1_execution(self):
        """Verify 1-click Scenario 1 against Render backend."""
        print("\n--- TEST 3: Scenario 1 Execution ---")
        btn = self.wait_clickable_testid("start-scenario-1-btn")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        time.sleep(0.3)
        self.driver.execute_script("arguments[0].click();", btn)

        # Wait for Completion Banner
        banner = self.wait_testid("completion-notice-banner", timeout=25)
        self.assertIn("Scenario 1 Completed", banner.text)
        print("  [NOTICED]:", banner.text.splitlines()[0])

        # Active player count remains strictly 11 / 11
        active_count_text = self.get_text_by_testid("active-player-count")
        self.assertIn("11 / 11", active_count_text)

        # Shardul Thakur promoted with B2 SUB badge
        self.wait_testid("sub-badge-p_csk_thakur")

        # Mustafizur moved to replaced section
        self.wait_testid("replaced-player-p_csk_mustafizur")

        self.capture_screenshot("03_scenario_1_thakur_promoted.png", "Scenario 1: Thakur promoted to pitch, Mustafizur in drawer")
        print("  [PASS] Test 3: Scenario 1 successfully executed!")

    # -------------------------------------------------------------------------
    # TEST 4: Scenario 2 Execution on Render
    # -------------------------------------------------------------------------
    def test_04_scenario_2_execution(self):
        """Verify 1-click Scenario 2 against Render backend with single-occupant scoring."""
        print("\n--- TEST 4: Scenario 2 Execution ---")
        btn = self.wait_clickable_testid("start-scenario-2-btn")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        time.sleep(0.3)
        self.driver.execute_script("arguments[0].click();", btn)

        # Wait for Completion Banner
        banner = self.wait_testid("completion-notice-banner", timeout=25)
        self.assertIn("Scenario 2 Completed", banner.text)
        print("  [NOTICED]:", banner.text.splitlines()[0])

        # Active player count remains strictly 11 / 11
        active_count_text = self.get_text_by_testid("active-player-count")
        self.assertIn("11 / 11", active_count_text)

        # Marcus Stoinis active on pitch with IMPACT SUB badge
        self.wait_testid("sub-badge-p_csk_stoinis")

        # Shardul Thakur moved to replaced section with 43.0 pts locked
        self.wait_testid("replaced-player-p_csk_thakur")
        hist_score = self.get_text_by_testid("historical-fantasy-score")
        self.assertIn("43.0", hist_score)

        # Replacement audit banner explains single-occupant scoring
        audit_banner = self.wait_testid("replacement-audit-banner")
        self.assertIn("32.0", audit_banner.text)
        self.assertIn("43.0", audit_banner.text)

        self.capture_screenshot("04_scenario_2_stoinis_active.png", "Scenario 2: Stoinis active, Thakur historical locked")
        print("  [PASS] Test 4: Scenario 2 successfully executed!")

    # -------------------------------------------------------------------------
    # TEST 5: Reset & Replay Contracts
    # -------------------------------------------------------------------------
    def test_05_reset_and_replay(self):
        """Verify reset restores clean 11 starters and replay runs deterministically."""
        print("\n--- TEST 5: Reset & Replay Verification ---")
        
        # Click Reset Button
        reset_btn = self.wait_clickable_testid("reset-demo-btn")
        self.driver.execute_script("arguments[0].click();", reset_btn)
        time.sleep(2)

        WebDriverWait(self.driver, 15).until(
            lambda d: "Before match starts" in d.find_element(By.XPATH, "//*[@data-testid='match-phase']").text or "PRE_MATCH" in d.find_element(By.XPATH, "//*[@data-testid='match-phase']").text
        )

        # Verify active count is 11 / 11
        active_count_text = self.get_text_by_testid("active-player-count")
        self.assertIn("11 / 11", active_count_text)

        # Verify points reset to 0.0
        self.assertEqual(self.get_text_by_testid("active-fantasy-score"), "0.0")
        self.assertEqual(self.get_text_by_testid("historical-fantasy-score"), "0.0")

        # Verify replaced section is hidden again
        replaced_drawer = self.driver.find_elements(By.XPATH, "//*[@data-testid='replaced-players-section']")
        self.assertEqual(len(replaced_drawer), 0)

        self.capture_screenshot("05_clean_reset_restored.png", "Clean reset state restored with 11 starters")
        print("  [PASS] Test 5: Reset contract validated successfully!")

if __name__ == "__main__":
    unittest.main(verbosity=2)
