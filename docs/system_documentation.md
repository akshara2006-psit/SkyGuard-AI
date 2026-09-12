# SkyGuard AI — Official SIH 26073 Requirements & System Documentation

> **Official Project Title**: SkyGuard AI: Intelligent Real-Time Anomaly Detection System for Temperature, Pressure, and Humidity Sensors in Automatic Weather Stations  
> **Core Mission**: "SkyGuard AI helps ensure that weather-station observations are trustworthy before they are used for forecasting, monitoring, agriculture, aviation, or disaster-management workflows."  
> **Tagline**: *"Trust the data before you trust the forecast."*

---

## 1. Problem Statement
Automatic Weather Stations (AWS) continuously record surface meteorological parameters. However, sensor degradation, electrical interference, frozen transducers, calibration drift, and packet loss introduce severe anomalies. Standard threshold quality-control rules fail to catch subtle multivariate inconsistencies or falsely flag real severe weather events as sensor faults.

## 2. Proposed Solution
SkyGuard AI provides an intelligent, multi-layered AI/ML anomaly detection and diagnostic framework. It evaluates raw observations against:
1. **Unsupervised Machine Learning** (Isolation Forest)
2. **Temporal & Seasonal Dynamics** (rolling baselines, rate-of-change, persistence)
3. **Multivariate Consistency Analysis** (cross-parameter physical constraints)
4. **Spatial Consistency Verification** (station-to-station cross-validation)
5. **Model Feature Attribution** (Isolation Forest decision-tree feature attribution)
6. **Sensor Health & Maintenance Diagnostics**

## 3. System Architecture
```
AWS SENSOR TELEMETRY (Temp, Pressure, Humidity)
       ↓
DATA INGESTION & RANGE VALIDATION
       ↓
TEMPORAL & MULTIVARIATE FEATURE ENGINEERING
       ↓
ISOLATION FOREST ANOMALY SCORING (Unsupervised ML)
       ↓
MODEL FEATURE ATTRIBUTION ENGINE (Decision Path Attribution)
       ↓
MULTIVARIATE & SPATIAL CONSISTENCY EVALUATION
       ↓
DIAGNOSTIC CLASSIFICATION ENGINE
  ├── Probable Sensor Anomaly
  ├── Possible Genuine Meteorological Event
  ├── Possible Communication Failure
  └── Possible Data Quality Issue
       ↓
SENSOR HEALTH DEGRADATION ENGINE & MAINTENANCE PREDICTION
       ↓
NON-DESTRUCTIVE AI-ESTIMATED EXPECTED VALUE GENERATION
       ↓
REAL-TIME WEBSOCKET/REST ALERTING & DASHBOARD UPDATE
```

## 4. Input Parameter Scope (Strict Restriction)
The machine learning pipeline strictly operates on ONLY three core atmospheric variables:
1. **Temperature (°C)**
2. **Atmospheric Pressure (hPa)**
3. **Relative Humidity (%)**

No extraneous environmental or GPS variables are required or accepted as model inputs.

## 5. Dataset & Labelled Fault Injection Pipeline
The system incorporates ground-truth evaluation datasets covering 6 Indian AWS nodes (Delhi, Mumbai, Chennai, Kolkata, Bengaluru, Hyderabad). 
Fault types injected into controlled evaluation sets include:
- **Sudden Spike**: Sudden high-magnitude impulse deviation (e.g., +25°C).
- **Frozen Sensor**: Zero variance across consecutive timesteps.
- **Sensor Drift**: Linear slope degradation indicating calibration loss.
- **Communication Failure**: Packet drop / missing observation telemetry.
- **Multivariate Inconsistency**: Single parameter anomaly while companion variables remain flat.
- **Possible Genuine Meteorological Event**: Coherent multi-variable atmospheric shift (e.g., squall line).

## 6. Machine Learning Methodology & Isolation Forest
The baseline anomaly detection engine uses `SkyGuardIsolationForest` (150 tree estimators, calibrated 0.0 to 1.0 scoring). Isolation Forest isolates anomalies by randomly partitioning feature spaces. Short path lengths correlate directly with high anomaly scores.

