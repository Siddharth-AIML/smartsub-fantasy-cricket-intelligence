# SmartSub – AI-Powered Fantasy Cricket Substitution Intelligence
### Full-Stack Architecture v2.2 Specification & Implementation

SmartSub is a specialized full-stack intelligence platform engineered to simulate cricket match dynamics, model fantasy cricket bench priorities (B1–B4), execute a deterministic event-driven substitution engine, and provide tactical explanations using the **Google Gemini API** (with zero-dependency deterministic fallback templates).

---

## 1. Key Architectural Capabilities

1. **Deterministic Substitution Engine (v2.2 Corrected)**:
   - **Scenario 1**: When an unannounced fantasy starter ($S_{\text{DNP}}$, e.g. Mustafizur Rahman) is detected, Backup 1 ($P_{\text{B1}}$, Devon Conway) is bypassed because their real-match status is `DID_NOT_PLAY`. Backup 2 ($P_{\text{B2}}$, Shardul Thakur), who is confirmed in the real-world `PLAYING_XI`, is evaluated against platform squad composition constraints and promoted to `SELECTED`.
   - **Scenario 2**: During Innings 2, Marcus Stoinis ($P_{\text{B3}}$) enters as an Impact Player for Shardul Thakur ($P_{\text{B2}}$). $P_{\text{B2}}$'s 1st-innings bowling points ($43.0$ pts) are permanently locked in an immutable ledger, while $P_{\text{B3}}$ contributes exclusively to the 2nd-innings ledger.
2. **Orthogonal State Architecture**:
   - Decoupled into `FantasySlotType` (`STARTER`, `BACKUP`), `BackupPriority` (`1`–`4`, `None`), `RealMatchParticipation` (`NOT_STARTED`, `PLAYING_XI`, `IMPACT_ENTERED`, `BENCH_SUBSTITUTE`, `DID_NOT_PLAY`), and `FantasySelectionStatus` (`SELECTED`, `REPLACEMENT_CANDIDATE`, `SUBSTITUTED_OUT`, `NOT_SELECTED`).
3. **Dual-Adapter Persistence**:
   - SQLite (`sqlite+aiosqlite:///./smartsub.db`) out-of-the-box for zero-config local execution.
   - PostgreSQL (`postgresql+asyncpg://...`) for production via `DATABASE_URL`.
4. **Authoritative Rule Evidence Register**:
   - Explicitly cites Dream11 official help center rules (`R-D11-01` to `R-D11-04`), BCCI IPL match playing conditions (`R-IPL-01`), and SmartSub proposed experimental rules (`R-SUB-01`, `R-SUB-02`).
5. **Deterministic AI Explainability**:
   - Post-hoc tactical explainability using the **Google Gemini API**. Zero hallucinated confidence scores or invented platform rules. Automatic fallback to structured deterministic templates when `GEMINI_API_KEY` is absent.
6. **Atomic & Idempotent Event Engine**:
   - SHA-256 idempotency keys, database-level unique constraints, monotonic sequence validation, out-of-order event rejection, and deterministic replay from $t=0$.

---

## 2. Project Directory Structure

```
c:\Dream11_artifact\
├── backend/
│   ├── app/
│   │   ├── config.py              # Dual-adapter database & Gemini settings
│   │   ├── database.py            # SQLAlchemy async & sync engines
│   │   ├── main.py                # FastAPI app & CORS configuration
│   │   ├── models/                # Player, Match, Squad, LineupSlot, Decision, AI models
│   │   ├── schemas/               # Pydantic v2 schemas
│   │   ├── services/
│   │   │   ├── validators.py      # PreMatch, OfficialPlatform, & Experimental validators
│   │   │   ├── match_simulator.py # Cricket state machine (toss, ball, over, jump, impact)
│   │   │   ├── substitution_engine.py # Idempotent substitution engine (Scenario 1 & 2)
│   │   │   ├── gemini_ai.py       # Google Gemini API & deterministic fallback service
│   │   │   ├── seed_data.py       # Canonical CSK vs MI 15-player unique roster
│   │   │   └── rule_evidence_register.py # Authoritative rule citation register
│   │   └── routers/               # Matches, Fantasy Teams, Substitutions, AI, Rules
│   ├── tests/
│   │   ├── test_all_scenarios.py  # 8 domain & constraint test specifications
│   │   └── test_api_endpoints.py  # API router integration tests
│   ├── pytest.ini
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx                # Main dashboard coordinator
│       ├── components/
│       │   ├── Header.jsx         # App header & provenance watermark
│       │   ├── MatchSimulatorCard.jsx # Cricket scoreboard & interactive simulator controls
│       │   ├── PitchVisualizer.jsx # 11-player field formation visualizer
│       │   ├── BenchPriorityManager.jsx # Draggable B1–B4 bench queue
│       │   ├── InningsLedgerCard.jsx # Immutable innings-based scoring ledger
│       │   ├── RuleSandbox.jsx    # Scenario 1 & 2 toggles & Rule Mode switcher
│       │   ├── AIExplanationCard.jsx # Gemini AI tactical breakdown & trade-offs
│       │   ├── DecisionAuditList.jsx # Chronological substitution timeline
│       │   ├── SquadDiffModal.jsx # Visual before/after squad state diff
│       │   └── RuleEvidenceModal.jsx # Full Rule Evidence Register
│       └── services/api.js        # REST API integration client
└── README.md
```

---

## 3. How to Run the Application

### 3.1 Start the FastAPI Backend
```bash
cd backend
.\venv\Scripts\python run.py
```
* Backend API: `http://localhost:8000`
* Interactive OpenAPI Docs: `http://localhost:8000/docs`
* Health Endpoint: `http://localhost:8000/health`

*(Optional) Configure Google Gemini API:*
Create a `.env` file in `backend/` with:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
*(If no API key is provided, the backend automatically provides high-fidelity deterministic fallback template rationales with `is_fallback: true`.)*

### 3.2 Start the React + Vite Frontend
```bash
cd frontend
npm run dev
```
* Frontend Dashboard: `http://localhost:5173`

---

## 4. Running the Automated Test Suite

The backend contains 12 comprehensive unit and integration tests covering all 8 requirements from Architecture v2.2:
```bash
$env:PYTHONPATH="backend"
.\backend\venv\Scripts\python -m pytest backend/tests -c backend/pytest.ini -v
```

### Verified Test Matrix:
* `test_scenario_1_b2_replaces_dnp_starter_when_b1_dnp` (PASSED)
* `test_scenario_1_b2_rejected_when_violating_credit_limit` (PASSED)
* `test_fantasy_roster_unique_15_players_prevention` (PASSED)
* `test_player_participating_in_both_innings_scoring` (PASSED)
* `test_scenario_2_preserves_outgoing_player_bat_bowl_field_points` (PASSED)
* `test_captain_vice_captain_multiplier_behavior_on_substitution` (PASSED)
* `test_duplicate_and_out_of_order_impact_player_events` (PASSED)
* `test_deterministic_event_replay_after_multiple_substitutions` (PASSED)
* `test_health_endpoint` (PASSED)
* `test_rules_evidence_register` (PASSED)
* `test_matches_endpoint` (PASSED)
* `test_fantasy_team_endpoint` (PASSED)
