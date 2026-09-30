# Accentra Fraud Rule Engine & Analyst Review Console

[![Tests](https://img.shields.io/badge/pytest-27%20passed-success)](backend/tests)
[![Stack](https://img.shields.io/badge/FastAPI-0.110+-009688)](https://fastapi.tiangolo.com)
[![Frontend](https://img.shields.io/badge/React%2019-Vite%20TypeScript-61DAFB)](frontend/)
[![AWS](https://img.shields.io/badge/AWS-SNS%20%7C%20SES-FF9900)](backend/app/notifications/)
[![Database](https://img.shields.io/badge/SQLAlchemy-PostgreSQL%20%7C%20SQLite-336791)](backend/app/models.py)

An enterprise-grade FinTech Fraud Detection Rule Engine with a high-performance evaluation core, pluggable rule architecture (Open/Closed Principle), asynchronous AWS SNS/SES high-risk alerting with idempotency guards, and an interactive React analyst reviewer console.

---

## 1. System Architecture

```text
Payment Gateway / Upstream Simulator
               │
               ▼  POST /api/transactions
┌────────────────────────────────────────────────────────┐       ┌──────────────────────────────────────┐
│  FastAPI Backend Service                               │       │  React Reviewer Console              │
│  ├── REST API Routers                                  │◄─────►│  (Vite + TypeScript + React Query)   │
│  │   ├── /api/transactions (Ingest, Evaluate, Re-eval) │  REST │  ├── Live Risk Queue Table           │
│  │   ├── /api/flags (Filter, Sort, Review Actions)     │       │  ├── Flag Detail & Evidence Drawer   │
│  │   ├── /api/rules (Dynamic Weight/Threshold Tuning)  │       │  ├── Impossible Travel Kinematics    │
│  │   ├── /api/stats (Real-Time Metrics)                │       │  ├── Audit Log Timeline              │
│  │   └── /api/simulator (Attack Vector Injection)      │       │  └── Transaction Simulator           │
│  ├── Pluggable Rule Engine Core                        │       └──────────────────────────────────────┘
│  │   ├── Rule Registry (@register_rule + pkgutil)      │
│  │   ├── Rule Isolation (Try/Catch per rule)           │
│  │   ├── Weighted Score Aggregation Capped at 100      │
│  │   └── Pluggable Rule Modules:                       │
│  │       ├── rules/velocity.py (Burst frequency)       │
│  │       ├── rules/amount.py (Rolling z-score / ratio) │
│  │       └── rules/geo.py (Haversine implied speed)    │
│  └── Notification Service                              │───────► AWS SNS Topic / AWS SES Email
│      ├── Idempotency Guard (notified_at flag check)    │         (Structured JSON / HTML Alert)
│      └── Exponential Backoff Retries                   │
└───────────────────────────┬────────────────────────────┘
                            │ SQLAlchemy ORM
                            ▼
           PostgreSQL (Prod) / SQLite (Dev)
```

---

## 2. Key Capabilities & Functional Requirements

| Requirement | Implementation Detail | Status |
| :--- | :--- | :---: |
| **FR-1: Transaction Ingestion** | `POST /api/transactions` ingests, persists to database, executes engine, records rule results, and returns decision. | ✅ |
| **FR-2: Fault Isolation** | Each rule runs in an isolated `try/except` sandbox. An unhandled exception in one rule returns `score=0` with error evidence and never impacts other rules. | ✅ |
| **FR-3: Pluggable Core Rules** | **R1 (Velocity)**, **R2 (Unusual Amount)**, and **R3 (Impossible Travel)** fully implemented with mathematical rigour. | ✅ |
| **FR-4: Open/Closed Principle** | Adding a new rule requires only creating a new `.py` file decorated with `@register_rule`. The engine discovers it automatically with **zero edits to engine code**. | ✅ |
| **FR-5: Weighted Aggregation** | `Aggregate Score = min(100, max(scores) + 0.25 * sum(other_scores))` factoring in rule weights. | ✅ |
| **FR-6: Fraud Flag Creation** | Transactions with `score >= FLAG_THRESHOLD` (default 50) automatically create a `FraudFlag` in `PENDING` status. | ✅ |
| **FR-7: AWS Alerting** | `score >= HIGH_RISK_THRESHOLD` (default 80) dispatches AWS SNS topic publication or SES email alert asynchronously via background tasks. | ✅ |
| **FR-8: Console Queue** | Flag Queue with color-coded risk badges (Crimson $\ge 80$, Amber $50-79$, Emerald $< 50$), status tabs, score filter, and pagination. | ✅ |
| **FR-9: Detail & Kinematics** | Deep investigation modal showing transaction metadata, evidence tables, and travel speed vs commercial jet limit. | ✅ |
| **FR-10: Analyst Resolution** | Reviewers can resolve flags as `REVIEWED` or `CLEARED` with audit notes; every action is written to `audit_log`. Confirmation required for `CLEARED`. | ✅ |
| **FR-11: Rule Tuning** | Thresholds ($N, W, k, M, V$) and weights are dynamically configurable via `GET /api/rules` and `PUT /api/rules/{name}` from the UI. | ✅ |
| **FR-12: On-Demand Re-evaluation** | `POST /api/transactions/{id}/re-evaluate` re-evaluates transactions after rule tuning. | ✅ |

---

## 3. Pluggable Rule Specifications

### R1: Transaction Velocity (`rules/velocity.py`)
- **Trigger**: Account executes more than $N$ transactions (default 5) within lookback window $W$ (default 10 minutes).
- **Score Formula**: $\min(100, 40 + 15 \times (\text{count} - N))$.
- **Evidence**: Total transaction count, window minutes, threshold, prior transaction IDs.

### R2: Unusual Transaction Amount (`rules/amount.py`)
- **Trigger**:
  - **Established History ($\ge 5$ txns)**: Amount exceeds $\mu + k \cdot \sigma$ ($z\text{-score} \ge k$, default $k = 3.0$) of last 30 days.
  - **Thin History ($< 5$ txns)**: Amount exceeds $M \times$ prior average (default $M = 3.0$), or initial new account charge $\ge \$5,000$.
- **Score Formula**: Proportional scaling with $z$-score or multiple ratio, capped at 100.
- **Evidence**: 30-day mean, standard deviation, calculated $z$-score, thin history ratio.

### R3: Impossible Geographical Location (`rules/geo.py`)
- **Trigger**: Great-circle distance (Haversine formula) divided by elapsed hours implies speed $> V$ km/h (default 900 km/h, commercial airliner speed).
- **Score Formula**: 90 if implied speed $> 2V$ (e.g. supersonic or teleportation), otherwise 70.
- **Evidence**: Prior location (lat/lon, timestamp, merchant), current location, distance in km, elapsed time, implied speed in km/h. Missing coordinates skip evaluation without false triggers.

---

## 4. Alerting & Idempotency Guard (`notifications/`)

- **Pluggable Backends**: `NOTIFIER=log` (local development), `NOTIFIER=sns` (AWS SNS), `NOTIFIER=ses` (AWS SES).
- **Idempotency Guard**: Alerts are dispatched strictly when `fraud_flags.notified_at IS NULL`. Once sent, `notified_at` is timestamped. Re-evaluating a transaction will never send duplicate alerts.
- **Retry Mechanism**: Transient AWS network errors retry with exponential backoff (3 attempts). Notification errors run in background tasks and never block or fail the transaction API.

---

## 5. Quickstart & Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### 1. Clone & Set Up Backend

```bash
# Clone the repository
git clone https://github.com/KTJAGANNATHAN0/Acentra-Health-BUILD-TO-CARE-202.git
cd Acentra-Health-BUILD-TO-CARE-202

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate   # Windows
# source venv/bin/activate # Linux/macOS

# Install dependencies
pip install -r backend/requirements.txt

# Run database seed (generates baseline history & realistic fraud patterns)
python backend/scripts/seed.py

# Run test suite
pytest backend/tests -v
```

### 2. Start the Backend API Server

```bash
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be accessible at: `http://127.0.0.1:8000/docs`.

### 3. Set Up & Start Reviewer Console Frontend

In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 6. Docker Compose Deployment

To run the complete production stack (PostgreSQL + FastAPI + React in Nginx):

```bash
docker-compose up --build
```
- Frontend Reviewer Console: `http://localhost:5173`
- Backend API & Swagger: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`

---

## 7. Automated Test Suite

The test suite covers unit tests for every boundary condition, engine isolation, dynamic extensibility, and REST API integration:

```bash
pytest backend/tests -v
```

```text
backend/tests/test_api.py::test_health_endpoint PASSED
backend/tests/test_api.py::test_post_transaction_normal PASSED
backend/tests/test_api.py::test_post_transaction_high_risk_flagged PASSED
backend/tests/test_api.py::test_flag_listing_and_filtering PASSED
backend/tests/test_api.py::test_flag_detail_and_patch_status PASSED
backend/tests/test_api.py::test_re_evaluate_endpoint PASSED
backend/tests/test_api.py::test_rule_config_get_and_put PASSED
backend/tests/test_api.py::test_dashboard_stats PASSED
backend/tests/test_engine.py::test_score_aggregation_formula PASSED
backend/tests/test_engine.py::test_rule_isolation_fault_tolerance PASSED
backend/tests/test_engine.py::test_disabled_rule_skipped PASSED
backend/tests/test_engine.py::test_dynamic_rule_registration_open_closed_principle PASSED
backend/tests/test_notifications.py::test_notification_idempotency PASSED
backend/tests/test_rules.py::TestVelocityRule::test_velocity_under_threshold PASSED
backend/tests/test_rules.py::TestVelocityRule::test_velocity_exactly_at_threshold PASSED
backend/tests/test_rules.py::TestVelocityRule::test_velocity_exceeds_threshold PASSED
backend/tests/test_rules.py::TestVelocityRule::test_velocity_ignores_outside_window PASSED
backend/tests/test_rules.py::TestAmountRule::test_thin_history_normal_amount PASSED
backend/tests/test_rules.py::TestAmountRule::test_thin_history_spike_amount PASSED
backend/tests/test_rules.py::TestAmountRule::test_established_history_z_score_trigger PASSED
backend/tests/test_rules.py::TestAmountRule::test_new_account_large_purchase PASSED
backend/tests/test_rules.py::TestImpossibleTravelRule::test_haversine_formula PASSED
backend/tests/test_rules.py::TestImpossibleTravelRule::test_normal_commute_not_triggered PASSED
backend/tests/test_rules.py::TestImpossibleTravelRule::test_subsonic_commercial_flight_not_triggered PASSED
backend/tests/test_rules.py::TestImpossibleTravelRule::test_impossible_travel_teleportation_triggered_high PASSED
backend/tests/test_rules.py::TestImpossibleTravelRule::test_impossible_travel_moderate_triggered_70 PASSED
backend/tests/test_rules.py::TestImpossibleTravelRule::test_missing_coordinates_gracefully_skipped PASSED

======================== 27 passed in 0.41s ========================
```

---

## 8. License & Authorship

Developed for **Acentra Health** as part of the **BUILD-TO-CARE-202** Fraud Prevention Initiative.
Licensed under the Apache-2.0 License.