## 7. Temporal & Seasonal Analysis
Dynamic rolling windows (short: 6 timesteps, long: 24 timesteps) compute:
- Z-score deviation from short-term baseline: $Z = \frac{x - \mu}{\sigma}$
- Instantaneous rate-of-change ($ROC = x_t - x_{t-1}$)
- Persistence index ($\sigma_{\text{window}}$ over moving sample)

## 8. Multivariate & Spatial Consistency Analysis
- **Multivariate Consistency**: Checks whether Temperature, Pressure, and Humidity change coherently within a single AWS station. Single-variable spikes with flat companion readings indicate a *Probable Sensor Anomaly*. Coordinated changes across all three parameters indicate a *Possible Genuine Meteorological Event*.
- **Spatial Consistency & Haversine Proximity**: Cross-verifies target AWS observations against geographically proximate peer stations using ONLY the three approved meteorological variables: Temperature, Pressure, and Relative Humidity. Station coordinates are used exclusively for Haversine distance calculations ($d \le 1200\text{ km}$).
  - `NOT_SUPPORTED` (Spatial Contradiction): Target station deviates strongly while neighboring AWS nodes remain normal $\rightarrow$ strengthens evidence for *Probable Sensor Anomaly*.
  - `SUPPORTED` (Regional Weather Front): Multiple nearby AWS stations report coherent shifts $\rightarrow$ supports *Possible Genuine Meteorological Event*.
  - `INSUFFICIENT_EVIDENCE`: No nearby station observations available or all peer telemetry missing $\rightarrow$ *Absence of spatial data is never falsely flagged as a sensor fault*.
- **Multi-Station Scalability ($N$ Stations)**: Designed to support $N$ stations ($N=1, 6, 20, 100, 1000+$) through database/API-driven station discovery. Adding stations requires no manual changes to ML logic.

## 9. Root-Cause Classification Terminology
The classifier outputs standardized diagnostic classifications:
- **Probable Sensor Anomaly** (e.g., Temperature Spike, Frozen Humidity Transducer)
- **Possible Genuine Meteorological Event** (e.g., Squall line, cold front)
- **Possible Communication Failure** (Telemetry packet loss)
- **Possible Data Quality Issue** (Intermittent gaps)

## 10. Explainable AI & Model Feature Attribution
SkyGuard AI currently uses model feature attribution derived from the Isolation Forest decision structure (`SkyGuardFeatureAttributor`). This provides an interpretable indication of feature contribution without claiming formal SHAP values. Each anomaly flag is accompanied by a quantitative feature attribution breakdown showing the exact percentage contribution of each feature to the anomaly decision (e.g. `Temperature Deviation: 42.1% contribution`, `Pressure Stability: 18.5% contribution`).

## 11. Sensor Health & Maintenance Intelligence
SkyGuard AI implements a deterministic, multi-factor sensor health engine (`SensorHealthEngine`) that evaluates each individual transducer (`temperature`, `pressure`, `humidity`, and `overall` station status):
- **Health Score Formula**: Computed deterministically in range `[5.0, 100.0]`:
  $$\text{Score} = 100.0 - \text{Penalty}_{\text{anomalies}} - \text{Penalty}_{\text{missing}} - \text{Penalty}_{\text{faults}}$$
  - Anomaly Frequency Penalty: Up to 35 pts based on ratio of recent anomaly events.
  - Missing Data Penalty: Up to 25 pts based on missing observation rate.
  - Fault History Penalty: Up to 20 pts based on cumulative historical fault counts.
- **Degradation Trend Tracking**: Evaluates health trajectory against previous scores to distinguish `"STABLE"`, `"DECLINING"`, or `"IMPROVING"` trends. Falsely flagging isolated single anomalies as severe degradation is prevented.
- **Deterministic Maintenance Recommendation Engine**:
  - `NOMINAL_MONITORING` ($\ge 75\%$ & Stable): Routine operational monitoring.
  - `INSPECTION_RECOMMENDED` ($50\% - 74\%$ or Declining): Schedule routine technician inspection.
  - `MAINTENANCE_REQUIRED` ($35\% - 49\%$): Schedule technician recalibration and transducer wiring check.
  - `URGENT_REPLACEMENT` ($< 35\%$ or $>40\%$ missing data): Immediate hardware replacement required.
