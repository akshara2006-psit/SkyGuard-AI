# 🛡️ SkyGuard AI
### SIH 26073 — AI/ML-Based Intelligent Anomaly Detection for Automatic Weather Stations (AWS)

> **"Before we trust the weather forecast, SkyGuard asks: can we trust the data?"**

SkyGuard AI is an intelligent data quality, sensor anomaly detection, and transducer health monitoring platform designed as a quality-control layer between Automatic Weather Station (AWS) networks and downstream meteorological applications.

---

## 🌟 Key Features

1. **Multi-Tier Anomaly Detection Architecture**:
   - **Machine Learning**: Calibrated Isolation Forest learns multi-dimensional normal distributions.
   - **Temporal Rule Engine**: Real-time detection of abrupt spikes (3.5+ sigma), stuck/frozen transducers, linear calibration drift, and telemetry packet dropouts.
   - **Multivariate Coherence**: Cross-sensor analysis to differentiate localized sensor faults from coordinated meteorological events (e.g. cold fronts, squall lines).
2. **Diagnostic Cause Classification & Explainable AI**:
   - Diagnostic synthesizer outputs evidence-based classifications:
     - `PROBABLE_SENSOR_FAULT`
     - `POSSIBLE_WEATHER_EVENT`
     - `POSSIBLE_COMMUNICATION_FAILURE`
     - `POSSIBLE_DATA_QUALITY_ISSUE`
     - `NORMAL`
   - Non-hallucinated narrative explanations detailing the physical evidence and recommended remediation actions.
3. **Sensor Health & Degradation Engine**:
   - Transparent degradation index (0-100%) tracking recent anomaly density, packet loss, and historical fault counts.
4. **AI-Estimated Expected Value Comparison**:
   - Non-destructive tracking: preserves raw observed measurements while providing baseline expected values for operational decision-making.
5. **Interactive SIH Demo Simulation Engine**:
   - Real-time stream generation with 6 pre-configured demo scenarios:
     1. Normal weather baseline
     2. Temperature sensor spike (+30°C on Delhi Safdarjung)
     3. Frozen humidity sensor (Mumbai Colaba)
     4. Linear sensor drift (Chennai Nungambakkam)
     5. Telemetry packet drop (Kolkata Alipore)
     6. Genuine weather front (Bengaluru HAL — proves the AI does not blindly flag genuine weather as sensor faults)
6. **Empirical Model Evaluation**:
   - Reproducible benchmark script evaluated on a 12,960-observation ground-truth dataset with precision, recall, F1-score, and false alarm rates.

---

## 🏗️ System Architecture

```text
AWS Telemetry (Temp, Pressure, Humidity, Timestamp, Station ID)
    ↓
Data Preprocessing & Range Validation
    ↓
Temporal & Cross-Parameter Feature Engineering
    ↓
┌────────────────────────────────────────────────────────┐
│             Multi-Tier Diagnostic Core                │
│                                                        │
│  [Isolation Forest]    [Temporal Rules]   [Multivariate]│
│  Anomaly Score (0-1)   Spike/Freeze/Drift  Coherence    │
└────────────────────────────────────────────────────────┘
    ↓
Cause Classifier & Confidence Estimator
    ↓
Explainable AI Engine + Sensor Health Index
    ↓
FastAPI Backend & Async SQLite Storage
    ↓
React + Vite Operational Dashboard (Recharts)
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Backend Setup
```bash
cd F:\SkyGuardAI\backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be accessible at: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd F:\SkyGuardAI\frontend
npm install
npm run dev
```
Dashboard will be accessible at: `http://localhost:5173`

---

## 🧪 Testing & Model Evaluation

### Run Unit Tests
```bash
cd F:\SkyGuardAI
python tests/test_ml_pipeline.py
python tests/test_api_endpoints.py
```

### Run Ground-Truth Benchmark Evaluation
```bash
cd F:\SkyGuardAI
python scripts/evaluate_model.py
```

---

## 📋 5-7 Minute SIH Demonstration Flow

1. **Dashboard Overview**: Open `http://localhost:5173`. Show the 6 AWS nodes across India (Delhi, Mumbai, Chennai, Kolkata, Bengaluru, Hyderabad).
2. **Start Live Simulation**: Click **Start Simulation**. Observe real-time sensor updates every 3 seconds.
3. **Scenario 2 — Temperature Spike**: Select the *Temp Spike (AWS-001)* scenario. Click into `AWS-001`.
   - Point out the red anomaly badge, observed (e.g. 58°C) vs expected (31°C) comparison, anomaly score (~95%), and the AI explanation pointing out that companion sensors remained stable.
   - Show the recommended action: *"Inspect temperature transducer for electrical noise or grounding issue."*
4. **Scenario 6 — Genuine Meteorological Event**: Select the *Genuine Weather Event (AWS-005)* scenario. Click into `AWS-005`.
   - Highlight that the system classifies it as `POSSIBLE_WEATHER_EVENT` (Cyan badge) with ~85% confidence because temperature, pressure, and humidity shifted coherently.
   - Point out that SkyGuard AI **does not blindly blame the hardware**.
5. **Sensor Health Degradation**: Show how repeated faults degrade the Sensor Health score from 100% to Warning/Critical status with explainable breakdown.
6. **Alert Center**: Open the **Alert Operations** tab and demonstrate acknowledging active incidents.
7. **Model Benchmark**: Click the **Model Benchmark** button in the navbar to present empirical Precision, Recall, and per-fault detection rates.

---

## 📁 Repository Structure

```text
F:\SkyGuardAI
│
├── backend/
│   ├── app/
│   │   ├── api/             # REST endpoints (routes, simulation_routes)
│   │   ├── database/        # Async SQLAlchemy database connection
│   │   ├── ml/              # Isolation Forest, Temporal & Multivariate Analyzers, Classifier
│   │   ├── models/          # SQLAlchemy database models
│   │   ├── services/        # Station CRUD, Alert management, Live simulation runner
│   │   ├── config.py        # Environment settings
│   │   └── main.py          # FastAPI application & lifespan
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/      # Navbar, StationDetail, StationList, Alerts, Timeline, Charts
│   │   ├── services/        # Axios API clients
│   │   ├── App.jsx          # Monitoring dashboard
│   │   └── index.css        # High-contrast operational dark theme
│   └── package.json
│
├── data/
│   ├── raw/                 # Generated raw AWS baseline files
│   ├── processed/           # Benchmark datasets with ground-truth fault injection
│   └── generated/           # Consolidated datasets
│
├── scripts/
│   ├── generate_dataset.py  # Realistic diurnal/synoptic weather time-series generator
│   ├── inject_faults.py     # Controlled reproducible synthetic fault injection
│   └── evaluate_model.py    # Benchmark evaluation pipeline
│
├── tests/
│   ├── test_ml_pipeline.py  # Preprocessing, temporal, multivariate & health tests
│   └── test_api_endpoints.py# FastAPI route verification tests
│
├── docs/                    # Architectural & SIH documentation
├── PROJECT_STATUS.md        # Continuous implementation status tracker
└── README.md
```