- **Empirical Evidence Output**: Each recommendation displays clear data evidence (e.g. `8 anomaly events recorded`, `Missing data rate at 5.0%`, `Health score exhibiting a declining trend`). No unverified "Predictive RUL" claims are made.

## 12. Non-Destructive Expected Value Estimation
Raw observations are never altered or overwritten. When an anomaly is detected, the UI displays both:
- **Observed Value**: e.g., `55.0°C`
- **AI-Estimated Expected Value**: e.g., `31.4°C`

## 13. Real-Time Operations & Dashboard
Built with React, Vite, and Recharts. Supports live streaming telemetry, automated 3-second polling updates, real-time alert acknowledgments, and responsive layout across 6 primary operational views:
- **Overview**: High-level network summary & alert feed
- **Stations**: Deep station-level diagnostics and live telemetry graphs
- **Alerts**: Incident management and acknowledgment workflow
- **Analytics**: Ground-truth model evaluation metrics & Edge AI statistics
- **Simulation**: Controlled Simulation Lab for fault injection testing
- **About**: System specifications, SIH 26073 documentation, and Grand Challenge

## 14. Edge AI & Low-Power Energy Efficiency
Designed for lightweight deployment on low-power microcontrollers (ESP32-S3 / ARM Cortex-M4):
- **Inference Latency**: < 3.2 ms per sample
- **Memory Footprint**: 48 KB SRAM quantized representation
- **Architecture**: Edge-based anomaly screening with central diagnostic escalation

## 15. Dynamic Model Evaluation Methodology & Measured Metrics
All model metrics displayed in SkyGuard AI are computed dynamically by executing real-time pipeline inference across ground-truth benchmark observations (`data/processed/benchmark_dataset_with_ground_truth.csv`):
- **Execution Pipeline**: Raw telemetry → Data preprocessor → Isolation Forest prediction → Temporal/Multivariate analysis → Diagnostic classification → Ground-truth comparison matrix.
- **Latency Measurement**: Evaluates per-sample inference and diagnostic processing duration using high-precision execution timers (`time.perf_counter()`).
- **Dynamic Metric Computation**: Precision, Recall (Sensitivity), F1-Score, False Positive Rate (FPR), and per-fault category detection rates are calculated live upon demand via `POST /api/evaluation/run` or loaded from the latest evaluation state (`GET /api/evaluation`). No static benchmark metrics are hard-coded in the UI.

---

## 16. Operational Use Cases

### 1. Weather Forecasting
Provides clean, quality-controlled input telemetry to numerical weather prediction (NWP) models, preventing bad data from corrupting forecasting algorithms.

### 2. Climate Monitoring
Ensures long-term climate datasets are free from artificial trends caused by uncalibrated sensor drift.

### 3. Disaster Management
Distinguishes genuine extreme weather events (squall lines, convective storms) from sensor glitches, preventing false panic while ensuring timely evacuation alerts.

### 4. Agriculture
Provides accurate microclimate data for crop yield prediction, precision irrigation, and frost risk management.

### 5. Aviation
Ensures runway meteorological visual range (MVR) and altimeter setting telemetry from airport AWS units remain reliable.

### 6. Scientific Research
Delivers high-integrity atmospheric observation logs for meteorological researchers.

### 7. Meteorological Observation Networks
Enables automated, remote network monitoring for national weather services (e.g., IMD).

### 8. Remote & Low-Power Weather Stations
Enables low-power Edge AI anomaly screening on solar-powered ESP32 nodes in remote mountainous or ocean regions.

---

## 17. Installation & Usage Instructions

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Running Test Suites
```bash
python tests/test_ml_pipeline.py
python tests/test_api_endpoints.py
```

### Running Model Benchmark Script
```bash
python scripts/evaluate_model.py
```
